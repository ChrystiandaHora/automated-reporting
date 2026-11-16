<template>
  <span :class="variant === 'plain' ? '' : [base, cores[variant]]">
    <slot />
  </span>
</template>

<script setup lang="ts">
/** Selo de status/categoria. As cores seguem os tokens badge-* do tema. */
withDefaults(defineProps<{
  variant?: 'green' | 'gray' | 'blue' | 'orange' | 'purple' | 'hpa' | 'plain'
}>(), { variant: 'gray' })

const base = 'inline-block rounded-md px-2.5 py-1 text-[0.72rem] leading-none font-bold tracking-[0.03em] uppercase'

const cores: Record<string, string> = {
  green: 'border border-badge-green-border bg-badge-green text-badge-green-foreground',
  gray: 'border border-border-strong bg-muted text-muted-foreground',
  blue: 'border border-badge-code-border bg-badge-code text-badge-code-foreground',
  orange: 'border border-badge-orange-border bg-badge-orange text-badge-orange-foreground',
  purple: 'border border-badge-purple-border bg-badge-purple text-badge-purple-foreground',
  hpa: 'border border-badge-hpa-border bg-badge-hpa text-badge-hpa-foreground',
  plain: ''
}
</script>
