import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type CommitSummary, type Analise, type HistoricoItem } from '../api'

export const useCommitsStore = defineStore('commits', () => {
  const commits = ref<CommitSummary[]>([])
  const historico = ref<HistoricoItem[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchCommits() {
    loading.value = true
    error.value = ''
    try {
      commits.value = await api.commits.listar()
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchHistorico() {
    historico.value = await api.historico.listar()
  }

  async function importar(commit_hash: string, gitlab_url?: string, token?: string, project_path?: string) {
    const result = await api.commits.importar({ gitlab_url, token, project_path, commit_hash })
    await fetchCommits()
    return result
  }

  async function deletar(sha: string) {
    await api.commits.deletar(sha)
    commits.value = commits.value.filter(c => c.id !== sha)
  }

  return { commits, historico, loading, error, fetchCommits, fetchHistorico, importar, deletar }
})

export const useAnaliseStore = defineStore('analise', () => {
  const analise = ref<Analise | null>(null)
  const loading = ref(false)
  const analisando = ref(false)
  const enviando = ref<Record<number, boolean>>({})
  const error = ref('')

  async function fetchAnalise(sha: string) {
    loading.value = true
    error.value = ''
    analise.value = null
    try {
      analise.value = await api.analise.obter(sha)
    } catch (e: any) {
      if (e.response?.status !== 404) {
        error.value = e.response?.data?.detail ?? String(e)
      }
    } finally {
      loading.value = false
    }
  }

  async function analisar(sha: string, forcar = false) {
    analisando.value = true
    error.value = ''
    try {
      analise.value = await api.analise.analisar(sha, forcar)
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      throw e
    } finally {
      analisando.value = false
    }
  }

  async function salvarAtividades(sha: string) {
    if (!analise.value) return
    await api.analise.atualizar(sha, analise.value.atividades, analise.value.complexidade_global)
  }

  async function enviar(sha: string, idx: number, payload: any) {
    enviando.value = { ...enviando.value, [idx]: true }
    error.value = ''
    try {
      const res = await api.enviar(sha, { atividade_idx: idx, ...payload })
      return res
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? String(e)
      throw e
    } finally {
      const next = { ...enviando.value }
      delete next[idx]
      enviando.value = next
    }
  }

  return { analise, loading, analisando, enviando, error, fetchAnalise, analisar, salvarAtividades, enviar }
})
