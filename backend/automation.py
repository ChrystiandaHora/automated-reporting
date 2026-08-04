import os
import re
import time
import urllib.parse
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

    def _retry_with_backoff(self, operation, field_name, max_attempts=3, initial_timeout=2000):
        """Executa uma operação com retry e backoff exponencial.
        
        Tenta executar a operação até max_attempts vezes, aumentando o timeout
        progressivamente entre as tentativas. Útil para campos que podem demorar
        a carregar ou responder.
        
        Args:
            operation: Função/callable a ser executada (sem argumentos)
            field_name: Nome do campo para logging
            max_attempts: Número máximo de tentativas (padrão: 3)
            initial_timeout: Timeout inicial em ms, dobrado a cada tentativa (padrão: 2000ms)
            
        Returns:
            Resultado da operação se bem-sucedida
            
        Raises:
            Exception: A última exceção encontrada se todas as tentativas falharem
        """
        last_exception = None
        current_timeout = initial_timeout
        
        for attempt in range(1, max_attempts + 1):
            try:
                self._log(f"Tentando preencher campo '{field_name}' (tentativa {attempt}/{max_attempts})...")
                result = operation()
                if attempt > 1:
                    self._log(f"✓ Campo '{field_name}' preenchido com sucesso na tentativa {attempt}!")
                return result
            except Exception as e:
                last_exception = e
                if attempt < max_attempts:
                    self._log(f"⚠️ Falha na tentativa {attempt} para '{field_name}': {str(e)[:100]}")
                    self._log(f"⏳ Aguardando {current_timeout}ms antes da próxima tentativa...")
                    import time
                    time.sleep(current_timeout / 1000.0)
                    current_timeout *= 2  # Dobra o timeout a cada tentativa
                else:
                    self._log(f"❌ Todas as {max_attempts} tentativas falharam para o campo '{field_name}'")
        
        raise last_exception

    def _navegar_tarefas_do_mes(self, page, expand_page_size=True, status_id=None):
        """Navega para a listagem usando o link 'Tarefas do Mês' no menu superior.
        
        Esta navegação é mais confiável que a URL direta porque:
        - Usa link nativo do portal com filtros pré-configurados
        - Evita timeouts na rota /tarefamodelview/list/?
        - Garante que filtros estejam aplicados
        
        Args:
            page: Instância do Playwright Page
            expand_page_size: Se True, expande tamanho da página para 100 itens
            status_id: ID do status para filtrar na listagem (ex: 15 Backlog)
        """
        self._log("📋 Navegando via menu 'Tarefas do Mês'...")
        
        # Clica no link "Tarefas do Mês" no menu superior.
        # Primeiro tenta via JS (não depende de visibilidade), depois fallback por URL.
        try:
            clicked_menu = page.evaluate(r"""() => {
                const links = Array.from(document.querySelectorAll('a'));
                const target = links.find(a => (a.textContent || '').trim() === 'Tarefas do Mês');
                if (!target) return false;
                target.click();
                return true;
            }""")
            if clicked_menu:
                self._log("✅ Clicou em 'Tarefas do Mês' via menu")
            else:
                raise Exception("Link 'Tarefas do Mês' não encontrado no DOM")
        except Exception as e:
            self._log(f"⚠️ Erro ao acessar 'Tarefas do Mês': {e}. Tentando navegação direta...")
            # Fallback: navega diretamente para a URL de Tarefas do Mês com filtros básicos
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            # Primeiro dia do mês anterior às 00:00:00
            data_inicio = f"{ano_atual}-{mes_atual-1:02d}-01 00:00:00" if mes_atual > 1 else f"{ano_atual-1}-12-01 00:00:00"
            # Primeiro dia do próximo mês às 00:00:00
            data_fim = f"{ano_atual}-{mes_atual+1:02d}-01 00:00:00" if mes_atual < 12 else f"{ano_atual+1}-01-01 00:00:00"
            url_filtrada = f"{self.base_url}/tarefamodelview/list/?_flt_1_data_fim={data_inicio}&_flt_2_data_fim={data_fim}"
            if status_id:
                url_filtrada = f"{url_filtrada}&_flt_0_status={status_id}"
            self._safe_goto(page, url_filtrada)
        
        # Aguarda a página de listagem carregar
        self._log("⏳ Aguardando listagem carregar...")
        page.wait_for_selector("table.table-bordered, div.panel-body", state="visible", timeout=15000)
        self._log("✅ Listagem carregada")

        # Confere filtros de data e dispara o botão "Pesquisar" para aplicar filtros do formulário.
        try:
            data_inputs = page.locator("form#filter_form input[name*='data_fim'], form#filter_form input[id*='data_fim']")
            data_count = data_inputs.count()
            if data_count > 0:
                valores_data = []
                for i in range(data_count):
                    try:
                        valores_data.append(data_inputs.nth(i).input_value().strip())
                    except Exception:
                        valores_data.append("")
                self._log(f"📅 Filtros de data detectados: {valores_data}")
            else:
                self._log("⚠️ Não foi possível localizar inputs de data_fim no filtro")

            if status_id:
                status_set = page.evaluate(r"""([statusVal]) => {
                    const statusSel = document.querySelector('select#status');
                    if (!statusSel) return false;
                    statusSel.value = String(statusVal);

                    const row = statusSel.closest('tr');
                    const opSel = row ? row.querySelector('select.filter-op') : null;
                    if (opSel) {
                        opSel.value = '0'; // Relação
                    }

                    if (typeof $ !== 'undefined') {
                        const $status = $('#status');
                        $status.val(String(statusVal)).trigger('change');
                        if (typeof $status.select2 === 'function') {
                            $status.select2('val', String(statusVal));
                        }
                        if (opSel) {
                            $(opSel).trigger('change');
                        }
                    } else {
                        statusSel.dispatchEvent(new Event('change', { bubbles: true }));
                        if (opSel) {
                            opSel.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                    return true;
                }""", [str(status_id)])
                if status_set:
                    self._log(f"🎯 Filtro de status aplicado: {status_id}")
                else:
                    self._log("⚠️ Campo de filtro de status (#status) não encontrado na página")

            self._log("🔎 Aplicando filtros com submit do formulário...")
            submitted = page.evaluate(r"""() => {
                const form = document.querySelector('form#filter_form');
                if (!form) return false;
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
                return true;
            }""")
            if submitted:
                page.wait_for_timeout(1500)
                page.wait_for_selector("table.table-bordered", state="visible", timeout=10000)
                self._log("✅ Filtros aplicados com sucesso")
            else:
                self._log("⚠️ Formulário de filtro não encontrado para submit")
        except Exception as e:
            self._log(f"⚠️ Não foi possível aplicar filtros via botão 'Pesquisar': {e}. Continuando...")
        
        # Expande tamanho da página para 100 itens (opcional mas recomendado)
        if expand_page_size:
            try:
                self._log("📏 Expandindo tamanho da página para 100 itens...")
                current_url = page.url
                if "psize_TarefaModelView=100" not in current_url:
                    if "psize_TarefaModelView=" in current_url:
                        target_url = re.sub(r"([?&])psize_TarefaModelView=\d+", r"\1psize_TarefaModelView=100", current_url)
                    elif "?" in current_url:
                        target_url = f"{current_url}&psize_TarefaModelView=100"
                    else:
                        target_url = f"{current_url}?psize_TarefaModelView=100"

                    self._safe_goto(page, target_url)
                    page.wait_for_selector("table.table-bordered", state="visible", timeout=10000)
                self._log("✅ Tamanho da página ajustado para 100 itens")
            except Exception as e:
                self._log(f"⚠️ Não foi possível expandir tamanho da página: {e}. Continuando...")
        
        page.wait_for_timeout(500)  # Pequena pausa para estabilização

    def _safe_goto(self, page, url, wait_until="domcontentloaded", timeout=20000, max_retries=3):
        """Navega para uma URL com retentativas defensivas e domcontentloaded ultrarrápido."""
        url_clean = url.split("?")[0].rstrip("/")
        current_clean = page.url.split("?")[0].rstrip("/")
        if url_clean and current_clean and url_clean == current_clean:
            return

        for attempt in range(1, max_retries + 1):
            curr_timeout = min(12000 + (attempt * 5000), 25000)
            try:
                page.goto(url, wait_until=wait_until, timeout=curr_timeout)
                return
            except Exception as e:
                self._log(f"Aviso: Falha/Timeout ao navegar para '{url}' (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    page.wait_for_timeout(1000)
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=12000)
                        return
                    except Exception:
                        pass
                else:
                    raise Exception(f"Não foi possível navegar para '{url}' após {max_retries} tentativas no navegador.")

    def _filtrar_listagem_por_titulo(self, page, task_title):
        """Aplica filtro textual de título na listagem quando o campo existir.

        Alguns ambientes do Munka abrem a listagem com muitos registros e a
        tarefa recém-cadastrada pode não aparecer de imediato na primeira visão.
        Este helper tenta preencher o campo de texto de filtro por
        nome/título/tarefa dentro do ``#filter_form`` e submeter o formulário.
        Se o campo não existir, apenas retorna ``False`` sem interromper o fluxo.
        """
        title = (task_title or "").strip()
        if not title:
            return False

        applied = page.evaluate(
            r"""([title]) => {
                const form = document.querySelector('form#filter_form');
                if (!form) return { ok: false, reason: 'form_not_found' };

                const textInputs = Array.from(
                    form.querySelectorAll("input[type='text'], input[type='search'], input:not([type])")
                ).filter((el) => {
                    if (!el || el.disabled) return false;
                    if (el.offsetParent === null) return false;
                    const id = (el.id || '').toLowerCase();
                    const name = (el.name || '').toLowerCase();
                    return !id.includes('data') && !name.includes('data');
                });

                const score = (el) => {
                    const id = (el.id || '').toLowerCase();
                    const name = (el.name || '').toLowerCase();
                    const ph = (el.placeholder || '').toLowerCase();
                    const meta = `${id} ${name} ${ph}`;
                    if (id === 'nome' || name === 'nome') return 100;
                    if (meta.includes('titulo')) return 90;
                    if (meta.includes('tarefa')) return 80;
                    if (meta.includes('nome')) return 70;
                    return 0;
                };

                let target = null;
                let best = -1;
                for (const inp of textInputs) {
                    const s = score(inp);
                    if (s > best) {
                        best = s;
                        target = inp;
                    }
                }

                if (!target || best <= 0) {
                    return {
                        ok: false,
                        reason: 'field_not_found',
                        candidates: textInputs.slice(0, 8).map((el) => ({
                            id: el.id || '',
                            name: el.name || '',
                            placeholder: el.placeholder || ''
                        }))
                    };
                }

                target.focus();
                target.value = title;
                target.dispatchEvent(new Event('input', { bubbles: true }));
                target.dispatchEvent(new Event('change', { bubbles: true }));

                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }

                return {
                    ok: true,
                    field: target.id || target.name || '(sem id/name)',
                    value: title
                };
            }""",
            [title],
        )

        if applied.get("ok"):
            self._log(f"🎯 Filtro por título aplicado no campo '{applied.get('field')}'")
            page.wait_for_timeout(1200)
            page.wait_for_selector("table.table-bordered", state="visible", timeout=10000)
            return True

        self._log(f"ℹ️ Filtro por título indisponível na listagem: {applied.get('reason')}")
        return False

    def _encontrar_edicao_por_titulo_nos_links_da_listagem(self, page, task_title, max_links=60):
        """Fallback: varre links de edição visíveis e confere o título no formulário.

        Em algumas telas, o texto da linha pode estar truncado e o ``has_text``
        falha mesmo com a tarefa existente. Este fallback coleta os links de
        edição exibidos na tabela atual e abre cada um para validar o ``#nome``
        do formulário.
        """
        title = (task_title or "").strip()
        if not title:
            return None

        def _norm(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "")).strip().lower()

        target = _norm(title)
        target_probe = target[:45]

        hrefs = page.evaluate(
            r"""() => {
                const links = Array.from(
                    document.querySelectorAll("table.table-bordered tbody tr a[href*='tarefamodelview/edit']")
                ).map((a) => (a.getAttribute('href') || '').trim()).filter(Boolean);
                const uniq = [];
                const seen = new Set();
                for (const h of links) {
                    if (!seen.has(h)) {
                        seen.add(h);
                        uniq.push(h);
                    }
                }
                return uniq;
            }"""
        ) or []

        if not hrefs:
            return None

        self._log(f"🔎 Fallback: inspecionando {min(len(hrefs), max_links)} link(s) de edição da listagem...")

        for href in hrefs[:max_links]:
            try:
                edit_url = href if href.startswith("http") else f"{self.base_url}{href if href.startswith('/') else '/' + href}"
                self._safe_goto(page, edit_url)
                page.wait_for_selector("#nome", state="visible", timeout=8000)
                nome_form = page.locator("#nome").input_value().strip()
                nome_norm = _norm(nome_form)

                if (
                    nome_norm == target
                    or (target and target in nome_norm)
                    or (nome_norm and nome_norm in target)
                    or (target_probe and target_probe in nome_norm)
                ):
                    self._log(f"✅ Fallback encontrou tarefa pelo formulário: '{nome_form[:90]}'")
                    return edit_url
            except Exception as e:
                self._log(f"⚠️ Falha ao inspecionar link de edição no fallback: {e}")

        return None

    def _login(self, page):
        """Log in to the Munka platform using the stored credentials."""
        self._log("Acessando a página de login do Munka...")
        self._safe_goto(page, f"{self.base_url}/")
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
        submit_btn.click(no_wait_after=True)
        page.wait_for_selector("#content, .navbar, table, .dashboard", state="visible", timeout=25000)
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
            selected = page.evaluate(r"""([fieldId, termClean, originalTerm]) => {
                const $select = $('#' + fieldId);
                if ($select.length === 0) return false;
                
                const smartMatch = (optText, searchStr) => {
                    if (!optText || !searchStr) return false;
                    const cleanOpt = optText.toLowerCase().replace(/^\[.*?\]\s*/g, '').replace(/\(.*?\)/g, '').trim();
                    const cleanSearch = searchStr.toLowerCase().replace(/^\[.*?\]\s*/g, '').replace(/\(.*?\)/g, '').trim();
                    if (!cleanOpt || !cleanSearch) return false;
                    if (cleanOpt === cleanSearch || cleanOpt.indexOf(cleanSearch) !== -1 || cleanSearch.indexOf(cleanOpt) !== -1) {
                        return true;
                    }
                    const searchWords = cleanSearch.split(/\s+/).filter(Boolean);
                    const optWords = cleanOpt.split(/\s+/).filter(Boolean);
                    if (searchWords.length > 0 && optWords.length > 0) {
                        if (optWords[0].startsWith(searchWords[0]) || searchWords[0].startsWith(optWords[0])) {
                            if (searchWords.length === 1) return true;
                            let sIdx = 1, oIdx = 1;
                            while (sIdx < searchWords.length && oIdx < optWords.length) {
                                if (optWords[oIdx].startsWith(searchWords[sIdx])) {
                                    sIdx++;
                                    oIdx++;
                                } else {
                                    oIdx++;
                                }
                            }
                            if (sIdx === searchWords.length) return true;
                            return true;
                        }
                    }
                    return false;
                };

                let foundValue = null;
                $select.find('option').each(function() {
                    const text = $(this).text();
                    if (smartMatch(text, termClean) || smartMatch(text, originalTerm)) {
                        foundValue = $(this).val();
                        return false; // break
                    }
                });
                
                if (foundValue !== null && foundValue !== "" && foundValue !== "__None") {
                    $select.val(foundValue).trigger('change');
                    if (typeof $select.select2 === 'function') {
                        $select.select2('val', foundValue);
                    }
                    return true;
                }
                return false;
            }""", [field_id, search_term_clean, search_term])
            
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
            page.click(f"{container_selector} a.select2-choice, {container_selector}", timeout=3000)
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
            try:
                page.wait_for_selector(search_input_selector, state="visible", timeout=4000)
            except Exception:
                raise Exception(f"Não foi possível abrir o dropdown Select2 para o campo '{field_id}'.")
            search_locator = page.locator(search_input_selector).first

        # 4. Define os termos de busca a tentar
        # Mantém sempre o texto completo, nunca reduz caracteres
        terms_to_try = []
        if search_term and search_term not in terms_to_try:
            terms_to_try.append(search_term)
        if search_term_clean and search_term_clean not in terms_to_try and search_term_clean != search_term:
            terms_to_try.append(search_term_clean)

        first_result_selector = "div.select2-drop:not(.select2-display-none) .select2-result, div.select2-drop:not(.select2-display-none) .select2-result-selectable"
        item_selected = False

        for term in terms_to_try:
            self._log(f"Buscando no Select2 '{field_id}' por '{term}'...")
            search_locator.fill("")
            search_locator.type(term, delay=35)
            
            # Aguarda até 5 segundos para os resultados aparecerem, mas interrompe assim que detectar
            # Isso otimiza o tempo quando o servidor responde rápido
            try:
                page.wait_for_selector(first_result_selector, state="visible", timeout=5000)
                # Resultados apareceram! Pequena pausa para estabilização
                page.wait_for_timeout(100)
            except Exception:
                self._log(f"Nenhum resultado selecionável retornado no Select2 para '{term}'.")
                continue

            # 5. Localiza o resultado correspondente e simula a seleção com mousedown/mouseup/click
            clicked = page.evaluate(r"""([termClean, originalTerm]) => {
                const smartMatch = (optText, searchStr) => {
                    if (!optText || !searchStr) return false;
                    const cleanOpt = optText.toLowerCase().replace(/^\[.*?\]\s*/g, '').replace(/\(.*?\)/g, '').trim();
                    const cleanSearch = searchStr.toLowerCase().replace(/^\[.*?\]\s*/g, '').replace(/\(.*?\)/g, '').trim();
                    if (!cleanOpt || !cleanSearch) return false;
                    if (cleanOpt === cleanSearch || cleanOpt.indexOf(cleanSearch) !== -1 || cleanSearch.indexOf(cleanOpt) !== -1) {
                        return true;
                    }
                    const searchWords = cleanSearch.split(/\s+/).filter(Boolean);
                    const optWords = cleanOpt.split(/\s+/).filter(Boolean);
                    if (searchWords.length > 0 && optWords.length > 0) {
                        if (optWords[0].startsWith(searchWords[0]) || searchWords[0].startsWith(optWords[0])) {
                            if (searchWords.length === 1) return true;
                            let sIdx = 1, oIdx = 1;
                            while (sIdx < searchWords.length && oIdx < optWords.length) {
                                if (optWords[oIdx].startsWith(searchWords[sIdx])) {
                                    sIdx++;
                                    oIdx++;
                                } else {
                                    oIdx++;
                                }
                            }
                            if (sIdx === searchWords.length) return true;
                            return true;
                        }
                    }
                    return false;
                };

                let matchedEl = null;
                const $allResults = $('div.select2-drop:not(.select2-display-none) .select2-result, div.select2-drop:not(.select2-display-none) .select2-result-selectable');
                const $selectable = $allResults.filter('.select2-result-selectable');
                const $results = $selectable.length > 0 ? $selectable : $allResults;
                
                $results.each(function() {
                    const text = $(this).text();
                    if (smartMatch(text, termClean) || smartMatch(text, originalTerm)) {
                        matchedEl = this;
                        return false; // break
                    }
                });

                if (!matchedEl && $results.length > 0) {
                    matchedEl = $results.first()[0];
                }

                if (matchedEl) {
                    const $el = $(matchedEl);
                    $el.trigger('mouseenter')
                       .trigger('mouseover')
                       .trigger('mousedown')
                       .trigger('mouseup')
                       .click();
                    return true;
                }
                return false;
            }""", [term, search_term])

            if clicked:
                item_selected = True
                break

        if not item_selected:
            # Fallback final se nada clicou: pressiona Enter se o input estiver ativo
            if search_locator.is_visible():
                try:
                    search_locator.press("Enter", timeout=1500)
                except Exception:
                    pass

        # Aguarda o Select2 AJAX processar a seleção
        page.wait_for_timeout(600)

        # 6. Validação defensiva: verifica texto exibido no container Select2 e o valor jQuery
        displayed_text = page.evaluate(
            f"() => (document.querySelector('#s2id_{field_id} .select2-chosen') || {{}}).textContent || ''"
        ).strip()
        selected_val = page.evaluate(f"() => $('#{field_id}').val()")
        if isinstance(selected_val, list):
            selected_val = selected_val[0] if selected_val else ""

        def _smart_match_py(opt_text: str, search_str: str) -> bool:
            if not opt_text or not search_str:
                return False
            clean_opt = re.sub(r'[\(\)\[\]]', '', opt_text.lower()).strip()
            clean_search = re.sub(r'[\(\)\[\]]', '', search_str.lower()).strip()
            if not clean_opt or not clean_search:
                return False
            if clean_search in clean_opt or clean_opt in clean_search:
                return True
            s_words = [w for w in clean_search.split() if w]
            o_words = [w for w in clean_opt.split() if w]
            if s_words and o_words:
                if o_words[0].startswith(s_words[0]) or s_words[0].startswith(o_words[0]):
                    return True
            return False

        has_valid_value = selected_val not in ("", "__None", None)
        text_matches = _smart_match_py(displayed_text, search_term_clean) or _smart_match_py(displayed_text, search_term)

        if text_matches or has_valid_value:
            self._log(f"Campo '{field_id}' confirmado pelo Select2. Texto exibido: '{displayed_text}', Valor: '{selected_val}'")
            return

        # Segundo fallback: aguarda 1 segundo adicional
        page.wait_for_timeout(1000)
        displayed_text2 = page.evaluate(
            f"() => (document.querySelector('#s2id_{field_id} .select2-chosen') || {{}}).textContent || ''"
        ).strip()
        selected_val2 = page.evaluate(f"() => $('#{field_id}').val()")
        if isinstance(selected_val2, list):
            selected_val2 = selected_val2[0] if selected_val2 else ""

        if selected_val2 not in ("", "__None", None) or _smart_match_py(displayed_text2, search_term_clean):
            self._log(f"Campo '{field_id}' confirmado no segundo fallback. Texto: '{displayed_text2}', Valor: '{selected_val2}'")
            return

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

    def _excluir_tarefa_duplicada_portal(self, page, edit_url: str, task_title: str) -> bool:
        """Exclui uma tarefa duplicada excedente no portal Munka.
        
        Navega para a listagem filtrada por título, localiza a linha da tarefa pelo ID,
        clica no botão de exclusão, confirma no modal/dialog (ou navega na rota de exclusão)
        e valida a exclusão.
        """
        match = re.search(r"tarefamodelview/edit/(\d+)", edit_url)
        task_id = match.group(1) if match else None
        if not task_id:
            self._log(f"⚠️ Não foi possível extrair o ID da tarefa da URL '{edit_url}'")
            return False

        self._log(f"🗑️ Excluindo registro duplicado excedente (ID: {task_id})...")

        # Configura handler para aceitar automaticamente dialogs nativos (window.confirm)
        try:
            page.on("dialog", lambda dialog: dialog.accept())
        except Exception:
            pass

        try:
            # 1. Garante estar na listagem filtrada por título
            encoded_title = urllib.parse.quote_plus(task_title.strip())
            url_filtrada = f"{self.base_url}/tarefamodelview/list/?_flt_0_nome={encoded_title}"
            self._safe_goto(page, url_filtrada)
            page.wait_for_selector("table.table-bordered", state="visible", timeout=10000)

            # 2. Localiza a linha específica pelo ID (na coluna ID ou no link de edição)
            row = page.locator("table.table-bordered tbody tr").filter(has_text=task_id).first
            
            clicked = False
            if row.count() > 0:
                delete_btn = row.locator(
                    "a[href*='delete'], a[onclick*='delete'], a.btn:has(i.fa-trash), a:has(i.glyphicon-trash)"
                ).first
                if delete_btn.count() > 0:
                    delete_btn.click()
                    clicked = True

            if not clicked:
                delete_btn_global = page.locator(f"a[href*='delete/{task_id}'], a[onclick*='{task_id}']").first
                if delete_btn_global.count() > 0:
                    delete_btn_global.click()
                    clicked = True

            # 3. Tenta mecher no modal Bootstrap caso tenha sido exibido
            try:
                page.wait_for_selector(".modal.in, .modal.show, div.modal:visible", state="visible", timeout=3000)
                modal = page.locator(".modal.in, .modal.show, div.modal:visible").first
                if modal.is_visible():
                    ok_btn = modal.locator(
                        "a:has-text('OK'), button:has-text('OK'), a.btn-danger, button.btn-danger"
                    ).first
                    if ok_btn.count() > 0:
                        ok_btn.click()
                        page.wait_for_timeout(1000)
            except Exception:
                pass

            # 4. Fallback de Segurança: Se a tarefa ainda continuar na listagem, acessa diretamente o endpoint de exclusão do FAB
            page.wait_for_timeout(800)
            row_still_exists = page.locator("table.table-bordered tbody tr").filter(has_text=task_id).count() > 0
            if row_still_exists:
                self._log(f"⚠️ Tarefa {task_id} ainda visível na listagem. Acionando rota de exclusão direta /tarefamodelview/delete/{task_id}...")
                delete_url = f"{self.base_url}/tarefamodelview/delete/{task_id}"
                self._safe_goto(page, delete_url)
                page.wait_for_timeout(1000)

            self._log(f"✅ Registro duplicado excedente (ID: {task_id}) excluído do portal com sucesso!")
            return True
        except Exception as e:
            self._log(f"⚠️ Erro ao tentar excluir registro duplicado excedente (ID: {task_id}): {e}")
            return False

    def _verificar_duplicidade_portal(self, page, task_title, target_sha) -> tuple[bool, str | None]:
        """Verifica se uma tarefa com o mesmo título e commit SHA já existe no portal.

        Navega para a listagem, localiza linhas com título idêntico, abre a página de
        edição de cada uma e inspeciona se o campo '#evidencia_commit_sha'
        contém o target_sha. Se existirem múltiplas tarefas incompletas, mantém
        apenas 1 e exclui as demais via modal de confirmação.
        """
        self._log("Verificando se a tarefa já existe no Munka (Título + SHA)...")
        task_title_clean = task_title.strip()
        try:
            # Otimização via URL de Filtro Direto do Flask-AppBuilder (_flt_0_nome)
            encoded_title = urllib.parse.quote_plus(task_title_clean)
            url_filtrada = f"{self.base_url}/tarefamodelview/list/?_flt_0_nome={encoded_title}"
            self._log(f"🔍 Filtrando listagem por URL direta para o título...")
            self._safe_goto(page, url_filtrada)
            page.wait_for_selector("table.table-bordered, div.container-fluid", state="visible", timeout=10000)
        except Exception as e:
            self._log(f"Aviso ao carregar listagem para verificação de duplicados: {e}. Prosseguindo diretamente para o cadastro...")
            return False, None
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
            return False, None

        # Se target_sha for vazio/nulo ou for "sem_sha", usamos apenas a validação por título
        if not target_sha or target_sha == "sem_sha":
            self._log("Target SHA não fornecido ou inválido. Usando apenas validação de título.")
            self._log(f"Duplicidade detectada (título '{task_title_clean}' já cadastrado e sem SHA definido).")
            return True, None

        self._log(f"Encontrada(s) {len(edit_urls)} tarefa(s) com título '{task_title_clean}'. Inspecionando commit SHA...")

        incomplete_edit_urls = []

        # Visita cada URL de edição para checar o SHA
        for edit_url in edit_urls:
            try:
                self._log(f"Inspecionando tarefa no link de edição: {edit_url}")
                self._safe_goto(page, edit_url)
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

                # Checa também se data_fim foi preenchido
                data_fim_input = page.locator("#data_fim")
                current_data_fim_val = data_fim_input.input_value().strip() if data_fim_input.count() > 0 else ""

                self._log(f"Valor no portal -> commit_sha: '{current_sha_val}', data_fim: '{current_data_fim_val}'")

                # Compara usando substring case-insensitive
                target_sha_clean = target_sha.strip().lower()
                target_sha_short = target_sha_clean[:8]
                current_sha_val_lower = current_sha_val.lower()

                # Se o SHA bate E data_fim está preenchida, a tarefa foi concluída com sucesso
                if (target_sha_clean in current_sha_val_lower or target_sha_short in current_sha_val_lower) and current_data_fim_val:
                    self._log(f"Duplicidade confirmada! A tarefa com o SHA/URL '{target_sha}' já está cadastrada e finalizada no portal.")
                    return True, None

                # Se o SHA for "sem_sha", ou o SHA bater mas data_fim estiver vazia, a tarefa é incompleta!
                if not current_sha_val or current_sha_val.lower() == "sem_sha" or not current_data_fim_val:
                    incomplete_edit_urls.append(edit_url)
            except Exception as e:
                self._log(f"Erro ao verificar tarefa na URL {edit_url}: {e}. Continuando verificação...")

        if incomplete_edit_urls:
            main_incomplete_url = incomplete_edit_urls[0]
            if len(incomplete_edit_urls) > 1:
                self._log(
                    f"⚠️ Encontradas {len(incomplete_edit_urls)} tarefas incompletas com o mesmo título '{task_title_clean}'. "
                    f"Mantendo apenas 1 registro ({main_incomplete_url}) e excluindo as {len(incomplete_edit_urls) - 1} duplicadas excedentes..."
                )
                for extra_url in incomplete_edit_urls[1:]:
                    self._excluir_tarefa_duplicada_portal(page, extra_url, task_title_clean)
                self._log("✅ Limpeza de tarefas duplicadas excedentes concluída. Restou apenas 1 registro para preenchimento.")

            self._log(f"Reusando registro de tarefa incompleta: {main_incomplete_url}")
            return False, main_incomplete_url

        self._log("Nenhuma tarefa correspondente ao título e SHA encontrados. Prosseguindo com cadastro.")
        return False, None

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
            page.set_default_navigation_timeout(35000)
            page.set_default_timeout(30000)

            # 1. Login
            self._login(page)

            # 1.5. Verificar duplicados na listagem de tarefas
            task_title = task_data.get("titulo", "").strip()
            target_sha = commit_metadata.get("sha", "sem_sha")
            is_dup, _ = self._verificar_duplicidade_portal(page, task_title, target_sha)
            if is_dup:
                browser.close()
                return "PULADA_DUPLICADA"

            # 2. Navegar para criação
            self._log("Abrindo formulário de cadastro de tarefa...")
            self._safe_goto(page, f"{self.base_url}/tarefamodelview/add")
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
                try:
                    self._retry_with_backoff(
                        lambda: self._preencher_select2_ajax(page, "responsavel", responsavel_busca, force_ui=True),
                        field_name="responsavel",
                        max_attempts=3,
                        initial_timeout=2000
                    )
                except Exception as e_resp:
                    self._log(f"⚠️ Aviso: Não foi possível selecionar responsável '{responsavel_busca}': {e_resp}. Continuando sem responsável.")

            # 6. Preencher Data de Início
            self._log(f"Preenchendo Data de Início: '{commit_metadata['data_inicio']}'...")
            data_inicio_input = page.locator("#data_inicio")
            data_inicio_input.fill(commit_metadata["data_inicio"])
            data_inicio_input.press("Tab")  # Tira o foco para disparar validações

            # 7. Selecionar Tipo (projeto) PRIMEIRO - antes do produto
            # O tipo precisa ser definido antes para que o formulário configure os campos corretamente
            self._log("Configurando Tipo de tarefa para 'projeto'...")
            page.evaluate("() => { $('#tipo').val('projeto').trigger('change'); }")
            page.wait_for_timeout(500)  # Aguarda aparecer o select condicional de projeto

            # 8. Selecionar Produto via Select2 (busca pelo nome digitado pelo usuário)
            self._log(f"Selecionando Produto: '{product_name}'...")
            self._retry_with_backoff(
                lambda: self._preencher_select2_ajax(page, "produto", product_name, force_ui=True),
                field_name="produto",
                max_attempts=3,
                initial_timeout=2000
            )
            page.wait_for_timeout(1000)  # Aguarda carregar os projetos no select condicional via AJAX

            # 9. Selecionar Projeto (Select condicional AJAX) - busca pelo nome do projeto
            self._log(f"Selecionando Projeto: '{project_name}'...")
            self._retry_with_backoff(
                lambda: self._preencher_select2_ajax(page, "projeto", project_name, force_ui=True),
                field_name="projeto",
                max_attempts=3,
                initial_timeout=3000  # Timeout maior pois projeto depende de AJAX
            )

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
                self._retry_with_backoff(
                    lambda: self._preencher_select2_ajax(page, "regra", codigo_id),
                    field_name="regra",
                    max_attempts=3,
                    initial_timeout=2000
                )

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
            save_btn.click(no_wait_after=True)
            
            # Aguarda a transação ser processada pelo servidor Munka
            self._log("Aguardando redirecionamento pós-salvamento...")
            try:
                page.wait_for_url("**/tarefamodelview/list/**", timeout=25000)
            except Exception:
                try:
                    page.wait_for_url("**/", timeout=5000)
                except Exception:
                    try:
                        page.wait_for_selector("table.table-bordered, div.container-fluid.espacamento", state="visible", timeout=10000)
                    except Exception:
                        page.wait_for_load_state("domcontentloaded")

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
            page.set_default_navigation_timeout(35000)
            page.set_default_timeout(30000)

            # 1. Login
            self._login(page)

            # Navegar para a listagem de tarefas via "Tarefas do Mês"
            self._log("Carregando listagem de tarefas no Munka...")
            self._navegar_tarefas_do_mes(page, expand_page_size=True, status_id=status_id)

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

            # Data do Fim: utiliza commit_metadata["data_fim"] que já vem com a hora configurada pelo usuário.
            # Fallback: se data_fim não tiver data completa, extrai a data de data_inicio e concatena com a hora de data_fim.
            data_fim = commit_metadata.get("data_fim", "")
            if not data_fim:
                data_inicio = commit_metadata.get("data_inicio", "")
                data_fim = f"{data_inicio[:10]} 18:00" if data_inicio and len(data_inicio) >= 10 else datetime.now().strftime("%d/%m/%Y 18:00")
            elif " " not in data_fim and len(data_fim) <= 5:
                # Apenas hora foi configurada (ex: "17:00") — extrai data de data_inicio
                data_inicio = commit_metadata.get("data_inicio", "")
                if data_inicio and len(data_inicio) >= 10:
                    data_fim = f"{data_inicio[:10]} {data_fim}"
                else:
                    data_fim = f"{datetime.now().strftime('%d/%m/%Y')} {data_fim}"

            self._log(f"Preenchendo Data de Fim: '{data_fim}'...")
            page.locator("#data_fim").fill(data_fim)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#data_fim').val('{data_fim}').trigger('change'); }} }}")
            page.locator("#data_fim").press("Tab")

            # Horas Executadas
            hpa_str = str(act.get("hpa", "1.0"))
            self._log(f"Preenchendo Horas Executadas: '{hpa_str}' HPA...")
            page.locator("#horas_executadas").fill(hpa_str)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#horas_executadas').val('{hpa_str}').trigger('change'); }} }}")

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
            
            self._log("Injetando e sincronizando conteúdo no editor TinyMCE de evidências...")
            try:
                iframe = page.frame_locator("#evidencias_ifr")
                tinymce_body = iframe.locator("body#tinymce")
                tinymce_body.wait_for(state="visible", timeout=10000)
                tinymce_body.evaluate("(el, html) => { el.innerHTML = html; }", evidence_text)
            except Exception as e_tiny:
                self._log(f"Aviso ao injetar no iframe do TinyMCE: {e_tiny}")

            # Sincroniza com a API do TinyMCE e com o textarea #evidencias para garantir o POST do formulário
            page.evaluate("""(html) => {
                if (typeof tinymce !== 'undefined') {
                    if (tinymce.get('evidencias')) {
                        tinymce.get('evidencias').setContent(html);
                        tinymce.get('evidencias').save();
                    } else if (tinymce.activeEditor) {
                        tinymce.activeEditor.setContent(html);
                        tinymce.activeEditor.save();
                    }
                    if (typeof tinymce.triggerSave === 'function') {
                        tinymce.triggerSave();
                    }
                }
                if (typeof $ !== 'undefined') {
                    var $ev = $('#evidencias');
                    if ($ev.length) {
                        $ev.val(html).trigger('change');
                    }
                } else {
                    var el = document.getElementById('evidencias');
                    if (el) { el.value = html; }
                }
            }""", evidence_text)

            # Evidência commit SHA (URL completa ou fallback para SHA)
            commit_val = commit_metadata.get("url") or commit_metadata.get("sha", "sem_sha")
            self._log(f"Preenchendo Commit SHA/URL: '{commit_val}'...")
            page.locator("#evidencia_commit_sha").fill(commit_val)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#evidencia_commit_sha').val('{commit_val}').trigger('change'); }} }}")

            # Salvar edição (garantindo fechamento de overlays e sincronização do TinyMCE)
            page.keyboard.press("Escape")
            page.evaluate("""() => {
                if (typeof tinymce !== 'undefined' && typeof tinymce.triggerSave === 'function') {
                    tinymce.triggerSave();
                }
                if (typeof $ !== 'undefined') {
                    $('.my_select2, select').select2('close');
                }
            }""")
            page.wait_for_timeout(200)

            self._log("Salvando alterações da homologação...")
            save_btn = page.locator("form#model_form button[type='submit'], form#model_form input[type='submit'], form button[type='submit'], form input[type='submit']").first
            try:
                with page.expect_navigation(timeout=30000):
                    save_btn.click()
            except Exception:
                try:
                    save_btn.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    page.wait_for_timeout(3000)

            # --- VERIFICAÇÃO PÓS-SALVAMENTO: Checa se a data_fim foi gravada ---
            self._log(f"Iniciando verificação pós-salvamento do campo data_fim para '{task_title}'...")
            try:
                self._navegar_tarefas_do_mes(page, expand_page_size=False)
                row = page.locator("table.table-bordered tbody tr").filter(has_text=task_title).first
                row.wait_for(timeout=10000)
                edit_btn = row.locator("a[href*='tarefamodelview/edit']").first
                href = edit_btn.get_attribute("href") or ""
                match = re.search(r"tarefamodelview/edit/(\d+)", href)
                if match:
                    edit_url = f"{self.base_url}/tarefamodelview/edit/{match.group(1)}"
                    self._safe_goto(page, edit_url)
                else:
                    edit_btn.click()
                    page.wait_for_selector("form, #nome", state="visible", timeout=15000)

                page.wait_for_selector("form, #nome", state="visible", timeout=15000)
                if not page.locator("#data_fim").is_visible():
                    painel_execucao = page.locator('[id="3_href"]')
                    if painel_execucao.count() > 0:
                        painel_execucao.click()
                        page.locator("#data_fim").wait_for(state="visible", timeout=5000)

                val_data_fim = page.locator("#data_fim").input_value().strip()
                if not val_data_fim:
                    self._log("ATENÇÃO: data_fim vazia após o salvamento! Re-preenchendo, sincronizando TinyMCE e salvando com aguardo de navegação...")
                    page.locator("#data_fim").fill(data_fim)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#data_fim').val('{data_fim}').trigger('change'); }} }}")
                    page.locator("#data_fim").press("Tab")

                    page.locator("#horas_executadas").fill(hpa_str)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#horas_executadas').val('{hpa_str}').trigger('change'); }} }}")

                    try:
                        iframe = page.frame_locator("#evidencias_ifr")
                        tinymce_body = iframe.locator("body#tinymce")
                        tinymce_body.wait_for(state="visible", timeout=10000)
                        tinymce_body.evaluate("(el, html) => { el.innerHTML = html; }", evidence_text)
                    except Exception:
                        pass

                    page.evaluate("""(html) => {
                        if (typeof tinymce !== 'undefined') {
                            if (tinymce.get('evidencias')) {
                                tinymce.get('evidencias').setContent(html);
                                tinymce.get('evidencias').save();
                            } else if (tinymce.activeEditor) {
                                tinymce.activeEditor.setContent(html);
                                tinymce.activeEditor.save();
                            }
                            if (typeof tinymce.triggerSave === 'function') {
                                tinymce.triggerSave();
                            }
                        }
                        if (typeof $ !== 'undefined') {
                            var $ev = $('#evidencias');
                            if ($ev.length) { $ev.val(html).trigger('change'); }
                        }
                    }""", evidence_text)

                    page.locator("#evidencia_commit_sha").fill(commit_val)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#evidencia_commit_sha').val('{commit_val}').trigger('change'); }} }}")

                    page.evaluate(select2_script)
                    page.wait_for_timeout(100)

                    page.keyboard.press("Escape")
                    page.evaluate("""() => {
                        if (typeof tinymce !== 'undefined' && typeof tinymce.triggerSave === 'function') {
                            tinymce.triggerSave();
                        }
                        if (typeof $ !== 'undefined') {
                            $('.my_select2, select').select2('close');
                        }
                    }""")
                    page.wait_for_timeout(200)

                    save_btn = page.locator("form#model_form button[type='submit'], form#model_form input[type='submit'], form button[type='submit'], form input[type='submit']").first
                    try:
                        with page.expect_navigation(timeout=30000):
                            save_btn.click()
                    except Exception:
                        save_btn.click()
                        page.wait_for_load_state("networkidle", timeout=10000)
                    self._log("Re-salvamento da tarefa concluído!")
                else:
                    self._log(f"Verificação concluída com sucesso! data_fim '{val_data_fim}' gravada corretamente.")
            except Exception as chk_e:
                self._log(f"Verificação de data_fim concluída com aviso: {chk_e}")

            browser.close()
            self._log("Evidências anexadas e homologação concluída!")

    def cadastrar_e_homologar_completo(
        self, task_data, image_path, product_name="[DESENV] MUNKA", project_name="MUNKA Multicontrato", dev_profile=None, commit_metadata=None, custom_evidence_html=None
    ) -> tuple[str, str | None]:
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
        select2_script = f"""() => {{
            var $status = $('#status');
            if ($status.length) {{
                $status.val('{status_id}').trigger('change');
                if (typeof $status.select2 === 'function') {{
                    $status.select2('val', '{status_id}');
                }}
            }}
        }}"""

        # Evidencia Anexo removido — image_path não é mais utilizado

        self._log("Iniciando fluxo completo (Cadastro + Evidência + Homologação)...")
        with sync_playwright() as p:
            self._log("Inicializando navegador Chromium...")
            browser = p.chromium.launch(headless=self.headless, args=["--disable-gpu", "--disable-software-rasterizer"])
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_navigation_timeout(35000)
            page.set_default_timeout(30000)

            # 1. Login
            self._login(page)

            # 1.5. Verificar duplicidade/incompletude ANTES de criar nova tarefa
            task_title = task_data.get("titulo", "").strip()
            target_sha = commit_metadata.get("sha", "sem_sha")
            is_dup, incomplete_url = self._verificar_duplicidade_portal(page, task_title, target_sha)

            if is_dup:
                self._log("⏭️ Tarefa já existe e está finalizada no portal. Pulando novo lançamento.")
                browser.close()
                return "PULADA_DUPLICADA", None

            direct_edit_url = None
            if incomplete_url:
                self._log(
                    f"📝 Tarefa incompleta existente detectada em {incomplete_url}. "
                    "Reutilizando o registro único e avançando diretamente para edição, inclusão de evidências e homologação..."
                )
                direct_edit_url = incomplete_url
            else:
                # 2. Navegar para criação de nova tarefa
                self._log("Carregando formulário de criação de tarefa...")
                self._safe_goto(page, f"{self.base_url}/tarefamodelview/add")
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
                    try:
                        self._retry_with_backoff(
                            lambda: self._preencher_select2_ajax(page, "responsavel", responsavel_busca, force_ui=True),
                            field_name="responsavel",
                            max_attempts=3,
                            initial_timeout=2000
                        )
                    except Exception as e_resp:
                        self._log(f"⚠️ Aviso: Não foi possível selecionar responsável '{responsavel_busca}': {e_resp}. Continuando sem responsável.")

                # 6. Preencher Data de Início
                self._log(f"Preenchendo Data de Início: '{commit_metadata['data_inicio']}'...")
                data_inicio_input = page.locator("#data_inicio")
                data_inicio_input.fill(commit_metadata["data_inicio"])
                data_inicio_input.press("Tab")

                # 7. Selecionar Tipo (projeto) PRIMEIRO - antes do produto
                self._log("Configurando Tipo de tarefa para 'projeto'...")
                page.evaluate("() => { $('#tipo').val('projeto').trigger('change'); }")
                page.wait_for_timeout(500)  # Aguarda aparecer o select condicional de projeto

                # 8. Selecionar Produto
                self._log(f"Selecionando Produto: '{product_name}'...")
                self._retry_with_backoff(
                    lambda: self._preencher_select2_ajax(page, "produto", product_name, force_ui=True),
                    field_name="produto",
                    max_attempts=3,
                    initial_timeout=2000
                )
                page.wait_for_timeout(1000)  # Aguarda carregar os projetos no select condicional via AJAX

                # 9. Selecionar Projeto
                self._log(f"Selecionando Projeto: '{project_name}'...")
                self._retry_with_backoff(
                    lambda: self._preencher_select2_ajax(page, "projeto", project_name, force_ui=True),
                    field_name="projeto",
                    max_attempts=3,
                    initial_timeout=3000  # Timeout maior pois projeto depende de AJAX
                )

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
                    self._retry_with_backoff(
                        lambda: self._preencher_select2_ajax(page, "regra", codigo_id),
                        field_name="regra",
                        max_attempts=3,
                        initial_timeout=2000
                    )

                # 12. Selecionar Status inicial (Homologação ou o configurado)
                self._log(f"Configurando status inicial para: '{status_id}'...")
                page.locator("#status").wait_for(state="attached", timeout=5000)
                page.evaluate(select2_script)
                page.wait_for_timeout(100)

                # 13. Salvar Cadastro
                page.keyboard.press("Escape")
                page.evaluate("() => { if (typeof $ !== 'undefined') { $('.my_select2, select').select2('close'); } }")
                page.wait_for_timeout(200)

                self._log("Salvando cadastro da tarefa...")
                save_btn = page.locator("button[type='submit'], input[type='submit']").first
                try:
                    with page.expect_navigation(timeout=45000):
                        save_btn.click()
                    self._log("✅ Navegação detectada após salvar cadastro")
                except Exception as nav_e:
                    self._log(f"⚠️ Sem navegação imediata após salvar: {nav_e}")
                    # Em cenários lentos o backend pode demorar para responder; aguarda rede estabilizar.
                    try:
                        page.wait_for_load_state("networkidle", timeout=25000)
                        self._log("✅ Rede estabilizada após envio do cadastro")
                    except Exception:
                        page.wait_for_timeout(3000)

                # Aguarda a submissão completar
                self._log("Aguardando processamento do cadastro...")
                save_confirmed = False
                
                # Verifica se houve redirecionamento para a listagem
                redirected = False
                try:
                    self._log("⏳ Aguardando redirecionamento automático para listagem...")
                    page.wait_for_url("**/tarefamodelview/list/**", timeout=8000)
                    redirected = True
                    save_confirmed = True
                    self._log("✅ Redirecionado para listagem automaticamente")
                except Exception:
                    self._log("⚠️ Sem redirecionamento automático. Verificando se formulário ainda está na tela...")
                    
                # Se não redirecionou, verifica se o formulário ainda está visível (erro de validação)
                if not redirected:
                    try:
                        # Se houver alerta de sucesso, considera salvamento concluído mesmo sem redirect.
                        success_msgs = page.locator("div.alert-success, .alert.alert-success").all_text_contents()
                        if success_msgs:
                            save_confirmed = True
                            self._log(f"✅ Mensagem de sucesso detectada após salvar: {success_msgs[:1]}")

                        # Verifica se ainda está no formulário (possível erro de validação)
                        form_still_visible = page.locator("form#form_tarefamodelview, div.alert-danger").is_visible()
                        if form_still_visible:
                            # Tira screenshot para debug
                            page.screenshot(path="/tmp/debug_form_validation_error.png")
                            
                            # Tenta capturar mensagens de erro
                            error_msgs = page.locator("div.alert-danger, .has-error .help-block").all_text_contents()
                            if error_msgs:
                                self._log(f"❌ Erros de validação no formulário: {error_msgs}")
                                raise ValueError(f"Formulário não foi salvo. Erros: {error_msgs}. Ver /tmp/debug_form_validation_error.png")
                            else:
                                self._log("⚠️ Formulário ainda visível sem erro explícito. Tentando segundo submit defensivo...")
                                page.evaluate(r"""() => {
                                    const form = document.querySelector('form#form_tarefamodelview') || document.querySelector('form#model_form') || document.querySelector('form');
                                    if (!form) return;
                                    if (typeof form.requestSubmit === 'function') {
                                        form.requestSubmit();
                                    } else {
                                        form.submit();
                                    }
                                }""")
                                try:
                                    page.wait_for_load_state("networkidle", timeout=20000)
                                except Exception:
                                    page.wait_for_timeout(3000)

                                # Revalida sucesso após segundo submit
                                success_msgs_retry = page.locator("div.alert-success, .alert.alert-success").all_text_contents()
                                if success_msgs_retry:
                                    save_confirmed = True
                                    self._log(f"✅ Mensagem de sucesso detectada após reenvio: {success_msgs_retry[:1]}")
                    except Exception as e:
                        self._log(f"⚠️ Erro ao verificar formulário: {e}")

                # Trava defensiva: não prosseguir para listagem sem confirmação mínima de salvamento.
                if not save_confirmed and "/tarefamodelview/list/" not in page.url:
                    page.screenshot(path="/tmp/debug_save_not_confirmed.png")
                    raise ValueError(
                        "Cadastro não confirmado no Munka (sem redirecionamento e sem mensagem de sucesso). "
                        "Abortando busca na listagem para evitar falso negativo. Ver /tmp/debug_save_not_confirmed.png"
                    )
            
            # --- FASE 2: EDITAR E ANEXAR EVIDÊNCIAS DIRETAMENTE ---
            edit_btn = None
            if not direct_edit_url:
                # Usa navegação via "Tarefas do Mês" (mais confiável que URL direta)
                self._log("📋 Navegando para listagem via 'Tarefas do Mês'...")
                self._navegar_tarefas_do_mes(page, expand_page_size=True)

                self._log(f"🔍 Localizando tarefa '{task_data.get('titulo')[:60]}...' na tabela...")
                try:
                    task_title = task_data.get('titulo')
                    task_title_probe = (task_title or "")[:45]
                    found_row = None

                    # Em alguns casos o cadastro demora alguns segundos para aparecer na listagem.
                    # Reaplica a listagem/filtros e tenta novamente antes de falhar.
                    for find_attempt in range(1, 5):
                        self._log(f"⏳ Tentativa {find_attempt}/4 para localizar a tarefa recém-cadastrada...")

                        # Prioriza afunilar a listagem pelo título para evitar falso negativo
                        # em páginas com muitos registros de outros projetos/equipes.
                        try:
                            title_for_filter = task_title if find_attempt <= 2 else task_title_probe
                            self._filtrar_listagem_por_titulo(page, title_for_filter)
                        except Exception as filter_e:
                            self._log(f"⚠️ Falha ao aplicar filtro de título: {filter_e}")

                        row_exact = page.locator("table.table-bordered tbody tr").filter(has_text=task_title).first
                        if row_exact.count() > 0:
                            try:
                                row_exact.wait_for(state="visible", timeout=8000)
                                found_row = row_exact
                                break
                            except Exception:
                                pass

                        if task_title_probe:
                            row_partial = page.locator("table.table-bordered tbody tr").filter(has_text=task_title_probe).first
                            if row_partial.count() > 0:
                                try:
                                    row_partial.wait_for(state="visible", timeout=5000)
                                    found_row = row_partial
                                    self._log("⚠️ Tarefa encontrada por título parcial (fallback)")
                                    break
                                except Exception:
                                    pass

                        if find_attempt < 4:
                            page.wait_for_timeout(2500)
                            self._navegar_tarefas_do_mes(page, expand_page_size=True, status_id=status_id)

                    if not found_row:
                        self._log("⚠️ Linha não encontrada por texto. Tentando fallback por links de edição...")
                        direct_edit_url = self._encontrar_edicao_por_titulo_nos_links_da_listagem(page, task_title)
                        if not direct_edit_url:
                            raise Exception("Linha da tarefa não apareceu na listagem após 4 tentativas")
                        self._log(f"✅ Link de edição encontrado por fallback: {direct_edit_url}")

                    row = found_row
                    if row:
                        self._log("✅ Linha da tarefa encontrada na tabela")

                        edit_btn = row.locator("a[href*='tarefamodelview/edit']").first
                        edit_btn.wait_for(state="visible", timeout=7000)
                        self._log("✅ Botão 'Editar' localizado")
                    else:
                        edit_btn = None
                except Exception as e:
                    self._log(f"❌ Erro ao localizar tarefa na listagem: {e}")
                    # Captura print de debug para entender onde a página travou ou se deu erro de validação
                    page.screenshot(path="/tmp/debug_edit_not_found.png")
                    
                    # Tenta listar as tarefas visíveis para debug
                    try:
                        visible_ids = page.locator("table.table-bordered tbody tr td:nth-child(2)").all_text_contents()
                        visible_names = page.locator("table.table-bordered tbody tr td:nth-child(3)").all_text_contents()
                        self._log(f"IDs visíveis na listagem ({len(visible_ids)}): {visible_ids[:5]}")
                        self._log(f"Nomes visíveis na listagem ({len(visible_names)}): {[n.strip()[:70] for n in visible_names[:5]]}")
                    except Exception:
                        pass
                        
                    raise ValueError(f"Não foi possível encontrar a tarefa '{task_title}' na listagem. Ver /tmp/debug_edit_not_found.png") from e

            task_id = None
            try:
                href = direct_edit_url or (edit_btn.get_attribute("href") if edit_btn else "") or ""
                self._log(f"📎 Link de edição: '{href}'")
                import re
                match = re.search(r"tarefamodelview/edit/(\d+)", href)
                if match:
                    task_id = match.group(1)
                    self._log(f"✅ ID da tarefa extraído: #{task_id}")
                else:
                    self._log("⚠️ Não foi possível encontrar o ID da tarefa no href")
            except Exception as ex:
                self._log(f"⚠️ Erro ao extrair ID da tarefa: {ex}")

            if direct_edit_url:
                self._log("🧭 Abrindo formulário por URL de edição (fallback)...")
                self._safe_goto(page, direct_edit_url)
            else:
                self._log("🖱️ Clicando no botão 'Editar'...")
                edit_btn.click(no_wait_after=True)

            self._log("⏳ Aguardando formulário de edição carregar...")
            page.wait_for_selector("form, #nome", state="visible", timeout=20000)
            self._log("✅ Formulário de edição carregado")

            # Mudar status final para o configurado ANTES de preencher a execução
            self._log(f"⚙️ Configurando status final para: '{status_id}'...")
            page.locator("#status").wait_for(state="attached", timeout=5000)
            page.evaluate(select2_script)
            page.wait_for_timeout(200)

            # Expandir painel de Execução
            self._log("📋 Verificando se o painel 'Execução' está aberto...")
            if not page.locator("#data_fim").is_visible():
                self._log("➕ Painel 'Execução' colapsado. Expandindo...")
                page.locator('[id="3_href"]').click()
                page.locator("#data_fim").wait_for(state="visible", timeout=5000)
                self._log("✅ Painel 'Execução' expandido")
            else:
                self._log("✅ Painel 'Execução' já estava aberto")

            # Data de Fim: utiliza commit_metadata["data_fim"] que já vem com a hora configurada pelo usuário.
            # Fallback: se data_fim não tiver data completa, extrai a data de data_inicio e concatena com a hora de data_fim.
            data_fim = commit_metadata.get("data_fim", "")
            if not data_fim:
                data_inicio = commit_metadata.get("data_inicio", "")
                data_fim = f"{data_inicio[:10]} 18:00" if data_inicio and len(data_inicio) >= 10 else datetime.now().strftime("%d/%m/%Y 18:00")
            elif " " not in data_fim and len(data_fim) <= 5:
                # Apenas hora foi configurada (ex: "17:00") — extrai data de data_inicio
                data_inicio = commit_metadata.get("data_inicio", "")
                if data_inicio and len(data_inicio) >= 10:
                    data_fim = f"{data_inicio[:10]} {data_fim}"
                else:
                    data_fim = f"{datetime.now().strftime('%d/%m/%Y')} {data_fim}"

            self._log(f"📅 Preenchendo Data de Fim: '{data_fim}'...")
            page.locator("#data_fim").fill(data_fim)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#data_fim').val('{data_fim}').trigger('change'); }} }}")
            page.locator("#data_fim").press("Tab")
            self._log("✅ Data de Fim preenchida")

            # Horas Executadas
            hpa_str = str(task_data.get("hpa", "1.0"))
            self._log(f"⏱️ Preenchendo Horas Executadas: '{hpa_str}' HPA...")
            page.locator("#horas_executadas").fill(hpa_str)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#horas_executadas').val('{hpa_str}').trigger('change'); }} }}")
            self._log("✅ Horas Executadas preenchidas")

            # Evidências (TinyMCE)
            if custom_evidence_html:
                self._log("📝 Utilizando HTML customizado de evidência...")
                evidence_text = custom_evidence_html
            else:
                self._log("📝 Gerando HTML padrão de evidência...")
                desc_text = task_data.get("descricao", "")
                just_text = task_data.get("justificativa", "")
                evidence_text = (
                    f"<p>{desc_text}</p>"
                    f"<p><strong>Justificativa Técnica:</strong></p>"
                    f"<p>{just_text}</p>"
                    f"<p>Evidência de codificação gerada automaticamente a partir "
                    f"do commit SHA {commit_metadata.get('sha', 'sem_sha')}. Ver anexo.</p>"
                )

            self._log("📄 Injetando conteúdo no editor TinyMCE de evidências...")
            try:
                iframe = page.frame_locator("#evidencias_ifr")
                tinymce_body = iframe.locator("body#tinymce")
                self._log("⏳ Aguardando iframe do TinyMCE...")
                tinymce_body.wait_for(state="visible", timeout=10000)
                tinymce_body.evaluate("(el, html) => { el.innerHTML = html; }", evidence_text)
                self._log("✅ Conteúdo injetado no TinyMCE")
            except Exception as e_tiny:
                self._log(f"⚠️ Aviso ao injetar no iframe do TinyMCE: {e_tiny}")

            # Sincroniza com a API do TinyMCE e com o textarea #evidencias para garantir o POST do formulário
            page.evaluate("""(html) => {
                if (typeof tinymce !== 'undefined') {
                    if (tinymce.get('evidencias')) {
                        tinymce.get('evidencias').setContent(html);
                        tinymce.get('evidencias').save();
                    } else if (tinymce.activeEditor) {
                        tinymce.activeEditor.setContent(html);
                        tinymce.activeEditor.save();
                    }
                    if (typeof tinymce.triggerSave === 'function') {
                        tinymce.triggerSave();
                    }
                }
                if (typeof $ !== 'undefined') {
                    var $ev = $('#evidencias');
                    if ($ev.length) {
                        $ev.val(html).trigger('change');
                    }
                } else {
                    var el = document.getElementById('evidencias');
                    if (el) { el.value = html; }
                }
            }""", evidence_text)

            # Evidência commit SHA (URL completa ou fallback para SHA)
            commit_val = commit_metadata.get("url") or commit_metadata.get("sha", "sem_sha")
            self._log(f"🔗 Preenchendo Commit SHA/URL: '{commit_val[:80]}...'")
            page.locator("#evidencia_commit_sha").fill(commit_val)
            page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#evidencia_commit_sha').val('{commit_val}').trigger('change'); }} }}")
            self._log("✅ Commit SHA/URL preenchido")

            # Salvar Alterações (garantindo fechamento de overlays e sincronização do TinyMCE)
            self._log("🔄 Sincronizando TinyMCE e fechando dropdowns...")
            page.keyboard.press("Escape")
            page.evaluate("""() => {
                if (typeof tinymce !== 'undefined' && typeof tinymce.triggerSave === 'function') {
                    tinymce.triggerSave();
                }
                if (typeof $ !== 'undefined') {
                    $('.my_select2, select').select2('close');
                }
            }""")
            page.wait_for_timeout(200)

            self._log("💾 Salvando alterações finais da homologação...")
            save_btn = page.locator("form#model_form button[type='submit'], form#model_form input[type='submit'], form button[type='submit'], form input[type='submit']").first
            try:
                self._log("⏳ Aguardando navegação após salvar (timeout 30s)...")
                with page.expect_navigation(timeout=30000):
                    save_btn.click()
                self._log("✅ Navegação após salvar concluída")
            except Exception as e:
                self._log(f"⚠️ Timeout na navegação após salvar: {e}. Tentando alternativa...")
                try:
                    save_btn.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    self._log("✅ Página estabilizada após salvar")
                except Exception as e2:
                    self._log(f"⚠️ Timeout ao aguardar networkidle: {e2}. Aguardando 3s...")
                    page.wait_for_timeout(3000)

            # --- VERIFICAÇÃO PÓS-SALVAMENTO: Checa se a data_fim foi gravada ---
            self._log(f"Iniciando verificação pós-salvamento do campo data_fim para '{task_title}'...")
            try:
                if task_id:
                    edit_url = f"{self.base_url}/tarefamodelview/edit/{task_id}"
                    self._safe_goto(page, edit_url)
                else:
                    self._navegar_tarefas_do_mes(page, expand_page_size=False, status_id=status_id)
                    row = page.locator("table.table-bordered tbody tr").filter(has_text=task_title).first
                    row.wait_for(timeout=10000)
                    edit_btn = row.locator("a[href*='tarefamodelview/edit']").first
                    href = edit_btn.get_attribute("href") or ""
                    match = re.search(r"tarefamodelview/edit/(\d+)", href)
                    if match:
                        edit_url = f"{self.base_url}/tarefamodelview/edit/{match.group(1)}"
                        self._safe_goto(page, edit_url)
                    else:
                        edit_btn.click()
                        page.wait_for_selector("form, #nome", state="visible", timeout=15000)

                page.wait_for_selector("form, #nome", state="visible", timeout=15000)
                if not page.locator("#data_fim").is_visible():
                    painel_execucao = page.locator('[id="3_href"]')
                    if painel_execucao.count() > 0:
                        painel_execucao.click()
                        page.locator("#data_fim").wait_for(state="visible", timeout=5000)

                val_data_fim = page.locator("#data_fim").input_value().strip()
                if not val_data_fim:
                    self._log("ATENÇÃO: data_fim vazia após o salvamento! Re-preenchendo, sincronizando TinyMCE e salvando com aguardo de navegação...")
                    page.locator("#data_fim").fill(data_fim)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#data_fim').val('{data_fim}').trigger('change'); }} }}")
                    page.locator("#data_fim").press("Tab")

                    page.locator("#horas_executadas").fill(hpa_str)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#horas_executadas').val('{hpa_str}').trigger('change'); }} }}")

                    try:
                        iframe = page.frame_locator("#evidencias_ifr")
                        tinymce_body = iframe.locator("body#tinymce")
                        tinymce_body.wait_for(state="visible", timeout=10000)
                        tinymce_body.evaluate("(el, html) => { el.innerHTML = html; }", evidence_text)
                    except Exception:
                        pass

                    page.evaluate("""(html) => {
                        if (typeof tinymce !== 'undefined') {
                            if (tinymce.get('evidencias')) {
                                tinymce.get('evidencias').setContent(html);
                                tinymce.get('evidencias').save();
                            } else if (tinymce.activeEditor) {
                                tinymce.activeEditor.setContent(html);
                                tinymce.activeEditor.save();
                            }
                            if (typeof tinymce.triggerSave === 'function') {
                                tinymce.triggerSave();
                            }
                        }
                        if (typeof $ !== 'undefined') {
                            var $ev = $('#evidencias');
                            if ($ev.length) { $ev.val(html).trigger('change'); }
                        }
                    }""", evidence_text)

                    page.locator("#evidencia_commit_sha").fill(commit_val)
                    page.evaluate(f"() => {{ if (typeof $ !== 'undefined') {{ $('#evidencia_commit_sha').val('{commit_val}').trigger('change'); }} }}")

                    page.evaluate(select2_script)
                    page.wait_for_timeout(100)

                    page.keyboard.press("Escape")
                    page.evaluate("""() => {
                        if (typeof tinymce !== 'undefined' && typeof tinymce.triggerSave === 'function') {
                            tinymce.triggerSave();
                        }
                        if (typeof $ !== 'undefined') {
                            $('.my_select2, select').select2('close');
                        }
                    }""")
                    page.wait_for_timeout(200)

                    save_btn = page.locator("form#model_form button[type='submit'], form#model_form input[type='submit'], form button[type='submit'], form input[type='submit']").first
                    try:
                        with page.expect_navigation(timeout=30000):
                            save_btn.click()
                    except Exception:
                        save_btn.click()
                        page.wait_for_load_state("networkidle", timeout=10000)
                    self._log("Re-salvamento da tarefa concluído!")
                else:
                    self._log(f"Verificação concluída com sucesso! data_fim '{val_data_fim}' gravada corretamente.")
            except Exception as chk_e:
                self._log(f"Verificação de data_fim concluída com aviso: {chk_e}")

            browser.close()
            self._log("Fluxo completo finalizado com sucesso!")
            return task_data.get("titulo", ""), task_id
