<template>
  <span class="inline-flex items-center">
    <button
      class="relative inline-flex size-[34px] cursor-pointer items-center justify-center rounded-full border bg-card transition-all duration-200"
      :class="notificacoes.length ? 'border-warning text-warning' : 'border-border-strong text-muted-foreground hover:border-primary hover:text-foreground'"
      @click="abrir"
      :aria-label="notificacoes.length ? `Notificações: ${notificacoes.length} nova(s)` : 'Notificações'"
      title="Notificações"
    >
      <i class="fa-solid fa-bell" aria-hidden="true"></i>
      <span v-if="notificacoes.length" class="absolute -top-[5px] -right-[5px] inline-flex h-[17px] min-w-[17px] items-center justify-center rounded-full bg-warning px-1 text-[0.65rem] font-extrabold text-black">{{ notificacoes.length }}</span>
    </button>

    <BaseModal v-if="aberto" size="auto" labelledby="sino-titulo" class="max-h-[80vh] w-[95vw] max-w-140" @close="fechar">
        <div class="mb-4 flex items-center justify-between border-b-2 border-primary pb-3">
          <h2 id="sino-titulo" class="flex items-center gap-2 text-base font-extrabold text-foreground">
            <button v-if="selecionada" class="cursor-pointer rounded-sm border border-border-strong bg-transparent px-2 py-0.5 text-muted-foreground hover:border-primary hover:text-foreground" @click="selecionada = null" aria-label="Voltar">
              <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
            </button>
            {{ selecionada ? 'Tarefas movidas' : 'Notificações' }}
          </h2>
          <button class="cursor-pointer rounded-sm border border-border-strong bg-transparent px-2 py-0.5 text-muted-foreground hover:border-canvas-danger hover:bg-canvas-danger hover:text-white" @click="fechar" aria-label="Fechar notificações">
            <i class="fa-solid fa-xmark" aria-hidden="true"></i>
          </button>
        </div>

        <div v-if="!selecionada" class="flex flex-col gap-2 overflow-y-auto">
          <p v-if="!notificacoes.length" class="py-6 text-center text-subtle-foreground">Nenhuma notificação.</p>
          <button v-for="n in notificacoes" :key="n.id" class="flex w-full cursor-pointer items-center gap-3 rounded-md border border-border-strong bg-card px-4 py-3 text-left text-foreground hover:border-primary" @click="selecionada = n">
            <i class="fa-solid fa-arrows-rotate text-primary" aria-hidden="true"></i>
            <span class="flex flex-1 flex-col gap-0.5">
              <strong>{{ n.mudancas.length }} {{ n.mudancas.length === 1 ? 'tarefa foi movida' : 'tarefas foram movidas' }} de status</strong>
              <small class="text-subtle-foreground">Sincronização com o Munka · {{ formatarHora(n.quando) }}</small>
            </span>
            <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
          </button>
        </div>

        <div v-else class="flex flex-col gap-2 overflow-y-auto">
          <ul class="flex list-none flex-col gap-2">
            <li v-for="(m, i) in selecionada.mudancas" :key="i" class="flex flex-col gap-1.5 rounded-md border border-border-strong px-3 py-2.5">
              <span class="font-semibold break-words">
                <span v-if="m.task_id" class="font-bold text-subtle-foreground">#{{ m.task_id }}</span> {{ m.titulo }}
              </span>
              <span class="flex items-center gap-2 text-subtle-foreground">
                <BaseBadge variant="gray">{{ m.de }}</BaseBadge>
                <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
                <BaseBadge variant="blue">{{ m.para }}</BaseBadge>
              </span>
            </li>
          </ul>
        </div>

        <div class="mt-4 flex justify-end" v-if="notificacoes.length">
          <button class="cursor-pointer rounded-sm border border-border-strong bg-transparent px-3 py-1.5 text-[0.8rem] text-muted-foreground hover:border-primary hover:text-foreground" @click="limparTodas">Limpar notificações</button>
        </div>
    </BaseModal>
  </span>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useFilaStore } from '../stores/fila'
import BaseModal from './ui/BaseModal.vue'
import BaseBadge from './ui/BaseBadge.vue'

interface Mudanca { task_id?: string; titulo: string; de: string; para: string }
interface Notificacao { id: number; quando: string; mudancas: Mudanca[] }

const JANELA_MS = 24 * 60 * 60 * 1000

const filaStore = useFilaStore()
// Só em memória: ao recarregar a página, os avisos recentes voltam a aparecer.
const dispensadas = ref<Set<number>>(new Set())
const aberto = ref(false)
const selecionada = ref<Notificacao | null>(null)

// Derivadas dos jobs de sincronização já concluídos; nada é persistido.
const notificacoes = computed<Notificacao[]>(() => {
  const limite = Date.now() - JANELA_MS
  const lista: Notificacao[] = []
  for (const j of filaStore.jobs) {
    if (j.tipo !== 'verificacao' || j.status !== 'done' || dispensadas.value.has(j.id)) continue
    const quando = j.concluido_em || j.criado_em
    if (new Date(quando).getTime() < limite) continue
    const mudancas = j.resultado?.mudancas
    if (Array.isArray(mudancas) && mudancas.length > 0) {
      lista.push({ id: j.id, quando, mudancas })
    }
  }
  return lista.sort((a, b) => b.quando.localeCompare(a.quando))
})

function formatarHora(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function abrir() { aberto.value = true; selecionada.value = null }
function fechar() { aberto.value = false; selecionada.value = null }
function limparTodas() {
  const novo = new Set(dispensadas.value)
  notificacoes.value.forEach(n => novo.add(n.id))
  dispensadas.value = novo
  selecionada.value = null
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') fechar()
}
watch(aberto, v => {
  if (v) document.addEventListener('keydown', onKeydown)
  else document.removeEventListener('keydown', onKeydown)
})
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>
