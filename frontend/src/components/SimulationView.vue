
<template>
  <div class="simulation-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>
        <span class="header-icon">⚙️</span>
        仿真参数配置
      </h1>
      <p class="header-subtitle">配置仿真参数，模拟食堂运行情况</p>
    </div>

    <div class="simulation-container">
      <!-- 左侧配置面板 -->
      <div class="config-panel">
        <div class="panel-header">
          <h2>
            <span class="panel-icon">🔧</span>
            参数设置
          </h2>
        </div>

        <!-- 预设场景卡片 -->
        <div class="preset-cards">
          <div class="preset-card" :class="{ active: activePreset === 'breakfast' }" @click="loadPreset('breakfast')">
            <div class="preset-emoji">🍳</div>
            <div class="preset-info">
              <div class="preset-name">早餐场景</div>
              <div class="preset-desc">5窗口 · 20桌 · 200人 · 快食</div>
            </div>
          </div>
          <div class="preset-card" :class="{ active: activePreset === 'lunch' }" @click="loadPreset('lunch')">
            <div class="preset-emoji">🍱</div>
            <div class="preset-info">
              <div class="preset-name">午餐场景</div>
              <div class="preset-desc">15窗口 · 50桌 · 1000人 · 高峰</div>
            </div>
          </div>
          <div class="preset-card" :class="{ active: activePreset === 'dinner' }" @click="loadPreset('dinner')">
            <div class="preset-emoji">🍽️</div>
            <div class="preset-info">
              <div class="preset-name">晚餐场景</div>
              <div class="preset-desc">15窗口 · 40桌 · 800人 · 中峰</div>
            </div>
          </div>
        </div>

        <div class="config-form">
          <!-- 窗口数量 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">🏪</span>
              <label>窗口数量</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.windowCount"
                min="2"
                max="30"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.windowCount-2)/28*100}%, #e2e8f0 ${(config.windowCount-2)/28*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.windowCount }}</span>
            </div>
            <div class="input-hint">推荐值: 8-12个窗口</div>
          </div>

          <!-- 桌子数量 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">🪑</span>
              <label>桌子数量</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.tableCount"
                min="10"
                max="100"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.tableCount-10)/90*100}%, #e2e8f0 ${(config.tableCount-10)/90*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.tableCount }}</span>
            </div>
            <div class="input-hint">总座位数: {{ config.tableCount * 4 }}个</div>
          </div>

          <!-- 打饭速度 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">⚡</span>
              <label>打饭速度 (分钟/人)</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.servingSpeed"
                min="0.5"
                max="1"
                step="0.1"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.servingSpeed-0.5)/0.5*100}%, #e2e8f0 ${(config.servingSpeed-0.5)/0.5*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.servingSpeed.toFixed(1) }}</span>
            </div>
            <div class="input-hint">每个窗口服务一人所需时间</div>
          </div>

          <!-- 学生总数 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">👥</span>
              <label>学生总数</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.studentCount"
                min="200"
                max="1000"
                step="10"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.studentCount-200)/800*100}%, #e2e8f0 ${(config.studentCount-200)/800*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.studentCount }}</span>
            </div>
          </div>

          <!-- 仿真时间 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">⏱️</span>
              <label>仿真时间 (分钟)</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.simulationTime"
                min="60"
                max="120"
                step="10"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.simulationTime-60)/60*100}%, #e2e8f0 ${(config.simulationTime-60)/60*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.simulationTime }}min</span>
            </div>
          </div>

          <!-- 平均就餐时间 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">🍽️</span>
              <label>平均就餐时间 (分钟)</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.avgEatTime"
                min="10"
                max="30"
                step="1"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.avgEatTime-10)/20*100}%, #e2e8f0 ${(config.avgEatTime-10)/20*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.avgEatTime }}min</span>
            </div>
            <div class="input-hint">学生完成一餐所需的平均时间</div>
          </div>

          <!-- 到达率 -->
          <div class="form-group">
            <div class="label-with-icon">
              <span class="input-icon">📈</span>
              <label>到达率 (人/分钟)</label>
            </div>
            <div class="slider-container">
              <input
                type="range"
                v-model.number="config.arrivalRate"
                min="5"
                max="100"
                step="1"
                class="slider"
                :style="{ background: `linear-gradient(to right, #667eea 0%, #667eea ${(config.arrivalRate-5)/95*100}%, #e2e8f0 ${(config.arrivalRate-5)/95*100}%, #e2e8f0 100%)` }"
              >
              <span class="value-badge">{{ config.arrivalRate.toFixed(1) }}</span>
            </div>
          </div>

          <!-- 新增：仿真速率控制 -->
          <div class="form-group highlight">
            <div class="label-with-icon">
              <span class="input-icon">⚡</span>
              <label>仿真播放速度</label>
            </div>
            <div class="speed-control">
              <span class="speed-label">慢</span>
              <input
                type="range"
                v-model.number="simulationSpeed"
                min="1"
                max="10"
                step="1"
                class="slider speed-slider"
                :style="{ background: `linear-gradient(to right, #48bb78 0%, #48bb78 ${(simulationSpeed-1)/9*100}%, #e2e8f0 ${(simulationSpeed-1)/9*100}%, #e2e8f0 100%)` }"
              >
              <span class="speed-label">快</span>
              <span class="speed-value">{{ simulationSpeed }}x</span>
            </div>
            <div class="input-hint">控制仿真动画的播放速度</div>
          </div>

          <!-- 运行按钮 -->
          <button
            @click="runSimulation"
            class="run-btn"
            :disabled="running"
          >
            <span v-if="!running" class="btn-content">
              <span class="btn-icon">▶️</span>
              开始仿真
            </span>
            <span v-else class="btn-content">
              <span class="spinner"></span>
              仿真运行中...
            </span>
          </button>
        </div>
      </div>

      <!-- 右侧预览面板 -->
      <div class="preview-panel">
        <h2>
          <span class="panel-icon">👁️</span>
          参数预览
        </h2>

        <!-- 参数卡片 -->
        <div class="preview-cards">
          <div class="preview-card" v-for="item in previewItems" :key="item.label">
            <div class="card-icon">{{ item.icon }}</div>
            <div class="card-content">
              <div class="card-label">{{ item.label }}</div>
              <div class="card-value">{{ item.value }}</div>
            </div>
          </div>
        </div>

        <!-- 新增：速度预览 -->
        <div class="speed-preview">
          <div class="speed-indicator">
            <span class="speed-indicator-icon">🎬</span>
            <span class="speed-indicator-label">播放速度:</span>
            <span class="speed-indicator-value">{{ simulationSpeed }}x</span>
          </div>
          <div class="speed-description">
            {{ getSpeedDescription }}
          </div>
        </div>

        <!-- 容量警告 -->
        <div class="capacity-warning" v-if="showWarning">
          <div class="warning-icon">⚠️</div>
          <div class="warning-text">
            <strong>容量预警</strong>
            <p>学生总数超过座位容量的2倍，可能会出现严重拥堵</p>
          </div>
        </div>

        <!-- 负载预测 -->
        <div class="load-prediction">
          <h3>📊 负载预测</h3>
          <div class="prediction-bars">
            <div class="prediction-item">
              <span class="prediction-label">窗口负载</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: windowLoad + '%' }"></div>
              </div>
              <span class="prediction-value">{{ windowLoad }}%</span>
            </div>
            <div class="prediction-item">
              <span class="prediction-label">座位占用</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: seatLoad + '%' }"></div>
              </div>
              <span class="prediction-value">{{ seatLoad }}%</span>
            </div>
          </div>
        </div>

        <!-- 食堂布局预览 -->
        <div class="layout-preview">
          <h3>食堂布局预览</h3>
          <div class="mini-layout">
            <div class="mini-entry">入口</div>
            <div class="mini-arrow">↓</div>
            <div class="mini-windows">
              <div
                v-for="i in Math.min(config.windowCount, 15)"
                :key="'w'+i"
                class="mini-win"
              ></div>
              <span v-if="config.windowCount > 15" class="mini-more">+{{ config.windowCount - 15 }}</span>
            </div>
            <div class="mini-arrow">↓</div>
            <div class="mini-tables">
              <div
                v-for="i in Math.min(config.tableCount, 30)"
                :key="'t'+i"
                class="mini-table"
              ></div>
              <span v-if="config.tableCount > 30" class="mini-more">+{{ config.tableCount - 30 }}桌</span>
            </div>
            <div class="mini-arrow">↓</div>
            <div class="mini-exit">出口</div>
          </div>
          <div class="layout-stats">
            <span>{{ config.windowCount }}窗口</span>
            <span>{{ config.tableCount * 4 }}座位</span>
          </div>
        </div>

        <!-- 参数提示 -->
        <div class="param-tips" v-if="paramTips.length > 0">
          <div class="tip-item" v-for="(tip, i) in paramTips" :key="i" :class="tip.level">
            <span class="tip-icon">{{ tip.icon }}</span>
            <span>{{ tip.text }}</span>
          </div>
        </div>

        <!-- 最近仿真记录 -->
        <div class="recent-simulations" v-if="recentResults.length > 0">
          <h3>📋 最近仿真记录</h3>
          <div class="results-list">
            <div
              v-for="result in recentResults"
              :key="result.id"
              class="result-item"
            >
              <div class="result-info" @click="viewResult(result.id)">
                <span class="result-time">{{ formatTime(result.createdAt) }}</span>
                <span class="result-id">#{{ result.id.slice(-6) }}</span>
              </div>
              <div class="result-actions">
                <span class="view-link" @click="viewResult(result.id)">查看 →</span>
                <button
                  class="delete-btn"
                  @click.stop="deleteResult(result.id)"
                  title="删除记录"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '../stores/simulation.js'

