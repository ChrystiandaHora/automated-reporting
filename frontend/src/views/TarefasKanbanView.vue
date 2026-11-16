<template>
  <div>
    <header class="mb-4 flex flex-wrap items-center justify-between gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-bold text-foreground">Kanban de Tarefas - Munka</h1>
        <TutorialModal screenId="tarefas-kanban" />
        <span class="rounded-full bg-primary-glow px-2.5 py-0.5 text-xs font-bold text-primary-light">{{ tarefasFiltradas.length }} de {{ dados.total }}</span>
      </div>

      <div class="flex items-center gap-2" role="group" aria-label="Seletor de Mês e Ano">
        <button type="button" class="cursor-pointer rounded-lg border border-border bg-card px-3 py-1.5 text-foreground" aria-label="Mês anterior" @click="mudarMes(-1)">
          <i class="fa-solid fa-chevron-left" aria-hidden="true"></i>
        </button>
        <BaseSelect v-model.number="mes" auto-width aria-label="Mês selecionado" @change="carregar">
          <option v-for="(nome, idx) in meses" :key="idx" :value="idx + 1">{{ nome }}</option>
        </BaseSelect>
        <BaseInput v-model.number="ano" type="number" auto-width class="w-22" min="2020" max="2035" aria-label="Ano selecionado" @change="carregar" />
        <button type="button" class="cursor-pointer rounded-lg border border-border bg-card px-3 py-1.5 text-foreground" aria-label="Próximo mês" @click="mudarMes(1)">
          <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
        </button>
      </div>
    </header>

    <div data-tour="tarefas-kanban-filtros" class="mb-4 flex flex-wrap gap-4">
      <label class="mb-[0.35rem] flex flex-col gap-1">
        <span class="text-[0.7rem] font-bold uppercase text-subtle-foreground">Regra</span>
        <BaseSelect v-model="filtroRegra" aria-label="Filtrar por regra">
          <option value="">Todas</option>
          <option v-for="r in opcoesRegra" :key="r" :value="r">{{ r }}</option>
        </BaseSelect>
      </label>
      <label class="mb-[0.35rem] flex flex-col gap-1">
        <span class="text-[0.7rem] font-bold uppercase text-subtle-foreground">Nome da atividade</span>
        <BaseInput v-model="filtroAtividade" type="text" placeholder="Contém..." aria-label="Filtrar por nome da atividade" />
      </label>
    </div>

    <StateMessage v-if="loading" type="loading">Carregando tarefas...</StateMessage>

    <div v-else data-tour="tarefas-kanban-board" class="flex items-start gap-3 overflow-x-auto pb-3" role="list">
      <section v-for="col in colunas" :key="col.status.id" class="flex max-h-[70vh] flex-none basis-[280px] flex-col rounded-[10px] border border-border bg-card" role="listitem" :aria-label="col.status.rotulo">
        <header class="flex items-center justify-between border-b border-border px-3 py-2.5">
          <span class="text-[0.85rem] font-bold text-foreground">{{ col.status.rotulo }}</span>
          <span class="rounded-full bg-slate-400/15 px-2 py-0.5 text-xs font-bold text-muted-foreground">{{ col.tarefas.length }}</span>
        </header>
        <div class="flex flex-col gap-2 overflow-y-auto p-2.5">
          <p v-if="col.tarefas.length === 0" class="py-3 text-center text-[0.8rem] text-subtle-foreground">Nenhuma tarefa</p>
          <article v-for="t in col.tarefas" :key="t.id" class="flex flex-col gap-1.5 rounded-lg border border-border bg-background px-3 py-2.5">
            <div class="break-words text-[0.82rem] font-semibold text-foreground">{{ t.titulo }}</div>
            <div class="flex flex-wrap gap-1">
              <span v-if="t.codigo" class="rounded-md border border-badge-code-border bg-badge-code px-1.5 py-0.5 text-[0.68rem] font-bold text-badge-code-foreground">{{ t.codigo }}</span>
              <span class="rounded-md border border-badge-code-border bg-badge-code px-1.5 py-0.5 text-[0.68rem] font-bold text-badge-code-foreground">{{ t.hpa }}h</span>
              <span v-if="t.status_munka && t.status_munka !== col.status.rotulo" class="rounded-md border border-badge-orange-border bg-badge-orange px-1.5 py-0.5 text-[0.68rem] font-bold text-badge-orange-foreground" title="Texto no portal">{{ t.status_munka }}</span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <span v-if="t.munka_atualizado_em" class="text-[0.68rem] text-subtle-foreground">Atualizado em {{ formatarData(t.munka_atualizado_em) }}</span>
              <a v-if="t.task_url" :href="t.task_url" target="_blank" rel="noopener noreferrer" class="text-[0.8rem] text-primary-light" aria-label="Abrir tarefa no Munka">
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
import BaseInput from '../components/ui/BaseInput.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import StateMessage from '../components/ui/StateMessage.vue'

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
