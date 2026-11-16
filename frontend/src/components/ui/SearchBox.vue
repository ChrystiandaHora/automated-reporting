<template>
  <div class="relative inline-flex min-w-60 max-w-120 flex-1 items-center">
    <i class="fa-solid pointer-events-none absolute left-3.5 z-2 text-[0.88rem] text-muted-foreground" :class="icon" aria-hidden="true"></i>
    <input
      v-model="model"
      type="text"
      :placeholder="placeholder"
      :aria-label="ariaLabel"
      class="h-[38px] w-full rounded-lg border border-input bg-background px-[2.35rem] text-[0.85rem] text-foreground transition-all duration-200 focus:border-primary focus:ring-3 focus:ring-primary-glow focus:outline-none"
    />
    <button
      v-if="model"
      type="button"
      class="absolute right-2 inline-flex size-6 cursor-pointer items-center justify-center rounded-sm border-none bg-transparent text-[0.78rem] text-muted-foreground transition-all duration-150 hover:bg-border hover:text-foreground"
      aria-label="Limpar busca"
      @click="limpar"
    >
      <i class="fa-solid fa-xmark" aria-hidden="true"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
/** Campo de busca com ícone e botão de limpar. v-model (string). */
withDefaults(defineProps<{
  placeholder?: string
  ariaLabel?: string
  icon?: string
}>(), { icon: 'fa-magnifying-glass' })

const model = defineModel<string>({ default: '' })
const emit = defineEmits<{ clear: [] }>()

function limpar() {
  model.value = ''
  emit('clear')
}
</script>
