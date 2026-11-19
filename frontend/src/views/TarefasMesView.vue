<template>
  <div class="flex flex-col gap-6">
    <!-- Cabeçalho -->
    <header class="mb-8 flex flex-wrap items-start justify-between gap-5 border-b border-border-strong pb-5 max-md:flex-col">
      <div class="min-w-70 flex-1">
        <div class="flex items-center gap-3">
          <PageTitle>Tarefas do Mês - Munka</PageTitle>
          <TutorialModal screenId="tarefas-mes" />
          <span v-if="dados.total > 0" class="rounded-full border border-border-strong bg-muted px-2.5 py-1 text-xs font-semibold text-muted-foreground">
            {{ dados.total }} lançada{{ dados.total > 1 ? 's' : '' }}
          </span>
        </div>
        <p class="mt-1.5 max-w-180 text-sm leading-normal text-muted-foreground">
          Audite e gerencie tarefas lançadas no portal Munka. Selecione e ajuste atividades livremente quantas vezes for necessário, de forma individual ou em lote.
        </p>
      </div>

      <!-- Controles de Mês/Ano e Ações Principais -->
      <div data-tour="tarefas-mes-acoes-periodo" class="flex flex-wrap items-center gap-3 max-md:w-full max-md:justify-between">
        <!-- Seletor de Período -->
        <div class="flex items-center gap-1 rounded-lg border border-border bg-card px-1.5 py-1" role="group" aria-label="Seletor de Mês e Ano">
          <button
            type="button"
            data-tour="tarefas-mes-nav-mes" :class="classesNavMes"
            @click="mudarMes(-1)"
            title="Mês anterior"
            aria-label="Mês anterior"
          >
            <i class="fa-solid fa-chevron-left" aria-hidden="true"></i>
          </button>

          <div class="flex items-center gap-1">
            <select v-model.number="mesAtual" class="rounded-lg border-0 bg-transparent px-1.5 py-1 text-sm font-bold text-foreground shadow-field focus:ring-3 focus:ring-primary-glow focus:outline-none [&_option]:bg-card [&_option]:text-foreground" aria-label="Mês selecionado" @change="carregarTarefas">
              <option v-for="(nome, idx) in meses" :key="idx" :value="idx + 1">
                {{ nome }}
              </option>
            </select>
            <input
              v-model.number="anoAtual"
              type="number"
              class="w-15 rounded border border-transparent bg-transparent px-1 py-0.5 text-center text-sm font-semibold text-muted-foreground shadow-field focus:border-border-strong focus:bg-slate-400/10 focus:text-foreground focus:ring-3 focus:ring-primary-glow focus:outline-none"
              min="2020"
              max="2035"
              aria-label="Ano selecionado"
              @change="carregarTarefas"
            />
          </div>

          <button
            type="button"
            data-tour="tarefas-mes-nav-mes" :class="classesNavMes"
            @click="mudarMes(1)"
            title="Próximo mês"
            aria-label="Próximo mês"
          >
            <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
          </button>

          <button
            v-if="!isMesAtual"
            type="button"
            data-tour="tarefas-mes-hoje" class="cursor-pointer rounded-md border border-primary bg-primary-glow px-2 py-1 text-xs font-bold text-primary transition-all duration-150 hover:bg-primary hover:text-white"
            @click="irParaMesAtual"
            title="Voltar para o mês corrente"
          >
            Hoje
          </button>
        </div>

        <!-- Botão Sincronizar Munka -->
        <button
          type="button"
          data-tour="tarefas-mes-sincronizar" class="flex cursor-pointer items-center gap-2 rounded-lg border border-primary bg-card px-4 py-2 text-sm font-bold text-primary transition-all duration-150 enabled:hover:bg-primary enabled:hover:text-white enabled:hover:shadow-[0_2px_8px] enabled:hover:shadow-accent/25 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="sincronizando || loading"
          @click="sincronizarComMunka"
          title="Verificar status real das tarefas navegando no portal Munka"
        >
          <i class="fa-solid fa-arrows-rotate" :class="{ 'fa-spin': sincronizando }" aria-hidden="true"></i>
          <span>{{ sincronizando ? 'Sincronizando...' : 'Sincronizar no Munka' }}</span>
        </button>

        <!-- Botão Recarregar Local -->
        <BaseButton
          size="sm"
          :disabled="loading"
          @click="carregarTarefas"
          title="Atualizar listagem local"
        >
          <i class="fa-solid fa-rotate" :class="{ 'fa-spin': loading }" aria-hidden="true"></i>
          <span>Atualizar</span>
        </BaseButton>
      </div>
    </header>

    <!-- Cards de Métricas e Indicadores -->
    <section data-tour="tarefas-mes-metricas" class="grid grid-cols-[repeat(auto-fit,minmax(210px,1fr))] gap-4" aria-label="Métricas de Tarefas do Mês">
      <div data-tour="tarefas-mes-metrica-card" :class="[classesMetricaCard, 'border-border bg-card hover:border-border-strong']">
        <div :class="[classesMetricaIcone, 'bg-blue-500/15 text-blue-500']">
          <i class="fa-solid fa-list-check" aria-hidden="true"></i>
        </div>
        <div class="flex flex-col">
          <span :class="classesMetricaLabel">Total Lançadas</span>
          <span :class="[classesMetricaValor, 'text-foreground']">{{ dados.total }}</span>
        </div>
      </div>

      <div data-tour="tarefas-mes-metrica-card" :class="[classesMetricaCard, 'border-green-500/35 bg-linear-135 from-card to-green-500/5']">
        <div :class="[classesMetricaIcone, 'bg-green-500/15 text-green-500']">
          <i class="fa-solid fa-unlock-keyhole" aria-hidden="true"></i>
        </div>
        <div class="flex flex-col">
          <span :class="classesMetricaLabel">Disponíveis p/ Ajuste</span>
          <span :class="[classesMetricaValor, 'text-green-500']">{{ dados.total }}</span>
          <span :class="classesMetricaHint">Seleção e edição livre</span>
        </div>
      </div>

      <div data-tour="tarefas-mes-metrica-card" :class="[classesMetricaCard, 'border-border bg-card hover:border-border-strong']">
        <div :class="[classesMetricaIcone, 'bg-slate-400/15 text-muted-foreground']">
          <i class="fa-solid fa-check-double" aria-hidden="true"></i>
        </div>
        <div class="flex flex-col">
          <span :class="classesMetricaLabel">Concluídas no Munka</span>
          <span :class="[classesMetricaValor, 'text-foreground']">{{ dados.concluidas }}</span>
          <span :class="classesMetricaHint">Aprovadas no portal</span>
        </div>
      </div>

      <div data-tour="tarefas-mes-metrica-card" :class="[classesMetricaCard, selecionadasCount > 0 ? 'border-primary bg-linear-135 from-card to-primary-glow' : 'border-border bg-card hover:border-border-strong']">
        <div :class="[classesMetricaIcone, 'bg-primary-glow text-primary']">
          <i class="fa-solid fa-square-check" aria-hidden="true"></i>
        </div>
        <div class="flex flex-col">
          <span :class="classesMetricaLabel">Selecionadas</span>
          <div class="flex items-center gap-2">
            <span :class="[classesMetricaValor, 'text-primary']">{{ selecionadasCount }}</span>
            <button
              v-if="selecionadasCount > 0"
              type="button"
              class="cursor-pointer rounded border-0 bg-transparent px-1.5 py-0.5 text-xs text-muted-foreground no-underline transition-colors duration-150 hover:bg-primary-glow hover:text-foreground hover:no-underline"
              @click="limparSelecao"
            >
              Limpar
            </button>
          </div>
          <span v-if="selecionadasCount > 0" :class="classesMetricaHint">Prontas para ajuste em lote</span>
        </div>
      </div>
    </section>

    <!-- Barra de Ações de Lote Flutuante / Topo quando há selecionadas -->
    <div v-if="selecionadasCount > 0" data-tour="tarefas-mes-acao-lote" class="flex animate-fade-in items-center justify-between gap-4 rounded-[10px] border border-primary bg-primary-glow px-5 py-3" role="toolbar" aria-label="Ações para itens selecionados">
      <div class="flex items-center gap-2.5 text-sm text-foreground [&_i]:text-lg [&_i]:text-primary">
        <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
        <span><strong>{{ selecionadasCount }}</strong> tarefa{{ selecionadasCount > 1 ? 's' : '' }} selecionada{{ selecionadasCount > 1 ? 's' : '' }}</span>
      </div>
      <div class="flex items-center gap-3">
        <BaseButton variant="primary" @click="abrirModalAjusteLote">
          <i class="fa-solid fa-sliders" aria-hidden="true"></i>
          <span>Ajustar {{ selecionadasCount }} Selecionada{{ selecionadasCount > 1 ? 's' : '' }} em Lote</span>
        </BaseButton>
        <BaseButton size="sm" @click="limparSelecao">
          Cancelar Seleção
        </BaseButton>
      </div>
    </div>

    <!-- Barra de Filtros e Busca -->
    <FiltersBar data-tour="tarefas-mes-filtros">
      <SearchBox
        v-model="filtroTexto"
        placeholder="Buscar por título, autor, SHA de commit ou código..."
        aria-label="Buscar tarefas"
      />

      <div class="flex h-9.5 flex-wrap items-center gap-1.5 rounded-lg border border-border bg-card px-1 py-0.5" role="radiogroup" aria-label="Filtrar por status">
        <button
          type="button"
          :class="[classesPill, filtroStatus === 'todos' ? classesPillAtiva.todos : classesPillInativa]"
          @click="filtroStatus = 'todos'"
        >
          Todas ({{ tarefasFiltradasPorTexto.length }})
        </button>
        <button
          type="button"
          :class="[classesPill, filtroStatus === 'abertas' ? classesPillAtiva.abertas : classesPillInativa]"
          @click="filtroStatus = 'abertas'"
        >
          <i class="fa-solid fa-spinner" aria-hidden="true"></i>
          <span>Em Aberto ({{ contagemAbertas }})</span>
        </button>
        <button
          type="button"
          :class="[classesPill, filtroStatus === 'concluidas' ? classesPillAtiva.concluidas : classesPillInativa]"
          @click="filtroStatus = 'concluidas'"
        >
          <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
          <span>Concluídas ({{ contagemConcluidas }})</span>
        </button>
      </div>

      <div class="flex w-full flex-wrap items-end gap-3 border-t border-border pt-3.5" role="group" aria-label="Filtros por coluna">
        <label :class="[classesFiltroItem, 'min-w-40']">
          <span :class="classesFiltroLabel">Regra</span>
          <MultiSelectFiltro
            v-model="filtroRegra"
            :opcoes="opcoesRegra.map(r => ({ valor: r, rotulo: r }))"
            placeholder="Todas"
            aria-label="Filtrar por regra"
          />
        </label>

        <label :class="[classesFiltroItem, 'min-w-55 flex-1']">
          <span :class="classesFiltroLabel">Nome da atividade</span>
          <BaseInput
            v-model="filtroAtividade"
            type="text"
            placeholder="Contém..."
            aria-label="Filtrar por nome da atividade"
          />
        </label>

        <label :class="[classesFiltroItem, 'min-w-40']">
          <span :class="classesFiltroLabel">Status no portal</span>
          <MultiSelectFiltro
            v-model="filtroStatusPortal"
            :opcoes="opcoesStatusPortal.map(s => ({ valor: s.valor, rotulo: `${s.rotulo} (${s.total})` }))"
            placeholder="Todos"
            aria-label="Filtrar por status no portal"
          />
        </label>

        <label :class="[classesFiltroItem, 'min-w-40']">
          <span :class="classesFiltroLabel">Condição supervisor</span>
          <BaseSelect v-model="filtroStatus" aria-label="Filtrar por condição do supervisor">
            <option value="todos">Todas</option>
            <option value="abertas">Em Aberto</option>
            <option value="concluidas">Concluídas</option>
          </BaseSelect>
        </label>

        <BaseButton
          v-if="filtrosAtivos"
          class="h-9"
          @click="resetarFiltros"
        >
          <i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i>
          <span>Limpar filtros</span>
        </BaseButton>
      </div>

      <div v-if="chipsAtivos.length" class="flex w-full flex-wrap items-center gap-2" aria-label="Filtros ativos">
        <button
          v-for="c in chipsAtivos"
          :key="c.chave"
          type="button"
          class="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-primary bg-primary-glow px-2.5 py-0.5 text-xs font-bold text-primary hover:opacity-80"
          :aria-label="`Remover filtro ${c.rotulo}`"
          @click="c.remover()"
        >
          <span>{{ c.rotulo }}</span>
          <i class="fa-solid fa-xmark" aria-hidden="true"></i>
        </button>
      </div>
    </FiltersBar>

    <!-- Estado de Carregamento -->
    <StateMessage v-if="loading && dados.tarefas.length === 0" type="loading" role="status" aria-live="polite">
      <i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
      <span>Carregando tarefas do mês...</span>
    </StateMessage>

    <!-- Estado Vazio -->
    <div v-else-if="tarefasExibidas.length === 0" class="flex flex-col items-center justify-center rounded-[14px] border border-dashed border-border bg-card px-6 py-12 text-center" role="status">
      <div class="mb-4 flex size-15 items-center justify-center rounded-full bg-slate-400/10 text-[1.75rem] text-muted-foreground">
        <i class="fa-solid fa-calendar-xmark" aria-hidden="true"></i>
      </div>
      <h3 class="text-[1.17em] font-bold">Nenhuma tarefa encontrada</h3>
      <p v-if="filtrosAtivos">
        Nenhuma tarefa corresponde aos filtros aplicados. Tente ajustar os termos de pesquisa.
      </p>
      <p v-else>
        Não foram encontrados lançamentos no mês de <strong>{{ meses[mesAtual - 1] }} de {{ anoAtual }}</strong>.
      </p>
      <div class="mt-5 flex gap-3">
        <BaseButton v-if="filtrosAtivos" @click="resetarFiltros">
          Limpar Filtros
        </BaseButton>
        <BaseButton variant="primary" @click="sincronizarComMunka">
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
          <span>Sincronizar com o Portal Munka</span>
        </BaseButton>
      </div>
    </div>

    <!-- Tabela de Tarefas -->
    <div v-else class="overflow-x-auto rounded-xl border border-border bg-card">
      <table
        class="w-full border-collapse text-left text-sm [&_td]:border-b [&_td]:border-border-strong [&_td]:px-4 [&_td]:py-3.5 [&_td]:align-middle [&_td]:text-foreground [&_th]:border-b [&_th]:border-border [&_th]:bg-muted [&_th]:px-4 [&_th]:py-3.5 [&_th]:text-xs [&_th]:font-bold [&_th]:tracking-wider [&_th]:text-muted-foreground [&_th]:uppercase [&>tbody>tr:last-child>td]:border-b-0"
        aria-label="Tabela de tarefas do mês"
      >
        <thead>
          <tr>
            <th class="w-10 text-center">
              <input
                type="checkbox"
                :class="classesCheckbox"
                :checked="todosSelecionados"
                :disabled="tarefasExibidas.length === 0"
                :title="todosSelecionados ? 'Desmarcar todas' : 'Selecionar todas as tarefas visíveis'"
                aria-label="Selecionar todas as tarefas"
                @change="toggleSelecionarTodas"
              />
            </th>
            <th class="w-27.5">ID Munka</th>
            <th class="min-w-65">Atividade & Commit</th>
            <th class="w-32.5">Regra / HPA</th>
            <th class="min-w-37.5">Status no Portal</th>
            <th class="w-40">Condição Supervisor</th>
            <th class="w-25 text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="t in tarefasExibidas"
            :key="t.id"
            :class="isSelecionada(t.id) ? 'bg-primary-glow' : 'hover:bg-slate-400/4'"
          >
            <!-- Checkbox de Seleção -->
            <td class="text-center">
              <input
                type="checkbox"
                :class="classesCheckbox"
                :checked="isSelecionada(t.id)"
                :title="isSelecionada(t.id) ? 'Desmarcar tarefa' : 'Selecionar tarefa para ajuste'"
                :aria-label="`Selecionar tarefa ${t.titulo}`"
                @change="toggleSelecao(t.id)"
              />
            </td>

            <!-- ID Munka com Link -->
            <td>
              <a
                v-if="t.task_id"
                :href="t.task_url || '#'"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 rounded bg-primary-glow px-1.5 py-0.5 text-sm font-bold text-primary no-underline hover:bg-primary hover:text-white hover:no-underline"
                title="Abrir tarefa no portal Munka"
              >
                <span>#{{ t.task_id }}</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[0.65rem] opacity-80" aria-hidden="true"></i>
              </a>
              <span v-else class="text-sm text-muted-foreground" title="ID não registrado no lançamento">
                —
              </span>
            </td>

            <!-- Título & Commit -->
            <td>
              <div class="flex flex-col gap-1">
                <span class="leading-snug font-semibold text-foreground" :title="t.titulo">
                  {{ t.titulo }}
                </span>
                <div class="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <router-link
                    v-if="t.commit_id"
                    :to="`/commits/${t.commit_id}`"
                    class="inline-flex items-center gap-1 rounded border border-border-strong bg-muted px-1.5 py-px font-mono text-xs text-primary no-underline hover:border-primary"
                    :title="`Ver commit ${t.commit_id}`"
                  >
                    <i class="fa-solid fa-code-commit" aria-hidden="true"></i>
                    <span>{{ t.commit_id.slice(0, 8) }}</span>
                  </router-link>
                  <span v-if="t.commit_autor" :class="classesMetaCommit" :title="t.commit_autor">
                    <i class="fa-regular fa-user" aria-hidden="true"></i>
                    <span>{{ t.commit_autor }}</span>
                  </span>
                  <span v-if="t.commit_mensagem" :class="classesMetaCommit" :title="t.commit_mensagem">
                    "{{ t.commit_mensagem }}"
                  </span>
                </div>
              </div>
            </td>

            <!-- Regra / HPA -->
            <td>
              <div class="flex items-center gap-1.5">
                <span class="inline-block rounded-md px-1.5 py-0.5 text-xs leading-none font-bold tracking-[0.03em] uppercase"><code>{{ t.codigo || '—' }}</code></span>
                <span class="rounded border border-border-strong bg-slate-400/15 px-1.5 py-0.5 text-xs font-bold text-foreground">{{ t.hpa }}h</span>
              </div>
            </td>

            <!-- Status no Munka -->
            <td>
              <div class="flex flex-col items-start gap-1">
                <BaseBadge :variant="obterClasseBadgeStatus(t.status_munka || t.status)">
                  <span class="mr-1 inline-block size-1.5 rounded-full bg-current"></span>
                  <span>{{ t.status_munka || t.status }}</span>
                </BaseBadge>
                <span v-if="t.munka_atualizado_em" class="flex items-center gap-1 text-xs text-muted-foreground" :title="`Última checagem no Munka: ${formatarDataHora(t.munka_atualizado_em)}`">
                  <i class="fa-regular fa-clock" aria-hidden="true"></i>
                  <span>{{ obterTempoRelativo(t.munka_atualizado_em) }}</span>
                </span>
              </div>
            </td>

            <!-- Condição do Supervisor / Status -->
            <td>
              <span
                v-if="isTarefaConcluida(t)"
                :class="[classesCondicao, 'border-border-strong bg-slate-400/12 text-muted-foreground']"
                title="Tarefa concluída no Munka. Seleção e edições continuam liberadas a qualquer momento."
              >
                <i class="fa-solid fa-check-double" aria-hidden="true"></i>
                <span>Concluída</span>
              </span>
              <span
                v-else
                :class="[classesCondicao, 'border-green-500/30 bg-green-500/15 text-green-500']"
                title="Tarefa em andamento no Munka. Disponível para ajuste."
              >
                <i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>
                <span>Em Aberto</span>
              </span>
            </td>

            <!-- Ações -->
            <td class="text-right">
              <button
                type="button"
                class="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-border-strong bg-muted px-3 py-1.5 text-xs font-semibold text-foreground transition-all duration-150 enabled:hover:border-primary enabled:hover:bg-primary-glow enabled:hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
                title="Ajustar campos desta tarefa no Munka"
                @click="abrirModalAjusteSingle(t)"
              >
                <i class="fa-solid fa-sliders" aria-hidden="true"></i>
                <span>Ajustar</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Ajuste Individual -->
    <div v-if="modalAjusteSingleAberto" :class="classesOverlay" @click.self="fecharModalSingle">
      <div :class="classesModal" role="dialog" aria-modal="true" aria-labelledby="modal-single-title">
        <header :class="classesModalHeader">
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-3">
              <i class="fa-solid fa-pen-to-square text-xl text-primary" aria-hidden="true"></i>
              <h2 id="modal-single-title" :class="classesModalTitulo">Ajustar Tarefa no Munka</h2>
              <span :class="classesModalContador">{{ tarefaAlvoSingle?.task_id ? `#${tarefaAlvoSingle.task_id}` : '(Busca pelo título)' }}</span>
            </div>
            <span class="text-sm text-muted-foreground">
              Modifique os campos desejados desta tarefa individualmente.
            </span>
          </div>
          <button type="button" :class="classesModalFechar" @click="fecharModalSingle" aria-label="Fechar modal">×</button>
        </header>

        <form @submit.prevent="salvarAjusteSingle">
          <div :class="classesModalCorpo">
            <div class="mb-6 flex items-center justify-between gap-4 rounded-[10px] border border-border-strong bg-muted px-5 py-3.5">
              <span class="text-base font-bold text-foreground">{{ tarefaAlvoSingle?.titulo }}</span>
              <BaseBadge :variant="obterClasseBadgeStatus(tarefaAlvoSingle?.status_munka || tarefaAlvoSingle?.status)">
                {{ tarefaAlvoSingle?.status_munka || tarefaAlvoSingle?.status }}
              </BaseBadge>
            </div>

            <div class="grid grid-cols-2 gap-5 max-md:grid-cols-1">
              <!-- Status -->
              <div :class="classesFormGrupo">
                <label for="single_status" :class="classesFormLabel"><i class="fa-solid fa-tag"></i> Status</label>
                <BaseSelect id="single_status" v-model="formSingle.status_id" :class="classesCampo">
                  <option v-for="st in CATALOGO_STATUS" :key="st.id" :value="st.id">{{ st.rotulo }} ({{ st.id }})</option>
                </BaseSelect>
              </div>

              <!-- Perfil do Profissional (Cargo) -->
              <div :class="classesFormGrupo">
                <label for="single_cargo" :class="classesFormLabel"><i class="fa-solid fa-user-tie"></i> Perfil do Profissional (Cargo)</label>
                <BaseSelect id="single_cargo" v-model="formSingle.cargo" :class="classesCampo">
                  <option value="9">Desenvolvedor (9)</option>
                  <option value="11">Analista de Sistemas (11)</option>
                  <option value="12">Arquiteto de Software (12)</option>
                  <option value="16">Analista de Testes (16)</option>
                </BaseSelect>
              </div>

              <!-- Nível -->
              <div :class="classesFormGrupo">
                <label for="single_nivel" :class="classesFormLabel"><i class="fa-solid fa-layer-group"></i> Nível</label>
                <BaseSelect id="single_nivel" v-model="formSingle.nivel" :class="classesCampo">
                  <option value="1">Júnior (1)</option>
                  <option value="2">Pleno (2)</option>
                  <option value="3">Sênior (3)</option>
                  <option value="4">Único (4)</option>
                </BaseSelect>
              </div>

              <!-- Tipo -->
              <div :class="classesFormGrupo">
                <label for="single_tipo" :class="classesFormLabel"><i class="fa-solid fa-shapes"></i> Tipo</label>
                <BaseInput
                  id="single_tipo"
                  v-model="formSingle.tipo"
                  placeholder="projeto"
                  :class="classesCampo" />
              </div>

              <!-- Responsável -->
              <div :class="[classesFormGrupo, 'col-span-2 max-md:col-span-1']">
                <label for="single_responsavel" :class="classesFormLabel"><i class="fa-solid fa-id-card-clip"></i> Responsável</label>
                <BaseInput
                  id="single_responsavel"
                  v-model="formSingle.responsavel"
                  placeholder="Nome do responsável no Munka (busca Select2)"
                  :class="classesCampo" />
              </div>

              <!-- Produto -->
              <div :class="classesFormGrupo">
                <label for="single_produto" :class="classesFormLabel"><i class="fa-solid fa-box-archive"></i> Produto</label>
                <BaseInput
                  id="single_produto"
                  v-model="formSingle.produto"
                  placeholder="Ex: [DESENV] MUNKA"
                  :class="classesCampo" />
              </div>

              <!-- Projeto -->
              <div :class="classesFormGrupo">
                <label for="single_projeto" :class="classesFormLabel"><i class="fa-solid fa-diagram-project"></i> Projeto</label>
                <BaseInput
                  id="single_projeto"
                  v-model="formSingle.projeto"
                  placeholder="Ex: MUNKA Multicontrato"
                  :class="classesCampo" />
              </div>
            </div>
          </div>

          <footer :class="classesModalRodape">
            <div class="text-sm font-semibold">
              <span>Campos aplicados apenas nesta tarefa</span>
            </div>
            <div class="flex items-center gap-3">
              <BaseButton @click="fecharModalSingle" :disabled="salvando">
                Cancelar
              </BaseButton>
              <BaseButton type="submit" variant="primary" :disabled="salvando">
                <i v-if="salvando" class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
                <i v-else class="fa-solid fa-check" aria-hidden="true"></i>
                <span>{{ salvando ? 'Enfileirando...' : 'Salvar Alterações' }}</span>
              </BaseButton>
            </div>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal de Ajuste em Lote (Múltiplas Selecionadas) -->
    <div v-if="modalAjusteLoteAberto" :class="classesOverlay" @click.self="fecharModalLote">
      <div :class="classesModal" role="dialog" aria-modal="true" aria-labelledby="modal-lote-title">
        <header :class="classesModalHeader">
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-3">
              <i class="fa-solid fa-sliders text-xl text-primary" aria-hidden="true"></i>
              <h2 id="modal-lote-title" :class="classesModalTitulo">Ajuste em Lote de Tarefas</h2>
              <span :class="classesModalContador">{{ selecionadasCount }} selecionadas</span>
            </div>
            <span class="text-sm text-muted-foreground">
              Escolha quais campos deseja sobrescrever em lote nas tarefas selecionadas.
            </span>
          </div>
          <button type="button" :class="classesModalFechar" @click="fecharModalLote" aria-label="Fechar modal">×</button>
        </header>

        <form @submit.prevent="salvarAjusteLote">
          <div :class="classesModalCorpo">
            <div class="mb-5 flex items-center gap-3 rounded-[10px] border border-blue-500/25 bg-blue-500/10 px-5 py-3 text-sm text-foreground [&_i]:shrink-0 [&_i]:text-lg [&_i]:text-primary [&_span]:ml-1 [&_span]:text-sm [&_span]:text-muted-foreground">
              <i class="fa-solid fa-circle-info" aria-hidden="true"></i>
              <div>
                <strong>Instrução de edição em lote:</strong>
                <span>Marque a caixa de cada campo que deseja modificar. Campos desmarcados manterão os valores já existentes no Munka.</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4.5 max-[720px]:grid-cols-1">
              <!-- Status -->
              <div :class="classeLoteCard(habilitarCampo.status)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.status = !habilitarCampo.status">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.status" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-tag"></i> Status</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.status)">
                    <i v-if="habilitarCampo.status" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.status ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseSelect v-model="formLote.status_id" :disabled="!habilitarCampo.status" :class="classesCampo">
                    <option v-for="st in CATALOGO_STATUS" :key="st.id" :value="st.id">{{ st.rotulo }} ({{ st.id }})</option>
                  </BaseSelect>
                </div>
              </div>

              <!-- Cargo (Perfil do Profissional) -->
              <div :class="classeLoteCard(habilitarCampo.cargo)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.cargo = !habilitarCampo.cargo">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.cargo" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-user-tie"></i> Perfil / Cargo</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.cargo)">
                    <i v-if="habilitarCampo.cargo" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.cargo ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseSelect v-model="formLote.cargo" :disabled="!habilitarCampo.cargo" :class="classesCampo">
                    <option value="9">Desenvolvedor (9)</option>
                    <option value="11">Analista de Sistemas (11)</option>
                    <option value="12">Arquiteto de Software (12)</option>
                    <option value="16">Analista de Testes (16)</option>
                  </BaseSelect>
                </div>
              </div>

              <!-- Nível -->
              <div :class="classeLoteCard(habilitarCampo.nivel)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.nivel = !habilitarCampo.nivel">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.nivel" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-layer-group"></i> Nível</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.nivel)">
                    <i v-if="habilitarCampo.nivel" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.nivel ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseSelect v-model="formLote.nivel" :disabled="!habilitarCampo.nivel" :class="classesCampo">
                    <option value="1">Júnior (1)</option>
                    <option value="2">Pleno (2)</option>
                    <option value="3">Sênior (3)</option>
                    <option value="4">Único (4)</option>
                  </BaseSelect>
                </div>
              </div>

              <!-- Responsável -->
              <div :class="classeLoteCard(habilitarCampo.responsavel)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.responsavel = !habilitarCampo.responsavel">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.responsavel" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-id-card-clip"></i> Responsável</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.responsavel)">
                    <i v-if="habilitarCampo.responsavel" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.responsavel ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseInput
                    v-model="formLote.responsavel"
                    :disabled="!habilitarCampo.responsavel"
                    placeholder="Nome do responsável no Munka"
                    :class="classesCampo" />
                </div>
              </div>

              <!-- Tipo -->
              <div :class="classeLoteCard(habilitarCampo.tipo)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.tipo = !habilitarCampo.tipo">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.tipo" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-shapes"></i> Tipo</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.tipo)">
                    <i v-if="habilitarCampo.tipo" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.tipo ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseInput
                    v-model="formLote.tipo"
                    :disabled="!habilitarCampo.tipo"
                    placeholder="projeto"
                    :class="classesCampo" />
                </div>
              </div>

              <!-- Produto -->
              <div :class="classeLoteCard(habilitarCampo.produto)">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.produto = !habilitarCampo.produto">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.produto" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-box-archive"></i> Produto</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.produto)">
                    <i v-if="habilitarCampo.produto" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.produto ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseInput
                    v-model="formLote.produto"
                    :disabled="!habilitarCampo.produto"
                    placeholder="Ex: [DESENV] MUNKA"
                    :class="classesCampo" />
                </div>
              </div>

              <!-- Projeto -->
              <div :class="[classeLoteCard(habilitarCampo.projeto), 'col-span-2 max-[720px]:col-span-1']">
                <div :class="classesLoteCabecalho" @click="habilitarCampo.projeto = !habilitarCampo.projeto">
                  <label :class="classesLoteToggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.projeto" :class="classesCheckbox" />
                    <span :class="classesLoteNome"><i class="fa-solid fa-diagram-project"></i> Projeto</span>
                  </label>
                  <span :class="classeLoteIndicador(habilitarCampo.projeto)">
                    <i v-if="habilitarCampo.projeto" class="fa-solid fa-check mr-1" aria-hidden="true"></i>
                    <span>{{ habilitarCampo.projeto ? 'Sobrescrever' : 'Manter original' }}</span>
                  </span>
                </div>
                <div class="w-full">
                  <BaseInput
                    v-model="formLote.projeto"
                    :disabled="!habilitarCampo.projeto"
                    placeholder="Ex: MUNKA Multicontrato"
                    :class="classesCampo" />
                </div>
              </div>
            </div>
          </div>

          <!-- Sticky Footer -->
          <footer :class="classesModalRodape">
            <div class="text-sm font-semibold">
              <span v-if="totalCamposHabilitados === 0" class="flex items-center gap-1.5 text-warning">
                <i class="fa-solid fa-triangle-exclamation"></i> Marque ao menos um campo acima
              </span>
              <span v-else class="flex items-center gap-1.5 text-success">
                <i class="fa-solid fa-check"></i> {{ totalCamposHabilitados }} campo(s) serão aplicados em {{ selecionadasCount }} tarefa(s)
              </span>
            </div>
            <div class="flex items-center gap-3">
              <BaseButton @click="fecharModalLote" :disabled="salvando">
                Cancelar
              </BaseButton>
              <BaseButton
                type="submit"
                variant="primary"
                :disabled="salvando || totalCamposHabilitados === 0"
              >
                <i v-if="salvando" class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
                <i v-else class="fa-solid fa-check-double" aria-hidden="true"></i>
                <span>{{ salvando ? 'Enfileirando...' : `Aplicar em ${selecionadasCount} Tarefas` }}</span>
              </BaseButton>
            </div>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type TarefaMesItem, type TarefasMesResponse, type Config } from '../api'
