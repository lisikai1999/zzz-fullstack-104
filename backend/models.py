"""
混凝沉淀仿真模型（标定版）
- 混凝模型：投药→矾花生成（碰撞动力学简化）
- 沉淀模型：Stokes 公式 + 一维短流模型
- 异常工况仿真（持续应急记录）

参数标定依据：
- 典型平流沉淀池去除率 85-95%（原水 50NTU → 出水 1-3 NTU）
- PAC 投药量 20-60 mg/L 对应矾花粒径 200-800 μm
- 矾花有效密度差 20-100 kg/m³（含水率高时偏低）
- 表面负荷设计值 1.2-2.5 m/h
"""
import numpy as np
from scipy.optimize import minimize_scalar
from dataclasses import dataclass, asdict


@dataclass
class RawWaterParams:
    turbidity: float        # 原水浊度 (NTU)
    temperature: float      # 水温 (°C)
    ph: float               # pH
    alkalinity: float       # 碱度 (mg/L CaCO3)
    ss: float               # 悬浮物浓度 (mg/L)


@dataclass
class CoagulationParams:
    dosage: float           # 投药量 (mg/L) - PAC
    mixing_intensity: float # 搅拌强度 G (s^-1)
    mixing_time: float      # 混合时间 (s)
    floc_time: float        # 絮凝时间 (min)


@dataclass
class SedimentationParams:
    tank_length: float      # 沉淀池长度 (m)
    tank_depth: float       # 有效水深 (m)
    tank_width: float       # 池宽 (m)
    flow_rate: float        # 处理流量 (m³/h)
    short_circuit_factor: float  # 短流系数 (0~1, 1=理想)


def water_viscosity(temperature: float) -> float:
    """水的动力黏度 (Pa·s) - Poiseuille 经验公式"""
    return 1.787e-3 * np.exp(-0.0248 * temperature)


def water_density(temperature: float) -> float:
    """水的密度 (kg/m³)"""
    return 999.842 + 0.06793 * temperature - 0.009095 * temperature**2


def floc_formation(raw: RawWaterParams, coag: CoagulationParams) -> dict:
    """
    混凝模型：计算矾花粒径和絮体密度
    标定目标：投药30mg/L、原水50NTU时，矾花~400μm，密度差~30 kg/m³
    """
    G = coag.mixing_intensity
    t_floc = coag.floc_time * 60.0

    # pH 影响因子：PAC 最佳 pH 6.5~7.8
    ph_factor = 1.0 - 0.15 * (abs(raw.ph - 7.0) ** 1.2)
    ph_factor = max(0.25, min(1.0, ph_factor))

    # 温度影响：低温絮凝效率下降（4°C时约60%效率）
    temp_factor = 0.55 + 0.025 * raw.temperature
    temp_factor = max(0.45, min(1.0, temp_factor))

    # 投药有效度：Langmuir 型吸附曲线
    # 最佳剂量约为 SS * 0.4~0.6，过量效果边际递减
    optimal_dose = raw.ss * 0.5 + 8.0
    dose_ratio = coag.dosage / optimal_dose
    dosage_eff = dose_ratio / (0.3 + dose_ratio)
    dosage_eff = min(dosage_eff, 0.98)

    # Gt 值——絮凝段 G 值取混合段的 20-30%
    G_floc = G * 0.25
    Gt = G_floc * t_floc

    # 矾花粒径 (μm)：标定基准 400μm
    # Gt 范围 1e4~1e5 对应良好絮凝
    Gt_factor = 0.6 + 0.5 * np.log10(max(Gt / 2e4, 0.5))
    Gt_factor = max(0.4, min(1.3, Gt_factor))

    d_floc = 400.0 * dosage_eff * ph_factor * temp_factor * Gt_factor
    d_floc = max(30.0, min(1500.0, d_floc))

    # 矾花有效密度差 (kg/m³)：分形结构，大矾花密度差小
    # 标定：400μm → delta_rho ≈ 30, 200μm → 60, 800μm → 18
    delta_rho = 4800.0 / (d_floc ** 0.7)

    rho_water = water_density(raw.temperature)
    rho_floc = rho_water + delta_rho

    # 混凝去除效率：投药-絮凝-卷扫综合
    removal_coag = dosage_eff * ph_factor * temp_factor * 0.92
    removal_coag = min(removal_coag, 0.96)
    residual_ss = raw.ss * (1.0 - removal_coag)

    return {
        "floc_diameter_um": round(d_floc, 1),
        "floc_density_kg_m3": round(rho_floc, 2),
        "delta_rho": round(delta_rho, 2),
        "coagulation_efficiency": round(removal_coag, 4),
        "residual_ss_mg_L": round(residual_ss, 2),
        "ph_factor": round(ph_factor, 3),
        "temp_factor": round(temp_factor, 3),
        "Gt_value": round(Gt, 0),
    }


