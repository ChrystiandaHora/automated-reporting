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

  function playJobStatusTone(kind: 'success' | 'error') {
    if (typeof window === 'undefined') return

    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioCtx) return

    try {
      const ctx = new AudioCtx()

      const beep = (freq: number, start: number, duration: number, volume = 0.38, type: OscillatorType = 'sine') => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()

        osc.type = type
        osc.frequency.setValueAtTime(freq, start)

        // Rampa suave de entrada (attack) para evitar estalos e dar presença
        gain.gain.setValueAtTime(0.001, start)
        gain.gain.linearRampToValueAtTime(volume, start + 0.012)
        gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)

        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start(start)
        osc.stop(start + duration)
      }

      const now = ctx.currentTime
      if (kind === 'success') {
        // Tom duplo ascendente estilo Teams/WhatsApp (E5 -> B5 com brilho harmônico)
        beep(659.25, now, 0.18, 0.35, 'sine')
        beep(659.25, now, 0.18, 0.15, 'triangle')

        beep(987.77, now + 0.12, 0.28, 0.42, 'sine')
        beep(1318.51, now + 0.12, 0.28, 0.18, 'sine')
      } else {
        // Tom duplo descendente de alerta marcante (B4 -> E4)
        beep(493.88, now, 0.18, 0.40, 'sine')
        beep(329.63, now + 0.14, 0.28, 0.42, 'sine')
        beep(329.63, now + 0.14, 0.28, 0.18, 'triangle')
      }

      setTimeout(() => {
        ctx.close().catch(() => {})
      }, 1500)
    } catch {
      // Ignora erros de áudio (ex: autoplay policy)
    }
  }

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
                playJobStatusTone('success')
              } else {
                toastStore.addToast(`❌ Falha na execução: ${identificador}.`, 'error')
                playJobStatusTone('error')
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

  async function cancelarJob(id: number) {
    try {
      await api.fila.cancelar(id)
      toastStore.addToast(`❌ Tarefa cancelada com sucesso.`, 'info')
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
      toastStore.addToast(`⚡ ${res.message}`, 'success')
      await fetchJobs(true)
      startPolling()
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      toastStore.addToast(`Erro ao reenfileirar tarefas: ${error.value}`, 'error')
      throw e
    }
  }

  return { jobs, loading, error, polling, fetchJobs, enfileirarAnalise, enfileirarEnvio, reenfileirarComErros, removerJob, cancelarJob, startPolling, stopPolling }
})