import { useToastStore } from '../stores/toast'
import { useFilaStore } from '../stores/fila'
import { useTarefasMesStore } from '../stores/tarefasMes'
import { storeToRefs } from 'pinia'
import TutorialModal from '../components/TutorialModal.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import MultiSelectFiltro from '../components/ui/MultiSelectFiltro.vue'
import FiltersBar from '../components/ui/FiltersBar.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import SearchBox from '../components/ui/SearchBox.vue'
import StateMessage from '../components/ui/StateMessage.vue'
import { CATALOGO_STATUS, resolverStatus, rotuloStatus, isStatusConcluido, classeBadgeStatus, type VarianteBadgeStatus } from '../config/statusMunka'

// Classes Tailwind reutilizadas no template (strings completas para o Tailwind detectar).
const classesNavMes = 'cursor-pointer rounded-md border-0 bg-transparent px-2.5 py-1.5 text-muted-foreground transition-all duration-150 hover:bg-slate-400/15 hover:text-foreground'
const classesMetricaCard = 'flex items-center gap-4 rounded-xl border px-5 py-4 transition-all duration-150 hover:-translate-y-0.5'
const classesMetricaIcone = 'flex size-11 shrink-0 items-center justify-center rounded-[10px] text-lg'
const classesMetricaLabel = 'text-xs font-bold tracking-wider text-muted-foreground uppercase'
const classesMetricaValor = 'text-2xl leading-tight font-extrabold'
const classesMetricaHint = 'mt-0.5 text-xs text-muted-foreground'

