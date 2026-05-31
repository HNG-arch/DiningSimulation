# 北京交通大学食堂就餐仿真系统 — 源代码说明文档

## 1. 项目概述

本项目是一个**食堂就餐离散事件仿真系统**，采用前后端分离架构：
- **后端**：FastAPI + SQLite + NumPy，用于仿真引擎和数据分析
- **前端**：Vue 3 + Vite + Axios，提供可视化配置和分析界面
- **测试**：Playwright 端到端测试框架

---

## 2. 项目目录结构

```
DiningSimulation-master/
├── CLAUDE.md                              # 项目指引文档
├── README.md
│
├── docs/                                  # 文档目录
│   ├── ARCHITECTURE.md                    # 本文件：架构说明
├── backend/                               # 后端服务目录
│   ├── app/                               # FastAPI 应用
│   │   ├── core/                          # 核心业务逻辑
│   │   │   ├── simulation.py              # 仿真引擎核心类
│   │   │   ├── models.py                  # 数据模型定义
│   │   │   ├── analysis.py                # 决策分析模块
│   │   │   └── random_utils.py            # 随机数生成工具
│   │   └── main.py                        # FastAPI 主入口/API路由
│   ├── scripts/                           # 工具脚本
│   │   ├── analyze_results.py             # 数据分析工具
│   │   ├── generate_test_data.py          # 测试数据生成
│   │   ├── validate_model.py              # 模型验证脚本
│   │   ├── watch_simulation.py            # 仿真调试观察
│   │   └── screenshot_pages.py            # 截图工具
│   ├── data/                              # 数据目录
│   │   └── simulation_history.db          # SQLite 数据库
│   ├── tests/                             # 测试目录
│   │   └── e2e/                           # 端到端测试
│   │       ├── conftest.py
│   │       ├── test_e2e.py
│   │       └── screenshot_scenario1.png
│   └── requirements.txt                   # 后端依赖
│
├── frontend/                              # 前端应用目录
│   ├── src/
│   │   ├── views/                         # 页面级组件
│   │   │   ├── SimulationView.vue         # 参数配置页面
│   │   │   ├── CafeteriaView.vue          # 食堂仿真可视化页面
│   │   │   └── AnalysisView.vue           # 决策分析页面
│   │   ├── components/                    # 复用子组件
│   │   ├── router/
│   │   │   └── index.js                   # Vue Router 路由配置
│   │   ├── stores/                        # Pinia 状态管理
│   │   ├── assets/                        # 静态资源
│   │   ├── App.vue                        # 根组件
│   │   └── main.js                        # 前端入口文件
│   ├── package.json                       # 前端依赖配置
│   ├── vite.config.js                     # Vite 构建配置
│   └── dist/                              # 生产构建输出
│
└── .gitignore                             # Git 忽略规则
```

**目录结构重构说明**：
- ✅ `backend/scripts/` — 所有工具脚本集中管理
- ✅ `backend/data/` — SQLite 数据库统一存储
- ✅ `backend/tests/e2e/` — 测试文件统一在 backend 下
- ✅ `frontend/src/views/` — 页面级组件与子组件分离
- ✅ `docs/` — 文档文件统一管理，使用英文名
- ✅ `backend/requirements.txt` — 唯一的后端依赖文件

---

## 3. 后端详细说明

### 3.1 backend/app/main.py

**功能**：FastAPI 主入口文件，定义所有 RESTful API 路由。

**核心 API 端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/config` | POST | 配置仿真参数 |
| `/api/start` | POST | 启动仿真引擎 |
| `/api/stop` | POST | 强制停止仿真 |
| `/api/state` | GET | 获取实时状态快照 |
| `/api/stats` | GET | 获取仿真统计信息 |
| `/api/simulation/run` | POST | 立即运行仿真并返回结果 |
| `/api/simulation/results` | GET | 获取历史仿真记录列表 |
| `/api/simulation/results/{id}` | GET | 获取单条记录详情 |
| `/api/analysis/summary` | GET | 综合分析摘要 |
| `/api/analysis/cost/{id}` | GET | 成本分析 |
| `/api/analysis/optimize` | GET | 获取最优配置推荐 |
| `/api/analysis/train` | POST | 训练 ML 模型 |
| `/api/analysis/u-curve` | GET | U型成本曲线数据 |
| `/api/analysis/heatmap` | GET | 热力图数据 |
| `/api/analysis/explain` | GET | 模型解读 HTML |

---

### 3.2 backend/app/core/models.py

**功能**：定义数据模型、Pydantic 验证类和成本计算工具。

**核心数据结构**：

```python
# 配置参数模型
ConfigParams: window_count, seat_count, arrival_rate, avg_serve_time,
              avg_eat_time, simulation_duration, tick_step, tick_delay,
              serve_time_std, eat_time_std, random_seed, student_count

