<template>
  <div class="page kanban-page">
    <header class="kanban-header">
      <div class="title-row">
        <h1>Kanban de Tarefas - Munka</h1>
        <TutorialModal screenId="tarefas-kanban" />
        <span class="counter-badge">{{ tarefasFiltradas.length }} de {{ dados.total }}</span>
      </div>

      <div class="periodo" role="group" aria-label="Seletor de Mês e Ano">
        <button type="button" class="btn-mes" aria-label="Mês anterior" @click="mudarMes(-1)">
          <i class="fa-solid fa-chevron-left" aria-hidden="true"></i>
        </button>
        <select v-model.number="mes" class="filter-select" aria-label="Mês selecionado" @change="carregar">
          <option v-for="(nome, idx) in meses" :key="idx" :value="idx + 1">{{ nome }}</option>
        </select>
        <input v-model.number="ano" type="number" class="filter-input ano" min="2020" max="2035" aria-label="Ano selecionado" @change="carregar" />
        <button type="button" class="btn-mes" aria-label="Próximo mês" @click="mudarMes(1)">
          <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
        </button>
      </div>
    </header>

    <div class="filters-bar">
      <label class="filter-field">
        <span class="filter-label">Regra</span>
        <select v-model="filtroRegra" class="filter-select" aria-label="Filtrar por regra">
          <option value="">Todas</option>
          <option v-for="r in opcoesRegra" :key="r" :value="r">{{ r }}</option>
        </select>
      </label>
      <label class="filter-field">
        <span class="filter-label">Nome da atividade</span>
        <input v-model="filtroAtividade" type="text" class="filter-input" placeholder="Contém..." aria-label="Filtrar por nome da atividade" />
      </label>
    </div>

    <div v-if="loading" class="loading">Carregando tarefas...</div>

    <div v-else class="kanban-board" role="list">
      <section v-for="col in colunas" :key="col.status.id" class="kanban-col" role="listitem" :aria-label="col.status.rotulo">
        <header class="kanban-col-head">
          <span class="col-title">{{ col.status.rotulo }}</span>
          <span class="col-count">{{ col.tarefas.length }}</span>
        </header>
        <div class="kanban-col-body">
          <p v-if="col.tarefas.length === 0" class="col-vazia">Nenhuma tarefa</p>
          <article v-for="t in col.tarefas" :key="t.id" class="kanban-card">
            <div class="card-titulo">{{ t.titulo }}</div>
            <div class="card-meta">
              <span v-if="t.codigo" class="chip">{{ t.codigo }}</span>
              <span class="chip">{{ t.hpa }}h</span>
              <span v-if="t.status_munka && t.status_munka !== col.status.rotulo" class="chip chip-portal" :title="'Texto no portal'">{{ t.status_munka }}</span>
            </div>
            <div class="card-rodape">
              <span v-if="t.munka_atualizado_em" class="card-data">Atualizado em {{ formatarData(t.munka_atualizado_em) }}</span>
              <a v-if="t.task_url" :href="t.task_url" target="_blank" rel="noopener noreferrer" class="card-link" aria-label="Abrir tarefa no Munka">
                <i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i>
              </a>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { api, type TarefaMesItem, type TarefasMesResponse } from '../api'
import { useToastStore } from '../stores/toast'
import { useTarefasMesStore } from '../stores/tarefasMes'
import { CATALOGO_STATUS, STATUS_OUTROS, resolverStatus, type StatusMunka } from '../config/statusMunka'
import TutorialModal from '../components/TutorialModal.vue'

const meses = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const toastStore = useToastStore()
const { mes, ano } = storeToRefs(useTarefasMesStore())

const loading = ref(false)
const dados = ref<TarefasMesResponse>({ mes: mes.value, ano: ano.value, total: 0, editaveis: 0, concluidas: 0, tarefas: [] })
const filtroRegra = ref('')
const filtroAtividade = ref('')

