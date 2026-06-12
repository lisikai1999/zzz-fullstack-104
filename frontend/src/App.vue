<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>混凝沉淀仿真系统</h1>
      <span class="subtitle">投药优化 · 沉淀模拟 · 异常工况应急</span>
    </el-header>
    <el-main>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="工艺流程仿真" name="simulation">
          <SimulationPanel />
        </el-tab-pane>
        <el-tab-pane label="投药量优化" name="optimization">
          <OptimizationPanel />
        </el-tab-pane>
        <el-tab-pane label="异常工况模拟" name="abnormal">
          <AbnormalPanel />
        </el-tab-pane>
        <el-tab-pane label="历史记录" name="history">
          <HistoryPanel />
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import SimulationPanel from './components/SimulationPanel.vue'
import OptimizationPanel from './components/OptimizationPanel.vue'
import AbnormalPanel from './components/AbnormalPanel.vue'
import HistoryPanel from './components/HistoryPanel.vue'

const activeTab = ref('simulation')
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; background: #f0f2f5; }
.app-container { min-height: 100vh; }
.app-header {
  background: linear-gradient(135deg, #1a73e8, #0d47a1);
  color: white;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 24px;
}
.app-header h1 { font-size: 20px; font-weight: 600; }
.app-header .subtitle { font-size: 13px; opacity: 0.8; }
.el-main { padding: 20px; }
.el-tabs { background: white; border-radius: 8px; }
</style>
