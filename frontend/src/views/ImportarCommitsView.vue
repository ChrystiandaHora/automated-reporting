<template>
  <div class="page">
    <!-- Cabeçalho da Página -->
    <div class="page-header">
      <div class="header-left">
        <button type="button" class="btn-ghost btn-back" @click="$router.push('/commits')">
          <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
          <span>Voltar aos Commits</span>
        </button>
        <div class="title-row">
          <h1>Importar Commits do GitLab</h1>
          <HelpModal title="Como funciona a importação" :items="helpItems" />
        </div>
        <p class="header-subtitle">
          Importe commits em lote a partir de uma ou mais instâncias do GitLab com credenciais configuradas.
        </p>
      </div>

      <div class="header-right">
        <router-link to="/config" class="btn-ghost btn-sm">
          <i class="fa-solid fa-gear" aria-hidden="true"></i>
          <span>Gerenciar Contas GitLab</span>
        </router-link>
      </div>
    </div>

    <!-- Mensagens Globais de Sucesso ou Erro -->
    <div v-if="erroGlobal" class="error-banner" role="alert">
      {{ erroGlobal }}
    </div>

    <!-- SEÇÃO 1: SELEÇÃO DA CONTA GITLAB -->
    <section class="section" aria-labelledby="heading-git-selection">
      <div class="section-title">
        <span class="step-badge" aria-hidden="true">1</span>
        <div class="step-title-block">
          <h2 id="heading-git-selection">Selecione a Instância / Conta do GitLab</h2>
          <span class="step-sub">Escolha qual token e URL base serão utilizados para ler os commits e diffs da API</span>
        </div>
      </div>

      <!-- Estado de Carregamento das Contas -->
      <div v-if="loadingContas" class="loading-contas" role="status" aria-live="polite">
        Carregando instâncias GitLab configuradas...
      </div>

      <!-- Alerta quando não há contas cadastradas -->
      <div v-else-if="contas.length === 0" class="empty-contas-box">
        <p>Nenhuma conta do GitLab cadastrada no momento.</p>
        <router-link to="/config" class="btn-primary" style="margin-top: 0.5rem;">
          <i class="fa-solid fa-plus" aria-hidden="true"></i>
          <span>Cadastrar Conta GitLab nas Configurações</span>
        </router-link>
      </div>

      <!-- Grid de Contas GitLab -->
      <div v-else class="git-accounts-grid" role="radiogroup" aria-label="Instâncias do GitLab disponíveis">
        
        <!-- Opção: Detecção Automática por Domínio -->
        <div 
          class="git-account-card auto-detect-card"
          :class="{ 'selected': selectedAccountId === 0 }"
          tabindex="0"
          role="radio"
          :aria-checked="selectedAccountId === 0"
          @click="selectedAccountId = 0"
          @keydown.enter.prevent="selectedAccountId = 0"
          @keydown.space.prevent="selectedAccountId = 0"
        >
          <div class="account-card-header">
            <div class="account-icon-wrap auto-icon">
              <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true" style="font-size: 1.15rem;"></i>
            </div>
            <div class="account-header-info">
              <div class="account-title-row">
                <h3 class="account-name">Detecção Automática</h3>
                <span class="badge badge-smart">SMART MATCH</span>
              </div>
              <span class="account-url">Mapeia cada URL para sua respectiva conta GitLab cadastrada</span>
            </div>
          </div>
          <div class="radio-indicator-pill" aria-hidden="true">
            <div class="radio-dot" v-if="selectedAccountId === 0"></div>
          </div>
        </div>

        <!-- Contas Cadastradas -->
        <div 
          v-for="conta in contas" 
          :key="conta.id" 
          class="git-account-card"
          :class="{ 'selected': selectedAccountId === conta.id }"
          tabindex="0"
          role="radio"
          :aria-checked="selectedAccountId === conta.id"
          @click="selectedAccountId = conta.id"
          @keydown.enter.prevent="selectedAccountId = conta.id"
          @keydown.space.prevent="selectedAccountId = conta.id"
        >
          <div class="account-card-header">
            <div class="account-icon-wrap gitlab-icon">
              <i class="fa-brands fa-gitlab" aria-hidden="true" style="font-size: 1.25rem;"></i>
            </div>
            <div class="account-header-info">
              <div class="account-title-row">
                <h3 class="account-name">{{ conta.nome }}</h3>
                <span v-if="conta.padrao" class="badge badge-padrao">PADRÃO</span>
              </div>
              <span class="account-url">{{ conta.url }}</span>
              <span class="account-token-tag">Token: {{ conta.token_mascarado }}</span>
            </div>
          </div>
          <div class="radio-indicator-pill" aria-hidden="true">
            <div class="radio-dot" v-if="selectedAccountId === conta.id"></div>
          </div>
        </div>

      </div>
    </section>

    <!-- SEÇÃO 2: INFORMAR COMMITS -->
    <section class="section" aria-labelledby="heading-commits-input">
      <div class="section-title">
        <span class="step-badge" aria-hidden="true">2</span>
        <div class="step-title-block">
          <h2 id="heading-commits-input">Informe os Commits</h2>
          <span class="step-sub">Cole as URLs completas dos commits do GitLab (uma por linha)</span>
        </div>
      </div>

      <div class="input-container-grid">
        <div class="textarea-col">
          <label for="input-commits-area" class="input-label">
            URLs dos commits:
          </label>
          <textarea 
            id="input-commits-area"
            v-model="urlsTexto"
            class="commits-textarea"
            rows="8"
            placeholder="Exemplo:&#10;https://gitlab.empresa.com/grupo/projeto/-/commit/a1b2c3d4e5f6...&#10;https://gitlab.empresa.com/outro/projeto/-/commit/f6e5d4c3b2a1..."
            :disabled="importando"
          ></textarea>

          <div class="textarea-actions">
            <button 
              type="button" 
              class="btn-ghost btn-sm" 
              @click="limparTexto"
              :disabled="importando || !urlsTexto"
            >
              <i class="fa-solid fa-eraser" aria-hidden="true"></i>
              <span>Limpar Texto</span>
            </button>
            <span class="parsed-counter">
              <strong>{{ parsedItems.length }}</strong> commit{{ parsedItems.length !== 1 ? 's' : '' }} identificado{{ parsedItems.length !== 1 ? 's' : '' }}
            </span>
          </div>
        </div>

        <!-- Painel Lateral de Pré-Visualização / Inspetor -->
        <div class="inspector-col">
          <h3 class="inspector-title">
            <i class="fa-solid fa-magnifying-glass-chart" aria-hidden="true"></i>
            Pré-Visualização Inteligente
          </h3>

          <div v-if="parsedItems.length === 0" class="inspector-empty">
            Cole as URLs dos commits no campo ao lado para visualizar a validação em tempo real.
          </div>

          <div v-else class="inspector-items-list">
            <div 
              v-for="(item, idx) in parsedItems" 
              :key="idx" 
              class="inspector-item"
              :class="{ 'is-invalid': !item.valido }"
            >
              <div class="item-top">
                <span v-if="item.valido" class="item-sha">{{ item.sha.slice(0, 8) }}</span>
                <span v-else class="item-invalid-badge">Formato Inválido</span>
                <span class="item-project" :title="item.projeto">{{ item.projeto || 'Projeto desconhecido' }}</span>
              </div>
              <div class="item-bottom">
                <span class="item-domain" :title="item.dominio">{{ item.dominio || 'Domínio não detectado' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SEÇÃO 3: EXECUÇÃO E FEEDBACK DA IMPORTAÇÃO -->
    <section class="section action-section">
      <div class="action-bar-card">
        <div class="action-info">
          <span class="action-count-text">
            Pronto para importar <strong>{{ parsedItemsValidos.length }}</strong> commit{{ parsedItemsValidos.length !== 1 ? 's' : '' }}
          </span>
          <span class="action-target-text">
            Instância Git: <strong>{{ nomeContaSelecionada }}</strong>
          </span>
        </div>

        <button 
          type="button" 
          class="btn-primary btn-lg" 
          :disabled="importando || parsedItemsValidos.length === 0" 
          @click="executarImportacao"
        >
          <span v-if="importando" class="spinner-dot-sm"></span>
          <span>{{ importando ? `Importando (${progressoAtual}/${parsedItemsValidos.length})...` : `Importar ${parsedItemsValidos.length} Commit(s)` }}</span>
        </button>
      </div>

      <!-- Barra de Progresso durante a Importação -->
      <div v-if="importando || relatorioExecucao.length > 0" class="progress-container">
        <div 
          class="progress-track" 
          role="progressbar" 
          :aria-valuenow="progressoAtual" 
          aria-valuemin="0" 
          :aria-valuemax="parsedItemsValidos.length"
          aria-label="Progresso da importação dos commits"
        >
          <div 
            class="progress-fill" 
            :style="{ width: percentualProgresso + '%' }"
          ></div>
        </div>

        <!-- Relatório Detalhado de Resultados -->
        <div class="results-report" role="region" aria-label="Resultados da importação">
          <div class="results-summary">
            <span class="res-stat stat-success">✔ {{ totalSucessos }} importado(s)</span>
            <span class="res-stat stat-existing">ℹ {{ totalJaExistiam }} já existia(m)</span>
            <span v-if="totalFalhas > 0" class="res-stat stat-error">❌ {{ totalFalhas }} falha(s)</span>
          </div>

          <div class="results-list">
            <div 
              v-for="(res, idx) in relatorioExecucao" 
              :key="idx" 
              class="result-row"
              :class="`status-${res.status}`"
            >
              <div class="res-status-col">
                <span v-if="res.status === 'sucesso'" class="res-badge badge-green">NOVO</span>
                <span v-else-if="res.status === 'existente'" class="res-badge badge-blue">EXISTENTE</span>
                <span v-else class="res-badge badge-red">ERRO</span>
              </div>
              <div class="res-info-col">
                <span class="res-sha">{{ res.sha ? res.sha.slice(0, 8) : 'Commit' }}</span>
                <span class="res-msg">{{ res.mensagem }}</span>
              </div>
            </div>
          </div>

          <!-- Ações Pós-Importação -->
          <div v-if="!importando && relatorioExecucao.length > 0" class="post-import-actions">
            <button type="button" class="btn-primary" @click="$router.push('/analisar')">
              ⚡ Prosseguir para Análise com IA →
            </button>
            <button type="button" class="btn-ghost" @click="$router.push('/commits')">
              Ver Todos os Commits
            </button>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type GitAccount } from '../api'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Seleção da Conta GitLab', text: 'Você pode escolher qual das contas GitLab cadastradas em Configurações utilizar. A opção "Detecção Automática" identifica o domínio de cada link e associa a conta correta automaticamente.' },
  { title: 'Importação em Lote', text: 'Cole múltiplos links de commits (um por linha). O sistema extrai automaticamente o projeto e o SHA do commit.' },
  { title: 'Evita Duplicidade', text: 'Commits que já foram importados anteriormente são preservados sem duplicar no banco de dados.' },
  { title: 'Nova Conta GitLab', text: 'Caso precise de uma instância nova que ainda não esteja na lista, clique em "Gerenciar Contas GitLab" no topo da página.' },
]

