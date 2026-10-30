<template>
  <div class="page tarefas-mes-page">
    <!-- Cabeçalho -->
    <header class="page-header">
      <div class="header-main-col">
        <div class="title-row">
          <h1>Tarefas do Mês - Munka</h1>
          <HelpModal title="Sobre as Tarefas do Mês" :items="helpItems" />
          <span v-if="dados.total > 0" class="counter-badge">
            {{ dados.total }} lançada{{ dados.total > 1 ? 's' : '' }}
          </span>
        </div>
        <p class="page-subtitle">
          Audite e gerencie tarefas lançadas no portal Munka. Tarefas que ainda não foram marcadas como concluídas pelo supervisor podem ser alteradas individualmente ou em lote.
        </p>
      </div>

      <!-- Controles de Mês/Ano e Ações Principais -->
      <div class="header-actions-col">
        <!-- Seletor de Período -->
        <div class="periodo-selector-card" role="group" aria-label="Seletor de Mês e Ano">
          <button 
            type="button" 
            class="btn-nav-mes" 
            @click="mudarMes(-1)" 
            title="Mês anterior"
            aria-label="Mês anterior"
          >
            <i class="fa-solid fa-chevron-left" aria-hidden="true"></i>
          </button>

          <div class="periodo-selects">
            <select v-model.number="mesAtual" class="select-mes" aria-label="Mês selecionado" @change="carregarTarefas">
              <option v-for="(nome, idx) in meses" :key="idx" :value="idx + 1">
                {{ nome }}
              </option>
            </select>
            <input 
              v-model.number="anoAtual" 
              type="number" 
              class="input-ano" 
              min="2020" 
              max="2035" 
              aria-label="Ano selecionado"
              @change="carregarTarefas"
            />
          </div>

          <button 
            type="button" 
            class="btn-nav-mes" 
            @click="mudarMes(1)" 
            title="Próximo mês"
            aria-label="Próximo mês"
          >
            <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
          </button>

          <button 
            v-if="!isMesAtual" 
            type="button" 
            class="btn-mes-hoje" 
            @click="irParaMesAtual" 
            title="Voltar para o mês corrente"
          >
            Hoje
          </button>
        </div>

        <!-- Botão Sincronizar Munka -->
        <button 
          type="button" 
          class="btn-sync-munka" 
          :disabled="sincronizando || loading"
          @click="sincronizarComMunka" 
          title="Verificar status real das tarefas navegando no portal Munka"
        >
          <i class="fa-solid fa-arrows-rotate" :class="{ 'fa-spin': sincronizando }" aria-hidden="true"></i>
          <span>{{ sincronizando ? 'Sincronizando...' : 'Sincronizar no Munka' }}</span>
        </button>

        <!-- Botão Recarregar Local -->
        <button 
          type="button" 
          class="btn-ghost btn-sm" 
          :disabled="loading" 
          @click="carregarTarefas" 
          title="Atualizar listagem local"
        >
          <i class="fa-solid fa-rotate" :class="{ 'fa-spin': loading }" aria-hidden="true"></i>
          <span>Atualizar</span>
        </button>
      </div>
    </header>

    <!-- Cards de Métricas e Indicadores -->
    <section class="metricas-grid" aria-label="Métricas de Tarefas do Mês">
      <div class="metrica-card">
        <div class="metrica-icon icon-total">
          <i class="fa-solid fa-list-check" aria-hidden="true"></i>
        </div>
        <div class="metrica-info">
          <span class="metrica-label">Total Lançadas</span>
          <span class="metrica-valor">{{ dados.total }}</span>
        </div>
      </div>

      <div class="metrica-card highlight-editavel">
        <div class="metrica-icon icon-editavel">
          <i class="fa-solid fa-unlock-keyhole" aria-hidden="true"></i>
        </div>
        <div class="metrica-info">
          <span class="metrica-label">Disponíveis p/ Ajuste</span>
          <span class="metrica-valor text-green">{{ dados.editaveis }}</span>
          <span class="metrica-hint">Não concluídas pelo supervisor</span>
        </div>
      </div>

      <div class="metrica-card">
        <div class="metrica-icon icon-concluida">
          <i class="fa-solid fa-lock" aria-hidden="true"></i>
        </div>
        <div class="metrica-info">
          <span class="metrica-label">Concluídas (Bloqueadas)</span>
          <span class="metrica-valor text-muted">{{ dados.concluidas }}</span>
          <span class="metrica-hint">Aprovadas no Munka</span>
        </div>
      </div>

      <div class="metrica-card" :class="{ 'has-selected': selecionadasCount > 0 }">
        <div class="metrica-icon icon-selecionadas">
          <i class="fa-solid fa-square-check" aria-hidden="true"></i>
        </div>
        <div class="metrica-info">
          <span class="metrica-label">Selecionadas</span>
          <div class="selecionadas-row">
            <span class="metrica-valor text-accent">{{ selecionadasCount }}</span>
            <button 
              v-if="selecionadasCount > 0" 
              type="button" 
              class="btn-limpar-selecao" 
              @click="limparSelecao"
            >
              Limpar
            </button>
          </div>
          <span v-if="selecionadasCount > 0" class="metrica-hint">Prontas para ajuste em lote</span>
        </div>
      </div>
    </section>

    <!-- Barra de Ações de Lote Flutuante / Topo quando há selecionadas -->
    <div v-if="selecionadasCount > 0" class="bulk-action-bar" role="toolbar" aria-label="Ações para itens selecionados">
      <div class="bulk-info">
        <i class="fa-solid fa-circle-check" aria-hidden="true"></i>
        <span><strong>{{ selecionadasCount }}</strong> tarefa{{ selecionadasCount > 1 ? 's' : '' }} selecionada{{ selecionadasCount > 1 ? 's' : '' }}</span>
      </div>
      <div class="bulk-buttons">
        <button type="button" class="btn-primary btn-bulk-edit" @click="abrirModalAjusteLote">
          <i class="fa-solid fa-sliders" aria-hidden="true"></i>
          <span>Ajustar {{ selecionadasCount }} Selecionada{{ selecionadasCount > 1 ? 's' : '' }} em Lote</span>
        </button>
        <button type="button" class="btn-ghost btn-sm" @click="limparSelecao">
          Cancelar Seleção
        </button>
      </div>
    </div>

    <!-- Barra de Filtros e Busca -->
    <div class="filters-bar">
      <div class="search-wrap">
        <i class="fa-solid fa-magnifying-glass search-icon" aria-hidden="true"></i>
        <input 
          v-model="filtroTexto" 
          type="text" 
          class="search-input" 
          placeholder="Buscar por título, autor, SHA de commit ou código..."
          aria-label="Buscar tarefas"
        />
        <button 
          v-if="filtroTexto" 
          type="button" 
          class="btn-clear-search" 
          @click="filtroTexto = ''" 
          title="Limpar busca"
        >
          ×
        </button>
      </div>

      <div class="status-filter-pills" role="radiogroup" aria-label="Filtrar por editabilidade">
        <button 
          type="button" 
          class="pill-btn" 
          :class="{ active: filtroStatus === 'todos' }" 
          @click="filtroStatus = 'todos'"
        >
          Todas ({{ tarefasFiltradasPorTexto.length }})
        </button>
        <button 
          type="button" 
          class="pill-btn pill-editavel" 
          :class="{ active: filtroStatus === 'editaveis' }" 
          @click="filtroStatus = 'editaveis'"
        >
          <i class="fa-solid fa-pen" aria-hidden="true"></i>
          <span>Editáveis ({{ contagemEditaveis }})</span>
        </button>
        <button 
          type="button" 
          class="pill-btn pill-concluida" 
          :class="{ active: filtroStatus === 'concluidas' }" 
          @click="filtroStatus = 'concluidas'"
        >
          <i class="fa-solid fa-lock" aria-hidden="true"></i>
          <span>Concluídas ({{ contagemConcluidas }})</span>
        </button>
      </div>
    </div>

    <!-- Estado de Carregamento -->
    <div v-if="loading && dados.tarefas.length === 0" class="loading" role="status" aria-live="polite">
      <i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
      <span>Carregando tarefas do mês...</span>
    </div>

    <!-- Estado Vazio -->
    <div v-else-if="tarefasExibidas.length === 0" class="empty-state-card" role="status">
      <div class="empty-icon-wrap">
        <i class="fa-solid fa-calendar-xmark" aria-hidden="true"></i>
      </div>
      <h3>Nenhuma tarefa encontrada</h3>
      <p v-if="filtroTexto || filtroStatus !== 'todos'">
        Nenhuma tarefa corresponde aos filtros aplicados. Tente ajustar os termos de pesquisa.
      </p>
      <p v-else>
        Não foram encontrados lançamentos no mês de <strong>{{ meses[mesAtual - 1] }} de {{ anoAtual }}</strong>.
      </p>
      <div class="empty-actions">
        <button v-if="filtroTexto || filtroStatus !== 'todos'" type="button" class="btn-ghost" @click="resetarFiltros">
          Limpar Filtros
        </button>
        <button type="button" class="btn-primary" @click="sincronizarComMunka">
          <i class="fa-solid fa-arrows-rotate" aria-hidden="true"></i>
          <span>Sincronizar com o Portal Munka</span>
        </button>
      </div>
    </div>

    <!-- Tabela de Tarefas -->
    <div v-else class="table-container">
      <table class="tarefas-table" aria-label="Tabela de tarefas do mês">
        <thead>
          <tr>
            <th class="col-checkbox">
              <input 
                type="checkbox" 
                class="custom-checkbox" 
                :checked="todosEditaveisSelecionados" 
                :disabled="tarefasEditaveisVisiveis.length === 0"
                :title="todosEditaveisSelecionados ? 'Desmarcar todas' : 'Selecionar todas as editáveis visíveis'"
                aria-label="Selecionar todas as tarefas editáveis"
                @change="toggleSelecionarTodas"
              />
            </th>
            <th class="col-id">ID Munka</th>
            <th class="col-titulo">Atividade & Commit</th>
            <th class="col-codigo">Regra / HPA</th>
            <th class="col-status-munka">Status no Portal</th>
            <th class="col-supervisor">Condição Supervisor</th>
            <th class="col-acoes text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="t in tarefasExibidas" 
            :key="t.id" 
            :class="{ 
              'row-concluida': !t.pode_alterar, 
              'row-selected': isSelecionada(t.id) 
            }"
          >
            <!-- Checkbox de Seleção -->
            <td class="col-checkbox">
              <input 
                type="checkbox" 
                class="custom-checkbox" 
                :checked="isSelecionada(t.id)" 
                :disabled="!t.pode_alterar"
                :title="!t.pode_alterar ? 'Tarefa já concluída pelo supervisor (bloqueada para alteração)' : 'Selecionar tarefa para ajuste'"
                :aria-label="`Selecionar tarefa ${t.titulo}`"
                @change="toggleSelecao(t.id)"
              />
            </td>

            <!-- ID Munka com Link -->
            <td class="col-id">
              <a 
                v-if="t.task_id" 
                :href="t.task_url || '#'" 
                target="_blank" 
                rel="noopener noreferrer" 
                class="munka-id-link" 
                title="Abrir tarefa no portal Munka"
              >
                <span>#{{ t.task_id }}</span>
                <i class="fa-solid fa-arrow-up-right-from-square external-icon" aria-hidden="true"></i>
              </a>
              <span v-else class="badge-pending-id" title="ID não registrado no lançamento">
                —
              </span>
            </td>

            <!-- Título & Commit -->
            <td class="col-titulo">
              <div class="titulo-wrapper">
                <span class="tarefa-nome" :title="t.titulo">
                  {{ t.titulo }}
                </span>
                <div class="tarefa-meta">
                  <router-link 
                    v-if="t.commit_id" 
                    :to="`/commits/${t.commit_id}`" 
                    class="commit-sha-badge"
                    :title="`Ver commit ${t.commit_id}`"
                  >
                    <i class="fa-solid fa-code-commit" aria-hidden="true"></i>
                    <span>{{ t.commit_id.slice(0, 8) }}</span>
                  </router-link>
                  <span v-if="t.commit_autor" class="commit-autor" :title="t.commit_autor">
                    <i class="fa-regular fa-user" aria-hidden="true"></i>
                    <span>{{ t.commit_autor }}</span>
                  </span>
                  <span v-if="t.commit_mensagem" class="commit-msg" :title="t.commit_mensagem">
                    "{{ t.commit_mensagem }}"
                  </span>
                </div>
              </div>
            </td>

            <!-- Regra / HPA -->
            <td class="col-codigo">
              <div class="codigo-wrapper">
                <span class="badge badge-code"><code>{{ t.codigo || '—' }}</code></span>
                <span class="hpa-badge">{{ t.hpa }}h</span>
              </div>
            </td>

            <!-- Status no Munka -->
            <td class="col-status-munka">
              <div class="status-portal-cell">
                <span class="badge" :class="obterClasseBadgeStatus(t.status_munka || t.status)">
                  <span class="status-dot"></span>
                  <span>{{ t.status_munka || t.status }}</span>
                </span>
                <span v-if="t.munka_atualizado_em" class="sync-time-hint" :title="`Última checagem no Munka: ${formatarDataHora(t.munka_atualizado_em)}`">
                  <i class="fa-regular fa-clock" aria-hidden="true"></i>
                  <span>{{ obterTempoRelativo(t.munka_atualizado_em) }}</span>
                </span>
              </div>
            </td>

            <!-- Condição do Supervisor (Editabilidade) -->
            <td class="col-supervisor">
              <span 
                v-if="t.pode_alterar" 
                class="badge-condicao badge-editavel" 
                title="Esta tarefa ainda não foi para a aba de concluído pelo supervisor, portanto pode ser alterada."
              >
                <i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>
                <span>Pode Alterar</span>
              </span>
              <span 
                v-else 
                class="badge-condicao badge-bloqueada" 
                title="Tarefa concluída pelo supervisor no Munka. Edições estão travadas para manter conformidade."
              >
                <i class="fa-solid fa-lock" aria-hidden="true"></i>
                <span>Concluída (Bloqueada)</span>
              </span>
            </td>

            <!-- Ações -->
            <td class="col-acoes text-right">
              <button 
                type="button" 
                class="btn-ajustar-single" 
                :disabled="!t.pode_alterar"
                :title="!t.pode_alterar ? 'Esta tarefa já foi concluída pelo supervisor' : 'Ajustar campos desta tarefa no Munka'"
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
    <div v-if="modalAjusteSingleAberto" class="modal-overlay" @click.self="fecharModalSingle">
      <div class="modal modal-lg modal-tarefas-mes" role="dialog" aria-modal="true" aria-labelledby="modal-single-title">
        <header class="modal-header">
          <div class="modal-title-wrap">
            <div class="modal-title-row">
              <i class="fa-solid fa-pen-to-square modal-header-icon" aria-hidden="true"></i>
              <h2 id="modal-single-title">Ajustar Tarefa no Munka</h2>
              <span class="modal-count-badge">{{ tarefaAlvoSingle?.task_id ? `#${tarefaAlvoSingle.task_id}` : '(Busca pelo título)' }}</span>
            </div>
            <span class="modal-sub">
              Modifique os campos desejados desta tarefa individualmente.
            </span>
          </div>
          <button type="button" class="btn-close-modal" @click="fecharModalSingle" aria-label="Fechar modal">×</button>
        </header>

        <form @submit.prevent="salvarAjusteSingle" class="form-ajuste">
          <div class="modal-body">
            <div class="target-task-preview">
              <span class="preview-title">{{ tarefaAlvoSingle?.titulo }}</span>
              <span class="badge" :class="obterClasseBadgeStatus(tarefaAlvoSingle?.status_munka || tarefaAlvoSingle?.status)">
                {{ tarefaAlvoSingle?.status_munka || tarefaAlvoSingle?.status }}
              </span>
            </div>

            <div class="form-grid">
              <!-- Status -->
              <div class="form-group">
                <label for="single_status"><i class="fa-solid fa-tag"></i> Status</label>
                <select id="single_status" v-model="formSingle.status_id" class="field-select">
                  <option value="15">Backlog (15)</option>
                  <option value="16">Backlog Prioritário (16)</option>
                  <option value="17">Aberto / Pendente (17)</option>
                  <option value="18">Desenvolvimento (18)</option>
                  <option value="20">Homologação (20)</option>
                  <option value="21">Concluído (21)</option>
                </select>
              </div>

              <!-- Perfil do Profissional (Cargo) -->
              <div class="form-group">
                <label for="single_cargo"><i class="fa-solid fa-user-tie"></i> Perfil do Profissional (Cargo)</label>
                <select id="single_cargo" v-model="formSingle.cargo" class="field-select">
                  <option value="9">Desenvolvedor (9)</option>
                  <option value="11">Analista de Sistemas (11)</option>
                  <option value="12">Arquiteto de Software (12)</option>
                  <option value="16">Analista de Testes (16)</option>
                </select>
              </div>

              <!-- Nível -->
              <div class="form-group">
                <label for="single_nivel"><i class="fa-solid fa-layer-group"></i> Nível</label>
                <select id="single_nivel" v-model="formSingle.nivel" class="field-select">
                  <option value="1">Júnior (1)</option>
                  <option value="2">Pleno (2)</option>
                  <option value="3">Sênior (3)</option>
                  <option value="4">Único (4)</option>
                </select>
              </div>

              <!-- Tipo -->
              <div class="form-group">
                <label for="single_tipo"><i class="fa-solid fa-shapes"></i> Tipo</label>
                <input 
                  id="single_tipo" 
                  v-model="formSingle.tipo" 
                  placeholder="projeto" 
                  class="field-input"
                />
              </div>

              <!-- Responsável -->
              <div class="form-group form-col-full">
                <label for="single_responsavel"><i class="fa-solid fa-id-card-clip"></i> Responsável</label>
                <input 
                  id="single_responsavel" 
                  v-model="formSingle.responsavel" 
                  placeholder="Nome do responsável no Munka (busca Select2)" 
                  class="field-input"
                />
              </div>

              <!-- Produto -->
              <div class="form-group">
                <label for="single_produto"><i class="fa-solid fa-box-archive"></i> Produto</label>
                <input 
                  id="single_produto" 
                  v-model="formSingle.produto" 
                  placeholder="Ex: [DESENV] MUNKA" 
                  class="field-input"
                />
              </div>

              <!-- Projeto -->
              <div class="form-group">
                <label for="single_projeto"><i class="fa-solid fa-diagram-project"></i> Projeto</label>
                <input 
                  id="single_projeto" 
                  v-model="formSingle.projeto" 
                  placeholder="Ex: MUNKA Multicontrato" 
                  class="field-input"
                />
              </div>
            </div>
          </div>

          <footer class="modal-actions-sticky">
            <div class="footer-summary">
              <span>Campos aplicados apenas nesta tarefa</span>
            </div>
            <div class="footer-buttons">
              <button type="button" class="btn-ghost" @click="fecharModalSingle" :disabled="salvando">
                Cancelar
              </button>
              <button type="submit" class="btn-primary" :disabled="salvando">
                <i v-if="salvando" class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
                <i v-else class="fa-solid fa-check" aria-hidden="true"></i>
                <span>{{ salvando ? 'Enfileirando...' : 'Salvar Alterações' }}</span>
              </button>
            </div>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal de Ajuste em Lote (Múltiplas Selecionadas) -->
    <div v-if="modalAjusteLoteAberto" class="modal-overlay" @click.self="fecharModalLote">
      <div class="modal modal-lg modal-tarefas-mes" role="dialog" aria-modal="true" aria-labelledby="modal-lote-title">
        <header class="modal-header">
          <div class="modal-title-wrap">
            <div class="modal-title-row">
              <i class="fa-solid fa-sliders modal-header-icon" aria-hidden="true"></i>
              <h2 id="modal-lote-title">Ajuste em Lote de Tarefas</h2>
              <span class="modal-count-badge">{{ selecionadasCount }} selecionadas</span>
            </div>
            <span class="modal-sub">
              Escolha quais campos deseja sobrescrever em lote nas tarefas selecionadas.
            </span>
          </div>
          <button type="button" class="btn-close-modal" @click="fecharModalLote" aria-label="Fechar modal">×</button>
        </header>

        <form @submit.prevent="salvarAjusteLote" class="form-ajuste-lote">
          <div class="modal-body">
            <div class="lote-notice-card">
              <i class="fa-solid fa-circle-info" aria-hidden="true"></i>
              <div>
                <strong>Instrução de edição em lote:</strong>
                <span>Marque a caixa de cada campo que deseja modificar. Campos desmarcados manterão os valores já existentes no Munka.</span>
              </div>
            </div>

            <div class="lote-fields-grid">
              <!-- Status -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.status }">
                <div class="field-card-header" @click="habilitarCampo.status = !habilitarCampo.status">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.status" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-tag"></i> Status</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.status }">
                    {{ habilitarCampo.status ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <select v-model="formLote.status_id" :disabled="!habilitarCampo.status" class="field-select">
                    <option value="15">Backlog (15)</option>
                    <option value="16">Backlog Prioritário (16)</option>
                    <option value="17">Aberto / Pendente (17)</option>
                    <option value="18">Desenvolvimento (18)</option>
                    <option value="20">Homologação (20)</option>
                    <option value="21">Concluído (21)</option>
                  </select>
                </div>
              </div>

              <!-- Cargo (Perfil do Profissional) -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.cargo }">
                <div class="field-card-header" @click="habilitarCampo.cargo = !habilitarCampo.cargo">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.cargo" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-user-tie"></i> Perfil / Cargo</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.cargo }">
                    {{ habilitarCampo.cargo ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <select v-model="formLote.cargo" :disabled="!habilitarCampo.cargo" class="field-select">
                    <option value="9">Desenvolvedor (9)</option>
                    <option value="11">Analista de Sistemas (11)</option>
                    <option value="12">Arquiteto de Software (12)</option>
                    <option value="16">Analista de Testes (16)</option>
                  </select>
                </div>
              </div>

              <!-- Nível -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.nivel }">
                <div class="field-card-header" @click="habilitarCampo.nivel = !habilitarCampo.nivel">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.nivel" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-layer-group"></i> Nível</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.nivel }">
                    {{ habilitarCampo.nivel ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <select v-model="formLote.nivel" :disabled="!habilitarCampo.nivel" class="field-select">
                    <option value="1">Júnior (1)</option>
                    <option value="2">Pleno (2)</option>
                    <option value="3">Sênior (3)</option>
                    <option value="4">Único (4)</option>
                  </select>
                </div>
              </div>

              <!-- Responsável -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.responsavel }">
                <div class="field-card-header" @click="habilitarCampo.responsavel = !habilitarCampo.responsavel">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.responsavel" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-id-card-clip"></i> Responsável</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.responsavel }">
                    {{ habilitarCampo.responsavel ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <input 
                    v-model="formLote.responsavel" 
                    :disabled="!habilitarCampo.responsavel" 
                    placeholder="Nome do responsável no Munka" 
                    class="field-input"
                  />
                </div>
              </div>

              <!-- Tipo -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.tipo }">
                <div class="field-card-header" @click="habilitarCampo.tipo = !habilitarCampo.tipo">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.tipo" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-shapes"></i> Tipo</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.tipo }">
                    {{ habilitarCampo.tipo ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <input 
                    v-model="formLote.tipo" 
                    :disabled="!habilitarCampo.tipo" 
                    placeholder="projeto" 
                    class="field-input"
                  />
                </div>
              </div>

              <!-- Produto -->
              <div class="lote-field-card" :class="{ 'is-enabled': habilitarCampo.produto }">
                <div class="field-card-header" @click="habilitarCampo.produto = !habilitarCampo.produto">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.produto" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-box-archive"></i> Produto</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.produto }">
                    {{ habilitarCampo.produto ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <input 
                    v-model="formLote.produto" 
                    :disabled="!habilitarCampo.produto" 
                    placeholder="Ex: [DESENV] MUNKA" 
                    class="field-input"
                  />
                </div>
              </div>

              <!-- Projeto -->
              <div class="lote-field-card field-card-full" :class="{ 'is-enabled': habilitarCampo.projeto }">
                <div class="field-card-header" @click="habilitarCampo.projeto = !habilitarCampo.projeto">
                  <label class="lote-field-toggle" @click.stop>
                    <input type="checkbox" v-model="habilitarCampo.projeto" class="custom-checkbox" />
                    <span class="field-name"><i class="fa-solid fa-diagram-project"></i> Projeto</span>
                  </label>
                  <span class="field-active-indicator" :class="{ 'tag-active': habilitarCampo.projeto }">
                    {{ habilitarCampo.projeto ? '✓ Sobrescrever' : 'Manter original' }}
                  </span>
                </div>
                <div class="field-input-wrap">
                  <input 
                    v-model="formLote.projeto" 
                    :disabled="!habilitarCampo.projeto" 
                    placeholder="Ex: MUNKA Multicontrato" 
                    class="field-input"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Sticky Footer -->
          <footer class="modal-actions-sticky">
            <div class="footer-summary">
              <span v-if="totalCamposHabilitados === 0" class="summary-zero">
                <i class="fa-solid fa-triangle-exclamation"></i> Marque ao menos um campo acima
              </span>
              <span v-else class="summary-active">
                <i class="fa-solid fa-check"></i> {{ totalCamposHabilitados }} campo(s) serão aplicados em {{ selecionadasCount }} tarefa(s)
              </span>
            </div>
            <div class="footer-buttons">
              <button type="button" class="btn-ghost" @click="fecharModalLote" :disabled="salvando">
                Cancelar
              </button>
              <button 
                type="submit" 
                class="btn-primary" 
                :disabled="salvando || totalCamposHabilitados === 0"
              >
                <i v-if="salvando" class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>
                <i v-else class="fa-solid fa-check-double" aria-hidden="true"></i>
                <span>{{ salvando ? 'Enfileirando...' : `Aplicar em ${selecionadasCount} Tarefas` }}</span>
              </button>
            </div>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { api, type TarefaMesItem, type TarefasMesResponse, type Config } from '../api'
import { useToastStore } from '../stores/toast'
import { useFilaStore } from '../stores/fila'
import HelpModal from '../components/HelpModal.vue'

const helpItems = [
  { 
    title: 'Tarefas do Mês', 
    text: 'Lista todas as tarefas enviadas pelo sistema no mês selecionado, consolidando informações de status lidas diretamente da plataforma Munka.' 
  },
  { 
    title: 'Condição do Supervisor (Editabilidade)', 
    text: 'Se uma tarefa já foi aprovada e movida para a aba de Concluído pelo supervisor no Munka, ela fica bloqueada para prevenir divergências. Todas as demais tarefas continuam disponíveis para alteração.' 
  },
  { 
    title: 'Sincronizar no Munka', 
    text: 'Executa uma checagem automatizada via Playwright para ler os status reais mais recentes no portal Munka e atualizar o banco de dados local.' 
  },
  { 
    title: 'Ajuste em Lote', 
    text: 'Selecione múltiplas tarefas abertas e ajuste campos como Cargo, Nível, Responsável, Produto, Tipo, Projeto e Status de uma única vez.' 
  },
]

const meses = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const hoje = new Date()
const mesAtual = ref<number>(hoje.getMonth() + 1)
const anoAtual = ref<number>(hoje.getFullYear())

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
const filtroStatus = ref<'todos' | 'editaveis' | 'concluidas'>('todos')

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

// Contagens e Filtros
const tarefasFiltradasPorTexto = computed(() => {
  const q = filtroTexto.value.trim().toLowerCase()
  if (!q) return dados.value.tarefas
  return dados.value.tarefas.filter(t => {
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

const contagemEditaveis = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => t.pode_alterar).length
})

const contagemConcluidas = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => !t.pode_alterar).length
})

const tarefasExibidas = computed(() => {
  return tarefasFiltradasPorTexto.value.filter(t => {
    if (filtroStatus.value === 'editaveis') return t.pode_alterar
    if (filtroStatus.value === 'concluidas') return !t.pode_alterar
    return true
  })
})

const tarefasEditaveisVisiveis = computed(() => {
  return tarefasExibidas.value.filter(t => t.pode_alterar)
})

const selecionadasCount = computed(() => selecionadosIds.value.length)

const todosEditaveisSelecionados = computed(() => {
  if (tarefasEditaveisVisiveis.value.length === 0) return false
  return tarefasEditaveisVisiveis.value.every(t => selecionadosIds.value.includes(t.id))
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
  if (todosEditaveisSelecionados.value) {
    // Desmarca as visíveis
    const idsVisiveis = new Set(tarefasEditaveisVisiveis.value.map(t => t.id))
    selecionadosIds.value = selecionadosIds.value.filter(id => !idsVisiveis.has(id))
  } else {
    // Marca todas as editáveis visíveis
    const novoSet = new Set([...selecionadosIds.value, ...tarefasEditaveisVisiveis.value.map(t => t.id)])
    selecionadosIds.value = Array.from(novoSet)
  }
}

function limparSelecao() {
  selecionadosIds.value = []
}

function resetarFiltros() {
  filtroTexto.value = ''
  filtroStatus.value = 'todos'
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
  if (!t.pode_alterar) return
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
    const statusMap: Record<string, string> = {
      '15': 'Backlog',
      '16': 'Backlog Prioritário',
      '17': 'Aberto / Pendente',
      '18': 'Desenvolvimento',
      '20': 'Homologação',
      '21': 'Concluído'
    }
    const novoNome = statusMap[formSingle.status_id] || `Status ${formSingle.status_id}`
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
      const statusMap: Record<string, string> = {
        '15': 'Backlog',
        '16': 'Backlog Prioritário',
        '17': 'Aberto / Pendente',
        '18': 'Desenvolvimento',
        '20': 'Homologação',
        '21': 'Concluído'
      }
      const novoNome = statusMap[formLote.status_id] || `Status ${formLote.status_id}`
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

function obterClasseBadgeStatus(status?: string): string {
  if (!status) return 'badge-gray'
  const s = status.toLowerCase()
  if (s.includes('conclu') || s === '21' || s.includes('aprov')) return 'badge-green'
  if (s.includes('homolog') || s === '20') return 'badge-blue'
  if (s.includes('desenv') || s === '18') return 'badge-orange'
  if (s.includes('backlog')) return 'badge-gray'
  if (s.includes('aberto') || s.includes('pendente') || s === '17') return 'badge-yellow'
  return 'badge-blue'
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

<style scoped>
.tarefas-mes-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.header-main-col {
  flex: 1;
  min-width: 280px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.counter-badge {
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}

.page-subtitle {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin-top: 0.35rem;
  line-height: 1.45;
  max-width: 720px;
}

.header-actions-col {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Seletor de Período */
.periodo-selector-card {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 3px 6px;
  gap: 4px;
}

.btn-nav-mes {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-nav-mes:hover {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text);
}

.periodo-selects {
  display: flex;
  align-items: center;
  gap: 4px;
}

.select-mes {
  background: transparent;
  border: none;
  color: var(--text);
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 6px;
  outline: none;
}

.select-mes option {
  background: var(--card-bg);
  color: var(--text);
}

.input-ano {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 600;
  width: 60px;
  text-align: center;
  padding: 2px 4px;
  border-radius: 4px;
  outline: none;
}

.input-ano:focus {
  border-color: var(--border);
  background: rgba(148, 163, 184, 0.1);
  color: var(--text);
}

.btn-mes-hoje {
  background: var(--accent-glow);
  color: var(--accent);
  border: 1px solid var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-mes-hoje:hover {
  background: var(--accent);
  color: #fff;
}

.btn-sync-munka {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--card-bg);
  border: 1px solid var(--accent);
  color: var(--accent);
  padding: 0.45rem 0.95rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-sync-munka:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 168, 204, 0.25);
}

.btn-sync-munka:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Métricas Grid */
.metricas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 1rem;
}

.metrica-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  transition: transform 0.15s, border-color 0.15s;
}

.metrica-card:hover {
  border-color: var(--border);
  transform: translateY(-2px);
}

.metrica-card.highlight-editavel {
  border-color: rgba(34, 197, 94, 0.35);
  background: linear-gradient(135deg, var(--card-bg) 0%, rgba(34, 197, 94, 0.05) 100%);
}

.metrica-card.has-selected {
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--card-bg) 0%, var(--accent-glow) 100%);
}

.metrica-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}

