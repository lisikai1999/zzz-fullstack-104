<template>
  <div class="abnormal-panel">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><WarningFilled /></el-icon>
              <span>异常工况触发器</span>
            </div>
          </template>
          <el-form :model="form" label-position="top" size="small">
            <el-form-item label="异常类型">
              <el-radio-group v-model="form.event_type" @change="onEventTypeChange">
                <el-radio-button value="storm">
                  <el-icon><Cloudy /></el-icon> 暴雨高浊
                </el-radio-button>
                <el-radio-button value="ph_anomaly">
                  <el-icon><Warning /></el-icon> pH异常
                </el-radio-button>
                <el-radio-button value="low_temp_low_turbidity">
                  <el-icon><Cold /></el-icon> 低温低浊
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-divider content-position="left">事件参数</el-divider>

            <template v-if="form.event_type === 'storm'">
              <el-form-item label="浊度峰值倍数">
                <el-slider v-model="form.event_params.peak_factor" :min="2" :max="20" :step="0.5" show-input />
              </el-form-item>
            </template>
            <template v-else-if="form.event_type === 'ph_anomaly'">
              <el-form-item label="目标pH">
                <el-slider v-model="form.event_params.target_ph" :min="4" :max="10" :step="0.1" show-input />
              </el-form-item>
            </template>
            <template v-else>
              <el-form-item label="温度 (°C)">
                <el-slider v-model="form.event_params.target_temp" :min="1" :max="10" :step="0.5" show-input />
              </el-form-item>
              <el-form-item label="低浊浊度 (NTU)">
                <el-slider v-model="form.event_params.target_turbidity" :min="1" :max="20" :step="0.5" show-input />
              </el-form-item>
            </template>

            <el-form-item label="事件开始 (min)">
              <el-slider v-model="form.event_params.start_min" :min="5" :max="60" show-input />
            </el-form-item>
            <el-form-item label="事件结束 (min)">
              <el-slider v-model="form.event_params.end_min" :min="30" :max="180" show-input />
            </el-form-item>
            <el-form-item label="仿真总时长 (min)">
              <el-slider v-model="form.event_params.duration_min" :min="60" :max="300" :step="10" show-input />
            </el-form-item>

            <el-divider content-position="left">常规运行参数</el-divider>
            <el-form-item label="原水浊度 (NTU)">
              <el-slider v-model="form.raw_water.turbidity" :min="10" :max="200" show-input />
            </el-form-item>
            <el-form-item label="常规投药量 (mg/L)">
              <el-slider v-model="form.coagulation.dosage" :min="5" :max="100" show-input />
            </el-form-item>

            <el-form-item>
              <el-button type="danger" @click="runAbn" :loading="loading" style="width:100%">
                <el-icon><VideoPlay /></el-icon>
                触发异常仿真
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <!-- 趋势图 -->
        <el-card shadow="never" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>异常工况水质响应</span>
              <el-tag type="danger" size="small" style="margin-left:auto">
                峰值浊度: {{ result.max_effluent_turbidity }} NTU @ {{ result.max_turbidity_time_min }} min
              </el-tag>
            </div>
          </template>
          <v-chart :option="trendChart" style="height: 320px" autoresize />
        </el-card>

        <!-- 投药量变化 -->
        <el-card shadow="never" style="margin-top:16px" v-if="result">
          <template #header>
            <div class="card-header">
              <el-icon><Odometer /></el-icon>
              <span>应急投药量调整曲线</span>
            </div>
          </template>
          <v-chart :option="dosageChart" style="height: 250px" autoresize />
        </el-card>

        <!-- 应急措施 -->
        <el-card shadow="never" style="margin-top:16px" v-if="result && result.emergency_actions.length">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>应急投药方案</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(action, idx) in result.emergency_actions"
              :key="idx"
              :timestamp="action.time_min + ' min'"
              type="danger"
              placement="top"
            >
              {{ action.action }}
            </el-timeline-item>
          </el-timeline>
          <el-alert
            v-if="result.summary.recovery_time_min"
            :title="`出水浊度恢复时间: ${result.summary.recovery_time_min} min`"
            type="info"
            show-icon
            :closable="false"
          />
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
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkAreaComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { runAbnormalEvent } from '../api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkAreaComponent])

const loading = ref(false)
const result = ref(null)

const form = ref({
  raw_water: { turbidity: 50, temperature: 20, ph: 7.2, alkalinity: 120, ss: 60 },
  coagulation: { dosage: 30, mixing_intensity: 300, mixing_time: 60, floc_time: 15 },
  sedimentation: { tank_length: 30, tank_depth: 3.5, tank_width: 6, flow_rate: 500, short_circuit_factor: 0.7 },
  event_type: 'storm',
  event_params: { duration_min: 150, start_min: 30, end_min: 90, peak_factor: 5.0 },
})

function onEventTypeChange(type) {
  if (type === 'storm') {
    form.value.event_params = { duration_min: 150, start_min: 30, end_min: 90, peak_factor: 5.0 }
  } else if (type === 'ph_anomaly') {
    form.value.event_params = { duration_min: 150, start_min: 30, end_min: 90, target_ph: 5.5 }
  } else {
    form.value.event_params = { duration_min: 180, start_min: 30, end_min: 150, target_temp: 4.0, target_turbidity: 5.0 }
  }
}

const trendChart = computed(() => {
  if (!result.value) return {}
  const d = result.value
  const step = Math.max(1, Math.floor(d.time_min.length / 150))
  const times = d.time_min.filter((_, i) => i % step === 0)
  const effluent = d.effluent_turbidity_NTU.filter((_, i) => i % step === 0)
  const inlet = d.inlet_turbidity_NTU.filter((_, i) => i % step === 0)

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['原水浊度', '出水浊度'] },
    grid: { left: 60, right: 30, top: 40, bottom: 50 },
    dataZoom: [{ type: 'inside' }],
    xAxis: { type: 'category', name: '时间 (min)', data: times },
    yAxis: { type: 'value', name: '浊度 (NTU)' },
    series: [
      {
        name: '原水浊度',
        type: 'line',
        smooth: true,
        data: inlet,
        lineStyle: { color: '#e53935', width: 2 },
        areaStyle: { color: 'rgba(229,57,53,0.05)' },
      },
      {
        name: '出水浊度',
        type: 'line',
        smooth: true,
        data: effluent,
        lineStyle: { color: '#1a73e8', width: 2 },
        areaStyle: { color: 'rgba(26,115,232,0.1)' },
      },
    ],
  }
})

const dosageChart = computed(() => {
  if (!result.value) return {}
  const d = result.value
  const step = Math.max(1, Math.floor(d.time_min.length / 150))
  const times = d.time_min.filter((_, i) => i % step === 0)
  const dosages = d.dosage_mg_L.filter((_, i) => i % step === 0)

  return {
    tooltip: { trigger: 'axis', formatter: '{b} min<br/>投药量: {c} mg/L' },
    grid: { left: 60, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'category', name: '时间 (min)', data: times },
    yAxis: { type: 'value', name: '投药量 (mg/L)' },
    series: [{
      type: 'line',
      smooth: true,
      data: dosages,
      lineStyle: { color: '#43a047', width: 2 },
      areaStyle: { color: 'rgba(67,160,71,0.15)' },
    }],
  }
})

async function runAbn() {
  loading.value = true
  try {
    const res = await runAbnormalEvent(form.value)
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
</style>
