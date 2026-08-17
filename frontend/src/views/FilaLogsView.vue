<template>
  <div class="page">
    <!-- Header da Página -->
    <div class="page-header">
      <div class="title-row">
        <h1>Logs de Execução</h1>
        <span v-if="logs.length > 0" class="logs-count-badge">
          {{ logsFiltrados.length }} de {{ logs.length }} log{{ logs.length > 1 ? 's' : '' }}
        </span>
      </div>

      <div class="header-actions">
        <!-- Botão Excluir Selecionados -->
        <button 
          v-if="selecionados.length > 0"
          type="button"
          class="btn-danger-link btn-bulk-delete" 
          @click="removerSelecionados"
          :title="`Excluir ${selecionados.length} log(s) selecionado(s)`"
          aria-label="Excluir logs selecionados"
        >
          🗑️ Excluir Selecionados ({{ selecionados.length }})
        </button>

        <button type="button" class="btn-ghost btn-sm" @click="carregarLogs">↻ Atualizar</button>
      </div>
    </div>

    <!-- Barra de Filtros e Seleção -->
    <div class="filters-bar" role="search" aria-label="Filtros de logs">
      <div class="search-box">
        <span class="search-icon" aria-hidden="true">🔍</span>
        <input 
          id="search-logs-input"
          v-model="filtroTexto" 
          type="search" 
          placeholder="Buscar por título, commit ou conteúdo de log..." 
          aria-label="Buscar nos logs de execução"
          class="input-search"
        />
        <button 
          v-if="filtroTexto" 
          type="button" 
          class="btn-clear-search" 
          @click="filtroTexto = ''"
          aria-label="Limpar busca"
        >
          ✕
        </button>
      </div>

      <!-- Filtro de Status -->
      <div class="status-filters" role="group" aria-label="Filtrar por status">
        <button 
          type="button"
          class="filter-pill"
          :class="{ active: filtroStatus === 'todos' }"
          @click="filtroStatus = 'todos'"
        >
          Todos ({{ logs.length }})
        </button>
        <button 
          type="button"
          class="filter-pill filter-retrying"
          :class="{ active: filtroStatus === 'retrying' }"
          @click="filtroStatus = 'retrying'"
        >
          🔄 Retries ({{ countStatus('retrying') }})
        </button>
        <button 
          type="button"
          class="filter-pill filter-error"
          :class="{ active: filtroStatus === 'error' }"
          @click="filtroStatus = 'error'"
        >
          ❌ Erros ({{ countStatus('error') }})
        </button>
        <button 
          type="button"
          class="filter-pill filter-done"
          :class="{ active: filtroStatus === 'done' }"
          @click="filtroStatus = 'done'"
        >
          ✔ Sucesso ({{ countStatus('done') }})
        </button>
      </div>

      <!-- Checkbox de Selecionar Todos -->
      <div v-if="logsFiltrados.length > 0" class="select-all-container">
        <label class="checkbox-label" for="select-all-checkbox">
          <input 
            id="select-all-checkbox"
            type="checkbox" 
            :checked="todosSelecionados" 
            @change="alternarSelecionarTodos"
            aria-label="Selecionar todos os logs visíveis"
          />
          <span>Selecionar Todos</span>
        </label>
      </div>
    </div>

    <!-- Indicador de Carregamento -->
    <div v-if="loading && logs.length === 0" class="loading" role="status">
      Carregando histórico de logs...
    </div>

    <!-- Estado Vazio -->
    <div v-else-if="logsFiltrados.length === 0" class="empty" role="status">
      {{ filtroTexto || filtroStatus !== 'todos' ? 'Nenhum log encontrado para os filtros selecionados.' : 'Nenhum log de execução salvo ainda.' }}
    </div>

    <!-- Lista de Logs -->
    <div v-else class="logs-list" role="feed" aria-label="Lista de logs de execução">
      <article 
        v-for="log in logsFiltrados" 
        :key="log.id" 
        class="log-card"
        :class="`log-card-${log.status}`"
      >
        <div class="log-card-header">
          <div class="log-header-left">
            <!-- Checkbox Individual -->
            <label class="checkbox-label" :for="`checkbox-log-${log.id}`">
              <input 
                :id="`checkbox-log-${log.id}`"
                type="checkbox" 
                :checked="isSelecionado(log.id)" 
                @change="alternarSelecao(log.id)"
                :aria-label="`Selecionar log #${log.id} da atividade ${log.titulo_atividade || log.commit_id}`"
              />
            </label>

            <!-- Badge Tipo -->
            <span 
              class="badge" 
              :class="log.tipo === 'analise' ? 'badge-blue' : 'badge-purple'"
            >
              {{ log.tipo === 'analise' ? 'Análise AI' : 'Envio Portal' }}
            </span>

            <!-- Badge Status / Tentativa -->
            <span class="badge" :class="obterClasseStatusBadge(log.status)">
              {{ obterTextoStatus(log) }}
            </span>

            <!-- Data / Timestamp -->
            <span class="log-time" :title="formatarDataCompleta(log.criado_em)">
              {{ formatarDataRelativa(log.criado_em) }}
            </span>
          </div>

          <div class="log-header-right">
            <!-- Link do Commit -->
            <router-link 
              v-if="log.commit_id" 
              :to="`/commits/${log.commit_id}`" 
              class="commit-hash-link"
              :title="`Ver commit ${log.commit_id}`"
            >
              {{ log.commit_id.slice(0, 8) }}
            </router-link>

            <!-- Botão de Expandir / Colapsar Terminal -->
            <button 
              type="button"
              class="btn-ghost btn-xs"
              :aria-expanded="isExpandido(log.id)"
              :aria-controls="`terminal-body-${log.id}`"
              @click="alternarExpandir(log.id)"
            >
              {{ isExpandido(log.id) ? '▲ Ocultar Texto' : '▼ Expandir Logs' }}
            </button>

            <!-- Botão Deletar Individual -->
            <button 
              type="button"
              class="btn-danger-link btn-xs" 
              @click="removerLog(log.id)"
              :aria-label="`Excluir log #${log.id}`"
              title="Excluir este log"
            >
              🗑️ Excluir
            </button>
          </div>
        </div>

        <div class="log-card-body">
          <div class="log-meta-info">
            <span v-if="log.titulo_atividade" class="log-activity-title">
              <strong>Atividade:</strong> "{{ log.titulo_atividade }}"
            </span>
            <span v-if="log.commit_mensagem" class="log-commit-msg" :title="log.commit_mensagem">
              <strong>Commit:</strong> {{ log.commit_mensagem }}
            </span>
          </div>

          <!-- Resumo de Primeira / Última linha se colapsado -->
          <div v-if="!isExpandido(log.id)" class="log-preview" @click="alternarExpandir(log.id)">
            <span class="preview-text">
              {{ obterResumoLog(log) }}
            </span>
            <span class="preview-hint">(Clique para expandir texto completo)</span>
          </div>

          <!-- Terminal de Logs Formatado (Quando Expandido) -->
          <div 
            v-show="isExpandido(log.id)" 
            :id="`terminal-body-${log.id}`" 
            class="terminal-container"
          >
            <div class="terminal-header">
              <span>Terminal de Log de Execução (Tentativa #{{ log.tentativa }})</span>
              <button 
                type="button" 
                class="btn-copy-log" 
                @click="copiarTextoLog(log)"
                aria-label="Copiar texto dos logs para a área de transferência"
              >
                📋 Copiar
              </button>
            </div>
            <pre class="terminal-body"><div v-for="(linha, idx) in log.logs" :key="idx" :class="{'error-line': linha.startsWith('❌') || linha.includes('ERRO') || linha.includes('Falha'), 'warning-line': linha.startsWith('⚠️') || linha.startsWith('⏸️')}">{{ linha }}</div></pre>
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

const toastStore = useToastStore()

const logs = ref<FilaLogItem[]>([])
const loading = ref(false)
const filtroTexto = ref('')
const filtroStatus = ref<'todos' | 'retrying' | 'error' | 'done'>('todos')
const selecionados = ref<number[]>([])
const expandidos = ref<Record<number, boolean>>({})

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
  if (log.status === 'done') return `✔ Sucesso (Tentativa ${log.tentativa})`
  if (log.status === 'retrying') return `🔄 Retry (Tentativa ${log.tentativa})`
  if (log.status === 'error') return `❌ Falha Final (Tentativa ${log.tentativa})`
  return log.status
}

