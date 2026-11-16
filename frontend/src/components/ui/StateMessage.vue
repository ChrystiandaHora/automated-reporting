<template>
  <component :is="tag" :class="classes[type]">
    <slot />
  </component>
</template>

<script setup lang="ts">
/** Mensagens de estado: carregando, vazio, erro e sucesso. */
withDefaults(defineProps<{
  type: 'loading' | 'empty' | 'error' | 'success'
  tag?: string
}>(), { tag: 'div' })

const centralizado = 'py-12 text-center text-[0.95rem] tracking-[0.01em] text-muted-foreground'

const classes: Record<string, string> = {
  loading: centralizado,
  empty: centralizado,
  error: 'mt-2 rounded-sm border-l-3 border-danger bg-danger/10 px-3.5 py-2.5 text-sm leading-normal text-danger',
  success: 'font-semibold text-success'
}
</script>
