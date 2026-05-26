<template>
  <div class="cafeteria-view">
    <div class="header">
      <h1>🍽️ 食堂场景模拟</h1>

      <div v-if="isSimulating" class="simulation-controls">
        <div class="simulation-status">
          <span class="status-badge active">仿真运行中</span>
          <span class="time-display">时间: {{ formatTime(currentTime) }} / {{ formatTime(totalTime) }} 分钟</span>
          <span class="progress-text">{{ round(progressPercentage) }}%</span>
        </div>

        <div class="control-buttons">
          <button @click="togglePause" class="control-btn" :class="{ paused: isPaused }">
            {{ isPaused ? '▶️ 继续' : '⏸️ 暂停' }}
          </button>
          <button @click="stopSimulation" class="control-btn stop-btn">
            ⏹️ 终止
          </button>
        </div>

        <div class="speed-control">
          <span>🐌</span>
          <input type="range" v-model.number="playbackSpeed" min="1" max="20" step="1" class="speed-slider">
          <span>🐇</span>
          <span class="speed-value">{{ playbackSpeed }}x</span>
        </div>
      </div>
    </div>

    <div class="control-panel">
      <div class="control-item">
        <label>🏪 窗口数量 ({{ config.windowCount }})</label>
        <input type="range" v-model.number="config.windowCount" min="5" max="15" :disabled="isSimulating">
      </div>
      <div class="control-item">
        <label>🪑 桌子数量 ({{ config.tableCount }})</label>
        <input type="range" v-model.number="config.tableCount" min="20" max="50" :disabled="isSimulating">
      </div>
      <div class="control-item">
        <label>⚡ 打饭速度 ({{ config.servingSpeed.toFixed(1) }}分钟/人)</label>
        <input type="range" v-model.number="config.servingSpeed" min="0.5" max="1" step="0.1" :disabled="isSimulating">
      </div>
      <button @click="resetToDefault" class="reset-btn" :disabled="isSimulating">🔄 重置</button>
    </div>

    <div class="cafeteria-layout">
      <div class="entrance">
        <div class="entrance-icon">🚪</div>
        <div class="entrance-label">入口</div>
        <div class="entrance-stats">
          <div class="stat-row">
            <span>⏱️ 到达率:</span>
            <span class="value">{{ config.arrivalRate }}/分</span>
          </div>
          <div class="stat-row">
            <span>👥 排队中:</span>
            <span class="value highlight">{{ waitingQueueLength }}</span>
          </div>
          <div class="stat-row">
            <span>📊 已到达:</span>
            <span class="value">{{ totalArrived }}</span>
          </div>
        </div>
        <div class="arrival-animation">
          <div v-for="student in arrivingStudents" :key="student.id"
               class="arriving-student" :style="student.style">
            👤
          </div>
        </div>
      </div>

      <div class="windows-area">
        <h3>🍚 打饭窗口</h3>
        <div class="windows-grid">
          <div v-for="window in windows" :key="window.id" class="window-card"
               :style="{ backgroundColor: getWindowColor(window.queueLength) }">
            <div class="window-header">
              <span class="window-number">窗口 {{ window.id }}</span>
              <span class="serving-indicator" v-if="window.isServing">
                <span class="pulse"></span> 服务中
              </span>
            </div>
            <div class="window-info">
              <div class="queue-info">
                <span>👥 排队: {{ window.queueLength }}人</span>
                <div class="queue-bars">
                  <div v-for="i in min(window.queueLength, 10)" :key="i"
                       class="queue-bar" :style="{ width: (100 / Math.max(window.queueLength, 1)) + '%' }"></div>
                </div>
              </div>
              <div class="service-info">
                <span>⚡ {{ config.servingSpeed }}分钟/人</span>
                <span>📊 {{ window.totalServed }}人</span>
              </div>
            </div>
            <div class="queue-visual">
              <span v-for="(person, idx) in window.queueAnimation" :key="idx"
                    class="person-icon" :style="{ animationDelay: idx * 0.1 + 's' }">
                👤
              </span>
              <span v-if="window.queueLength > 5" class="more">+{{ window.queueLength-5 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="dining-area">
        <h3>🍽️ 就餐区</h3>
        <div class="tables-grid">
          <div v-for="table in diningTables" :key="table.id" class="table-card"
               :class="{ 'table-full': table.occupiedSeats === 4 }">
            <div class="table-header">
              <span class="table-number">餐桌 {{ table.id }}</span>
              <span class="table-status">{{ table.occupiedSeats }}/4</span>
            </div>
            <div class="seats">
              <div v-for="(seat, idx) in table.seats" :key="idx"
                   class="seat" :class="{ occupied: seat.occupied, 'seat-animation': seat.justOccupied }">
                <div class="seat-content">
                  <span class="seat-icon">{{ seat.occupied ? '👤' : '🪑' }}</span>
                  <div v-if="seat.occupied && seat.remainingTime" class="eating-timer">
                    {{ ceil(seat.remainingTime) }}s
                    <div class="timer-bar" :style="{ width: seat.eatProgress + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="table-progress" v-if="table.occupiedSeats > 0">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: (table.occupiedSeats / 4 * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="exit">
        <div class="exit-icon">🚪</div>
        <div class="exit-label">出口</div>
        <div class="exit-stats">
          <div class="stat-row">
            <span>✅ 已离开:</span>
            <span class="value">{{ totalCompleted }}</span>
          </div>
          <div class="stat-row">
            <span>📈 完成率:</span>
            <span class="value">{{ completionRate }}%</span>
          </div>
        </div>
        <div class="exit-animation">
          <div v-for="student in leavingStudents" :key="student.id"
               class="leaving-student" :style="student.style">
            👋
          </div>
        </div>
      </div>
    </div>

    <div class="stats-panel">
      <h3>📊 实时统计</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">📊 总排队人数:</span>
          <span class="stat-value">{{ totalQueueLength }}人</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">🪑 空余座位:</span>
          <span class="stat-value">{{ emptySeats }}个</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">🍽️ 就餐人数:</span>
          <span class="stat-value">{{ diningPeople }}人</span>
        </div>
        <div class="stat-item highlight">
          <span class="stat-label">⏰ 平均等待:</span>
          <span class="stat-value">{{ avgWaitTime.toFixed(1) }}分钟</span>
        </div>
        <div class="stat-item highlight">
          <span class="stat-label">✅ 已完成就餐:</span>
          <span class="stat-value">{{ totalCompleted }}/{{ totalStudents }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">🔄 座位周转率:</span>
          <span class="stat-value">{{ seatTurnover.toFixed(2) }}次/时</span>
        </div>
        <div class="stat-item highlight">
          <span class="stat-label">😊 满意度:</span>
          <span class="stat-value">{{ (satisfaction * 100).toFixed(1) }}%</span>
        </div>
      </div>
      <div class="progress-bar-container">
        <div class="progress-bar" :style="{ width: progressPercentage + '%' }">
          <span class="progress-label">{{ round(progressPercentage) }}%</span>
        </div>
      </div>
    </div>

    <div v-if="errorMessage" class="error-message">
      <span>⚠️</span> {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 配置（默认值，会被 localStorage 或 SimulationView 传递的值覆盖）
const config = reactive({
  windowCount: 10,
  tableCount: 25,
  servingSpeed: 1,
  arrivalRate: 15,
  simulationDuration: 120,
  avgEatTime: 600
})

// 状态变量
const windows = ref([])
const diningTables = ref([])
const isSimulating = ref(false)
const isPaused = ref(false)
const playbackSpeed = ref(5)
const totalTime = ref(60)
const currentTime = ref(0)
const totalServed = ref(0)
const avgWaitTime = ref(0)
const waitingQueueLength = ref(0)
const seatTurnover = ref(0)
const totalArrived = ref(0)
const totalCompleted = ref(0)
const eatingCount = ref(0)
const satisfaction = ref(0)
const errorMessage = ref('')

// 动画相关
const arrivingStudents = ref([])
const leavingStudents = ref([])
let studentIdCounter = 0
let pollingInterval = null
let prevTotalArrived = 0
let prevTotalCompleted = 0

// 计算属性
const progressPercentage = computed(() => totalTime.value ? (currentTime.value / totalTime.value) * 100 : 0)
const totalQueueLength = computed(() => windows.value.reduce((sum, w) => sum + (w.queueLength || 0), 0))
const emptySeats = computed(() => config.tableCount * 4 - eatingCount.value)
const diningPeople = computed(() => eatingCount.value)
const totalStudents = computed(() => Math.floor(config.arrivalRate * totalTime.value))
const completionRate = computed(() => totalStudents.value ? ((totalCompleted.value / totalStudents.value) * 100).toFixed(1) : 0)

// 添加到达动画
const addArrivalAnimation = (count = 1) => {
  for (let i = 0; i < count; i++) {
    const id = studentIdCounter++
    arrivingStudents.value.push({ id, style: { left: Math.random() * 80 + 10 + '%', animationDelay: (i * 0.1) + 's' } })
    setTimeout(() => { arrivingStudents.value = arrivingStudents.value.filter(s => s.id !== id) }, 2000)
  }
}

// 添加离开动画
const addLeaveAnimation = (count = 1) => {
  for (let i = 0; i < count; i++) {
    const id = studentIdCounter++
    leavingStudents.value.push({ id, style: { right: Math.random() * 80 + 10 + '%', animationDelay: (i * 0.1) + 's' } })
    setTimeout(() => { leavingStudents.value = leavingStudents.value.filter(s => s.id !== id) }, 2000)
  }
}

// 初始化窗口显示
const initWindows = () => {
  windows.value = Array.from({ length: config.windowCount }, (_, i) => ({
    id: i + 1,
    queueLength: 0,
    speed: config.servingSpeed,
    totalServed: 0,
    isServing: false,
    queueAnimation: []
  }))
}

// 初始化餐桌显示
const initTables = () => {
  diningTables.value = Array.from({ length: config.tableCount }, (_, i) => ({
    id: i + 1,
    seats: Array.from({ length: 4 }, () => ({
      occupied: false,
      remainingTime: 0,
      eatProgress: 0,
      justOccupied: false
    })),
    occupiedSeats: 0
  }))
}

// 初始化所有显示
const initDisplay = () => {
  initWindows()
  initTables()
}

// 更新窗口排队动画
const updateQueueAnimation = () => {
  windows.value.forEach(window => {
    window.queueAnimation = Array(Math.min(window.queueLength, 8)).fill(null)
  })
}

// 更新显示数据（从后端state）
const updateDisplay = (state) => {
  if (!state) return

  currentTime.value = state.current_time || 0
  avgWaitTime.value = state.statistics?.avg_wait_time || 0
  totalServed.value = state.statistics?.throughput || 0
  waitingQueueLength.value = state.total_queue ?? (state.windows?.reduce((sum, w) => sum + (w.queue_length || 0), 0) || 0)
  seatTurnover.value = state.statistics?.seat_turnover || 0
  satisfaction.value = state.statistics?.satisfaction || 0
  totalArrived.value = state.total_arrived || 0
  totalCompleted.value = state.total_completed || 0
  eatingCount.value = state.eating_count || 0

  // 检测新到达
  if (totalArrived.value > prevTotalArrived) {
    addArrivalAnimation(Math.min(totalArrived.value - prevTotalArrived, 5))
  }
  prevTotalArrived = totalArrived.value

  // 检测新离开
  if (totalCompleted.value > prevTotalCompleted) {
    addLeaveAnimation(Math.min(totalCompleted.value - prevTotalCompleted, 5))
  }
  prevTotalCompleted = totalCompleted.value

  // 更新窗口信息
  if (state.windows && state.windows.length > 0) {
    state.windows.forEach((windowState, idx) => {
      if (windows.value[idx]) {
        windows.value[idx].queueLength = windowState.queue_length || 0
        windows.value[idx].totalServed = windowState.total_served || 0
        windows.value[idx].isServing = windowState.serve_time_left > 0
      }
    })
    updateQueueAnimation()
  }

  // 更新就餐区（使用真实的座位矩阵数据）
  if (state.seats && diningTables.value.length > 0) {
    updateDiningAreaFromSeats(state.seats)
  }
}

// 从后端座位矩阵更新就餐区显示
const updateDiningAreaFromSeats = (seatsData) => {
  const seatMatrix = seatsData.data || []
  const backendRows = seatsData.rows || 0
  const backendCols = seatsData.cols || 0

  if (seatMatrix.length === 0) return

  // 将后端座位矩阵映射到前端餐桌显示
  let flatSeatIndex = 0
  const totalSeatsNeeded = config.tableCount * 4
  const flatSeats = []

  // 将二维矩阵展平为一维数组
  for (let r = 0; r < backendRows; r++) {
    for (let c = 0; c < backendCols; c++) {
      if (r < seatMatrix.length && c < seatMatrix[r].length) {
        flatSeats.push(seatMatrix[r][c])
      }
    }
  }

  // 分配到各餐桌
  diningTables.value.forEach((table) => {
    let occupiedInTable = 0
    for (let seatIdx = 0; seatIdx < 4; seatIdx++) {
      const remainSec = flatSeatIndex < flatSeats.length ? flatSeats[flatSeatIndex] : 0
      flatSeatIndex++
      const isOccupied = remainSec > 0
      const wasOccupied = table.seats[seatIdx]?.occupied || false

      if (isOccupied && !wasOccupied) {
        table.seats[seatIdx] = {
          occupied: true,
          remainingTime: remainSec,
          eatProgress: (remainSec / (config.avgEatTime || 600)) * 100,
          justOccupied: true
        }
        occupiedInTable++
        setTimeout(() => {
          if (table.seats[seatIdx]) table.seats[seatIdx].justOccupied = false
        }, 500)
      } else if (!isOccupied && wasOccupied) {
        table.seats[seatIdx] = {
          occupied: false,
          remainingTime: 0,
          eatProgress: 0,
          justOccupied: false
        }
      } else if (isOccupied && wasOccupied && table.seats[seatIdx]) {
        table.seats[seatIdx].remainingTime = remainSec
        table.seats[seatIdx].eatProgress = (remainSec / (config.avgEatTime || 600)) * 100
        table.seats[seatIdx].justOccupied = false
        occupiedInTable++
      }
    }
    table.occupiedSeats = occupiedInTable
  })
}

// 开始轮询后端状态
const startPolling = () => {
  if (pollingInterval) clearInterval(pollingInterval)
  const intervalTime = Math.max(400, 2000 / playbackSpeed.value)

  pollingInterval = setInterval(async () => {
    if (!isPaused.value && isSimulating.value) {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/state')

        if (response.data.success && response.data.state) {
          updateDisplay(response.data.state)

          // 检查仿真是否完成（修改判定条件：时间已经对齐了 totalTime.value）
          if (response.data.state.current_time >= totalTime.value) {
            
            // 【修复：直接停止仿真】不再额外等待 state
            await endSimulationCleanUp()
            
          }
        } else if (!response.data.success) {
           // 如果state为none且不报错，可能是强停的
        }
      } catch (error) {
        console.error('获取状态失败:', error)
      }
    }
  }, intervalTime)
}

// 【新增方法】完美处理正常跑完后的逻辑
const endSimulationCleanUp = async () => {
    if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
    }
    isSimulating.value = false
    
    // 获取最终统计结果
    try {
        const statsResponse = await axios.get('http://127.0.0.1:8000/api/stats')
        if (statsResponse.data.success && statsResponse.data.is_finished) {
            // 保存结果ID供分析页使用
            const resultsResponse = await axios.get('http://127.0.0.1:8000/api/simulation/results')
            if (resultsResponse.data.length > 0) {
            localStorage.setItem('lastSimulationId', resultsResponse.data[0].id)
            }
            errorMessage.value = '仿真已完成！可前往"决策分析"查看详细结果。'
            setTimeout(() => { errorMessage.value = '' }, 5000)
        }
    } catch (e) {
        console.error('获取统计失败:', e)
    }
}

// 从localStorage加载配置并开始仿真
const loadAndStartSimulation = () => {
  const savedConfig = localStorage.getItem('simulationConfig')
  if (savedConfig) {
    try {
      const parsed = JSON.parse(savedConfig)
      config.windowCount = parsed.windowCount || 10
      config.tableCount = parsed.tableCount || 25
      config.servingSpeed = parsed.servingSpeed || 1.0
      config.arrivalRate = parsed.arrivalRate || 30
      config.simulationDuration = parsed.simulationDuration || 60
      config.avgEatTime = parsed.avgEatTime || 600
      totalTime.value = parsed.simulationDuration || 60
    } catch (e) {
      console.error('解析配置失败:', e)
    }
  }

  const savedSpeed = localStorage.getItem('simulationSpeed')
  if (savedSpeed) {
    playbackSpeed.value = parseInt(savedSpeed) || 5
  }

  // 如果有 'running' 查询参数，说明需要开始仿真
  if (route.query.running === 'true') {
    const routeSpeed = parseInt(route.query.speed)
    if (routeSpeed) playbackSpeed.value = routeSpeed

    isSimulating.value = true
    isPaused.value = false
    errorMessage.value = ''
    studentIdCounter = 0
    prevTotalArrived = 0
    prevTotalCompleted = 0
    initDisplay()
    startPolling()
  }
}

// 【终极修复：带有发送 POST 停止指令的完整方法】
const stopSimulation = async () => {
  isSimulating.value = false
  isPaused.value = false
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  
  try {
    // 通知后端彻底停止
    await axios.post('http://127.0.0.1:8000/api/stop')
    errorMessage.value = '仿真已手动终止'
    setTimeout(() => { errorMessage.value = '' }, 3000)
  } catch (error) {
    console.error('终止后端仿真失败:', error)
  }
}

// 切换暂停
const togglePause = () => {
  isPaused.value = !isPaused.value
}

// 重置配置
const resetToDefault = () => {
  if (!isSimulating.value) {
    config.windowCount = 10
    config.tableCount = 25
    config.servingSpeed = 1
    config.arrivalRate = 15
    config.simulationDuration = 120
    initDisplay()
  }
}

// 暴露 Math 方法给模板
const round = (v) => Math.round(v)
const ceil = (v) => Math.ceil(v)
const min = (a, b) => Math.min(a, b)

// 获取窗口颜色
const getWindowColor = (queueLength) => {
  if (queueLength < 3) return 'linear-gradient(135deg, #d4edda, #c3e6cb)'
  if (queueLength < 7) return 'linear-gradient(135deg, #fff3cd, #ffeaa7)'
  return 'linear-gradient(135deg, #f8d7da, #f5c6cb)'
}

// 格式化时间
const formatTime = (minutes) => {
  const mins = Math.floor(minutes)
  const secs = Math.floor((minutes % 1) * 60)
  return `${mins}:${String(secs).padStart(2, '0')}`
}

// 监听速度变化
watch(playbackSpeed, () => {
  if (isSimulating.value && !isPaused.value) {
    startPolling()
  }
})

// 监听配置变化
watch([() => config.windowCount, () => config.tableCount], () => {
  if (!isSimulating.value) {
    initDisplay()
  }
})

onMounted(() => {
  initDisplay()
  // 检查是否需要自动开始仿真（由SimulationView触发）
  loadAndStartSimulation()
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
})
</script>

<style scoped>
/* 保持原有样式不变 */
.cafeteria-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

h1 {
  color: white;
  margin: 0;
  font-size: 2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.simulation-controls {
  background: white;
  padding: 15px 25px;
  border-radius: 50px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  gap: 25px;
  flex-wrap: wrap;
}

.simulation-status {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

.time-display {
  font-weight: 600;
  color: #2c3e50;
  font-family: monospace;
  font-size: 1.1rem;
}

.progress-text {
  color: #666;
  font-size: 0.9rem;
}

.control-buttons {
  display: flex;
  gap: 10px;
}

.control-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 25px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s;
  background: #3498db;
  color: white;
  font-weight: 500;
}

.control-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
}

.control-btn.paused {
  background: #f39c12;
}

.control-btn.stop-btn {
  background: #e74c3c;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.speed-slider {
  width: 120px;
  height: 6px;
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}

.speed-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: #667eea;
  border-radius: 50%;
  cursor: pointer;
}

.speed-value {
  min-width: 45px;
  font-weight: bold;
  color: #667eea;
}

.control-panel {
  background: white;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  display: flex;
  gap: 25px;
  flex-wrap: wrap;
  align-items: center;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 200px;
}

.control-item label {
  font-weight: 600;
  color: #555;
}

.control-item input {
  width: 100%;
}

.reset-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.reset-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.cafeteria-layout {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  position: relative;
  margin-bottom: 20px;
  min-height: 600px;
}

.entrance, .exit {
  position: absolute;
  top: 20px;
  text-align: center;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  padding: 15px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 10;
  min-width: 140px;
}

.entrance {
  left: 20px;
}

.exit {
  right: 20px;
}

.entrance-icon, .exit-icon {
  font-size: 36px;
}

.entrance-label, .exit-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
  font-weight: 500;
}

