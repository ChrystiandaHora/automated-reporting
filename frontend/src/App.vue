<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFilaStore } from './stores/fila'
import { api } from './api'
import ToastManager from './components/ToastManager.vue'

type ThemeMode = 'dark' | 'light' | 'auto'

const route = useRoute()
const filaStore = useFilaStore()

const activeJobsCount = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending' || j.status === 'running').length
})

const routeTitles: Record<string, string> = {
  '/commits': 'Commits',
  '/analisar': 'Analisar',
  '/fila': 'Fila de Execução',
  '/modelos': 'Modelos',
  '/historico': 'Histórico',
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

watch(activeJobsCount, async (count) => {
  if (count === 0 && isWakeLockActive.value) {
    await releaseWakeLock()
    localStorage.setItem('nexus-anti-sleep', 'false')
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
    await releaseWakeLock()
    localStorage.setItem('nexus-anti-sleep', 'false')
  } else {
    await requestWakeLock()
    localStorage.setItem('nexus-anti-sleep', 'true')
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible' && localStorage.getItem('nexus-anti-sleep') !== 'false') {
    requestWakeLock()
  }
}

onMounted(() => {
  const modoSalvo = localStorage.getItem('nexus-theme-mode') as ThemeMode | null
  if (modoSalvo && ['dark', 'light', 'auto'].includes(modoSalvo)) {
    setMode(modoSalvo)
  } else {
    setMode('auto')
  }

  // Ativa por padrão o Modo Anti-Sleep para garantir que o PC não durma durante execuções
  const antiSleepSalvo = localStorage.getItem('nexus-anti-sleep')
  if (antiSleepSalvo !== 'false') {
    requestWakeLock()
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)

  // Verifica o horário local a cada minuto para atualizar o tema automático sem recarregar
  timerInterval = window.setInterval(atualizarTemaAuto, 60000)

  filaStore.startPolling()
  checarAtualizacaoProjeto()
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  releaseWakeLock()
  if (timerInterval !== null) {
    clearInterval(timerInterval)
  }
  filaStore.stopPolling()
})
</script>

<template>
  <div class="app">
    <a href="#main-content" class="skip-link">Pular para o conteúdo principal</a>
    <header class="topbar" role="banner">
      <div class="brand">
        <svg class="brand-icon" viewBox="0 0 36 36" fill="none" aria-hidden="true" focusable="false">
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
        <span class="brand-text">NEXUS</span>
        <span 
          v-if="hasProjectUpdate" 
          class="project-update-badge" 
          role="status"
          :title="`Nova atualização disponível! ${projectBehindCount} commit(s) atrás. Execute 'git pull' no terminal para atualizar o projeto.`"
        >
          Update {{ projectBehindCount > 0 ? `(${projectBehindCount})` : '' }}
        </span>
      </div>

      <nav class="nav" aria-label="Navegação principal">
        <router-link to="/commits">Commits</router-link>
        <router-link to="/fila">
          Fila
          <span v-if="activeJobsCount > 0" class="fila-badge" aria-live="polite" :aria-label="`${activeJobsCount} tarefas ativas`">{{ activeJobsCount }}</span>
        </router-link>
        <router-link to="/modelos">Modelos</router-link>
        <router-link to="/historico">Histórico</router-link>
        <router-link to="/config">Configuração</router-link>
      </nav>

      <div class="topbar-actions">
        <button 
          class="anti-sleep-btn" 
          :class="{ active: isWakeLockActive }" 
          @click="toggleWakeLock" 
          :aria-pressed="isWakeLockActive"
          :title="isWakeLockActive ? 'Anti-Sleep ATIVO: Seu computador NÃO vai bloquear a tela nem entrar em modo de suspensão enquanto esta página estiver aberta.' : 'Clique para ativar o Modo Anti-Sleep (Impede bloqueio de tela e suspensão do computador).'"
          aria-label="Alternar Modo Anti-Sleep"
        >
          <span class="anti-sleep-dot" aria-hidden="true"></span>
          <span class="anti-sleep-icon" aria-hidden="true">☕</span>
          <span class="anti-sleep-text">{{ isWakeLockActive ? 'Anti-Sleep Ativo' : 'Anti-Sleep Off' }}</span>
        </button>

        <div class="theme-segmented" role="group" aria-label="Seleção de tema visual">
          <button 
            class="theme-segment-btn" 
            :class="{ active: themeMode === 'light' }" 
            @click="setMode('light')" 
            :aria-pressed="themeMode === 'light'"
            aria-label="Ativar Tema Claro"
            title="Tema Claro"
          >
            <svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
            <span class="theme-label">Claro</span>
          </button>

          <button 
            class="theme-segment-btn" 
            :class="{ active: themeMode === 'dark' }" 
            @click="setMode('dark')" 
            :aria-pressed="themeMode === 'dark'"
            aria-label="Ativar Tema Escuro"
            title="Tema Escuro"
          >
            <svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
            <span class="theme-label">Escuro</span>
          </button>

          <button 
            class="theme-segment-btn" 
            :class="{ active: themeMode === 'auto' }" 
            @click="setMode('auto')" 
            :aria-pressed="themeMode === 'auto'"
            aria-label="Ativar Tema Automático por horário"
            title="Tema Automático (Baseado no horário local: 06:00 às 18:00 Claro, 18:00 às 06:00 Escuro)"
          >
            <svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span class="theme-label">Auto</span>
          </button>
        </div>
      </div>
    </header>

    <main class="content" id="main-content" tabIndex="-1">
      <router-view />
    </main>
    <ToastManager />
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.skip-link {
  position: absolute;
  top: -100px;
  left: 1rem;
  background: var(--accent);
  color: #ffffff;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  z-index: 9999;
  transition: top 0.2s ease;
  text-decoration: none;
}
.skip-link:focus {
  top: 1rem;
  outline: 3px solid var(--accent-light);
  outline-offset: 2px;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

:root, [data-theme="dark"] {
  --bg: #0F172A;
  --card-bg: #1E293B;
  --card-border: #334155;
  --border: #475569;
  --input-border: #64748B;
  --text: #F8FAFC;
  --text-muted: #CBD5E1;
  --text-subtle: #94A3B8;
  --accent: #3B82F6;
  --accent-light: #60A5FA;
  --accent-cyan: #06B6D4;
  --accent-grad: linear-gradient(135deg, #06b6d4 0%, #3B82F6 50%, #a855f7 100%);
  --accent-glow: rgba(59, 130, 246, 0.25);
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --topbar-bg: rgba(15, 23, 42, 0.85);

  --badge-code-bg: rgba(96, 165, 250, 0.12);
  --badge-code-color: #93C5FD;
  --badge-code-border: rgba(96, 165, 250, 0.3);

  --badge-hpa-bg: rgba(251, 191, 36, 0.12);
  --badge-hpa-color: #FCD34D;
  --badge-hpa-border: rgba(251, 191, 36, 0.3);

  --badge-green-bg: rgba(16, 185, 129, 0.15);
  --badge-green-color: #34D399;
  --badge-green-border: rgba(16, 185, 129, 0.3);

  --badge-orange-bg: rgba(245, 158, 11, 0.15);
  --badge-orange-color: #FBBF24;
  --badge-orange-border: rgba(245, 158, 11, 0.3);

  --badge-purple-bg: rgba(168, 85, 247, 0.15);
  --badge-purple-color: #C084FC;
  --badge-purple-border: rgba(168, 85, 247, 0.3);

  --header-group-bg: rgba(255, 255, 255, 0.03);
  --sha-box-bg: rgba(255, 255, 255, 0.05);
  --sha-box-color: #94A3B8;
  
  font-family: 'Outfit', 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}

[data-theme="light"] {
  --bg: #F8FAFC;
  --card-bg: #FFFFFF;
  --card-border: #CBD5E1;
  --border: #94A3B8;
  --input-border: #718096;
  --text: #0F172A;
  --text-muted: #374151;
  --text-subtle: #4B5563;
  --accent: #1D4ED8;
  --accent-light: #1E40AF;
  --accent-cyan: #0369A1;
  --accent-grad: linear-gradient(135deg, #1D4ED8 0%, #4F46E5 50%, #7C3AED 100%);
  --accent-glow: rgba(29, 78, 216, 0.12);
  --success: #047857;
  --warning: #92400E;
  --error: #B91C1C;
  --topbar-bg: rgba(248, 250, 252, 0.95);

  --badge-code-bg: #EFF6FF;
  --badge-code-color: #1E40AF;
  --badge-code-border: #BFDBFE;

  --badge-hpa-bg: #FEF3C7;
  --badge-hpa-color: #92400E;
  --badge-hpa-border: #FDE68A;

  --badge-green-bg: #D1FAE5;
  --badge-green-color: #065F46;
  --badge-green-border: #A7F3D0;

  --badge-orange-bg: #FFEDD5;
  --badge-orange-color: #9A3412;
  --badge-orange-border: #FDBA74;

  --badge-purple-bg: #F3E8FF;
  --badge-purple-color: #6B21A8;
  --badge-purple-border: #E9D5FF;

  --header-group-bg: #F1F5F9;
  --sha-box-bg: #F1F5F9;
  --sha-box-color: #1E293B;
}

body {
  background: var(--bg);
  color: var(--text);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.02);
}
::-webkit-scrollbar-thumb {
  background: var(--card-border);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--text-subtle);
}

.app { display: flex; flex-direction: column; min-height: 100vh; }

/* ── Topbar ── */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--topbar-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 2rem;
  height: 64px;
  gap: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
  cursor: default;
}

.brand-icon {
  width: 32px;
  height: 32px;
  filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.3));
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.brand:hover .brand-icon {
  transform: scale(1.08) rotate(4deg);
}

.brand-text {
  font-weight: 900;
  font-size: 1.35rem;
  letter-spacing: 0.08em;
  color: var(--text);
}

.nav {
  display: flex;
  gap: 0.5rem;
}

.nav a {
  color: var(--text-muted);
  text-decoration: none;
  text-transform: capitalize;
  font-weight: 500;
  font-size: 0.88rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}
.nav a:hover { 
  color: var(--text); 
  background: rgba(148, 163, 184, 0.1); 
}
.nav a.router-link-active { 
  background: var(--accent-glow);
  color: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ── Anti-Sleep Button ── */
.anti-sleep-btn {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.35rem 0.75rem;
  border-radius: 99px;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}

.anti-sleep-btn:hover {
  border-color: var(--accent);
  color: var(--text);
}

.anti-sleep-btn.active {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.22);
}

.anti-sleep-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-subtle);
  transition: all 0.2s ease;
}

