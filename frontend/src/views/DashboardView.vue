<template>
  <div class="flex flex-col gap-8" data-tour="dashboard-pagina">
    <!-- Cabeçalho do Dashboard -->
    <header data-tour="dashboard-cabecalho" class="mb-8 flex flex-wrap items-start justify-between gap-6 border-b border-border pb-6 light:border-slate-200">
      <div class="flex min-w-65 flex-col gap-2">
        <div class="flex items-center gap-3">
          <h1 class="text-[1.75rem] font-extrabold tracking-tight text-foreground">Dashboard de Indicadores</h1>
          <TutorialModal screenId="dashboard" />
        </div>
        <p class="text-sm leading-normal text-muted-foreground">
          Métricas consolidadas de commits, análise preditiva com IA e faturamento HPA integrado ao Munka.
        </p>
      </div>

      <!-- Controles de Período e Ações Rápidas -->
      <div class="flex flex-wrap items-center gap-3 max-md:w-full max-md:justify-between">
        <div v-if="store.stats" class="flex items-center gap-2.5 rounded-lg border border-border-strong bg-card px-3 py-1.5 light:border-slate-300">
          <label for="mes-filtro-dashboard" class="mb-1.4 block text-sm leading-[1.4] font-bold uppercase tracking-wider text-muted-foreground">Período:</label>
          <div class="relative flex items-center">
            <select 
              id="mes-filtro-dashboard" 
              v-model="mesSelecionado" 
              class="w-full cursor-pointer appearance-none rounded-lg border-0 bg-transparent py-2.4 pr-6 pl-3.4 text-sm font-semibold text-foreground shadow-field outline-none focus:ring-3 focus:ring-primary-glow" 
              aria-label="Filtrar indicadores por período ou mês"
            >
              <option value="todos">Consolidado (Todos os Meses)</option>
              <option v-for="m in store.stats.months" :key="m" :value="m">
                {{ formatarMesExtenso(m) }}
              </option>
            </select>
            <i class="fa-solid fa-chevron-down pointer-events-none absolute right-0 text-xs text-muted-foreground" aria-hidden="true"></i>
          </div>
        </div>

        <button 
          type="button" 
          class="inline-flex size-9 cursor-pointer disabled:cursor-not-allowed items-center justify-center rounded-lg border border-border-strong bg-card text-muted-foreground transition duration-150 hover:border-primary hover:text-foreground light:border-slate-300 light:text-slate-600 light:hover:border-blue-600 light:hover:text-foreground" 
          :disabled="atualizando"
          @click="recarregarDados"
          title="Recarregar dados do dashboard"
          aria-label="Recarregar dados do dashboard"
        >
          <i class="fa-solid fa-rotate" :class="{ 'fa-spin': atualizando }" aria-hidden="true"></i>
        </button>

        <BaseButton variant="primary" data-tour="dashboard-importar" @click="$router.push('/importar')">
          <i class="fa-solid fa-file-import" aria-hidden="true"></i>
          <span>+ Importar Commit</span>
        </BaseButton>
      </div>
    </header>

    <!-- Barra de Conectividade e Saúde dos Serviços -->
    <div class="mb-1 flex flex-wrap items-center justify-between gap-5 rounded-[10px] border border-border bg-muted px-5.5 py-3.5 text-sm light:border-slate-200 light:bg-slate-50" role="region" aria-label="Status das integrações do sistema">
      <div class="flex flex-wrap items-center gap-4">
        <template v-for="(item, idx) in integracoes" :key="item.chave">
          <span v-if="idx > 0" class="text-border-strong" aria-hidden="true">·</span>
          <span :class="['inline-flex items-center gap-2 font-medium', item.ativo ? 'text-foreground' : 'text-muted-foreground']">
            <span :class="['inline-block size-1.75 rounded-full', item.ativo ? 'bg-success shadow-[0_0_6px] shadow-emerald-500/50' : 'bg-slate-500']"></span>
            <i :class="item.icone" aria-hidden="true"></i>
            <span>{{ item.texto }}</span>
          </span>
        </template>
      </div>

      <div >
        <router-link to="/fila" class="no-underline outline-none" title="Ver fila de execução em tempo real">
          <span v-if="totalTarefasAtivasNaFila > 0" class="inline-flex items-center gap-2 rounded-md border border-amber-500/35 bg-amber-500/15 px-3 py-1 text-xs font-bold text-amber-400">
            <span class="size-1.5 animate-spin rounded-full border-2 border-transparent border-t-current border-r-current [animation-duration:0.8s]"></span>
            <span>{{ totalTarefasAtivasNaFila }} tarefa{{ totalTarefasAtivasNaFila > 1 ? 's' : '' }} na fila</span>
          </span>
          <span v-else class="inline-flex items-center gap-2 rounded-md border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
            <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
            <span>Fila operacional</span>
          </span>
        </router-link>
      </div>
    </div>

    <!-- Estado de Carregamento -->
    <StateMessage v-if="store.loading && store.commits.length === 0" type="loading" role="status" aria-live="polite">
      Carregando indicadores do dashboard...
    </StateMessage>

    <!-- Estado Vazio -->
    <div v-else-if="store.commits.length === 0" class="flex flex-col items-center justify-center gap-4 rounded-[14px] border border-dashed border-border-strong bg-card px-6 py-14 text-center light:border-slate-300">
      <div class="flex size-14 items-center justify-center rounded-2xl bg-blue-500/12 text-2xl text-primary">
        <i class="fa-solid fa-chart-line" aria-hidden="true"></i>
      </div>
      <h2 class="text-xl font-bold text-foreground">Nenhum dado cadastrado ainda</h2>
      <p class="max-w-120 text-sm leading-normal text-muted-foreground">Importe commits do GitLab para que a IA analise as alterações de código e gere os relatórios de faturamento HPA automaticamente.</p>
      <BaseButton variant="primary" @click="$router.push('/importar')">
        <i class="fa-solid fa-file-import" aria-hidden="true"></i>
        <span>Importar Primeiro Commit</span>
      </BaseButton>
    </div>

    <!-- Conteúdo Principal do Dashboard -->
    <main v-else class="flex flex-col gap-9">
      
      <!-- 1. FAIXA EXECUTIVA DE KPIS (ESTILO SAAS CONSOLIDADO) -->
      <section data-tour="dashboard-kpis" class="grid grid-cols-5 overflow-hidden rounded-xl border border-border bg-card shadow-[0_1px_3px] shadow-black/5 light:border-slate-200 light:shadow-[0_1px_4px] light:shadow-black/4 max-[1100px]:grid-cols-3 max-md:grid-cols-1" aria-label="Indicadores executivos">
        <!-- KPI 1: Horas HPA -->
        <div :class="kpiCell">
          <div :class="kpiHeader">
            <span :class="kpiLabel">HPA Faturável</span>
            <span :class="[kpiBadgeBase, taxaHpaEnviado === 100 ? kpiBadgeTons.green : kpiBadgeTons.blue]">
              {{ taxaHpaEnviado }}% enviado
            </span>
          </div>
          <div :class="kpiValueRow">
            <span :class="kpiNum">{{ statsExibidas.total_hpa }}</span>
            <span :class="kpiUnit">h</span>
          </div>
          <div :class="kpiProgress" role="progressbar" :aria-valuenow="taxaHpaEnviado" aria-valuemin="0" aria-valuemax="100" :aria-label="`Percentual de HPA enviado: ${taxaHpaEnviado}%`">
            <div :class="[kpiBar, 'bg-primary']" :style="{ width: `${taxaHpaEnviado}%` }"></div>
          </div>
          <span :class="kpiSub">
            <strong>{{ hpaEnviadoPeriodo }}h</strong> enviados · {{ hpaPendentePeriodo }}h pendentes
          </span>
        </div>

        <!-- KPI 2: Atividades -->
        <div :class="kpiCell">
          <div :class="kpiHeader">
            <span :class="kpiLabel">Tarefas Identificadas</span>
            <span :class="[kpiBadgeBase, kpiBadgeTons.neutral]">
              {{ Object.keys(statsExibidas.codes).length }} tipos
            </span>
          </div>
          <div :class="kpiValueRow">
            <span :class="kpiNum">{{ statsExibidas.total_tasks }}</span>
            <span :class="kpiUnit">atividades</span>
          </div>
          <div :class="kpiProgress" role="progressbar" :aria-valuenow="taxaTarefasEnviadas" aria-valuemin="0" aria-valuemax="100" :aria-label="`Percentual de tarefas enviadas: ${taxaTarefasEnviadas}%`">
            <div :class="[kpiBar, 'bg-accent']" :style="{ width: `${taxaTarefasEnviadas}%` }"></div>
          </div>
          <span :class="kpiSub">
            <strong>{{ tarefasEnviadasPeriodo }}</strong> enviadas ao Munka ({{ taxaTarefasEnviadas }}%)
          </span>
        </div>

        <!-- KPI 3: Commits & Cobertura IA -->
        <div :class="kpiCell">
          <div :class="kpiHeader">
            <span :class="kpiLabel">Commits no Período</span>
            <span :class="[kpiBadgeBase, taxaAnaliseIA >= 90 ? kpiBadgeTons.green : kpiBadgeTons.amber]">
              {{ taxaAnaliseIA }}% IA
            </span>
          </div>
          <div :class="kpiValueRow">
            <span :class="kpiNum">{{ totalCommitsPeriodo }}</span>
            <span :class="kpiUnit">commits</span>
          </div>
          <div :class="kpiProgress" role="progressbar" :aria-valuenow="taxaAnaliseIA" aria-valuemin="0" aria-valuemax="100" :aria-label="`Cobertura de análise IA: ${taxaAnaliseIA}%`">
            <div :class="[kpiBar, 'bg-success']" :style="{ width: `${taxaAnaliseIA}%` }"></div>
          </div>
          <span :class="kpiSub">
            <strong>{{ commitsAnalisadosPeriodo }}</strong> analisados · {{ commitsPendentesPeriodo }} pendentes
          </span>
        </div>

        <!-- KPI 4: Média HPA por Tarefa -->
        <div :class="kpiCell">
          <div :class="kpiHeader">
            <span :class="kpiLabel">Esforço Médio</span>
            <span :class="[kpiBadgeBase, kpiBadgeTons.neutral]">
              HPA / Tarefa
            </span>
          </div>
          <div :class="kpiValueRow">
            <span :class="kpiNum">{{ mediaHpaPorTarefa }}</span>
            <span :class="kpiUnit">h/tarefa</span>
          </div>
          <div :class="kpiProgress">
            <div :class="[kpiBar, 'bg-warning']" :style="{ width: `${Math.min(100, Math.round((Number(mediaHpaPorTarefa) / 3.0) * 100))}%` }"></div>
          </div>
          <span :class="kpiSub">
            {{ distribuicaoRepositorios.length }} repositórios avaliados
          </span>
        </div>

        <!-- KPI 5: Fila de Execução -->
        <div :class="kpiCell">
          <div :class="kpiHeader">
            <span :class="kpiLabel">Status da Fila</span>
            <span :class="[kpiBadgeBase, totalTarefasAtivasNaFila > 0 ? kpiBadgeTons.amber : kpiBadgeTons.green]">
              {{ totalTarefasAtivasNaFila > 0 ? 'Processando' : 'Sincronizado' }}
            </span>
          </div>
          <div :class="kpiValueRow">
            <span :class="kpiNum">{{ totalTarefasAtivasNaFila }}</span>
            <span :class="kpiUnit">em fila</span>
          </div>
          <div :class="kpiProgress">
            <div :class="[kpiBar, 'bg-primary']" :style="{ width: totalTarefasAtivasNaFila > 0 ? '70%' : '100%' }"></div>
          </div>
          <span :class="kpiSub">
            <router-link to="/fila" class="inline-flex items-center gap-1.5 text-primary-light no-underline transition-[gap] duration-150 hover:gap-2 hover:text-foreground light:text-blue-700">
              <span>{{ totalTarefasAtivasNaFila > 0 ? `${tarefasRunning} rodando, ${tarefasPending} na espera` : 'Nenhum job pendente' }}</span>
              <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
            </router-link>
          </span>
        </div>
      </section>

      <!-- 2. ALERTA OPERACIONAL DE AÇÕES PENDENTES (SE HOUVER PENDÊNCIAS) -->
      <section v-if="commitsPendentesPeriodo > 0 || tarefasPendentesPeriodo > 0" data-tour="dashboard-alerta" class="flex flex-wrap items-center justify-between gap-6 rounded-xl border border-amber-500/35 bg-amber-500/8 px-7 py-5 light:border-amber-200 light:bg-amber-50" role="region" aria-label="Ações pendentes recomendadas">
        <div class="flex size-10.5 shrink-0 items-center justify-center rounded-[10px] bg-amber-500/20 text-lg text-amber-400">
          <i class="fa-solid fa-bolt" aria-hidden="true"></i>
        </div>
        <div class="min-w-65 flex-1">
          <h3 class="text-base font-bold text-foreground light:text-amber-900">Ações recomendadas para este período</h3>
          <p class="mt-1.5 text-sm leading-normal text-muted-foreground light:text-amber-800 [&_strong]:text-yellow-200 light:[&_strong]:text-amber-900">
            <span v-if="commitsPendentesPeriodo > 0">
              Existem <strong>{{ commitsPendentesPeriodo }} commit{{ commitsPendentesPeriodo > 1 ? 's' : '' }}</strong> aguardando análise de IA.
            </span>
            <span v-if="commitsPendentesPeriodo > 0 && tarefasPendentesPeriodo > 0"> · </span>
            <span v-if="tarefasPendentesPeriodo > 0">
              Existem <strong>{{ tarefasPendentesPeriodo }} tarefa{{ tarefasPendentesPeriodo > 1 ? 's' : '' }}</strong> ({{ hpaPendentePeriodo }}h HPA) prontas aguardando envio ao Munka.
            </span>
          </p>
        </div>
        <div >
          <button 
            type="button" 
            class="inline-flex cursor-pointer items-center gap-2 rounded-lg border-0 bg-amber-600 px-5 py-2.5 text-sm font-bold text-white transition-colors duration-150 hover:bg-amber-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white" 
            @click="$router.push('/commits')"
          >
            <span>Gerenciar na Tela de Commits</span>
            <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
          </button>
        </div>
      </section>

      <!-- 3. FUNIL DE AUTOMAÇÃO DO FLUXO DE VALOR (PIPELINE SAAS) -->
      <section :class="painel" data-tour="dashboard-pipeline" aria-label="Pipeline do fluxo de valor">
        <div :class="painelCabecalho">
          <div :class="painelTitulo">
            <i class="fa-solid fa-timeline" aria-hidden="true"></i>
            <h2 :class="painelTituloH2">Pipeline de Automação</h2>
          </div>
          <span :class="painelInfo">Ciclo Completo: Ingestão Git → IA Gemini → Timesheet Munka</span>
        </div>

        <div data-tour="dashboard-pipeline-etapas" class="grid grid-cols-4 gap-5 max-[1100px]:grid-cols-2 max-md:grid-cols-1">
          <div
            v-for="(etapa, idx) in etapasPipeline"
            :key="etapa.numero"
            class="relative flex items-center gap-4 rounded-[10px] border border-border bg-muted px-5.5 py-5 light:border-slate-200 light:bg-slate-50"
          >
            <div :class="['flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-extrabold', etapa.concluida ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-400' : 'border-blue-500/40 bg-blue-500/15 text-blue-400']">{{ etapa.numero }}</div>
            <div class="flex flex-1 flex-col gap-1">
              <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">{{ etapa.rotulo }}</span>
              <span class="my-0.5 text-lg font-extrabold tracking-tight text-foreground">{{ etapa.valor }}</span>
              <span class="text-xs leading-snug text-muted-foreground">{{ etapa.descricao }}</span>
            </div>
            <i v-if="idx < etapasPipeline.length - 1" class="fa-solid fa-chevron-right text-sm text-border max-md:[--fa-display:none]" aria-hidden="true"></i>
          </div>
        </div>
      </section>

      <!-- 4. GRID CENTRAL: REPOSITÓRIOS E HISTÓRICO MENSAL -->
      <div data-tour="dashboard-grade-central" class="grid grid-cols-2 gap-8 max-[1100px]:grid-cols-1">
        
        <!-- Coluna Esquerda: Distribuição por Repositório -->
        <section :class="painel" data-tour="dashboard-repositorios" aria-label="Distribuição por Repositório">
          <div :class="painelCabecalho">
            <div :class="painelTitulo">
              <i class="fa-brands fa-git-alt" aria-hidden="true"></i>
              <h2 :class="painelTituloH2">Repositórios & Faturamento</h2>
            </div>
            <router-link to="/commits" :class="linkPainel" title="Abrir lista completa de commits">
              <span>Ver Commits</span>
              <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
            </router-link>
          </div>

          <div v-if="distribuicaoRepositorios.length === 0" :class="painelVazio">
            Nenhum repositório com dados no período selecionado.
          </div>

          <div v-else class="flex max-h-100 flex-col gap-3.5 overflow-y-auto pr-1">
            <div 
              v-for="repo in distribuicaoRepositorios" 
              :key="repo.nome" 
              class="group flex cursor-pointer items-center justify-between gap-5 rounded-[10px] border border-border bg-muted px-5.5 py-4.5 transition duration-150 hover:translate-x-0.5 hover:border-primary hover:bg-blue-500/8 light:border-slate-200 light:bg-slate-50 light:hover:border-blue-600 light:hover:bg-blue-50"
              tabindex="0"
              role="button"
              @click="navegarParaRepo(repo.nome)"
              @keydown.enter.prevent="navegarParaRepo(repo.nome)"
              @keydown.space.prevent="navegarParaRepo(repo.nome)"
              :title="`Filtrar commits de ${repo.nome}`"
            >
              <div class="flex min-w-0 flex-1 items-center gap-3.5">
                <span class="size-2.5 shrink-0 rounded-full" :class="repo.colorClass"></span>
                <div class="flex min-w-0 flex-col gap-1.5">
                  <span class="truncate text-base font-bold tracking-tight text-foreground" :title="repo.nome">{{ repo.nome }}</span>
                  <div class="flex flex-wrap items-center gap-2">
                    <span :class="[pilulaBase, pilulaNeutra]">{{ repo.commitsCount }} commit{{ repo.commitsCount > 1 ? 's' : '' }}</span>
                    <span :class="[pilulaBase, pilulaNeutra]">{{ repo.totalTarefas }} tarefa{{ repo.totalTarefas > 1 ? 's' : '' }}</span>
                    <span v-if="repo.pendentes > 0" :class="[pilulaBase, pilulaAmbar]" title="Commits pendentes de análise">
                      {{ repo.pendentes }} pendente{{ repo.pendentes > 1 ? 's' : '' }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="flex shrink-0 items-center gap-4">
                <div class="flex flex-col items-end gap-0.5">
                  <div class="text-base font-extrabold text-foreground">
                    <strong>{{ repo.totalHpa.toFixed(1) }}</strong>
                    <span class="ml-px text-xs text-muted-foreground">h</span>
                  </div>
                  <span class="text-xs text-muted-foreground">
                    {{ repo.hpaEnviado.toFixed(1) }}h env. ({{ repo.pctHpaEnviado }}%)
                  </span>
                </div>

                <div class="w-16" :title="`${repo.pctHpaEnviado}% do HPA enviado ao Munka`">
                  <div class="h-1.5 w-full overflow-hidden rounded-xs bg-white/8 light:bg-slate-200">
                    <div class="h-full rounded-xs bg-success" :style="{ width: `${repo.pctHpaEnviado}%` }"></div>
                  </div>
                </div>

                <i class="fa-solid fa-chevron-right text-xs text-muted-foreground transition-transform duration-150 group-hover:translate-x-0.5 group-hover:text-primary-light" aria-hidden="true"></i>
              </div>
            </div>
          </div>
        </section>

        <!-- Coluna Direita: Gráfico de Evolução Mensal (SVG Dinâmico) -->
        <section :class="painel" data-tour="dashboard-evolucao" aria-label="Evolução Mensal de HPA">
          <div :class="painelCabecalho">
            <div :class="painelTitulo">
              <i class="fa-solid fa-chart-simple" aria-hidden="true"></i>
              <h2 :class="painelTituloH2">Evolução Mensal de HPA</h2>
            </div>
            <span :class="painelInfo">Clique em uma barra para filtrar o mês</span>
          </div>

          <div v-if="historicoMensal.length === 0" :class="painelVazio">
            Nenhum histórico mensal disponível.
          </div>

          <div v-else class="flex flex-1 flex-col gap-5">
            <!-- Gráfico de Barras SVG Responsivo e Dinâmico -->
            <svg 
              class="h-auto min-h-50 w-full overflow-visible" 
              viewBox="0 0 520 180" 
              role="img" 
              aria-label="Gráfico de barras de HPA por mês"
            >
              <!-- Linhas horizontais de referência (Grid) -->
              <line x1="45" y1="20" x2="510" y2="20" :class="svgGrade" />
              <text x="40" y="24" :class="svgEixo" text-anchor="end">{{ maxHpaMensal }}h</text>

              <line x1="45" y1="80" x2="510" y2="80" :class="svgGrade" />
              <text x="40" y="84" :class="svgEixo" text-anchor="end">{{ Math.round(maxHpaMensal / 2) }}h</text>

              <line x1="45" y1="140" x2="510" y2="140" class="stroke-border stroke-[1.5]" />
              <text x="40" y="144" :class="svgEixo" text-anchor="end">0h</text>

              <!-- Barras Mensais -->
              <g 
                v-for="(item, idx) in historicoMensal" 
                :key="item.mes" 
                class="group cursor-pointer outline-none"
                tabindex="0"
                role="button"
                :aria-label="`${item.labelLongo}: ${item.hpa} horas HPA, ${item.tarefas} tarefas`"
                @click="selecionarMes(item.mes)"
                @keydown.enter.prevent="selecionarMes(item.mes)"
                @keydown.space.prevent="selecionarMes(item.mes)"
              >
                <!-- Retângulo da Barra -->
                <rect 
                  :x="calcularXBarra(idx, historicoMensal.length)"
                  :y="calcularYBarra(item.hpa)"
                  :width="calcularLarguraBarra(historicoMensal.length)"
                  :height="calcularAlturaBarra(item.hpa)"
                  rx="4"
                  ry="4"
                  :class="['transition-[fill] duration-150', mesSelecionado === item.mes ? 'fill-primary' : 'fill-blue-500/55 group-hover:fill-primary-light light:fill-blue-300 light:group-hover:fill-blue-500']"
                />

                <!-- Rótulo de Valor no Topo da Barra -->
                <text 
                  :x="calcularXBarra(idx, historicoMensal.length) + (calcularLarguraBarra(historicoMensal.length) / 2)"
                  :y="Math.max(14, calcularYBarra(item.hpa) - 5)"
                  class="fill-foreground text-[10px] font-bold"
                  text-anchor="middle"
                >
                  {{ item.hpa }}h
                </text>

                <!-- Rótulo do Mês na Base -->
                <text 
                  :x="calcularXBarra(idx, historicoMensal.length) + (calcularLarguraBarra(historicoMensal.length) / 2)"
                  y="160"
                  :class="['text-[10px]', mesSelecionado === item.mes ? 'fill-primary-light font-extrabold' : 'fill-muted-foreground font-semibold light:fill-slate-600']"
                  text-anchor="middle"
                >
                  {{ item.labelCurto }}
                </text>
              </g>
            </svg>

            <!-- Legenda e Destaque do Mês Ativo -->
            <div class="mt-2 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4.5 text-sm light:border-slate-200">
              <div class="inline-flex items-center gap-2 text-muted-foreground">
                <span class="size-2 rounded-full bg-primary"></span>
                <span>Visualizando: <strong>{{ mesSelecionado === 'todos' ? 'Todos os meses acumulados' : formatarMesExtenso(mesSelecionado) }}</strong></span>
              </div>
              <button 
                v-if="mesSelecionado !== 'todos'" 
                type="button" 
                class="cursor-pointer rounded-md border border-border-strong bg-transparent px-3.5 py-1.5 text-xs font-semibold text-foreground transition duration-150 hover:border-primary hover:bg-white/8 light:border-slate-300 light:text-slate-700 light:hover:border-blue-600 light:hover:bg-slate-100 light:hover:text-blue-700" 
                @click="mesSelecionado = 'todos'"
                title="Voltar para visão consolidada"
              >
                Ver Consolidado
              </button>
            </div>
          </div>
        </section>

      </div>

      <!-- 5. TABELA DE QUANTIFICAÇÃO POR TIPO DE SERVIÇO (CÓDIGOS FATURÁVEIS) -->
      <section :class="[painel, 'gap-6']" aria-label="Quantificação por Tipo de Serviço">
        <div :class="painelCabecalho">
          <div class="flex flex-col gap-1.5">
            <div :class="painelTitulo">
              <i class="fa-solid fa-tags" aria-hidden="true"></i>
              <h2 :class="painelTituloH2">Quantificação por Tipo de Serviço</h2>
            </div>
            <p class="text-sm leading-normal text-muted-foreground">Códigos de serviço faturáveis gerados e justificados pela IA com base nas mudanças de código.</p>
          </div>

          <!-- Controles de Busca e Ordenação da Tabela -->
          <div class="mb-1 flex flex-wrap items-center gap-4">
            <div class="relative flex min-w-50 items-center">
              <i class="fa-solid fa-magnifying-glass absolute left-3.5 text-xs text-muted-foreground" aria-hidden="true"></i>
              <input 
                type="search" 
                v-model="termoBuscaCodigo" 
                placeholder="Buscar código..." 
                aria-label="Filtrar por código de serviço"
                class="w-full rounded-lg border border-border-strong bg-card py-2 pr-3.5 pl-9 text-sm text-foreground shadow-field outline-none focus:border-primary focus:ring-3 focus:ring-primary-glow light:border-slate-300 light:focus:border-blue-600"
              />
            </div>

            <div class="inline-flex gap-0.75 rounded-lg border border-border bg-muted p-0.75" role="group" aria-label="Ordenar códigos por">
              <button 
                v-for="op in opcoesOrdenacao"
                :key="op.valor"
                type="button" 
                :class="['cursor-pointer rounded-md px-3 py-1.5 text-xs font-semibold transition duration-150', ordenacaoCodigos === op.valor ? 'border border-border bg-card text-foreground' : 'border-0 bg-transparent text-muted-foreground hover:text-foreground light:text-slate-600']"
                @click="ordenacaoCodigos = op.valor"
              >
                {{ op.rotulo }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="codigosProcessados.length === 0" :class="painelVazio">
          Nenhum código de serviço encontrado para os critérios selecionados.
        </div>

        <!-- Tabela SaaS de Alta Densidade e Alinhamento Preciso -->
        <div v-else class="overflow-x-auto">
          <table class="w-full border-collapse text-left text-sm">
            <thead>
              <tr>
                <th v-for="col in colunasTabela" :key="col.rotulo" scope="col" :class="['border-b border-border bg-background px-5.5 py-4.5 text-xs font-bold uppercase tracking-wider text-muted-foreground light:border-slate-200 light:text-slate-600', col.direita ? 'text-right' : 'text-left']">{{ col.rotulo }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in codigosProcessados" :key="item.codigo" class="transition-colors duration-150 hover:bg-white/2 light:hover:bg-slate-50 [&:last-child>td]:border-b-0">
                <td :class="celula">
                  <div>
                    <BaseBadge variant="plain"><code>{{ item.codigo }}</code></BaseBadge>
                  </div>
                </td>
                <td :class="[celula, 'text-right']">
                  <strong>{{ item.count }}</strong>
                  <span :class="subUnidade">tarefa{{ item.count > 1 ? 's' : '' }}</span>
                </td>
                <td :class="[celula, 'text-right']">
                  <span class="text-base font-extrabold text-primary-light light:text-blue-700">{{ item.hpa.toFixed(1) }}</span>
                  <span :class="subUnidade">h</span>
                </td>
                <td :class="[celula, 'text-right']">
                  <span>{{ item.media }}h</span>
                </td>
                <td :class="celula">
                  <div class="flex max-w-50 items-center gap-4">
                    <div class="h-1.75 flex-1 overflow-hidden rounded-sm bg-white/8 light:bg-slate-200">
                      <div class="h-full rounded-sm bg-primary" :style="{ width: `${item.pctHpa}%` }"></div>
                    </div>
                    <span class="min-w-8 text-xs font-bold text-muted-foreground">{{ item.pctHpa }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import { api } from '../api'
import TutorialModal from '../components/TutorialModal.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import StateMessage from '../components/ui/StateMessage.vue'
import type { CommitSummary } from '../api'

// Classes Tailwind reutilizadas no template (strings completas para o Tailwind detectar)
const kpiCell = 'flex flex-col gap-2.5 border-r border-border px-6.5 py-6 transition-colors duration-150 last:border-r-0 hover:bg-white/2 light:border-slate-200 light:hover:bg-slate-50 max-[1100px]:nth-3:border-r-0 max-md:border-r-0 max-md:border-b max-md:last:border-b-0'
const kpiHeader = 'flex items-center justify-between gap-2'
const kpiLabel = 'text-sm font-semibold tracking-tight text-muted-foreground'
const kpiValueRow = 'mt-1.5 mb-0.5 flex items-baseline gap-1.5'
const kpiNum = 'text-[2.1rem] leading-[1.1] font-extrabold tracking-tight text-foreground tabular-nums'
const kpiUnit = 'text-sm font-semibold text-muted-foreground'
const kpiProgress = 'mt-2 mb-1.5 h-1.25 w-full overflow-hidden rounded-xs bg-white/8 light:bg-slate-200'
const kpiBar = 'h-full rounded-xs transition-[width] duration-300'
const kpiSub = 'mt-1 text-sm leading-normal text-muted-foreground light:text-slate-600 [&_strong]:text-foreground'
const kpiBadgeBase = 'rounded-sm border px-2 py-1 text-xs font-bold'
const kpiBadgeTons = {
  blue: 'border-blue-500/30 bg-blue-500/15 text-blue-400',
  green: 'border-emerald-500/30 bg-emerald-500/15 text-emerald-400',
  amber: 'border-amber-500/30 bg-amber-500/15 text-amber-400',
  neutral: 'border-slate-400/25 bg-slate-400/12 text-slate-300'
}

const painel = 'flex flex-col rounded-xl border border-border bg-card px-8 py-7 light:border-slate-200 light:shadow-[0_1px_4px] light:shadow-black/4'
const painelCabecalho = 'mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5 light:border-slate-200'
const painelTitulo = 'flex items-center gap-2.5 text-primary-light'
const painelTituloH2 = 'text-xl font-bold tracking-tight text-foreground'
const painelInfo = 'text-xs font-medium text-muted-foreground'
const painelVazio = 'py-10 text-center text-sm text-muted-foreground italic'
const linkPainel = 'inline-flex items-center gap-1.5 text-sm font-semibold text-primary-light no-underline transition-[gap] duration-150 hover:gap-2 hover:text-foreground'

const pilulaBase = 'rounded-sm px-1.75 py-0.5 text-xs font-semibold'
const pilulaNeutra = 'bg-white/6 text-muted-foreground light:bg-slate-200 light:text-slate-700'
const pilulaAmbar = 'bg-amber-500/15 text-amber-400 light:bg-amber-100 light:text-amber-800'

const svgGrade = 'stroke-white/6 [stroke-dasharray:4_4] light:stroke-slate-200'
const svgEixo = 'fill-muted-foreground text-[10px]'

const celula = 'border-b border-border px-5.5 py-4.5 align-middle text-foreground light:border-slate-200'
const subUnidade = 'ml-1 text-xs font-normal text-muted-foreground'

const opcoesOrdenacao = [
  { valor: 'hpa', rotulo: 'Mais HPA' },
  { valor: 'count', rotulo: 'Mais Tarefas' },
  { valor: 'codigo', rotulo: 'Código' }
] as const

const colunasTabela = [
  { rotulo: 'Código do Serviço', direita: false },
  { rotulo: 'Tarefas', direita: true },
  { rotulo: 'HPA Total', direita: true },
  { rotulo: 'Média / Tarefa', direita: true },
  { rotulo: 'Participação', direita: false }
]

const router = useRouter()
const store = useCommitsStore()
const filaStore = useFilaStore()

const mesSelecionado = ref<string>('todos')
const atualizando = ref(false)
const termoBuscaCodigo = ref('')
const ordenacaoCodigos = ref<'hpa' | 'count' | 'codigo'>('hpa')

const servicosStatus = ref<{ gemini: boolean; munka: boolean; gitlab: boolean }>({
  gemini: true,
  munka: true,
  gitlab: true
})

onMounted(async () => {
  await carregarTudo()
  filaStore.startPolling()
})

async function carregarTudo() {
  atualizando.value = true
  try {
    await Promise.all([
      store.fetchCommits(),
      store.fetchStats(),
      filaStore.fetchJobs(true),
      verificarStatusServicos()
    ])
  } catch (err) {
    console.error('Erro ao carregar dados do dashboard:', err)
  } finally {
    atualizando.value = false
  }
}

async function recarregarDados() {
  await carregarTudo()
}

async function verificarStatusServicos() {
  try {
    const cfg = await api.config.obter()
    if (cfg && cfg.status) {
      servicosStatus.value = cfg.status
    }
  } catch {
    // fallback
  }
}

// Helper: Extrai mês/ano (MM/AAAA) do commit
function obterMesAnoCommit(c: CommitSummary): string {
  if (c.data_autor) {
    try {
      const d = new Date(c.data_autor)
      if (!isNaN(d.getTime())) {
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        return `${mes}/${d.getFullYear()}`
      }
    } catch {
      // fallback
    }
  }
  if (c.data && c.data.includes('/')) {
    const parts = c.data.split('/')
    if (parts.length === 3) {
      return `${parts[1]}/${parts[2]}`
    }
  }
  return 'Outros'
}

// Commits filtrados pelo período selecionado
const commitsDoPeriodo = computed(() => {
  if (mesSelecionado.value === 'todos') {
    return store.commits
  }
  return store.commits.filter(c => obterMesAnoCommit(c) === mesSelecionado.value)
})

// Estatísticas brutas do período
const statsExibidas = computed(() => {
  if (!store.stats) {
    return { codes: {}, total_tasks: 0, total_hpa: 0 }
  }
  if (mesSelecionado.value === 'todos') {
    return store.stats.totals
  }
  return store.stats.by_month[mesSelecionado.value] || { codes: {}, total_tasks: 0, total_hpa: 0 }
})

// Métricas de Commits
const totalCommitsPeriodo = computed(() => commitsDoPeriodo.value.length)

const commitsAnalisadosPeriodo = computed(() => {
  return commitsDoPeriodo.value.filter(c => c.analisado).length
})

const commitsPendentesPeriodo = computed(() => {
  return commitsDoPeriodo.value.filter(c => !c.analisado).length
})

const taxaAnaliseIA = computed(() => {
  if (totalCommitsPeriodo.value === 0) return 0
  return Math.round((commitsAnalisadosPeriodo.value / totalCommitsPeriodo.value) * 100)
})

// Métricas de HPA
const hpaEnviadoPeriodo = computed(() => {
  const total = commitsDoPeriodo.value.reduce((acc, c) => acc + (c.hpa_enviado || 0), 0)
  return Number(total.toFixed(1))
})

const hpaPendentePeriodo = computed(() => {
  const diff = statsExibidas.value.total_hpa - hpaEnviadoPeriodo.value
  return Math.max(0, Number(diff.toFixed(1)))
})

const taxaHpaEnviado = computed(() => {
  const total = statsExibidas.value.total_hpa
  if (total <= 0) return 0
  return Math.min(100, Math.round((hpaEnviadoPeriodo.value / total) * 100))
})

// Métricas de Tarefas
const tarefasEnviadasPeriodo = computed(() => {
  return commitsDoPeriodo.value.reduce((acc, c) => acc + (c.atividades_enviadas || 0), 0)
})

const tarefasPendentesPeriodo = computed(() => {
  const total = statsExibidas.value.total_tasks
  return Math.max(0, total - tarefasEnviadasPeriodo.value)
})

const taxaTarefasEnviadas = computed(() => {
  const total = statsExibidas.value.total_tasks
  if (total <= 0) return 0
  return Math.min(100, Math.round((tarefasEnviadasPeriodo.value / total) * 100))
})

const mediaHpaPorTarefa = computed(() => {
  const total = statsExibidas.value.total_tasks
  const hpa = statsExibidas.value.total_hpa
  if (!total || total === 0) return '0.0'
  return (hpa / total).toFixed(1)
})

// Métricas da Fila em tempo real
const totalTarefasAtivasNaFila = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending' || j.status === 'running').length
})

const tarefasRunning = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'running').length
})