function obterClasseStatusBadge(status: string) {
  if (status === 'done') return 'badge-green'
  if (status === 'retrying') return 'badge-orange'
  if (status === 'error') return 'badge-red'
  return 'badge-blue'
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

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-row h1 {
  font-size: 1.6rem;
  font-weight: 700;
  margin: 0;
  color: var(--text);
}

.logs-count-badge {
  background: var(--bg);
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 0.2rem 0.65rem;
  border-radius: 12px;
  border: 1px solid var(--card-border);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-bulk-delete {
  font-size: 0.85rem;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.12);
  color: var(--error);
  transition: all 0.2s ease;
}

.btn-bulk-delete:hover {
  background: rgba(239, 68, 68, 0.22);
  border-color: var(--error);
}

.filters-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  background: var(--card-bg);
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 1px solid var(--card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 260px;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.9rem;
  color: var(--text-muted);
  pointer-events: none;
}

.input-search {
  width: 100%;
  padding: 0.5rem 2.2rem 0.5rem 2.2rem;
  border-radius: 8px;
  border: 1px solid var(--input-border);
  background: var(--bg);
  color: var(--text);
  font-size: 0.9rem;
  outline: none;
  transition: all 0.2s ease;
}

.input-search:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.btn-clear-search {
  position: absolute;
  right: 0.5rem;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.2rem;
  font-size: 0.85rem;
}

.status-filters {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.filter-pill {
  background: var(--bg);
  border: 1px solid var(--card-border);
  color: var(--text-muted);
  padding: 0.35rem 0.8rem;
  border-radius: 20px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-pill:hover {
  background: var(--header-group-bg);
  color: var(--text);
  border-color: var(--border);
}

.filter-pill.active {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
  font-weight: 600;
}

.filter-pill.filter-retrying.active {
  background: var(--warning);
  border-color: var(--warning);
  color: #ffffff;
}

.filter-pill.filter-error.active {
  background: var(--error);
  border-color: var(--error);
  color: #ffffff;
}

.filter-pill.filter-done.active {
  background: var(--success);
  border-color: var(--success);
  color: #ffffff;
}

.select-all-container {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.log-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  transition: all 0.25s ease;
}

.log-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
}

.log-card-retrying {
  border-left: 4px solid var(--warning);
}

.log-card-error {
  border-left: 4px solid var(--error);
}

.log-card-done {
  border-left: 4px solid var(--success);
}

.log-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--header-group-bg);
  border-bottom: 1px solid var(--card-border);
  flex-wrap: wrap;
  gap: 0.5rem;
}