.anti-sleep-btn.active .anti-sleep-dot {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: pulse-dot 1.8s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

@media (max-width: 640px) {
  .anti-sleep-text { display: none; }
}

/* ── Theme Segmented Control ── */
.theme-segmented {
  display: inline-flex;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
  transition: all 0.3s ease;
}

.theme-segment-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 0.35rem 0.65rem;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.theme-segment-btn:hover {
  color: var(--text);
  background: rgba(148, 163, 184, 0.08);
}

.theme-segment-btn.active {
  background: var(--accent);
  color: #ffffff;
  box-shadow: 0 2px 8px var(--accent-glow);
}

.theme-icon {
  width: 14px;
  height: 14px;
}

@media (max-width: 640px) {
  .theme-label { display: none; }
  .theme-segment-btn { padding: 0.35rem; }
}

.fila-badge {
  background: var(--warning);
  color: #000;
  border-radius: 99px;
  padding: 0 6px;
  font-size: 0.7rem;
  font-weight: 800;
  height: 18px;
  min-width: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.nav a.router-link-active .fila-badge {
  background: var(--accent);
  color: #fff;
}

.project-update-badge {
  margin-left: 0.75rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #a855f7, #3b82f6);
  color: #ffffff;
  padding: 3px 8px;
  border-radius: 99px;
  vertical-align: middle;
  animation: pulse-badge 2.5s infinite;
  cursor: pointer;
}

@keyframes pulse-badge {
  0% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.5); }
  70% { box-shadow: 0 0 0 8px rgba(168, 85, 247, 0); }
  100% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0); }
}

