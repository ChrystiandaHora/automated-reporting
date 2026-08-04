<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Histórico de Envios</h1>
        <HelpModal title="Histórico de Envios" :items="helpItems" />
        <span v-if="items.length > 0" class="history-count-badge">
          {{ items.length }} atividade{{ items.length > 1 ? 's' : '' }}
        </span>
      </div>
      <button class="btn-ghost btn-sm" @click="carregarHistorico()">↻ Atualizar</button>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-else-if="items.length === 0" class="empty">
      Nenhuma atividade enviada ainda.
    </div>

    <div v-else class="history-list-grouped">
      <!-- Percorre os dias agrupados por data (data do commit ou envio) -->
      <div v-for="grupo in historicoAgrupado" :key="grupo.data" class="date-group">
        
        <!-- Cabeçalho do dia: "23 Jun, 2026 - 3 atividades" -->
        <div class="date-group-header">
          <span class="date-text">{{ grupo.data }}</span>
          <span class="commit-count-text">{{ grupo.items.length }} atividade{{ grupo.items.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Lista de atividades enviadas desse dia -->
        <div class="date-group-items">
          <div 
            v-for="item in grupo.items" 
            :key="item.id" 
            class="history-row"
          >
            <!-- Lado Esquerdo: Avatar do Autor do Commit -->
            <div 
              class="history-avatar" 
              :style="{ backgroundColor: obterCorAvatar(item.commit_autor || 'Sistema') }"
              :title="item.commit_autor || 'Autor não informado'"
            >
              {{ obterIniciais(item.commit_autor || 'SI') }}
            </div>

            <!-- Centro: Título da atividade, Badges e Informações do Commit -->
            <div class="history-info">
              <div class="history-title-container">
                <span class="history-title" :title="item.titulo">
                  {{ item.titulo }}
                </span>
                
                <!-- Badges: Código, HPA e Status -->
                <div class="history-row-badges">
                  <span class="badge badge-code"><code>{{ item.codigo }}</code></span>
                  <span class="hpa-badge">{{ item.hpa }}h</span>
                  <span class="badge" :class="item.tem_data_fim === false || item.status?.includes('Sem Data Fim') || item.status?.includes('Incompleta') ? 'badge-orange' : 'badge-green'">
                    {{ item.tem_data_fim === false ? '⚠️ Sem Data Fim' : item.status }}
                  </span>
                </div>
              </div>

              <div class="history-sub-info">
                <span v-if="item.commit_mensagem" class="history-commit-msg" :title="item.commit_mensagem">
                  Commit: {{ item.commit_mensagem }}
                </span>
                <span class="history-time-info">
                  Enviado {{ obterTempoRelativo(item.enviado_em) }} ({{ formatDate(item.enviado_em) }})
                </span>
              </div>
            </div>

            <!-- Lado Direito: Link para o Commit e Ações -->
            <div class="history-actions" @click.stop>
              <!-- SHA Box Link -->
              <router-link 
                v-if="item.commit_id" 
                :to="`/commits/${item.commit_id}`" 
                class="sha-box-link"
                :title="`Ver detalhes do commit ${item.commit_id}`"
              >
                {{ item.commit_id.slice(0, 8) }}
              </router-link>

              <!-- Botão Re-enviar / Retry -->
              <button 
                class="btn-ghost btn-sm btn-reenviar-history" 
                @click="reenviarItemHistorico(item)"
                title="Re-enviar esta atividade ao portal Munka"
              >
                ↻ Re-enviar
              </button>

              <!-- Botão Excluir -->
              <button 
                class="action-btn delete-btn" 
                @click="abrirModalConfirmacao(item.id)"
                title="Remover do histórico"
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" stroke="#f85149" fill="none" />
                  <line x1="15" y1="9" x2="9" y2="15" stroke="#f85149" />
                  <line x1="9" y1="9" x2="15" y2="15" stroke="#f85149" />
                </svg>
              </button>
            </div>

          </div>
        </div>

      </div>
    </div>

    <!-- Modal de Confirmação de Exclusão -->
    <div v-if="exibindoModalConfirmacao" class="modal-overlay" @click.self="fecharModalConfirmacao">
      <div ref="confirmModalRef" class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
        <h2 id="confirm-modal-title">Confirmar Exclusão</h2>
        <p>Tem certeza de que deseja remover esta atividade do histórico? Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="fecharModalConfirmacao">Cancelar</button>
          <button class="btn-danger" @click="confirmarExclusao">Excluir</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { api, type HistoricoItem } from '../api'
import { useToastStore } from '../stores/toast'
import { useFilaStore } from '../stores/fila'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'O que é exibido aqui', text: 'Todas as atividades enviadas com sucesso aos portais de faturamento. Organizadas por data de commit e envio de forma cronológica.' },
  { title: 'Código (coluna)', text: 'Código do catálogo de serviços identificado pelo Gemini (ex: 21a, 57b). Determina o tipo de serviço faturado e o valor por hora correspondente.' },
  { title: 'HPA', text: 'Horas Previstas para Execução da Atividade — quantidade de horas faturadas para aquela atividade, conforme o catálogo de serviços.' },
  { title: 'Navegar ao commit', text: 'Clique no botão com o hash do commit (SHA) para abrir a página de detalhes do commit original.' },
]

