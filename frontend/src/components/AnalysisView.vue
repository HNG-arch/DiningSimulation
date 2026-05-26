
<template>
  <div class="analysis-view">
    <h1>📈 决策分析</h1>
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

      <div class="analysis-card">
        <h2>💰 成本分析（当前配置）</h2>
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

      <div class="analysis-card">
        <h2>🧠 ML 模型性能</h2>
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

      <div class="analysis-card full-width" v-if="modelTrained">
        <h2>📉 成本 U型曲线 — 为什么窗口不能无限多？</h2>
        <div class="u-curve-container" v-if="uCurveData">
          <div class="curve-info">
            <span class="curve-param">座位固定: {{ uCurveData.fixed_params.seat }} | 到达率: {{ uCurveData.fixed_params.arrival_rate }} 人/分</span>
            <span class="curve-best">最优窗口数: <strong>{{ uCurveData.best_window }}</strong> | 最低成本: <strong>{{ uCurveData.best_cost }} 元</strong></span>
          </div>
          <div class="curve-chart">
            <div class="chart-y-label">成本(元)</div>
            <div class="chart-area">
              <div class="curve-line">
                <div class="curve-point" v-for="(cost, i) in uCurveData.costs" :key="i"
                     :style="{ left: (i / (uCurveData.windows.length - 1)) * 100 + '%', bottom: costPercent(cost) + '%' }"
                     :class="{ 'best-point': uCurveData.windows[i] === uCurveData.best_window }">
                  <div class="point-tooltip" v-if="showCurveTooltip(i)">
                    {{ uCurveData.windows[i] }}窗口<br/>{{ cost }}元<br/>等待{{ uCurveData.wait_times[i] }}分
                  </div>
                </div>
              </div>
              <div class="curve-svg-line">
                <svg :viewBox="'0 0 ' + curveSvgWidth + ' ' + curveSvgHeight" preserveAspectRatio="none">
                  <polyline :points="curvePolyline" fill="none" stroke="#667eea" stroke-width="2" vector-effect="non-scaling-stroke" />
                </svg>
              </div>
            </div>
            <div class="chart-x-label">窗口数量 →</div>
          </div>
        </div>
        <div v-else class="no-data-inline">训练模型后显示成本曲线</div>
      </div>

      <div class="analysis-card full-width" v-if="modelTrained">
        <h2>🗺️ 木桶效应热力图 — 窗口与座位的联动关系</h2>
        <div class="heatmap-container" v-if="heatmapData">
          <div class="heatmap-info">
            <span>到达率: {{ heatmapData.fixed_params.arrival_rate }} 人/分 | 颜色越深 = 等待越久</span>
          </div>
          <div class="heatmap-grid">
            <div class="heatmap-y-header">
              <div class="corner-label">座位↓/窗口→</div>
              <div class="col-header" v-for="w in heatmapData.windows" :key="'h-'+w">{{ w }}</div>
            </div>
            <div class="heatmap-row" v-for="(row, ri) in heatmapData.matrix" :key="'r-'+ri">
              <div class="row-header">{{ heatmapData.seats[ri] }}</div>
              <div class="heat-cell" v-for="(val, ci) in row" :key="'c-'+ri+'-'+ci"
                   :style="{ backgroundColor: heatColor(val) }"
                   :title="'窗口:' + heatmapData.windows[ci] + ' 座位:' + heatmapData.seats[ri] + ' 等待:' + val + '分钟'">
                {{ val }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-data-inline">训练模型后显示热力图</div>
      </div>

      <div class="analysis-card">
        <h2>💡 ML 优化建议</h2>
        <ul class="suggestions" v-if="computedSuggestions.length > 0">
          <li :class="['suggestion-item', s.type || 'default']" v-for="(s, index) in computedSuggestions" :key="index">
            <span class="suggestion-icon">{{ s.icon }}</span>
            {{ s.text }}
          </li>
        </ul>
        <div v-else class="no-data-inline">暂无建议</div>
      </div>

      <div class="analysis-card full-width" v-if="optimumData">
        <h2>🎯 智能推荐：最低成本配置</h2>
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

      <div class="analysis-card full-width">
        <h2>📉 等待时间 / 排队长度 趋势</h2>
        <div class="trend-chart" v-if="timeSeries.length > 0">
          <div class="chart-legend">
            <span class="legend-item"><span class="dot blue"></span> 平均等待(分钟)</span>
            <span class="legend-item"><span class="dot red"></span> 排队总人数</span>
          </div>
          <div class="trend-line">
            <div class="trend-point" v-for="(point, i) in sampledTimeSeries" :key="i"
                 :title="'时间: ' + point.time + '分钟\n等待: ' + point.avg_wait + '分钟\n排队: ' + point.queue_length_sum + '人'">
              <div class="point-bar-group">
                <div class="point-bar wait-bar" :style="{ height: minVal(point.avg_wait * 8, 100) + '%' }"></div>
                <div class="point-bar queue-bar" :style="{ height: minVal(point.queue_length_sum * 2, 100) + '%' }"></div>
              </div>
              <div class="point-label">{{ point.time }}'</div>
            </div>
          </div>
        </div>
        <div v-else class="no-data-inline">暂无时间序列数据</div>
      </div>

      <div class="analysis-card full-width">
        <h2>🏪 各窗口吞吐量</h2>
        <div class="window-throughput" v-if="currentResult.statistics?.throughput_per_window?.length > 0">
          <div class="throughput-bar-item" v-for="(count, idx) in currentResult.statistics.throughput_per_window" :key="idx">
            <span class="throughput-label">窗口{{ idx + 1 }}</span>
            <div class="throughput-bar-track">
              <div class="throughput-bar-fill" :style="{ width: throughputPercent(count) + '%' }"></div>
            </div>
            <span class="throughput-value">{{ count }}人</span>
          </div>
        </div>
      </div>
    </div>

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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

const route = useRoute()

const minVal = (a, b) => Math.min(a, b)

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
const hoveredCurveIdx = ref(-1)

const showExplanation = ref(false)
const explanationHtml = ref('')
const loadingExplanation = ref(false)

const curveSvgWidth = 500
const curveSvgHeight = 200

const r2Class = computed(() => {
  if (!modelMetrics.value) return ''
  const r2 = modelMetrics.value.r2_score
  if (r2 >= 0.9) return 'r2-excellent'
  if (r2 >= 0.7) return 'r2-good'
  if (r2 >= 0.5) return 'r2-medium'
  return 'r2-poor'
})

const showCurveTooltip = (i) => {
  return hoveredCurveIdx.value === i
}

const costPercent = (cost) => {
  if (!uCurveData.value) return 0
  const maxCost = Math.max(...uCurveData.value.costs, 1)
  const minCost = Math.min(...uCurveData.value.costs, 0)
  const range = maxCost - minCost || 1
  return ((cost - minCost) / range) * 80
}

const curvePolyline = computed(() => {
  if (!uCurveData.value) return ''
  const costs = uCurveData.value.costs
  const maxC = Math.max(...costs, 1)
  const minC = Math.min(...costs, 0)
  const range = maxC - minC || 1
  const n = costs.length
  return costs.map((c, i) => {
    const x = (i / (n - 1)) * curveSvgWidth
    const y = curveSvgHeight - ((c - minC) / range) * (curveSvgHeight - 20)
    return `${x},${y}`
  }).join(' ')
})

const heatColor = (val) => {
  if (!heatmapData.value) return '#ffffff'
  const allVals = heatmapData.value.matrix.flat()
  const maxV = Math.max(...allVals, 1)
  const minV = Math.min(...allVals, 0)
  const ratio = (val - minV) / (maxV - minV || 1)
  const r = Math.round(255)
  const g = Math.round(255 * (1 - ratio * 0.9))
  const b = Math.round(100 * (1 - ratio))
  const textColor = ratio > 0.6 ? '#fff' : '#333'
  return `rgb(${r},${g},${b})`
}

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

const computedSuggestions = computed(() => {
  if (!currentResult.value) return []
  const stats = currentResult.value.statistics || {}
  const cfg = currentResult.value.config || {}
  const suggestions = []

  if ((stats.avg_wait_time || 0) > 5) {
    suggestions.push({ icon: '⚠️', text: '平均等待时间超过5分钟，建议增加窗口数量或提高打饭效率', type: 'warning' })
  }
  if ((stats.satisfaction_score || 0) < 0.6) {
    suggestions.push({ icon: '📉', text: '满意度偏低(低于60%)，建议优化排队动线，减少拥堵', type: 'danger' })
  }
  if ((stats.seat_turnover || 0) < 4) {
    suggestions.push({ icon: '🔄', text: '座位周转率偏低，建议调整座位布局，提高空间利用率', type: 'info' })
  }
  const maxThroughput = Math.max(...(stats.throughput_per_window || [0]))
  const minThroughput = Math.min(...(stats.throughput_per_window || [0]))
  if (maxThroughput > 0 && (maxThroughput - minThroughput) / maxThroughput > 0.3) {
    suggestions.push({ icon: '⚖️', text: '各窗口服务量不均衡，考虑调整窗口分配策略', type: 'info' })
  }
  if (cfg.window_count && cfg.seat_count && cfg.seat_count < cfg.window_count * 8) {
    suggestions.push({ icon: '🪑', text: '座位数相对窗口数偏少，可能导致学生无法及时入座', type: 'warning' })
  }
  if (modelTrained.value && optimumData.value) {
    suggestions.push({
      icon: '🤖',
      text: `ML推荐：${optimumData.value.window_count}窗口 + ${optimumData.value.seat_count}座位时综合成本最低(¥${optimumData.value.cost.total})`,
      type: 'ml'
    })
  }
  suggestions.push({ icon: '📱', text: '引入预约订餐系统，分散高峰客流', type: 'default' })
  suggestions.push({ icon: '🍱', text: '根据时段调整菜品供应结构，减少食材浪费', type: 'default' })
  return suggestions.slice(0, 6)
})

const sampledTimeSeries = computed(() => {
  if (timeSeries.value.length <= 20) return timeSeries.value
  const step = Math.ceil(timeSeries.value.length / 20)
  return timeSeries.value.filter((_, i) => i % step === 0)
})

const maxThroughput = computed(() => {
  const arr = currentResult.value?.statistics?.throughput_per_window || [1]
  return Math.max(...arr, 1)
})
const throughputPercent = (count) => (count / maxThroughput.value) * 100

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
  if (val) {
    await loadExplanation()
  }
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
    const lastId = localStorage.getItem('lastSimulationId')
    if (lastId && allResults.value.some(r => r.id === lastId)) {
      selectedResultId.value = lastId
      await loadResult()
    } else if (allResults.value.length > 0) {
      selectedResultId.value = allResults.value[0].id
      await loadResult()
    }
  }
})
</script>

