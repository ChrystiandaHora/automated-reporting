<template>
  <div class="page">
    <div class="page-header">
      <div class="title-row">
        <h1>Commits</h1>
        <HelpModal title="Como funciona esta página" :items="helpItems" />
      </div>
      <button class="btn-primary" @click="showImport = true">+ Importar Commit</button>
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
              <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
              </svg>
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
              <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z"/>
              </svg>
              <span>Linha do Tempo (Data)</span>
              <span class="mode-count-badge" :title="`${commitsFiltrados.length} commits`">
                {{ commitsFiltrados.length }}
              </span>
            </button>
          </div>

          <!-- Busca de Commits / Repositórios -->
          <div class="search-box">
            <svg class="search-icon" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true" focusable="false">
              <path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/>
            </svg>
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
              ✕
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
              <button type="button" class="tag-remove-btn" @click="apenasNaFila = false" aria-label="Remover filtro de fila">✕</button>
            </span>
            <span v-if="repositorioFiltro !== 'todos'" class="filter-tag">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
              </svg>
              <span>{{ repositorioFiltro }}</span>
              <button type="button" class="tag-remove-btn" @click="repositorioFiltro = 'todos'" aria-label="Remover filtro deste repositório">✕</button>
            </span>
            <span v-if="termoBusca" class="filter-tag">
              <span>"{{ termoBusca }}"</span>
              <button type="button" class="tag-remove-btn" @click="termoBusca = ''" aria-label="Remover filtro de texto">✕</button>
            </span>
            <span class="filter-match-count">
              ({{ commitsFiltrados.length }} commit{{ commitsFiltrados.length !== 1 ? 's' : '' }} encontrado{{ commitsFiltrados.length !== 1 ? 's' : '' }})
            </span>
          </div>
          <button type="button" class="btn-clear-all" @click="limparTodosFiltros">
            Limpar Filtros
          </button>
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
              <div class="repo-avatar-icon" :class="repo.colorClass">
                <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true" focusable="false">
                  <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
                </svg>
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
                  ✓ {{ repo.analisados }} Analisado{{ repo.analisados !== 1 ? 's' : '' }}
                </span>
                <span v-if="repo.pendentes > 0" class="badge badge-status badge-gray" :title="`${repo.pendentes} commit(s) pendente(s)`">
                  ⏳ {{ repo.pendentes }} Pendente{{ repo.pendentes !== 1 ? 's' : '' }}
                </span>
                <span v-if="repo.totalHpa > 0" class="badge badge-status badge-hpa" :title="`${repo.totalHpa} horas HPA estimadas`">
                  ⚡ {{ repo.totalHpa }}h HPA
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
                <svg 
                  class="chevron-icon" 
                  :class="{ rotated: isRepoColapsado(repo.nome) }"
                  viewBox="0 0 24 24" 
                  width="18" 
                  height="18" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2.5" 
                  stroke-linecap="round" 
                  stroke-linejoin="round"
                  aria-hidden="true"
                  focusable="false"
                >
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </button>
            </div>
          </div>

          <!-- Lista de Commits do Repositório (colapsável) -->
          <div v-show="!isRepoColapsado(repo.nome)" class="repo-commits-list">
            <div 
              v-for="commit in repo.commits" 
              :key="commit.id" 
              class="commit-row"
              tabindex="0"
              role="link"
              @click="$router.push(`/commits/${commit.id}`)"
              @keydown.enter.prevent="$router.push(`/commits/${commit.id}`)"
              @keydown.space.prevent="$router.push(`/commits/${commit.id}`)"
            >
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
                        <span class="queue-icon-txt" v-else>⏳</span>
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

              <!-- Lado Direito: Ações e SHA -->
              <div class="commit-actions" @click.stop>
                <!-- Botão Excluir -->
                <button 
                  class="action-btn delete-btn" 
                  @click="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10" stroke="#f85149" fill="none" />
                    <line x1="15" y1="9" x2="9" y2="15" stroke="#f85149" />
                    <line x1="9" y1="9" x2="15" y2="15" stroke="#f85149" />
                  </svg>
                </button>

                <!-- SHA Box -->
                <span class="sha-box">{{ commit.id.slice(0, 8) }}</span>

                <!-- Botão Copiar SHA -->
                <button 
                  class="action-btn copy-btn" 
                  @click="copiarSHA(commit.id)"
                  title="Copiar SHA completo"
                  aria-label="Copiar SHA completo"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </button>

                <!-- Botão Navegar (Folder) -->
                <button 
                  class="action-btn folder-btn" 
                  @click="$router.push(`/commits/${commit.id}`)"
                  title="Ver detalhes da análise"
                  aria-label="Ver detalhes da análise"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
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
              tabindex="0"
              role="link"
              @click="$router.push(`/commits/${commit.id}`)"
              @keydown.enter.prevent="$router.push(`/commits/${commit.id}`)"
              @keydown.space.prevent="$router.push(`/commits/${commit.id}`)"
            >
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
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" aria-hidden="true" focusable="false">
                      <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z"/>
                    </svg>
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
                        <span class="queue-icon-txt" v-else>⏳</span>
                        {{ obterInfoFila(commit.id)!.envios }} na fila
                      </span>
                    </template>
                  </div>
                </div>
                <span class="commit-author-time">
                  {{ commit.autor }} authored {{ obterTempoRelativo(commit.data_autor) }}
                </span>
              </div>

              <!-- Lado Direito: Ações e SHA -->
              <div class="commit-actions" @click.stop>
                <!-- Botão Excluir -->
                <button 
                  class="action-btn delete-btn" 
                  @click="abrirModalConfirmacao(commit)"
                  title="Excluir commit"
                  aria-label="Excluir commit"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10" stroke="#f85149" fill="none" />
                    <line x1="15" y1="9" x2="9" y2="15" stroke="#f85149" />
                    <line x1="9" y1="9" x2="15" y2="15" stroke="#f85149" />
                  </svg>
                </button>

                <!-- SHA Box -->
                <span class="sha-box">{{ commit.id.slice(0, 8) }}</span>

                <!-- Botão Copiar SHA -->
                <button 
                  class="action-btn copy-btn" 
                  @click="copiarSHA(commit.id)"
                  title="Copiar SHA completo"
                  aria-label="Copiar SHA completo"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </button>

                <!-- Botão Navegar (Folder) -->
                <button 
                  class="action-btn folder-btn" 
                  @click="$router.push(`/commits/${commit.id}`)"
                  title="Ver detalhes da análise"
                  aria-label="Ver detalhes da análise"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
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

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useCommitsStore } from '../stores/commits'
import { useFilaStore } from '../stores/fila'
import { useToastStore } from '../stores/toast'
import HelpModal from '../components/HelpModal.vue'
import type { CommitSummary } from '../api'