.log-header-left, .log-header-right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.log-time {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.commit-hash-link {
  font-family: monospace;
  font-size: 0.82rem;
  background: var(--bg);
  border: 1px solid var(--card-border);
  color: var(--text-muted);
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.commit-hash-link:hover {
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
}

.log-card-body {
  padding: 0.85rem 1rem;
}

.log-meta-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.9rem;
  margin-bottom: 0.6rem;
  color: var(--text);
}

.log-activity-title {
  color: var(--text);
  font-weight: 600;
}

.log-commit-msg {
  font-size: 0.83rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.log-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0.85rem;
  background: var(--bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  cursor: pointer;
  font-family: monospace;
  font-size: 0.82rem;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.log-preview:hover {
  border-color: var(--accent);
  color: var(--text);
}

.preview-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 78%;
}

.preview-hint {
  font-family: inherit;
  font-size: 0.75rem;
  color: var(--accent);
  font-weight: 500;
  flex-shrink: 0;
}

/* Terminal Console Component */
.terminal-container {
  margin-top: 0.65rem;
  background: #090d16;
  border: 1px solid var(--card-border);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.45rem 0.85rem;
  background: #111827;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.78rem;
  color: #9ca3af;
}

.btn-copy-log {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #d1d5db;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-copy-log:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.terminal-body {
  padding: 0.85rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #e5e7eb;
  background: #090d16;
  max-height: 380px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.error-line {
  color: #f87171;
}

.warning-line {
  color: #fde047;
}

/* Badges Theme Responsive */
.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.badge-blue {
  background: var(--badge-code-bg);
  color: var(--badge-code-color);
  border: 1px solid var(--badge-code-border);
}

.badge-purple {
  background: var(--badge-purple-bg);
  color: var(--badge-purple-color);
  border: 1px solid var(--badge-purple-border);
}

.badge-green {
  background: var(--badge-green-bg);
  color: var(--badge-green-color);
  border: 1px solid var(--badge-green-border);
}

.badge-orange {
  background: var(--badge-orange-bg);
  color: var(--badge-orange-color);
  border: 1px solid var(--badge-orange-border);
}

.badge-red {
  background: rgba(239, 68, 68, 0.12);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.95rem;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}
</style>
