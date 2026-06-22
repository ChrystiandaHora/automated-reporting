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

    <div v-else class="jobs-list">
      <div 
        v-for="job in filaStore.jobs" 
        :key="job.id" 
        class="job-card"
        :class="`job-card-${job.status}`"
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
          <div class="commit-info">
            <span class="commit-hash">{{ job.commit_id.slice(0, 8) }}</span>
            <span class="commit-msg">{{ job.commit_mensagem }}</span>
          </div>

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
        </div>

        <div class="job-footer">
          <div class="status-indicator">
            <span class="status-dot" :class="`status-${job.status}`"></span>
            <span class="status-text">{{ formatarStatus(job.status) }}</span>
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
import { ref, onMounted } from 'vue'
import { useFilaStore } from '../stores/fila'

const filaStore = useFilaStore()
const logJobSelecionado = ref<any>(null)

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
</style>
