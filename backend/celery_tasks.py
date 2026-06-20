import json
import os
import tempfile
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from celery_app import celery_app


@celery_app.task(bind=True, name="tasks.analisar_commit")
def analisar_commit_task(self, commit_id: str, diff_raw: str, forcar: bool = False):
    from database import SessionLocal
    import models
    from gemini_service import analisar_diff

    with SessionLocal() as db:
        analise_existente = db.query(models.Analise).filter_by(commit_id=commit_id).first()
        if analise_existente and not forcar:
            return {
                "commit_id": commit_id,
                "complexidade_global": analise_existente.complexidade_global,
                "atividades": json.loads(analise_existente.atividades_json),
                "analisado_em": analise_existente.analisado_em,
            }

        relatorio = analisar_diff(diff_raw)
        atividades = [a.model_dump() for a in relatorio.atividades]
        analisado_em = datetime.now().isoformat()

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

        return {
            "commit_id": commit_id,
            "complexidade_global": relatorio.complexidade_global,
            "atividades": atividades,
            "analisado_em": analisado_em,
        }


@celery_app.task(bind=True, name="tasks.enviar_atividade")
def enviar_atividade_task(self, commit_id: str, atividade_idx: int, cfg: dict):
    from database import SessionLocal
    import models
    from evidence_generator import gerar_html_evidencia
    from diff_renderer import generate_diff_image
    from automation import MunkaAutomation

    logs = []

    def log(msg: str):
        logs.append(msg)
        self.update_state(state="PROGRESS", meta={"logs": logs})

    with SessionLocal() as db:
        commit = db.query(models.Commit).filter_by(id=commit_id).first()
        analise = db.query(models.Analise).filter_by(commit_id=commit_id).first()

        atividades = json.loads(analise.atividades_json)
        atividade = dict(atividades[atividade_idx])

        gitlab_base = cfg.get("GITLAB_URL", "")
        gitlab_url_commit = f"{gitlab_base.rstrip('/')}/commit/{commit.id}" if gitlab_base else commit.id

        commit_metadata = {
            "data_inicio": f"{commit.data} 08:00",
            "data_fim": f"{commit.data} 18:00",
            "sha": commit.id,
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
                    commit.diff_raw,
                    system_name=cfg.get("MUNKA_PROJETO", ""),
                    complexity=complexity,
                )
            except Exception:
                evidencia_html = ""

        image_path = tempfile.mktemp(suffix=".png")
        try:
            generate_diff_image(commit.diff_raw, image_path)
        except Exception as e:
            log(f"Aviso: não foi possível gerar imagem de evidência: {e}")
            image_path = None

        try:
            auto = MunkaAutomation(
                username=cfg["MUNKA_USER"],
                password=cfg["MUNKA_PASS"],
                munka_url=cfg.get("MUNKA_URL", ""),
                headless=True,
                log_callback=log,
            )
            log(f"Executando fluxo completo (Cadastro + Evidência)...")
            resultado = auto.cadastrar_e_homologar_completo(
                task_data=atividade,
                image_path=image_path,
                product_name=cfg.get("MUNKA_PRODUTO", ""),
                project_name=cfg.get("MUNKA_PROJETO", ""),
                dev_profile=dev_profile,
                commit_metadata=commit_metadata,
                custom_evidence_html=evidencia_html,
            )
        finally:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception:
                    pass

        pulada = resultado == "PULADA_DUPLICADA"
        if not pulada:
            status_id = cfg.get("MUNKA_STATUS_ID", "17")
            hist = models.Historico(
                commit_id=commit.id,
                titulo=atividade.get("titulo", ""),
                codigo=atividade.get("codigo_id", ""),
                hpa=float(atividade.get("hpa", 0)),
                status="Pendente" if status_id == "17" else "Homologada",
                enviado_em=datetime.now().isoformat(),
            )
            db.add(hist)
            db.commit()

        return {"resultado": resultado, "logs": logs}
