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
        <div class="status-item" :class="cfg.status.gemini ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>Gemini {{ cfg.status.gemini ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div class="status-item" :class="cfg.status.munka ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>Munka {{ cfg.status.munka ? 'Conectado' : 'Não configurado' }}</span>
        </div>
        <div class="status-item" :class="cfg.status.gitlab ? 'status-ok' : 'status-err'">
          <span class="status-dot-sm"></span>
          <span>GitLab {{ cfg.status.gitlab ? 'Conectado' : 'Não configurado' }}</span>
        </div>
      </div>

      <div class="config-grid">
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
            <option value="15">Backlog</option>
            <option value="16">Backlog Prioritário</option>
            <option value="17">Pendente</option>
            <option value="20">Homologação</option>
            <option value="21">Concluído</option>
            <option value="18">Desenvolvimento</option>
          </select>
          <label>Data/Hora de Início Padrão (Ex: 08:00 ou DD/MM/YYYY 08:00)</label>
          <input v-model="form.munka_data_inicio" placeholder="Ex: 08:00" />
          <label>Data/Hora de Fim Padrão (Ex: 18:00 ou DD/MM/YYYY 18:00)</label>
          <input v-model="form.munka_data_fim" placeholder="Ex: 18:00" />
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
  { title: 'Cargo Padrão', text: 'Cargo utilizado no faturamento das atividades no portal Munka.' },
  { title: 'Nível Padrão', text: 'Nível de faturamento das atividades (ex: Júnior, Pleno, Sênior).' },
  { title: 'Datas e Horas Padrão', text: 'Defina os valores padrão para preenchimento de início e fim da atividade. Caso informe apenas a hora (ex: 08:00), a data do commit será utilizada.' },
  { title: 'Demais Configurações', text: 'As credenciais de acesso ao Munka, tokens do GitLab e chave da API do Gemini devem ser configurados diretamente no arquivo .env do servidor.' },
  { title: 'Indicadores de status', text: 'Os badges indicam se as variáveis de ambiente necessárias foram detectadas no servidor.' },
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
  munka_data_inicio: '08:00', munka_data_fim: '18:00',
  status: { gemini: false, munka: false, gitlab: false },
})

const form = ref({
  gemini_api_key: '', munka_user: '', munka_pass: '',
  gitlab_token: '', gitlab_url: '',
  munka_cargo: '9', munka_nivel: '3', munka_responsavel: '',
  munka_produto: '[DESENV] MUNKA', munka_projeto: 'MUNKA Multicontrato', munka_status_id: '17',
  munka_data_inicio: '08:00', munka_data_fim: '18:00',
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
    form.value.munka_data_inicio = cfg.value.munka_data_inicio || '08:00'
    form.value.munka_data_fim = cfg.value.munka_data_fim || '18:00'
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

.status-bar { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1.75rem; flex-wrap: wrap; }
.status-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 99px;
  border: 1px solid;
}
.status-dot-sm {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.status-ok  {
  border-color: rgba(74, 222, 128, 0.4);
  color: #4ade80;
  background: rgba(34, 197, 94, 0.08);
}
.status-err {
  border-color: rgba(248, 113, 113, 0.4);
  color: #f87171;
  background: rgba(239, 68, 68, 0.08);
}

.config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }

.config-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.config-section h3 {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--accent-light);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid rgba(96, 165, 250, 0.2);
  padding-bottom: 0.625rem;
}
.success { color: #4ade80; margin-top: 1rem; font-weight: 600; }
</style>
