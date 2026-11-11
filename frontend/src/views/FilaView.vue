<template>
  <div class="page fila-page">
    <div class="page-header">
      <div class="title-row">
        <h1>Fila de Execução</h1>
        <TutorialModal screenId="fila" />
        <span v-if="concurrencyInfo" class="concurrency-badge" :title="`Fila de análises: ${concurrencyInfo.queues.analises} workers | Fila de envios: ${concurrencyInfo.queues.envios} workers | Pool compartilhado de até ${concurrencyInfo.total_system_limit} workers simultâneos`">
          <i class="fa-solid fa-bolt" aria-hidden="true" style="margin-right: 4px;"></i>Concorrência: {{ concurrencyInfo.queues.analises }} análises / {{ concurrencyInfo.queues.envios }} envios ({{ concurrencyInfo.total_system_limit }} total | {{ concurrencyInfo.cpu_cores }} Cores CPU)
        </span>
      </div>
      <div class="header-actions">
        <button 
          v-if="pausedJobsCount > 0" 
          class="btn-ghost btn-sm btn-retomar" 
          @click="retomarTodas"
          :title="`Volta para a fila as ${pausedJobsCount} tarefa(s) pausada(s)`"
        >
          <i class="fa-solid fa-play" aria-hidden="true"></i>
          <span>Retomar Pausadas ({{ pausedJobsCount }})</span>
        </button>
        <button 
          v-if="pausableJobsCount > 0" 
          class="btn-ghost btn-sm btn-pausar" 
          @click="pausarTodas"
          :title="`Pausa as ${pausableJobsCount} análise(s)/envio(s) que ainda não começaram. O que está em execução termina normalmente.`"
        >
          <i class="fa-solid fa-pause" aria-hidden="true"></i>
          <span>Pausar Pendentes ({{ pausableJobsCount }})</span>
        </button>
        <button 
          v-if="failedJobsCount > 0" 
          class="btn-retry-all" 
          @click="reenfileirarTodasComFalha"
          :title="`Reenfileira todas as ${failedJobsCount} tarefas com falha`"
        >
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true" style="margin-right: 4px;"></i>
          <span>Reenfileirar Todas com Falha ({{ failedJobsCount }})</span>
        </button>
        <button 
          class="btn-ghost btn-sm btn-limpar-antigos" 
          @click="limparMesesAnteriores" 
          title="Remover tarefas da fila concluídas ou com erro de meses passados"
        >
          <i class="fa-solid fa-broom" aria-hidden="true"></i>
          <span>Limpar Meses Anteriores</span>
        </button>
        <button class="btn-ghost btn-sm" @click="atualizarFila">
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true" style="margin-right: 4px;"></i>
          <span>Atualizar</span>
        </button>
      </div>
    </div>

    <!-- Feedback de carregamento inicial -->
    <div v-if="filaStore.loading && filaStore.jobs.length === 0" class="loading">Carregando fila...</div>

    <template v-else>
      <!-- SEÇÃO DE TAREFAS EM EXECUÇÃO AGORA (FIXADA NO TOPO) -->
      <section v-if="jobsEmExecucao.length > 0" class="fila-execucao-topo" aria-label="Tarefas em execução agora">
        <div class="execucao-topo-header">
          <div class="execucao-topo-title">
            <span class="live-pulse-icon">
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
            </span>
            <div>
              <h2>Em Execução Agora</h2>
              <span class="execucao-topo-sub">
                {{ jobsEmExecucao.length === 1 ? '1 tarefa sendo processada em tempo real' : `${jobsEmExecucao.length} tarefas sendo processadas simultaneamente` }}
                <span v-if="pendingJobsCount > 0" class="execucao-topo-pending-pill">
                  • {{ pendingJobsCount }} aguardando na fila
                </span>
              </span>
            </div>
          </div>
          <div class="execucao-topo-badge">
            <span class="live-dot-pulse"></span>
            <span>AO VIVO</span>
          </div>
        </div>

        <div class="running-cards-grid">
          <div 
            v-for="job in jobsEmExecucao" 
            :key="job.id" 
            class="running-task-card"
            :class="`running-task-${job.tipo}`"
          >
            <div class="running-task-header">
              <div class="running-task-badges">
                <span 
                  class="badge" 
                  :class="{
                    'badge-blue': job.tipo === 'analise',
                    'badge-purple': job.tipo === 'envio' || job.tipo === 'ajuste',
                    'badge-orange': job.tipo === 'verificacao'
                  }"
                >
                  <i 
                    :class="{
                      'fa-solid fa-wand-magic-sparkles': job.tipo === 'analise',
                      'fa-solid fa-cloud-arrow-up': job.tipo === 'envio',
                      'fa-solid fa-sliders': job.tipo === 'ajuste',
                      'fa-solid fa-arrows-rotate': job.tipo === 'verificacao'
                    }"
                    aria-hidden="true"
                    style="margin-right: 4px;"
                  ></i>
                  {{ formatarTipoJob(job.tipo) }}
                </span>
                <span class="running-job-id">Job #{{ job.id }}</span>
                <span class="running-job-time">{{ formatarData(job.criado_em) }}</span>
              </div>

              <div class="running-task-actions">
                <router-link
                  v-if="job.commit_id && job.commit_id !== 'sem-commit'"
                  :to="`/commits/${job.commit_id}`"
                  class="btn-ghost btn-xs"
                  title="Ver página deste commit"
                >
                  <i class="fa-solid fa-code-commit" aria-hidden="true" style="margin-right: 4px;"></i>Ver Commit
                </router-link>

                <button 
                  class="btn-live-logs btn-xs" 
                  @click="abrirLogs(job)"
                  title="Acompanhar logs ao vivo da execução"
                >
                  <i class="fa-solid fa-terminal" aria-hidden="true" style="margin-right: 4px;"></i>
                  <span>Logs (Ao Vivo)</span>
                </button>
                
                <button 
                  class="btn-danger-link btn-xs" 
                  @click="cancelarJob(job.id)"
                  title="Interromper esta tarefa imediatamente"
                >
                  <i class="fa-solid fa-ban" aria-hidden="true" style="margin-right: 4px;"></i>
                  <span>Cancelar</span>
                </button>
              </div>
            </div>

            <div class="running-task-body">
              <div v-if="job.commit_id && job.commit_id !== 'sem-commit'" class="running-task-commit-info">
                <router-link :to="`/commits/${job.commit_id}`" class="commit-hash-link">
                  {{ job.commit_id.slice(0, 8) }}
                </router-link>
                <span class="running-commit-msg" :title="job.commit_mensagem">
                  {{ job.commit_mensagem }}
                </span>
              </div>

              <div class="running-task-meta">
                <template v-if="job.tipo === 'analise'">
                  <span class="meta-label">Modelo AI:</span>
                  <strong class="meta-value">{{ job.modelo || 'Gemini 3.8 Flash' }}</strong>
                </template>
                <template v-else-if="job.tipo === 'envio'">
                  <span class="meta-label">Atividade:</span>
                  <strong class="meta-value">"{{ job.titulo_atividade || 'Lançamento de atividade no portal Munka...' }}"</strong>
                </template>
                <template v-else-if="job.tipo === 'ajuste'">
                  <span class="meta-label">Ajuste Munka:</span>
                  <strong class="meta-value">{{ job.titulo_atividade || 'Ajuste de campos de tarefa no portal' }}</strong>
                </template>
                <template v-else-if="job.tipo === 'verificacao'">
                  <span class="meta-label">Sincronização:</span>
                  <strong class="meta-value">Varredura e auditoria dos status no portal Munka</strong>
                </template>
              </div>

              <div class="running-log-box">
                <span class="live-dot-pulse"></span>
                <span class="live-log-text">{{ obterUltimoLog(job) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Aviso sutil quando não há tarefas rodando, mas há pendentes na fila -->
      <div v-if="jobsEmExecucao.length === 0 && pendingJobsCount > 0" class="fila-pending-bar">
        <div class="pending-bar-info">
          <i class="fa-solid fa-clock-rotate-left" aria-hidden="true"></i>
          <span><strong>{{ pendingJobsCount }} tarefa(s) aguardando na fila.</strong> Os workers iniciarão o processamento conforme a disponibilidade de concorrência.</span>
        </div>
      </div>

      <!-- Layout Dividido Verticalmente: Lançamentos (Esquerda) e Ajustes (Direita) -->
      <div class="fila-split-layout">
      
      <!-- COLUNA ESQUERDA: Lançamentos ao Munka & Análises -->
      <section class="fila-coluna coluna-lancamentos">
        <div class="coluna-header">
          <div class="coluna-title-left">
            <div class="coluna-icon icon-lancamentos">
              <i class="fa-solid fa-cloud-arrow-up" aria-hidden="true"></i>
            </div>
            <div>
              <h2>Lançamentos</h2>
              <span class="coluna-sub">Análises AI e Envios ao Portal Munka</span>
            </div>
          </div>
          <span class="coluna-badge">{{ jobsLancamentos.length }}</span>
        </div>

        <div v-if="jobsLancamentos.length === 0" class="empty-coluna">
          <i class="fa-regular fa-folder-open empty-coluna-icon" aria-hidden="true"></i>
          <span>Nenhum lançamento de atividade na fila.</span>
        </div>

        <div v-else class="fila-grouped">
          <!-- Percorre os commits agrupados -->
          <div v-for="grupo in jobsLancamentosAgrupados" :key="grupo.commit_id" class="commit-group">
            <!-- Cabeçalho do Commit -->
            <button 
              class="commit-group-header" 
              type="button"
              :aria-expanded="!isGrupoColapsado(grupo.commit_id, grupo)"
              :aria-controls="'group-jobs-' + grupo.commit_id"
              @click="alternarGrupo(grupo.commit_id)" 
            >
              <div class="commit-group-info">
                <span class="collapse-icon" aria-hidden="true">{{ isGrupoColapsado(grupo.commit_id, grupo) ? '▶' : '▼' }}</span>
                <router-link v-if="grupo.commit_id && grupo.commit_id !== 'sem-commit'" :to="`/commits/${grupo.commit_id}`" class="commit-hash-link" @click.stop>
                  {{ grupo.commit_id.slice(0, 8) }}
                </router-link>
                <span class="commit-msg-link" :title="grupo.commit_mensagem">
                  {{ grupo.commit_mensagem }}
                </span>
                <span v-if="temExecucaoNoGrupo(grupo)" class="badge-running-pill" title="Existe tarefa sendo executada neste commit">
                  <span class="live-dot-pulse"></span>
                  <span>Em Execução</span>
                </span>
              </div>
              <div class="commit-group-right">
                <button 
                  v-if="pausaveisNoGrupo(grupo) > 0" 
                  type="button"
                  class="btn-ghost btn-xs btn-pausar" 
                  @click.stop="filaStore.pausarJobs({ job_ids: idsPausaveis(grupo.jobs) })"
                  :title="`Pausar ${pausaveisNoGrupo(grupo)} tarefa(s) pendente(s) deste commit`"
                >
                  <i class="fa-solid fa-pause" aria-hidden="true"></i>
                  <span>Pausar ({{ pausaveisNoGrupo(grupo) }})</span>
                </button>
                <button 
                  v-if="pausadosNoGrupo(grupo) > 0" 
                  type="button"
                  class="btn-ghost btn-xs btn-retomar" 
                  @click.stop="filaStore.retomarJobs({ job_ids: idsPausados(grupo.jobs) })"
                  :title="`Retomar ${pausadosNoGrupo(grupo)} tarefa(s) pausada(s) deste commit`"
                >
                  <i class="fa-solid fa-play" aria-hidden="true"></i>
                  <span>Retomar ({{ pausadosNoGrupo(grupo) }})</span>
                </button>
                <button 
                  v-if="temErrosNoGrupo(grupo)" 
                  class="btn-retry-commit" 
                  @click.stop="reenfileirarGrupo(grupo)"
                  :title="`Reenfileirar ${errosNoGrupoCount(grupo)} tarefa(s) com falha deste commit`"
                >
                  <i class="fa-solid fa-arrows-rotate" aria-hidden="true" style="margin-right: 4px;"></i>
                  <span>Falhas ({{ errosNoGrupoCount(grupo) }})</span>
                </button>
                <span class="job-count-badge">{{ grupo.jobs.length }}</span>
              </div>
            </button>

            <!-- Lista de tarefas deste commit -->
            <div v-show="!isGrupoColapsado(grupo.commit_id, grupo)" :id="'group-jobs-' + grupo.commit_id" class="commit-group-jobs">
              <div 
                v-for="job in grupo.jobs" 
                :key="job.id" 
                class="job-row"
                :class="`job-row-${job.status}`"
              >
                <div class="job-header">
                  <span 
                    class="badge" 
                    :class="job.tipo === 'analise' ? 'badge-blue' : 'badge-purple'"
                  >
                    {{ job.tipo === 'analise' ? 'Análise AI' : 'Envio Portal' }}
                  </span>
                  
                  <span class="job-time">{{ formatarData(job.criado_em) }}</span>
                  
                  <div class="job-actions">
                    <!-- Botão de Verificação / Correção -->
                    <button 
                      v-if="job.status === 'done' && job.tipo === 'envio'" 
                      class="btn-xs btn-verificacao-status" 
                      :class="{
                        'btn-status-ok': !isVerificando(job.id) && obterStatusVerificacao(job) === 'ok',
                        'btn-status-divergencia': !isVerificando(job.id) && obterStatusVerificacao(job) === 'divergencia',
                        'btn-status-default': isVerificando(job.id) || !obterStatusVerificacao(job)
                      }"
                      @click="handleAcaoVerificacao(job)"
                      :disabled="isVerificando(job.id)"
                      :title="obterTituloVerificacao(job)"
                    >
                      <template v-if="isVerificando(job.id)">
                        <i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true" style="margin-right: 4px;"></i>Verificando...
                      </template>
                      <template v-else-if="obterStatusVerificacao(job) === 'ok'">
                        <i class="fa-solid fa-circle-check" aria-hidden="true" style="margin-right: 4px;"></i>Lançamento OK
                      </template>
                      <template v-else-if="obterStatusVerificacao(job) === 'divergencia'">
                        <i class="fa-solid fa-triangle-exclamation" aria-hidden="true" style="margin-right: 4px;"></i>Corrigir
                      </template>
                      <template v-else>
                        <i class="fa-solid fa-magnifying-glass" aria-hidden="true" style="margin-right: 4px;"></i>Verificar
                      </template>
                    </button>

                    <!-- Botão de Ver Commit (análise concluída abre o commit analisado) -->
                    <router-link
                      v-if="job.status === 'done' && job.tipo === 'analise' && job.commit_id"
                      :to="`/commits/${job.commit_id}`"
                      class="btn-ghost btn-xs"
                    >
                      <i class="fa-solid fa-code-commit" aria-hidden="true" style="margin-right: 4px;"></i>Ver Commit
                    </router-link>

                    <!-- Botão de Ver Tarefa (envio concluído abre a tarefa no portal) -->
                    <a
                      v-else-if="job.status === 'done' && job.resultado && job.resultado.task_url"
                      :href="job.resultado.task_url" 
                      target="_blank" 
                      class="btn-ghost btn-xs" 
                    >
                      Ver Tarefa
                    </a>
                    
                    <!-- Botão de Ver Logs -->
                    <button 
                      v-if="job.status === 'running' || (job.resultado && job.resultado.logs && job.resultado.logs.length)" 
                      class="btn-ghost btn-xs" 
                      @click="abrirLogs(job)"
                    >
                      <i :class="job.status === 'running' ? 'fa-solid fa-terminal' : 'fa-solid fa-file-waveform'" aria-hidden="true" style="margin-right: 4px;"></i>
                      <span>{{ job.status === 'running' ? 'Logs (Ao Vivo)' : 'Ver Logs' }}</span>
                    </button>
                    
                    <!-- Botão Pausar (só antes de começar: envio em execução está no meio do portal) -->
                    <button 
                      v-if="podePausar(job)" 
                      class="btn-ghost btn-xs btn-pausar" 
                      @click="filaStore.pausarJobs({ job_ids: [job.id] })"
                      title="Pausa esta tarefa antes de ela começar"
                    >
                      <i class="fa-solid fa-pause" aria-hidden="true"></i><span>Pausar</span>
                    </button>

                    <!-- Botão Retomar -->
                    <button 
                      v-if="job.status === 'paused'" 
                      class="btn-ghost btn-xs btn-retomar" 
                      @click="filaStore.retomarJobs({ job_ids: [job.id] })"
                      title="Devolve esta tarefa para a fila"
                    >
                      <i class="fa-solid fa-play" aria-hidden="true"></i><span>Retomar</span>
                    </button>

                    <!-- Botão Cancelar -->
                    <button 
                      v-if="job.status === 'pending' || job.status === 'running' || job.status === 'paused'" 
                      class="btn-danger-link" 
                      @click="cancelarJob(job.id)"
                      :title="job.status === 'running' ? 'Interrompe a execução' : 'Remove da fila'"
                    >
                      <i class="fa-solid fa-ban" aria-hidden="true" style="margin-right: 4px;"></i>
                      <span>Cancelar</span>
                    </button>

                    <!-- Botão Limpar -->
                    <button 
                      v-if="['done', 'error'].includes(job.status)" 
                      class="btn-danger-link" 
                      @click="removerJob(job.id)"
                    >
                      Limpar
                    </button>
                  </div>
                </div>

                <div class="job-body">
                  <div v-if="job.tipo === 'analise'" class="job-meta">
                    <strong>Modelo:</strong> {{ job.modelo }}
                  </div>
                  
                  <div v-else-if="job.tipo === 'envio'" class="job-meta">
                    <strong>Atividade:</strong> "{{ job.titulo_atividade || 'Carregando título...' }}"
                  </div>

                  <!-- Mensagem de Erro -->
                  <div v-if="job.status === 'error'" class="error-box">
                    <span>{{ obterMensagemErro(job) }}</span>
                  </div>

                  <!-- Faixa de Logs em Tempo Real durante Execução -->
                  <div v-if="job.status === 'running'" class="running-log-box">
                    <span class="live-dot-pulse"></span>
                    <span class="live-log-text">{{ obterUltimoLog(job) }}</span>
                  </div>

                  <!-- Seleção de outro modelo em caso de limite atingido -->
                  <div v-if="podeMudarModelo(job)" class="mudar-modelo-box">
                    <label :for="'select-model-' + job.id" class="mudar-modelo-label">Limite atingido. Tentar outro modelo:</label>
                    <div class="mudar-modelo-control">
                      <select 
                        :id="'select-model-' + job.id"
                        :value="obterModeloSelecionado(job.id, job.modelo)" 
                        @change="atualizarModeloSelecionado(job.id, $event)"
                        class="select-modelo"
                      >
                        <option v-for="m in models" :key="m.name" :value="m.name">
                          {{ m.name }}
                        </option>
                      </select>
                      <button class="btn-primary-mudar" @click="reprocessarComOutroModelo(job)">
                        Reprocessar
                      </button>
                    </div>
                  </div>

                  <!-- Reenviar em caso de término ou falha de envio -->
                  <div v-if="job.tipo === 'envio' && (job.status === 'error' || job.status === 'completed')" class="mudar-modelo-box">
                    <span class="mudar-modelo-label">
                      {{ job.status === 'completed' ? 'Atividade concluída. Deseja re-enviar ao portal?' : 'Esta atividade falhou no envio. Deseja tentar novamente?' }}
                    </span>
                    <div class="mudar-modelo-control">
                      <button class="btn-primary-mudar" @click="reenviarAtividade(job)">
                        {{ job.status === 'completed' ? 'Re-enviar Envio' : 'Tentar Novamente' }}
                      </button>
                    </div>
                  </div>
                </div>

                <div class="job-footer">
                  <div class="status-indicator">
                    <span class="status-dot" :class="`status-${job.status}`"></span>
                    <span class="status-text">{{ formatarStatus(job.status) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- COLUNA DIREITA: Ajustes dos Cards & Sincronizações -->
      <section class="fila-coluna coluna-ajustes">
        <div class="coluna-header">
          <div class="coluna-title-left">
            <div class="coluna-icon icon-ajustes">
              <i class="fa-solid fa-sliders" aria-hidden="true"></i>
            </div>
            <div>
              <h2>Ajustes & Sincronizações</h2>
              <span class="coluna-sub">Ajustes de campos e auditoria de status no Munka</span>
            </div>
          </div>
          <span class="coluna-badge badge-ajuste">{{ jobsAjustes.length }}</span>
        </div>

        <div v-if="jobsAjustes.length === 0" class="empty-coluna">
          <i class="fa-solid fa-sliders empty-coluna-icon" aria-hidden="true"></i>
          <span>Nenhum ajuste ou sincronização na fila.</span>
          <router-link to="/tarefas-mes" class="btn-link-tarefas-mes">
            Ir para Tarefas do Mês para ajustar cards →
          </router-link>
        </div>

        <div v-else class="ajustes-cards-list">
          <div 
            v-for="job in jobsAjustes" 
            :key="job.id" 
            class="ajuste-card"
            :class="`ajuste-card-${job.status}`"
          >
            <!-- Card Header -->
            <div class="ajuste-card-header">
              <div class="ajuste-card-header-left">
                <span class="badge" :class="job.tipo === 'ajuste' ? 'badge-purple' : 'badge-orange'">
                  <i :class="job.tipo === 'ajuste' ? 'fa-solid fa-sliders' : 'fa-solid fa-arrows-rotate'" aria-hidden="true"></i>
                  <span>{{ job.tipo === 'ajuste' ? 'Ajuste Munka' : 'Sincronização' }}</span>
                </span>
                <span class="job-time">{{ formatarData(job.criado_em) }}</span>
              </div>

              <div class="job-actions">
                <!-- Botão Ver Logs -->
                <button 
                  v-if="job.status === 'running' || (job.resultado && job.resultado.logs && job.resultado.logs.length)" 
                  class="btn-ghost btn-xs" 
                  @click="abrirLogs(job)"
                >
                  <i :class="job.status === 'running' ? 'fa-solid fa-terminal' : 'fa-solid fa-file-waveform'" aria-hidden="true" style="margin-right: 4px;"></i>
                  <span>{{ job.status === 'running' ? 'Logs (Ao Vivo)' : 'Ver Logs' }}</span>
                </button>

                <!-- Botão Cancelar -->
                <button 
                  v-if="job.status === 'pending' || job.status === 'running'" 
                  class="btn-danger-link" 
                  @click="cancelarJob(job.id)"
                >
                  <i class="fa-solid fa-ban" aria-hidden="true" style="margin-right: 4px;"></i>
                  <span>Cancelar</span>
                </button>

                <!-- Botão Limpar -->
                <button 
                  v-if="['done', 'error'].includes(job.status)" 
                  class="btn-danger-link" 
                  @click="removerJob(job.id)"
                >
                  Limpar
                </button>
              </div>
            </div>

            <!-- Card Body -->
            <div class="ajuste-card-body">
              <div class="ajuste-title-row">
                <span class="ajuste-title">
                  {{ job.titulo_atividade || (job.tipo === 'ajuste' ? 'Ajuste de Tarefa no Munka' : 'Sincronização de Status') }}
                </span>
              </div>

              <!-- Chips com os campos alterados -->
              <div v-if="obterAlteracoesJob(job)" class="ajuste-chips-container">
                <span class="chips-label">Campos alterados:</span>
                <div class="chips-list">
                  <span v-for="(val, chave) in obterAlteracoesJob(job)" :key="chave" class="param-chip">
                    <strong>{{ formatarNomeCampo(String(chave)) }}:</strong>
                    <span>{{ formatarValorCampo(String(chave), String(val)) }}</span>
                  </span>
                </div>
              </div>

              <!-- Se for sincronização -->
              <div v-else-if="job.tipo === 'verificacao'" class="sync-desc-box">
                <i class="fa-solid fa-circle-nodes" aria-hidden="true"></i>
                <span>Varredura da listagem de tarefas do mês e atualização dos status no portal.</span>
              </div>

              <!-- Faixa de Logs ao Vivo durante Execução -->
              <div v-if="job.status === 'running'" class="running-log-box">
                <span class="live-dot-pulse"></span>
                <span class="live-log-text">{{ obterUltimoLog(job) }}</span>
              </div>

              <!-- Mensagem de Erro -->
              <div v-if="job.status === 'error'" class="error-box">
                <span>{{ obterMensagemErro(job) }}</span>
              </div>

              <!-- Resumo de Conclusão -->
              <div v-if="job.status === 'done' && job.resultado" class="done-summary-box">
                <template v-if="job.tipo === 'ajuste'">
                  <span class="summary-check">
                    <i class="fa-solid fa-circle-check" aria-hidden="true" style="margin-right: 4px;"></i>
                    <span>Sucesso: {{ job.resultado.sucessos || 1 }} tarefa(s) ajustada(s) no portal.</span>
                  </span>
                  <span v-if="job.resultado.puladas" class="summary-warn">
                    <i class="fa-solid fa-triangle-exclamation" aria-hidden="true" style="margin-right: 4px;"></i>
                    <span>{{ job.resultado.puladas }} tarefa(s) já estavam concluídas pelo supervisor e foram preservadas.</span>
                  </span>
                </template>
                <template v-else>
                  <span class="summary-check">
                    <i class="fa-solid fa-circle-check" aria-hidden="true" style="margin-right: 4px;"></i>
                    <span>Sincronização concluída: {{ job.resultado.total_portal || 0 }} tarefas lidas no portal, {{ job.resultado.total_atualizadas || 0 }} atualizadas no banco.</span>
                  </span>
                </template>
              </div>
            </div>

            <!-- Card Footer -->
            <div class="job-footer">
              <div class="status-indicator">
                <span class="status-dot" :class="`status-${job.status}`"></span>
                <span class="status-text">{{ formatarStatus(job.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
    </template>

    <!-- Modal de Logs -->
    <div v-if="logJobSelecionado" class="modal-overlay" @click.self="fecharLogs">
      <div ref="logsModalRef" class="modal modal-wide" role="dialog" aria-modal="true" aria-labelledby="logs-modal-title">
        <h2 id="logs-modal-title">Logs de Automação (Job #{{ logJobSelecionado.id }})</h2>
        <p class="modal-subtitle">Tarefa: "{{ logJobSelecionado.titulo_atividade }}"</p>
        
        <div class="terminal-container">
          <div class="terminal-header">
            <span>Logs de Execução Playwright</span>
            <span class="status-badge" :class="logJobSelecionado.status === 'running' ? 'badge-blue' : `badge-${logJobSelecionado.status}`">
              <span v-if="logJobSelecionado.status === 'running'">
                <i class="fa-solid fa-bolt" aria-hidden="true" style="margin-right: 4px;"></i>TRANSMITINDO AO VIVO
              </span>
              <span v-else>{{ logJobSelecionado.status }}</span>
            </span>
          </div>
          <pre class="terminal-body"><div v-for="(log, idx) in (logJobSelecionado.resultado?.logs || [])" :key="idx" :class="{'error-line': log.includes('\u274c') || log.includes('ERRO')}">{{ log }}</div></pre>
        </div>

        <div class="modal-actions">
          <button class="btn-ghost" @click="fecharLogs">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useFilaStore } from '../stores/fila'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import { api, type Config } from '../api'

const filaStore = useFilaStore()
const toastStore = useToastStore()
const logJobSelecionado = ref<any>(null)
const concurrencyInfo = ref<Config['concurrency'] | null>(null)

const logsModalRef = ref<HTMLElement | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

const jobsEmVerificacao = ref<Record<number, boolean>>({})

function isVerificando(jobId: number): boolean {
  return !!jobsEmVerificacao.value[jobId]
}

const failedJobsCount = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'error').length
})

// ── Pausa: só análises/envios que ainda não começaram ──
function podePausar(job: { tipo: string; status: string }) {
  return job.status === 'pending' && (job.tipo === 'analise' || job.tipo === 'envio')
}

function idsPausaveis(jobs: any[]) {
  return jobs.filter(podePausar).map(j => j.id)
}

function idsPausados(jobs: any[]) {
  return jobs.filter(j => j.status === 'paused').map(j => j.id)
}

function pausaveisNoGrupo(grupo: { jobs: any[] }) {
  return idsPausaveis(grupo.jobs).length
}

function pausadosNoGrupo(grupo: { jobs: any[] }) {
  return idsPausados(grupo.jobs).length
}

const pausableJobsCount = computed(() => idsPausaveis(filaStore.jobs).length)
const pausedJobsCount = computed(() => idsPausados(filaStore.jobs).length)

async function pausarTodas() {
  if (confirm(`Pausar ${pausableJobsCount.value} tarefa(s) que ainda não começaram? As que já estão em execução terminam normalmente.`)) {
    await filaStore.pausarJobs({})
  }
}

async function retomarTodas() {
  await filaStore.retomarJobs({})
}

async function reenfileirarTodasComFalha() {
  if (confirm(`Deseja reenfileirar todas as ${failedJobsCount.value} tarefas com falha para processamento automático?`)) {
    await filaStore.reenfileirarComErros()
  }
}

async function limparMesesAnteriores() {
  if (!confirm('Deseja remover da fila todas as tarefas de meses anteriores já concluídas ou com erro? As tarefas do mês atual serão mantidas.')) {
    return
  }
  try {
    const res = await api.fila.limparMesesAnteriores()
    toastStore.addToast(res.message, 'success')
    await filaStore.fetchJobs()
  } catch (e: any) {
    toastStore.addToast(`Erro ao limpar tarefas de meses anteriores: ${e.response?.data?.detail || e.message || e}`, 'error')
  }
}

// ── Tarefas em Execução e Pendentes ──
const jobsEmExecucao = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'running')
})

