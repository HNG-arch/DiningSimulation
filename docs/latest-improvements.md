# 最新改进建议（供 Claude Code 终端执行）

> 按优先级排列，每条均包含文件路径 + 具体代码。

---

## 改动 A：双门系统（左侧门 + 底部门，均可同时进出）

**文件：** `frontend/src/components/CafeteriaView.vue`

### A1 — Template 重构（中栏布局）

将中栏 `<div class="center-panel">` 内部完全替换为以下结构：

```html
<!-- 中栏：食堂平面图 -->
<div class="center-panel">

  <!-- 左侧门 + 主楼层（并排） -->
  <div class="floor-body">

    <!-- 左侧门 -->
    <div class="door-side">
      <div class="door-label">门 1</div>
      <div class="door-particles-v">
        <span v-for="a in arrivingAnimationsLeft" :key="'la'+a.id"
          class="flow-h enter" :style="{ animationDelay: a.delay + 'ms', top: a.top + '%' }"></span>
        <span v-for="l in leavingAnimationsLeft" :key="'ll'+l.id"
          class="flow-h leave" :style="{ animationDelay: l.delay + 'ms', top: l.top + '%' }"></span>
      </div>
      <div class="door-side-stats">
        <span class="ds-in">↦ {{ leftArrived }}</span>
        <span class="ds-out">↤ {{ leftCompleted }}</span>
      </div>
    </div>

    <!-- 主楼层 -->
    <div class="floor-main">
      <!-- 人流过道（到窗口） -->
      <div class="aisle-flow">
        <span v-for="i in flowCount" :key="'f1-'+i" class="flow-particle"
          :style="{ animationDelay: (i * 0.15) + 's', left: (10 + Math.random() * 80) + '%' }"></span>
      </div>

      <!-- 窗口区 -->
      <div class="windows-zone">
        <div class="windows-row" :style="{ '--n': Math.min(windows.length, 20) }">
          <div v-for="w in windows" :key="w.id" class="window-card"
            :class="{ 'is-serving': w.isServing }"
            :style="{ borderColor: queueColor(w.queueLength), boxShadow: w.isServing ? '0 0 0 2px '+queueColor(w.queueLength)+'30' : 'none' }">
            <div class="win-header">
              <span class="win-num">{{ w.id }}</span>
              <span class="win-served">{{ w.totalServed }}</span>
            </div>
            <div class="win-queue">
              <span v-for="i in Math.min(w.queueLength, 12)" :key="i" class="queue-dot"
                :style="{ background: queueColor(w.queueLength) }"></span>
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

      <!-- 人流过道（到座位） -->
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
          <span>{{ waitingSeatCount }} 人等待座位</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 底部门 -->
  <div class="door-bottom">
    <div class="door-label">门 2</div>
    <div class="door-particles-h">
      <span v-for="a in arrivingAnimationsBottom" :key="'ba'+a.id"
        class="flow-v enter" :style="{ animationDelay: a.delay + 'ms', left: a.left + '%' }"></span>
      <span v-for="l in leavingAnimationsBottom" :key="'bl'+l.id"
        class="flow-v leave" :style="{ animationDelay: l.delay + 'ms', left: l.left + '%' }"></span>
    </div>
    <div class="door-bottom-stats">
      <span class="ds-in">↑ {{ bottomArrived }} 进入</span>
      <span class="ds-sep">·</span>
      <span class="ds-out">{{ bottomCompleted }} 离开 ↓</span>
      <span class="ds-sep">·</span>
      <span class="ds-rate">{{ config.arrivalRate }}/min</span>
    </div>
  </div>
</div>
```

### A2 — Script：替换动画相关变量和函数

**删除**原有这两行：
```js
const arrivingAnimations = ref([])
const leavingAnimations = ref([])
```

**替换为：**
```js
const arrivingAnimationsLeft   = ref([])
const arrivingAnimationsBottom = ref([])
const leavingAnimationsLeft    = ref([])
const leavingAnimationsBottom  = ref([])
const leftArrived     = ref(0)
const leftCompleted   = ref(0)
const bottomArrived   = ref(0)
const bottomCompleted = ref(0)
```

**删除**原有 `triggerArrivalAnim` 和 `triggerLeaveAnim` 两个函数，**替换为：**

```js
const triggerArrivalAnim = (count) => {
  for (let i = 0; i < Math.min(count, 6); i++) {
    const id = animIdCounter++
    if (Math.random() < 0.5) {
      leftArrived.value++
      const item = { id, delay: i * 80, top: 20 + Math.random() * 60 }
      arrivingAnimationsLeft.value.push(item)
      setTimeout(() => { arrivingAnimationsLeft.value = arrivingAnimationsLeft.value.filter(a => a.id !== id) }, 1800)
    } else {
      bottomArrived.value++
      const item = { id, delay: i * 80, left: 15 + Math.random() * 70 }
      arrivingAnimationsBottom.value.push(item)
      setTimeout(() => { arrivingAnimationsBottom.value = arrivingAnimationsBottom.value.filter(a => a.id !== id) }, 1800)
    }
  }
}

const triggerLeaveAnim = (count) => {
  for (let i = 0; i < Math.min(count, 6); i++) {
    const id = animIdCounter++
    if (Math.random() < 0.5) {
      leftCompleted.value++
      const item = { id, delay: i * 80, top: 20 + Math.random() * 60 }
      leavingAnimationsLeft.value.push(item)
      setTimeout(() => { leavingAnimationsLeft.value = leavingAnimationsLeft.value.filter(a => a.id !== id) }, 1800)
    } else {
      bottomCompleted.value++
      const item = { id, delay: i * 80, left: 15 + Math.random() * 70 }
      leavingAnimationsBottom.value.push(item)
      setTimeout(() => { leavingAnimationsBottom.value = leavingAnimationsBottom.value.filter(a => a.id !== id) }, 1800)
    }
  }
}
```

