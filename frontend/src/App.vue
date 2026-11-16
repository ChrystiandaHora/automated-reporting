<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFilaStore } from './stores/fila'
import { api } from './api'
import { useToastStore } from './stores/toast'
import ToastManager from './components/ToastManager.vue'
import NotificacoesSino from './components/NotificacoesSino.vue'
import { instalarDesbloqueioAudio } from './utils/somNotificacao'

type ThemeMode = 'dark' | 'light' | 'auto'

const route = useRoute()
const filaStore = useFilaStore()
const toastStore = useToastStore()

const activeJobsCount = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending' || j.status === 'running').length
})

const itensNavegacao = [
  { to: '/dashboard', icone: 'fa-chart-line', rotulo: 'Dashboard' },
  { to: '/commits', icone: 'fa-code-commit', rotulo: 'Commits' },
  { to: '/importar', icone: 'fa-cloud-arrow-down', rotulo: 'Importar' },
  { to: '/analisar', icone: 'fa-wand-magic-sparkles', rotulo: 'Análise' },
  { to: '/fila', icone: 'fa-list-check', rotulo: 'Fila' },
  { to: '/fila-logs', icone: 'fa-file-waveform', rotulo: 'Logs' },
  { to: '/modelos', icone: 'fa-microchip', rotulo: 'Modelos' },
  { to: '/historico', icone: 'fa-clock-rotate-left', rotulo: 'Histórico' },
  { to: '/tarefas-mes', icone: 'fa-calendar-check', rotulo: 'Tarefas do Mês' },
  { to: '/config', icone: 'fa-gear', rotulo: 'Configuração' }
]

// Mesma regra do router-link-active: a rota exata ou qualquer subrota.
function itemAtivo(to: string): boolean {
  return route.path === to || route.path.startsWith(`${to}/`)
}

const modosTema: { modo: ThemeMode; icone: string; rotulo: string; titulo: string; aria: string }[] = [
  { modo: 'light', icone: 'fa-sun', rotulo: 'Claro', titulo: 'Tema Claro', aria: 'Ativar Tema Claro' },
  { modo: 'dark', icone: 'fa-moon', rotulo: 'Escuro', titulo: 'Tema Escuro', aria: 'Ativar Tema Escuro' },
  {
    modo: 'auto',
    icone: 'fa-circle-half-stroke',
    rotulo: 'Auto',
    titulo: 'Tema Automático (Baseado no horário local: 06:00 às 18:00 Claro, 18:00 às 06:00 Escuro)',
    aria: 'Ativar Tema Automático por horário'
  }
]

const routeTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/commits': 'Commits',
  '/importar': 'Importar Commits',
  '/analisar': 'Analisar',
  '/fila': 'Fila de Execução',
  '/fila-logs': 'Logs de Execução',
  '/modelos': 'Modelos',
  '/historico': 'Histórico',
  '/tarefas-mes/lista': 'Tarefas do Mês - Ajuste Munka',
  '/tarefas-mes/kanban': 'Tarefas do Mês - Kanban',
  '/config': 'Configuração'
}

// Atualiza o título da aba do navegador incluindo a contagem de tarefas ativas na fila
watch([activeJobsCount, () => route.path], ([count, path]) => {
  let pageTitle = 'Nexus'
  if (path && routeTitles[path]) {
    pageTitle = `${routeTitles[path]} - Nexus`
  } else if (path && path.startsWith('/commits/')) {
    pageTitle = `Detalhes do Commit - Nexus`
  }

  if (count > 0) {
    document.title = `(${count}) ${pageTitle}`
  } else {
    document.title = pageTitle
  }
}, { immediate: true })

const IDLE_TIMEOUT_MS = 2 * 60 * 1000 // 2 minutos de ociosidade
let idleTimeoutId: number | null = null

function iniciarIdleTimeout() {
  cancelarIdleTimeout()
  idleTimeoutId = window.setTimeout(async () => {
    // Usuário ativou ou tarefas terminaram, passaram 2 minutos sem tarefas na fila -> desliga automaticamente
    if (isWakeLockActive.value && activeJobsCount.value === 0) {
      await releaseWakeLock()
      localStorage.setItem('nexus-anti-sleep', 'false')
      toastStore.addToast('Anti-Sleep desativado automaticamente após 2 minutos sem tarefas na fila.', 'info')
    }
  }, IDLE_TIMEOUT_MS)
}