.entrance-stats, .exit-stats {
  margin-top: 10px;
  font-size: 13px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  gap: 10px;
}

.stat-row .value {
  font-weight: bold;
  color: #2c3e50;
}

.stat-row .value.highlight {
  color: #e74c3c;
  font-size: 1.1rem;
}

.arrival-animation, .exit-animation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1000;
}

.arriving-student, .leaving-student {
  position: absolute;
  font-size: 28px;
  animation: arrive 2s ease-out forwards;
}

@keyframes arrive {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
  }
  20% {
    transform: translate(-50%, -50%) scale(1.2);
    opacity: 1;
  }
  80% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -100%) scale(0.8);
    opacity: 0;
  }
}

.leaving-student {
  animation: leave 2s ease-out forwards;
}

@keyframes leave {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  50% {
    transform: translate(-50%, -150%) scale(1.2);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -300%) scale(0);
    opacity: 0;
  }
}

.windows-area, .dining-area {
  margin-top: 80px;
}

.windows-area h3, .dining-area h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1.3rem;
}

.windows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.window-card {
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  transition: all 0.3s;
  cursor: pointer;
}

.window-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.window-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.window-number {
  font-size: 18px;
  font-weight: bold;
  color: #2c3e50;
}

.serving-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  background: #ff4757;
  color: white;
  padding: 3px 10px;
  border-radius: 20px;
}

