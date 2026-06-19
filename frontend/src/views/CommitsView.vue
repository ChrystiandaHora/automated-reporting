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
      Nenhum commit importado. Clique em "Importar Commit" para começar.
    </div>

    <div v-else class="commit-list">
      <div
        v-for="commit in store.commits"
        :key="commit.id"
        class="commit-card"
        @click="$router.push(`/commits/${commit.id}`)"
      >
        <div class="commit-card-top">
          <span class="badge" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
            {{ commit.analisado ? 'Analisado' : 'Pendente' }}
          </span>
          <template v-if="commit.analisado">
            <span class="badge" :class="(commit.atividades_enviadas || 0) === (commit.atividades_total || 0) && (commit.atividades_total || 0) > 0 ? 'badge-blue' : ((commit.atividades_enviadas || 0) > 0 ? 'badge-orange' : 'badge-purple')">
              {{ commit.atividades_enviadas || 0 }} de {{ commit.atividades_total || 0 }} enviadas
            </span>
            <span class="badge badge-hours">
              {{ (commit.hpa_enviado || 0).toFixed(1) }}h / {{ (commit.hpa_total || 0).toFixed(1) }}h
            </span>
          </template>
          <span class="commit-sha">{{ commit.id.slice(0, 8) }}</span>
        </div>
        <div class="commit-msg">{{ commit.mensagem || '(sem mensagem)' }}</div>
        
        <!-- Barra de Progresso Faturamento -->
        <div v-if="commit.analisado && (commit.atividades_total || 0) > 0" class="progress-container">
          <div 
            class="progress-bar" 
            :style="{ width: ((commit.atividades_enviadas || 0) / (commit.atividades_total || 1) * 100) + '%' }"
            :class="{ 'completed': commit.atividades_enviadas === commit.atividades_total }"
          ></div>
        </div>

        <div class="commit-meta">
          <span>{{ commit.data }}</span>
          <span>{{ commit.projeto }}</span>
          <span>{{ commit.autor }}</span>
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
  { title: 'PRIVATE-TOKEN do GitLab', text: 'Token de acesso pessoal do GitLab. Gere em: GitLab → Preferências → Tokens de Acesso → Escopo "read_repository". Salve na página de Configuração para não precisar preencher toda vez.' },
  { title: 'Caminho do Projeto', text: 'Namespace/nome do repositório no GitLab, exatamente como aparece na URL. Exemplo: para gitlab.suaorganizacao.com/grupo/projeto o caminho é "grupo/projeto".' },
  { title: 'Status dos commits', text: '"Analisado" (verde) indica que o Gemini processou o diff e gerou atividades de faturamento. "Pendente" (cinza) significa que o commit foi importado mas ainda não foi analisado — clique nele para analisar.' },
]

const store = useCommitsStore()
const showImport = ref(false)
const importing = ref(false)
const importError = ref('')

const form = ref({
  commit_hash: '',
})

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
    if (res.ja_existia) {
      alert('Este commit já estava importado.')
    }
  } catch (e: any) {
    importError.value = e.response?.data?.detail ?? String(e)
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.commit-list { display: flex; flex-direction: column; gap: 0.75rem; }
.commit-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
}
.commit-card:hover { border-color: var(--accent); transform: translateY(-1px); }
.commit-card-top { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem; }
.commit-sha { font-family: monospace; font-size: 0.85rem; color: var(--text-muted); margin-left: auto; }
.commit-msg { font-weight: 500; margin-bottom: 0.5rem; }
.commit-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: var(--text-muted); }

/* Progress bar and custom badge styles */
.progress-container {
  width: 100%;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  margin: 0.75rem 0;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}
.progress-bar.completed {
  background: #3fb950;
}
.badge-hours {
  background: rgba(88,166,255,0.06);
  color: var(--text-muted);
  border: 1px dashed var(--border);
  border-radius: 4px;
  font-family: monospace;
}
</style>