const pendingJobsCount = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending').length
})

function formatarTipoJob(tipo: string): string {
  const map: Record<string, string> = {
    analise: 'Análise AI',
    envio: 'Envio Portal',
    ajuste: 'Ajuste Munka',
    verificacao: 'Sincronização'
  }
  return map[tipo] || tipo
}

function temExecucaoNoGrupo(grupo: { jobs: any[] }) {
  return grupo.jobs.some(j => j.status === 'running')
}

// ── Divisão entre Lançamentos e Ajustes ──
const jobsLancamentos = computed(() => {
  return filaStore.jobs.filter(j => j.tipo === 'analise' || j.tipo === 'envio')
})

const jobsAjustes = computed(() => {
  return filaStore.jobs
    .filter(j => j.tipo === 'ajuste' || j.tipo === 'verificacao')
    .sort((a, b) => {
      // Prioridade: Tarefas em execução primeiro, depois pendentes, depois por data mais recente
      if (a.status === 'running' && b.status !== 'running') return -1
      if (b.status === 'running' && a.status !== 'running') return 1
      if (a.status === 'pending' && b.status !== 'pending') return -1
      if (b.status === 'pending' && a.status !== 'pending') return 1
      return new Date(b.criado_em).getTime() - new Date(a.criado_em).getTime()
    })
})