const opcoesRegra = computed(() =>
  [...new Set(dados.value.tarefas.map(t => t.codigo).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
)

const tarefasFiltradas = computed(() => {
  const q = filtroAtividade.value.trim().toLowerCase()
  return dados.value.tarefas.filter(t => {
    if (filtroRegra.value && t.codigo !== filtroRegra.value) return false
    if (q && !(t.titulo || '').toLowerCase().includes(q)) return false
    return true
  })
})

const colunas = computed(() => {
  const porStatus = new Map<string, TarefaMesItem[]>()
  for (const t of tarefasFiltradas.value) {
    const id = resolverStatus(t.status_munka || t.status)?.id ?? STATUS_OUTROS.id
    if (!porStatus.has(id)) porStatus.set(id, [])
    porStatus.get(id)!.push(t)
  }
  const cols: { status: StatusMunka; tarefas: TarefaMesItem[] }[] = CATALOGO_STATUS.map(s => ({
    status: s,
    tarefas: porStatus.get(s.id) || []
  }))
  const outros = porStatus.get(STATUS_OUTROS.id) || []
  if (outros.length) cols.push({ status: STATUS_OUTROS, tarefas: outros })
  return cols
})

function mudarMes(delta: number) {
  let m = mes.value + delta
  let a = ano.value
  if (m < 1) { m = 12; a-- }
  if (m > 12) { m = 1; a++ }
  mes.value = m
  ano.value = a
  carregar()
}

function formatarData(iso: string): string {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

async function carregar() {
  loading.value = true
  try {
    dados.value = await api.tarefasMes.listar(mes.value, ano.value)
  } catch (e: any) {
    toastStore.addToast(`Erro ao carregar tarefas do mês: ${e.message || e}`, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.kanban-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem; }
.title-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.title-row h1 { font-size: 1.5rem; font-weight: 700; color: var(--text); }
.counter-badge { font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 999px; background: var(--accent-glow); color: var(--accent-light); }
.periodo { display: flex; align-items: center; gap: 0.5rem; }
.btn-mes { background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text); border-radius: 8px; padding: 0.4rem 0.7rem; cursor: pointer; }
.filters-bar { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.filter-field { display: flex; flex-direction: column; gap: 0.25rem; }
.filter-label { font-size: 0.7rem; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; }
.filter-select, .filter-input { background: var(--card-bg); border: 1px solid var(--input-border); color: var(--text); border-radius: 8px; padding: 0.4rem 0.6rem; font-size: 0.85rem; }
.filter-input.ano { width: 5.5rem; }

.kanban-board { display: flex; gap: 0.75rem; overflow-x: auto; padding-bottom: 0.75rem; align-items: flex-start; }
.kanban-col { flex: 0 0 280px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; display: flex; flex-direction: column; max-height: 70vh; }
.kanban-col-head { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--card-border); }
.col-title { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.col-count { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); background: rgba(148, 163, 184, 0.15); border-radius: 999px; padding: 0.1rem 0.5rem; }
.kanban-col-body { padding: 0.6rem; display: flex; flex-direction: column; gap: 0.5rem; overflow-y: auto; }
.col-vazia { font-size: 0.8rem; color: var(--text-subtle); text-align: center; padding: 0.75rem 0; }
.kanban-card { background: var(--bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.6rem 0.7rem; display: flex; flex-direction: column; gap: 0.4rem; }
.card-titulo { font-size: 0.82rem; font-weight: 600; color: var(--text); word-break: break-word; }
.card-meta { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.chip { font-size: 0.68rem; font-weight: 700; padding: 0.1rem 0.45rem; border-radius: 6px; background: var(--badge-code-bg); color: var(--badge-code-color); border: 1px solid var(--badge-code-border); }
.chip-portal { background: var(--badge-orange-bg); color: var(--badge-orange-color); border-color: var(--badge-orange-border); }
.card-rodape { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.card-data { font-size: 0.68rem; color: var(--text-subtle); }
.card-link { color: var(--accent-light); font-size: 0.8rem; }
</style>