const classesPill = 'inline-flex h-8 cursor-pointer items-center gap-[0.45rem] rounded-md px-3 text-sm transition-all duration-200 select-none'
const classesPillInativa = 'border-0 bg-transparent font-semibold text-muted-foreground hover:bg-slate-400/10 hover:text-foreground'
const classesPillAtiva = {
  todos: 'border border-border-strong bg-muted font-bold text-foreground',
  abertas: 'border border-green-500 bg-green-500/15 font-bold text-green-500',
  concluidas: 'border border-border-strong bg-slate-400/20 font-bold text-foreground'
}

const classesFiltroLabel = 'text-xs font-bold tracking-wider text-muted-foreground uppercase'
const classesFiltroItem = 'mb-[0.35rem] flex flex-col gap-1'
const classesCheckbox = 'size-4 cursor-pointer accent-primary disabled:cursor-not-allowed'
const classesMetaCommit = 'inline-flex max-w-80 items-center gap-1 overflow-hidden text-ellipsis whitespace-nowrap'
const classesCondicao = 'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-bold'

const classesOverlay = 'fixed inset-0 z-1000 flex animate-fade-in items-center justify-center bg-black/70 p-4 backdrop-blur-[6px]'
const classesModal = 'flex max-h-[90vh] w-215 max-w-[95vw] animate-scale-in flex-col overflow-hidden rounded-2xl border border-border-strong bg-card text-foreground shadow-[0_20px_60px] shadow-black/50'
const classesModalHeader = 'flex shrink-0 items-center justify-between border-b border-border-strong bg-card px-7 py-5'
const classesModalTitulo = 'mb-1 text-xl leading-tight font-extrabold text-foreground'
const classesModalContador = 'rounded-full border border-primary bg-primary-glow px-2 py-0.5 text-xs font-bold text-primary'
const classesModalFechar = 'cursor-pointer rounded border-0 bg-transparent px-1 py-0 text-[1.6rem] leading-none text-muted-foreground transition-colors duration-150 hover:text-foreground'
const classesModalCorpo = 'max-h-[calc(90vh-145px)] flex-1 overflow-y-auto px-7 py-6'
const classesModalRodape = 'flex shrink-0 items-center justify-between gap-4 border-t border-border-strong bg-card px-7 py-4.5'