const jobsLancamentosAgrupados = computed(() => {
  const grupos: Record<string, { commit_id: string; commit_mensagem: string; jobs: any[] }> = {}
  
  for (const job of jobsLancamentos.value) {
    const key = job.commit_id || 'sem-commit'
    if (!grupos[key]) {
      grupos[key] = {
        commit_id: job.commit_id,
        commit_mensagem: job.commit_mensagem || '(sem mensagem)',
        jobs: []
      }
    }
    grupos[key].jobs.push(job)
  }

  // Dentro de cada commit: running primeiro, depois pending, depois mais novas
  for (const key in grupos) {
    grupos[key].jobs.sort((a, b) => {
      if (a.status === 'running' && b.status !== 'running') return -1
      if (b.status === 'running' && a.status !== 'running') return 1
      if (a.status === 'pending' && b.status !== 'pending') return -1
      if (b.status === 'pending' && a.status !== 'pending') return 1
      return new Date(b.criado_em).getTime() - new Date(a.criado_em).getTime()
    })
  }
  
  return Object.values(grupos).sort((a, b) => {
    // Commits com tarefas em execução vão diretamente para o topo
    const hasRunningA = a.jobs.some(j => j.status === 'running')
    const hasRunningB = b.jobs.some(j => j.status === 'running')
    if (hasRunningA && !hasRunningB) return -1
    if (!hasRunningA && hasRunningB) return 1

    // Commits com tarefas pendentes em seguida
    const hasPendingA = a.jobs.some(j => j.status === 'pending')
    const hasPendingB = b.jobs.some(j => j.status === 'pending')
    if (hasPendingA && !hasPendingB) return -1
    if (!hasPendingA && hasPendingB) return 1

    const maxA = Math.max(...a.jobs.map(j => new Date(j.criado_em).getTime()))
    const maxB = Math.max(...b.jobs.map(j => new Date(j.criado_em).getTime()))
    return maxB - maxA
  })
})