const toastStore = useToastStore()

const contas = ref<GitAccount[]>([])
const loadingContas = ref(true)
const selectedAccountId = ref<number>(0) // 0 = Auto-detectar

const urlsTexto = ref('')
const importando = ref(false)
const progressoAtual = ref(0)
const erroGlobal = ref('')

interface ResultadoItem {
  url: string
  sha: string
  status: 'sucesso' | 'existente' | 'erro'
  mensagem: string
}

const relatorioExecucao = ref<ResultadoItem[]>([])

onMounted(async () => {
  await carregarContas()
})

async function carregarContas() {
  loadingContas.value = true
  try {
    const list = await api.gitAccounts.listar()
    contas.value = list
    // Pré-seleciona a conta padrão ou a auto-detecção
    const padrao = list.find(c => c.padrao)
    if (padrao) {
      selectedAccountId.value = padrao.id
    } else if (list.length > 0) {
      selectedAccountId.value = list[0].id
    } else {
      selectedAccountId.value = 0
    }
  } catch (e: any) {
    erroGlobal.value = `Erro ao carregar contas GitLab: ${e.response?.data?.detail ?? String(e)}`
  } finally {
    loadingContas.value = false
  }
}

interface ParsedCommit {
  raw: string
  valido: boolean
  dominio: string
  projeto: string
  sha: string
}