const router = useRouter()
const store = useSimulationStore()

// 本地表单配置（用户编辑的，不绑定 store reactive）
const config = reactive({
  windowCount: store.config.windowCount,
  tableCount: store.config.tableCount,
  servingSpeed: store.config.servingSpeed,
  studentCount: store.config.studentCount,
  simulationTime: store.config.simulationTime,
  arrivalRate: store.config.arrivalRate,
  avgEatTime: store.config.avgEatTime
})

// simulationSpeed 本地维护
const simulationSpeed = ref(store.simulationSpeed)

const running = ref(false)
const recentResults = ref([])
const loadingConfig = ref(true)
const activePreset = ref('')

// 配置使用 Pinia store 中的 config，不再本地维护

// 从后端获取推荐配置作为初始值
const fetchConfigFromBackend = async () => {
  try {
    loadingConfig.value = true
    const response = await axios.get('http://127.0.0.1:8000/api/simulation/config')
    const bc = response.data
    config.windowCount = bc.window_count ?? 10
    config.tableCount = bc.table_count ?? 30
    config.servingSpeed = bc.serving_speed ?? 1
    config.studentCount = bc.student_count ?? 500
    config.simulationTime = bc.simulation_duration ?? 120
    config.arrivalRate = bc.arrival_rate ?? 15
    config.avgEatTime = (bc.avg_eat_time ?? 600) / 60
    console.log('从后端加载配置成功')
  } catch (error) {
    console.error('获取后端配置失败，使用 store 默认配置:', error)
  } finally {
    loadingConfig.value = false
  }
}

