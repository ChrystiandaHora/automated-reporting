<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Dashboard de Indicadores</h1>
        <HelpModal title="Sobre o Dashboard" :items="helpItems" />
      </div>

      <!-- Filtro Mês a Mês -->
      <div v-if="store.stats" class="header-filter-box">
        <label for="mes-filtro-dashboard" class="filter-label">Período:</label>
        <select id="mes-filtro-dashboard" v-model="mesSelecionado" class="select-periodo" aria-label="Filtrar indicadores por mês">
          <option value="todos">Todos os Meses (Consolidado)</option>
          <option v-for="m in store.stats.months" :key="m" :value="m">
            {{ formatarMesExtenso(m) }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="store.loading" class="loading" role="status" aria-live="polite">
      Carregando indicadores do dashboard...
    </div>

    <div v-else class="dashboard-content">
      
      <!-- Cards de Resumo Principal -->
      <section class="summary-grid" aria-label="Resumo geral de indicadores">
        <div class="kpi-card highlight-blue">
          <div class="kpi-icon-wrap">
            <i class="fa-solid fa-list-check" aria-hidden="true"></i>
          </div>
          <div class="kpi-body">
            <span class="kpi-card-label">Total de Tarefas</span>
            <span class="kpi-card-val">{{ statsExibidas.total_tasks }}</span>
            <span class="kpi-card-sub">atividades identificadas</span>
          </div>
        </div>

        <div class="kpi-card highlight-green">
          <div class="kpi-icon-wrap">
            <i class="fa-solid fa-clock" aria-hidden="true"></i>
          </div>
          <div class="kpi-body">
            <span class="kpi-card-label">Total Horas HPA</span>
            <span class="kpi-card-val">{{ statsExibidas.total_hpa }}h</span>
            <span class="kpi-card-sub">faturamento previsto</span>
          </div>
        </div>

        <div class="kpi-card highlight-purple">
          <div class="kpi-icon-wrap">
            <i class="fa-solid fa-shapes" aria-hidden="true"></i>
          </div>
          <div class="kpi-body">
            <span class="kpi-card-label">Tipos Distintos</span>
            <span class="kpi-card-val">{{ Object.keys(statsExibidas.codes).length }}</span>
            <span class="kpi-card-sub">códigos de serviço</span>
          </div>
        </div>

        <div class="kpi-card highlight-amber">
          <div class="kpi-icon-wrap">
            <i class="fa-solid fa-chart-simple" aria-hidden="true"></i>
          </div>
          <div class="kpi-body">
            <span class="kpi-card-label">Média HPA / Tarefa</span>
            <span class="kpi-card-val">{{ mediaHpaPorTarefa }}h</span>
            <span class="kpi-card-sub">esforço médio estimado</span>
          </div>
        </div>
      </section>

      <!-- Painel de Repositórios & Distribuição -->
      <section class="dashboard-panel" aria-label="Distribuição por Repositório">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fa-brands fa-git-alt" aria-hidden="true" style="color: #f97316; font-size: 1.15rem;"></i>
            <h2>Distribuição por Repositório</h2>
          </div>
          <router-link to="/commits" class="link-action">Ver lista de commits →</router-link>
        </div>

        <div v-if="distribuicaoRepositorios.length === 0" class="panel-empty">
          Nenhum commit ou repositório cadastrado.
        </div>

        <div v-else class="repos-kpi-grid">
          <div 
            v-for="repo in distribuicaoRepositorios" 
            :key="repo.nome" 
            class="repo-stat-card"
          >
            <div class="repo-card-top">
              <div class="repo-name-group">
                <i class="fa-solid fa-folder-open" aria-hidden="true" style="color: var(--accent); font-size: 0.95rem;"></i>
                <span class="repo-name" :title="repo.nome">{{ repo.nome }}</span>
              </div>
              <span class="repo-commits-count">{{ repo.commitsCount }} commit{{ repo.commitsCount > 1 ? 's' : '' }}</span>
            </div>

            <div class="repo-card-stats">
              <div class="repo-stat-item">
                <span class="repo-stat-lbl">Tarefas:</span>
                <span class="repo-stat-val">{{ repo.analisados + repo.pendentes }}</span>
              </div>
              <div class="repo-stat-item">
                <span class="repo-stat-lbl">HPA Total:</span>
                <span class="repo-stat-val">{{ repo.totalHpa }}h</span>
              </div>
            </div>

            <div class="progress-bar" role="progressbar" :aria-valuenow="repo.pctTotal" aria-valuemin="0" aria-valuemax="100" :aria-label="`Representatividade de ${repo.nome}`">
              <div class="progress-fill" :style="{ width: `${repo.pctTotal}%` }"></div>
            </div>
            <span class="progress-sub">{{ repo.pctTotal }}% do total de commits</span>
          </div>
        </div>
      </section>

      <!-- Painel de Quantificação por Tipo de Serviço -->
      <section class="dashboard-panel" aria-label="Quantificação por Tipo de Serviço">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fa-solid fa-tags" aria-hidden="true" style="color: #38bdf8; font-size: 1.15rem;"></i>
            <h2>Quantificação por Tipo de Serviço</h2>
          </div>
          <span class="panel-subtitle">Baseado nas atividades geradas pelas análises de IA</span>
        </div>

        <div v-if="Object.keys(statsExibidas.codes).length === 0" class="panel-empty">
          Nenhuma atividade registrada para o período selecionado.
        </div>

        <div v-else class="codes-grid">
          <div 
            v-for="(info, code) in statsExibidas.codes" 
            :key="code"
            class="code-card"
          >
            <div class="code-card-header">
              <span class="badge badge-code"><code>{{ code }}</code></span>
              <span class="code-tasks-count">{{ info.count }} tarefa{{ info.count > 1 ? 's' : '' }}</span>
            </div>

            <div class="code-card-footer">
              <span class="code-hpa-val">{{ info.hpa }}h HPA</span>
              <span class="code-pct-val" v-if="statsExibidas.total_tasks > 0">
                {{ Math.round((info.count / statsExibidas.total_tasks) * 100) }}%
              </span>
            </div>

            <!-- Barra de Progresso Visual -->
            <div class="progress-bar" role="progressbar" :aria-valuenow="statsExibidas.total_tasks > 0 ? Math.round((info.count / statsExibidas.total_tasks) * 100) : 0" aria-valuemin="0" aria-valuemax="100" :aria-label="`Percentual do serviço ${code}`">
              <div 
                class="progress-fill" 
                :style="{ width: `${statsExibidas.total_tasks > 0 ? (info.count / statsExibidas.total_tasks) * 100 : 0}%` }"
              ></div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCommitsStore } from '../stores/commits'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Visão Geral do Dashboard', text: 'Esta tela consolida os indicadores globais de faturamento HPA, tipos de serviço prestados e a distribuição de atividades por repositório.' },
  { title: 'Filtro por Período', text: 'Você pode selecionar um mês específico para avaliar a produtividade mensal ou manter em "Todos os Meses" para uma análise acumulada.' },
  { title: 'Códigos de Serviço', text: 'Cada código representa um item de serviço faturável identificado e justificado automaticamente pelo modelo de IA com base nas mudanças de código.' },
]

