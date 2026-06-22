<template>
  <div class="page">
    <div class="page-header">
      <button class="btn-ghost" @click="$router.back()">← Voltar</button>
      <div class="title-row">
        <h1>{{ commit?.mensagem || sha.slice(0, 8) }}</h1>
        <HelpModal title="Detalhes do Commit" :items="helpItems" />
      </div>
    </div>

    <div v-if="loadingCommit" class="loading">Carregando...</div>

    <template v-else-if="commit">
      <!-- Storytelling Dashboard -->
      <div class="story-dashboard">
        <div class="story-step active">
          <div class="step-icon">📥</div>
          <div class="step-info">
            <span class="step-title">Importado</span>
            <span class="step-desc">Código e diff localizados</span>
          </div>
        </div>
        <div class="story-arrow">➔</div>
        <div class="story-step" :class="{ 'active': commit.analisado }">
          <div class="step-icon">🤖</div>
          <div class="step-info">
            <span class="step-title">Análise AI</span>
            <span class="step-desc" v-if="commit.analisado">{{ commit.atividades_total || 0 }} atividades identificadas</span>
            <span class="step-desc" v-else>Pendente de análise Gemini</span>
          </div>
        </div>
        <div class="story-arrow">➔</div>
        <div class="story-step" :class="{ 
          'active': commit.analisado && (commit.atividades_enviadas || 0) > 0,
          'completed': commit.analisado && commit.atividades_enviadas === commit.atividades_total && (commit.atividades_total || 0) > 0
        }">
          <div class="step-icon">🚀</div>
          <div class="step-info">
            <span class="step-title">Faturamento</span>
            <span class="step-desc" v-if="commit.analisado && (commit.atividades_total || 0) > 0">
              {{ commit.atividades_enviadas || 0 }} de {{ commit.atividades_total || 0 }} enviadas ({{ (commit.hpa_enviado || 0).toFixed(1) }}h / {{ (commit.hpa_total || 0).toFixed(1) }}h)
            </span>
            <span class="step-desc" v-else-if="commit.analisado">Sem atividades faturáveis</span>
            <span class="step-desc" v-else>Aguardando automação</span>
          </div>
        </div>
      </div>

      <!-- Metadados do commit -->
      <div class="meta-bar" :class="{ 'meta-bar-editing': editandoMeta }">
        <template v-if="!editandoMeta">
          <span><b>SHA:</b> {{ commit.id.slice(0, 12) }}</span>
          <span><b>Data:</b> {{ commit.data }}</span>
          <span><b>Projeto:</b> {{ commit.projeto }}</span>
          <span><b>Autor:</b> {{ commit.autor }}</span>
          <button class="btn-ghost btn-sm meta-edit-btn" @click="abrirEditarMeta" title="Editar metadados">✏</button>
        </template>
        <template v-else>
          <div class="meta-edit-form">
            <label>Data</label>
            <input v-model="metaEditavel.data" placeholder="DD/MM/YYYY" style="width: 7.5rem" />
            <label>Projeto</label>
            <input v-model="metaEditavel.projeto" placeholder="grupo/repositorio" style="flex: 1; min-width: 12rem" />
            <label>Autor</label>
            <input v-model="metaEditavel.autor" placeholder="Nome do autor" style="flex: 1; min-width: 10rem" />
            <label>Mensagem</label>
            <input v-model="metaEditavel.mensagem" placeholder="Mensagem do commit" style="flex: 2; min-width: 14rem" />
          </div>
          <div class="meta-edit-actions">
            <button class="btn-primary btn-sm" @click="salvarMeta" :disabled="salvandoMeta">{{ salvandoMeta ? 'Salvando...' : '✓ Salvar' }}</button>
            <button class="btn-ghost btn-sm" @click="cancelarEditarMeta">✗ Cancelar</button>
          </div>
        </template>
      </div>

      <!-- Seção de Análise -->
      <div class="section">
        <div class="section-header">
          <h2>Análise Gemini</h2>
          <div class="section-actions">
            <router-link :to="`/analisar?commit=${sha}`" class="btn-ghost" style="text-decoration: none; display: inline-block;">
              {{ analiseStore.analise ? 'Re-analisar com AI' : 'Analisar com AI' }}
            </router-link>
            <button v-if="analiseStore.analise" class="btn-ghost" :disabled="analiseStore.analisando || enviandoAtividade" @click="salvar">Salvar edições</button>
            <button v-if="analiseStore.analise" class="btn-primary" :disabled="analiseStore.analisando || enviandoAtividade || selecionadas.length === 0" @click="enviarSelecionadas">
              Enviar Selecionadas ({{ selecionadas.length }})
            </button>
            <button v-if="analiseStore.analise" class="btn-primary" :disabled="analiseStore.analisando || enviandoAtividade" @click="enviarTodasFila">
              Enviar Todas ao Munka
            </button>
          </div>
        </div>

        <div v-if="analiseStore.error" class="error">{{ analiseStore.error }}</div>

        <div v-if="analiseStore.analisando" class="loading">Analisando diff com Gemini AI...</div>

        <template v-else-if="analiseStore.analise">
          <div class="complexidade-box">
            <label>Complexidade Global</label>
            <textarea v-model="analiseStore.analise.complexidade_global" rows="3"></textarea>
          </div>

          <!-- Lista de atividades -->
          <div 
            v-for="(atv, idx) in analiseStore.analise.atividades" 
            :key="idx" 
            class="atividade-card"
            :class="{ 'enviada': atv.enviado }"
          >
            <div class="atividade-header">
              <input 
                type="checkbox" 
                :value="idx" 
                v-model="selecionadas" 
                style="width: auto; margin-right: 0.5rem;"
                :disabled="atv.enviado"
              />
              <span class="badge badge-blue">{{ atv.etapa }}</span>
              <span class="atividade-codigo">{{ atv.codigo_id }} · {{ atv.hpa }}h</span>
              <span v-if="atv.enviado" class="badge badge-green" style="margin-left: auto; margin-right: 1rem;">✔ Enviada</span>
              <span v-else class="badge badge-orange" style="margin-left: auto; margin-right: 1rem;">Pendente</span>
              <button
                class="btn-sm"
                :class="atv.enviado ? 'btn-ghost' : 'btn-primary'"
                :disabled="!!enviandoIndividual[idx]"
                @click="enviarUma(idx)"
              >
                {{ enviandoIndividual[idx] ? 'Enfileirando...' : (atv.enviado ? 'Re-enviar' : 'Enviar ao Munka') }}
              </button>
            </div>

            <div class="atividade-body">
              <label>Título</label>
              <input v-model="atv.titulo" />
              <label>Descrição</label>
              <textarea v-model="atv.descricao" rows="3"></textarea>
              <label>Justificativa</label>
              <textarea v-model="atv.justificativa" rows="3"></textarea>
              <label>Categoria</label>
              <input v-model="atv.categoria" />
              <label>Código</label>
              <input v-model="atv.codigo_id" style="width: 6rem" />
              <label>HPA (horas)</label>
              <input v-model.number="atv.hpa" type="number" style="width: 5rem" />
              <label>Arquivos afetados</label>
              <div class="files-list">
                <span v-for="f in atv.arquivos" :key="f" class="file-chip">{{ f }}</span>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="empty">
          Nenhuma análise disponível. Clique em "Analisar com AI".
        </div>
      </div>

      <!-- Diff raw -->
      <details class="section diff-section">
        <summary><h2>Diff do Commit</h2></summary>
        <pre class="diff-raw">{{ commit.diff_raw }}</pre>
      </details>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnaliseStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import { api } from '../api'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Analisar com AI', text: 'Permite selecionar um modelo específico do Gemini para processar as alterações de código e identificar as atividades cobráveis conforme o Catálogo de Serviços.' },
  { title: 'O que são Atividades', text: 'Cada atividade representa uma entrega técnica independente identificada no commit: uma inclusão, alteração ou deleção.' },
  { title: 'HPA (Horas Previstas)', text: 'Horas Previstas para Execução da Atividade — valor definido pelo catálogo de serviços para cada tipo de entrega técnica.' },
  { title: 'Fila de Envios', text: 'Ao clicar para enviar, as atividades entram em uma fila assíncrona. Você pode sair desta página e acompanhar o progresso em tempo real pela aba Fila.' }
]

