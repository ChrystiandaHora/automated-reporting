<template>
  <div class="mx-auto max-w-[1200px] p-6">
    <!-- Header da Página -->
    <PageHeader class="flex-wrap gap-4">
      <div class="flex items-center gap-3">
        <PageTitle>Logs de Execução</PageTitle>
        <TutorialModal screenId="fila-logs" />
        <span v-if="logs.length > 0" class="rounded-xl border border-border bg-background px-2.5 py-0.75 text-sm text-muted-foreground">
          {{ logsFiltrados.length }} de {{ logs.length }} log{{ logs.length > 1 ? 's' : '' }}
        </span>
      </div>

      <div class="flex items-center gap-3" data-tour="fila-logs-acoes">
        <!-- Botão Excluir Selecionados -->
        <button 
          v-if="selecionados.length > 0"
          type="button"
          data-tour="fila-logs-excluir-selecionados"
          class="cursor-pointer rounded-md border border-red-500/40 bg-red-500/12 px-3 py-1.5 text-sm text-danger transition hover:border-danger hover:bg-red-500/22" 
          @click="removerSelecionados"
          :title="`Excluir ${selecionados.length} log(s) selecionado(s)`"
          aria-label="Excluir logs selecionados"
        >
          <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
          <span>Excluir Selecionados ({{ selecionados.length }})</span>
        </button>

        <BaseButton size="sm" @click="carregarLogs">
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
          <span>Atualizar</span>
        </BaseButton>
      </div>
    </PageHeader>

    <!-- Barra de Filtros e Seleção -->
    <FiltersBar class="shadow-card" role="search" aria-label="Filtros de logs" data-tour="fila-logs-filtros">
      <SearchBox
        v-model="filtroTexto"
        placeholder="Buscar por título, commit ou conteúdo de log..."
        aria-label="Buscar nos logs de execução"
        data-tour="fila-logs-busca"
      />

      <!-- Filtro de Status -->
      <div class="inline-flex flex-wrap items-center gap-1.5" role="group" aria-label="Filtrar por status" data-tour="fila-logs-status">
        <button 
          type="button"
          data-tour="fila-logs-pill"
          :class="classesPill.todos"
          @click="filtroStatus = 'todos'"
        >
          Todos ({{ logs.length }})
        </button>
        <button 
          type="button"
          data-tour="fila-logs-pill"
          :class="classesPill.retrying"
          @click="filtroStatus = 'retrying'"
        >
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
          <span>Retries ({{ countStatus('retrying') }})</span>
        </button>
        <button 
          type="button"
          data-tour="fila-logs-pill"
          :class="classesPill.error"
          @click="filtroStatus = 'error'"
        >
          <i class="fa-solid fa-circle-xmark" aria-hidden="true"></i>
          <span>Erros ({{ countStatus('error') }})</span>
        </button>
        <button 
          type="button"
          data-tour="fila-logs-pill"
          :class="classesPill.done"
          @click="filtroStatus = 'done'"
        >
          <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
          <span>Sucesso ({{ countStatus('done') }})</span>
        </button>
      </div>

      <!-- Checkbox de Selecionar Todos -->
      <div v-if="logsFiltrados.length > 0" class="flex items-center">
        <label :class="labelCheck" for="select-all-checkbox">
          <input 
            id="select-all-checkbox"
            type="checkbox" 
            class="size-4 cursor-pointer accent-primary"
            :checked="todosSelecionados" 
            @change="alternarSelecionarTodos"
            aria-label="Selecionar todos os logs visíveis"
          />
          <span>Selecionar Todos</span>
        </label>
      </div>
    </FiltersBar>

    <!-- Indicador de Carregamento -->
    <StateMessage v-if="loading && logs.length === 0" type="loading" class="rounded-xl border border-border bg-card p-12 shadow-card" role="status">
      Carregando histórico de logs...
    </StateMessage>

    <!-- Estado Vazio -->
    <StateMessage v-else-if="logsFiltrados.length === 0" type="empty" class="rounded-xl border border-border bg-card p-12 shadow-card" role="status">
      {{ filtroTexto || filtroStatus !== 'todos' ? 'Nenhum log encontrado para os filtros selecionados.' : 'Nenhum log de execução salvo ainda.' }}
    </StateMessage>

    <!-- Lista de Logs -->
    <div v-else class="flex flex-col gap-3.5" role="feed" aria-label="Lista de logs de execução" data-tour="fila-logs-lista">
      <article 
        v-for="log in logsFiltrados" 
        :key="log.id" 
        :class="[cardLog, bordaPorStatus[log.status]]"
        data-tour="fila-logs-card"
      >
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted px-4 py-3">
          <div class="flex items-center gap-2.5">
            <!-- Checkbox Individual -->
            <label :class="labelCheck" :for="`checkbox-log-${log.id}`">
              <input 
                :id="`checkbox-log-${log.id}`"
                type="checkbox" 
                class="size-4 cursor-pointer accent-primary"
                :checked="isSelecionado(log.id)" 
                @change="alternarSelecao(log.id)"
                :aria-label="`Selecionar log #${log.id} da atividade ${log.titulo_atividade || log.commit_id}`"
              />
            </label>

            <!-- Badge Tipo -->
            <BaseBadge :variant="log.tipo === 'analise' ? 'blue' : 'purple'">
              {{ log.tipo === 'analise' ? 'Análise AI' : 'Envio Portal' }}
            </BaseBadge>

            <!-- Badge Status / Tentativa -->
            <BaseBadge :variant="varianteStatusBadge(log.status)" :class="classeBadgeStatus(log.status)">
              <i v-if="log.status === 'done'" class="fa-solid fa-circle-check mr-1" aria-hidden="true"></i>
              <i v-else-if="log.status === 'retrying'" class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
              <i v-else-if="log.status === 'error'" class="fa-solid fa-circle-xmark mr-1" aria-hidden="true"></i>
              {{ obterTextoStatus(log) }}
            </BaseBadge>

            <!-- Data / Timestamp -->
            <span class="text-xs text-muted-foreground" :title="formatarDataCompleta(log.criado_em)">
              {{ formatarDataRelativa(log.criado_em) }}
            </span>
          </div>

          <div class="flex items-center gap-2.5">
            <!-- Link do Commit -->
            <router-link 
              v-if="log.commit_id" 
              :to="`/commits/${log.commit_id}`" 
              class="rounded-md border border-border bg-background px-2 py-[3px] font-mono text-[0.8rem] text-muted-foreground transition-all duration-200 hover:border-primary hover:bg-primary-glow hover:text-primary"
              :title="`Ver commit ${log.commit_id}`"
            >
              {{ log.commit_id.slice(0, 8) }}
            </router-link>

            <!-- Botão de Expandir / Colapsar Terminal -->
            <BaseButton
              size="xs"
              :aria-expanded="isExpandido(log.id)"
              :aria-controls="`terminal-body-${log.id}`"
              @click="alternarExpandir(log.id)"
            >
              <i :class="[isExpandido(log.id) ? 'fa-solid fa-chevron-up' : 'fa-solid fa-chevron-down', 'mr-1']" aria-hidden="true"></i>
              <span>{{ isExpandido(log.id) ? 'Ocultar Texto' : 'Expandir Logs' }}</span>
            </BaseButton>

            <!-- Botão Deletar Individual -->
            <button 
              type="button"
              class="cursor-pointer rounded-[5px] border border-red-500/40 bg-red-500/12 px-2.25 py-1 text-xs text-danger transition hover:border-danger hover:bg-red-500/22" 
              @click="removerLog(log.id)"
              :aria-label="`Excluir log #${log.id}`"
              title="Excluir este log"
            >
              <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
              <span>Excluir</span>
            </button>
          </div>
        </div>

        <div class="px-4 py-3.5">
          <div class="mb-2.5 flex flex-col gap-1.25 text-sm text-foreground">
            <span v-if="log.titulo_atividade" class="font-semibold text-foreground">
              <strong>Atividade:</strong> "{{ log.titulo_atividade }}"
            </span>
            <span v-if="log.commit_mensagem" class="truncate text-sm text-muted-foreground" :title="log.commit_mensagem">
              <strong>Commit:</strong> {{ log.commit_mensagem }}
            </span>
          </div>

          <!-- Resumo de Primeira / Última linha se colapsado -->
          <div v-if="!isExpandido(log.id)" class="flex cursor-pointer items-center justify-between rounded-lg border border-border bg-background px-3.5 py-2 font-mono text-sm text-muted-foreground transition hover:border-primary hover:text-foreground" @click="alternarExpandir(log.id)">
            <span class="max-w-[78%] truncate">
              {{ obterResumoLog(log) }}
            </span>
            <span class="shrink-0 font-sans text-xs font-medium text-primary">(Clique para expandir texto completo)</span>
          </div>

          <!-- Terminal de Logs Formatado (Quando Expandido) -->
          <div 
            v-show="isExpandido(log.id)" 
            :id="`terminal-body-${log.id}`" 
            class="mt-2.5 overflow-hidden rounded-lg border border-border bg-terminal shadow-[inset_0_2px_8px] shadow-black/40"
          >
            <div class="flex items-center justify-between border-b border-white/8 bg-gray-900 px-3.5 py-2 text-xs text-gray-400">
              <span>Terminal de Log de Execução (Tentativa #{{ log.tentativa }})</span>
              <button 
                type="button" 
                class="cursor-pointer rounded border border-white/20 bg-transparent px-2 py-0.75 text-xs text-gray-300 transition hover:bg-white/10 hover:text-white" 
                @click="copiarTextoLog(log)"
                aria-label="Copiar texto dos logs para a área de transferência"
              >
                <i class="fa-solid fa-copy" aria-hidden="true"></i>
                <span>Copiar</span>
              </button>
            </div>
            <pre class="max-h-95 overflow-y-auto bg-terminal p-3.5 font-terminal text-xs leading-normal break-words whitespace-pre-wrap text-gray-200"><div v-for="(linha, idx) in log.logs" :key="idx" :class="{'text-red-400': linha.includes('\u274c') || linha.includes('ERRO') || linha.includes('Falha'), 'text-yellow-300': linha.includes('\u26a0') || linha.includes('\u23f8')}">{{ linha }}</div></pre>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type FilaLogItem } from '../api'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import FiltersBar from '../components/ui/FiltersBar.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import SearchBox from '../components/ui/SearchBox.vue'
