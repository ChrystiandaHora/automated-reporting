<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { api, type ModelStatus } from '../api'

const modelos = ref<ModelStatus[]>([])
const loading = ref(true)
const autoRefresh = ref(true)
const testingModelId = ref<string | null>(null)
let refreshInterval: any = null

// Modal de Edição de Limites
const editingModel = ref<ModelStatus | null>(null)
const editForm = ref({
  rpm_limit: 10,
  tpm_limit: 250000,
  rpd_limit: 500,
})

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
  <div class="modelos-view">
    <div class="header-section">
      <div class="header-text">
        <h1 class="page-title">
          Limites de taxa por modelo
          <span class="info-icon" title="Máximo de uso por modelo em comparação com o limite estabelecido">ⓘ</span>
        </h1>
        <p class="page-subtitle">
          Monitoramento em tempo real do volume de requisições (RPM), consumo de tokens (TPM) e uso diário (RPD).
        </p>
      </div>

      <div class="actions-header">
        <label class="toggle-label">
          <input type="checkbox" v-model="autoRefresh" />
          <span>Auto-atualizar (3s)</span>
        </label>
        <button class="btn-secondary" @click="resetarMetricas">Resetar Métricas</button>
        <button class="btn-primary" @click="carregarLimites">Atualizar Agora</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Carregando métricas dos modelos...</p>
    </div>

    <div v-else class="table-container glass-card">
      <table class="model-table">
        <thead>
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
        <tbody>
          <tr v-for="model in modelos" :key="model.id">
            <td class="model-name-cell" data-label="Modelo">
              <div class="model-title">{{ model.name }}</div>
              <div class="model-id-badge">{{ model.id }}</div>
            </td>
            <td data-label="Categoria">
              <span class="category-badge">{{ model.category }}</span>
            </td>

            <!-- RPM Metric -->
            <td class="metric-cell" data-label="RPM">
              <div class="metric-info">
                <span class="metric-text">{{ model.rpm }} / {{ model.rpm_limit }}</span>
                <span class="metric-pct">{{ model.rpm_pct }}%</span>
              </div>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill"
                  :class="{
                    'fill-danger': model.rpm_pct >= 85,
                    'fill-warning': model.rpm_pct >= 60 && model.rpm_pct < 85,
                    'fill-ok': model.rpm_pct < 60
                  }"
                  :style="{ width: Math.min(model.rpm_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- TPM Metric -->
            <td class="metric-cell" data-label="TPM">
              <div class="metric-info">
                <span class="metric-text">{{ formatTokens(model.tpm) }} / {{ formatTokens(model.tpm_limit) }}</span>
                <span class="metric-pct">{{ model.tpm_pct }}%</span>
              </div>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill"
                  :class="{
                    'fill-danger': model.tpm_pct >= 85,
                    'fill-warning': model.tpm_pct >= 60 && model.tpm_pct < 85,
                    'fill-ok': model.tpm_pct < 60
                  }"
                  :style="{ width: Math.min(model.tpm_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- RPD Metric -->
            <td class="metric-cell" data-label="RPD">
              <div class="metric-info">
                <span class="metric-text">{{ model.rpd }} / {{ model.rpd_limit }}</span>
                <span class="metric-pct">{{ model.rpd_pct }}%</span>
              </div>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill"
                  :class="{
                    'fill-danger': model.rpd_pct >= 85,
                    'fill-warning': model.rpd_pct >= 60 && model.rpd_pct < 85,
                    'fill-ok': model.rpd_pct < 60
                  }"
                  :style="{ width: Math.min(model.rpd_pct, 100) + '%' }"
                ></div>
              </div>
            </td>

            <!-- Status Pill -->
            <td data-label="Status">
              <span
                class="status-pill"
                :class="{
                  'pill-danger': model.status === 'danger',
                  'pill-warning': model.status === 'warning',
                  'pill-ok': model.status === 'ok'
                }"
              >
                <span class="status-dot"></span>
                {{ model.status === 'danger' ? 'Limite Crítico' : model.status === 'warning' ? 'Atenção' : 'Operacional' }}
              </span>
            </td>

            <!-- Actions -->
            <td class="text-right actions-cell" data-label="Ações">
              <button
                class="btn-sm btn-outline"
                :disabled="testingModelId === model.id"
                @click="simularChamada(model.id)"
                title="Simular 1 chamada para este modelo"
              >
                {{ testingModelId === model.id ? 'Testando...' : '⚡ Testar' }}
              </button>
              <button class="btn-sm btn-icon" @click="abrirEdicao(model)" title="Editar Limites">
                ⚙️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal para Editar Limites -->
    <div v-if="editingModel" class="modal-backdrop" @click.self="fecharEdicao">
      <div class="modal-card glass-card">
        <h2>Configurar Limites - {{ editingModel.name }}</h2>
        <p class="modal-desc">Ajuste os parâmetros máximos de taxa para este modelo de API.</p>

        <div class="form-group">
          <label>RPM Máximo (Requisições / Minuto):</label>
          <input type="number" v-model.number="editForm.rpm_limit" min="1" />
        </div>

        <div class="form-group">
          <label>TPM Máximo (Tokens / Minuto):</label>
          <input type="number" v-model.number="editForm.tpm_limit" min="1000" step="1000" />
        </div>

        <div class="form-group">
          <label>RPD Máximo (Requisições / Dia):</label>
          <input type="number" v-model.number="editForm.rpd_limit" min="1" />
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="fecharEdicao">Cancelar</button>
          <button class="btn-primary" @click="salvarLimites">Salvar Limites</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modelos-view {
  width: 100%;
  max-width: 80rem; /* max-w-7xl */
  margin-left: auto;
  margin-right: auto;
  padding: 1.5rem 1rem;
  box-sizing: border-box;
}

