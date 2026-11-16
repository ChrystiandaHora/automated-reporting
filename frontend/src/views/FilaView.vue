<template>
  <div class="fila-page w-full max-w-full overflow-x-hidden">
    <PageHeader>
      <div data-tour="fila-titulo" class="flex flex-wrap items-center gap-2">
        <PageTitle>Fila de Execução</PageTitle>
        <TutorialModal screenId="fila" />
        <span v-if="concurrencyInfo" data-tour="fila-concorrencia" class="ml-2 rounded-full border border-primary bg-primary-glow px-2.5 py-1 text-xs font-semibold text-primary" :title="`Fila de análises: ${concurrencyInfo.queues.analises} workers | Fila de envios: ${concurrencyInfo.queues.envios} workers | Pool compartilhado de até ${concurrencyInfo.total_system_limit} workers simultâneos`">
          <i class="fa-solid fa-bolt mr-1" aria-hidden="true"></i>Concorrência: {{ concurrencyInfo.queues.analises }} análises / {{ concurrencyInfo.queues.envios }} envios ({{ concurrencyInfo.total_system_limit }} total | {{ concurrencyInfo.cpu_cores }} Cores CPU)
        </span>
      </div>
      <div data-tour="fila-acoes" class="flex shrink-0 items-center gap-2.5">
        <BaseButton
          v-if="pausedJobsCount > 0"
          variant="plain"
          :class="[ghostPlain, btnSm, btnRetomar]"
          @click="retomarTodas"
          :title="`Volta para a fila as ${pausedJobsCount} tarefa(s) pausada(s)`"
        >
          <i class="fa-solid fa-play" aria-hidden="true"></i>
          <span>Retomar Pausadas ({{ pausedJobsCount }})</span>
        </BaseButton>
        <BaseButton
          v-if="pausableJobsCount > 0"
          variant="plain"
          :class="[ghostPlain, btnSm, btnPausar]"
          @click="pausarTodas"
          :title="`Pausa as ${pausableJobsCount} análise(s)/envio(s) que ainda não começaram. O que está em execução termina normalmente.`"
        >
          <i class="fa-solid fa-pause" aria-hidden="true"></i>
          <span>Pausar Pendentes ({{ pausableJobsCount }})</span>
        </BaseButton>
        <button
          v-if="failedJobsCount > 0"
          data-tour="fila-reenfileirar-falhas"
          class="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border-0 bg-linear-135 from-red-500 to-red-600 px-3.5 py-2 text-xs font-semibold text-white shadow-[0_2px_8px] shadow-red-500/35 transition-all duration-200 hover:-translate-y-px hover:shadow-[0_4px_12px] hover:shadow-red-500/45 hover:brightness-110"
          @click="reenfileirarTodasComFalha"
          :title="`Reenfileira todas as ${failedJobsCount} tarefas com falha`"
        >
          <i class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
          <span>Reenfileirar Todas com Falha ({{ failedJobsCount }})</span>
        </button>
        <BaseButton
          size="sm"
          @click="limparMesesAnteriores"
          title="Remover tarefas da fila concluídas ou com erro de meses passados"
        >
          <i class="fa-solid fa-broom" aria-hidden="true"></i>
          <span>Limpar Meses Anteriores</span>
        </BaseButton>
        <BaseButton size="sm" @click="atualizarFila">
          <i class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
          <span>Atualizar</span>
        </BaseButton>
      </div>
    </PageHeader>

    <!-- Feedback de carregamento inicial -->
    <StateMessage v-if="filaStore.loading && filaStore.jobs.length === 0" type="loading">Carregando fila...</StateMessage>

    <template v-else>
      <!-- SEÇÃO DE TAREFAS EM EXECUÇÃO AGORA (FIXADA NO TOPO) -->
      <section v-if="jobsEmExecucao.length > 0" class="relative mt-5 mb-2 overflow-hidden rounded-[14px] border border-primary bg-card p-5 shadow-[0_0_24px] shadow-blue-500/20 before:absolute before:inset-x-0 before:top-0 before:h-0.75 before:bg-(image:--accent-grad)" aria-label="Tarefas em execução agora">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <span class="flex size-9 animate-queue-icon items-center justify-center rounded-[10px] bg-primary-glow text-lg text-primary shadow-[0_0_12px] shadow-primary-glow">
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
            </span>
            <div>
              <h2 class="text-lg leading-tight font-extrabold text-foreground">Em Execução Agora</h2>
              <span class="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                {{ jobsEmExecucao.length === 1 ? '1 tarefa sendo processada em tempo real' : `${jobsEmExecucao.length} tarefas sendo processadas simultaneamente` }}
                <span v-if="pendingJobsCount > 0" class="font-semibold text-accent">
                  • {{ pendingJobsCount }} aguardando na fila
                </span>
              </span>
            </div>
          </div>
          <div class="inline-flex items-center gap-2 rounded-full border border-primary bg-blue-500/15 px-3 py-1 text-xs font-extrabold tracking-wider text-primary uppercase">
            <span :class="liveDot"></span>
            <span>AO VIVO</span>
          </div>
        </div>

        <div class="grid grid-cols-[repeat(auto-fill,minmax(420px,1fr))] gap-4 max-sm:grid-cols-1">
          <div
            v-for="job in jobsEmExecucao"
            :key="job.id"
            class="flex min-w-0 flex-col gap-3 rounded-[10px] border border-l-4 border-blue-500/35 border-l-primary bg-muted p-4 shadow-card transition-[border-color,box-shadow] duration-200 hover:border-primary hover:shadow-[0_0_16px] hover:shadow-blue-500/20"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex flex-wrap items-center gap-2">
                <BaseBadge :variant="varianteBadgeTipo(job.tipo)">
                  <i
                    class="mr-1"
                    :class="{
                      'fa-solid fa-wand-magic-sparkles': job.tipo === 'analise',
                      'fa-solid fa-cloud-arrow-up': job.tipo === 'envio',
                      'fa-solid fa-sliders': job.tipo === 'ajuste',
                      'fa-solid fa-arrows-rotate': job.tipo === 'verificacao'
                    }"
                    aria-hidden="true"
                  ></i>
                  {{ formatarTipoJob(job.tipo) }}
                </BaseBadge>
                <span class="text-xs font-bold text-muted-foreground">Job #{{ job.id }}</span>
                <span class="text-xs text-subtle-foreground">{{ formatarData(job.criado_em) }}</span>
              </div>

              <div class="flex items-center gap-1.5">
                <router-link
                  v-if="job.commit_id && job.commit_id !== 'sem-commit'"
                  :to="`/commits/${job.commit_id}`"
                  :class="linkGhostXs"
                  title="Ver página deste commit"
                >
                  <i class="fa-solid fa-code-commit mr-1" aria-hidden="true"></i>Ver Commit
                </router-link>

                <button
                  :class="['inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-primary bg-blue-500/15 font-bold text-primary transition-all duration-200 hover:bg-primary hover:text-white', btnXs]"
                  @click="abrirLogs(job)"
                  title="Acompanhar logs ao vivo da execução"
                >
                  <i class="fa-solid fa-terminal mr-1" aria-hidden="true"></i>
                  <span>Logs (Ao Vivo)</span>
                </button>

                <button
                  :class="btnDangerXs"
                  @click="cancelarJob(job.id)"
                  title="Interromper esta tarefa imediatamente"
                >
                  <i class="fa-solid fa-ban mr-1" aria-hidden="true"></i>
                  <span>Cancelar</span>
                </button>
              </div>
            </div>

            <div class="flex min-w-0 flex-col gap-2">
              <div v-if="job.commit_id && job.commit_id !== 'sem-commit'" class="flex min-w-0 items-center gap-2 text-sm">
                <router-link :to="`/commits/${job.commit_id}`" :class="hashLink">
                  {{ job.commit_id.slice(0, 8) }}
                </router-link>
                <span class="truncate font-semibold text-foreground" :title="job.commit_mensagem">
                  {{ job.commit_mensagem }}
                </span>
              </div>

              <div class="flex flex-wrap items-baseline gap-1.5 text-sm">
                <template v-if="job.tipo === 'analise'">
                  <span :class="metaLabel">Modelo AI:</span>
                  <strong :class="metaValue">{{ job.modelo || 'Gemini 3.8 Flash' }}</strong>
                </template>
                <template v-else-if="job.tipo === 'envio'">
                  <span :class="metaLabel">Atividade:</span>
                  <strong :class="metaValue">"{{ job.titulo_atividade || 'Lançamento de atividade no portal Munka...' }}"</strong>
                </template>
                <template v-else-if="job.tipo === 'ajuste'">
                  <span :class="metaLabel">Ajuste Munka:</span>
                  <strong :class="metaValue">{{ job.titulo_atividade || 'Ajuste de campos de tarefa no portal' }}</strong>
                </template>
                <template v-else-if="job.tipo === 'verificacao'">
                  <span :class="metaLabel">Sincronização:</span>
                  <strong :class="metaValue">Varredura e auditoria dos status no portal Munka</strong>
                </template>
              </div>

              <div :class="runningLogBox">
                <span :class="liveDot"></span>
                <span :class="liveLogText">{{ obterUltimoLog(job) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Aviso sutil quando não há tarefas rodando, mas há pendentes na fila -->
      <div v-if="jobsEmExecucao.length === 0 && pendingJobsCount > 0" class="mt-4 mb-2 flex items-center justify-between rounded-[10px] border border-dashed border-border-strong bg-card px-5 py-3 text-sm text-muted-foreground">
        <div class="flex items-center gap-2.5 [&_i]:text-accent">
          <i class="fa-solid fa-clock-rotate-left" aria-hidden="true"></i>
          <span><strong>{{ pendingJobsCount }} tarefa(s) aguardando na fila.</strong> Os workers iniciarão o processamento conforme a disponibilidade de concorrência.</span>
        </div>
      </div>

      <!-- Layout Dividido Verticalmente: Lançamentos (Esquerda) e Ajustes (Direita) -->
      <div class="mt-4 grid w-full max-w-full grid-cols-2 items-start gap-7 max-lg:grid-cols-1">

      <!-- COLUNA ESQUERDA: Lançamentos ao Munka & Análises -->
      <section data-tour="fila-lancamentos" class="flex w-full min-w-0 flex-col gap-4 border-r border-r-border-strong pr-7 max-lg:border-r-0 max-lg:border-b max-lg:border-b-border-strong max-lg:pr-0 max-lg:pb-6">
        <div :class="colunaHeader">
          <div class="flex min-w-0 items-center gap-3">
            <div :class="[colunaIcon, 'bg-blue-500/15 text-blue-500']">
              <i class="fa-solid fa-cloud-arrow-up" aria-hidden="true"></i>
            </div>
            <div>
              <h2 :class="colunaTitulo">Lançamentos</h2>
              <span class="text-xs text-muted-foreground">Análises AI e Envios ao Portal Munka</span>
            </div>
          </div>
          <span :class="[colunaBadge, 'border-border-strong bg-muted text-foreground']">{{ jobsLancamentos.length }}</span>
        </div>

        <div v-if="jobsLancamentos.length === 0" :class="emptyColuna">
          <i class="fa-regular fa-folder-open mb-1 text-[2rem] opacity-50" aria-hidden="true"></i>
          <span>Nenhum lançamento de atividade na fila.</span>
        </div>

        <div v-else class="flex w-full min-w-0 flex-col gap-5">
          <!-- Percorre os commits agrupados -->
          <div v-for="grupo in jobsLancamentosAgrupados" :key="grupo.commit_id" class="flex w-full min-w-0 flex-col overflow-hidden rounded-xl border border-border bg-card p-6 text-foreground shadow-card transition-all duration-250">
            <!-- Cabeçalho do Commit -->
            <button
              class="flex w-full min-w-0 cursor-pointer items-center justify-between gap-3 rounded-none border-0 border-b border-b-border-strong bg-transparent px-0 pt-0 pb-3 text-left text-sm text-inherit outline-none select-none"
              type="button"
              :aria-expanded="!isGrupoColapsado(grupo.commit_id, grupo)"
              :aria-controls="'group-jobs-' + grupo.commit_id"
              @click="alternarGrupo(grupo.commit_id)"
            >
              <div class="flex min-w-0 flex-1 items-center gap-2.5 overflow-hidden">
                <span class="inline-block shrink-0 rounded-md border border-border bg-background px-1.5 py-0.5 text-[0.65rem] text-muted-foreground transition-all duration-200" aria-hidden="true">{{ isGrupoColapsado(grupo.commit_id, grupo) ? '▶' : '▼' }}</span>
                <router-link v-if="grupo.commit_id && grupo.commit_id !== 'sem-commit'" :to="`/commits/${grupo.commit_id}`" :class="hashLink" @click.stop>
                  {{ grupo.commit_id.slice(0, 8) }}
                </router-link>
                <span class="block min-w-0 flex-1 truncate text-sm font-semibold text-foreground" :title="grupo.commit_mensagem">
                  {{ grupo.commit_mensagem }}
                </span>
                <span v-if="temExecucaoNoGrupo(grupo)" class="ml-2 inline-flex items-center gap-1.5 rounded-full border border-primary bg-blue-500/15 px-2 py-0.5 align-middle text-xs font-bold text-primary" title="Existe tarefa sendo executada neste commit">
                  <span :class="liveDot"></span>
                  <span>Em Execução</span>
                </span>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <BaseButton
                  v-if="pausaveisNoGrupo(grupo) > 0"
                  variant="plain"
                  :class="[ghostPlain, btnXs, btnPausar]"
                  @click.stop="filaStore.pausarJobs({ job_ids: idsPausaveis(grupo.jobs) })"
                  :title="`Pausar ${pausaveisNoGrupo(grupo)} tarefa(s) pendente(s) deste commit`"
                >
                  <i class="fa-solid fa-pause" aria-hidden="true"></i>
                  <span>Pausar ({{ pausaveisNoGrupo(grupo) }})</span>
                </BaseButton>
                <BaseButton
                  v-if="pausadosNoGrupo(grupo) > 0"
                  variant="plain"
                  :class="[ghostPlain, btnXs, btnRetomar]"
                  @click.stop="filaStore.retomarJobs({ job_ids: idsPausados(grupo.jobs) })"
                  :title="`Retomar ${pausadosNoGrupo(grupo)} tarefa(s) pausada(s) deste commit`"
                >
                  <i class="fa-solid fa-play" aria-hidden="true"></i>
                  <span>Retomar ({{ pausadosNoGrupo(grupo) }})</span>
                </BaseButton>
                <button
                  v-if="temErrosNoGrupo(grupo)"
                  class="inline-flex shrink-0 cursor-pointer items-center gap-1 rounded-md border-0 bg-linear-135 from-red-500 to-red-700 px-2.5 py-1 text-xs font-semibold text-white shadow-[0_2px_6px] shadow-red-500/30 transition-all duration-200 hover:-translate-y-px hover:brightness-115"
                  @click.stop="reenfileirarGrupo(grupo)"
                  :title="`Reenfileirar ${errosNoGrupoCount(grupo)} tarefa(s) com falha deste commit`"
                >
                  <i class="fa-solid fa-arrows-rotate mr-1" aria-hidden="true"></i>
                  <span>Falhas ({{ errosNoGrupoCount(grupo) }})</span>
                </button>
                <span class="shrink-0 rounded-full border border-border-strong bg-muted px-2 py-0.5 text-xs font-bold text-muted-foreground">{{ grupo.jobs.length }}</span>
              </div>
            </button>

            <!-- Lista de tarefas deste commit -->
            <div v-show="!isGrupoColapsado(grupo.commit_id, grupo)" :id="'group-jobs-' + grupo.commit_id" class="flex min-w-0 flex-col overflow-hidden pt-2">
              <div
                v-for="job in grupo.jobs"
                :key="job.id"
                class="mb-1.5 min-w-0 rounded-md border-b border-b-border-strong px-4.5 py-4 transition-colors duration-150 last:mb-0 last:border-b-0"
                :class="classesJobRow[job.status]"
              >
                <div class="mb-2.5 flex flex-wrap items-center gap-2.5">
                  <BaseBadge :variant="job.tipo === 'analise' ? 'blue' : 'purple'">
                    {{ job.tipo === 'analise' ? 'Análise AI' : 'Envio Portal' }}
                  </BaseBadge>

                  <span :class="jobTime">{{ formatarData(job.criado_em) }}</span>

                  <div class="ml-auto flex flex-wrap items-center gap-2">
                    <!-- Botão de Verificação / Correção -->
                    <button
                      v-if="job.status === 'done' && job.tipo === 'envio'"
                      :class="['cursor-pointer rounded-md border px-2.5 py-1 text-xs font-semibold transition-all duration-200 hover:-translate-y-px disabled:cursor-not-allowed', classesVerificacao(job)]"
                      @click="handleAcaoVerificacao(job)"
                      :disabled="isVerificando(job.id)"
                      :title="obterTituloVerificacao(job)"
                    >
                      <template v-if="isVerificando(job.id)">
                        <i class="fa-solid fa-circle-notch fa-spin mr-1" aria-hidden="true"></i>Verificando...
                      </template>
                      <template v-else-if="obterStatusVerificacao(job) === 'ok'">
                        <i class="fa-solid fa-circle-check mr-1" aria-hidden="true"></i>Lançamento OK
                      </template>
                      <template v-else-if="obterStatusVerificacao(job) === 'divergencia'">
                        <i class="fa-solid fa-triangle-exclamation mr-1" aria-hidden="true"></i>Corrigir
                      </template>
                      <template v-else>
                        <i class="fa-solid fa-magnifying-glass mr-1" aria-hidden="true"></i>Verificar
                      </template>
                    </button>

                    <!-- Botão de Ver Commit (análise concluída abre o commit analisado) -->
                    <router-link
                      v-if="job.status === 'done' && job.tipo === 'analise' && job.commit_id"
                      :to="`/commits/${job.commit_id}`"
                      :class="linkGhostXs"
                    >
                      <i class="fa-solid fa-code-commit mr-1" aria-hidden="true"></i>Ver Commit
                    </router-link>

                    <!-- Botão de Ver Tarefa (envio concluído abre a tarefa no portal) -->
                    <a
                      v-else-if="job.status === 'done' && job.resultado && job.resultado.task_url"
                      :href="job.resultado.task_url"
                      target="_blank"
                      :class="linkGhostXs"
                    >
                      Ver Tarefa
                    </a>

                    <!-- Botão de Ver Logs -->
                    <BaseButton
                      v-if="job.status === 'running' || (job.resultado && job.resultado.logs && job.resultado.logs.length)"
                      size="xs"
                      @click="abrirLogs(job)"
                    >
                      <i class="mr-1" :class="job.status === 'running' ? 'fa-solid fa-terminal' : 'fa-solid fa-file-waveform'" aria-hidden="true"></i>
                      <span>{{ job.status === 'running' ? 'Logs (Ao Vivo)' : 'Ver Logs' }}</span>
                    </BaseButton>

                    <!-- Botão Pausar (só antes de começar: envio em execução está no meio do portal) -->
                    <BaseButton
                      v-if="podePausar(job)"
                      variant="plain"
                      :class="[ghostPlain, btnXs, btnPausar]"
                      @click="filaStore.pausarJobs({ job_ids: [job.id] })"
                      title="Pausa esta tarefa antes de ela começar"
                    >
                      <i class="fa-solid fa-pause" aria-hidden="true"></i><span>Pausar</span>
                    </BaseButton>

                    <!-- Botão Retomar -->
                    <BaseButton
                      v-if="job.status === 'paused'"
                      variant="plain"
                      :class="[ghostPlain, btnXs, btnRetomar]"
                      @click="filaStore.retomarJobs({ job_ids: [job.id] })"
                      title="Devolve esta tarefa para a fila"
                    >
                      <i class="fa-solid fa-play" aria-hidden="true"></i><span>Retomar</span>
                    </BaseButton>

                    <!-- Botão Cancelar -->
                    <button
                      v-if="job.status === 'pending' || job.status === 'running' || job.status === 'paused'"
                      :class="btnDanger"
                      @click="cancelarJob(job.id)"
                      :title="job.status === 'running' ? 'Interrompe a execução' : 'Remove da fila'"
                    >
                      <i class="fa-solid fa-ban mr-1" aria-hidden="true"></i>
                      <span>Cancelar</span>
                    </button>

                    <!-- Botão Limpar -->
                    <button
                      v-if="['done', 'error'].includes(job.status)"
                      :class="btnDanger"
                      @click="removerJob(job.id)"
                    >
                      Limpar
                    </button>
                  </div>
                </div>

                <div class="mb-2.5 min-w-0">
                  <div v-if="job.tipo === 'analise'" :class="jobMeta">
                    <strong>Modelo:</strong> {{ job.modelo }}
                  </div>

                  <div v-else-if="job.tipo === 'envio'" :class="jobMeta">
                    <strong>Atividade:</strong> "{{ job.titulo_atividade || 'Carregando título...' }}"
                  </div>

                  <!-- Mensagem de Erro -->
                  <div v-if="job.status === 'error'" :class="errorBox">
                    <span>{{ obterMensagemErro(job) }}</span>
                  </div>

                  <!-- Faixa de Logs em Tempo Real durante Execução -->
                  <div v-if="job.status === 'running'" :class="runningLogBox">
                    <span :class="liveDot"></span>
                    <span :class="liveLogText">{{ obterUltimoLog(job) }}</span>
                  </div>

                  <!-- Seleção de outro modelo em caso de limite atingido -->
                  <div v-if="podeMudarModelo(job)" :class="mudarModeloBox">
                    <label :for="'select-model-' + job.id" :class="mudarModeloLabelTag">Limite atingido. Tentar outro modelo:</label>
                    <div :class="mudarModeloControl">
                      <select
                        :id="'select-model-' + job.id"
                        :value="obterModeloSelecionado(job.id, job.modelo)"
                        @change="atualizarModeloSelecionado(job.id, $event)"
                        class="w-auto rounded-md border border-border-strong bg-card px-2 py-1 text-xs font-semibold text-foreground shadow-field transition-all duration-200 focus:border-primary focus:ring-3 focus:ring-primary-glow focus:outline-none"
                      >
                        <option v-for="m in models" :key="m.name" :value="m.name">
                          {{ m.name }}
                        </option>
                      </select>
                      <button :class="btnPrimaryMudar" @click="reprocessarComOutroModelo(job)">
                        Reprocessar
                      </button>
                    </div>
                  </div>

                  <!-- Reenviar em caso de término ou falha de envio -->
                  <div v-if="job.tipo === 'envio' && (job.status === 'error' || job.status === 'completed')" :class="mudarModeloBox">
                    <span :class="mudarModeloLabel">
                      {{ job.status === 'completed' ? 'Atividade concluída. Deseja re-enviar ao portal?' : 'Esta atividade falhou no envio. Deseja tentar novamente?' }}
                    </span>
                    <div :class="mudarModeloControl">
                      <button :class="btnPrimaryMudar" @click="reenviarAtividade(job)">
                        {{ job.status === 'completed' ? 'Re-enviar Envio' : 'Tentar Novamente' }}
                      </button>
                    </div>
                  </div>
                </div>

                <div :class="jobFooter">
                  <div class="flex items-center gap-2 font-semibold">
                    <span :class="['size-2 rounded-full', classesDotStatus[job.status]]"></span>
                    <span class="text-xs tracking-wider uppercase">{{ formatarStatus(job.status) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- COLUNA DIREITA: Ajustes dos Cards & Sincronizações -->
      <section data-tour="fila-ajustes" class="flex w-full min-w-0 flex-col gap-4">
        <div :class="colunaHeader">
          <div class="flex min-w-0 items-center gap-3">
            <div :class="[colunaIcon, 'bg-primary-glow text-primary']">
              <i class="fa-solid fa-sliders" aria-hidden="true"></i>
            </div>
            <div>
              <h2 :class="colunaTitulo">Ajustes & Sincronizações</h2>
              <span class="text-xs text-muted-foreground">Ajustes de campos e auditoria de status no Munka</span>
            </div>
          </div>
          <span :class="[colunaBadge, 'border-primary bg-primary-glow text-primary']">{{ jobsAjustes.length }}</span>
        </div>

        <div v-if="jobsAjustes.length === 0" :class="emptyColuna">
          <i class="fa-solid fa-sliders mb-1 text-[2rem] opacity-50" aria-hidden="true"></i>
          <span>Nenhum ajuste ou sincronização na fila.</span>
          <router-link to="/tarefas-mes" class="mt-2 inline-block rounded-sm px-2 py-1 text-sm font-bold text-primary no-underline transition-colors duration-150 hover:bg-primary-glow hover:no-underline">
            Ir para Tarefas do Mês para ajustar cards →
          </router-link>
        </div>

        <div v-else class="flex w-full min-w-0 flex-col gap-4">
          <div
            v-for="job in jobsAjustes"
            :key="job.id"
            :class="['w-full min-w-0 rounded-xl border bg-card p-5 shadow-card transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-px hover:border-y-primary hover:border-r-primary', classesCardAjuste[job.status] ?? classesCardAjusteBase]"
          >
            <!-- Card Header -->
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2.5">
                <BaseBadge :variant="job.tipo === 'ajuste' ? 'purple' : 'orange'">
                  <i :class="job.tipo === 'ajuste' ? 'fa-solid fa-sliders' : 'fa-solid fa-arrows-rotate'" aria-hidden="true"></i>
                  <span>{{ job.tipo === 'ajuste' ? 'Ajuste Munka' : 'Sincronização' }}</span>
                </BaseBadge>
                <span :class="jobTime">{{ formatarData(job.criado_em) }}</span>
              </div>

              <div class="ml-auto flex flex-wrap items-center gap-2">
                <!-- Botão Ver Logs -->
                <BaseButton
                  v-if="job.status === 'running' || (job.resultado && job.resultado.logs && job.resultado.logs.length)"
                  size="xs"
                  @click="abrirLogs(job)"
                >
                  <i class="mr-1" :class="job.status === 'running' ? 'fa-solid fa-terminal' : 'fa-solid fa-file-waveform'" aria-hidden="true"></i>
                  <span>{{ job.status === 'running' ? 'Logs (Ao Vivo)' : 'Ver Logs' }}</span>
                </BaseButton>

                <!-- Botão Cancelar -->
                <button
                  v-if="job.status === 'pending' || job.status === 'running'"
                  :class="btnDanger"
                  @click="cancelarJob(job.id)"
                >
                  <i class="fa-solid fa-ban mr-1" aria-hidden="true"></i>
                  <span>Cancelar</span>
                </button>

                <!-- Botão Limpar -->
                <button
                  v-if="['done', 'error'].includes(job.status)"
                  :class="btnDanger"
                  @click="removerJob(job.id)"
                >
                  Limpar
                </button>
              </div>
            </div>

            <!-- Card Body -->
            <div class="mb-3 flex min-w-0 flex-col gap-2.5">
              <div>
                <span class="text-base font-bold wrap-anywhere text-foreground">
                  {{ job.titulo_atividade || (job.tipo === 'ajuste' ? 'Ajuste de Tarefa no Munka' : 'Sincronização de Status') }}
                </span>
              </div>

              <!-- Chips com os campos alterados -->
              <div v-if="obterAlteracoesJob(job)" class="mt-1 flex flex-col gap-1.5">
                <span class="text-xs font-bold tracking-wide text-muted-foreground uppercase">Campos alterados:</span>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="(val, chave) in obterAlteracoesJob(job)" :key="chave" class="inline-flex gap-1 rounded-md border border-border-strong bg-muted px-2 py-0.5 text-xs text-foreground [&_strong]:text-primary">
                    <strong>{{ formatarNomeCampo(String(chave)) }}:</strong>
                    <span>{{ formatarValorCampo(String(chave), String(val)) }}</span>
                  </span>
                </div>
              </div>

              <!-- Se for sincronização -->
              <div v-else-if="job.tipo === 'verificacao'" class="flex items-center gap-2 rounded-md border border-badge-orange-border bg-badge-orange px-3 py-2 text-xs text-badge-orange-foreground">
                <i class="fa-solid fa-circle-nodes" aria-hidden="true"></i>
                <span>Varredura da listagem de tarefas do mês e atualização dos status no portal.</span>
              </div>

              <!-- Faixa de Logs ao Vivo durante Execução -->
              <div v-if="job.status === 'running'" :class="runningLogBox">
                <span :class="liveDot"></span>
                <span :class="liveLogText">{{ obterUltimoLog(job) }}</span>
              </div>

              <!-- Mensagem de Erro -->
              <div v-if="job.status === 'error'" :class="errorBox">
                <span>{{ obterMensagemErro(job) }}</span>
              </div>

              <!-- Resumo de Conclusão -->
              <div v-if="job.status === 'done' && job.resultado" class="flex flex-col gap-0.5 rounded-md border border-badge-green-border bg-badge-green px-3 py-2 text-xs">
                <template v-if="job.tipo === 'ajuste'">
                  <span class="font-semibold text-badge-green-foreground">
                    <i class="fa-solid fa-circle-check mr-1" aria-hidden="true"></i>
                    <span>Sucesso: {{ job.resultado.sucessos || 1 }} tarefa(s) ajustada(s) no portal.</span>
                  </span>
                  <span v-if="job.resultado.puladas" class="text-xs text-warning">
                    <i class="fa-solid fa-triangle-exclamation mr-1" aria-hidden="true"></i>
                    <span>{{ job.resultado.puladas }} tarefa(s) já estavam concluídas pelo supervisor e foram preservadas.</span>
                  </span>
                </template>
                <template v-else>
                  <span class="font-semibold text-badge-green-foreground">
                    <i class="fa-solid fa-circle-check mr-1" aria-hidden="true"></i>
                    <span>Sincronização concluída: {{ job.resultado.total_portal || 0 }} tarefas lidas no portal, {{ job.resultado.total_atualizadas || 0 }} atualizadas no banco.</span>
                  </span>
                </template>
              </div>
            </div>

            <!-- Card Footer -->
            <div :class="jobFooter">
              <div class="flex items-center gap-2 font-semibold">
                <span :class="['size-2 rounded-full', classesDotStatus[job.status]]"></span>
                <span class="text-xs tracking-wider uppercase">{{ formatarStatus(job.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
    </template>

    <!-- Modal de Logs -->
    <BaseModal v-if="logJobSelecionado" ref="logsModalRef" size="auto" labelledby="logs-modal-title" class="max-h-[85vh] w-200 max-w-[95vw] overflow-y-auto" @close="fecharLogs">
        <h2 id="logs-modal-title" class="mb-1 text-xl font-bold text-foreground">Logs de Automação (Job #{{ logJobSelecionado.id }})</h2>
        <p class="-mt-2 mb-2 text-xs text-muted-foreground">Tarefa: "{{ logJobSelecionado.titulo_atividade }}"</p>

        <div class="mt-2 overflow-hidden rounded-[10px] border border-border-strong bg-canvas">
          <div class="flex items-center justify-between border-b border-white/8 bg-canvas-subtle px-4 py-2.5 text-xs font-semibold text-slate-400">
            <span>Logs de Execução Playwright</span>
            <span class="rounded-sm px-1.5 py-0.5 text-[0.65rem] font-bold uppercase" :class="classesBadgeLog[logJobSelecionado.status]">
              <span v-if="logJobSelecionado.status === 'running'">
                <i class="fa-solid fa-bolt mr-1" aria-hidden="true"></i>TRANSMITINDO AO VIVO
              </span>
              <span v-else>{{ logJobSelecionado.status }}</span>
            </span>
          </div>
          <pre class="max-h-95 overflow-y-auto p-4 font-terminal text-xs leading-normal break-all whitespace-pre-wrap text-terminal-foreground"><div v-for="(log, idx) in (logJobSelecionado.resultado?.logs || [])" :key="idx" :class="{'text-canvas-danger': log.includes('\u274c') || log.includes('ERRO')}">{{ log }}</div></pre>
        </div>

      <template #actions>
        <BaseButton @click="fecharLogs">Fechar</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useFilaStore } from '../stores/fila'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import StateMessage from '../components/ui/StateMessage.vue'
import { api, type Config } from '../api'

// ── Classes utilitárias reaproveitadas no template ──
const btnXs = 'rounded-[5px] px-2.25 py-1 text-xs'
const btnSm = 'rounded-md px-3.25 py-1.5 text-[0.82rem]'
// Visual "ghost" para botões plain que trocam a cor do texto (pausar/retomar)
const ghostPlain = 'border border-border-strong bg-card hover:enabled:-translate-y-px hover:enabled:border-primary disabled:opacity-40'
const btnPausar = 'text-amber-600 hover:enabled:text-primary'
const btnRetomar = 'text-emerald-600 hover:enabled:text-primary'
// Link com o visual do BaseButton ghost xs (BaseButton só renderiza <button>)
const linkGhostXs = `inline-flex cursor-pointer items-center justify-center gap-2 border border-border-strong bg-card font-semibold leading-none text-foreground no-underline transition-all duration-200 hover:-translate-y-px hover:border-primary hover:text-primary ${btnXs}`
const btnDangerBase = 'cursor-pointer border-0 bg-transparent text-xs font-semibold tracking-wide text-danger uppercase transition-all duration-200 hover:bg-red-500/8'
const btnDanger = `${btnDangerBase} px-2 py-1 rounded-md`
const btnDangerXs = `${btnDangerBase} ${btnXs}`
const btnPrimaryMudar = 'cursor-pointer rounded-md border-0 bg-(image:--accent-grad) px-3 py-1.5 text-xs font-bold text-white uppercase shadow-[0_2px_6px] shadow-blue-500/15 transition-all duration-200 hover:-translate-y-px hover:brightness-110'
const hashLink = 'shrink-0 rounded-md border border-border bg-background px-2 py-[3px] font-mono text-[0.8rem] font-bold text-muted-foreground no-underline transition-all duration-200 hover:border-primary hover:bg-primary-glow hover:text-primary'
const liveDot = 'size-2 shrink-0 animate-queue-dot rounded-full bg-blue-500 shadow-[0_0_8px] shadow-blue-500'
const runningLogBox = 'flex min-w-0 items-center gap-2 overflow-hidden rounded-md border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-sm text-primary'
const liveLogText = 'min-w-0 truncate font-mono'
const errorBox = 'mt-1.5 rounded-r-md border-l-3 border-l-danger bg-red-500/8 px-3.5 py-2.5 text-xs font-medium wrap-anywhere text-danger'
const jobTime = 'text-xs text-muted-foreground'
const jobMeta = 'overflow-hidden text-sm text-ellipsis text-foreground'
const jobFooter = 'flex items-center border-t border-slate-400/12 pt-2 text-xs'
const metaLabel = 'text-xs font-bold tracking-wide text-muted-foreground uppercase'
const metaValue = 'font-semibold wrap-anywhere text-foreground'
const mudarModeloBox = 'mt-3 flex flex-col gap-2 rounded-[10px] border border-dashed border-border-strong bg-muted p-3.5'
const mudarModeloLabel = 'text-xs font-semibold text-muted-foreground'
const mudarModeloLabelTag = `${mudarModeloLabel} mb-[0.35rem] block leading-[1.4] tracking-[0.05em] uppercase`
const mudarModeloControl = 'flex flex-wrap items-center gap-2'
const colunaHeader = 'flex min-w-0 items-center justify-between rounded-xl border border-border-strong bg-card px-5 py-3.5 shadow-card'
const colunaIcon = 'flex size-9.5 shrink-0 items-center justify-center rounded-lg text-lg'
const colunaTitulo = 'text-base leading-tight font-extrabold text-foreground'
const colunaBadge = 'shrink-0 rounded-full border px-2.5 py-1 text-sm font-bold'
const emptyColuna = 'flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border-strong bg-card px-6 py-12 text-center text-sm text-muted-foreground'

const classesDotStatus: Record<string, string> = {
  pending: 'bg-yellow-500',
  paused: 'bg-slate-400',
  running: 'bg-blue-500 shadow-[0_0_8px] shadow-blue-500 animate-queue-dot-slow',
  done: 'bg-emerald-500 shadow-[0_0_6px] shadow-emerald-500/30',
  error: 'bg-red-500 shadow-[0_0_6px] shadow-red-500/30',
}

const classesJobRow: Record<string, string> = {
  running: 'border-l-3 border-l-primary bg-primary-glow',
  done: 'border-l-3 border-l-success bg-emerald-500/5',
  error: 'border-l-3 border-l-danger bg-red-500/5',
}

function varianteBadgeTipo(tipo: string): 'blue' | 'purple' | 'orange' | 'plain' {
  if (tipo === 'analise') return 'blue'
  if (tipo === 'envio' || tipo === 'ajuste') return 'purple'
  if (tipo === 'verificacao') return 'orange'
  return 'plain'
}

const classesCardAjusteBase = 'border-border-strong bg-card hover:border-l-primary'
const classesCardAjuste: Record<string, string> = {
  running: 'border-primary border-l-3 border-l-primary bg-linear-135 from-card to-primary-glow',
  done: 'border-border-strong border-l-3 border-l-success bg-card',
  error: 'border-border-strong border-l-3 border-l-danger bg-card',
}

const classesBadgeLog: Record<string, string> = {
  running: 'border border-badge-code-border bg-badge-code text-badge-code-foreground',
  done: 'bg-emerald-500/15 text-emerald-400',
  error: 'bg-red-500/15 text-red-400',
}

const classesVerificacaoPadrao = 'border-blue-400/40 bg-blue-400/8 text-primary hover:bg-blue-400/18'
const classesVerificacaoOk = 'border-emerald-500/40 bg-emerald-500/10 text-success hover:bg-emerald-500/20'
const classesVerificacaoDivergencia = 'border-amber-500/50 bg-amber-500/12 text-warning hover:bg-amber-500/25'
function classesVerificacao(job: any): string {
  if (!isVerificando(job.id)) {
    const status = obterStatusVerificacao(job)
    if (status === 'ok') return classesVerificacaoOk
    if (status === 'divergencia') return classesVerificacaoDivergencia
  }
  return classesVerificacaoPadrao
}

const filaStore = useFilaStore()
const toastStore = useToastStore()
const logJobSelecionado = ref<any>(null)
const concurrencyInfo = ref<Config['concurrency'] | null>(null)

const logsModalRef = ref<InstanceType<typeof BaseModal> | null>(null)
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
      const btn = logsModalRef.value?.panel?.querySelector('[data-modal-actions] button') as HTMLElement
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