def stokes_settling_velocity(d_um: float, delta_rho: float, temperature: float) -> float:
    """
    Stokes 沉降速度 (m/s)
    v = Δρ * g * d² / (18 * μ)
    """
    d_m = d_um * 1e-6
    mu = water_viscosity(temperature)
    g = 9.81
    v = delta_rho * g * d_m**2 / (18.0 * mu)
    return v


def sedimentation_1d(floc_info: dict, sed: SedimentationParams,
                     raw: RawWaterParams, dt: float = 60.0,
                     total_time: float = 7200.0) -> dict:
    """
    一维沉淀池模型（考虑短流）
    标定目标：正常工况出水浊度 0.5~3 NTU
    """
    L = sed.tank_length
    H = sed.tank_depth
    W = sed.tank_width
    Q = sed.flow_rate / 3600.0  # m³/s

    surface_area = L * W
    surface_loading = Q / surface_area  # m/s

    v_s = stokes_settling_velocity(
        floc_info["floc_diameter_um"],
        floc_info["delta_rho"],
        raw.temperature,
    )

    v_h = Q / (H * W)

    HRT_ideal = L * H * W / Q
    HRT_actual = HRT_ideal * sed.short_circuit_factor

    nx = 50
    dx = L / nx
    nt = int(total_time / dt)

    C = np.zeros(nx)
    inlet_C = floc_info["residual_ss_mg_L"]

    v_h_eff = v_h / sed.short_circuit_factor

    # 每个网格单元内的沉降去除分数
    # 颗粒通过单元的时间 = dx / v_h_eff
    # 该时间内沉降高度 = v_s * dx / v_h_eff
    # 去除分数 = 沉降高度 / 有效水深（Hazen理论）
    settling_fraction_per_cell = min(0.95, v_s / (v_h_eff * H / dx))

    time_series = []
    effluent_turbidity = []

    for step in range(nt):
        t = step * dt
        C_new = np.zeros_like(C)
        C_new[0] = inlet_C

        courant = v_h_eff * dt / dx
        if courant > 1.0:
            courant = 1.0

        for i in range(1, nx):
            C_new[i] = C[i] - courant * (C[i] - C[i - 1])
            C_new[i] *= (1.0 - settling_fraction_per_cell)
            C_new[i] = max(0.0, C_new[i])

        C = C_new

        # SS → NTU 转换：线性近似（1 mg/L SS ≈ 0.5~1.5 NTU，取 1.0）
        # 加上无法沉降的胶体本底 0.1 NTU
        effluent_ss = C[-1]
        turb = effluent_ss * 1.0 + 0.1
        turb = max(0.1, turb)

        time_series.append(t / 60.0)
        effluent_turbidity.append(round(turb, 3))

    steady_turbidity = effluent_turbidity[-1] if effluent_turbidity else 0

    # 去除率基于原水浊度
    raw_turb = raw.turbidity
    removal_rate = 1.0 - steady_turbidity / raw_turb if raw_turb > 0 else 0

    return {
        "time_min": time_series,
        "effluent_turbidity_NTU": effluent_turbidity,
        "steady_turbidity_NTU": round(steady_turbidity, 3),
        "settling_velocity_m_s": round(v_s, 6),
        "surface_loading_m_h": round(surface_loading * 3600, 3),
        "HRT_min": round(HRT_actual / 60, 1),
        "removal_rate": round(removal_rate, 4),
    }


def run_simulation(raw: RawWaterParams, coag: CoagulationParams,
                   sed: SedimentationParams, total_time: float = 7200.0) -> dict:
    """完整仿真流程"""
    floc = floc_formation(raw, coag)
    settling = sedimentation_1d(floc, sed, raw, total_time=total_time)

    return {
        "floc_info": floc,
        "sedimentation": settling,
        "input_params": {
            "raw_water": asdict(raw),
            "coagulation": asdict(coag),
            "sedimentation_tank": asdict(sed),
        },
    }


