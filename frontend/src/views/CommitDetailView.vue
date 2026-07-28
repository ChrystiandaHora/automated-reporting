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
              Enviar Todas ao Portal
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
                class="atividade-header-checkbox"
                :disabled="atv.enviado"
              />
              <span class="badge badge-blue">{{ atv.etapa }}</span>
              <span class="atividade-codigo">{{ atv.codigo_id }} · {{ atv.hpa }}h</span>
              <span class="atividade-titulo-header" :title="atv.titulo || 'Atividade sem Título'">{{ atv.titulo || 'Atividade sem Título' }}</span>
              <span v-if="atv.enviado && !atv.data_fim_missing" class="badge badge-green" style="margin-left: auto; margin-right: 1.25rem;">✔ Enviada</span>
              <span v-else-if="atv.enviado && atv.data_fim_missing" class="badge badge-orange" style="margin-left: auto; margin-right: 1.25rem;">⚠️ Sem Data Fim</span>
              <span v-else class="badge badge-orange" style="margin-left: auto; margin-right: 1.25rem;">Pendente</span>
              <button
                class="btn-sm"
                :class="(atv.enviado || atv.data_fim_missing) ? 'btn-ghost' : 'btn-primary'"
                :disabled="!!enviandoIndividual[idx]"
                @click="enviarUma(idx)"
              >
                {{ enviandoIndividual[idx] ? 'Enfileirando...' : ((atv.enviado || atv.data_fim_missing) ? 'Re-enviar' : 'Enviar ao Portal') }}
              </button>
            </div>

            <div class="card-tabs">
              <button 
                type="button" 
                class="tab-btn" 
                :class="{ 'active': activeTabs[idx] !== 'preview' }" 
                @click="activeTabs[idx] = 'form'"
              >
                📝 Formulário
              </button>
              <button 
                type="button" 
                class="tab-btn" 
                :class="{ 'active': activeTabs[idx] === 'preview' }" 
                @click="carregarPreview(idx)"
              >
                🔍 Visualizar Evidência
              </button>
            </div>

            <div v-show="activeTabs[idx] !== 'preview'" class="atividade-body">
              <label>Título</label>
              <input v-model="atv.titulo" />
              <label>Descrição</label>
              <textarea v-model="atv.descricao" rows="3"></textarea>
              <label>Justificativa</label>
              <textarea v-model="atv.justificativa" rows="3"></textarea>
              <label>Categoria</label>
              <input v-model="atv.categoria" />
              <label>Código</label>
              <input v-model="atv.codigo_id" @input="recalcularHpa(atv)" style="width: 6rem" />
              <label>HPA (horas)</label>
              <input v-model.number="atv.hpa" type="number" style="width: 5rem" />
              <label>Complexidade</label>
              <select v-model="atv.complexidade" @change="recalcularHpa(atv)" style="width: 8rem">
                <option value="Baixa">Baixa</option>
                <option value="Média">Média</option>
                <option value="Alta">Alta</option>
              </select>
              <label>Arquivos Afetados (Clique em "Visualizar Alterações" para abrir o diff)</label>
              <div class="files-list-interactive">
                <div v-for="f in atv.arquivos" :key="f" class="file-chip-container">
                  <div class="file-chip-row">
                    <span class="file-chip-name">📄 {{ f }}</span>
                    <button 
                      type="button" 
                      class="btn-ghost btn-xs file-diff-btn" 
                      @click="alternarDiffArquivo(idx, f)"
                      :class="{ 'btn-active-diff': exibindoDiff[idx]?.[f] }"
                    >
                      {{ exibindoDiff[idx]?.[f] ? 'Ocultar Diff' : 'Visualizar Alterações' }}
                    </button>
                  </div>
                  <div v-if="exibindoDiff[idx]?.[f]" class="file-diff-preview">
                    <div 
                      v-for="(line, lidx) in obterDiffLinhas(f)" 
                      :key="lidx" 
                      :class="`diff-line diff-line-${line.type}`"
                    >
                      {{ line.text }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="activeTabs[idx] === 'preview'" class="atividade-preview-body">
              <div v-if="loadingPreviews[idx]" class="preview-loading">
                <div class="spinner"></div>
                <span>Gerando pré-visualização...</span>
              </div>
              <div v-else-if="previews[idx]" class="preview-container">
                <div class="preview-header">
                  <div class="preview-header-title">
                    <span class="preview-dot"></span>
                    Pré-visualização da Evidência
                  </div>
                  <div style="display: flex; gap: 0.5rem;">
                    <button type="button" class="btn-ghost btn-sm" @click="copiarEvidencia(idx)" :disabled="!previews[idx]">
                      {{ statusCopia[idx] ? '✅ Copiado!' : '📋 Copiar HTML' }}
                    </button>
                    <button type="button" class="btn-ghost btn-sm" @click="carregarPreview(idx)">🔄 Atualizar</button>
                  </div>
                </div>
                <div class="preview-iframe-wrapper">
                  <iframe 
                    :srcdoc="previews[idx]" 
                    frameborder="0" 
                    width="100%" 
                    scrolling="no"
                    @load="ajustarAlturaIframe($event)"
                    class="preview-iframe"
                  ></iframe>
                </div>
              </div>
              <div v-else class="preview-error">
                <span class="preview-error-icon">⚠️</span>
                <span>Erro ao gerar pré-visualização da evidência.</span>
                <button type="button" class="btn-primary btn-sm" @click="carregarPreview(idx)">🔄 Tentar Novamente</button>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="empty">
          Nenhuma análise disponível. Clique em "Analisar com AI".
        </div>
      </div>

      <!-- Diff raw -->
      <div class="section diff-section">
        <div class="diff-section-header" @click="showCommitDiff = !showCommitDiff">
          <h2>Diff Completo do Commit</h2>
          <span class="collapse-icon-btn">{{ showCommitDiff ? '▼ Ocultar Diff' : '▶ Mostrar Diff' }}</span>
        </div>
        <div v-show="showCommitDiff" class="diff-raw-container">
          <pre class="diff-raw">{{ commit.diff_raw }}</pre>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
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

const activeTabs = ref<Record<number, string>>({})
const previews = ref<Record<number, string>>({})
const loadingPreviews = ref<Record<number, boolean>>({})
const statusCopia = ref<Record<number, boolean>>({})

const showCommitDiff = ref(false)
const exibindoDiff = ref<Record<number, Record<string, boolean>>>({})

function alternarDiffArquivo(taskIdx: number, filePath: string) {
  if (!exibindoDiff.value[taskIdx]) {
    exibindoDiff.value[taskIdx] = {}
  }
  exibindoDiff.value[taskIdx][filePath] = !exibindoDiff.value[taskIdx][filePath]
}

function obterDiffArquivo(filePath: string): string {
  if (!commit.value || !commit.value.diff_raw) return ''
  const diffCompleto = commit.value.diff_raw
  const linhas = diffCompleto.split('\n')
  let capturando = false
  const trecho: string[] = []
  const caminhoNormalizado = filePath.replace(/\\/g, '/')
  
  for (const linha of linhas) {
    if (linha.startsWith('diff --git')) {
      if (capturando) break
      if (linha.includes(caminhoNormalizado)) {
        capturando = true
        trecho.push(linha)
      }
    } else if (capturando) {
      trecho.push(linha)
    }
  }
  return trecho.join('\n')
}

function obterDiffLinhas(filePath: string) {
  const diffText = obterDiffArquivo(filePath)
  if (!diffText) return [{ type: 'info', text: 'Sem alterações ou arquivo não encontrado no diff.' }]
  return diffText.split('\n').map(line => {
    if (line.startsWith('+') && !line.startsWith('+++')) {
      return { type: 'add', text: line }
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      return { type: 'del', text: line }
    } else if (line.startsWith('@@')) {
      return { type: 'hunk', text: line }
    } else if (line.startsWith('diff') || line.startsWith('index') || line.startsWith('---') || line.startsWith('+++')) {
      return { type: 'meta', text: line }
    } else {
      return { type: 'normal', text: line }
    }
  })
}

async function copiarEvidencia(idx: number) {
  const htmlContent = previews.value[idx]
  if (!htmlContent) return
  try {
    await navigator.clipboard.writeText(htmlContent)
    statusCopia.value[idx] = true
    setTimeout(() => {
      statusCopia.value[idx] = false
    }, 2000)
  } catch (err) {
    console.error('Falha ao copiar:', err)
    alert('Não foi possível copiar o HTML automaticamente.')
  }
}

async function carregarPreview(idx: number) {
  activeTabs.value[idx] = 'preview'
  loadingPreviews.value[idx] = true
  try {
    const atv = analiseStore.analise?.atividades?.[idx]
    if (!atv) throw new Error('Atividade não encontrada')
    const res = await api.analise.previewEvidencia(sha, atv, commit.value?.projeto)
    previews.value[idx] = res.html
  } catch (err) {
    console.error(err)
    previews.value[idx] = ''
  } finally {
    loadingPreviews.value[idx] = false
  }
}

function ajustarAlturaIframe(event: Event) {
  const iframe = event.target as HTMLIFrameElement
  if (iframe && iframe.contentWindow) {
    const doc = iframe.contentDocument || iframe.contentWindow.document
    if (doc && doc.documentElement) {
      setTimeout(() => {
        iframe.style.height = doc.documentElement.scrollHeight + 'px'
      }, 50)
    }
  }
}

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

function obterHpaPorCodigoEComplexidade(codigoId: string, complexidade: string): number | null {
  const code = codigoId.trim().toLowerCase()
  const comp = complexidade || 'Baixa'
  
  if (code === '1') return comp === 'Baixa' ? 24 : comp === 'Média' ? 32 : 40
  if (code === '2') return comp === 'Baixa' ? 5 : comp === 'Média' ? 11 : 17
  if (code === '51') return comp === 'Baixa' ? 5 : comp === 'Média' ? 11 : 16
  if (code === '5') return comp === 'Baixa' ? 22 : comp === 'Média' ? 29 : 36
  if (code === '55') return 8
  if (code === '56a') return 14
  if (code === '56b') return 8
  if (code === '56c') return 2
  if (code === '56d') return 4
  if (code === '6') return 2
  if (code === '7') return 1
  if (code === '8') return 22
  if (code === '9a') return 22
  if (code === '9b') return 10
  if (code === '10') return 1
  if (code === '11') return 1

  if (code === '14') return comp === 'Baixa' ? 11 : comp === 'Média' ? 14 : 17
  if (code === '15') return comp === 'Baixa' ? 8 : comp === 'Média' ? 10 : 12
  if (code === '16') return 6
  if (code === '57') return comp === 'Baixa' ? 5 : comp === 'Média' ? 6 : 8
  if (code === '58') return comp === 'Baixa' ? 4 : comp === 'Média' ? 5 : 6
  if (code === '59a') return 4
  if (code === '59b') return 10
  if (code === '60') return comp === 'Baixa' ? 2 : comp === 'Média' ? 3 : 4
  if (code === '61') return comp === 'Baixa' ? 1 : comp === 'Média' ? 2 : 4
  if (code === '62a') return 2
  if (code === '62b') return 3
  if (code === '63') return 8

  if (code === '21a') return 4
  if (code === '21b') return 1
  if (code === '21c') return 1
  if (code === '21d') return 2
  if (code === '21e') return 2
  if (code === '21f') return 1
  if (code === '21g') return 4
  if (code === '21h') return 1

  if (code === '22a') return 4
  if (code === '22b') return 1
  if (code === '23a') return 8
  if (code === '23b') return 2
  if (code === '24a') return 6
  if (code === '24b') return 2
  if (code === '25a') return 4
  if (code === '25b') return 2
  if (code === '26') return 4
  if (code === '28') return 24
  if (code === '29') return 4

  if (code === '30') return 6
  if (code === '31') return 1
  if (code === '32') return 1
  if (code === '33') return comp === 'Baixa' ? 8 : comp === 'Média' ? 16 : 36
  if (code === '35') return 6

  if (code === '39') return 2
  if (code === '40') return 4
  if (code === '42') return 36
  if (code === '43') return 0.10

  if (code === '44a') return 2
  if (code === '44b') return 1
  if (code === '45a') return 4
  if (code === '45b') return 1
  if (code === '46') return 2

  if (code === '64') return 2
  if (code === '65') return 0.5
  if (code === '66') return 1
  if (code === '67') return 0.25
  if (code === '68') return 0.25
  if (code === '69') return 0.25
  if (code === '70') return 0.5

  if (code === '71') return 1
  if (code === '72') return 1
  if (code === '73') return 1
  if (code === '74') return 1
  if (code === '75') return 1
  if (code === '76') return 1
  if (code === '77') return comp === 'Baixa' ? 5 : comp === 'Média' ? 10 : 20

  return null
}

function recalcularHpa(atv: any) {
  if (atv.codigo_id && atv.complexidade) {
    const valorHpa = obterHpaPorCodigoEComplexidade(atv.codigo_id, atv.complexidade)
    if (valorHpa !== null) {
      atv.hpa = valorHpa
    }
  }
}

let timerCheckDataFim: any = null

async function executarChecagemDataFim() {
  if (!sha || !analiseStore.analise || !analiseStore.analise.atividades) return
  try {
    const res = await api.commits.verificarDataFim(sha)
    if (res && res.atividades) {
      const statusMap = new Map(res.atividades.map(a => [a.titulo, a]))
      for (const atv of analiseStore.analise.atividades) {
        const st = statusMap.get(atv.titulo)
        if (st) {
          atv.enviado = st.enviado
          atv.data_fim_missing = st.data_fim_missing
        }
      }
    }
  } catch (e) {
    console.error('Erro na checagem periódica de data_fim:', e)
  }
}

onMounted(async () => {
  try {
    commit.value = await api.commits.obter(sha)
  } finally {
    loadingCommit.value = false
  }
  await analiseStore.fetchAnalise(sha)
  await executarChecagemDataFim()

  timerCheckDataFim = setInterval(async () => {
    await executarChecagemDataFim()
  }, 30000)
})

onUnmounted(() => {
  if (timerCheckDataFim) {
    clearInterval(timerCheckDataFim)
    timerCheckDataFim = null
  }
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
  border: 1px solid var(--card-border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  gap: 1rem;
  border-radius: 12px;
}
.story-step { display: flex; align-items: center; gap: 0.75rem; flex: 1; }
.step-icon { font-size: 1.9rem; opacity: 0.4; transition: opacity 0.3s, transform 0.3s; }
.story-step.active .step-icon { opacity: 1; transform: scale(1.05); }
.story-step.completed .step-icon { opacity: 1; }
.step-info { display: flex; flex-direction: column; }
.step-title {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.story-step.active .step-title { color: #fff; }
.story-step.completed .step-title { color: #4ade80; }
.step-desc {
  font-size: 0.82rem;
  color: var(--text-subtle, #9ca3af);
  margin-top: 0.2rem;
  line-height: 1.4;
}
.story-step.active .step-desc { color: var(--text-muted); }
.story-arrow { color: var(--accent-light); font-weight: 900; font-size: 1.1rem; opacity: 0.7; }

/* ── Meta bar ── */
.meta-bar {
  display: flex; flex-wrap: wrap; gap: 1.25rem; align-items: center;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 10px;
  padding: 0.875rem 1.25rem;
  font-size: 0.88rem;
  margin-bottom: 1.5rem;
  color: var(--text-muted);
  line-height: 1.5;
}
.meta-bar b { color: var(--text); font-weight: 700; }
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
  border-bottom: 2px solid rgba(59, 130, 246, 0.5);
  padding-bottom: 0.75rem;
}
.section-header h2 { font-size: 1.15rem; font-weight: 800; letter-spacing: -0.01em; color: #fff; }
.section-actions { display: flex; gap: 0.5rem; }

.complexidade-box { margin-bottom: 1.25rem; }
.complexidade-box textarea { width: 100%; }

/* ── Activity cards ── */
.atividade-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  margin-bottom: 1.25rem;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s;
}
.atividade-card:hover {
  border-color: rgba(96, 165, 250, 0.35);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}
.atividade-card.enviada {
  border-color: rgba(34, 197, 94, 0.4);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.08);
}
.atividade-card.enviada:hover {
  border-color: rgba(34, 197, 94, 0.6);
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.12);
}
.atividade-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--card-border);
  background: rgba(255, 255, 255, 0.02);
}
.atividade-card.enviada .atividade-header {
  background: rgba(34, 197, 94, 0.04);
}
.atividade-header-checkbox {
  all: revert !important;
  width: 18px !important;
  height: 18px !important;
  margin: 0 !important;
  cursor: pointer !important;
  accent-color: var(--accent-light) !important;
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
}
.atividade-codigo {
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 600;
  white-space: nowrap;
}
.atividade-titulo-header {
  font-size: 0.9rem;
  font-weight: 600;
  color: #fff;
  margin-left: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
  flex: 1;
}
.atividade-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}
.atividade-body input, .atividade-body textarea { width: 100%; }

/* ── Interactive File Diff ── */
.files-list-interactive {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.35rem;
}
.file-chip-container {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.015);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
}
.file-chip-container:hover {
  border-color: rgba(96, 165, 250, 0.2);
  background: rgba(255, 255, 255, 0.03);
}
.file-chip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
}
.file-chip-name {
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  color: #c1c7d4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}
.file-diff-btn {
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  padding: 2px 8px !important;
  border-radius: 4px !important;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-active-diff {
  background: rgba(96, 165, 250, 0.12) !important;
  border-color: rgba(96, 165, 250, 0.3) !important;
  color: #93c5fd !important;
}
.file-diff-preview {
  background: #03050a;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 0.5rem 0.75rem;
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 250px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.diff-line {
  white-space: pre;
  padding: 1px 4px;
  border-radius: 2px;
  line-height: 1.4;
}
.diff-line-add {
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
}
.diff-line-del {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
}
.diff-line-hunk {
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
  font-weight: 600;
}
.diff-line-meta {
  color: #a78bfa;
  font-weight: 600;
}
.diff-line-normal {
  color: #d1d5db;
}
.diff-line-info {
  color: var(--text-muted);
  font-style: italic;
  padding: 0.5rem 0;
}

/* ── Diff section ── */
.diff-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  margin-top: 1.5rem;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}
.diff-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--card-border);
  transition: background 0.2s;
}
.diff-section-header:hover {
  background: rgba(96, 165, 250, 0.04);
}
.diff-section-header h2 {
  font-size: 1.15rem;
  font-weight: 800;
  color: #fff;
  margin: 0;
}
.collapse-icon-btn {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--accent-light);
  background: rgba(96, 165, 250, 0.08);
  border: 1px solid rgba(96, 165, 250, 0.2);
  padding: 4px 10px;
  border-radius: 6px;
}
.diff-raw-container {
  padding: 1rem;
  background: #03050a;
}
.diff-raw {
  margin: 0;
  font-size: 0.78rem;
  overflow-x: auto;
  white-space: pre;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  color: #d1d5db;
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

/* ── Card Tabs styling ── */
.card-tabs {
  display: flex;
  background: rgba(238, 238, 238, 0.02);
  border-bottom: 2px solid var(--border);
}
.tab-btn {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  padding: 0.5rem 1.25rem;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  border-radius: 0;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.tab-btn:hover {
  background: rgba(238, 238, 238, 0.05);
  color: var(--text);
}
.tab-btn.active {
  border-bottom-color: var(--accent);
  color: var(--text);
  background: rgba(0, 122, 204, 0.04);
}

.atividade-preview-body {
  padding: 1.25rem;
  background: transparent;
  border-top: 1px solid var(--card-border);
}
.preview-loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  padding: 3rem 2rem;
  justify-content: center;
  background: rgba(255, 255, 255, 0.01);
  border-radius: 10px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}
.preview-container {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
  padding: 0.625rem 0.875rem;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(96, 165, 250, 0.2);
  border-radius: 8px;
}
.preview-header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #93c5fd;
  font-weight: 700;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.preview-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-light);
  display: inline-block;
  box-shadow: 0 0 6px rgba(96, 165, 250, 0.6);
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.preview-iframe-wrapper {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  background: #ffffff;
}
.preview-iframe {
  border: none;
  background: #ffffff;
  width: 100%;
  min-height: 200px;
  display: block;
}
.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.875rem;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
  background: rgba(239, 68, 68, 0.04);
  border: 1px dashed rgba(239, 68, 68, 0.2);
  border-radius: 10px;
}
.preview-error-icon {
  font-size: 2rem;
  opacity: 0.7;
}
</style>
