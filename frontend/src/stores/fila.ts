import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type FilaItem } from '../api'
import { useToastStore } from './toast'
import { tocarSomStatus } from '../utils/somNotificacao'

export const useFilaStore = defineStore('fila', () => {
  const jobs = ref<FilaItem[]>([])
  const loading = ref(false)
  const error = ref('')
  const polling = ref(false)
  let pollingInterval: any = null

  const toastStore = useToastStore()

  // Mapeamento dos últimos estados conhecidos dos jobs para detectar transições
  const statusAnteriores = new Map<number, string>()

  // Jobs cujo término já foi notificado (id -> status final). Evita toast/som duplicado
  // quando a tela da fila e a store consultam o backend ao mesmo tempo.
  const notificados = new Map<number, string>()
  // Sequência das requisições: uma resposta atrasada não pode sobrescrever uma mais nova
  let seqRequisicao = 0
  let seqAplicada = 0

  async function fetchJobs(quiet = false) {
    if (!quiet) loading.value = true
    error.value = ''
    const seq = ++seqRequisicao
    try {
      const data = await api.fila.listar()
      if (seq < seqAplicada) return
      seqAplicada = seq

      let sucessos = 0
      let falhas = 0

      // Detecta mudanças de status para emitir toasts
      if (statusAnteriores.size > 0) {
        for (const job of data) {
          if (job.status === 'pending' || job.status === 'running') {
            // Voltou para a fila (retry/retomada): poderá notificar de novo ao terminar
            notificados.delete(job.id)
            continue
          }
          const statusAntigo = statusAnteriores.get(job.id)
          // Se o job mudou de pending/running para done/error
          if ((statusAntigo === 'pending' || statusAntigo === 'running') && (job.status === 'done' || job.status === 'error')) {
            if (notificados.get(job.id) === job.status) continue
            notificados.set(job.id, job.status)

            const hashCurto = job.commit_id.slice(0, 8)
            const identificador = job.tipo === 'analise'
              ? `Análise do commit ${hashCurto}`
              : `Atividade "${job.titulo_atividade || 'sem título'}"`

            if (job.status === 'done') {
              toastStore.addToast(`${identificador} concluída com sucesso!`, 'success')
              sucessos++
            } else {
              toastStore.addToast(`Falha na execução: ${identificador}.`, 'error')
              falhas++
            }
          }
        }
      }

      // Um único aviso sonoro por rodada, mesmo que várias tarefas terminem juntas.
      // Falha tem prioridade: é o que exige atenção.
      if (falhas > 0) tocarSomStatus('error')
      else if (sucessos > 0) tocarSomStatus('success')

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
      toastStore.addToast(`${commitIds.length} commit(s) enfileirado(s) para análise.`, 'info')
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
      toastStore.addToast(`Envio da atividade enfileirado com sucesso.`, 'info')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao enfileirar envio: ${error.value}`, 'error')
      throw e
    }
  }

  async function enfileirarEnvioLote(commitIds: string[], forcarReenvio: boolean = false) {
    error.value = ''
    try {
      const res = await api.fila.enfileirarEnvioLote({ commit_ids: commitIds, forcar_reenvio: forcarReenvio })
      toastStore.addToast(`${res.total_enfileirados} tarefa(s) de ${res.commits_processados} commit(s) adicionada(s) à fila!`, 'success')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao enfileirar tarefas em lote: ${error.value}`, 'error')
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

  async function cancelarJob(id: number) {
    try {
      await api.fila.cancelar(id)
      toastStore.addToast(`Tarefa cancelada com sucesso.`, 'info')
      await fetchJobs(true)
    } catch (e: any) {
      toastStore.addToast(`Erro ao cancelar tarefa: ${e.response?.data?.detail ?? String(e)}`, 'error')
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

  async function reenfileirarComErros(commitId?: string) {
    error.value = ''
    try {
      const res = await api.fila.retryFailed(commitId)
      toastStore.addToast(`${res.message}`, 'success')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao reenfileirar tarefas: ${error.value}`, 'error')
      throw e
    }
  }

  return { jobs, loading, error, polling, fetchJobs, enfileirarAnalise, enfileirarEnvio, enfileirarEnvioLote, reenfileirarComErros, removerJob, cancelarJob, startPolling, stopPolling }
})
