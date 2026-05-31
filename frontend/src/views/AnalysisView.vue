<template>
  <div class="analysis-view">
    <h1>决策分析</h1>
    <button class="btn-info" @click="showExplanation = true">📖 查看模型解读</button>

    <div class="result-selector" v-if="allResults.length > 0">
      <label>📋 选择仿真记录：</label>
      <select v-model="selectedResultId" @change="loadResult">
        <option value="">-- 选择一条记录 --</option>
        <option v-for="r in allResults" :key="r.id" :value="r.id">
          #{{ r.id.slice(-6) }} — {{ formatDateTime(r.createdAt) }} ({{ r.duration }}分钟)
        </option>
      </select>
      <button @click="refreshList" class="btn-secondary">🔄 刷新列表</button>

      <div class="ml-train-section">
        <span class="model-badge" :class="{ trained: modelTrained }">
          {{ modelTrained ? '🤖 模型已训练' : '⚠️ 模型未训练' }}
        </span>
        <button @click="trainModel" :disabled="trainingInProgress" class="btn-primary">
          {{ trainingInProgress ? '⏳ 训练中...' : '🧠 训练ML模型' }}
        </button>
      </div>
    </div>

    <div v-if="!currentResult && allResults.length === 0" class="no-data">
      <div class="no-data-icon">📭</div>
      <h3>暂无仿真数据</h3>
      <p>请先前往「运行仿真」页面执行一次仿真</p>
      <button @click="$router.push('/simulation')" class="go-btn">前往运行仿真 →</button>
    </div>

    <div v-if="currentResult" class="analysis-grid">

      <!-- 成本分析 -->
      <div class="analysis-card">
        <h2>成本分析（当前配置）</h2>
        <div class="cost-breakdown" v-if="costData">
          <div class="cost-item window-cost">
            <span class="cost-label">🏪 窗口运营</span>
            <span class="cost-value">{{ costData.window_cost }} 元/天</span>
          </div>
          <div class="cost-item seat-cost">
            <span class="cost-label">🪑 座位摊销</span>
            <span class="cost-value">{{ costData.seat_cost }} 元/天</span>
          </div>
          <div class="cost-item penalty-cost" v-if="costData.penalty > 0">
            <span class="cost-label">⏰ 排队惩罚</span>
            <span class="cost-value">{{ costData.penalty }} 元/天</span>
          </div>
          <div class="cost-divider"></div>
          <div class="cost-item total-cost">
            <span class="cost-label">📊 综合成本</span>
            <span class="cost-value highlight">{{ costData.total }} 元/天</span>
          </div>
        </div>
        <div v-else class="no-data-inline">选择仿真记录后显示成本</div>
      </div>

      <!-- ML 模型性能 -->
      <div class="analysis-card">
        <h2>ML 模型性能</h2>
        <div v-if="modelMetrics" class="model-metrics">
          <div class="metric-item">
            <span class="metric-label">R² 决定系数</span>
            <span class="metric-value" :class="r2Class">{{ (modelMetrics.r2_score * 100).toFixed(1) }}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">MAE 平均误差</span>
            <span class="metric-value">{{ modelMetrics.mae }} 分钟</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">训练样本</span>
            <span class="metric-value">{{ modelMetrics.sample_count }} 条</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">训练集/测试集</span>
            <span class="metric-value">{{ modelMetrics.train_count }} / {{ modelMetrics.test_count }}</span>
          </div>
        </div>
        <div v-else class="no-data-inline">请先训练 ML 模型</div>
      </div>

      <!-- ECharts U型曲线 -->
      <div class="analysis-card full-width" v-if="modelTrained">
        <h2>成本 U型曲线 — 为什么窗口不能无限多？</h2>
        <div class="chart-container" v-if="uCurveData">
          <div class="curve-info">
            <span class="curve-param">座位固定: {{ uCurveData.fixed_params.seat }} | 到达率: {{ uCurveData.fixed_params.arrival_rate }} 人/分</span>
            <span class="curve-best">最优窗口数: <strong>{{ uCurveData.best_window }}</strong> | 最低成本: <strong>{{ uCurveData.best_cost }} 元</strong></span>
          </div>
          <div ref="uCurveChart" class="echarts-box"></div>
        </div>
        <div v-else class="no-data-inline">训练模型后显示成本曲线</div>
      </div>

      <!-- ECharts 热力图 -->
      <div class="analysis-card full-width" v-if="modelTrained">
        <h2>木桶效应热力图 — 窗口与座位的联动关系</h2>
        <div class="chart-container" v-if="heatmapData">
          <div class="heatmap-info">
            <span>到达率: {{ heatmapData.fixed_params.arrival_rate }} 人/分 | 颜色越深 = 等待越久</span>
          </div>
          <div ref="heatmapChart" class="echarts-box" style="height:350px"></div>
        </div>
        <div v-else class="no-data-inline">训练模型后显示热力图</div>
      </div>

      <!-- 最优配置推荐 -->
      <div class="analysis-card full-width" v-if="optimumData">
        <h2>智能推荐：最低成本配置</h2>
        <div class="optimum-grid">
          <div class="optimum-section">
            <h3>推荐配置</h3>
            <div class="optimum-config">
              <div class="opt-item"><span>🏪</span> {{ optimumData.window_count }} 个窗口</div>
              <div class="opt-item"><span>🪑</span> {{ optimumData.seat_count }} 个座位</div>
              <div class="opt-item"><span>📈</span> 到达率 {{ optimumData.arrival_rate }} 人/分</div>
            </div>
          </div>
          <div class="optimum-section">
            <h3>预期效果</h3>
            <div class="optimum-metrics">
              <div class="opt-item"><span>⏱️</span> 等待 {{ optimumData.avg_wait_time?.toFixed(2) }} 分钟</div>
              <div class="opt-item"><span>✅</span> 服务 {{ optimumData.throughput_total }} 人</div>
              <div class="opt-item"><span>😊</span> 满意度 {{ (optimumData.satisfaction_score * 100).toFixed(1) }}%</div>
            </div>
          </div>
          <div class="optimum-section">
            <h3>成本明细</h3>
            <div class="optimum-cost">
              <div class="opt-item"><span>🏪</span> 运营 {{ optimumData.cost.operating }} 元</div>
              <div class="opt-item"><span>⏰</span> 惩罚 {{ optimumData.cost.penalty }} 元</div>
              <div class="opt-item highlight"><span>📊</span> 总计 {{ optimumData.cost.total }} 元/天</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ECharts 时间趋势图 -->
      <div class="analysis-card full-width">
        <h2>等待时间 / 排队长度 趋势</h2>
        <div ref="trendChart" class="echarts-box" v-if="timeSeries.length > 0"></div>
        <div v-else class="no-data-inline">暂无时间序列数据</div>
      </div>

      <!-- ECharts 吞吐量柱状图 -->
      <div class="analysis-card full-width" v-if="currentResult.statistics?.throughput_per_window?.length">
        <h2>各窗口吞吐量</h2>
        <div ref="throughputChart" class="echarts-box"></div>
      </div>

      <!-- ECharts 满意度 vs 等待时间散点图 -->
      <div class="analysis-card full-width" v-if="allResults.length > 0">
        <h2>满意度 vs 等待时间 — 历史仿真分布</h2>
        <div class="scatter-info">
          <span>共 {{ allResults.length }} 条仿真记录 · 气泡大小=吞吐量 · 红色=当前选中</span>
        </div>
        <div ref="scatterChart" class="echarts-box"></div>
      </div>
    </div>

    <!-- 模型解读弹窗 -->
    <div v-if="showExplanation" class="modal-overlay" @click="showExplanation = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📖 模型解读</h3>
          <button class="modal-close" @click="showExplanation = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingExplanation" class="loading">加载中...</div>
          <div v-else v-html="explanationHtml"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useSimulationStore } from '../stores/simulation.js'