const items = ref<HistoricoItem[]>([])
const loading = ref(true)
const toastStore = useToastStore()
const filaStore = useFilaStore()

let timerHistorico: any = null

const itemParaDeletar = ref<number | null>(null)
const exibindoModalConfirmacao = ref(false)

const confirmModalRef = ref<HTMLElement | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

function handleConfirmKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    fecharModalConfirmacao()
  }
  if (e.key === 'Tab' && confirmModalRef.value) {
    const focusable = confirmModalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    if (focusable.length === 0) return
    const first = focusable[0] as HTMLElement
    const last = focusable[focusable.length - 1] as HTMLElement
    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus()
        e.preventDefault()
      }
    } else {
      if (document.activeElement === last) {
        first.focus()
        e.preventDefault()
      }
    }
  }
}

watch(exibindoModalConfirmacao, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleConfirmKeydown)
    nextTick(() => {
      const btn = confirmModalRef.value?.querySelector('.modal-actions button') as HTMLElement
      btn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleConfirmKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

async function reenviarItemHistorico(item: HistoricoItem) {
  if (!item.commit_id) {
    toastStore.addToast('Commit ID não encontrado para esta atividade', 'error')
    return
  }
  if (confirm(`Deseja re-enviar a atividade "${item.titulo}" ao portal?`)) {
    try {
      // Busca a análise do commit para encontrar o índice correto da atividade pelo título
      const analise = await api.analise.obter(item.commit_id)
      const idx = analise.atividades.findIndex((a: any) => a.titulo === item.titulo)
      if (idx === -1) {
        toastStore.addToast(`Atividade "${item.titulo}" não encontrada na análise do commit`, 'error')
        return
      }
      await filaStore.enfileirarEnvio(item.commit_id, idx)
      toastStore.addToast('Envio adicionado à fila com sucesso!', 'success')
    } catch (e: any) {
      toastStore.addToast(`Erro ao enfileirar re-envio: ${e.message || e}`, 'error')
    }
  }
}

onMounted(async () => {
  await carregarHistorico()
  timerHistorico = setInterval(async () => {
    await carregarHistorico(true)
  }, 30000)
})

onUnmounted(() => {
  if (timerHistorico) {
    clearInterval(timerHistorico)
    timerHistorico = null
  }
})

async function carregarHistorico(quiet: boolean | Event = false) {
  const isQuiet = typeof quiet === 'boolean' ? quiet : false
  if (!isQuiet) loading.value = true
  try {
    items.value = await api.historico.listar()
  } finally {
    if (!isQuiet) loading.value = false
  }
}

function formatarDataCabecalho(dataStr: string): string {
  if (!dataStr) return 'Outras datas'
  const parts = dataStr.split('/')
  if (parts.length === 3) {
    const dia = parseInt(parts[0], 10)
    const mesIdx = parseInt(parts[1], 10) - 1
    const ano = parts[2]
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const mesNome = meses[mesIdx] || parts[1]
    return `${dia} ${mesNome}, ${ano}`
  }
  return dataStr
}

function obterDataParaAgrupamento(item: HistoricoItem): string {
  // 1. Prioriza data_autor do commit
  if (item.commit_data_autor) {
    try {
      const d = new Date(item.commit_data_autor)
      if (!isNaN(d.getTime())) {
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const ano = d.getFullYear()
        return `${dia}/${mes}/${ano}`
      }
    } catch {
      // fallback
    }
  }
  // 2. Data formatada do commit (DD/MM/YYYY)
  if (item.commit_data) {
    return item.commit_data
  }
  // 3. Data de envio da atividade (enviado_em)
  if (item.enviado_em) {
    try {
      const d = new Date(item.enviado_em)
      if (!isNaN(d.getTime())) {
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const ano = d.getFullYear()
        return `${dia}/${mes}/${ano}`
      }
    } catch {
      // fallback
    }
  }
  return 'Outras datas'
}

function obterTime(item: HistoricoItem): number {
  if (item.commit_data_autor) {
    const t = new Date(item.commit_data_autor).getTime()
    if (!isNaN(t)) return t
  }
  if (item.commit_data) {
    const parts = item.commit_data.split('/')
    if (parts.length === 3) {
      const t = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0])).getTime()
      if (!isNaN(t)) return t
    }
  }
  if (item.enviado_em) {
    const t = new Date(item.enviado_em).getTime()
    if (!isNaN(t)) return t
  }
  return 0
}

