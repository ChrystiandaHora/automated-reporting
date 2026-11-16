<template>
  <div>
    <PageHeader>
      <div class="flex items-center gap-2">
        <PageTitle>Histórico de Envios</PageTitle>
        <TutorialModal screenId="historico" />
        <span v-if="items.length > 0" class="text-xs font-bold text-muted-foreground bg-muted px-2 py-0.75 border border-border-strong rounded-full ml-2 align-middle">
          {{ items.length }} atividade{{ items.length > 1 ? 's' : '' }}
        </span>
      </div>
      <BaseButton size="sm" @click="carregarHistorico()">
        <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
        <span>Atualizar</span>
      </BaseButton>
    </PageHeader>

    <StateMessage v-if="loading" type="loading">Carregando...</StateMessage>

    <StateMessage v-else-if="items.length === 0" type="empty">
      Nenhuma atividade enviada ainda.
    </StateMessage>

    <div v-else>
      <!-- Barra de Filtros e Busca -->
      <FiltersBar data-tour="historico-filtros" role="search" aria-label="Filtros de histórico">
        <SearchBox
          v-model="termoBusca"
          data-tour="historico-busca"
          placeholder="Buscar por título, código, autor ou commit..."
          ariaLabel="Buscar atividades no histórico"
        />

        <div class="inline-flex flex-wrap items-center gap-1.5" role="group" aria-label="Filtrar por status">
          <PillButton :active="filtroStatus === 'todos'" @click="filtroStatus = 'todos'">
            Todas ({{ items.length }})
          </PillButton>
          <PillButton :active="filtroStatus === 'concluidas'" @click="filtroStatus = 'concluidas'">
            <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
            <span>Concluídas ({{ totalConcluidas }})</span>
          </PillButton>
          <PillButton :active="filtroStatus === 'sem_data'" @click="filtroStatus = 'sem_data'">
            <i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
            <span>Sem Data Fim ({{ totalSemDataFim }})</span>
          </PillButton>
        </div>
      </FiltersBar>

      <!-- Estado sem resultados nos filtros -->
      <StateMessage v-if="itemsFiltrados.length === 0" type="empty">
        <p>Nenhuma atividade encontrada para os filtros selecionados.</p>
        <BaseButton size="sm" class="mt-2" @click="limparFiltros">
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
          <span>Limpar Filtros</span>
        </BaseButton>
      </StateMessage>

      <div v-else data-tour="historico-lista" class="flex flex-col gap-6 mt-4">
      <!-- Percorre os dias agrupados por data (data do commit ou envio) -->
      <div v-for="grupo in historicoAgrupado" :key="grupo.data" class="flex flex-col">
        
        <!-- Cabeçalho do dia: "23 Jun, 2026 - 3 atividades" -->
        <div data-tour="historico-grupo-cabecalho" class="flex items-baseline gap-2 px-5 py-3 bg-muted border border-border border-b-0 rounded-t-[10px] text-sm">
          <span class="font-extrabold text-foreground text-base">{{ grupo.data }}</span>
          <span class="text-muted-foreground text-sm font-medium">{{ grupo.items.length }} atividade{{ grupo.items.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Lista de atividades enviadas desse dia -->
        <div data-tour="historico-grupo-itens" class="border border-border border-t-0 bg-card flex flex-col rounded-b-[10px] overflow-hidden">
          <div 
            v-for="item in grupo.items" 
            :key="item.id" 
            class="flex items-center px-5 py-3.5 border-b border-border-strong transition-colors duration-150 last:border-b-0 hover:bg-primary-glow"
          >
            <!-- Lado Esquerdo: Avatar do Autor do Commit -->
            <div 
              class="size-9 rounded-full text-white flex items-center justify-center text-xs font-extrabold mr-4 shrink-0 border border-border-strong text-shadow-[0_1px_2px] text-shadow-black/40" 
              :class="obterClasseAvatar(item.commit_autor || 'Sistema')"
              :title="item.commit_autor || 'Autor não informado'"
            >
              {{ obterIniciais(item.commit_autor || 'SI') }}
            </div>

            <!-- Centro: Título da atividade, Badges e Informações do Commit -->
            <div class="flex flex-col gap-1 flex-1 min-w-0">
              <div class="flex items-center gap-3 flex-wrap">
                <span class="text-base font-bold text-foreground truncate max-w-112.5" :title="item.titulo">
                  {{ item.titulo }}
                </span>
                
                <!-- Badges: Código, HPA e Status -->
                <div class="flex items-center gap-1.5 flex-wrap">
                  <BaseBadge variant="plain"><code class="text-xs border border-badge-code-border text-badge-code-foreground bg-badge-code px-1.25 py-px font-courier rounded">{{ item.codigo }}</code></BaseBadge>
                  <span class="font-courier font-bold text-badge-hpa-foreground bg-badge-hpa border border-badge-hpa-border px-1.5 py-px text-xs rounded-md">{{ item.hpa }}h</span>
                  <BaseBadge :variant="item.tem_data_fim === false || item.status?.includes('Sem Data Fim') || item.status?.includes('Incompleta') ? 'orange' : 'green'">
                    <i v-if="item.tem_data_fim === false" class="fa-solid fa-triangle-exclamation mr-1" aria-hidden="true"></i>
                    {{ item.tem_data_fim === false ? 'Sem Data Fim' : item.status }}
                  </BaseBadge>
                </div>
              </div>

              <div class="flex items-center gap-4 text-xs text-muted-foreground">
                <span v-if="item.commit_mensagem" class="truncate max-w-87.5 text-muted-foreground" :title="item.commit_mensagem">
                  Commit: {{ item.commit_mensagem }}
                </span>
                <span class="text-xs text-muted-foreground">
                  Enviado {{ obterTempoRelativo(item.enviado_em) }} ({{ formatDate(item.enviado_em) }})
                </span>
              </div>
            </div>

            <!-- Lado Direito: Link para o Commit e Ações -->
            <div data-tour="historico-acoes" class="flex items-center gap-2 shrink-0 ml-4" @click.stop>
              <!-- SHA Box Link -->
              <router-link 
                v-if="item.commit_id" 
                :to="`/commits/${item.commit_id}`" 
                data-tour="historico-sha-link"
                class="font-courier text-xs text-code-foreground bg-code border border-border-strong rounded-md px-2.5 py-1.25 tracking-wider font-bold transition-all duration-150 hover:bg-primary-glow hover:text-primary hover:border-primary"
                :title="`Ver detalhes do commit ${item.commit_id}`"
              >
                {{ item.commit_id.slice(0, 8) }}
              </router-link>

              <!-- Botão Re-enviar / Retry -->
              <BaseButton
                variant="plain"
                data-tour="historico-reenviar"
                class="rounded-md border border-border-strong bg-card px-2.5 py-1 text-xs text-primary hover:-translate-y-px hover:border-primary hover:bg-primary-glow"
                @click="reenviarItemHistorico(item)"
                title="Re-enviar esta atividade ao portal Munka"
              >
                ↻ Re-enviar
              </BaseButton>

              <!-- Botão Excluir -->
              <button 
                type="button"
                class="flex items-center justify-center cursor-pointer bg-transparent border-0 p-1 text-canvas-danger opacity-85 transition-[opacity,scale] duration-100 hover:opacity-100 hover:scale-110 hover:text-canvas-danger-hover" 
                @click="abrirModalConfirmacao(item.id)"
                title="Remover do histórico"
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" class="stroke-canvas-danger" fill="none" />
                  <line x1="15" y1="9" x2="9" y2="15" class="stroke-canvas-danger" />
                  <line x1="9" y1="9" x2="15" y2="15" class="stroke-canvas-danger" />
                </svg>
              </button>
            </div>

          </div>
        </div>

      </div>
    </div>
  </div>

    <!-- Modal de Confirmação de Exclusão -->
    <BaseModal v-if="exibindoModalConfirmacao" ref="modalRef" labelledby="confirm-modal-title" @close="fecharModalConfirmacao">
      <h2 id="confirm-modal-title" class="mb-1 text-xl font-bold text-foreground">Confirmar Exclusão</h2>
      <p>Tem certeza de que deseja remover esta atividade do histórico? Esta ação não pode ser desfeita.</p>
      <template #actions>
        <BaseButton @click="fecharModalConfirmacao">Cancelar</BaseButton>
        <button type="button" class="inline-flex cursor-pointer items-center justify-center gap-2 border-2 border-border-strong bg-canvas-danger px-4.5 py-2 text-sm leading-none font-bold tracking-wide text-white shadow-[3px_3px_0] shadow-border-strong transition-[translate,box-shadow] duration-100 hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-canvas-danger-hover hover:shadow-[5px_5px_0] hover:shadow-border-strong" @click="confirmarExclusao">Excluir</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { api, type HistoricoItem } from '../api'
import { useToastStore } from '../stores/toast'
import { useFilaStore } from '../stores/fila'
import TutorialModal from '../components/TutorialModal.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import FiltersBar from '../components/ui/FiltersBar.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import PillButton from '../components/ui/PillButton.vue'
import SearchBox from '../components/ui/SearchBox.vue'
import StateMessage from '../components/ui/StateMessage.vue'

const items = ref<HistoricoItem[]>([])
const loading = ref(true)
const toastStore = useToastStore()
const filaStore = useFilaStore()

const termoBusca = ref('')
const filtroStatus = ref<'todos' | 'concluidas' | 'sem_data'>('todos')

const totalConcluidas = computed(() => {
  return items.value.filter(i => i.tem_data_fim !== false && !i.status?.includes('Sem Data Fim') && !i.status?.includes('Incompleta')).length
})

const totalSemDataFim = computed(() => {
  return items.value.filter(i => i.tem_data_fim === false || i.status?.includes('Sem Data Fim') || i.status?.includes('Incompleta')).length
})

const itemsFiltrados = computed(() => {
  let list = items.value

  if (filtroStatus.value === 'concluidas') {
    list = list.filter(i => i.tem_data_fim !== false && !i.status?.includes('Sem Data Fim') && !i.status?.includes('Incompleta'))
  } else if (filtroStatus.value === 'sem_data') {
    list = list.filter(i => i.tem_data_fim === false || i.status?.includes('Sem Data Fim') || i.status?.includes('Incompleta'))
  }

  if (termoBusca.value.trim()) {
    const termo = termoBusca.value.toLowerCase().trim()
    list = list.filter(i => 
      (i.titulo && i.titulo.toLowerCase().includes(termo)) ||
      (i.codigo && i.codigo.toLowerCase().includes(termo)) ||
      (i.commit_id && i.commit_id.toLowerCase().includes(termo)) ||
      (i.commit_autor && i.commit_autor.toLowerCase().includes(termo)) ||
      (i.commit_mensagem && i.commit_mensagem.toLowerCase().includes(termo))
    )
  }

  return list
})

function limparFiltros() {
  termoBusca.value = ''
  filtroStatus.value = 'todos'
}

let timerHistorico: any = null

const itemParaDeletar = ref<number | null>(null)
const exibindoModalConfirmacao = ref(false)

const modalRef = ref<InstanceType<typeof BaseModal> | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

function handleConfirmKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    fecharModalConfirmacao()
  }
  const painel = modalRef.value?.panel
  if (e.key === 'Tab' && painel) {
    const focusable = painel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    if (focusable.length === 0) return
    const first = focusable[0] as HTMLElement
    const last = focusable[focusable.length - 1] as HTMLElement
    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus()
        e.preventDefault()
      }
    } else {
      if (document.activeElement === last) {
        first.focus()
        e.preventDefault()
      }
    }
  }
}