const route = useRoute()
const store = useSimulationStore()

const allResults = ref([])
const selectedResultId = ref('')
const currentResult = ref(null)
const timeSeries = ref([])
const costData = ref(null)
const optimumData = ref(null)

const modelTrained = ref(false)
const modelMetrics = ref(null)
const trainingInProgress = ref(false)
const uCurveData = ref(null)
const heatmapData = ref(null)

const showExplanation = ref(false)
const explanationHtml = ref('')
const loadingExplanation = ref(false)

// ECharts 容器 refs
const uCurveChart = ref(null)
const heatmapChart = ref(null)
const trendChart = ref(null)
const throughputChart = ref(null)
const scatterChart = ref(null)

// 图表实例缓存
let uCurveInstance = null
let heatmapInstance = null
let trendInstance = null
let throughputInstance = null
let scatterInstance = null

const r2Class = computed(() => {
  if (!modelMetrics.value) return ''
  const r2 = modelMetrics.value.r2_score
  if (r2 >= 0.9) return 'r2-excellent'
  if (r2 >= 0.7) return 'r2-good'
  if (r2 >= 0.5) return 'r2-medium'
  return 'r2-poor'
})

// ==================== ECharts 渲染函数 ====================

const renderUCurve = () => {
  if (!uCurveData.value || !uCurveChart.value) return
  if (!uCurveInstance) {
    uCurveInstance = echarts.init(uCurveChart.value)
  }
  const d = uCurveData.value
  uCurveInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['运营成本', '惩罚成本', '总成本'], bottom: 0, itemGap: 25, textStyle: { fontSize: 12 } },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: d.windows, name: '窗口数' },
    yAxis: { type: 'value', name: '成本(元)' },
    series: [
      { name: '运营成本', type: 'line', data: d.operatings, smooth: true, lineStyle: { color: '#52c41a' }, itemStyle: { color: '#52c41a' }, symbol: 'none' },
      { name: '惩罚成本', type: 'line', data: d.penalties, smooth: true, lineStyle: { color: '#f5222d' }, itemStyle: { color: '#f5222d' }, symbol: 'none' },
      {
        name: '总成本', type: 'line', data: d.costs, smooth: true,
        lineStyle: { color: '#667eea', width: 2.5 },
        itemStyle: { color: '#667eea' },
        markPoint: {
          data: [{
            name: '最优', coord: [d.windows.indexOf(d.best_window), d.best_cost],
            symbol: 'pin', symbolSize: 35,
            itemStyle: { color: '#f5222d' },
            label: { formatter: `最优\n{doc}窗口\n{c}元` }
          }],
          animation: true
        }
      }
    ]
  }, true)
}

