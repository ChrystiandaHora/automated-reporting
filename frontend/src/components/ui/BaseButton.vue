<template>
  <component :is="to ? RouterLink : 'button'" :to="to" :type="to ? undefined : type" :class="classes">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

/**
 * Botão padrão do sistema. Cores e tamanhos vêm só daqui: para mudar o visual de
 * todos os botões, edite este arquivo. Não passe utilidades que conflitem com a
 * variante/tamanho (padding, cor, borda); para um botão totalmente próprio use
 * variant="plain" e traga as utilidades na tela.
 */
const props = withDefaults(defineProps<{
  variant?: 'primary' | 'ghost' | 'danger' | 'plain'
  size?: 'md' | 'sm' | 'xs'
  type?: 'button' | 'submit' | 'reset'
  /** Quando informado, renderiza um router-link com o mesmo visual do botão. */
  to?: RouteLocationRaw
}>(), {
  variant: 'ghost',
  size: 'md',
  type: 'button'
})

const base = 'inline-flex cursor-pointer no-underline items-center justify-center gap-2 font-semibold leading-none transition-all duration-200 disabled:cursor-not-allowed'

const variantes: Record<string, string> = {
  primary: 'border-none bg-primary text-white shadow-[0_4px_12px] shadow-primary-glow hover:enabled:-translate-y-px hover:enabled:brightness-110 active:enabled:translate-y-0 disabled:opacity-40 disabled:shadow-none',
  ghost: 'border border-border-strong bg-card text-foreground hover:enabled:-translate-y-px hover:enabled:border-primary hover:enabled:text-primary disabled:opacity-40',
  danger: 'border-none bg-canvas-danger text-white hover:enabled:bg-canvas-danger-hover disabled:opacity-40',
  plain: ''
}

const tamanhos: Record<string, string> = {
  md: 'rounded-lg px-5 py-2.5 text-[0.88rem] tracking-[0.01em]',
  sm: 'rounded-md px-3.25 py-1.5 text-[0.82rem]',
  xs: 'rounded-[5px] px-2.25 py-1 text-xs'
}

const classes = computed(() => props.variant === 'plain'
  ? [base]
  : [base, variantes[props.variant], tamanhos[props.size]])
</script>