const classesFormGrupo = 'flex flex-col gap-2'
const classesFormLabel = 'mb-[0.35rem] flex items-center gap-1.5 text-xs leading-[1.4] font-bold tracking-wide text-muted-foreground uppercase [&_i]:text-primary'
const classesCampo = 'font-medium disabled:cursor-not-allowed disabled:border-slate-400/15 disabled:bg-slate-400/5 disabled:opacity-45'

const classesLoteCardBase = 'flex flex-col gap-2.5 rounded-xl border px-4.5 py-4 transition-all duration-150'
const classesLoteCabecalho = 'flex cursor-pointer items-center justify-between select-none'
const classesLoteToggle = 'mb-[0.35rem] flex cursor-pointer items-center gap-2.5 text-sm leading-[1.4] font-bold tracking-[0.05em] text-foreground uppercase'
const classesLoteNome = 'inline-flex items-center gap-1.5 [&_i]:text-sm [&_i]:text-primary'

function classeLoteCard(ativo: boolean): string {
  return `${classesLoteCardBase} ${ativo
    ? 'border-primary bg-primary-glow shadow-[0_0_12px] shadow-blue-500/15'
    : 'border-border-strong bg-muted hover:border-primary-light'}`
}

function classeLoteIndicador(ativo: boolean): string {
  return `rounded-full border px-2 py-0.5 text-xs font-semibold transition-all duration-150 ${ativo
    ? 'border-primary bg-blue-500/15 text-primary'
    : 'border-border-strong bg-card text-muted-foreground'}`
}