.icon-total { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.icon-editavel { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.icon-concluida { background: rgba(148, 163, 184, 0.15); color: var(--text-muted); }
.icon-selecionadas { background: var(--accent-glow); color: var(--accent); }

.metrica-info {
  display: flex;
  flex-direction: column;
}

.metrica-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  font-weight: 700;
}

.metrica-valor {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
}

.metrica-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.text-green { color: #22c55e !important; }
.text-accent { color: var(--accent) !important; }

.selecionadas-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-limpar-selecao {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.72rem;
  text-decoration: underline;
  cursor: pointer;
}

.btn-limpar-selecao:hover {
  color: var(--text);
}

/* Barra de Ações em Lote */
.bulk-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: var(--accent-glow);
  border: 1px solid var(--accent);
  border-radius: 10px;
  animation: fadeIn 0.2s ease;
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.9rem;
  color: var(--text);
}

.bulk-info i {
  color: var(--accent);
  font-size: 1.1rem;
}

.bulk-buttons {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-bulk-edit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
}

/* Filtros */
.filters-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 480px;
  min-width: 260px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.search-input {
  width: 100%;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  color: var(--text);
  padding: 0.55rem 2rem 0.55rem 2.25rem;
  border-radius: 8px;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus {
  border-color: var(--accent);
}

.btn-clear-search {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.1rem;
  cursor: pointer;
}

.status-filter-pills {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  padding: 3px;
  border-radius: 8px;
}

.pill-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.15s ease;
}

.pill-btn:hover {
  color: var(--text);
  background: rgba(148, 163, 184, 0.1);
}

.pill-btn.active {
  background: var(--header-group-bg);
  color: var(--text);
  font-weight: 700;
  border: 1px solid var(--border);
}

.pill-btn.pill-editavel.active {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border-color: #22c55e;
}

.pill-btn.pill-concluida.active {
  background: rgba(148, 163, 184, 0.2);
  color: var(--text);
  border-color: var(--border);
}

/* Tabela */
.table-container {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  overflow-x: auto;
}

.tarefas-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.88rem;
}