### A3 — CSS：追加到 `<style scoped>` 末尾

```css
/* ========== 双门布局 ========== */
.floor-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.floor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 6px 8px;
}

/* 左侧门 */
.door-side {
  width: 38px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #EEF2FF 0%, #F0FDF4 100%);
  border-right: 2px dashed #C7D2FE;
  border-radius: 8px 0 0 8px;
  position: relative;
  overflow: hidden;
  gap: 6px;
  padding: 8px 0;
}

.door-label {
  font-size: 0.6rem;
  font-weight: 700;
  color: #6366F1;
  letter-spacing: 0.5px;
}

.door-side .door-label {
  writing-mode: vertical-rl;
}

.door-particles-v {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.door-side-stats {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 0.55rem;
  font-weight: 600;
}

/* 底部门 */
.door-bottom {
  height: 42px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(90deg, #EEF2FF 0%, #F0FDF4 50%, #EEF2FF 100%);
  border-top: 2px dashed #C7D2FE;
  border-radius: 0 0 8px 8px;
  position: relative;
  overflow: hidden;
}

.door-particles-h {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.door-bottom-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.65rem;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.ds-in   { color: #3B82F6; }
.ds-out  { color: #10B981; }
.ds-sep  { color: #CBD5E1; }
.ds-rate { color: #94A3B8; }

/* 左门粒子：水平移动 */
.flow-h {
  position: absolute;
  width: 9px; height: 9px;
  border-radius: 50%;
}
.flow-h.enter {
  background: #3B82F6;
  box-shadow: 0 0 8px 2px rgba(59,130,246,0.5);
  animation: flowRight 1.6s ease-in-out forwards;
}
.flow-h.leave {
  background: #10B981;
  box-shadow: 0 0 8px 2px rgba(16,185,129,0.5);
  animation: flowLeft 1.6s ease-in-out forwards;
}
@keyframes flowRight {
  0%   { left: -12px; opacity: 0; }
  15%  { opacity: 1; }
  85%  { opacity: 0.8; }
  100% { left: calc(100% + 12px); opacity: 0; }
}
@keyframes flowLeft {
  0%   { left: calc(100% + 12px); opacity: 0; }
  15%  { opacity: 1; }
  85%  { opacity: 0.8; }
  100% { left: -12px; opacity: 0; }
}

/* 底部门粒子：垂直移动 */
.flow-v {
  position: absolute;
  width: 9px; height: 9px;
  border-radius: 50%;
}
.flow-v.enter {
  background: #3B82F6;
  box-shadow: 0 0 8px 2px rgba(59,130,246,0.5);
  animation: flowUp 1.6s ease-in-out forwards;
}
.flow-v.leave {
  background: #10B981;
  box-shadow: 0 0 8px 2px rgba(16,185,129,0.5);
  animation: flowDown 1.6s ease-in-out forwards;
}
@keyframes flowUp {
  0%   { top: calc(100% + 12px); opacity: 0; }
  15%  { opacity: 1; }
  85%  { opacity: 0.8; }
  100% { top: -12px; opacity: 0; }
}
@keyframes flowDown {
  0%   { top: -12px; opacity: 0; }
  15%  { opacity: 1; }
  85%  { opacity: 0.8; }
  100% { top: calc(100% + 12px); opacity: 0; }
}
```

---

## 改动 B：座位区自适应铺满（消除空白）

**文件：** `frontend/src/components/CafeteriaView.vue`

### B1 — Script（替换 seatCols）

```js
// 原来：
const seatCols = computed(() => Math.min(Math.ceil(Math.sqrt(config.tableCount)), 10))
// 改为：
const seatCols = computed(() => Math.ceil(Math.sqrt(config.tableCount * 1.5)))
```

### B2 — CSS（替换 seats 相关样式）

```css
.seats-zone {
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 4px;
  position: relative;
  overflow: hidden;
}

.seats-grid {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  grid-auto-rows: 1fr;
  gap: 4px;
  width: 100%;
  height: 100%;
}

.table-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  min-height: 0;
}

.table-seats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  width: 100%;
  flex: 1;
  min-height: 0;
}

.seat-dot {
  border-radius: 50%;
  background: #F1F5F9;
  border: 1.5px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  width: 100%;
  aspect-ratio: 1;
}
```

---

## 改动 C：接口 Bug（重新配置时场景页断开）

### C1 — `frontend/src/components/SimulationView.vue`

在 `runSimulation` 函数里，`running.value = true` 的下一行插入：

```js
// 若有仿真在跑，先停止再配置
try {
  const st = await axios.get('http://127.0.0.1:8000/api/state')
  if (st.data?.state?.is_running) {
    await axios.post('http://127.0.0.1:8000/api/stop')
    await new Promise(r => setTimeout(r, 700))
  }
} catch (e) {}
```

### C2 — `frontend/src/components/CafeteriaView.vue`

在 `loadAndStart` 函数内，`if (route.query.running === 'true') { ... }` 块结尾的 `}` 之后追加：

```js
// 检查后端是否仍在运行，自动恢复轮询
try {
  const r = await axios.get('http://127.0.0.1:8000/api/state')
  if (r.data.success && r.data.state?.is_running) {
    isSimulating.value = true
    isPaused.value = false
    initDisplay()
    startPolling()
  }
} catch (e) {}
```

---

*改动优先级：A（双门）> B（座位铺满）> C（Bug修复）*