// 预览卡片数据
const previewItems = computed(() => [
  { icon: '🏪', label: '窗口数量', value: config.windowCount },
  { icon: '🪑', label: '桌子数量', value: config.tableCount },
  { icon: '💺', label: '总座位数', value: config.tableCount * 4 },
  { icon: '👥', label: '学生总数', value: config.studentCount },
  { icon: '⏱️', label: '仿真时长', value: config.simulationTime + '分钟' },
  { icon: '🍽️', label: '平均就餐时间', value: config.avgEatTime + '分钟' },
  { icon: '⚡', label: '到达率', value: config.arrivalRate.toFixed(1) + '/分钟' }
])

// 计算负载
const windowLoad = computed(() => {
  const maxCapacity = (config.windowCount / config.servingSpeed) * config.simulationTime
  return Math.min(100, Math.round((config.studentCount / maxCapacity) * 100))
})

const seatLoad = computed(() => {
  const totalSeats = config.tableCount * 4
  return Math.min(100, Math.round((config.studentCount / (totalSeats * 2)) * 100))
})

const getSpeedDescription = computed(() => {
  if (simulationSpeed.value <= 3) return '慢速播放，适合观察细节'
  if (simulationSpeed.value <= 6) return '中速播放，平衡速度和观察'
  return '快速播放，快速预览整体趋势'
})

const showWarning = computed(() => {
  return config.studentCount > config.tableCount * 4 * 2
})