const meses = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const tarefasMesStore = useTarefasMesStore()
const { mes: mesAtual, ano: anoAtual } = storeToRefs(tarefasMesStore)

const isMesAtual = computed(() => {
  const d = new Date()
  return mesAtual.value === (d.getMonth() + 1) && anoAtual.value === d.getFullYear()
})

const toastStore = useToastStore()
const filaStore = useFilaStore()

const loading = ref<boolean>(false)
const sincronizando = ref<boolean>(false)
const salvando = ref<boolean>(false)

const dados = ref<TarefasMesResponse>({
  mes: mesAtual.value,
  ano: anoAtual.value,
  total: 0,
  editaveis: 0,
  concluidas: 0,
  tarefas: []
})

// Filtros locais
const filtroTexto = ref<string>('')
const filtroStatus = ref<'todos' | 'abertas' | 'concluidas'>('todos')
const filtroRegra = ref<string[]>([])
const filtroAtividade = ref<string>('')
const filtroStatusPortal = ref<string[]>([])

// Filtros persistidos na query da URL (?q=&cond=&regra=21a,22b&portal=homologacao&atividade=)
const route = useRoute()
const router = useRouter()
const listaDaQuery = (v: unknown): string[] =>
  (typeof v === 'string' ? v : '').split(',').map(x => x.trim()).filter(Boolean)