const route = useRoute()
const router = useRouter()
const sha = route.params.sha as string

const commit = ref<any>(null)
const loadingCommit = ref(true)
const analiseStore = useAnaliseStore()
const filaStore = useFilaStore()

const selecionadas = ref<number[]>([])
const enviandoIndividual = ref<Record<number, boolean>>({})
const enviandoAtividade = ref(false)

const editandoMeta = ref(false)
const salvandoMeta = ref(false)
const metaEditavel = ref({ data: '', projeto: '', autor: '', mensagem: '' })

function abrirEditarMeta() {
  metaEditavel.value = {
    data: commit.value.data,
    projeto: commit.value.projeto,
    autor: commit.value.autor,
    mensagem: commit.value.mensagem,
  }
  editandoMeta.value = true
}

function cancelarEditarMeta() {
  editandoMeta.value = false
}

async function salvarMeta() {
  salvandoMeta.value = true
  try {
    await api.commits.atualizar(sha, metaEditavel.value)
    Object.assign(commit.value, metaEditavel.value)
    editandoMeta.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail ?? 'Erro ao salvar metadados.')
  } finally {
    salvandoMeta.value = false
  }
}

onMounted(async () => {
  try {
    commit.value = await api.commits.obter(sha)
  } finally {
    loadingCommit.value = false
  }
  await analiseStore.fetchAnalise(sha)
})