import StateMessage from '../components/ui/StateMessage.vue'

const toastStore = useToastStore()

const logs = ref<FilaLogItem[]>([])
const loading = ref(false)
const filtroTexto = ref('')
const filtroStatus = ref<'todos' | 'retrying' | 'error' | 'done'>('todos')
const selecionados = ref<number[]>([])
const expandidos = ref<Record<number, boolean>>({})

// ── Classes reutilizadas no template ──
const badgeErro = 'border border-red-500/30 bg-red-500/12 text-danger'
const labelCheck = 'mb-1.5 flex cursor-pointer items-center gap-1.5 text-sm font-bold tracking-[0.05em] text-muted-foreground uppercase select-none'
const cardLog = 'overflow-hidden rounded-xl border border-border bg-card shadow-card transition duration-250 hover:border-primary hover:border-l-primary hover:shadow-[0_8px_25px_rgba(0,0,0,0.08)]'
const bordaPorStatus: Record<string, string> = {
  retrying: 'border-l-4 border-l-warning',
  error: 'border-l-4 border-l-danger',
  done: 'border-l-4 border-l-success',
}

const pillBase = 'inline-flex h-[34px] cursor-pointer items-center gap-[0.45rem] rounded-lg border px-3 text-[0.82rem] select-none transition-all duration-200'
const pillInativo = 'border-border bg-background font-medium text-muted-foreground hover:border-border-strong hover:bg-muted hover:text-foreground'
const pillAtivo: Record<string, string> = {
  todos: 'border-primary bg-primary font-semibold text-white',
  retrying: 'border-warning bg-warning font-semibold text-white',
  error: 'border-danger bg-danger font-semibold text-white',
  done: 'border-success bg-success font-semibold text-white',
}
type FiltroStatus = 'todos' | 'retrying' | 'error' | 'done'
const classesPill = computed(() => {
  const montar = (valor: FiltroStatus) => [pillBase, filtroStatus.value === valor ? pillAtivo[valor] : pillInativo]
  return { todos: montar('todos'), retrying: montar('retrying'), error: montar('error'), done: montar('done') }
})

