<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Commits</h1>
        <HelpModal title="Como funciona esta página" :items="helpItems" />
      </div>
      <button class="btn-primary" @click="$router.push('/importar')">
        <i class="fa-solid fa-file-import" aria-hidden="true"></i>
        <span>+ Importar Commit</span>
      </button>
    </div>

    <!-- Modal de importação -->
    <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
      <div ref="importModalRef" class="modal" role="dialog" aria-modal="true" aria-labelledby="import-modal-title">
        <h2 id="import-modal-title">Importar Commits do GitLab (Lote)</h2>
        <label for="import-commit-hashes">URLs Completas dos Commits do GitLab (uma por linha)</label>
        <textarea 
          id="import-commit-hashes"
          v-model="form.commit_hashes" 
          placeholder="Ex:&#10;https://gitlab.suaorganizacao.com/grupo/projeto/-/commit/abc123hash" 
          rows="6"
        ></textarea>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showImport = false">Cancelar</button>
          <button class="btn-primary" :disabled="importing || !form.commit_hashes.trim()" @click="importar">
            {{ importing ? 'Importando...' : 'Importar' }}
          </button>
        </div>
        <p v-if="importError" class="error">{{ importError }}</p>
      </div>
    </div>

    <!-- Estado de Carregamento -->
    <div v-if="store.loading" class="loading" role="status" aria-live="polite">Carregando commits...</div>

    <!-- Estado Vazio -->
    <div v-else-if="store.commits.length === 0" class="empty">
      Nenhum commit importado. Clique em "+ Importar Commit" para começar.
    </div>

    <!-- Área Principal de Commits & Repositórios -->
    <div v-else class="commits-content-area">
      
      <!-- Barra de Controle: Alternador de Visualização, Busca e Filtros Rápidos -->
      <section class="repo-control-bar" aria-label="Controles de exibição e filtros por repositório">
        <div class="control-top-row">
          
          <!-- Alternador de Modos (Tabs Acessíveis) -->
          <div class="view-mode-tabs" role="tablist" aria-label="Modo de visualização dos commits">
            <button 
              id="tab-modo-repo"
              type="button"
              role="tab"
              class="mode-tab-btn" 
              :class="{ active: visaoModo === 'repositorio' }"
              :aria-selected="visaoModo === 'repositorio'"
              aria-controls="panel-commits-view"
              @click="setVisaoModo('repositorio')"
            >
              <i class="fa-solid fa-folder-tree" aria-hidden="true" style="font-size: 0.95rem;"></i>
              <span>Por Repositório</span>
              <span class="mode-count-badge" :title="`${repositoriosResumo.length} repositórios ativos`">
                {{ repositoriosResumo.length }}
              </span>
            </button>

            <button 
              id="tab-modo-data"
              type="button"
              role="tab"
              class="mode-tab-btn" 
              :class="{ active: visaoModo === 'data' }"
              :aria-selected="visaoModo === 'data'"
              aria-controls="panel-commits-view"
              @click="setVisaoModo('data')"
            >
              <i class="fa-solid fa-calendar-days" aria-hidden="true" style="font-size: 0.95rem;"></i>
              <span>Linha do Tempo (Data)</span>
              <span class="mode-count-badge" :title="`${commitsFiltrados.length} commits`">
                {{ commitsFiltrados.length }}
              </span>
            </button>
          </div>

          <!-- Busca de Commits / Repositórios -->
          <div class="search-box">
            <i class="fa-solid fa-magnifying-glass search-icon" aria-hidden="true" style="color: var(--text-muted); font-size: 0.85rem;"></i>
            <input 
              type="search"
              v-model="termoBusca"
              placeholder="Buscar por mensagem, SHA ou repositório..."
              class="search-input"
              aria-label="Buscar commits por mensagem, hash ou repositório"
            />
            <button 
              v-if="termoBusca" 
              type="button" 
              class="clear-search-btn" 
              @click="termoBusca = ''" 
              aria-label="Limpar texto da busca"
              title="Limpar busca"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
            </button>
          </div>
        </div>

        <!-- Chips de Seleção Rápida por Repositório e Status de Fila -->
        <div class="repo-chips-wrapper" role="region" aria-label="Filtrar por repositório específico ou fila">
          <span class="chips-label">Filtros:</span>
          <div class="chips-list">
            <button 
              type="button" 
              class="repo-chip" 
              :class="{ active: repositorioFiltro === 'todos' && !apenasNaFila }"
              :aria-pressed="repositorioFiltro === 'todos' && !apenasNaFila"
              @click="limparFiltroFila"
            >
              <span>Todos</span>
              <span class="chip-count">{{ store.commits.length }}</span>
            </button>

            <!-- Chip Especial: Apenas na Fila -->
            <button 
              v-if="totalTarefasAtivasNaFila > 0"
              type="button" 
              class="repo-chip chip-na-fila" 
              :class="{ active: apenasNaFila }"
              :aria-pressed="apenasNaFila"
              @click="apenasNaFila = !apenasNaFila"
              :title="`Filtrar commits com tarefas ativas na fila (${totalTarefasAtivasNaFila} tarefas ativas)`"
            >
              <span class="chip-dot pulse" aria-hidden="true"></span>
              <span>Na Fila</span>
              <span class="chip-count">{{ totalTarefasAtivasNaFila }}</span>
            </button>

            <!-- Chips de Repositórios -->
            <button 
              v-for="repo in repositoriosResumo" 
              :key="repo.nome"
              type="button" 
              class="repo-chip" 
              :class="[repo.colorClass, { active: repositorioFiltro === repo.nome }]"
              :aria-pressed="repositorioFiltro === repo.nome"
              @click="toggleFiltroRepo(repo.nome)"
              :title="`Filtrar commits do repositório ${repo.nome} (${repo.totalCommits} commits)`"
            >
              <span class="chip-dot" aria-hidden="true"></span>
              <span class="chip-name">{{ repo.nome }}</span>
              <span class="chip-count">{{ repo.totalCommits }}</span>
              <span v-if="repo.totalNaFila > 0" class="chip-fila-badge" title="Tarefas na fila">
                {{ repo.totalNaFila }} fila
              </span>
            </button>
          </div>
        </div>

        <!-- Barra de Status com Filtros Ativos -->
        <div v-if="repositorioFiltro !== 'todos' || termoBusca || apenasNaFila" class="active-filter-bar" role="status" aria-live="polite">
          <div class="filter-bar-items">
            <span class="filter-bar-label">Filtros ativos:</span>
            <span v-if="apenasNaFila" class="filter-tag filter-tag-amber">
              <span class="spinner-dot-xs"></span>
              <span>Apenas na Fila ({{ totalTarefasAtivasNaFila }} tarefas)</span>
              <button type="button" class="tag-remove-btn" @click="apenasNaFila = false" aria-label="Remover filtro de fila">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span v-if="repositorioFiltro !== 'todos'" class="filter-tag">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
              </svg>
              <span>{{ repositorioFiltro }}</span>
              <button type="button" class="tag-remove-btn" @click="repositorioFiltro = 'todos'" aria-label="Remover filtro deste repositório">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span v-if="termoBusca" class="filter-tag">
              <span>"{{ termoBusca }}"</span>
              <button type="button" class="tag-remove-btn" @click="termoBusca = ''" aria-label="Remover filtro de texto">
                <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              </button>
            </span>
            <span class="filter-match-count">
              ({{ commitsFiltrados.length }} commit{{ commitsFiltrados.length !== 1 ? 's' : '' }} encontrado{{ commitsFiltrados.length !== 1 ? 's' : '' }})
            </span>
          </div>
          <button type="button" class="btn-clear-all" @click="limparTodosFiltros">
            Limpar Filtros
          </button>
        </div>

        <!-- Barra de Ações Rápidas de Seleção em Lote -->
        <div class="selection-quick-bar" role="toolbar" aria-label="Ações de seleção rápida de commits">
          <div class="selection-quick-left">
            <span class="selection-quick-label">
              <i class="fa-solid fa-list-check" aria-hidden="true"></i>
              <span>Seleção em lote:</span>
            </span>
            <button 
              type="button" 
              class="btn-quick-select"
              @click="selecionarTodosExibidos"
              :title="`Selecionar todos os ${commitsFiltrados.length} commits exibidos`"
            >
              Selecionar Todos ({{ commitsFiltrados.length }})
            </button>
            <button 
              v-if="totalCommitsAnalisadosExibidos > 0"
              type="button" 
              class="btn-quick-select btn-quick-analisados"
              @click="selecionarApenasAnalisados"
              :title="`Selecionar apenas os ${totalCommitsAnalisadosExibidos} commits analisados (com tarefas)`"
            >
              <i class="fa-solid fa-bolt" aria-hidden="true"></i>
              Apenas Analisados ({{ totalCommitsAnalisadosExibidos }})
            </button>
            <button 
              v-if="totalCommitsPendentesExibidos > 0"
              type="button" 
              class="btn-quick-select btn-quick-pendentes"
              @click="selecionarApenasPendentes"
              :title="`Selecionar apenas os ${totalCommitsPendentesExibidos} commits pendentes de análise`"
            >
              <i class="fa-solid fa-clock" aria-hidden="true"></i>
              Apenas Pendentes ({{ totalCommitsPendentesExibidos }})
            </button>
          </div>

          <div class="selection-quick-right" v-if="selecionados.length > 0">
            <span class="selected-pill">
              <strong>{{ selecionados.length }}</strong> selecionado{{ selecionados.length > 1 ? 's' : '' }}
            </span>
            <button 
              type="button" 
              class="btn-quick-clear" 
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
      <div v-if="commitsFiltrados.length === 0" class="empty">
        <p>Nenhum commit encontrado para os critérios selecionados.</p>
        <button type="button" class="btn-ghost" @click="limparTodosFiltros" style="margin-top: 0.75rem;">
          Limpar Filtros
        </button>
      </div>

      <!-- PAINEL 1: VISÃO POR REPOSITÓRIO -->
      <div 
        v-else-if="visaoModo === 'repositorio'" 
        id="panel-commits-view" 
        class="repo-cards-container" 
        role="tabpanel" 
        aria-labelledby="tab-modo-repo"
      >
        <div 
          v-for="repo in commitsAgrupadosPorRepo" 
          :key="repo.nome" 
          class="repo-card"
        >
          <!-- Cabeçalho do Card de Repositório -->
          <div 
            class="repo-card-header"
            tabindex="0"
            role="button"
            :aria-expanded="!isRepoColapsado(repo.nome)"
            @click="toggleColapsoRepo(repo.nome)"
            @keydown.enter.prevent="toggleColapsoRepo(repo.nome)"
            @keydown.space.prevent="toggleColapsoRepo(repo.nome)"
          >
            <div class="repo-header-main">
              <!-- Checkbox para selecionar/desmarcar todos do repositório -->
              <div class="repo-select-col" @click.stop @keydown.stop>
                <input 
                  type="checkbox"
                  class="repo-checkbox"
                  :checked="isRepoTotalmenteSelecionado(repo)"
                  :indeterminate="isRepoParcialmenteSelecionado(repo)"
                  @change="toggleSelecionarTodosRepo(repo)"
                  :aria-label="`Selecionar todos os commits do repositório ${repo.nome}`"
                  :title="`Selecionar todos os commits do repositório ${repo.nome}`"
                />
              </div>
              <div class="repo-avatar-icon" :class="repo.colorClass">
                <i class="fa-brands fa-git-alt" aria-hidden="true" style="font-size: 1.15rem;"></i>
              </div>
              <div class="repo-header-text">
                <div class="repo-title-row">
                  <h3 class="repo-title">{{ repo.nome }}</h3>
                  <span class="badge badge-repo-count">{{ repo.commits.length }} commit{{ repo.commits.length > 1 ? 's' : '' }}</span>
                </div>
                <span class="repo-subtitle">
                  <span v-if="repo.ultimoCommitData">Mais recente em: <strong>{{ repo.ultimoCommitData }}</strong></span>
                  <span v-else>Repositório de atividades</span>
                </span>
              </div>
            </div>

            <!-- Lado Direito: Métricas e Indicador de Toggle -->
            <div class="repo-header-actions" @click.stop>
              <div class="repo-stats-pills">
                <!-- Badge Dinâmico de Tarefas na Fila do Repositório -->
                <span 
                  v-if="repo.totalNaFila > 0" 
                  class="badge badge-status badge-fila-repo" 
                  :title="`${repo.totalNaFila} tarefa(s) deste repositório estão na fila de execução`"
                >
                  <span class="spinner-dot-xs"></span>
                  {{ repo.totalNaFila }} na fila
                </span>

                <span class="badge badge-status badge-green" :title="`${repo.analisados} commit(s) analisado(s)`">
                  <i class="fa-solid fa-circle-check" aria-hidden="true" style="margin-right: 2px;"></i>
                  {{ repo.analisados }} Analisado{{ repo.analisados !== 1 ? 's' : '' }}
                </span>
                <span v-if="repo.pendentes > 0" class="badge badge-status badge-gray" :title="`${repo.pendentes} commit(s) pendente(s)`">
                  <i class="fa-solid fa-clock" aria-hidden="true" style="margin-right: 2px;"></i>
                  {{ repo.pendentes }} Pendente{{ repo.pendentes !== 1 ? 's' : '' }}
                </span>
                <span v-if="repo.totalHpa > 0" class="badge badge-status badge-hpa" :title="`${repo.totalHpa} horas HPA estimadas`">
                  <i class="fa-solid fa-bolt" aria-hidden="true" style="margin-right: 2px;"></i>
                  {{ repo.totalHpa }}h HPA
                </span>
              </div>

              <!-- Botão Expandir / Recolher -->
              <button 
                type="button" 
                class="repo-toggle-btn"
                @click="toggleColapsoRepo(repo.nome)"
                :aria-expanded="!isRepoColapsado(repo.nome)"
                :aria-label="isRepoColapsado(repo.nome) ? `Expandir commits do repositório ${repo.nome}` : `Recolher commits do repositório ${repo.nome}`"
                :title="isRepoColapsado(repo.nome) ? 'Expandir commits' : 'Recolher commits'"
              >
                <i 
                  class="fa-solid fa-chevron-down chevron-icon" 
                  :class="{ rotated: isRepoColapsado(repo.nome) }"
                  aria-hidden="true"
                ></i>
              </button>
            </div>
          </div>

          <!-- Lista de Commits do Repositório (colapsável) -->
          <div v-show="!isRepoColapsado(repo.nome)" class="repo-commits-list">
            <div 
              v-for="commit in repo.commits" 
              :key="commit.id" 
              class="commit-row"
              :class="{ 'is-selected': isCommitSelecionado(commit.id) }"
              tabindex="0"
              role="row"
              :aria-selected="isCommitSelecionado(commit.id)"
              @click="toggleSelectCommit(commit.id)"
              @keydown.enter.prevent="toggleSelectCommit(commit.id)"
              @keydown.space.prevent="toggleSelectCommit(commit.id)"
            >
              <!-- Seleção do Commit (Checkbox) -->
              <div class="commit-select-col" @click.stop @keydown.stop>
                <input 
                  type="checkbox"
                  :id="`select-repo-${commit.id}`"
                  class="commit-checkbox"
                  :checked="isCommitSelecionado(commit.id)"
                  @change="toggleSelectCommit(commit.id)"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem || 'sem mensagem'}`"
                />
              </div>

              <!-- Lado Esquerdo: Avatar do Autor -->
              <div 
                class="commit-avatar" 
                :style="{ backgroundColor: obterCorAvatar(commit.autor) }"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Centro: Mensagem e Metadados -->
              <div class="commit-info">
                <div class="commit-msg-container">
                  <span class="commit-msg-title" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>

                  <!-- Badges de Status, Envio e FILA -->
                  <div class="commit-row-badges">
                    <span class="badge badge-status" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
                      {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                    </span>

                    <template v-if="commit.analisado">
                      <span class="badge badge-status" :class="
                        (commit.atividades_enviadas || 0) === (commit.atividades_total || 0) && (commit.atividades_total || 0) > 0
                          ? 'badge-blue'
                          : (commit.atividades_enviadas || 0) > 0
                            ? 'badge-orange'
                            : 'badge-purple'
                      ">
                        {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
                      </span>
                    </template>

                    <!-- BADGE DINÂMICO DE FILA -->
                    <template v-if="obterInfoFila(commit.id)">
                      <span 
                        v-if="obterInfoFila(commit.id)!.analisando" 
                        class="badge badge-status badge-fila-analise"
                        title="Análise de IA deste commit aguardando ou processando na fila"
                      >
                        <span class="pulse-dot"></span>
                        Análise na fila
                      </span>

                      <span 
                        v-if="obterInfoFila(commit.id)!.envios > 0" 
                        class="badge badge-status badge-fila-envio"
                        :class="{ 'is-running': obterInfoFila(commit.id)!.running > 0 }"
                        :title="`${obterInfoFila(commit.id)!.envios} tarefa(s) deste commit na fila (${obterInfoFila(commit.id)!.running} em execução, ${obterInfoFila(commit.id)!.pending} aguardando)`"
                      >
                        <span class="spinner-dot-xs" v-if="obterInfoFila(commit.id)!.running > 0"></span>
                        <i class="fa-solid fa-clock" aria-hidden="true" style="font-size: 0.72rem; margin-right: 2px;" v-else></i>
                        {{ obterInfoFila(commit.id)!.envios }} na fila
                      </span>
                    </template>
                  </div>
                </div>
                <span class="commit-author-time">
                  <span class="commit-date-badge">{{ formatarDataCurta(commit.data_autor || commit.data) }}</span>
                  · {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
                </span>
              </div>

              <!-- Lado Direito: Ações, SHA e Olho para Entrar -->
              <div class="commit-actions" @click.stop>
                <!-- Botão Excluir -->
                <button 
                  type="button"
                  class="action-btn delete-btn" 
                  @click.stop="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                </button>

                <!-- Botão SHA interativo (copia ao clicar) -->
                <button 
                  type="button"
                  class="sha-btn" 
                  :class="{ 'is-copied': shaCopiadoId === commit.id }"
                  @click.stop="copiarSHA(commit.id)"
                  :title="shaCopiadoId === commit.id ? 'SHA copiado!' : 'Clique para copiar o SHA completo'"
                  :aria-label="`Copiar hash SHA ${commit.id}`"
                >
                  <span v-if="shaCopiadoId === commit.id" class="sha-copied-badge">
                    <i class="fa-solid fa-check" aria-hidden="true"></i>
                    <span>Copiado!</span>
                  </span>
                  <span v-else class="sha-code-text">
                    {{ commit.id.slice(0, 8) }}
                  </span>
                </button>

                <!-- Botão Olho: ÚNICO método para entrar no commit -->
                <button 
                  type="button"
                  class="action-btn eye-btn" 
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
        class="commit-list-grouped" 
        role="tabpanel" 
        aria-labelledby="tab-modo-data"
      >
        <!-- Percorre os dias agrupados -->
        <div v-for="grupo in commitsAgrupadosPorData" :key="grupo.data" class="date-group">
          
          <!-- Cabeçalho do dia: "31 Ago, 2026 2 commits" -->
          <div class="date-group-header">
            <span class="date-text">{{ grupo.data }}</span>
            <span class="commit-count-text">{{ grupo.commits.length }} commit{{ grupo.commits.length > 1 ? 's' : '' }}</span>
          </div>

          <!-- Lista de commits desse dia -->
          <div class="date-group-commits">
            <div 
              v-for="commit in grupo.commits" 
              :key="commit.id" 
              class="commit-row"
              :class="{ 'is-selected': isCommitSelecionado(commit.id) }"
              tabindex="0"
              role="row"
              :aria-selected="isCommitSelecionado(commit.id)"
              @click="toggleSelectCommit(commit.id)"
              @keydown.enter.prevent="toggleSelectCommit(commit.id)"
              @keydown.space.prevent="toggleSelectCommit(commit.id)"
            >
              <!-- Seleção do Commit (Checkbox) -->
              <div class="commit-select-col" @click.stop @keydown.stop>
                <input 
                  type="checkbox"
                  :id="`select-data-${commit.id}`"
                  class="commit-checkbox"
                  :checked="isCommitSelecionado(commit.id)"
                  @change="toggleSelectCommit(commit.id)"
                  :aria-label="`Selecionar commit ${commit.id.slice(0, 8)}: ${commit.mensagem || 'sem mensagem'}`"
                />
              </div>

              <!-- Lado Esquerdo: Avatar do Autor -->
              <div 
                class="commit-avatar" 
                :style="{ backgroundColor: obterCorAvatar(commit.autor) }"
                :title="commit.autor"
              >
                {{ obterIniciais(commit.autor) }}
              </div>

              <!-- Centro: Mensagem, Repositório e Metadados -->
              <div class="commit-info">
                <div class="commit-msg-container">
                  <!-- Tag / Badge destacada do Repositório -->
                  <button 
                    type="button" 
                    class="badge-repo-pill" 
                    :class="obterClasseCorRepo(commit.projeto)" 
                    @click.stop="toggleFiltroRepo(commit.projeto)"
                    :title="`Filtrar pelo repositório ${commit.projeto || 'Sem repositório'}`"
                    aria-label="Filtrar por este repositório"
                  >
                    <i class="fa-brands fa-gitlab" aria-hidden="true" style="font-size: 0.78rem;"></i>
                    <span>{{ commit.projeto || 'Sem repositório' }}</span>
                  </button>

                  <span class="commit-msg-title" :title="commit.mensagem">
                    {{ commit.mensagem || '(sem mensagem)' }}
                  </span>

                  <!-- Badges de Status, Envio e FILA -->
                  <div class="commit-row-badges">
                    <span class="badge badge-status" :class="commit.analisado ? 'badge-green' : 'badge-gray'">
                      {{ commit.analisado ? 'Analisado' : 'Pendente' }}
                    </span>

                    <template v-if="commit.analisado">
                      <span class="badge badge-status" :class="
                        (commit.atividades_enviadas || 0) === (commit.atividades_total || 0) && (commit.atividades_total || 0) > 0
                          ? 'badge-blue'
                          : (commit.atividades_enviadas || 0) > 0
                            ? 'badge-orange'
                            : 'badge-purple'
                      ">
                        {{ commit.atividades_enviadas || 0 }}/{{ commit.atividades_total || 0 }} env.
                      </span>
                    </template>

                    <!-- BADGE DINÂMICO DE FILA -->
                    <template v-if="obterInfoFila(commit.id)">
                      <span 
                        v-if="obterInfoFila(commit.id)!.analisando" 
                        class="badge badge-status badge-fila-analise"
                        title="Análise de IA deste commit aguardando ou processando na fila"
                      >
                        <span class="pulse-dot"></span>
                        Análise na fila
                      </span>

                      <span 
                        v-if="obterInfoFila(commit.id)!.envios > 0" 
                        class="badge badge-status badge-fila-envio"
                        :class="{ 'is-running': obterInfoFila(commit.id)!.running > 0 }"
                        :title="`${obterInfoFila(commit.id)!.envios} tarefa(s) deste commit na fila (${obterInfoFila(commit.id)!.running} em execução, ${obterInfoFila(commit.id)!.pending} aguardando)`"
                      >
                        <span class="spinner-dot-xs" v-if="obterInfoFila(commit.id)!.running > 0"></span>
                        <i class="fa-solid fa-clock" aria-hidden="true" style="font-size: 0.72rem; margin-right: 2px;" v-else></i>
                        {{ obterInfoFila(commit.id)!.envios }} na fila
                      </span>
                    </template>
                  </div>
                </div>
                <span class="commit-author-time">
                  {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
                </span>
              </div>

              <!-- Lado Direito: Ações, SHA e Olho para Entrar -->
              <div class="commit-actions" @click.stop>
                <!-- Botão Excluir -->
                <button 
                  type="button"
                  class="action-btn delete-btn" 
                  @click.stop="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <i class="fa-solid fa-trash-can" aria-hidden="true"></i>
                </button>

                <!-- Botão SHA interativo (copia ao clicar) -->
                <button 
                  type="button"
                  class="sha-btn" 
                  :class="{ 'is-copied': shaCopiadoId === commit.id }"
                  @click.stop="copiarSHA(commit.id)"
                  :title="shaCopiadoId === commit.id ? 'SHA copiado!' : 'Clique para copiar o SHA completo'"
                  :aria-label="`Copiar hash SHA ${commit.id}`"
                >
                  <span v-if="shaCopiadoId === commit.id" class="sha-copied-badge">
                    <i class="fa-solid fa-check" aria-hidden="true"></i>
                    <span>Copiado!</span>
                  </span>
                  <span v-else class="sha-code-text">
                    {{ commit.id.slice(0, 8) }}
                  </span>
                </button>

                <!-- Botão Olho: ÚNICO método para entrar no commit -->
                <button 
                  type="button"
                  class="action-btn eye-btn" 
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
    <div v-if="exibindoModalConfirmacao" class="modal-overlay" @click.self="fecharModalConfirmacao">
      <div ref="confirmModalRef" class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
        <h2 id="confirm-modal-title">Confirmar Exclusão</h2>
        <p>Tem certeza de que deseja excluir o commit <strong>{{ commitParaDeletar?.id.slice(0, 8) }}</strong> e sua respectiva análise? Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="fecharModalConfirmacao">Cancelar</button>
          <button class="btn-danger" @click="confirmarExclusao">Excluir</button>
        </div>
      </div>
    </div>

    <!-- BARRA FLUTUANTE DE AÇÕES EM LOTE (STICKY FOOTER) -->
    <transition name="slide-up">
      <div 
        v-if="selecionados.length > 0" 
        class="bulk-action-footer" 
        role="region" 
        aria-label="Ações para commits selecionados"
        aria-live="polite"
      >
        <div class="bulk-footer-content">
          <div class="bulk-info-col">
            <div class="bulk-counter-row">
              <span class="bulk-badge-selected">
                <i class="fa-solid fa-check-double" aria-hidden="true"></i>
                {{ selecionados.length }} commit{{ selecionados.length > 1 ? 's' : '' }} marcado{{ selecionados.length > 1 ? 's' : '' }}
              </span>
              <span class="bulk-repo-tag" v-if="totalReposSelecionadosCount > 0">
                ({{ totalReposSelecionadosCount }} repositório{{ totalReposSelecionadosCount > 1 ? 's' : '' }})
              </span>
            </div>

            <div class="bulk-stats-row">
              <span v-if="totalTarefasProntas > 0" class="bulk-stat-pill stat-tasks" title="Tarefas prontas para enfileiramento no Munka">
                <i class="fa-solid fa-bolt" aria-hidden="true"></i>
                <strong>{{ totalTarefasProntas }}</strong> tarefa{{ totalTarefasProntas > 1 ? 's' : '' }} pronta{{ totalTarefasProntas > 1 ? 's' : '' }} ({{ totalHpaSelecionado.toFixed(1) }}h HPA)
              </span>
              <span v-else-if="totalCommitsAnalisadosSelecionados > 0 && totalTarefasJaEnviadas > 0" class="bulk-stat-pill stat-sent" title="Todas as tarefas destes commits já foram enviadas">
                <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
                {{ totalTarefasJaEnviadas }} tarefa(s) já enviada(s)
              </span>
              <span v-if="totalCommitsPendentesSelecionados > 0" class="bulk-stat-pill stat-pending" title="Commits ainda não analisados pela IA">
                <i class="fa-solid fa-clock" aria-hidden="true"></i>
                <strong>{{ totalCommitsPendentesSelecionados }}</strong> commit{{ totalCommitsPendentesSelecionados > 1 ? 's' : '' }} pendente{{ totalCommitsPendentesSelecionados > 1 ? 's' : '' }} de análise
              </span>
            </div>
          </div>

          <div class="bulk-actions-col">
            <button 
              type="button" 
              class="btn-ghost btn-sm" 
              @click="desmarcarTodos"
              aria-label="Limpar seleção atual de commits"
            >
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
              <span>Limpar</span>
            </button>

            <!-- Botão Principal: Enfileirar Tarefas no Munka -->
            <button 
              v-if="totalTarefasProntas > 0"
              type="button" 
              class="btn-primary btn-bulk-send" 
              :disabled="enfileirandoEnvio" 
              @click="executarEnfileirarTarefasLote"
              :aria-label="`Enfileirar ${totalTarefasProntas} tarefas no Munka`"
            >
              <span v-if="enfileirandoEnvio" class="spinner-dot-sm" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-paper-plane" aria-hidden="true"></i>
              <span>{{ enfileirandoEnvio ? 'Enfileirando...' : `Adicionar ${totalTarefasProntas} Tarefa(s) na Fila Munka` }}</span>
            </button>

            <!-- Botão Alternativo: Reenfileirar tarefas já enviadas -->
            <button 
              v-else-if="totalCommitsAnalisadosSelecionados > 0 && totalTarefasJaEnviadas > 0"
              type="button" 
              class="btn-warning btn-bulk-send" 
              :disabled="enfileirandoEnvio" 
              @click="executarEnfileirarTarefasLoteForcado"
              :aria-label="`Reenfileirar ${totalTarefasJaEnviadas} tarefas no Munka`"
              title="Todas as tarefas já foram enviadas. Clique para reenfileirar novamente."
            >
              <span v-if="enfileirandoEnvio" class="spinner-dot-sm" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-rotate-right" aria-hidden="true"></i>
              <span>{{ enfileirandoEnvio ? 'Reenfileirando...' : `Reenfileirar ${totalTarefasJaEnviadas} Tarefa(s)` }}</span>
            </button>

            <!-- Botão Secundário: Enfileirar Análise AI para pendentes -->
            <button 
              v-if="totalCommitsPendentesSelecionados > 0"
              type="button" 
              class="btn-secondary btn-bulk-ai" 
              :disabled="enfileirandoAnalise" 
              @click="executarEnfileirarAnaliseLote"
              :aria-label="`Enfileirar ${totalCommitsPendentesSelecionados} commits para análise de IA`"
            >
              <span v-if="enfileirandoAnalise" class="spinner-dot-sm" aria-hidden="true"></span>
              <i v-else class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>
              <span>{{ enfileirandoAnalise ? 'Enfileirando IA...' : `Analisar ${totalCommitsPendentesSelecionados} com IA` }}</span>
            </button>

            <!-- Atalho para a página da fila -->
            <router-link 
              to="/fila" 
              class="btn-ghost btn-sm btn-view-queue"
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
import HelpModal from '../components/HelpModal.vue'
import type { CommitSummary } from '../api'

const route = useRoute()

const helpItems = [
  { title: 'Seleção em Lote e Automação', text: 'Clique na barra do commit ou marque o checkbox para selecioná-lo. Use os botões de seleção rápida no topo ou a barra flutuante para adicionar tarefas diretamente na fila do Munka!' },
  { title: 'Abrir Detalhes do Commit', text: 'Para evitar cliques acidentais, use o ícone de olho na lateral direita de cada commit para entrar e ver suas atividades e detalhes.' },
  { title: 'Copiar Hash SHA', text: 'Clique diretamente no número do hash SHA para copiá-lo para a área de transferência.' },
  { title: 'Visualização por Repositório', text: 'Permite inspecionar commits organizados por projeto do GitLab com métricas consolidadas (tarefas, status e horas HPA).' },
  { title: 'Linha do Tempo', text: 'Exibe a ordem cronológica dos commits de todos os repositórios, com badges coloridos identificando a origem de cada commit.' },
  { title: 'Dinamismo da Fila em Tempo Real', text: 'Os commits mostram um badge dinâmico indicando quantas tarefas daquele commit estão na fila do Celery aguardando ou em processamento.' },
  { title: 'Importar Commit', text: 'Clique em "+ Importar Commit" e informe um ou mais SHAs ou URLs completos do GitLab (um por linha) para importação.' },
]

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

const importModalRef = ref<HTMLElement | null>(null)
const confirmModalRef = ref<HTMLElement | null>(null)
const previousActiveElement = ref<HTMLElement | null>(null)

function handleImportKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    showImport.value = false
  }
  if (e.key === 'Tab' && importModalRef.value) {
    const focusable = importModalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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
  if (e.key === 'Tab' && confirmModalRef.value) {
    const focusable = confirmModalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
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
      const textarea = importModalRef.value?.querySelector('textarea') as HTMLElement
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
      const btn = confirmModalRef.value?.querySelector('.modal-actions button') as HTMLElement
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

<style scoped>
.title-row { display: flex; align-items: center; gap: 0.5rem; }

.commits-content-area {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ── BARRA DE CONTROLE E FILTROS ── */
.repo-control-bar {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
}

.control-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

/* Tabs do Modo de Visualização */
.view-mode-tabs {
  display: inline-flex;
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}

.mode-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.9rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted, #8b949e);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
}

.mode-tab-btn:hover {
  color: var(--text, #f0f6fc);
}

.mode-tab-btn:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: 2px;
}

.mode-tab-btn.active {
  background: var(--card-bg, #161b22);
  color: var(--text, #f0f6fc);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.mode-count-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
  background: var(--accent-glow, rgba(56, 189, 248, 0.15));
  color: var(--accent, #58a6ff);
  border: 1px solid var(--border, #30363d);
}

/* Campo de Busca */
.search-box {
  display: flex;
  align-items: center;
  position: relative;
  flex: 1;
  max-width: 420px;
  min-width: 260px;
}

.search-icon {
  position: absolute;
  left: 0.85rem;
  color: var(--text-muted, #8b949e);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.55rem 2.2rem 0.55rem 2.4rem;
  font-size: 0.88rem;
  background: var(--bg, #0d1117);
  color: var(--text, #f0f6fc);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus {
  border-color: var(--accent, #58a6ff);
}

.clear-search-btn {
  position: absolute;
  right: 0.6rem;
  background: transparent;
  border: none;
  color: var(--text-muted, #8b949e);
  font-size: 0.85rem;
  padding: 0.2rem 0.4rem;
  cursor: pointer;
  border-radius: 4px;
}

.clear-search-btn:hover {
  color: var(--text, #f0f6fc);
}

/* Chips de Repositórios e Fila */
.repo-chips-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-top: 0.25rem;
  border-top: 1px dashed var(--border, #30363d);
}

.chips-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #8b949e);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.chips-list {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.repo-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 20px;
  background: var(--bg, #0d1117);
  color: var(--text-muted, #8b949e);
  border: 1px solid var(--border, #30363d);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.repo-chip:hover {
  border-color: var(--accent, #58a6ff);
  color: var(--text, #f0f6fc);
  transform: translateY(-1px);
}

.repo-chip.active {
  background: var(--accent, #388bfd);
  color: #ffffff;
  border-color: var(--accent, #388bfd);
  box-shadow: 0 2px 8px rgba(56, 139, 253, 0.3);
}

.repo-chip.active .chip-count {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

/* Chip especial Na Fila */
.repo-chip.chip-na-fila {
  border-color: rgba(245, 158, 11, 0.4);
  color: #fbbf24;
}

.repo-chip.chip-na-fila:hover {
  border-color: #f59e0b;
}

.repo-chip.chip-na-fila.active {
  background: var(--warning, #d97706);
  color: #ffffff;
  border-color: #d97706;
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.chip-dot.pulse {
  animation: pulse-dot-anim 1.5s infinite;
}

@keyframes pulse-dot-anim {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.chip-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-count {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted, #8b949e);
}

.chip-fila-badge {
  font-size: 0.68rem;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Barra de Filtros Ativos */
.active-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  padding: 0.5rem 0.85rem;
  flex-wrap: wrap;
}

.filter-bar-items {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.filter-bar-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted, #8b949e);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  background: var(--card-bg, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text, #f0f6fc);
}

.filter-tag-amber {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.35);
  color: #fbbf24;
}

.tag-remove-btn {
  background: transparent;
  border: none;
  color: var(--text-muted, #8b949e);
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 3px;
}

.tag-remove-btn:hover {
  color: #f85149;
}

.filter-match-count {
  font-size: 0.8rem;
  color: var(--text-muted, #8b949e);
}

.btn-clear-all {
  background: transparent;
  border: none;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--accent, #58a6ff);
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}

.btn-clear-all:hover {
  text-decoration: underline;
}

/* ── CARDS DE REPOSITÓRIO (MODO "POR REPOSITÓRIO") ── */
.repo-cards-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.repo-card {
  background: var(--card-bg, #161b22);
  border: 1px solid var(--card-border, #30363d);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: border-color 0.15s ease;
}

.repo-card:hover {
  border-color: var(--border, #475569);
}

.repo-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.35rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.02));
  border-bottom: 1px solid var(--card-border, #30363d);
  cursor: pointer;
  transition: background 0.15s;
  gap: 1rem;
  flex-wrap: wrap;
}

.repo-card-header:hover {
  background: var(--accent-glow, rgba(56, 189, 248, 0.08));
}

.repo-card-header:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: -2px;
}

.repo-header-main {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
  flex: 1;
}

.repo-avatar-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid transparent;
}

.repo-header-text {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.repo-title-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.repo-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text, #f0f6fc);
  letter-spacing: -0.01em;
  word-break: break-word;
}

.badge-repo-count {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  color: var(--text-muted, #8b949e);
}

.repo-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted, #8b949e);
}

.repo-subtitle strong {
  color: var(--text, #f0f6fc);
}

.repo-header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

.repo-stats-pills {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.repo-toggle-btn {
  background: var(--bg, #0d1117);
  border: 1px solid var(--border, #30363d);
  color: var(--text-muted, #8b949e);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.repo-toggle-btn:hover {
  color: var(--text, #f0f6fc);
  border-color: var(--accent, #58a6ff);
}

.chevron-icon {
  transition: transform 0.2s ease;
}

.chevron-icon.rotated {
  transform: rotate(-90deg);
}

.repo-commits-list {
  display: flex;
  flex-direction: column;
}

/* ── LINHA DO TEMPO (MODO "POR DATA") ── */
.commit-list-grouped {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.date-group {
  display: flex;
  flex-direction: column;
}

.date-group-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--card-border, #30363d);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  font-size: 0.88rem;
}

.date-text {
  font-weight: 800;
  color: var(--text, #f0f6fc);
  font-size: 0.95rem;
}

.commit-count-text {
  color: var(--text-muted, #8b949e);
  font-size: 0.82rem;
  font-weight: 500;
}

.date-group-commits {
  border: 1px solid var(--card-border, #30363d);
  border-top: none;
  background: var(--card-bg, #161b22);
  display: flex;
  flex-direction: column;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
}

/* ── LINHA DE COMMIT INDIVIDUAL ── */
.commit-row {
  display: flex;
  align-items: center;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid var(--border, #334155);
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: background 0.15s ease, border-left-color 0.15s ease;
  outline: none;
  user-select: none;
}

.commit-row:last-child {
  border-bottom: none;
}

.commit-row:hover {
  background: rgba(59, 130, 246, 0.05);
}

.commit-row:focus-visible {
  background: rgba(59, 130, 246, 0.09);
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: -2px;
}

.commit-row.is-selected {
  background: rgba(59, 130, 246, 0.09);
  border-left-color: var(--accent, #3b82f6);
}

.commit-row.is-selected:hover {
  background: rgba(59, 130, 246, 0.14);
}

.commit-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 800;
  margin-right: 0.9rem;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.commit-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.commit-msg-container {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

/* Badge do Repositório (Tag destacada) */
.badge-repo-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  max-width: 220px;
  text-decoration: none;
  outline: none;
}

.badge-repo-pill:hover {
  filter: brightness(1.15);
  transform: translateY(-1px);
}

.badge-repo-pill:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: 2px;
}

.commit-msg-title {
  font-size: 0.93rem;
  font-weight: 600;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 540px;
  letter-spacing: -0.01em;
}

.commit-row-badges {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  align-items: center;
}

.badge-status {
  font-size: 0.7rem;
  padding: 3px 8px;
  font-weight: 700;
  border-radius: 4px;
  letter-spacing: 0.02em;
}

/* ── BADGES DINÂMICOS DE FILA (ESTADO ATIVO) ── */
.badge-fila-envio {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.badge-fila-envio.is-running {
  background: rgba(245, 158, 11, 0.25);
  border-color: #f59e0b;
  color: #fef08a;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
  animation: pulse-border 2s infinite ease-in-out;
}

.badge-fila-analise {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 800;
}

.badge-fila-repo {
  background: rgba(245, 158, 11, 0.18);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 800;
}

.spinner-dot-xs {
  width: 7px;
  height: 7px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-right-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
  flex-shrink: 0;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
  animation: pulse-dot-anim 1.2s infinite ease-in-out;
  flex-shrink: 0;
}

.queue-icon-txt {
  font-size: 0.72rem;
  line-height: 1;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
  70% { box-shadow: 0 0 0 5px rgba(245, 158, 11, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.commit-author-time {
  font-size: 0.8rem;
  color: var(--text-muted, #8b949e);
  margin-top: 0.1rem;
}

.commit-date-badge {
  font-weight: 700;
  color: var(--text, #f0f6fc);
}

/* ── AÇÕES DA LINHA DO COMMIT ── */
.commit-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-shrink: 0;
  margin-left: 0.75rem;
}

/* Botão SHA interativo (copia ao clicar) */
.sha-btn {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--sha-box-color, #94a3b8);
  background: var(--sha-box-bg, rgba(255, 255, 255, 0.05));
  border: 1px solid var(--border, #334155);
  border-radius: 6px;
  padding: 0.28rem 0.65rem;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 82px;
  height: 30px;
  outline: none;
  box-sizing: border-box;
}

.sha-btn:hover {
  color: var(--accent-light, #60a5fa);
  border-color: var(--accent, #3b82f6);
  background: rgba(59, 130, 246, 0.12);
  transform: translateY(-1px);
}

.sha-btn:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

.sha-btn.is-copied {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.5);
}

.sha-copied-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.sha-code-text {
  font-size: 0.78rem;
  letter-spacing: 0.04em;
}

/* Botões de Ação Padronizados */
.action-btn {
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--border, #475569);
  border-radius: 7px;
  color: var(--text-muted, #cbd5e1);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 30px;
  padding: 0;
  transition: all 0.15s ease;
  outline: none;
  box-sizing: border-box;
}

.action-btn:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

/* Botão Olho (Entrar no Commit) */
.eye-btn {
  font-size: 0.85rem;
}

.eye-btn:hover {
  color: #ffffff;
  background: var(--accent, #3b82f6);
  border-color: var(--accent, #3b82f6);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
}

/* Botão Deletar */
.delete-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #f85149;
  opacity: 0.85;
  font-size: 0.9rem;
}

.delete-btn:hover {
  opacity: 1;
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.35);
  color: #ef4444;
  transform: translateY(-1px);
}

.delete-btn:focus-visible {
  outline: 2px solid #ef4444;
  outline-offset: 2px;
}

.btn-danger {
  background: #f85149;
  color: #ffffff;
  border: 2px solid var(--border);
  border-radius: 0;
  padding: 0.5rem 1.1rem;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.88rem;
  letter-spacing: 0.02em;
  box-shadow: 3px 3px 0 var(--border);
  transition: transform 0.1s, box-shadow 0.1s;
}

.btn-danger:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: 5px 5px 0 var(--border);
  background: #ff6b6b;
}

/* ── PALETA DE CORES DETERMINÍSTICA PARA REPOSITÓRIOS (WCAG AA CONFORME) ── */
/* Modo Escuro (Default) */
.repo-color-default {
  background: rgba(148, 163, 184, 0.12);
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.repo-color-0 {
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.35);
}

.repo-color-1 {
  background: rgba(192, 132, 252, 0.12);
  color: #c084fc; /* taste-skill-ignore */
  border: 1px solid rgba(192, 132, 252, 0.35);
}

.repo-color-2 {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.35);
}

.repo-color-3 {
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.35);
}

.repo-color-4 {
  background: rgba(244, 114, 182, 0.12);
  color: #f472b6;
  border: 1px solid rgba(244, 114, 182, 0.35);
}

.repo-color-5 {
  background: rgba(129, 140, 248, 0.12);
  color: #818cf8; /* taste-skill-ignore */
  border: 1px solid rgba(129, 140, 248, 0.35);
}

/* Modo Claro Adaptativo */
:global([data-theme="light"]) .repo-color-default {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}

:global([data-theme="light"]) .repo-color-0 {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #7dd3fc;
}

:global([data-theme="light"]) .repo-color-1 {
  background: #f3e8ff;
  color: #7e22ce;
  border: 1px solid #d8b4fe;
}

:global([data-theme="light"]) .repo-color-2 {
  background: #d1fae5;
  color: #047857;
  border: 1px solid #6ee7b7;
}

:global([data-theme="light"]) .repo-color-3 {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fcd34d;
}

:global([data-theme="light"]) .repo-color-4 {
  background: #fce7f3;
  color: #be185d;
  border: 1px solid #f9a8d4;
}

:global([data-theme="light"]) .repo-color-5 {
  background: #e0e7ff;
  color: #4338ca;
  border: 1px solid #a5b4fc;
}

:global([data-theme="light"]) .badge-fila-envio {
  background: #fef3c7;
  color: #b45309;
  border-color: #fcd34d;
}

:global([data-theme="light"]) .badge-fila-envio.is-running {
  background: #fde68a;
  color: #92400e;
  border-color: #f59e0b;
}

:global([data-theme="light"]) .badge-fila-analise {
  background: #e0f2fe;
  color: #0369a1;
  border-color: #7dd3fc;
}

:global([data-theme="light"]) .badge-fila-repo {
  background: #fef3c7;
  color: #b45309;
  border-color: #fcd34d;
}

:global([data-theme="light"]) .filter-tag-amber {
  background: #fef3c7;
  color: #b45309;
  border-color: #fcd34d;
}

/* ── ESTILOS DE SELEÇÃO EM LOTE E CHECKBOXES (A11Y) ── */
.repo-select-col,
.commit-select-col {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.repo-checkbox,
.commit-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent, #3b82f6);
  border-radius: 4px;
}

.repo-checkbox:focus-visible,
.commit-checkbox:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

.commit-row.is-selected {
  background: rgba(59, 130, 246, 0.08);
  border-left: 3px solid var(--accent, #3b82f6);
}

.commit-row.is-selected:hover {
  background: rgba(59, 130, 246, 0.14);
}

/* ── BARRA DE SELEÇÃO RÁPIDA ── */
.selection-quick-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  background: var(--header-group-bg, rgba(255, 255, 255, 0.03));
  border-radius: 8px;
  border: 1px solid var(--card-border, #334155);
}

.selection-quick-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.selection-quick-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted, #cbd5e1);
  margin-right: 0.25rem;
}

.btn-quick-select {
  background: transparent;
  border: 1px solid var(--border, #475569);
  color: var(--text, #f8fafc);
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-quick-select:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent, #3b82f6);
  color: var(--accent-light, #60a5fa);
}

.btn-quick-select:focus-visible {
  outline: 2px solid var(--accent, #3b82f6);
  outline-offset: 2px;
}

.btn-quick-analisados {
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

.btn-quick-analisados:hover {
  background: rgba(16, 185, 129, 0.12);
  border-color: #34d399;
  color: #6ee7b7;
}

.btn-quick-pendentes {
  border-color: rgba(245, 158, 11, 0.4);
  color: #fbbf24;
}

.btn-quick-pendentes:hover {
  background: rgba(245, 158, 11, 0.12);
  border-color: #fbbf24;
  color: #fde68a;
}

.selection-quick-right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.selected-pill {
  font-size: 0.8rem;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  color: var(--accent-light, #60a5fa);
  border: 1px solid rgba(59, 130, 246, 0.35);
  font-weight: 600;
}

.btn-quick-clear {
  background: transparent;
  border: none;
  color: var(--text-muted, #cbd5e1);
  font-size: 0.78rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: color 0.15s ease;
}

.btn-quick-clear:hover {
  color: var(--error, #ef4444);
}

.btn-quick-clear:focus-visible {
  outline: 2px solid var(--error, #ef4444);
  outline-offset: 2px;
}

/* ── BARRA FLUTUANTE DE AÇÕES EM LOTE (STICKY FOOTER) ── */
.bulk-action-footer {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 3rem);
  max-width: 1100px;
  background: var(--card-bg, #1e293b);
  border: 1px solid var(--accent, #3b82f6);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.5), 0 0 20px var(--accent-glow, rgba(59, 130, 246, 0.3));
  border-radius: 14px;
  padding: 0.9rem 1.4rem;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.bulk-footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.bulk-info-col {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.bulk-counter-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.bulk-badge-selected {
  font-weight: 700;
  font-size: 0.98rem;
  color: var(--text, #f8fafc);
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.bulk-badge-selected i {
  color: var(--accent-light, #60a5fa);
}

.bulk-repo-tag {
  font-size: 0.82rem;
  color: var(--text-muted, #cbd5e1);
}

.bulk-stats-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.bulk-stat-pill {
  font-size: 0.78rem;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.bulk-stat-pill.stat-tasks {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.bulk-stat-pill.stat-sent {
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.bulk-stat-pill.stat-pending {
  background: rgba(245, 158, 11, 0.15);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.bulk-actions-col {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.btn-bulk-send {
  font-weight: 700;
  padding: 0.6rem 1.25rem;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.btn-bulk-send:focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}

.btn-bulk-ai {
  font-size: 0.85rem;
  padding: 0.6rem 1rem;
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc; /* taste-skill-ignore */
  border: 1px solid rgba(168, 85, 247, 0.4);
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.15s ease;
}

.btn-bulk-ai:hover {
  background: rgba(168, 85, 247, 0.3);
  border-color: #c084fc; /* taste-skill-ignore */
}

.btn-bulk-ai:focus-visible {
  outline: 2px solid #c084fc; /* taste-skill-ignore */
  outline-offset: 2px;
}

.btn-view-queue {
  font-size: 0.82rem;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-warning {
  background: #d97706;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  padding: 0.6rem 1.1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: background 0.15s ease;
}

.btn-warning:hover {
  background: #b45309;
}

.btn-warning:focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}

/* Animação slide-up */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}

/* Modo Claro (A11Y High Contrast & Design Taste) */
:global([data-theme="light"]) .repo-control-bar {
  background: #ffffff;
  border-color: #e2e8f0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

:global([data-theme="light"]) .view-mode-tabs {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .mode-tab-btn {
  color: #475569;
}

:global([data-theme="light"]) .mode-tab-btn:hover {
  color: #0f172a;
}

:global([data-theme="light"]) .mode-tab-btn.active {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

:global([data-theme="light"]) .mode-count-badge {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

:global([data-theme="light"]) .search-input {
  background: #ffffff;
  color: #0f172a;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .search-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

:global([data-theme="light"]) .repo-chip {
  background: #ffffff;
  color: #334155;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .repo-chip:hover {
  background: #f8fafc;
  border-color: #2563eb;
  color: #0f172a;
}

:global([data-theme="light"]) .repo-chip.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

:global([data-theme="light"]) .chip-count {
  background: #f1f5f9;
  color: #475569;
}

:global([data-theme="light"]) .repo-card {
  background: #ffffff;
  border-color: #e2e8f0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

:global([data-theme="light"]) .repo-card-header {
  background: #f8fafc;
  border-bottom-color: #e2e8f0;
}

:global([data-theme="light"]) .repo-card-header:hover {
  background: #f1f5f9;
}

:global([data-theme="light"]) .repo-title {
  color: #0f172a;
}

:global([data-theme="light"]) .badge-repo-count {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #334155;
}

:global([data-theme="light"]) .repo-toggle-btn {
  background: #ffffff;
  border-color: #cbd5e1;
  color: #475569;
}

:global([data-theme="light"]) .repo-toggle-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
}

:global([data-theme="light"]) .date-group-header {
  background: #f8fafc;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .date-text {
  color: #0f172a;
}

:global([data-theme="light"]) .commit-count-text {
  color: #475569;
}

:global([data-theme="light"]) .date-group-commits {
  background: #ffffff;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .commit-row {
  border-bottom-color: #e2e8f0;
}

:global([data-theme="light"]) .commit-row:hover {
  background: #f8fafc;
}

:global([data-theme="light"]) .commit-row.is-selected {
  background: #f0f7ff;
  border-left-color: #2563eb;
}

:global([data-theme="light"]) .commit-row.is-selected:hover {
  background: #e6f0fc;
}

:global([data-theme="light"]) .commit-msg-title {
  color: #0f172a;
}

:global([data-theme="light"]) .commit-author-time {
  color: #475569;
}

:global([data-theme="light"]) .commit-date-badge {
  color: #0f172a;
}

:global([data-theme="light"]) .sha-btn {
  background: #f8fafc;
  color: #334155;
  border-color: #cbd5e1;
}

:global([data-theme="light"]) .sha-btn:hover {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #93c5fd;
}

:global([data-theme="light"]) .sha-btn.is-copied {
  background: #d1fae5;
  color: #047857;
  border-color: #34d399;
}

:global([data-theme="light"]) .action-btn {
  background: #ffffff;
  border-color: #cbd5e1;
  color: #475569;
}

:global([data-theme="light"]) .eye-btn:hover {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

:global([data-theme="light"]) .delete-btn {
  background: transparent;
  border-color: transparent;
  color: #dc2626;
}

:global([data-theme="light"]) .delete-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

:global([data-theme="light"]) .selection-quick-bar {
  background: #f8fafc;
  border-color: #e2e8f0;
}

:global([data-theme="light"]) .selection-quick-label {
  color: #475569;
}

:global([data-theme="light"]) .btn-quick-select {
  border-color: #cbd5e1;
  color: #0f172a;
}

:global([data-theme="light"]) .btn-quick-select:hover {
  background: #f1f5f9;
  border-color: #2563eb;
}

:global([data-theme="light"]) .btn-quick-analisados {
  background: #ecfdf5;
  border-color: #a7f3d0;
  color: #065f46;
}

:global([data-theme="light"]) .btn-quick-analisados:hover {
  background: #d1fae5;
  border-color: #34d399;
  color: #064e3b;
}

:global([data-theme="light"]) .btn-quick-pendentes {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}

:global([data-theme="light"]) .btn-quick-pendentes:hover {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #78350f;
}

:global([data-theme="light"]) .selected-pill {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

:global([data-theme="light"]) .bulk-action-footer {
  background: #ffffff;
  border-color: #3b82f6;
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.12), 0 0 16px rgba(59, 130, 246, 0.2);
}
</style>
