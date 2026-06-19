<template>
  <div class="app">
    <nav class="sidebar">
      <div class="brand">Munka 2.0</div>
      <router-link to="/commits">Commits</router-link>
      <router-link to="/historico">Histórico</router-link>
      <router-link to="/config">Configuração</router-link>
    </nav>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0e1117;
  --card-bg: #161b22;
  --border: #30363d;
  --accent: #58a6ff;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --sidebar-w: 200px;
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
}

body { background: var(--bg); }

.app { display: flex; min-height: 100vh; }

.sidebar {
  width: var(--sidebar-w);
  background: #0d1117;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 1.5rem 1rem;
  gap: 0.25rem;
  position: fixed;
  top: 0; left: 0; bottom: 0;
}

.brand {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 1.5rem;
  padding: 0 0.5rem;
}

.sidebar a {
  color: var(--text-muted);
  text-decoration: none;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: background 0.15s, color 0.15s;
}

.sidebar a:hover { background: rgba(255,255,255,0.05); color: var(--text); }
.sidebar a.router-link-active { background: rgba(88,166,255,0.12); color: var(--accent); font-weight: 500; }

.content {
  margin-left: var(--sidebar-w);
  flex: 1;
  padding: 2rem;
  max-width: 1100px;
}

/* Shared page styles */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.5rem; font-weight: 700; }

.loading { color: var(--text-muted); padding: 2rem 0; }
.empty { color: var(--text-muted); padding: 2rem 0; }
.error { color: #f85149; font-size: 0.85rem; margin-top: 0.5rem; }

.badge {
  font-size: 0.75rem; font-weight: 600;
  padding: 2px 8px; border-radius: 20px; display: inline-block;
}
.badge-green { background: rgba(63,185,80,0.2); color: #3fb950; }
.badge-gray  { background: rgba(139,148,158,0.2); color: #8b949e; }
.badge-blue  { background: rgba(88,166,255,0.15); color: #58a6ff; }
.badge-orange { background: rgba(240,138,0,0.15); color: #f08a00; }
.badge-purple { background: rgba(188,117,237,0.15); color: #bc75ed; }

/* Inputs / textareas */
input, textarea, select {
  background: #0d1117;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 6px;
  padding: 0.4rem 0.6rem;
  font-size: 0.9rem;
  font-family: inherit;
  width: 100%;
  resize: vertical;
}
input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--accent);
}

/* Buttons */
.btn-primary {
  background: var(--accent);
  color: #0d1117;
  border: none;
  border-radius: 6px;
  padding: 0.45rem 1rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.85; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.45rem 0.9rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-ghost:hover { border-color: var(--text-muted); color: var(--text); }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.modal {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.75rem;
  width: 480px;
  max-width: 95vw;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.modal h2 { margin-bottom: 0.5rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }

label { font-size: 0.85rem; font-weight: 500; display: block; }
</style>