watch(exibindoModalConfirmacao, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleConfirmKeydown)
    nextTick(() => {
      const btn = modalRef.value?.panel?.querySelector('[data-modal-actions] button') as HTMLElement
      btn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleConfirmKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

async function reenviarItemHistorico(item: HistoricoItem) {
  if (!item.commit_id) {
    toastStore.addToast('Commit ID não encontrado para esta atividade', 'error')
    return
  }
  if (confirm(`Deseja re-enviar a atividade "${item.titulo}" ao portal?`)) {
    try {
      // Busca a análise do commit para encontrar o índice correto da atividade pelo título
      const analise = await api.analise.obter(item.commit_id)
      const idx = analise.atividades.findIndex((a: any) => a.titulo === item.titulo)
      if (idx === -1) {
        toastStore.addToast(`Atividade "${item.titulo}" não encontrada na análise do commit`, 'error')
        return
      }
      await filaStore.enfileirarEnvio(item.commit_id, idx)
      toastStore.addToast('Envio adicionado à fila com sucesso!', 'success')
    } catch (e: any) {
      toastStore.addToast(`Erro ao enfileirar re-envio: ${e.message || e}`, 'error')
    }
  }
}

onMounted(async () => {
  await carregarHistorico()
  timerHistorico = setInterval(async () => {
    await carregarHistorico(true)
  }, 30000)
})

onUnmounted(() => {
  if (timerHistorico) {
    clearInterval(timerHistorico)
    timerHistorico = null
  }
})

async function carregarHistorico(quiet: boolean | Event = false) {
  const isQuiet = typeof quiet === 'boolean' ? quiet : false
  if (!isQuiet) loading.value = true
  try {
    items.value = await api.historico.listar()
  } finally {
    if (!isQuiet) loading.value = false
  }
}

function formatarDataCabecalho(dataStr: string): string {
  if (!dataStr) return 'Outras datas'
  const parts = dataStr.split('/')
  if (parts.length === 3) {
    const dia = parseInt(parts[0], 10)
    const mesIdx = parseInt(parts[1], 10) - 1
    const ano = parts[2]
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const mesNome = meses[mesIdx] || parts[1]
    return `${dia} ${mesNome}, ${ano}`
  }
  return dataStr
}

function obterDataParaAgrupamento(item: HistoricoItem): string {
  // 1. Prioriza data_autor do commit
  if (item.commit_data_autor) {
    try {
      const d = new Date(item.commit_data_autor)
      if (!isNaN(d.getTime())) {
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const ano = d.getFullYear()
        return `${dia}/${mes}/${ano}`
      }
    } catch {
      // fallback
    }
  }
  // 2. Data formatada do commit (DD/MM/YYYY)
  if (item.commit_data) {
    return item.commit_data
  }
  // 3. Data de envio da atividade (enviado_em)
  if (item.enviado_em) {
    try {
      const d = new Date(item.enviado_em)
      if (!isNaN(d.getTime())) {
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const ano = d.getFullYear()
        return `${dia}/${mes}/${ano}`
      }
    } catch {
      // fallback
    }
  }
  return 'Outras datas'
}

function obterTime(item: HistoricoItem): number {
  if (item.commit_data_autor) {
    const t = new Date(item.commit_data_autor).getTime()
    if (!isNaN(t)) return t
  }
  if (item.commit_data) {
    const parts = item.commit_data.split('/')
    if (parts.length === 3) {
      const t = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0])).getTime()
      if (!isNaN(t)) return t
    }
  }
  if (item.enviado_em) {
    const t = new Date(item.enviado_em).getTime()
    if (!isNaN(t)) return t
  }
  return 0
}