const tarefasPending = computed(() => {
  return filaStore.jobs.filter(j => j.status === 'pending').length
})

function formatarMesExtenso(mesAno: string): string {
  if (!mesAno || !mesAno.includes('/')) return mesAno
  const [mes, ano] = mesAno.split('/')
  const meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]
  const mesIdx = parseInt(mes, 10) - 1
  const nomeMes = meses[mesIdx] || mes
  return `${nomeMes} de ${ano}`
}

function obterClasseCorRepo(nome?: string): string {
  if (!nome) return 'repo-color-default'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const idx = Math.abs(hash) % 6
  return `repo-color-${idx}`
}

function navegarParaRepo(nome: string) {
  router.push({ path: '/commits', query: { repo: nome } })
}

// Distribuição consolidada por Repositório
const distribuicaoRepositorios = computed(() => {
  const commits = commitsDoPeriodo.value
  const total = commits.length
  if (total === 0) return []

  const map: Record<string, {
    nome: string
    commitsCount: number
    analisados: number
    pendentes: number
    totalTarefas: number
    tarefasEnviadas: number
    totalHpa: number
    hpaEnviado: number
    hpaPendente: number
    pctHpaEnviado: number
    colorClass: string
  }> = {}

  for (const c of commits) {
    const nome = c.projeto?.trim() || 'Sem repositório'
    if (!map[nome]) {
      map[nome] = {
        nome,
        commitsCount: 0,
        analisados: 0,
        pendentes: 0,
        totalTarefas: 0,
        tarefasEnviadas: 0,
        totalHpa: 0,
        hpaEnviado: 0,
        hpaPendente: 0,
        pctHpaEnviado: 0,
        colorClass: obterClasseCorRepo(nome)
      }
    }
    const item = map[nome]
    item.commitsCount++
    if (c.analisado) item.analisados++
    else item.pendentes++
    if (c.atividades_total) item.totalTarefas += c.atividades_total
    if (c.atividades_enviadas) item.tarefasEnviadas += c.atividades_enviadas
    if (c.hpa_total) item.totalHpa += c.hpa_total
    if (c.hpa_enviado) item.hpaEnviado += c.hpa_enviado
  }

  return Object.values(map)
    .map(r => {
      const hpaPendente = Math.max(0, r.totalHpa - r.hpaEnviado)
      const pctHpaEnviado = r.totalHpa > 0 ? Math.min(100, Math.round((r.hpaEnviado / r.totalHpa) * 100)) : 0
      return {
        ...r,
        hpaPendente,
        pctHpaEnviado
      }
    })
    .sort((a, b) => b.totalHpa - a.totalHpa)
})

