<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { api, type ModelStatus } from '../api'
import TutorialModal from '../components/TutorialModal.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseLabel from '../components/ui/BaseLabel.vue'
import BaseModal from '../components/ui/BaseModal.vue'

const modelos = ref<ModelStatus[]>([])
const loading = ref(true)
const autoRefresh = ref(true)
const testingModelId = ref<string | null>(null)
let refreshInterval: any = null

const editModalRef = ref<InstanceType<typeof BaseModal> | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

// Modal de Edição de Limites
const editingModel = ref<ModelStatus | null>(null)
const editForm = ref({
  rpm_limit: 10,
  tpm_limit: 250000,
  rpd_limit: 500,
})

// ── Classes reutilizadas no template ──
const btnPrimario = 'rounded-lg bg-primary bg-(image:--accent-grad) px-4 py-2 text-sm text-white shadow-[0_4px_12px] shadow-primary-glow hover:enabled:-translate-y-px hover:enabled:opacity-90 hover:enabled:brightness-110 active:enabled:translate-y-0 disabled:opacity-40 disabled:shadow-none'
const btnSecundario = 'rounded-lg border border-border-strong bg-white/6 px-4 py-2 text-sm text-foreground hover:bg-white/10'

const tdCls = 'border-b border-border-strong p-4 align-middle text-foreground max-md:flex max-md:items-center max-md:justify-between max-md:border-white/5 max-md:px-0 max-md:py-2.5 max-md:last:border-b-0 max-md:last:pb-0 max-md:before:mr-3 max-md:before:min-w-22.5 max-md:before:shrink-0 max-md:before:text-xs max-md:before:font-semibold max-md:before:tracking-wider max-md:before:text-muted-foreground max-md:before:uppercase max-md:before:content-[attr(data-label)]'
const tdMetricaCls = 'min-w-40 max-md:w-full max-md:flex-col max-md:items-stretch max-md:before:mb-1.5'
const metricaInfoCls = 'mb-1.5 flex justify-between text-xs max-md:w-full'
const barraFundoCls = 'h-1.5 w-full overflow-hidden rounded-full bg-white/8'
const barraCls = 'h-full rounded-full transition-[width,background-color] duration-400 ease-[ease]'

function classeFaixa(pct: number): string {
  if (pct >= 85) return 'bg-red-500 shadow-[0_0_8px] shadow-red-500/40'
  if (pct >= 60) return 'bg-yellow-500 shadow-[0_0_8px] shadow-yellow-500/40'
  return 'bg-green-500 shadow-[0_0_8px] shadow-green-500/40'
}

const classesStatus: Record<string, { pill: string; dot: string }> = {
  ok: { pill: 'border border-green-500/30 bg-green-500/15 text-green-400', dot: 'bg-green-400' },
  warning: { pill: 'border border-yellow-500/30 bg-yellow-500/15 text-yellow-300', dot: 'bg-yellow-300' },
  danger: { pill: 'border border-red-500/30 bg-red-500/15 text-red-400', dot: 'bg-red-400' },
}

function formatTokens(val: number): string {
  if (val >= 1_000_000) {
    return (val / 1_000_000).toFixed(val % 1_000_000 === 0 ? 0 : 2) + 'M'
  }
  if (val >= 1_000) {
    return (val / 1_000).toFixed(val % 1_000 === 0 ? 0 : 2) + 'K'
  }
  return val.toString()
}

async function carregarLimites() {
  try {
    const data = await api.modelos.limits()
    modelos.value = data
  } catch (e) {
    console.error('Erro ao carregar limites de modelos:', e)
  } finally {
    loading.value = false
  }
}

async function simularChamada(modelId: string) {
  testingModelId.value = modelId
  try {
    await api.modelos.testCall(modelId)
    await carregarLimites()
  } catch (e) {
    console.error('Erro ao testar chamada do modelo:', e)
  } finally {
    testingModelId.value = null
  }
}

async function resetarMetricas() {
  if (!confirm('Deseja resetar os contadores de requisições de todos os modelos?')) return
  try {
    await api.modelos.reset()
    await carregarLimites()
  } catch (e) {
    console.error('Erro ao resetar métricas:', e)
  }
}

function handleEditKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    fecharEdicao()
  }
  const painel = editModalRef.value?.panel
  if (e.key === 'Tab' && painel) {
    const focusable = painel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    if (focusable.length === 0) return
    const first = focusable[0] as HTMLElement
    const last = focusable[focusable.length - 1] as HTMLElement
    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus()
        e.preventDefault()
      }
    } else {
      if (document.activeElement === last) {
        first.focus()
        e.preventDefault()
      }
    }
  }
}

