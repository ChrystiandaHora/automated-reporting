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
      <button class="btn-ghost btn-sm" @click="carregarHistorico">↻ Atualizar</button>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-else-if="items.length === 0" class="empty">
      Nenhuma atividade enviada ainda.
    </div>

    <div v-else class="history-grouped">
      <!-- Percorre os commits agrupados no histórico -->
      <div v-for="grupo in historicoAgrupado" :key="grupo.commit_id" class="commit-group">
        <!-- Cabeçalho do Commit no Histórico -->
        <div class="commit-group-header" @click="alternarGrupo(grupo.commit_id)" style="cursor: pointer; user-select: none;">
          <div class="commit-group-info">
            <span class="collapse-icon">{{ isGrupoColapsado(grupo.commit_id) ? '▶' : '▼' }}</span>
            <span class="commit-label">Commit:</span>
            <router-link :to="`/commits/${grupo.commit_id}`" class="sha-link" @click.stop>
              {{ grupo.commit_id?.slice(0, 12) ?? '-' }}
            </router-link>
            <span class="group-time">Último envio: {{ formatDate(grupo.enviado_em) }}</span>
          </div>
          <span class="job-count-badge">{{ grupo.items.length }} atividade{{ grupo.items.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Tabela das atividades do Commit -->
        <div v-show="!isGrupoColapsado(grupo.commit_id)" class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Data de Envio</th>
                <th width="140">Commit</th>
                <th>Título da Atividade</th>
                <th width="100">Código</th>
                <th width="80">HPA</th>
                <th width="120">Status</th>
                <th width="80" style="text-align: center;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in grupo.items" :key="item.id">
                <td class="col-date">{{ formatDate(item.enviado_em) }}</td>
                <td class="col-commit">
                  <router-link :to="`/commits/${item.commit_id || grupo.commit_id}`" class="sha-link" :title="item.commit_id || grupo.commit_id">
                    {{ (item.commit_id || grupo.commit_id)?.slice(0, 8) ?? '-' }}
                  </router-link>
                </td>
                <td class="col-title" :title="item.titulo">
                  <router-link :to="`/commits/${item.commit_id || grupo.commit_id}`" class="activity-link">
                    {{ item.titulo }}
                  </router-link>
                </td>
                <td><code>{{ item.codigo }}</code></td>
                <td><span class="hpa-badge">{{ item.hpa }}h</span></td>
                <td><span class="badge badge-green">{{ item.status }}</span></td>
                <td>
                  <div class="action-cell">
                    <button class="btn-delete-item" @click="abrirModalConfirmacao(item.id)" title="Remover do histórico">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmação de Exclusão -->
    <div v-if="exibindoModalConfirmacao" class="modal-overlay" @click.self="fecharModalConfirmacao">
      <div class="modal">
        <h2>Confirmar Exclusão</h2>
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
import { ref, onMounted, computed } from 'vue'
import { api, type HistoricoItem } from '../api'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'O que é exibido aqui', text: 'Todas as atividades enviadas com sucesso aos portais de faturamento. Cada linha corresponde a uma atividade individual — um mesmo commit pode gerar múltiplas atividades com códigos diferentes.' },
  { title: 'Código (coluna)', text: 'Código do catálogo de serviços identificado pelo Gemini (ex: 21a, 57b). Determina o tipo de serviço faturado e o valor por hora correspondente.' },
  { title: 'HPA', text: 'Horas Previstas para Execução da Atividade — quantidade de horas faturadas para aquela atividade, conforme o catálogo de serviços.' },
  { title: 'Navegar ao commit', text: 'Clique no hash (8 primeiros caracteres) na coluna Commit para abrir a página de detalhes do commit original.' },
]

const items = ref<HistoricoItem[]>([])
const loading = ref(true)
const toastStore = useToastStore()

const itemParaDeletar = ref<number | null>(null)
const exibindoModalConfirmacao = ref(false)

const gruposColapsados = ref<Record<string, boolean>>({})