// Analisa em tempo real o texto digitado
const parsedItems = computed<ParsedCommit[]>(() => {
  const linhas = urlsTexto.value
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)

  return linhas.map(linha => {
    const match = linha.match(/(https?:\/\/[^/]+)\/(.+?)\/(?:-\/)?commit\/([0-9a-fA-F]{6,64})/)
    if (match) {
      return {
        raw: linha,
        valido: true,
        dominio: match[1],
        projeto: match[2],
        sha: match[3],
      }
    }

    // Se veio apenas um hash ou URL curta
    const shaMatch = linha.match(/([0-9a-fA-F]{40})/)
    if (shaMatch) {
      return {
        raw: linha,
        valido: true,
        dominio: '',
        projeto: '',
        sha: shaMatch[1],
      }
    }

    return {
      raw: linha,
      valido: false,
      dominio: '',
      projeto: '',
      sha: '',
    }
  })
})

const parsedItemsValidos = computed(() => {
  return parsedItems.value.filter(i => i.valido)
})

const nomeContaSelecionada = computed(() => {
  if (selectedAccountId.value === 0) return 'Detecção Automática (Smart Match)'
  const conta = contas.value.find(c => c.id === selectedAccountId.value)
  return conta ? `${conta.nome} (${conta.url})` : 'Padrão'
})

