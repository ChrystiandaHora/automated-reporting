import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export interface CommitSummary {
  id: string
  data: string
  projeto: string
  autor: string
  mensagem: string
  importado_em: string
  analisado: boolean
  atividades_total?: number
  atividades_enviadas?: number
  hpa_total?: number
  hpa_enviado?: number
}

export interface Atividade {
  etapa: string
  titulo: string
  descricao: string
  categoria: string
  codigo_id: string
  hpa: number
  arquivos: string[]
  justificativa: string
  evidencia_html?: string
  is_media?: boolean
  enviado?: boolean
}

export interface Analise {
  commit_id: string
  complexidade_global: string
  atividades: Atividade[]
  analisado_em: string
}

export interface HistoricoItem {
  id: number
  commit_id: string
  titulo: string
  codigo: string
  hpa: number
  status: string
  enviado_em: string
}

export interface Config {
  gemini_api_key: string
  munka_user: string
  munka_pass: string
  gitlab_token: string
  gitlab_url: string
  gitlab_project: string
  munka_cargo: string
  munka_nivel: string
  munka_responsavel: string
  munka_produto: string
  munka_projeto: string
  munka_status_id: string
  status: { gemini: boolean; munka: boolean; gitlab: boolean }
}

export interface TaskResponse {
  task_id: string
  status: string
}

export interface TaskStatus {
  task_id: string
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: any
  error?: string
  meta?: any
}

export const api = {
  commits: {
    listar: () => http.get<CommitSummary[]>('/commits').then(r => r.data),
    obter: (sha: string) => http.get<any>(`/commits/${sha}`).then(r => r.data),
    importar: (payload: { gitlab_url?: string; token?: string; project_path?: string; commit_hash: string }) =>
      http.post<{ id: string; ja_existia: boolean }>('/commits/importar', payload).then(r => r.data),
    deletar: (sha: string) => http.delete(`/commits/${sha}`),
  },
  analise: {
    obter: (sha: string) => http.get<Analise>(`/commits/${sha}/analise`).then(r => r.data),
    analisar: (sha: string, forcar = false) =>
      http.post<Analise | TaskResponse>(`/commits/${sha}/analisar`, { forcar }).then(r => r.data),
    atualizar: (sha: string, atividades: Atividade[], complexidade_global?: string) =>
      http.put(`/commits/${sha}/atividades`, { atividades, complexidade_global }).then(r => r.data),
  },
  task: {
    status: (taskId: string) => http.get<TaskStatus>(`/task/${taskId}`).then(r => r.data),
  },
  enviar: (sha: string, payload: {
    atividade_idx: number
    cargo: string
    nivel: string
    responsavel: string
    produto: string
    projeto: string
    status_id: string
    headless: boolean
    gitlab_url?: string
  }) => http.post<{ ok: boolean; pulada_duplicada: boolean; mensagem: string }>(`/commits/${sha}/enviar`, payload).then(r => r.data),
  historico: {
    listar: () => http.get<HistoricoItem[]>('/historico').then(r => r.data),
  },
  config: {
    obter: () => http.get<Config>('/config').then(r => r.data),
    salvar: (payload: Partial<Config>) => http.post('/config', payload).then(r => r.data),
  },
}
