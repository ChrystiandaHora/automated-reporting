import os
import json
import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

def _obter_caminho_config_persistente() -> str:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///munka.db")
    db_dir = "."
    if db_url.startswith("sqlite:///"):
        db_path = db_url[10:]
        if "/" in db_path or "\\" in db_path:
            db_dir = os.path.dirname(db_path) or "."
    return os.path.join(db_dir, "config_persistente.json")

def carregar_config_persistente():
    caminho = _obter_caminho_config_persistente()
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                for k, v in config_data.items():
                    if v is not None:
                        os.environ[k] = str(v)
        except Exception as e:
            print(f"Erro ao carregar configuracoes persistentes: {e}")

carregar_config_persistente()

def obter_config_valores() -> dict:
    config_valores = {
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "MUNKA_URL": os.environ.get("MUNKA_URL", ""),
        "MUNKA_USER": os.environ.get("MUNKA_USER", ""),
        "MUNKA_PASS": os.environ.get("MUNKA_PASS", ""),
        "GITLAB_TOKEN": os.environ.get("GITLAB_TOKEN", ""),
        "GITLAB_URL": os.environ.get("GITLAB_URL", ""),
        "MUNKA_CARGO": os.environ.get("MUNKA_CARGO", "9"),
        "MUNKA_NIVEL": os.environ.get("MUNKA_NIVEL", "3"),
        "MUNKA_RESPONSAVEL": os.environ.get("MUNKA_RESPONSAVEL", ""),
        "MUNKA_PRODUTO": os.environ.get("MUNKA_PRODUTO", "[DESENV] MUNKA"),
        "MUNKA_PROJETO": os.environ.get("MUNKA_PROJETO", "MUNKA Multicontrato"),
        "MUNKA_STATUS_ID": os.environ.get("MUNKA_STATUS_ID", "17"),
    }
    caminho = _obter_caminho_config_persistente()
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                for k, v in config_data.items():
                    if v is not None:
                        config_valores[k] = str(v)
        except Exception as e:
            print(f"Erro ao ler configuracoes persistentes dinamicamente: {e}")
    return config_valores


from database import engine, get_db, Base, SessionLocal
import models
from gitlab_service import obter_metadados_commit, obter_diff_commit
from gemini_service import analisar_diff
from evidence_generator import gerar_html_evidencia
from automation import MunkaAutomation
from celery_app import celery_app
from celery.result import AsyncResult
from celery_tasks import analisar_commit_task, enviar_atividade_task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Munka API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://localhost:80"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Schemas ───────────────────────────────────────────────

class ImportarRequest(BaseModel):
    commit_hash: str
    gitlab_url: Optional[str] = None
    token: Optional[str] = None
    project_path: Optional[str] = None

class AnalisarRequest(BaseModel):
    forcar: bool = False  # ignora cache se True

class AtualizarAtividadesRequest(BaseModel):
    atividades: list
    complexidade_global: Optional[str] = None

class EnviarRequest(BaseModel):
    atividade_idx: int
    cargo: str = "9"
    nivel: str = "3"
    responsavel: str = ""
    produto: str = "[DESENV] MUNKA"
    projeto: str = "MUNKA Multicontrato"
    status_id: str = "17"
    headless: bool = True
    gitlab_url: Optional[str] = None

class AtualizarCommitRequest(BaseModel):
    data: Optional[str] = None
    projeto: Optional[str] = None
    autor: Optional[str] = None
    mensagem: Optional[str] = None

class ConfiguracaoRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    munka_url: Optional[str] = None
    munka_user: Optional[str] = None
    munka_pass: Optional[str] = None
    gitlab_token: Optional[str] = None
    gitlab_url: Optional[str] = None
    munka_cargo: Optional[str] = None
    munka_nivel: Optional[str] = None
    munka_responsavel: Optional[str] = None
    munka_produto: Optional[str] = None
    munka_projeto: Optional[str] = None
    munka_status_id: Optional[str] = None

class FilaAnaliseRequest(BaseModel):
    commit_ids: list[str]
    modelo: str = "Gemini 2.5 Flash"

class FilaEnvioRequest(BaseModel):
    commit_id: str
    atividade_idx: int


# ─── Helpers ────────────────────────────────────────────────────────────────