<style scoped>
.analysis-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  color: white;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.result-selector label {
  font-weight: 600;
  color: #2c3e50;
}

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

.model-badge.trained {
  background: #d4edda;
  color: #155724;
}

.btn-primary {
  padding: 8px 18px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

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
  padding: 10px 20px;
  background: linear-gradient(135deg, #17a2b8, #138496);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s;
  margin-bottom: 15px;
}

.btn-info:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(23, 162, 184, 0.4);
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.no-data-icon { font-size: 4rem; margin-bottom: 16px; }
.no-data h3 { color: #2c3e50; margin-bottom: 10px; }
.no-data p { color: #666; margin-bottom: 20px; }

.go-btn {
  padding: 12px 30px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}
.go-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.analysis-card {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.analysis-card.full-width { grid-column: 1 / -1; }
.analysis-card h2 {
  color: #2c3e50;
  font-size: 1.2rem;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

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

.u-curve-container {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 15px;
}
.curve-info {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 0.85rem;
}
.curve-param { color: #718096; }
.curve-best { color: #2d3748; }
.curve-best strong { color: #e53e3e; }

.curve-chart {
  display: flex;
  gap: 10px;
  height: 250px;
}
.chart-y-label {
  writing-mode: vertical-lr;
  text-orientation: mixed;
  font-size: 0.75rem;
  color: #a0aec0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 25px;
}
.chart-area {
  flex: 1;
  position: relative;
  border-left: 2px solid #e2e8f0;
  border-bottom: 2px solid #e2e8f0;
}
.chart-x-label {
  text-align: right;
  font-size: 0.75rem;
  color: #a0aec0;
  margin-top: 6px;
  padding-right: 20px;
}
.curve-line { position: absolute; inset: 0; }
.curve-point {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #667eea;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 2;
}
.curve-point.best-point {
  width: 14px;
  height: 14px;
  background: #e53e3e;
  box-shadow: 0 0 8px rgba(229, 62, 62, 0.5);
}
.curve-point:hover { transform: translate(-50%, -50%) scale(1.5); z-index: 10; }
.curve-point:hover .point-tooltip {
  display: block;
}
.point-tooltip {
  display: none;
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  background: #2d3748;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  white-space: nowrap;
  line-height: 1.5;
  z-index: 20;
}
.curve-svg-line {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}
.curve-svg-line svg {
  width: 100%;
  height: 100%;
}

.heatmap-container {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 15px;
  overflow-x: auto;
}
.heatmap-info { margin-bottom: 12px; font-size: 0.85rem; color: #718096; }
.heatmap-grid { display: flex; flex-direction: column; gap: 0; }
.heatmap-y-header {
  display: flex;
  gap: 0;
}
.corner-label {
  width: 65px;
  font-size: 0.65rem;
  color: #a0aec0;
  text-align: center;
}
.col-header {
  width: 45px;
  text-align: center;
  font-size: 0.7rem;
  color: #718096;
}
.heatmap-row {
  display: flex;
  gap: 0;
}
.row-header {
  width: 65px;
  text-align: right;
  padding-right: 6px;
  font-size: 0.7rem;
  color: #718096;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.heat-cell {
  width: 45px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  border: 1px solid rgba(255,255,255,0.3);
  cursor: default;
}

.suggestions { list-style: none; padding: 0; }
.suggestion-item {
  padding: 10px 14px;
  margin: 6px 0;
  background: #f8f9fa;
  border-radius: 8px;
  color: #555;
  font-size: 0.9rem;
  border-left: 3px solid #e2e8f0;
  transition: background 0.2s;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.suggestion-item:hover { background: #eef2ff; }
.suggestion-item.warning { border-left-color: #ed8936; background: #fffaf0; }
.suggestion-item.danger { border-left-color: #e53e3e; background: #fff5f5; }
.suggestion-item.info { border-left-color: #4299e1; background: #ebf8ff; }
.suggestion-item.ml { border-left-color: #667eea; background: #f3f0ff; }
.suggestion-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }

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

.trend-chart { padding: 15px 10px; background: #f8f9fa; border-radius: 10px; overflow-x: auto; }
.chart-legend { display: flex; gap: 20px; margin-bottom: 15px; font-size: 0.85rem; }
.legend-item { display: flex; align-items: center; gap: 6px; color: #666; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot.blue { background: #3498db; }
.dot.red { background: #e74c3c; }
.trend-line { display: flex; justify-content: space-around; align-items: flex-end; height: 220px; min-width: 500px; }
.trend-point { display: flex; flex-direction: column; align-items: center; gap: 4px; cursor: pointer; }
.point-bar-group { display: flex; gap: 3px; align-items: flex-end; height: 180px; }
.point-bar { width: 12px; border-radius: 3px 3px 0 0; transition: height 0.3s; min-height: 2px; }
.wait-bar { background: #3498db; }
.queue-bar { background: #e74c3c; }
.point-label { font-size: 10px; color: #999; margin-top: 4px; }

.window-throughput { display: flex; flex-direction: column; gap: 8px; }
.throughput-bar-item { display: flex; align-items: center; gap: 10px; }
.throughput-label { width: 55px; font-size: 0.85rem; color: #666; text-align: right; }
.throughput-bar-track { flex: 1; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
.throughput-bar-fill {
  height: 100%; background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 10px; transition: width 0.5s; min-width: 4px;
}
.throughput-value { width: 45px; font-size: 0.85rem; font-weight: 600; color: #2c3e50; }

.no-data-inline { text-align: center; color: #999; padding: 30px; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 900px;
  width: 90%;
  max-height: 85vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
}

.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body {
  padding: 24px;
  max-height: calc(85vh - 80px);
  overflow-y: auto;
  color: #333;
  line-height: 1.8;
}

.modal-body .loading {
  text-align: center;
  color: #666;
  padding: 40px;
}

@media (max-width: 768px) {
  .analysis-grid { grid-template-columns: 1fr; }
  .optimum-grid { grid-template-columns: 1fr; }
  .curve-chart { height: 200px; }
}
</style>