@media (min-width: 640px) {
  .modelos-view {
    padding: 2rem 1.5rem;
  }
}

@media (min-width: 1024px) {
  .modelos-view {
    padding: 2.5rem 2rem;
  }
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-text {
  flex: 1 1 300px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.info-icon {
  font-size: 1rem;
  opacity: 0.6;
  cursor: help;
}

.page-subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 4px;
}

.actions-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-muted);
  cursor: pointer;
  background: rgba(255, 255, 255, 0.05);
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  user-select: none;
}

.toggle-label input {
  accent-color: var(--accent);
}

.table-container {
  width: 100%;
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-overflow-scrolling: touch;
}

.model-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.9rem;
}

.model-table th {
  background: rgba(0, 0, 0, 0.3);
  padding: 14px 16px;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.model-table td {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.model-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.model-name-cell .model-title {
  font-weight: 600;
  color: var(--text);
  font-size: 0.95rem;
  white-space: nowrap;
}

.model-id-badge {
  font-size: 0.75rem;
  color: var(--text-subtle);
  font-family: monospace;
  margin-top: 2px;
}

.category-badge {
  background: rgba(255, 255, 255, 0.06);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.05);
  white-space: nowrap;
}

.metric-cell {
  min-width: 160px;
}

.metric-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
  margin-bottom: 6px;
}

.metric-text {
  font-weight: 600;
  color: var(--text);
}

.metric-pct {
  color: var(--text-subtle);
  font-size: 0.78rem;
}

.progress-bar-bg {
  height: 6px;
  width: 100%;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 99px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease, background-color 0.4s ease;
}

.fill-ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.fill-warning {
  background: #eab308;
  box-shadow: 0 0 8px rgba(234, 179, 8, 0.4);
}

.fill-danger {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.pill-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}
.pill-ok .status-dot { background: #4ade80; }

.pill-warning {
  background: rgba(234, 179, 8, 0.15);
  color: #fde047;
  border: 1px solid rgba(234, 179, 8, 0.3);
}
.pill-warning .status-dot { background: #fde047; }

.pill-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.pill-danger .status-dot { background: #f87171; }

.actions-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  white-space: nowrap;
}

.btn-primary {
  background: var(--accent-grad);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
  transition: opacity 0.2s;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: 6px;
}

.btn-outline {
  background: transparent;
  color: var(--accent-light);
  border: 1px solid var(--accent);
  cursor: pointer;
}

.btn-outline:hover {
  background: var(--accent-glow);
}

.btn-icon {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
}

.text-right {
  text-align: right;
}

.loading-state {
  text-align: center;
  padding: 48px;
  color: var(--text-muted);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Modal Styles */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--card-border);
  background: #0f172a;
}

.modal-card h2 {
  font-size: 1.2rem;
  margin-bottom: 6px;
  color: var(--text);
}

.modal-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  margin-bottom: 6px;
  color: var(--text-muted);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.9rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

/* ── Responsividade Avançada (Mobile e Tablets) ── */

@media (max-width: 900px) {
  .header-section {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .actions-header {
    width: 100%;
    justify-content: space-between;
  }

  .actions-header button,
  .actions-header .toggle-label {
    flex: 1 1 auto;
    justify-content: center;
    text-align: center;
  }
}

@media (max-width: 768px) {
  /* Layout em Cards para dispositivos móveis */
  .table-container {
    background: transparent;
    border: none;
    backdrop-filter: none;
    overflow: visible;
  }

  .model-table,
  .model-table thead,
  .model-table tbody,
  .model-table th,
  .model-table td,
  .model-table tr {
    display: block;
  }

  .model-table thead {
    display: none;
  }

  .model-table tbody tr {
    margin-bottom: 16px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }

  .model-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .model-table td:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .model-table td::before {
    content: attr(data-label);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-right: 12px;
    min-width: 90px;
    flex-shrink: 0;
  }

  .metric-cell {
    width: 100%;
    flex-direction: column;
    align-items: stretch !important;
  }

  .metric-cell::before {
    margin-bottom: 6px;
  }

  .metric-info {
    width: 100%;
  }

  .actions-cell {
    justify-content: flex-end;
    padding-top: 12px !important;
  }

  .page-title {
    font-size: 1.3rem;
  }
}

@media (max-width: 480px) {
  .actions-header {
    flex-direction: column;
    align-items: stretch;
  }

  .actions-header button,
  .actions-header .toggle-label {
    width: 100%;
  }

  .modal-card {
    padding: 18px;
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions button {
    width: 100%;
  }
}
</style>
