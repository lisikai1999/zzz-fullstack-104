import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export function runSimulation(params) {
  return api.post('/simulate', params)
}

export function runOptimization(params) {
  return api.post('/optimize', params)
}

export function runAbnormalEvent(params) {
  return api.post('/abnormal', params)
}

export function getDefaults() {
  return api.get('/defaults')
}

export function getHistory(limit = 50) {
  return api.get('/history', { params: { limit } })
}
