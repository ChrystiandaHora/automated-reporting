// Som de conclusão/falha das tarefas da fila.
//
// Um único AudioContext para a aplicação inteira: criar um contexto por toque fazia o
// navegador entregá-lo "suspended" (política de autoplay, sem gesto do usuário) e o som
// simplesmente não saía. O contexto é destravado no primeiro clique/tecla e reaproveitado.
// Toda saída passa por ganho mestre + compressor, para o volume ser sempre o mesmo.

export type TipoSom = 'success' | 'error'

const VOLUME_MESTRE = 0.55
const INTERVALO_MINIMO_MS = 700

let ctx: AudioContext | null = null
let saida: AudioNode | null = null
let ultimoToque = 0

function obterContexto(): AudioContext | null {
  if (ctx) return ctx
  if (typeof window === 'undefined') return null
  const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
  if (!AudioCtx) return null

  ctx = new AudioCtx()
  const ganho = ctx.createGain()
  ganho.gain.value = VOLUME_MESTRE
  const compressor = ctx.createDynamicsCompressor()
  compressor.threshold.value = -20
  compressor.knee.value = 6
  compressor.ratio.value = 6
  compressor.attack.value = 0.003
  compressor.release.value = 0.15
  ganho.connect(compressor)
  compressor.connect(ctx.destination)
  saida = ganho
  return ctx
}

async function garantirRodando(c: AudioContext): Promise<boolean> {
  if (c.state === 'running') return true
  try {
    // resume() pode ficar pendente para sempre sem gesto do usuário: limita a espera
    await Promise.race([c.resume(), new Promise(r => setTimeout(r, 300))])
  } catch {
    /* ignora */
  }
  return (c.state as string) === 'running'
}

/** Instala o destrave do áudio no primeiro gesto do usuário. Chamar uma vez no boot. */
export function instalarDesbloqueioAudio() {
  if (typeof window === 'undefined') return
  const destravar = () => {
    const c = obterContexto()
    if (!c) return
    c.resume().then(() => {
      if (c.state === 'running') {
        window.removeEventListener('pointerdown', destravar, true)
        window.removeEventListener('keydown', destravar, true)
      }
    }).catch(() => {})
  }
  window.addEventListener('pointerdown', destravar, true)
  window.addEventListener('keydown', destravar, true)
}

function nota(c: AudioContext, destino: AudioNode, freq: number, inicio: number, duracao: number, pico: number) {
  const osc = c.createOscillator()
  const env = c.createGain()
  osc.type = 'sine'
  osc.frequency.setValueAtTime(freq, inicio)
  // Envelope fixo: ataque curto (sem estalo), sustentação breve e decaimento até o silêncio
  env.gain.setValueAtTime(0, inicio)
  env.gain.linearRampToValueAtTime(pico, inicio + 0.015)
  env.gain.setValueAtTime(pico, inicio + duracao * 0.35)
  env.gain.exponentialRampToValueAtTime(0.0001, inicio + duracao)
  osc.connect(env)
  env.connect(destino)
  osc.start(inicio)
  osc.stop(inicio + duracao + 0.02)
}

/**
 * Toca o aviso de sucesso ou falha. Retorna false se o navegador não permitiu tocar
 * (nenhum clique na página ainda) ou se outro aviso acabou de tocar.
 */
export async function tocarSomStatus(tipo: TipoSom): Promise<boolean> {
  const agora = Date.now()
  if (agora - ultimoToque < INTERVALO_MINIMO_MS) return false

  const c = obterContexto()
  if (!c || !saida) return false
  if (!(await garantirRodando(c))) return false
  ultimoToque = Date.now()

  // Pequena folga para o agendamento não cair no passado e cortar o início da nota
  const t = c.currentTime + 0.04
  if (tipo === 'success') {
    // Duas notas ascendentes, claras (Dó6 → Sol6)
    nota(c, saida, 1046.5, t, 0.16, 0.8)
    nota(c, saida, 1568.0, t + 0.13, 0.32, 0.8)
  } else {
    // Três notas graves descendentes, inconfundíveis com o sucesso (Mi5 → Si4 → Mi4)
    nota(c, saida, 659.25, t, 0.16, 0.9)
    nota(c, saida, 493.88, t + 0.15, 0.16, 0.9)
    nota(c, saida, 329.63, t + 0.30, 0.38, 0.9)
  }
  return true
}
