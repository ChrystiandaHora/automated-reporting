<template>
  <div>
    <PageHeader>
      <BaseButton @click="$router.back()">← Voltar</BaseButton>
      <div class="flex items-center gap-2">
        <PageTitle>{{ commit?.mensagem || sha.slice(0, 8) }}</PageTitle>
        <TutorialModal screenId="commit-detail" />
      </div>
    </PageHeader>

    <StateMessage v-if="loadingCommit" type="loading">Carregando...</StateMessage>

    <template v-else-if="commit">
      <!-- Storytelling Dashboard -->
      <div class="mb-6 flex items-center justify-between gap-4 rounded-xl border border-border-strong bg-card p-6 text-foreground shadow-card transition-all duration-250 ease-in-out">
        <div :class="classesEtapa(true, false)">
          <div :class="classesIconeEtapa(true)">
            <i class="fa-solid fa-cloud-arrow-down" aria-hidden="true"></i>
          </div>
          <div class="flex flex-col">
            <span :class="classesTituloEtapa(true, false)">Importado</span>
            <span :class="classesDescEtapa(true)">Código e diff localizados</span>
          </div>
        </div>
        <div class="text-lg font-light text-muted-foreground opacity-70">
          <i class="fa-solid fa-arrow-right-long" aria-hidden="true"></i>
        </div>
        <div :class="classesEtapa(etapaAnaliseAtiva, false)">
          <div :class="classesIconeEtapa(etapaAnaliseAtiva)">
            <i class="fa-solid fa-robot" aria-hidden="true"></i>
          </div>
          <div class="flex flex-col">
            <span :class="classesTituloEtapa(etapaAnaliseAtiva, false)">Análise AI</span>
            <span :class="classesDescEtapa(etapaAnaliseAtiva)" v-if="commit.analisado">{{ commit.atividades_total || 0 }} atividades identificadas</span>
            <span :class="classesDescEtapa(etapaAnaliseAtiva)" v-else>Pendente de análise Gemini</span>
          </div>
        </div>
        <div class="text-lg font-light text-muted-foreground opacity-70">
          <i class="fa-solid fa-arrow-right-long" aria-hidden="true"></i>
        </div>
        <div :class="classesEtapa(etapaFaturamentoAtiva, etapaFaturamentoCompleta)">
          <div :class="classesIconeEtapa(etapaFaturamentoAtiva)">
            <i class="fa-solid fa-rocket" aria-hidden="true"></i>
          </div>
          <div class="flex flex-col">
            <span :class="classesTituloEtapa(etapaFaturamentoAtiva, etapaFaturamentoCompleta)">Faturamento</span>
            <span :class="classesDescEtapa(etapaFaturamentoAtiva)" v-if="commit.analisado && (commit.atividades_total || 0) > 0">
              {{ commit.atividades_enviadas || 0 }} de {{ commit.atividades_total || 0 }} enviadas ({{ (commit.hpa_enviado || 0).toFixed(1) }}h / {{ (commit.hpa_total || 0).toFixed(1) }}h)
            </span>
            <span :class="classesDescEtapa(etapaFaturamentoAtiva)" v-else-if="commit.analisado">Sem atividades faturáveis</span>
            <span :class="classesDescEtapa(etapaFaturamentoAtiva)" v-else>Aguardando automação</span>
          </div>
        </div>
      </div>

      <!-- Metadados do commit -->
      <div
        data-tour="commit-detail-metadados"
        class="mb-6 flex flex-wrap items-center rounded-[10px] border border-border-strong bg-background px-5 py-3 text-sm leading-normal text-muted-foreground [&_b]:font-bold [&_b]:text-foreground"
        :class="editandoMeta ? 'gap-3' : 'gap-5'"
      >
        <template v-if="!editandoMeta">
          <span><b>SHA:</b> {{ commit.id.slice(0, 12) }}</span>
          <span><b>Data:</b> {{ commit.data }}</span>
          <span><b>Projeto:</b> {{ commit.projeto }}</span>
          <span><b>Autor:</b> {{ commit.autor }}</span>
          <BaseButton data-tour="commit-detail-editar-metadados" class="ml-auto" @click="abrirEditarMeta" title="Editar metadados" aria-label="Editar metadados">
            <i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>
          </BaseButton>
        </template>
        <template v-else>
          <div class="flex flex-1 flex-wrap items-center gap-x-3 gap-y-1.5">
            <BaseLabel for="meta-data">Data</BaseLabel>
            <BaseInput id="meta-data" v-model="metaEditavel.data" placeholder="DD/MM/YYYY" />
            <BaseLabel for="meta-project">Projeto</BaseLabel>
            <BaseInput id="meta-project" v-model="metaEditavel.projeto" placeholder="grupo/repositorio" class="min-w-48 flex-1" />
            <BaseLabel for="meta-author">Autor</BaseLabel>
            <BaseInput id="meta-author" v-model="metaEditavel.autor" placeholder="Nome do autor" class="min-w-40 flex-1" />
            <BaseLabel for="meta-message">Mensagem</BaseLabel>
            <BaseInput id="meta-message" v-model="metaEditavel.mensagem" placeholder="Mensagem do commit" class="min-w-56 flex-2" />
          </div>
          <div class="flex items-center gap-2">
            <BaseButton variant="primary" @click="salvarMeta" :disabled="salvandoMeta">
              <i class="fa-solid fa-check" aria-hidden="true"></i>
              <span>{{ salvandoMeta ? 'Salvando...' : 'Salvar' }}</span>
            </BaseButton>
            <BaseButton @click="cancelarEditarMeta">
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              <span>Cancelar</span>
            </BaseButton>
          </div>
        </template>
      </div>

      <!-- Seção de Análise -->
      <div class="mb-8">
        <div class="mb-5 flex items-center justify-between border-b-2 border-blue-500/50 pb-3">
          <h2 class="text-lg font-extrabold tracking-tight text-foreground">Análise Gemini</h2>
          <div class="flex gap-2">
            <router-link :to="`/analisar?commit=${sha}`" :class="classesLinkGhost">
              {{ analiseStore.analise ? 'Re-analisar com AI' : 'Analisar com AI' }}
            </router-link>
            <BaseButton v-if="analiseStore.analise" :disabled="analiseStore.analisando || enviandoAtividade" @click="salvar">Salvar edições</BaseButton>
            <BaseButton v-if="analiseStore.analise" variant="primary" :disabled="analiseStore.analisando || enviandoAtividade || selecionadas.length === 0" @click="enviarSelecionadas">
              Enviar Selecionadas ({{ selecionadas.length }})
            </BaseButton>
            <BaseButton v-if="analiseStore.analise" variant="primary" :disabled="analiseStore.analisando || enviandoAtividade" @click="enviarTodasFila">
              Enviar Todas ao Portal
            </BaseButton>
          </div>
        </div>

        <StateMessage v-if="analiseStore.error" type="error">{{ analiseStore.error }}</StateMessage>

        <StateMessage v-if="analiseStore.analisando" type="loading">Analisando diff com Gemini AI...</StateMessage>

        <template v-else-if="analiseStore.analise">
          <div class="mb-5">
            <BaseLabel for="global-complexity">Complexidade Global</BaseLabel>
            <BaseTextarea id="global-complexity" v-model="analiseStore.analise.complexidade_global" rows="3" />
          </div>

          <!-- Lista de atividades -->
          <div 
            v-for="(atv, idx) in analiseStore.analise.atividades" 
            :key="idx" 
            data-tour="commit-detail-atividade"
            class="mb-5 overflow-hidden rounded-xl border border-border-strong bg-card p-6 text-foreground shadow-card transition-all duration-250 ease-in-out hover:-translate-y-px hover:border-primary hover:shadow-[0_8px_25px] hover:shadow-black/8"
          >
            <div data-tour="commit-detail-atividade-cabecalho" class="flex items-center gap-4 border-b border-border-strong bg-transparent px-6 pt-4 pb-3">
              <input 
                type="checkbox" 
                :value="idx" 
                v-model="selecionadas" 
                :id="'atv-check-' + idx"
                class="size-4.5 cursor-pointer accent-primary-light disabled:cursor-not-allowed"
                :disabled="atv.enviado"
                :aria-label="'Selecionar atividade: ' + (atv.titulo || 'Atividade sem Título')"
              />
              <BaseBadge variant="blue">{{ atv.etapa }}</BaseBadge>
              <span class="whitespace-nowrap font-courier text-[0.85rem] font-semibold text-muted-foreground">{{ atv.codigo_id }} · {{ atv.hpa }}h</span>
              <span class="ml-3 max-w-100 flex-1 truncate text-sm font-semibold text-foreground" :title="atv.titulo || 'Atividade sem Título'">{{ atv.titulo || 'Atividade sem Título' }}</span>
              <BaseBadge v-if="atv.enviado && !atv.data_fim_missing" variant="green" class="ml-auto mr-5">
                <i class="fa-solid fa-check mr-1" aria-hidden="true"></i>Enviada
              </BaseBadge>
              <BaseBadge v-else-if="atv.enviado && atv.data_fim_missing" variant="orange" class="ml-auto mr-5">
                <i class="fa-solid fa-triangle-exclamation mr-1" aria-hidden="true"></i>Sem Data Fim
              </BaseBadge>
              <BaseBadge v-else variant="orange" class="ml-auto mr-5">Pendente</BaseBadge>
              <BaseButton
                :variant="(atv.enviado || atv.data_fim_missing) ? 'ghost' : 'primary'"
                :disabled="!!enviandoIndividual[idx]"
                @click="enviarUma(idx)"
              >
                {{ enviandoIndividual[idx] ? 'Enfileirando...' : ((atv.enviado || atv.data_fim_missing) ? 'Re-enviar' : 'Enviar ao Portal') }}
              </BaseButton>
            </div>

            <div data-tour="commit-detail-abas" class="mt-4 flex border-b border-border-strong bg-white/2" role="tablist" aria-label="Abas de opções da atividade">
              <button 
                type="button" 
                data-tour="commit-detail-aba"
                :class="classesAba(activeTabs[idx] !== 'preview')"
                role="tab"
                :aria-selected="activeTabs[idx] !== 'preview'"
                :aria-controls="'tab-form-' + idx"
                @click="activeTabs[idx] = 'form'"
              >
                <i class="fa-solid fa-file-lines mr-1" aria-hidden="true"></i>
                <span>Formulário</span>
              </button>
              <button 
                type="button" 
                data-tour="commit-detail-aba"
                :class="classesAba(activeTabs[idx] === 'preview')"
                role="tab"
                :aria-selected="activeTabs[idx] === 'preview'"
                :aria-controls="'tab-preview-' + idx"
                @click="carregarPreview(idx)"
              >
                <i class="fa-solid fa-eye mr-1" aria-hidden="true"></i>
                <span>Visualizar Evidência</span>
              </button>
            </div>

            <div v-show="activeTabs[idx] !== 'preview'" :id="'tab-form-' + idx" role="tabpanel" class="flex flex-col gap-2.5 px-5 pt-4 pb-5">
              <BaseLabel :for="'atv-titulo-' + idx">Título</BaseLabel>
              <BaseInput :id="'atv-titulo-' + idx" v-model="atv.titulo" />
              <BaseLabel :for="'atv-desc-' + idx">Descrição</BaseLabel>
              <BaseTextarea :id="'atv-desc-' + idx" v-model="atv.descricao" rows="3" />
              <BaseLabel :for="'atv-just-' + idx">Justificativa</BaseLabel>
              <BaseTextarea :id="'atv-just-' + idx" v-model="atv.justificativa" rows="3" />
              <BaseLabel :for="'atv-cat-' + idx">Categoria</BaseLabel>
              <BaseInput :id="'atv-cat-' + idx" v-model="atv.categoria" />
              <BaseLabel :for="'atv-code-' + idx">Código</BaseLabel>
              <BaseInput :id="'atv-code-' + idx" v-model="atv.codigo_id" @input="recalcularHpa(atv)" />
              <BaseLabel :for="'atv-hpa-' + idx">HPA (horas)</BaseLabel>
              <BaseInput :id="'atv-hpa-' + idx" v-model.number="atv.hpa" type="number" />
              <BaseLabel :for="'atv-comp-' + idx">Complexidade</BaseLabel>
              <BaseSelect :id="'atv-comp-' + idx" v-model="atv.complexidade" @change="recalcularHpa(atv)">
                <option value="Baixa">Baixa</option>
                <option value="Média">Média</option>
                <option value="Alta">Alta</option>
              </BaseSelect>
              <BaseLabel :for="'atv-files-' + idx">Arquivos Afetados (Clique em "Visualizar Alterações" para abrir o diff)</BaseLabel>
              <div :id="'atv-files-' + idx" data-tour="commit-detail-arquivos" class="mt-1.5 flex flex-col gap-2">
                <div
                  v-for="f in atv.arquivos"
                  :key="f"
                  class="flex flex-col overflow-hidden rounded-lg border border-white/5 bg-white/2 transition-all duration-200 hover:border-blue-400/20 hover:bg-white/3"
                >
                  <div class="flex items-center justify-between px-3 py-2">
                    <span class="max-w-4/5 truncate font-courier text-xs text-file-name">
                      <i class="fa-solid fa-file-code mr-1" aria-hidden="true"></i>
                      <span>{{ f }}</span>
                    </span>
                    <BaseButton
                      variant="plain"
                      :class="classesBotaoDiff(!!exibindoDiff[idx]?.[f])"
                      @click="alternarDiffArquivo(idx, f)"
                    >
                      {{ exibindoDiff[idx]?.[f] ? 'Ocultar Diff' : 'Visualizar Alterações' }}
                    </BaseButton>
                  </div>
                  <div v-if="exibindoDiff[idx]?.[f]" class="flex max-h-62.5 flex-col overflow-auto border-t border-white/5 bg-diff-surface px-3 py-2 font-courier text-xs">
                    <div 
                      v-for="(line, lidx) in obterDiffLinhas(f)" 
                      :key="lidx" 
                      :class="classesLinhaDiff[line.type]"
                    >
                      {{ line.text }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="activeTabs[idx] === 'preview'" :id="'tab-preview-' + idx" role="tabpanel" class="border-t border-border bg-transparent p-5">
              <div v-if="loadingPreviews[idx]" class="flex items-center justify-center gap-3 rounded-[10px] border border-dashed border-white/8 bg-white/1 px-8 py-12 text-sm text-muted-foreground">
                <div class="size-3 animate-spin rounded-full border-2 border-white/15 border-t-primary"></div>
                <span>Gerando pré-visualização...</span>
              </div>
              <div v-else-if="previews[idx]" class="flex flex-col gap-3.5">
                <div class="flex items-center justify-between rounded-lg border border-blue-400/20 bg-blue-500/6 px-3.5 py-2.5 text-xs font-semibold text-muted-foreground">
                  <div class="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-blue-300">
                    <span class="inline-block size-1.75 animate-pulse rounded-full bg-primary-light shadow-[0_0_6px] shadow-blue-400/60"></span>
                    Pré-visualização da Evidência
                  </div>
                  <div class="flex gap-2">
                    <BaseButton @click="copiarEvidencia(idx)" :disabled="!previews[idx]">
                      <i :class="statusCopia[idx] ? 'fa-solid fa-check' : 'fa-solid fa-clipboard'" class="mr-1" aria-hidden="true"></i>
                      <span>{{ statusCopia[idx] ? 'Copiado!' : 'Copiar HTML' }}</span>
                    </BaseButton>
                    <BaseButton @click="carregarPreview(idx)">
                      <i class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
                      <span>Atualizar</span>
                    </BaseButton>
                  </div>
                </div>
                <div class="overflow-hidden rounded-[10px] border border-white/12 bg-white shadow-lg shadow-black/40 inset-ring-1 inset-ring-white/4">
                  <iframe 
                    :srcdoc="previews[idx]" 
                    frameborder="0" 
                    width="100%" 
                    scrolling="no"
                    @load="ajustarAlturaIframe($event)"
                    class="block min-h-50 w-full border-0 bg-white"
                    :title="'Pré-visualização da Evidência para Atividade ' + (atv.titulo || idx)"
                  ></iframe>
                </div>
              </div>
              <div v-else class="flex flex-col items-center gap-3.5 rounded-[10px] border border-dashed border-red-500/20 bg-red-500/4 px-8 py-12 text-center text-sm text-muted-foreground">
                <i class="fa-solid fa-triangle-exclamation text-[2rem] opacity-70" aria-hidden="true"></i>
                <span>Erro ao gerar pré-visualização da evidência.</span>
                <BaseButton variant="primary" @click="carregarPreview(idx)">
                  <i class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
                  <span>Tentar Novamente</span>
                </BaseButton>
              </div>
            </div>
          </div>
        </template>

        <StateMessage v-else type="empty">
          Nenhuma análise disponível. Clique em "Analisar com AI".
        </StateMessage>
      </div>

      <!-- Diff raw -->
      <div data-tour="commit-detail-diff" class="mt-6 mb-8 overflow-hidden rounded-xl border border-border bg-card shadow-lg shadow-black/15">
        <div 
          data-tour="commit-detail-diff-cabecalho"
          class="flex items-center justify-between border-b border-border bg-white/2 px-5 py-4 transition-colors duration-200 hover:bg-blue-400/4" 
          @click="showCommitDiff = !showCommitDiff"
          tabindex="0"
          role="button"
          :aria-expanded="showCommitDiff"
          @keydown.enter.prevent="showCommitDiff = !showCommitDiff"
          @keydown.space.prevent="showCommitDiff = !showCommitDiff"
        >
          <h2 class="text-lg font-extrabold text-foreground">Diff Completo do Commit</h2>
          <span class="rounded-md border border-blue-400/20 bg-blue-400/8 px-2.5 py-1 text-xs font-bold text-primary-light">{{ showCommitDiff ? '▼ Ocultar Diff' : '▶ Mostrar Diff' }}</span>
        </div>
        <div v-show="showCommitDiff" class="bg-diff-surface p-4">
          <pre class="max-h-100 overflow-auto whitespace-pre font-courier text-xs text-gray-300">{{ commit.diff_raw }}</pre>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnaliseStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import { api } from '../api'
import TutorialModal from '../components/TutorialModal.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseLabel from '../components/ui/BaseLabel.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import BaseTextarea from '../components/ui/BaseTextarea.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import StateMessage from '../components/ui/StateMessage.vue'

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
const etapaAnaliseAtiva = computed(() => !!commit.value?.analisado)
const etapaFaturamentoAtiva = computed(() => !!commit.value?.analisado && (commit.value?.atividades_enviadas || 0) > 0)
const etapaFaturamentoCompleta = computed(() =>
  !!commit.value?.analisado
  && commit.value?.atividades_enviadas === commit.value?.atividades_total
  && (commit.value?.atividades_total || 0) > 0
)

const etapaBase = 'flex flex-1 items-center gap-3 rounded-[10px] border px-5 py-3 transition-all duration-300 max-w-[30%]'

function classesEtapa(ativa: boolean, completa: boolean) {
  if (completa) return `${etapaBase} border-success bg-success/8 opacity-100`
  return ativa
    ? `${etapaBase} border-primary bg-primary-glow opacity-100`
    : `${etapaBase} border-border-strong bg-background opacity-60`
}

const classesLinkGhost = 'inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-border-strong bg-card px-5 py-2.5 text-[0.88rem] leading-none font-semibold tracking-[0.01em] text-foreground transition-all duration-200 hover:-translate-y-px hover:border-primary hover:text-primary'

const classesAba = (ativa: boolean) =>
  'flex cursor-pointer items-center gap-1.5 rounded-none border-b-2 bg-transparent px-4 py-2 text-xs font-semibold transition-all duration-200 '
  + (ativa ? 'border-primary text-primary' : 'border-transparent text-muted-foreground')

const classesBotaoDiff = (aberto: boolean) =>
  'rounded-sm border px-2 py-0.5 text-[0.72rem] font-bold hover:border-primary hover:text-primary '
  + (aberto ? 'border-blue-400/30 bg-blue-400/12 text-blue-300' : 'border-border-strong bg-card text-foreground')

const classesIconeEtapa = (ativa: boolean) =>
  ativa
    ? 'text-3xl opacity-100 scale-105 transition-[opacity,transform] duration-300'
    : 'text-3xl opacity-40 transition-[opacity,transform] duration-300'

function classesTituloEtapa(ativa: boolean, completa: boolean) {
  if (completa) return 'text-sm font-bold uppercase tracking-wide text-green-400'
  return ativa
    ? 'text-sm font-bold uppercase tracking-wide text-primary'
    : 'text-sm font-bold uppercase tracking-wide text-muted-foreground'
}

const classesDescEtapa = (ativa: boolean) =>
  ativa
    ? 'mt-1 text-sm leading-snug text-foreground'
    : 'mt-1 text-sm leading-snug text-subtle-foreground'

const classesLinhaDiff: Record<string, string> = {
  add: 'whitespace-pre rounded-xs bg-green-500/12 px-1 py-px leading-snug text-green-400',
  del: 'whitespace-pre rounded-xs bg-red-500/12 px-1 py-px leading-snug text-red-400',
  hunk: 'whitespace-pre rounded-xs bg-blue-500/10 px-1 py-px font-semibold leading-snug text-blue-300',
  meta: 'whitespace-pre rounded-xs px-1 py-px font-semibold leading-snug text-violet-400',
  normal: 'whitespace-pre rounded-xs px-1 py-px leading-snug text-gray-300',
  info: 'whitespace-pre rounded-xs py-2 leading-snug italic text-muted-foreground',
}
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