def _extrair_metadados_diff(diff_text: str, filename: str = "") -> tuple[str, str, str, str]:
    """Extract SHA, date, project, and author from raw diff text.

    Parses common git diff header patterns to recover commit metadata.
    Falls back to the filename for the date and empty strings for project/author
    when the respective fields are not present in the diff text.

    Args:
        diff_text: Raw diff content, optionally containing git log headers
            (commit, Author, Date, Project lines).
        filename: Optional filename hint used to extract the date when the
            diff header does not contain a Date line
            (expects pattern ``diff_commits_YYYY_MM_DD``).

    Returns:
        A 4-tuple ``(sha, data_dd_mm_yyyy, projeto, autor)`` where
        ``sha`` is the full or short commit hash (``"sem_sha"`` when not
        found), ``data_dd_mm_yyyy`` is the commit date formatted as
        ``DD/MM/YYYY``, ``projeto`` is the project path, and ``autor`` is
        the commit author name.
    """
    sha = "sem_sha"
    sha_match = re.search(r'\b([0-9a-fA-F]{40})\b', diff_text)
    if sha_match:
        sha = sha_match.group(1)
    else:
        sha_match = re.search(r'^commit\s+([0-9a-fA-F]{7,40})', diff_text, re.MULTILINE)
        if sha_match:
            sha = sha_match.group(1)

    data_formatada = None
    date_match = re.search(r'Date:\s+(.+)', diff_text)
    if date_match:
        date_str = date_match.group(1).strip()
        for fmt in ("%a %b %d %H:%M:%S %Y", "%Y-%m-%d"):
            try:
                clean = re.sub(r'\s+[-+]\d{4}$', '', date_str)
                dt = datetime.strptime(clean, fmt)
                data_formatada = dt.strftime("%d/%m/%Y")
                break
            except Exception:
                continue
    if not data_formatada:
        m = re.search(r'diff_commits_(\d{4})_(\d{2})_(\d{2})', filename)
        if m:
            data_formatada = f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
        else:
            data_formatada = datetime.now().strftime("%d/%m/%Y")

    project_match = re.search(r'Project:\s+(.+)', diff_text)
    projeto = project_match.group(1).strip() if project_match else ""

    autor_match = re.search(r'Author:\s+(.+?)\s*<', diff_text)
    autor = autor_match.group(1).strip() if autor_match else ""

    return sha, data_formatada, projeto, autor


def _update_env(key: str, value: str):
    """Persist an environment variable to the local .env file and the persistent config.json,
    then update the current process.
    """
    # 1. Atualiza .env local se possivel (desenvolvimento local)
    env_path = ".env"
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass # Ignora erros se .env no container for read-only
        
    # 2. Atualiza no processo atual
    os.environ[key] = value

    # 3. Salva no arquivo de configuracao persistente (/data/config_persistente.json no Docker)
    caminho_persistente = _obter_caminho_config_persistente()
    config_data = {}
    if os.path.exists(caminho_persistente):
        try:
            with open(caminho_persistente, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass
    config_data[key] = value
    try:
        with open(caminho_persistente, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar configuracao persistente em {caminho_persistente}: {e}")


def _injetar_status_envio(commit_id: str, atividades: list, db: Session) -> list:
    historico = db.query(models.Historico).filter_by(commit_id=commit_id).all()
    envios_por_titulo = {}
    for h in historico:
        envios_por_titulo[h.titulo] = envios_por_titulo.get(h.titulo, 0) + 1
        
    for atv in atividades:
        titulo = atv.get("titulo", "")
        if envios_por_titulo.get(titulo, 0) > 0:
            atv["enviado"] = True
            envios_por_titulo[titulo] -= 1
        else:
            atv["enviado"] = False
    return atividades



# ─── Endpoints: Commits ─────────────────────────────────────────────────────

@app.get("/commits")
def listar_commits(db: Session = Depends(get_db)):
    """List all imported commits ordered by most-recently imported first.

    Returns:
        A JSON array where each element contains ``id``, ``data``,
        ``projeto``, ``autor``, ``mensagem``, ``importado_em``, ``analisado``,
        and activities billing metrics.
    """
    commits = db.query(models.Commit).order_by(models.Commit.importado_em.desc()).all()
    result = []
    for c in commits:
        analise = db.query(models.Analise).filter_by(commit_id=c.id).first()
        atividades_total = 0
        atividades_enviadas = 0
        hpa_total = 0.0
        hpa_enviado = 0.0
        if analise:
            try:
                atividades = json.loads(analise.atividades_json)
                atividades_total = len(atividades)
                hpa_total = sum(float(a.get("hpa", 0) or 0) for a in atividades)
                
                historicos = db.query(models.Historico).filter_by(commit_id=c.id).all()
                envios_por_titulo = {}
                for h in historicos:
                    envios_por_titulo[h.titulo] = envios_por_titulo.get(h.titulo, 0) + 1
                
                for a in atividades:
                    titulo = a.get("titulo", "")
                    hpa = float(a.get("hpa", 0) or 0)
                    if envios_por_titulo.get(titulo, 0) > 0:
                        atividades_enviadas += 1
                        hpa_enviado += hpa
                        envios_por_titulo[titulo] -= 1
            except Exception:
                pass
        
        diff_preview = ""
        if c.diff_raw:
            marker = "--- DIFF COMEÇA AQUI ---"
            idx = c.diff_raw.find(marker)
            if idx != -1:
                raw = c.diff_raw[idx + len(marker):].strip()
                lines = [l for l in raw.split('\n')
                         if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))][:4]
                diff_preview = '\n'.join(lines)

        result.append({
            "id": c.id,
            "data": c.data,
            "projeto": c.projeto,
            "autor": c.autor,
            "mensagem": c.mensagem,
            "importado_em": c.importado_em,
            "analisado": analise is not None,
            "atividades_total": atividades_total,
            "atividades_enviadas": atividades_enviadas,
            "hpa_total": hpa_total,
            "hpa_enviado": hpa_enviado,
            "diff_preview": diff_preview,
        })
    return result


