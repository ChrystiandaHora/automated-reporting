export interface TutorialStep {
  title: string
  icon: string
  description: string
  tip?: string
  target?: string // Seletor CSS do elemento a ser destacado na tela com spotlight
}

export interface ScreenTutorial {
  id: string
  title: string
  subtitle: string
  steps: TutorialStep[]
}

export const TUTORIALS: Record<string, ScreenTutorial> = {
  dashboard: {
    id: 'dashboard',
    title: 'Guia do Dashboard',
    subtitle: 'Visão executiva e métricas operacionais de commits e lançamentos',
    steps: [
      {
        title: 'Métricas e Indicadores em Tempo Real',
        icon: 'fa-solid fa-chart-line',
        target: '.kpi-executive-strip, .dashboard-header, .page-header',
        description: 'No topo da tela, você encontra os cartões de KPIs com o total de commits importados, horas faturadas (HPA), pendências de análise por IA e o status atual da fila de automação.',
        tip: 'Clique nos números para acessar diretamente as listagens correspondentes.'
      },
      {
        title: 'Banners de Ações Rápidas',
        icon: 'fa-solid fa-wand-magic-sparkles',
        target: '.action-alert-banner, .btn-import-shortcut, .dashboard-header',
        description: 'O sistema avalia proativamente se existem commits pendentes de análise ou atividades prontas para envio, oferecendo atalhos rápidos com um clique.',
        tip: 'Ideal para iniciar o dia de trabalho faturando commits acumulados.'
      },
      {
        title: 'Pipeline do Fluxo de Trabalho',
        icon: 'fa-solid fa-timeline',
        target: '.funnel-panel, .pipeline-track, .dashboard-page',
        description: 'Acompanhe as 3 etapas essenciais de cada commit: Importação inicial do GitLab, Enriquecimento com IA e Envio automatizado ao portal Munka.',
        tip: 'Acompanhe a barra de progresso visual de conversão de ponta a ponta.'
      },
      {
        title: 'Gráficos de Histórico e Repositórios',
        icon: 'fa-solid fa-chart-pie',
        target: '.dashboard-two-col-grid, .monthly-history-panel, .repo-distribution-panel',
        description: 'Visualize a evolução mensal das horas entregues e a distribuição percentual do esforço faturado por repositório.',
        tip: 'Use os seletores de período e ordenação para refinar a visualização analítica.'
      }
    ]
  },

  commits: {
    id: 'commits',
    title: 'Guia de Commits',
    subtitle: 'Navegação, busca e gestão de todo o histórico importado',
    steps: [
      {
        title: 'Modos de Visualização (Repo vs Data)',
        icon: 'fa-solid fa-folder-tree',
        target: '.view-mode-tabs',
        description: 'Alterne entre a visualização "Por Repositório" (cards organizados por projeto) e "Linha do Tempo (Data)" (ordenação cronológica de todos os commits).',
        tip: 'Use o modo por repositório para inspecionar um projeto específico com mais clareza.'
      },
      {
        title: 'Filtros Rápidos e Busca Instantânea',
        icon: 'fa-solid fa-magnifying-glass',
        target: '.search-box, .search-input',
        description: 'Filtre commits digitando mensagens, hash SHA ou nomes de repositórios. A busca pesquisa em tempo real conforme você digita.',
        tip: 'Os filtros ativos aparecem em destaque e podem ser limpos com um clique no botão "X".'
      },
      {
        title: 'Filtro de Repositórios e Fila Ativa',
        icon: 'fa-solid fa-code-commit',
        target: '.repo-chips-wrapper, .chips-list',
        description: 'Selecione chips de repositórios específicos ou ative o filtro "Na Fila" para acompanhar commits com tarefas ativas no momento.',
        tip: 'O chip "Na Fila" exibe o número de tarefas em execução em tempo real.'
      },
      {
        title: 'Importar Novos Commits do GitLab',
        icon: 'fa-solid fa-file-import',
        target: '.page-header .btn-primary, .title-row',
        description: 'Clique no botão "+ Importar Commit" para abrir a tela de importação em lote a partir das instâncias configuradas do GitLab.',
        tip: 'Você pode colar links diretos ou múltiplos commits para importar com validação prévia.'
      }
    ]
  },

  importar: {
    id: 'importar',
    title: 'Guia de Importação de Commits',
    subtitle: 'Importação em lote via URLs do GitLab com validação em tempo real',
    steps: [
      {
        title: '1. Seleção da Conta ou Instância GitLab',
        icon: 'fa-brands fa-gitlab',
        target: '.git-accounts-grid, .git-account-card, section[aria-labelledby="heading-git-selection"]',
        description: 'Escolha qual token e URL base serão utilizados para ler os commits e diffs da API. O modo "Detecção Automática" identifica o domínio de cada link colado de forma inteligente.',
        tip: 'Se a instância corporativa não estiver listada, adicione-a no atalho "Gerenciar Contas GitLab".'
      },
      {
        title: '2. Inserção das URLs dos Commits',
        icon: 'fa-solid fa-link',
        target: '#input-commits-area, .commits-textarea, .textarea-col',
        description: 'Cole as URLs completas dos commits do GitLab neste campo de texto, inserindo uma URL por linha.',
        tip: 'O contador no rodapé informa em tempo real a quantidade de links válidos identificados.'
      },
      {
        title: '3. Painel de Pré-Visualização Inteligente',
        icon: 'fa-solid fa-magnifying-glass-chart',
        target: '.inspector-col',
        description: 'Conforme você cola os links, o sistema inspeciona automaticamente cada URL, extraindo o hash SHA, o repositório e o domínio correspondente.',
        tip: 'Linhas com formato incompatível ganham uma etiqueta vermelha de alerta.'
      },
      {
        title: '4. Executar Importação em Lote',
        icon: 'fa-solid fa-cloud-arrow-down',
        target: '.action-bar-card, .action-section',
        description: 'Clique em "Importar Commit(s)" para iniciar o download dos diffs, mensagens e metadados com barra de progresso em tempo real.',
        tip: 'Commits já existentes no banco são preservados e identificados para evitar duplicidades.'
      }
    ]
  },

  analisar: {
    id: 'analisar',
    title: 'Guia de Análise com Inteligência Artificial',
    subtitle: 'Geração automatizada de evidências e enquadramento no catálogo de serviços',
    steps: [
      {
        title: '1. Escolha do Modelo de Inteligência Artificial',
        icon: 'fa-solid fa-microchip',
        target: '.model-grid, .model-card, section:has(#heading-passo-1)',
        description: 'Escolha o modelo Gemini ou OpenAI configurado no sistema. Modelos como Gemini Flash oferecem velocidade com alto limite de requisições por minuto.',
        tip: 'Configure os limites de RPM/TPM na tela de Modelos para evitar estouro de cotas.'
      },
      {
        title: '2. Filtro de Status (Pendentes vs Analisados)',
        icon: 'fa-solid fa-filter',
        target: '.status-segmented, .status-btn',
        description: 'Utilize os botões de status para visualizar apenas os commits que ainda não possuem análise de IA gerada.',
        tip: 'Use o campo de busca para encontrar commits de sprints ou funcionalidades específicas.'
      },
      {
        title: '3. Seleção Rápida em Lote',
        icon: 'fa-solid fa-bolt',
        target: '.batch-buttons, .btn-batch-action',
        description: 'Clique em "Selecionar Pendentes" para marcar todos os itens pendentes com um único clique antes de iniciar a análise.',
        tip: 'Você pode desmarcar itens individuais se preferir.'
      },
      {
        title: '4. Enfileirar Análise e Acompanhar Fila',
        icon: 'fa-solid fa-wand-magic-sparkles',
        target: '.action-footer, .page-header .btn-ghost, .page-header',
        description: 'Ao selecionar commits, a barra flutuante permite confirmar o enfileiramento em lote. Você pode acompanhar a execução dos workers em tempo real na aba "Ver Fila de Execução".',
        tip: 'Todas as evidências geradas são 100% editáveis no detalhe do commit.'
      }
    ]
  },

  fila: {
    id: 'fila',
    title: 'Guia da Fila de Execução',
    subtitle: 'Monitoramento em tempo real dos workers de análise e lançamento',
    steps: [
      {
        title: 'Monitor de Concorrência e Workers',
        icon: 'fa-solid fa-bolt',
        target: '.concurrency-badge, .header-left',
        description: 'Veja no topo a capacidade de workers simultâneos divididos entre fila de Análises de IA e fila de Lançamentos automáticos no portal Munka.',
        tip: 'Workers ociosos auxiliam a outra fila automaticamente se houver acúmulo de tarefas.'
      },
      {
        title: 'Coluna de Lançamentos no Portal Munka',
        icon: 'fa-solid fa-list-check',
        target: '.coluna-lancamentos',
        description: 'As tarefas ativas exibem animações e atualizações em tempo real. Clique em "Logs (Ao Vivo)" para assistir à execução passo a passo do Playwright.',
        tip: 'Se ocorrer alguma falha no portal, o motivo exato será gravado nos logs.'
      },
      {
        title: 'Coluna de Ajustes e Sincronização',
        icon: 'fa-solid fa-sliders',
        target: '.coluna-ajustes',
        description: 'A coluna direita é dedicada aos ajustes de tarefas do mês e sincronizações em lote executadas no portal Munka.',
        tip: 'Permite acompanhar edições de perfil, nível e projeto aplicadas em lote.'
      },
      {
        title: 'Ações Globais: Reenfileirar Falhas e Limpeza',
        icon: 'fa-solid fa-arrows-rotate',
        target: '.header-actions, .btn-retry-all',
        description: 'Em caso de instabilidade de rede no portal, o botão "Reenfileirar Todas com Falha" reexecuta os lançamentos sem retrabalho manual.',
        tip: 'Use o botão da vassoura para limpar tarefas de meses passados já concluídas.'
      }
    ]
  },

  'fila-logs': {
    id: 'fila-logs',
    title: 'Guia de Logs de Execução',
    subtitle: 'Auditoria técnica, histórico de retries e diagnóstico de automação',
    steps: [
      {
        title: 'Barra de Filtros e Busca de Logs',
        icon: 'fa-solid fa-magnifying-glass',
        target: '.filters-bar, .search-box',
        description: 'Filtre rapidamente por "Erros", "Retries" ou "Sucesso". Use a busca para encontrar mensagens específicas de erro ou hash de commits.',
        tip: 'A busca pesquisa inclusive o conteúdo textual interno dos logs.'
      },
      {
        title: 'Ações em Lote e Exclusão',
        icon: 'fa-solid fa-trash-can',
        target: '.header-actions, .btn-bulk-delete',
        description: 'Selecione múltiplos logs antigos e exclua-os em lote para manter a base limpa e leve.',
        tip: 'Logs com falha final contêm o relatório completo de diagnóstico.'
      },
      {
        title: 'Lista de Logs e Terminal Interativo',
        icon: 'fa-solid fa-terminal',
        target: '.logs-list, .log-card',
        description: 'Expanda qualquer card para visualizar o log formatado em estilo terminal. Linhas de erro ganham destaque especial.',
        tip: 'Clique no botão "Copiar" para enviar o log técnico ao time de suporte.'
      },
      {
        title: 'Filtros Rápidos por Status',
        icon: 'fa-solid fa-circle-check',
        target: '.status-filters, .filter-pill',
        description: 'Alterne com um clique entre "Todos", "Erros", "Retrying" e "Concluídos" para isolar ocorrências críticas.',
        tip: 'Itens com erro mantêm a pilha de chamadas e capturas de tela quando aplicável.'
      }
    ]
  },

  modelos: {
    id: 'modelos',
    title: 'Guia de Modelos de Inteligência Artificial',
    subtitle: 'Gerenciamento de provedores, limites de taxa (Rate Limit) e custos',
    steps: [
      {
        title: 'Tabela de Modelos e Métricas de Consumo',
        icon: 'fa-solid fa-microchip',
        target: '.model-table, .table-container, .glass-card',
        description: 'Gerencie os modelos de IA cadastrados no sistema (Gemini 2.5 Flash, Gemini Pro, GPT-4o, etc.) e acompanhe o consumo de RPM, TPM e RPD.',
        tip: 'Prefira modelos Flash para análises diárias em lote devido ao excelente custo-benefício.'
      },
      {
        title: 'Controles de Atualização e Métricas',
        icon: 'fa-solid fa-arrows-rotate',
        target: '.actions-header, .header-section',
        description: 'Mantenha o auto-refresh ativo para acompanhar o esgotamento ou renovação dos limites por minuto de cada API.',
        tip: 'O botão "Resetar Métricas" zera contadores locais de requisições.'
      },
      {
        title: 'Simulação e Teste de Conexão com API',
        icon: 'fa-solid fa-bolt',
        target: '.btn-outline, .actions-cell',
        description: 'Clique no botão "Testar" de qualquer modelo para disparar uma requisição rápida de validação e checar se sua chave de API está operando normalmente.',
        tip: 'O tempo de resposta do teste indica a latência média atual da API.'
      },
      {
        title: 'Edição de Limites Máximos (RPM / TPM)',
        icon: 'fa-solid fa-gear',
        target: '.btn-icon, .actions-cell',
        description: 'Clique no ícone de engrenagem para ajustar os parâmetros de RPM (requisições por minuto), TPM (tokens) e cotas diárias de cada modelo.',
        tip: 'O limitador do Nexus previne erros de cota (HTTP 429) pausando tarefas de forma inteligente.'
      }
    ]
  },

  historico: {
    id: 'historico',
    title: 'Guia do Histórico de Envios',
    subtitle: 'Arquivo cronológico de todas as atividades faturadas no portal Munka',
    steps: [
      {
        title: 'Barra de Filtros e Pesquisa',
        icon: 'fa-solid fa-magnifying-glass',
        target: '.filters-toolbar, .search-box',
        description: 'Encontre atividades buscando por título, código do catálogo (ex: 21a, 57b), autor ou mensagem do commit original.',
        tip: 'Use o filtro "Sem Data Fim" para identificar tarefas que foram lançadas sem horário de término.'
      },
      {
        title: 'Organização Cronológica por Datas',
        icon: 'fa-solid fa-clock-rotate-left',
        target: '.date-group-header, .date-group-items, .history-list-grouped',
        description: 'Suas atividades enviadas ficam agrupadas por dia, facilitando a conferência com o seu espelho de ponto e medições.',
        tip: 'O cabeçalho de cada dia exibe a contagem total de atividades enviadas naquela data.'
      },
      {
        title: 'Re-envio Rápido para a Fila',
        icon: 'fa-solid fa-arrows-rotate',
        target: '.btn-reenviar-history, .history-actions',
        description: 'Se precisar reenviar uma atividade cujo status no portal tenha sido alterado ou excluído por engano, utilize o botão "Re-enviar".',
        tip: 'A tarefa será reenfileirada automaticamente na fila de lançamentos.'
      },
      {
        title: 'Rastreabilidade com Hash SHA',
        icon: 'fa-solid fa-code-commit',
        target: '.commit-hash-link, .history-actions, .date-group-items',
        description: 'Clique na badge com o hash SHA do commit para visualizar a evidência original gerada e o diff completo que originou o lançamento.',
        tip: 'Evite excluir atividades do histórico para preservar a integridade das medições.'
      }
    ]
  },

  'tarefas-mes': {
    id: 'tarefas-mes',
    title: 'Guia de Tarefas do Mês (Ajuste Munka)',
    subtitle: 'Conferência, sincronização e edição em lote de lançamentos no portal',
    steps: [
      {
        title: 'Navegação por Período (Mês e Ano)',
        icon: 'fa-solid fa-calendar-check',
        target: '.header-actions-col, .btn-mes-hoje, .btn-nav-mes',
        description: 'Selecione o mês e ano desejados ou use as setas para navegar entre meses anteriores. O botão "Hoje" retorna instantaneamente ao mês corrente.',
        tip: 'O sistema carrega os dados locais instantaneamente e calcula as métricas do mês.'
      },
      {
        title: 'Sincronização em Tempo Real com o Portal',
        icon: 'fa-solid fa-arrows-rotate',
        target: '.btn-sync-munka, .header-actions-col',
        description: 'O botão "Sincronizar no Munka" abre uma automação headless para ler o status real de todas as tarefas diretamente nas telas do portal Munka.',
        tip: 'Execute no início ou final da sprint para garantir que nenhuma aprovação ficou pendente.'
      },
      {
        title: 'Métricas do Mês e Contagem de Tarefas',
        icon: 'fa-solid fa-square-check',
        target: '.metricas-grid, .metrica-card',
        description: 'Acompanhe o total de tarefas lançadas, concluídas e o número de itens selecionados para modificações em lote.',
        tip: 'Clique no botão "Limpar" para desselecionar todos os checkboxes de uma vez.'
      },
      {
        title: 'Filtros Rápidos e Ações em Lote',
        icon: 'fa-solid fa-sliders',
        target: '.filters-bar, .bulk-action-bar, .metricas-grid',
        description: 'Filtre tarefas por texto ou status. Ao marcar checkboxes na listagem, uma barra de ações em lote permite aplicar alterações em múltiplos itens de uma vez só.',
        tip: 'Excelente para quando um lote inteiro de atividades precisa mudar de Backlog para Desenvolvimento.'
      }
    ]
  },

  config: {
    id: 'config',
    title: 'Guia de Configurações do Sistema',
    subtitle: 'Integrações GitLab, credenciais Munka, concorrência e backups',
    steps: [
      {
        title: 'Gestão de Contas do GitLab',
        icon: 'fa-brands fa-gitlab',
        target: '.gitlab-full-section, .git-table-wrapper, #heading-git',
        description: 'Cadastre e gerencie múltiplas URLs de GitLab e tokens de acesso pessoal (PAT). Você pode testar a conexão de cada conta com um clique.',
        tip: 'O Nexus valida permissões de leitura de projetos e commits antes de salvar.'
      },
      {
        title: 'Status Operacional e Concorrência de Workers',
        icon: 'fa-solid fa-bolt',
        target: '.status-bar, .status-item',
        description: 'Visualize os limites de concorrência por fila e a quantidade de núcleos de processamento dedicados à automação.',
        tip: 'O sistema rebalanceia workers automaticamente quando uma fila esvazia.'
      },
      {
        title: 'Backups Automáticos em JSON e SQL',
        icon: 'fa-solid fa-database',
        target: '.backups-list, .config-section:has(.fa-database), .config-section',
        description: 'Crie cópias de segurança de todo o banco de dados e arquivos de evidência a qualquer momento clicando em "Criar Backup Agora".',
        tip: 'O Nexus também realiza auto-save contínuo de todas as alterações persistentes.'
      },
      {
        title: 'Salvar Configurações Globais',
        icon: 'fa-solid fa-floppy-disk',
        target: '.page-header .btn-primary, .page-header',
        description: 'Após alterar credenciais de autenticação, perfis padrão ou concorrência, clique no botão "Salvar" no topo da página para aplicar.',
        tip: 'As configurações ficam salvas no volume de dados persistente.'
      }
    ]
  },

  'commit-detail': {
    id: 'commit-detail',
    title: 'Guia de Detalhes do Commit',
    subtitle: 'Auditoria de evidências geradas, formulário de faturamento e inspeção de diffs',
    steps: [
      {
        title: 'Abas de Navegação (Formulário vs Evidência)',
        icon: 'fa-solid fa-folder-open',
        target: '.card-tabs, .tab-btn',
        description: 'Alterne entre o formulário de edição das atividades faturadas e a pré-visualização da evidência em HTML gerada pela IA.',
        tip: 'A evidência pode ser visualizada ou copiada para a área de transferência com um clique.'
      },
      {
        title: 'Formulário da Atividade Faturada',
        icon: 'fa-solid fa-file-lines',
        target: '.atividade-card, .atividade-header, .card-tabs',
        description: 'Revise o título, descrição, justificativa de entrega, código do catálogo e estimativa HPA. Qualquer campo pode ser refinado livremente.',
        tip: 'Ao alterar o código de serviço, o HPA é recalculado automaticamente.'
      },
      {
        title: 'Barra de Metadados do Commit',
        icon: 'fa-solid fa-code-commit',
        target: '.meta-bar, .meta-edit-btn',
        description: 'Inspecione autor, data, hash SHA e mensagem original do commit. Você pode editar os metadados se necessário para fins de faturamento.',
        tip: 'O botão "Salvar Metadados" persiste as alterações no banco de dados.'
      },
      {
        title: 'Diffs e Arquivos Modificados',
        icon: 'fa-solid fa-code-compare',
        target: '.diff-section, .files-list-interactive, .diff-section-header',
        description: 'Inspecione as alterações linha a linha nos arquivos afetados para auditoria e validação técnica da entrega.',
        tip: 'Arquivos com muitas linhas alteradas podem ser recolhidos para facilitar a leitura.'
      }
    ]
  }
}
