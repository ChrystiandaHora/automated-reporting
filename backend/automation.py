import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright


class MunkaAutomation:
    def __init__(self, username, password, munka_url=None, headless=True, log_callback=None):
        """Initialize the MunkaAutomation instance with credentials and options.

        Args:
            username: Login username for the Munka platform.
            password: Login password for the Munka platform.
            munka_url: Base URL of the Munka portal. Falls back to MUNKA_URL env var.
            headless: Whether to run Chromium in headless mode. Defaults to True.
            log_callback: Optional callable that receives each log message string.
                If provided, it is called in addition to the default stdout print.
                Exceptions raised by the callback are caught and printed, so they
                will never interrupt automation execution.
        """
        self.username = username
        self.password = password
        self.base_url = (munka_url or os.environ.get("MUNKA_URL", "")).rstrip("/")
        self.headless = headless
        self.log_callback = log_callback

    def _log(self, message):
        """Print a log message and forward it to the optional log callback.

        Always prints to stdout with the ``[MunkaAutomation]`` prefix. If a
        ``log_callback`` was supplied at construction time, it is also called
        with the raw message. Any exception raised by the callback is silently
        caught so it never interrupts automation execution.

        Args:
            message: The log message string to emit.
        """
        print(f"[MunkaAutomation] {message}")
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception as e:
                print(f"Erro no callback de log: {e}")

    def _login(self, page):
        """Log in to the Munka platform using the stored credentials.

        Navigates to the Munka root URL and waits for the network to become
        idle. If a password field is not present on the resulting page, an
        active session is assumed and the method returns immediately without
        attempting to fill credentials. Otherwise, the username and password
        inputs are located via broad CSS selectors, filled in, and the submit
        button is clicked. The method then waits for the network to idle again
        before returning.

        Args:
            page: ``playwright.sync_api.Page`` instance representing the active
                browser tab.
        """
        self._log("Acessando a página de login do Munka...")
        page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
        page.wait_for_selector("input[type='password'], #content, .navbar", state="visible", timeout=15000)

        # Se não houver campo de senha, assume que já está logado ou na tela principal
        if not page.locator("input[type='password']").count():
            self._log("Sessão já ativa. Pulando login.")
            return

        self._log("Preenchendo usuário e senha...")
        username_input = page.locator(
            "input[type='text'], input[name*='user'], input[name*='login']"
        ).first
        password_input = page.locator("input[type='password']").first
        submit_btn = page.locator(
            "button[type='submit'], input[type='submit'], "
            "button:has-text('Entrar'), button:has-text('Login')"
        ).first

        username_input.fill(self.username)
        password_input.fill(self.password)
        self._log("Efetuando login...")
        submit_btn.click()
        page.wait_for_selector("#content, .navbar, table, .dashboard", state="visible", timeout=15000)
        self._log("Login realizado com sucesso!")

    def _preencher_select2_ajax(self, page, field_id, search_term, force_ui=False):
        """Interact with a Select2 field (AJAX or static) on the Munka platform.

        The method follows a defensive, multi-step strategy to handle the
        variety of Select2 configurations present in the Munka forms:

        1. Closes any currently open Select2 dropdown via ``Escape``.
        2. Opens the target dropdown by clicking its ``#s2id_<field_id>``
           container. Falls back to triggering ``select2('open')`` via jQuery
           if the container is not found or the click fails.
        3. Waits for the visible search input (``input.select2-input``). If it
           does not appear, forces another jQuery open call and retries — this
           retry covers edge cases where the first click was intercepted.
        4. Clears any pre-existing text, then types ``search_term`` with a
           small per-character delay to mimic human input and trigger AJAX.
        5. Waits 600 ms for AJAX responses or static option rendering.
        6. Clicks the first selectable result in the open dropdown. Falls back
           to pressing ``Enter`` if no clickable result element is found.

        Args:
            page: ``playwright.sync_api.Page`` instance representing the active
                browser tab.
            field_id: The HTML ``id`` attribute of the underlying ``<select>``
                element (e.g. ``"produto"``, ``"projeto"``, ``"regra"``).
            search_term: Text to type into the Select2 search box. For AJAX
                fields this triggers a server-side search; for static fields
                it filters the already-loaded options.
        """
        # Aguarda carregamento de opções (por exemplo, após selecionar Perfil/Cargo)
        self._log(f"Aguardando opções para o campo '{field_id}'...")
        try:
            page.wait_for_function(
                f"() => {{ const el = document.querySelector('#{field_id}'); return el && el.options && el.options.length > 1; }}",
                timeout=4000
            )
        except Exception:
            pass

        # Lista as opções para ajudar na depuração e configuração
        opcoes = page.evaluate(f"() => {{ "
                               f"  const opts = []; "
                               f"  $('#{field_id} option').each(function() {{ "
                               f"    const txt = $(this).text().trim(); "
                               f"    if (txt) opts.push(txt); "
                               f"  }}); "
                               f"  return opts; "
                               f"}}")
        if opcoes:
            self._log(f"Opções disponíveis no select '{field_id}': {opcoes}")

        import re
        # Remove prefixo de colchetes (ex: [DESENV], [ARQ]) para busca e comparação
        search_term_clean = re.sub(r'^\[.*?\]\s*', '', search_term).strip()
        self._log(f"Termo de busca original para '{field_id}': '{search_term}' -> Limpo: '{search_term_clean}'")

        # 0. Tenta seleção direta via jQuery (se as opções já estiverem pré-carregadas no DOM)
        selected = False
        if not force_ui:
            self._log(f"Tentando seleção direta via jQuery para o campo '{field_id}' com termo '{search_term_clean}'...")
            selected = page.evaluate(r"""([fieldId, termClean]) => {
                const $select = $('#' + fieldId);
                if ($select.length === 0) return false;
                
                const normalize = (str) => {
                    if (!str) return '';
                    return str
                        .toLowerCase()
                        .replace(/^\[.*?\]\s*/g, '') // remove brackets prefix
                        .replace(/\(.*?\)/g, '')     // remove parentheses suffix
                        .trim();
                };

                const search = normalize(termClean);
                let foundValue = null;
                $select.find('option').each(function() {
                    const text = $(this).text();
                    const textNorm = normalize(text);
                    if (textNorm && search && (textNorm === search || textNorm.indexOf(search) !== -1 || search.indexOf(textNorm) !== -1)) {
                        foundValue = $(this).val();
                        return false; // break
                    }
                });
                
                if (foundValue !== null && foundValue !== "") {
                    $select.val(foundValue).trigger('change');
                    if (typeof $select.select2 === 'function') {
                        $select.select2('val', foundValue);
                    }
                    return true;
                }
                return false;
            }""", [field_id, search_term_clean])
            
            if selected:
                self._log(f"Campo '{field_id}' selecionado com sucesso via jQuery!")
                page.wait_for_timeout(200)
                return

        self._log(f"Seleção direta via jQuery sem correspondência. Prosseguindo com interação UI...")

        # 1. Fecha qualquer dropdown Select2 que esteja aberto
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)

        # 2. Abre o dropdown: tenta clicar no container s2id_ primeiro,
        #    que é a interação humana que ativa os focus/classes corretos.
        container_selector = f"#s2id_{field_id}"
        try:
            page.wait_for_selector(container_selector, state="visible", timeout=4000)
            page.click(f"{container_selector} a.select2-choice, {container_selector}")
        except Exception:
            # Fallback: Abre via API jQuery do Select2
            page.evaluate(f"() => {{ $('#{field_id}').select2('open'); }}")

        # 3. Aguarda o input de busca ficar visível
        search_input_selector = "input.select2-input:visible"
        try:
            page.wait_for_selector(search_input_selector, state="visible", timeout=5000)
            search_locator = page.locator(search_input_selector).first
        except Exception:
            # Fallback final: tenta forçar o open novamente e aguardar
            page.evaluate(f"() => {{ $('#{field_id}').select2('open'); }}")
            page.wait_for_timeout(200)
            page.wait_for_selector(search_input_selector, state="visible", timeout=5000)
            search_locator = page.locator(search_input_selector).first

        # 4. Digita o termo de busca (limpa antes para garantir estado inicial)
        search_locator.fill("")
        search_locator.type(search_term_clean, delay=35)

        # 5. Aguarda o AJAX retornar resultados (ou opções renderizarem)
        try:
            page.wait_for_selector(
                "div.select2-drop:not(.select2-display-none) .select2-result",
                state="visible", timeout=4000
            )
        except Exception:
            pass  # sem resultados visíveis — o click/Enter no passo 6 vai tratar

        # 6. Seleciona o resultado que corresponde ao termo de busca
        first_result_selector = "div.select2-drop:not(.select2-display-none) .select2-result-selectable"
        try:
            page.wait_for_selector(first_result_selector, state="visible", timeout=4000)
            
            # Localiza o resultado que bate com o termo usando a normalização
            clicked = page.evaluate(r"""([termClean]) => {
                const normalize = (str) => {
                    if (!str) return '';
                    return str
                        .toLowerCase()
                        .replace(/^\[.*?\]\s*/g, '') // remove brackets prefix
                        .replace(/\(.*?\)/g, '')     // remove parentheses suffix
                        .trim();
                };
                
                const search = normalize(termClean);
                let matchedEl = null;
                
                $('div.select2-drop:not(.select2-display-none) .select2-result-selectable').each(function() {
                    const text = $(this).text();
                    const textNorm = normalize(text);
                    if (textNorm && search && (textNorm === search || textNorm.indexOf(search) !== -1 || search.indexOf(textNorm) !== -1)) {
                        matchedEl = this;
                        return false; // break
                    }
                });
                
                if (matchedEl) {
                    $(matchedEl).trigger('mouseenter').click();
                    return true;
                }
                return false;
            }""", [search_term_clean])
            
            if not clicked:
                self._log("Sem correspondência exata no dropdown. Clicando no primeiro resultado disponível...")
                page.click(first_result_selector)
        except Exception:
            # Fallback: pressiona Enter se o input ainda estiver visível/ativo, sem travar o timeout longo
            if search_locator.is_visible():
                try:
                    search_locator.press("Enter", timeout=1500)
                except Exception:
                    pass

        # Aguarda um pouco mais para o Select2 AJAX processar a seleção
        page.wait_for_timeout(600)

        # 7. Validação defensiva: verifica texto exibido no container Select2
        #    (mais confiável que .val() para campos AJAX que populam via JSON)
        displayed_text = page.evaluate(
            f"() => (document.querySelector('#s2id_{field_id} .select2-chosen') || {{}}).textContent || ''"
        )
        import re as _re
        _norm = lambda s: _re.sub(r'\s+', ' ', s.lower().replace('[', '').replace(']', '')).strip()
        if _norm(search_term_clean) and _norm(search_term_clean) in _norm(displayed_text):
            self._log(f"Campo '{field_id}' confirmado pelo texto exibido: '{displayed_text.strip()}'")
            return

        # Fallback: tenta .val() do jQuery (campos não-AJAX)
        selected_val = page.evaluate(f"() => $('#{field_id}').val()")
        # .val() pode retornar array (multiple select) — normaliza para string
        if isinstance(selected_val, list):
            selected_val = selected_val[0] if selected_val else ""
        if not selected_val or selected_val == "" or selected_val == "__None":
            # Segundo fallback: aguarda 1 segundo e verifica tanto .val() quanto texto exibido
            page.wait_for_timeout(1000)
            displayed_text2 = page.evaluate(
                f"() => (document.querySelector('#s2id_{field_id} .select2-chosen') || {{}}).textContent || ''"
            )
            if _norm(search_term_clean) and _norm(search_term_clean) in _norm(displayed_text2):
                self._log(f"Campo '{field_id}' confirmado (fallback delay) pelo texto: '{displayed_text2.strip()}'")
                return
            selected_val = page.evaluate(f"() => $('#{field_id}').val()")
            if isinstance(selected_val, list):
                selected_val = selected_val[0] if selected_val else ""
            if not selected_val or selected_val == "" or selected_val == "__None":
                resultados_busca = []
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(100)
                    page.wait_for_selector(container_selector, state="visible", timeout=3000)
                    page.click(f"{container_selector} a.select2-choice, {container_selector}")
                    page.wait_for_selector(search_input_selector, state="visible", timeout=3000)
                    search_locator.fill("")
                    page.wait_for_timeout(1500)
                    
                    resultados_busca = page.evaluate(r"""() => {
                        const res = [];
                        $('div.select2-drop:not(.select2-display-none) .select2-result').each(function() {
                            const txt = $(this).text().trim();
                            if (txt) res.push(txt);
                        });
                        return res;
                    }""")
                    page.keyboard.press("Escape")
                except Exception:
                    pass

                msg_erro = (
                    f"Não foi possível selecionar '{search_term}' no campo select2 '{field_id}'. "
                    f"Verifique se o nome está correto."
                )
                if resultados_busca:
                    msg_erro += f" Opções disponíveis no dropdown para este campo: {resultados_busca}"
                
                raise ValueError(msg_erro)

    def _verificar_duplicidade_portal(self, page, task_title, target_sha) -> bool:
        """Verifica se uma tarefa com o mesmo título e commit SHA já existe no portal.

        Navega para a listagem, localiza linhas com título idêntico, abre a página de
        edição de cada uma e inspeciona se o campo '#evidencia_commit_sha'
        contém o target_sha.
        """
        self._log("Verificando se a tarefa já existe no Munka (Título + SHA)...")
        page.goto(f"{self.base_url}/tarefamodelview/list/?", wait_until="domcontentloaded")
        page.wait_for_selector("table.table-bordered, div.container-fluid.espacamento", state="visible", timeout=15000)

        task_title_clean = task_title.strip()
        rows = page.locator("table.table-bordered tbody tr")
        count = rows.count()
        edit_urls = []

        for i in range(count):
            row = rows.nth(i)
            title_el = row.locator("td:nth-child(3)")
            if title_el.count() > 0:
                row_title = title_el.text_content().strip()
                if row_title == task_title_clean:
                    edit_link = row.locator("a[href*='tarefamodelview/edit']").first
                    if edit_link.count() > 0:
                        href = edit_link.get_attribute("href")
                        if href:
                            if href.startswith("/"):
                                href = f"{self.base_url}{href}"
                            edit_urls.append(href)

        if not edit_urls:
            self._log("Nenhuma tarefa com esse título encontrada no portal.")
            return False

        # Se target_sha for vazio/nulo ou for "sem_sha", usamos apenas a validação por título
        if not target_sha or target_sha == "sem_sha":
            self._log("Target SHA não fornecido ou inválido. Usando apenas validação de título.")
            self._log(f"Duplicidade detectada (título '{task_title_clean}' já cadastrado e sem SHA definido).")
            return True

        self._log(f"Encontrada(s) {len(edit_urls)} tarefa(s) com título '{task_title_clean}'. Inspecionando commit SHA...")

        # Visita cada URL de edição para checar o SHA
        for edit_url in edit_urls:
            try:
                self._log(f"Inspecionando tarefa no link de edição: {edit_url}")
                page.goto(edit_url, wait_until="domcontentloaded")
                page.wait_for_selector("form, #nome", state="visible", timeout=15000)

                # Garante que o painel 'Execução' esteja aberto para carregar o campo de commit SHA
                painel_execucao = page.locator('[id="3_href"]')
                if painel_execucao.count() > 0:
                    if not painel_execucao.is_visible():
                        page.click("a.accordion-toggle:has-text('Execução')")
                        page.wait_for_selector('[id="3_href"]', state="visible", timeout=5000)

                # Aguarda e lê o valor do campo '#evidencia_commit_sha'
                sha_input = page.locator("#evidencia_commit_sha")
                sha_input.wait_for(state="attached", timeout=5000)
                current_sha_val = sha_input.input_value().strip()

                self._log(f"Valor atual de evidencia_commit_sha no portal: '{current_sha_val}'")

                # Compara usando substring case-insensitive
                target_sha_clean = target_sha.strip().lower()
                target_sha_short = target_sha_clean[:8]
                current_sha_val_lower = current_sha_val.lower()

                if target_sha_clean in current_sha_val_lower or target_sha_short in current_sha_val_lower:
                    self._log(f"Duplicidade confirmada! A tarefa com o SHA/URL '{target_sha}' já está cadastrada no portal.")
                    return True
            except Exception as e:
                self._log(f"Erro ao verificar tarefa na URL {edit_url}: {e}. Continuando verificação...")

        self._log("Nenhuma tarefa correspondente ao título e SHA encontrados. Prosseguindo com cadastro.")
        return False

    def cadastrar_tarefa(
        self, task_data, product_name="[DESENV] MUNKA", project_name="MUNKA Multicontrato", dev_profile=None, commit_metadata=None
    ) -> str:
        """Create a new task (Fase 1) on the Munka platform.

        Opens a new Playwright browser session, logs in, checks for duplicate
        task titles, fills the task creation form (profile, start date, product,
        project, optional complexity matrix, service rule, title, and status),
        and saves the record. The browser is closed before returning.

        Args:
            task_data: Dictionary with task fields:
                - ``titulo`` (str): Task title. Used for duplicate detection and
                  for filling the ``#nome`` field.
                - ``codigo_id`` (str): Service/rule code searched via Select2
                  (``#regra`` field). Skipped if empty.
                - ``hpa`` (str | float): Executed hours. Not used in this phase;
                  reserved for ``cadastrar_e_homologar_completo``.
                - ``etapa`` (str): Pipeline stage. Informational; not directly
                  submitted in this phase.
                - ``is_media`` (bool): When ``True``, injects the 15 medium-
                  complexity scores into the complexity matrix and triggers the
                  site's native recalculation function.
                - ``evidencia_html`` (str): Custom evidence HTML. Not used in
                  this phase; reserved for Fase 2.
            product_name: Display name of the Munka product to select via
                Select2 (``#produto`` field). Defaults to ``"[DESENV] MUNKA"``.
            project_name: Display name of the Munka project to select via
                Select2 (``#projeto`` field). Defaults to ``"MUNKA Multicontrato"``.
            dev_profile: Dictionary with developer profile fields:
                - ``cargo`` (str): Numeric string for the role/position value
                  set on ``#cargo``. Defaults to ``"9"``.
                - ``nivel`` (str): Numeric string for the seniority level set
                  on ``#nivel``. Defaults to ``"3"``.
                - ``responsavel`` (str): Search term for the responsible person
                  Select2 field. Skipped when empty or absent.
                - ``status_id`` (str): Numeric string for the task status set
                  on ``#status``. Defaults to ``"20"`` (Homologação).
            commit_metadata: Dictionary with commit/timing metadata:
                - ``data_inicio`` (str): Start date in ``DD/MM/YYYY HH:MM``
                  format, filled into ``#data_inicio``.
                - ``sha`` (str): Commit SHA. Used as fallback for the commit
                  evidence field when ``url`` is absent (Fase 2 only).

        Returns:
            The task title string (``task_data["titulo"]``) on success, or the
            sentinel string ``"PULADA_DUPLICADA"`` if a task with the same
            title was already found in the listing table.

        Raises:
            FileNotFoundError: If the evidence image path does not exist
                (only relevant when called as part of a combined flow).
        """
        if dev_profile is None:
            dev_profile = {"cargo": "9", "nivel": "3", "responsavel": ""}
        if commit_metadata is None:
            commit_metadata = {
                "data_inicio": datetime.now().strftime("%d/%m/%Y 09:00"),
                "sha": "sem_sha",
            }

        self._log("Iniciando cadastro de tarefa...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--disable-gpu", "--disable-software-rasterizer"])
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_navigation_timeout(90000)

            # 1. Login
            self._login(page)

            # 1.5. Verificar duplicados na listagem de tarefas
            task_title = task_data.get("titulo", "").strip()
            target_sha = commit_metadata.get("sha", "sem_sha")
            if self._verificar_duplicidade_portal(page, task_title, target_sha):
                browser.close()
                return "PULADA_DUPLICADA"

            # 2. Navegar para criação
            self._log("Abrindo formulário de cadastro de tarefa...")
            page.goto(f"{self.base_url}/tarefamodelview/add", wait_until="domcontentloaded")
            page.wait_for_selector("form, #nome", state="visible", timeout=15000)
            # Aguarda o Select2 estar completamente inicializado
            page.wait_for_selector("#s2id_produto, #s2id_projeto", state="visible", timeout=5000)

            # 3. Preencher Nome (Título)
            self._log(f"Preenchendo título da tarefa: '{task_data.get('titulo')}'...")
            page.locator("#nome").fill(task_data.get("titulo", ""))

            # 4. Preencher Perfil (Cargo) e Nível usando jQuery do site
            self._log(f"Selecionando Perfil: Cargo '{dev_profile.get('cargo')}' e Nível '{dev_profile.get('nivel')}'...")
            page.evaluate(
                f"() => {{ $('#cargo').val('{dev_profile['cargo']}').trigger('change'); }}"
            )
            page.wait_for_timeout(100)
            page.evaluate(
                f"() => {{ $('#nivel').val('{dev_profile['nivel']}').trigger('change'); }}"
            )
            page.wait_for_timeout(100)

            # 5. Selecionar Responsável usando Select2 AJAX
            responsavel_busca = dev_profile.get("responsavel", "")
            if responsavel_busca:
                self._log(f"Selecionando Responsável: '{responsavel_busca}'...")
                self._preencher_select2_ajax(page, "responsavel", responsavel_busca)

            # 6. Preencher Data de Início
            self._log(f"Preenchendo Data de Início: '{commit_metadata['data_inicio']}'...")
            data_inicio_input = page.locator("#data_inicio")
            data_inicio_input.fill(commit_metadata["data_inicio"])
            data_inicio_input.press("Tab")  # Tira o foco para disparar validações

            # 8. Selecionar Tipo (projeto) via jQuery
            self._log("Selecionando Tipo de tarefa: 'projeto'...")
            page.evaluate("() => { $('#tipo').val('projeto').trigger('change'); }")
            page.wait_for_timeout(200)  # Aguarda aparecer o select condicional de projeto

            # 7. Selecionar Produto via Select2 (busca pelo nome digitado pelo usuário)
            self._log(f"Selecionando Produto: '{product_name}'...")
            self._preencher_select2_ajax(page, "produto", product_name, force_ui=True)
            page.wait_for_timeout(1000)  # Aguarda carregar os projetos no select condicional via AJAX

            # 9. Selecionar Projeto (Select condicional AJAX) - busca pelo nome do projeto
            self._log(f"Selecionando Projeto: '{project_name}'...")
            self._preencher_select2_ajax(page, "projeto", project_name, force_ui=True)

            # 10. Matriz de Complexidade Condicional
            # Se for complexidade média, precisamos alterar as 15 pontuações
            is_media = task_data.get("is_media", False)
            if is_media:
                self._log("Complexidade média detectada. Preenchendo matriz de 15 pontos...")
                # Garante que o painel de complexidade está expandido
                # Nota: seletores CSS não aceitam IDs que começam com número → usar [id="..."]
                painel_complexidade = page.locator('[id="1_href"]')
                if not painel_complexidade.is_visible():
                    page.click("a.accordion-toggle:has-text('Complexidade')")
                    page.wait_for_selector('[id="1_href"]', state="visible")

                # Injeta os 15 valores requeridos na tabela de pontuação via jQuery
                matrix_script = r"""() => {
                    $('#Volume\ de\ Dados-13').val('37').trigger('change');
                    $('#Processamento\ Distribuido-14').val('38').trigger('change');
                    $('#Escalabilidade-15').val('41').trigger('change');
                    $('#Publico\ Alvo-16').val('45').trigger('change');
                    $('#Volume\ de\ Acessos-17').val('48').trigger('change');
                    $('#Desempenho-18').val('50').trigger('change');
                    $('#Disponibilidade-19').val('52').trigger('change');
                    $('#Segurança-20').val('53').trigger('change');
                    $('#Interoperabilidade-21').val('56').trigger('change');
                    $('#Confiabilidade-22').val('58').trigger('change');
                    $('#Padroes\ de\ Projeto-23').val('60').trigger('change');
                    $('#Legais-24').val('62').trigger('change');
                    $('#Estrategia\ Governamental-25').val('64').trigger('change');
                    $('#Urgencia-26').val('66').trigger('change');
                    $('#Impacto-27').val('68').trigger('change');

                    // Dispara recálculo nativo do site
                    calcular_pontuacao_requisitos(atualiza_servicos);
                }"""
                page.evaluate(matrix_script)
                # Aguarda o site processar o recálculo da pontuação
                try:
                    page.wait_for_function(
                        "() => { const el = document.querySelector('#pontuacao_total, [name*=pontuacao], .pontuacao-resultado'); "
                        "return el && el.value && parseFloat(el.value) > 0; }",
                        timeout=3000
                    )
                except Exception:
                    page.wait_for_timeout(500)  # fallback conservador

            # 11. Selecionar Serviço (regra) - Autocomplete Select2
            codigo_id = task_data.get("codigo_id", "")
            if codigo_id:
                self._log(f"Selecionando Serviço (Regra): '{codigo_id}'...")
                self._preencher_select2_ajax(page, "regra", codigo_id)

            # 12. Selecionar Status como "Homologação" (valor "20") ou o configurado na barra lateral
            status_id = "20"
            if dev_profile and "status_id" in dev_profile:
                status_id = dev_profile["status_id"]
            
            self._log(f"Configurando status para: '{status_id}'...")
            page.locator("#status").wait_for(state="attached", timeout=5000)
            select2_script = f"""() => {{
                var $status = $('#status');
                if ($status.length) {{
                    $status.val('{status_id}').trigger('change');
                    if (typeof $status.select2 === 'function') {{
                        $status.select2('val', '{status_id}');
                    }}
                }}
            }}"""
            page.evaluate(select2_script)
            page.wait_for_timeout(100)

            # 13. Salvar (garantindo fechamento de overlays do Select2)
            page.keyboard.press("Escape")
            page.evaluate("() => { if (typeof $ !== 'undefined') { $('.my_select2, select').select2('close'); } }")
            page.wait_for_timeout(200)

            self._log("Salvando cadastro da tarefa...")
            save_btn = page.locator("button[type='submit'], input[type='submit']").first
            save_btn.click()
            
            # Aguarda a transação ser processada pelo servidor Munka
            self._log("Aguardando redirecionamento pós-salvamento...")
            try:
                page.wait_for_url("**/tarefamodelview/list/**", timeout=15000)
            except Exception:
                try:
                    page.wait_for_url("**/", timeout=5000)
                except Exception:
                    page.wait_for_load_state("networkidle")

            browser.close()
            self._log("Tarefa cadastrada com sucesso!")
            return task_data.get("titulo", "")

    def anexar_evidencia_e_homologar(
        self, task_title, image_path, act=None, commit_metadata=None, status_id="20", custom_evidence_html=None
    ):
        """Attach evidence and finalize homologation for an existing task (Fase 2).

        Opens a new Playwright browser session, logs in, locates the task row
        in the listing table by title, opens the edit form, expands the
        "Execução" panel, fills in the end date (derived from
        ``commit_metadata["data_inicio"]`` at 18:00, or falls back to
        ``data_fim``), executed hours, evidence HTML (injected directly into
        the TinyMCE iframe body), commit SHA or URL, and uploads the evidence
        image. Finally sets the task status and saves. The browser is closed
        before returning.

        Args:
            task_title: Exact title of the task to locate in the listing table.
            image_path: Absolute path to the screenshot/image file to upload as
                the evidence attachment (``#evidencia_anexo``).
            act: Dictionary with activity fields used to build the default
                evidence HTML when ``custom_evidence_html`` is not provided:
                - ``hpa`` (str | float): Executed hours. Defaults to ``"1.0"``.
                - ``descricao`` (str): Activity description paragraph.
                - ``justificativa`` (str): Technical justification paragraph.
            commit_metadata: Dictionary with commit/timing metadata:
                - ``data_inicio`` (str): Start date in ``DD/MM/YYYY HH:MM``
                  format. The end date is derived from this value at 18:00.
                - ``data_fim`` (str): Explicit end date fallback in
                  ``DD/MM/YYYY HH:MM`` format, used when ``data_inicio`` is
                  absent or too short.
                - ``sha`` (str): Commit SHA used in the evidence text and as
                  fallback for ``#evidencia_commit_sha``.
                - ``url`` (str): Full commit URL. Takes precedence over ``sha``
                  when filling ``#evidencia_commit_sha``.
            status_id: Numeric string for the final task status set on
                ``#status``. Defaults to ``"20"`` (Homologação).
            custom_evidence_html: When provided, this HTML string is injected
                verbatim into the TinyMCE evidence editor, bypassing the
                auto-generated evidence template.

        Raises:
            FileNotFoundError: If ``image_path`` does not point to an existing
                file.
            ValueError: If the task with ``task_title`` cannot be found in the
                listing table. A debug screenshot is saved to
                ``/tmp/debug_list_not_found.png``.
        """
        if act is None:
            act = {"hpa": "1.0"}
        if commit_metadata is None:
            commit_metadata = {
                "data_fim": datetime.now().strftime("%d/%m/%Y 18:00"),
                "sha": "sem_sha",
            }

        # Evidencia Anexo removido — image_path não é mais utilizado

        self._log(f"Iniciando anexo de evidências para a tarefa: '{task_title}'...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--disable-gpu", "--disable-software-rasterizer"])
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_navigation_timeout(90000)

            # 1. Login
            self._login(page)

            # Navegar para a listagem de tarefas
            self._log("Carregando listagem de tarefas no Munka...")
            page.goto(f"{self.base_url}/tarefamodelview/list/?", wait_until="domcontentloaded")
            page.wait_for_selector("table.table-bordered, div.container-fluid.espacamento", state="visible", timeout=15000)

            # 2. Localizar o botão "Editar" na linha correspondente na tabela
            self._log(f"Localizando tarefa '{task_title}' na listagem da tabela...")
            try:
                # Aguarda a tabela/linha carregar
                row = page.locator("table.table-bordered tbody tr").filter(has_text=task_title).first
                row.wait_for(timeout=15000)
                edit_btn = row.locator("a[href*='tarefamodelview/edit']").first
            except Exception as e:
                # Captura print de debug se não achar na listagem
                page.screenshot(path="/tmp/debug_list_not_found.png")
                raise ValueError(
                    f"Não foi possível encontrar a tarefa '{task_title}' na listagem da tabela. "
                    f"Verifique o print /tmp/debug_list_not_found.png"
                ) from e

            self._log("Clicando no botão 'Editar'...")
            edit_btn.click()
            page.wait_for_selector("form, #nome", state="visible", timeout=15000)

            # Mudar status final para o configurado ANTES de preencher a execução
            self._log(f"Definindo status final para: '{status_id}'...")
            page.locator("#status").wait_for(state="attached", timeout=5000)
            select2_script = f"""() => {{
                var $status = $('#status');
                if ($status.length) {{
                    $status.val('{status_id}').trigger('change');
                    if (typeof $status.select2 === 'function') {{
                        $status.select2('val', '{status_id}');
                    }}
                }}
            }}"""
            page.evaluate(select2_script)
            page.wait_for_timeout(200)

            # 4. Preencher o bloco Execução
            self._log("Verificando se o painel 'Execução' está aberto...")
            if not page.locator("#data_fim").is_visible():
                self._log("Painel 'Execução' colapsado. Clicando para expandir...")
                page.locator('[id="3_href"]').click()
                page.locator("#data_fim").wait_for(state="visible", timeout=5000)

            # Data do Fim: preenche com base no commit_metadata["data_inicio"], alterando o horário para 18:00
            data_inicio = commit_metadata.get("data_inicio", "")
            if data_inicio and len(data_inicio) >= 10:
                data_fim = f"{data_inicio[:10]} 18:00"
            else:
                data_fim = commit_metadata.get("data_fim", datetime.now().strftime("%d/%m/%Y 18:00"))

            self._log(f"Preenchendo Data de Fim: '{data_fim}'...")
            page.locator("#data_fim").fill(data_fim)
            page.locator("#data_fim").press("Tab")

            # Horas Executadas
            self._log(f"Preenchendo Horas Executadas: '{act.get('hpa', '1.0')}' HPA...")
            page.locator("#horas_executadas").fill(str(act.get("hpa", "1.0")))

            # Evidências (TinyMCE)
            if custom_evidence_html:
                self._log("Utilizando HTML customizado de evidência...")
                evidence_text = custom_evidence_html
            else:
                self._log("Gerando HTML padrão de evidência...")
                desc_text = act.get("descricao", "")
                just_text = act.get("justificativa", "")
                evidence_text = (
                    f"<p>{desc_text}</p>"
                    f"<p><strong>Justificativa Técnica:</strong></p>"
                    f"<p>{just_text}</p>"
                    f"<p>Evidência de codificação gerada automaticamente a partir "
                    f"do commit SHA {commit_metadata.get('sha', 'sem_sha')}. Ver anexo.</p>"
                )
            
            self._log("Injetando conteúdo HTML no editor TinyMCE de evidências...")
            iframe = page.frame_locator("#evidencias_ifr")
            tinymce_body = iframe.locator("body#tinymce")
            # Aguarda o TinyMCE de evidências carregar para evitar pular em branco
            tinymce_body.wait_for(state="visible", timeout=10000)
            tinymce_body.evaluate(
                "(el, html) => { el.innerHTML = html; }", evidence_text
            )

            # Evidência commit SHA (URL completa ou fallback para SHA)
            commit_val = commit_metadata.get("url") or commit_metadata.get("sha", "sem_sha")
            self._log(f"Preenchendo Commit SHA/URL: '{commit_val}'...")
            page.locator("#evidencia_commit_sha").fill(commit_val)

            # Evidencia Anexo removido conforme solicitado

            # Salvar edição (garantindo fechamento de overlays do Select2)
            page.keyboard.press("Escape")
            page.evaluate("() => { if (typeof $ !== 'undefined') { $('.my_select2, select').select2('close'); } }")
            page.wait_for_timeout(100)

            self._log("Salvando alterações da homologação...")
            save_btn = page.locator("button[type='submit'], input[type='submit']").first
            save_btn.click()
            
            # Aguarda a transação ser processada pelo servidor Munka
            self._log("Aguardando confirmação do salvamento...")
            try:
                page.wait_for_url("**/tarefamodelview/list/**", timeout=15000)
            except Exception:
                try:
                    page.wait_for_url("**/", timeout=5000)
                except Exception:
                    page.wait_for_load_state("networkidle")

            browser.close()
            self._log("Evidências anexadas e homologação concluída!")

    def cadastrar_e_homologar_completo(
        self, task_data, image_path, product_name="[DESENV] MUNKA", project_name="MUNKA Multicontrato", dev_profile=None, commit_metadata=None, custom_evidence_html=None
    ) -> str:
        """Run the full task workflow (Cadastro + Evidência + Homologação) in one browser session.

        Combines Fase 1 (task creation) and Fase 2 (evidence attachment and
        homologation) without closing the browser between phases. This avoids
        the overhead of a second login and guarantees that the evidence is
        attached to the task that was just created, eliminating race conditions
        that could occur when two sessions run sequentially.

        The method first checks for a duplicate title in the listing table. If
        found, it closes the browser and returns the sentinel ``"PULADA_DUPLICADA"``
        immediately without submitting any form.

        After saving the new task, it navigates back to the listing table (or
        remains there if the server already redirected), locates the newly
        created row, opens the edit form, fills the execution block
        (``data_fim``, ``horas_executadas``, TinyMCE evidence, commit SHA/URL,
        image upload), sets the final status, and saves.

        Args:
            task_data: Dictionary with task fields:
                - ``titulo`` (str): Task title. Used for duplicate detection,
                  the ``#nome`` field, and locating the row in Fase 2.
                - ``codigo_id`` (str): Service/rule code for the Select2
                  ``#regra`` field. Skipped if empty.
                - ``hpa`` (str | float): Executed hours filled into
                  ``#horas_executadas`` in Fase 2. Defaults to ``"1.0"``.
                - ``etapa`` (str): Pipeline stage. Informational only.
                - ``is_media`` (bool): When ``True``, injects the 15 medium-
                  complexity scores and triggers site recalculation.
                - ``evidencia_html`` (str): Not read directly; pass
                  ``custom_evidence_html`` instead for custom evidence content.
            image_path: Absolute path to the screenshot/image file to upload as
                the evidence attachment (``#evidencia_anexo``).
            product_name: Display name of the Munka product for the Select2
                ``#produto`` field. Defaults to ``"[DESENV] MUNKA"``.
            project_name: Display name of the Munka project for the Select2
                ``#projeto`` field. Defaults to ``"MUNKA Multicontrato"``.
            dev_profile: Dictionary with developer profile fields:
                - ``cargo`` (str): Numeric string for ``#cargo``. Defaults to
                  ``"9"``.
                - ``nivel`` (str): Numeric string for ``#nivel``. Defaults to
                  ``"3"``.
                - ``responsavel`` (str): Search term for the responsible person
                  Select2 field. Skipped when empty or absent.
                - ``status_id`` (str): Numeric string for the task status set
                  on ``#status`` in both phases. Defaults to ``"20"``
                  (Homologação).
            commit_metadata: Dictionary with commit/timing metadata:
                - ``data_inicio`` (str): Start date in ``DD/MM/YYYY HH:MM``
                  format for ``#data_inicio``. The end date is derived from
                  this value at 18:00.
                - ``data_fim`` (str): Explicit end date fallback in
                  ``DD/MM/YYYY HH:MM`` format.
                - ``sha`` (str): Commit SHA used in the evidence text and as
                  fallback for ``#evidencia_commit_sha``.
                - ``url`` (str): Full commit URL. Takes precedence over ``sha``
                  when filling ``#evidencia_commit_sha``.
            custom_evidence_html: When provided, this HTML string is injected
                verbatim into the TinyMCE evidence editor, bypassing the
                auto-generated evidence template.

        Returns:
            The task title string (``task_data["titulo"]``) on successful
            completion of both phases, or the sentinel string
            ``"PULADA_DUPLICADA"`` if a task with the same title was already
            found in the listing table before any form was submitted.

        Raises:
            FileNotFoundError: If ``image_path`` does not point to an existing
                file. Raised before the browser is launched.
            ValueError: If the newly created task cannot be located in the
                listing table during Fase 2. A debug screenshot is saved to
                ``/tmp/debug_edit_not_found.png``.
        """
        if dev_profile is None:
            dev_profile = {"cargo": "9", "nivel": "3", "responsavel": "", "status_id": "17"}
        if commit_metadata is None:
            commit_metadata = {
                "data_inicio": datetime.now().strftime("%d/%m/%Y 09:00"),
                "data_fim": datetime.now().strftime("%d/%m/%Y 18:00"),
                "sha": "sem_sha",
            }
        status_id = dev_profile.get("status_id", "17")

        # Evidencia Anexo removido — image_path não é mais utilizado

        self._log("Iniciando fluxo completo (Cadastro + Evidência + Homologação)...")
        with sync_playwright() as p:
            self._log("Inicializando navegador Chromium...")
            browser = p.chromium.launch(headless=self.headless, args=["--disable-gpu", "--disable-software-rasterizer"])
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_navigation_timeout(90000)

            # 1. Login
            self._login(page)

            # 1.5. Verificar duplicados na listagem de tarefas
            task_title = task_data.get("titulo", "").strip()
            target_sha = commit_metadata.get("sha", "sem_sha")
            if self._verificar_duplicidade_portal(page, task_title, target_sha):
                browser.close()
                return "PULADA_DUPLICADA"

            # 2. Navegar para criação
            self._log("Carregando formulário de criação de tarefa...")
            page.goto(f"{self.base_url}/tarefamodelview/add", wait_until="domcontentloaded")
            page.wait_for_selector("form, #nome", state="visible", timeout=15000)
            # Aguarda o Select2 estar completamente inicializado
            page.wait_for_selector("#s2id_produto, #s2id_projeto", state="visible", timeout=5000)

            # 3. Preencher Nome (Título)
            self._log(f"Preenchendo Título da tarefa: '{task_data.get('titulo')}'...")
            page.locator("#nome").fill(task_data.get("titulo", ""))

            # 4. Preencher Perfil (Cargo) e Nível
            self._log(f"Preenchendo Perfil: Cargo '{dev_profile.get('cargo')}' e Nível '{dev_profile.get('nivel')}'...")
            page.evaluate(f"() => {{ $('#cargo').val('{dev_profile['cargo']}').trigger('change'); }}")
            page.wait_for_timeout(100)
            page.evaluate(f"() => {{ $('#nivel').val('{dev_profile['nivel']}').trigger('change'); }}")
            page.wait_for_timeout(100)

            # 5. Selecionar Responsável
            responsavel_busca = dev_profile.get("responsavel", "")
            if responsavel_busca:
                self._log(f"Selecionando Responsável: '{responsavel_busca}'...")
                self._preencher_select2_ajax(page, "responsavel", responsavel_busca)

            # 6. Preencher Data de Início
            self._log(f"Preenchendo Data de Início: '{commit_metadata['data_inicio']}'...")
            data_inicio_input = page.locator("#data_inicio")
            data_inicio_input.fill(commit_metadata["data_inicio"])
            data_inicio_input.press("Tab")

            # 8. Selecionar Tipo (projeto)
            self._log("Configurando Tipo de tarefa para 'projeto'...")
            page.evaluate("() => { $('#tipo').val('projeto').trigger('change'); }")
            page.wait_for_timeout(200)

            # 7. Selecionar Produto
            self._log(f"Selecionando Produto: '{product_name}'...")
            self._preencher_select2_ajax(page, "produto", product_name, force_ui=True)
            page.wait_for_timeout(1000)  # Aguarda carregar os projetos no select condicional via AJAX

            # 9. Selecionar Projeto
            self._log(f"Selecionando Projeto: '{project_name}'...")
            self._preencher_select2_ajax(page, "projeto", project_name, force_ui=True)

            # 10. Matriz de Complexidade se for média
            is_media = task_data.get("is_media", False)
            if is_media:
                self._log("Complexidade média detectada. Preenchendo matriz de 15 pontos do Munka...")
                painel_complexidade = page.locator('[id="1_href"]')
                if not painel_complexidade.is_visible():
                    page.click("a.accordion-toggle:has-text('Complexidade')")
                    page.wait_for_selector('[id="1_href"]', state="visible")

                matrix_script = r"""() => {
                    $('#Volume\ de\ Dados-13').val('37').trigger('change');
                    $('#Processamento\ Distribuido-14').val('38').trigger('change');
                    $('#Escalabilidade-15').val('41').trigger('change');
                    $('#Publico\ Alvo-16').val('45').trigger('change');
                    $('#Volume\ de\ Acessos-17').val('48').trigger('change');
                    $('#Desempenho-18').val('50').trigger('change');
                    $('#Disponibilidade-19').val('52').trigger('change');
                    $('#Segurança-20').val('53').trigger('change');
                    $('#Interoperabilidade-21').val('56').trigger('change');
                    $('#Confiabilidade-22').val('58').trigger('change');
                    $('#Padroes\ de\ Projeto-23').val('60').trigger('change');
                    $('#Legais-24').val('62').trigger('change');
                    $('#Estrategia\ Governamental-25').val('64').trigger('change');
                    $('#Urgencia-26').val('66').trigger('change');
                    $('#Impacto-27').val('68').trigger('change');
                    calcular_pontuacao_requisitos(atualiza_servicos);
                }"""
                page.evaluate(matrix_script)
                # Aguarda o site processar o recálculo da pontuação
                try:
                    page.wait_for_function(
                        "() => { const el = document.querySelector('#pontuacao_total, [name*=pontuacao], .pontuacao-resultado'); "
                        "return el && el.value && parseFloat(el.value) > 0; }",
                        timeout=3000
                    )
                except Exception:
                    page.wait_for_timeout(500)  # fallback conservador

            # 11. Selecionar Serviço (regra)
            codigo_id = task_data.get("codigo_id", "")
            if codigo_id:
                self._log(f"Selecionando Serviço (Regra): '{codigo_id}'...")
                self._preencher_select2_ajax(page, "regra", codigo_id)

            # 12. Selecionar Status inicial (Homologação ou o configurado)
            self._log(f"Configurando status inicial para: '{status_id}'...")
            page.locator("#status").wait_for(state="attached", timeout=5000)
            select2_script = f"""() => {{
                var $status = $('#status');
                if ($status.length) {{
                    $status.val('{status_id}').trigger('change');
                    if (typeof $status.select2 === 'function') {{
                        $status.select2('val', '{status_id}');
                    }}
                }}
            }}"""
            page.evaluate(select2_script)
            page.wait_for_timeout(100)

            # 13. Salvar Cadastro
            page.keyboard.press("Escape")
            page.evaluate("() => { if (typeof $ !== 'undefined') { $('.my_select2, select').select2('close'); } }")
            page.wait_for_timeout(200)

            self._log("Salvando cadastro da tarefa...")
            save_btn = page.locator("button[type='submit'], input[type='submit']").first
            save_btn.click()

            # Aguarda a submissão completar
            self._log("Aguardando processamento do cadastro...")
            try:
                page.wait_for_url("**/tarefamodelview/list/**", timeout=15000)
            except Exception:
                try:
                    page.wait_for_url("**/", timeout=5000)
                except Exception:
                    page.wait_for_load_state("networkidle")
            
            # --- FASE 2: EDITAR E ANEXAR EVIDÊNCIAS DIRETAMENTE ---
            # Se já estivermos na listagem, não precisamos recarregar. Se não, navegamos até lá.
            if "/tarefamodelview/list/" not in page.url:
                self._log("Navegando para a listagem de tarefas...")
                page.goto(f"{self.base_url}/tarefamodelview/list/?", wait_until="domcontentloaded")
            else:
                self._log("Já estamos na listagem de tarefas. Carregando dados...")
            page.wait_for_selector("table.table-bordered, div.container-fluid.espacamento", state="visible", timeout=15000)

            self._log(f"Localizando tarefa recém-criada '{task_data.get('titulo')}' na tabela...")
            try:
                # Aguarda a tabela/linha carregar
                task_title = task_data.get('titulo')
                row = page.locator("table.table-bordered tbody tr").filter(has_text=task_title).first
                row.wait_for(timeout=15000)
                edit_btn = row.locator("a[href*='tarefamodelview/edit']").first
            except Exception as e:
                # Captura print de debug para entender onde a página travou ou se deu erro de validação
                page.screenshot(path="/tmp/debug_edit_not_found.png")
                raise ValueError(f"Não foi possível encontrar a tarefa recém-criada '{task_title}' na listagem. Ver /tmp/debug_edit_not_found.png") from e

            self._log("Clicando no botão 'Editar'...")
            edit_btn.click()
            page.wait_for_selector("form, #nome", state="visible", timeout=15000)

            # Mudar status final para o configurado ANTES de preencher a execução
            self._log(f"Configurando status final para: '{status_id}'...")
            page.locator("#status").wait_for(state="attached", timeout=5000)
            page.evaluate(select2_script)
            page.wait_for_timeout(200)

            # Expandir painel de Execução
            self._log("Verificando se o painel 'Execução' está aberto...")
            if not page.locator("#data_fim").is_visible():
                self._log("Painel 'Execução' colapsado. Clicando para expandir...")
                page.locator('[id="3_href"]').click()
                page.locator("#data_fim").wait_for(state="visible", timeout=5000)

            # Data de Fim
            data_inicio = commit_metadata.get("data_inicio", "")
            if data_inicio and len(data_inicio) >= 10:
                data_fim = f"{data_inicio[:10]} 18:00"
            else:
                data_fim = commit_metadata.get("data_fim", datetime.now().strftime("%d/%m/%Y 18:00"))

            self._log(f"Preenchendo Data de Fim: '{data_fim}'...")
            page.locator("#data_fim").fill(data_fim)
            page.locator("#data_fim").press("Tab")

            # Horas Executadas
            self._log(f"Preenchendo Horas Executadas: '{task_data.get('hpa', '1.0')}' HPA...")
            page.locator("#horas_executadas").fill(str(task_data.get("hpa", "1.0")))

            # Evidências (TinyMCE)
            if custom_evidence_html:
                self._log("Utilizando HTML customizado de evidência...")
                evidence_text = custom_evidence_html
            else:
                self._log("Gerando HTML padrão de evidência...")
                desc_text = task_data.get("descricao", "")
                just_text = task_data.get("justificativa", "")
                evidence_text = (
                    f"<p>{desc_text}</p>"
                    f"<p><strong>Justificativa Técnica:</strong></p>"
                    f"<p>{just_text}</p>"
                    f"<p>Evidência de codificação gerada automaticamente a partir "
                    f"do commit SHA {commit_metadata.get('sha', 'sem_sha')}. Ver anexo.</p>"
                )

            self._log("Injetando conteúdo HTML no editor TinyMCE de evidências...")
            iframe = page.frame_locator("#evidencias_ifr")
            tinymce_body = iframe.locator("body#tinymce")
            tinymce_body.wait_for(state="visible", timeout=10000)
            tinymce_body.evaluate("(el, html) => { el.innerHTML = html; }", evidence_text)

            # Evidência commit SHA (URL completa ou fallback para SHA)
            commit_val = commit_metadata.get("url") or commit_metadata.get("sha", "sem_sha")
            self._log(f"Preenchendo Commit SHA/URL: '{commit_val}'...")
            page.locator("#evidencia_commit_sha").fill(commit_val)

            # Evidencia Anexo removido conforme solicitado

            # Status já definido anteriormente no início do fluxo de edição

            # Salvar Alterações
            page.keyboard.press("Escape")
            page.evaluate("() => { if (typeof $ !== 'undefined') { $('.my_select2, select').select2('close'); } }")
            page.wait_for_timeout(200)

            self._log("Salvando alterações finais da homologação...")
            save_btn = page.locator("button[type='submit'], input[type='submit']").first
            save_btn.click()

            self._log("Aguardando finalização do processo no Munka...")
            try:
                page.wait_for_url("**/tarefamodelview/list/**", timeout=15000)
            except Exception:
                try:
                    page.wait_for_url("**/", timeout=5000)
                except Exception:
                    page.wait_for_load_state("networkidle")

            browser.close()
            self._log("Fluxo completo finalizado com sucesso!")
            return task_data.get("titulo", "")