function obterIniciais(nome?: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

function obterClasseAvatar(nome?: string): string {
  if (!nome) return 'bg-avatar-default'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    'bg-avatar-blue',
    'bg-canvas-success',
    'bg-canvas-danger',
    'bg-avatar-amber',
    'bg-avatar-purple',
    'bg-avatar-indigo',
    'bg-avatar-cyan'
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function obterTempoRelativo(isoStr?: string): string {
  if (!isoStr) return 'há algum tempo'
  try {
    const d = new Date(isoStr)
    const agora = new Date()
    const diffMs = agora.getTime() - d.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'agora mesmo'
    if (diffMin === 1) return 'há 1 minuto'
    if (diffMin < 60) return `há ${diffMin} minutos`
    if (diffHour === 1) return 'há 1 hora'
    if (diffHour < 24) return `há ${diffHour} horas`
    if (diffDay === 1) return 'ontem'
    return `há ${diffDay} dias`
  } catch {
    return 'há algum tempo'
  }
}

function formatDate(iso: string) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString('pt-BR')
  } catch {
    return iso
  }
}

const historicoAgrupado = computed(() => {
  const grupos: Record<string, HistoricoItem[]> = {}
  
  for (const item of itemsFiltrados.value) {
    const dataAgrupamento = obterDataParaAgrupamento(item)
    const dataFormatada = formatarDataCabecalho(dataAgrupamento)
    if (!grupos[dataFormatada]) {
      grupos[dataFormatada] = []
    }
    grupos[dataFormatada].push(item)
  }
  
  for (const chave of Object.keys(grupos)) {
    grupos[chave].sort((a, b) => obterTime(b) - obterTime(a))
  }
  
  const chavesOrdenadas = Object.keys(grupos).sort((a, b) => {
    const timeA = obterTime(grupos[a][0])
    const timeB = obterTime(grupos[b][0])
    return timeB - timeA
  })
  
  return chavesOrdenadas.map(chave => ({
    data: chave,
    items: grupos[chave]
  }))
})

function abrirModalConfirmacao(id: number) {
  itemParaDeletar.value = id
  exibindoModalConfirmacao.value = true
}

function fecharModalConfirmacao() {
  itemParaDeletar.value = null
  exibindoModalConfirmacao.value = false
}

async function confirmarExclusao() {
  if (itemParaDeletar.value === null) return
  try {
    await api.historico.remover(itemParaDeletar.value)
    items.value = items.value.filter(i => i.id !== itemParaDeletar.value)
    toastStore.addToast('Item removido do histórico.', 'info')
  } catch (e: any) {
    toastStore.addToast(`Erro ao remover: ${e.response?.data?.detail ?? String(e)}`, 'error')
  } finally {
    fecharModalConfirmacao()
  }
}
</script>