function obterIniciais(nome?: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

function obterCorAvatar(nome?: string): string {
  if (!nome) return '#777'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    '#007acc', // Blue
    '#3fb950', // Green
    '#f85149', // Red
    '#d29922', // Orange/Yellow
    '#bc8cff', // Purple
    '#1f6feb', // Light Blue
    '#30b6e6'  // Cyan
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function obterTempoRelativo(isoStr?: string): string {
  if (!isoStr) return 'há algum tempo'
  try {
    const d = new Date(isoStr)
    const agora = new Date()
    const diffMs = agora.getTime() - d.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'agora mesmo'
    if (diffMin === 1) return 'há 1 minuto'
    if (diffMin < 60) return `há ${diffMin} minutos`
    if (diffHour === 1) return 'há 1 hora'
    if (diffHour < 24) return `há ${diffHour} horas`
    if (diffDay === 1) return 'ontem'
    return `há ${diffDay} dias`
  } catch {
    return 'há algum tempo'
  }
}

function formatDate(iso: string) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString('pt-BR')
  } catch {
    return iso
  }
}

const historicoAgrupado = computed(() => {
  const grupos: Record<string, HistoricoItem[]> = {}
  
  for (const item of items.value) {
    const dataAgrupamento = obterDataParaAgrupamento(item)
    const dataFormatada = formatarDataCabecalho(dataAgrupamento)
    if (!grupos[dataFormatada]) {
      grupos[dataFormatada] = []
    }
    grupos[dataFormatada].push(item)
  }
  
  for (const chave of Object.keys(grupos)) {
    grupos[chave].sort((a, b) => obterTime(b) - obterTime(a))
  }
  
  const chavesOrdenadas = Object.keys(grupos).sort((a, b) => {
    const timeA = obterTime(grupos[a][0])
    const timeB = obterTime(grupos[b][0])
    return timeB - timeA
  })
  
  return chavesOrdenadas.map(chave => ({
    data: chave,
    items: grupos[chave]
  }))
})