// Histórico mensal cronológico para o gráfico SVG
function parseMesAno(mesAno: string): number {
  const parts = mesAno.split('/')
  if (parts.length === 2) {
    const m = parseInt(parts[0], 10)
    const y = parseInt(parts[1], 10)
    return y * 12 + m
  }
  return 0
}

const historicoMensal = computed(() => {
  if (!store.stats || !store.stats.months.length) return []
  const mesesOrdenados = [...store.stats.months].sort((a, b) => parseMesAno(a) - parseMesAno(b))
  return mesesOrdenados.map(mes => {
    const st = store.stats?.by_month[mes] || { total_hpa: 0, total_tasks: 0, codes: {} }
    const [m, a] = mes.split('/')
    const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const labelCurto = `${nomesMeses[parseInt(m, 10) - 1] || m}/${a.slice(2)}`
    return {
      mes,
      labelCurto,
      labelLongo: formatarMesExtenso(mes),
      hpa: Number(st.total_hpa.toFixed(1)),
      tarefas: st.total_tasks
    }
  })
})

const maxHpaMensal = computed(() => {
  if (!historicoMensal.value.length) return 10
  const max = Math.max(...historicoMensal.value.map(item => item.hpa))
  return max > 0 ? Math.ceil(max * 1.2) : 10
})