function lerFiltrosDaUrl() {
  const q = route.query
  filtroTexto.value = typeof q.q === 'string' ? q.q : ''
  filtroAtividade.value = typeof q.atividade === 'string' ? q.atividade : ''
  filtroRegra.value = listaDaQuery(q.regra)
  filtroStatusPortal.value = listaDaQuery(q.portal)
  filtroStatus.value = q.cond === 'abertas' || q.cond === 'concluidas' ? q.cond : 'todos'
}
lerFiltrosDaUrl()

function gravarFiltrosNaUrl() {
  const novos: Record<string, string> = {}
  if (filtroTexto.value.trim()) novos.q = filtroTexto.value.trim()
  if (filtroAtividade.value.trim()) novos.atividade = filtroAtividade.value.trim()
  if (filtroRegra.value.length) novos.regra = filtroRegra.value.join(',')
  if (filtroStatusPortal.value.length) novos.portal = filtroStatusPortal.value.join(',')
  if (filtroStatus.value !== 'todos') novos.cond = filtroStatus.value
  const base = { ...route.query }
  for (const k of ['q', 'atividade', 'regra', 'portal', 'cond']) delete base[k]
  router.replace({ query: { ...base, ...novos } })
}
watch([filtroTexto, filtroAtividade, filtroRegra, filtroStatusPortal, filtroStatus], gravarFiltrosNaUrl, { deep: true })

const filtrosAtivos = computed(() =>
  !!filtroTexto.value ||
  filtroStatus.value !== 'todos' ||
  filtroRegra.value.length > 0 ||
  !!filtroAtividade.value.trim() ||
  filtroStatusPortal.value.length > 0
)