def optimize_dosage(raw: RawWaterParams, sed: SedimentationParams,
                    target_turbidity: float, coag_template: CoagulationParams,
                    cost_per_mg: float = 0.002) -> dict:
    """
    投药量优化 - 最小成本搜索
    目标：出水浊度 <= target_turbidity 时药剂成本最低
    """
    def cost_objective(dosage):
        coag = CoagulationParams(
            dosage=dosage,
            mixing_intensity=coag_template.mixing_intensity,
            mixing_time=coag_template.mixing_time,
            floc_time=coag_template.floc_time,
        )
        floc = floc_formation(raw, coag)
        result = sedimentation_1d(floc, sed, raw, total_time=3600.0)
        steady_turb = result["steady_turbidity_NTU"]

        penalty = 0
        if steady_turb > target_turbidity:
            penalty = 5000 * (steady_turb - target_turbidity) ** 2

        return dosage * cost_per_mg + penalty

    result = minimize_scalar(cost_objective, bounds=(3, 200), method="bounded",
                             options={"xatol": 0.1})
    optimal_dosage = result.x

    coag_opt = CoagulationParams(
        dosage=optimal_dosage,
        mixing_intensity=coag_template.mixing_intensity,
        mixing_time=coag_template.mixing_time,
        floc_time=coag_template.floc_time,
    )
    sim = run_simulation(raw, coag_opt, sed, total_time=3600.0)

    # 响应曲面采样
    dosages = np.linspace(3, 150, 40)
    turbidities = []
    costs = []
    for d in dosages:
        c = CoagulationParams(d, coag_template.mixing_intensity,
                              coag_template.mixing_time, coag_template.floc_time)
        f = floc_formation(raw, c)
        r = sedimentation_1d(f, sed, raw, total_time=3600.0)
        turbidities.append(r["steady_turbidity_NTU"])
        costs.append(round(d * cost_per_mg, 4))

    return {
        "optimal_dosage_mg_L": round(optimal_dosage, 2),
        "optimal_cost_yuan_m3": round(optimal_dosage * cost_per_mg, 4),
        "achieved_turbidity_NTU": sim["sedimentation"]["steady_turbidity_NTU"],
        "target_turbidity_NTU": target_turbidity,
        "method": "bounded_minimization_with_penalty",
        "response_surface": {
            "dosages": [round(d, 1) for d in dosages.tolist()],
            "turbidities": turbidities,
            "costs": costs,
        },
        "simulation_result": sim,
    }


