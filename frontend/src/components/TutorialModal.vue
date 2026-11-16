<template>
  <span class="tutorial-wrapper inline-flex items-center ml-1.5">
    <!-- Botão Gatilho Manual '?' -->
    <button 
      type="button"
      class="size-6 rounded-md border border-border-strong bg-background text-primary text-xs font-extrabold cursor-pointer inline-flex items-center justify-center transition-all duration-200 shadow-[0_1px_3px] shadow-black/8 hover:bg-primary hover:text-white hover:border-primary hover:-translate-y-px hover:shadow-[0_4px_10px_var(--color-primary-glow)]" 
      @click="abrirManual" 
      :title="`Abrir guia guiado: ${tutorial.title}`"
      aria-label="Abrir guia guiado e tutorial desta tela"
    >
      <i class="fa-solid fa-question" aria-hidden="true"></i>
    </button>

    <!-- Modal do Tutorial Guiado com Spotlight -->
    <Teleport to="body">
      <div 
        v-if="open" 
        :class="[
          'tutorial-overlay fixed inset-0 z-9999 flex items-center justify-center p-6 animate-fade-in overflow-y-auto',
          spotlightAtivo ? 'has-spotlight bg-transparent' : 'bg-tutorial-overlay/82 backdrop-blur-xs'
        ]"
        @click.self="pularTutorial"
        role="presentation"
      >
        <!-- Spotlight / Efeito de Destaque com tela escurecida ao redor -->
        <div 
          v-if="spotlightAtivo && spotlightStyle" 
          class="tutorial-spotlight fixed z-9997 pointer-events-none border-2 border-blue-500 rounded-xl transition-all duration-300 ease-[cubic-bezier(0.25,1,0.5,1)] animate-spotlight-glow" 
          :style="spotlightStyle"
          aria-hidden="true"
        >
          <div class="spotlight-pulse-ring absolute -inset-1.5 border border-dashed border-blue-500/80 rounded-2xl opacity-70"></div>
          <div class="spotlight-badge absolute -top-3.5 right-3 bg-blue-500 text-white text-[0.68rem] font-extrabold px-2 py-0.5 rounded-full inline-flex items-center gap-1 uppercase tracking-wider shadow-[0_2px_8px] shadow-black/40">
            <i class="fa-solid fa-crosshairs" aria-hidden="true"></i>
            <span>Destaque</span>
          </div>
        </div>

        <!-- Card do Tutorial Guiado -->
        <div 
          ref="modalRef" 
          :class="[
            'tutorial-modal-card w-full max-w-[560px] bg-card border border-border rounded-2xl flex flex-col overflow-hidden relative z-9999 transition-all duration-350 ease-[cubic-bezier(0.25,1,0.5,1)] animate-scale-up-modal',
            spotlightAtivo && posicaoCard === 'bottom' ? 'card-anchored-bottom mt-auto mb-8 shadow-tutorial-card-anchored' : '',
            spotlightAtivo && posicaoCard === 'top' ? 'card-anchored-top mt-8 mb-auto shadow-tutorial-card-anchored' : '',
            spotlightAtivo && posicaoCard !== 'center' ? '' : 'card-centered m-auto shadow-tutorial-card'
          ]"
          role="dialog" 
          aria-modal="true" 
          :aria-labelledby="titleId"
        >
          <!-- Cabeçalho do Tutorial -->
          <div class="tutorial-header pt-5 px-6 pb-4 flex items-start justify-between gap-4 border-b border-border-strong relative max-[600px]:p-4">
            <div class="tutorial-header-left">
              <span class="tutorial-badge inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-primary-glow text-primary text-xs font-bold uppercase tracking-wider mb-1.5">
                <i class="fa-solid fa-graduation-cap" aria-hidden="true"></i>
                <span>Tutorial Guiado</span>
              </span>
              <h2 :id="titleId" class="text-xl font-extrabold text-foreground leading-tight mb-1">{{ tutorial.title }}</h2>
              <p class="tutorial-subtitle text-[0.82rem] text-muted-foreground leading-snug">{{ tutorial.subtitle }}</p>
            </div>
            <button 
              type="button" 
              class="bg-transparent border border-border-strong text-muted-foreground size-8 rounded-lg inline-flex items-center justify-center text-sm cursor-pointer transition-all duration-150 shrink-0 hover:bg-red-500/15 hover:text-danger hover:border-danger" 
              @click="pularTutorial" 
              aria-label="Fechar tutorial"
              title="Pular tutorial"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
            </button>
          </div>

          <!-- Barra de Progresso e Indicador de Passos -->
          <div class="tutorial-progress-bar-container w-full h-1 bg-slate-400/15 relative">
            <div 
              class="tutorial-progress-bar-fill h-full bg-(image:--accent-grad) transition-[width] duration-300" 
              :style="{ width: `${((passoAtual + 1) / totalPassos) * 100}%` }"
            ></div>
          </div>

          <div class="tutorial-steps-indicator flex items-center justify-center gap-2.5 pt-3.5 px-4 pb-1" role="tablist" aria-label="Navegação dos passos do tutorial">
            <button 
              v-for="(p, idx) in tutorial.steps" 
              :key="idx"
              type="button"
              :class="[
                'step-dot-btn size-[26px] rounded-full border text-xs font-bold inline-flex items-center justify-center cursor-pointer transition-all duration-200',
                passoAtual === idx ? classesDotAtivo : passoAtual > idx ? classesDotConcluido : classesDotPendente
              ]"
              @click="irParaPasso(idx)"
              :aria-label="`Ir para o passo ${idx + 1}: ${p.title}`"
              :title="p.title"
            >
              <span class="step-dot-number">{{ idx + 1 }}</span>
            </button>
          </div>

          <!-- Corpo do Passo Atual com Transição Suave -->
          <div class="tutorial-body pt-5 px-7 pb-6 min-h-45 flex items-center">
            <div class="w-full flex gap-5 items-start animate-fade-in-step max-[600px]:flex-col max-[600px]:items-center max-[600px]:text-center" :key="passoAtual">
              <div class="step-icon-wrap size-13 rounded-xl bg-primary-glow border border-primary text-primary text-2xl flex items-center justify-center shrink-0 shadow-[0_4px_12px] shadow-blue-500/15">
                <i :class="passo.icon" aria-hidden="true"></i>
              </div>

              <div class="step-content flex-1">
                <div class="step-meta-row flex items-center gap-3 mb-1 flex-wrap">
                  <span class="step-counter text-xs font-bold text-primary uppercase tracking-wider">Passo {{ passoAtual + 1 }} de {{ totalPassos }}</span>
                  <span v-if="spotlightAtivo" class="step-target-badge text-[0.7rem] font-bold text-emerald-500 bg-emerald-500/12 border border-emerald-500/30 px-[7px] py-px rounded-full inline-flex items-center gap-1">
                    <i class="fa-solid fa-crosshairs" aria-hidden="true"></i>
                    <span>Elemento focado na tela</span>
                  </span>
                </div>
                <h3 class="text-lg font-extrabold text-foreground mb-2 leading-[1.3]">{{ passo.title }}</h3>
                <p class="step-description text-sm text-muted-foreground leading-[1.55] mb-3.5">{{ passo.description }}</p>

                <div v-if="passo.tip" class="step-tip-box flex items-start gap-2.5 px-3.5 py-2.5 bg-amber-500/8 border border-amber-500/25 rounded-lg text-[0.82rem] text-foreground max-[600px]:text-left">
                  <i class="fa-solid fa-lightbulb tip-icon text-warning text-[0.95rem] mt-0.5 shrink-0" aria-hidden="true"></i>
                  <span class="tip-text leading-[1.45] text-muted-foreground [&_strong]:text-foreground"><strong>Dica Prática:</strong> {{ passo.tip }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Rodapé com Navegação -->
          <div class="tutorial-footer px-6 py-4 bg-muted border-t border-border-strong flex items-center justify-between gap-4 max-[600px]:px-4 max-[600px]:py-3.5 max-[600px]:flex-col max-[600px]:gap-3">
            <button 
              type="button" 
              class="bg-transparent border-0 text-muted-foreground text-[0.82rem] font-semibold cursor-pointer px-2.5 py-1.5 rounded-md transition-all duration-150 hover:text-foreground hover:bg-slate-400/10" 
              @click="pularTutorial"
            >
              Pular Tutorial
            </button>

            <div class="flex items-center gap-2.5 max-[600px]:w-full max-[600px]:justify-between">
              <button 
                type="button" 
                :class="[classesBotaoNav, 'bg-card border-border-strong text-foreground enabled:hover:border-primary enabled:hover:bg-primary-glow enabled:hover:text-primary disabled:opacity-40 disabled:cursor-not-allowed']"
                :disabled="passoAtual === 0"
                @click="passoAnterior"
              >
                <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
                <span>Anterior</span>
              </button>

              <button 
                v-if="passoAtual < totalPassos - 1"
                data-tutorial-focus
                type="button" 
                :class="[classesBotaoNav, 'bg-primary border-primary text-white hover:bg-primary-light hover:shadow-[0_4px_12px_var(--color-primary-glow)]']"
                @click="proximoPasso"
              >
                <span>Próximo</span>
                <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
              </button>

              <button 
                v-else
                data-tutorial-focus
                type="button" 
                :class="[classesBotaoNav, 'bg-success border-success text-white hover:brightness-110 hover:shadow-[0_4px_12px] hover:shadow-emerald-500/30']"
                @click="concluirTutorial"
              >
                <i class="fa-solid fa-check" aria-hidden="true"></i>
                <span>Concluir Tutorial</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </Teleport>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { TUTORIALS, type ScreenTutorial } from '../config/tutorials'

const props = defineProps<{
  screenId: string
  title?: string
}>()

const tutorial = computed<ScreenTutorial>(() => {
  if (TUTORIALS[props.screenId]) {
    return TUTORIALS[props.screenId]
  }
  return {
    id: props.screenId,
    title: props.title || 'Guia da Página',
    subtitle: 'Principais funcionalidades e dicas de uso',
    steps: [
      {
        title: 'Visão Geral',
        icon: 'fa-solid fa-circle-info',
        description: 'Explore os recursos e atalhos disponíveis nesta tela para otimizar suas tarefas.'
      }
    ]
  }
})

const open = ref(false)
const passoAtual = ref(0)
const modalRef = ref<HTMLElement | null>(null)
const titleId = `tutorial-title-${props.screenId}`

const totalPassos = computed(() => tutorial.value.steps.length)
const passo = computed(() => tutorial.value.steps[passoAtual.value] || tutorial.value.steps[0])

// Classes por estado dos botões de passo e base dos botões de navegação
const classesDotPendente = 'border-border-strong bg-background text-muted-foreground'
const classesDotConcluido = 'bg-emerald-500/15 border-success text-success'
const classesDotAtivo = 'bg-primary border-primary text-white scale-115 shadow-[0_0_10px_var(--color-primary-glow)]'
const classesBotaoNav = 'h-9 px-4 rounded-lg text-sm font-semibold cursor-pointer inline-flex items-center gap-2 border transition-all duration-200'

const storageKey = computed(() => `nexus-tour-${props.screenId}`)

// ── Estado do Spotlight ──
const spotlightAtivo = ref(false)
const spotlightCoords = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const posicaoCard = ref<'center' | 'top' | 'bottom'>('center')
let highlightedElement: HTMLElement | null = null
let retryTimer: number | null = null

const spotlightStyle = computed(() => {
  if (!spotlightCoords.value) return null
  const { top, left, width, height } = spotlightCoords.value
  return {
    top: `${Math.max(4, top)}px`,
    left: `${Math.max(4, left)}px`,
    width: `${Math.max(20, width)}px`,
    height: `${Math.max(20, height)}px`,
  }
})

function limparElementoDestacado() {
  if (highlightedElement) {
    highlightedElement.classList.remove('tutorial-target-highlighted')
    highlightedElement = null
  }
}

function encontrarElementoAlvo(): HTMLElement | null {
  if (!passo.value.target) return null
  const selectors = passo.value.target.split(',').map(s => s.trim())

  for (const sel of selectors) {
    try {
      const el = document.querySelector(sel) as HTMLElement | null
      if (el) {
        const rect = el.getBoundingClientRect()
        // Aceita se tiver dimensões mínimas ou estiver visível no DOM
        if (rect.width > 0 || rect.height > 0) {
          return el
        }
      }
    } catch {
      // Ignora erro de seletor complexo
    }
  }
  return null
}

function recalcularPosicaoSemScroll() {
  if (!open.value || !highlightedElement) return
  const rect = highlightedElement.getBoundingClientRect()
  const padding = 10

  spotlightCoords.value = {
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + (padding * 2),
    height: rect.height + (padding * 2)
  }
}

function atualizarSpotlight(permitirScroll = true): boolean {
  if (!open.value || !passo.value.target) {
    limparElementoDestacado()
    spotlightAtivo.value = false
    spotlightCoords.value = null
    posicaoCard.value = 'center'
    return false
  }

  const targetEl = encontrarElementoAlvo()

  if (targetEl) {
    if (highlightedElement !== targetEl) {
      limparElementoDestacado()
      highlightedElement = targetEl
      highlightedElement.classList.add('tutorial-target-highlighted')
    }

    const rect = targetEl.getBoundingClientRect()
    const padding = 10

    spotlightCoords.value = {
      top: rect.top - padding,
      left: rect.left - padding,
      width: rect.width + (padding * 2),
      height: rect.height + (padding * 2)
    }
    spotlightAtivo.value = true

    // Ancorar o card no topo ou no rodapé para nunca cobrir o elemento focado
    const viewportHeight = window.innerHeight
    const elementoCentroY = rect.top + (rect.height / 2)

    if (elementoCentroY < viewportHeight * 0.48) {
      // Elemento no topo -> Card no rodapé
      posicaoCard.value = 'bottom'
    } else {
      // Elemento embaixo -> Card no topo
      posicaoCard.value = 'top'
    }

    // Scroll suave se estiver fora do viewport
    if (permitirScroll && (rect.top < 60 || rect.bottom > viewportHeight - 60)) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Após o scroll terminar, recalcula as coordenadas fixas
      setTimeout(() => {
        recalcularPosicaoSemScroll()
      }, 250)
      setTimeout(() => {
        recalcularPosicaoSemScroll()
      }, 500)
    }
    return true
  } else {
    // Alvo não encontrado nesta tentativa
    limparElementoDestacado()
    spotlightAtivo.value = false
    spotlightCoords.value = null
    posicaoCard.value = 'center'
    return false
  }
}

