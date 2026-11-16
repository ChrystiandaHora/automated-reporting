<template>
  <div>
    <div class="mb-4 flex gap-1 border-b-2 border-border-strong" role="tablist" aria-label="Visões de Tarefas do Mês">
      <router-link
        v-for="aba in abas"
        :key="aba.to"
        :to="aba.to"
        class="-mb-0.5 inline-flex items-center gap-1.5 border-b-2 px-5 py-2 text-[0.85rem] font-bold no-underline transition-all hover:bg-slate-400/10 hover:text-foreground"
        role="tab"
        :aria-selected="route.path === aba.to"
        :class="route.path === aba.to ? 'border-primary bg-primary-glow text-foreground' : 'border-transparent text-muted-foreground'"
      >
        <i :class="aba.icon" aria-hidden="true"></i>
        <span>{{ aba.label }}</span>
      </router-link>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
const abas = [
  { to: '/tarefas-mes/lista', label: 'Lista', icon: 'fa-solid fa-list-check' },
  { to: '/tarefas-mes/kanban', label: 'Kanban', icon: 'fa-solid fa-table-columns' }
]
</script>