async function carregarLogs() {
  loading.value = true
  try {
    logs.value = await api.filaLogs.listar()
  } catch (e: any) {
    toastStore.addToast(`Erro ao carregar logs de execução: ${e.response?.data?.detail ?? String(e)}`, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  carregarLogs()
})

const logsFiltrados = computed(() => {
  return logs.value.filter(item => {
    // Filtro por status
    if (filtroStatus.value !== 'todos' && item.status !== filtroStatus.value) {
      return false
    }
    // Filtro por busca textual
    if (filtroTexto.value.trim()) {
      const q = filtroTexto.value.toLowerCase()
      const matchCommitMsg = item.commit_mensagem?.toLowerCase().includes(q)
      const matchTitulo = item.titulo_atividade?.toLowerCase().includes(q)
      const matchSha = item.commit_id?.toLowerCase().includes(q)
      const matchLogs = item.logs?.some(l => l.toLowerCase().includes(q))
      return matchCommitMsg || matchTitulo || matchSha || matchLogs
    }
    return true
  })
})

function countStatus(status: 'retrying' | 'error' | 'done') {
  return logs.value.filter(l => l.status === status).length
}

function isExpandido(id: number) {
  return !!expandidos.value[id]
}

function alternarExpandir(id: number) {
  expandidos.value[id] = !expandidos.value[id]
}

function isSelecionado(id: number) {
  return selecionados.value.includes(id)
}

function alternarSelecao(id: number) {
  if (isSelecionado(id)) {
    selecionados.value = selecionados.value.filter(sId => sId !== id)
  } else {
    selecionados.value.push(id)
  }
}

const todosSelecionados = computed(() => {
  if (logsFiltrados.value.length === 0) return false
  return logsFiltrados.value.every(item => selecionados.value.includes(item.id))
})

function alternarSelecionarTodos() {
  if (todosSelecionados.value) {
    // Desmarca todos os visíveis
    const visiveisIds = logsFiltrados.value.map(i => i.id)
    selecionados.value = selecionados.value.filter(id => !visiveisIds.includes(id))
  } else {
    // Marca todos os visíveis
    const visiveisIds = logsFiltrados.value.map(i => i.id)
    const set = new Set([...selecionados.value, ...visiveisIds])
    selecionados.value = Array.from(set)
  }
}

async function removerLog(id: number) {
  if (!confirm(`Tem certeza que deseja excluir o log #${id}?`)) return
  try {
    await api.filaLogs.remover(id)
    logs.value = logs.value.filter(l => l.id !== id)
    selecionados.value = selecionados.value.filter(sId => sId !== id)
    toastStore.addToast(`Log #${id} removido com sucesso.`, 'info')
  } catch (e: any) {
    toastStore.addToast(`Erro ao remover log: ${e.response?.data?.detail ?? String(e)}`, 'error')
  }
}

async function removerSelecionados() {
  const qtd = selecionados.value.length
  if (qtd === 0) return
  if (!confirm(`Tem certeza que deseja remover todos os ${qtd} log(s) selecionado(s)?`)) return

  try {
    await api.filaLogs.removerMultiplos(selecionados.value)
    logs.value = logs.value.filter(l => !selecionados.value.includes(l.id))
    toastStore.addToast(`${qtd} log(s) removido(s) com sucesso.`, 'success')
    selecionados.value = []
  } catch (e: any) {
    toastStore.addToast(`Erro ao remover logs: ${e.response?.data?.detail ?? String(e)}`, 'error')
  }
}

function obterTextoStatus(log: FilaLogItem) {
  if (log.status === 'done') return `Sucesso (Tentativa ${log.tentativa})`
  if (log.status === 'retrying') return `Retry (Tentativa ${log.tentativa})`
  if (log.status === 'error') return `Falha Final (Tentativa ${log.tentativa})`
  return log.status
}

function classeBadgeStatus(status: string) {
  return status === 'error' ? badgeErro : ''
}

function varianteStatusBadge(status: string) {
  if (status === 'done') return 'green'
  if (status === 'retrying') return 'orange'
  if (status === 'error') return 'plain'
  return 'blue'
}

function obterResumoLog(log: FilaLogItem) {
  if (!log.logs || log.logs.length === 0) return '(Sem conteúdo de log registrado)'
  const ultima = log.logs[log.logs.length - 1]
  return ultima
}

function copiarTextoLog(log: FilaLogItem) {
  const texto = log.logs ? log.logs.join('\n') : ''
  if (navigator.clipboard) {
    navigator.clipboard.writeText(texto).then(() => {
      toastStore.addToast('Texto do log copiado para a área de transferência.', 'info')
    })
  }
}

function formatarDataCompleta(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('pt-BR')
  } catch {
    return iso
  }
}

function formatarDataRelativa(iso: string) {
  if (!iso) return ''
  try {
    const data = new Date(iso)
    const agora = new Date()
    const diffMs = agora.getTime() - data.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    
    if (diffMin < 1) return 'Agora mesmo'
    if (diffMin < 60) return `Há ${diffMin} min`
    const diffHoras = Math.floor(diffMin / 60)
    if (diffHoras < 24) return `Há ${diffHoras}h`
    return data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}
</script>