const renderHeatmap = () => {
  if (!heatmapData.value || !heatmapChart.value) return
  if (!heatmapInstance) {
    heatmapInstance = echarts.init(heatmapChart.value)
  }
  const d = heatmapData.value
  const seriesData = []
  d.matrix.forEach((row, ri) => {
    row.forEach((val, ci) => {
      seriesData.push([ci, ri, val])
    })
  })
  // 找出最优点
  let minVal = Infinity, minCi = 0, minRi = 0
  seriesData.forEach(([ci, ri, v]) => { if (v < minVal) { minVal = v; minCi = ci; minRi = ri } })

  heatmapInstance.setOption({
    tooltip: {
      formatter: (p) => `窗口: ${d.windows[p.data[0]]} | 座位: ${d.seats[p.data[1]]}<br/>等待: ${p.data[2]} 分钟`
    },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: d.windows, name: '窗口数', position: 'bottom' },
    yAxis: { type: 'category', data: d.seats, name: '座位数' },
    visualMap: {
      min: Math.min(...seriesData.map(s => s[2])),
      max: Math.max(...seriesData.map(s => s[2])),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#e6f7ff', '#91d5ff', '#1890ff', '#0050b3'] }
    },
    series: [{
      type: 'heatmap', data: seriesData,
      label: { show: true, fontSize: 10 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
      markPoint: {
        symbol: 'pin', symbolSize: 30,
        data: [{
          name: '最优', coord: [minCi, minRi],
          itemStyle: { color: '#f5222d' },
          label: { formatter: '最优\n{c}min', fontSize: 10 }
        }]
      }
    }]
  }, true)
}

const renderTrend = () => {
  if (!timeSeries.value.length || !trendChart.value) return
  if (!trendInstance) {
    trendInstance = echarts.init(trendChart.value)
  }
  const times = timeSeries.value.map(t => t.time)
  const waits = timeSeries.value.map(t => t.avg_wait)
  const queues = timeSeries.value.map(t => t.queue_length_sum)

  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均等待(分)', '排队总人数'], bottom: 0, itemGap: 25, textStyle: { fontSize: 12 } },
    grid: { left: 50, right: 50, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: times, name: '时间(分钟)', boundaryGap: false },
    yAxis: [
      { type: 'value', name: '分钟' },
      { type: 'value', name: '人数' }
    ],
    series: [
      { name: '平均等待(分)', type: 'line', data: waits, smooth: true, yAxisIndex: 0, lineStyle: { color: '#1890ff' }, itemStyle: { color: '#1890ff' }, symbol: 'none', areaStyle: { color: 'rgba(24,144,255,0.1)' } },
      { name: '排队总人数', type: 'bar', data: queues, yAxisIndex: 1, itemStyle: { color: 'rgba(245,34,45,0.5)' }, barMaxWidth: 8 }
    ]
  }, true)
}

