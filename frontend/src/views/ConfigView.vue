<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Configuração</h1>
        <HelpModal title="Configuração das Integrações" :items="helpItems" />
      </div>
      <button class="btn-primary" :disabled="saving" @click="salvar">
        {{ saving ? 'Salvando...' : 'Salvar' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <template v-else>
      <div class="status-bar">
        <span class="status-badge" :class="cfg.status.gemini ? 'status-ok' : 'status-err'">
          {{ cfg.status.gemini ? '● GEMINI OK' : '✗ GEMINI' }}
        </span>
        <span class="status-badge" :class="cfg.status.munka ? 'status-ok' : 'status-err'">
          {{ cfg.status.munka ? '● MUNKA OK' : '✗ MUNKA' }}
        </span>
        <span class="status-badge" :class="cfg.status.gitlab ? 'status-ok' : 'status-err'">
          {{ cfg.status.gitlab ? '● GITLAB OK' : '✗ GITLAB' }}
        </span>
      </div>

      <div class="config-grid">
        <div class="config-section">
          <h3>Gemini AI</h3>
          <label>API Key</label>
          <input v-model="form.gemini_api_key" type="password" placeholder="Insira para atualizar" autocomplete="off" />
        </div>

        <div class="config-section">
          <h3>Munka - Acesso</h3>
          <label>Usuário</label>
          <input v-model="form.munka_user" placeholder="Login" />
          <label>Senha</label>
          <input v-model="form.munka_pass" type="password" placeholder="Insira para atualizar" autocomplete="off" />
        </div>

        <div class="config-section">
          <h3>Munka - Faturamento Padrão</h3>
          <label>Cargo Padrão</label>
          <select v-model="form.munka_cargo">
            <option value="9">Desenvolvedor</option>
            <option value="11">Analista de Sistemas</option>
            <option value="12">Arquiteto de Software</option>
            <option value="16">Analista de Testes</option>
          </select>
          <label>Nível Padrão</label>
          <select v-model="form.munka_nivel">
            <option value="1">Júnior</option>
            <option value="2">Pleno</option>
            <option value="3">Sênior</option>
            <option value="4">Único</option>
          </select>
          <label>Responsável Padrão (busca)</label>
          <input v-model="form.munka_responsavel" placeholder="Ex: João Silva" />
          <label>Produto Padrão</label>
          <input v-model="form.munka_produto" placeholder="Ex: [DESENV] MUNKA" />
          <label>Projeto Padrão</label>
          <input v-model="form.munka_projeto" placeholder="Ex: [DESENV] MUNKA" />
          <label>Status Inicial Padrão</label>
          <select v-model="form.munka_status_id">
            <option value="17">Pendente</option>
            <option value="20">Homologação</option>
            <option value="21">Concluído</option>
            <option value="18">Desenvolvimento</option>
          </select>
        </div>

        <div class="config-section">
          <h3>GitLab</h3>
          <label>URL</label>
          <input v-model="form.gitlab_url" placeholder="https://gitlab.suaorganizacao.com" />
          <label>Token</label>
          <input v-model="form.gitlab_token" type="password" placeholder="Insira para atualizar" autocomplete="off" />
        </div>
      </div>

      <p v-if="msg" :class="ok ? 'success' : 'error'">{{ msg }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Config } from '../api'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'Gemini API Key', text: 'Chave da API do Google Gemini, usada para análise de diffs. Obtenha em aistudio.google.com (Get API Key). O modelo padrão é gemini-2.5-flash com fallback automático para outros modelos.' },
  { title: 'Credenciais Munka', text: 'Usuário e senha do portal Munka. Usados pelo Playwright para automatizar o cadastro e homologação das atividades no sistema de faturamento.' },
  { title: 'Token do GitLab', text: 'PRIVATE-TOKEN de acesso pessoal ao GitLab para baixar diffs via API. Gere em: GitLab → Preferências → Tokens de Acesso. Escopo mínimo: read_repository.' },
  { title: 'Como as credenciais são salvas', text: 'Todas as configurações são armazenadas no arquivo .env no servidor. Campos deixados em branco não sobrescrevem os valores existentes — preencha apenas o que deseja atualizar.' },
  { title: 'Indicadores de status', text: 'Verde (●) indica que a credencial está configurada no servidor. Vermelho (●) indica ausência. O status reflete apenas a presença da variável, não sua validade.' },
]

const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const ok = ref(false)

const cfg = ref<Config>({
  gemini_api_key: '', munka_user: '', munka_pass: '',
  gitlab_token: '', gitlab_url: '',
  munka_cargo: '9', munka_nivel: '3', munka_responsavel: '',
  munka_produto: '[DESENV] MUNKA', munka_projeto: 'MUNKA Multicontrato', munka_status_id: '17',
  status: { gemini: false, munka: false, gitlab: false },
})

const form = ref({
  gemini_api_key: '', munka_user: '', munka_pass: '',
  gitlab_token: '', gitlab_url: '',
  munka_cargo: '9', munka_nivel: '3', munka_responsavel: '',
  munka_produto: '[DESENV] MUNKA', munka_projeto: 'MUNKA Multicontrato', munka_status_id: '17',
})

onMounted(async () => {
  try {
    cfg.value = await api.config.obter()
    form.value.munka_user = cfg.value.munka_user
    form.value.gitlab_url = cfg.value.gitlab_url
    form.value.munka_cargo = cfg.value.munka_cargo || '9'
    form.value.munka_nivel = cfg.value.munka_nivel || '3'
    form.value.munka_responsavel = cfg.value.munka_responsavel || ''
    form.value.munka_produto = cfg.value.munka_produto || '[DESENV] MUNKA'
    form.value.munka_projeto = cfg.value.munka_projeto || 'MUNKA Multicontrato'
    form.value.munka_status_id = cfg.value.munka_status_id || '17'
  } finally {
    loading.value = false
  }
})

async function salvar() {
  saving.value = true
  msg.value = ''
  try {
    // Filtra apenas campos sensíveis vazios ou não modificados
    const payload: any = {}
    for (const [k, v] of Object.entries(form.value)) {
      if (k.includes('key') || k.includes('pass') || k.includes('token')) {
        if (v && v !== '***') payload[k] = v
      } else {
        if (v !== undefined && v !== null) payload[k] = v
      }
    }
    await api.config.salvar(payload)
    cfg.value = await api.config.obter()
    ok.value = true
    msg.value = 'Configurações salvas!'
  } catch (e: any) {
    ok.value = false
    msg.value = e.response?.data?.detail ?? String(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }

.status-bar { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1.75rem; flex-wrap: wrap; }
.status-badge {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 2px;
  border: 1px solid;
}
.status-ok  { border-color: #3fb950; color: #3fb950; }
.status-err { border-color: #f85149; color: #f85149; }

.config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }

.config-section {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: 0;
  box-shadow: var(--shadow);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.config-section h3 {
  margin: 0 0 0.75rem;
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid rgba(0,122,204,0.3);
  padding-bottom: 0.5rem;
}
.success { color: #3fb950; margin-top: 1rem; font-weight: 600; }
</style>
