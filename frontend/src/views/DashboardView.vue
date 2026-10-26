<template>
  <div class="page dashboard-page">
    <!-- Cabeçalho do Dashboard -->
    <header class="page-header dashboard-header">
      <div class="header-main-col">
        <div class="title-row">
          <h1>Dashboard de Indicadores</h1>
          <HelpModal title="Sobre o Dashboard" :items="helpItems" />
        </div>
        <p class="dashboard-subtitle">
          Métricas consolidadas de commits, análise preditiva com IA e faturamento HPA integrado ao Munka.
        </p>
      </div>

      <!-- Controles de Período e Ações Rápidas -->
      <div class="header-controls-col">
        <div v-if="store.stats" class="period-control-wrap">
          <label for="mes-filtro-dashboard" class="filter-label">Período:</label>
          <div class="select-wrapper">
            <select 
              id="mes-filtro-dashboard" 
              v-model="mesSelecionado" 
              class="select-periodo" 
              aria-label="Filtrar indicadores por período ou mês"
            >
              <option value="todos">Consolidado (Todos os Meses)</option>
              <option v-for="m in store.stats.months" :key="m" :value="m">
                {{ formatarMesExtenso(m) }}
              </option>
            </select>
            <i class="fa-solid fa-chevron-down select-chevron" aria-hidden="true"></i>
          </div>
        </div>

        <button 
          type="button" 
          class="btn-refresh" 
          :disabled="atualizando"
          @click="recarregarDados"
          title="Recarregar dados do dashboard"
          aria-label="Recarregar dados do dashboard"
        >
          <i class="fa-solid fa-rotate" :class="{ 'fa-spin': atualizando }" aria-hidden="true"></i>
        </button>

        <button 
          type="button" 
          class="btn-primary btn-import-shortcut" 
          @click="$router.push('/importar')"
        >
          <i class="fa-solid fa-file-import" aria-hidden="true"></i>
          <span>+ Importar Commit</span>
        </button>
      </div>
    </header>

    <!-- Barra de Conectividade e Saúde dos Serviços -->
    <div class="system-status-bar" role="region" aria-label="Status das integrações do sistema">
      <div class="status-items-left">
        <span class="status-item" :class="{ 'is-active': servicosStatus.gitlab }">
          <span class="status-indicator"></span>
          <i class="fa-brands fa-gitlab" aria-hidden="true"></i>
          <span>GitLab {{ servicosStatus.gitlab ? 'Conectado' : 'Aguardando' }}</span>
        </span>
        <span class="status-divider" aria-hidden="true">·</span>
        <span class="status-item" :class="{ 'is-active': servicosStatus.gemini }">
          <span class="status-indicator"></span>
          <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>
          <span>Gemini IA {{ servicosStatus.gemini ? 'Ativo' : 'Pendente' }}</span>
        </span>
        <span class="status-divider" aria-hidden="true">·</span>
        <span class="status-item" :class="{ 'is-active': servicosStatus.munka }">
          <span class="status-indicator"></span>
          <i class="fa-solid fa-briefcase" aria-hidden="true"></i>
          <span>Munka {{ servicosStatus.munka ? 'Conectado' : 'Não configurado' }}</span>
        </span>
      </div>

      <div class="status-items-right">
        <router-link to="/fila" class="queue-status-link" title="Ver fila de execução em tempo real">
          <span v-if="totalTarefasAtivasNaFila > 0" class="queue-active-badge">
            <span class="spinner-dot-xs"></span>
            <span>{{ totalTarefasAtivasNaFila }} tarefa{{ totalTarefasAtivasNaFila > 1 ? 's' : '' }} na fila</span>
          </span>
          <span v-else class="queue-idle-badge">
            <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
            <span>Fila operacional</span>
          </span>
        </router-link>
      </div>
    </div>

    <!-- Estado de Carregamento -->
    <div v-if="store.loading && store.commits.length === 0" class="loading" role="status" aria-live="polite">
      Carregando indicadores do dashboard...
    </div>

    <!-- Estado Vazio -->
    <div v-else-if="store.commits.length === 0" class="empty-dashboard-card">
      <div class="empty-icon-wrap">
        <i class="fa-solid fa-chart-line" aria-hidden="true"></i>
      </div>
      <h2>Nenhum dado cadastrado ainda</h2>
      <p>Importe commits do GitLab para que a IA analise as alterações de código e gere os relatórios de faturamento HPA automaticamente.</p>
      <button type="button" class="btn-primary" @click="$router.push('/importar')">
        <i class="fa-solid fa-file-import" aria-hidden="true"></i>
        <span>Importar Primeiro Commit</span>
      </button>
    </div>

    <!-- Conteúdo Principal do Dashboard -->
    <main v-else class="dashboard-content">
      
      <!-- 1. FAIXA EXECUTIVA DE KPIS (ESTILO SAAS CONSOLIDADO) -->
      <section class="kpi-executive-strip" aria-label="Indicadores executivos">
        <!-- KPI 1: Horas HPA -->
        <div class="kpi-strip-cell">
          <div class="kpi-cell-header">
            <span class="kpi-cell-label">HPA Faturável</span>
            <span class="badge-kpi-status" :class="taxaHpaEnviado === 100 ? 'status-green' : 'status-blue'">
              {{ taxaHpaEnviado }}% enviado
            </span>
          </div>
          <div class="kpi-cell-value-row">
            <span class="kpi-cell-num">{{ statsExibidas.total_hpa }}</span>
            <span class="kpi-cell-unit">h</span>
          </div>
          <div class="kpi-cell-progress" role="progressbar" :aria-valuenow="taxaHpaEnviado" aria-valuemin="0" aria-valuemax="100" :aria-label="`Percentual de HPA enviado: ${taxaHpaEnviado}%`">
            <div class="kpi-progress-bar" :style="{ width: `${taxaHpaEnviado}%` }"></div>
          </div>
          <span class="kpi-cell-sub">
            <strong>{{ hpaEnviadoPeriodo }}h</strong> enviados · {{ hpaPendentePeriodo }}h pendentes
          </span>
        </div>

        <!-- KPI 2: Atividades -->
        <div class="kpi-strip-cell">
          <div class="kpi-cell-header">
            <span class="kpi-cell-label">Tarefas Identificadas</span>
            <span class="badge-kpi-status status-neutral">
              {{ Object.keys(statsExibidas.codes).length }} tipos
            </span>
          </div>
          <div class="kpi-cell-value-row">
            <span class="kpi-cell-num">{{ statsExibidas.total_tasks }}</span>
            <span class="kpi-cell-unit">atividades</span>
          </div>
          <div class="kpi-cell-progress" role="progressbar" :aria-valuenow="taxaTarefasEnviadas" aria-valuemin="0" aria-valuemax="100" :aria-label="`Percentual de tarefas enviadas: ${taxaTarefasEnviadas}%`">
            <div class="kpi-progress-bar kpi-bar-cyan" :style="{ width: `${taxaTarefasEnviadas}%` }"></div>
          </div>
          <span class="kpi-cell-sub">
            <strong>{{ tarefasEnviadasPeriodo }}</strong> enviadas ao Munka ({{ taxaTarefasEnviadas }}%)
          </span>
        </div>

        <!-- KPI 3: Commits & Cobertura IA -->
        <div class="kpi-strip-cell">
          <div class="kpi-cell-header">
            <span class="kpi-cell-label">Commits no Período</span>
            <span class="badge-kpi-status" :class="taxaAnaliseIA >= 90 ? 'status-green' : 'status-amber'">
              {{ taxaAnaliseIA }}% IA
            </span>
          </div>
          <div class="kpi-cell-value-row">
            <span class="kpi-cell-num">{{ totalCommitsPeriodo }}</span>
            <span class="kpi-cell-unit">commits</span>
          </div>
          <div class="kpi-cell-progress" role="progressbar" :aria-valuenow="taxaAnaliseIA" aria-valuemin="0" aria-valuemax="100" :aria-label="`Cobertura de análise IA: ${taxaAnaliseIA}%`">
            <div class="kpi-progress-bar kpi-bar-emerald" :style="{ width: `${taxaAnaliseIA}%` }"></div>
          </div>
          <span class="kpi-cell-sub">
            <strong>{{ commitsAnalisadosPeriodo }}</strong> analisados · {{ commitsPendentesPeriodo }} pendentes
          </span>
        </div>

        <!-- KPI 4: Média HPA por Tarefa -->
        <div class="kpi-strip-cell">
          <div class="kpi-cell-header">
            <span class="kpi-cell-label">Esforço Médio</span>
            <span class="badge-kpi-status status-neutral">
              HPA / Tarefa
            </span>
          </div>
          <div class="kpi-cell-value-row">
            <span class="kpi-cell-num">{{ mediaHpaPorTarefa }}</span>
            <span class="kpi-cell-unit">h/tarefa</span>
          </div>
          <div class="kpi-cell-progress">
            <div class="kpi-progress-bar kpi-bar-amber" :style="{ width: `${Math.min(100, Math.round((Number(mediaHpaPorTarefa) / 3.0) * 100))}%` }"></div>
          </div>
          <span class="kpi-cell-sub">
            {{ distribuicaoRepositorios.length }} repositórios avaliados
          </span>
        </div>

        <!-- KPI 5: Fila de Execução -->
        <div class="kpi-strip-cell kpi-cell-queue">
          <div class="kpi-cell-header">
            <span class="kpi-cell-label">Status da Fila</span>
            <span class="badge-kpi-status" :class="totalTarefasAtivasNaFila > 0 ? 'status-amber' : 'status-green'">
              {{ totalTarefasAtivasNaFila > 0 ? 'Processando' : 'Sincronizado' }}
            </span>
          </div>
          <div class="kpi-cell-value-row">
            <span class="kpi-cell-num">{{ totalTarefasAtivasNaFila }}</span>
            <span class="kpi-cell-unit">em fila</span>
          </div>
          <div class="kpi-cell-progress">
            <div class="kpi-progress-bar kpi-bar-blue" :style="{ width: totalTarefasAtivasNaFila > 0 ? '70%' : '100%' }"></div>
          </div>
          <span class="kpi-cell-sub">
            <router-link to="/fila" class="kpi-queue-link">
              <span>{{ totalTarefasAtivasNaFila > 0 ? `${tarefasRunning} rodando, ${tarefasPending} na espera` : 'Nenhum job pendente' }}</span>
              <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
            </router-link>
          </span>
        </div>
      </section>

      <!-- 2. ALERTA OPERACIONAL DE AÇÕES PENDENTES (SE HOUVER PENDÊNCIAS) -->
      <section v-if="commitsPendentesPeriodo > 0 || tarefasPendentesPeriodo > 0" class="action-alert-banner" role="region" aria-label="Ações pendentes recomendadas">
        <div class="alert-icon-col">
          <i class="fa-solid fa-bolt" aria-hidden="true"></i>
        </div>
        <div class="alert-text-col">
          <h3 class="alert-title">Ações recomendadas para este período</h3>
          <p class="alert-desc">
            <span v-if="commitsPendentesPeriodo > 0">
              Existem <strong>{{ commitsPendentesPeriodo }} commit{{ commitsPendentesPeriodo > 1 ? 's' : '' }}</strong> aguardando análise de IA.
            </span>
            <span v-if="commitsPendentesPeriodo > 0 && tarefasPendentesPeriodo > 0"> · </span>
            <span v-if="tarefasPendentesPeriodo > 0">
              Existem <strong>{{ tarefasPendentesPeriodo }} tarefa{{ tarefasPendentesPeriodo > 1 ? 's' : '' }}</strong> ({{ hpaPendentePeriodo }}h HPA) prontas aguardando envio ao Munka.
            </span>
          </p>
        </div>
        <div class="alert-action-col">
          <button 
            type="button" 
            class="btn-alert-action" 
            @click="$router.push('/commits')"
          >
            <span>Gerenciar na Tela de Commits</span>
            <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
          </button>
        </div>
      </section>

      <!-- 3. FUNIL DE AUTOMAÇÃO DO FLUXO DE VALOR (PIPELINE SAAS) -->
      <section class="dashboard-panel funnel-panel" aria-label="Pipeline do fluxo de valor">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fa-solid fa-timeline" aria-hidden="true"></i>
            <h2>Pipeline de Automação</h2>
          </div>
          <span class="panel-badge-info">Ciclo Completo: Ingestão Git → IA Gemini → Timesheet Munka</span>
        </div>

        <div class="pipeline-track">
          <!-- Passo 1: Ingestão -->
          <div class="pipeline-stage stage-completed">
            <div class="stage-num-badge">1</div>
            <div class="stage-info">
              <span class="stage-label">Ingestão Git</span>
              <span class="stage-val">{{ totalCommitsPeriodo }} Commits</span>
              <span class="stage-desc">{{ distribuicaoRepositorios.length }} Repositórios monitorados</span>
            </div>
            <i class="fa-solid fa-chevron-right stage-arrow" aria-hidden="true"></i>
          </div>

          <!-- Passo 2: IA Gemini -->
          <div class="pipeline-stage" :class="taxaAnaliseIA >= 90 ? 'stage-completed' : 'stage-progress'">
            <div class="stage-num-badge">2</div>
            <div class="stage-info">
              <span class="stage-label">Análise de IA</span>
              <span class="stage-val">{{ commitsAnalisadosPeriodo }} Analisados</span>
              <span class="stage-desc">{{ taxaAnaliseIA }}% dos commits processados</span>
            </div>
            <i class="fa-solid fa-chevron-right stage-arrow" aria-hidden="true"></i>
          </div>

          <!-- Passo 3: Atividades & HPA -->
          <div class="pipeline-stage stage-completed">
            <div class="stage-num-badge">3</div>
            <div class="stage-info">
              <span class="stage-label">Atividades HPA</span>
              <span class="stage-val">{{ statsExibidas.total_tasks }} Tarefas</span>
              <span class="stage-desc">{{ statsExibidas.total_hpa }}h faturáveis mapeadas</span>
            </div>
            <i class="fa-solid fa-chevron-right stage-arrow" aria-hidden="true"></i>
          </div>

          <!-- Passo 4: Envio Munka -->
          <div class="pipeline-stage" :class="taxaTarefasEnviadas === 100 ? 'stage-completed' : 'stage-progress'">
            <div class="stage-num-badge">4</div>
            <div class="stage-info">
              <span class="stage-label">Timesheet Munka</span>
              <span class="stage-val">{{ tarefasEnviadasPeriodo }} Enviadas</span>
              <span class="stage-desc">{{ hpaEnviadoPeriodo }}h faturadas com sucesso ({{ taxaTarefasEnviadas }}%)</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. GRID CENTRAL: REPOSITÓRIOS E HISTÓRICO MENSAL -->
      <div class="dashboard-two-col-grid">
        
        <!-- Coluna Esquerda: Distribuição por Repositório -->
        <section class="dashboard-panel repo-distribution-panel" aria-label="Distribuição por Repositório">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fa-brands fa-git-alt" aria-hidden="true"></i>
              <h2>Repositórios & Faturamento</h2>
            </div>
            <router-link to="/commits" class="link-panel-action" title="Abrir lista completa de commits">
              <span>Ver Commits</span>
              <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>
            </router-link>
          </div>

          <div v-if="distribuicaoRepositorios.length === 0" class="panel-empty">
            Nenhum repositório com dados no período selecionado.
          </div>

          <div v-else class="repo-rows-list">
            <div 
              v-for="repo in distribuicaoRepositorios" 
              :key="repo.nome" 
              class="repo-list-row"
              tabindex="0"
              role="button"
              @click="navegarParaRepo(repo.nome)"
              @keydown.enter.prevent="navegarParaRepo(repo.nome)"
              @keydown.space.prevent="navegarParaRepo(repo.nome)"
              :title="`Filtrar commits de ${repo.nome}`"
            >
              <div class="repo-row-left">
                <span class="repo-badge-dot" :class="repo.colorClass"></span>
                <div class="repo-row-titles">
                  <span class="repo-row-name" :title="repo.nome">{{ repo.nome }}</span>
                  <div class="repo-row-badges">
                    <span class="repo-meta-pill">{{ repo.commitsCount }} commit{{ repo.commitsCount > 1 ? 's' : '' }}</span>
                    <span class="repo-meta-pill">{{ repo.totalTarefas }} tarefa{{ repo.totalTarefas > 1 ? 's' : '' }}</span>
                    <span v-if="repo.pendentes > 0" class="repo-meta-pill pill-amber" title="Commits pendentes de análise">
                      {{ repo.pendentes }} pendente{{ repo.pendentes > 1 ? 's' : '' }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="repo-row-right">
                <div class="repo-hpa-col">
                  <div class="repo-hpa-val">
                    <strong>{{ repo.totalHpa.toFixed(1) }}</strong>
                    <span class="unit-sm">h</span>
                  </div>
                  <span class="repo-hpa-sub">
                    {{ repo.hpaEnviado.toFixed(1) }}h env. ({{ repo.pctHpaEnviado }}%)
                  </span>
                </div>

                <div class="repo-progress-wrap" :title="`${repo.pctHpaEnviado}% do HPA enviado ao Munka`">
                  <div class="repo-mini-bar">
                    <div class="repo-mini-fill" :style="{ width: `${repo.pctHpaEnviado}%` }"></div>
                  </div>
                </div>

                <i class="fa-solid fa-chevron-right repo-nav-arrow" aria-hidden="true"></i>
              </div>
            </div>
          </div>
        </section>

        <!-- Coluna Direita: Gráfico de Evolução Mensal (SVG Dinâmico) -->
        <section class="dashboard-panel monthly-history-panel" aria-label="Evolução Mensal de HPA">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fa-solid fa-chart-simple" aria-hidden="true"></i>
              <h2>Evolução Mensal de HPA</h2>
            </div>
            <span class="panel-badge-info">Clique em uma barra para filtrar o mês</span>
          </div>

          <div v-if="historicoMensal.length === 0" class="panel-empty">
            Nenhum histórico mensal disponível.
          </div>

          <div v-else class="chart-container">
            <!-- Gráfico de Barras SVG Responsivo e Dinâmico -->
            <svg 
              class="monthly-bars-svg" 
              viewBox="0 0 520 180" 
              role="img" 
              aria-label="Gráfico de barras de HPA por mês"
            >
              <!-- Linhas horizontais de referência (Grid) -->
              <line x1="45" y1="20" x2="510" y2="20" class="svg-gridline" />
              <text x="40" y="24" class="svg-axis-lbl" text-anchor="end">{{ maxHpaMensal }}h</text>

              <line x1="45" y1="80" x2="510" y2="80" class="svg-gridline" />
              <text x="40" y="84" class="svg-axis-lbl" text-anchor="end">{{ Math.round(maxHpaMensal / 2) }}h</text>

              <line x1="45" y1="140" x2="510" y2="140" class="svg-baseline" />
              <text x="40" y="144" class="svg-axis-lbl" text-anchor="end">0h</text>

              <!-- Barras Mensais -->
              <g 
                v-for="(item, idx) in historicoMensal" 
                :key="item.mes" 
                class="svg-bar-group"
                :class="{ 'is-selected': mesSelecionado === item.mes }"
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
                  class="svg-bar-rect"
                />

                <!-- Rótulo de Valor no Topo da Barra -->
                <text 
                  :x="calcularXBarra(idx, historicoMensal.length) + (calcularLarguraBarra(historicoMensal.length) / 2)"
                  :y="Math.max(14, calcularYBarra(item.hpa) - 5)"
                  class="svg-bar-val"
                  text-anchor="middle"
                >
                  {{ item.hpa }}h
                </text>

                <!-- Rótulo do Mês na Base -->
                <text 
                  :x="calcularXBarra(idx, historicoMensal.length) + (calcularLarguraBarra(historicoMensal.length) / 2)"
                  y="160"
                  class="svg-bar-lbl"
                  text-anchor="middle"
                >
                  {{ item.labelCurto }}
                </text>
              </g>
            </svg>

            <!-- Legenda e Destaque do Mês Ativo -->
            <div class="chart-footer-bar">
              <div class="chart-active-pill">
                <span class="active-dot"></span>
                <span>Visualizando: <strong>{{ mesSelecionado === 'todos' ? 'Todos os meses acumulados' : formatarMesExtenso(mesSelecionado) }}</strong></span>
              </div>
              <button 
                v-if="mesSelecionado !== 'todos'" 
                type="button" 
                class="btn-reset-period" 
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
      <section class="dashboard-panel codes-table-panel" aria-label="Quantificação por Tipo de Serviço">
        <div class="panel-header">
          <div class="panel-title-group">
            <div class="panel-title">
              <i class="fa-solid fa-tags" aria-hidden="true"></i>
              <h2>Quantificação por Tipo de Serviço</h2>
            </div>
            <p class="panel-desc">Códigos de serviço faturáveis gerados e justificados pela IA com base nas mudanças de código.</p>
          </div>

          <!-- Controles de Busca e Ordenação da Tabela -->
          <div class="table-controls-row">
            <div class="table-search-box">
              <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
              <input 
                type="search" 
                v-model="termoBuscaCodigo" 
                placeholder="Buscar código..." 
                aria-label="Filtrar por código de serviço"
                class="input-table-search"
              />
            </div>

            <div class="table-sort-group" role="group" aria-label="Ordenar códigos por">
              <button 
                type="button" 
                class="sort-tab-btn" 
                :class="{ active: ordenacaoCodigos === 'hpa' }"
                @click="ordenacaoCodigos = 'hpa'"
              >
                Mais HPA
              </button>
              <button 
                type="button" 
                class="sort-tab-btn" 
                :class="{ active: ordenacaoCodigos === 'count' }"
                @click="ordenacaoCodigos = 'count'"
              >
                Mais Tarefas
              </button>
              <button 
                type="button" 
                class="sort-tab-btn" 
                :class="{ active: ordenacaoCodigos === 'codigo' }"
                @click="ordenacaoCodigos = 'codigo'"
              >
                Código
              </button>
            </div>
          </div>
        </div>

        <div v-if="codigosProcessados.length === 0" class="panel-empty">
          Nenhum código de serviço encontrado para os critérios selecionados.
        </div>

        <!-- Tabela SaaS de Alta Densidade e Alinhamento Preciso -->
        <div v-else class="table-responsive-wrapper">
          <table class="saas-data-table">
            <thead>
              <tr>
                <th scope="col" class="th-code">Código do Serviço</th>
                <th scope="col" class="th-count text-right">Tarefas</th>
                <th scope="col" class="th-hpa text-right">HPA Total</th>
                <th scope="col" class="th-avg text-right">Média / Tarefa</th>
                <th scope="col" class="th-share">Participação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in codigosProcessados" :key="item.codigo" class="tr-code-row">
                <td class="td-code">
                  <div class="code-badge-wrap">
                    <span class="badge badge-code"><code>{{ item.codigo }}</code></span>
                  </div>
                </td>
                <td class="td-count text-right">
                  <strong>{{ item.count }}</strong>
                  <span class="sub-unit">tarefa{{ item.count > 1 ? 's' : '' }}</span>
                </td>
                <td class="td-hpa text-right">
                  <span class="hpa-highlight">{{ item.hpa.toFixed(1) }}</span>
                  <span class="sub-unit">h</span>
                </td>
                <td class="td-avg text-right">
                  <span>{{ item.media }}h</span>
                </td>
                <td class="td-share">
                  <div class="share-cell-layout">
                    <div class="mini-progress-track">
                      <div class="mini-progress-fill" :style="{ width: `${item.pctHpa}%` }"></div>
                    </div>
                    <span class="share-pct-label">{{ item.pctHpa }}%</span>
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
import HelpModal from '../components/HelpModal.vue'
import type { CommitSummary } from '../api'

const router = useRouter()
const store = useCommitsStore()
const filaStore = useFilaStore()

const helpItems = [
  { title: 'Visão Geral Executiva', text: 'Painel consolidado com indicadores de faturamento HPA, esforço médio, tarefas mapeadas e taxas de conversão do código para o Munka.' },
  { title: 'Filtro Temporal', text: 'Selecione um mês específico para avaliar a produtividade mensal ou mantenha em "Consolidado" para visualizar o acumulado histórico.' },
  { title: 'Gráfico Interativo', text: 'Clique nas barras mensais para alternar rapidamente o período exibido no dashboard.' },
  { title: 'Pipeline de Automação', text: 'Acompanhe as 4 etapas do fluxo operacional: Ingestão de Commits Git, Análise por IA (Gemini), Extração de Atividades HPA e Envio ao Timesheet Munka.' },
  { title: 'Quantificação por Código', text: 'Analise a distribuição de esforço e faturamento por categoria e código de serviço prestado.' },
]

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
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 2.25rem;
}

