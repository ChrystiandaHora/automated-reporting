<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Configuração</h1>
        <HelpModal title="Configuração das Integrações" :items="helpItems" />
      </div>
      <button class="btn-primary" :disabled="saving" @click="salvar">
        <i class="fa-solid fa-floppy-disk" aria-hidden="true"></i>
        <span>{{ saving ? 'Salvando...' : 'Salvar' }}</span>
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
        <div class="status-item" :class="gitAccounts.length > 0 ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>GitLab {{ gitAccounts.length > 0 ? `${gitAccounts.length} conta(s)` : 'Não configurado' }}</span>
        </div>
        <div v-if="cfg.concurrency" class="status-item status-info">
          <span class="status-dot-sm"></span>
          <span>⚡ Concorrência: {{ cfg.concurrency.total_system_limit }} total ({{ cfg.concurrency.queues.analises }} análises / {{ cfg.concurrency.queues.envios }} envios)</span>
        </div>
      </div>

      <div class="config-grid">
        
        <!-- SEÇÃO: CONTAS E INSTÂNCIAS DO GITLAB (NOVO) -->
        <div class="config-section gitlab-full-section">
          <div class="section-top-bar">
            <div>
              <h3>Contas e Instâncias do GitLab</h3>
              <p class="concurrency-note" style="margin: 0;">
                Cadastre e gerencie múltiplas URLs e tokens do GitLab para importar commits de diferentes projetos sem precisar alterar o <code>.env</code>.
              </p>
            </div>
            <button type="button" class="btn-primary btn-sm" @click="abrirModalNovoGit">
              <i class="fa-solid fa-plus" aria-hidden="true"></i>
              <span>Cadastrar Nova Conta GitLab</span>
            </button>
          </div>

          <!-- Lista de Contas Cadastradas -->
          <div v-if="loadingGitAccounts" class="loading-inline">Carregando contas GitLab...</div>
          <div v-else-if="gitAccounts.length === 0" class="empty-inline">
            Nenhuma conta GitLab cadastrada. Clique no botão acima para adicionar a primeira.
          </div>
          <div v-else class="git-table-wrapper">
            <table class="git-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>URL Base</th>
                  <th>Token (PAT)</th>
                  <th>Padrão</th>
                  <th>Conexão</th>
                  <th width="120">Ações</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="conta in gitAccounts" :key="conta.id">
                  <td>
                    <div class="git-name-cell">
                      <i class="fa-brands fa-gitlab" aria-hidden="true" style="color: #fb923c; font-size: 1.1rem; flex-shrink: 0;"></i>
                      <strong>{{ conta.nome }}</strong>
                    </div>
                  </td>
                  <td><code class="url-code">{{ conta.url }}</code></td>
                  <td><span class="token-masked">{{ conta.token_mascarado }}</span></td>
                  <td>
                    <span v-if="conta.padrao" class="badge badge-green">PADRÃO</span>
                    <button v-else type="button" class="btn-link" @click="definirComoPadrao(conta)">Definir Padrão</button>
                  </td>
                  <td>
                    <div class="test-col">
                      <button 
                        type="button" 
                        class="btn-test-action"
                        :disabled="testandoGitId === conta.id"
                        @click="testarConexaoGit(conta.id)"
                        title="Validar token contra a API do GitLab"
                      >
                        <i class="fa-solid fa-plug" aria-hidden="true"></i>
                        <span>{{ testandoGitId === conta.id ? 'Testando...' : 'Testar Conexão' }}</span>
                      </button>
                      <span v-if="testeResultados[conta.id]" class="test-feedback-pill" :class="testeResultados[conta.id].ok ? 'test-ok' : 'test-err'">
                        {{ testeResultados[conta.id].ok ? `✔ ${testeResultados[conta.id].mensagem}` : `❌ ${testeResultados[conta.id].mensagem}` }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div class="action-buttons-cell">
                      <button type="button" class="btn-icon" @click="abrirModalEditarGit(conta)" title="Editar Conta" aria-label="Editar conta">
                        <i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>
                      </button>
                      <button type="button" class="btn-icon btn-icon-danger" @click="removerGitAccount(conta)" title="Excluir Conta" aria-label="Excluir conta">
                        <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

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
              <i class="fa-solid fa-database" aria-hidden="true"></i>
              <span>{{ backupLoading ? 'Gerando Backup...' : 'Criar Backup JSON + SQL Agora' }}</span>
            </button>
            <button class="btn-ghost" :disabled="pingLoading" @click="executarPingMunka">
              <i class="fa-solid fa-network-wired" aria-hidden="true"></i>
              <span>{{ pingLoading ? 'Testando...' : 'Testar Conectividade (Ping Munka)' }}</span>
            </button>
          </div>

          <div v-if="pingResult" class="ping-box" :class="pingResult.ok ? 'ping-ok' : 'ping-err'" style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem;">
            <strong>{{ pingResult.ok ? '✔ Conexão Ativa:' : '⚠️ Conexão Indisponível:' }}</strong> {{ pingResult.mensagem }}
          </div>

          <div v-if="backupsList.length > 0" class="backups-list" style="margin-top: 1.25rem;">
            <span class="config-section-label" id="backups-list-label" style="font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.5rem;">
              <i class="fa-solid fa-box-archive" aria-hidden="true" style="color: var(--accent);"></i>
              <span>Arquivos de Backup Salvos (JSON + SQL)</span>
            </span>
            <div style="max-height: 160px; overflow-y: auto; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem;" role="list" aria-labelledby="backups-list-label">
              <div v-for="b in backupsList" :key="b.nome" style="display: flex; justify-content: space-between; font-size: 0.78rem; padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border);" role="listitem">
                <span><i class="fa-solid fa-file-code" aria-hidden="true" style="color: var(--text-muted); margin-right: 5px;"></i>{{ b.nome }}</span>
                <span style="color: var(--text-muted)">{{ (b.tamanho_bytes / 1024).toFixed(1) }} KB</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <p v-if="msg" :class="ok ? 'success' : 'error'">{{ msg }}</p>
    </template>

    <!-- MODAL DE CADASTRO / EDIÇÃO DE CONTA GITLAB -->
    <div v-if="showGitModal" class="modal-overlay" @click.self="fecharModalGit">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="git-modal-title">
        <h2 id="git-modal-title">
          <i class="fa-brands fa-gitlab" aria-hidden="true" style="color: #fb923c; margin-right: 6px;"></i>
          <span>{{ gitForm.id ? 'Editar Conta GitLab' : 'Cadastrar Conta GitLab' }}</span>
        </h2>
        
        <label for="git_nome">Nome / Rótulo Amigável</label>
        <input 
          id="git_nome" 
          v-model="gitForm.nome" 
          placeholder="Ex: GitLab Saúde GO, GitLab Matriz, GitLab Pessoal" 
          required
        />

        <label for="git_url">URL Base da Instância GitLab</label>
        <input 
          id="git_url" 
          v-model="gitForm.url" 
          placeholder="Ex: https://git.saude-go.net ou https://gitlab.com" 
          required
        />

        <label for="git_token">
          Personal Access Token (PAT)
          <span v-if="gitForm.id" class="label-help">(deixe em branco ou *** para manter o token atual)</span>
        </label>
        <div class="password-input-wrap">
          <input 
            id="git_token" 
            :type="mostrarToken ? 'text' : 'password'" 
            v-model="gitForm.token" 
            placeholder="glpat-xxxxxxxxxxxxxxxxxxxx" 
            required
          />
          <button 
            type="button" 
            class="toggle-pwd-btn" 
            @click="mostrarToken = !mostrarToken"
            :aria-label="mostrarToken ? 'Ocultar token' : 'Exibir token'"
          >
            <i :class="mostrarToken ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'" aria-hidden="true"></i>
            <span>{{ mostrarToken ? 'Ocultar' : 'Ver' }}</span>
          </button>
        </div>

        <div class="checkbox-row" style="margin-top: 1rem;">
          <input id="git_padrao" type="checkbox" v-model="gitForm.padrao" />
          <label for="git_padrao" style="margin: 0; cursor: pointer;">Definir como GitLab padrão para importação</label>
        </div>

        <p v-if="gitModalErro" class="error" style="margin-top: 0.75rem;">{{ gitModalErro }}</p>

        <div class="modal-actions" style="margin-top: 1.5rem;">
          <button type="button" class="btn-ghost" @click="fecharModalGit">Cancelar</button>
          <button 
            type="button" 
            class="btn-primary" 
            :disabled="salvandoGit || !gitForm.url.trim() || (!gitForm.id && !gitForm.token.trim())" 
            @click="salvarGitAccount"
          >
            <i class="fa-solid fa-floppy-disk" aria-hidden="true"></i>
            <span>{{ salvandoGit ? 'Salvando...' : 'Salvar Conta' }}</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Config, type GitAccount } from '../api'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Contas do GitLab', text: 'Você pode cadastrar múltiplas URLs e Tokens do GitLab (PAT). Ao importar commits, o sistema pode alternar entre essas contas ou usar detecção automática de domínio sem precisar alterar o .env.' },
  { title: 'Cargo e Nível Padrão', text: 'Valores padrão sugeridos nos cadastros de atividades no Munka.' },
  { title: 'Datas e Horas Padrão', text: 'Defina os valores padrão para preenchimento de início e fim da atividade. Caso informe apenas a hora (ex: 08:00), a data do commit será utilizada.' },
  { title: 'Testar Conexão', text: 'O botão Testar Conexão faz uma requisição autenticada ao GitLab chamando /api/v4/user para checar se o token é válido.' },
]

