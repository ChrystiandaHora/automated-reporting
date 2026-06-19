import os
import json
import urllib.parse
import re
from datetime import datetime

import requests as _requests


def _gitlab_get(url: str, token: str) -> str:
    """Make an authenticated GET request to the GitLab API.

    Uses a ``PRIVATE-TOKEN`` header for authentication. SSL verification is
    intentionally disabled (``verify=False``) to support self-hosted GitLab
    instances with self-signed certificates.

    Args:
        url: Full URL of the GitLab API endpoint to call.
        token: GitLab personal access token (PAT) with at least ``read_api``
            scope.

    Returns:
        The raw response body as a UTF-8 string. The caller is responsible for
        parsing it (e.g. via ``json.loads``).

    Raises:
        RuntimeError: If the HTTP response status code indicates failure
            (``not resp.ok``), including the status code and the first 300
            characters of the response body in the message.
    """
    resp = _requests.get(url, headers={"PRIVATE-TOKEN": token}, verify=False, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"GitLab API retornou {resp.status_code}: {resp.text[:300]}")
    return resp.text


def obter_metadados_commit(gitlab_url: str, token: str, project_path: str, commit_hash: str) -> dict:
    """Fetch commit metadata from the GitLab Commits API.

    Calls ``GET /api/v4/projects/:id/repository/commits/:sha`` and returns the
    parsed JSON object. The ``project_path`` is percent-encoded before being
    embedded in the URL so that paths containing slashes (e.g.
    ``"group/subgroup/repo"``) are handled correctly.

    Args:
        gitlab_url: Base URL of the GitLab instance, e.g.
            ``"https://gitlab.example.com"``. Trailing slashes are stripped.
        token: GitLab personal access token passed to ``_gitlab_get``.
        project_path: Namespace and repository name as they appear in GitLab,
            e.g. ``"mygroup/myrepo"``.
        commit_hash: Full or abbreviated SHA-1 of the target commit.

    Returns:
        A dict representing the GitLab commit object. Relevant keys include:
        ``id`` (full SHA), ``message``, ``title``, ``author_name``,
        ``author_email``, ``committed_date``, and ``created_at``.

    Raises:
        ValueError: If the API response is not valid JSON, if the response
            contains a 4xx status code embedded in a JSON ``message`` field,
            or if the ``id`` key is absent from the response (unexpected shape).
        RuntimeError: Propagated from ``_gitlab_get`` on HTTP-level failures.
    """
    project_encoded = urllib.parse.quote_plus(project_path)
    url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_encoded}/repository/commits/{commit_hash}"

    stdout = _gitlab_get(url, token)

    try:
        dados = json.loads(stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Não foi possível decodificar o JSON da API. Resposta:\n{stdout[:500]}")

    if isinstance(dados, dict) and "message" in dados and "40" in str(dados.get("status", "")):
        raise ValueError(f"Erro na API do GitLab: {dados['message']}")

    if "id" not in dados:
        raise ValueError(f"Resposta inesperada da API do GitLab: {dados}")

    return dados


def obter_diff_commit(gitlab_url: str, token: str, project_path: str, commit_hash: str) -> str:
    """Retrieve the unified diff for a GitLab commit.

    Uses a two-stage strategy to maximise compatibility across GitLab versions
    and instance configurations:

    1. **Patch endpoint** – calls
       ``GET /api/v4/projects/:id/repository/commits/:sha/patch``.
       If the response is non-empty and does not start with ``{`` or ``[``
       (i.e. it is genuine patch text rather than a JSON error body), it is
       returned immediately.

    2. **JSON diff fallback** – if the patch endpoint fails or returns a JSON
       body, calls ``GET /api/v4/projects/:id/repository/commits/:sha/diff``
       instead. The resulting list of file-diff objects is reconstructed into
       a standard unified-diff string, including ``diff --git``, ``new file``/
       ``deleted file`` mode lines, ``---``/``+++`` headers, and the raw hunk
       text from each entry's ``diff`` field.

    Args:
        gitlab_url: Base URL of the GitLab instance, e.g.
            ``"https://gitlab.example.com"``. Trailing slashes are stripped.
        token: GitLab personal access token passed to ``_gitlab_get``.
        project_path: Namespace and repository name as they appear in GitLab,
            e.g. ``"mygroup/myrepo"``.
        commit_hash: Full or abbreviated SHA-1 of the target commit.

    Returns:
        A raw unified-diff string suitable for passing to ``analisar_diff``.

    Raises:
        ValueError: If the JSON diff response cannot be decoded, contains an
            API error message, or is not a list as expected.
        RuntimeError: Propagated from ``_gitlab_get`` if the fallback diff
            endpoint itself returns an HTTP error.
    """
    project_encoded = urllib.parse.quote_plus(project_path)

    # 1. Tenta patch bruto
    patch_url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_encoded}/repository/commits/{commit_hash}/patch"
    try:
        patch_text = _gitlab_get(patch_url, token)
        if patch_text.strip().startswith(("{", "[")):
            try:
                json.loads(patch_text)
                raise ValueError("Retornou JSON no endpoint de patch")
            except json.JSONDecodeError:
                return patch_text
        else:
            if patch_text.strip():
                return patch_text
    except Exception:
        pass

    # 2. Fallback: JSON diff
    diff_url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_encoded}/repository/commits/{commit_hash}/diff"
    stdout = _gitlab_get(diff_url, token)

    try:
        diff_json = json.loads(stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Não foi possível decodificar o diff JSON. Resposta:\n{stdout[:500]}")

    if isinstance(diff_json, dict) and "message" in diff_json:
        raise ValueError(f"Erro na API do GitLab ao obter diff: {diff_json['message']}")

    if not isinstance(diff_json, list):
        raise ValueError(f"Resposta de diff inválida: {diff_json}")

    diff_lines = []
    for entry in diff_json:
        old_path = entry.get("old_path")
        new_path = entry.get("new_path")
        diff_content = entry.get("diff")

        diff_lines.append(f"diff --git a/{old_path} b/{new_path}")
        if entry.get("new_file"):
            diff_lines.append(f"new file mode {entry.get('b_mode', '100644')}")
        elif entry.get("deleted_file"):
            diff_lines.append(f"deleted file mode {entry.get('a_mode', '100644')}")

        diff_lines.append(f"--- a/{old_path}")
        diff_lines.append(f"+++ b/{new_path}")
        diff_lines.append(diff_content)
        diff_lines.append("")

    return "\n".join(diff_lines)


def importar_commit_gitlab(gitlab_url: str, token: str, project_path: str, commit_hash: str, output_dir: str = "commits") -> str:
    """Download commit metadata and diff, then persist them to a text file.

    Kept for backward compatibility with tooling that consumed the original
    file-based workflow. New code should prefer calling
    ``obter_metadados_commit`` and ``obter_diff_commit`` directly.

    The output file is named ``diff_commits_<YYYY_MM_DD>_<short_sha>.txt`` and
    written inside ``output_dir`` (created if it does not exist). The file
    header contains the commit date, author, project path, and subject line,
    followed by the full unified diff.

    Args:
        gitlab_url: Base URL of the GitLab instance, e.g.
            ``"https://gitlab.example.com"``. Trailing slashes are stripped.
        token: GitLab personal access token passed to the underlying helpers.
        project_path: Namespace and repository name as they appear in GitLab,
            e.g. ``"mygroup/myrepo"``.
        commit_hash: Full or abbreviated SHA-1 of the target commit. Only the
            first eight characters are used in the filename.
        output_dir: Directory where the output file is saved. Defaults to
            ``"commits"`` relative to the current working directory.

    Returns:
        The file path of the generated text file as a string, e.g.
        ``"commits/diff_commits_2024_01_15_a1b2c3d4.txt"``.

    Raises:
        ValueError: Propagated from ``obter_metadados_commit`` or
            ``obter_diff_commit`` if the API returns unexpected data.
        RuntimeError: Propagated from ``_gitlab_get`` on HTTP-level failures.
        OSError: If ``output_dir`` cannot be created or the file cannot be
            written.
    """
    meta = obter_metadados_commit(gitlab_url, token, project_path, commit_hash)
    diff_text = obter_diff_commit(gitlab_url, token, project_path, commit_hash)

    committed_date_str = meta.get("committed_date") or meta.get("created_at") or ""
    data_obj = None
    if committed_date_str:
        try:
            clean_date = re.sub(r'(\.\d+)?([+-]\d{2}:?\d{2}|Z)$', '', committed_date_str)
            data_obj = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass

    if not data_obj:
        data_obj = datetime.now()

    data_formatada_nome = data_obj.strftime("%Y_%m_%d")
    data_formatada_header = data_obj.strftime("%d/%m/%Y")
    short_sha = commit_hash[:8]

    filename = f"diff_commits_{data_formatada_nome}_{short_sha}.txt"
    filepath = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    conteudo = [
        f"Data do commit: {data_formatada_header} | Diff do commit {short_sha}",
        f"commit {meta.get('id') or commit_hash}",
        f"Author: {meta.get('author_name') or 'Desconhecido'} <{meta.get('author_email') or 'desconhecido@exemplo.com'}>",
        f"Date: {committed_date_str or datetime.now().isoformat()}",
        f"Project: {project_path}",
        f"Subject: {meta.get('title') or 'Sem Titulo'}",
        "",
        meta.get("message", ""),
        "",
        "--- DIFF COMEÇA AQUI ---",
        "",
        diff_text,
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(conteudo))

    return filepath