const percentualProgresso = computed(() => {
  if (parsedItemsValidos.value.length === 0) return 0
  return Math.round((progressoAtual.value / parsedItemsValidos.value.length) * 100)
})

const totalSucessos = computed(() => relatorioExecucao.value.filter(r => r.status === 'sucesso').length)
const totalJaExistiam = computed(() => relatorioExecucao.value.filter(r => r.status === 'existente').length)
const totalFalhas = computed(() => relatorioExecucao.value.filter(r => r.status === 'erro').length)

function limparTexto() {
  urlsTexto.value = ''
  relatorioExecucao.value = []
  progressoAtual.value = 0
}

async function executarImportacao() {
  if (parsedItemsValidos.value.length === 0) return

  importando.value = true
  erroGlobal.value = ''
  relatorioExecucao.value = []
  progressoAtual.value = 0

  for (const item of parsedItemsValidos.value) {
    try {
      const payload: any = {
        commit_hash: item.raw,
      }
      
      // Se não for detecção automática, envia o account_id explícito
      if (selectedAccountId.value !== 0) {
        payload.git_account_id = selectedAccountId.value
      }

      const res = await api.commits.importar(payload)

      if (res.ja_existia) {
        relatorioExecucao.value.push({
          url: item.raw,
          sha: res.id || item.sha,
          status: 'existente',
          mensagem: `Commit ${item.sha ? item.sha.slice(0, 8) : ''} já havia sido importado previamente.`,
        })
      } else {
        relatorioExecucao.value.push({
          url: item.raw,
          sha: res.id || item.sha,
          status: 'sucesso',
          mensagem: `Commit ${item.sha ? item.sha.slice(0, 8) : ''} importado com sucesso!`,
        })
      }
    } catch (e: any) {
      const detail = e.response?.data?.detail ?? e.message ?? String(e)
      relatorioExecucao.value.push({
        url: item.raw,
        sha: item.sha,
        status: 'erro',
        mensagem: `Falha na importação: ${detail}`,
      })
    } finally {
      progressoAtual.value++
    }
  }

  importando.value = false

  if (totalFalhas.value > 0) {
    toastStore.addToast(`Importação finalizada com ${totalFalhas.value} erro(s).`, 'error')
  } else {
    toastStore.addToast(`Importação concluída com sucesso! (${totalSucessos.value} novos)`, 'success')
  }
}
</script>