function calcularLarguraBarra(totalMeses: number): number {
  if (totalMeses <= 1) return 50
  const espacoUtil = 440
  const maxLargura = 44
  const calculada = (espacoUtil / totalMeses) * 0.55
  return Math.min(maxLargura, Math.max(22, calculada))
}

function calcularXBarra(idx: number, totalMeses: number): number {
  const espacoUtil = 440
  const startX = 60
  if (totalMeses <= 1) return startX + 180
  const step = espacoUtil / totalMeses
  const w = calcularLarguraBarra(totalMeses)
  return startX + (idx * step) + (step - w) / 2
}

function calcularAlturaBarra(hpa: number): number {
  const alturaMax = 115
  if (maxHpaMensal.value <= 0 || hpa <= 0) return 3
  const alt = (hpa / maxHpaMensal.value) * alturaMax
  return Math.max(3, Math.round(alt))
}

function calcularYBarra(hpa: number): number {
  const baseline = 140
  const alt = calcularAlturaBarra(hpa)
  return baseline - alt
}

function selecionarMes(mes: string) {
  if (mesSelecionado.value === mes) {
    mesSelecionado.value = 'todos'
  } else {
    mesSelecionado.value = mes
  }
}

// Processamento da tabela de Códigos
const codigosProcessados = computed(() => {
  const entries = Object.entries(statsExibidas.value.codes).map(([codigo, info]) => {
    const hpa = info.hpa
    const count = info.count
    const media = count > 0 ? (hpa / count).toFixed(1) : '0.0'
    const pctHpa = statsExibidas.value.total_hpa > 0 
      ? Math.round((hpa / statsExibidas.value.total_hpa) * 100) 
      : 0
    return {
      codigo,
      count,
      hpa,
      media,
      pctHpa
    }
  })

  let filtered = entries
  if (termoBuscaCodigo.value.trim()) {
    const q = termoBuscaCodigo.value.toLowerCase().trim()
    filtered = filtered.filter(item => item.codigo.toLowerCase().includes(q))
  }

  if (ordenacaoCodigos.value === 'hpa') {
    filtered.sort((a, b) => b.hpa - a.hpa)
  } else if (ordenacaoCodigos.value === 'count') {
    filtered.sort((a, b) => b.count - a.count)
  } else {
    filtered.sort((a, b) => a.codigo.localeCompare(b.codigo))
  }

  return filtered
})