function temErrosNoGrupo(grupo: { commit_id: string; jobs: any[] }) {
  return grupo.jobs.some(j => j.status === 'error')
}

function errosNoGrupoCount(grupo: { commit_id: string; jobs: any[] }) {
  return grupo.jobs.filter(j => j.status === 'error').length
}

async function reenfileirarGrupo(grupo: { commit_id: string; jobs: any[] }) {
  const count = errosNoGrupoCount(grupo)
  if (confirm(`Deseja reenfileirar ${count} tarefa(s) com falha deste commit (${grupo.commit_id.slice(0, 8)})?`)) {
    await filaStore.reenfileirarComErros(grupo.commit_id)
  }
}

const gruposColapsados = ref<Record<string, boolean>>({})

function alternarGrupo(commitId: string) {
  gruposColapsados.value[commitId] = !gruposColapsados.value[commitId]
}

function isGrupoColapsado(commitId: string, grupo?: { jobs: any[] }) {
  // Se houver qualquer tarefa em execução no commit, mantém sempre expandido
  if (grupo && grupo.jobs.some(j => j.status === 'running')) {
    return false
  }
  return !!gruposColapsados.value[commitId]
}

let globalPollInterval: any = null

onMounted(async () => {
  await filaStore.fetchJobs()
  try {
    const cfg = await api.config.obter()
    if (cfg.concurrency) {
      concurrencyInfo.value = cfg.concurrency
    }
  } catch (e) {
    console.error("Erro ao carregar configuracoes de concorrencia:", e)
  }

  globalPollInterval = setInterval(() => {
    filaStore.fetchJobs(true)
  }, 3500)
})

