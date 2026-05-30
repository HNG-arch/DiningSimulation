import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useSimulationStore = defineStore('simulation', () => {
  // 仿真配置参数
  const config = reactive({
    windowCount: 10,
    tableCount: 30,
    servingSpeed: 1.0,
    studentCount: 500,
    simulationTime: 120,
    simulationDuration: 120,
    arrivalRate: 15,
    avgEatTime: 10,
    avgServeTimeSeconds: 60,
    avgEatTimeSeconds: 600,
    tickStep: 1.0
  })

  // 仿真运行状态
  const isRunning = ref(false)
  const simulationSpeed = ref(5)

  // 最近一次仿真ID（用于跨页面传递）
  const lastSimulationId = ref(localStorage.getItem('lastSimulationId') || null)

  // 设置配置
  function setConfig(cfg) {
    Object.assign(config, cfg)
  }

  // 保存最后仿真ID
  function setLastSimulationId(id) {
    lastSimulationId.value = id
    if (id) localStorage.setItem('lastSimulationId', id)
  }

  return { config, isRunning, simulationSpeed, lastSimulationId, setConfig, setLastSimulationId }
})