function abrirModalConfirmacao(id: number) {
  itemParaDeletar.value = id
  exibindoModalConfirmacao.value = true
}

function fecharModalConfirmacao() {
  itemParaDeletar.value = null
  exibindoModalConfirmacao.value = false
}

async function confirmarExclusao() {
  if (itemParaDeletar.value === null) return
  try {
    await api.historico.remover(itemParaDeletar.value)
    items.value = items.value.filter(i => i.id !== itemParaDeletar.value)
    toastStore.addToast('Item removido do histórico.', 'info')
  } catch (e: any) {
    toastStore.addToast(`Erro ao remover: ${e.response?.data?.detail ?? String(e)}`, 'error')
  } finally {
    fecharModalConfirmacao()
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }

.history-count-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--header-group-bg);
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 99px;
  margin-left: 0.5rem;
  vertical-align: middle;
}

.btn-sm {
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
}

/* Agrupamento por Data (idêntico a CommitsView) */
.history-list-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1rem;
}

.date-group {
  display: flex;
  flex-direction: column;
}

.date-group-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--header-group-bg);
  border: 1px solid var(--card-border);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  font-size: 0.88rem;
}

.date-text {
  font-weight: 800;
  color: var(--text);
  font-size: 0.95rem;
}

.commit-count-text {
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 500;
}

.date-group-items {
  border: 1px solid var(--card-border);
  border-top: none;
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
}

.history-row {
  display: flex;
  align-items: center;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.history-row:last-child {
  border-bottom: none;
}

.history-row:hover {
  background: var(--accent-glow);
}

.history-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
  margin-right: 1rem;
  flex-shrink: 0;
  border: 1px solid var(--border);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.history-title-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.history-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 450px;
}

.history-row-badges {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.badge-code code {
  font-size: 0.75rem;
  border: 1px solid var(--badge-code-border);
  color: var(--badge-code-color);
  background: var(--badge-code-bg);
  padding: 1px 5px;
  font-family: 'Courier New', monospace;
  border-radius: 4px;
}

.hpa-badge {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  color: var(--badge-hpa-color);
  background: var(--badge-hpa-bg);
  border: 1px solid var(--badge-hpa-border);
  padding: 1px 6px;
  font-size: 0.75rem;
  border-radius: 6px;
}

.history-sub-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.history-commit-msg {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 350px;
  color: var(--text-muted);
}

.history-time-info {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  margin-left: 1rem;
}

.sha-box-link {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: var(--sha-box-color);
  background: var(--sha-box-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.6rem;
  letter-spacing: 0.04em;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.15s;
}

.sha-box-link:hover {
  background: var(--accent-glow);
  color: var(--accent);
  border-color: var(--accent);
}

.action-btn {
  background: var(--bg);
  border: 2px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem;
  transition: border-color 0.12s, color 0.12s, transform 0.1s;
}

.btn-reenviar-history {
  color: var(--accent, #58a6ff);
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  border: 1px solid var(--border);
}

.btn-reenviar-history:hover {
  background: var(--accent-glow, rgba(88, 166, 255, 0.1));
  border-color: var(--accent, #58a6ff);
}

.delete-btn {
  border: none;
  background: transparent;
  padding: 0.25rem;
  color: #f85149;
  opacity: 0.85;
  transition: opacity 0.12s, transform 0.1s;
}

.delete-btn:hover {
  opacity: 1;
  transform: scale(1.1);
  color: #ff6b6b;
}

.btn-danger {
  background: #f85149;
  color: #ffffff;
  border: 2px solid var(--border);
  border-radius: 0;
  padding: 0.5rem 1.1rem;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.88rem;
  letter-spacing: 0.02em;
  box-shadow: 3px 3px 0 var(--border);
  transition: transform 0.1s, box-shadow 0.1s;
}

.btn-danger:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 5px 5px 0 var(--border);
  background: #ff6b6b;
}
</style>
