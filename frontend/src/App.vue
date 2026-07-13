<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useFilaStore } from './stores/fila'
import { api } from './api'
import ToastManager from './components/ToastManager.vue'

const filaStore = useFilaStore()

const activeJobsCount = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending' || j.status === 'running').length
})

const hasProjectUpdate = ref(false)
const projectBehindCount = ref(0)

async function checarAtualizacaoProjeto() {
  try {
    const res = await api.projeto.verificarAtualizacao()
    hasProjectUpdate.value = res.has_update
    projectBehindCount.value = res.behind_count
  } catch (e) {
    console.error("Falha ao verificar atualizações do projeto:", e)
  }
}

onMounted(() => {
  filaStore.startPolling()
  checarAtualizacaoProjeto()
})

onUnmounted(() => {
  filaStore.stopPolling()
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <span class="brand">
        MUNKA
        <span 
          v-if="hasProjectUpdate" 
          class="project-update-badge" 
          :title="`Nova atualização disponível! ${projectBehindCount} commit(s) atrás. Execute 'git pull' no terminal para atualizar o projeto.`"
        >
          Update {{ projectBehindCount > 0 ? `(${projectBehindCount})` : '' }}
        </span>
      </span>
      <nav class="nav">
        <router-link to="/commits">Commits</router-link>
        <router-link to="/fila">
          Fila
          <span v-if="activeJobsCount > 0" class="fila-badge">{{ activeJobsCount }}</span>
        </router-link>
        <router-link to="/historico">Histórico</router-link>
        <router-link to="/config">Configuração</router-link>
      </nav>
    </header>
    <main class="content">
      <router-view />
    </main>
    <ToastManager />
  </div>
</template>


<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #060913;
  --card-bg: rgba(17, 24, 39, 0.45);
  --card-border: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.05);
  --accent: #2563eb;
  --accent-light: #3b82f6;
  --accent-grad: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  --accent-glow: rgba(59, 130, 246, 0.15);
  --text: #f3f4f6;
  --text-muted: #9ca3af;
  --success: #10b981;
  --error: #ef4444;
  --warning: #f59e0b;
  --topbar-bg: rgba(6, 9, 19, 0.75);
  
  font-family: 'Outfit', 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}

body {
  background: var(--bg);
  background-image: 
    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.04) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.04) 0px, transparent 50%);
  background-attachment: fixed;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.01);
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
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
  border-bottom: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  padding: 0 3rem;
  height: 64px;
  gap: 3rem;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
}

.brand {
  font-weight: 850;
  font-size: 1.3rem;
  color: #fff;
  letter-spacing: -0.03em;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #ffffff 40%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}
.nav a:hover { 
  color: #fff; 
  background: rgba(255, 255, 255, 0.03); 
}
.nav a.router-link-active { 
  background: rgba(59, 130, 246, 0.08);
  color: var(--accent-light);
  border-color: rgba(59, 130, 246, 0.2);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.05);
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
  background: var(--accent-light);
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
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 2.5rem 2rem;
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
  background: linear-gradient(to right, #ffffff, #9ca3af);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.loading, .empty { 
  color: var(--text-muted); 
  padding: 3rem 0; 
  text-align: center;
  font-size: 0.95rem;
}
.error { 
  color: var(--error); 
  font-size: 0.85rem; 
  margin-top: 0.5rem; 
  background: rgba(239, 68, 68, 0.08);
  border-left: 3px solid var(--error);
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
}
.success { color: var(--success); }

/* ── Badges ── */
.badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  display: inline-block;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.badge-green  { background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); }
.badge-gray   { background: rgba(255, 255, 255, 0.04); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.08); }
.badge-blue   { background: rgba(59, 130, 246, 0.1); color: var(--accent-light); border: 1px solid rgba(59, 130, 246, 0.2); }
.badge-orange { background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-purple { background: rgba(139, 92, 246, 0.1); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.2); }

