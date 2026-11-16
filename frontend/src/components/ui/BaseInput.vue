<template>
  <input v-model="model" :class="[campo, autoWidth ? '' : 'w-full']" />
</template>

<script setup lang="ts">
import { campo } from './campo'

/**
 * Campo de texto/número/data. Suporta v-model, v-model.number e v-model.trim.
 * Não use para checkbox, radio, range ou file (estilize direto com utilidades).
 * `autoWidth` remove a largura 100% quando a tela define a largura do campo.
 */
defineProps<{ autoWidth?: boolean }>()

const [model, modifiers] = defineModel<string | number | null | undefined>({
  set(valor) {
    if (modifiers.trim && typeof valor === 'string') valor = valor.trim()
    if (modifiers.number && typeof valor === 'string') {
      const n = parseFloat(valor)
      return Number.isNaN(n) ? valor : n
    }
    return valor
  }
})
</script>