onUnmounted(() => {
  if (globalPollInterval) clearInterval(globalPollInterval)
})

function atualizarFila() {
  filaStore.fetchJobs()
}

function formatarData(isoString: string) {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    return d.toLocaleString('pt-BR')
  } catch {
    return isoString
  }
}

function formatarStatus(status: string) {
  const map: Record<string, string> = {
    pending: 'Aguardando na fila',
    running: 'Executando tarefa',
    paused: 'Pausado',
    done: 'Concluído',
    error: 'Falhou'
  }
  return map[status] ?? status
}

function formatarNomeCampo(chave: string): string {
  const map: Record<string, string> = {
    cargo: 'Perfil',
    nivel: 'Nível',
    responsavel: 'Responsável',
    produto: 'Produto',
    tipo: 'Tipo',
    projeto: 'Projeto',
    status: 'Status',
    status_id: 'Status'
  }
  return map[chave] || chave
}

function formatarValorCampo(chave: string, val: string): string {
  if (chave === 'cargo') {
    const cMap: Record<string, string> = {
      '9': 'Desenvolvedor',
      '11': 'Analista de Sistemas',
      '12': 'Arquiteto de Software',
      '16': 'Analista de Testes'
    }
    return cMap[val] ? `${val} (${cMap[val]})` : val
  }
  if (chave === 'nivel') {
    const nMap: Record<string, string> = {
      '1': 'Júnior',
      '2': 'Pleno',
      '3': 'Sênior',
      '4': 'Único'
    }
    return nMap[val] ? `${val} (${nMap[val]})` : val
  }
  if (chave === 'status' || chave === 'status_id') {
    const sMap: Record<string, string> = {
      '15': 'Backlog',
      '16': 'Backlog Prioritário',
      '17': 'Aberto / Pendente',
      '18': 'Desenvolvimento',
      '20': 'Homologação',
      '21': 'Concluído'
    }
    return sMap[val] ? `${val} (${sMap[val]})` : val
  }
  return val
}

