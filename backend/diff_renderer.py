import os
import html
import tempfile
from playwright.sync_api import sync_playwright

def render_diff_to_html(diff_content: str) -> str:
    """Convert raw git diff text into a styled, self-contained HTML document.

    Produces a complete ``<!DOCTYPE html>`` page with dark-mode styling
    (GitHub-inspired ``#0d1117`` background) suitable for rendering in a
    headless browser. Each diff line is wrapped in a ``<div class="line
    <type>">`` element where ``<type>`` is one of:

    - ``addition`` — lines starting with ``+`` (excluding ``+++`` headers),
      rendered in green with a green left border.
    - ``deletion`` — lines starting with ``-`` (excluding ``---`` headers),
      rendered in red with a red left border.
    - ``header`` — hunk range lines starting with ``@@``, rendered in blue.
    - ``meta`` — git metadata lines (``diff --git``, ``index``, ``--- a/``,
      ``+++ b/``), rendered in grey.
    - ``normal`` — all other context lines, rendered in the default foreground
      colour.

    All line content is HTML-escaped before insertion.

    Args:
        diff_content: Raw unified diff text (one or more files).

    Returns:
        A complete HTML document string, including ``<head>`` with embedded
        CSS and a ``<body>`` containing one ``<div>`` per diff line.
    """
    lines = diff_content.splitlines()
    html_lines = []
    for line in lines:
        # Codifica caracteres HTML especiais para segurança e renderização correta
        escaped_line = html.escape(line)
        if line.startswith('+') and not line.startswith('+++'):
            class_name = 'addition'
        elif line.startswith('-') and not line.startswith('---'):
            class_name = 'deletion'
        elif line.startswith('@@'):
            class_name = 'header'
        elif line.startswith('diff --git') or line.startswith('index ') or line.startswith('--- a/') or line.startswith('+++ b/'):
            class_name = 'meta'
        else:
            class_name = 'normal'
        
        # Manter espaçamento do início
        html_lines.append(f'<div class="line {class_name}">{escaped_line}</div>')
    
    html_body = "\n".join(html_lines)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
                font-size: 12px;
                line-height: 1.6;
                margin: 0;
                padding: 15px;
            }}
            .line {{
                white-space: pre-wrap;
                padding: 1px 8px;
                border-radius: 2px;
                font-family: inherit;
            }}
            .addition {{
                background-color: rgba(46, 160, 67, 0.15);
                color: #3fb950;
                border-left: 3px solid #2ea043;
            }}
            .deletion {{
                background-color: rgba(248, 81, 73, 0.15);
                color: #f85149;
                border-left: 3px solid #f85149;
            }}
            .header {{
                color: #58a6ff;
                background-color: rgba(56, 139, 253, 0.1);
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 5px;
            }}
            .meta {{
                color: #8b949e;
                font-weight: bold;
            }}
            .normal {{
                color: #c9d1d9;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    return html_content

def generate_diff_image(diff_content: str, output_path: str = "evidencia_temp.png"):
    """Render a git diff as a PNG image via a headless Chromium browser.

    The process is:

    1. Convert ``diff_content`` to a styled HTML document using
       ``render_diff_to_html``.
    2. Write the HTML to a temporary file (``tempfile.mktemp`` with a
       ``.html`` suffix).
    3. Launch Playwright's Chromium in headless mode at a 1024×768 viewport,
       navigate to the temporary file via a ``file:///`` URL, and take a
       full-page screenshot saved to ``output_path``.
    4. Delete the temporary HTML file in a ``finally`` block, regardless of
       whether the screenshot succeeded.

    Args:
        diff_content: Raw unified diff text to render.
        output_path: Destination path for the PNG screenshot. Defaults to
            ``"evidencia_temp.png"`` in the current working directory.

    Raises:
        playwright.sync_api.Error: If Playwright fails to launch the browser,
            navigate to the page, or capture the screenshot (e.g. Chromium is
            not installed or the page crashes).
        OSError: If the temporary HTML file cannot be written, or if
            ``output_path`` is not writable.
    """
    html_content = render_diff_to_html(diff_content)
    
    temp_html_path = tempfile.mktemp(suffix=".html")
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--disable-software-rasterizer"]
            )
            # Define uma largura confortável para exibir código sem quebras excessivas
            context = browser.new_context(viewport={"width": 1024, "height": 768})
            page = context.new_page()
            page.goto(f"file:///{temp_html_path.replace(os.sep, '/')}")
            
            # Tira o print de toda a página (full page)
            page.screenshot(path=output_path, full_page=True)
            browser.close()
    finally:
        if os.path.exists(temp_html_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass
