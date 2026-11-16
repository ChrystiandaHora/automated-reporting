/** Catálogo único de status do Munka (espelha backend/status_munka.py). */
export interface StatusMunka {
  id: string
  rotulo: string
  concluida: boolean
  badge: string
}

export const STATUS_OUTROS: StatusMunka = {
  id: 'outros',
  rotulo: 'Sem status / Outros',
  concluida: false,
  badge: 'badge-gray'
}

export const CATALOGO_STATUS: StatusMunka[] = [
  { id: '15', rotulo: 'Backlog', concluida: false, badge: 'badge-gray' },
  { id: '16', rotulo: 'Backlog Prioritário', concluida: false, badge: 'badge-gray' },
  { id: '17', rotulo: 'Pendente', concluida: false, badge: 'badge-yellow' },
  { id: '18', rotulo: 'Desenvolvimento', concluida: false, badge: 'badge-orange' },
  { id: '19', rotulo: 'Concluído para o Supervisor', concluida: true, badge: 'badge-green' },
  { id: '20', rotulo: 'Homologação', concluida: false, badge: 'badge-blue' },
  { id: '21', rotulo: 'Concluído', concluida: true, badge: 'badge-green' },
  { id: '22', rotulo: 'Arquivado', concluida: false, badge: 'badge-gray' },
  { id: '35', rotulo: 'Evidência com Pendência', concluida: false, badge: 'badge-orange' }
]

export function normalizarTexto(valor?: string | null): string {
  return (valor || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
}

// Textos locais/portal que não batem com o rótulo exato do catálogo.
const ALIASES: Record<string, string> = {
  'enviado ao munka': '17',
  'aberto / pendente': '17',
  'aberto': '17',
  'pendente': '17',
  'concluido para o supervisor': '19',
  'concluido': '21'
}

/** Resolve um texto/ID de status (status_munka || status) para o item do catálogo. */
export function resolverStatus(valor?: string | null): StatusMunka | null {
  const n = normalizarTexto(valor)
  if (!n) return null
  const porId = CATALOGO_STATUS.find(s => s.id === n)
  if (porId) return porId
  const porRotulo = CATALOGO_STATUS.find(s => normalizarTexto(s.rotulo) === n)
  if (porRotulo) return porRotulo
  const idAlias = ALIASES[n]
  if (idAlias) return CATALOGO_STATUS.find(s => s.id === idAlias) || null
  return null
}

export function rotuloStatus(id: string): string {
  return CATALOGO_STATUS.find(s => s.id === id)?.rotulo || `Status ${id}`
}

export function isStatusConcluido(valor?: string | null): boolean {
  const s = normalizarTexto(valor)
  const r = resolverStatus(valor)
  if (r) return r.concluida
  return s.includes('conclu') || s.includes('supervisor') || s.includes('aprovad') || s.includes('finalizad')
}

export function classeBadgeStatus(valor?: string | null): string {
  if (!valor) return 'badge-gray'
  const r = resolverStatus(valor)
  if (r) return r.badge
  const s = normalizarTexto(valor)
  if (s.includes('conclu') || s.includes('aprov')) return 'badge-green'
  if (s.includes('homolog')) return 'badge-blue'
  if (s.includes('desenv')) return 'badge-orange'
  if (s.includes('backlog')) return 'badge-gray'
  if (s.includes('aberto') || s.includes('pendente')) return 'badge-yellow'
  return 'badge-blue'
}