function obterAlteracoesJob(job: any): Record<string, any> | null {
  if (!job.resultado) return null
  let res = job.resultado
  if (typeof res === 'string') {
    try { res = JSON.parse(res) } catch { return null }
  }
  return res.alteracoes || null
}

function obterMensagemErro(job: any) {
  if (!job.resultado) return 'Erro desconhecido.'
  if (job.resultado.error) return job.resultado.error
  if (job.resultado.logs && job.resultado.logs.length) {
    const erroLog = [...job.resultado.logs].reverse().find((l: string) => l.includes('\u274c') || l.includes('ERRO'))
    if (erroLog) return erroLog
  }
  return 'Erro técnico na execução do job.'
}

async function cancelarJob(id: number) {
  if (confirm('Deseja realmente cancelar esta tarefa? Se estiver em execução, será interrompida imediatamente.')) {
    await filaStore.cancelarJob(id)
  }
}

async function removerJob(id: number) {
  await filaStore.removerJob(id)
}

function obterUltimoLog(job: any): string {
  if (job.resultado && job.resultado.logs && job.resultado.logs.length) {
    return job.resultado.logs[job.resultado.logs.length - 1]
  }
  return 'Executando automação no portal Munka...'
}

function handleLogsKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    fecharLogs()
  }
}

watch(logJobSelecionado, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleLogsKeydown)
    nextTick(() => {
      const btn = logsModalRef.value?.querySelector('.modal-actions button') as HTMLElement
      btn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleLogsKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

let logsInterval: any = null

function abrirLogs(job: any) {
  logJobSelecionado.value = job
  if (logsInterval) clearInterval(logsInterval)
  
  logsInterval = setInterval(async () => {
    if (!logJobSelecionado.value) return
    await filaStore.fetchJobs(true)
    const updated = filaStore.jobs.find(j => j.id === logJobSelecionado.value.id)
    if (updated) {
      logJobSelecionado.value = updated
    }
  }, 1200)
}

function fecharLogs() {
  if (logsInterval) {
    clearInterval(logsInterval)
    logsInterval = null
  }
  logJobSelecionado.value = null
}

const verificandoJobId = ref<number | null>(null)
const corrigindoJobId = ref<number | null>(null)

function obterStatusVerificacao(job: any) {
  if (!job.resultado) return null
  let res = job.resultado
  if (typeof res === 'string') {
    try { res = JSON.parse(res) } catch { return null }
  }
  if (res.verificacao) {
    return res.verificacao.overall_ok ? 'ok' : 'divergencia'
  }
  return null
}

function obterTituloVerificacao(job: any) {
  const status = obterStatusVerificacao(job)
  if (status === 'ok') return 'Todos os campos conferidos com sucesso no portal. Clique para re-verificar.'
  if (status === 'divergencia') return 'Inconformidade detectada nos campos do portal Munka. Clique para corrigir.'
  return 'Clique para verificar se os campos da tarefa no portal Munka correspondem ao commit.'
}

async function handleAcaoVerificacao(job: any) {
  const status = obterStatusVerificacao(job)
  if (status === 'divergencia') {
    await executarCorrigir(job)
  } else {
    await executarVerificar(job)
  }
}

async function executarVerificar(job: any) {
  verificandoJobId.value = job.id
  try {
    await api.fila.verificar(job.id)
    await filaStore.fetchJobs()
  } catch (err: any) {
    alert(`Erro ao enfileirar verificação: ${err.response?.data?.detail || err.message || String(err)}`)
  } finally {
    verificandoJobId.value = null
  }
}

async function executarCorrigir(job: any) {
  if (!job) return
  corrigindoJobId.value = job.id
  try {
    await api.fila.corrigir(job.id)
    await filaStore.fetchJobs()
  } catch (err: any) {
    alert(`Erro ao enfileirar correção: ${err.response?.data?.detail || err.message || String(err)}`)
  } finally {
    corrigindoJobId.value = null
  }
}

const models = [
  { name: 'Gemini 3.8 Flash' },
  { name: 'Gemini 3.7 Flash' },
  { name: 'Gemini 3.6 Flash' },
  { name: 'Gemini 3.5 Flash Lite' }
]

const modelosSelecionados = ref<Record<number, string>>({})

function obterModeloSelecionado(jobId: number, modeloAtual?: string) {
  if (modelosSelecionados.value[jobId] === undefined) {
    modelosSelecionados.value[jobId] = modeloAtual || 'Gemini 3.8 Flash'
  }
  return modelosSelecionados.value[jobId]
}

function atualizarModeloSelecionado(jobId: number, event: Event) {
  const target = event.target as HTMLSelectElement
  modelosSelecionados.value[jobId] = target.value
}

function podeMudarModelo(job: any) {
  if (job.tipo !== 'analise') return false
  if (job.status === 'error') {
    const msg = obterMensagemErro(job).toLowerCase()
    return msg.includes('429') || msg.includes('quota') || msg.includes('limit') || msg.includes('exhausted')
  }
  if (job.status === 'running' && job.resultado && job.resultado.status === 'retrying') {
    return true
  }
  return false
}

async function reprocessarComOutroModelo(job: any) {
  const modeloSelecionado = modelosSelecionados.value[job.id] || job.modelo || 'Gemini 3.8 Flash'
  if (confirm(`Deseja cancelar a tarefa atual e iniciar uma nova análise com o modelo ${modeloSelecionado}?`)) {
    try {
      await filaStore.removerJob(job.id)
      await filaStore.enfileirarAnalise([job.commit_id], modeloSelecionado)
    } catch {
      // Erro tratado pelo toast
    }
  }
}

async function reenviarAtividade(job: any) {
  const acao = job.status === 'completed' ? 're-enviar esta atividade ao portal' : 'remover a tentativa com erro e tentar novamente'
  if (confirm(`Deseja realmente ${acao}?`)) {
    try {
      await filaStore.removerJob(job.id)
      await filaStore.enfileirarEnvio(job.commit_id, job.atividade_idx)
    } catch {
      // Erro tratado pelo toast
    }
  }
}
</script>

<style scoped>
.fila-page {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.concurrency-badge {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-glow);
  border: 1px solid var(--accent);
  padding: 4px 10px;
  border-radius: 99px;
  margin-left: 0.5rem;
}

.header-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-shrink: 0;
}

.btn-retry-all {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #ffffff;
  border: none;
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.35);
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-retry-all:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.45);
}

