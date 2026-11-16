<template>
  <textarea v-model="model" :class="[campo, autoWidth ? '' : 'w-full']"></textarea>
</template>

<script setup lang="ts">
import { campo } from './campo'

/** Área de texto padrão. Suporta v-model e v-model.trim. */
defineProps<{ autoWidth?: boolean }>()

const [model, modifiers] = defineModel<string | null | undefined>({
  set(valor) {
    return modifiers.trim && typeof valor === 'string' ? valor.trim() : valor
  }
})
</script>
