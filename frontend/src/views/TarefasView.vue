<template>
  <div class="tarefas-wrapper">
    <div class="tarefas-tabs" role="tablist" aria-label="Visões de Tarefas do Mês">
      <router-link
        v-for="aba in abas"
        :key="aba.to"
        :to="aba.to"
        class="tarefas-tab"
        role="tab"
        :aria-selected="route.path === aba.to"
        :class="{ active: route.path === aba.to }"
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

<style scoped>
.tarefas-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 2px solid var(--border);
  margin-bottom: 1rem;
}
.tarefas-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-muted);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
}
.tarefas-tab:hover { color: var(--text); background: rgba(148, 163, 184, 0.08); }
.tarefas-tab.active { color: var(--text); border-bottom-color: var(--accent); background: var(--accent-glow); }
</style>