const paramTips = computed(() => {
  const tips = []
  const totalSeats = config.tableCount * 4
  if (totalSeats < config.windowCount * 5) {
    tips.push({ icon: '🪑', text: '座位数相对窗口偏少，可能导致等座拥堵', level: 'warn' })
  }
  if (config.windowCount < 6 && config.studentCount > 500) {
    tips.push({ icon: '🏪', text: '窗口数偏少，高峰期可能出现严重排队', level: 'warn' })
  }
  if (config.windowCount > 20) {
    tips.push({ icon: '💰', text: '窗口数量较多，运营成本偏高', level: 'info' })
  }
  if (config.studentCount > totalSeats * 3) {
    tips.push({ icon: '⚠️', text: '学生数远超座位容量，需扩大座位区', level: 'danger' })
  }
  return tips
})

// 加载预设场景（使用用户配置的值）
const loadPreset = async (scene) => {
  try {
    loadingConfig.value = true

    activePreset.value = scene
    if (scene === 'breakfast') {
      // 早餐场景：低负载，吃得快
      config.windowCount = 5
      config.tableCount = 20
      config.servingSpeed = 0.5
      config.studentCount = 200
      config.simulationTime = 120
      config.arrivalRate = 10
      config.avgEatTime = 10
    } else if (scene === 'lunch') {
      // 午餐场景：尝试从后端获取推荐配置
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/simulation/config/recommended')
        const backendConfig = response.data
        config.windowCount = Math.min(backendConfig.window_count ?? 15, 15)
        config.tableCount = backendConfig.table_count ?? 50
        config.servingSpeed = backendConfig.serving_speed ?? 1
        config.studentCount = backendConfig.student_count ?? 1000
        config.simulationTime = Math.min(backendConfig.simulation_duration ?? 120, 120)
        config.arrivalRate = backendConfig.arrival_rate ?? 20
        config.avgEatTime = (backendConfig.avg_eat_time ?? 600) / 60
      } catch (error) {
        console.error('获取推荐配置失败，使用前端默认午餐配置', error)
        config.windowCount = 15
        config.tableCount = 50
        config.servingSpeed = 1
        config.studentCount = 1000
        config.simulationTime = 120
        config.arrivalRate = 20
        config.avgEatTime = 10
      }
    } else if (scene === 'dinner') {
      config.windowCount = 15
      config.tableCount = 40
      config.servingSpeed = 1
      config.studentCount = 800
      config.simulationTime = 120
      config.arrivalRate = 20
      config.avgEatTime = 12
    }

  } catch (error) {
    console.error('加载预设场景失败:', error)
  } finally {
    loadingConfig.value = false
  }
}

// 运行仿真 - 使用异步流程: config + start, 然后跳转到食堂视图实时显示
const runSimulation = async () => {
  running.value = true

  try {
    // 将前端配置转换为后端需要的格式（时间单位：秒）
    const avgServeTimeSeconds = config.servingSpeed * 60   // 分钟/人 → 秒
    const avgEatTimeSeconds = config.avgEatTime * 60       // 从用户配置获取，分钟 → 秒

    const requestData = {
      window_count: config.windowCount,
      seat_count: config.tableCount * 4,
      arrival_rate: config.arrivalRate,
      avg_serve_time: avgServeTimeSeconds,        // 秒
      avg_eat_time: avgEatTimeSeconds,            // 秒（使用用户配置）
      simulation_duration: config.simulationTime, // 分钟
      tick_step: 1.0,                             // 步长1分钟
      tick_delay: 1.5 / simulationSpeed.value,    // 实际延迟(秒)，更慢便于观察
      student_count: config.studentCount,         // 学生总数上限
      serve_time_std: null,
      eat_time_std: null,
      random_seed: null
    }

    console.log('发送配置到后端 (时间单位:秒, 步长:1分钟):', requestData)

    // 步骤1: 配置仿真参数
    const configResponse = await axios.post('http://127.0.0.1:8000/api/config', requestData)
    if (!configResponse.data.success) {
      throw new Error('配置失败: ' + (configResponse.data.message || '未知错误'))
    }
    console.log('配置成功:', configResponse.data)

    // 步骤2: 启动仿真（后台线程运行）
    const startResponse = await axios.post('http://127.0.0.1:8000/api/start')
    if (!startResponse.data.success) {
      throw new Error('启动失败: ' + (startResponse.data.message || '未知错误'))
    }
    console.log('仿真已启动:', startResponse.data)

    // 将配置保存到 Pinia store，供 CafeteriaView 使用
    store.setConfig({
      windowCount: config.windowCount,
      tableCount: config.tableCount,
      servingSpeed: config.servingSpeed,
      arrivalRate: config.arrivalRate,
      studentCount: config.studentCount,
      simulationDuration: config.simulationTime,
      avgEatTime: config.avgEatTime,
      tickStep: 1.0,
      avgServeTimeSeconds: avgServeTimeSeconds,
      avgEatTimeSeconds: avgEatTimeSeconds
    })
    store.simulationSpeed = simulationSpeed.value

    // 跳转到食堂视图，实时显示仿真过程
    router.push({
      path: '/',
      query: {
        running: 'true',
        speed: simulationSpeed.value
      }
    })
  } catch (error) {
    console.error('仿真运行失败:', error)
    alert('仿真运行失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    running.value = false
  }
}

// 获取最近仿真记录
const fetchRecentResults = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/simulation/results')
    recentResults.value = response.data.slice(0, 5)
  } catch (error) {
    console.error('获取仿真记录失败:', error)
  }
}

