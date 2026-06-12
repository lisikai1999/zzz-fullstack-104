<template>
  <div class="simulation-panel">
    <!-- 工艺流程图 - SVG 工程图 -->
    <el-card class="flow-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon><Connection /></el-icon>
          <span>工艺流程图</span>
          <el-tag v-if="result" type="success" size="small" style="margin-left:auto">
            去除率: {{ (result.sedimentation.removal_rate * 100).toFixed(1) }}%
          </el-tag>
        </div>
      </template>
      <div class="svg-container">
        <svg viewBox="0 0 960 260" xmlns="http://www.w3.org/2000/svg" class="process-svg">
          <!-- 背景管道 -->
          <line x1="0" y1="140" x2="80" y2="140" stroke="#5c9bd6" stroke-width="6" />
          <line x1="170" y1="140" x2="260" y2="140" stroke="#5c9bd6" stroke-width="6" />
          <line x1="380" y1="140" x2="440" y2="140" stroke="#5c9bd6" stroke-width="6" />
          <line x1="720" y1="140" x2="780" y2="140" stroke="#5c9bd6" stroke-width="6" />
          <line x1="880" y1="140" x2="960" y2="140" stroke="#26a69a" stroke-width="6" />

          <!-- 流向箭头 -->
          <polygon points="168,135 178,140 168,145" fill="#5c9bd6"/>
          <polygon points="258,135 268,140 258,145" fill="#5c9bd6"/>
          <polygon points="438,135 448,140 438,145" fill="#5c9bd6"/>
          <polygon points="778,135 788,140 778,145" fill="#26a69a"/>

          <!-- 1. 原水取水口 -->
          <g transform="translate(80,100)">
            <rect x="0" y="0" width="90" height="80" rx="4" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
            <path d="M10,60 Q25,45 40,60 Q55,75 70,60 Q80,50 85,60" fill="none" stroke="#1976d2" stroke-width="2" opacity="0.6"/>
            <path d="M10,50 Q25,35 40,50 Q55,65 70,50 Q80,40 85,50" fill="none" stroke="#1976d2" stroke-width="1.5" opacity="0.4"/>
            <text x="45" y="20" text-anchor="middle" font-size="11" font-weight="600" fill="#1565c0">原水</text>
          </g>
          <!-- 原水参数标注 -->
          <g transform="translate(80,185)">
            <text x="45" y="12" text-anchor="middle" font-size="9" fill="#555">{{ form.raw_water.turbidity }} NTU</text>
            <text x="45" y="24" text-anchor="middle" font-size="9" fill="#555">pH {{ form.raw_water.ph }} | {{ form.raw_water.temperature }}°C</text>
          </g>

          <!-- 2. 快速混合池（搅拌器符号） -->
          <g transform="translate(260,95)">
            <rect x="0" y="0" width="120" height="90" rx="4" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
            <!-- 搅拌器 -->
            <line x1="60" y1="8" x2="60" y2="55" stroke="#e65100" stroke-width="2.5"/>
            <line x1="40" y1="55" x2="80" y2="55" stroke="#e65100" stroke-width="3"/>
            <line x1="42" y1="65" x2="78" y2="65" stroke="#e65100" stroke-width="2.5"/>
            <!-- 加药管 -->
            <line x1="95" y1="0" x2="95" y2="-25" stroke="#43a047" stroke-width="2.5" stroke-dasharray="4,2"/>
            <circle cx="95" cy="-28" r="5" fill="#43a047"/>
            <text x="95" y="-36" text-anchor="middle" font-size="9" fill="#2e7d32" font-weight="600">PAC</text>
            <text x="60" y="82" text-anchor="middle" font-size="10" font-weight="600" fill="#e65100">混合+加药</text>
          </g>
          <!-- 加药参数 -->
          <g transform="translate(260,190)">
            <text x="60" y="12" text-anchor="middle" font-size="9" fill="#555">PAC {{ form.coagulation.dosage }} mg/L</text>
            <text x="60" y="24" text-anchor="middle" font-size="9" fill="#555">G={{ form.coagulation.mixing_intensity }}s⁻¹ | {{ form.coagulation.floc_time }}min</text>
          </g>

          <!-- 3. 平流沉淀池（梯形池体+刮泥机） -->
          <g transform="translate(440,85)">
            <!-- 池体 -->
            <rect x="0" y="10" width="280" height="100" rx="2" fill="#ede7f6" stroke="#5e35b1" stroke-width="2"/>
            <!-- 水面 -->
            <line x1="5" y1="25" x2="275" y2="25" stroke="#7c4dff" stroke-width="1" stroke-dasharray="6,3"/>
            <!-- 矾花沉降示意 -->
            <circle cx="50" cy="45" r="4" fill="#a5d6a7" opacity="0.8"/>
            <circle cx="80" cy="55" r="5" fill="#81c784" opacity="0.7"/>
            <circle cx="120" cy="65" r="6" fill="#66bb6a" opacity="0.7"/>
            <circle cx="160" cy="78" r="5" fill="#4caf50" opacity="0.6"/>
            <circle cx="70" cy="72" r="3" fill="#a5d6a7" opacity="0.6"/>
            <circle cx="110" cy="80" r="4" fill="#81c784" opacity="0.5"/>
            <circle cx="200" cy="85" r="4" fill="#4caf50" opacity="0.5"/>
            <!-- 污泥层 -->
            <rect x="5" y="90" width="270" height="15" rx="2" fill="#8d6e63" opacity="0.4"/>
            <!-- 刮泥机 -->
            <line x1="30" y1="90" x2="50" y2="105" stroke="#5d4037" stroke-width="2"/>
            <line x1="130" y1="90" x2="150" y2="105" stroke="#5d4037" stroke-width="2"/>
            <line x1="230" y1="90" x2="250" y2="105" stroke="#5d4037" stroke-width="2"/>
            <!-- 排泥口 -->
            <rect x="125" y="105" width="30" height="8" fill="#5d4037" opacity="0.6" rx="1"/>
            <!-- 出水堰 -->
            <rect x="260" y="20" width="15" height="40" fill="#b39ddb" stroke="#5e35b1" stroke-width="1"/>
            <path d="M262,25 L262,55 M267,25 L267,55 M272,25 L272,55" stroke="#5e35b1" stroke-width="0.5" opacity="0.5"/>
            <text x="140" y="7" text-anchor="middle" font-size="11" font-weight="600" fill="#4527a0">平流沉淀池</text>
          </g>
          <!-- 沉淀池参数 -->
          <g transform="translate(440,200)">
            <text x="140" y="12" text-anchor="middle" font-size="9" fill="#555">{{ form.sedimentation.tank_length }}m × {{ form.sedimentation.tank_width }}m × {{ form.sedimentation.tank_depth }}m | Q={{ form.sedimentation.flow_rate }}m³/h</text>
            <text x="140" y="24" text-anchor="middle" font-size="9" fill="#555">短流系数 {{ form.sedimentation.short_circuit_factor }} | 表面负荷 {{ result ? result.sedimentation.surface_loading_m_h : '-' }} m/h</text>
          </g>

          <!-- 4. 出水 -->
          <g transform="translate(790,100)">
            <rect x="0" y="0" width="90" height="80" rx="4" fill="#e0f2f1" stroke="#00897b" stroke-width="2"/>
            <!-- 清水标志 -->
            <circle cx="45" cy="40" r="20" fill="none" stroke="#26a69a" stroke-width="2"/>
            <path d="M35,40 L42,47 L55,33" stroke="#26a69a" stroke-width="3" fill="none"/>
            <text x="45" y="72" text-anchor="middle" font-size="11" font-weight="600" fill="#00695c">出水</text>
          </g>
          <!-- 出水参数 -->
          <g transform="translate(790,185)">
            <text x="45" y="12" text-anchor="middle" font-size="10" :fill="effTurbColor" font-weight="600">
              {{ result ? result.sedimentation.steady_turbidity_NTU : '-' }} NTU
            </text>
            <text x="45" y="26" text-anchor="middle" font-size="9" fill="#555">
              {{ result ? '去除' + (result.sedimentation.removal_rate * 100).toFixed(1) + '%' : '待仿真' }}
            </text>
          </g>
        </svg>
      </div>
    </el-card>

    <el-row :gutter="16">
      <!-- 参数面板 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>仿真参数</span>
            </div>
          </template>
          <el-form :model="form" label-position="top" size="small">
            <el-divider content-position="left">原水水质</el-divider>
            <el-form-item label="浊度 (NTU)">
              <el-slider v-model="form.raw_water.turbidity" :min="1" :max="2000" :step="1" show-input />
            </el-form-item>
            <el-form-item label="温度 (°C)">
              <el-slider v-model="form.raw_water.temperature" :min="1" :max="35" :step="0.5" show-input />
            </el-form-item>
            <el-form-item label="pH">
              <el-slider v-model="form.raw_water.ph" :min="4" :max="10" :step="0.1" show-input />
            </el-form-item>
            <el-form-item label="悬浮物 (mg/L)">
              <el-slider v-model="form.raw_water.ss" :min="1" :max="3000" :step="1" show-input />
            </el-form-item>
            <el-form-item label="碱度 (mg/L)">
              <el-slider v-model="form.raw_water.alkalinity" :min="10" :max="400" :step="5" show-input />
            </el-form-item>

            <el-divider content-position="left">投药参数</el-divider>
            <el-form-item label="投药量 PAC (mg/L)">
              <el-slider v-model="form.coagulation.dosage" :min="5" :max="150" :step="1" show-input />
            </el-form-item>
            <el-form-item label="搅拌强度 G (s⁻¹)">
              <el-slider v-model="form.coagulation.mixing_intensity" :min="100" :max="800" :step="10" show-input />
            </el-form-item>
            <el-form-item label="絮凝时间 (min)">
              <el-slider v-model="form.coagulation.floc_time" :min="5" :max="40" :step="1" show-input />
            </el-form-item>

            <el-divider content-position="left">沉淀池</el-divider>
            <el-form-item label="池长 (m)">
              <el-slider v-model="form.sedimentation.tank_length" :min="10" :max="80" :step="1" show-input />
            </el-form-item>
            <el-form-item label="流量 (m³/h)">
              <el-slider v-model="form.sedimentation.flow_rate" :min="50" :max="3000" :step="10" show-input />
            </el-form-item>
            <el-form-item label="短流系数">
              <el-slider v-model="form.sedimentation.short_circuit_factor" :min="0.3" :max="1.0" :step="0.05" show-input />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="runSim" :loading="loading" style="width:100%">
                运行仿真
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 结果图表 -->
      <el-col :span="16">
        <el-card shadow="never" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>出水浊度变化曲线</span>
              <el-tag type="success" size="small" style="margin-left:auto">
                稳态浊度: {{ result.sedimentation.steady_turbidity_NTU }} NTU
              </el-tag>
            </div>
          </template>
          <v-chart :option="chartOption" style="height: 320px" autoresize />
        </el-card>

        <el-row :gutter="16" style="margin-top:16px" v-if="result">
          <el-col :span="6">
            <el-statistic title="矾花粒径 (μm)" :value="result.floc_info.floc_diameter_um" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="沉降速度 (mm/s)" :value="(result.sedimentation.settling_velocity_m_s * 1000).toFixed(2)" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="停留时间 (min)" :value="result.sedimentation.HRT_min" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="去除率 (%)" :value="(result.sedimentation.removal_rate * 100).toFixed(1)" />
          </el-col>
        </el-row>

        <el-card shadow="never" style="margin-top:16px" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>混凝效果指标</span>
            </div>
          </template>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="混凝效率">{{ (result.floc_info.coagulation_efficiency * 100).toFixed(1) }}%</el-descriptions-item>
            <el-descriptions-item label="pH影响因子">{{ result.floc_info.ph_factor }}</el-descriptions-item>
            <el-descriptions-item label="温度影响因子">{{ result.floc_info.temp_factor }}</el-descriptions-item>
            <el-descriptions-item label="Gt值">{{ result.floc_info.Gt_value }}</el-descriptions-item>
            <el-descriptions-item label="密度差 (kg/m³)">{{ result.floc_info.delta_rho }}</el-descriptions-item>
            <el-descriptions-item label="表面负荷 (m/h)">{{ result.sedimentation.surface_loading_m_h }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { runSimulation } from '../api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, MarkLineComponent])

const loading = ref(false)
const result = ref(null)

const form = ref({
  raw_water: { turbidity: 50, temperature: 20, ph: 7.2, alkalinity: 120, ss: 60 },
  coagulation: { dosage: 30, mixing_intensity: 300, mixing_time: 60, floc_time: 15 },
  sedimentation: { tank_length: 30, tank_depth: 3.5, tank_width: 6, flow_rate: 500, short_circuit_factor: 0.7 },
  total_time_min: 120,
})

const effTurbColor = computed(() => {
  if (!result.value) return '#555'
  const t = result.value.sedimentation.steady_turbidity_NTU
  if (t <= 1.0) return '#2e7d32'
  if (t <= 3.0) return '#f57c00'
  return '#c62828'
})

const chartOption = computed(() => {
  if (!result.value) return {}
  const data = result.value.sedimentation
  const step = Math.max(1, Math.floor(data.time_min.length / 120))
  return {
    tooltip: { trigger: 'axis', formatter: '{b} min<br/>浊度: {c} NTU' },
    grid: { left: 60, right: 30, top: 30, bottom: 40 },
    xAxis: { type: 'category', name: '时间 (min)', data: data.time_min.filter((_, i) => i % step === 0) },
    yAxis: { type: 'value', name: '浊度 (NTU)', min: 0 },
    series: [{
      type: 'line',
      smooth: true,
      data: data.effluent_turbidity_NTU.filter((_, i) => i % step === 0),
      lineStyle: { color: '#1a73e8', width: 2 },
      areaStyle: { color: 'rgba(26,115,232,0.1)' },
      markLine: {
        data: [{ yAxis: 1, name: '目标 1 NTU', lineStyle: { color: '#e53935', type: 'dashed' } }],
      },
    }],
  }
})

async function runSim() {
  loading.value = true
  try {
    const res = await runSimulation(form.value)
    result.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.simulation-panel { display: flex; flex-direction: column; gap: 16px; }
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.svg-container { width: 100%; overflow-x: auto; }
.process-svg { width: 100%; min-width: 700px; height: auto; }
</style>