.tarefas-table th {
  padding: 0.85rem 1rem;
  background: var(--header-group-bg);
  border-bottom: 1px solid var(--card-border);
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.tarefas-table td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.tarefas-table tr:last-child td {
  border-bottom: none;
}

.tarefas-table tr:hover {
  background: rgba(148, 163, 184, 0.04);
}

.row-selected {
  background: var(--accent-glow) !important;
}

.row-concluida {
  opacity: 0.78;
}

.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-id {
  width: 110px;
}

.col-titulo {
  min-width: 260px;
}

.col-codigo {
  width: 130px;
}

.col-status-munka {
  min-width: 150px;
}

.col-supervisor {
  width: 160px;
}

.col-acoes {
  width: 100px;
}

.text-right {
  text-align: right;
}

/* Custom Checkbox */
.custom-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
}

/* ID Munka Link */
.munka-id-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--accent-glow);
  font-size: 0.82rem;
}

.munka-id-link:hover {
  text-decoration: underline;
}

.external-icon {
  font-size: 0.65rem;
  opacity: 0.8;
}

.badge-pending-id {
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* Titulo & Commit */
.titulo-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.tarefa-nome {
  font-weight: 600;
  color: var(--text);
  line-height: 1.35;
}

.tarefa-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.commit-sha-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-family: monospace;
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--accent);
  text-decoration: none;
  font-size: 0.75rem;
}