// Integrações exibidas na barra de status
const integracoes = computed(() => [
  {
    chave: 'gitlab',
    icone: 'fa-brands fa-gitlab',
    ativo: servicosStatus.value.gitlab,
    texto: `GitLab ${servicosStatus.value.gitlab ? 'Conectado' : 'Aguardando'}`
  },
  {
    chave: 'gemini',
    icone: 'fa-solid fa-wand-magic-sparkles',
    ativo: servicosStatus.value.gemini,
    texto: `Gemini IA ${servicosStatus.value.gemini ? 'Ativo' : 'Pendente'}`
  },
  {
    chave: 'munka',
    icone: 'fa-solid fa-briefcase',
    ativo: servicosStatus.value.munka,
    texto: `Munka ${servicosStatus.value.munka ? 'Conectado' : 'Não configurado'}`
  }
])

// Etapas do pipeline de automação
const etapasPipeline = computed(() => [
  {
    numero: 1,
    rotulo: 'Ingestão Git',
    valor: `${totalCommitsPeriodo.value} Commits`,
    descricao: `${distribuicaoRepositorios.value.length} Repositórios monitorados`,
    concluida: true
  },
  {
    numero: 2,
    rotulo: 'Análise de IA',
    valor: `${commitsAnalisadosPeriodo.value} Analisados`,
    descricao: `${taxaAnaliseIA.value}% dos commits processados`,
    concluida: taxaAnaliseIA.value >= 90
  },
  {
    numero: 3,
    rotulo: 'Atividades HPA',
    valor: `${statsExibidas.value.total_tasks} Tarefas`,
    descricao: `${statsExibidas.value.total_hpa}h faturáveis mapeadas`,
    concluida: true
  },
  {
    numero: 4,
    rotulo: 'Timesheet Munka',
    valor: `${tarefasEnviadasPeriodo.value} Enviadas`,
    descricao: `${hpaEnviadoPeriodo.value}h faturadas com sucesso (${taxaTarefasEnviadas.value}%)`,
    concluida: taxaTarefasEnviadas.value === 100
  }
])
</script>
