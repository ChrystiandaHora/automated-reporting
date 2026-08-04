<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Commits</h1>
        <HelpModal title="Como funciona esta página" :items="helpItems" />
      </div>
      <button class="btn-primary" @click="showImport = true">+ Importar Commit</button>
    </div>

    <!-- Modal de importação -->
    <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
      <div ref="importModalRef" class="modal" role="dialog" aria-modal="true" aria-labelledby="import-modal-title">
        <h2 id="import-modal-title">Importar Commits do GitLab (Lote)</h2>
        <label for="import-commit-hashes">URLs Completas dos Commits do GitLab (uma por linha)</label>
        <textarea 
          id="import-commit-hashes"
          v-model="form.commit_hashes" 
          placeholder="Ex:&#10;https://gitlab.suaorganizacao.com/grupo/projeto/-/commit/abc123hash" 
          rows="6"
        ></textarea>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showImport = false">Cancelar</button>
          <button class="btn-primary" :disabled="importing || !form.commit_hashes.trim()" @click="importar">
            {{ importing ? 'Importando...' : 'Importar' }}
          </button>
        </div>
        <p v-if="importError" class="error">{{ importError }}</p>
      </div>
    </div>

    <!-- Painel de KPIs de Tarefas por Tipo -->
    <div v-if="store.stats" class="kpi-panel">
      <div class="kpi-panel-header">
        <div class="kpi-panel-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <h2>Indicadores de Tarefas por Tipo</h2>
        </div>

        <!-- Filtro Mês a Mês -->
        <div class="kpi-filter-box">
          <label for="mes-filtro" class="kpi-filter-label">Mês:</label>
          <select id="mes-filtro" v-model="mesSelecionado" class="kpi-select">
            <option value="todos">Todos os Meses</option>
            <option v-for="m in store.stats.months" :key="m" :value="m">
              {{ formatarMesExtenso(m) }}
            </option>
          </select>
        </div>
      </div>

      <!-- Resumo Geral -->
      <div class="kpi-summary-cards">
        <div class="kpi-card highlight">
          <span class="kpi-card-label">Total de Tarefas</span>
          <span class="kpi-card-val">{{ statsExibidas.total_tasks }}</span>
          <span class="kpi-card-sub">atividades identificadas</span>
        </div>
        <div class="kpi-card highlight-green">
          <span class="kpi-card-label">Total Horas HPA</span>
          <span class="kpi-card-val">{{ statsExibidas.total_hpa }}h</span>
          <span class="kpi-card-sub">faturamento previsto</span>
        </div>
        <div class="kpi-card highlight-purple">
          <span class="kpi-card-label">Tipos Distintos</span>
          <span class="kpi-card-val">{{ Object.keys(statsExibidas.codes).length }}</span>
          <span class="kpi-card-sub">códigos de serviço</span>
        </div>
      </div>

      <!-- Quantificação por Código de Serviço (ex: 21a - 10, 21b - 3) -->
      <div class="kpi-codes-section">
        <div class="kpi-section-title">Quantificação por Tipo de Serviço:</div>
        
        <div v-if="Object.keys(statsExibidas.codes).length === 0" class="kpi-empty">
          Nenhuma atividade registrada para o período selecionado.
        </div>

        <div v-else class="kpi-codes-grid">
          <div 
            v-for="(info, code) in statsExibidas.codes" 
            :key="code"
            class="kpi-code-card"
          >
            <div class="kpi-code-header">
              <span class="badge badge-code"><code>{{ code }}</code></span>
              <span class="kpi-code-count">{{ info.count }} tarefa{{ info.count > 1 ? 's' : '' }}</span>
            </div>
            <div class="kpi-code-footer">
              <span class="kpi-code-hpa">{{ info.hpa }}h HPA</span>
              <span class="kpi-code-pct" v-if="statsExibidas.total_tasks > 0">
                {{ Math.round((info.count / statsExibidas.total_tasks) * 100) }}%
              </span>
            </div>
            <!-- Barra de Progresso Visual -->
            <div class="kpi-progress-bar">
              <div 
                class="kpi-progress-fill" 
                :style="{ width: `${statsExibidas.total_tasks > 0 ? (info.count / statsExibidas.total_tasks) * 100 : 0}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.loading" class="loading">Carregando commits...</div>

    <div v-else-if="store.commits.length === 0" class="empty">
      Nenhum commit importado. Clique em "+ Importar Commit" para começar.
    </div>

    <div v-else class="commit-list-grouped">
      <!-- Percorre os dias agrupados -->
      <div v-for="grupo in commitsAgrupados" :key="grupo.data" class="date-group">
        
        <!-- Cabeçalho do dia: "23 Jun, 2026 3 commits" -->
        <div class="date-group-header">
          <span class="date-text">{{ grupo.data }}</span>
          <span class="commit-count-text">{{ grupo.commits.length }} commit{{ grupo.commits.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Lista de commits desse dia -->
        <div class="date-group-commits">
          <div 
            v-for="commit in grupo.commits" 
            :key="commit.id" 
            class="commit-row"
            tabindex="0"
            role="link"
            @click="$router.push(`/commits/${commit.id}`)"
            @keydown.enter.prevent="$router.push(`/commits/${commit.id}`)"
            @keydown.space.prevent="$router.push(`/commits/${commit.id}`)"
          >
            <!-- Lado Esquerdo: Avatar do Autor -->
            <div 
              class="commit-avatar" 
              :style="{ backgroundColor: obterCorAvatar(commit.autor) }"
              :title="commit.autor"
            >
              {{ obterIniciais(commit.autor) }}
            </div>

            <!-- Centro: Mensagem e Metadados -->
            <div class="commit-info">
              <div class="commit-msg-container">
                <span class="commit-msg-title" :title="commit.mensagem">
                  {{ commit.mensagem || '(sem mensagem)' }}
                </span>
                <!-- Badge de Status de Envio de Atividades -->
                <div class="commit-row-badges">
                  <span class="badge badge-status" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
                    {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                  </span>
                  <template v-if="commit.analisado">
                    <span class="badge badge-status" :class="
                      (commit.atividades_enviadas || 0) === (commit.atividades_total || 0) && (commit.atividades_total || 0) > 0
                        ? 'badge-blue'
                        : (commit.atividades_enviadas || 0) > 0
                          ? 'badge-orange'
                          : 'badge-purple'
                    ">
                      {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
                    </span>
                  </template>
                </div>
              </div>
              <span class="commit-author-time">
                {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
              </span>
            </div>

            <!-- Lado Direito: Ações e SHA -->
            <div class="commit-actions" @click.stop>
              <!-- Botão Excluir (qualquer commit importado) -->
              <button 
                class="action-btn delete-btn" 
                @click="abrirModalConfirmacao(commit)"
                title="Excluir commit"
              >
                <!-- Círculo vermelho com X -->
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" stroke="#f85149" fill="none" />
                  <line x1="15" y1="9" x2="9" y2="15" stroke="#f85149" />
                  <line x1="9" y1="9" x2="15" y2="15" stroke="#f85149" />
                </svg>
              </button>

              <!-- SHA Box -->
              <span class="sha-box">{{ commit.id.slice(0, 8) }}</span>

              <!-- Botão Copiar SHA -->
              <button 
                class="action-btn copy-btn" 
                @click="copiarSHA(commit.id)"
                title="Copiar SHA completo"
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>

              <!-- Botão Navegar (Folder) -->
              <button 
                class="action-btn folder-btn" 
                @click="$router.push(`/commits/${commit.id}`)"
                title="Ver detalhes da análise"
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
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
        <p>Tem certeza de que deseja excluir o commit <strong>{{ commitParaDeletar?.id.slice(0, 8) }}</strong> e sua respectiva análise? Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="fecharModalConfirmacao">Cancelar</button>
          <button class="btn-danger" @click="confirmarExclusao">Excluir</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useCommitsStore } from '../stores/commits'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Importar Commit', text: 'Clique em "+ Importar Commit" e informe um ou mais SHAs ou URLs completos do GitLab (um por linha) para importação.' },
  { title: 'PRIVATE-TOKEN do GitLab', text: 'Token de acesso pessoal do GitLab. Gere em: GitLab → Preferências → Tokens de Acesso → Escopo "read_repository". Salve na página de Configuração.' },
  { title: 'Status dos commits', text: '"Analisado" (verde) indica que o Gemini processou o diff e gerou atividades de faturamento. "Pendente" (cinza) significa que o commit foi importado mas ainda não foi analisado.' },
  { title: 'Resiliência', text: 'O Nexus utiliza Redis Lock para garantir envios sequenciais ao portal de faturamento e otimizações do Playwright para evitar erros de navegação em conexões lentas.' },
]

const store = useCommitsStore()
const toastStore = useToastStore()
const showImport = ref(false)
const importing = ref(false)
const importError = ref('')
const form = ref({ commit_hashes: '' })

const commitParaDeletar = ref<any>(null)
const exibindoModalConfirmacao = ref(false)

const importModalRef = ref<HTMLElement | null>(null)
const confirmModalRef = ref<HTMLElement | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

function handleImportKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    showImport.value = false
  }
  if (e.key === 'Tab' && importModalRef.value) {
    const focusable = importModalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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

watch(showImport, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleImportKeydown)
    nextTick(() => {
      const textarea = importModalRef.value?.querySelector('textarea') as HTMLElement
      textarea?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleImportKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

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

const mesSelecionado = ref<string>('todos')

const statsExibidas = computed(() => {
  if (!store.stats) {
    return { codes: {}, total_tasks: 0, total_hpa: 0 }
  }
  if (mesSelecionado.value === 'todos') {
    return store.stats.totals
  }
  return store.stats.by_month[mesSelecionado.value] || { codes: {}, total_tasks: 0, total_hpa: 0 }
})

function formatarMesExtenso(mesAno: string): string {
  if (!mesAno || !mesAno.includes('/')) return mesAno
  const [mes, ano] = mesAno.split('/')
  const meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]
  const mesIdx = parseInt(mes, 10) - 1
  const nomeMes = meses[mesIdx] || mes
  return `${nomeMes} de ${ano} (${mesAno})`
}

onMounted(async () => {
  await store.fetchCommits()
})

function formatarDataCabecalho(dataStr: string): string {
  if (!dataStr) return ''
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

function obterIniciais(nome: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

function obterCorAvatar(nome: string): string {
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
  if (!isoStr) return 'some time ago'
  try {
    const d = new Date(isoStr)
    const agora = new Date()
    const diffMs = agora.getTime() - d.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'just now'
    if (diffMin === 1) return '1 minute ago'
    if (diffMin < 60) return `${diffMin} minutes ago`
    if (diffHour === 1) return '1 hour ago'
    if (diffHour < 24) return `${diffHour} hours ago`
    if (diffDay === 1) return 'yesterday'
    return `${diffDay} days ago`
  } catch {
    return 'some time ago'
  }
}

async function copiarSHA(sha: string) {
  try {
    await navigator.clipboard.writeText(sha)
    toastStore.addToast('SHA copiado para a área de transferência!', 'success')
  } catch (err) {
    console.error('Falha ao copiar SHA:', err)
  }
}



function abrirModalConfirmacao(commit: any) {
  commitParaDeletar.value = commit
  exibindoModalConfirmacao.value = true
}

function fecharModalConfirmacao() {
  commitParaDeletar.value = null
  exibindoModalConfirmacao.value = false
}

async function confirmarExclusao() {
  if (!commitParaDeletar.value) return
  try {
    await store.deletar(commitParaDeletar.value.id)
    toastStore.addToast('Commit e análise excluídos com sucesso.', 'info')
  } catch (e: any) {
    toastStore.addToast(`Erro ao excluir: ${e.response?.data?.detail ?? String(e)}`, 'error')
  } finally {
    fecharModalConfirmacao()
  }
}

function obterDataParaAgrupamento(commit: any): string {
  if (commit.data_autor) {
    try {
      const d = new Date(commit.data_autor)
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
  return commit.data
}

const commitsAgrupados = computed(() => {
  const grupos: Record<string, typeof store.commits> = {}
  
  for (const commit of store.commits) {
    const dataAgrupamento = obterDataParaAgrupamento(commit)
    const dataFormatada = formatarDataCabecalho(dataAgrupamento)
    if (!grupos[dataFormatada]) {
      grupos[dataFormatada] = []
    }
    grupos[dataFormatada].push(commit)
  }
  
  const obterTime = (c: any) => {
    const tsStr = c.data_autor || c.importado_em
    if (tsStr) {
      const t = new Date(tsStr).getTime()
      if (!isNaN(t)) return t
    }
    if (c.data) {
      const parts = c.data.split('/')
      if (parts.length === 3) {
        return new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0])).getTime()
      }
    }
    return 0
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
    commits: grupos[chave]
  }))
})

async function importar() {
  importing.value = true
  importError.value = ''
  
  const urls = form.value.commit_hashes
    .split('\n')
    .map(h => h.trim())
    .filter(h => h.length > 0)
    
  if (urls.length === 0) {
    importError.value = 'Informe pelo menos uma URL completa de commit.'
    importing.value = false
    return
  }

  const urlsInvalidas = urls.filter(u => !u.startsWith('http://') && !u.startsWith('https://'))
  if (urlsInvalidas.length > 0) {
    importError.value = 'Todas as linhas devem ser URLs completas do GitLab (começando com http:// ou https://).'
    importing.value = false
    return
  }

  let sucessos = 0
  let falhas = 0

  for (const url of urls) {
    try {
      await store.importar(url)
      sucessos++
    } catch (e: any) {
      falhas++
      console.error(`Erro ao importar commit ${url}:`, e)
    }
  }

  showImport.value = false
  form.value.commit_hashes = ''
  importing.value = false
  
  alert(`Importação concluída! Sucessos: ${sucessos}, Falhas: ${falhas}`)
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }

.commit-list-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.date-group-commits {
  border: 1px solid var(--card-border);
  border-top: none;
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
}

.commit-row {
  display: flex;
  align-items: center;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}

.commit-row:last-child {
  border-bottom: none;
}

.commit-row:hover {
  background: var(--accent-glow);
}

.commit-avatar {
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

.commit-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
  min-width: 0;
}

.commit-msg-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.commit-msg-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 500px;
}

.commit-row-badges {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.badge-status {
  font-size: 0.7rem;
  padding: 3px 8px;
  font-weight: 700;
}

.commit-author-time {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}

.commit-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  margin-left: 1rem;
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

.action-btn:hover {
  color: var(--text);
  border-color: var(--accent);
  transform: translateY(-1px);
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

.sha-box {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: var(--sha-box-color);
  background: var(--sha-box-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.6rem;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.copy-btn, .folder-btn {
  padding: 0.4rem;
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

/* Painel de KPIs */
.kpi-panel {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.kpi-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border, #30363d);
  flex-wrap: wrap;
  gap: 1rem;
}

.kpi-panel-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--accent, #58a6ff);
}

.kpi-panel-title h2 {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0;
  color: var(--text, #f0f6fc);
}

.kpi-filter-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.kpi-filter-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted, #8b949e);
}

.kpi-select {
  background: var(--bg, #0d1117);
  color: var(--text, #c9d1d9);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 0.4rem 0.8rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}

.kpi-select:focus, .kpi-select:hover {
  border-color: var(--accent, #58a6ff);
}

.kpi-summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.kpi-card {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 0.9rem 1.1rem;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s, border-color 0.15s;
}

.kpi-card:hover {
  transform: translateY(-2px);
}

.kpi-card.highlight { border-left: 4px solid var(--accent, #58a6ff); }
.kpi-card.highlight-green { border-left: 4px solid #3fb950; }
.kpi-card.highlight-purple { border-left: 4px solid #bc8cff; }

.kpi-card-label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted, #8b949e);
  letter-spacing: 0.05em;
}

.kpi-card-val {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  margin: 0.2rem 0;
}

.kpi-card-sub {
  font-size: 0.75rem;
  color: var(--text-muted, #8b949e);
}

.kpi-codes-section {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.kpi-section-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.kpi-empty {
  font-size: 0.88rem;
  color: var(--text-muted, #8b949e);
  padding: 1rem 0;
  font-style: italic;
}

.kpi-codes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.8rem;
}

.kpi-code-card {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  transition: all 0.15s;
}

.kpi-code-card:hover {
  border-color: var(--accent, #58a6ff);
  transform: translateY(-2px);
}

.kpi-code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-code-count {
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
}

.kpi-code-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: var(--text-muted, #8b949e);
}

.kpi-code-hpa {
  font-weight: 600;
}

.kpi-code-pct {
  font-weight: 700;
  color: var(--accent, #58a6ff);
}

.kpi-progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 0.2rem;
}

.kpi-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #58a6ff, #388bfd);
  border-radius: 2px;
  transition: width 0.3s ease;
}
</style>