const toastStore = useToastStore()
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

// ── Gestão de Contas GitLab ──
const gitAccounts = ref<GitAccount[]>([])
const loadingGitAccounts = ref(false)
const showGitModal = ref(false)
const mostrarToken = ref(false)
const salvandoGit = ref(false)
const gitModalErro = ref('')
const testandoGitId = ref<number | null>(null)
const testeResultados = ref<Record<number, { ok: boolean; mensagem: string }>>({})

const gitForm = ref<{
  id: number | null
  nome: string
  url: string
  token: string
  padrao: boolean
}>({
  id: null,
  nome: '',
  url: '',
  token: '',
  padrao: false,
})

async function carregarGitAccounts() {
  loadingGitAccounts.value = true
  try {
    gitAccounts.value = await api.gitAccounts.listar()
  } catch (e) {
    console.error('Erro ao carregar contas GitLab:', e)
  } finally {
    loadingGitAccounts.value = false
  }
}

function abrirModalNovoGit() {
  gitForm.value = {
    id: null,
    nome: '',
    url: '',
    token: '',
    padrao: gitAccounts.value.length === 0,
  }
  mostrarToken.value = false
  gitModalErro.value = ''
  showGitModal.value = true
}

function abrirModalEditarGit(conta: GitAccount) {
  gitForm.value = {
    id: conta.id,
    nome: conta.nome,
    url: conta.url,
    token: '***',
    padrao: conta.padrao,
  }
  mostrarToken.value = false
  gitModalErro.value = ''
  showGitModal.value = true
}

