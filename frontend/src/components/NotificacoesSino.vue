<template>
  <span class="sino-wrapper">
    <button
      class="sino-btn"
      :class="{ 'tem-novas': notificacoes.length > 0 }"
      @click="abrir"
      :aria-label="notificacoes.length ? `Notificações: ${notificacoes.length} nova(s)` : 'Notificações'"
      title="Notificações"
    >
      <i class="fa-solid fa-bell" aria-hidden="true"></i>
      <span v-if="notificacoes.length" class="sino-badge">{{ notificacoes.length }}</span>
    </button>

    <div v-if="aberto" class="modal-overlay" @click.self="fechar">
      <div class="modal sino-modal" role="dialog" aria-modal="true" aria-labelledby="sino-titulo">
        <div class="sino-header">
          <h2 id="sino-titulo">
            <button v-if="selecionada" class="sino-voltar" @click="selecionada = null" aria-label="Voltar">
              <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
            </button>
            {{ selecionada ? 'Tarefas movidas' : 'Notificações' }}
          </h2>
          <button class="sino-fechar" @click="fechar" aria-label="Fechar notificações">
            <i class="fa-solid fa-xmark" aria-hidden="true"></i>
          </button>
        </div>

        <div v-if="!selecionada" class="sino-corpo">
          <p v-if="!notificacoes.length" class="sino-vazio">Nenhuma notificação.</p>
          <button v-for="n in notificacoes" :key="n.id" class="sino-item" @click="selecionada = n">
            <i class="fa-solid fa-arrows-rotate sino-item-icone" aria-hidden="true"></i>
            <span class="sino-item-texto">
              <strong>{{ n.mudancas.length }} {{ n.mudancas.length === 1 ? 'tarefa foi movida' : 'tarefas foram movidas' }} de status</strong>
              <small>Sincronização com o Munka · {{ formatarHora(n.quando) }}</small>
            </span>
            <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
          </button>
        </div>

        <div v-else class="sino-corpo">
          <ul class="sino-lista">
            <li v-for="(m, i) in selecionada.mudancas" :key="i" class="sino-mudanca">
              <span class="sino-mudanca-titulo">
                <span v-if="m.task_id" class="sino-id">#{{ m.task_id }}</span> {{ m.titulo }}
              </span>
              <span class="sino-mudanca-status">
                <span class="badge badge-gray">{{ m.de }}</span>
                <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
                <span class="badge badge-blue">{{ m.para }}</span>
              </span>
            </li>
          </ul>
        </div>

        <div class="sino-rodape" v-if="notificacoes.length">
          <button class="sino-limpar" @click="limparTodas">Limpar notificações</button>
        </div>
      </div>
    </div>
  </span>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useFilaStore } from '../stores/fila'

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

<style scoped>
.sino-wrapper { display: inline-flex; align-items: center; }
.sino-btn {
  position: relative;
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 34px;
  height: 34px;
  border-radius: 99px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.sino-btn:hover { border-color: var(--accent); color: var(--text); }
.sino-btn.tem-novas { color: var(--warning); border-color: var(--warning); }
.sino-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: var(--warning);
  color: #000;
  border-radius: 99px;
  font-size: 0.65rem;
  font-weight: 800;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.sino-modal { max-width: 560px; width: 95vw; max-height: 80vh; display: flex; flex-direction: column; }
.sino-header {
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 2px solid var(--accent); padding-bottom: 0.75rem; margin-bottom: 1rem;
}
.sino-header h2 { font-size: 1rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; }
.sino-fechar, .sino-voltar {
  background: transparent; border: 1px solid var(--border); color: var(--text-muted);
  cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 4px;
}
.sino-fechar:hover { background: #f85149; color: #fff; border-color: #f85149; }
.sino-voltar:hover { border-color: var(--accent); color: var(--text); }
.sino-corpo { overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; }
.sino-vazio { color: var(--text-subtle); text-align: center; padding: 1.5rem 0; }
.sino-item {
  display: flex; align-items: center; gap: 0.75rem; text-align: left; width: 100%;
  background: var(--card-bg); border: 1px solid var(--border); color: var(--text);
  padding: 0.75rem 1rem; border-radius: 6px; cursor: pointer;
}
.sino-item:hover { border-color: var(--accent); }
.sino-item-icone { color: var(--accent); }
.sino-item-texto { flex: 1; display: flex; flex-direction: column; gap: 0.15rem; }
.sino-item-texto small { color: var(--text-subtle); }
.sino-lista { list-style: none; display: flex; flex-direction: column; gap: 0.5rem; }
.sino-mudanca {
  display: flex; flex-direction: column; gap: 0.35rem;
  border: 1px solid var(--border); border-radius: 6px; padding: 0.6rem 0.8rem;
}
.sino-mudanca-titulo { font-weight: 600; word-break: break-word; }
.sino-id { color: var(--text-subtle); font-weight: 700; }
.sino-mudanca-status { display: flex; align-items: center; gap: 0.5rem; color: var(--text-subtle); }
.sino-rodape { margin-top: 1rem; display: flex; justify-content: flex-end; }
.sino-limpar {
  background: transparent; border: 1px solid var(--border); color: var(--text-muted);
  padding: 0.3rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem;
}
.sino-limpar:hover { border-color: var(--accent); color: var(--text); }
</style>