@app.post("/commits/importar", status_code=201)
def importar_commit(req: ImportarRequest, db: Session = Depends(get_db)):
    """Import a GitLab commit into the local database.

    Fetches commit metadata and the raw diff from GitLab using the provided
    credentials.  If the commit (matched by full or 8-character short SHA)
    already exists, returns early without creating a duplicate.

    Returns:
        ``{"id": "<full-sha>", "ja_existia": false}`` on successful import,
        or ``{"id": "<full-sha>", "ja_existia": true}`` when the commit was
        already present.

    Raises:
        HTTPException: 400 when GitLab metadata or diff retrieval fails.
    """
    cfg = obter_config_valores()
    
    gitlab_url = (req.gitlab_url or "").strip() or cfg.get("GITLAB_URL")
    token = (req.token or "").strip() or cfg.get("GITLAB_TOKEN")
    project_path = (req.project_path or "").strip()

    commit_hash = req.commit_hash.strip()
    # Tenta extrair da URL completa do GitLab: https://gitlab.exemplo.com/grupo/projeto/-/commit/ee91a8e2...
    url_match = re.search(r'(https?://[^/]+)/(.+?)/(?:-/)?commit/([0-9a-fA-F]{6,64})', commit_hash)
    if url_match:
        url_extracted = url_match.group(1)
        project_extracted = url_match.group(2)
        sha_extracted = url_match.group(3)
        commit_hash = sha_extracted
        if not gitlab_url:
            gitlab_url = url_extracted
        if not project_path:
            project_path = project_extracted
    else:
        # Fallback para extração simples de SHA caso venha algo como /commit/sha no final
        sha_match = re.search(r'/commit/([0-9a-fA-F]{6,64})', commit_hash)
        if sha_match:
            commit_hash = sha_match.group(1)

    if not gitlab_url or not token or not project_path:
        raise HTTPException(
            status_code=400,
            detail="Forneça a URL completa do commit GitLab (ex: https://gitlab.empresa.com/grupo/projeto/-/commit/abc123) ou informe o projeto manualmente"
        )

    # Verifica se já existe
    existing = db.query(models.Commit).filter_by(id=commit_hash).first()
    if not existing:
        # Tenta match por SHA curto (8 chars)
        short = commit_hash[:8]
        existing = db.query(models.Commit).filter(models.Commit.id.like(f"{short}%")).first()
    if existing:
        return {"id": existing.id, "ja_existia": True}

    try:
        meta = obter_metadados_commit(gitlab_url, token, project_path, commit_hash)
        diff_text = obter_diff_commit(gitlab_url, token, project_path, commit_hash)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    sha_full = meta.get("id") or commit_hash
    committed_date_str = meta.get("committed_date") or meta.get("created_at") or ""
    data_formatada = datetime.now().strftime("%d/%m/%Y")
    if committed_date_str:
        try:
            clean = re.sub(r'(\.\d+)?([+-]\d{2}:?\d{2}|Z)$', '', committed_date_str)
            dt = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S")
            data_formatada = dt.strftime("%d/%m/%Y")
        except Exception:
            pass

    mensagem = meta.get("message", meta.get("title", ""))
    # Adiciona cabeçalho de metadados ao diff (mantém compatibilidade com evidence_generator)
    diff_com_header = "\n".join([
        f"Data do commit: {data_formatada} | Diff do commit {sha_full[:8]}",
        f"commit {sha_full}",
        f"Author: {meta.get('author_name', '')} <{meta.get('author_email', '')}>",
        f"Date: {committed_date_str}",
        f"Project: {project_path}",
        f"Subject: {meta.get('title', '')}",
        "",
        mensagem,
        "",
        "--- DIFF COMEÇA AQUI ---",
        "",
        diff_text,
    ])

    commit_obj = models.Commit(
        id=sha_full,
        data=data_formatada,
        projeto=project_path,
        autor=meta.get("author_name", ""),
        mensagem=mensagem,
        diff_raw=diff_com_header,
        importado_em=datetime.now().isoformat(),
    )
    db.add(commit_obj)
    db.commit()
    return {"id": sha_full, "ja_existia": False}