const store = useCommitsStore()
const mesSelecionado = ref<string>('todos')

onMounted(async () => {
  if (store.commits.length === 0) {
    await store.fetchCommits()
  } else if (!store.stats) {
    await store.fetchStats()
  }
})

const statsExibidas = computed(() => {
  if (!store.stats) {
    return { codes: {}, total_tasks: 0, total_hpa: 0 }
  }
  if (mesSelecionado.value === 'todos') {
    return store.stats.totals
  }
  return store.stats.by_month[mesSelecionado.value] || { codes: {}, total_tasks: 0, total_hpa: 0 }
})

const mediaHpaPorTarefa = computed(() => {
  const total = statsExibidas.value.total_tasks
  const hpa = statsExibidas.value.total_hpa
  if (!total || total === 0) return '0.0'
  return (hpa / total).toFixed(1)
})

function formatarMesExtenso(mesAno: string): string {
  if (!mesAno || !mesAno.includes('/')) return mesAno
  const [mes, ano] = mesAno.split('/')
  const meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]
  const mesIdx = parseInt(mes, 10) - 1
  const nomeMes = meses[mesIdx] || mes
  return `${nomeMes} de ${ano}`
}

function obterClasseCorRepo(nome?: string): string {
  if (!nome) return 'repo-color-default'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const idx = Math.abs(hash) % 6
  return `repo-color-${idx}`
}