function alternarGrupo(commitId: string) {
  gruposColapsados.value[commitId] = !gruposColapsados.value[commitId]
}

function isGrupoColapsado(commitId: string) {
  return !!gruposColapsados.value[commitId]
}

const historicoAgrupado = computed(() => {
  const grupos: Record<string, { commit_id: string; enviado_em: string; items: HistoricoItem[] }> = {}
  
  for (const item of items.value) {
    const key = item.commit_id || 'sem-commit'
    if (!grupos[key]) {
      grupos[key] = {
        commit_id: item.commit_id,
        enviado_em: item.enviado_em,
        items: []
      }
    }
    grupos[key].items.push(item)
  }
  
  // Ordena os grupos pela data de envio mais recente do primeiro item do grupo
  return Object.values(grupos).sort((a, b) => {
    const timeA = new Date(a.enviado_em).getTime()
    const timeB = new Date(b.enviado_em).getTime()
    return timeB - timeA
  })
})

onMounted(async () => {
  await carregarHistorico()
})

async function carregarHistorico() {
  loading.value = true
  try {
    items.value = await api.historico.listar()
  } finally {
    loading.value = false
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
.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--card-border);
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-top: none;
}
table { width: 100%; border-collapse: collapse; }
th {
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(96, 165, 250, 0.3);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  background: rgba(59, 130, 246, 0.04);
}
td { padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.875rem; }
tr:hover td { background: rgba(96, 165, 250, 0.03); }
tr:last-child td { border-bottom: none; }
.sha-link {
  font-family: 'Courier New', monospace;
  color: var(--accent-light);
  text-decoration: none;
  font-size: 0.82rem;
  background: rgba(96, 165, 250, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(96, 165, 250, 0.2);
  transition: all 0.2s ease;
}
.sha-link:hover { background: rgba(96, 165, 250, 0.15); color: #bfdbfe; }
.activity-link { color: var(--text); text-decoration: none; font-weight: 600; transition: color 0.2s; }
.activity-link:hover { color: var(--accent-light); }
code {
  font-size: 0.78rem;
  border: 1px solid rgba(96, 165, 250, 0.3);
  color: #93c5fd;
  background: rgba(96, 165, 250, 0.06);
  padding: 2px 6px;
  font-family: 'Courier New', monospace;
  border-radius: 4px;
}
.hpa-badge {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  color: #fcd34d;
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.25);
  padding: 2px 8px;
  font-size: 0.82rem;
  border-radius: 6px;
}
.action-cell {
  display: flex;
  justify-content: center;
  align-items: center;
}
.btn-delete-item {
  background: transparent;
  border: none;
  color: rgba(248, 113, 113, 0.7);
  cursor: pointer;
  padding: 5px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.btn-delete-item:hover {
  color: #f87171;
  background: rgba(239, 68, 68, 0.08);
  transform: scale(1.05);
}
.col-date {
  white-space: nowrap;
  color: var(--text-muted);
  font-size: 0.82rem;
}
.col-title {
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.btn-danger {
  background: rgba(239, 68, 68, 0.9);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.1rem;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.88rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}
.btn-danger:hover {
  background: #ef4444;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3);
}
.history-count-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 3px 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 99px;
  margin-left: 0.5rem;
  vertical-align: middle;
}
.btn-sm {
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
}

/* Agrupamento do histórico */
.history-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1rem;
}
.commit-group {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
.commit-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--card-border);
  cursor: pointer;
  transition: background 0.15s;
}
.commit-group-header:hover {
  background: rgba(96, 165, 250, 0.04);
}
.commit-group-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}
.collapse-icon {
  font-size: 0.65rem;
  color: var(--text-muted);
  width: 12px;
  display: inline-block;
}
.commit-label {
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--text-subtle, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.group-time {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-left: 0.5rem;
}
.job-count-badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  padding: 3px 9px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 99px;
  margin-left: 1rem;
  flex-shrink: 0;
}
</style>