/* ── CABEÇALHO DO DASHBOARD ── */
.dashboard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--card-border, #334155);
}

.header-main-col {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  min-width: 260px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-row h1 {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--text, #f8fafc);
}

.dashboard-subtitle {
  font-size: 0.9rem;
  color: var(--text-muted, #94a3b8);
  margin: 0;
  line-height: 1.45;
}

.header-controls-col {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.period-control-wrap {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--border, #334155);
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
}

.filter-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.select-periodo {
  appearance: none;
  background: transparent;
  color: var(--text, #f8fafc);
  border: none;
  padding-right: 1.5rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.select-chevron {
  position: absolute;
  right: 0;
  pointer-events: none;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.btn-refresh {
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--border, #334155);
  border-radius: 8px;
  color: var(--text-muted, #94a3b8);
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
}

.btn-refresh:hover {
  color: var(--text, #f8fafc);
  border-color: var(--accent, #3b82f6);
}

.btn-refresh:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

.btn-import-shortcut {
  font-weight: 700;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}

/* ── BARRA DE CONECTIVIDADE / STATUS ── */
.system-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.4rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border: 1px solid var(--card-border, #334155);
  border-radius: 10px;
  font-size: 0.84rem;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 0.25rem;
}

.status-items-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.status-item {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-muted, #94a3b8);
  font-weight: 500;
}

.status-item.is-active {
  color: var(--text, #f8fafc);
}

.status-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #64748b;
  display: inline-block;
}

.status-item.is-active .status-indicator {
  background: var(--success, #10b981);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

.status-divider {
  color: var(--border, #334155);
}

.queue-status-link {
  text-decoration: none;
  outline: none;
}

.queue-active-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.35);
  font-weight: 700;
  font-size: 0.78rem;
}

.queue-idle-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
  font-weight: 600;
  font-size: 0.78rem;
}

.spinner-dot-xs {
  width: 6px;
  height: 6px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-right-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── FAIXA EXECUTIVA DE KPIS (CONTAINER UNIFICADO) ── */
.kpi-executive-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--card-border, #334155);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.kpi-strip-cell {
  padding: 1.5rem 1.6rem;
  border-right: 1px solid var(--card-border, #334155);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  transition: background 0.15s ease;
}

.kpi-strip-cell:last-child {
  border-right: none;
}

.kpi-strip-cell:hover {
  background: rgba(255, 255, 255, 0.02);
}

.kpi-cell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.kpi-cell-label {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-muted, #94a3b8);
  letter-spacing: -0.01em;
}

.badge-kpi-status {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 5px;
}

.status-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-green {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-amber {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-neutral {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.kpi-cell-value-row {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  margin: 0.35rem 0 0.15rem 0;
}

.kpi-cell-num {
  font-size: 2.1rem;
  font-weight: 800;
  color: var(--text, #f8fafc);
  line-height: 1.1;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.kpi-cell-unit {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted, #94a3b8);
}

.kpi-cell-progress {
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 0.45rem;
  margin-bottom: 0.35rem;
}

.kpi-progress-bar {
  height: 100%;
  background: var(--accent, #3b82f6);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.kpi-bar-cyan {
  background: var(--accent-cyan, #06b6d4);
}

.kpi-bar-emerald {
  background: var(--success, #10b981);
}

.kpi-bar-amber {
  background: var(--warning, #f59e0b);
}

.kpi-bar-blue {
  background: var(--accent, #3b82f6);
}

.kpi-cell-sub {
  font-size: 0.82rem;
  color: var(--text-muted, #94a3b8);
  margin-top: 0.25rem;
  line-height: 1.45;
}

.kpi-cell-sub strong {
  color: var(--text, #f8fafc);
}

.kpi-queue-link {
  color: var(--accent-light, #60a5fa);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: gap 0.15s ease;
}

.kpi-queue-link:hover {
  text-decoration: underline;
  gap: 0.55rem;
}

/* ── BANNER DE AÇÃO RECOMENDADA ── */
.action-alert-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.25rem 1.75rem;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 12px;
  flex-wrap: wrap;
}

.alert-icon-col {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}

.alert-text-col {
  flex: 1;
  min-width: 260px;
}

.alert-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text, #f8fafc);
}

.alert-desc {
  margin: 0.35rem 0 0 0;
  font-size: 0.86rem;
  color: var(--text-muted, #cbd5e1);
  line-height: 1.45;
}

.alert-desc strong {
  color: #fef08a;
}

.btn-alert-action {
  background: #d97706;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1.25rem;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.15s ease;
}

.btn-alert-action:hover {
  background: #b45309;
}

.btn-alert-action:focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}

/* ── PAINEL DE PIPELINE DE VALOR (FUNIL SAAS) ── */
.funnel-panel {
  padding: 1.75rem 2rem;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--card-border, #334155);
  padding-bottom: 1.25rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--accent-light, #60a5fa);
}

.panel-title h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text, #f8fafc);
  letter-spacing: -0.01em;
}

.panel-badge-info {
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
  font-weight: 500;
}

.pipeline-track {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.25rem;
}

.pipeline-stage {
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border: 1px solid var(--card-border, #334155);
  border-radius: 10px;
  padding: 1.25rem 1.35rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.stage-num-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--border, #475569);
  color: var(--text-muted, #94a3b8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 800;
  flex-shrink: 0;
}

.stage-completed .stage-num-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.4);
}

.stage-progress .stage-num-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.4);
}

.stage-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.stage-label {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stage-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text, #f8fafc);
  letter-spacing: -0.01em;
  margin: 0.1rem 0;
}

.stage-desc {
  font-size: 0.78rem;
  color: var(--text-muted, #94a3b8);
  line-height: 1.4;
}

.stage-arrow {
  color: var(--card-border, #475569);
  font-size: 0.85rem;
}

/* ── GRID CENTRAL DE 2 COLUNAS (REPOSITÓRIOS & EVOLUÇÃO) ── */
.dashboard-two-col-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.dashboard-panel {
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--card-border, #334155);
  border-radius: 12px;
  padding: 1.75rem 2rem;
  display: flex;
  flex-direction: column;
}

.link-panel-action {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--accent-light, #60a5fa);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: gap 0.15s ease;
}

.link-panel-action:hover {
  text-decoration: underline;
  gap: 0.55rem;
}

.panel-empty {
  font-size: 0.88rem;
  color: var(--text-muted, #94a3b8);
  font-style: italic;
  padding: 2.5rem 0;
  text-align: center;
}

/* Lista de Repositórios */
.repo-rows-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.repo-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.35rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border: 1px solid var(--card-border, #334155);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
  gap: 1.25rem;
}

.repo-list-row:hover {
  background: rgba(59, 130, 246, 0.08);
  border-color: var(--accent, #3b82f6);
  transform: translateX(2px);
}

.repo-list-row:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

.repo-row-left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
  flex: 1;
}

.repo-badge-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.repo-row-titles {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.repo-row-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text, #f8fafc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.repo-row-badges {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.repo-meta-pill {
  font-size: 0.74rem;
  font-weight: 600;
  padding: 2px 7px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted, #94a3b8);
  border-radius: 4px;
}

.repo-meta-pill.pill-amber {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}

.repo-row-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

.repo-hpa-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
}

.repo-hpa-val {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text, #f8fafc);
}

.unit-sm {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  margin-left: 1px;
}

.repo-hpa-sub {
  font-size: 0.72rem;
  color: var(--text-muted, #94a3b8);
}

.repo-progress-wrap {
  width: 64px;
}

.repo-mini-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.repo-mini-fill {
  height: 100%;
  background: var(--success, #10b981);
  border-radius: 3px;
}

.repo-nav-arrow {
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  transition: transform 0.15s ease;
}

.repo-list-row:hover .repo-nav-arrow {
  color: var(--accent-light, #60a5fa);
  transform: translateX(2px);
}

/* Gráfico de Evolução SVG */
.chart-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  flex: 1;
}

.monthly-bars-svg {
  width: 100%;
  height: auto;
  min-height: 200px;
  overflow: visible;
}

.svg-gridline {
  stroke: rgba(255, 255, 255, 0.06);
  stroke-dasharray: 4 4;
}

.svg-baseline {
  stroke: var(--card-border, #334155);
  stroke-width: 1.5;
}

.svg-axis-lbl {
  font-size: 10px;
  fill: var(--text-muted, #94a3b8);
  font-family: inherit;
}

.svg-bar-group {
  cursor: pointer;
  outline: none;
}

.svg-bar-rect {
  fill: rgba(59, 130, 246, 0.55);
  transition: fill 0.15s ease;
}

.svg-bar-group:hover .svg-bar-rect {
  fill: var(--accent-light, #60a5fa);
}

.svg-bar-group.is-selected .svg-bar-rect {
  fill: var(--accent, #3b82f6);
}

.svg-bar-val {
  font-size: 10px;
  font-weight: 700;
  fill: var(--text, #f8fafc);
  font-family: inherit;
}

.svg-bar-lbl {
  font-size: 10px;
  font-weight: 600;
  fill: var(--text-muted, #94a3b8);
  font-family: inherit;
}

.svg-bar-group.is-selected .svg-bar-lbl {
  fill: var(--accent-light, #60a5fa);
  font-weight: 800;
}

.chart-footer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--card-border, #334155);
  padding-top: 1.1rem;
  margin-top: 0.5rem;
  font-size: 0.82rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.chart-active-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-muted, #94a3b8);
}

.active-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent, #3b82f6);
}

.btn-reset-period {
  background: transparent;
  border: 1px solid var(--border, #475569);
  color: var(--text, #f8fafc);
  border-radius: 6px;
  padding: 0.35rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-reset-period:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent, #3b82f6);
}

/* ── TABELA DE CÓDIGOS DE SERVIÇO (ALTA DENSIDADE) ── */
.codes-table-panel {
  gap: 1.5rem;
}

.panel-title-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.panel-desc {
  font-size: 0.84rem;
  color: var(--text-muted, #94a3b8);
  margin: 0;
  line-height: 1.45;
}

.table-controls-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.25rem;
}

.table-search-box {
  display: flex;
  align-items: center;
  position: relative;
  min-width: 200px;
}

.table-search-box i {
  position: absolute;
  left: 0.85rem;
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
}

.input-table-search {
  width: 100%;
  padding: 0.55rem 0.85rem 0.55rem 2.2rem;
  font-size: 0.85rem;
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--border, #475569);
  border-radius: 8px;
  color: var(--text, #f8fafc);
  outline: none;
}

.input-table-search:focus {
  border-color: var(--accent, #3b82f6);
}

.table-sort-group {
  display: inline-flex;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--card-border, #334155);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}

.sort-tab-btn {
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  padding: 0.4rem 0.8rem;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sort-tab-btn:hover {
  color: var(--text, #f8fafc);
}

.sort-tab-btn.active {
  background: var(--card-bg, #1e293b);
  color: var(--text, #f8fafc);
  border: 1px solid var(--card-border, #475569);
}

.table-responsive-wrapper {
  overflow-x: auto;
}

.saas-data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.88rem;
}

.saas-data-table th {
  padding: 1.1rem 1.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted, #94a3b8);
  border-bottom: 1px solid var(--card-border, #334155);
}

.saas-data-table td {
  padding: 1.15rem 1.4rem;
  border-bottom: 1px solid var(--card-border, #334155);
  color: var(--text, #f8fafc);
  vertical-align: middle;
}

.saas-data-table tbody tr:last-child td {
  border-bottom: none;
}

.tr-code-row {
  transition: background 0.15s ease;
}

.tr-code-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.text-right {
  text-align: right;
}

.sub-unit {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  margin-left: 0.25rem;
  font-weight: 400;
}

.hpa-highlight {
  font-weight: 800;
  color: var(--accent-light, #60a5fa);
  font-size: 0.95rem;
}

.share-cell-layout {
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 200px;
}

.mini-progress-track {
  flex: 1;
  height: 7px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  background: var(--accent, #3b82f6);
  border-radius: 4px;
}

.share-pct-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted, #cbd5e1);
  min-width: 32px;
}

/* Estado Vazio Elegante */
.empty-dashboard-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3.5rem 1.5rem;
  background: var(--card-bg, #1e293b);
  border: 1px dashed var(--border, #475569);
  border-radius: 14px;
  text-align: center;
  gap: 1rem;
}

.empty-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--accent, #3b82f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.empty-dashboard-card h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text, #f8fafc);
}

.empty-dashboard-card p {
  margin: 0;
  max-width: 480px;
  font-size: 0.88rem;
  color: var(--text-muted, #94a3b8);
  line-height: 1.5;
}

/* ── MODO CLARO (A11Y & DESIGN TASTE) ── */
:global([data-theme="light"]) .dashboard-header {
  border-bottom-color: #e2e8f0;
}

:global([data-theme="light"]) .title-row h1 {
  color: #0f172a;
}

:global([data-theme="light"]) .period-control-wrap {
  background: #ffffff;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .select-periodo {
  color: #0f172a;
}

:global([data-theme="light"]) .btn-refresh {
  background: #ffffff;
  border-color: #cbd5e1;
  color: #475569;
}

:global([data-theme="light"]) .btn-refresh:hover {
  color: #0f172a;
  border-color: #2563eb;
}

:global([data-theme="light"]) .system-status-bar {
  background: #f8fafc;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .status-item.is-active {
  color: #0f172a;
}

:global([data-theme="light"]) .kpi-executive-strip {
  background: #ffffff;
  border-color: #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:global([data-theme="light"]) .kpi-strip-cell {
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .kpi-strip-cell:hover {
  background: #f8fafc;
}

:global([data-theme="light"]) .kpi-cell-num {
  color: #0f172a;
}

:global([data-theme="light"]) .kpi-cell-sub strong {
  color: #0f172a;
}

:global([data-theme="light"]) .kpi-cell-progress {
  background: #e2e8f0;
}

:global([data-theme="light"]) .kpi-cell-sub {
  color: #475569;
}

:global([data-theme="light"]) .kpi-queue-link {
  color: #1d4ed8;
}

:global([data-theme="light"]) .action-alert-banner {
  background: #fffbeb;
  border-color: #fde68a;
}

:global([data-theme="light"]) .alert-title {
  color: #78350f;
}

:global([data-theme="light"]) .alert-desc {
  color: #92400e;
}

:global([data-theme="light"]) .alert-desc strong {
  color: #78350f;
}

:global([data-theme="light"]) .dashboard-panel {
  background: #ffffff;
  border-color: #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:global([data-theme="light"]) .panel-header {
  border-bottom-color: #e2e8f0;
}

:global([data-theme="light"]) .panel-title h2 {
  color: #0f172a;
}

:global([data-theme="light"]) .pipeline-stage {
  background: #f8fafc;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .stage-val {
  color: #0f172a;
}

:global([data-theme="light"]) .repo-list-row {
  background: #f8fafc;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .repo-list-row:hover {
  background: #f0f7ff;
  border-color: #2563eb;
}

:global([data-theme="light"]) .repo-row-name {
  color: #0f172a;
}

:global([data-theme="light"]) .repo-hpa-val {
  color: #0f172a;
}

:global([data-theme="light"]) .repo-meta-pill {
  background: #e2e8f0;
  color: #334155;
}

:global([data-theme="light"]) .repo-meta-pill.pill-amber {
  background: #fef3c7;
  color: #92400e;
}

:global([data-theme="light"]) .repo-mini-bar {
  background: #e2e8f0;
}

:global([data-theme="light"]) .svg-gridline {
  stroke: #e2e8f0;
}

:global([data-theme="light"]) .svg-baseline {
  stroke: #cbd5e1;
}

:global([data-theme="light"]) .svg-bar-rect {
  fill: #93c5fd;
}

:global([data-theme="light"]) .svg-bar-group:hover .svg-bar-rect {
  fill: #3b82f6;
}

:global([data-theme="light"]) .svg-bar-group.is-selected .svg-bar-rect {
  fill: #1d4ed8;
}

:global([data-theme="light"]) .svg-bar-val {
  fill: #0f172a;
}

:global([data-theme="light"]) .svg-bar-lbl {
  fill: #475569;
}

:global([data-theme="light"]) .chart-footer-bar {
  border-top-color: #e2e8f0;
}

:global([data-theme="light"]) .btn-reset-period {
  border-color: #cbd5e1;
  color: #334155;
}

:global([data-theme="light"]) .btn-reset-period:hover {
  background: #f1f5f9;
  border-color: #2563eb;
  color: #1d4ed8;
}

:global([data-theme="light"]) .input-table-search {
  background: #ffffff;
  border-color: #cbd5e1;
  color: #0f172a;
}

:global([data-theme="light"]) .input-table-search:focus {
  border-color: #2563eb;
}

:global([data-theme="light"]) .table-sort-group {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .sort-tab-btn {
  color: #475569;
}

:global([data-theme="light"]) .sort-tab-btn.active {
  background: #ffffff;
  color: #0f172a;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .saas-data-table th {
  color: #475569;
  border-bottom-color: #e2e8f0;
}

:global([data-theme="light"]) .saas-data-table td {
  border-bottom-color: #e2e8f0;
  color: #0f172a;
}

:global([data-theme="light"]) .tr-code-row:hover {
  background: #f8fafc;
}

:global([data-theme="light"]) .hpa-highlight {
  color: #1d4ed8;
}

:global([data-theme="light"]) .mini-progress-track {
  background: #e2e8f0;
}

:global([data-theme="light"]) .empty-dashboard-card {
  background: #ffffff;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .empty-dashboard-card h2 {
  color: #0f172a;
}

/* ── RESPONSIVIDADE (TABLET & MOBILE) ── */
@media (max-width: 1100px) {
  .kpi-executive-strip {
    grid-template-columns: repeat(3, 1fr);
  }
  .kpi-strip-cell:nth-child(3) {
    border-right: none;
  }
  .pipeline-track {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard-two-col-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .kpi-executive-strip {
    grid-template-columns: 1fr;
  }
  .kpi-strip-cell {
    border-right: none;
    border-bottom: 1px solid var(--card-border, #334155);
  }
  .kpi-strip-cell:last-child {
    border-bottom: none;
  }
  .pipeline-track {
    grid-template-columns: 1fr;
  }
  .stage-arrow {
    display: none;
  }
  .header-controls-col {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