const distribuicaoRepositorios = computed(() => {
  const total = store.commits.length
  if (total === 0) return []

  const map: Record<string, {
    nome: string
    commitsCount: number
    analisados: number
    pendentes: number
    totalHpa: number
    colorClass: string
    pctTotal: number
  }> = {}

  for (const c of store.commits) {
    const nome = c.projeto?.trim() || 'Sem repositório'
    if (!map[nome]) {
      map[nome] = {
        nome,
        commitsCount: 0,
        analisados: 0,
        pendentes: 0,
        totalHpa: 0,
        colorClass: obterClasseCorRepo(nome),
        pctTotal: 0
      }
    }
    map[nome].commitsCount++
    if (c.analisado) map[nome].analisados++
    else map[nome].pendentes++
    if (c.hpa_total) map[nome].totalHpa += c.hpa_total
  }

  return Object.values(map)
    .map(r => ({
      ...r,
      pctTotal: Math.round((r.commitsCount / total) * 100)
    }))
    .sort((a, b) => b.commitsCount - a.commitsCount)
})
</script>

<style scoped>
.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-filter-box {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.filter-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted, #8b949e);
}

.select-periodo {
  background: var(--bg, #0d1117);
  color: var(--text, #f0f6fc);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 0.5rem 0.9rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s ease;
}

.select-periodo:hover, .select-periodo:focus {
  border-color: var(--accent, #58a6ff);
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ── RESUMO PRINCIPAL ── */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
}

.kpi-card {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.2rem 1.4rem;
  display: flex;
  align-items: center;
  gap: 1.1rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent, #58a6ff);
}

.kpi-icon-wrap {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.highlight-blue .kpi-icon-wrap {
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.highlight-green .kpi-icon-wrap {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.highlight-purple .kpi-icon-wrap {
  background: rgba(192, 132, 252, 0.12);
  color: #c084fc;
  border: 1px solid rgba(192, 132, 252, 0.3);
}

.highlight-amber .kpi-icon-wrap {
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.kpi-body {
  display: flex;
  flex-direction: column;
}

.kpi-card-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted, #8b949e);
  letter-spacing: 0.05em;
}

.kpi-card-val {
  font-size: 1.8rem;
  font-weight: 900;
  color: var(--text, #f0f6fc);
  line-height: 1.2;
  margin: 0.15rem 0;
}

.kpi-card-sub {
  font-size: 0.76rem;
  color: var(--text-muted, #8b949e);
}

/* ── PAINÉIS DO DASHBOARD ── */
.dashboard-panel {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.35rem 1.6rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border, #30363d);
  padding-bottom: 0.85rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--accent, #58a6ff);
}

.panel-title h2 {
  font-size: 1.15rem;
  font-weight: 800;
  margin: 0;
  color: var(--text, #f0f6fc);
}

.panel-subtitle {
  font-size: 0.82rem;
  color: var(--text-muted, #8b949e);
}

.link-action {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent, #58a6ff);
  text-decoration: none;
  transition: opacity 0.15s;
}

.link-action:hover {
  text-decoration: underline;
}

.panel-empty {
  font-size: 0.9rem;
  color: var(--text-muted, #8b949e);
  padding: 1.5rem 0;
  font-style: italic;
}

/* ── GRID DE REPOSITÓRIOS ── */
.repos-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.repo-stat-card {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 10px;
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  transition: all 0.15s ease;
}

.repo-stat-card:hover {
  border-color: var(--accent, #58a6ff);
  transform: translateY(-2px);
}

.repo-stat-top {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.repo-stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.repo-stat-name {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.repo-stat-count {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.repo-stat-metrics {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  border-top: 1px dashed var(--border, #30363d);
  padding-top: 0.45rem;
}

.repo-metric-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.metric-label {
  color: var(--text-muted, #8b949e);
}

.metric-val {
  font-weight: 800;
}

.text-green { color: #34d399; }
.text-muted { color: var(--text-muted, #8b949e); }
.text-amber { color: #fbbf24; }

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #6366f1);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-sub {
  font-size: 0.72rem;
  color: var(--text-muted, #8b949e);
}

/* ── GRID DE CÓDIGOS DE SERVIÇO ── */
.codes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 0.9rem;
}

.code-card {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: all 0.15s ease;
}

.code-card:hover {
  border-color: var(--accent, #58a6ff);
  transform: translateY(-2px);
}

.code-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.code-tasks-count {
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
}

.code-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-muted, #8b949e);
}

.code-hpa-val {
  font-weight: 700;
}

.code-pct-val {
  font-weight: 800;
  color: var(--accent, #58a6ff);
}

/* Cores de repositórios */
.repo-color-0 { background: #38bdf8; }
.repo-color-1 { background: #c084fc; }
.repo-color-2 { background: #34d399; }
.repo-color-3 { background: #fbbf24; }
.repo-color-4 { background: #f472b6; }
.repo-color-5 { background: #818cf8; }
.repo-color-default { background: #94a3b8; }
</style>
