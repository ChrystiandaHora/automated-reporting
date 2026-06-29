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
      <div class="modal">
        <h2>Importar Commits do GitLab (Lote)</h2>
        <label>URLs Completas ou SHAs dos Commits (um por linha)</label>
        <textarea 
          v-model="form.commit_hashes" 
          placeholder="Ex:&#10;082630b1&#10;https://gitlab.../commit/abc123" 
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
            @click="$router.push(`/commits/${commit.id}`)"
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
      <div class="modal">
        <h2>Confirmar Exclusão</h2>
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
import { ref, onMounted, computed } from 'vue'
import { useCommitsStore } from '../stores/commits'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Importar Commit', text: 'Clique em "+ Importar Commit" e informe um ou mais SHAs ou URLs completos do GitLab (um por linha) para importação.' },
  { title: 'PRIVATE-TOKEN do GitLab', text: 'Token de acesso pessoal do GitLab. Gere em: GitLab → Preferências → Tokens de Acesso → Escopo "read_repository". Salve na página de Configuração.' },
  { title: 'Status dos commits', text: '"Analisado" (verde) indica que o Gemini processou o diff e gerou atividades de faturamento. "Pendente" (cinza) significa que o commit foi importado mas ainda não foi analisado.' },
  { title: 'Resiliência', text: 'Utilizamos Redis Lock para garantir envios sequenciais ao Munka e aumentamos o timeout do Playwright para 90s para evitar erros de navegação em conexões lentas.' },
]

const store = useCommitsStore()
const toastStore = useToastStore()
const showImport = ref(false)
const importing = ref(false)
const importError = ref('')
const form = ref({ commit_hashes: '' })

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

const commitParaDeletar = ref<any>(null)
const exibindoModalConfirmacao = ref(false)

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
  
  const hashes = form.value.commit_hashes
    .split('\n')
    .map(h => h.trim())
    .filter(h => h.length > 0)
    
  if (hashes.length === 0) {
    importError.value = 'Informe pelo menos um SHA ou URL de commit.'
    importing.value = false
    return
  }

  let sucessos = 0
  let falhas = 0

  for (const hash of hashes) {
    try {
      await store.importar(hash)
      sucessos++
    } catch (e: any) {
      falhas++
      console.error(`Erro ao importar commit ${hash}:`, e)
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
  padding: 0.65rem 1rem;
  background: rgba(238, 238, 238, 0.02);
  border: 2px solid var(--border);
  border-bottom: none;
  font-size: 0.88rem;
}

.date-text {
  font-weight: 800;
  color: var(--text);
}

.commit-count-text {
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 500;
}

.date-group-commits {
  border: 2px solid var(--border);
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
}

.commit-row {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(238, 238, 238, 0.08);
  cursor: pointer;
  transition: background 0.1s;
}

.commit-row:last-child {
  border-bottom: none;
}

.commit-row:hover {
  background: rgba(238, 238, 238, 0.02);
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
  border: 1px solid rgba(255, 255, 255, 0.15);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
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
  font-size: 0.65rem;
  padding: 1px 5px;
}

.commit-author-time {
  font-size: 0.76rem;
  color: var(--text-muted);
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
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--text-muted);
  background: rgba(238, 238, 238, 0.04);
  border: 2px solid var(--border);
  padding: 0.3rem 0.6rem;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.copy-btn, .folder-btn {
  padding: 0.4rem;
}

.btn-danger {
  background: #f85149;
  color: var(--text);
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