/* ── Content ── */
.content {
  flex: 1;
  max-width: 80rem;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding: 1.5rem 1rem;
  box-sizing: border-box;
}

@media (min-width: 640px) {
  .content { padding: 2rem 1.5rem; }
}

@media (min-width: 1024px) {
  .content { padding: 2.5rem 2rem; }
}

/* ── Shared page ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1.25rem;
}
.page-header h1 { 
  font-size: 1.75rem; 
  font-weight: 700; 
  letter-spacing: -0.02em;
  color: var(--text);
}

.loading, .empty { 
  color: var(--text-muted); 
  padding: 3rem 0; 
  text-align: center;
  font-size: 0.95rem;
  letter-spacing: 0.01em;
}
.error { 
  color: var(--error); 
  font-size: 0.875rem; 
  margin-top: 0.5rem; 
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid var(--error);
  padding: 0.625rem 0.875rem;
  border-radius: 4px;
  line-height: 1.5;
}
.success { color: var(--success); font-weight: 600; }

/* ── Badges ── */
.badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  line-height: 1;
}
.badge-green  { background: var(--badge-green-bg); color: var(--badge-green-color); border: 1px solid var(--badge-green-border); }
.badge-gray   { background: var(--header-group-bg); color: var(--text-muted); border: 1px solid var(--border); }
.badge-blue   { background: var(--badge-code-bg); color: var(--badge-code-color); border: 1px solid var(--badge-code-border); }
.badge-orange { background: var(--badge-orange-bg); color: var(--badge-orange-color); border: 1px solid var(--badge-orange-border); }
.badge-purple { background: var(--badge-purple-bg); color: var(--badge-purple-color); border: 1px solid var(--badge-purple-border); }

