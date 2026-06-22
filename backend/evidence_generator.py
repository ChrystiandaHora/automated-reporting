import html
import re
from datetime import datetime

# Estilos CSS comuns que serão embutidos
CSS_STYLE = """
.medicao-evidencia {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: #fff;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 20px;
    max-width: 980px;
    margin: 0 auto;
}
.medicao-evidencia h3 {
    margin-top: 0;
    color: #1f75cb;
    border-bottom: 2px solid #1f75cb;
    padding-bottom: 8px;
    font-size: 1.2rem;
}
.medicao-evidencia p {
    margin: 6px 0;
    font-size: 0.9rem;
    line-height: 1.5;
}
.medicao-evidencia .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    background: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 15px;
    border: 1px solid #e1e4e8;
}
.medicao-evidencia .meta-item {
    font-size: 0.85rem;
}
.medicao-evidencia .meta-item strong {
    color: #57606a;
}
.medicao-evidencia .badge-hpa {
    background: #e6ffec;
    color: #1a7f37;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 0.85rem;
    display: inline-block;
}
.medicao-evidencia .file-section {
    margin-top: 20px;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    overflow: hidden;
}
.medicao-evidencia .file-header {
    background: #f6f8fa;
    padding: 8px 14px;
    font-family: monospace;
    font-size: 0.8rem;
    color: #57606a;
    border-bottom: 1px solid #d0d7de;
}
.medicao-evidencia .diff-table {
    width: 100%;
    border-collapse: collapse;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
    font-size: 0.78rem;
}
.medicao-evidencia .diff-table td {
    padding: 2px 8px;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.5;
}
.medicao-evidencia .diff-table .ln {
    width: 1%;
    min-width: 40px;
    text-align: right;
    color: #8c959f;
    background: #f6f8fa;
    border-right: 1px solid #d0d7de;
    user-select: none;
}
.medicao-evidencia .impacto-box {
    background: #fffbe6;
    border-left: 4px solid #d4a017;
    padding: 10px 14px;
    margin-top: 15px;
    border-radius: 0 4px 4px 0;
    font-size: 0.88rem;
}
.medicao-evidencia .justif-box {
    background: #f6f8fa;
    border-left: 4px solid #8c959f;
    padding: 10px 14px;
    margin-top: 15px;
    border-radius: 0 4px 4px 0;
    font-size: 0.88rem;
}
"""

# Estilos inline para as linhas da tabela de diff (usados nos <tr> e <td>)
_TD_BASE    = "padding: 2px 10px; font-family: monospace; font-size: 11px;"
_TD_LN      = f"background-color: #f6f8fa; color: #8c959f; text-align: right; border-right: 1px solid #d0d7de; {_TD_BASE} user-select: none; width: 1%; min-width: 35px;"
_TD_CODE    = f"{_TD_BASE} white-space: pre-wrap;"

_STYLES = {
    "add": {
        "ln":   f"background-color: #ccffd8; color: #1a7f37; text-align: right; border-right: 1px solid #d0d7de; {_TD_BASE}",
        "code": f"background-color: #e6ffec; color: #1a7f37; {_TD_CODE}",
    },
    "del": {
        "ln":   f"background-color: #ffd7d5; color: #cf222e; text-align: right; border-right: 1px solid #d0d7de; {_TD_BASE}",
        "code": f"background-color: #ffebe9; color: #cf222e; {_TD_CODE}",
    },
    "hunk": {
        "span": "background-color: #ddf4ff; color: #0550ae; text-align: center; border-right: 1px solid #d0d7de; padding: 2px 10px; font-family: monospace; font-size: 11px;",
        "code": "background-color: #ddf4ff; color: #0550ae; padding: 2px 10px; font-family: monospace; font-size: 11px; white-space: pre-wrap;",
    },
    "ctx": {
        "ln":   _TD_LN,
        "code": f"background-color: #ffffff; color: #24292f; {_TD_CODE}",
    },
}


def extrair_diff_do_arquivo(diff_completo: str, caminho_arquivo: str) -> str:
    """Extrai do diff completo do commit apenas o trecho relativo ao arquivo indicado.

    Percorre o diff linha por linha procurando o cabeçalho ``diff --git`` que
    contenha ``caminho_arquivo`` e captura tudo até o próximo cabeçalho ou fim
    do texto.

    Args:
        diff_completo: Texto completo do diff do commit (saída de ``git diff``).
        caminho_arquivo: Caminho relativo do arquivo (ex: ``"src/models.py"``).

    Returns:
        String com o trecho do diff referente ao arquivo, ou ``""`` se não
        encontrado.
    """
    linhas = diff_completo.splitlines()
    capturando = False
    trecho: list[str] = []

    for linha in linhas:
        if linha.startswith("diff --git"):
            if capturando:
                break  # Início de novo arquivo — encerra captura
            if caminho_arquivo.replace("\\", "/") in linha:
                capturando = True
                trecho.append(linha)
        elif capturando:
            trecho.append(linha)

    return "\n".join(trecho)


