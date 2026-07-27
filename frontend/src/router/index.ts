import { createRouter, createWebHistory } from 'vue-router'
import CommitsView from '../views/CommitsView.vue'
import CommitDetailView from '../views/CommitDetailView.vue'
import HistoryView from '../views/HistoryView.vue'
import ConfigView from '../views/ConfigView.vue'
import AnalisarView from '../views/AnalisarView.vue'
import FilaView from '../views/FilaView.vue'
import ModelosView from '../views/ModelosView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/commits' },
    { path: '/commits', component: CommitsView },
    { path: '/commits/:sha', component: CommitDetailView },
    { path: '/analisar', component: AnalisarView },
    { path: '/fila', component: FilaView },
    { path: '/modelos', component: ModelosView },
    { path: '/historico', component: HistoryView },
    { path: '/config', component: ConfigView },
  ],
})


