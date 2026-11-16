<template>
  <select v-model="model" :class="[campo, autoWidth ? '' : 'w-full']">
    <slot />
  </select>
</template>

<script setup lang="ts">
import { campo } from './campo'

/** Select padrão. Suporta v-model e v-model.number. */
defineProps<{ autoWidth?: boolean }>()

const [model, modifiers] = defineModel<string | number | boolean | null | undefined>({
  set(valor) {
    if (modifiers.number && typeof valor === 'string') {
      const n = parseFloat(valor)
      return Number.isNaN(n) ? valor : n
    }
    return valor
  }
})
</script>