const chipsAtivos = computed(() => {
  const chips: { chave: string; rotulo: string; remover: () => void }[] = []
  if (filtroTexto.value.trim()) {
    chips.push({ chave: 'q', rotulo: `Busca: ${filtroTexto.value.trim()}`, remover: () => { filtroTexto.value = '' } })
  }
  for (const r of filtroRegra.value) {
    chips.push({ chave: `r-${r}`, rotulo: `Regra: ${r}`, remover: () => { filtroRegra.value = filtroRegra.value.filter(x => x !== r) } })
  }
  if (filtroAtividade.value.trim()) {
    chips.push({ chave: 'a', rotulo: `Atividade: ${filtroAtividade.value.trim()}`, remover: () => { filtroAtividade.value = '' } })
  }
  for (const p of filtroStatusPortal.value) {
    const rotulo = opcoesStatusPortal.value.find(o => o.valor === p)?.rotulo ?? p
    chips.push({ chave: `p-${p}`, rotulo: `Portal: ${rotulo}`, remover: () => { filtroStatusPortal.value = filtroStatusPortal.value.filter(x => x !== p) } })
  }
  if (filtroStatus.value !== 'todos') {
    chips.push({ chave: 'c', rotulo: `Condição: ${filtroStatus.value === 'abertas' ? 'Em aberto' : 'Concluídas'}`, remover: () => { filtroStatus.value = 'todos' } })
  }
  return chips
})

// Seleção de itens
const selecionadosIds = ref<number[]>([])

const configPadrao = ref<Partial<Config>>({})

// Modais
const modalAjusteSingleAberto = ref<boolean>(false)
const tarefaAlvoSingle = ref<TarefaMesItem | null>(null)
const formSingle = reactive({
  cargo: '9',
  nivel: '3',
  responsavel: '',
  tipo: 'projeto',
  produto: '[DESENV] MUNKA',
  projeto: 'MUNKA Multicontrato',
  status_id: '20'
})

const modalAjusteLoteAberto = ref<boolean>(false)
const habilitarCampo = reactive({
  cargo: false,
  nivel: false,
  responsavel: false,
  tipo: false,
  produto: false,
  projeto: false,
  status: false
})

const formLote = reactive({
  cargo: '9',
  nivel: '3',
  responsavel: '',
  tipo: 'projeto',
  produto: '[DESENV] MUNKA',
  projeto: 'MUNKA Multicontrato',
  status_id: '20'
})

const totalCamposHabilitados = computed(() => {
  return Object.values(habilitarCampo).filter(Boolean).length
})

function isTarefaConcluida(t: TarefaMesItem): boolean {
  return isStatusConcluido(t.status_munka || t.status)
}

function statusPortalDe(t: TarefaMesItem): string {
  return t.status_munka || t.status || ''
}

// Valor do filtro: ID do catálogo quando reconhecido; texto cru caso contrário.
function chaveStatusPortal(t: TarefaMesItem): string {
  const texto = statusPortalDe(t)
  return resolverStatus(texto)?.id ?? texto
}

const opcoesRegra = computed(() =>
  [...new Set(dados.value.tarefas.map(t => t.codigo).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
)

// Catálogo completo (mesmo sem tarefas) + status desconhecidos vindos do portal.
const opcoesStatusPortal = computed(() => {
  const contagem = new Map<string, number>()
  for (const t of dados.value.tarefas) {
    const k = chaveStatusPortal(t)
    if (k) contagem.set(k, (contagem.get(k) || 0) + 1)
  }
  const catalogo = CATALOGO_STATUS.map(s => ({
    valor: s.id,
    rotulo: s.rotulo,
    total: contagem.get(s.id) || 0
  }))
  const ids = new Set(CATALOGO_STATUS.map(s => s.id))
  const extras = [...contagem.keys()]
    .filter(k => !ids.has(k))
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
    .map(k => ({ valor: k, rotulo: k, total: contagem.get(k) || 0 }))
  return [...catalogo, ...extras]
})

// Contagens e Filtros
// Busca geral + filtros por coluna; a condição do supervisor é aplicada depois,
// para que as contagens dos botões reflitam os demais filtros.
const tarefasFiltradasPorTexto = computed(() => {
  const q = filtroTexto.value.trim().toLowerCase()
  const atividade = filtroAtividade.value.trim().toLowerCase()
  return dados.value.tarefas.filter(t => {
    if (filtroRegra.value.length && !filtroRegra.value.includes(t.codigo)) return false
    if (filtroStatusPortal.value.length && !filtroStatusPortal.value.includes(chaveStatusPortal(t))) return false
    if (atividade && !(t.titulo || '').toLowerCase().includes(atividade)) return false
    if (!q) return true
    return (
      (t.titulo && t.titulo.toLowerCase().includes(q)) ||
      (t.commit_id && t.commit_id.toLowerCase().includes(q)) ||
      (t.commit_autor && t.commit_autor.toLowerCase().includes(q)) ||
      (t.commit_mensagem && t.commit_mensagem.toLowerCase().includes(q)) ||
      (t.codigo && t.codigo.toLowerCase().includes(q)) ||
      (t.task_id && t.task_id.toLowerCase().includes(q))
    )
  })
})

const contagemAbertas = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => !isTarefaConcluida(t)).length
})

const contagemConcluidas = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => isTarefaConcluida(t)).length
})

const tarefasExibidas = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => {
    if (filtroStatus.value === 'abertas') return !isTarefaConcluida(t)
    if (filtroStatus.value === 'concluidas') return isTarefaConcluida(t)
    return true
  })
})

const selecionadasCount = computed(() => selecionadosIds.value.length)

const todosSelecionados = computed(() => {
  if (tarefasExibidas.value.length === 0) return false
  return tarefasExibidas.value.every(t => selecionadosIds.value.includes(t.id))
})

function isSelecionada(id: number): boolean {
  return selecionadosIds.value.includes(id)
}

function toggleSelecao(id: number) {
  const idx = selecionadosIds.value.indexOf(id)
  if (idx > -1) {
    selecionadosIds.value.splice(idx, 1)
  } else {
    selecionadosIds.value.push(id)
  }
}

function toggleSelecionarTodas() {
  if (todosSelecionados.value) {
    // Desmarca as visíveis
    const idsVisiveis = new Set(tarefasExibidas.value.map(t => t.id))
    selecionadosIds.value = selecionadosIds.value.filter(id => !idsVisiveis.has(id))
  } else {
    // Marca todas as visíveis
    const novoSet = new Set([...selecionadosIds.value, ...tarefasExibidas.value.map(t => t.id)])
    selecionadosIds.value = Array.from(novoSet)
  }
}

function limparSelecao() {
  selecionadosIds.value = []
}

function resetarFiltros() {
  filtroTexto.value = ''
  filtroStatus.value = 'todos'
  filtroRegra.value = []
  filtroAtividade.value = ''
  filtroStatusPortal.value = []
}

function mudarMes(delta: number) {
  let novoMes = mesAtual.value + delta
  let novoAno = anoAtual.value
  if (novoMes > 12) {
    novoMes = 1
    novoAno += 1
  } else if (novoMes < 1) {
    novoMes = 12
    novoAno -= 1
  }
  mesAtual.value = novoMes
  anoAtual.value = novoAno
  carregarTarefas()
}