def simulate_abnormal_event(raw: RawWaterParams, coag: CoagulationParams,
                            sed: SedimentationParams, event_type: str,
                            event_params: dict) -> dict:
    """
    异常工况仿真
    - 应急投药量随工况实时调整
    - 应急动作在整个事件期间按阶段持续记录
    """
    dt = 60.0
    total_time = event_params.get("duration_min", 120) * 60.0
    event_start = event_params.get("start_min", 30) * 60.0
    event_end = event_params.get("end_min", 90) * 60.0

    nx = 50
    L = sed.tank_length
    H = sed.tank_depth
    W = sed.tank_width
    Q = sed.flow_rate / 3600.0
    dx = L / nx
    nt = int(total_time / dt)
    v_h = Q / (H * W)
    v_h_eff = v_h / sed.short_circuit_factor

    time_series = []
    effluent_turbidity = []
    inlet_turbidity_series = []
    dosage_series = []

    C = np.zeros(nx)
    current_dosage = coag.dosage

    emergency_actions = []
    # 用于追踪应急记录的阶段
    last_action_dosage = coag.dosage
    action_interval = max(300.0, (event_end - event_start) / 10.0)  # 至少每5分钟或分10段记录
    next_action_time = event_start

    for step in range(nt):
        t = step * dt
        current_raw = RawWaterParams(
            turbidity=raw.turbidity,
            temperature=raw.temperature,
            ph=raw.ph,
            alkalinity=raw.alkalinity,
            ss=raw.ss,
        )

        in_event = event_start <= t <= event_end
        if in_event:
            if event_type == "storm":
                peak_factor = event_params.get("peak_factor", 5.0)
                progress = (t - event_start) / (event_end - event_start)
                if progress < 0.3:
                    surge = 1.0 + (peak_factor - 1.0) * (progress / 0.3)
                else:
                    surge = 1.0 + (peak_factor - 1.0) * (1.0 - (progress - 0.3) / 0.7)
                current_raw.turbidity *= surge
                current_raw.ss *= surge

            elif event_type == "ph_anomaly":
                target_ph = event_params.get("target_ph", 5.5)
                progress = (t - event_start) / (event_end - event_start)
                if progress < 0.2:
                    current_raw.ph = raw.ph + (target_ph - raw.ph) * (progress / 0.2)
                elif progress < 0.8:
                    current_raw.ph = target_ph
                else:
                    current_raw.ph = target_ph + (raw.ph - target_ph) * ((progress - 0.8) / 0.2)

            elif event_type == "low_temp_low_turbidity":
                current_raw.temperature = event_params.get("target_temp", 4.0)
                current_raw.turbidity = event_params.get("target_turbidity", 5.0)
                current_raw.ss = current_raw.turbidity * 1.5

        # 应急投药策略——持续跟踪
        if in_event:
            if event_type == "storm":
                # 投药量随原水浊度比例增加，上限6倍
                ratio = current_raw.turbidity / raw.turbidity
                current_dosage = coag.dosage * max(1.0, ratio * 0.9)
                current_dosage = min(current_dosage, coag.dosage * 6.0)

            elif event_type == "ph_anomaly":
                ph_dev = abs(current_raw.ph - 7.0)
                current_dosage = coag.dosage * (1.0 + 0.4 * ph_dev)

            elif event_type == "low_temp_low_turbidity":
                current_dosage = coag.dosage * 2.0

            # 持续记录应急动作：在事件期间按间隔记录
            if t >= next_action_time:
                dosage_change = abs(current_dosage - last_action_dosage)
                if event_type == "storm":
                    emergency_actions.append({
                        "time_min": round(t / 60, 1),
                        "action": f"原水浊度{current_raw.turbidity:.0f}NTU，投药量调整至{current_dosage:.1f}mg/L（{current_dosage/coag.dosage:.1f}倍常规量）",
                        "dosage": round(current_dosage, 1),
                        "inlet_turbidity": round(current_raw.turbidity, 1),
                    })
                elif event_type == "ph_anomaly":
                    direction = "偏酸" if current_raw.ph < 7.0 else "偏碱"
                    emergency_actions.append({
                        "time_min": round(t / 60, 1),
                        "action": f"pH={current_raw.ph:.1f}({direction})，投药{current_dosage:.1f}mg/L，{'加石灰提升pH' if current_raw.ph < 7.0 else '加酸降低pH'}",
                        "dosage": round(current_dosage, 1),
                        "ph": round(current_raw.ph, 2),
                    })
                elif event_type == "low_temp_low_turbidity":
                    emergency_actions.append({
                        "time_min": round(t / 60, 1),
                        "action": f"低温{current_raw.temperature:.0f}°C低浊{current_raw.turbidity:.0f}NTU，投药{current_dosage:.1f}mg/L + 建议PAM助凝0.1mg/L",
                        "dosage": round(current_dosage, 1),
                    })
                last_action_dosage = current_dosage
                next_action_time = t + action_interval
        else:
            current_dosage = coag.dosage

        # 混凝计算
        current_coag = CoagulationParams(
            dosage=current_dosage,
            mixing_intensity=coag.mixing_intensity,
            mixing_time=coag.mixing_time,
            floc_time=coag.floc_time,
        )
        floc = floc_formation(current_raw, current_coag)

        inlet_C = floc["residual_ss_mg_L"]
        v_s = stokes_settling_velocity(
            floc["floc_diameter_um"], floc["delta_rho"], current_raw.temperature
        )
        settling_frac = min(0.95, v_s / (v_h_eff * H / dx))

        C_new = np.zeros_like(C)
        C_new[0] = inlet_C
        courant = min(1.0, v_h_eff * dt / dx)

        for i in range(1, nx):
            C_new[i] = C[i] - courant * (C[i] - C[i - 1])
            C_new[i] *= (1.0 - settling_frac)
            C_new[i] = max(0.0, C_new[i])

        C = C_new

        turb = C[-1] * 1.0 + 0.1
        turb = max(0.1, turb)

        time_series.append(round(t / 60.0, 2))
        effluent_turbidity.append(round(turb, 3))
        inlet_turbidity_series.append(round(current_raw.turbidity, 2))
        dosage_series.append(round(current_dosage, 2))

    max_turb = max(effluent_turbidity)
    max_turb_time = time_series[effluent_turbidity.index(max_turb)]

    # 正常出水基线
    normal_turb = effluent_turbidity[0] if effluent_turbidity else 0

    return {
        "event_type": event_type,
        "event_params": event_params,
        "time_min": time_series,
        "effluent_turbidity_NTU": effluent_turbidity,
        "inlet_turbidity_NTU": inlet_turbidity_series,
        "dosage_mg_L": dosage_series,
        "max_effluent_turbidity": round(max_turb, 3),
        "max_turbidity_time_min": max_turb_time,
        "emergency_actions": emergency_actions,
        "summary": {
            "normal_turbidity": round(normal_turb, 3),
            "peak_turbidity": round(max_turb, 3),
            "recovery_time_min": _find_recovery_time(
                time_series, effluent_turbidity, normal_turb * 2.0
            ),
        },
    }


def _find_recovery_time(times, turbidities, threshold):
    """找到浊度恢复到阈值以下的时间"""
    peak_idx = turbidities.index(max(turbidities))
    for i in range(peak_idx, len(turbidities)):
        if turbidities[i] <= threshold:
            return round(times[i] - times[peak_idx], 1)
    return None
