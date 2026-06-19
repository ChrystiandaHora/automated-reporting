import { createRouter, createWebHistory } from 'vue-router'
import CommitsView from '../views/CommitsView.vue'
import CommitDetailView from '../views/CommitDetailView.vue'
import HistoryView from '../views/HistoryView.vue'
import ConfigView from '../views/ConfigView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/commits' },
    { path: '/commits', component: CommitsView },
    { path: '/commits/:sha', component: CommitDetailView },
    { path: '/historico', component: HistoryView },
    { path: '/config', component: ConfigView },
  ],
})