def renderizar_tabela_diff(diff_texto: str) -> str:
    """Converte texto de diff unificado em uma tabela HTML colorida estilo GitHub.

    Cada linha do diff é mapeada para uma linha ``<tr>`` com dois números de
    linha (antes/depois) e o conteúdo colorido conforme o tipo:

    - ``+`` → verde (adição)
    - ``-`` → vermelho (remoção)
    - ``@@`` → azul claro (hunk header)
    - demais → branco (contexto)

    As linhas de cabeçalho de metadados do git (``diff --git``, ``index``,
    ``--- a/``, ``+++ b/``) são omitidas da tabela pois já aparecem no
    ``file-header`` acima.

    Args:
        diff_texto: Trecho de diff unificado de um único arquivo.

    Returns:
        String HTML com a tag ``<table>`` completa pronta para embutir no
        documento de evidência.
    """
    linhas = diff_texto.splitlines()
    linhas_html: list[str] = []
    ln_antes = 0
    ln_depois = 0

    # Tenta extrair os números de linha iniciais do primeiro hunk
    for linha in linhas:
        m = re.match(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', linha)
        if m:
            ln_antes = int(m.group(1)) - 1
            ln_depois = int(m.group(2)) - 1
            break

    for linha in linhas:
        esc = html.escape(linha)

        # Hunk header (@@ ... @@)
        if linha.startswith("@@"):
            m = re.match(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)', linha)
            if m:
                ln_antes = int(m.group(1)) - 1
                ln_depois = int(m.group(2)) - 1
                resto = html.escape("@@ " + m.group(3).strip()) if m.group(3).strip() else ""
                st = _STYLES["hunk"]
                linhas_html.append(
                    f'<tr class="hunk">'
                    f'<td style="{st["span"]}" colspan="2">@@</td>'
                    f'<td style="{st["code"]}">@@ {html.escape(m.group(0)[3:].split("@@")[0].strip())} @@{html.escape(m.group(3))}</td>'
                    f'</tr>'
                )
            continue

        # Linhas de metadados git — omitidas da tabela
        if any(linha.startswith(p) for p in ("diff --git", "index ", "--- a/", "+++ b/", "--- /dev/null", "+++ /dev/null", "\\ No newline")):
            continue

        if linha.startswith("+"):
            ln_depois += 1
            st = _STYLES["add"]
            linhas_html.append(
                f'<tr class="add">'
                f'<td style="{_TD_LN}">&nbsp;</td>'
                f'<td style="{st["ln"]}">{ln_depois}</td>'
                f'<td style="{st["code"]}">{esc}</td>'
                f'</tr>'
            )
        elif linha.startswith("-"):
            ln_antes += 1
            st = _STYLES["del"]
            linhas_html.append(
                f'<tr class="del">'
                f'<td style="{st["ln"]}">{ln_antes}</td>'
                f'<td style="{_TD_LN}">&nbsp;</td>'
                f'<td style="{st["code"]}">{esc}</td>'
                f'</tr>'
            )
        else:
            ln_antes += 1
            ln_depois += 1
            st = _STYLES["ctx"]
            linhas_html.append(
                f'<tr class="ctx">'
                f'<td style="{st["ln"]}">{ln_antes}</td>'
                f'<td style="{st["ln"]}">{ln_depois}</td>'
                f'<td style="{st["code"]}">{esc if esc.strip() else "&nbsp;"}</td>'
                f'</tr>'
            )

    rows = "\n".join(linhas_html)
    return (
        '<table style="width: 100%; border-collapse: collapse; margin: 0; border: 0;">'
        "<tbody>"
        f"{rows}"
        "</tbody>"
        "</table>"
    )


def gerar_html_evidencia(act: dict, commit_metadata: dict, diff_completo: str, system_name: str = "Novo Sistema", complexity: str = "Única") -> str:
    """Build the complete HTML evidence document for a Munka activity.

    Assembles a self-contained HTML fragment (not a full ``<!DOCTYPE>``
    document) intended to be attached to the corresponding Munka task as
    evidence of the work performed. The fragment embeds the ``CSS_STYLE``
    block and is structured in four sections:

    1. **Header / Metadata grid** — activity code, title, system name,
       complexity, commit SHA, start date, category, and HPA workload badge.
    2. **Technical description** — the activity's ``descricao`` field rendered
       as a paragraph.
    3. **Changed source files** — for each path listed in ``act["arquivos"]``,
       calls ``extrair_diff_do_arquivo`` and ``renderizar_tabela_diff`` to
       render the relevant diff as a colour-coded table inside a
       ``.file-section`` block. Files with no captured diff get a highlighted
       warning header instead.
    4. **Impact and justification boxes** — a fixed impact statement for the
       system and the activity's ``justificativa`` field.

    Args:
        act: Dictionary representing the Munka activity. Expected keys:
            ``codigo_id``, ``titulo``, ``categoria``, ``hpa``, ``descricao``,
            ``arquivos`` (list of file paths), and ``justificativa``.
        commit_metadata: Dictionary with commit information. Expected keys:
            ``sha`` (commit hash string) and ``data_inicio`` (formatted date
            string, e.g. ``"14/06/2026 10:00"``).
        diff_completo: Full git diff text for the commit, used to extract
            per-file diffs for the files listed in ``act["arquivos"]``.
        system_name: Human-readable name of the system being modified.
            Defaults to ``"Novo Sistema"``.
        complexity: Complexity label for the activity (e.g. ``"Única"``,
            ``"Simples"``). Defaults to ``"Única"``.

    Returns:
        A multi-line HTML string forming the complete evidence fragment,
        starting with a ``<style>`` block and ending with the closing
        ``</div>`` of the ``.medicao-evidencia`` container.
    """
    sha = commit_metadata.get("sha", "sem_sha")
    data_inicio = commit_metadata.get("data_inicio", datetime.now().strftime("%d/%m/%Y %H:%M"))

    # 1. Cabeçalho e Metadados
    html_parts = []
    html_parts.append(f"<style>\n{CSS_STYLE}\n</style>")
    html_parts.append('<div class="medicao-evidencia">')
    html_parts.append(f'<h3>EVIDÊNCIA DE ATIVIDADE — {act.get("codigo_id")} — {act.get("titulo")}</h3>')

    html_parts.append('<div class="meta-grid">')
    html_parts.append(f'<div class="meta-item"><strong>Sistema:</strong> {system_name}</div>')
    html_parts.append(f'<div class="meta-item"><strong>Complexidade:</strong> {complexity}</div>')
    html_parts.append(f'<div class="meta-item"><strong>Commit SHA:</strong> <code>{sha}</code></div>')
    html_parts.append(f'<div class="meta-item"><strong>Data Início:</strong> {data_inicio}</div>')
    html_parts.append(f'<div class="meta-item"><strong>Categoria:</strong> {act.get("categoria")}</div>')
    html_parts.append(f'<div class="meta-item"><strong>Carga Horária (HPA):</strong> <span class="badge-hpa">{act.get("hpa")}h</span></div>')
    html_parts.append('</div>')

    # 2. Descrição Técnica da Atividade
    html_parts.append(f'<p>{act.get("descricao")}</p>')

    # 3. Diffs dos Arquivos Relacionados
    arquivos = act.get("arquivos", [])
    if arquivos:
        html_parts.append('<p style="font-weight: bold; margin-top: 15px; color: #1f75cb; font-size: 0.95rem;">Código Fonte Alterado:</p>')

        for arq in arquivos:
            diff_arq = extrair_diff_do_arquivo(diff_completo, arq)
            if diff_arq:
                tabela_html = renderizar_tabela_diff(diff_arq)
                html_parts.append(f"""
                <div class="file-section">
                    <div class="file-header">diff --git a/{arq} b/{arq}</div>
                    {tabela_html}
                </div>
                """)
            else:
                html_parts.append(f"""
                <div class="file-section">
                    <div class="file-header" style="background-color:#fff5f5;color:#9e2a2b;">Arquivo: {arq} (Sem alterações de diff capturadas)</div>
                </div>
                """)

    # 4. Impacto e Justificativa
    html_parts.append(f"""
    <div class="impacto-box">
        <strong>Impacto da Alteração:</strong>
        <p style="margin:4px 0 0;">O código modificado atende diretamente à necessidade descrita, garantindo integridade referencial, novos comportamentos dinâmicos ou correções necessárias no sistema {system_name}.</p>
    </div>
    <div class="justif-box">
        <strong>Justificativa do Enquadramento (Catálogo de Serviços):</strong>
        <p style="margin:4px 0 0;">{act.get("justificativa")}</p>
    </div>
    """)

    html_parts.append('</div>')  # Fim .medicao-evidencia

    return "\n".join(html_parts)
