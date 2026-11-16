<template>
  <div class="pb-26">
    <PageHeader data-tour="analisar-cabecalho">
      <div class="flex items-center gap-3">
        <PageTitle>Análise de Commits com IA</PageTitle>
        <TutorialModal screenId="analisar" />
      </div>
      <router-link
        to="/fila"
        data-tour="analisar-fila-link"
        class="inline-flex cursor-pointer items-center justify-center gap-2 rounded-md border border-border-strong bg-card px-3.25 py-1.5 text-[0.82rem] leading-none font-semibold text-foreground transition-all duration-200 hover:-translate-y-px hover:border-primary hover:text-primary"
      >
        <i class="fa-solid fa-list-check" aria-hidden="true"></i>
        <span>Ver Fila de Execução →</span>
      </router-link>
    </PageHeader>

    <!-- Seção 1: Seleção de Modelo de IA -->
    <section class="mb-10" aria-labelledby="heading-passo-1">
      <div class="flex items-center gap-3 mb-5">
        <span class="bg-primary text-white rounded-full font-black size-7.5 flex items-center justify-center text-sm shadow-[0_2px_8px] shadow-canvas-accent/30" aria-hidden="true">1</span>
        <h2 id="heading-passo-1" class="text-xl font-extrabold text-foreground m-0">Selecione o Modelo de IA</h2>
      </div>
      
      <div data-tour="analisar-modelos" class="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5" role="radiogroup" aria-label="Selecione o Modelo de Inteligência Artificial">
        <div 
          v-for="model in models" 
          :key="model.name" 
          data-tour="analisar-modelo-card"
          :class="[classesCardModelo, selectedModel === model.name ? classesCardModeloSelecionado : classesCardModeloNormal]"
          tabindex="0"
          role="radio"
          :aria-checked="selectedModel === model.name"
          @click="selectedModel = model.name"
          @keydown.enter.prevent="selectedModel = model.name"
          @keydown.space.prevent="selectedModel = model.name"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold px-2 py-0.5 rounded-md border" :class="model.badgeClass">{{ model.badge }}</span>
            <div
              class="size-4.5 rounded-full border-2 flex items-center justify-center"
              :class="selectedModel === model.name ? 'border-primary' : 'border-border-strong'"
              aria-hidden="true"
            >
              <div class="size-2 rounded-full bg-primary" v-if="selectedModel === model.name"></div>
            </div>
          </div>
          <h3 class="text-base font-extrabold text-foreground m-0">
            <i class="fa-solid fa-microchip text-primary mr-1.25 text-sm" aria-hidden="true"></i>
            <span>{{ model.name }}</span>
          </h3>
          <p class="text-xs leading-normal text-muted-foreground m-0">{{ model.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Seção 2: Seleção de Commits com Separação por Repositório -->
    <section class="mb-10" aria-labelledby="heading-passo-2">
      <div class="flex items-center gap-3 mb-5">
        <span class="bg-primary text-white rounded-full font-black size-7.5 flex items-center justify-center text-sm shadow-[0_2px_8px] shadow-canvas-accent/30" aria-hidden="true">2</span>
        <h2 id="heading-passo-2" class="text-xl font-extrabold text-foreground m-0">Selecione os Commits para Análise</h2>
      </div>

      <!-- Barra de Controle & Filtros de Repositórios -->
      <div class="bg-card border border-border-strong rounded-xl p-5 flex flex-col gap-4 mb-6 shadow-[0_4px_14px] shadow-black/15" aria-label="Filtros e organização de commits para análise">
        <div class="flex items-center justify-between gap-4 flex-wrap">
          
          <!-- Alternador de Modos (Tabs Acessíveis) -->
          <div class="inline-flex bg-background border border-border-strong rounded-lg p-0.75 gap-0.75" role="tablist" aria-label="Modo de exibição dos commits">
            <button 
              id="tab-analise-repo"
              type="button"
              role="tab"
              :class="classesAbaModo(visaoModo === 'repositorio')"
              :aria-selected="visaoModo === 'repositorio'"
              aria-controls="panel-analise-view"
              @click="visaoModo = 'repositorio'"
            >
              <i class="fa-solid fa-folder-tree text-base" aria-hidden="true"></i>
              <span>Por Repositório</span>
              <span class="text-xs font-bold px-1.5 py-px rounded-[10px] bg-primary-glow text-primary">{{ repositoriosResumo.length }}</span>
            </button>

            <button 
              id="tab-analise-lista"
              type="button"
              role="tab"
              :class="classesAbaModo(visaoModo === 'lista')"
              :aria-selected="visaoModo === 'lista'"
              aria-controls="panel-analise-view"
              @click="visaoModo = 'lista'"
            >
              <i class="fa-solid fa-list-ul text-base" aria-hidden="true"></i>
              <span>Todos em Lista</span>
              <span class="text-xs font-bold px-1.5 py-px rounded-[10px] bg-primary-glow text-primary">{{ commitsFiltrados.length }}</span>
            </button>
          </div>

          <!-- Filtro de Status (Pendentes / Analisados / Todos) -->
          <div data-tour="analisar-status" class="inline-flex flex-wrap items-center bg-background border border-border-strong rounded-lg p-0.75 gap-0.75" role="group" aria-label="Filtrar por status de análise">
            <button 
              type="button"
              data-tour="analisar-status-btn"
              :class="classesStatusBtn(statusFiltro === 'todos')"
              @click="statusFiltro = 'todos'"
            >
              Todos ({{ commitsStore.commits.length }})
            </button>
            <button 
              type="button"
              data-tour="analisar-status-btn"
              :class="classesStatusBtn(statusFiltro === 'pendentes', true)"
              @click="statusFiltro = 'pendentes'"
            >
              Apenas Pendentes ({{ totalPendentesGeral }})
            </button>
            <button 
              type="button"
              data-tour="analisar-status-btn"
              :class="classesStatusBtn(statusFiltro === 'analisados')"
              @click="statusFiltro = 'analisados'"
            >
              Analisados
            </button>
          </div>

          <!-- Campo de Busca -->
          <div class="flex min-w-60 max-w-95 flex-1">
            <SearchBox
              v-model="termoBusca"
              placeholder="Buscar por mensagem, SHA ou repositório..."
              ariaLabel="Buscar commits por mensagem, hash ou repositório"
            />
          </div>
        </div>

        <!-- Chips de Seleção Rápida por Repositório -->
        <div class="flex items-center gap-3 flex-wrap pt-1 border-t border-dashed border-border-strong" role="region" aria-label="Filtrar por repositório específico">
          <span class="text-sm font-bold text-muted-foreground uppercase tracking-wider shrink-0">Repositórios:</span>
          <div class="flex items-center gap-2 flex-wrap">
            <button 
              type="button" 
              :class="[classesChip, repositorioFiltro === 'todos' ? classesChipAtivo : classesChipNeutro]"
              :aria-pressed="repositorioFiltro === 'todos'"
              @click="repositorioFiltro = 'todos'"
            >
              <span>Todos</span>
              <span :class="[classesChipContador, repositorioFiltro === 'todos' ? classesChipContadorAtivo : classesChipContadorNormal]">{{ commitsStore.commits.length }}</span>
            </button>

            <button 
              v-for="repo in repositoriosResumo" 
              :key="repo.nome"
              type="button" 
              :class="[classesChip, repositorioFiltro === repo.nome ? classesChipAtivo : [repo.colorClass, classesChipHoverColorido]]"
              :aria-pressed="repositorioFiltro === repo.nome"
              @click="toggleFiltroRepo(repo.nome)"
              :title="`Filtrar commits de ${repo.nome}`"
            >
              <span class="size-2 rounded-full bg-current shrink-0" aria-hidden="true"></span>
              <span class="max-w-50 truncate">{{ repo.nome }}</span>
              <span :class="[classesChipContador, repositorioFiltro === repo.nome ? classesChipContadorAtivo : classesChipContadorNormal]">{{ repo.commits.length }}</span>
            </button>
          </div>
        </div>

        <!-- Ações Rápidas de Seleção em Lote -->
        <div class="flex items-center justify-between gap-4 bg-sky-400/6 border border-sky-400/20 rounded-lg px-3.5 py-2.25 flex-wrap">
          <div class="text-sm text-foreground">
            <strong class="text-primary">{{ selecionados.length }}</strong> de {{ commitsFiltrados.length }} selecionados
          </div>

          <div data-tour="analisar-lote" class="flex items-center gap-2.5 flex-wrap">
            <button 
              type="button" 
              data-tour="analisar-lote-btn" :class="[classesBtnLoteBase, classesBtnLoteNeutro]"
              @click="selecionarTodosPendentes"
              :disabled="totalPendentesExibidos === 0"
              title="Selecionar todos os commits pendentes exibidos"
            >
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
              <span>Selecionar Pendentes ({{ totalPendentesExibidos }})</span>
            </button>
            <button 
              type="button" 
              data-tour="analisar-lote-btn" :class="[classesBtnLoteBase, classesBtnLoteNeutro]"
              @click="selecionarTodosExibidos"
              :disabled="commitsFiltrados.length === 0"
            >
              <i class="fa-solid fa-check-double" aria-hidden="true"></i>
              <span>Selecionar Todos Exibidos</span>
            </button>
            <button 
              v-if="selecionados.length > 0"
              type="button" 
              data-tour="analisar-lote-btn" class="text-canvas-danger border-canvas-danger/30" :class="classesBtnLoteBase"
              @click="desmarcarTodos"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              <span>Desmarcar Todos</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Estados de Carregamento e Vazio -->
      <StateMessage v-if="commitsStore.loading" type="loading" role="status" aria-live="polite">
        Carregando commits para análise...
      </StateMessage>

      <StateMessage v-else-if="commitsStore.commits.length === 0" type="empty">
        Nenhum commit importado encontrado.
      </StateMessage>

      <StateMessage v-else-if="commitsFiltrados.length === 0" type="empty">
        <p>Nenhum commit encontrado para os filtros selecionados.</p>
        <BaseButton class="mt-3" @click="limparFiltros">
          Limpar Filtros
        </BaseButton>
      </StateMessage>

      <!-- MODO 1: AGRUPADO POR REPOSITÓRIO -->
      <div 
        v-else-if="visaoModo === 'repositorio'" 
        id="panel-analise-view" 
        class="flex flex-col gap-6" 
        role="tabpanel" 
        aria-labelledby="tab-analise-repo"
      >
        <div 
          v-for="repo in commitsAgrupadosPorRepo" 
          :key="repo.nome" 
          class="bg-card border border-border-strong rounded-xl overflow-hidden shadow-[0_4px_16px] shadow-black/15"
        >
          <!-- Cabeçalho do Card de Repositório -->
          <div class="flex items-center justify-between px-5 py-4 bg-muted border-b border-border-strong gap-4 flex-wrap">
            <div class="flex items-center gap-3.5 flex-1 min-w-0">
              <!-- Checkbox para selecionar/desmarcar todos do repositório -->
              <input 
                type="checkbox"
                class="size-4.5 cursor-pointer accent-primary"
                :checked="isRepoTotalmenteSelecionado(repo)"
                :indeterminate="isRepoParcialmenteSelecionado(repo)"
                @change="toggleSelecionarTodosRepo(repo)"
                :aria-label="`Selecionar todos os commits de ${repo.nome}`"
                :title="`Selecionar todos os commits de ${repo.nome}`"
              />

              <div class="size-9 rounded-lg flex items-center justify-center shrink-0" :class="repo.colorClass">
                <i class="fa-brands fa-git-alt text-lg" aria-hidden="true"></i>
              </div>

              <div class="flex flex-col gap-0.5 min-w-0">
                <h3 class="m-0 text-base font-extrabold text-foreground truncate">{{ repo.nome }}</h3>
                <span class="text-xs text-muted-foreground">
                  {{ repo.commits.length }} commit{{ repo.commits.length > 1 ? 's' : '' }}
                  <span v-if="repo.pendentes > 0" class="text-primary font-bold ml-1.25">({{ repo.pendentes }} pendente{{ repo.pendentes > 1 ? 's' : '' }})</span>
                </span>
              </div>
            </div>

            <!-- Ações Rápidas do Repositório -->
            <div class="flex items-center gap-3">
              <button 
                v-if="repo.pendentes > 0"
                type="button" 
                class="bg-background border border-primary text-primary px-2.75 py-1.5 text-xs font-bold rounded-md cursor-pointer transition-all duration-150 hover:bg-primary hover:text-white"
                @click="selecionarPendentesDoRepo(repo)"
                title="Selecionar apenas os pendentes deste repositório"
              >
                <i class="fa-solid fa-plus" aria-hidden="true"></i>
                <span>Selecionar Pendentes ({{ repo.pendentes }})</span>
              </button>

              <button 
                type="button" 
                class="bg-background border border-border-strong text-muted-foreground size-8 rounded-md flex items-center justify-center cursor-pointer"
                @click="toggleColapsoRepo(repo.nome)"
                :aria-expanded="!isRepoColapsado(repo.nome)"
                :aria-label="isRepoColapsado(repo.nome) ? `Expandir ${repo.nome}` : `Recolher ${repo.nome}`"
              >
                <i 
                  class="fa-solid fa-chevron-down transition-transform duration-200" 
                  :class="{ '-rotate-90': isRepoColapsado(repo.nome) }"
                  aria-hidden="true"
                ></i>
              </button>
            </div>
          </div>

          <!-- Lista de Commits do Repositório -->
          <div v-show="!isRepoColapsado(repo.nome)" class="flex flex-col">
            <div 
              v-for="commit in repo.commits" 
              :key="commit.id"
              :class="classesLinhaCommit(selecionados.includes(commit.id))"
              @click="toggleSelecionado(commit.id)"
              tabindex="0"
              role="checkbox"
              :aria-checked="selecionados.includes(commit.id)"
              @keydown.enter.prevent="toggleSelecionado(commit.id)"
              @keydown.space.prevent="toggleSelecionado(commit.id)"
            >
              <div @click.stop>
                <input 
                  type="checkbox" 
                  class="size-4.25 cursor-pointer accent-primary"
                  :value="commit.id" 
                  v-model="selecionados"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem}`"
                />
              </div>

              <!-- Avatar do Autor -->
              <div 
                class="size-8 rounded-full text-white flex items-center justify-center text-xs font-extrabold shrink-0 border border-border-strong" 
                :class="obterClasseAvatar(commit.autor)"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Mensagem e Informações -->
              <div class="flex flex-col gap-0.75 flex-1 min-w-0">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <span class="font-courier text-xs text-muted-foreground bg-white/5 border border-border-strong rounded px-1.25 py-px font-bold">{{ commit.id.slice(0, 8) }}</span>
                  <span class="text-sm font-semibold text-foreground truncate max-w-137.5" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>
                </div>
                <div class="text-xs text-muted-foreground">
                  <span>{{ commit.autor }}</span>
                  <span>· {{ commit.data }}</span>
                </div>
              </div>

              <!-- Status do Commit -->
              <div class="flex items-center gap-1.5 shrink-0">
                <BaseBadge :variant="commit.analisado ? 'green' : 'gray'">
                  {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                </BaseBadge>
                <BaseBadge v-if="commit.analisado && commit.atividades_total" variant="purple" title="Atividades identificadas">
                  {{ commit.atividades_total }} atv.
                </BaseBadge>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- MODO 2: TODOS EM LISTA UNIFICADA -->
      <div 
        v-else 
        id="panel-analise-view" 
        class="flex flex-col bg-card border border-border-strong rounded-xl overflow-hidden" 
        role="tabpanel" 
        aria-labelledby="tab-analise-lista"
      >
        <div 
          v-for="commit in commitsFiltrados" 
          :key="commit.id"
          :class="classesLinhaCommit(selecionados.includes(commit.id))"
          @click="toggleSelecionado(commit.id)"
          tabindex="0"
          role="checkbox"
          :aria-checked="selecionados.includes(commit.id)"
          @keydown.enter.prevent="toggleSelecionado(commit.id)"
          @keydown.space.prevent="toggleSelecionado(commit.id)"
        >
          <div @click.stop>
            <input 
              type="checkbox" 
              class="size-4.25 cursor-pointer accent-primary"
              :value="commit.id" 
              v-model="selecionados"
              :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}`"
            />
          </div>

          <div 
            class="size-8 rounded-full text-white flex items-center justify-center text-xs font-extrabold shrink-0 border border-border-strong" 
            :class="obterClasseAvatar(commit.autor)"
            :title="commit.autor"
          >
            {{ obterIniciais(commit.autor) }}
          </div>

          <div class="flex flex-col gap-0.75 flex-1 min-w-0">
            <div class="flex items-center gap-2.5 flex-wrap">
              <!-- Tag do Repositório -->
              <span class="inline-flex items-center gap-1.5 text-xs font-bold px-1.5 py-0.5 rounded-[5px] whitespace-nowrap" :class="obterClasseCorRepo(commit.projeto)">
                <i class="fa-brands fa-gitlab text-xs mr-0.75" aria-hidden="true"></i>
                <span>{{ commit.projeto || 'Sem repositório' }}</span>
              </span>

              <span class="font-courier text-xs text-muted-foreground bg-white/5 border border-border-strong rounded px-1.25 py-px font-bold">{{ commit.id.slice(0, 8) }}</span>
              <span class="text-sm font-semibold text-foreground truncate max-w-137.5" :title="commit.mensagem">
                {{ commit.mensagem || '(sem mensagem)' }}
              </span>
            </div>
            <div class="text-xs text-muted-foreground">
              <span>{{ commit.autor }}</span>
              <span>· {{ commit.data }}</span>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <BaseBadge :variant="commit.analisado ? 'green' : 'gray'">
              {{ commit.analisado ? 'Analisado' : 'Pendente' }}
            </BaseBadge>
          </div>
        </div>
      </div>
    </section>

    <!-- Barra de Ação Flutuante (Sticky Footer) -->
    <div data-tour="analisar-barra-acao" class="fixed bottom-0 inset-x-0 bg-topbar backdrop-blur-md border-t border-border-strong px-8 py-4 flex items-center justify-between z-100 shadow-[0_-4px_20px] shadow-black/40 gap-4 flex-wrap" v-if="selecionados.length > 0" role="region" aria-label="Ações para commits selecionados">
      <div class="flex items-center gap-2.5 text-sm text-foreground flex-wrap">
        <span><strong class="text-primary text-base">{{ selecionados.length }}</strong> commit(s) selecionado(s)</span>
        <span class="text-sm text-muted-foreground">({{ totalRepositoriosSelecionados }} repositório(s) envolvido(s))</span>
        <span class="text-muted-foreground">·</span>
        <span>Modelo: <strong class="text-emerald-400">{{ selectedModel }}</strong></span>
      </div>

      <div class="flex items-center gap-3">
        <BaseButton @click="desmarcarTodos">
          <i class="fa-solid fa-xmark" aria-hidden="true"></i>
          <span>Limpar Seleção</span>
        </BaseButton>
        <BaseButton
          variant="primary"
          :disabled="enfileirando"
          @click="confirmarAnalise"
        >
          <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>
          <span>{{ enfileirando ? 'Enfileirando...' : `Confirmar e Enfileirar (${selecionados.length})` }}</span>
        </BaseButton>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import TutorialModal from '../components/TutorialModal.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import SearchBox from '../components/ui/SearchBox.vue'
import StateMessage from '../components/ui/StateMessage.vue'
import type { CommitSummary } from '../api'

const router = useRouter()
const route = useRoute()
const commitsStore = useCommitsStore()
const filaStore = useFilaStore()

const selectedModel = ref('Gemini 3.8 Flash')
const selecionados = ref<string[]>([])
const enfileirando = ref(false)

// Modos de exibição e filtros
const visaoModo = ref<'repositorio' | 'lista'>('repositorio')
const statusFiltro = ref<'todos' | 'pendentes' | 'analisados'>('pendentes')
const repositorioFiltro = ref<string>('todos')
const termoBusca = ref<string>('')
const reposColapsados = ref<Record<string, boolean>>({})

const classesBadgeModelo = {
  purple: 'bg-badge-purple text-badge-purple-foreground border-badge-purple-border',
  blue: 'bg-badge-code text-badge-code-foreground border-badge-code-border',
  green: 'bg-badge-green text-badge-green-foreground border-badge-green-border',
  orange: 'bg-badge-orange text-badge-orange-foreground border-badge-orange-border'
}

const classesCardModelo = 'bg-card border-2 rounded-xl p-5.5 cursor-pointer transition-all duration-150 outline-none focus-visible:outline-solid focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 flex flex-col gap-2 hover:-translate-y-0.5 hover:border-primary'
const classesCardModeloNormal = 'border-border-strong shadow-[0_4px_14px] shadow-black/15'
const classesCardModeloSelecionado = 'border-primary bg-primary-glow shadow-[0_4px_16px] shadow-canvas-accent/25 -translate-y-0.5'

const classesAbaModoBase = 'inline-flex items-center gap-2 px-3.5 py-1.75 text-sm font-semibold border-0 rounded-md cursor-pointer transition-all duration-150'
function classesAbaModo(ativo: boolean) {
  return [classesAbaModoBase, ativo
    ? 'bg-card text-foreground shadow-[0_2px_8px] shadow-black/25'
    : 'bg-transparent text-muted-foreground hover:text-foreground']
}

const classesStatusBtnBase = 'inline-flex h-8.5 cursor-pointer items-center gap-[0.45rem] rounded-md border-0 px-3 text-[0.82rem] select-none transition-all duration-200'
function classesStatusBtn(ativo: boolean, destaque = false) {
  if (!ativo) return [classesStatusBtnBase, 'bg-transparent text-muted-foreground font-semibold hover:text-foreground']
  return [classesStatusBtnBase, destaque ? 'bg-card text-primary font-bold' : 'bg-card text-foreground font-semibold']
}

const classesChip = 'inline-flex items-center gap-1.75 px-3 py-1.5 text-sm font-semibold rounded-full border cursor-pointer transition-all duration-150 whitespace-nowrap hover:-translate-y-px'
const classesChipNeutro = 'bg-background text-muted-foreground border-border-strong hover:border-primary hover:text-foreground'
const classesChipHoverColorido = 'dark:hover:border-primary dark:hover:text-foreground'
const classesChipAtivo = 'bg-primary text-white border-primary shadow-[0_2px_8px] shadow-canvas-accent/30'
const classesChipContador = 'text-xs font-extrabold px-1.5 py-px rounded-[10px]'
const classesChipContadorNormal = 'bg-white/8 text-muted-foreground'
const classesChipContadorAtivo = 'bg-white/25 text-white'

const classesBtnLoteBase = 'bg-background border text-xs font-semibold px-3 py-1.5 rounded-md cursor-pointer transition-all duration-150 enabled:hover:border-primary enabled:hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed'
const classesBtnLoteNeutro = 'border-border-strong text-foreground'

const classesLinhaCommitBase = 'flex items-center px-5 py-3 border-b border-border-strong cursor-pointer transition-colors duration-120 outline-none focus-visible:outline-solid focus-visible:outline-2 focus-visible:outline-primary -outline-offset-2 gap-3.5 last:border-b-0'
function classesLinhaCommit(selecionado: boolean) {
  return [classesLinhaCommitBase, selecionado ? 'bg-canvas-accent/12' : 'hover:bg-primary-glow']
}

// Cores por repositório (escuro por padrão, variante clara via light:)
const classesCorRepoPadrao = 'border bg-slate-400/12 text-slate-300 border-slate-400/30 light:bg-slate-100 light:text-slate-700 light:border-slate-300'
const classesCorRepo = [
  'border bg-sky-400/12 text-sky-400 border-sky-400/35 light:bg-sky-100 light:text-sky-700 light:border-sky-300',
  'border bg-purple-400/12 text-purple-400 border-purple-400/35 light:bg-purple-100 light:text-purple-700 light:border-purple-300',
  'border bg-emerald-400/12 text-emerald-400 border-emerald-400/35 light:bg-emerald-100 light:text-emerald-700 light:border-emerald-300',
  'border bg-amber-400/12 text-amber-400 border-amber-400/35 light:bg-amber-100 light:text-amber-700 light:border-amber-300',
  'border bg-pink-400/12 text-pink-400 border-pink-400/35 light:bg-pink-100 light:text-pink-700 light:border-pink-300',
  'border bg-indigo-400/12 text-indigo-400 border-indigo-400/35 light:bg-indigo-100 light:text-indigo-700 light:border-indigo-300'
]

const models = [
  { name: 'Gemini 3.8 Flash', badge: 'Mais Recente', badgeClass: classesBadgeModelo.purple, desc: 'Modelo topo de linha mais atual. Maior capacidade de raciocínio e precisão na classificação.' },
  { name: 'Gemini 3.7 Flash', badge: 'Alta Performance', badgeClass: classesBadgeModelo.blue, desc: 'Excelente capacidade analítica e raciocínio avançado para diffs de código complexos.' },
  { name: 'Gemini 3.6 Flash', badge: 'Rápido & Estável', badgeClass: classesBadgeModelo.green, desc: 'Equilíbrio sólido entre tempo de resposta e qualidade na análise de mudanças técnicas.' },
  { name: 'Gemini 3.5 Flash Lite', badge: 'Recomendado (Maior Cota)', badgeClass: classesBadgeModelo.orange, desc: 'Maior limite diário (500 RPD). Ideal para análises em lote contínuas.' }
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

function obterClasseAvatar(nome: string): string {
  if (!nome) return 'bg-avatar-default'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    'bg-avatar-blue', 'bg-canvas-success', 'bg-canvas-danger', 'bg-avatar-amber',
    'bg-avatar-purple', 'bg-avatar-indigo', 'bg-avatar-cyan'
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function obterClasseCorRepo(nome?: string): string {
  if (!nome) return classesCorRepoPadrao
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const idx = Math.abs(hash) % 6
  return classesCorRepo[idx]
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
