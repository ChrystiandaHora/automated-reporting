<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useFilaStore } from './stores/fila'
import ToastManager from './components/ToastManager.vue'

const filaStore = useFilaStore()

onMounted(() => {
  filaStore.startPolling()
})

onUnmounted(() => {
  filaStore.stopPolling()
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <span class="brand">MUNKA</span>
      <nav class="nav">
        <router-link to="/commits">Commits</router-link>
        <router-link to="/fila">Fila</router-link>
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
  --bg: #101010;
  --card-bg: #1a1a1a;
  --border: #EEEEEE;
  --accent: #007acc;
  --text: #EEEEEE;
  --text-muted: #777;
  --shadow: 4px 4px 0 #007acc;
  --shadow-hover: 7px 7px 0 #007acc;
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
}

body { background: var(--bg); }

.app { display: flex; flex-direction: column; min-height: 100vh; }

/* ── Topbar ── */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 2px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 2rem;
  height: 56px;
  gap: 2rem;
}

.brand {
  font-weight: 900;
  font-size: 1.1rem;
  color: var(--accent);
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.nav {
  display: flex;
  gap: 0.25rem;
}

.nav a {
  color: var(--text-muted);
  text-decoration: none;
  text-transform: uppercase;
  font-weight: 700;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  padding: 0.3rem 0.75rem;
  border: 2px solid transparent;
  transition: color 0.1s, border-color 0.1s, background 0.1s;
}
.nav a:hover { color: var(--text); border-color: var(--border); }
.nav a.router-link-active { background: var(--accent); color: var(--bg); border-color: var(--border); }

/* ── Content ── */
.content {
  flex: 1;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem;
}

/* ── Shared page ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.75rem;
}
.page-header h1 { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; }

.loading { color: var(--text-muted); padding: 2rem 0; }
.empty   { color: var(--text-muted); padding: 2rem 0; }
.error   { color: #f85149; font-size: 0.85rem; margin-top: 0.5rem; }
.success { color: #3fb950; }

/* ── Badges ── */
.badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 2px;
  display: inline-block;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: transparent;
}
.badge-green  { border: 1px solid #3fb950; color: #3fb950; }
.badge-gray   { border: 1px solid #555; color: #888; }
.badge-blue   { border: 1px solid var(--accent); color: var(--accent); }
.badge-orange { border: 1px solid #f08a00; color: #f08a00; }
.badge-purple { border: 1px solid #bc75ed; color: #bc75ed; }

/* ── Inputs ── */
input, textarea, select {
  background: var(--card-bg);
  border: 2px solid var(--border);
  color: var(--text);
  border-radius: 0;
  padding: 0.4rem 0.6rem;
  font-size: 0.9rem;
  font-family: inherit;
  width: 100%;
  resize: vertical;
}
input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 2px 2px 0 var(--accent);
}

/* ── Buttons ── */
.btn-primary {
  background: var(--accent);
  color: var(--text);
  border: 2px solid var(--border);
  border-radius: 0;
  padding: 0.5rem 1.1rem;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.88rem;
  letter-spacing: 0.02em;
  box-shadow: 3px 3px 0 var(--border);
  transition: transform 0.1s, box-shadow 0.1s;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 5px 5px 0 var(--border);
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-ghost {
  background: transparent;
  color: var(--text);
  border: 2px solid var(--border);
  border-radius: 0;
  padding: 0.5rem 0.9rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--accent);
  transition: transform 0.1s, box-shadow 0.1s, background 0.1s;
}
.btn-ghost:hover:not(:disabled) {
  background: var(--accent);
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 5px 5px 0 var(--accent);
}
.btn-ghost:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: 0;
  padding: 1.75rem;
  box-shadow: 8px 8px 0 var(--accent);
  width: 480px;
  max-width: 95vw;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.modal h2 { font-size: 1.1rem; font-weight: 800; margin-bottom: 0.25rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }

label {
  font-size: 0.75rem;
  font-weight: 700;
  display: block;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}
</style>