function dispararAtualizacaoComRetentativas(tentativasRestantes = 5) {
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }

  const sucesso = atualizarSpotlight(true)
  if (!sucesso && tentativasRestantes > 0 && open.value) {
    const delay = (6 - tentativasRestantes) * 120 // 120ms, 240ms, 360ms...
    retryTimer = window.setTimeout(() => {
      dispararAtualizacaoComRetentativas(tentativasRestantes - 1)
    }, delay)
  }
}

let animFrameId: number | null = null
function onScrollOrResize() {
  if (!open.value || !spotlightAtivo.value) return
  if (animFrameId) cancelAnimationFrame(animFrameId)
  animFrameId = requestAnimationFrame(() => {
    recalcularPosicaoSemScroll()
  })
}

let previousActiveElement: HTMLElement | null = null

function checarPrimeiraVisita() {
  if (typeof window === 'undefined') return
  let jaVisitou: string | null = null
  try {
    jaVisitou = localStorage.getItem(storageKey.value)
  } catch {
    // Armazenamento indisponível: mostra o tutorial
  }
  if (!jaVisitou) {
    passoAtual.value = 0
    open.value = true
  }
}

function abrirManual() {
  passoAtual.value = 0
  open.value = true
}

function irParaPasso(idx: number) {
  passoAtual.value = idx
}

