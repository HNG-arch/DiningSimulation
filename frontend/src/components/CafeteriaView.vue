<template>
  <div class="cafeteria-view">
    <!-- 顶部控制栏 -->
    <div class="top-bar">
      <div class="top-left">
        <h1 class="page-title">食堂场景模拟</h1>
        <span class="sim-badge" v-if="isSimulating" :class="{ paused: isPaused }">
          {{ isPaused ? '已暂停' : '运行中' }}
        </span>
      </div>

      <div class="top-center" v-if="isSimulating">
        <div class="time-bar-wrapper">
          <div class="time-bar">
            <div class="time-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
          <span class="time-text">{{ formatTime(currentTime) }} / {{ formatTime(totalTime) }} min</span>
        </div>
      </div>

      <div class="top-right">
        <div class="speed-group">
          <button class="speed-btn" @click="playbackSpeed = Math.max(1, playbackSpeed - 1)">−</button>
          <span class="speed-label">{{ playbackSpeed }}x</span>
          <button class="speed-btn" @click="playbackSpeed = Math.min(20, playbackSpeed + 1)">+</button>
        </div>
        <button v-if="isSimulating" @click="togglePause" class="ctrl-btn" :class="{ warn: isPaused }">
          {{ isPaused ? '继续' : '暂停' }}
        </button>
        <button v-if="isSimulating" @click="stopSimulation" class="ctrl-btn danger">终止</button>
      </div>
    </div>

    <!-- 主体三栏布局 -->
    <div class="main-area">
      <!-- 左栏：实时图表 -->
      <div class="left-panel">
        <div class="mini-chart-card">
          <div class="chart-title">等待时间趋势</div>
          <svg class="mini-svg" :viewBox="'0 0 200 80'" preserveAspectRatio="none">
            <line x1="0" y1="28" x2="200" y2="28" stroke="#f0f0f0" stroke-width="1" />
            <line x1="0" y1="54" x2="200" y2="54" stroke="#f0f0f0" stroke-width="1" />
            <polygon :points="waitAreaPoints" fill="#667eea" opacity="0.1" />
            <polyline :points="waitChartPoints" fill="none" stroke="#667eea" stroke-width="1.5" vector-effect="non-scaling-stroke" />
            <text v-if="waitHistory.length < 2" x="100" y="46" text-anchor="middle" fill="#d9d9d9" font-size="9" font-family="sans-serif">等待数据...</text>
          </svg>
          <div class="chart-value">{{ avgWaitTime.toFixed(1) }}<span class="unit"> min</span></div>
        </div>

        <div class="mini-chart-card">
          <div class="chart-title">窗口负载</div>
          <div class="bar-chart">
            <div class="bar-item" v-for="w in windows" :key="w.id">
              <div class="bar-label">{{ w.id }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ height: barHeight(w.queueLength) + '%', background: queueColor(w.queueLength) }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="mini-chart-card">
          <div class="chart-title">就餐人数趋势</div>
          <svg class="mini-svg" :viewBox="'0 0 200 80'" preserveAspectRatio="none">
            <line x1="0" y1="28" x2="200" y2="28" stroke="#f0f0f0" stroke-width="1" />
            <line x1="0" y1="54" x2="200" y2="54" stroke="#f0f0f0" stroke-width="1" />
            <polygon :points="eatingAreaPoints" fill="#52c41a" opacity="0.1" />
            <polyline :points="eatingChartPoints" fill="none" stroke="#52c41a" stroke-width="1.5" vector-effect="non-scaling-stroke" />
            <text v-if="eatingHistory.length < 2" x="100" y="46" text-anchor="middle" fill="#d9d9d9" font-size="9" font-family="sans-serif">等待数据...</text>
          </svg>
          <div class="chart-value green">{{ eatingCount }}<span class="unit">人</span></div>
        </div>

        <div class="mini-chart-card">
          <div class="chart-title">满意度</div>
          <div class="gauge-bar">
            <div class="gauge-track">
              <div class="gauge-fill" :style="{ width: (satisfaction * 100).toFixed(0) + '%' }"></div>
            </div>
          </div>
          <div class="chart-value" :class="satisfaction >= 0.8 ? 'green' : satisfaction >= 0.5 ? 'yellow' : 'red'">
            {{ (satisfaction * 100).toFixed(1) }}<span class="unit">%</span>
          </div>
        </div>

        <div class="mini-chart-card">
          <div class="chart-title">完成进度</div>
          <div class="ring-container">
            <svg class="ring-svg" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="32" fill="none" stroke="#e8e8e8" stroke-width="6" />
              <circle cx="40" cy="40" r="32" fill="none" stroke="#667eea" stroke-width="6" stroke-linecap="round"
                :stroke-dasharray="ringDasharray" transform="rotate(-90 40 40)" style="transition: stroke-dasharray 0.5s" />
            </svg>
            <div class="ring-center">
              <div class="ring-big">{{ Math.round(progressPercentage) }}%</div>
              <div class="ring-sub">{{ totalCompleted }}/{{ totalStudents }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中栏：食堂平面图 -->
      <div class="center-panel">
        <!-- 入口区 -->
        <div class="entry-zone">
          <div class="zone-icon">入口</div>
          <div class="arrival-anchor">
            <span v-for="a in arrivingAnimations" :key="a.id" class="arrive-dot" :style="{ animationDelay: a.delay + 'ms' }"></span>
          </div>
          <div class="entry-stats">
            <span>到达 {{ totalArrived }}人</span>
            <span class="dot-sep">·</span>
            <span>到达率 {{ config.arrivalRate }}/min</span>
          </div>
        </div>

        <!-- 人流过道 -->
        <div class="aisle-flow">
          <span v-for="i in flowCount" :key="'f1-'+i" class="flow-particle"
            :style="{ animationDelay: (i * 0.15) + 's', left: (10 + Math.random() * 80) + '%' }"></span>
        </div>

        <!-- 窗口区 -->
        <div class="windows-zone">
          <div class="windows-row" :style="{ '--n': Math.min(windows.length, 20) }">
            <div v-for="w in windows" :key="w.id" class="window-card"
              :class="{ 'is-serving': w.isServing }"
              :style="{ '--qc': queueColor(w.queueLength), borderColor: queueColor(w.queueLength), boxShadow: w.isServing ? '0 0 0 2px '+queueColor(w.queueLength)+'30, 0 4px 18px '+queueColor(w.queueLength)+'25' : 'none' }">
              <div class="win-header">
                <span class="win-num">{{ w.id }}</span>
                <span class="win-served">{{ w.totalServed }}</span>
              </div>
              <div class="win-queue">
                <span v-for="i in Math.min(w.queueLength, 12)" :key="i" class="queue-dot"
                  :style="{ background: queueColor(w.queueLength), animationDelay: i * 0.05 + 's' }"></span>
                <span v-if="w.queueLength > 12" class="queue-more">+{{ w.queueLength - 12 }}</span>
                <span v-if="w.queueLength === 0" class="queue-empty">空</span>
              </div>
              <div class="win-footer" :class="{ serving: w.isServing }">
                {{ w.isServing ? '服务中' : '空闲' }}
              </div>
              <div class="win-glow" v-if="w.isServing"></div>
            </div>
          </div>
        </div>

        <!-- 人流过道 -->
        <div class="aisle-flow wide">
          <span v-for="i in flowCount" :key="'f2-'+i" class="flow-particle down"
            :style="{ animationDelay: (i * 0.2) + 's', left: (5 + Math.random() * 90) + '%' }"></span>
        </div>

        <!-- 座位区 -->
        <div class="seats-zone">
          <div class="seats-grid" :style="{ '--cols': seatCols }">
            <div v-for="table in diningTables" :key="table.id" class="table-unit"
              :class="{ 'has-people': table.occupiedSeats > 0 }">
              <div class="table-top"></div>
              <div class="table-seats">
                <div v-for="(seat, si) in table.seats" :key="si" class="seat-dot"
                  :class="{ occupied: seat.occupied, finishing: seat.occupied && seat.remainingTime < 30, popping: seat.justOccupied }">
                  <span v-if="seat.occupied" class="seat-timer">{{ Math.ceil(seat.remainingTime) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="waitingSeatCount > 0" class="waiting-zone">
            <span class="waiting-icon">⏳</span>
            <span>{{ waitingSeatCount }}人等待座位</span>
          </div>
        </div>

        <!-- 出口区 -->
        <div class="exit-zone">
          <div class="zone-icon">出口</div>
          <div class="exit-anchor">
            <span v-for="l in leavingAnimations" :key="l.id" class="leave-dot" :style="{ animationDelay: l.delay + 'ms' }"></span>
          </div>
          <div class="exit-stats-text">
            <span>离开 {{ totalCompleted }}人</span>
            <span class="dot-sep">·</span>
            <span>完成率 {{ completionRate }}%</span>
          </div>
        </div>
      </div>

      <!-- 右栏：实时统计 -->
      <div class="right-panel">
        <div class="stat-card">
          <div class="stat-icon s-blue">👥</div>
          <div class="stat-body">
            <div class="stat-label">总排队人数</div>
            <div class="stat-num">{{ totalQueueLength }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon s-green">🪑</div>
          <div class="stat-body">
            <div class="stat-label">空余座位</div>
            <div class="stat-num">{{ emptySeats }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon s-orange">🍽️</div>
          <div class="stat-body">
            <div class="stat-label">正在就餐</div>
            <div class="stat-num">{{ diningPeople }}</div>
          </div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-icon s-purple">⏰</div>
          <div class="stat-body">
            <div class="stat-label">平均等待</div>
            <div class="stat-num">{{ avgWaitTime.toFixed(1) }}<span class="num-unit">min</span></div>
          </div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-icon s-purple">✅</div>
          <div class="stat-body">
            <div class="stat-label">已完成</div>
            <div class="stat-num">{{ totalCompleted }}<span class="num-unit">/{{ totalStudents }}</span></div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon s-teal">🔄</div>
          <div class="stat-body">
            <div class="stat-label">座位周转率</div>
            <div class="stat-num">{{ seatTurnover.toFixed(2) }}<span class="num-unit">次/时</span></div>
          </div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-icon s-purple">😊</div>
          <div class="stat-body">
            <div class="stat-label">满意度</div>
            <div class="stat-num">{{ (satisfaction * 100).toFixed(1) }}<span class="num-unit">%</span></div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="errorMessage" class="toast">{{ errorMessage }}</div>
    <div v-if="!isSimulating && totalCompleted === 0" class="empty-hint">
      请先在「运行仿真」页面配置参数并启动仿真
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import { useSimulationStore } from '../stores/simulation.js'

const route = useRoute()
const store = useSimulationStore()
const config = store.config

const windows = ref([])
const diningTables = ref([])
const isSimulating = ref(false)
const isPaused = ref(false)
const playbackSpeed = ref(5)
const totalTime = ref(60)
const currentTime = ref(0)
const avgWaitTime = ref(0)
const seatTurnover = ref(0)
const totalArrived = ref(0)
const totalCompleted = ref(0)
const eatingCount = ref(0)
const satisfaction = ref(0)
const errorMessage = ref('')
const waitingSeatCount = ref(0)

const arrivingAnimations = ref([])
const leavingAnimations = ref([])
let animIdCounter = 0
let pollingInterval = null
let prevTotalArrived = 0
let prevTotalCompleted = 0

const waitHistory = ref([])
const eatingHistory = ref([])

const flowCount = computed(() => Math.min(Math.floor(totalArrived.value / 3), 12))
const seatCols = computed(() => Math.min(Math.ceil(Math.sqrt(config.tableCount)), 10))

const progressPercentage = computed(() => totalTime.value ? (currentTime.value / totalTime.value) * 100 : 0)
const totalQueueLength = computed(() => windows.value.reduce((sum, w) => sum + (w.queueLength || 0), 0))
const emptySeats = computed(() => config.tableCount * 4 - eatingCount.value)
const diningPeople = computed(() => eatingCount.value)
const totalStudents = computed(() => Math.floor(config.arrivalRate * totalTime.value))
const completionRate = computed(() => totalStudents.value ? ((totalCompleted.value / totalStudents.value) * 100).toFixed(1) : 0)

const ringDasharray = computed(() => {
  const c = 2 * Math.PI * 32; const p = Math.min(progressPercentage.value, 100) / 100
  return `${(c * p).toFixed(1)} ${c.toFixed(1)}`
})

const barHeight = (len) => {
  const maxQ = Math.max(...windows.value.map(w => w.queueLength || 0), 1)
  return (len / maxQ) * 100
}

const queueColor = (len) => {
  if (len <= 2) return '#52c41a'
  if (len <= 6) return '#faad14'
  if (len <= 10) return '#fa8c16'
  return '#f5222d'
}

const waitChartPoints = computed(() => {
  const arr = waitHistory.value
  if (arr.length < 2) return '0,80 200,80'
  const maxVal = Math.max(...arr, 0.5); const h = 72
  return arr.map((v, i) => `${(i / Math.max(arr.length - 1, 1)) * 200},${h - (v / maxVal) * h + 4}`).join(' ')
})

const eatingChartPoints = computed(() => {
  const arr = eatingHistory.value
  if (arr.length < 2) return '0,80 200,80'
  const maxVal = Math.max(...arr, 1); const h = 72
  return arr.map((v, i) => `${(i / Math.max(arr.length - 1, 1)) * 200},${h - (v / maxVal) * h + 4}`).join(' ')
})

const waitAreaPoints = computed(() => {
  const arr = waitHistory.value
  if (arr.length < 2) return '0,80 200,80'
  const maxVal = Math.max(...arr, 0.5); const h = 72
  const pts = arr.map((v, i) => `${(i / Math.max(arr.length - 1, 1)) * 200},${h - (v / maxVal) * h + 4}`).join(' ')
  return `${pts} 200,80 0,80`
})

const eatingAreaPoints = computed(() => {
  const arr = eatingHistory.value
  if (arr.length < 2) return '0,80 200,80'
  const maxVal = Math.max(...arr, 1); const h = 72
  const pts = arr.map((v, i) => `${(i / Math.max(arr.length - 1, 1)) * 200},${h - (v / maxVal) * h + 4}`).join(' ')
  return `${pts} 200,80 0,80`
})

const triggerArrivalAnim = (count) => {
  for (let i = 0; i < Math.min(count, 5); i++) {
    const id = animIdCounter++; arrivingAnimations.value.push({ id, delay: i * 80 })
    setTimeout(() => { arrivingAnimations.value = arrivingAnimations.value.filter(a => a.id !== id) }, 2000)
  }
}
const triggerLeaveAnim = (count) => {
  for (let i = 0; i < Math.min(count, 5); i++) {
    const id = animIdCounter++; leavingAnimations.value.push({ id, delay: i * 80 })
    setTimeout(() => { leavingAnimations.value = leavingAnimations.value.filter(a => a.id !== id) }, 2000)
  }
}

const initWindows = () => { windows.value = Array.from({ length: config.windowCount }, (_, i) => ({ id: i + 1, queueLength: 0, totalServed: 0, isServing: false })) }
const initTables = () => { diningTables.value = Array.from({ length: config.tableCount }, (_, i) => ({ id: i + 1, seats: Array.from({ length: 4 }, () => ({ occupied: false, remainingTime: 0, justOccupied: false })), occupiedSeats: 0 })) }
const initDisplay = () => { initWindows(); initTables(); waitHistory.value = []; eatingHistory.value = [] }

const updateDisplay = (state) => {
  if (!state) return
  currentTime.value = state.current_time || 0; avgWaitTime.value = state.statistics?.avg_wait_time || 0
  seatTurnover.value = state.statistics?.seat_turnover || 0; satisfaction.value = state.statistics?.satisfaction || 0
  totalArrived.value = state.total_arrived || 0; totalCompleted.value = state.total_completed || 0
  eatingCount.value = state.eating_count || 0; waitingSeatCount.value = state.waiting_seat || 0
  if (Math.round(currentTime.value * 10) % 3 === 0) { waitHistory.value.push(avgWaitTime.value); if (waitHistory.value.length > 60) waitHistory.value.shift() }
  if (Math.round(currentTime.value * 10) % 4 === 0) { eatingHistory.value.push(eatingCount.value); if (eatingHistory.value.length > 50) eatingHistory.value.shift() }
  if (totalArrived.value > prevTotalArrived) triggerArrivalAnim(totalArrived.value - prevTotalArrived)
  prevTotalArrived = totalArrived.value
  if (totalCompleted.value > prevTotalCompleted) triggerLeaveAnim(totalCompleted.value - prevTotalCompleted)
  prevTotalCompleted = totalCompleted.value
  if (state.windows?.length) state.windows.forEach((ws, idx) => { if (windows.value[idx]) { windows.value[idx].queueLength = ws.queue_length || 0; windows.value[idx].totalServed = ws.total_served || 0; windows.value[idx].isServing = ws.serve_time_left > 0 } })
  if (state.seats && diningTables.value.length) updateSeats(state.seats)
}

const updateSeats = (seatsData) => {
  const sm = seatsData.data || []; if (!sm.length) return
  const fs = []; for (let r = 0; r < seatsData.rows; r++) for (let c = 0; c < seatsData.cols; c++) { if (r < sm.length && c < sm[r].length) fs.push(sm[r][c]) }
  let fi = 0
  diningTables.value.forEach(t => {
    let oc = 0; for (let s = 0; s < 4; s++) {
      const rs = fi < fs.length ? fs[fi] : 0; fi++; const io = rs > 0; const wo = t.seats[s]?.occupied
      if (io && !wo) { t.seats[s] = { occupied: true, remainingTime: rs, justOccupied: true }; oc++; setTimeout(() => { if (t.seats[s]) t.seats[s].justOccupied = false }, 500) }
      else if (!io && wo) { t.seats[s] = { occupied: false, remainingTime: 0, justOccupied: false } }
      else if (io && wo && t.seats[s]) { t.seats[s].remainingTime = rs; t.seats[s].justOccupied = false; oc++ }
    }
    t.occupiedSeats = oc
  })
}

const startPolling = () => {
  if (pollingInterval) clearInterval(pollingInterval)
  pollingInterval = setInterval(async () => {
    if (!isPaused.value && isSimulating.value) {
      try {
        const r = await axios.get('http://127.0.0.1:8000/api/state')
        if (r.data.success && r.data.state) { updateDisplay(r.data.state); if (r.data.state.current_time >= totalTime.value) await endCleanup() }
      } catch (e) { console.error(e) }
    }
  }, Math.max(400, 2000 / playbackSpeed.value))
}

const endCleanup = async () => {
  if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null }
  isSimulating.value = false
  try {
    const sr = await axios.get('http://127.0.0.1:8000/api/stats')
    if (sr.data.success && sr.data.is_finished) {
      const rr = await axios.get('http://127.0.0.1:8000/api/simulation/results')
      if (rr.data.length) store.setLastSimulationId(rr.data[0].id)
      errorMessage.value = '仿真已完成！可前往「决策分析」查看详细结果。'
      setTimeout(() => { errorMessage.value = '' }, 5000)
    }
  } catch (e) { console.error(e) }
}

const loadAndStart = () => {
  totalTime.value = config.simulationDuration || 60
  playbackSpeed.value = store.simulationSpeed || 5
  if (route.query.running === 'true') {
    const rs = parseInt(route.query.speed); if (rs) playbackSpeed.value = rs
    isSimulating.value = true; isPaused.value = false; errorMessage.value = ''
    animIdCounter = 0; prevTotalArrived = 0; prevTotalCompleted = 0
    initDisplay(); startPolling()
  }
}

const stopSimulation = async () => {
  isSimulating.value = false; isPaused.value = false
  if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null }
  try { await axios.post('http://127.0.0.1:8000/api/stop'); errorMessage.value = '仿真已手动终止'; setTimeout(() => { errorMessage.value = '' }, 3000) } catch (e) { }
}
const togglePause = () => { isPaused.value = !isPaused.value }
const formatTime = (m) => { const mi = Math.floor(m), s = Math.floor((m % 1) * 60); return `${mi}:${String(s).padStart(2, '0')}` }

watch(playbackSpeed, () => { if (isSimulating.value && !isPaused.value) startPolling() })
watch([() => config.windowCount, () => config.tableCount], () => { if (!isSimulating.value) initDisplay() })
onMounted(() => { initDisplay(); loadAndStart() })
onUnmounted(() => { if (pollingInterval) clearInterval(pollingInterval) })
</script>

<style scoped>
.cafeteria-view {
  height: 100vh;
  background: #f0f2f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ========== 顶部控制栏 ========== */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: #fff; border-bottom: 1px solid #e8e8e8;
  position: sticky; top: 60px; z-index: 100; gap: 16px;
}
.top-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 1.15rem; font-weight: 700; color: #1a1a1a; margin: 0; }
.sim-badge { font-size: 0.75rem; padding: 2px 10px; border-radius: 10px; background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.sim-badge.paused { background: #fff7e6; color: #fa8c16; border-color: #ffd591; }
.top-center { flex: 1; max-width: 400px; }
.time-bar-wrapper { display: flex; align-items: center; gap: 10px; }
.time-bar { flex: 1; height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.time-fill { height: 100%; background: #667eea; border-radius: 3px; transition: width 0.3s; }
.time-text { font-size: 0.8rem; color: #8c8c8c; white-space: nowrap; }
.top-right { display: flex; align-items: center; gap: 8px; }
.speed-group { display: flex; align-items: center; gap: 4px; }
.speed-btn { width: 26px; height: 26px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.9rem; line-height: 1; color: #595959; }
.speed-btn:hover { border-color: #667eea; color: #667eea; }
.speed-label { font-size: 0.85rem; font-weight: 600; color: #1a1a1a; min-width: 32px; text-align: center; }
.ctrl-btn { padding: 5px 16px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.85rem; color: #595959; }
.ctrl-btn:hover { border-color: #667eea; color: #667eea; }
.ctrl-btn.warn { background: #fff7e6; border-color: #fa8c16; color: #fa8c16; }
.ctrl-btn.danger { background: #fff1f0; border-color: #f5222d; color: #f5222d; }

/* ========== 三栏主体 ========== */
.main-area { display: flex; gap: 8px; margin-top: 8px; height: calc(100vh - 48px - 52px - 16px); }

/* ========== 左栏 ========== */
.left-panel { width: 180px; flex-shrink: 0; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
.mini-chart-card { background: #fff; border-radius: 8px; padding: 8px 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.chart-title { font-size: 0.72rem; color: #8c8c8c; margin-bottom: 4px; }
.mini-svg { width: 100%; height: 60px; }
.chart-value { text-align: right; font-size: 1.1rem; font-weight: 700; color: #1a1a1a; margin-top: 2px; }
.chart-value .unit { font-size: 0.65rem; font-weight: 400; color: #8c8c8c; }
.chart-value.green { color: #52c41a; }
.chart-value.yellow { color: #faad14; }
.chart-value.red { color: #f5222d; }

.bar-chart { display: flex; align-items: flex-end; gap: 3px; height: 60px; }
.bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.bar-label { font-size: 0.55rem; color: #bfbfbf; margin-bottom: 1px; }
.bar-track { width: 100%; height: 50px; background: #f5f5f5; border-radius: 2px 2px 0 0; }
.bar-fill { height: 100%; border-radius: 2px 2px 0 0; transition: height 0.4s; min-height: 1px; }

.gauge-bar { padding: 2px 0; }
.gauge-track { width: 100%; height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; margin: 2px 0; }
.gauge-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #f5222d, #faad14, #52c41a); transition: width 0.5s; }

.ring-container { position: relative; width: 76px; height: 76px; margin: 0 auto; }
.ring-svg { width: 76px; height: 76px; }
.ring-svg circle:last-of-type { filter: drop-shadow(0 0 3px rgba(102,126,234,0.5)); }
.ring-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.ring-big { font-size: 0.95rem; font-weight: 700; color: #1a1a1a; }
.ring-sub { font-size: 0.55rem; color: #bfbfbf; }

/* ========== 中栏 ========== */
.center-panel { flex: 1; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); padding: 8px 12px; display: flex; flex-direction: column; align-items: center; gap: 3px; overflow: hidden; }

.entry-zone {
  text-align: center; padding: 6px 12px;
  background: linear-gradient(180deg, #e8f4ff, #f0f7ff);
  border: 1px solid #bdd7ff;
  border-bottom: 2px solid #4096ff;
  border-radius: 8px; width: 100%; max-width: 700px; position: relative;
}
.exit-zone {
  text-align: center; padding: 6px 12px;
  background: linear-gradient(0deg, #f0fff0, #f6fff6);
  border: 1px solid #b7ebc0;
  border-top: 2px solid #52c41a;
  border-radius: 8px; width: 100%; max-width: 700px; position: relative;
}
.zone-icon { font-size: 0.85rem; font-weight: 700; color: #1a1a1a; letter-spacing: 0.5px; }
.entry-stats, .exit-stats-text { font-size: 0.7rem; color: #8c8c8c; margin-top: 2px; }
.dot-sep { margin: 0 4px; }

.arrival-anchor, .exit-anchor { position: absolute; top: -8px; left: 50%; transform: translateX(-50%); display: flex; gap: 4px; }
.arrive-dot, .leave-dot { width: 8px; height: 8px; border-radius: 50%; animation: popDot 1.2s ease-out forwards; }
.arrive-dot { background: #1890ff; }
.leave-dot { background: #52c41a; }
@keyframes popDot { 0% { opacity: 1; transform: translateY(0) scale(1); } 100% { opacity: 0; transform: translateY(-30px) scale(0); } }

/* 过道人流 */
.aisle-flow { width: 100%; max-width: 700px; height: 14px; position: relative; overflow: hidden; background: linear-gradient(90deg, transparent, #fafafa, transparent); border-radius: 3px; }
.aisle-flow.wide { height: 18px; }
.flow-particle { position: absolute; top: 50%; width: 4px; height: 4px; border-radius: 50%; background: #1890ff; opacity: 0.5; animation: fpFlow 2s linear infinite; }
.flow-particle.down { animation-name: fpFlow; background: #667eea; }
@keyframes fpFlow { 0% { transform: translateY(-200%); opacity: 0; } 30% { opacity: 0.6; } 70% { opacity: 0.6; } 100% { transform: translateY(400%); opacity: 0; } }

/* 窗口区 */
.windows-zone { width: 100%; max-width: 700px; overflow-x: auto; padding: 2px 0; }
.windows-row { display: flex; gap: 4px; justify-content: center; }
.window-card { width: calc((100% - 4px * (var(--n) - 1)) / var(--n)); min-width: 46px; max-width: 100px; background: #fff; border: 2px solid #e8e8e8; border-radius: 8px; padding: 4px; text-align: center; transition: border-color 0.3s, box-shadow 0.3s; position: relative; overflow: hidden; }
.win-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.win-num { font-size: 0.72rem; font-weight: 600; color: #1a1a1a; }
.win-served { font-size: 0.6rem; color: #bfbfbf; }
.win-queue { display: flex; flex-wrap: wrap; justify-content: center; gap: 2px; min-height: 20px; margin: 3px 0; align-content: flex-start; }
.queue-dot { width: 5px; height: 5px; border-radius: 50%; background: #52c41a; animation: qJoin 0.3s ease-out; }
@keyframes qJoin { 0% { transform: translateY(-6px); opacity: 0; } 100% { transform: translateY(0); opacity: 1; } }
.queue-more { font-size: 0.55rem; color: #f5222d; font-weight: 600; margin-left: 2px; }
.queue-empty { font-size: 0.55rem; color: #d9d9d9; }
.win-footer { font-size: 0.58rem; color: #bfbfbf; margin-top: 1px; }
.win-footer.serving { color: #52c41a; font-weight: 500; }
.window-card.is-serving { transform: translateY(-1px); }
.win-glow {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--qc, #52c41a), transparent);
  border-radius: 8px 8px 0 0;
  animation: scanLine 1.4s ease-in-out infinite;
  transform-origin: center;
}
@keyframes scanLine {
  0%, 100% { transform: scaleX(0.2); opacity: 0.5; }
  50% { transform: scaleX(1); opacity: 1; }
}

/* 座位区 */
.seats-zone { flex: 1; width: 100%; max-width: 700px; background: #f5f5f7; border-radius: 8px; padding: 8px; position: relative; overflow-y: auto; min-height: 0; }
.seats-grid { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; align-content: flex-start; }
.table-unit {
  width: calc((100% - 6px * (var(--cols) - 1)) / var(--cols));
  min-width: 38px; max-width: 64px;
  background: #fff;
  border: 1px solid #e8e2d8;
  border-radius: 10px;
  padding: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.table-unit.has-people {
  border-color: #91caff;
  box-shadow: 0 2px 8px rgba(24,144,255,0.12);
}
.table-top {
  width: 65%; height: 5px;
  background: linear-gradient(90deg, #e0d8cc, #ccc5ba, #e0d8cc);
  border-radius: 3px;
}
.table-unit.has-people .table-top {
  background: linear-gradient(90deg, #91caff, #69b1ff, #91caff);
}
.table-seats { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; width: 100%; }
.seat-dot {
  width: 100%; aspect-ratio: 1;
  border-radius: 40%;
  background: #f2ede5;
  border: 1.5px solid #e0d8cc;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.25s, border-color 0.25s, box-shadow 0.25s;
}
.seat-dot.occupied {
  background: #1890ff;
  border-color: #40a9ff;
  box-shadow: 0 1px 4px rgba(24,144,255,0.35);
}
.seat-dot.finishing {
  background: #52c41a;
  border-color: #73d13d;
  animation: finishPulse 1.4s ease-in-out infinite;
}
@keyframes finishPulse {
  0%, 100% { box-shadow: 0 0 0 0px rgba(82,196,26,0.4); }
  50% { box-shadow: 0 0 0 4px rgba(82,196,26,0.0); }
}
.seat-dot.popping { animation: seatPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
@keyframes seatPop { 0% { transform: scale(0); } 60% { transform: scale(1.15); } 100% { transform: scale(1); } }
.seat-timer { font-size: 0.45rem; color: #fff; font-weight: 700; line-height: 1; }
.waiting-zone { margin-top: 6px; text-align: center; font-size: 0.7rem; color: #fa8c16; background: #fff7e6; border-radius: 6px; padding: 3px 10px; display: inline-block; position: absolute; bottom: 6px; right: 8px; }
.waiting-icon { margin-right: 3px; }

/* ========== 右栏 ========== */
.right-panel { width: 160px; flex-shrink: 0; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
.stat-card {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border-radius: 8px; padding: 8px 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border-left: 3px solid transparent;
  transition: border-color 0.2s;
}
.stat-card.highlight { background: #f9f7ff; border-left-color: #667eea; }
.stat-icon { font-size: 1rem; width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.s-blue { background: #e6f7ff; border-color: #1890ff; }
.s-green { background: #f6ffed; }
.s-orange { background: #fff7e6; }
.s-purple { background: #f9f0ff; }
.s-teal { background: #e6fffb; }
.stat-body { flex: 1; min-width: 0; }
.stat-label { font-size: 0.6rem; color: #bfbfbf; }
.stat-num { font-size: 0.95rem; font-weight: 700; color: #1a1a1a; transition: color 0.3s; }
.stat-num .num-unit { font-size: 0.55rem; font-weight: 400; color: #8c8c8c; margin-left: 1px; }

.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); padding: 10px 24px; background: #1a1a1a; color: #fff; border-radius: 8px; font-size: 0.85rem; z-index: 1000; }
.empty-hint { text-align: center; padding: 60px 20px; color: #bfbfbf; font-size: 0.95rem; }
</style>