function cancelarIdleTimeout() {
  if (idleTimeoutId !== null) {
    clearTimeout(idleTimeoutId)
    idleTimeoutId = null
  }
}

watch(activeJobsCount, async (newCount) => {
  if (newCount > 0) {
    // Existem processos na fila -> liga automaticamente (se ainda não estiver) e cancela a ociosidade
    cancelarIdleTimeout()
    if (!isWakeLockActive.value) {
      await requestWakeLock()
      if (isWakeLockActive.value) {
        localStorage.setItem('nexus-anti-sleep', 'true')
        toastStore.addToast('Anti-Sleep ativado automaticamente: há tarefas na fila.', 'info')
      }
    }
    return
  }

  if (!isWakeLockActive.value) return

  if (newCount === 0) {
    // Não há tarefas na fila (ou todas terminaram) -> inicia tolerância de 2 minutos antes de desligar
    iniciarIdleTimeout()
  }
})

const hasProjectUpdate = ref(false)
const projectBehindCount = ref(0)

const themeMode = ref<ThemeMode>('auto')
const resolvedTheme = ref<'dark' | 'light'>('dark')
let timerInterval: number | null = null

function obterTemaPorHorario(): 'dark' | 'light' {
  const hora = new Date().getHours()
  // Entre 06:00 e 17:59 -> Claro | Entre 18:00 e 05:59 -> Escuro
  return (hora >= 6 && hora < 18) ? 'light' : 'dark'
}

function applyResolvedTheme(theme: 'dark' | 'light') {
  resolvedTheme.value = theme
  document.documentElement.setAttribute('data-theme', theme)
}

function atualizarTemaAuto() {
  if (themeMode.value === 'auto') {
    applyResolvedTheme(obterTemaPorHorario())
  }
}

function setMode(mode: ThemeMode) {
  themeMode.value = mode
  localStorage.setItem('nexus-theme-mode', mode)

  if (mode === 'auto') {
    atualizarTemaAuto()
  } else {
    applyResolvedTheme(mode)
  }
}

async function checarAtualizacaoProjeto() {
  try {
    const res = await api.projeto.verificarAtualizacao()
    hasProjectUpdate.value = res.has_update
    projectBehindCount.value = res.behind_count
  } catch (e) {
    console.error("Falha ao verificar atualizações do projeto:", e)
  }
}

const isWakeLockActive = ref(false)
let wakeLockSentinel: any = null

async function requestWakeLock() {
  if (wakeLockSentinel && !wakeLockSentinel.released) {
    isWakeLockActive.value = true
    return
  }
  if ('wakeLock' in navigator) {
    try {
      wakeLockSentinel = await (navigator as any).wakeLock.request('screen')
      isWakeLockActive.value = true
      wakeLockSentinel.addEventListener('release', () => {
        isWakeLockActive.value = false
      })
    } catch (err: any) {
      console.warn('Wake Lock request failed:', err)
      isWakeLockActive.value = false
    }
  } else {
    isWakeLockActive.value = true
  }
}

async function releaseWakeLock() {
  if (wakeLockSentinel) {
    try {
      await wakeLockSentinel.release()
      wakeLockSentinel = null
    } catch (e) {
      console.warn('Wake Lock release error:', e)
    }
  }
  isWakeLockActive.value = false
}

async function toggleWakeLock() {
  if (isWakeLockActive.value) {
    // Regra: só pode ficar no off manualmente quando não houver nenhuma atividade na fila
    if (activeJobsCount.value > 0) {
      toastStore.addToast('O Anti-Sleep não pode ser desligado enquanto houver tarefas em execução na fila.', 'info')
      return
    }
    cancelarIdleTimeout()
    await releaseWakeLock()
    localStorage.setItem('nexus-anti-sleep', 'false')
  } else {
    await requestWakeLock()
    localStorage.setItem('nexus-anti-sleep', 'true')
    if (activeJobsCount.value === 0) {
      // Usuário clicou para ligar e não tem nada na fila -> tolerância de 2 minutos
      iniciarIdleTimeout()
    } else {
      // Já existem tarefas na fila -> permanece ativo até a fila esvaziar e tolerância de 2 min
      cancelarIdleTimeout()
    }
  }
}

