<template>
  <button
    type="button"
    class="inline-flex h-[34px] cursor-pointer items-center gap-[0.45rem] rounded-lg border px-3 text-[0.82rem] select-none transition-all duration-200"
    :class="active
      ? 'border-primary bg-primary-glow font-semibold text-primary'
      : 'border-border-strong bg-background font-medium text-muted-foreground hover:border-primary hover:text-foreground'"
    :aria-pressed="active"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
/** Botão de filtro em formato de pílula (estado ativo/inativo). */
defineProps<{ active?: boolean }>()
</script>
