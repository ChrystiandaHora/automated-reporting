import { defineStore } from 'pinia'
import { ref } from 'vue'

/** Período (mês/ano) compartilhado entre as abas Lista e Kanban de Tarefas. */
export const useTarefasMesStore = defineStore('tarefasMes', () => {
  const hoje = new Date()
  const mes = ref<number>(hoje.getMonth() + 1)
  const ano = ref<number>(hoje.getFullYear())
  return { mes, ano }
})
