<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Commits</h1>
        <HelpModal title="Como funciona esta página" :items="helpItems" />
      </div>
      <button class="btn-primary" @click="showImport = true">+ Importar Commit</button>
    </div>

    <!-- Modal de importação -->
    <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
      <div class="modal">
        <h2>Importar Commit do GitLab</h2>
        <label>URL Completa ou SHA do Commit</label>
        <input v-model="form.commit_hash" placeholder="Ex: 082630b1 ou https://gitlab.../commit/..." />
        <div class="modal-actions">
          <button class="btn-ghost" @click="showImport = false">Cancelar</button>
          <button class="btn-primary" :disabled="importing || !form.commit_hash.trim()" @click="importar">
            {{ importing ? 'Importando...' : 'Importar' }}
          </button>
        </div>
        <p v-if="importError" class="error">{{ importError }}</p>
      </div>
    </div>

    <div v-if="store.loading" class="loading">Carregando commits...</div>

    <div v-else-if="store.commits.length === 0" class="empty">
      Nenhum commit importado. Clique em "+ Importar Commit" para começar.
    </div>

    <div v-else class="commit-list">
      <div
        v-for="commit in store.commits"
        :key="commit.id"
        class="commit-card"
        @click="$router.push(`/commits/${commit.id}`)"
      >
        <div class="card-header">
          <span class="commit-sha">{{ commit.id.slice(0, 8) }}</span>
          <div class="card-badges">
            <span class="badge" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
              {{ commit.analisado ? 'Analisado' : 'Pendente' }}
            </span>
            <template v-if="commit.analisado">
              <span class="badge" :class="
                (commit.atividades_enviadas || 0) === (commit.atividades_total || 0) && (commit.atividades_total || 0) > 0
                  ? 'badge-blue'
                  : (commit.atividades_enviadas || 0) > 0
                    ? 'badge-orange'
                    : 'badge-purple'
              ">
                {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
              </span>
              <span class="badge badge-hours">
                {{ (commit.hpa_enviado || 0).toFixed(1) }}h / {{ (commit.hpa_total || 0).toFixed(1) }}h
              </span>
            </template>
          </div>
        </div>

        <div class="commit-msg">{{ commit.mensagem || '(sem mensagem)' }}</div>

        <div v-if="commit.diff_preview" class="diff-preview">
          <div
            v-for="(line, i) in commit.diff_preview.split('\n').filter(l => l.trim())"
            :key="i"
            class="diff-line"
            :class="line.startsWith('+') ? 'diff-add' : 'diff-remove'"
          >{{ line }}</div>
        </div>

        <div class="card-footer">
          <div v-if="commit.analisado && (commit.atividades_total || 0) > 0" class="progress-wrap">
            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: ((commit.atividades_enviadas || 0) / (commit.atividades_total || 1) * 100) + '%' }"
                :class="{ 'completed': commit.atividades_enviadas === commit.atividades_total }"
              ></div>
            </div>
            <span class="progress-pct">
              {{ Math.round((commit.atividades_enviadas || 0) / (commit.atividades_total || 1) * 100) }}%
            </span>
          </div>
          <div class="commit-meta">
            <span>{{ commit.data }}</span>
            <span class="sep">·</span>
            <span>{{ commit.projeto }}</span>
            <span class="sep">·</span>
            <span>{{ commit.autor }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCommitsStore } from '../stores/commits'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Importar Commit', text: 'Clique em "+ Importar Commit" e informe a URL completa do commit no GitLab ou apenas o hash curto (ex: abc123). O sistema baixa automaticamente os metadados e o diff.' },
  { title: 'PRIVATE-TOKEN do GitLab', text: 'Token de acesso pessoal do GitLab. Gere em: GitLab → Preferências → Tokens de Acesso → Escopo "read_repository". Salve na página de Configuração.' },
  { title: 'Status dos commits', text: '"Analisado" (verde) indica que o Gemini processou o diff e gerou atividades de faturamento. "Pendente" (cinza) significa que o commit foi importado mas ainda não foi analisado.' },
]

const store = useCommitsStore()
const showImport = ref(false)
const importing = ref(false)
const importError = ref('')
const form = ref({ commit_hash: '' })

onMounted(async () => {
  await store.fetchCommits()
})

async function importar() {
  importing.value = true
  importError.value = ''
  try {
    const res = await store.importar(form.value.commit_hash)
    showImport.value = false
    form.value.commit_hash = ''
    if (res.ja_existia) alert('Este commit já estava importado.')
  } catch (e: any) {
    importError.value = e.response?.data?.detail ?? String(e)
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.commit-list { display: flex; flex-direction: column; gap: 1rem; }

.commit-card {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: 0;
  cursor: pointer;
  transition: transform 0.12s, box-shadow 0.12s;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.commit-card:hover {
  transform: translateY(-3px) translateX(-3px);
  box-shadow: var(--shadow-hover);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.25rem 0.5rem;
}
.commit-sha {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--text-muted);
  background: rgba(238,238,238,0.05);
  padding: 2px 7px;
  border: 1px solid rgba(238,238,238,0.15);
  letter-spacing: 0.04em;
}
.card-badges { display: flex; gap: 0.4rem; margin-left: auto; flex-wrap: wrap; }
.badge-hours { border: 1px solid rgba(238,238,238,0.25); color: var(--text-muted); font-family: monospace; }

.commit-msg {
  font-weight: 600;
  font-size: 0.97rem;
  padding: 0.3rem 1.25rem 0.75rem;
  line-height: 1.45;
}

.diff-preview {
  background: #0a0a0a;
  border-top: 1px solid rgba(238,238,238,0.1);
  border-bottom: 1px solid rgba(238,238,238,0.1);
  padding: 0.6rem 1.25rem;
  font-family: 'Courier New', monospace;
  font-size: 0.76rem;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.diff-line { white-space: pre; overflow: hidden; text-overflow: ellipsis; }
.diff-add    { color: #3fb950; }
.diff-remove { color: #f85149; }

.card-footer {
  padding: 0.65rem 1.25rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-wrap { display: flex; align-items: center; gap: 0.6rem; }
.progress-track {
  flex: 1;
  height: 5px;
  background: rgba(238,238,238,0.08);
  border: 1px solid rgba(238,238,238,0.18);
  overflow: hidden;
}
.progress-fill { height: 100%; background: var(--accent); transition: width 0.3s ease; }
.progress-fill.completed { background: #3fb950; }
.progress-pct { font-size: 0.72rem; font-weight: 700; color: var(--text-muted); min-width: 2.5rem; text-align: right; }

.commit-meta { display: flex; gap: 0.4rem; font-size: 0.78rem; color: var(--text-muted); flex-wrap: wrap; }
.sep { color: rgba(238,238,238,0.2); }
</style>
