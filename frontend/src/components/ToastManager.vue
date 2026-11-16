<template>
  <div class="fixed bottom-8 right-8 z-[9999] flex w-[90vw] max-w-[400px] flex-col gap-3" aria-live="polite" role="status">
    <TransitionGroup
      enter-from-class="opacity-0 translate-y-5 scale-95"
      leave-to-class="opacity-0 -translate-y-5 scale-95"
      enter-active-class="transition-all duration-200"
      leave-active-class="transition-all duration-200"
    >
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="relative flex cursor-pointer items-center justify-between gap-4 border-2 bg-card px-5 py-4 text-[0.85rem] font-medium text-foreground transition-all duration-200"
        :class="classesPorTipo[toast.type] ?? classesPorTipo.info"
        @click="toastStore.removeToast(toast.id)"
      >
        <span class="sr-only">{{ toast.type === 'error' ? 'Erro: ' : toast.type === 'success' ? 'Sucesso: ' : 'Info: ' }}</span>
        <span class="flex-1 leading-[1.4]">{{ toast.message }}</span>
        <button
          class="flex cursor-pointer items-center justify-center border-none bg-transparent p-0 text-xl leading-none text-muted-foreground transition-colors hover:text-foreground"
          aria-label="Fechar notificação"
          @click.stop="toastStore.removeToast(toast.id)"
        >&times;</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from '../stores/toast'

const toastStore = useToastStore()

const classesPorTipo: Record<string, string> = {
  info: 'border-primary shadow-solid-primary',
  success: 'border-canvas-success shadow-solid-success',
  error: 'border-canvas-danger shadow-solid-danger'
}
</script>