.commit-sha-badge:hover {
  border-color: var(--accent);
}

.commit-autor, .commit-msg {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 320px;
}

/* Regra & HPA */
.codigo-wrapper {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.badge-code {
  font-size: 0.8rem;
  padding: 2px 6px;
}

.hpa-badge {
  background: rgba(148, 163, 184, 0.15);
  border: 1px solid var(--border);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--text);
}

/* Status Munka Cell */
.status-portal-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: flex-start;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
  margin-right: 4px;
}

.sync-time-hint {
  font-size: 0.7rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* Condição do Supervisor */
.badge-condicao {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}

.badge-editavel {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.badge-bloqueada {
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

/* Botão Ajustar Single */
.btn-ajustar-single {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-ajustar-single:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-glow);
}

.btn-ajustar-single:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Modais */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  animation: fadeIn 0.2s ease-out;
}

.modal-tarefas-mes {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
  width: 860px !important;
  max-width: 95vw !important;
  max-height: 90vh !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
  gap: 0 !important;
  overflow: hidden !important;
  animation: modalScale 0.2s ease;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.75rem;
  border-bottom: 1px solid var(--border);
  background: var(--card-bg);
  flex-shrink: 0;
}

.modal-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.modal-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.modal-header-icon {
  font-size: 1.25rem;
  color: var(--accent);
}

.modal-title-wrap h2 {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
}

.modal-count-badge {
  background: var(--accent-glow);
  color: var(--accent);
  border: 1px solid var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 99px;
}

.modal-sub {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.btn-close-modal {
  background: transparent;
  border: none;
  font-size: 1.6rem;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  border-radius: 4px;
  transition: color 0.15s;
}

.btn-close-modal:hover {
  color: var(--text);
}

.modal-body {
  padding: 1.5rem 1.75rem;
  overflow-y: auto;
  flex: 1;
  max-height: calc(90vh - 145px);
}

.target-task-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

.preview-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--text);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.form-col-full {
  grid-column: span 2;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-group label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.form-group label i {
  color: var(--accent);
}

/* Lote Modal Styles */
.lote-notice-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 10px;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.85rem;
  color: var(--text);
}

.lote-notice-card i {
  color: var(--accent);
  font-size: 1.15rem;
  flex-shrink: 0;
}

.lote-notice-card span {
  color: var(--text-muted);
  font-size: 0.82rem;
  margin-left: 0.25rem;
}

.lote-fields-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.15rem;
}

