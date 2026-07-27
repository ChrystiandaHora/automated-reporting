import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export interface CommitSummary {
  id: string
  data: string
  projeto: string
  autor: string
  mensagem: string
  importado_em: string
  data_autor?: string
  analisado: boolean
  atividades_total?: number
  atividades_enviadas?: number
  hpa_total?: number
  hpa_enviado?: number
  diff_preview?: string
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
  complexidade?: string
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
  commit_data?: string
  commit_data_autor?: string
  commit_autor?: string
  commit_mensagem?: string
}

export interface Config {
  gemini_api_key: string
  munka_user: string
  munka_pass: string
  gitlab_token: string
  gitlab_url: string
  munka_cargo: string
  munka_nivel: string
  munka_responsavel: string
  munka_produto: string
  munka_projeto: string
  munka_status_id: string
  munka_data_inicio?: string
  munka_data_fim?: string
  status: { gemini: boolean; munka: boolean; gitlab: boolean }
  concurrency?: {
    cpu_cores: number
    total_system_limit: number
    limit_per_queue: number
    queues: {
      analises: number
      envios: number
    }
  }
}

export interface CommitUpdate {
  data?: string
  projeto?: string
  autor?: string
  mensagem?: string
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

export interface FilaItem {
  id: number
  tipo: 'analise' | 'envio'
  commit_id: string
  atividade_idx?: number
  modelo?: string
  status: 'pending' | 'running' | 'done' | 'error'
  task_id?: string
  resultado?: any
  criado_em: string
  concluido_em?: string
  commit_mensagem: string
  titulo_atividade?: string
}

export interface ProjetoAtualizacao {
  has_update: boolean
  behind_count: number
  error?: string
}

export interface ModelStatus {
  id: string
  name: string
  category: string
  rpm: number
  rpm_limit: number
  rpm_pct: number
  tpm: number
  tpm_limit: number
  tpm_pct: number
  rpd: number
  rpd_limit: number
  rpd_pct: number
  max_pct: number
  status: 'ok' | 'warning' | 'danger'
}

export const api = {
  commits: {
    listar: () => http.get<CommitSummary[]>('/commits').then(r => r.data),
    obter: (sha: string) => http.get<any>(`/commits/${sha}`).then(r => r.data),
    importar: (payload: { gitlab_url?: string; token?: string; project_path?: string; commit_hash: string }) =>
      http.post<{ id: string; ja_existia: boolean }>('/commits/importar', payload).then(r => r.data),
    atualizar: (sha: string, payload: CommitUpdate) =>
      http.patch(`/commits/${sha}`, payload).then(r => r.data),
    deletar: (sha: string) => http.delete(`/commits/${sha}`),
  },
  analise: {
    obter: (sha: string) => http.get<Analise>(`/commits/${sha}/analise`).then(r => r.data),
    analisar: (sha: string, forcar = false) =>
      http.post<Analise | TaskResponse>(`/commits/${sha}/analisar`, { forcar }).then(r => r.data),
    atualizar: (sha: string, atividades: Atividade[], complexidade_global?: string) =>
      http.put(`/commits/${sha}/atividades`, { atividades, complexidade_global }).then(r => r.data),
    previewEvidencia: (sha: string, atividade: Atividade, projeto?: string) =>
      http.post<{ html: string }>(`/commits/${sha}/preview-evidencia`, { atividade, projeto }).then(r => r.data),
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
    remover: (id: number) => http.delete(`/historico/${id}`).then(r => r.data),
  },
  config: {
    obter: () => http.get<Config>('/config').then(r => r.data),
    salvar: (payload: Partial<Config>) => http.post('/config', payload).then(r => r.data),
  },
  fila: {
    listar: () => http.get<FilaItem[]>('/fila').then(r => r.data),
    enfileirarAnalise: (payload: { commit_ids: string[]; modelo: string }) =>
      http.post<{ ok: boolean; job_ids: number[] }>('/fila/analise', payload).then(r => r.data),
    enfileirarEnvio: (payload: { commit_id: string; atividade_idx: number }) =>
      http.post<{ ok: boolean; job_id: number }>('/fila/envio', payload).then(r => r.data),
    remover: (id: number) => http.delete(`/fila/${id}`).then(r => r.data),
  },
  projeto: {
    verificarAtualizacao: () => http.get<any>('/projeto/atualizacao').then(r => r.data),
  },
  modelos: {
    limits: () => http.get<ModelStatus[]>('/modelos/limits').then(r => r.data),
    atualizarLimits: (modelId: string, limits: { rpm_limit?: number; tpm_limit?: number; rpd_limit?: number }) =>
      http.put<{ ok: boolean }>(`/modelos/limits/${modelId}`, limits).then(r => r.data),
    testCall: (modelId: string) =>
      http.post<{ ok: boolean; metrics: any }>('/modelos/test-call', { model_id: modelId }).then(r => r.data),
    reset: () => http.post<{ ok: boolean }>('/modelos/reset').then(r => r.data),
  },
}


