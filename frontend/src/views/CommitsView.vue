<template>
  <div>
    <PageHeader>
      <div data-tour="commits-titulo" class="flex items-center gap-2">
        <PageTitle>Commits</PageTitle>
        <TutorialModal screenId="commits" />
      </div>
      <BaseButton variant="primary" data-tour="commits-importar" @click="$router.push('/importar')">
        <i class="fa-solid fa-file-import" aria-hidden="true"></i>
        <span>+ Importar Commit</span>
      </BaseButton>
    </PageHeader>

    <!-- Modal de importação -->
    <BaseModal v-if="showImport" ref="importModalRef" labelledby="import-modal-title" @close="showImport = false">
      <h2 id="import-modal-title" class="mb-1 text-xl font-bold text-foreground">Importar Commits do GitLab (Lote)</h2>
      <BaseLabel for="import-commit-hashes">URLs Completas dos Commits do GitLab (uma por linha)</BaseLabel>
      <BaseTextarea
        id="import-commit-hashes"
        v-model="form.commit_hashes"
        placeholder="Ex:&#10;https://gitlab.suaorganizacao.com/grupo/projeto/-/commit/abc123hash"
        rows="6"
      />
      <div data-modal-actions class="mt-4 flex justify-end gap-3">
        <BaseButton variant="ghost" @click="showImport = false">Cancelar</BaseButton>
        <BaseButton variant="primary" :disabled="importing || !form.commit_hashes.trim()" @click="importar">
          {{ importing ? 'Importando...' : 'Importar' }}
        </BaseButton>
      </div>
      <StateMessage v-if="importError" type="error" tag="p">{{ importError }}</StateMessage>
    </BaseModal>

    <!-- Estado de Carregamento -->
    <StateMessage v-if="store.loading" type="loading" role="status" aria-live="polite">Carregando commits...</StateMessage>

    <!-- Estado Vazio -->
    <StateMessage v-else-if="store.commits.length === 0" type="empty">
      Nenhum commit importado. Clique em "+ Importar Commit" para começar.
    </StateMessage>

    <!-- Área Principal de Commits & Repositórios -->
    <div v-else class="flex flex-col gap-6">

      <!-- Barra de Controle: Alternador de Visualização, Busca e Filtros Rápidos -->
      <section :class="cls.controlBar" aria-label="Controles de exibição e filtros por repositório">
        <div class="flex items-center justify-between gap-4 flex-wrap">

          <!-- Alternador de Modos (Tabs Acessíveis) -->
          <div data-tour="commits-modos" class="inline-flex bg-background border border-border-strong rounded-lg p-0.75 gap-0.75 light:bg-slate-100 light:border-slate-300" role="tablist" aria-label="Modo de visualização dos commits">
            <button
              id="tab-modo-repo"
              type="button"
              role="tab"
              :class="[cls.abaModo, visaoModo === 'repositorio' ? cls.abaModoAtiva : cls.abaModoInativa]"
              :aria-selected="visaoModo === 'repositorio'"
              aria-controls="panel-commits-view"
              @click="setVisaoModo('repositorio')"
            >
              <i class="fa-solid fa-folder-tree text-[0.95rem]" aria-hidden="true"></i>
              <span>Por Repositório</span>
              <span :class="cls.modoContagem" :title="`${repositoriosResumo.length} repositórios ativos`">
                {{ repositoriosResumo.length }}
              </span>
            </button>

            <button
              id="tab-modo-data"
              type="button"
              role="tab"
              :class="[cls.abaModo, visaoModo === 'data' ? cls.abaModoAtiva : cls.abaModoInativa]"
              :aria-selected="visaoModo === 'data'"
              aria-controls="panel-commits-view"
              @click="setVisaoModo('data')"
            >
              <i class="fa-solid fa-calendar-days text-[0.95rem]" aria-hidden="true"></i>
              <span>Linha do Tempo (Data)</span>
              <span :class="cls.modoContagem" :title="`${commitsFiltrados.length} commits`">
                {{ commitsFiltrados.length }}
              </span>
            </button>
          </div>

          <!-- Busca de Commits / Repositórios -->
          <SearchBox
            v-model="termoBusca"
            data-tour="commits-busca"
            placeholder="Buscar por mensagem, SHA ou repositório..."
            aria-label="Buscar commits por mensagem, hash ou repositório"
          />
        </div>

        <!-- Chips de Seleção Rápida por Repositório e Status de Fila -->
        <div data-tour="commits-chips" class="flex items-center gap-3 flex-wrap pt-1 border-t border-dashed border-border-strong" role="region" aria-label="Filtrar por repositório específico ou fila">
          <span class="text-[0.82rem] font-bold text-muted-foreground uppercase tracking-wider shrink-0">Filtros:</span>
          <div data-tour="commits-chips-lista" class="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              :class="[cls.chip, chipTodosAtivo ? cls.chipAtivo : [cls.chipInativo, cls.chipCorTodos]]"
              :aria-pressed="chipTodosAtivo"
              @click="limparFiltroFila"
            >
              <span>Todos</span>
              <span :class="classeChipContagem(chipTodosAtivo)">{{ store.commits.length }}</span>
            </button>

            <!-- Chip Especial: Apenas na Fila -->
            <button
              v-if="totalTarefasAtivasNaFila > 0"
              type="button"
              :class="[cls.chip, apenasNaFila ? cls.chipAtivoFila : [cls.chipInativo, cls.chipCorFila]]"
              :aria-pressed="apenasNaFila"
              @click="apenasNaFila = !apenasNaFila"
              :title="`Filtrar commits com tarefas ativas na fila (${totalTarefasAtivasNaFila} tarefas ativas)`"
            >
              <span class="size-2 rounded-full bg-current shrink-0 animate-pulse-chip" aria-hidden="true"></span>
              <span>Na Fila</span>
              <span :class="classeChipContagem(apenasNaFila)">{{ totalTarefasAtivasNaFila }}</span>
            </button>

            <!-- Chips de Repositórios -->
            <button
              v-for="repo in repositoriosResumo"
              :key="repo.nome"
              type="button"
              :class="[cls.chip, repositorioFiltro === repo.nome ? cls.chipAtivo : [cls.chipInativo, CORES_REPO[repo.colorClass].chip]]"
              :aria-pressed="repositorioFiltro === repo.nome"
              @click="toggleFiltroRepo(repo.nome)"
              :title="`Filtrar commits do repositório ${repo.nome} (${repo.totalCommits} commits)`"
            >
              <span class="size-2 rounded-full bg-current shrink-0" aria-hidden="true"></span>
              <span class="max-w-55 overflow-hidden text-ellipsis">{{ repo.nome }}</span>
              <span :class="classeChipContagem(repositorioFiltro === repo.nome)">{{ repo.totalCommits }}</span>
              <span v-if="repo.totalNaFila > 0" class="text-[0.68rem] font-extrabold px-1.25 py-px rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30" title="Tarefas na fila">
                {{ repo.totalNaFila }} fila
              </span>
            </button>
          </div>
        </div>

        <!-- Barra de Status com Filtros Ativos -->
        <div v-if="repositorioFiltro !== 'todos' || termoBusca || apenasNaFila" class="flex items-center justify-between gap-3 bg-sky-400/8 border border-sky-400/25 rounded-lg px-3.5 py-2 flex-wrap" role="status" aria-live="polite">
          <div class="flex items-center gap-2.5 flex-wrap">
            <span class="text-[0.82rem] font-semibold text-muted-foreground">Filtros ativos:</span>
            <span v-if="apenasNaFila" :class="[cls.filtroTag, cls.filtroTagAmbar]">
              <span :class="cls.spinnerXs"></span>
              <span>Apenas na Fila ({{ totalTarefasAtivasNaFila }} tarefas)</span>
              <button type="button" :class="cls.tagRemover" @click="apenasNaFila = false" aria-label="Remover filtro de fila">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span v-if="repositorioFiltro !== 'todos'" :class="[cls.filtroTag, cls.filtroTagNeutra]">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
              </svg>
              <span>{{ repositorioFiltro }}</span>
              <button type="button" :class="cls.tagRemover" @click="repositorioFiltro = 'todos'" aria-label="Remover filtro deste repositório">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span v-if="termoBusca" :class="[cls.filtroTag, cls.filtroTagNeutra]">
              <span>"{{ termoBusca }}"</span>
              <button type="button" :class="cls.tagRemover" @click="termoBusca = ''" aria-label="Remover filtro de texto">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span class="text-xs text-muted-foreground">
              ({{ commitsFiltrados.length }} commit{{ commitsFiltrados.length !== 1 ? 's' : '' }} encontrado{{ commitsFiltrados.length !== 1 ? 's' : '' }})
            </span>
          </div>
          <button type="button" class="bg-transparent border-0 text-[0.82rem] font-semibold text-primary cursor-pointer px-2 py-0.75 rounded transition-colors duration-150 hover:bg-primary-glow" @click="limparTodosFiltros">
            Limpar Filtros
          </button>
        </div>

        <!-- Barra de Ações Rápidas de Seleção em Lote -->
        <div class="flex items-center justify-between flex-wrap gap-3 px-3.5 py-2.5 bg-muted rounded-lg border border-border light:bg-slate-50 light:border-slate-200" role="toolbar" aria-label="Ações de seleção rápida de commits">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="flex items-center gap-1.5 text-[0.82rem] font-semibold text-muted-foreground mr-1 light:text-slate-600">
              <i class="fa-solid fa-list-check" aria-hidden="true"></i>
              <span>Seleção em lote:</span>
            </span>
            <button
              type="button"
              :class="[cls.btnSelecao, cls.btnSelecaoNeutro]"
              @click="selecionarTodosExibidos"
              :title="`Selecionar todos os ${commitsFiltrados.length} commits exibidos`"
            >
              Selecionar Todos ({{ commitsFiltrados.length }})
            </button>
            <button
              v-if="totalCommitsAnalisadosExibidos > 0"
              type="button"
              :class="[cls.btnSelecao, cls.btnSelecaoAnalisados]"
              @click="selecionarApenasAnalisados"
              :title="`Selecionar apenas os ${totalCommitsAnalisadosExibidos} commits analisados (com tarefas)`"
            >
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
              Apenas Analisados ({{ totalCommitsAnalisadosExibidos }})
            </button>
            <button
              v-if="totalCommitsPendentesExibidos > 0"
              type="button"
              :class="[cls.btnSelecao, cls.btnSelecaoPendentes]"
              @click="selecionarApenasPendentes"
              :title="`Selecionar apenas os ${totalCommitsPendentesExibidos} commits pendentes de análise`"
            >
              <i class="fa-solid fa-clock" aria-hidden="true"></i>
              Apenas Pendentes ({{ totalCommitsPendentesExibidos }})
            </button>
          </div>

          <div class="flex items-center gap-2.5" v-if="selecionados.length > 0">
            <span class="text-xs px-2.5 py-0.75 rounded-xl bg-blue-500/15 text-primary-light border border-blue-500/35 font-semibold light:bg-blue-50 light:text-blue-700 light:border-blue-200">
              <strong>{{ selecionados.length }}</strong> selecionado{{ selecionados.length > 1 ? 's' : '' }}
            </span>
            <button
              type="button"
              class="bg-transparent border-0 text-muted-foreground text-xs cursor-pointer inline-flex items-center gap-1.25 px-2 py-1 rounded transition-colors duration-150 hover:text-danger focus-visible:outline-danger"
              @click="desmarcarTodos"
              title="Desmarcar todos os commits"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              Limpar
            </button>
          </div>
        </div>

      </section>

      <!-- Mensagem quando os filtros não retornam nada -->
      <StateMessage v-if="commitsFiltrados.length === 0" type="empty">
        <p>Nenhum commit encontrado para os critérios selecionados.</p>
        <BaseButton variant="ghost" class="mt-3" @click="limparTodosFiltros">
          Limpar Filtros
        </BaseButton>
      </StateMessage>

      <!-- PAINEL 1: VISÃO POR REPOSITÓRIO -->
      <div
        v-else-if="visaoModo === 'repositorio'"
        id="panel-commits-view"
        class="flex flex-col gap-6"
        role="tabpanel"
        aria-labelledby="tab-modo-repo"
      >
        <div
          v-for="repo in commitsAgrupadosPorRepo"
          :key="repo.nome"
          :class="cls.repoCard"
        >
          <!-- Cabeçalho do Card de Repositório -->
          <div
            :class="cls.repoCardHeader"
            tabindex="0"
            role="button"
            :aria-expanded="!isRepoColapsado(repo.nome)"
            @click="toggleColapsoRepo(repo.nome)"
            @keydown.enter.prevent="toggleColapsoRepo(repo.nome)"
            @keydown.space.prevent="toggleColapsoRepo(repo.nome)"
          >
            <div class="flex items-center gap-3.5 min-w-0 flex-1">
              <!-- Checkbox para selecionar/desmarcar todos do repositório -->
              <div :class="cls.colunaSelecao" @click.stop @keydown.stop>
                <input
                  type="checkbox"
                  :class="cls.checkbox"
                  :checked="isRepoTotalmenteSelecionado(repo)"
                  :indeterminate="isRepoParcialmenteSelecionado(repo)"
                  @change="toggleSelecionarTodosRepo(repo)"
                  :aria-label="`Selecionar todos os commits do repositório ${repo.nome}`"
                  :title="`Selecionar todos os commits do repositório ${repo.nome}`"
                />
              </div>
              <div :class="['size-10 rounded-[10px] flex items-center justify-center shrink-0 border', CORES_REPO[repo.colorClass].tag]">
                <i class="fa-brands fa-git-alt text-lg" aria-hidden="true"></i>
              </div>
              <div class="flex flex-col gap-0.75 min-w-0">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <h3 class="m-0 text-lg font-extrabold text-foreground tracking-[-0.01em] [word-break:break-word] light:text-slate-900">{{ repo.nome }}</h3>
                  <span class="inline-block text-xs font-bold leading-none tracking-[0.03em] uppercase px-2 py-0.5 bg-background border border-border-strong rounded-xl text-muted-foreground light:bg-slate-100 light:border-slate-300 light:text-slate-700">{{ repo.commits.length }} commit{{ repo.commits.length > 1 ? 's' : '' }}</span>
                </div>
                <span class="text-xs text-muted-foreground [&_strong]:text-foreground">
                  <span v-if="repo.ultimoCommitData">Mais recente em: <strong>{{ repo.ultimoCommitData }}</strong></span>
                  <span v-else>Repositório de atividades</span>
                </span>
              </div>
            </div>

            <!-- Lado Direito: Métricas e Indicador de Toggle -->
            <div class="flex items-center gap-4 shrink-0" @click.stop>
              <div class="flex items-center gap-2 flex-wrap">
                <!-- Badge Dinâmico de Tarefas na Fila do Repositório -->
                <span
                  v-if="repo.totalNaFila > 0"
                  :class="cls.badgeFilaRepo"
                  :title="`${repo.totalNaFila} tarefa(s) deste repositório estão na fila de execução`"
                >
                  <span :class="cls.spinnerXs"></span>
                  {{ repo.totalNaFila }} na fila
                </span>

                <BaseBadge variant="green" :title="`${repo.analisados} commit(s) analisado(s)`">
                  <i class="fa-solid fa-circle-check mr-0.5" aria-hidden="true"></i>
                  {{ repo.analisados }} Analisado{{ repo.analisados !== 1 ? 's' : '' }}
                </BaseBadge>
                <BaseBadge v-if="repo.pendentes > 0" variant="gray" :title="`${repo.pendentes} commit(s) pendente(s)`">
                  <i class="fa-solid fa-clock mr-0.5" aria-hidden="true"></i>
                  {{ repo.pendentes }} Pendente{{ repo.pendentes !== 1 ? 's' : '' }}
                </BaseBadge>
                <BaseBadge v-if="repo.totalHpa > 0" variant="hpa" :title="`${repo.totalHpa} horas HPA estimadas`">
                  <i class="fa-solid fa-bolt mr-0.5" aria-hidden="true"></i>
                  {{ repo.totalHpa }}h HPA
                </BaseBadge>
              </div>

              <!-- Botão Expandir / Recolher -->
              <button
                type="button"
                class="bg-background border border-border-strong text-muted-foreground text-[0.83rem] size-8 rounded-md flex items-center justify-center cursor-pointer transition-all duration-150 hover:text-foreground hover:border-primary light:bg-white light:border-slate-300 light:text-slate-600 light:hover:border-blue-600 light:hover:text-blue-600"
                @click="toggleColapsoRepo(repo.nome)"
                :aria-expanded="!isRepoColapsado(repo.nome)"
                :aria-label="isRepoColapsado(repo.nome) ? `Expandir commits do repositório ${repo.nome}` : `Recolher commits do repositório ${repo.nome}`"
                :title="isRepoColapsado(repo.nome) ? 'Expandir commits' : 'Recolher commits'"
              >
                <i
                  :class="['fa-solid fa-chevron-down transition-transform duration-200', isRepoColapsado(repo.nome) ? '-rotate-90' : '']"
                  aria-hidden="true"
                ></i>
              </button>
            </div>
          </div>

          <!-- Lista de Commits do Repositório (colapsável) -->
          <div v-show="!isRepoColapsado(repo.nome)" class="flex flex-col">
            <div
              v-for="commit in repo.commits"
              :key="commit.id"
              :class="[cls.commitRow, isCommitSelecionado(commit.id) ? cls.commitRowSelecionada : cls.commitRowOciosa]"
              tabindex="0"
              role="row"
              :aria-selected="isCommitSelecionado(commit.id)"
              @click="toggleSelectCommit(commit.id)"
              @keydown.enter.prevent="toggleSelectCommit(commit.id)"
              @keydown.space.prevent="toggleSelectCommit(commit.id)"
            >
              <!-- Seleção do Commit (Checkbox) -->
              <div :class="cls.colunaSelecao" @click.stop @keydown.stop>
                <input
                  type="checkbox"
                  :id="`select-repo-${commit.id}`"
                  :class="cls.checkbox"
                  :checked="isCommitSelecionado(commit.id)"
                  @change="toggleSelectCommit(commit.id)"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem || 'sem mensagem'}`"
                />
              </div>

              <!-- Lado Esquerdo: Avatar do Autor -->
              <div
                :class="cls.avatar"
                v-bind="atributosAvatar(commit.autor)"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Centro: Mensagem e Metadados -->
              <div class="flex flex-col gap-1 flex-1 min-w-0">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <span :class="cls.commitTitulo" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>

                  <!-- Badges de Status, Envio e FILA -->
                  <div class="flex gap-1.5 flex-wrap items-center">
                    <BaseBadge :variant="commit.analisado ? 'green' : 'gray'">
                      {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                    </BaseBadge>

                    <template v-if="commit.analisado">
                      <BaseBadge :variant="variantEnviadas(commit)">
                        {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
                      </BaseBadge>
                    </template>

                    <!-- BADGE DINÂMICO DE FILA -->
                    <template v-if="obterInfoFila(commit.id)">
                      <span
                        v-if="obterInfoFila(commit.id)!.analisando"
                        :class="cls.badgeFilaAnalise"
                        title="Análise de IA deste commit aguardando ou processando na fila"
                      >
                        <span class="size-1.5 rounded-full bg-current inline-block animate-pulse-queue shrink-0"></span>
                        Análise na fila
                      </span>

                      <span
                        v-if="obterInfoFila(commit.id)!.envios > 0"
                        :class="obterInfoFila(commit.id)!.running > 0 ? cls.badgeFilaEnvioRodando : cls.badgeFilaEnvio"
                        :title="`${obterInfoFila(commit.id)!.envios} tarefa(s) deste commit na fila (${obterInfoFila(commit.id)!.running} em execução, ${obterInfoFila(commit.id)!.pending} aguardando)`"
                      >
                        <span :class="cls.spinnerXs" v-if="obterInfoFila(commit.id)!.running > 0"></span>
                        <i class="fa-solid fa-clock text-xs mr-0.5" aria-hidden="true" v-else></i>
                        {{ obterInfoFila(commit.id)!.envios }} na fila
                      </span>
                    </template>
                  </div>
                </div>
                <span :class="cls.commitAutorTempo">
                  <span :class="cls.commitData">{{ formatarDataCurta(commit.data_autor || commit.data) }}</span>
                  · {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
                </span>
              </div>

              <!-- Lado Direito: Ações, SHA e Olho para Entrar -->
              <div class="flex items-center gap-2 shrink-0 ml-3" @click.stop>
                <!-- Botão Excluir -->
                <button
                  type="button"
                  :class="[cls.btnAcao, cls.btnExcluir]"
                  @click.stop="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                </button>

                <!-- Botão SHA interativo (copia ao clicar) -->
                <button
                  type="button"
                  :class="[cls.btnSha, shaCopiadoId === commit.id ? cls.btnShaCopiado : cls.btnShaNormal]"
                  @click.stop="copiarSHA(commit.id)"
                  :title="shaCopiadoId === commit.id ? 'SHA copiado!' : 'Clique para copiar o SHA completo'"
                  :aria-label="`Copiar hash SHA ${commit.id}`"
                >
                  <span v-if="shaCopiadoId === commit.id" class="inline-flex items-center gap-1.25 text-xs font-bold tracking-[0.01em]">
                    <i class="fa-solid fa-check" aria-hidden="true"></i>
                    <span>Copiado!</span>
                  </span>
                  <span v-else class="text-xs tracking-[0.04em]">
                    {{ commit.id.slice(0, 8) }}
                  </span>
                </button>

                <!-- Botão Olho: ÚNICO método para entrar no commit -->
                <button
                  type="button"
                  :class="[cls.btnAcao, cls.btnOlho]"
                  @click.stop="$router.push(`/commits/${commit.id}`)"
                  title="Abrir detalhes do commit"
                  :aria-label="`Abrir detalhes do commit ${commit.id.slice(0, 8)}`"
                >
                  <i class="fa-solid fa-eye" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PAINEL 2: VISÃO POR DATA (LINHA DO TEMPO) -->
      <div
        v-else
        id="panel-commits-view"
        class="flex flex-col gap-6"
        role="tabpanel"
        aria-labelledby="tab-modo-data"
      >
        <!-- Percorre os dias agrupados -->
        <div v-for="grupo in commitsAgrupadosPorData" :key="grupo.data" class="flex flex-col">

          <!-- Cabeçalho do dia: "31 Ago, 2026 2 commits" -->
          <div class="flex items-baseline gap-2 px-5 py-3 bg-muted border border-b-0 border-border rounded-t-[10px] text-sm light:bg-slate-50 light:border-slate-200">
            <span class="font-extrabold text-foreground text-[0.95rem] light:text-slate-900">{{ grupo.data }}</span>
            <span class="text-muted-foreground text-[0.82rem] font-medium light:text-slate-600">{{ grupo.commits.length }} commit{{ grupo.commits.length > 1 ? 's' : '' }}</span>
          </div>

          <!-- Lista de commits desse dia -->
          <div class="border border-t-0 border-border bg-card flex flex-col rounded-b-[10px] overflow-hidden light:bg-white light:border-slate-200">
            <div
              v-for="commit in grupo.commits"
              :key="commit.id"
              :class="[cls.commitRow, isCommitSelecionado(commit.id) ? cls.commitRowSelecionada : cls.commitRowOciosa]"
              tabindex="0"
              role="row"
              :aria-selected="isCommitSelecionado(commit.id)"
              @click="toggleSelectCommit(commit.id)"
              @keydown.enter.prevent="toggleSelectCommit(commit.id)"
              @keydown.space.prevent="toggleSelectCommit(commit.id)"
            >
              <!-- Seleção do Commit (Checkbox) -->
              <div :class="cls.colunaSelecao" @click.stop @keydown.stop>
                <input
                  type="checkbox"
                  :id="`select-data-${commit.id}`"
                  :class="cls.checkbox"
                  :checked="isCommitSelecionado(commit.id)"
                  @change="toggleSelectCommit(commit.id)"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem || 'sem mensagem'}`"
                />
              </div>

              <!-- Lado Esquerdo: Avatar do Autor -->
              <div
                :class="cls.avatar"
                v-bind="atributosAvatar(commit.autor)"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Centro: Mensagem, Repositório e Metadados -->
              <div class="flex flex-col gap-1 flex-1 min-w-0">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <!-- Tag / Badge destacada do Repositório -->
                  <button
                    type="button"
                    :class="['inline-flex items-center gap-1.5 border text-xs font-bold px-2 py-0.75 rounded-md cursor-pointer transition-all duration-150 whitespace-nowrap max-w-55 no-underline hover:brightness-115 hover:-translate-y-px', CORES_REPO[obterClasseCorRepo(commit.projeto)].tag]"
                    @click.stop="toggleFiltroRepo(commit.projeto)"
                    :title="`Filtrar pelo repositório ${commit.projeto || 'Sem repositório'}`"
                    aria-label="Filtrar por este repositório"
                  >
                    <i class="fa-brands fa-gitlab text-xs" aria-hidden="true"></i>
                    <span>{{ commit.projeto || 'Sem repositório' }}</span>
                  </button>

                  <span :class="cls.commitTitulo" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>

                  <!-- Badges de Status, Envio e FILA -->
                  <div class="flex gap-1.5 flex-wrap items-center">
                    <BaseBadge :variant="commit.analisado ? 'green' : 'gray'">
                      {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                    </BaseBadge>

                    <template v-if="commit.analisado">
                      <BaseBadge :variant="variantEnviadas(commit)">
                        {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
                      </BaseBadge>
                    </template>

                    <!-- BADGE DINÂMICO DE FILA -->
                    <template v-if="obterInfoFila(commit.id)">
                      <span
                        v-if="obterInfoFila(commit.id)!.analisando"
                        :class="cls.badgeFilaAnalise"
                        title="Análise de IA deste commit aguardando ou processando na fila"
                      >
                        <span class="size-1.5 rounded-full bg-current inline-block animate-pulse-queue shrink-0"></span>
                        Análise na fila
                      </span>

                      <span
                        v-if="obterInfoFila(commit.id)!.envios > 0"
                        :class="obterInfoFila(commit.id)!.running > 0 ? cls.badgeFilaEnvioRodando : cls.badgeFilaEnvio"
                        :title="`${obterInfoFila(commit.id)!.envios} tarefa(s) deste commit na fila (${obterInfoFila(commit.id)!.running} em execução, ${obterInfoFila(commit.id)!.pending} aguardando)`"
                      >
                        <span :class="cls.spinnerXs" v-if="obterInfoFila(commit.id)!.running > 0"></span>
                        <i class="fa-solid fa-clock text-xs mr-0.5" aria-hidden="true" v-else></i>
                        {{ obterInfoFila(commit.id)!.envios }} na fila
                      </span>
                    </template>
                  </div>
                </div>
                <span :class="cls.commitAutorTempo">
                  {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
                </span>
              </div>

              <!-- Lado Direito: Ações, SHA e Olho para Entrar -->
              <div class="flex items-center gap-2 shrink-0 ml-3" @click.stop>
                <!-- Botão Excluir -->
                <button
                  type="button"
                  :class="[cls.btnAcao, cls.btnExcluir]"
                  @click.stop="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                </button>

                <!-- Botão SHA interativo (copia ao clicar) -->
                <button
                  type="button"
                  :class="[cls.btnSha, shaCopiadoId === commit.id ? cls.btnShaCopiado : cls.btnShaNormal]"
                  @click.stop="copiarSHA(commit.id)"
                  :title="shaCopiadoId === commit.id ? 'SHA copiado!' : 'Clique para copiar o SHA completo'"
                  :aria-label="`Copiar hash SHA ${commit.id}`"
                >
                  <span v-if="shaCopiadoId === commit.id" class="inline-flex items-center gap-1.25 text-xs font-bold tracking-[0.01em]">
                    <i class="fa-solid fa-check" aria-hidden="true"></i>
                    <span>Copiado!</span>
                  </span>
                  <span v-else class="text-xs tracking-[0.04em]">
                    {{ commit.id.slice(0, 8) }}
                  </span>
                </button>

                <!-- Botão Olho: ÚNICO método para entrar no commit -->
                <button
                  type="button"
                  :class="[cls.btnAcao, cls.btnOlho]"
                  @click.stop="$router.push(`/commits/${commit.id}`)"
                  title="Abrir detalhes do commit"
                  :aria-label="`Abrir detalhes do commit ${commit.id.slice(0, 8)}`"
                >
                  <i class="fa-solid fa-eye" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>

    </div>

    <!-- Modal de Confirmação de Exclusão -->
    <BaseModal v-if="exibindoModalConfirmacao" ref="confirmModalRef" labelledby="confirm-modal-title" @close="fecharModalConfirmacao">
      <h2 id="confirm-modal-title" class="mb-1 text-xl font-bold text-foreground">Confirmar Exclusão</h2>
      <p>Tem certeza de que deseja excluir o commit <strong>{{ commitParaDeletar?.id.slice(0, 8) }}</strong> e sua respectiva análise? Esta ação não pode ser desfeita.</p>
      <template #actions>
        <BaseButton variant="ghost" @click="fecharModalConfirmacao">Cancelar</BaseButton>
        <button type="button" :class="cls.btnPerigo" @click="confirmarExclusao">Excluir</button>
      </template>
    </BaseModal>

    <!-- BARRA FLUTUANTE DE AÇÕES EM LOTE (STICKY FOOTER) -->
    <transition
      enter-active-class="transition-all duration-250 ease-[cubic-bezier(0.16,1,0.3,1)]"
      leave-active-class="transition-all duration-250 ease-[cubic-bezier(0.16,1,0.3,1)]"
      enter-from-class="translate-y-full opacity-0"
      leave-to-class="translate-y-full opacity-0"
    >
      <div
        v-if="selecionados.length > 0"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-3rem)] max-w-275 bg-card border border-primary shadow-[0_14px_36px] shadow-black/50 drop-shadow-[0_0_20px] drop-shadow-primary-glow rounded-[14px] px-5.5 py-3.5 z-1000 backdrop-blur-[10px] light:bg-white light:border-blue-500 light:shadow-black/12 light:drop-shadow-[0_0_16px] light:drop-shadow-blue-500/20"
        role="region"
        aria-label="Ações para commits selecionados"
        aria-live="polite"
      >
        <div class="flex items-center justify-between flex-wrap gap-4">
          <div class="flex flex-col gap-1.25">
            <div class="flex items-center gap-2.5">
              <span class="font-bold text-base text-foreground inline-flex items-center gap-2 [&_i]:text-primary-light">
                <i class="fa-solid fa-check-double" aria-hidden="true"></i>
                {{ selecionados.length }} commit{{ selecionados.length > 1 ? 's' : '' }} marcado{{ selecionados.length > 1 ? 's' : '' }}
              </span>
              <span class="text-[0.82rem] text-muted-foreground" v-if="totalReposSelecionadosCount > 0">
                ({{ totalReposSelecionadosCount }} repositório{{ totalReposSelecionadosCount > 1 ? 's' : '' }})
              </span>
            </div>

            <div class="flex items-center gap-2.5 flex-wrap">
              <span v-if="totalTarefasProntas > 0" :class="[cls.statPill, 'bg-emerald-500/15 text-emerald-400 border-emerald-500/35']" title="Tarefas prontas para enfileiramento no Munka">
                <i class="fa-solid fa-bolt" aria-hidden="true"></i>
                <strong>{{ totalTarefasProntas }}</strong> tarefa{{ totalTarefasProntas > 1 ? 's' : '' }} pronta{{ totalTarefasProntas > 1 ? 's' : '' }} ({{ totalHpaSelecionado.toFixed(1) }}h HPA)
              </span>
              <span v-else-if="totalCommitsAnalisadosSelecionados > 0 && totalTarefasJaEnviadas > 0" :class="[cls.statPill, 'bg-blue-500/12 text-blue-300 border-blue-500/25']" title="Todas as tarefas destes commits já foram enviadas">
                <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
                {{ totalTarefasJaEnviadas }} tarefa(s) já enviada(s)
              </span>
              <span v-if="totalCommitsPendentesSelecionados > 0" :class="[cls.statPill, 'bg-amber-500/15 text-amber-300 border-amber-500/35']" title="Commits ainda não analisados pela IA">
                <i class="fa-solid fa-clock" aria-hidden="true"></i>
                <strong>{{ totalCommitsPendentesSelecionados }}</strong> commit{{ totalCommitsPendentesSelecionados > 1 ? 's' : '' }} pendente{{ totalCommitsPendentesSelecionados > 1 ? 's' : '' }} de análise
              </span>
            </div>
          </div>

          <div class="flex items-center gap-2.5 flex-wrap">
            <BaseButton
              variant="ghost"
              size="sm"
              @click="desmarcarTodos"
              aria-label="Limpar seleção atual de commits"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              <span>Limpar</span>
            </BaseButton>

            <!-- Botão Principal: Enfileirar Tarefas no Munka -->
            <BaseButton
              v-if="totalTarefasProntas > 0"
              variant="primary"
              class="focus-visible:outline-white"
              :disabled="enfileirandoEnvio"
              @click="executarEnfileirarTarefasLote"
              :aria-label="`Enfileirar ${totalTarefasProntas} tarefas no Munka`"
            >
              <span v-if="enfileirandoEnvio" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-paper-plane" aria-hidden="true"></i>
              <span>{{ enfileirandoEnvio ? 'Enfileirando...' : `Adicionar ${totalTarefasProntas} Tarefa(s) na Fila Munka` }}</span>
            </BaseButton>

            <!-- Botão Alternativo: Reenfileirar tarefas já enviadas -->
            <BaseButton
              v-else-if="totalCommitsAnalisadosSelecionados > 0 && totalTarefasJaEnviadas > 0"
              variant="plain"
              :class="cls.btnReenfileirar"
              :disabled="enfileirandoEnvio"
              @click="executarEnfileirarTarefasLoteForcado"
              :aria-label="`Reenfileirar ${totalTarefasJaEnviadas} tarefas no Munka`"
              title="Todas as tarefas já foram enviadas. Clique para reenfileirar novamente."
            >
              <span v-if="enfileirandoEnvio" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-rotate-right" aria-hidden="true"></i>
              <span>{{ enfileirandoEnvio ? 'Reenfileirando...' : `Reenfileirar ${totalTarefasJaEnviadas} Tarefa(s)` }}</span>
            </BaseButton>

            <!-- Botão Secundário: Enfileirar Análise AI para pendentes -->
            <BaseButton
              v-if="totalCommitsPendentesSelecionados > 0"
              variant="plain"
              class="text-sm px-4 py-2.5 bg-purple-500/20 text-purple-400 border border-purple-500/40 rounded-lg hover:bg-purple-500/30 hover:border-purple-400 focus-visible:outline-purple-400"
              :disabled="enfileirandoAnalise"
              @click="executarEnfileirarAnaliseLote"
              :aria-label="`Enfileirar ${totalCommitsPendentesSelecionados} commits para análise de IA`"
            >
              <span v-if="enfileirandoAnalise" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>
              <span>{{ enfileirandoAnalise ? 'Enfileirando IA...' : `Analisar ${totalCommitsPendentesSelecionados} com IA` }}</span>
            </BaseButton>

            <!-- Atalho para a página da fila -->
            <router-link
              to="/fila"
              class="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-md border border-border-strong bg-card px-3.25 py-1.5 text-[0.82rem] leading-none font-semibold text-foreground no-underline transition-all duration-200 hover:-translate-y-px hover:border-primary hover:text-primary"
              title="Abrir painel da Fila de Execução"
            >
              <i class="fa-solid fa-list-ol" aria-hidden="true"></i>
              <span>Ver Fila</span>
            </router-link>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import { useToastStore } from '../stores/toast'
import TutorialModal from '../components/TutorialModal.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseBadge from '../components/ui/BaseBadge.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import BaseTextarea from '../components/ui/BaseTextarea.vue'
import BaseLabel from '../components/ui/BaseLabel.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageTitle from '../components/ui/PageTitle.vue'
import StateMessage from '../components/ui/StateMessage.vue'
import SearchBox from '../components/ui/SearchBox.vue'
import type { CommitSummary } from '../api'

const route = useRoute()

// ── Classes Tailwind reutilizadas no template (strings completas, detectáveis pelo Tailwind) ──
const cls = {
  controlBar:
    'bg-card border border-border-strong rounded-xl p-5 flex flex-col gap-4 shadow-[0_4px_14px] shadow-black/15 light:bg-white light:border-slate-200 light:shadow-[0_2px_10px] light:shadow-black/4',

  // Abas de modo de visualização
  abaModo:
    'inline-flex items-center gap-2 h-8.5 px-3.5 text-sm font-semibold border-0 rounded-md cursor-pointer transition-all duration-150 hover:text-foreground light:hover:text-slate-900',
  abaModoInativa: 'bg-transparent text-muted-foreground light:text-slate-600',
  abaModoAtiva:
    'bg-card text-foreground shadow-[0_2px_8px] shadow-black/25 light:bg-white light:text-slate-900 light:border light:border-slate-200 light:shadow-[0_1px_3px] light:shadow-black/8',
  modoContagem:
    'text-xs font-bold px-1.5 py-0.5 rounded-full bg-primary-glow text-primary border border-border-strong light:bg-blue-50 light:text-blue-700 light:border-blue-200',

  // Chips de filtro
  chip:
    'inline-flex items-center gap-2 px-3 py-1.5 text-[0.82rem] font-semibold rounded-full border cursor-pointer whitespace-nowrap transition-all duration-150 hover:-translate-y-px',
  chipInativo:
    'light:bg-white light:text-slate-700 light:border-slate-300 light:hover:bg-slate-50 light:hover:border-blue-600 light:hover:text-slate-900',
  chipCorTodos:
    'bg-background text-muted-foreground border-border-strong hover:border-primary hover:text-foreground',
  chipCorFila: 'bg-background text-amber-400 border-amber-500/40 hover:border-amber-500',
  chipAtivo:
    'text-white bg-primary border-primary shadow-[0_2px_8px] shadow-canvas-accent/30 light:bg-blue-600 light:border-blue-600 light:shadow-blue-600/25',
  chipAtivoFila:
    'text-white bg-warning border-amber-600 shadow-[0_2px_8px] shadow-canvas-accent/30 light:bg-blue-600 light:border-blue-600 light:shadow-blue-600/25',
  chipCount: 'text-xs font-extrabold px-1.5 py-px rounded-full',
  chipCountInativo: 'bg-white/8 text-muted-foreground light:bg-slate-100 light:text-slate-600',

  // Filtros ativos
  filtroTag:
    'inline-flex items-center gap-1.5 px-2 py-0.75 border rounded-md text-xs font-semibold',
  filtroTagNeutra: 'bg-card border-border-strong text-foreground',
  filtroTagAmbar:
    'bg-amber-500/15 border-amber-500/35 text-amber-400 light:bg-amber-100 light:border-amber-300 light:text-amber-700',
  tagRemover:
    'bg-transparent border-0 text-muted-foreground text-xs cursor-pointer px-0.5 rounded-sm hover:text-canvas-danger',
  spinnerXs:
    'size-1.75 border-2 border-transparent border-t-current border-r-current rounded-full animate-spin inline-block shrink-0',

  // Seleção rápida
  btnSelecao:
    'border px-2.5 py-1.25 rounded-md text-xs font-medium cursor-pointer transition-all duration-150 inline-flex items-center gap-1.5',
  btnSelecaoNeutro:
    'bg-transparent border-border-strong text-foreground hover:bg-white/8 hover:border-primary hover:text-primary-light light:border-slate-300 light:text-slate-900 light:hover:bg-slate-100 light:hover:border-blue-600 light:hover:text-slate-900',
  btnSelecaoAnalisados:
    'bg-transparent border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/12 hover:border-emerald-400 hover:text-emerald-300 light:bg-emerald-50 light:border-emerald-200 light:text-emerald-800 light:hover:bg-emerald-100 light:hover:border-emerald-400 light:hover:text-emerald-900',
  btnSelecaoPendentes:
    'bg-transparent border-amber-500/40 text-amber-400 hover:bg-amber-500/12 hover:border-amber-400 hover:text-amber-200 light:bg-amber-50 light:border-amber-200 light:text-amber-800 light:hover:bg-amber-100 light:hover:border-amber-500 light:hover:text-amber-900',

  // Cards de repositório
  repoCard:
    'bg-card border border-border rounded-xl overflow-hidden shadow-[0_4px_16px] shadow-black/15 transition-colors duration-150 hover:border-border-strong light:bg-white light:border-slate-200 light:shadow-[0_2px_10px] light:shadow-black/4 light:hover:border-slate-200',
  repoCardHeader:
    'flex items-center justify-between px-5.5 py-4.5 bg-muted border-b border-border cursor-pointer transition-colors duration-150 gap-4 flex-wrap hover:bg-primary-glow focus-visible:-outline-offset-2 light:bg-slate-50 light:border-slate-200 light:hover:bg-slate-100',
  colunaSelecao: 'flex items-center justify-center mr-3 shrink-0',
  checkbox:
    'size-4.5 cursor-pointer accent-primary rounded focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-primary focus-visible:outline-offset-2',

  // Badges de fila (visual próprio; os de status usam BaseBadge)
  badgeFilaEnvio:
    'border inline-flex items-center gap-1.25 rounded px-2 py-0.75 text-[0.7rem] leading-none tracking-wide uppercase font-extrabold bg-amber-500/15 text-amber-400 border-amber-500/40 light:bg-amber-100 light:text-amber-700 light:border-amber-300',
  badgeFilaEnvioRodando:
    'border inline-flex items-center gap-1.25 rounded px-2 py-0.75 text-[0.7rem] leading-none tracking-wide uppercase font-extrabold bg-amber-500/25 text-yellow-200 border-amber-500 shadow-[0_0_10px] shadow-amber-500/30 animate-pulse-border light:bg-amber-200 light:text-amber-800 light:border-amber-500',
  badgeFilaAnalise:
    'border inline-flex items-center gap-1.5 rounded px-2 py-0.75 text-[0.7rem] leading-none tracking-wide uppercase font-extrabold bg-sky-400/15 text-sky-400 border-sky-400/40 light:bg-sky-100 light:text-sky-700 light:border-sky-300',
  badgeFilaRepo:
    'border inline-flex items-center gap-1.5 rounded px-2 py-0.75 text-[0.7rem] leading-none tracking-wide uppercase font-extrabold bg-amber-500/18 text-amber-400 border-amber-500/40 light:bg-amber-100 light:text-amber-700 light:border-amber-300',

  // Linha de commit
  commitRow:
    'flex items-center px-5 py-3.5 border-b border-b-border-strong border-l-3 cursor-pointer select-none transition-colors duration-150 last:border-b-0 focus-visible:-outline-offset-2 light:border-b-slate-200',
  commitRowOciosa:
    'border-l-transparent hover:bg-blue-500/5 focus-visible:bg-blue-500/9 light:hover:bg-slate-50',
  commitRowSelecionada:
    'border-l-primary bg-blue-500/8 hover:bg-blue-500/14 light:bg-blue-50 light:border-l-blue-600 light:hover:bg-blue-600/10',
  avatar:
    'size-9 rounded-full text-white flex items-center justify-center text-xs font-extrabold mr-3.5 shrink-0 border border-white/12 text-shadow-[0_1px_2px] text-shadow-black/35 shadow-[0_2px_4px] shadow-black/15',
  commitTitulo:
    'text-sm font-semibold text-foreground truncate max-w-135 tracking-[-0.01em] light:text-slate-900',
  commitAutorTempo: 'text-xs text-muted-foreground mt-0.5 light:text-slate-600',
  commitData: 'font-bold text-foreground light:text-slate-900',

  // Botões de ação da linha
  btnAcao:
    'inline-flex items-center justify-center w-8 h-7.5 p-0 rounded-md cursor-pointer border transition-all duration-150',
  btnOlho:
    'bg-card border-border-strong text-muted-foreground text-sm hover:text-white hover:bg-primary hover:border-primary hover:-translate-y-px hover:shadow-[0_2px_8px] hover:shadow-blue-500/35 light:bg-white light:border-slate-300 light:text-slate-600 light:hover:bg-blue-600 light:hover:border-blue-600 light:hover:text-white light:hover:shadow-blue-600/25',
  btnExcluir:
    'bg-transparent border-transparent text-canvas-danger opacity-85 text-sm hover:opacity-100 hover:bg-red-500/15 hover:border-red-500/35 hover:text-red-500 hover:-translate-y-px focus-visible:outline-red-500 light:text-red-600 light:hover:bg-red-100 light:hover:border-red-300 light:hover:text-red-700',
  btnSha:
    'inline-flex items-center justify-center font-mono text-xs font-bold border rounded-md px-2.5 py-1.25 tracking-[0.04em] cursor-pointer transition-all duration-150 min-w-20.5 h-7.5 hover:-translate-y-px',
  btnShaNormal:
    'text-code-foreground bg-code border-border-strong hover:text-primary-light hover:border-primary hover:bg-blue-500/12 light:bg-slate-50 light:text-slate-700 light:border-slate-300 light:hover:bg-blue-50 light:hover:text-blue-700 light:hover:border-blue-300',
  btnShaCopiado:
    'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 light:bg-emerald-100 light:text-emerald-700 light:border-emerald-400',

  // Barra de ações em lote
  statPill: 'text-xs px-2 py-0.75 rounded-md inline-flex items-center gap-1.5 border',
  btnReenfileirar:
    'px-5 py-2.5 text-[0.83rem] shadow-[0_4px_14px] shadow-blue-500/35 bg-amber-600 text-white border-0 rounded-lg hover:bg-amber-700 focus-visible:outline-white',

  // Modal de exclusão
  btnPerigo:
    'inline-flex items-center justify-center gap-2 leading-none bg-canvas-danger text-white border-2 border-border-strong rounded-none px-4.5 py-2 font-bold cursor-pointer text-sm tracking-wide shadow-[3px_3px_0] shadow-border-strong transition-[transform,box-shadow] duration-100 hover:-translate-y-0.5 hover:-translate-x-0.5 hover:shadow-[5px_5px_0] hover:shadow-border-strong hover:bg-canvas-danger-hover',
}

// Paleta determinística por repositório: `chip` (só tema escuro; o claro vem do chip) e `tag` (escuro + claro).
const CORES_REPO: Record<string, { chip: string; tag: string }> = {
  'repo-color-default': {
    chip: 'bg-slate-400/12 text-slate-300 border-slate-400/30 hover:border-primary hover:text-foreground',
    tag: 'bg-slate-400/12 text-slate-300 border-slate-400/30 light:bg-slate-100 light:text-slate-700 light:border-slate-300',
  },
  'repo-color-0': {
    chip: 'bg-sky-400/12 text-sky-400 border-sky-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-sky-400/12 text-sky-400 border-sky-400/35 light:bg-sky-100 light:text-sky-700 light:border-sky-300',
  },
  'repo-color-1': {
    chip: 'bg-purple-400/12 text-purple-400 border-purple-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-purple-400/12 text-purple-400 border-purple-400/35 light:bg-purple-100 light:text-purple-700 light:border-purple-300',
  },
  'repo-color-2': {
    chip: 'bg-emerald-400/12 text-emerald-400 border-emerald-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-emerald-400/12 text-emerald-400 border-emerald-400/35 light:bg-emerald-100 light:text-emerald-700 light:border-emerald-300',
  },
  'repo-color-3': {
    chip: 'bg-amber-400/12 text-amber-400 border-amber-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-amber-400/12 text-amber-400 border-amber-400/35 light:bg-amber-100 light:text-amber-700 light:border-amber-300',
  },
  'repo-color-4': {
    chip: 'bg-pink-400/12 text-pink-400 border-pink-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-pink-400/12 text-pink-400 border-pink-400/35 light:bg-pink-100 light:text-pink-700 light:border-pink-300',
  },
  'repo-color-5': {
    chip: 'bg-indigo-400/12 text-indigo-400 border-indigo-400/35 hover:border-primary hover:text-foreground',
    tag: 'bg-indigo-400/12 text-indigo-400 border-indigo-400/35 light:bg-indigo-100 light:text-indigo-700 light:border-indigo-300',
  },
}

function variantEnviadas(commit: CommitSummary): 'blue' | 'orange' | 'purple' {
  const enviadas = commit.atividades_enviadas || 0
  const total = commit.atividades_total || 0
  if (enviadas === total && total > 0) return 'blue'
  return enviadas > 0 ? 'orange' : 'purple'
}

const chipTodosAtivo = computed(() => repositorioFiltro.value === 'todos' && !apenasNaFila.value)

// Cor do avatar vem dos dados (hash do autor): única parte dinâmica, aplicada via style.
function atributosAvatar(nome: string) {
  return { style: { backgroundColor: obterCorAvatar(nome) } }
}

function classeChipContagem(ativo: boolean) {
  return [cls.chipCount, ativo ? 'bg-white/25 text-white' : cls.chipCountInativo]
}


const store = useCommitsStore()
const filaStore = useFilaStore()
const toastStore = useToastStore()
const showImport = ref(false)
const importing = ref(false)
const importError = ref('')
const form = ref({ commit_hashes: '' })

// Modo de visualização: 'repositorio' (padrão) ou 'data'
const visaoModo = ref<'repositorio' | 'data'>(
  (localStorage.getItem('nexus-commits-view-mode') as 'repositorio' | 'data') || 'repositorio'
)

// Filtros
const repositorioFiltro = ref<string>('todos')
const termoBusca = ref<string>('')
const apenasNaFila = ref<boolean>(false)

// Controle de colapso de cards de repositório
const reposColapsados = ref<Record<string, boolean>>({})

function isRepoColapsado(nome: string): boolean {
  return !!reposColapsados.value[nome]
}

function toggleColapsoRepo(nome: string) {
  reposColapsados.value[nome] = !reposColapsados.value[nome]
}

function setVisaoModo(modo: 'repositorio' | 'data') {
  visaoModo.value = modo
  localStorage.setItem('nexus-commits-view-mode', modo)
}

function toggleFiltroRepo(nome?: string) {
  const repoNome = nome || 'Sem repositório'
  if (repositorioFiltro.value === repoNome) {
    repositorioFiltro.value = 'todos'
  } else {
    repositorioFiltro.value = repoNome
  }
}

function limparFiltroFila() {
  repositorioFiltro.value = 'todos'
  apenasNaFila.value = false
}

function limparTodosFiltros() {
  repositorioFiltro.value = 'todos'
  termoBusca.value = ''
  apenasNaFila.value = false
}

const commitParaDeletar = ref<any>(null)
const exibindoModalConfirmacao = ref(false)

const importModalRef = ref<InstanceType<typeof BaseModal> | null>(null)
const confirmModalRef = ref<InstanceType<typeof BaseModal> | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

function handleImportKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    showImport.value = false
  }
  if (e.key === 'Tab' && importModalRef.value?.panel) {
    const focusable = importModalRef.value.panel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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

function handleConfirmKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    fecharModalConfirmacao()
  }
  if (e.key === 'Tab' && confirmModalRef.value?.panel) {
    const focusable = confirmModalRef.value.panel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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

watch(showImport, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleImportKeydown)
    nextTick(() => {
      const textarea = importModalRef.value?.panel?.querySelector('textarea') as HTMLElement
      textarea?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleImportKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

watch(exibindoModalConfirmacao, (newVal) => {
  if (newVal) {
    previousActiveElement.value = document.activeElement as HTMLElement
    document.addEventListener('keydown', handleConfirmKeydown)
    nextTick(() => {
      const btn = confirmModalRef.value?.panel?.querySelector('[data-modal-actions] button') as HTMLElement
      btn?.focus()
    })
  } else {
    document.removeEventListener('keydown', handleConfirmKeydown)
    if (previousActiveElement.value) {
      previousActiveElement.value.focus()
      previousActiveElement.value = null
    }
  }
})

// Mapeamento dinâmico de tarefas ativas na fila por Commit
interface FilaCommitInfo {
  total: number
  analisando: boolean
  envios: number
  running: number
  pending: number
}

const filaPorCommit = computed<Record<string, FilaCommitInfo>>(() => {
  const map: Record<string, FilaCommitInfo> = {}

  for (const job of filaStore.jobs) {
    // Apenas jobs em andamento (pending ou running)
    if (job.status !== 'pending' && job.status !== 'running') continue
    if (!job.commit_id) continue

    const sha = job.commit_id
    // Procura correspondência na lista de commits
    const commitMatch = store.commits.find(c => 
      c.id === sha || c.id.startsWith(sha) || sha.startsWith(c.id)
    )
    const chave = commitMatch ? commitMatch.id : sha

    if (!map[chave]) {
      map[chave] = { total: 0, analisando: false, envios: 0, running: 0, pending: 0 }
    }

    map[chave].total++
    if (job.tipo === 'analise') {
      map[chave].analisando = true
    } else {
      map[chave].envios++
    }

    if (job.status === 'running') {
      map[chave].running++
    } else {
      map[chave].pending++
    }
  }

  return map
})

function obterInfoFila(commitId: string): FilaCommitInfo | undefined {
  return filaPorCommit.value[commitId]
}

const totalTarefasAtivasNaFila = computed(() => {
  return Object.values(filaPorCommit.value).reduce((acc, curr) => acc + curr.total, 0)
})

// Auto-atualização: quando tarefas terminam no Celery, atualiza a lista de commits discretamente
watch(() => filaStore.jobs, (newJobs, oldJobs) => {
  if (!oldJobs || oldJobs.length === 0) return
  const concluidosNovos = newJobs.filter(j => j.status === 'done' || j.status === 'error').length
  const concluidosAntigos = oldJobs.filter(j => j.status === 'done' || j.status === 'error').length
  if (concluidosNovos > concluidosAntigos) {
    store.fetchCommits()
  }
}, { deep: true })

onMounted(async () => {
  if (route.query.repo) {
    repositorioFiltro.value = String(route.query.repo)
  }
  if (route.query.fila === 'true') {
    apenasNaFila.value = true
  }
  await store.fetchCommits()
  await filaStore.fetchJobs(true)
  filaStore.startPolling()
})

function formatarDataCabecalho(dataStr: string): string {
  if (!dataStr) return ''
  const parts = dataStr.split('/')
  if (parts.length === 3) {
    const dia = parseInt(parts[0], 10)
    const mesIdx = parseInt(parts[1], 10) - 1
    const ano = parts[2]
    const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const mesNome = meses[mesIdx] || parts[1]
    return `${dia} ${mesNome}, ${ano}`
  }
  return dataStr
}

function formatarDataCurta(isoOuData?: string): string {
  if (!isoOuData) return ''
  if (isoOuData.includes('/')) {
    const parts = isoOuData.split('/')
    if (parts.length === 3) {
      const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
      const mesIdx = parseInt(parts[1], 10) - 1
      return `${parts[0]} ${meses[mesIdx] || parts[1]}`
    }
  }
  try {
    const d = new Date(isoOuData)
    if (!isNaN(d.getTime())) {
      const dia = d.getDate()
      const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
      return `${dia} ${meses[d.getMonth()]}`
    }
  } catch {
    // fallback
  }
  return isoOuData
}

function obterIniciais(nome: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

function obterCorAvatar(nome: string): string {
  if (!nome) return '#777'
  let hash = 0
  for (let i = 0; i < nome.length; i++) {
    hash = nome.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    '#007acc', '#3fb950', '#f85149', '#d29922', '#bc8cff', '#1f6feb', '#30b6e6'
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
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

function obterTempoRelativo(isoStr?: string): string {
  if (!isoStr) return 'some time ago'
  try {
    const d = new Date(isoStr)
    const agora = new Date()
    const diffMs = agora.getTime() - d.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'just now'
    if (diffMin === 1) return '1 minute ago'
    if (diffMin < 60) return `${diffMin} minutes ago`
    if (diffHour === 1) return '1 hour ago'
    if (diffHour < 24) return `${diffHour} hours ago`
    if (diffDay === 1) return 'yesterday'
    return `${diffDay} days ago`
  } catch {
    return 'some time ago'
  }
}

const shaCopiadoId = ref<string | null>(null)
let shaCopiadoTimer: number | null = null

async function copiarSHA(sha: string) {
  try {
    await navigator.clipboard.writeText(sha)
    shaCopiadoId.value = sha
    if (shaCopiadoTimer) clearTimeout(shaCopiadoTimer)
    shaCopiadoTimer = window.setTimeout(() => {
      shaCopiadoId.value = null
    }, 1800)
    toastStore.addToast('SHA copiado para a área de transferência!', 'success')
  } catch (err) {
    console.error('Falha ao copiar SHA:', err)
  }
}

function abrirModalConfirmacao(commit: any) {
  commitParaDeletar.value = commit
  exibindoModalConfirmacao.value = true
}

function fecharModalConfirmacao() {
  commitParaDeletar.value = null
  exibindoModalConfirmacao.value = false
}

async function confirmarExclusao() {
  if (!commitParaDeletar.value) return
  try {
    await store.deletar(commitParaDeletar.value.id)
    toastStore.addToast('Commit e análise excluídos com sucesso.', 'info')
  } catch (e: any) {
    toastStore.addToast(`Erro ao excluir: ${e.response?.data?.detail ?? String(e)}`, 'error')
  } finally {
    fecharModalConfirmacao()
  }
}

function obterTimestamp(c: CommitSummary): number {
  if (c.data_autor) {
    const t = new Date(c.data_autor).getTime()
    if (!isNaN(t)) return t
  }
  if (c.data) {
    const parts = c.data.split('/')
    if (parts.length === 3) {
      const dia = parseInt(parts[0], 10)
      const mes = parseInt(parts[1], 10) - 1
      const ano = parseInt(parts[2], 10)
      const t = new Date(ano, mes, dia).getTime()
      if (!isNaN(t)) return t
    }
  }
  if (c.importado_em) {
    const t = new Date(c.importado_em).getTime()
    if (!isNaN(t)) return t
  }
  return 0
}

function obterDataParaAgrupamento(commit: CommitSummary): string {
  if (commit.data_autor) {
    try {
      const d = new Date(commit.data_autor)
      if (!isNaN(d.getTime())) {
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const ano = d.getFullYear()
        return `${dia}/${mes}/${ano}`
      }
    } catch {
      // fallback
    }
  }
  return commit.data
}

// Resumo consolidado de todos os repositórios
const repositoriosResumo = computed(() => {
  const map: Record<string, {
    nome: string
    totalCommits: number
    analisados: number
    pendentes: number
    totalHpa: number
    totalNaFila: number
    colorClass: string
    ultimoTimestamp: number
    ultimoCommitData?: string
  }> = {}

  for (const c of store.commits) {
    const repoNome = c.projeto?.trim() || 'Sem repositório'
    if (!map[repoNome]) {
      map[repoNome] = {
        nome: repoNome,
        totalCommits: 0,
        analisados: 0,
        pendentes: 0,
        totalHpa: 0,
        totalNaFila: 0,
        colorClass: obterClasseCorRepo(repoNome),
        ultimoTimestamp: 0,
        ultimoCommitData: undefined,
      }
    }
    const item = map[repoNome]
    item.totalCommits++
    if (c.analisado) {
      item.analisados++
    } else {
      item.pendentes++
    }
    if (c.hpa_total) {
      item.totalHpa += c.hpa_total
    }

    const infoFila = filaPorCommit.value[c.id]
    if (infoFila && infoFila.total > 0) {
      item.totalNaFila += infoFila.total
    }

    const t = obterTimestamp(c)
    if (t > item.ultimoTimestamp) {
      item.ultimoTimestamp = t
      item.ultimoCommitData = formatarDataCabecalho(obterDataParaAgrupamento(c))
    }
  }

  return Object.values(map).sort((a, b) => b.totalCommits - a.totalCommits)
})

// Commits filtrados por repositório, busca e fila
const commitsFiltrados = computed(() => {
  let list = store.commits

  // Filtro por repositório
  if (repositorioFiltro.value !== 'todos') {
    list = list.filter(c => {
      const repoNome = c.projeto?.trim() || 'Sem repositório'
      return repoNome === repositorioFiltro.value
    })
  }

  // Filtro por "Apenas na Fila"
  if (apenasNaFila.value) {
    list = list.filter(c => {
      const info = filaPorCommit.value[c.id]
      return !!info && info.total > 0
    })
  }

  // Filtro textual
  if (termoBusca.value.trim()) {
    const q = termoBusca.value.trim().toLowerCase()
    list = list.filter(c => {
      const msg = (c.mensagem || '').toLowerCase()
      const id = (c.id || '').toLowerCase()
      const autor = (c.autor || '').toLowerCase()
      const proj = (c.projeto || '').toLowerCase()
      return msg.includes(q) || id.includes(q) || autor.includes(q) || proj.includes(q)
    })
  }

  return list
})

// Agrupamento por Data (para o modo Linha do Tempo)
const commitsAgrupadosPorData = computed(() => {
  const grupos: Record<string, CommitSummary[]> = {}
  
  for (const commit of commitsFiltrados.value) {
    const dataAgrupamento = obterDataParaAgrupamento(commit)
    const dataFormatada = formatarDataCabecalho(dataAgrupamento)
    if (!grupos[dataFormatada]) {
      grupos[dataFormatada] = []
    }
    grupos[dataFormatada].push(commit)
  }
  
  for (const chave of Object.keys(grupos)) {
    grupos[chave].sort((a, b) => obterTimestamp(b) - obterTimestamp(a))
  }
  
  const chavesOrdenadas = Object.keys(grupos).sort((a, b) => {
    const timeA = obterTimestamp(grupos[a][0])
    const timeB = obterTimestamp(grupos[b][0])
    return timeB - timeA
  })
  
  return chavesOrdenadas.map(chave => ({
    data: chave,
    commits: grupos[chave]
  }))
})

// Agrupamento por Repositório (para o modo Por Repositório)
const commitsAgrupadosPorRepo = computed(() => {
  const map: Record<string, {
    nome: string
    commits: CommitSummary[]
    analisados: number
    pendentes: number
    totalHpa: number
    totalNaFila: number
    colorClass: string
    ultimoCommitData?: string
  }> = {}

  for (const c of commitsFiltrados.value) {
    const repoNome = c.projeto?.trim() || 'Sem repositório'
    if (!map[repoNome]) {
      map[repoNome] = {
        nome: repoNome,
        commits: [],
        analisados: 0,
        pendentes: 0,
        totalHpa: 0,
        totalNaFila: 0,
        colorClass: obterClasseCorRepo(repoNome),
        ultimoCommitData: undefined
      }
    }
    const r = map[repoNome]
    r.commits.push(c)
    if (c.analisado) {
      r.analisados++
    } else {
      r.pendentes++
    }
    if (c.hpa_total) {
      r.totalHpa += c.hpa_total
    }
    const info = filaPorCommit.value[c.id]
    if (info && info.total > 0) {
      r.totalNaFila += info.total
    }
  }

  // Ordena os commits dentro de cada repositório por data decrescente
  const resultado = Object.values(map).map(r => {
    r.commits.sort((a, b) => obterTimestamp(b) - obterTimestamp(a))
    if (r.commits.length > 0) {
      r.ultimoCommitData = formatarDataCabecalho(obterDataParaAgrupamento(r.commits[0]))
    }
    return r
  })

  // Ordena os repositórios pelo volume de commits
  return resultado.sort((a, b) => b.commits.length - a.commits.length)
})

async function importar() {
  importing.value = true
  importError.value = ''
  
  const urls = form.value.commit_hashes
    .split('\n')
    .map(h => h.trim())
    .filter(h => h.length > 0)
    
  if (urls.length === 0) {
    importError.value = 'Informe pelo menos uma URL completa de commit.'
    importing.value = false
    return
  }

  const urlsInvalidas = urls.filter(u => !u.startsWith('http://') && !u.startsWith('https://'))
  if (urlsInvalidas.length > 0) {
    importError.value = 'Todas as linhas devem ser URLs completas do GitLab (começando com http:// ou https://).'
    importing.value = false
    return
  }

  let sucessos = 0
  let falhas = 0
  const erros: string[] = []

  for (const url of urls) {
    try {
      await store.importar(url)
      sucessos++
    } catch (e: any) {
      falhas++
      const msg = e.response?.data?.detail ?? e.message ?? String(e)
      erros.push(msg)
      console.error(`Erro ao importar commit ${url}:`, msg, e)
    }
  }

  showImport.value = false
  form.value.commit_hashes = ''
  importing.value = false
  
  if (falhas > 0) {
    const errorMsg = erros.length > 0 ? erros[0] : 'Erro desconhecido'
    toastStore.addToast(`Importação concluída com falhas. Sucessos: ${sucessos}, Falhas: ${falhas}. Detalhe: ${errorMsg}`, 'error')
  } else {
    toastStore.addToast(`Importação concluída com sucesso! (${sucessos} commit(s))`, 'success')
  }
}

// ─── SELEÇÃO EM LOTE DE COMMITS ──────────────────────────────────────────
const selecionados = ref<string[]>([])
const enfileirandoEnvio = ref(false)
const enfileirandoAnalise = ref(false)

function isCommitSelecionado(id: string): boolean {
  return selecionados.value.includes(id)
}

function toggleSelectCommit(id: string) {
  const idx = selecionados.value.indexOf(id)
  if (idx >= 0) {
    selecionados.value.splice(idx, 1)
  } else {
    selecionados.value.push(id)
  }
}

function isRepoTotalmenteSelecionado(repo: { commits: CommitSummary[] }): boolean {
  if (!repo.commits.length) return false
  return repo.commits.every(c => selecionados.value.includes(c.id))
}

function isRepoParcialmenteSelecionado(repo: { commits: CommitSummary[] }): boolean {
  const marcados = repo.commits.filter(c => selecionados.value.includes(c.id)).length
  return marcados > 0 && marcados < repo.commits.length
}

function toggleSelecionarTodosRepo(repo: { commits: CommitSummary[] }) {
  if (isRepoTotalmenteSelecionado(repo)) {
    const ids = new Set(repo.commits.map(c => c.id))
    selecionados.value = selecionados.value.filter(id => !ids.has(id))
  } else {
    const idsParaAdicionar = repo.commits.map(c => c.id).filter(id => !selecionados.value.includes(id))
    selecionados.value.push(...idsParaAdicionar)
  }
}

function selecionarTodosExibidos() {
  const ids = commitsFiltrados.value.map(c => c.id)
  const novos = ids.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...novos)
}

function selecionarApenasAnalisados() {
  const ids = commitsFiltrados.value.filter(c => c.analisado).map(c => c.id)
  const novos = ids.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...novos)
}

function selecionarApenasPendentes() {
  const ids = commitsFiltrados.value.filter(c => !c.analisado).map(c => c.id)
  const novos = ids.filter(id => !selecionados.value.includes(id))
  selecionados.value.push(...novos)
}

function desmarcarTodos() {
  selecionados.value = []
}

const totalCommitsAnalisadosExibidos = computed(() => {
  return commitsFiltrados.value.filter(c => c.analisado).length
})

const totalCommitsPendentesExibidos = computed(() => {
  return commitsFiltrados.value.filter(c => !c.analisado).length
})

const commitsSelecionadosObjs = computed(() => {
  const set = new Set(selecionados.value)
  return store.commits.filter(c => set.has(c.id))
})

const totalTarefasProntas = computed(() => {
  return commitsSelecionadosObjs.value.reduce((acc, c) => {
    if (!c.analisado) return acc
    const total = c.atividades_total || 0
    const enviadas = c.atividades_enviadas || 0
    return acc + Math.max(0, total - enviadas)
  }, 0)
})

const totalTarefasJaEnviadas = computed(() => {
  return commitsSelecionadosObjs.value.reduce((acc, c) => acc + (c.atividades_enviadas || 0), 0)
})

const totalHpaSelecionado = computed(() => {
  return commitsSelecionadosObjs.value.reduce((acc, c) => acc + (c.hpa_total || 0), 0)
})

const totalCommitsAnalisadosSelecionados = computed(() => {
  return commitsSelecionadosObjs.value.filter(c => c.analisado).length
})

const totalCommitsPendentesSelecionados = computed(() => {
  return commitsSelecionadosObjs.value.filter(c => !c.analisado).length
})

const totalReposSelecionadosCount = computed(() => {
  const repos = new Set<string>()
  for (const c of commitsSelecionadosObjs.value) {
    repos.add(c.projeto?.trim() || 'Sem repositório')
  }
  return repos.size
})

async function executarEnfileirarTarefasLote() {
  if (selecionados.value.length === 0) return
  enfileirandoEnvio.value = true
  try {
    await filaStore.enfileirarEnvioLote(selecionados.value, false)
    await store.fetchCommits()
    desmarcarTodos()
  } catch {
    // Erro já tratado pelo toastStore
  } finally {
    enfileirandoEnvio.value = false
  }
}

async function executarEnfileirarTarefasLoteForcado() {
  if (selecionados.value.length === 0) return
  const confirmar = confirm(`Todas as tarefas já constam como enviadas. Deseja reenfileirar todas as tarefas destes commits para o Munka mesmo assim?`)
  if (!confirmar) return

  enfileirandoEnvio.value = true
  try {
    await filaStore.enfileirarEnvioLote(selecionados.value, true)
    await store.fetchCommits()
    desmarcarTodos()
  } catch {
    // Erro já tratado pelo toastStore
  } finally {
    enfileirandoEnvio.value = false
  }
}

async function executarEnfileirarAnaliseLote() {
  const pendentesIds = commitsSelecionadosObjs.value.filter(c => !c.analisado).map(c => c.id)
  if (pendentesIds.length === 0) return

  enfileirandoAnalise.value = true
  try {
    await filaStore.enfileirarAnalise(pendentesIds, 'Gemini 3.8 Flash')
    await store.fetchCommits()
    toastStore.addToast(`Análise de IA enfileirada com sucesso para ${pendentesIds.length} commit(s)!`, 'success')
  } catch {
    // Erro já tratado pelo toastStore
  } finally {
    enfileirandoAnalise.value = false
  }
}
</script>
