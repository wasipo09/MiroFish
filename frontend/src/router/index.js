import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import SimulationPostsView from '../views/SimulationPostsView.vue'

const routes = [
  { path: '/', name: 'Home', component: Home, meta: { title: 'News Analysis' } },
  { path: '/market-research/:projectId', alias: '/process/:projectId', name: 'Process', component: Process, props: true, meta: { title: 'Advanced Market Research Engine' } },
  { path: '/market-reaction/:simulationId', alias: '/simulation/:simulationId', name: 'Simulation', component: SimulationView, props: true, meta: { title: 'Market Reaction Setup' } },
  { path: '/market-reaction/:simulationId/run', alias: '/simulation/:simulationId/start', name: 'SimulationRun', component: SimulationRunView, props: true, meta: { title: 'Market Reaction Run' } },
  { path: '/market-reaction/:simulationId/posts', name: 'SimulationPosts', component: SimulationPostsView, props: true, meta: { title: 'Simulation Posts' } },
  { path: '/news-report/:reportId', alias: '/report/:reportId', name: 'Report', component: ReportView, props: true, meta: { title: 'Market News Report' } },
  { path: '/research-interaction/:reportId', alias: '/interaction/:reportId', name: 'Interaction', component: InteractionView, props: true, meta: { title: 'Research Interaction' } }
]

const router = createRouter({ history: createWebHistory(), routes })
router.afterEach(to => { document.title = `${to.meta.title || 'News Intelligence'} | PilkQuant` })

export default router