const renderThroughput = () => {
  const arr = currentResult.value?.statistics?.throughput_per_window
  if (!arr?.length || !throughputChart.value) return
  if (!throughputInstance) {
    throughputInstance = echarts.init(throughputChart.value)
  }
  const labels = arr.map((_, i) => `窗口${i + 1}`)
  throughputInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '服务人数' },
    series: [{
      type: 'bar', data: arr,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ])
      },
      barMaxWidth: 40
    }]
  }, true)
}

const renderScatter = () => {
  if (!allResults.value.length || !scatterChart.value) return
  if (!scatterInstance) {
    scatterInstance = echarts.init(scatterChart.value)
  }
  const curId = selectedResultId.value
  const others = []
  const current = []
  const throughputs = allResults.value.map(r => r.throughput || 0)
  const maxThroughput = Math.max(...throughputs, 1)
  allResults.value.forEach(r => {
    const wait = r.avgWaitTime ?? 0
    const sat = (r.satisfaction ?? 0) * 100
    const tp = r.throughput || 0
    const size = 8 + (tp / maxThroughput) * 32
    const point = {
      value: [wait, sat, tp, r.windowCount, r.seatCount, r.id],
      symbolSize: size
    }
    if (String(r.id) === String(curId)) current.push(point)
    else others.push(point)
  })

  scatterInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const [w, s, tp, wc, sc, id] = p.data.value
        return `记录 #${String(id).slice(-6)}<br/>
                等待: ${w.toFixed(2)} 分钟<br/>
                满意度: ${s.toFixed(1)}%<br/>
                吞吐: ${tp} 人<br/>
                配置: ${wc}窗口 / ${sc}座位`
      }
    },
    grid: { left: 60, right: 30, top: 30, bottom: 50 },
    xAxis: { type: 'value', name: '平均等待时间(分)', nameLocation: 'middle', nameGap: 30, splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: { type: 'value', name: '满意度(%)', min: 0, max: 100, splitLine: { lineStyle: { type: 'dashed' } } },
    legend: {
      data: ['历史仿真', '当前选中'],
      bottom: 0,
      itemGap: 30,
      textStyle: { fontSize: 12, lineHeight: 20 }
    },
    series: [
      {
        name: '历史仿真', type: 'scatter', data: others,
        itemStyle: {
          color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.9)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.4)' }
          ]),
          borderColor: '#667eea', borderWidth: 1
        }
      },
      {
        name: '当前选中', type: 'scatter', data: current,
        itemStyle: {
          color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
            { offset: 0, color: 'rgba(245, 34, 45, 1)' },
            { offset: 1, color: 'rgba(245, 34, 45, 0.5)' }
          ]),
          borderColor: '#f5222d', borderWidth: 2
        },
        emphasis: { itemStyle: { shadowBlur: 20, shadowColor: 'rgba(245,34,45,0.6)' } }
      }
    ]
  }, true)
}

// 统一的图表渲染入口
const renderAllCharts = async () => {
  await nextTick()
  renderUCurve()
  renderHeatmap()
  renderTrend()
  renderThroughput()
  renderScatter()
}

// 监听数据变化重绘
watch([uCurveData, heatmapData, timeSeries, () => currentResult.value?.statistics?.throughput_per_window, allResults, selectedResultId], () => {
  renderAllCharts()
}, { deep: true })

// ==================== 数据加载 ====================

const refreshList = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/simulation/results')
    allResults.value = response.data || []
  } catch (error) {
    console.error('获取仿真记录失败:', error)
  }
}

