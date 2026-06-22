import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type FilaItem } from '../api'
import { useToastStore } from './toast'

export const useFilaStore = defineStore('fila', () => {
  const jobs = ref<FilaItem[]>([])
  const loading = ref(false)
  const error = ref('')
  const polling = ref(false)
  let pollingInterval: any = null

  const toastStore = useToastStore()

  // Mapeamento dos últimos estados conhecidos dos jobs para detectar transições
  const statusAnteriores = new Map<number, string>()

  async function fetchJobs(quiet = false) {
    if (!quiet) loading.value = true
    error.value = ''
    try {
      const data = await api.fila.listar()
      
      // Detecta mudanças de status para emitir toasts
      if (statusAnteriores.size > 0) {
        for (const job of data) {
          const statusAntigo = statusAnteriores.get(job.id)
          if (statusAntigo && statusAntigo !== job.status) {
            // Se o job mudou de pending/running para done/error
            if ((statusAntigo === 'pending' || statusAntigo === 'running') && (job.status === 'done' || job.status === 'error')) {
              const hashCurto = job.commit_id.slice(0, 8)
              const identificador = job.tipo === 'analise' 
                ? `Análise do commit ${hashCurto}` 
                : `Atividade "${job.titulo_atividade || 'sem título'}"`

              if (job.status === 'done') {
                toastStore.addToast(`✔ ${identificador} concluída com sucesso!`, 'success')
              } else {
                toastStore.addToast(`❌ Falha na execução: ${identificador}.`, 'error')
              }
            }
          }
        }
      }

      // Atualiza o mapa de status anteriores
      statusAnteriores.clear()
      for (const job of data) {
        statusAnteriores.set(job.id, job.status)
      }

      jobs.value = data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
    } finally {
      if (!quiet) loading.value = false
    }
  }

  async function enfileirarAnalise(commitIds: string[], modelo: string) {
    error.value = ''
    try {
      const res = await api.fila.enfileirarAnalise({ commit_ids: commitIds, modelo })
      toastStore.addToast(`📥 ${commitIds.length} commit(s) enfileirado(s) para análise.`, 'info')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao enfileirar análise: ${error.value}`, 'error')
      throw e
    }
  }

  async function enfileirarEnvio(commitId: string, atividadeIdx: number) {
    error.value = ''
    try {
      const res = await api.fila.enfileirarEnvio({ commit_id: commitId, atividade_idx: atividadeIdx })
      toastStore.addToast(`📥 Envio da atividade enfileirado com sucesso.`, 'info')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao enfileirar envio: ${error.value}`, 'error')
      throw e
    }
  }

  async function removerJob(id: number) {
    try {
      await api.fila.remover(id)
      jobs.value = jobs.value.filter(j => j.id !== id)
      statusAnteriores.delete(id)
      toastStore.addToast(`Tarefa removida da fila.`, 'info')
    } catch (e: any) {
      toastStore.addToast(`Erro ao remover tarefa: ${e.response?.data?.detail ?? String(e)}`, 'error')
    }
  }

  function startPolling() {
    if (polling.value) return
    polling.value = true
    // Roda imediatamente
    fetchJobs(true)
    pollingInterval = setInterval(() => {
      // Verifica se ainda existem tarefas pendentes ou rodando
      const temAtivos = jobs.value.some(j => j.status === 'pending' || j.status === 'running')
      if (!temAtivos) {
        stopPolling()
        return
      }
      fetchJobs(true)
    }, 3000)
  }

  function stopPolling() {
    polling.value = false
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }

  return { jobs, loading, error, polling, fetchJobs, enfileirarAnalise, enfileirarEnvio, removerJob, startPolling, stopPolling }
})