/* ── Inputs ── */
input, textarea, select {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid var(--card-border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
  padding: 0.55rem 0.75rem !important;
  font-size: 0.9rem !important;
  font-family: inherit !important;
  width: 100% !important;
  resize: vertical !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}
input:focus, textarea:focus, select:focus {
  outline: none !important;
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: var(--accent-light) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* ── Buttons ── */
.btn-primary {
  background: var(--accent-grad) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 0.6rem 1.25rem !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.18) !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  transform: none !important;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3) !important;
  filter: brightness(1.1) !important;
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0) !important;
}
.btn-primary:disabled { opacity: 0.4 !important; cursor: not-allowed !important; box-shadow: none !important; }

.btn-ghost {
  background: rgba(255, 255, 255, 0.02) !important;
  color: var(--text) !important;
  border: 1px solid var(--card-border) !important;
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
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
  transform: translateY(-1px) !important;
}
.btn-ghost:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(3, 7, 18, 0.8) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  animation: fadeIn 0.25s ease-out;
}
.modal {
  background: #111827 !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 16px !important;
  padding: 2rem !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 0 1px var(--card-border) !important;
  width: 500px !important;
  max-width: 95vw !important;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: scaleIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.modal h2 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem; }

label {
  font-size: 0.75rem;
  font-weight: 600;
  display: block;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.3rem;
}

/* ── Glow / Glass Cards Overrides ── */
.job-card, .commit-card, .commit-group, .atividade-card, .config-section, .import-box, .story-dashboard {
  background: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  padding: 1.5rem !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.job-card:hover, .commit-card:hover, .atividade-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.3) !important;
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.08), 0 0 0 1px rgba(59, 130, 246, 0.15) !important;
}

/* Specific elements adjustments */
.commit-group-header, .atividade-header {
  border-bottom: 1px solid var(--card-border) !important;
  background: transparent !important;
  padding-bottom: 0.75rem !important;
}

.commit-group-jobs, .atividade-body {
  padding-top: 1rem !important;
}

.job-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
  border-left: none !important;
  transition: all 0.2s ease !important;
}
.job-row-running {
  background: rgba(59, 130, 246, 0.03) !important;
  border-left: 3px solid var(--accent-light) !important;
}
.job-row-done {
  background: rgba(16, 185, 129, 0.02) !important;
  border-left: 3px solid var(--success) !important;
}
.job-row-error {
  background: rgba(239, 68, 68, 0.02) !important;
  border-left: 3px solid var(--error) !important;
}

.commit-hash-link, .sha-link, .activity-link, .file-chip, .collapse-icon {
  border-radius: 6px !important;
  padding: 3px 8px !important;
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  transition: all 0.2s ease !important;
  font-size: 0.8rem !important;
  color: var(--text-muted) !important;
}
.commit-hash-link:hover, .sha-link:hover, .activity-link:hover {
  background: rgba(59, 130, 246, 0.1) !important;
  border-color: rgba(59, 130, 246, 0.25) !important;
  color: var(--accent-light) !important;
}

.table-wrapper {
  border: 1px solid var(--card-border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
}

table {
  border-collapse: collapse !important;
  width: 100% !important;
}
th {
  background: rgba(255, 255, 255, 0.01) !important;
  border-bottom: 1px solid var(--card-border) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  padding: 0.75rem 1rem !important;
}
td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important;
  padding: 0.75rem 1rem !important;
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
  border: none !important;
  background: rgba(255, 255, 255, 0.02) !important;
  box-shadow: none !important;
  padding: 0.75rem 1.25rem !important;
  border-radius: 10px !important;
  flex: 1 !important;
  max-width: 30% !important;
  opacity: 0.6 !important;
}
.story-step.active {
  background: rgba(59, 130, 246, 0.08) !important;
  border: 1px solid rgba(59, 130, 246, 0.25) !important;
  opacity: 1 !important;
}
.story-step.completed {
  background: rgba(16, 185, 129, 0.08) !important;
  border: 1px solid rgba(16, 185, 129, 0.25) !important;
  opacity: 1 !important;
}
.story-arrow {
  color: var(--text-muted) !important;
  font-weight: 300 !important;
}

.meta-bar {
  background: rgba(255, 255, 255, 0.01) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 10px !important;
  padding: 0.75rem 1.25rem !important;
  margin-bottom: 1.5rem !important;
}
.card-tabs {
  margin-top: 1rem !important;
  border-bottom: 1px solid var(--card-border) !important;
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
  color: var(--accent-light) !important;
  border-bottom-color: var(--accent-light) !important;
}
</style>