function fecharModalGit() {
  showGitModal.value = false
}

async function salvarGitAccount() {
  salvandoGit.value = true
  gitModalErro.value = ''
  try {
    if (gitForm.value.id) {
      await api.gitAccounts.atualizar(gitForm.value.id, {
        nome: gitForm.value.nome,
        url: gitForm.value.url,
        token: gitForm.value.token,
        padrao: gitForm.value.padrao,
      })
      toastStore.addToast('Conta GitLab atualizada com sucesso!', 'success')
    } else {
      await api.gitAccounts.criar({
        nome: gitForm.value.nome,
        url: gitForm.value.url,
        token: gitForm.value.token,
        padrao: gitForm.value.padrao,
      })
      toastStore.addToast('Conta GitLab cadastrada com sucesso!', 'success')
    }
    showGitModal.value = false
    await carregarGitAccounts()
  } catch (e: any) {
    gitModalErro.value = e.response?.data?.detail ?? e.message ?? String(e)
  } finally {
    salvandoGit.value = false
  }
}

async function definirComoPadrao(conta: GitAccount) {
  try {
    await api.gitAccounts.atualizar(conta.id, { padrao: true })
    toastStore.addToast(`Conta ${conta.nome} definida como padrão!`, 'success')
    await carregarGitAccounts()
  } catch (e: any) {
    toastStore.addToast(`Erro ao definir padrão: ${e.response?.data?.detail ?? String(e)}`, 'error')
  }
}

