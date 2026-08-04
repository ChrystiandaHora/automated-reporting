<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Configuração</h1>
        <HelpModal title="Configuração das Integrações" :items="helpItems" />
      </div>
      <button class="btn-primary" :disabled="saving" @click="salvar">
        {{ saving ? 'Salvando...' : 'Salvar' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <template v-else>
      <div class="status-bar">
        <div class="status-item" :class="cfg.status.gemini ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>Gemini {{ cfg.status.gemini ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div class="status-item" :class="cfg.status.munka ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>Munka {{ cfg.status.munka ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div class="status-item" :class="cfg.status.gitlab ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>GitLab {{ cfg.status.gitlab ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div v-if="cfg.concurrency" class="status-item status-info">
          <span class="status-dot-sm"></span>
          <span>⚡ Concorrência: {{ cfg.concurrency.total_system_limit }} total ({{ cfg.concurrency.queues.analises }} análises / {{ cfg.concurrency.queues.envios }} envios)</span>
        </div>
      </div>

      <div class="config-grid">
        <div class="config-section">
          <h3>Munka - Faturamento Padrão</h3>
          <label for="munka_cargo">Cargo Padrão</label>
          <select id="munka_cargo" v-model="form.munka_cargo">
            <option value="9">Desenvolvedor</option>
            <option value="11">Analista de Sistemas</option>
            <option value="12">Arquiteto de Software</option>
            <option value="16">Analista de Testes</option>
          </select>
          <label for="munka_nivel">Nível Padrão</label>
          <select id="munka_nivel" v-model="form.munka_nivel">
            <option value="1">Júnior</option>
            <option value="2">Pleno</option>
            <option value="3">Sênior</option>
            <option value="4">Único</option>
          </select>
          <label for="munka_responsavel">Responsável Padrão (busca)</label>
          <input id="munka_responsavel" v-model="form.munka_responsavel" placeholder="Ex: João Silva" />
          <label for="munka_produto">Produto Padrão</label>
          <input id="munka_produto" v-model="form.munka_produto" placeholder="Ex: [DESENV] MUNKA" />
          <label for="munka_projeto">Projeto Padrão</label>
          <input id="munka_projeto" v-model="form.munka_projeto" placeholder="Ex: [DESENV] MUNKA" />
          <label for="munka_status_id">Status Inicial Padrão</label>
          <select id="munka_status_id" v-model="form.munka_status_id">
            <option value="15">Backlog</option>
            <option value="16">Backlog Prioritário</option>
            <option value="17">Pendente</option>
            <option value="20">Homologação</option>
            <option value="21">Concluído</option>
            <option value="18">Desenvolvimento</option>
          </select>
          <label for="munka_data_inicio">Data/Hora de Início Padrão (Ex: 08:00 ou DD/MM/YYYY 08:00)</label>
          <input id="munka_data_inicio" v-model="form.munka_data_inicio" placeholder="Ex: 08:00" />
          <label for="munka_data_fim">Data/Hora de Fim Padrão (Ex: 18:00 ou DD/MM/YYYY 18:00)</label>
          <input id="munka_data_fim" v-model="form.munka_data_fim" placeholder="Ex: 18:00" />
        </div>

        <div class="config-section" v-if="cfg.concurrency">
          <h3>Processamento Assíncrono</h3>
          <div class="concurrency-info">
            <div class="info-row">
              <span class="info-label">CPU Cores Detectados:</span>
              <span class="info-value">{{ cfg.concurrency.cpu_cores }} Cores</span>
            </div>
            <div class="info-row">
              <span class="info-label">Capacidade Total do Sistema:</span>
              <span class="info-value highlight">{{ cfg.concurrency.total_system_limit }} processos simultâneos</span>
            </div>
            <div class="info-row">
              <span class="info-label">Pool Dinâmico de Workers:</span>
              <span class="info-value shared-badge">⚡ Ativo (Prioridade + Fallback)</span>
            </div>
            <div class="info-row sub">
              <span class="info-label">• Fila de Análise de Commits:</span>
              <span class="info-value">{{ cfg.concurrency.queues.analises }} workers <span class="queue-detail">(Prioridade: Análises | Auxílio: Lançamentos)</span></span>
            </div>
            <div class="info-row sub">
              <span class="info-label">• Fila de Lançamento no Munka:</span>
              <span class="info-value">{{ cfg.concurrency.queues.envios }} workers <span class="queue-detail">(Prioridade: Lançamentos | Auxílio: Análises)</span></span>
            </div>
          </div>
          <p class="concurrency-note">
            ⚡ <strong>Rebalanceamento Automático:</strong> Os workers são alocados com prioridade para sua fila principal. Quando uma das filas fica ociosa e a outra acumula tarefas, todos os workers ociosos passam a auxiliar automaticamente a fila ativa.
          </p>
        </div>

        <div class="config-section">
          <h3>Segurança & Backup Automático</h3>
          <p class="concurrency-note">
            💾 <strong>Auto-Save em JSON + SQL:</strong> O sistema realiza cópias de segurança automáticas de todas as tarefas, evidencias, commits e histórico no volume de dados persistente.
          </p>
          <div style="display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap;">
            <button class="btn-primary" :disabled="backupLoading" @click="executarBackupManual">
              {{ backupLoading ? 'Gerando Backup...' : '⚡ Criar Backup JSON + SQL Agora' }}
            </button>
            <button class="btn-ghost" :disabled="pingLoading" @click="executarPingMunka">
              {{ pingLoading ? 'Testando...' : '🔍 Testar Conectividade (Ping Munka)' }}
            </button>
          </div>

          <div v-if="pingResult" class="ping-box" :class="pingResult.ok ? 'ping-ok' : 'ping-err'" style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem;">
            <strong>{{ pingResult.ok ? '✔ Conexão Ativa:' : '⚠️ Conexão Indisponível:' }}</strong> {{ pingResult.mensagem }}
          </div>

          <div v-if="backupsList.length > 0" class="backups-list" style="margin-top: 1.25rem;">
            <span class="config-section-label" id="backups-list-label" style="font-weight: 600; font-size: 0.9rem; display: block; margin-bottom: 0.5rem;">Arquivos de Backup Salvos (JSON + SQL)</span>
            <div style="max-height: 160px; overflow-y: auto; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem;" role="list" aria-labelledby="backups-list-label">
              <div v-for="b in backupsList" :key="b.nome" style="display: flex; justify-content: space-between; font-size: 0.78rem; padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border);" role="listitem">
                <span>📄 {{ b.nome }}</span>
                <span style="color: var(--text-muted)">{{ (b.tamanho_bytes / 1024).toFixed(1) }} KB</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <p v-if="msg" :class="ok ? 'success' : 'error'">{{ msg }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Config } from '../api'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Cargo Padrão', text: 'Cargo utilizado no faturamento das atividades no portal Munka.' },
  { title: 'Nível Padrão', text: 'Nível de faturamento das atividades (ex: Júnior, Pleno, Sênior).' },
  { title: 'Datas e Horas Padrão', text: 'Defina os valores padrão para preenchimento de início e fim da atividade. Caso informe apenas a hora (ex: 08:00), a data do commit será utilizada.' },
  { title: 'Demais Configurações', text: 'As credenciais de acesso ao Munka, tokens do GitLab e chave da API do Gemini devem ser configurados diretamente no arquivo .env do servidor.' },
  { title: 'Indicadores de status', text: 'Os badges indicam se as variáveis de ambiente necessárias foram detectadas no servidor.' },
]

const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const ok = ref(false)

const cfg = ref<Config>({
  gemini_api_key: '', munka_user: '', munka_pass: '',
  gitlab_token: '', gitlab_url: '',
  munka_cargo: '9', munka_nivel: '3', munka_responsavel: '',
  munka_produto: '[DESENV] MUNKA', munka_projeto: 'MUNKA Multicontrato', munka_status_id: '17',
  munka_data_inicio: '08:00', munka_data_fim: '18:00',
  status: { gemini: false, munka: false, gitlab: false },
})

const form = ref({
  gemini_api_key: '', munka_user: '', munka_pass: '',
  gitlab_token: '', gitlab_url: '',
  munka_cargo: '9', munka_nivel: '3', munka_responsavel: '',
  munka_produto: '[DESENV] MUNKA', munka_projeto: 'MUNKA Multicontrato', munka_status_id: '17',
  munka_data_inicio: '08:00', munka_data_fim: '18:00',
})

const backupLoading = ref(false)
const pingLoading = ref(false)
const pingResult = ref<{ ok: boolean; mensagem: string } | null>(null)
const backupsList = ref<any[]>([])

async function carregarBackups() {
  try {
    const res = await api.backup.listar()
    if (res && res.backups) {
      backupsList.value = res.backups
    }
  } catch (e) {
    console.error("Erro ao carregar lista de backups:", e)
  }
}

async function executarBackupManual() {
  backupLoading.value = true
  try {
    const res = await api.backup.criar()
    ok.value = true
    msg.value = `✔ Backup manual gerado com sucesso! (${res.counts?.commits || 0} commits, ${res.counts?.fila || 0} tarefas)`
    await carregarBackups()
  } catch (e: any) {
    ok.value = false
    msg.value = `Erro ao gerar backup: ${e.response?.data?.detail ?? String(e)}`
  } finally {
    backupLoading.value = false
  }
}

async function executarPingMunka() {
  pingLoading.value = true
  pingResult.value = null
  try {
    const res = await api.pingMunka()
    pingResult.value = res
  } catch (e: any) {
    pingResult.value = { ok: false, mensagem: `Falha na conexao com o servidor: ${e.message}` }
  } finally {
    pingLoading.value = false
  }
}

onMounted(async () => {
  try {
    cfg.value = await api.config.obter()
    form.value.munka_user = cfg.value.munka_user
    form.value.gitlab_url = cfg.value.gitlab_url
    form.value.munka_cargo = cfg.value.munka_cargo || '9'
    form.value.munka_nivel = cfg.value.munka_nivel || '3'
    form.value.munka_responsavel = cfg.value.munka_responsavel || ''
    form.value.munka_produto = cfg.value.munka_produto || '[DESENV] MUNKA'
    form.value.munka_projeto = cfg.value.munka_projeto || 'MUNKA Multicontrato'
    form.value.munka_status_id = cfg.value.munka_status_id || '17'
    form.value.munka_data_inicio = cfg.value.munka_data_inicio || '08:00'
    form.value.munka_data_fim = cfg.value.munka_data_fim || '18:00'
    await carregarBackups()
  } finally {
    loading.value = false
  }
})

async function salvar() {
  saving.value = true
  msg.value = ''
  try {
    // Filtra apenas campos sensíveis vazios ou não modificados
    const payload: any = {}
    for (const [k, v] of Object.entries(form.value)) {
      if (k.includes('key') || k.includes('pass') || k.includes('token')) {
        if (v && v !== '***') payload[k] = v
      } else {
        if (v !== undefined && v !== null) payload[k] = v
      }
    }
    await api.config.salvar(payload)
    cfg.value = await api.config.obter()
    ok.value = true
    msg.value = 'Configurações salvas!'
  } catch (e: any) {
    ok.value = false
    msg.value = e.response?.data?.detail ?? String(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }

.status-bar { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1.75rem; flex-wrap: wrap; }
.status-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 99px;
  border: 1px solid;
}
.status-dot-sm {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.status-ok  {
  border-color: rgba(74, 222, 128, 0.4);
  color: #4ade80;
  background: rgba(34, 197, 94, 0.08);
}
.status-err {
  border-color: rgba(248, 113, 113, 0.4);
  color: #f87171;
  background: rgba(239, 68, 68, 0.08);
}
.status-info {
  border-color: rgba(96, 165, 250, 0.4);
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.08);
}

.config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }

.config-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.config-section h3 {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--accent-light);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid rgba(96, 165, 250, 0.2);
  padding-bottom: 0.625rem;
}

.concurrency-info {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.info-row.sub {
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
  padding-left: 0.5rem;
}

.info-label {
  font-weight: 500;
}

.info-value {
  font-weight: 700;
}

.info-value.highlight {
  color: #60a5fa;
  font-size: 0.95rem;
}

.shared-badge {
  color: #34d399;
  font-size: 0.82rem;
  background: rgba(52, 211, 153, 0.12);
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid rgba(52, 211, 153, 0.25);
}

.queue-detail {
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  margin-left: 0.35rem;
}

.concurrency-note {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  margin-top: 0.5rem;
  line-height: 1.4;
}

.concurrency-note code {
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 5px;
  border-radius: 4px;
  font-family: monospace;
}

.success { color: #4ade80; margin-top: 1rem; font-weight: 600; }
</style>
