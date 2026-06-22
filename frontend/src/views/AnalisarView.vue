<template>
  <div class="page">
    <div class="page-header">
      <button class="btn-ghost btn-sm" @click="$router.back()">← Voltar</button>
      <div class="title-row">
        <h1>Análise de Commits</h1>
      </div>
    </div>

    <!-- Seção 1: Seleção de Modelo -->
    <div class="section">
      <div class="section-title">
        <span class="step-badge">1</span>
        <h2>Selecione o Modelo de AI</h2>
      </div>
      
      <div class="model-grid">
        <div 
          v-for="model in models" 
          :key="model.name" 
          class="model-card"
          :class="{ 'selected': selectedModel === model.name }"
          @click="selectedModel = model.name"
        >
          <div class="model-header">
            <span class="model-badge" :class="model.badgeClass">{{ model.badge }}</span>
            <h3>{{ model.name }}</h3>
          </div>
          <p class="model-desc">{{ model.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Seção 2: Seleção de Commits -->
    <div class="section">
      <div class="section-title">
        <span class="step-badge">2</span>
        <h2>Selecione os Commits para Análise</h2>
      </div>

      <div v-if="commitsStore.loading" class="loading">Carregando commits...</div>
      <div v-else-if="commitsStore.commits.length === 0" class="empty">
        Nenhum commit importado encontrado.
      </div>
      
      <div v-else class="table-container">
        <table class="commit-table">
          <thead>
            <tr>
              <th width="40">
                <input 
                  type="checkbox" 
                  :checked="todosSelecionados" 
                  @change="alternarTodos" 
                />
              </th>
              <th>SHA / Mensagem</th>
              <th>Projeto</th>
              <th>Data</th>
              <th width="100">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="commit in commitsStore.commits" 
              :key="commit.id"
              :class="{ 'row-selected': selecionados.includes(commit.id) }"
              @click="toggleSelecionado(commit.id)"
            >
              <td>
                <input 
                  type="checkbox" 
                  :value="commit.id" 
                  v-model="selecionados"
                  @click.stop
                />
              </td>
              <td class="col-msg">
                <span class="commit-hash">{{ commit.id.slice(0, 8) }}</span>
                <span class="commit-msg-text" :title="commit.mensagem">{{ commit.mensagem || '(sem mensagem)' }}</span>
              </td>
              <td>{{ commit.projeto }}</td>
              <td class="col-date">{{ commit.data }}</td>
              <td>
                <span class="badge" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
                  {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Seção 3: Ações -->
    <div class="action-footer" v-if="selecionados.length > 0">
      <div class="footer-info">
        <strong>{{ selecionados.length }}</strong> commit(s) selecionado(s) para análise com <strong>{{ selectedModel }}</strong>.
      </div>
      <button 
        class="btn-primary" 
        :disabled="enfileirando" 
        @click="confirmarAnalise"
      >
        {{ enfileirando ? 'Enfileirando...' : 'Confirmar e Enfileirar' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'

const router = useRouter()
const route = useRoute()
const commitsStore = useCommitsStore()
const filaStore = useFilaStore()

const selectedModel = ref('Gemini 2.5 Flash')
const selecionados = ref<string[]>([])
const enfileirando = ref(false)

const models = [
  { name: 'Gemini 2.5 Flash', badge: 'Recomendado', badgeClass: 'badge-blue', desc: 'Melhor equilíbrio entre velocidade, inteligência e custo. Ideal para a maioria dos commits.' },
  { name: 'Gemini 3.5 Flash', badge: 'Alta Performance', badgeClass: 'badge-purple', desc: 'Modelo topo de linha mais recente. Máxima precisão na classificação de atividades.' },
  { name: 'Gemini 2.5 Flash Lite', badge: 'Super Rápido', badgeClass: 'badge-green', desc: 'Mais leve e veloz. Indicado para análises rápidas em commits de baixa complexidade.' },
  { name: 'Gemini 3 Flash', badge: 'Nova Geração', badgeClass: 'badge-orange', desc: 'Próxima geração com raciocínio apurado.' },
  { name: 'Gemini 3.1 Flash Lite', badge: 'Ultra Eficiente', badgeClass: 'badge-gray', desc: 'Modelo compacto de última geração com alta eficiência operacional.' }
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

const todosSelecionados = computed(() => {
  return commitsStore.commits.length > 0 && selecionados.value.length === commitsStore.commits.length
})

function alternarTodos() {
  if (todosSelecionados.value) {
    selecionados.value = []
  } else {
    selecionados.value = commitsStore.commits.map(c => c.id)
  }
}

function toggleSelecionado(id: string) {
  const index = selecionados.value.indexOf(id)
  if (index === -1) {
    selecionados.value.push(id)
  } else {
    selecionados.value.splice(index, 1)
  }
}


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
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.section { margin-bottom: 2.5rem; }
.section-title { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; }
.step-badge {
  background: var(--accent);
  color: var(--bg);
  border: 2px solid var(--border);
  font-weight: 900;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
}
.section-title h2 { font-size: 1.15rem; font-weight: 800; }

/* Grid de modelos */
.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}
.model-card {
  background: var(--card-bg);
  border: 2px solid var(--border);
  padding: 1.25rem;
  cursor: pointer;
  box-shadow: 4px 4px 0 rgba(238,238,238,0.1);
  transition: transform 0.12s, box-shadow 0.12s, border-color 0.12s;
}
.model-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 6px 6px 0 rgba(238,238,238,0.2);
}
.model-card.selected {
  border-color: var(--accent);
  box-shadow: 6px 6px 0 var(--accent);
  transform: translateY(-3px) translateX(-3px);
}
.model-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.model-badge {
  font-size: 0.6rem;
}
.model-card h3 { font-size: 0.95rem; font-weight: 800; }
.model-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.4; }

/* Tabela de commits */
.table-container {
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  background: var(--card-bg);
  overflow-x: auto;
}
.commit-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
}
.commit-table th, .commit-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(238,238,238,0.1);
}
.commit-table th {
  background: rgba(238,238,238,0.02);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.04em;
}
.commit-table tbody tr {
  cursor: pointer;
  transition: background 0.1s;
}
.commit-table tbody tr:hover {
  background: rgba(0,122,204,0.03);
}
.commit-table tbody tr.row-selected {
  background: rgba(0,122,204,0.06);
}

.col-msg {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.commit-hash {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--text-muted);
  background: rgba(238,238,238,0.05);
  padding: 1px 5px;
  border: 1px solid rgba(238,238,238,0.1);
}
.commit-msg-text {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 450px;
}
.col-date {
  color: var(--text-muted);
  font-size: 0.8rem;
}

/* Footer de ação fixo na parte inferior */
.action-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--bg);
  border-top: 2px solid var(--border);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  box-shadow: 0 -4px 10px rgba(0,0,0,0.5);
}
.footer-info { font-size: 0.88rem; }
.footer-info strong { color: var(--accent); }

/* Ajusta margem inferior da página por causa do footer fixo */
.page { padding-bottom: 6rem; }
</style>