const helpItems = [
  { title: 'Visualização por Repositório', text: 'Permite inspecionar commits organizados por projeto do GitLab com métricas consolidadas (tarefas, status e horas HPA).' },
  { title: 'Dinamismo da Fila em Tempo Real', text: 'Os commits mostram um badge dinâmico indicando quantas tarefas daquele commit estão na fila do Celery aguardando ou em processamento.' },
  { title: 'Linha do Tempo', text: 'Exibe a ordem cronológica dos commits de todos os repositórios, com badges coloridos identificando a origem de cada commit.' },
  { title: 'Filtros Rápidos', text: 'Clique em "Na Fila" ou em qualquer chip de repositório para isolar rapidamente as alterações desejadas.' },
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

async function copiarSHA(sha: string) {
  try {
    await navigator.clipboard.writeText(sha)
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
  background: linear-gradient(135deg, #d97706, #f59e0b);
  color: #ffffff;
  border-color: #f59e0b;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.35);
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
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--border, #30363d);
  cursor: pointer;
  transition: background 0.15s;
  outline: none;
}

.commit-row:last-child {
  border-bottom: none;
}

.commit-row:hover {
  background: var(--accent-glow, rgba(56, 189, 248, 0.08));
}

.commit-row:focus-visible {
  background: var(--accent-glow, rgba(56, 189, 248, 0.12));
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: -2px;
}

.commit-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
  margin-right: 1rem;
  flex-shrink: 0;
  border: 1px solid var(--border, #30363d);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
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
  padding: 0.18rem 0.55rem;
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
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text, #f0f6fc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 520px;
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

.commit-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  margin-left: 1rem;
}

.action-btn {
  background: var(--bg, #0d1117);
  border: 2px solid var(--border, #30363d);
  color: var(--text-muted, #8b949e);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem;
  transition: border-color 0.12s, color 0.12s, transform 0.1s;
}

.action-btn:hover {
  color: var(--text, #f0f6fc);
  border-color: var(--accent, #58a6ff);
  transform: translateY(-1px);
}

.action-btn:focus-visible {
  outline: 2px solid var(--accent, #58a6ff);
  outline-offset: 2px;
}

.delete-btn {
  border: none;
  background: transparent;
  padding: 0.25rem;
  color: #f85149;
  opacity: 0.85;
  transition: opacity 0.12s, transform 0.1s;
}

.delete-btn:hover {
  opacity: 1;
  transform: scale(1.1);
  color: #ff6b6b;
}

.sha-box {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: var(--sha-box-color, #94a3b8);
  background: var(--sha-box-bg, rgba(255, 255, 255, 0.05));
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 0.3rem 0.6rem;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.copy-btn, .folder-btn {
  padding: 0.4rem;
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
  color: #c084fc;
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
  color: #818cf8;
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
</style>
