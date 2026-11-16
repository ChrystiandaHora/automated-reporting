<template>
  <!-- Teleport: ancestrais com backdrop-filter/transform (ex.: o header) viram o bloco de contenção de `fixed` -->
  <Teleport to="body">
  <div
    class="fixed inset-0 z-200 flex animate-fade-in items-center justify-center bg-slate-900/75 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div
      ref="panel"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="labelledby"
      v-bind="$attrs"
      class="flex animate-scale-in flex-col gap-4 rounded-2xl border border-border-strong bg-card p-7 text-foreground shadow-modal"
      :class="larguras[size]"
    >
      <slot />
      <div v-if="$slots.actions" data-modal-actions class="mt-4 flex justify-end gap-3">
        <slot name="actions" />
      </div>
    </div>
  </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineOptions({ inheritAttrs: false })

/**
 * Casca de modal: fundo escurecido + painel. Fecha ao clicar fora (evento `close`).
 * `size="auto"` não define largura nem largura máxima, para telas que precisam de uma
 * própria. Classes e atributos passados ao componente vão para o PAINEL (não para o fundo).
 * O elemento do painel (focus trap, foco inicial) fica em `modalRef.value?.panel`.
 */
withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'auto'
  labelledby?: string
}>(), { size: 'sm' })

const emit = defineEmits<{ close: [] }>()

const larguras: Record<string, string> = {
  sm: 'w-130 max-w-[95vw]',
  md: 'w-160 max-w-[95vw]',
  lg: 'w-215 max-w-[95vw]',
  xl: 'w-265 max-w-[95vw]',
  auto: ''
}

const panel = ref<HTMLElement | null>(null)
defineExpose({ panel })
</script>