@app.get("/commits/{sha}")
def obter_commit(sha: str, db: Session = Depends(get_db)):
    """Retrieve a single commit by full or short SHA prefix.

    Returns:
        A JSON object with ``id``, ``data``, ``projeto``, ``autor``,
        ``mensagem``, ``diff_raw``, ``importado_em``, and activities billing metrics.

    Raises:
        HTTPException: 404 when no commit matches the given SHA prefix.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    atividades_total = 0
    atividades_enviadas = 0
    hpa_total = 0.0
    hpa_enviado = 0.0
    if analise:
        try:
            atividades = json.loads(analise.atividades_json)
            atividades_total = len(atividades)
            hpa_total = sum(float(a.get("hpa", 0) or 0) for a in atividades)
            
            historicos = db.query(models.Historico).filter_by(commit_id=commit.id).all()
            envios_por_titulo = {}
            for h in historicos:
                envios_por_titulo[h.titulo] = envios_por_titulo.get(h.titulo, 0) + 1
            
            for a in atividades:
                titulo = a.get("titulo", "")
                hpa = float(a.get("hpa", 0) or 0)
                if envios_por_titulo.get(titulo, 0) > 0:
                    atividades_enviadas += 1
                    hpa_enviado += hpa
                    envios_por_titulo[titulo] -= 1
        except Exception:
            pass

    return {
        "id": commit.id,
        "data": commit.data,
        "projeto": commit.projeto,
        "autor": commit.autor,
        "mensagem": commit.mensagem,
        "diff_raw": commit.diff_raw,
        "importado_em": commit.importado_em,
        "analisado": analise is not None,
        "atividades_total": atividades_total,
        "atividades_enviadas": atividades_enviadas,
        "hpa_total": hpa_total,
        "hpa_enviado": hpa_enviado,
    }


@app.patch("/commits/{sha}")
def atualizar_commit(sha: str, req: AtualizarCommitRequest, db: Session = Depends(get_db)):
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    if req.data is not None:
        commit.data = req.data
    if req.projeto is not None:
        commit.projeto = req.projeto
    if req.autor is not None:
        commit.autor = req.autor
    if req.mensagem is not None:
        commit.mensagem = req.mensagem
    db.commit()
    return {"ok": True}


@app.delete("/commits/{sha}", status_code=204)
def deletar_commit(sha: str, db: Session = Depends(get_db)):
    """Delete a commit and its associated analysis by SHA prefix.

    Cascades the deletion to the related Analise record before removing the
    commit itself.

    Raises:
        HTTPException: 404 when no commit matches the given SHA prefix.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    db.query(models.Analise).filter_by(commit_id=commit.id).delete()
    db.delete(commit)
    db.commit()


# ─── Endpoints: Análise ─────────────────────────────────────────────────────

@app.get("/commits/{sha}/analise")
def obter_analise(sha: str, db: Session = Depends(get_db)):
    """Retrieve the Gemini analysis for a commit.

    Returns:
        A JSON object with ``commit_id``, ``complexidade_global``,
        ``atividades`` (deserialized list with 'enviado' status), and ``analisado_em``.

    Raises:
        HTTPException: 404 when the commit or its analysis is not found.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
        
    atividades = json.loads(analise.atividades_json)
    atividades = _injetar_status_envio(commit.id, atividades, db)
    
    return {
        "commit_id": analise.commit_id,
        "complexidade_global": analise.complexidade_global,
        "atividades": atividades,
        "analisado_em": analise.analisado_em,
    }


@app.post("/commits/{sha}/analisar")
def analisar_commit(sha: str, req: AnalisarRequest, db: Session = Depends(get_db)):
    """Queue (or return cached) Gemini analysis for a commit diff.

    If a cached analysis exists and ``req.forcar`` is ``False``, returns the
    result immediately. Otherwise queues an async Celery task and returns
    ``{"task_id": ..., "status": "queued"}`` for the client to poll via
    ``GET /task/{task_id}``.

    Raises:
        HTTPException: 404 when the commit is not found.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")

    analise_existente = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if analise_existente and not req.forcar:
        atividades = json.loads(analise_existente.atividades_json)
        atividades = _injetar_status_envio(commit.id, atividades, db)
        return {
            "commit_id": analise_existente.commit_id,
            "complexidade_global": analise_existente.complexidade_global,
            "atividades": atividades,
            "analisado_em": analise_existente.analisado_em,
        }

    task = analisar_commit_task.delay(commit.id, commit.diff_raw, req.forcar)
    return {"task_id": task.id, "status": "queued"}


@app.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Return the current state of a Celery background task.

    Returns a JSON object with ``task_id``, ``status`` (PENDING / STARTED /
    PROGRESS / SUCCESS / FAILURE), ``result`` (on SUCCESS), and ``error``
    (on FAILURE).
    """
    result = AsyncResult(task_id, app=celery_app)
    payload: dict = {"task_id": task_id, "status": result.state}
    if result.state == "SUCCESS":
        payload["result"] = result.result
    elif result.state == "FAILURE":
        payload["error"] = str(result.result)
    elif result.state == "PROGRESS":
        payload["meta"] = result.info or {}
    return payload


@app.put("/commits/{sha}/atividades")
def atualizar_atividades(sha: str, req: AtualizarAtividadesRequest, db: Session = Depends(get_db)):
    """Overwrite the activity list (and optionally global complexity) of an existing analysis.

    Replaces the stored ``atividades_json`` with the provided list.
    Optionally updates ``complexidade_global`` when the field is included in
    the request body.

    Returns:
        ``{"ok": true}`` on success.

    Raises:
        HTTPException: 404 when the commit or its analysis is not found.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada. Execute /analisar primeiro.")

    analise.atividades_json = json.dumps(req.atividades, ensure_ascii=False)
    if req.complexidade_global is not None:
        analise.complexidade_global = req.complexidade_global
    db.commit()
    return {"ok": True}


# ─── Endpoints: Envio ao Munka ──────────────────────────────────────────────

