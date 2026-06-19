import html
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
        ``</div>`` of the ``.medicao-evidencia`` container. This string is
        ready to be written to a file or embedded in an email/attachment for
        the Munka task.
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
        html_parts.append('<p style="font-weight:bold;margin-top:15px;color:#1f75cb;font-size:0.95rem;">Código Fonte Alterado:</p>')
        
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
    
    html_parts.append('</div>') # Fim .medicao-evidencia
    
    return "\n".join(html_parts)
