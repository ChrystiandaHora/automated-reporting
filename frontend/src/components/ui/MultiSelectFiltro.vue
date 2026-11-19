<template>
  <div ref="raiz" class="relative">
    <button
      type="button"
      :class="[campo, 'flex h-9.5 w-full cursor-pointer items-center justify-between gap-2 py-0 text-left']"
      :aria-expanded="aberto"
      aria-haspopup="listbox"
      :aria-label="ariaLabel"
      @click="aberto = !aberto"
    >
      <span class="truncate" :class="model.length ? 'text-foreground' : 'text-muted-foreground'">{{ resumo }}</span>
      <i class="fa-solid fa-chevron-down text-xs text-muted-foreground" aria-hidden="true"></i>
    </button>
    <div
      v-if="aberto"
      class="absolute left-0 z-50 mt-1 max-h-64 min-w-full overflow-y-auto rounded-lg border border-border-strong bg-card p-1 shadow-lg"
      role="listbox"
      aria-multiselectable="true"
    >
      <label
        v-for="o in opcoes"
        :key="o.valor"
        class="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-1.5 text-sm whitespace-nowrap hover:bg-slate-400/10"
      >
        <input type="checkbox" class="size-4 cursor-pointer accent-primary" :value="o.valor" v-model="model" />
        <span>{{ o.rotulo }}</span>
      </label>
      <p v-if="!opcoes.length" class="px-2.5 py-1.5 text-sm text-muted-foreground">Sem opções</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { campo } from './campo'

/** Dropdown de seleção múltipla com checkboxes. v-model é a lista de valores marcados. */
const props = defineProps<{
  opcoes: { valor: string; rotulo: string }[]
  placeholder: string
  ariaLabel?: string
}>()

const model = defineModel<string[]>({ default: () => [] })
const aberto = ref(false)
const raiz = ref<HTMLElement | null>(null)

const resumo = computed(() => {
  if (!model.value.length) return props.placeholder
  if (model.value.length === 1) {
    return props.opcoes.find(o => o.valor === model.value[0])?.rotulo ?? model.value[0]
  }
  return `${model.value.length} selecionados`
})

function aoClicarFora(e: MouseEvent) {
  if (raiz.value && !raiz.value.contains(e.target as Node)) aberto.value = false
}
function aoTeclar(e: KeyboardEvent) {
  if (e.key === 'Escape') aberto.value = false
}

onMounted(() => {
  document.addEventListener('click', aoClicarFora)
  document.addEventListener('keydown', aoTeclar)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', aoClicarFora)
  document.removeEventListener('keydown', aoTeclar)
})
</script>