@app.post("/commits/{sha}/enviar")
def enviar_atividade(sha: str, req: EnviarRequest, db: Session = Depends(get_db)):
    """Submit a single activity from a commit's analysis to the Munka system.

    Generates a PNG diff image and HTML evidence snippet, then drives the
    Munka web UI via Playwright (``MunkaAutomation``) to create and
    homologate the activity.  If Munka detects a duplicate, the submission
    is skipped and flagged without raising an error.  A successful
    submission is recorded in the ``Historico`` table.

    Returns:
        A JSON object with ``ok`` (``true``), ``pulada_duplicada`` (boolean),
        and ``mensagem`` describing the outcome.

    Raises:
        HTTPException: 400 when the commit/analysis is missing, the activity
            index is out of range, or Munka credentials are not configured.
        HTTPException: 500 when diff image generation or Playwright
            automation fails.
    """
    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    atividades = json.loads(analise.atividades_json)
    if req.atividade_idx < 0 or req.atividade_idx >= len(atividades):
        raise HTTPException(status_code=400, detail="Índice de atividade inválido")

    atividade = atividades[req.atividade_idx]

    cfg = obter_config_valores()
    user = cfg.get("MUNKA_USER")
    password = cfg.get("MUNKA_PASS")
    if not user or not password:
        raise HTTPException(status_code=400, detail="Credenciais MUNKA_USER/MUNKA_PASS não configuradas")

    # Geração de imagem removida — evidencia via HTML

    gitlab_base = req.gitlab_url or cfg.get("GITLAB_URL", "")
    if gitlab_base:
        # Monta URL completa: base + caminho do projeto + /commit/SHA
        gitlab_url_commit = f"{gitlab_base.rstrip('/')}/{(commit.projeto or '').strip('/')}/commit/{commit.id}"
    else:
        gitlab_url_commit = commit.id

    commit_metadata = {
        "data_inicio": f"{commit.data} 08:00",
        "data_fim": f"{commit.data} 18:00",
        "sha": commit.id,
        "url": gitlab_url_commit,
    }
    dev_profile = {
        "cargo": req.cargo,
        "nivel": req.nivel,
        "responsavel": req.responsavel,
        "status_id": req.status_id,
    }

    prefixes_media = ("57", "58", "59", "60", "61")
    atividade["is_media"] = str(atividade.get("codigo_id", "")).startswith(prefixes_media)

    # Gera evidência HTML se não existir na atividade
    evidencia_html = atividade.get("evidencia_html")
    if not evidencia_html:
        complexity = "Média" if atividade.get("is_media") else "Baixa/Única"
        try:
            evidencia_html = gerar_html_evidencia(
                atividade,
                commit_metadata,
                commit.diff_raw,
                system_name=req.projeto,
                complexity=complexity,
            )
        except Exception:
            evidencia_html = ""

    try:
        auto = MunkaAutomation(username=user, password=password, munka_url=cfg.get("MUNKA_URL", ""), headless=True)
        resultado = auto.cadastrar_e_homologar_completo(
            task_data=atividade,
            image_path=image_path,
            product_name=req.produto,
            project_name=req.projeto,
            dev_profile=dev_profile,
            commit_metadata=commit_metadata,
            custom_evidence_html=evidencia_html,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no Playwright: {e}")
    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass

    pulada = resultado == "PULADA_DUPLICADA"

    if not pulada:
        hist_status = "Pendente" if req.status_id == "17" else "Homologada"
        hist = models.Historico(
            commit_id=commit.id,
            titulo=atividade.get("titulo", ""),
            codigo=atividade.get("codigo_id", ""),
            hpa=float(atividade.get("hpa", 0)),
            status=hist_status,
            enviado_em=datetime.now().isoformat(),
        )
        db.add(hist)
        db.commit()

    return {
        "ok": True,
        "pulada_duplicada": pulada,
        "mensagem": "Pulada: já cadastrada" if pulada else "Enviado e Homologado com sucesso!",
    }


@app.get("/commits/{sha}/enviar-stream")
def enviar_atividade_stream(sha: str, atividade_idx: int, headless: bool = True, db: Session = Depends(get_db)):
    import time
    from fastapi.responses import StreamingResponse

    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{sha}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")

    atividades = json.loads(analise.atividades_json)
    if atividade_idx < 0 or atividade_idx >= len(atividades):
        raise HTTPException(status_code=400, detail="Índice de atividade inválido")

    cfg = obter_config_valores()
    if not cfg.get("MUNKA_USER") or not cfg.get("MUNKA_PASS"):
        raise HTTPException(status_code=400, detail="Credenciais MUNKA_USER/MUNKA_PASS não configuradas")

    task = enviar_atividade_task.delay(commit.id, atividade_idx, cfg)
    task_id = task.id

    def sse_generator():
        last_log_idx = 0
        while True:
            result = AsyncResult(task_id, app=celery_app)
            state = result.state
            meta = result.info if isinstance(result.info, dict) else {}

            logs = meta.get("logs", [])
            for log in logs[last_log_idx:]:
                last_log_idx += 1
                yield f"event: log\ndata: {json.dumps({'message': log}, ensure_ascii=False)}\n\n"

            if state == "SUCCESS":
                res = result.result or {}
                resultado = res.get("resultado", "ENVIADO")
                remaining = (res.get("logs") or [])[last_log_idx:]
                for log in remaining:
                    yield f"event: log\ndata: {json.dumps({'message': log}, ensure_ascii=False)}\n\n"
                yield f"event: success\ndata: {json.dumps({'message': resultado}, ensure_ascii=False)}\n\n"
                break
            elif state == "FAILURE":
                yield f"event: error\ndata: {json.dumps({'message': str(result.result)}, ensure_ascii=False)}\n\n"
                break

            time.sleep(0.5)
            yield ": keep-alive\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


# ─── Endpoints: Histórico ────────────────────────────────────────────────────

@app.get("/historico")
def listar_historico(db: Session = Depends(get_db)):
    """List all successfully submitted activities ordered by most-recently sent first.

    Returns:
        A JSON array where each element contains ``id``, ``commit_id``,
        ``titulo``, ``codigo``, ``hpa``, ``status``, and ``enviado_em``.
    """
    itens = db.query(models.Historico).order_by(models.Historico.enviado_em.desc()).all()
    return [
        {
            "id": h.id,
            "commit_id": h.commit_id,
            "titulo": h.titulo,
            "codigo": h.codigo,
            "hpa": h.hpa,
            "status": h.status,
            "enviado_em": h.enviado_em,
        }
        for h in itens
    ]


# ─── Endpoints: Configuração ────────────────────────────────────────────────

@app.get("/config")
def obter_config():
    """Return the current application configuration with sensitive values masked.

    API keys and passwords are replaced with ``"***"`` when set, or an
    empty string when absent.  A ``status`` sub-object provides boolean
    flags indicating whether each service is fully configured.

    Returns:
        A JSON object with config values.
    """
    cfg = obter_config_valores()
    return {
        "gemini_api_key": "***" if cfg.get("GEMINI_API_KEY") else "",
        "munka_url": cfg.get("MUNKA_URL", ""),
        "munka_user": cfg.get("MUNKA_USER", ""),
        "munka_pass": "***" if cfg.get("MUNKA_PASS") else "",
        "gitlab_token": "***" if cfg.get("GITLAB_TOKEN") else "",
        "gitlab_url": cfg.get("GITLAB_URL", ""),
        "munka_cargo": cfg.get("MUNKA_CARGO", "9"),
        "munka_nivel": cfg.get("MUNKA_NIVEL", "3"),
        "munka_responsavel": cfg.get("MUNKA_RESPONSAVEL", ""),
        "munka_produto": cfg.get("MUNKA_PRODUTO", "[DESENV] MUNKA"),
        "munka_projeto": cfg.get("MUNKA_PROJETO", "MUNKA Multicontrato"),
        "munka_status_id": cfg.get("MUNKA_STATUS_ID", "17"),
        "status": {
            "gemini": bool(cfg.get("GEMINI_API_KEY")),
            "munka": bool(cfg.get("MUNKA_USER") and cfg.get("MUNKA_PASS")),
            "gitlab": bool(cfg.get("GITLAB_TOKEN")),
        },
    }


@app.post("/config")
def salvar_config(req: ConfiguracaoRequest):
    """Save application configuration values to the .env file and current process environment.

    Only fields that are explicitly provided (non-``None``, non-empty string)
    are written.  Omitted fields are left unchanged.

    Returns:
        ``{"ok": true}`` on success.
    """
    mapping = {
        "gemini_api_key": "GEMINI_API_KEY",
        "munka_url": "MUNKA_URL",
        "munka_user": "MUNKA_USER",
        "munka_pass": "MUNKA_PASS",
        "gitlab_token": "GITLAB_TOKEN",
        "gitlab_url": "GITLAB_URL",
        "munka_cargo": "MUNKA_CARGO",
        "munka_nivel": "MUNKA_NIVEL",
        "munka_responsavel": "MUNKA_RESPONSAVEL",
        "munka_produto": "MUNKA_PRODUTO",
        "munka_projeto": "MUNKA_PROJETO",
        "munka_status_id": "MUNKA_STATUS_ID",
    }
    for field, env_key in mapping.items():
        value = getattr(req, field)
        if value is not None:
            if field in ("gemini_api_key", "munka_pass", "gitlab_token"):
                if value != "" and value != "***":
                    _update_env(env_key, value)
            else:
                _update_env(env_key, value)
    return {"ok": True}


# ─── Endpoints: Fila de Tarefas ─────────────────────────────────────────────

@app.post("/fila/analise", status_code=201)
def enfileirar_analise(req: FilaAnaliseRequest, db: Session = Depends(get_db)):
    jobs_enfileirados = []
    for commit_id in req.commit_ids:
        commit = db.query(models.Commit).filter(models.Commit.id.like(f"{commit_id}%")).first()
        if not commit:
            continue
        
        job = models.Fila(
            tipo="analise",
            commit_id=commit.id,
            modelo=req.modelo,
            status="pending",
            criado_em=datetime.now().isoformat()
        )
        db.add(job)
        db.flush()

        task = analisar_commit_task.delay(
            commit.id,
            commit.diff_raw,
            True,  # força re-análise
            req.modelo,
            job.id
        )
        job.task_id = task.id
        jobs_enfileirados.append(job.id)
    
    db.commit()
    return {"ok": True, "job_ids": jobs_enfileirados}


@app.post("/fila/envio", status_code=201)
def enfileirar_envio(req: FilaEnvioRequest, db: Session = Depends(get_db)):
    # 1. Limite de concorrência local de 5 envios simultâneos
    running_jobs = db.query(models.Fila).filter(
        models.Fila.tipo == "envio",
        models.Fila.status == "running"
    ).count()
    if running_jobs >= 5:
        raise HTTPException(
            status_code=429,
            detail="Fila de envios cheia. Máximo de 5 envios simultâneos permitidos."
        )

    commit = db.query(models.Commit).filter(models.Commit.id.like(f"{req.commit_id}%")).first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit não encontrado")
    
    analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Análise do commit não encontrada")

    atividades = json.loads(analise.atividades_json)
    if req.atividade_idx < 0 or req.atividade_idx >= len(atividades):
        raise HTTPException(status_code=400, detail="Índice de atividade inválido")

    job = models.Fila(
        tipo="envio",
        commit_id=commit.id,
        atividade_idx=req.atividade_idx,
        status="pending",
        criado_em=datetime.now().isoformat()
    )
    db.add(job)
    db.flush()

    cfg = obter_config_valores()
    if not cfg.get("MUNKA_USER") or not cfg.get("MUNKA_PASS"):
        raise HTTPException(status_code=400, detail="Credenciais MUNKA_USER/MUNKA_PASS não configuradas")

    task = enviar_atividade_task.delay(commit.id, req.atividade_idx, cfg, job.id)
    job.task_id = task.id
    db.commit()

    return {"ok": True, "job_id": job.id}


@app.get("/fila")
def listar_fila(db: Session = Depends(get_db)):
    jobs = db.query(models.Fila).order_by(models.Fila.criado_em.desc()).all()
    resultado = []
    for j in jobs:
        commit = db.query(models.Commit).filter_by(id=j.commit_id).first()
        mensagem = commit.mensagem if commit else "(sem commit)"
        
        titulo_atividade = None
        if j.tipo == "envio" and commit:
            analise = db.query(models.Analise).filter_by(commit_id=commit.id).first()
            if analise:
                try:
                    atividades = json.loads(analise.atividades_json)
                    if j.atividade_idx is not None and 0 <= j.atividade_idx < len(atividades):
                        titulo_atividade = atividades[j.atividade_idx].get("titulo")
                except:
                    pass

        resultado.append({
            "id": j.id,
            "tipo": j.tipo,
            "commit_id": j.commit_id,
            "atividade_idx": j.atividade_idx,
            "modelo": j.modelo,
            "status": j.status,
            "task_id": j.task_id,
            "resultado": json.loads(j.resultado) if j.resultado else None,
            "criado_em": j.criado_em,
            "concluido_em": j.concluido_em,
            "commit_mensagem": mensagem,
            "titulo_atividade": titulo_atividade
        })
    return resultado


@app.delete("/fila/{job_id}", status_code=204)
def remover_job_fila(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Fila).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    if job.status not in ("pending", "done", "error"):
        if job.task_id:
            try:
                celery_app.control.revoke(job.task_id, terminate=True)
            except:
                pass
            
    db.delete(job)
    db.commit()