/* Pausar / Retomar */
.btn-pausar,
.btn-retomar {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.btn-pausar { color: #d97706; }
.btn-retomar { color: #059669; }

/* Seção de Tarefas em Execução no Topo */
.fila-execucao-topo {
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  background: var(--card-bg);
  border: 1px solid var(--accent);
  border-radius: 14px;
  padding: 1.25rem;
  box-shadow: 0 0 24px rgba(59, 130, 246, 0.18), 0 4px 16px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.fila-execucao-topo::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-grad);
}

.execucao-topo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.execucao-topo-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.live-pulse-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--accent-glow);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  box-shadow: 0 0 12px var(--accent-glow);
  animation: pulseIcon 2s infinite ease-in-out;
}

.execucao-topo-header h2 {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
  margin: 0;
}

.execucao-topo-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.execucao-topo-pending-pill {
  color: var(--accent-cyan);
  font-weight: 600;
}

.execucao-topo-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 4px 12px;
  border-radius: 99px;
  text-transform: uppercase;
}

.running-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 1rem;
}

@media (max-width: 640px) {
  .running-cards-grid {
    grid-template-columns: 1fr;
  }
}

.running-task-card {
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(59, 130, 246, 0.35);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
  transition: border-color 0.2s, box-shadow 0.2s;
  min-width: 0;
}

.running-task-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 16px rgba(59, 130, 246, 0.2);
}

.running-task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.running-task-badges {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.running-job-id {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
}

.running-job-time {
  font-size: 0.75rem;
  color: var(--text-subtle);
}

.running-task-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-live-logs {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 6px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.2s ease;
}

.btn-live-logs:hover {
  background: var(--accent);
  color: #fff;
}

.running-task-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.running-task-commit-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  min-width: 0;
}

.running-commit-msg {
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.running-task-meta {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.meta-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.meta-value {
  color: var(--text);
  font-weight: 600;
  word-break: break-word;
}

.badge-running-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 99px;
  margin-left: 0.5rem;
  vertical-align: middle;
}

.fila-pending-bar {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--card-bg);
  border: 1px dashed var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.pending-bar-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.pending-bar-info i {
  color: var(--accent-cyan);
}

@keyframes pulseIcon {
  0% { transform: scale(1); box-shadow: 0 0 6px var(--accent-glow); }
  50% { transform: scale(1.08); box-shadow: 0 0 16px var(--accent-glow); }
  100% { transform: scale(1); box-shadow: 0 0 6px var(--accent-glow); }
}

/* Layout Dividido Verticalmente */
.fila-split-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1.75rem;
  align-items: start;
  margin-top: 1rem;
  width: 100%;
  max-width: 100%;
}

.coluna-lancamentos {
  border-right: 1px solid var(--border);
  padding-right: 1.75rem;
}

@media (max-width: 1024px) {
  .fila-split-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .coluna-lancamentos {
    border-right: none;
    padding-right: 0;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
  }
}

/* Colunas */
.fila-coluna {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  width: 100%;
}

.coluna-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.25rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  min-width: 0;
}

.coluna-title-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.coluna-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.icon-lancamentos {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.icon-ajustes {
  background: var(--accent-glow);
  color: var(--accent);
}

.coluna-header h2 {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
}

.coluna-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.coluna-badge {
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  color: var(--text);
  font-weight: 700;
  font-size: 0.85rem;
  padding: 3px 10px;
  border-radius: 99px;
  flex-shrink: 0;
}

.badge-ajuste {
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
}

.empty-coluna {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  background: var(--card-bg);
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--text-muted);
  font-size: 0.88rem;
  text-align: center;
  gap: 0.5rem;
}

.empty-coluna-icon {
  font-size: 2rem;
  opacity: 0.5;
  margin-bottom: 0.25rem;
}

.btn-link-tarefas-mes {
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
  font-size: 0.82rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
  transition: background-color 0.15s ease;
}

.btn-link-tarefas-mes:hover {
  text-decoration: none;
  background: var(--accent-glow);
}

/* Grupos de Commits (Lançamentos) */
.fila-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
  width: 100%;
}

.commit-group {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  width: 100%;
}

button.commit-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 0.75rem 0 !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--border) !important;
  border-radius: 0 !important;
  font-size: 0.88rem;
  cursor: pointer;
  user-select: none;
  font-family: inherit;
  color: inherit;
  width: 100%;
  text-align: left;
  gap: 0.75rem;
  min-width: 0;
  outline: none;
}