function proximoPasso() {
  if (passoAtual.value < totalPassos.value - 1) {
    passoAtual.value++
  }
}

function passoAnterior() {
  if (passoAtual.value > 0) {
    passoAtual.value--
  }
}

function salvarLeitura(valor: 'skipped' | 'completed') {
  try {
    localStorage.setItem(storageKey.value, valor)
  } catch {
    // Armazenamento indisponível: o tutorial volta a aparecer
  }
}

function pularTutorial() {
  salvarLeitura('skipped')
  fecharModal()
}

function concluirTutorial() {
  salvarLeitura('completed')
  fecharModal()
}

function fecharModal() {
  open.value = false
  limparElementoDestacado()
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (!open.value) return

  if (e.key === 'Escape') {
    pularTutorial()
  } else if (e.key === 'ArrowRight') {
    if (passoAtual.value < totalPassos.value - 1) {
      proximoPasso()
    } else {
      concluirTutorial()
    }
  } else if (e.key === 'ArrowLeft') {
    passoAnterior()
  } else if (e.key === 'Tab' && modalRef.value) {
    // Trap do foco para acessibilidade
    const focusable = modalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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

watch(passoAtual, () => {
  nextTick(() => {
    dispararAtualizacaoComRetentativas()
  })
})

watch(open, (newVal) => {
  if (newVal) {
    previousActiveElement = document.activeElement as HTMLElement | null
    document.addEventListener('keydown', handleKeydown)
    window.addEventListener('resize', onScrollOrResize, { passive: true })
    window.addEventListener('scroll', onScrollOrResize, { passive: true, capture: true })
    nextTick(() => {
      dispararAtualizacaoComRetentativas()
      const btn = modalRef.value?.querySelector('[data-tutorial-focus]') as HTMLElement | null
      btn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleKeydown)
    window.removeEventListener('resize', onScrollOrResize)
    window.removeEventListener('scroll', onScrollOrResize, true)
    limparElementoDestacado()
    spotlightAtivo.value = false
    spotlightCoords.value = null
    if (previousActiveElement) {
      previousActiveElement.focus()
      previousActiveElement = null
    }
  }
})

onMounted(() => {
  checarPrimeiraVisita()
})

onUnmounted(() => {
  fecharModal()
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', onScrollOrResize)
  window.removeEventListener('scroll', onScrollOrResize, true)
})
</script>
