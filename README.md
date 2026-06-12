# 混凝沉淀仿真系统

自来水厂混凝沉淀环节仿真工具，实现投药优化、沉降模拟和异常工况应急方案生成。

## 系统架构

- **后端**: FastAPI + SQLite + NumPy/SciPy
- **前端**: Vue3 + ECharts + Element Plus

## 核心功能

1. **工艺流程仿真** — 混凝剂投加→矾花形成→Stokes沉降（一维短流模型）→出水浊度时间曲线
2. **投药量优化** — 响应曲面法+惩罚函数最小化，给定目标浊度找药剂成本最低的最优投药量
3. **异常工况模拟** — 暴雨高浊/pH异常/低温低浊，实时仿真出水变化并生成应急投药方案

## 快速启动

### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# API 运行在 http://localhost:8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 开发服务器运行在 http://localhost:3000
```

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/simulate` | POST | 正常工况仿真 |
| `/api/optimize` | POST | 投药量优化 |
| `/api/abnormal` | POST | 异常工况仿真 |
| `/api/defaults` | GET | 获取默认参数 |
| `/api/history` | GET | 历史记录查询 |

## 模型说明

- **混凝模型**: 基于 Camp-Stein 碰撞动力学简化，考虑 pH 影响因子、温度影响因子、Gt 值
- **沉降模型**: Stokes 公式计算沉降速度，一维对流+沉降方程离散求解，短流系数修正实际流速
- **优化方法**: 有约束单变量优化 (scipy.optimize.minimize_scalar)，惩罚函数处理出水浊度约束