.pulse {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.queue-info, .service-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
  color: #555;
}

.queue-bars {
  display: flex;
  gap: 2px;
  margin-top: 4px;
}

.queue-bar {
  height: 3px;
  background: #3498db;
  border-radius: 2px;
  transition: width 0.3s;
}

.queue-visual {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0,0,0,0.1);
}

.person-icon {
  font-size: 22px;
  animation: bounceIn 0.5s ease-out;
}

@keyframes bounceIn {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 15px;
}

.table-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s;
}

.table-card.table-full {
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
  border: 2px solid #ffc107;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-number {
  font-weight: bold;
  color: #2c3e50;
}

.table-status {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  background: #e0e0e0;
  color: #666;
  font-weight: 500;
}

.seats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.seat {
  background: white;
  padding: 12px;
  text-align: center;
  border-radius: 10px;
  border: 2px solid #e0e0e0;
  transition: all 0.3s;
  position: relative;
}

.seat.occupied {
  background: linear-gradient(135deg, #a8e6cf, #d4edda);
  border-color: #28a745;
  animation: seatOccupy 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes seatOccupy {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

.seat.seat-animation {
  animation: seatFlash 0.5s ease-in-out;
}

@keyframes seatFlash {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); background: #ffeaa7; }
}

.seat-icon {
  font-size: 28px;
}

.eating-timer {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  white-space: nowrap;
}

.timer-bar {
  position: absolute;
  bottom: -20px;
  left: 0;
  height: 2px;
  background: #28a745;
  transition: width 0.3s;
}

.table-progress {
  margin-top: 10px;
}

.progress-bar {
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s;
}

.stats-panel {
  margin-top: 20px;
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stats-panel h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.3s;
}

.stat-item:hover {
  transform: translateX(5px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-item.highlight {
  background: linear-gradient(135deg, #e3f2fd, #bbdef5);
  border-left: 3px solid #2196f3;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #2c3e50;
}

.progress-bar-container {
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-label {
  position: absolute;
  right: 5px;
  top: -20px;
  font-size: 11px;
  color: #667eea;
  font-weight: bold;
}

.error-message {
  margin-top: 20px;
  padding: 15px 20px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 12px;
  border-left: 4px solid #f5c6cb;
  display: flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .cafeteria-view {
    padding: 10px;
  }

  .entrance, .exit {
    position: static;
    margin-bottom: 15px;
  }

  .windows-area, .dining-area {
    margin-top: 20px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>