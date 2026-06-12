<template>
  <div class="history-panel">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span>仿真历史记录</span>
          <el-button size="small" @click="loadHistory" :loading="loading" style="margin-left:auto">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <el-table :data="records" stripe style="width: 100%" empty-text="暂无记录，运行仿真后自动保存">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.record_type)" size="small">
              {{ typeLabel(row.record_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="主要参数">
          <template #default="{ row }">
            {{ summarizeParams(row.params) }}
          </template>
        </el-table-column>
        <el-table-column label="关键结果" width="200">
          <template #default="{ row }">
            {{ summarizeResults(row.results) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="dialogVisible" title="仿真详情" width="700px">
      <div v-if="selectedRecord">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="记录ID">{{ selectedRecord.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(selectedRecord.record_type) }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(selectedRecord.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>输入参数</el-divider>
        <pre class="json-block">{{ formatJson(selectedRecord.params) }}</pre>

        <el-divider>仿真结果</el-divider>
        <pre class="json-block">{{ formatResultSummary(selectedRecord.results) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHistory } from '../api'

const loading = ref(false)
const records = ref([])
const dialogVisible = ref(false)
const selectedRecord = ref(null)

onMounted(() => loadHistory())

async function loadHistory() {
  loading.value = true
  try {
    const res = await getHistory(100)
    records.value = res.data.records
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function typeLabel(type) {
  const map = {
    normal: '正常仿真',
    abnormal_storm: '暴雨工况',
    abnormal_ph_anomaly: 'pH异常',
    abnormal_low_temp_low_turbidity: '低温低浊',
  }
  return map[type] || type
}

function typeTag(type) {
  if (type === 'normal') return 'success'
  if (type.startsWith('abnormal')) return 'danger'
  return 'info'
}

function formatTime(iso) {
  if (!iso) return '-'
  return iso.replace('T', ' ').substring(0, 19)
}

function summarizeParams(paramsStr) {
  try {
    const p = JSON.parse(paramsStr)
    const rw = p.raw_water
    if (rw) {
      return `浊度${rw.turbidity}NTU pH${rw.ph} ${rw.temperature}°C`
    }
    return '-'
  } catch { return '-' }
}

function summarizeResults(resultsStr) {
  try {
    const r = JSON.parse(resultsStr)
    if (r.sedimentation && r.sedimentation.steady_turbidity_NTU !== undefined) {
      return `出水${r.sedimentation.steady_turbidity_NTU}NTU 去除${(r.sedimentation.removal_rate * 100).toFixed(1)}%`
    }
    if (r.max_effluent_turbidity !== undefined) {
      return `峰值${r.max_effluent_turbidity}NTU @${r.max_turbidity_time_min}min`
    }
    return '-'
  } catch { return '-' }
}

function showDetail(row) {
  selectedRecord.value = row
  dialogVisible.value = true
}

function formatJson(str) {
  try {
    const obj = JSON.parse(str)
    // Remove verbose arrays for readability
    const clean = { ...obj }
    return JSON.stringify(clean, null, 2)
  } catch { return str }
}

function formatResultSummary(str) {
  try {
    const obj = JSON.parse(str)
    const summary = {}
    if (obj.floc_info) summary['混凝'] = obj.floc_info
    if (obj.sedimentation) {
      const { time_min, effluent_turbidity_NTU, ...rest } = obj.sedimentation
      summary['沉淀'] = rest
    }
    if (obj.max_effluent_turbidity !== undefined) {
      const { time_min, effluent_turbidity_NTU, inlet_turbidity_NTU, dosage_mg_L, ...rest } = obj
      summary['异常工况'] = rest
    }
    return JSON.stringify(summary, null, 2)
  } catch { return str }
}
</script>

<style scoped>
.card-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.json-block {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