# 窗口状态模型
WindowState: window_id, queue_length, serve_time_left, total_served

# 学生记录模型
StudentRecord: id, arrive_time, queue_wait_time, seat_id, eat_time_left

# 统计结果模型
Statistics: avg_wait_time, throughput_per_window, throughput_total,
             seat_turnover, satisfaction_score, time_series
```

**成本常量**：
- `COST_PER_WINDOW = 300` 元/天（每个窗口运营成本）
- `COST_PER_SEAT = 5` 元/天（每个座位摊销成本）
- `PENALTY_PER_MINUTE = 80` 元/分钟（等待时间惩罚）

**核心函数**：
- `load_all_results()`: 从数据库加载所有仿真记录
- `calculate_cost()`: 计算综合运营成本
- `calculate_cost_tuple()`: 计算成本（元组格式）

---

### 3.3 backend/app/core/simulation.py

**功能**：食堂就餐仿真引擎核心实现。

**核心类**：`SimulationEngine`

**仿真流程**：
1. **学生到达**：时变泊松分布生成学生
2. **窗口排队**：最短队列优先分配
3. **打饭服务**：正态分布服务时间
4. **座位分配**：随机选择空座位
5. **就餐过程**：时间递减
6. **状态快照**：实时返回仿真状态

**关键方法**：
- `run(state_callback)`: 运行仿真，回调返回状态
- `step()`: 执行单个时间步
- `get_statistics()`: 获取统计结果
- `get_state_snapshot()`: 获取当前状态快照

---

### 3.4 backend/app/core/analysis.py

**功能**：决策分析模块，基于机器学习的优化建议。

**核心功能**：
- `train_model()`: 训练随机森林回归模型
- `predict_wait_time()`: 预测等待时间
- `optimize_config()`: 网格搜索最优配置
- `get_u_curve_data()`: U型成本曲线数据
- `get_heatmap_data()`: 窗口×座位热力图数据
- `get_analysis_summary()`: 综合分析摘要

**ML 特征**：`['window_count', 'seat_count', 'arrival_rate', 'avg_serve_time', 'avg_eat_time']`

---

### 3.5 backend/app/core/random_utils.py

**功能**：随机数生成工具函数。

**核心函数**：
- `poisson_arrivals(rate, duration, rng)`: 泊松分布到达数
- `normal_time(mean, std, rng)`: 截断正态分布时间

---

### 3.6 backend/scripts/ — 工具脚本目录

**功能**：独立执行的分析、测试、调试脚本。

| 脚本 | 功能 |
|------|------|
| `watch_simulation.py` | 实时观察仿真内部状态（调试用） |
| `analyze_results.py` | 离线数据分析，使用 RandomForest 训练和优化 |
| `generate_test_data.py` | 生成测试数据集（1830条仿真记录） |
| `validate_model.py` | 模型验证，生成 U型曲线和热力图验证图表 |
| `screenshot_pages.py` | 自动截图工具 |

**使用示例**：
```bash
cd backend/scripts
python analyze_results.py         # 分析现有数据库数据
python generate_test_data.py      # 生成测试数据
python validate_model.py          # 验证模型准确性
```

**数据库路径**：所有脚本自动查找 `backend/data/simulation_history.db`

---

## 4. 前端详细说明

### 4.1 frontend/src/main.js

**功能**：前端应用入口，初始化 Vue 应用。

**核心配置**：
- 引入 Vue Router
- 配置 Axios HTTP 客户端
- 挂载根组件

---

### 4.2 frontend/src/App.vue

**功能**：根组件，定义导航栏布局。

**导航结构**：
- `/` - 食堂场景 (CafeteriaView)
- `/simulation` - 运行仿真 (SimulationView)
- `/analysis` - 决策分析 (AnalysisView)

---

### 4.3 frontend/src/router/index.js

**功能**：Vue Router 路由配置。

**路由表**：
```javascript
{ path: '/', component: CafeteriaView }
{ path: '/simulation', component: SimulationView }
{ path: '/analysis', component: AnalysisView }
```

---

### 4.4 frontend/src/views/SimulationView.vue

**功能**：仿真参数配置页面。

**配置参数**（滑块控制）：
1. 窗口数量 (windowCount): 2-30
2. 桌子数量 (tableCount): 10-100
3. 服务速度 (servingSpeed): 0.5-2.0
4. 学生数量 (studentCount): 100-1500
5. 仿真时间 (simulationTime): 10-120分钟
6. 平均就餐时间 (avgEatTime): 5-20分钟
7. 到达率 (arrivalRate): 5-30人/分钟

**预设场景**：早餐 🍳 / 午餐 🍱 / 晚餐 🍽️

---

### 4.5 frontend/src/views/CafeteriaView.vue

**功能**：食堂仿真可视化页面，实时显示仿真过程。

**核心功能**：
- 实时动画显示窗口排队
- 座位占用热力图
- 仿真进度条
- 暂停/继续/终止控制
- 播放速度调节

**数据获取**：
- 轮询 `/api/state` 获取实时状态
- 轮询 `/api/stats` 获取统计信息

---

### 4.6 frontend/src/views/AnalysisView.vue

**功能**：决策分析页面，展示仿真结果和 ML 优化建议。

**核心模块**：
1. **成本分析卡片**：显示运营成本、惩罚成本
2. **ML 模型性能**：R²、MAE 指标
3. **U 型成本曲线**：窗口数量 vs 综合成本
4. **木桶效应热力图**：窗口×座位等待时间
5. **ML 优化建议**：智能推荐最优配置
6. **等待时间趋势**：时间序列图表
7. **各窗口吞吐量**：柱状图展示
8. **模型解读弹窗**：解释模型原理

---

## 5. 测试说明

### 5.1 backend/tests/e2e/conftest.py

**功能**：Pytest 配置，自动管理服务进程生命周期。

**Session 级 Fixtures**：
- `backend_process`: 启动/关闭 FastAPI 后端
- `frontend_process`: 启动/关闭 Vite 前端
- `browser`: 创建 Edge 浏览器实例
- `context`: 创建浏览器上下文
- `page`: 每个测试用例的独立页面

---

### 5.2 backend/tests/e2e/test_e2e.py

**功能**：5个端到端测试场景。

| 测试函数 | 说明 |
|---------|------|
| `test_scenario_normal_flow` | 正常流程：配置→仿真→分析验证 |
| `test_scenario_error_on_unconfigured` | 异常拦截：重复启动检测 |
| `test_scenario_database_verification` | 数据库：记录写入验证 |
| `test_ui_full_flow` | UI完整流程：滑块→预览→仿真→分析 |
| `test_ui_parameter_verification` | 参数验证：avg_eat_time 传递正确性 |

**运行指令**（在项目根目录）：
```bash
pytest backend/tests/e2e/ -v              # 无头模式
pytest backend/tests/e2e/ -v --headed     # 显示浏览器
```

---

## 6. 数据分析模块 (backend/scripts/)

### 6.1 analyze_results.py

**功能**：数据分析工具函数库，支持离线分析和模型优化。

**核心函数**：
- `load_data()`: 加载 SQLite 中的仿真数据
- `train_model()`: 训练随机森林回归模型（100棵树，max_depth=10）
- `calculate_cost()`: 根据窗口、座位数和等待时间计算综合成本
- `optimize_config()`: 网格搜索最优配置（625个组合）

**成本参数**：
- `COST_PER_WINDOW = 300` 元/天
- `COST_PER_SEAT = 5` 元/天
- `PENALTY_PER_MINUTE = 80` 元/分钟

**使用示例**：
```bash
cd backend/scripts
python analyze_results.py
```

---

### 6.2 validate_model.py

**功能**：模型验证脚本，生成验证图表和评估指标。

**验证内容**：
1. 机器学习核心指标（MAE、R² Score）
2. U型成本曲线（单变量优化）
3. 木桶效应热力图（双变量分析）

**输出**：
- 控制台输出：精度指标、最优配置建议
- 图表文件：`validation_1_u_curve.png`、`validation_2_heatmap.png`

---

### 6.3 generate_test_data.py

**功能**：生成测试数据集，用于模型训练和验证。

**数据规模**：
- 窗口数: 2-30（15种）
- 座位数: 50-400（15种）
- 到达率: 10-100 人/分钟
- 总记录数：约 1830 条

**生成策略**：
- 嵌入排队论非线性拥堵特征
- M/M/c 排队模型近似
- 自动写入 `backend/data/simulation_history.db`

---

### 6.4 validate_model.py 和其他脚本

见上方说明。

---

## 7. 数据库说明

### 7.1 backend/data/simulation_history.db

**SQLite 数据库**，存储仿真历史记录。

**数据库路径**：`backend/data/simulation_history.db`

**初始化**：
- 后端启动时自动创建（见 `backend/app/main.py::init_db()`）
- 表结构自动建立
- 所有脚本和 API 自动定位到此路径

**主表**：`simulation_runs`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| run_timestamp | TEXT | 运行时间戳 |
| window_count | INTEGER | 窗口数量 |
| seat_count | INTEGER | 座位数量 |
| arrival_rate | REAL | 到达率 |
| avg_serve_time | REAL | 平均服务时间(秒) |
| avg_eat_time | REAL | 平均就餐时间(秒) |
| simulation_duration | INTEGER | 仿真时长(分钟) |
| avg_wait_time | REAL | 平均等待时间(分钟) |
| throughput_total | INTEGER | 总吞吐量 |
| seat_turnover | REAL | 座位周转率 |
| satisfaction_score | REAL | 满意度分数 |
| time_series | TEXT | JSON时间序列 |

**关联表**：`window_throughput`
- 记录每个窗口的服务人数

---

## 8. 技术栈总结

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | >=0.104.0 |
| 后端服务器 | Uvicorn | >=0.24.0 |
| 数据验证 | Pydantic | >=2.5.0 |
| 科学计算 | NumPy | >=1.24.0 |
| 数据处理 | Pandas | >=1.5.0 |
| 机器学习 | scikit-learn | >=1.0.0 |
| 数据库 | SQLite | 内置 |
| 前端框架 | Vue 3 | 3.x |
| 构建工具 | Vite | 5.x |
| HTTP客户端 | Axios | 最新 |
| 路由 | Vue Router | 4.x |
| 测试框架 | Playwright | 0.8.0 |
| 测试运行器 | Pytest | >=7.4.0 |

---

## 9. 最新改进 (2026-05-30)

### 9.1 项目结构重构

**目标**：规范化项目布局，提升可维护性。

**主要调整**：
| 改动 | 说明 |
|------|------|
| `backend/scripts/` | 脚本集中管理：分析、数据生成、验证等 |
| `backend/data/` | 数据存储统一：SQLite 数据库单一位置 |
| `backend/tests/e2e/` | 测试合并到 backend：便于依赖管理 |
| `frontend/src/views/` | 页面与子组件分离：遵循 Vue 3 最佳实践 |
| `docs/` | 文档文件统一：使用英文命名和结构 |
| `backend/requirements.txt` | 依赖唯一化：消除冗余和版本冲突 |

---

### 9.2 后端 API 改进

**允许运行时重新配置** (`/api/config`):
- 原行为：运行中拒绝新配置请求
- 新行为：自动停止旧仿真，立即应用新配置
- 修改位置：`backend/app/main.py` 第 172-181 行

---



## 9. 快速开始命令

### 后端启动
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### E2E 测试
```bash
pytest backend/tests/e2e/ -v              # 无头模式
pytest backend/tests/e2e/ -v --headed     # 显示浏览器
```

### 离线数据分析
```bash
cd backend/scripts
python analyze_results.py         # 分析现有数据
python generate_test_data.py      # 生成新数据
python validate_model.py          # 验证模型
```