.commit-group-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  overflow: hidden;
  min-width: 0;
  flex: 1;
}

.collapse-icon {
  font-size: 0.65rem !important;
  color: var(--text-muted) !important;
  padding: 2px 6px !important;
  display: inline-block;
  flex-shrink: 0;
}

.commit-hash-link {
  font-family: monospace;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.commit-msg-link {
  color: var(--text);
  font-weight: 600;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
  display: block;
}

.commit-group-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.job-count-badge {
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  flex-shrink: 0;
}

.btn-retry-commit {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
  color: #ffffff;
  border: none;
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}

.btn-retry-commit:hover {
  filter: brightness(1.15);
  transform: translateY(-1px);
}

.commit-group-jobs {
  border: none !important;
  background: transparent !important;
  display: flex;
  flex-direction: column;
  padding-top: 0.5rem !important;
  overflow: hidden;
  min-width: 0;
}

.job-row {
  padding: 1rem 1.15rem;
  border-bottom: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 0.35rem;
  transition: background 0.15s;
  min-width: 0;
}

.job-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.job-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.65rem;
  flex-wrap: wrap;
}

.job-time {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.job-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.job-body {
  margin-bottom: 0.65rem;
  min-width: 0;
}

.job-meta {
  font-size: 0.85rem;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-footer {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.status-pending { background: #eab308; }
.status-dot.status-paused { background: #94a3b8; }
.status-dot.status-running { background: #3b82f6; box-shadow: 0 0 8px #3b82f6; animation: pulseDot 1.5s infinite; }
.status-dot.status-done { background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.3); }
.status-dot.status-error { background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.3); }

.status-text {
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.7rem;
}

/* Botões de Verificação */
.btn-verificacao-status {
  transition: all 0.2s ease;
  font-weight: 600;
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.72rem;
  cursor: pointer;
}
.btn-status-default {
  border: 1px solid rgba(96, 165, 250, 0.4) !important;
  color: var(--accent) !important;
  background: rgba(96, 165, 250, 0.08) !important;
}
.btn-status-default:hover {
  background: rgba(96, 165, 250, 0.18) !important;
  transform: translateY(-1px);
}
.btn-status-ok {
  border: 1px solid rgba(16, 185, 129, 0.4) !important;
  color: var(--success) !important;
  background: rgba(16, 185, 129, 0.1) !important;
}
.btn-status-ok:hover {
  background: rgba(16, 185, 129, 0.2) !important;
  transform: translateY(-1px);
}
.btn-status-divergencia {
  border: 1px solid rgba(245, 158, 11, 0.5) !important;
  color: var(--warning) !important;
  background: rgba(245, 158, 11, 0.12) !important;
}
.btn-status-divergencia:hover {
  background: rgba(245, 158, 11, 0.25) !important;
  transform: translateY(-1px);
}

/* Mudar Modelo / Reenviar Box */
.mudar-modelo-box {
  margin-top: 0.75rem;
  padding: 0.85rem;
  background: var(--header-group-bg);
  border: 1px dashed var(--border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.mudar-modelo-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}
.mudar-modelo-control {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}
.select-modelo {
  background: var(--card-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  font-size: 0.75rem !important;
  padding: 0.25rem 0.5rem !important;
  font-weight: 600 !important;
  width: auto !important;
}
.btn-primary-mudar {
  background: var(--accent-grad) !important;
  color: #fff !important;
  border: none !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  padding: 0.35rem 0.75rem !important;
  cursor: pointer !important;
  border-radius: 6px !important;
  text-transform: uppercase;
  transition: all 0.2s ease !important;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15) !important;
}
.btn-primary-mudar:hover {
  filter: brightness(1.1) !important;
  transform: translateY(-1px) !important;
}

/* Coluna de Ajustes (Cards) */
.ajustes-cards-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  width: 100%;
}

.ajuste-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  min-width: 0;
  width: 100%;
}

.ajuste-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.ajuste-card-running {
  border-color: var(--accent) !important;
  border-left: 3px solid var(--accent) !important;
  background: linear-gradient(135deg, var(--card-bg) 0%, var(--accent-glow) 100%);
}

.ajuste-card-done {
  border-left: 3px solid var(--success) !important;
}

.ajuste-card-error {
  border-left: 3px solid var(--error) !important;
}

.ajuste-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.ajuste-card-header-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ajuste-card-body {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 0.75rem;
  min-width: 0;
}

.ajuste-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--text);
  word-break: break-word;
}

.ajuste-chips-container {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.2rem;
}

.chips-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.param-chip {
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.78rem;
  color: var(--text);
  display: inline-flex;
  gap: 0.3rem;
}

.param-chip strong {
  color: var(--accent);
}

.sync-desc-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--badge-orange-bg);
  border: 1px solid var(--badge-orange-border);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.8rem;
  color: var(--badge-orange-color);
}

.running-log-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  font-size: 0.82rem;
  color: var(--accent);
  overflow: hidden;
  min-width: 0;
}

.live-dot-pulse {
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
  box-shadow: 0 0 8px #3b82f6;
  animation: pulseDot 1.2s infinite ease-in-out;
  flex-shrink: 0;
}

.live-log-text {
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.error-box {
  padding: 0.6rem 0.85rem;
  background: rgba(239, 68, 68, 0.08);
  border-left: 3px solid var(--error);
  border-radius: 0 6px 6px 0;
  color: var(--error);
  font-size: 0.78rem;
  font-weight: 500;
  margin-top: 0.4rem;
  word-break: break-word;
}

.done-summary-box {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0.5rem 0.75rem;
  background: var(--badge-green-bg);
  border: 1px solid var(--badge-green-border);
  border-radius: 6px;
  font-size: 0.8rem;
}

.summary-check {
  color: var(--badge-green-color);
  font-weight: 600;
}

.summary-warn {
  color: var(--warning);
  font-size: 0.75rem;
}

/* Modais e Terminais */
.modal-wide {
  width: 100% !important;
  max-width: 800px !important;
  max-height: 85vh !important;
  overflow-y: auto !important;
  box-sizing: border-box !important;
}

.modal-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: -0.5rem;
  margin-bottom: 0.5rem;
}

.terminal-container {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 1rem;
  background: #161b22;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
}

.status-badge {
  text-transform: uppercase;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}
.badge-done { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.badge-error { background: rgba(239, 68, 68, 0.15); color: #f87171; }

.terminal-body {
  padding: 1rem;
  max-height: 380px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: #e6edf3;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-line {
  color: #f85149;
}

.btn-xs {
  padding: 0.25rem 0.6rem !important;
  font-size: 0.72rem !important;
  border-radius: 6px !important;
}

.btn-danger-link {
  background: transparent;
  border: none;
  color: var(--error);
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.btn-danger-link:hover {
  background: rgba(239, 68, 68, 0.08);
}

@keyframes pulseDot {
  0% { transform: scale(0.9); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.6; }
}
</style>
