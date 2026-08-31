<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Análise de Commits com IA</h1>
        <HelpModal title="Como funciona a análise" :items="helpItems" />
      </div>
      <router-link to="/fila" class="btn-ghost btn-sm">
        Ver Fila de Execução →
      </router-link>
    </div>

    <!-- Seção 1: Seleção de Modelo de IA -->
    <section class="section" aria-labelledby="heading-passo-1">
      <div class="section-title">
        <span class="step-badge" aria-hidden="true">1</span>
        <h2 id="heading-passo-1">Selecione o Modelo de IA</h2>
      </div>
      
      <div class="model-grid" role="radiogroup" aria-label="Selecione o Modelo de Inteligência Artificial">
        <div 
          v-for="model in models" 
          :key="model.name" 
          class="model-card"
          :class="{ 'selected': selectedModel === model.name }"
          tabindex="0"
          role="radio"
          :aria-checked="selectedModel === model.name"
          @click="selectedModel = model.name"
          @keydown.enter.prevent="selectedModel = model.name"
          @keydown.space.prevent="selectedModel = model.name"
        >
          <div class="model-header">
            <span class="model-badge" :class="model.badgeClass">{{ model.badge }}</span>
            <div class="model-radio-indicator" aria-hidden="true">
              <div class="radio-dot" v-if="selectedModel === model.name"></div>
            </div>
          </div>
          <h3 class="model-name">{{ model.name }}</h3>
          <p class="model-desc">{{ model.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Seção 2: Seleção de Commits com Separação por Repositório -->
    <section class="section" aria-labelledby="heading-passo-2">
      <div class="section-title">
        <span class="step-badge" aria-hidden="true">2</span>
        <h2 id="heading-passo-2">Selecione os Commits para Análise</h2>
      </div>

      <!-- Barra de Controle & Filtros de Repositórios -->
      <div class="repo-control-bar" aria-label="Filtros e organização de commits para análise">
        <div class="control-top-row">
          
          <!-- Alternador de Modos (Tabs Acessíveis) -->
          <div class="view-mode-tabs" role="tablist" aria-label="Modo de exibição dos commits">
            <button 
              id="tab-analise-repo"
              type="button"
              role="tab"
              class="mode-tab-btn" 
              :class="{ active: visaoModo === 'repositorio' }"
              :aria-selected="visaoModo === 'repositorio'"
              aria-controls="panel-analise-view"
              @click="visaoModo = 'repositorio'"
            >
              <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">
                <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
              </svg>
              <span>Por Repositório</span>
              <span class="mode-count-badge">{{ repositoriosResumo.length }}</span>
            </button>

            <button 
              id="tab-analise-lista"
              type="button"
              role="tab"
              class="mode-tab-btn" 
              :class="{ active: visaoModo === 'lista' }"
              :aria-selected="visaoModo === 'lista'"
              aria-controls="panel-analise-view"
              @click="visaoModo = 'lista'"
            >
              <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">
                <path d="M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z"/>
              </svg>
              <span>Todos em Lista</span>
              <span class="mode-count-badge">{{ commitsFiltrados.length }}</span>
            </button>
          </div>

          <!-- Filtro de Status (Pendentes / Analisados / Todos) -->
          <div class="status-segmented" role="group" aria-label="Filtrar por status de análise">
            <button 
              type="button"
              class="status-btn"
              :class="{ active: statusFiltro === 'todos' }"
              @click="statusFiltro = 'todos'"
            >
              Todos ({{ commitsStore.commits.length }})
            </button>
            <button 
              type="button"
              class="status-btn highlight-pendente"
              :class="{ active: statusFiltro === 'pendentes' }"
              @click="statusFiltro = 'pendentes'"
            >
              Apenas Pendentes ({{ totalPendentesGeral }})
            </button>
            <button 
              type="button"
              class="status-btn"
              :class="{ active: statusFiltro === 'analisados' }"
              @click="statusFiltro = 'analisados'"
            >
              Analisados
            </button>
          </div>

          <!-- Campo de Busca -->
          <div class="search-box">
            <svg class="search-icon" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true">
              <path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/>
            </svg>
            <input 
              type="search"
              v-model="termoBusca"
              placeholder="Buscar por mensagem, SHA ou repositório..."
              class="search-input"
              aria-label="Buscar commits por mensagem, hash ou repositório"
            />
            <button 
              v-if="termoBusca" 
              type="button" 
              class="clear-search-btn" 
              @click="termoBusca = ''" 
              aria-label="Limpar busca"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Chips de Seleção Rápida por Repositório -->
        <div class="repo-chips-wrapper" role="region" aria-label="Filtrar por repositório específico">
          <span class="chips-label">Repositórios:</span>
          <div class="chips-list">
            <button 
              type="button" 
              class="repo-chip" 
              :class="{ active: repositorioFiltro === 'todos' }"
              :aria-pressed="repositorioFiltro === 'todos'"
              @click="repositorioFiltro = 'todos'"
            >
              <span>Todos</span>
              <span class="chip-count">{{ commitsStore.commits.length }}</span>
            </button>

            <button 
              v-for="repo in repositoriosResumo" 
              :key="repo.nome"
              type="button" 
              class="repo-chip" 
              :class="[repo.colorClass, { active: repositorioFiltro === repo.nome }]"
              :aria-pressed="repositorioFiltro === repo.nome"
              @click="toggleFiltroRepo(repo.nome)"
              :title="`Filtrar commits de ${repo.nome}`"
            >
              <span class="chip-dot" aria-hidden="true"></span>
              <span class="chip-name">{{ repo.nome }}</span>
              <span class="chip-count">{{ repo.commits.length }}</span>
            </button>
          </div>
        </div>

        <!-- Ações Rápidas de Seleção em Lote -->
        <div class="batch-selection-row">
          <div class="selection-status-badge">
            <strong>{{ selecionados.length }}</strong> de {{ commitsFiltrados.length }} selecionados
          </div>

          <div class="batch-buttons">
            <button 
              type="button" 
              class="btn-batch-action" 
              @click="selecionarTodosPendentes"
              :disabled="totalPendentesExibidos === 0"
              title="Selecionar todos os commits pendentes exibidos"
            >
              ⚡ Selecionar Pendentes ({{ totalPendentesExibidos }})
            </button>
            <button 
              type="button" 
              class="btn-batch-action" 
              @click="selecionarTodosExibidos"
              :disabled="commitsFiltrados.length === 0"
            >
              ✓ Selecionar Todos Exibidos
            </button>
            <button 
              v-if="selecionados.length > 0"
              type="button" 
              class="btn-batch-action btn-clear" 
              @click="desmarcarTodos"
            >
              ✕ Desmarcar Todos
            </button>
          </div>
        </div>
      </div>

      <!-- Estados de Carregamento e Vazio -->
      <div v-if="commitsStore.loading" class="loading" role="status" aria-live="polite">
        Carregando commits para análise...
      </div>

      <div v-else-if="commitsStore.commits.length === 0" class="empty">
        Nenhum commit importado encontrado.
      </div>

      <div v-else-if="commitsFiltrados.length === 0" class="empty">
        <p>Nenhum commit encontrado para os filtros selecionados.</p>
        <button type="button" class="btn-ghost" @click="limparFiltros" style="margin-top: 0.75rem;">
          Limpar Filtros
        </button>
      </div>

      <!-- MODO 1: AGRUPADO POR REPOSITÓRIO -->
      <div 
        v-else-if="visaoModo === 'repositorio'" 
        id="panel-analise-view" 
        class="repo-cards-grid" 
        role="tabpanel" 
        aria-labelledby="tab-analise-repo"
      >
        <div 
          v-for="repo in commitsAgrupadosPorRepo" 
          :key="repo.nome" 
          class="repo-analysis-card"
        >
          <!-- Cabeçalho do Card de Repositório -->
          <div class="repo-card-header">
            <div class="repo-card-header-left">
              <!-- Checkbox para selecionar/desmarcar todos do repositório -->
              <input 
                type="checkbox"
                class="repo-checkbox"
                :checked="isRepoTotalmenteSelecionado(repo)"
                :indeterminate="isRepoParcialmenteSelecionado(repo)"
                @change="toggleSelecionarTodosRepo(repo)"
                :aria-label="`Selecionar todos os commits de ${repo.nome}`"
                :title="`Selecionar todos os commits de ${repo.nome}`"
              />

              <div class="repo-avatar-icon" :class="repo.colorClass">
                <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true">
                  <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
                </svg>
              </div>

              <div class="repo-card-title-block">
                <h3 class="repo-card-name">{{ repo.nome }}</h3>
                <span class="repo-card-sub">
                  {{ repo.commits.length }} commit{{ repo.commits.length > 1 ? 's' : '' }}
                  <span v-if="repo.pendentes > 0" class="sub-pendente">({{ repo.pendentes }} pendente{{ repo.pendentes > 1 ? 's' : '' }})</span>
                </span>
              </div>
            </div>

            <!-- Ações Rápidas do Repositório -->
            <div class="repo-card-header-right">
              <button 
                v-if="repo.pendentes > 0"
                type="button" 
                class="btn-repo-quick"
                @click="selecionarPendentesDoRepo(repo)"
                title="Selecionar apenas os pendentes deste repositório"
              >
                + Selecionar Pendentes ({{ repo.pendentes }})
              </button>

              <button 
                type="button" 
                class="repo-collapse-btn"
                @click="toggleColapsoRepo(repo.nome)"
                :aria-expanded="!isRepoColapsado(repo.nome)"
                :aria-label="isRepoColapsado(repo.nome) ? `Expandir ${repo.nome}` : `Recolher ${repo.nome}`"
              >
                <svg 
                  class="chevron-icon" 
                  :class="{ rotated: isRepoColapsado(repo.nome) }"
                  viewBox="0 0 24 24" 
                  width="18" 
                  height="18" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2.5" 
                  stroke-linecap="round" 
                  stroke-linejoin="round"
                >
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </button>
            </div>
          </div>

          <!-- Lista de Commits do Repositório -->
          <div v-show="!isRepoColapsado(repo.nome)" class="repo-commits-table">
            <div 
              v-for="commit in repo.commits" 
              :key="commit.id"
              class="commit-select-row"
              :class="{ 'selected': selecionados.includes(commit.id) }"
              @click="toggleSelecionado(commit.id)"
              tabindex="0"
              role="checkbox"
              :aria-checked="selecionados.includes(commit.id)"
              @keydown.enter.prevent="toggleSelecionado(commit.id)"
              @keydown.space.prevent="toggleSelecionado(commit.id)"
            >
              <div class="row-checkbox-col" @click.stop>
                <input 
                  type="checkbox" 
                  :value="commit.id" 
                  v-model="selecionados"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem}`"
                />
              </div>

              <!-- Avatar do Autor -->
              <div 
                class="commit-avatar" 
                :style="{ backgroundColor: obterCorAvatar(commit.autor) }"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Mensagem e Informações -->
              <div class="commit-select-info">
                <div class="commit-select-top">
                  <span class="commit-hash">{{ commit.id.slice(0, 8) }}</span>
                  <span class="commit-msg-text" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>
                </div>
                <div class="commit-select-meta">
                  <span>{{ commit.autor }}</span>
                  <span>· {{ commit.data }}</span>
                </div>
              </div>

              <!-- Status do Commit -->
              <div class="row-status-col">
                <span class="badge" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
                  {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                </span>
                <span v-if="commit.analisado && commit.atividades_total" class="badge badge-purple" title="Atividades identificadas">
                  {{ commit.atividades_total }} atv.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- MODO 2: TODOS EM LISTA UNIFICADA -->
      <div 
        v-else 
        id="panel-analise-view" 
        class="unified-commits-list" 
        role="tabpanel" 
        aria-labelledby="tab-analise-lista"
      >
        <div 
          v-for="commit in commitsFiltrados" 
          :key="commit.id"
          class="commit-select-row"
          :class="{ 'selected': selecionados.includes(commit.id) }"
          @click="toggleSelecionado(commit.id)"
          tabindex="0"
          role="checkbox"
          :aria-checked="selecionados.includes(commit.id)"
          @keydown.enter.prevent="toggleSelecionado(commit.id)"
          @keydown.space.prevent="toggleSelecionado(commit.id)"
        >
          <div class="row-checkbox-col" @click.stop>
            <input 
              type="checkbox" 
              :value="commit.id" 
              v-model="selecionados"
              :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}`"
            />
          </div>

          <div 
            class="commit-avatar" 
            :style="{ backgroundColor: obterCorAvatar(commit.autor) }"
            :title="commit.autor"
          >
            {{ obterIniciais(commit.autor) }}
          </div>

          <div class="commit-select-info">
            <div class="commit-select-top">
              <!-- Tag do Repositório -->
              <span class="badge-repo-tag" :class="obterClasseCorRepo(commit.projeto)">
                <svg viewBox="0 0 16 16" width="11" height="11" fill="currentColor" aria-hidden="true">
                  <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
                </svg>
                <span>{{ commit.projeto || 'Sem repositório' }}</span>
              </span>

              <span class="commit-hash">{{ commit.id.slice(0, 8) }}</span>
              <span class="commit-msg-text" :title="commit.mensagem">
                {{ commit.mensagem || '(sem mensagem)' }}
              </span>
            </div>
            <div class="commit-select-meta">
              <span>{{ commit.autor }}</span>
              <span>· {{ commit.data }}</span>
            </div>
          </div>

          <div class="row-status-col">
            <span class="badge" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
              {{ commit.analisado ? 'Analisado' : 'Pendente' }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Barra de Ação Flutuante (Sticky Footer) -->
    <div class="action-footer" v-if="selecionados.length > 0" role="region" aria-label="Ações para commits selecionados">
      <div class="footer-info">
        <span class="footer-count"><strong>{{ selecionados.length }}</strong> commit(s) selecionado(s)</span>
        <span class="footer-repo-count">({{ totalRepositoriosSelecionados }} repositório(s) envolvido(s))</span>
        <span class="footer-divider">·</span>
        <span class="footer-model">Modelo: <strong>{{ selectedModel }}</strong></span>
      </div>

      <div class="footer-actions">
        <button 
          type="button" 
          class="btn-ghost" 
          @click="desmarcarTodos"
        >
          Limpar Seleção
        </button>
        <button 
          type="button"
          class="btn-primary" 
          :disabled="enfileirando" 
          @click="confirmarAnalise"
        >
          {{ enfileirando ? 'Enfileirando...' : `Confirmar e Enfileirar (${selecionados.length})` }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import HelpModal from '../components/HelpModal.vue'
import type { CommitSummary } from '../api'

const helpItems = [
  { title: 'Seleção por Repositório', text: 'Você pode marcar ou desmarcar todos os commits de um projeto específico com um único clique no checkbox do card do repositório.' },
  { title: 'Filtro por Status', text: 'Use o botão "Apenas Pendentes" para isolar rapidamente as alterações que ainda não foram processadas pelo Gemini.' },
  { title: 'Modelos de AI', text: 'O Gemini 3.5 Flash Lite é o modelo recomendado por equilibrar alta precisão e baixo tempo de resposta.' },
  { title: 'Fila de Execução', text: 'Ao confirmar, os commits são enviados para a fila do Celery e processados em paralelo conforme os limites de concorrência configurados.' },
]

const router = useRouter()
const route = useRoute()
const commitsStore = useCommitsStore()
const filaStore = useFilaStore()

const selectedModel = ref('Gemini 3.5 Flash Lite')
const selecionados = ref<string[]>([])
const enfileirando = ref(false)

// Modos de exibição e filtros
const visaoModo = ref<'repositorio' | 'lista'>('repositorio')
const statusFiltro = ref<'todos' | 'pendentes' | 'analisados'>('pendentes')
const repositorioFiltro = ref<string>('todos')
const termoBusca = ref<string>('')
const reposColapsados = ref<Record<string, boolean>>({})

const models = [
  { name: 'Gemini 2.5 Flash Lite', badge: 'Super Rápido', badgeClass: 'badge-green', desc: 'Mais leve e veloz. Indicado para análises rápidas em commits de baixa complexidade.' },
  { name: 'Gemini 3.1 Flash Lite', badge: 'Ultra Eficiente', badgeClass: 'badge-gray', desc: 'Modelo compacto de última geração com alta eficiência operacional.' },
  { name: 'Gemini 3.5 Flash', badge: 'Alta Performance', badgeClass: 'badge-purple', desc: 'Modelo topo de linha mais recente. Máxima precisão na classificação de atividades.' },
  { name: 'Gemini 3.5 Flash Lite', badge: 'Recomendado', badgeClass: 'badge-blue', desc: 'Equilíbrio ideal entre velocidade e precisão de análise.' }
]

onMounted(async () => {
  await commitsStore.fetchCommits()
  
  // Se veio sha por query string, pré-seleciona
  const shaQuery = route.query.commit as string
  if (shaQuery) {
    const commitCompleto = commitsStore.commits.find(c => c.id.startsWith(shaQuery))
    if (commitCompleto) {
      selecionados.value.push(commitCompleto.id)
    }
  }
})

function isRepoColapsado(nome: string): boolean {
  return !!reposColapsados.value[nome]
}

function toggleColapsoRepo(nome: string) {
  reposColapsados.value[nome] = !reposColapsados.value[nome]
}

function toggleFiltroRepo(nome?: string) {
  const repoNome = nome || 'Sem repositório'
  if (repositorioFiltro.value === repoNome) {
    repositorioFiltro.value = 'todos'
  } else {
    repositorioFiltro.value = repoNome
  }
}

function limparFiltros() {
  repositorioFiltro.value = 'todos'
  statusFiltro.value = 'todos'
  termoBusca.value = ''
}

function obterIniciais(nome: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

function obterCorAvatar(nome: string): string {
  if (!nome) return '#777'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    '#007acc', '#3fb950', '#f85149', '#d29922', '#bc8cff', '#1f6feb', '#30b6e6'
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function obterClasseCorRepo(nome?: string): string {
  if (!nome) return 'repo-color-default'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const idx = Math.abs(hash) % 6
  return `repo-color-${idx}`
}

function toggleSelecionado(id: string) {
  const index = selecionados.value.indexOf(id)
  if (index === -1) {
    selecionados.value.push(id)
  } else {
    selecionados.value.splice(index, 1)
  }
}

const totalPendentesGeral = computed(() => {
  return commitsStore.commits.filter(c => !c.analisado).length
})

// Commits filtrados pelos critérios ativos
const commitsFiltrados = computed(() => {
  let list = commitsStore.commits

  // Filtro por repositório
  if (repositorioFiltro.value !== 'todos') {
    list = list.filter(c => (c.projeto?.trim() || 'Sem repositório') === repositorioFiltro.value)
  }

  // Filtro por status
  if (statusFiltro.value === 'pendentes') {
    list = list.filter(c => !c.analisado)
  } else if (statusFiltro.value === 'analisados') {
    list = list.filter(c => c.analisado)
  }

  // Filtro textual
  if (termoBusca.value.trim()) {
    const q = termoBusca.value.trim().toLowerCase()
    list = list.filter(c => {
      const msg = (c.mensagem || '').toLowerCase()
      const id = (c.id || '').toLowerCase()
      const autor = (c.autor || '').toLowerCase()
      const proj = (c.projeto || '').toLowerCase()
      return msg.includes(q) || id.includes(q) || autor.includes(q) || proj.includes(q)
    })
  }

  return list
})

const totalPendentesExibidos = computed(() => {
  return commitsFiltrados.value.filter(c => !c.analisado).length
})

// Resumo consolidado de repositórios
const repositoriosResumo = computed(() => {
  const map: Record<string, {
    nome: string
    commits: CommitSummary[]
    pendentes: number
    analisados: number
    colorClass: string
  }> = {}

  for (const c of commitsStore.commits) {
    const repoNome = c.projeto?.trim() || 'Sem repositório'
    if (!map[repoNome]) {
      map[repoNome] = {
        nome: repoNome,
        commits: [],
        pendentes: 0,
        analisados: 0,
        colorClass: obterClasseCorRepo(repoNome)
      }
    }
    map[repoNome].commits.push(c)
    if (c.analisado) map[repoNome].analisados++
    else map[repoNome].pendentes++
  }

  return Object.values(map).sort((a, b) => b.commits.length - a.commits.length)
})

// Agrupamento por repositório para exibição
const commitsAgrupadosPorRepo = computed(() => {
  const map: Record<string, {
    nome: string
    commits: CommitSummary[]
    pendentes: number
    analisados: number
    colorClass: string
  }> = {}

  for (const c of commitsFiltrados.value) {
    const repoNome = c.projeto?.trim() || 'Sem repositório'
    if (!map[repoNome]) {
      map[repoNome] = {
        nome: repoNome,
        commits: [],
        pendentes: 0,
        analisados: 0,
        colorClass: obterClasseCorRepo(repoNome)
      }
    }
    map[repoNome].commits.push(c)
    if (c.analisado) map[repoNome].analisados++
    else map[repoNome].pendentes++
  }

  return Object.values(map).sort((a, b) => b.commits.length - a.commits.length)
})

// Helpers de seleção de repositório
function isRepoTotalmenteSelecionado(repo: { commits: CommitSummary[] }): boolean {
  if (repo.commits.length === 0) return false
  return repo.commits.every(c => selecionados.value.includes(c.id))
}

function isRepoParcialmenteSelecionado(repo: { commits: CommitSummary[] }): boolean {
  const count = repo.commits.filter(c => selecionados.value.includes(c.id)).length
  return count > 0 && count < repo.commits.length
}

function toggleSelecionarTodosRepo(repo: { commits: CommitSummary[] }) {
  if (isRepoTotalmenteSelecionado(repo)) {
    // Desmarcar todos desse repo
    const ids = new Set(repo.commits.map(c => c.id))
    selecionados.value = selecionados.value.filter(id => !ids.has(id))
  } else {
    // Marcar todos desse repo
    const idsToAdd = repo.commits.map(c => c.id).filter(id => !selecionados.value.includes(id))
    selecionados.value.push(...idsToAdd)
  }
}

function selecionarPendentesDoRepo(repo: { commits: CommitSummary[] }) {
  const pendentesIds = repo.commits.filter(c => !c.analisado).map(c => c.id)
  const idsToAdd = pendentesIds.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...idsToAdd)
}

function selecionarTodosPendentes() {
  const pendentesIds = commitsFiltrados.value.filter(c => !c.analisado).map(c => c.id)
  const idsToAdd = pendentesIds.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...idsToAdd)
}

function selecionarTodosExibidos() {
  const ids = commitsFiltrados.value.map(c => c.id)
  const idsToAdd = ids.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...idsToAdd)
}

function desmarcarTodos() {
  selecionados.value = []
}

const totalRepositoriosSelecionados = computed(() => {
  const repos = new Set<string>()
  for (const sha of selecionados.value) {
    const c = commitsStore.commits.find(commit => commit.id === sha)
    if (c) {
      repos.add(c.projeto?.trim() || 'Sem repositório')
    }
  }
  return repos.size
})

async function confirmarAnalise() {
  if (selecionados.value.length === 0) return
  enfileirando.value = true
  try {
    await filaStore.enfileirarAnalise(selecionados.value, selectedModel.value)
    router.push('/fila')
  } catch {
    // Erro já tratado pelo toast
  } finally {
    enfileirando.value = false
  }
}
</script>

<style scoped>
.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section {
  margin-bottom: 2.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.step-badge {
  background: var(--accent, #388bfd);
  color: #ffffff;
  border-radius: 50%;
  font-weight: 900;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(56, 139, 253, 0.3);
}

.section-title h2 {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  margin: 0;
}

/* ── GRID DE MODELOS DE IA ── */
.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
}

.model-card {
  background: var(--card-bg, #161b22);
  border: 2px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.35rem;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  transition: all 0.15s ease;
  outline: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.model-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent, #58a6ff);
}

.model-card:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: 2px;
}

.model-card.selected {
  border-color: var(--accent, #388bfd);
  background: var(--accent-glow, rgba(56, 189, 248, 0.08));
  box-shadow: 0 4px 16px rgba(56, 139, 253, 0.25);
  transform: translateY(-2px);
}

.model-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.model-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
}

.model-radio-indicator {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--border, #30363d);
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-card.selected .model-radio-indicator {
  border-color: var(--accent, #388bfd);
}

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent, #388bfd);
}

.model-name {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  margin: 0;
}

.model-desc {
  font-size: 0.8rem;
  color: var(--text-muted, #8b949e);
  line-height: 1.45;
  margin: 0;
}

/* ── BARRA DE CONTROLE DE COMMITS ── */
.repo-control-bar {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
}

.control-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.view-mode-tabs {
  display: inline-flex;
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}

.mode-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.85rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted, #8b949e);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-tab-btn:hover {
  color: var(--text, #f0f6fc);
}

.mode-tab-btn.active {
  background: var(--card-bg, #161b22);
  color: var(--text, #f0f6fc);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.mode-count-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--accent-glow, rgba(56, 189, 248, 0.15));
  color: var(--accent, #58a6ff);
}

.status-segmented {
  display: inline-flex;
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}

.status-btn {
  background: transparent;
  border: none;
  color: var(--text-muted, #8b949e);
  padding: 0.45rem 0.8rem;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.status-btn:hover {
  color: var(--text, #f0f6fc);
}

.status-btn.active {
  background: var(--card-bg, #161b22);
  color: var(--text, #f0f6fc);
}

.status-btn.highlight-pendente.active {
  color: var(--accent, #58a6ff);
  font-weight: 700;
}

.search-box {
  display: flex;
  align-items: center;
  position: relative;
  flex: 1;
  max-width: 380px;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 0.85rem;
  color: var(--text-muted, #8b949e);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.5rem 2.2rem 0.5rem 2.4rem;
  font-size: 0.85rem;
  background: var(--bg, #0d1117);
  color: var(--text, #f0f6fc);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  outline: none;
}

.search-input:focus {
  border-color: var(--accent, #58a6ff);
}

.clear-search-btn {
  position: absolute;
  right: 0.6rem;
  background: transparent;
  border: none;
  color: var(--text-muted, #8b949e);
  cursor: pointer;
}

.repo-chips-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-top: 0.25rem;
  border-top: 1px dashed var(--border, #30363d);
}

.chips-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.chips-list {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.repo-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 20px;
  background: var(--bg, #0d1117);
  color: var(--text-muted, #8b949e);
  border: 1px solid var(--border, #30363d);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.repo-chip:hover {
  border-color: var(--accent, #58a6ff);
  color: var(--text, #f0f6fc);
  transform: translateY(-1px);
}

.repo-chip.active {
  background: var(--accent, #388bfd);
  color: #ffffff;
  border-color: var(--accent, #388bfd);
  box-shadow: 0 2px 8px rgba(56, 139, 253, 0.3);
}

.repo-chip.active .chip-count {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.chip-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-count {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted, #8b949e);
}

.batch-selection-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: rgba(56, 189, 248, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  flex-wrap: wrap;
}

.selection-status-badge {
  font-size: 0.85rem;
  color: var(--text, #f0f6fc);
}

.selection-status-badge strong {
  color: var(--accent, #58a6ff);
}

.batch-buttons {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.btn-batch-action {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  color: var(--text, #f0f6fc);
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-batch-action:hover:not(:disabled) {
  border-color: var(--accent, #58a6ff);
  color: var(--accent, #58a6ff);
}

.btn-batch-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-batch-action.btn-clear {
  color: #f85149;
  border-color: rgba(248, 81, 73, 0.3);
}

/* ── CARDS DE REPOSITÓRIO (MODO POR REPOSITÓRIO) ── */
.repo-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.repo-analysis-card {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.repo-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border-bottom: 1px solid var(--border, #30363d);
  gap: 1rem;
  flex-wrap: wrap;
}

.repo-card-header-left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex: 1;
  min-width: 0;
}

.repo-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent, #388bfd);
}

.repo-avatar-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.repo-card-title-block {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.repo-card-name {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.repo-card-sub {
  font-size: 0.78rem;
  color: var(--text-muted, #8b949e);
}

.sub-pendente {
  color: var(--accent, #58a6ff);
  font-weight: 700;
  margin-left: 0.3rem;
}

.repo-card-header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-repo-quick {
  background: var(--bg, #0d1117);
  border: 1px solid var(--accent, #58a6ff);
  color: var(--accent, #58a6ff);
  padding: 0.35rem 0.7rem;
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-repo-quick:hover {
  background: var(--accent, #388bfd);
  color: #ffffff;
}

.repo-collapse-btn {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  color: var(--text-muted, #8b949e);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.chevron-icon {
  transition: transform 0.2s ease;
}

.chevron-icon.rotated {
  transform: rotate(-90deg);
}

/* ── LINHAS DE SELEÇÃO DE COMMITS ── */
.repo-commits-table, .unified-commits-list {
  display: flex;
  flex-direction: column;
}

.unified-commits-list {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  overflow: hidden;
}

.commit-select-row {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border, #30363d);
  cursor: pointer;
  transition: background 0.12s;
  outline: none;
  gap: 0.9rem;
}

.commit-select-row:last-child {
  border-bottom: none;
}

.commit-select-row:hover {
  background: var(--accent-glow, rgba(56, 189, 248, 0.08));
}

.commit-select-row.selected {
  background: rgba(56, 139, 253, 0.12);
}

.commit-select-row:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: -2px;
}

.row-checkbox-col input {
  width: 17px;
  height: 17px;
  cursor: pointer;
  accent-color: var(--accent, #388bfd);
}

.commit-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.76rem;
  font-weight: 800;
  flex-shrink: 0;
  border: 1px solid var(--border, #30363d);
}

.commit-select-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
  min-width: 0;
}

.commit-select-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.badge-repo-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 5px;
  white-space: nowrap;
}

.commit-hash {
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  color: var(--text-muted, #8b949e);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  padding: 1px 5px;
  font-weight: 700;
}

.commit-msg-text {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 550px;
}

.commit-select-meta {
  font-size: 0.78rem;
  color: var(--text-muted, #8b949e);
}

.row-status-col {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}

/* ── STICKY ACTION FOOTER ── */
.action-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--topbar-bg, rgba(15, 23, 42, 0.95));
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--border, #30363d);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 100;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.92rem;
  color: var(--text, #f0f6fc);
  flex-wrap: wrap;
}

.footer-count strong {
  color: var(--accent, #58a6ff);
  font-size: 1.05rem;
}

.footer-repo-count {
  font-size: 0.85rem;
  color: var(--text-muted, #8b949e);
}

.footer-divider {
  color: var(--text-muted, #8b949e);
}

.footer-model strong {
  color: #34d399;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page {
  padding-bottom: 6.5rem;
}

/* Cores de repositórios conformes com WCAG AA */
.repo-color-default {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.repo-color-0 {
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.35);
}

.repo-color-1 {
  background: rgba(192, 132, 252, 0.12);
  color: #c084fc;
  border: 1px solid rgba(192, 132, 252, 0.35);
}

.repo-color-2 {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.35);
}

.repo-color-3 {
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.35);
}

.repo-color-4 {
  background: rgba(244, 114, 182, 0.12);
  color: #f472b6;
  border: 1px solid rgba(244, 114, 182, 0.35);
}

.repo-color-5 {
  background: rgba(129, 140, 248, 0.12);
  color: #818cf8;
  border: 1px solid rgba(129, 140, 248, 0.35);
}

/* Modo Claro Adaptativo */
:global([data-theme="light"]) .repo-color-default {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}

:global([data-theme="light"]) .repo-color-0 {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #7dd3fc;
}

:global([data-theme="light"]) .repo-color-1 {
  background: #f3e8ff;
  color: #7e22ce;
  border: 1px solid #d8b4fe;
}

:global([data-theme="light"]) .repo-color-2 {
  background: #d1fae5;
  color: #047857;
  border: 1px solid #6ee7b7;
}

:global([data-theme="light"]) .repo-color-3 {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fcd34d;
}

:global([data-theme="light"]) .repo-color-4 {
  background: #fce7f3;
  color: #be185d;
  border: 1px solid #f9a8d4;
}

:global([data-theme="light"]) .repo-color-5 {
  background: #e0e7ff;
  color: #4338ca;
  border: 1px solid #a5b4fc;
}
</style>
