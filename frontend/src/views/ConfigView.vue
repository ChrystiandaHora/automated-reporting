<template>
  <div>
    <PageHeader data-tour="config-cabecalho">
      <div class="flex items-center gap-2">
        <PageTitle>Configuração</PageTitle>
        <TutorialModal screenId="config" />
      </div>
      <BaseButton variant="primary" data-tour="config-salvar" :disabled="saving" @click="salvar">
        <i class="fa-solid fa-floppy-disk" aria-hidden="true"></i>
        <span>{{ saving ? 'Salvando...' : 'Salvar' }}</span>
      </BaseButton>
    </PageHeader>

    <StateMessage v-if="loading" type="loading">Carregando...</StateMessage>

    <template v-else>
      <div class="mb-7 flex flex-wrap items-center gap-3" data-tour="config-status">
        <div :class="[statusItemBase, cfg.status.gemini ? statusOk : statusErr]">
          <span class="size-[7px] shrink-0 rounded-full bg-current"></span>
          <span>Gemini {{ cfg.status.gemini ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div :class="[statusItemBase, cfg.status.munka ? statusOk : statusErr]">
          <span class="size-[7px] shrink-0 rounded-full bg-current"></span>
          <span>Munka {{ cfg.status.munka ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div :class="[statusItemBase, gitAccounts.length > 0 ? statusOk : statusErr]">
          <span class="size-[7px] shrink-0 rounded-full bg-current"></span>
          <span>GitLab {{ gitAccounts.length > 0 ? `${gitAccounts.length} conta(s)` : 'Não configurado' }}</span>
        </div>
        <div v-if="cfg.concurrency" :class="[statusItemBase, 'border-blue-400/40 bg-blue-400/8 text-blue-400']">
          <span class="size-[7px] shrink-0 rounded-full bg-current"></span>
          <span><i class="fa-solid fa-bolt mr-1" aria-hidden="true"></i>Concorrência: {{ cfg.concurrency.total_system_limit }} total ({{ cfg.concurrency.queues.analises }} análises / {{ cfg.concurrency.queues.envios }} envios)</span>
        </div>
      </div>

      <div class="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-6">
        
        <!-- SEÇÃO: CONTAS E INSTÂNCIAS DO GITLAB (NOVO) -->
        <div :class="[secao, 'col-span-full']" data-tour="config-gitlab">
          <div class="mb-2 flex flex-wrap items-center justify-between gap-4 border-b border-blue-400/20 pb-3">
            <div>
              <h3 :class="tituloSecaoTopo">Contas e Instâncias do GitLab</h3>
              <p :class="notaCls">
                Cadastre e gerencie múltiplas URLs e tokens do GitLab para importar commits de diferentes projetos sem precisar alterar o <code class="rounded bg-white/8 px-1.25 py-0.5 font-mono">.env</code>.
              </p>
            </div>
            <BaseButton variant="primary" size="sm" @click="abrirModalNovoGit">
              <i class="fa-solid fa-plus" aria-hidden="true"></i>
              <span>Cadastrar Nova Conta GitLab</span>
            </BaseButton>
          </div>

          <!-- Lista de Contas Cadastradas -->
          <div v-if="loadingGitAccounts" class="py-6 text-center text-sm text-muted-foreground">Carregando contas GitLab...</div>
          <div v-else-if="gitAccounts.length === 0" class="py-6 text-center text-sm text-muted-foreground">
            Nenhuma conta GitLab cadastrada. Clique no botão acima para adicionar a primeira.
          </div>
          <div v-else class="overflow-x-auto rounded-lg border border-border-strong bg-background" data-tour="config-gitlab-tabela">
            <table :class="tabelaCls">
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
                    <div class="flex items-center gap-2">
                      <i class="fa-brands fa-gitlab shrink-0 text-lg text-orange-400" aria-hidden="true"></i>
                      <strong>{{ conta.nome }}</strong>
                    </div>
                  </td>
                  <td><code class="rounded bg-sky-400/8 px-1.5 py-0.5 font-mono text-xs text-primary">{{ conta.url }}</code></td>
                  <td><span class="font-mono text-xs text-muted-foreground">{{ conta.token_mascarado }}</span></td>
                  <td>
                    <BaseBadge v-if="conta.padrao" variant="green">PADRÃO</BaseBadge>
                    <button v-else type="button" class="cursor-pointer rounded border-0 bg-transparent px-1.5 py-1 text-xs font-semibold text-primary transition-colors duration-150 hover:bg-primary-glow" @click="definirComoPadrao(conta)">Definir Padrão</button>
                  </td>
                  <td>
                    <div class="flex flex-wrap items-center gap-2">
                      <button 
                        type="button" 
                        class="cursor-pointer rounded border border-border-strong bg-card px-2 py-[3px] text-xs font-semibold text-foreground transition enabled:hover:border-primary enabled:hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
                        :disabled="testandoGitId === conta.id"
                        @click="testarConexaoGit(conta.id)"
                        title="Validar token contra a API do GitLab"
                      >
                        <i class="fa-solid fa-plug" aria-hidden="true"></i>
                        <span>{{ testandoGitId === conta.id ? 'Testando...' : 'Testar Conexão' }}</span>
                      </button>
                      <span v-if="testeResultados[conta.id]" :class="['rounded px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap', testeResultados[conta.id].ok ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400']">
                        <i :class="[testeResultados[conta.id].ok ? 'fa-solid fa-circle-check' : 'fa-solid fa-circle-xmark', 'mr-1']" aria-hidden="true"></i>
                        {{ testeResultados[conta.id].mensagem }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div class="flex items-center gap-1.5">
                      <button type="button" :class="[btnIcone, 'hover:border-primary']" @click="abrirModalEditarGit(conta)" title="Editar Conta" aria-label="Editar conta">
                        <i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>
                      </button>
                      <button type="button" :class="[btnIcone, 'hover:border-canvas-danger hover:text-canvas-danger']" @click="removerGitAccount(conta)" title="Excluir Conta" aria-label="Excluir conta">
                        <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div :class="secao">
          <h3 :class="tituloSecao">Munka - Faturamento Padrão</h3>
          <BaseLabel for="munka_cargo">Cargo Padrão</BaseLabel>
          <BaseSelect id="munka_cargo" v-model="form.munka_cargo">
            <option value="9">Desenvolvedor</option>
            <option value="11">Analista de Sistemas</option>
            <option value="12">Arquiteto de Software</option>
            <option value="16">Analista de Testes</option>
          </BaseSelect>
          <BaseLabel for="munka_nivel">Nível Padrão</BaseLabel>
          <BaseSelect id="munka_nivel" v-model="form.munka_nivel">
            <option value="1">Júnior</option>
            <option value="2">Pleno</option>
            <option value="3">Sênior</option>
            <option value="4">Único</option>
          </BaseSelect>
          <BaseLabel for="munka_responsavel">Responsável Padrão (busca)</BaseLabel>
          <BaseInput id="munka_responsavel" v-model="form.munka_responsavel" placeholder="Ex: João Silva" />
          <BaseLabel for="munka_produto">Produto Padrão</BaseLabel>
          <BaseInput id="munka_produto" v-model="form.munka_produto" placeholder="Ex: [DESENV] MUNKA" />
          <BaseLabel for="munka_projeto">Projeto Padrão</BaseLabel>
          <BaseInput id="munka_projeto" v-model="form.munka_projeto" placeholder="Ex: [DESENV] MUNKA" />
          <BaseLabel for="munka_status_id">Status Inicial Padrão</BaseLabel>
          <BaseSelect id="munka_status_id" v-model="form.munka_status_id">
            <option v-for="st in CATALOGO_STATUS" :key="st.id" :value="st.id">{{ st.rotulo }}</option>
          </BaseSelect>
          <BaseLabel for="munka_data_inicio">Data/Hora de Início Padrão (Ex: 08:00 ou DD/MM/YYYY 08:00)</BaseLabel>
          <BaseInput id="munka_data_inicio" v-model="form.munka_data_inicio" placeholder="Ex: 08:00" />
          <BaseLabel for="munka_data_fim">Data/Hora de Fim Padrão (Ex: 18:00 ou DD/MM/YYYY 18:00)</BaseLabel>
          <BaseInput id="munka_data_fim" v-model="form.munka_data_fim" placeholder="Ex: 18:00" />
        </div>

        <div :class="secao" v-if="cfg.concurrency">
          <h3 :class="tituloSecao">Processamento Assíncrono</h3>
          <div class="mt-1 flex flex-col gap-2.5">
            <div class="flex items-center justify-between text-sm">
              <span class="font-medium">CPU Cores Detectados:</span>
              <span class="font-bold">{{ cfg.concurrency.cpu_cores }} Cores</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="font-medium">Capacidade Total do Sistema:</span>
              <span class="text-base font-bold text-blue-400">{{ cfg.concurrency.total_system_limit }} processos simultâneos</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="font-medium">Pool Dinâmico de Workers:</span>
              <span class="rounded-full border border-emerald-400/25 bg-emerald-400/12 px-2 py-0.5 text-sm font-bold text-emerald-400"><i class="fa-solid fa-bolt mr-1" aria-hidden="true"></i>Ativo (Prioridade + Fallback)</span>
            </div>
            <div class="flex items-center justify-between pl-2 text-xs text-muted-foreground">
              <span class="font-medium">• Fila de Análise de Commits:</span>
              <span class="font-bold">{{ cfg.concurrency.queues.analises }} workers <span :class="detalheFila">(Prioridade: Análises | Auxílio: Lançamentos)</span></span>
            </div>
            <div class="flex items-center justify-between pl-2 text-xs text-muted-foreground">
              <span class="font-medium">• Fila de Lançamento no Munka:</span>
              <span class="font-bold">{{ cfg.concurrency.queues.envios }} workers <span :class="detalheFila">(Prioridade: Lançamentos | Auxílio: Análises)</span></span>
            </div>
          </div>
          <p :class="[notaCls, 'mt-2']">
            <i class="fa-solid fa-bolt mr-1 text-primary" aria-hidden="true"></i><strong>Rebalanceamento Automático:</strong> Os workers são alocados com prioridade para sua fila principal. Quando uma das filas fica ociosa e a outra acumula tarefas, todos os workers ociosos passam a auxiliar automaticamente a fila ativa.
          </p>
        </div>

        <div :class="secao" data-tour="config-secao-backup">
          <h3 :class="tituloSecao">Segurança & Backup Automático</h3>
          <p :class="[notaCls, 'mt-2']">
            <i class="fa-solid fa-floppy-disk mr-1 text-primary" aria-hidden="true"></i><strong>Auto-Save em JSON + SQL:</strong> O sistema realiza cópias de segurança automáticas de todas as tarefas, evidencias, commits e histórico no volume de dados persistente.
          </p>
          <div class="mt-4 flex flex-wrap gap-3">
            <BaseButton variant="primary" :disabled="backupLoading" @click="executarBackupManual">
              <i class="fa-solid fa-database" aria-hidden="true"></i>
              <span>{{ backupLoading ? 'Gerando Backup...' : 'Criar Backup JSON + SQL Agora' }}</span>
            </BaseButton>
            <BaseButton variant="ghost" :disabled="pingLoading" @click="executarPingMunka">
              <i class="fa-solid fa-network-wired" aria-hidden="true"></i>
              <span>{{ pingLoading ? 'Testando...' : 'Testar Conectividade (Ping Munka)' }}</span>
            </BaseButton>
          </div>

          <div v-if="pingResult" class="mt-4 rounded-lg px-4 py-3 text-sm">
            <strong>
              <i :class="[pingResult.ok ? 'fa-solid fa-circle-check' : 'fa-solid fa-triangle-exclamation', 'mr-1']" aria-hidden="true"></i>
              {{ pingResult.ok ? 'Conexão Ativa:' : 'Conexão Indisponível:' }}
            </strong> {{ pingResult.mensagem }}
          </div>

          <div v-if="backupsList.length > 0" class="mt-5" data-tour="config-backups">
            <span class="mb-2 flex items-center gap-1.5 text-sm font-semibold" id="backups-list-label">
              <i class="fa-solid fa-box-archive text-primary" aria-hidden="true"></i>
              <span>Arquivos de Backup Salvos (JSON + SQL)</span>
            </span>
            <div class="max-h-40 overflow-y-auto rounded-lg border border-border-strong bg-background p-2" role="list" aria-labelledby="backups-list-label">
              <div v-for="b in backupsList" :key="b.nome" class="flex justify-between border-b border-border-strong px-2 py-1.5 text-xs" role="listitem">
                <span><i class="fa-solid fa-file-code mr-1 text-muted-foreground" aria-hidden="true"></i>{{ b.nome }}</span>
                <span class="text-muted-foreground">{{ (b.tamanho_bytes / 1024).toFixed(1) }} KB</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <p v-if="msg && ok" class="mt-4 font-semibold text-green-400">{{ msg }}</p>
      <StateMessage v-else-if="msg" type="error" tag="p">{{ msg }}</StateMessage>
    </template>

    <!-- MODAL DE CADASTRO / EDIÇÃO DE CONTA GITLAB -->
    <BaseModal v-if="showGitModal" labelledby="git-modal-title" @close="fecharModalGit">
      <h2 id="git-modal-title" class="mb-1 text-xl font-bold text-foreground">
        <i class="fa-brands fa-gitlab mr-1.5 text-orange-400" aria-hidden="true"></i>
        <span>{{ gitForm.id ? 'Editar Conta GitLab' : 'Cadastrar Conta GitLab' }}</span>
      </h2>
      
      <BaseLabel for="git_nome">Nome / Rótulo Amigável</BaseLabel>
      <BaseInput 
        id="git_nome" 
        v-model="gitForm.nome" 
        placeholder="Ex: GitLab Saúde GO, GitLab Matriz, GitLab Pessoal" 
        required
      />

      <BaseLabel for="git_url">URL Base da Instância GitLab</BaseLabel>
      <BaseInput 
        id="git_url" 
        v-model="gitForm.url" 
        placeholder="Ex: https://git.saude-go.net ou https://gitlab.com" 
        required
      />

      <BaseLabel for="git_token">
        Personal Access Token (PAT)
        <span v-if="gitForm.id" class="text-xs font-normal text-muted-foreground">(deixe em branco ou *** para manter o token atual)</span>
      </BaseLabel>
      <div class="relative flex items-center">
        <BaseInput 
          id="git_token" 
          :type="mostrarToken ? 'text' : 'password'" 
          v-model="gitForm.token" 
          placeholder="glpat-xxxxxxxxxxxxxxxxxxxx" 
          required
        />
        <button 
          type="button" 
          class="absolute right-2 cursor-pointer border-0 bg-transparent text-xs font-semibold text-muted-foreground" 
          @click="mostrarToken = !mostrarToken"
          :aria-label="mostrarToken ? 'Ocultar token' : 'Exibir token'"
        >
          <i :class="mostrarToken ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'" aria-hidden="true"></i>
          <span>{{ mostrarToken ? 'Ocultar' : 'Ver' }}</span>
        </button>
      </div>

      <div class="mt-4 flex items-center gap-2">
        <input id="git_padrao" class="cursor-pointer" type="checkbox" v-model="gitForm.padrao" />
        <label for="git_padrao" class="m-0 block cursor-pointer text-[0.78rem] leading-snug font-bold tracking-[0.05em] text-muted-foreground uppercase">Definir como GitLab padrão para importação</label>
      </div>

      <StateMessage v-if="gitModalErro" type="error" tag="p">{{ gitModalErro }}</StateMessage>

      <template #actions>
        <BaseButton variant="ghost" @click="fecharModalGit">Cancelar</BaseButton>
        <BaseButton
          variant="primary"
          :disabled="salvandoGit || !gitForm.url.trim() || (!gitForm.id && !gitForm.token.trim())" 
          @click="salvarGitAccount"
        >
          <i class="fa-solid fa-floppy-disk" aria-hidden="true"></i>
          <span>{{ salvandoGit ? 'Salvando...' : 'Salvar Conta' }}</span>
        </BaseButton>
      </template>
    </BaseModal>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Config, type GitAccount } from '../api'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import { CATALOGO_STATUS } from '../config/statusMunka'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseLabel from '../components/ui/BaseLabel.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import StateMessage from '../components/ui/StateMessage.vue'

// ── Classes reutilizadas no template ──
const secao = 'flex flex-col gap-3 rounded-xl border border-border bg-card p-6 text-foreground shadow-[0_4px_20px] shadow-black/15 transition-all duration-250'
const tituloSecao = 'mb-2 border-b border-blue-400/20 pb-2.5 text-xs font-extrabold tracking-widest text-primary-light uppercase'
const tituloSecaoTopo = 'mb-1 text-xs font-extrabold tracking-widest text-primary-light uppercase'
const notaCls = 'text-xs leading-snug text-muted-foreground'
const detalheFila = 'ml-1.5 text-xs font-normal text-muted-foreground'
const statusItemBase = 'flex items-center gap-1.5 rounded-full border px-3 py-1.25 text-xs font-semibold'
const statusOk = 'border-green-400/40 bg-green-500/8 text-green-400'
const statusErr = 'border-red-400/40 bg-red-500/8 text-red-400'
const tabelaCls = 'w-full border-collapse text-left text-sm [&_th]:border-b [&_th]:border-border-strong [&_th]:bg-white/2 [&_th]:px-4 [&_th]:py-3 [&_th]:text-left [&_th]:text-xs [&_th]:font-bold [&_th]:tracking-[0.05em] [&_th]:text-muted-foreground [&_th]:uppercase [&_td]:border-b [&_td]:border-border-strong [&_td]:px-4 [&_td]:py-3 [&_td]:text-foreground'
const btnIcone = 'cursor-pointer rounded border border-border-strong bg-transparent px-1.5 py-1 text-xs text-foreground transition'

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
    toastStore.addToast(`Backup realizado! Arquivo: ${arq}`, 'success')
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