/* ── Inputs ── */
input, textarea, select {
  background: var(--card-bg) !important;
  border: 1px solid var(--input-border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
  padding: 0.6rem 0.85rem !important;
  font-size: 0.9rem !important;
  font-family: inherit !important;
  width: 100% !important;
  resize: vertical !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}
input:focus, textarea:focus, select:focus {
  outline: none !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── Buttons ── */
.btn-primary {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 0.6rem 1.25rem !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 12px var(--accent-glow) !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  transform: none !important;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px) !important;
  filter: brightness(1.1) !important;
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0) !important;
}
.btn-primary:disabled { opacity: 0.4 !important; cursor: not-allowed !important; box-shadow: none !important; }

.btn-ghost {
  background: var(--card-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 0.6rem 1.1rem !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: none !important;
  transform: none !important;
}
.btn-ghost:hover:not(:disabled) {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  transform: translateY(-1px) !important;
}
.btn-ghost:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.75) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  animation: fadeIn 0.25s ease-out;
}
.modal {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important;
  padding: 2rem !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2) !important;
  width: 500px !important;
  max-width: 95vw !important;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  color: var(--text) !important;
  animation: scaleIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.modal h2 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem; color: var(--text); }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem; }

label {
  font-size: 0.78rem;
  font-weight: 700;
  display: block;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.35rem;
  line-height: 1.4;
}

/* ── Cards Overrides ── */
.job-card, .commit-card, .commit-group, .atividade-card, .config-section, .import-box, .story-dashboard {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
  padding: 1.5rem !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
  color: var(--text) !important;
}

.job-card:hover, .commit-card:hover, .atividade-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent) !important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
}

.commit-group-header, .atividade-header {
  border-bottom: 1px solid var(--border) !important;
  background: transparent !important;
  padding-bottom: 0.75rem !important;
}

.commit-group-jobs, .atividade-body {
  padding-top: 1rem !important;
}

.job-row {
  border-bottom: 1px solid var(--border) !important;
  border-left: none !important;
  transition: all 0.2s ease !important;
}
.job-row-running {
  background: var(--accent-glow) !important;
  border-left: 3px solid var(--accent) !important;
}
.job-row-done {
  background: rgba(16, 185, 129, 0.05) !important;
  border-left: 3px solid var(--success) !important;
}
.job-row-error {
  background: rgba(239, 68, 68, 0.05) !important;
  border-left: 3px solid var(--error) !important;
}

.commit-hash-link, .sha-link, .activity-link, .file-chip, .collapse-icon {
  border-radius: 6px !important;
  padding: 3px 8px !important;
  background: var(--bg) !important;
  border: 1px solid var(--border) !important;
  transition: all 0.2s ease !important;
  font-size: 0.8rem !important;
  color: var(--text-muted) !important;
}
.commit-hash-link:hover, .sha-link:hover, .activity-link:hover {
  background: var(--accent-glow) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

.table-wrapper {
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
}

table {
  border-collapse: collapse !important;
  width: 100% !important;
}
th {
  background: var(--bg) !important;
  border-bottom: 1px solid var(--border) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  padding: 0.75rem 1rem !important;
  color: var(--text-muted) !important;
}
td {
  border-bottom: 1px solid var(--border) !important;
  padding: 0.75rem 1rem !important;
  color: var(--text) !important;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.97); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Story dashboard details */
.story-dashboard {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  margin-bottom: 1.5rem !important;
}
.story-step {
  border: 1px solid var(--border) !important;
  background: var(--bg) !important;
  box-shadow: none !important;
  padding: 0.75rem 1.25rem !important;
  border-radius: 10px !important;
  flex: 1 !important;
  max-width: 30% !important;
  opacity: 0.6 !important;
  transition: all 0.3s ease !important;
}
.story-step.active {
  background: var(--accent-glow) !important;
  border: 1px solid var(--accent) !important;
  opacity: 1 !important;
}
.story-step.completed {
  background: rgba(16, 185, 129, 0.08) !important;
  border: 1px solid var(--success) !important;
  opacity: 1 !important;
}
.story-arrow {
  color: var(--text-muted) !important;
  font-weight: 300 !important;
}

.meta-bar {
  background: var(--bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 0.75rem 1.25rem !important;
  margin-bottom: 1.5rem !important;
}
.card-tabs {
  margin-top: 1rem !important;
  border-bottom: 1px solid var(--border) !important;
}
.tab-btn {
  background: transparent !important;
  border: none !important;
  padding: 0.5rem 1rem !important;
  font-weight: 600 !important;
  color: var(--text-muted) !important;
  border-bottom: 2px solid transparent !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}
.tab-btn.active {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
}
</style>