const trainModel = async () => {
  trainingInProgress.value = true
  try {
    const resp = await axios.post('http://127.0.0.1:8000/api/analysis/train')
    if (resp.data.success) {
      modelTrained.value = true
      modelMetrics.value = resp.data.metrics
      await loadMLData()
    }
  } catch (error) {
    console.error('模型训练失败:', error)
    if (error.response?.data?.detail) {
      alert('模型训练失败: ' + error.response.data.detail)
    } else {
      alert('模型训练失败，请稍后重试')
    }
  } finally {
    trainingInProgress.value = false
  }
}

const loadMLData = async () => {
  try {
    const [uResp, hResp] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/analysis/u-curve'),
      axios.get('http://127.0.0.1:8000/api/analysis/heatmap')
    ])
    if (uResp.data.success) uCurveData.value = uResp.data.data
    if (hResp.data.success) heatmapData.value = hResp.data.data
  } catch (e) {
    console.error('加载ML可视化数据失败:', e)
  }
}

const checkModelStatus = async () => {
  try {
    const resp = await axios.get('http://127.0.0.1:8000/api/analysis/model')
    if (resp.data.success && resp.data.data.trained) {
      modelTrained.value = true
      modelMetrics.value = resp.data.data.metrics
      await loadMLData()
    }
  } catch (e) {
    console.error('检查模型状态失败:', e)
  }
}

const loadResult = async () => {
  if (!selectedResultId.value) {
    currentResult.value = null
    timeSeries.value = []
    costData.value = null
    optimumData.value = null
    return
  }
  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/simulation/results/${selectedResultId.value}`)
    currentResult.value = response.data
    timeSeries.value = response.data.time_series || response.data.statistics?.time_series || []

    try {
      const [costResp, optResp] = await Promise.all([
        axios.get(`http://127.0.0.1:8000/api/analysis/cost/${selectedResultId.value}`),
        axios.get('http://127.0.0.1:8000/api/analysis/optimize')
      ])
      if (costResp.data.success) costData.value = costResp.data.cost
      if (optResp.data.success) optimumData.value = optResp.data.data
    } catch (e) {
      console.error('获取分析数据失败:', e)
      costData.value = null
      optimumData.value = null
    }
  } catch (error) {
    console.error('获取仿真详情失败:', error)
    currentResult.value = null
    timeSeries.value = []
  }
}