<style scoped>
.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.btn-back {
  width: fit-content;
  padding: 0.25rem 0.5rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.header-subtitle {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.error-banner {
  background: rgba(239, 68, 68, 0.15);
  border-left: 4px solid var(--error);
  color: var(--error);
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  font-size: 0.88rem;
  font-weight: 600;
}

.section {
  margin-bottom: 2.25rem;
}

.section-title {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  margin-bottom: 1.2rem;
}

.step-badge {
  background: var(--accent, #388bfd);
  color: #ffffff;
  border-radius: 50%;
  font-weight: 900;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(56, 139, 253, 0.3);
  flex-shrink: 0;
  margin-top: 2px;
}

.step-title-block {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.step-title-block h2 {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  margin: 0;
}

.step-sub {
  font-size: 0.82rem;
  color: var(--text-muted, #8b949e);
}

/* ── GRID DE CONTAS GITLAB ── */
.git-accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.git-account-card {
  background: var(--card-bg, #161b22);
  border: 2px solid var(--border, #30363d);
  border-radius: 10px;
  padding: 1.1rem;
  cursor: pointer;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  outline: none;
}

.git-account-card:hover {
  border-color: var(--accent, #58a6ff);
  transform: translateY(-2px);
}

.git-account-card:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: 2px;
}

.git-account-card.selected {
  border-color: var(--accent, #388bfd);
  background: var(--accent-glow, rgba(56, 189, 248, 0.08));
  box-shadow: 0 4px 16px rgba(56, 139, 253, 0.25);
  transform: translateY(-2px);
}

.account-card-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
}

.account-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.account-icon-wrap.auto-icon {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.account-icon-wrap.gitlab-icon {
  background: rgba(249, 115, 22, 0.15);
  color: #fb923c;
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.account-header-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.account-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.account-name {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge-smart {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(168, 85, 247, 0.2);
  color: #d8b4fe;
  border: 1px solid rgba(168, 85, 247, 0.35);
}

.badge-padrao {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.18);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.35);
}

.account-url {
  font-size: 0.78rem;
  color: var(--text-muted, #8b949e);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.account-token-tag {
  font-size: 0.7rem;
  color: var(--text-muted, #8b949e);
  font-family: monospace;
}

.radio-indicator-pill {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--border, #30363d);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.git-account-card.selected .radio-indicator-pill {
  border-color: var(--accent, #388bfd);
}

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent, #388bfd);
}

/* ── ÁREA DE TEXTO E INSPETOR ── */
.input-container-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 860px) {
  .input-container-grid {
    grid-template-columns: 1fr;
  }
}

.textarea-col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text, #f0f6fc);
}

.commits-textarea {
  width: 100%;
  box-sizing: border-box;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  padding: 0.85rem 1rem;
  background: var(--bg, #0d1117);
  color: var(--text, #f0f6fc);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}

.commits-textarea:focus {
  border-color: var(--accent, #58a6ff);
}

.textarea-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.3rem;
}

.parsed-counter {
  font-size: 0.82rem;
  color: var(--text-muted, #8b949e);
}

.parsed-counter strong {
  color: var(--accent, #58a6ff);
}

/* Painel Lateral do Inspetor */
.inspector-col {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.inspector-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
  display: flex;
  align-items: center;
  gap: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.inspector-empty {
  font-size: 0.82rem;
  color: var(--text-muted, #8b949e);
  font-style: italic;
  padding: 1.5rem 0;
  text-align: center;
}

.inspector-items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 220px;
  overflow-y: auto;
}

.inspector-item {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 0.45rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.inspector-item.is-invalid {
  border-color: rgba(248, 81, 73, 0.4);
}

.item-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.item-sha {
  font-family: monospace;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--accent, #58a6ff);
  background: rgba(56, 189, 248, 0.1);
  padding: 1px 4px;
  border-radius: 4px;
}

.item-invalid-badge {
  font-size: 0.7rem;
  font-weight: 800;
  color: #f85149;
}

.item-project {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-domain {
  font-size: 0.72rem;
  color: var(--text-muted, #8b949e);
}

/* ── BARRA DE AÇÃO E RESULTADOS ── */
.action-bar-card {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.25rem 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
  flex-wrap: wrap;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.action-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.action-count-text {
  font-size: 1.05rem;
  color: var(--text, #f0f6fc);
}

.action-count-text strong {
  color: var(--accent, #58a6ff);
}

.action-target-text {
  font-size: 0.85rem;
  color: var(--text-muted, #8b949e);
}

.action-target-text strong {
  color: var(--text, #f0f6fc);
}

.btn-lg {
  padding: 0.75rem 1.6rem;
  font-size: 0.95rem;
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
}

.spinner-dot-sm {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-right-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── BARRA DE PROGRESSO E RELATÓRIO ── */
.progress-container {
  margin-top: 1.5rem;
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #388bfd, #2ea043);
  transition: width 0.3s ease;
}

.results-summary {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  font-size: 0.9rem;
  font-weight: 700;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border, #30363d);
  flex-wrap: wrap;
}

.stat-success { color: #3fb950; }
.stat-existing { color: #58a6ff; }
.stat-error { color: #f85149; }

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 250px;
  overflow-y: auto;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  font-size: 0.85rem;
}

.res-status-col {
  flex-shrink: 0;
}

.res-badge {
  font-size: 0.68rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
}

.badge-red {
  background: rgba(248, 81, 73, 0.2);
  color: #ff7b72;
  border: 1px solid rgba(248, 81, 73, 0.4);
}

.res-info-col {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
  min-width: 0;
}

.res-sha {
  font-family: monospace;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
}

.res-msg {
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.post-import-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border, #30363d);
  flex-wrap: wrap;
}
</style>