function handleVisibilityChange() {
  if (document.visibilityState !== 'visible') return
  // O navegador solta o wake lock ao ocultar a aba; readquire se estava ligado ou se há fila
  if (localStorage.getItem('nexus-anti-sleep') === 'true' || activeJobsCount.value > 0) {
    requestWakeLock()
    if (activeJobsCount.value === 0) {
      iniciarIdleTimeout()
    } else {
      cancelarIdleTimeout()
    }
  }
}

onMounted(() => {
  instalarDesbloqueioAudio()

  const modoSalvo = localStorage.getItem('nexus-theme-mode') as ThemeMode | null
  if (modoSalvo && ['dark', 'light', 'auto'].includes(modoSalvo)) {
    setMode(modoSalvo)
  } else {
    setMode('auto')
  }

  const antiSleepSalvo = localStorage.getItem('nexus-anti-sleep')
  if (antiSleepSalvo === 'true') {
    requestWakeLock()
    if (activeJobsCount.value === 0) {
      iniciarIdleTimeout()
    }
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)

  // Verifica o horário local a cada minuto para atualizar o tema automático sem recarregar
  timerInterval = window.setInterval(atualizarTemaAuto, 60000)

  filaStore.startPolling()
  checarAtualizacaoProjeto()
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  cancelarIdleTimeout()
  releaseWakeLock()
  if (timerInterval !== null) {
    clearInterval(timerInterval)
  }
  filaStore.stopPolling()
})
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <a href="#main-content" class="absolute -top-25 left-4 z-9999 rounded-md bg-primary px-4 py-2 font-semibold text-white no-underline transition-[top] duration-200 focus:top-4 focus:outline-3 focus:outline-offset-2 focus:outline-primary-light">Pular para o conteúdo principal</a>
    <header class="sticky top-0 z-100 flex h-16 items-center gap-8 border-b border-border-strong bg-topbar px-8 shadow-topbar backdrop-blur-lg transition-colors duration-300" role="banner">
      <div class="group flex shrink-0 cursor-default items-center gap-3">
        <svg class="size-8 drop-shadow-[0_0_8px] drop-shadow-blue-500/30 transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] group-hover:scale-[1.08] group-hover:rotate-4" viewBox="0 0 36 36" fill="none" aria-hidden="true" focusable="false">
          <rect width="36" height="36" rx="10" fill="url(#brand-grad)" />
          <path d="M11 26V10L25 26V10" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="18" cy="18" r="2.5" fill="#38bdf8" />
          <defs>
            <linearGradient id="brand-grad" x1="0" y1="0" x2="36" y2="36">
              <stop offset="0%" stop-color="#06b6d4" />
              <stop offset="50%" stop-color="#6366f1" />
              <stop offset="100%" stop-color="#a855f7" />
            </linearGradient>
          </defs>
        </svg>
        <span class="text-[1.35rem] font-black tracking-[0.08em] text-foreground">NEXUS</span>
        <span
          v-if="hasProjectUpdate"
          class="ml-3 animate-pulse-badge cursor-pointer rounded-full bg-linear-135 from-purple-500 to-blue-500 px-2 py-0.75 align-middle text-[0.65rem] font-bold tracking-[0.02em] text-white"
          role="status"
          :title="`Nova atualização disponível! ${projectBehindCount} commit(s) atrás. Execute 'git pull' no terminal para atualizar o projeto.`"
        >
          Update {{ projectBehindCount > 0 ? `(${projectBehindCount})` : '' }}
        </span>
      </div>

      <nav class="flex gap-2" aria-label="Navegação principal">
        <router-link
          v-for="item in itensNavegacao"
          :key="item.to"
          :to="item.to"
          class="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-[0.88rem] capitalize no-underline transition-all duration-200"
          :class="itemAtivo(item.to)
            ? 'border-primary bg-primary-glow font-semibold text-primary'
            : 'border-transparent font-medium text-muted-foreground hover:bg-slate-400/10 hover:text-foreground'"
        >
          <i class="fa-solid text-[0.85rem]" :class="[item.icone, itemAtivo(item.to) ? 'text-primary opacity-100' : 'opacity-85']" aria-hidden="true"></i>
          <span>{{ item.rotulo }}</span>
          <span
            v-if="item.to === '/fila' && activeJobsCount > 0"
            class="inline-flex h-4.5 min-w-4.5 items-center justify-center rounded-full px-1.5 text-[0.7rem] font-extrabold transition-all duration-200"
            :class="itemAtivo(item.to) ? 'bg-primary text-white' : 'bg-warning text-black'"
            aria-live="polite"
            :aria-label="`${activeJobsCount} tarefas ativas`"
          >{{ activeJobsCount }}</span>
        </router-link>
      </nav>

      <div class="ml-auto flex items-center gap-3">
        <NotificacoesSino />

        <button
          class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-all duration-250 select-none"
          :class="[
            isWakeLockActive
              ? 'border-emerald-500/40 bg-emerald-500/12 text-emerald-400 shadow-[0_0_12px] shadow-emerald-500/22'
              : 'border-border-strong bg-card text-muted-foreground hover:border-primary hover:text-foreground',
            isWakeLockActive && activeJobsCount > 0 ? 'cursor-not-allowed' : 'cursor-pointer'
          ]"
          @click="toggleWakeLock"
          :aria-pressed="isWakeLockActive"
          :title="isWakeLockActive
            ? (activeJobsCount > 0
                ? `Anti-Sleep ATIVO: ${activeJobsCount} processo(s) na fila. Permanecerá ativo até a conclusão das tarefas e 2 minutos após o término.`
                : 'Anti-Sleep ATIVO: Fila vazia. O estado voltará para OFF após 2 minutos sem atividade, ou clique para desligar manualmente.')
            : 'Clique para ativar o Modo Anti-Sleep (Impede suspensão do computador enquanto houver processos ou por até 2 minutos sem atividade).'
          "
          aria-label="Alternar Modo Anti-Sleep"
        >
          <span
            class="size-1.75 rounded-full transition-all duration-200"
            :class="isWakeLockActive ? 'animate-pulse-dot-active bg-emerald-500 shadow-[0_0_8px] shadow-emerald-500' : 'bg-subtle-foreground'"
            aria-hidden="true"
          ></span>
          <i class="fa-solid fa-mug-hot" aria-hidden="true"></i>
          <span class="max-sm:hidden">{{ isWakeLockActive ? 'Anti-Sleep Ativo' : 'Anti-Sleep Off' }}</span>
        </button>

        <div class="inline-flex gap-0.5 rounded-[10px] border border-border-strong bg-card p-0.75 transition-all duration-300" role="group" aria-label="Seleção de tema visual">
          <button
            v-for="m in modosTema"
            :key="m.modo"
            class="inline-flex cursor-pointer items-center gap-1.5 rounded-[7px] border-none px-2.5 py-1.5 text-xs font-semibold transition-all duration-200 max-sm:p-1.5"
            :class="themeMode === m.modo
              ? 'bg-primary text-white shadow-[0_2px_8px] shadow-primary-glow'
              : 'bg-transparent text-muted-foreground hover:bg-slate-400/8 hover:text-foreground'"
            @click="setMode(m.modo)"
            :aria-pressed="themeMode === m.modo"
            :aria-label="m.aria"
            :title="m.titulo"
          >
            <i class="fa-solid inline-flex size-3.5 items-center justify-center text-[0.82rem]" :class="m.icone" aria-hidden="true"></i>
            <span class="max-sm:hidden">{{ m.rotulo }}</span>
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto w-full max-w-7xl flex-1 px-4 py-6 has-[.fila-page]:max-w-384 sm:px-6 sm:py-8 lg:px-8 lg:py-10" id="main-content" tabIndex="-1">
      <router-view />
    </main>
    <ToastManager />
  </div>
</template>