@media (max-width: 720px) {
  .lote-fields-grid, .form-grid {
    grid-template-columns: 1fr;
  }
  .form-col-full, .field-card-full {
    grid-column: span 1 !important;
  }
}

.lote-field-card {
  background: var(--header-group-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.95rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  transition: border-color 0.15s, background-color 0.15s, box-shadow 0.15s;
}

.lote-field-card:hover {
  border-color: var(--accent-light);
}

.lote-field-card.is-enabled {
  border-color: var(--accent) !important;
  background: var(--accent-glow) !important;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.15);
}

.field-card-full {
  grid-column: span 2;
}

.field-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.lote-field-toggle {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text);
  cursor: pointer;
}

.field-name {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.field-name i {
  color: var(--accent);
  font-size: 0.85rem;
}

.field-active-indicator {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--card-bg);
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid var(--border);
  transition: all 0.15s;
}

.field-active-indicator.tag-active {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.15);
}

.field-input-wrap {
  width: 100%;
}

.field-select,
.field-input {
  width: 100% !important;
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  padding: 0.6rem 0.85rem !important;
  border-radius: 8px !important;
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field-select:focus,
.field-input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

.field-select:disabled,
.field-input:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  background: rgba(148, 163, 184, 0.05) !important;
  border-color: rgba(148, 163, 184, 0.15) !important;
}

/* Sticky Footer */
.modal-actions-sticky {
  padding: 1.15rem 1.75rem;
  border-top: 1px solid var(--border);
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 1rem;
}

.footer-summary {
  font-size: 0.84rem;
  font-weight: 600;
}

.summary-zero {
  color: var(--warning);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.summary-active {
  color: var(--success);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.footer-buttons {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Empty State */
.empty-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 1.5rem;
  background: var(--card-bg);
  border: 1px dashed var(--card-border);
  border-radius: 14px;
}

.empty-icon-wrap {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.empty-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes modalScale {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
  .header-actions-col {
    width: 100%;
    justify-content: space-between;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
  .form-col-full {
    grid-column: span 1;
  }
  .lote-field-item {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