const deleteResult = async (id) => {
  if (!confirm('确定要删除这条仿真记录吗？')) {
    return
  }

  try {
    await axios.delete(`http://127.0.0.1:8000/api/simulation/results/${id}`)
    await fetchRecentResults()
    recentResults.value = recentResults.value.filter(r => r.id !== id)
    console.log('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
    await fetchRecentResults()
  }
}

const viewResult = (id) => {
  router.push({
    path: '/analysis',
    query: { simulationId: id }
  })
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 初始化
onMounted(() => {
  fetchConfigFromBackend()  // 从后端获取推荐配置作为初始值
  fetchRecentResults()      // 获取历史记录
})
</script>

<style scoped>
/* 添加新的样式 */
.highlight {
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #9ae6b4;
  margin: 10px 0;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.speed-label {
  color: #4a5568;
  font-size: 0.9rem;
}

.speed-slider {
  flex: 1;
}

.speed-slider::-webkit-slider-thumb {
  background: #48bb78;
  border-color: #48bb78;
}

.speed-value {
  min-width: 45px;
  text-align: center;
  padding: 4px 8px;
  background: #48bb78;
  color: white;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
}

.speed-preview {
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  padding: 15px;
  border-radius: 12px;
  margin: 15px 0;
  border: 1px solid #9ae6b4;
}

.speed-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.speed-indicator-icon {
  font-size: 1.2rem;
}

.speed-indicator-label {
  color: #276749;
  font-weight: 500;
}

.speed-indicator-value {
  background: #276749;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 1.1rem;
}

.speed-description {
  color: #276749;
  font-size: 0.9rem;
  padding-left: 30px;
}

/* 其他样式保持不变 */
.simulation-view {
  min-height: calc(100vh - 70px);
  padding: 30px;
  background: #f0f2f5;
}

.page-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.page-header h1 {
  font-size: 1.4rem;
  color: #1a1a1a;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 1.4rem;
}

.header-subtitle {
  color: #8c8c8c;
  font-size: 0.85rem;
}

.simulation-container {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 30px;
}

.config-panel {
  padding: 30px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.panel-header h2, .preview-panel h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.5rem;
  color: #2d3748;
}

.panel-icon {
  font-size: 1.8rem;
}

/* 预设场景卡片 */
.preset-cards {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
}

.preset-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #f7fafc;
  border: 1.5px solid #e8e8e8;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-card:hover {
  border-color: #667eea;
  background: #f5f3ff;
}

.preset-card.active {
  border-color: #667eea;
  background: #f5f3ff;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.15);
}

.preset-emoji { font-size: 1.6rem; flex-shrink: 0; }
.preset-info { min-width: 0; }
.preset-name { font-size: 0.85rem; font-weight: 600; color: #1a1a1a; }
.preset-desc { font-size: 0.7rem; color: #8c8c8c; margin-top: 2px; }

/* 食堂布局预览 */
.layout-preview {
  margin: 15px 0;
  padding: 15px;
  background: #fafafa;
  border-radius: 10px;
}

.layout-preview h3 {
  font-size: 0.9rem;
  color: #595959;
  margin-bottom: 10px;
}

.mini-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.mini-entry, .mini-exit {
  font-size: 0.7rem;
  color: #8c8c8c;
  padding: 3px 16px;
  background: #f0f0f0;
  border-radius: 4px;
}

.mini-arrow { font-size: 0.65rem; color: #bfbfbf; }

.mini-windows {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 100%;
}

.mini-win {
  width: 14px;
  height: 18px;
  background: #e6e6ff;
  border: 1px solid #b8b8e8;
  border-radius: 2px;
}

.mini-tables {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 100%;
}

.mini-table {
  width: 12px;
  height: 12px;
  background: #e8f5e9;
  border: 1px solid #b8d4b8;
  border-radius: 2px;
}

.mini-more { font-size: 0.65rem; color: #bfbfbf; }

.layout-stats {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
  font-size: 0.7rem;
  color: #8c8c8c;
}

/* 参数提示 */
.param-tips {
  margin: 15px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.78rem;
  color: #595959;
}
.tip-item.warn { background: #fffbe6; border-left: 3px solid #faad14; }
.tip-item.info { background: #e6f7ff; border-left: 3px solid #1890ff; }
.tip-item.danger { background: #fff1f0; border-left: 3px solid #f5222d; }
.tip-icon { font-size: 0.85rem; flex-shrink: 0; }

.config-form {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.label-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-icon {
  font-size: 1.2rem;
}

.form-group label {
  font-weight: 600;
  color: #4a5568;
  font-size: 1rem;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 15px;
}

.slider {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
  border: 2px solid #667eea;
  transition: transform 0.2s;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.value-badge {
  min-width: 60px;
  text-align: center;
  padding: 6px 12px;
  background: #f7fafc;
  border-radius: 50px;
  font-weight: 600;
  color: #667eea;
  font-size: 0.9rem;
  border: 1px solid #e2e8f0;
}

.input-hint {
  font-size: 0.85rem;
  color: #a0aec0;
  margin-left: 30px;
}

.run-btn {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.run-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 30px rgba(102, 126, 234, 0.4);
}

.run-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.btn-icon {
  font-size: 1.3rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-panel {
  padding: 30px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.preview-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin: 25px 0;
}

.preview-card {
  background: #f7fafc;
  padding: 15px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: transform 0.2s;
  border: 1px solid #e2e8f0;
}

.preview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-icon {
  font-size: 1.8rem;
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-label {
  font-size: 0.8rem;
  color: #a0aec0;
}

.card-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: #2d3748;
}

.capacity-warning {
  background: #feebc8;
  border-left: 4px solid #ed8936;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.warning-icon {
  font-size: 1.5rem;
}

.warning-text {
  flex: 1;
}

.warning-text strong {
  color: #c05621;
  display: block;
  margin-bottom: 5px;
}

.warning-text p {
  color: #7b341e;
  font-size: 0.9rem;
}

.load-prediction {
  background: #f7fafc;
  padding: 20px;
  border-radius: 12px;
  margin: 20px 0;
}

.load-prediction h3 {
  color: #2d3748;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.prediction-bars {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.prediction-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prediction-label {
  width: 80px;
  color: #4a5568;
  font-size: 0.9rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s;
}

.prediction-value {
  width: 45px;
  text-align: right;
  color: #667eea;
  font-weight: 600;
  font-size: 0.9rem;
}

.recent-simulations {
  margin-top: 30px;
}

.recent-simulations h3 {
  color: #2d3748;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f7fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e2e8f0;
}

.result-item:hover {
  background: white;
  border-color: #667eea;
  transform: translateX(5px);
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-time {
  font-size: 0.85rem;
  color: #a0aec0;
}

.result-id {
  font-weight: 600;
  color: #2d3748;
  font-family: monospace;
}

.view-link {
  color: #667eea;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-link:hover {
  color: #5a67d8;
  text-decoration: underline;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  opacity: 0.6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-btn:hover {
  opacity: 1;
  background-color: #fed7d7;
  transform: scale(1.1);
}

.delete-btn:active {
  transform: scale(0.95);
}
</style>
SimulationView.vue
目前显示的是“SimulationView.vue”。