const formatDateTime = (timestamp) => {
  if (!timestamp) return '未知时间'
  const date = new Date(timestamp)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${month}/${day} ${hours}:${minutes}`
}

const loadExplanation = async () => {
  loadingExplanation.value = true
  try {
    const resp = await axios.get('http://127.0.0.1:8000/api/analysis/explain')
    if (resp.data.success) {
      explanationHtml.value = resp.data.html || '<p>暂无解读内容</p>'
    } else {
      explanationHtml.value = '<p>获取解读内容失败</p>'
    }
  } catch (error) {
    console.error('获取模型解读失败:', error)
    explanationHtml.value = '<p>获取解读内容失败，请检查后端服务</p>'
  } finally {
    loadingExplanation.value = false
  }
}

watch(showExplanation, async (val) => {
  if (val) await loadExplanation()
})

watch(() => route.query.simulationId, (newId) => {
  if (newId) {
    selectedResultId.value = String(newId)
    loadResult()
  }
})

onMounted(async () => {
  await refreshList()
  await checkModelStatus()

  const simId = route.query.simulationId
  if (simId) {
    selectedResultId.value = String(simId)
    await loadResult()
  } else {
    const lastId = store.lastSimulationId
    if (lastId && allResults.value.some(r => r.id === lastId)) {
      selectedResultId.value = lastId
      await loadResult()
    } else if (allResults.value.length > 0) {
      selectedResultId.value = allResults.value[0].id
      await loadResult()
    }
  }
  renderAllCharts()
})

// 窗口 resize 时更新图表
const handleResize = () => {
  uCurveInstance?.resize()
  heatmapInstance?.resize()
  trendInstance?.resize()
  throughputInstance?.resize()
  scatterInstance?.resize()
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  uCurveInstance?.dispose()
  heatmapInstance?.dispose()
  trendInstance?.dispose()
  throughputInstance?.dispose()
  scatterInstance?.dispose()
})
</script>

<style scoped>
.analysis-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 16px;
  letter-spacing: -0.3px;
}

.result-selector {
  background: white;
  padding: 15px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.result-selector label { font-weight: 600; color: #2c3e50; }

.result-selector select {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 1rem;
  min-width: 250px;
  cursor: pointer;
}

.ml-train-section {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-badge {
  font-size: 0.85rem;
  padding: 6px 14px;
  border-radius: 20px;
  background: #fff3cd;
  color: #856404;
  font-weight: 600;
}
.model-badge.trained { background: #d4edda; color: #155724; }

.btn-primary {
  padding: 8px 18px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(79,70,229,0.35); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  padding: 8px 16px;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-secondary:hover { background: #e0e0e0; }

.btn-info {
  padding: 8px 18px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 500;
  margin-bottom: 15px;
  transition: all 0.2s;
}
.btn-info:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(79,70,229,0.35); }

.no-data {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.no-data-icon { font-size: 4rem; margin-bottom: 16px; }
.no-data h3 { color: #2c3e50; margin-bottom: 10px; }
.no-data p { color: #666; margin-bottom: 20px; }

.go-btn {
  padding: 12px 30px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
}
.go-btn:hover { opacity: 0.9; }

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 30px;
}

.analysis-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.analysis-card.full-width { grid-column: 1 / -1; }
.analysis-card h2 {
  color: #0F172A;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 14px;
  padding-bottom: 10px;
  padding-left: 10px;
  border-bottom: 1px solid #F1F5F9;
  border-left: 3px solid #4F46E5;
}

/* 图表容器 */
.chart-container {
  background: #fafafa;
  border-radius: 10px;
  padding: 15px;
}
.echarts-box {
  width: 100%;
  height: 320px;
}
.curve-info {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 0.85rem;
}
.curve-param { color: #718096; }
.curve-best { color: #2d3748; }
.curve-best strong { color: #e53e3e; }
.heatmap-info { margin-bottom: 12px; font-size: 0.85rem; color: #718096; }
.scatter-info { margin-bottom: 16px; font-size: 0.85rem; color: #718096; padding-bottom: 8px; }

/* 模型指标 */
.model-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.metric-item {
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}
.metric-label { font-size: 0.8rem; color: #a0aec0; margin-bottom: 4px; }
.metric-value { font-size: 1.2rem; font-weight: 700; color: #2d3748; }
.metric-value.r2-excellent { color: #38a169; }
.metric-value.r2-good { color: #4299e1; }
.metric-value.r2-medium { color: #ed8936; }
.metric-value.r2-poor { color: #e53e3e; }

/* 成本 */
.cost-breakdown { display: flex; flex-direction: column; gap: 10px; }
.cost-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: #f7fafc; border-radius: 8px; border-left: 3px solid #e2e8f0;
}
.cost-item.window-cost { border-left-color: #667eea; }
.cost-item.seat-cost { border-left-color: #48bb78; }
.cost-item.penalty-cost { border-left-color: #e74c3c; }
.cost-item.total-cost { border-left-color: #2d3748; background: #edf2f7; }
.cost-label { color: #4a5568; font-size: 0.95rem; }
.cost-value { font-weight: 700; color: #2d3748; font-size: 1.1rem; }
.cost-value.highlight { color: #e74c3c; font-size: 1.3rem; }
.cost-divider { height: 2px; background: #e2e8f0; margin: 4px 0; }

/* 最优配置 */
.optimum-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.optimum-section h3 { font-size: 0.95rem; color: #667eea; margin-bottom: 12px; }
.optimum-config, .optimum-metrics, .optimum-cost { display: flex; flex-direction: column; gap: 8px; }
.opt-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #f7fafc; border-radius: 6px;
  font-size: 0.9rem; color: #2d3748;
}
.opt-item span { font-size: 1.2rem; }
.opt-item.highlight { background: #fff5f5; border: 1px solid #feb2b2; font-weight: 700; }

.no-data-inline { text-align: center; color: #999; padding: 30px; }

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 900px;
  width: 90%;
  max-height: 85vh;
  overflow: hidden;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: white;
}
.modal-header h3 { margin: 0; font-size: 1.3rem; }
.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 8px;
}
.modal-body {
  padding: 24px;
  max-height: calc(85vh - 80px);
  overflow-y: auto;
  color: #333;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .analysis-grid { grid-template-columns: 1fr; }
  .optimum-grid { grid-template-columns: 1fr; }
}
</style>
