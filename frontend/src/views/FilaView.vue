<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Fila de Execução</h1>
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
            <span class="commit-hash">{{ grupo.commit_id.slice(0, 8) }}</span>
            <span class="commit-msg-title" :title="grupo.commit_mensagem">{{ grupo.commit_mensagem }}</span>
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
                {{ job.tipo === 'analise' ? 'Análise AI' : 'Envio Munka' }}
              </span>
              
              <span class="job-time">{{ formatarData(job.criado_em) }}</span>
              
              <div class="job-actions">
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

const filaStore = useFilaStore()
const logJobSelecionado = ref<any>(null)

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

.job-card {
  background: var(--card-bg);
  border: 2px solid var(--border);
  box-shadow: 4px 4px 0 rgba(238,238,238,0.1);
  padding: 1.25rem;
  transition: transform 0.1s, box-shadow 0.1s;
}
.job-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 6px 6px 0 rgba(238,238,238,0.15);
}

.job-card-running {
  border-color: var(--accent);
  box-shadow: 4px 4px 0 var(--accent);
}
.job-card-done {
  border-color: #3fb950;
  box-shadow: 4px 4px 0 rgba(63,185,80,0.15);
}
.job-card-error {
  border-color: #f85149;
  box-shadow: 4px 4px 0 rgba(248,81,73,0.15);
}

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
  background: rgba(238,238,238,0.06);
  border: 1px solid rgba(238,238,238,0.12);
  padding: 1px 4px;
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
  background: rgba(248,81,73,0.08);
  border-left: 3px solid #f85149;
  padding: 0.5rem 0.75rem;
  font-size: 0.78rem;
  color: #f85149;
  margin-top: 0.6rem;
  font-weight: 500;
}

.job-footer {
  display: flex;
  align-items: center;
  border-top: 1px solid rgba(238,238,238,0.08);
  padding-top: 0.6rem;
}
.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.status-pending { background: #888; }
.status-running { 
  background: var(--accent); 
  box-shadow: 0 0 8px var(--accent);
  animation: pulse 1.5s infinite;
}
.status-done { background: #3fb950; }
.status-error { background: #f85149; }

.status-text {
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.5; }
}

/* Modal de logs */
.modal-wide { width: 100%; max-width: 650px; }
.modal-subtitle {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: -0.5rem;
  margin-bottom: 0.5rem;
}
.terminal-container {
  background: #0a0a0a;
  border: 2px solid rgba(238,238,238,0.15);
  margin-top: 0.5rem;
}
.terminal-header {
  background: rgba(238,238,238,0.03);
  padding: 0.5rem 0.85rem;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(238,238,238,0.08);
}
.status-badge {
  text-transform: uppercase;
  font-size: 0.65rem;
  padding: 1px 4px;
}
.badge-done { color: #3fb950; }
.badge-error { color: #f85149; }

.terminal-body {
  padding: 0.85rem;
  font-size: 0.78rem;
  font-family: 'Courier New', Courier, monospace;
  max-height: 250px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  background: #000;
  color: #ccc;
}
.terminal-body div.error-line {
  color: #f85149;
}

.btn-xs {
  padding: 0.15rem 0.4rem;
  font-size: 0.72rem;
  box-shadow: 2px 2px 0 var(--accent);
}
.btn-xs:hover {
  box-shadow: 3px 3px 0 var(--accent);
}

.btn-danger-link {
  background: transparent;
  border: none;
  color: #f85149;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.btn-danger-link:hover {
  text-decoration: underline;
}

.warning-box {
  background: rgba(243,156,18,0.08);
  border-left: 3px solid #f39c12;
  padding: 0.5rem 0.75rem;
  font-size: 0.78rem;
  color: #f39c12;
  margin-top: 0.6rem;
  font-weight: 500;
}

.mudar-modelo-box {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(238,238,238,0.02);
  border: 1px dashed rgba(238,238,238,0.15);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.mudar-modelo-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
}
.mudar-modelo-control {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.select-modelo {
  background: var(--bg);
  color: var(--text);
  border: 2px solid var(--border);
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  font-weight: 600;
  outline: none;
}
.select-modelo:focus {
  border-color: var(--accent);
}
.btn-primary-mudar {
  background: var(--accent);
  color: var(--bg);
  border: 2px solid var(--border);
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  box-shadow: 2px 2px 0 var(--border);
  text-transform: uppercase;
}
.btn-primary-mudar:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 var(--border);
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
  border: 2px solid var(--border);
  background: var(--card-bg);
}
.commit-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1rem;
  background: rgba(238, 238, 238, 0.02);
  border-bottom: 2px solid var(--border);
}
.commit-group-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}
.collapse-icon {
  font-size: 0.65rem;
  color: var(--text-muted);
  width: 12px;
  display: inline-block;
}
.commit-msg-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.job-count-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  background: rgba(238, 238, 238, 0.05);
  padding: 2px 6px;
  border: 1px solid rgba(238, 238, 238, 0.1);
  margin-left: 1rem;
  flex-shrink: 0;
}
.commit-group-jobs {
  display: flex;
  flex-direction: column;
}
.job-row {
  padding: 1.25rem;
  border-bottom: 1px solid rgba(238, 238, 238, 0.08);
  transition: background-color 0.15s;
}
.job-row:last-child {
  border-bottom: none;
}
.job-row:hover {
  background-color: rgba(238, 238, 238, 0.01);
}
.job-row-running {
  border-left: 4px solid var(--accent);
  background-color: rgba(0, 122, 204, 0.02);
}
.job-row-done {
  border-left: 4px solid #3fb950;
  background-color: rgba(63, 185, 80, 0.02);
}
.job-row-error {
  border-left: 4px solid #f85149;
  background-color: rgba(248, 81, 73, 0.02);
}
</style>
