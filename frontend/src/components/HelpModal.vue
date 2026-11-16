<template>
  <span class="inline-flex items-center">
    <button
      class="size-5.5 shrink-0 cursor-pointer rounded-xs border-2 border-border-strong bg-transparent text-xs leading-none font-extrabold text-primary shadow-[2px_2px_0] shadow-primary transition duration-100 hover:-translate-x-px hover:-translate-y-px hover:bg-primary hover:text-background hover:shadow-[3px_3px_0] hover:shadow-primary"
      @click="open = true"
      :title="title"
    >?</button>

    <BaseModal v-if="open" ref="modalRef" size="auto" :labelledby="titleId" class="max-h-[80vh] w-[95vw] max-w-135" @close="open = false">
        <div class="mb-4 flex items-center justify-between border-b-2 border-primary pb-3">
          <h2 :id="titleId" class="text-base font-extrabold tracking-wide uppercase">{{ title }}</h2>
          <button
            data-close class="cursor-pointer rounded-none border-2 border-border-strong bg-transparent px-1.5 py-0.5 text-sm text-muted-foreground transition-colors duration-100 hover:border-canvas-danger hover:bg-canvas-danger hover:text-white"
            @click="open = false"
            aria-label="Fechar ajuda"
          >
            <i class="fa-solid fa-xmark" aria-hidden="true"></i>
          </button>
        </div>
        <div class="flex flex-col gap-4 overflow-y-auto">
          <div v-for="item in items" :key="item.title">
            <h3 class="mb-1 text-xs font-extrabold tracking-widest text-primary uppercase">{{ item.title }}</h3>
            <p class="text-sm leading-relaxed text-muted-foreground">{{ item.text }}</p>
          </div>
        </div>
    </BaseModal>
  </span>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import BaseModal from './ui/BaseModal.vue'

defineProps<{
  title: string
  items: Array<{ title: string; text: string }>
}>()

const open = ref(false)
const modalRef = ref<{ panel: HTMLElement | null } | null>(null)
const titleId = 'help-title-' + Math.random().toString(36).substring(2, 9)

let previousActiveElement: HTMLElement | null = null

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    open.value = false
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

watch(open, (newVal) => {
  if (newVal) {
    previousActiveElement = document.activeElement as HTMLElement | null
    document.addEventListener('keydown', handleKeydown)
    nextTick(() => {
      const closeBtn = modalRef.value?.panel?.querySelector('[data-close]') as HTMLElement | null
      closeBtn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleKeydown)
    if (previousActiveElement) {
      previousActiveElement.focus()
      previousActiveElement = null
    }
  }
})
</script>
