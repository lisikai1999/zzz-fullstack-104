"""
API 路由 - 仿真、优化、异常工况
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from models import (
    RawWaterParams, CoagulationParams, SedimentationParams,
    run_simulation, optimize_dosage, simulate_abnormal_event,
)
from database import save_simulation, save_optimization, get_history

router = APIRouter()


class RawWaterInput(BaseModel):
    turbidity: float = Field(default=50.0, ge=0.1, le=5000, description="原水浊度 NTU")
    temperature: float = Field(default=20.0, ge=0.5, le=40, description="水温 °C")
    ph: float = Field(default=7.2, ge=4.0, le=10.0, description="pH")
    alkalinity: float = Field(default=120.0, ge=10, le=500, description="碱度 mg/L")
    ss: float = Field(default=60.0, ge=1, le=6000, description="悬浮物 mg/L")


class CoagulationInput(BaseModel):
    dosage: float = Field(default=30.0, ge=1, le=200, description="投药量 mg/L")
    mixing_intensity: float = Field(default=300.0, ge=50, le=1000, description="搅拌强度 G (s⁻¹)")
    mixing_time: float = Field(default=60.0, ge=10, le=300, description="混合时间 s")
    floc_time: float = Field(default=15.0, ge=5, le=60, description="絮凝时间 min")


class SedimentationInput(BaseModel):
    tank_length: float = Field(default=30.0, ge=5, le=100, description="池长 m")
    tank_depth: float = Field(default=3.5, ge=1, le=8, description="有效水深 m")
    tank_width: float = Field(default=6.0, ge=2, le=30, description="池宽 m")
    flow_rate: float = Field(default=500.0, ge=10, le=5000, description="流量 m³/h")
    short_circuit_factor: float = Field(default=0.7, ge=0.2, le=1.0, description="短流系数")


class SimulationRequest(BaseModel):
    raw_water: RawWaterInput = RawWaterInput()
    coagulation: CoagulationInput = CoagulationInput()
    sedimentation: SedimentationInput = SedimentationInput()
    total_time_min: float = Field(default=120, ge=10, le=480, description="仿真总时间 min")


class OptimizationRequest(BaseModel):
    raw_water: RawWaterInput = RawWaterInput()
    sedimentation: SedimentationInput = SedimentationInput()
    coagulation_template: CoagulationInput = CoagulationInput()
    target_turbidity: float = Field(default=1.0, ge=0.1, le=10.0, description="目标出水浊度 NTU")
    cost_per_mg: float = Field(default=0.002, ge=0.0001, le=0.1, description="药剂单价 元/(mg·L)")


class AbnormalEventRequest(BaseModel):
    raw_water: RawWaterInput = RawWaterInput()
    coagulation: CoagulationInput = CoagulationInput()
    sedimentation: SedimentationInput = SedimentationInput()
    event_type: str = Field(description="异常类型: storm / ph_anomaly / low_temp_low_turbidity")
    event_params: Dict[str, Any] = Field(default_factory=lambda: {
        "duration_min": 120,
        "start_min": 30,
        "end_min": 90,
        "peak_factor": 5.0,
    })


@router.post("/simulate")
async def simulate(req: SimulationRequest):
    """运行正常工况仿真"""
    raw = RawWaterParams(**req.raw_water.model_dump())
    coag = CoagulationParams(**req.coagulation.model_dump())
    sed = SedimentationParams(**req.sedimentation.model_dump())

    result = run_simulation(raw, coag, sed, total_time=req.total_time_min * 60)

    await save_simulation(req.model_dump(), result, record_type="normal")
    return result


@router.post("/optimize")
async def optimize(req: OptimizationRequest):
    """投药量优化"""
    raw = RawWaterParams(**req.raw_water.model_dump())
    sed = SedimentationParams(**req.sedimentation.model_dump())
    coag_tmpl = CoagulationParams(**req.coagulation_template.model_dump())

    result = optimize_dosage(raw, sed, req.target_turbidity, coag_tmpl, req.cost_per_mg)

    await save_optimization(
        req.target_turbidity,
        req.raw_water.model_dump(),
        result["optimal_dosage_mg_L"],
        result["optimal_cost_yuan_m3"],
        result["method"],
    )
    return result


@router.post("/abnormal")
async def abnormal_event(req: AbnormalEventRequest):
    """异常工况仿真"""
    if req.event_type not in ("storm", "ph_anomaly", "low_temp_low_turbidity"):
        raise HTTPException(400, "event_type 必须为 storm / ph_anomaly / low_temp_low_turbidity")

    raw = RawWaterParams(**req.raw_water.model_dump())
    coag = CoagulationParams(**req.coagulation.model_dump())
    sed = SedimentationParams(**req.sedimentation.model_dump())

    result = simulate_abnormal_event(raw, coag, sed, req.event_type, req.event_params)

    await save_simulation(req.model_dump(), result, record_type=f"abnormal_{req.event_type}")
    return result


@router.get("/history")
async def history(limit: int = 50):
    """获取历史仿真记录"""
    records = await get_history(limit)
    return {"records": records}


@router.get("/defaults")
async def defaults():
    """获取默认参数"""
    return {
        "raw_water": RawWaterInput().model_dump(),
        "coagulation": CoagulationInput().model_dump(),
        "sedimentation": SedimentationInput().model_dump(),
        "event_presets": {
            "storm": {
                "description": "暴雨突发高浊",
                "params": {
                    "duration_min": 120,
                    "start_min": 30,
                    "end_min": 90,
                    "peak_factor": 5.0,
                },
            },
            "ph_anomaly": {
                "description": "pH异常偏低",
                "params": {
                    "duration_min": 120,
                    "start_min": 30,
                    "end_min": 90,
                    "target_ph": 5.5,
                },
            },
            "low_temp_low_turbidity": {
                "description": "低温低浊水",
                "params": {
                    "duration_min": 180,
                    "start_min": 30,
                    "end_min": 150,
                    "target_temp": 4.0,
                    "target_turbidity": 5.0,
                },
            },
        },
    }