function irParaMesAtual() {
  const d = new Date()
  mesAtual.value = d.getMonth() + 1
  anoAtual.value = d.getFullYear()
  carregarTarefas()
}

async function carregarTarefas() {
  loading.value = true
  limparSelecao()
  try {
    const res = await api.tarefasMes.listar(mesAtual.value, anoAtual.value)
    dados.value = res
  } catch (e: any) {
    toastStore.addToast(`Erro ao carregar tarefas do mês: ${e.message || e}`, 'error')
  } finally {
    loading.value = false
  }
}

async function sincronizarComMunka() {
  sincronizando.value = true
  try {
    const res = await api.tarefasMes.sincronizar()
    toastStore.addToast(`Sincronização com o portal Munka enfileirada com sucesso (Job #${res.job_id})!`, 'info')
    await filaStore.fetchJobs()
  } catch (e: any) {
    toastStore.addToast(`Erro ao disparar sincronização: ${e.response?.data?.detail || e.message || e}`, 'error')
  } finally {
    sincronizando.value = false
  }
}

function abrirModalAjusteSingle(t: TarefaMesItem) {
  tarefaAlvoSingle.value = t
  formSingle.cargo = configPadrao.value.munka_cargo || '9'
  formSingle.nivel = configPadrao.value.munka_nivel || '3'
  formSingle.responsavel = configPadrao.value.munka_responsavel || ''
  formSingle.tipo = 'projeto'
  formSingle.produto = configPadrao.value.munka_produto || '[DESENV] MUNKA'
  formSingle.projeto = configPadrao.value.munka_projeto || 'MUNKA Multicontrato'
  formSingle.status_id = configPadrao.value.munka_status_id || '20'
  modalAjusteSingleAberto.value = true
}

function fecharModalSingle() {
  modalAjusteSingleAberto.value = false
  tarefaAlvoSingle.value = null
}

async function salvarAjusteSingle() {
  if (!tarefaAlvoSingle.value) return
  salvando.value = true
  try {
    const res = await api.tarefasMes.ajustar({
      historico_ids: [tarefaAlvoSingle.value.id],
      cargo: formSingle.cargo,
      nivel: formSingle.nivel,
      responsavel: formSingle.responsavel,
      tipo: formSingle.tipo,
      produto: formSingle.produto,
      projeto: formSingle.projeto,
      status_id: formSingle.status_id
    })
    toastStore.addToast(`Ajuste da tarefa enfileirado com sucesso (Job #${res.job_id})!`, 'success')

    // Atualização otimista imediata na UI
    const novoNome = rotuloStatus(formSingle.status_id)
    tarefaAlvoSingle.value.status = novoNome
    tarefaAlvoSingle.value.status_munka = novoNome

    fecharModalSingle()
    await filaStore.fetchJobs()
    // Atualiza listagem em background
    carregarTarefas()
  } catch (e: any) {
    toastStore.addToast(`Erro ao ajustar tarefa: ${e.response?.data?.detail || e.message || e}`, 'error')
  } finally {
    salvando.value = false
  }
}

function abrirModalAjusteLote() {
  if (selecionadasCount.value === 0) return
  // Reseta toggles
  habilitarCampo.cargo = false
  habilitarCampo.nivel = false
  habilitarCampo.responsavel = false
  habilitarCampo.tipo = false
  habilitarCampo.produto = false
  habilitarCampo.projeto = false
  habilitarCampo.status = false

  formLote.cargo = configPadrao.value.munka_cargo || '9'
  formLote.nivel = configPadrao.value.munka_nivel || '3'
  formLote.responsavel = configPadrao.value.munka_responsavel || ''
  formLote.tipo = 'projeto'
  formLote.produto = configPadrao.value.munka_produto || '[DESENV] MUNKA'
  formLote.projeto = configPadrao.value.munka_projeto || 'MUNKA Multicontrato'
  formLote.status_id = configPadrao.value.munka_status_id || '20'

  modalAjusteLoteAberto.value = true
}

function fecharModalLote() {
  modalAjusteLoteAberto.value = false
}

async function salvarAjusteLote() {
  if (selecionadasCount.value === 0) return
  if (totalCamposHabilitados.value === 0) {
    toastStore.addToast('Selecione pelo menos um campo para alterar em lote.', 'info')
    return
  }

  const idsParaAjustar = [...selecionadosIds.value]
  const payload: any = {
    historico_ids: idsParaAjustar
  }

  if (habilitarCampo.cargo) payload.cargo = formLote.cargo
  if (habilitarCampo.nivel) payload.nivel = formLote.nivel
  if (habilitarCampo.responsavel) payload.responsavel = formLote.responsavel
  if (habilitarCampo.tipo) payload.tipo = formLote.tipo
  if (habilitarCampo.produto) payload.produto = formLote.produto
  if (habilitarCampo.projeto) payload.projeto = formLote.projeto
  if (habilitarCampo.status) payload.status_id = formLote.status_id

  salvando.value = true
  try {
    const res = await api.tarefasMes.ajustar(payload)
    toastStore.addToast(`Ajuste em lote enfileirado (Job #${res.job_id || 'OK'})! As alterações estão sendo aplicadas no Munka.`, 'success')

    // Atualização otimista imediata na UI das tarefas selecionadas
    if (habilitarCampo.status) {
      const novoNome = rotuloStatus(formLote.status_id)
      for (const t of dados.value.tarefas) {
        if (idsParaAjustar.includes(t.id)) {
          t.status = novoNome
          t.status_munka = novoNome
        }
      }
    }

    fecharModalLote()
    limparSelecao()
    await filaStore.fetchJobs()
    // Atualiza listagem em background
    carregarTarefas()
  } catch (e: any) {
    toastStore.addToast(`Erro ao ajustar tarefas: ${e.response?.data?.detail || e.message || e}`, 'error')
  } finally {
    salvando.value = false
  }
}

function obterClasseBadgeStatus(status?: string): VarianteBadgeStatus {
  return classeBadgeStatus(status)
}

function formatarDataHora(isoString: string): string {
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return isoString
    return d.toLocaleString('pt-BR')
  } catch {
    return isoString
  }
}

function obterTempoRelativo(isoString: string): string {
  try {
    const d = new Date(isoString)
    const diffMs = Date.now() - d.getTime()
    const diffMin = Math.floor(diffMs / (1000 * 60))
    if (diffMin < 1) return 'agora há pouco'
    if (diffMin < 60) return `há ${diffMin} min`
    const diffH = Math.floor(diffMin / 60)
    if (diffH < 24) return `há ${diffH}h`
    const diffD = Math.floor(diffH / 24)
    return `há ${diffD}d`
  } catch {
    return ''
  }
}

onMounted(async () => {
  try {
    configPadrao.value = await api.config.obter()
  } catch {
    // ignora se falhar
  }
  await carregarTarefas()
})
</script>
