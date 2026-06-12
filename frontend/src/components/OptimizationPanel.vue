<template>
  <div class="optimization-panel">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Aim /></el-icon>
              <span>优化参数设置</span>
            </div>
          </template>
          <el-form :model="form" label-position="top" size="small">
            <el-form-item label="目标出水浊度 (NTU)">
              <el-input-number v-model="form.target_turbidity" :min="0.1" :max="10" :step="0.1" style="width:100%" />
            </el-form-item>
            <el-form-item label="药剂单价 (元/mg·L)">
              <el-input-number v-model="form.cost_per_mg" :min="0.0001" :max="0.1" :step="0.0005" :precision="4" style="width:100%" />
            </el-form-item>

            <el-divider content-position="left">原水条件</el-divider>
            <el-form-item label="浊度 (NTU)">
              <el-slider v-model="form.raw_water.turbidity" :min="5" :max="1000" show-input />
            </el-form-item>
            <el-form-item label="温度 (°C)">
              <el-slider v-model="form.raw_water.temperature" :min="1" :max="35" :step="0.5" show-input />
            </el-form-item>
            <el-form-item label="pH">
              <el-slider v-model="form.raw_water.ph" :min="5" :max="9" :step="0.1" show-input />
            </el-form-item>
            <el-form-item label="悬浮物 (mg/L)">
              <el-slider v-model="form.raw_water.ss" :min="5" :max="1500" show-input />
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="runOpt" :loading="loading" style="width:100%">
                <el-icon><Promotion /></el-icon>
                寻找最优投药量
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <!-- 优化结果 -->
        <el-card shadow="never" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><Trophy /></el-icon>
              <span>优化结果</span>
            </div>
          </template>
          <el-row :gutter="16" class="result-stats">
            <el-col :span="6">
              <div class="stat-box optimal">
                <div class="stat-value">{{ result.optimal_dosage_mg_L }}</div>
                <div class="stat-label">最优投药量 (mg/L)</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box cost">
                <div class="stat-value">{{ result.optimal_cost_yuan_m3 }}</div>
                <div class="stat-label">药剂成本 (元/m³)</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box turbidity">
                <div class="stat-value">{{ result.achieved_turbidity_NTU }}</div>
                <div class="stat-label">实际出水浊度 (NTU)</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box target">
                <div class="stat-value">{{ result.target_turbidity_NTU }}</div>
                <div class="stat-label">目标浊度 (NTU)</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 响应曲面图 -->
        <el-card shadow="never" style="margin-top:16px" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>响应曲面 - 投药量 vs 出水浊度 / 成本</span>
            </div>
          </template>
          <v-chart :option="surfaceChart" style="height: 350px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { runOptimization } from '../api'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent])

const loading = ref(false)
const result = ref(null)

const form = ref({
  raw_water: { turbidity: 80, temperature: 18, ph: 7.0, alkalinity: 120, ss: 100 },
  sedimentation: { tank_length: 30, tank_depth: 3.5, tank_width: 6, flow_rate: 500, short_circuit_factor: 0.7 },
  coagulation_template: { dosage: 30, mixing_intensity: 300, mixing_time: 60, floc_time: 15 },
  target_turbidity: 1.0,
  cost_per_mg: 0.002,
})

const surfaceChart = computed(() => {
  if (!result.value) return {}
  const rs = result.value.response_surface
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['出水浊度', '药剂成本'], top: 0 },
    grid: { left: 60, right: 60, top: 40, bottom: 40 },
    xAxis: { type: 'category', name: '投药量 (mg/L)', data: rs.dosages },
    yAxis: [
      { type: 'value', name: '浊度 (NTU)', position: 'left', min: 0 },
      { type: 'value', name: '成本 (元/m³)', position: 'right', min: 0 },
    ],
    series: [
      {
        name: '出水浊度',
        type: 'line',
        smooth: true,
        data: rs.turbidities,
        lineStyle: { color: '#1a73e8', width: 2 },
        markLine: {
          data: [
            { yAxis: result.value.target_turbidity_NTU, name: '目标浊度', lineStyle: { color: '#e53935', type: 'dashed' } },
          ],
        },
      },
      {
        name: '药剂成本',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: rs.costs,
        lineStyle: { color: '#43a047', width: 2 },
        markLine: {
          data: [
            { xAxis: rs.dosages.indexOf(rs.dosages.reduce((a, b) => Math.abs(b - result.value.optimal_dosage_mg_L) < Math.abs(a - result.value.optimal_dosage_mg_L) ? b : a)), name: '最优点', lineStyle: { color: '#ff6f00' } },
          ],
        },
      },
    ],
  }
})

async function runOpt() {
  loading.value = true
  try {
    const res = await runOptimization(form.value)
    result.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.result-stats { margin-top: 8px; }
.stat-box {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}
.stat-box.optimal { background: #e8f5e9; border-color: #66bb6a; }
.stat-box.cost { background: #fff3e0; border-color: #ffa726; }
.stat-box.turbidity { background: #e3f2fd; border-color: #42a5f5; }
.stat-box.target { background: #fce4ec; border-color: #ef5350; }
.stat-value { font-size: 24px; font-weight: 700; color: #333; }
.stat-label { font-size: 12px; color: #666; margin-top: 4px; }
</style>
