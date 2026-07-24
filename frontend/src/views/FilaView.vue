<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Fila de Execução</h1>
        <span v-if="concurrencyInfo" class="concurrency-badge" :title="`Fila de análises: ${concurrencyInfo.queues.analises} workers | Fila de envios: ${concurrencyInfo.queues.envios} workers`">
          ⚡ Concorrência: {{ concurrencyInfo.queues.analises }} análises / {{ concurrencyInfo.queues.envios }} envios ({{ concurrencyInfo.cpu_cores }} Cores CPU)
        </span>
      </div>
      <button class="btn-ghost btn-sm" @click="atualizarFila">↻ Atualizar</button>
    </div>

    <div v-if="filaStore.loading && filaStore.jobs.length === 0" class="loading">Carregando fila...</div>
    
    <div v-else-if="filaStore.jobs.length === 0" class="empty">
      Nenhuma tarefa na fila de execução.
    </div>

    <div v-else class="fila-grouped">
      <!-- Percorre os commits agrupados -->
      <div v-for="grupo in jobsAgrupados" :key="grupo.commit_id" class="commit-group">
        <!-- Cabeçalho do Commit -->
        <div class="commit-group-header" @click="alternarGrupo(grupo.commit_id)" style="cursor: pointer; user-select: none;">
          <div class="commit-group-info">
            <span class="collapse-icon">{{ isGrupoColapsado(grupo.commit_id) ? '▶' : '▼' }}</span>
            <router-link :to="`/commits/${grupo.commit_id}`" class="commit-hash-link" @click.stop>
              {{ grupo.commit_id.slice(0, 8) }}
            </router-link>
            <router-link :to="`/commits/${grupo.commit_id}`" class="commit-msg-link" :title="grupo.commit_mensagem" @click.stop>
              {{ grupo.commit_mensagem }}
            </router-link>
          </div>
          <span class="job-count-badge">{{ grupo.jobs.length }} tarefa{{ grupo.jobs.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Lista de tarefas deste commit -->
        <div v-show="!isGrupoColapsado(grupo.commit_id)" class="commit-group-jobs">
          <div 
            v-for="job in grupo.jobs" 
            :key="job.id" 
            class="job-row"
            :class="`job-row-${job.status}`"
          >
            <div class="job-header">
              <span 
                class="badge" 
                :class="job.tipo === 'analise' ? 'badge-blue' : 'badge-purple'"
              >
                {{ job.tipo === 'analise' ? 'Análise AI' : 'Envio Portal' }}
              </span>
              
              <span class="job-time">{{ formatarData(job.criado_em) }}</span>
              
              <div class="job-actions">
                <!-- Botão de Ver Tarefa (para envio concluído com sucesso) -->
                <a 
                  v-if="job.status === 'done' && job.resultado && job.resultado.task_url" 
                  :href="job.resultado.task_url" 
                  target="_blank" 
                  class="btn-ghost btn-xs" 
                  style="text-decoration: none; margin-right: 0.5rem; display: inline-block;"
                >
                  Ver Tarefa
                </a>
                
                <!-- Botão de Ver Logs (para envio concluído ou com erro) -->
                <button 
                  v-if="job.resultado && job.resultado.logs && job.resultado.logs.length" 
                  class="btn-ghost btn-xs" 
                  @click="abrirLogs(job)"
                >
                  Ver Logs
                </button>
                
                <!-- Botão Cancelar (para pending) -->
                <button 
                  v-if="job.status === 'pending'" 
                  class="btn-danger-link" 
                  @click="cancelarJob(job.id)"
                >
                  Cancelar
                </button>

                <!-- Botão de Deletar (para done ou error) -->
                <button 
                  v-if="['done', 'error'].includes(job.status)" 
                  class="btn-danger-link" 
                  @click="removerJob(job.id)"
                >
                  Limpar
                </button>
              </div>
            </div>

            <div class="job-body">
              <div v-if="job.tipo === 'analise'" class="job-meta">
                <strong>Modelo:</strong> {{ job.modelo }}
              </div>
              
              <div v-else-if="job.tipo === 'envio'" class="job-meta">
                <strong>Atividade:</strong> "{{ job.titulo_atividade || 'Carregando título...' }}"
              </div>

              <!-- Mensagem de Erro -->
              <div v-if="job.status === 'error'" class="error-box">
                <span>{{ obterMensagemErro(job) }}</span>
              </div>

              <!-- Mensagem de Retry / Aguardando -->
              <div v-if="job.status === 'running' && job.resultado && job.resultado.status === 'retrying'" class="warning-box">
                <span>{{ job.resultado.mensagem || 'Aguardando tempo limite para tentar novamente...' }}</span>
              </div>

              <!-- Seleção de outro modelo em caso de limite atingido -->
              <div v-if="podeMudarModelo(job)" class="mudar-modelo-box">
                <span class="mudar-modelo-label">Limite atingido. Tentar outro modelo:</span>
                <div class="mudar-modelo-control">
                  <select 
                    :value="obterModeloSelecionado(job.id, job.modelo)" 
                    @change="atualizarModeloSelecionado(job.id, $event)"
                    class="select-modelo"
                  >
                    <option v-for="m in models" :key="m.name" :value="m.name">
                      {{ m.name }}
                    </option>
                  </select>
                  <button class="btn-primary-mudar" @click="reprocessarComOutroModelo(job)">
                    Reprocessar
                  </button>
                </div>
              </div>

              <!-- Opção de Reenviar em caso de falha de envio -->
              <div v-if="job.tipo === 'envio' && job.status === 'error'" class="mudar-modelo-box">
                <span class="mudar-modelo-label">Esta atividade falhou no envio. Deseja tentar novamente?</span>
                <div class="mudar-modelo-control">
                  <button class="btn-primary-mudar" @click="reenviarAtividade(job)">
                    Reenviar Envio
                  </button>
                </div>
              </div>
            </div>

            <div class="job-footer">
              <div class="status-indicator">
                <span class="status-dot" :class="`status-${job.status}`"></span>
                <span class="status-text">{{ formatarStatus(job.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Logs -->
    <div v-if="logJobSelecionado" class="modal-overlay" @click.self="fecharLogs">
      <div class="modal modal-wide">
        <h2>Logs de Automação (Job #{{ logJobSelecionado.id }})</h2>
        <p class="modal-subtitle">Tarefa: "{{ logJobSelecionado.titulo_atividade }}"</p>
        
        <div class="terminal-container">
          <div class="terminal-header">
            <span>Logs do Playwright</span>
            <span class="status-badge" :class="`badge-${logJobSelecionado.status}`">{{ logJobSelecionado.status }}</span>
          </div>
          <pre class="terminal-body"><div v-for="(log, idx) in logJobSelecionado.resultado.logs" :key="idx" :class="{'error-line': log.startsWith('❌') || log.startsWith('ERRO')}">{{ log }}</div></pre>
        </div>

        <div class="modal-actions">
          <button class="btn-ghost" @click="fecharLogs">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useFilaStore } from '../stores/fila'
import { api, type Config } from '../api'

const filaStore = useFilaStore()
const logJobSelecionado = ref<any>(null)
const concurrencyInfo = ref<Config['concurrency'] | null>(null)

const gruposColapsados = ref<Record<string, boolean>>({})

function alternarGrupo(commitId: string) {
  gruposColapsados.value[commitId] = !gruposColapsados.value[commitId]
}

function isGrupoColapsado(commitId: string) {
  return !!gruposColapsados.value[commitId]
}

const jobsAgrupados = computed(() => {
  const grupos: Record<string, { commit_id: string; commit_mensagem: string; jobs: any[] }> = {}
  
  for (const job of filaStore.jobs) {
    const key = job.commit_id
    if (!grupos[key]) {
      grupos[key] = {
        commit_id: job.commit_id,
        commit_mensagem: job.commit_mensagem || '(sem mensagem)',
        jobs: []
      }
    }
    grupos[key].jobs.push(job)
  }
  
  // Ordena os grupos pela data de criação do job mais recente
  return Object.values(grupos).sort((a, b) => {
    const maxA = Math.max(...a.jobs.map(j => new Date(j.criado_em).getTime()))
    const maxB = Math.max(...b.jobs.map(j => new Date(j.criado_em).getTime()))
    return maxB - maxA
  })
})

onMounted(async () => {
  await filaStore.fetchJobs()
  try {
    const cfg = await api.config.obter()
    if (cfg.concurrency) {
      concurrencyInfo.value = cfg.concurrency
    }
  } catch (e) {
    console.error("Erro ao carregar configuracoes de concorrencia:", e)
  }
})

function atualizarFila() {
  filaStore.fetchJobs()
}

function formatarData(isoString: string) {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    return d.toLocaleString('pt-BR')
  } catch {
    return isoString
  }
}

function formatarStatus(status: string) {
  const map: Record<string, string> = {
    pending: 'Aguardando na fila',
    running: 'Executando tarefa',
    done: 'Concluído',
    error: 'Falhou'
  }
  return map[status] ?? status
}

function obterMensagemErro(job: any) {
  if (!job.resultado) return 'Erro desconhecido.'
  if (job.resultado.error) return job.resultado.error
  if (job.resultado.logs && job.resultado.logs.length) {
    // Retorna a última linha de erro dos logs
    const erroLog = [...job.resultado.logs].reverse().find((l: string) => l.startsWith('❌') || l.includes('ERRO'))
    if (erroLog) return erroLog
  }
  return 'Erro técnico na execução do job.'
}

async function cancelarJob(id: number) {
  if (confirm('Deseja realmente cancelar esta tarefa na fila?')) {
    await filaStore.removerJob(id)
  }
}

async function removerJob(id: number) {
  await filaStore.removerJob(id)
}

function abrirLogs(job: any) {
  logJobSelecionado.value = job
}

function fecharLogs() {
  logJobSelecionado.value = null
}

const models = [
  { name: 'Gemini 2.5 Flash' },
  { name: 'Gemini 3.5 Flash' },
  { name: 'Gemini 2.5 Flash Lite' },
  { name: 'Gemini 3 Flash' },
  { name: 'Gemini 3.1 Flash Lite' }
]

const modelosSelecionados = ref<Record<number, string>>({})

function obterModeloSelecionado(jobId: number, modeloAtual?: string) {
  if (modelosSelecionados.value[jobId] === undefined) {
    modelosSelecionados.value[jobId] = modeloAtual || 'Gemini 2.5 Flash'
  }
  return modelosSelecionados.value[jobId]
}

function atualizarModeloSelecionado(jobId: number, event: Event) {
  const target = event.target as HTMLSelectElement
  modelosSelecionados.value[jobId] = target.value
}

function podeMudarModelo(job: any) {
  if (job.tipo !== 'analise') return false
  if (job.status === 'error') {
    const msg = obterMensagemErro(job).toLowerCase()
    return msg.includes('429') || msg.includes('quota') || msg.includes('limit') || msg.includes('exhausted') || msg.includes('resource') || msg.includes('503')
  }
  if (job.status === 'running' && job.resultado && job.resultado.status === 'retrying') {
    return true
  }
  return false
}

async function reprocessarComOutroModelo(job: any) {
  const modeloSelecionado = modelosSelecionados.value[job.id] || job.modelo || 'Gemini 2.5 Flash'
  if (confirm(`Deseja cancelar a tarefa atual e iniciar uma nova análise com o modelo ${modeloSelecionado}?`)) {
    try {
      await filaStore.removerJob(job.id)
      await filaStore.enfileirarAnalise([job.commit_id], modeloSelecionado)
    } catch {
      // Erro já tratado pelo toast
    }
  }
}

async function reenviarAtividade(job: any) {
  if (confirm('Deseja realmente remover esta tentativa com erro e enfileirar o envio novamente?')) {
    try {
      await filaStore.removerJob(job.id)
      await filaStore.enfileirarEnvio(job.commit_id, job.atividade_idx)
    } catch {
      // Erro tratado pelo toast
    }
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.jobs-list { display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem; }

.job-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.job-time {
  font-size: 0.72rem;
  color: var(--text-muted);
}
.job-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.job-body {
  margin-bottom: 0.85rem;
}
.commit-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}
.commit-hash {
  font-family: monospace;
  font-size: 0.78rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 2px 6px;
  border-radius: 4px;
}
.commit-msg {
  font-weight: 700;
  font-size: 0.9rem;
}
.job-meta {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.error-box {
  background: rgba(239, 68, 68, 0.08);
  border-left: 3px solid var(--error);
  padding: 0.6rem 0.85rem;
  font-size: 0.78rem;
  color: var(--error);
  margin-top: 0.6rem;
  font-weight: 500;
  border-radius: 0 6px 6px 0;
}

.job-footer {
  display: flex;
  align-items: center;
  border-top: 1px solid rgba(255,255,255,0.04);
  padding-top: 0.75rem;
}
.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-pending { background: #6b7280; }
.status-running { 
  background: var(--accent-light); 
  box-shadow: 0 0 10px var(--accent-light);
  animation: pulse 1.5s infinite;
}
.status-done { background: var(--success); box-shadow: 0 0 8px rgba(16, 185, 129, 0.3); }
.status-error { background: var(--error); box-shadow: 0 0 8px rgba(239, 68, 68, 0.3); }

.status-text {
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.7rem;
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.5; }
}

/* Modal de logs */
.modal-wide { width: 100%; max-width: 700px; }
.modal-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: -0.5rem;
  margin-bottom: 0.75rem;
}
.terminal-container {
  background: #060813;
  border: 1px solid var(--card-border);
  border-radius: 10px;
  margin-top: 0.75rem;
  overflow: hidden;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
}
.terminal-header {
  background: rgba(255, 255, 255, 0.02);
  padding: 0.6rem 1rem;
  font-size: 0.72rem;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.status-badge {
  text-transform: uppercase;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}
.badge-done { background: rgba(16, 185, 129, 0.1); color: var(--success); }
.badge-error { background: rgba(239, 68, 68, 0.1); color: var(--error); }

.terminal-body {
  padding: 1rem;
  font-size: 0.78rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  max-height: 350px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  background: #03050a;
  color: #d1d5db;
}
.terminal-body div.error-line {
  color: #f87171;
}

.btn-xs {
  padding: 0.25rem 0.6rem;
  font-size: 0.72rem;
  border-radius: 6px;
  box-shadow: none;
}

.btn-danger-link {
  background: transparent;
  border: none;
  color: var(--error);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  transition: all 0.2s ease;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
}
.btn-danger-link:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #f87171;
}

.warning-box {
  background: rgba(245, 158, 11, 0.08);
  border-left: 3px solid var(--warning);
  padding: 0.6rem 0.85rem;
  font-size: 0.78rem;
  color: var(--warning);
  margin-top: 0.6rem;
  font-weight: 500;
  border-radius: 0 6px 6px 0;
}

.mudar-modelo-box {
  margin-top: 0.75rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.mudar-modelo-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}
.mudar-modelo-control {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.select-modelo {
  background: #0b0f19 !important;
  color: var(--text) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 6px !important;
  font-size: 0.75rem !important;
  padding: 0.25rem 0.5rem !important;
  font-weight: 600 !important;
  width: auto !important;
}
.btn-primary-mudar {
  background: var(--accent-grad) !important;
  color: #fff !important;
  border: none !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  padding: 0.35rem 0.75rem !important;
  cursor: pointer !important;
  border-radius: 6px !important;
  text-transform: uppercase;
  transition: all 0.2s ease !important;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15) !important;
}
.btn-primary-mudar:hover {
  filter: brightness(1.1) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3) !important;
}

/* Agrupamento da fila por Commit */
.fila-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1rem;
}
.commit-group {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.commit-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.25rem !important;
  background: rgba(255, 255, 255, 0.01) !important;
  border-bottom: 1px solid var(--card-border) !important;
}
.commit-group-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}
.collapse-icon {
  font-size: 0.65rem !important;
  color: var(--text-muted) !important;
  padding: 2px 6px !important;
  display: inline-block;
  cursor: pointer;
}
.commit-hash-link {
  color: var(--accent-light) !important;
  text-decoration: none;
  font-family: monospace;
}
.commit-msg-link {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-decoration: none;
  min-width: 0;
  flex: 1;
  transition: color 0.2s ease;
}
.commit-msg-link:hover {
  color: var(--accent-light);
}
.job-count-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.03);
  padding: 2px 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  margin-left: 1rem;
  flex-shrink: 0;
}
.commit-group-jobs {
  display: flex;
  flex-direction: column;
  padding-top: 0 !important;
}
.job-row {
  padding: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
  transition: all 0.2s ease;
}
.job-row:last-child {
  border-bottom: none !important;
}
.job-row:hover {
  background-color: rgba(255, 255, 255, 0.015) !important;
}

.concurrency-badge {
  font-size: 0.78rem;
  font-weight: 600;
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.08);
  border: 1px solid rgba(96, 165, 250, 0.3);
  padding: 4px 10px;
  border-radius: 99px;
  margin-left: 0.75rem;
}
</style>