async function removerGitAccount(conta: GitAccount) {
  if (!confirm(`Tem certeza de que deseja excluir a conta GitLab "${conta.nome}"?`)) return
  try {
    await api.gitAccounts.remover(conta.id)
    toastStore.addToast('Conta GitLab excluída.', 'info')
    await carregarGitAccounts()
  } catch (e: any) {
    toastStore.addToast(`Erro ao excluir conta: ${e.response?.data?.detail ?? String(e)}`, 'error')
  }
}

async function testarConexaoGit(id: number) {
  testandoGitId.value = id
  delete testeResultados.value[id]
  try {
    const res = await api.gitAccounts.testar(id)
    testeResultados.value[id] = {
      ok: true,
      mensagem: `${res.usuario} conectado`,
    }
    toastStore.addToast(res.mensagem, 'success')
  } catch (e: any) {
    const detalhe = e.response?.data?.detail ?? e.message ?? 'Falha na conexão'
    testeResultados.value[id] = {
      ok: false,
      mensagem: detalhe,
    }
    toastStore.addToast(`Erro no GitLab: ${detalhe}`, 'error')
  } finally {
    testandoGitId.value = null
  }
}

// ── Backups & Conectividade Munka ──
const backupLoading = ref(false)
const backupsList = ref<{ nome: string; tamanho_bytes: number; criado_em: string }[]>([])
const pingLoading = ref(false)
const pingResult = ref<{ ok: boolean; mensagem: string } | null>(null)

async function carregarBackups() {
  try {
    const res = await api.backup.listar()
    backupsList.value = res.backups || res.arquivos || []
  } catch (e) {
    console.error('Erro ao carregar lista de backups:', e)
  }
}

async function executarBackupManual() {
  backupLoading.value = true
  try {
    const res = await api.backup.criar()
    const arq = res.arquivo_sql || res.files?.sql || 'backup_nexus_latest.sql'
    toastStore.addToast(`✔ Backup realizado! Arquivo: ${arq}`, 'success')
    await carregarBackups()
  } catch (e: any) {
    toastStore.addToast(`Erro ao criar backup: ${e.response?.data?.detail ?? e.message ?? String(e)}`, 'error')
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
    pingResult.value = { ok: false, mensagem: `Falha na conexão com o servidor: ${e.message}` }
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
    await carregarGitAccounts()
  } finally {
    loading.value = false
  }
})

async function salvar() {
  saving.value = true
  msg.value = ''
  try {
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

.gitlab-full-section {
  grid-column: 1 / -1;
}

.section-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(96, 165, 250, 0.2);
  padding-bottom: 0.75rem;
  margin-bottom: 0.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-top-bar h3 {
  border-bottom: none !important;
  padding-bottom: 0 !important;
  margin-bottom: 0.2rem !important;
}

.loading-inline, .empty-inline {
  font-size: 0.85rem;
  color: var(--text-muted);
  padding: 1.5rem 0;
  text-align: center;
}

.git-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.git-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
}

.git-table th, .git-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
}

.git-table th {
  background: rgba(255, 255, 255, 0.02);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.git-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.url-code {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--accent, #58a6ff);
  background: rgba(56, 189, 248, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

.token-masked {
  font-family: monospace;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.btn-link {
  background: transparent;
  border: none;
  color: var(--accent, #58a6ff);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.test-col {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-test-action {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-test-action:hover:not(:disabled) {
  border-color: var(--accent, #58a6ff);
  color: var(--accent, #58a6ff);
}

.test-feedback-pill {
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
}

.test-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.test-err {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.action-buttons-cell {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-icon {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  padding: 4px 7px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.12s;
}

.btn-icon:hover {
  border-color: var(--accent, #58a6ff);
}

.btn-icon-danger:hover {
  border-color: #f85149;
  color: #f85149;
}

.password-input-wrap {
  display: flex;
  position: relative;
  align-items: center;
}

.toggle-pwd-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-row input {
  width: auto !important;
  cursor: pointer;
}

.label-help {
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--text-muted);
}

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
