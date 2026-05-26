import { createRouter, createWebHistory } from 'vue-router'
import CafeteriaView from '../components/CafeteriaView.vue'
import AnalysisView from '../components/AnalysisView.vue'
import SimulationView from '../components/SimulationView.vue'

const routes = [
  {
    path: '/',
    name: 'Cafeteria',
    component: CafeteriaView
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: AnalysisView
  },
  {
    path: '/simulation',
    name: 'Simulation',
    component: SimulationView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router