watch(editingModel, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleEditKeydown)
    nextTick(() => {
      const input = editModalRef.value?.panel?.querySelector('input') as HTMLElement | null | undefined
      input?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleEditKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

function abrirEdicao(model: ModelStatus) {
  editingModel.value = model
  editForm.value = {
    rpm_limit: model.rpm_limit,
    tpm_limit: model.tpm_limit,
    rpd_limit: model.rpd_limit,
  }
}

function fecharEdicao() {
  editingModel.value = null
}

async function salvarLimites() {
  if (!editingModel.value) return
  try {
    await api.modelos.atualizarLimits(editingModel.value.id, editForm.value)
    fecharEdicao()
    await carregarLimites()
  } catch (e) {
    console.error('Erro ao salvar limites:', e)
  }
}

onMounted(() => {
  carregarLimites()
  refreshInterval = setInterval(() => {
    if (autoRefresh.value) {
      carregarLimites()
    }
  }, 3000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<template>
  <div class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-10">
    <div class="mb-6 flex flex-wrap items-start justify-between gap-4 max-[900px]:flex-col max-[900px]:items-stretch" data-tour="modelos-cabecalho">
      <div class="flex-[1_1_300px]">
        <div class="flex items-center gap-2">
          <h1 class="flex flex-wrap items-center gap-2 text-2xl font-bold text-foreground max-md:text-xl">Limites de taxa por modelo</h1>
          <TutorialModal screenId="modelos" />
        </div>
        <p class="mt-1 text-sm text-muted-foreground">
          Monitoramento em tempo real do volume de requisições (RPM), consumo de tokens (TPM) e uso diário (RPD).
        </p>
      </div>

      <div data-tour="modelos-acoes" class="flex flex-wrap items-center gap-3 max-[900px]:w-full max-[900px]:justify-between max-[900px]:*:flex-auto max-[900px]:*:justify-center max-[900px]:*:text-center max-[480px]:flex-col max-[480px]:items-stretch max-[480px]:*:w-full">
        <label class="mb-1.5 flex cursor-pointer items-center gap-2 rounded-lg border border-border-strong bg-white/5 px-3.5 py-2 text-sm font-bold tracking-[0.05em] text-muted-foreground uppercase select-none">
          <input type="checkbox" class="accent-primary" v-model="autoRefresh" />
          <span>Auto-atualizar (3s)</span>
        </label>
        <BaseButton variant="plain" :class="btnSecundario" @click="resetarMetricas">Resetar Métricas</BaseButton>
        <BaseButton variant="plain" :class="btnPrimario" @click="carregarLimites">Atualizar Agora</BaseButton>
      </div>
    </div>

    <div v-if="loading" class="p-12 text-center text-muted-foreground">
      <div class="mx-auto mb-4 size-8 animate-spin rounded-full border-3 border-white/10 border-t-primary"></div>
      <p>Carregando métricas dos modelos...</p>
    </div>

    <div v-else data-tour="modelos-tabela-wrapper" class="w-full overflow-x-auto rounded-xl border border-border bg-card backdrop-blur-md max-md:overflow-visible max-md:border-0 max-md:bg-transparent max-md:backdrop-blur-none">
      <table data-tour="modelos-tabela" class="w-full border-collapse text-left text-sm max-md:block [&_th]:text-left [&_th]:border-b [&_th]:border-border-strong [&_th]:bg-muted dark:[&_th]:bg-black/30 [&_th]:px-4 [&_th]:py-3.5 [&_th]:text-xs [&_th]:font-semibold [&_th]:tracking-wider [&_th]:whitespace-nowrap [&_th]:text-muted-foreground [&_th]:uppercase">
        <thead class="max-md:hidden">
          <tr>
            <th>Modelo</th>
            <th>Categoria</th>
            <th>RPM (Req/Min)</th>
            <th>TPM (Tokens/Min)</th>
            <th>RPD (Req/Dia)</th>
            <th>Status</th>
            <th class="text-right">Ações</th>
          </tr>
        </thead>
        <tbody class="max-md:block">
          <tr v-for="model in modelos" :key="model.id" class="hover:bg-white/2 max-md:mb-4 max-md:block max-md:rounded-[14px] max-md:border max-md:border-border max-md:bg-card max-md:p-4 max-md:shadow-[0_4px_20px] max-md:shadow-black/20 max-md:backdrop-blur-md">
            <td :class="tdCls" data-label="Modelo">
              <div>
                <div class="text-base font-semibold whitespace-nowrap text-foreground">{{ model.name }}</div>
                <div class="mt-0.5 font-mono text-xs text-subtle-foreground">{{ model.id }}</div>
              </div>
            </td>
            <td :class="tdCls" data-label="Categoria">
              <span class="rounded-md border border-white/5 bg-white/6 px-2 py-1 text-xs whitespace-nowrap text-muted-foreground">{{ model.category }}</span>
            </td>

            <!-- RPM Metric -->
            <td :class="[tdCls, tdMetricaCls]" data-label="RPM">
              <div :class="metricaInfoCls">
                <span class="font-semibold text-foreground">{{ model.rpm }} / {{ model.rpm_limit }}</span>
                <span class="text-xs text-subtle-foreground">{{ model.rpm_pct }}%</span>
              </div>
              <div :class="barraFundoCls">
                <div
                  :class="[barraCls, classeFaixa(model.rpm_pct)]"
                  :style="{ width: Math.min(model.rpm_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- TPM Metric -->
            <td :class="[tdCls, tdMetricaCls]" data-label="TPM">
              <div :class="metricaInfoCls">
                <span class="font-semibold text-foreground">{{ formatTokens(model.tpm) }} / {{ formatTokens(model.tpm_limit) }}</span>
                <span class="text-xs text-subtle-foreground">{{ model.tpm_pct }}%</span>
              </div>
              <div :class="barraFundoCls">
                <div
                  :class="[barraCls, classeFaixa(model.tpm_pct)]"
                  :style="{ width: Math.min(model.tpm_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- RPD Metric -->
            <td :class="[tdCls, tdMetricaCls]" data-label="RPD">
              <div :class="metricaInfoCls">
                <span class="font-semibold text-foreground">{{ model.rpd }} / {{ model.rpd_limit }}</span>
                <span class="text-xs text-subtle-foreground">{{ model.rpd_pct }}%</span>
              </div>
              <div :class="barraFundoCls">
                <div
                  :class="[barraCls, classeFaixa(model.rpd_pct)]"
                  :style="{ width: Math.min(model.rpd_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- Status Pill -->
            <td :class="tdCls" data-label="Status">
              <span
                :class="['inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap', classesStatus[model.status]?.pill]"
              >
                <span :class="['size-1.5 rounded-full', classesStatus[model.status]?.dot]"></span>
                {{ model.status === 'danger' ? 'Limite Crítico' : model.status === 'warning' ? 'Atenção' : 'Operacional' }}
              </span>
            </td>

            <!-- Actions -->
            <td :class="[tdCls, 'text-right whitespace-nowrap max-md:justify-end max-md:pt-3']" data-label="Ações" data-tour="modelos-celula-acoes">
              <div class="flex items-center justify-end gap-2">
              <button
                data-tour="modelos-testar"
                class="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-primary bg-transparent px-3 py-1.5 text-xs text-primary-light hover:bg-primary-glow disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="testingModelId === model.id"
                @click="simularChamada(model.id)"
                title="Simular 1 chamada para este modelo"
              >
                <i class="fa-solid fa-bolt" aria-hidden="true"></i>
                <span>{{ testingModelId === model.id ? 'Testando...' : 'Testar' }}</span>
              </button>
              <button data-tour="modelos-editar" class="cursor-pointer rounded-md border border-border-strong bg-transparent px-2 py-1.5 text-xs text-foreground hover:bg-white/10" @click="abrirEdicao(model)" title="Editar Limites" aria-label="Editar limites do modelo">
                <i class="fa-solid fa-gear" aria-hidden="true"></i>
              </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal para Editar Limites -->
    <BaseModal
      v-if="editingModel"
      ref="editModalRef"
      labelledby="edit-modal-title"
      class="max-[480px]:[&>div]:p-4.5 max-[480px]:[&_[data-modal-actions]]:flex-col max-[480px]:[&_[data-modal-actions]>*]:w-full"
      @close="fecharEdicao"
    >
      <div>
        <h2 id="edit-modal-title" class="mb-1.5 text-xl font-bold text-foreground">Configurar Limites - {{ editingModel.name }}</h2>
        <p class="text-sm text-muted-foreground">Ajuste os parâmetros máximos de taxa para este modelo de API.</p>
      </div>

      <div>
        <BaseLabel for="edit-rpm-limit">RPM Máximo (Requisições / Minuto):</BaseLabel>
        <BaseInput id="edit-rpm-limit" type="number" v-model.number="editForm.rpm_limit" min="1" />
      </div>

      <div>
        <BaseLabel for="edit-tpm-limit">TPM Máximo (Tokens / Minuto):</BaseLabel>
        <BaseInput id="edit-tpm-limit" type="number" v-model.number="editForm.tpm_limit" min="1000" step="1000" />
      </div>

      <div>
        <BaseLabel for="edit-rpd-limit">RPD Máximo (Requisições / Dia):</BaseLabel>
        <BaseInput id="edit-rpd-limit" type="number" v-model.number="editForm.rpd_limit" min="1" />
      </div>

      <template #actions>
        <BaseButton variant="plain" :class="btnSecundario" @click="fecharEdicao">Cancelar</BaseButton>
        <BaseButton variant="plain" :class="btnPrimario" @click="salvarLimites">Salvar Limites</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
