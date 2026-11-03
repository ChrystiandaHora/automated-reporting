<template>
  <span class="tutorial-wrapper">
    <!-- Botão Gatilho Manual '?' -->
    <button 
      type="button"
      class="tutorial-trigger-btn" 
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
        class="tutorial-overlay" 
        :class="{ 'has-spotlight': spotlightAtivo }"
        @click.self="pularTutorial"
        role="presentation"
      >
        <!-- Spotlight / Efeito de Destaque com tela escurecida ao redor -->
        <div 
          v-if="spotlightAtivo && spotlightStyle" 
          class="tutorial-spotlight" 
          :style="spotlightStyle"
          aria-hidden="true"
        >
          <div class="spotlight-pulse-ring"></div>
          <div class="spotlight-badge">
            <i class="fa-solid fa-crosshairs" aria-hidden="true"></i>
            <span>Destaque</span>
          </div>
        </div>

        <!-- Card do Tutorial Guiado -->
        <div 
          ref="modalRef" 
          class="tutorial-modal-card" 
          :class="{
            'card-anchored-bottom': spotlightAtivo && posicaoCard === 'bottom',
            'card-anchored-top': spotlightAtivo && posicaoCard === 'top',
            'card-centered': !spotlightAtivo || posicaoCard === 'center'
          }"
          role="dialog" 
          aria-modal="true" 
          :aria-labelledby="titleId"
        >
          <!-- Cabeçalho do Tutorial -->
          <div class="tutorial-header">
            <div class="tutorial-header-left">
              <span class="tutorial-badge">
                <i class="fa-solid fa-graduation-cap" aria-hidden="true"></i>
                <span>Tutorial Guiado</span>
              </span>
              <h2 :id="titleId">{{ tutorial.title }}</h2>
              <p class="tutorial-subtitle">{{ tutorial.subtitle }}</p>
            </div>
            <button 
              type="button" 
              class="tutorial-close-btn" 
              @click="pularTutorial" 
              aria-label="Fechar tutorial"
              title="Pular tutorial"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
            </button>
          </div>

          <!-- Barra de Progresso e Indicador de Passos -->
          <div class="tutorial-progress-bar-container">
            <div 
              class="tutorial-progress-bar-fill" 
              :style="{ width: `${((passoAtual + 1) / totalPassos) * 100}%` }"
            ></div>
          </div>

          <div class="tutorial-steps-indicator" role="tablist" aria-label="Navegação dos passos do tutorial">
            <button 
              v-for="(p, idx) in tutorial.steps" 
              :key="idx"
              type="button"
              class="step-dot-btn"
              :class="{ 
                active: passoAtual === idx, 
                completed: passoAtual > idx 
              }"
              @click="irParaPasso(idx)"
              :aria-label="`Ir para o passo ${idx + 1}: ${p.title}`"
              :title="p.title"
            >
              <span class="step-dot-number">{{ idx + 1 }}</span>
            </button>
          </div>

          <!-- Corpo do Passo Atual com Transição Suave -->
          <div class="tutorial-body">
            <div class="step-card" :key="passoAtual">
              <div class="step-icon-wrap">
                <i :class="passo.icon" aria-hidden="true"></i>
              </div>

              <div class="step-content">
                <div class="step-meta-row">
                  <span class="step-counter">Passo {{ passoAtual + 1 }} de {{ totalPassos }}</span>
                  <span v-if="spotlightAtivo" class="step-target-badge">
                    <i class="fa-solid fa-crosshairs" aria-hidden="true"></i>
                    <span>Elemento focado na tela</span>
                  </span>
                </div>
                <h3 class="step-title">{{ passo.title }}</h3>
                <p class="step-description">{{ passo.description }}</p>

                <div v-if="passo.tip" class="step-tip-box">
                  <i class="fa-solid fa-lightbulb tip-icon" aria-hidden="true"></i>
                  <span class="tip-text"><strong>Dica Prática:</strong> {{ passo.tip }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Rodapé com Navegação -->
          <div class="tutorial-footer">
            <button 
              type="button" 
              class="btn-tutorial-skip" 
              @click="pularTutorial"
            >
              Pular Tutorial
            </button>

            <div class="tutorial-footer-actions">
              <button 
                type="button" 
                class="btn-tutorial-nav btn-tutorial-prev"
                :disabled="passoAtual === 0"
                @click="passoAnterior"
              >
                <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
                <span>Anterior</span>
              </button>

              <button 
                v-if="passoAtual < totalPassos - 1"
                type="button" 
                class="btn-tutorial-nav btn-tutorial-next"
                @click="proximoPasso"
              >
                <span>Próximo</span>
                <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
              </button>

              <button 
                v-else
                type="button" 
                class="btn-tutorial-nav btn-tutorial-finish"
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
  const jaVisitou = sessionStorage.getItem(storageKey.value)
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

function pularTutorial() {
  sessionStorage.setItem(storageKey.value, 'skipped')
  fecharModal()
}

function concluirTutorial() {
  sessionStorage.setItem(storageKey.value, 'completed')
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
      const btn = modalRef.value?.querySelector('.btn-tutorial-next, .btn-tutorial-finish') as HTMLElement | null
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

<style scoped>
.tutorial-wrapper {
  display: inline-flex;
  align-items: center;
  margin-left: 0.35rem;
}

.tutorial-trigger-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.tutorial-trigger-btn:hover {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px var(--accent-glow);
}

/* ── Overlay Modal ── */
.tutorial-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  animation: fadeInOverlay 0.25s ease-out;
  background: rgba(10, 15, 30, 0.82);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  overflow-y: auto;
}

/* Quando o spotlight está ativo, o próprio spotlight escurece o restante com a box-shadow vazada */
.tutorial-overlay.has-spotlight {
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  pointer-events: auto;
}

@keyframes fadeInOverlay {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ── Spotlight / Efeito de Destaque ── */
.tutorial-spotlight {
  position: fixed;
  z-index: 9997;
  pointer-events: none;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  box-shadow: 
    0 0 0 9999px rgba(8, 12, 24, 0.86),
    0 0 0 3px rgba(59, 130, 246, 0.5),
    0 0 30px rgba(59, 130, 246, 0.8),
    inset 0 0 15px rgba(59, 130, 246, 0.25);
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  animation: spotlightGlow 2s infinite alternate ease-in-out;
}

@keyframes spotlightGlow {
  0% {
    box-shadow: 
      0 0 0 9999px rgba(8, 12, 24, 0.86),
      0 0 0 2px rgba(59, 130, 246, 0.4),
      0 0 20px rgba(59, 130, 246, 0.6),
      inset 0 0 10px rgba(59, 130, 246, 0.15);
  }
  100% {
    box-shadow: 
      0 0 0 9999px rgba(8, 12, 24, 0.88),
      0 0 0 4px rgba(59, 130, 246, 0.7),
      0 0 35px rgba(59, 130, 246, 0.9),
      inset 0 0 18px rgba(59, 130, 246, 0.3);
  }
}

.spotlight-pulse-ring {
  position: absolute;
  inset: -6px;
  border: 1px dashed rgba(59, 130, 246, 0.8);
  border-radius: 16px;
  opacity: 0.7;
  animation: pulseRotate 6s linear infinite;
}

.spotlight-badge {
  position: absolute;
  top: -14px;
  right: 12px;
  background: #3b82f6;
  color: #ffffff;
  font-size: 0.68rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 99px;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* ── Card do Tutorial Guiado ── */
.tutorial-modal-card {
  width: 100%;
  max-width: 560px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 9999;
  transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  animation: scaleUpModal 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tutorial-modal-card.card-centered {
  margin: auto;
}

.tutorial-modal-card.card-anchored-bottom {
  margin-top: auto;
  margin-bottom: 2rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.65), 0 0 25px rgba(59, 130, 246, 0.25);
}

.tutorial-modal-card.card-anchored-top {
  margin-top: 2rem;
  margin-bottom: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.65), 0 0 25px rgba(59, 130, 246, 0.25);
}

@keyframes scaleUpModal {
  from { transform: scale(0.92) translateY(10px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}

/* ── Header ── */
.tutorial-header {
  padding: 1.25rem 1.5rem 1rem;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid var(--border);
  position: relative;
}

.tutorial-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  background: var(--accent-glow);
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.4rem;
}

.tutorial-header h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 0.25rem;
}

.tutorial-subtitle {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.tutorial-close-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.tutorial-close-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: var(--error);
  border-color: var(--error);
}

/* ── Barra de Progresso ── */
.tutorial-progress-bar-container {
  width: 100%;
  height: 4px;
  background: rgba(148, 163, 184, 0.15);
  position: relative;
}

.tutorial-progress-bar-fill {
  height: 100%;
  background: var(--accent-grad);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Indicador de Passos (Dots) ── */
.tutorial-steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 0.85rem 1rem 0.25rem;
}

.step-dot-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.step-dot-btn.completed {
  background: rgba(16, 185, 129, 0.15);
  border-color: var(--success);
  color: var(--success);
}

.step-dot-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
  transform: scale(1.15);
  box-shadow: 0 0 10px var(--accent-glow);
}

/* ── Corpo do Passo ── */
.tutorial-body {
  padding: 1.25rem 1.75rem 1.5rem;
  min-height: 180px;
  display: flex;
  align-items: center;
}

.step-card {
  width: 100%;
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
  animation: fadeInStep 0.25s ease-out;
}

@keyframes fadeInStep {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: var(--accent-glow);
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 1.45rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.step-content {
  flex: 1;
}

.step-meta-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.3rem;
  flex-wrap: wrap;
}

.step-counter {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.step-target-badge {
  font-size: 0.7rem;
  font-weight: 700;
  color: #10b981;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 1px 7px;
  border-radius: 99px;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.step-description {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.55;
  margin-bottom: 0.85rem;
}

.step-tip-box {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.65rem 0.85rem;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.25);
  border-radius: 8px;
  font-size: 0.82rem;
  color: var(--text);
}

.step-tip-box .tip-icon {
  color: var(--warning);
  font-size: 0.95rem;
  margin-top: 2px;
  flex-shrink: 0;
}

.step-tip-box .tip-text {
  line-height: 1.45;
  color: var(--text-muted);
}

.step-tip-box .tip-text strong {
  color: var(--text);
}

/* ── Footer ── */
.tutorial-footer {
  padding: 1rem 1.5rem;
  background: var(--header-group-bg);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.btn-tutorial-skip {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-tutorial-skip:hover {
  color: var(--text);
  background: rgba(148, 163, 184, 0.1);
}

.tutorial-footer-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.btn-tutorial-nav {
  height: 36px;
  padding: 0 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 0.2s ease;
}

.btn-tutorial-prev {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-tutorial-prev:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--accent-glow);
  color: var(--accent);
}

.btn-tutorial-prev:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-tutorial-next {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #ffffff;
}

.btn-tutorial-next:hover {
  background: var(--accent-light);
  box-shadow: 0 4px 12px var(--accent-glow);
}

.btn-tutorial-finish {
  background: var(--success);
  border: 1px solid var(--success);
  color: #ffffff;
}

.btn-tutorial-finish:hover {
  filter: brightness(1.1);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

@media (max-width: 600px) {
  .step-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .step-tip-box {
    text-align: left;
  }
  .tutorial-header {
    padding: 1rem;
  }
  .tutorial-footer {
    padding: 0.85rem 1rem;
    flex-direction: column;
    gap: 0.75rem;
  }
  .tutorial-footer-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