async function salvar() {
  await analiseStore.salvarAtividades(sha)
  try {
    commit.value = await api.commits.obter(sha)
  } catch {}
  alert('Salvo com sucesso!')
}

async function enviarUma(idx: number) {
  enviandoIndividual.value[idx] = true
  try {
    // Salva as edições do formulário local antes de enfileirar
    await analiseStore.salvarAtividades(sha)
    await filaStore.enfileirarEnvio(sha, idx)
    // Recarrega contadores
    commit.value = await api.commits.obter(sha)
  } catch (err) {
    console.error(err)
  } finally {
    enviandoIndividual.value[idx] = false
  }
}

async function enviarSelecionadas() {
  if (selecionadas.value.length === 0) return
  enviandoAtividade.value = true
  
  try {
    await analiseStore.salvarAtividades(sha)
    
    let sucessos = 0
    for (const idx of selecionadas.value) {
      try {
        await filaStore.enfileirarEnvio(sha, idx)
        sucessos++
      } catch (err) {
        console.error(err)
      }
    }

    if (sucessos > 0) {
      selecionadas.value = []
      router.push('/fila')
    }
  } catch (err) {
    console.error(err)
  } finally {
    enviandoAtividade.value = false
  }
}

async function enviarTodasFila() {
  if (!analiseStore.analise || !analiseStore.analise.atividades.length) return
  enviandoAtividade.value = true
  
  try {
    await analiseStore.salvarAtividades(sha)
    
    const indices = analiseStore.analise.atividades
      .map((atv, i) => ({ atv, idx: i }))
      .filter(item => !item.atv.enviado)
      .map(item => item.idx)

    let targets = indices
    if (targets.length === 0) {
      const confirmar = confirm("Todas as atividades já estão marcadas como enviadas. Deseja re-enviar todas mesmo assim?")
      if (!confirmar) {
        enviandoAtividade.value = false
        return
      }
      targets = analiseStore.analise.atividades.map((_, i) => i)
    }

    let sucessos = 0
    for (const idx of targets) {
      try {
        await filaStore.enfileirarEnvio(sha, idx)
        sucessos++
      } catch (err) {
        console.error(err)
      }
    }

    if (sucessos > 0) {
      router.push('/fila')
    }
  } catch (err) {
    console.error(err)
  } finally {
    enviandoAtividade.value = false
  }
}
</script>


<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.title-row h1 { margin: 0; }

