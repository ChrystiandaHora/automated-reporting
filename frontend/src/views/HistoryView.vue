<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Histórico de Envios</h1>
        <HelpModal title="Histórico de Envios" :items="helpItems" />
      </div>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-else-if="items.length === 0" class="empty">
      Nenhuma atividade enviada ainda.
    </div>

    <div v-else class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Commit</th>
            <th>Título</th>
            <th>Código</th>
            <th>HPA</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ formatDate(item.enviado_em) }}</td>
            <td>
              <router-link :to="`/commits/${item.commit_id}`" class="sha-link">
                {{ item.commit_id?.slice(0, 8) ?? '-' }}
              </router-link>
            </td>
            <td>{{ item.titulo }}</td>
            <td><code>{{ item.codigo }}</code></td>
            <td>{{ item.hpa }}h</td>
            <td><span class="badge badge-green">{{ item.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type HistoricoItem } from '../api'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { title: 'O que é exibido aqui', text: 'Todas as atividades enviadas com sucesso ao portal Munka. Cada linha corresponde a uma atividade individual — um mesmo commit pode gerar múltiplas atividades com códigos diferentes.' },
  { title: 'Código (coluna)', text: 'Código do catálogo de serviços identificado pelo Gemini (ex: 21a, 57b). Determina o tipo de serviço faturado e o valor por hora correspondente.' },
  { title: 'HPA', text: 'Horas Previstas para Execução da Atividade — quantidade de horas faturadas para aquela atividade, conforme o catálogo de serviços.' },
  { title: 'Navegar ao commit', text: 'Clique no hash (8 primeiros caracteres) na coluna Commit para abrir a página de detalhes do commit original.' },
]

const items = ref<HistoricoItem[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = await api.historico.listar()
  } finally {
    loading.value = false
  }
})

function formatDate(iso: string) {
  if (!iso) return '-'
  return iso.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.table-wrapper { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 2px solid var(--border); font-size: 0.8rem; color: var(--text-muted); }
td { padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
.sha-link { font-family: monospace; color: var(--accent); text-decoration: none; }
.sha-link:hover { text-decoration: underline; }
code { font-size: 0.8rem; background: rgba(88,166,255,0.1); padding: 1px 5px; border-radius: 3px; }
</style>
