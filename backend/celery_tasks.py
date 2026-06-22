import json
import os
from datetime import datetime
import redis

from dotenv import load_dotenv

load_dotenv()

from celery_app import celery_app

redis_client = redis.Redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))



@celery_app.task(bind=True, name="tasks.analisar_commit")
def analisar_commit_task(self, commit_id: str, diff_raw: str, forcar: bool = False, modelo: str = "Gemini 2.5 Flash", fila_id: int = None):
    from database import SessionLocal
    import models
    from gemini_service import analisar_diff

    if fila_id:
        with SessionLocal() as db:
            fila_job = db.query(models.Fila).filter_by(id=fila_id).first()
            if fila_job:
                fila_job.status = "running"
                fila_job.task_id = self.request.id
                db.commit()

    try:
        # 1. Verifica cache rápido
        if not forcar:
            with SessionLocal() as db:
                analise_existente = db.query(models.Analise).filter_by(commit_id=commit_id).first()
                if analise_existente:
                    res = {
                        "commit_id": commit_id,
                        "complexidade_global": analise_existente.complexidade_global,
                        "atividades": json.loads(analise_existente.atividades_json),
                        "analisado_em": analise_existente.analisado_em,
                    }
                    if fila_id:
                        with SessionLocal() as db_f:
                            f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                            if f:
                                f.status = "done"
                                f.resultado = json.dumps(res, ensure_ascii=False)
                                f.concluido_em = datetime.now().isoformat()
                                db_f.commit()
                    return res

        # 2. Executa a chamada da API do Gemini (fora de qualquer transação de banco de dados)
        relatorio = analisar_diff(diff_raw, modelo=modelo)
        atividades = [a.model_dump() for a in relatorio.atividades]
        analisado_em = datetime.now().isoformat()

        # 3. Salva no banco em uma nova transação rápida
        with SessionLocal() as db:
            analise_existente = db.query(models.Analise).filter_by(commit_id=commit_id).first()
            if analise_existente:
                analise_existente.complexidade_global = relatorio.complexidade_global
                analise_existente.atividades_json = json.dumps(atividades, ensure_ascii=False)
                analise_existente.analisado_em = analisado_em
            else:
                db.add(models.Analise(
                    commit_id=commit_id,
                    complexidade_global=relatorio.complexidade_global,
                    atividades_json=json.dumps(atividades, ensure_ascii=False),
                    analisado_em=analisado_em,
                ))
            db.commit()

        res = {
            "commit_id": commit_id,
            "complexidade_global": relatorio.complexidade_global,
            "atividades": atividades,
            "analisado_em": analisado_em,
        }
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "done"
                    f.resultado = json.dumps(res, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        return res
    except Exception as e:
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps({"error": str(e)}, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        raise e


@celery_app.task(bind=True, name="tasks.enviar_atividade")
def enviar_atividade_task(self, commit_id: str, atividade_idx: int, cfg: dict, fila_id: int = None):
    from database import SessionLocal
    import models
    from evidence_generator import gerar_html_evidencia
    from automation import MunkaAutomation

    logs = []

    def log(msg: str):
        logs.append(msg)
        self.update_state(state="PROGRESS", meta={"logs": logs})

    if fila_id:
        with SessionLocal() as db:
            fila_job = db.query(models.Fila).filter_by(id=fila_id).first()
            if fila_job:
                fila_job.status = "running"
                fila_job.task_id = self.request.id
                db.commit()

    try:
        # 1. Consulta rápida dos dados no banco e fecha a sessão imediatamente
        with SessionLocal() as db:
            commit = db.query(models.Commit).filter_by(id=commit_id).first()
            analise = db.query(models.Analise).filter_by(commit_id=commit_id).first()
            if not commit or not analise:
                raise ValueError(f"Commit ou análise não encontrados para {commit_id}")

            commit_data_val = commit.data
            commit_diff_raw = commit.diff_raw
            commit_projeto = commit.projeto or ""
            atividades_json = analise.atividades_json

        atividades = json.loads(atividades_json)
        atividade = dict(atividades[atividade_idx])

        gitlab_base = cfg.get("GITLAB_URL", "")
        if gitlab_base:
            # Monta URL completa: base + caminho do projeto + /commit/SHA
            gitlab_url_commit = f"{gitlab_base.rstrip('/')}/{commit_projeto.strip('/')}/commit/{commit_id}"
        else:
            gitlab_url_commit = commit_id

        commit_metadata = {
            "data_inicio": f"{commit_data_val} 08:00",
            "data_fim": f"{commit_data_val} 18:00",
            "sha": commit_id,
            "url": gitlab_url_commit,
        }
        dev_profile = {
            "cargo": cfg.get("MUNKA_CARGO", "9"),
            "nivel": cfg.get("MUNKA_NIVEL", "3"),
            "responsavel": cfg.get("MUNKA_RESPONSAVEL", ""),
            "status_id": cfg.get("MUNKA_STATUS_ID", "17"),
        }

        prefixes_media = ("57", "58", "59", "60", "61")
        atividade["is_media"] = str(atividade.get("codigo_id", "")).startswith(prefixes_media)

        evidencia_html = atividade.get("evidencia_html")
        if not evidencia_html:
            complexity = "Média" if atividade.get("is_media") else "Baixa/Única"
            try:
                evidencia_html = gerar_html_evidencia(
                    atividade,
                    commit_metadata,
                    commit_diff_raw,
                    system_name=cfg.get("MUNKA_PROJETO", ""),
                    complexity=complexity,
                )
            except Exception:
                evidencia_html = ""

        auto = MunkaAutomation(
            username=cfg["MUNKA_USER"],
            password=cfg["MUNKA_PASS"],
            munka_url=cfg.get("MUNKA_URL", ""),
            headless=True,
            log_callback=log,
        )
        log(f"Executando fluxo completo (Cadastro + Evidência)...")
        log(f"Aguardando liberação da fila de conexões do portal Munka...")
        with redis_client.lock("munka_envio_lock", timeout=180, blocking_timeout=600):
            log(f"Conexão liberada! Acessando o portal Munka...")
            resultado = auto.cadastrar_e_homologar_completo(
                task_data=atividade,
                image_path=None,
                product_name=cfg.get("MUNKA_PRODUTO", ""),
                project_name=cfg.get("MUNKA_PROJETO", ""),
                dev_profile=dev_profile,
                commit_metadata=commit_metadata,
                custom_evidence_html=evidencia_html,
            )


        pulada = resultado == "PULADA_DUPLICADA"
        if not pulada:
            status_id = cfg.get("MUNKA_STATUS_ID", "17")
            # 2. Salva o histórico em uma transação rápida e isolada
            with SessionLocal() as db:
                hist = models.Historico(
                    commit_id=commit_id,
                    titulo=atividade.get("titulo", ""),
                    codigo=atividade.get("codigo_id", ""),
                    hpa=float(atividade.get("hpa", 0)),
                    status="Pendente" if status_id == "17" else "Homologada",
                    enviado_em=datetime.now().isoformat(),
                )
                db.add(hist)
                db.commit()

        res = {"resultado": resultado, "logs": logs}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "done"
                    f.resultado = json.dumps(res, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        return res
    except Exception as e:
        logs.append(f"ERRO: {str(e)}")
        res = {"resultado": "ERRO", "logs": logs}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps(res, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        raise e