/* ── Storytelling Dashboard ── */
.story-dashboard {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card-bg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  gap: 1rem;
}
.story-step { display: flex; align-items: center; gap: 0.75rem; flex: 1; }
.step-icon { font-size: 1.75rem; opacity: 0.2; transition: opacity 0.2s; }
.story-step.active .step-icon { opacity: 1; }
.story-step.completed .step-icon { opacity: 1; }
.step-info { display: flex; flex-direction: column; }
.step-title { font-weight: 700; font-size: 0.9rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.story-step.active .step-title { color: var(--text); }
.story-step.completed .step-title { color: #3fb950; }
.step-desc { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem; }
.story-arrow { color: var(--accent); font-weight: 900; font-size: 1.1rem; }

/* ── Meta bar ── */
.meta-bar {
  display: flex; flex-wrap: wrap; gap: 1.25rem; align-items: center;
  background: var(--card-bg);
  border: 2px solid var(--border);
  box-shadow: var(--shadow);
  padding: 0.75rem 1rem;
  font-size: 0.85rem; margin-bottom: 1.5rem;
}
.meta-bar-editing { gap: 0.75rem; }
.meta-edit-btn { margin-left: auto; padding: 0.2rem 0.6rem; font-size: 0.8rem; }
.meta-edit-form {
  display: flex; flex-wrap: wrap; gap: 0.4rem 0.75rem; align-items: center; flex: 1;
}
.meta-edit-form input { padding: 0.3rem 0.5rem; font-size: 0.82rem; }
.meta-edit-actions { display: flex; gap: 0.5rem; align-items: center; }

/* ── Sections ── */
.section { margin-bottom: 2rem; }
.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1.25rem;
  border-bottom: 2px solid var(--accent);
  padding-bottom: 0.5rem;
}
.section-header h2 { font-size: 1.1rem; font-weight: 800; letter-spacing: -0.01em; }
.section-actions { display: flex; gap: 0.5rem; }

.complexidade-box { margin-bottom: 1.25rem; }
.complexidade-box textarea { width: 100%; }

/* ── Activity cards ── */
.atividade-card {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: 0;
  margin-bottom: 1rem;
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.atividade-card.enviada {
  border-color: #3fb950;
  box-shadow: 4px 4px 0 #3fb950;
}
.atividade-header {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 2px solid var(--border);
  background: rgba(0,122,204,0.04);
}
.atividade-card.enviada .atividade-header { background: rgba(63,185,80,0.04); }
.atividade-codigo { font-family: monospace; font-size: 0.82rem; color: var(--text-muted); flex: 1; }
.atividade-body { padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.atividade-body input, .atividade-body textarea { width: 100%; }
.files-list { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.file-chip {
  font-family: monospace; font-size: 0.73rem;
  border: 1px solid var(--accent); color: var(--accent);
  padding: 2px 6px;
}

/* ── Diff section ── */
.diff-section summary { cursor: pointer; list-style: none; }
.diff-section summary h2 { display: inline; }
.diff-raw {
  background: #0a0a0a;
  border: 2px solid rgba(238,238,238,0.15);
  padding: 1rem; font-size: 0.78rem; overflow-x: auto; white-space: pre;
  max-height: 500px; overflow-y: auto; margin-top: 0.75rem;
  font-family: 'Courier New', monospace;
}

/* ── Buttons ── */
.btn-sm { padding: 0.3rem 0.75rem; font-size: 0.8rem; }

/* ── Modal terminal ── */
.modal-wide { width: 100%; max-width: 650px; }
.terminal-container {
  background: #0a0a0a;
  border: 2px solid rgba(238,238,238,0.2);
  margin-top: 1rem;
  overflow: hidden;
}
.terminal-header {
  background: rgba(238,238,238,0.04);
  padding: 0.5rem 1rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(238,238,238,0.1);
}
.terminal-body {
  padding: 1rem;
  font-size: 0.8rem;
  font-family: 'Courier New', Courier, monospace;
  max-height: 250px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.terminal-body div.log-line { color: #ccc; }
.terminal-body div.error-line { color: #f85149; }
.terminal-body div.success-line { color: var(--accent); }

.spinner {
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.15);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
