import json
import os
import time
from datetime import datetime, timezone
import redis

from dotenv import load_dotenv

load_dotenv()

from celery_app import celery_app

redis_client = redis.Redis.from_url(
    os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
)


from celery.exceptions import Retry


@celery_app.task(bind=True, name="tasks.analisar_commit")
def analisar_commit_task(
    self,
    commit_id: str,
    diff_raw: str,
    forcar: bool = False,
    modelo: str = "Gemini 2.5 Flash Lite",
    fila_id: int = None,
):
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
                analise_existente = (
                    db.query(models.Analise).filter_by(commit_id=commit_id).first()
                )
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
            analise_existente = (
                db.query(models.Analise).filter_by(commit_id=commit_id).first()
            )
            if analise_existente:
                analise_existente.complexidade_global = relatorio.complexidade_global
                analise_existente.atividades_json = json.dumps(
                    atividades, ensure_ascii=False
                )
                analise_existente.analisado_em = analisado_em
            else:
                db.add(
                    models.Analise(
                        commit_id=commit_id,
                        complexidade_global=relatorio.complexidade_global,
                        atividades_json=json.dumps(atividades, ensure_ascii=False),
                        analisado_em=analisado_em,
                    )
                )
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
                    try:
                        hist_log = models.FilaLogsHistorico(
                            fila_id=f.id,
                            tipo=f.tipo,
                            commit_id=f.commit_id,
                            atividade_idx=None,
                            tentativa=self.request.retries + 1,
                            status="done",
                            logs=json.dumps([f"Análise do commit concluída com sucesso via modelo '{modelo}'."], ensure_ascii=False),
                            criado_em=datetime.now().isoformat(),
                        )
                        db_f.add(hist_log)
                    except Exception as ex_log:
                        print(f"Erro ao salvar logs historicos no sucesso de analise: {ex_log}", flush=True)
                    db_f.commit()
        return res
    except Exception as e:
        import re
        msg_erro = str(e)
        is_rate_limit = any(k in msg_erro.lower() for k in ["503", "429", "overloaded", "demand", "quota", "exhausted", "limit"])

        if is_rate_limit and self.request.retries < 2:
            default_limit = 60 if self.request.retries == 0 else 120
            countdown = default_limit

            # Tenta extrair o delay recomendado pelo erro do Gemini
            match_retry = re.search(r"retry\s+in\s+([\d\.]+)\s*s", msg_erro, re.IGNORECASE)
            if match_retry:
                try:
                    countdown = min(int(float(match_retry.group(1))) + 2, default_limit)
                except ValueError:
                    pass
            else:
                match_delay = re.search(r"retryDelay':\s*'(\d+)\s*s'", msg_erro, re.IGNORECASE)
                if match_delay:
                    try:
                        countdown = min(int(match_delay.group(1)) + 2, default_limit)
                    except ValueError:
                        pass

            # Garante no mínimo 10 segundos para dar tempo de liberar a cota
            countdown = max(countdown, 10)

            if fila_id:
                with SessionLocal() as db_f:
                    f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                    if f:
                        # Mantém status 'running', mas atualiza resultado com info de retry
                        info_tentativa = {
                            "status": "retrying",
                            "error": msg_erro,
                            "retry_attempt": self.request.retries + 1,
                            "countdown": countdown,
                            "mensagem": f"Limite de requisições atingido. Tentando novamente em {countdown} segundos..."
                        }
                        f.resultado = json.dumps(info_tentativa, ensure_ascii=False)
                        try:
                            hist_log = models.FilaLogsHistorico(
                                fila_id=f.id,
                                tipo=f.tipo,
                                commit_id=f.commit_id,
                                atividade_idx=None,
                                tentativa=self.request.retries + 1,
                                status="retrying",
                                logs=json.dumps([f"Limite de requisições atingido. Tentando novamente em {countdown}s: {msg_erro}"], ensure_ascii=False),
                                criado_em=datetime.now().isoformat(),
                            )
                            db_f.add(hist_log)
                        except Exception as ex_log:
                            print(f"Erro ao salvar logs historicos no retry de analise: {ex_log}", flush=True)
                        db_f.commit()

            raise self.retry(exc=e, countdown=countdown)

        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps({"error": str(e)}, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    try:
                        hist_log = models.FilaLogsHistorico(
                            fila_id=f.id,
                            tipo=f.tipo,
                            commit_id=f.commit_id,
                            atividade_idx=None,
                            tentativa=self.request.retries + 1,
                            status="error",
                            logs=json.dumps([f"Erro na análise do commit: {str(e)}"], ensure_ascii=False),
                            criado_em=datetime.now().isoformat(),
                        )
                        db_f.add(hist_log)
                    except Exception as ex_log:
                        print(f"Erro ao salvar logs historicos na falha de analise: {ex_log}", flush=True)
                    db_f.commit()
        raise e


@celery_app.task(bind=True, name="tasks.enviar_atividade")
def enviar_atividade_task(
    self, commit_id: str, atividade_idx: int, cfg: dict, fila_id: int = None
):
    from database import SessionLocal
    import models
    from evidence_generator import gerar_html_evidencia
    from automation import MunkaAutomation

    logs = []

    def log(msg: str):
        logs.append(msg)
        self.update_state(state="PROGRESS", meta={"logs": logs})
        if fila_id:
            try:
                with SessionLocal() as db_log:
                    fj = db_log.query(models.Fila).filter_by(id=fila_id).first()
                    if fj and fj.status == "running":
                        fj.resultado = json.dumps({"resultado": "RUNNING", "logs": logs}, ensure_ascii=False)
                        db_log.commit()
            except Exception:
                pass

    if fila_id:
        with SessionLocal() as db:
            fila_job = db.query(models.Fila).filter_by(id=fila_id).first()
            if fila_job:
                fila_job.status = "running"
                fila_job.task_id = self.request.id
                fila_job.resultado = json.dumps({"resultado": "RUNNING", "logs": ["Iniciando automação..."]}, ensure_ascii=False)
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

        hora_inicio = cfg.get("MUNKA_DATA_INICIO", "08:00")
        hora_fim = cfg.get("MUNKA_DATA_FIM", "18:00")
        data_inicio_val = hora_inicio if " " in hora_inicio else f"{commit_data_val} {hora_inicio}"
        data_fim_val = hora_fim if " " in hora_fim else f"{commit_data_val} {hora_fim}"

        commit_metadata = {
            "data_inicio": data_inicio_val,
            "data_fim": data_fim_val,
            "sha": commit_id,
            "url": gitlab_url_commit,
        }
        dev_profile = {
            "cargo": cfg.get("MUNKA_CARGO", "9"),
            "nivel": cfg.get("MUNKA_NIVEL", "3"),
            "responsavel": cfg.get("MUNKA_RESPONSAVEL", ""),
            "status_id": cfg.get("MUNKA_STATUS_ID", "17"),
        }

        complexidade = atividade.get("complexidade")
        if complexidade:
            atividade["is_media"] = (complexidade in ("Média", "Alta"))
        else:
            prefixes_media = ("57", "58", "59", "60", "61")
            atividade["is_media"] = str(atividade.get("codigo_id", "")).startswith(
                prefixes_media
            )

        evidencia_html = atividade.get("evidencia_html")
        if not evidencia_html:
            if complexidade:
                complexity = complexidade
            else:
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

        from backup import verificar_ping_munka, gerar_backup_json_e_sql, verificar_e_executar_auto_backup_20min

        munka_url_config = cfg.get("MUNKA_URL", "")
        log("🔍 Realizando teste de conectividade (PING) no portal Munka...")
        ping_ok, ping_msg = verificar_ping_munka(munka_url_config, timeout=6)
        if not ping_ok:
            log(f"⚠️ PING FALHOU: Portal Munka indisponível ({ping_msg}).")
            log("⏸️ Pausando a tarefa temporariamente para evitar falhas consecutivas. Testando novamete em 30s...")
            res = {"resultado": "PAUSED_PING_FAILED", "logs": logs}
            if fila_id:
                with SessionLocal() as db_f:
                    f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                    if f:
                        f.status = "pending"
                        f.resultado = json.dumps(res, ensure_ascii=False)
                        try:
                            hist_log = models.FilaLogsHistorico(
                                fila_id=f.id,
                                tipo=f.tipo,
                                commit_id=f.commit_id,
                                atividade_idx=f.atividade_idx,
                                tentativa=self.request.retries + 1,
                                status="retrying",
                                logs=json.dumps(logs, ensure_ascii=False),
                                criado_em=datetime.now().isoformat(),
                            )
                            db_f.add(hist_log)
                        except Exception as ex_log:
                            print(f"Erro ao salvar logs historicos no ping retry: {ex_log}", flush=True)
                        db_f.commit()
            raise self.retry(exc=Exception(f"Portal Munka indisponível (Ping: {ping_msg})"), countdown=30, max_retries=9)

        log("✔ Portal Munka online. Iniciando automação do lançamento...")

        auto = MunkaAutomation(
            username=cfg["MUNKA_USER"],
            password=cfg["MUNKA_PASS"],
            munka_url=cfg.get("MUNKA_URL", ""),
            headless=True,
            log_callback=log,
        )
        attempt_curr = self.request.retries + 1
        log(f"Executando fluxo completo (Cadastro + Evidência) - Tentativa {attempt_curr}/10...")
        resultado, task_id = auto.cadastrar_e_homologar_completo(
            task_data=atividade,
            image_path=None,
            product_name=cfg.get("MUNKA_PRODUTO", ""),
            project_name=cfg.get("MUNKA_PROJETO", ""),
            dev_profile=dev_profile,
            commit_metadata=commit_metadata,
            custom_evidence_html=evidencia_html,
        )

        pulada = resultado == "PULADA_DUPLICADA"
        status_id = cfg.get("MUNKA_STATUS_ID", "17")
        status_map = {
            "15": "Backlog",
            "16": "Backlog Prioritário",
            "17": "Enviado ao Munka",
            "18": "Desenvolvimento",
            "20": "Homologação",
            "21": "Concluído"
        }
        if pulada:
            hist_status = "Concluído"
            tem_df = True
        else:
            hist_status = status_map.get(status_id, "Enviado ao Munka")
            tem_df = True
            if "Sem Data Fim" in str(hist_status) or "Incompleta" in str(hist_status):
                tem_df = False

        with SessionLocal() as db:
            hist = (
                db.query(models.Historico)
                .filter_by(commit_id=commit_id, titulo=atividade.get("titulo", ""))
                .first()
            )

            if hist:
                hist.status = hist_status
                hist.tem_data_fim = tem_df
                hist.enviado_em = datetime.now().isoformat()
                if atividade.get("codigo_id"):
                    hist.codigo = atividade.get("codigo_id")
                if atividade.get("hpa"):
                    hist.hpa = float(atividade.get("hpa"))
            else:
                hist = models.Historico(
                    commit_id=commit_id,
                    titulo=atividade.get("titulo", ""),
                    codigo=atividade.get("codigo_id", ""),
                    hpa=float(atividade.get("hpa", 0)),
                    status=hist_status,
                    enviado_em=datetime.now().isoformat(),
                    tem_data_fim=tem_df,
                )
                db.add(hist)

            analise = db.query(models.Analise).filter_by(commit_id=commit_id).first()
            if analise and analise.atividades_json:
                try:
                    atvs = json.loads(analise.atividades_json)
                    for a in atvs:
                        if a.get("titulo") == atividade.get("titulo"):
                            a["enviado"] = True
                    analise.atividades_json = json.dumps(atvs, ensure_ascii=False)
                except Exception:
                    pass

            db.commit()

        task_url = None
        if task_id:
            munka_url = cfg.get("MUNKA_URL", "").rstrip("/")
            if munka_url:
                task_url = f"{munka_url}/tarefamodelview/show/{task_id}"

        res = {"resultado": resultado, "task_id": task_id, "task_url": task_url, "logs": logs}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "done"
                    f.resultado = json.dumps(res, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    try:
                        hist_log = models.FilaLogsHistorico(
                            fila_id=f.id,
                            tipo=f.tipo,
                            commit_id=f.commit_id,
                            atividade_idx=f.atividade_idx,
                            tentativa=self.request.retries + 1,
                            status="done",
                            logs=json.dumps(logs, ensure_ascii=False),
                            criado_em=datetime.now().isoformat(),
                        )
                        db_f.add(hist_log)
                    except Exception as ex_log:
                        print(f"Erro ao salvar logs historicos no sucesso: {ex_log}", flush=True)
                    db_f.commit()

        try:
            verificar_e_executar_auto_backup_20min()
        except Exception as eb:
            log(f"Auto-save backup notice: {eb}")

        return res
    except Retry:
        raise
    except Exception as e:
        retry_num = self.request.retries
        max_retries = 9
        delays = [10, 15, 20, 30, 45, 60, 90, 120, 180]
        if retry_num < max_retries:
            next_attempt = retry_num + 2
            countdown = delays[retry_num] if retry_num < len(delays) else 180
            log(f"⚠️ Falha na tentativa {retry_num + 1}/{max_retries + 1}: {str(e)}")
            log(f"🔄 Reenfileirando automaticamente para tentar novamente em {countdown}s (Tentativa {next_attempt}/{max_retries + 1})...")
            res = {"resultado": "RETRYING", "logs": logs}
            if fila_id:
                with SessionLocal() as db_f:
                    f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                    if f:
                        f.status = "pending"
                        f.resultado = json.dumps(res, ensure_ascii=False)
                        try:
                            hist_log = models.FilaLogsHistorico(
                                fila_id=f.id,
                                tipo=f.tipo,
                                commit_id=f.commit_id,
                                atividade_idx=f.atividade_idx,
                                tentativa=retry_num + 1,
                                status="retrying",
                                logs=json.dumps(logs, ensure_ascii=False),
                                criado_em=datetime.now().isoformat(),
                            )
                            db_f.add(hist_log)
                        except Exception as ex_log:
                            print(f"Erro ao salvar logs historicos no retry: {ex_log}", flush=True)
                        db_f.commit()
            raise self.retry(exc=e, countdown=countdown, max_retries=max_retries)

        log(f"❌ Todas as {max_retries + 1} tentativas falharam com erro: {str(e)}")
        res = {"resultado": "ERRO", "logs": logs}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps(res, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    try:
                        hist_log = models.FilaLogsHistorico(
                            fila_id=f.id,
                            tipo=f.tipo,
                            commit_id=f.commit_id,
                            atividade_idx=f.atividade_idx,
                            tentativa=retry_num + 1,
                            status="error",
                            logs=json.dumps(logs, ensure_ascii=False),
                            criado_em=datetime.now().isoformat(),
                        )
                        db_f.add(hist_log)
                    except Exception as ex_log:
                        print(f"Erro ao salvar logs historicos na falha final: {ex_log}", flush=True)
                    db_f.commit()
        raise e


@celery_app.task(bind=True, name="tasks.verificar_lancamento")
def verificar_lancamento_task(self, target_job_id: int, fila_id: int = None):
    from database import SessionLocal
    import models
    from api import obter_config_valores
    from automation import MunkaAutomation

    logs = []

    def log(msg: str):
        logs.append(msg)
        self.update_state(state="PROGRESS", meta={"logs": logs})
        if fila_id:
            try:
                with SessionLocal() as db_log:
                    fj = db_log.query(models.Fila).filter_by(id=fila_id).first()
                    if fj and fj.status == "running":
                        fj.resultado = json.dumps({"resultado": "RUNNING", "logs": logs}, ensure_ascii=False)
                        db_log.commit()
            except Exception:
                pass

    if fila_id:
        with SessionLocal() as db:
            fila_job = db.query(models.Fila).filter_by(id=fila_id).first()
            if fila_job:
                fila_job.status = "running"
                fila_job.task_id = self.request.id
                fila_job.resultado = json.dumps({"resultado": "RUNNING", "logs": ["Iniciando automação de verificação..."]}, ensure_ascii=False)
                db.commit()

    try:
        log("🔍 Iniciando tarefa assíncrona de verificação do lançamento no portal Munka...")
        with SessionLocal() as db:
            target_job = db.query(models.Fila).filter_by(id=target_job_id).first()
            if not target_job:
                raise ValueError(f"Tarefa da fila #{target_job_id} não encontrada.")

            commit = db.query(models.Commit).filter_by(id=target_job.commit_id).first()
            analise = db.query(models.Analise).filter_by(commit_id=target_job.commit_id).first()
            if not commit or not analise:
                raise ValueError(f"Commit ou análise não encontrados para {target_job.commit_id}")

            atividades = json.loads(analise.atividades_json) if analise.atividades_json else []
            atividade = {}
            if target_job.atividade_idx is not None and 0 <= target_job.atividade_idx < len(atividades):
                atividade = atividades[target_job.atividade_idx]

            cfg = obter_config_valores()
            commit_data_val = commit.data
            hora_inicio = cfg.get("MUNKA_DATA_INICIO", "08:00")
            hora_fim = cfg.get("MUNKA_DATA_FIM", "18:00")
            data_inicio_val = hora_inicio if " " in hora_inicio else f"{commit_data_val} {hora_inicio}"
            data_fim_val = hora_fim if " " in hora_fim else f"{commit_data_val} {hora_fim}"
            codigo_id = atividade.get("codigo_id") or atividade.get("codigo") or ""

            status_map = {
                "15": "Backlog",
                "16": "Backlog Prioritário",
                "17": "Enviado ao Munka",
                "18": "Desenvolvimento",
                "20": "Homologação",
                "21": "Concluído"
            }
            status_id = cfg.get("MUNKA_STATUS_ID", "20")
            status_nome = status_map.get(status_id, "Homologação")

            expected = {
                "data_inicio": data_inicio_val,
                "data_fim": data_fim_val,
                "servico": codigo_id,
                "status": f"{status_id} ({status_nome})" if status_id else "Homologação",
                "commit": commit.id,
                "titulo": atividade.get("titulo", commit.mensagem),
            }

            task_id_or_url = None
            if target_job.resultado:
                try:
                    res_dict = json.loads(target_job.resultado)
                    task_id_or_url = res_dict.get("task_id") or res_dict.get("task_url")
                except Exception:
                    pass

            if not task_id_or_url:
                task_id_or_url = str(target_job.id)

        log("✔ Metadados esperados carregados. Iniciando browser Playwright...")
        auto = MunkaAutomation(
            username=cfg.get("MUNKA_USER", ""),
            password=cfg.get("MUNKA_PASS", ""),
            munka_url=cfg.get("MUNKA_URL", ""),
            headless=True,
            log_callback=log,
        )

        log("📋 Auditando campos no portal: Data Início, Data Fim, Serviço, Status e Commit...")
        report = auto.verificar_tarefa_portal(task_id_or_url, expected)
        report["logs"] = logs
        log(f"✅ Auditoria finalizada. Resultado geral: {'OK' if report.get('overall_ok') else 'Divergência Encontrada'}")

        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "done"
                    f.resultado = json.dumps(report, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    try:
                        hist_log = models.FilaLogsHistorico(
                            fila_id=f.id,
                            tipo=f.tipo,
                            commit_id=f.commit_id,
                            atividade_idx=f.atividade_idx,
                            tentativa=1,
                            status="done",
                            logs=json.dumps(logs, ensure_ascii=False),
                            criado_em=datetime.now().isoformat(),
                        )
                        db_f.add(hist_log)
                    except Exception:
                        pass
                    db_f.commit()

        with SessionLocal() as db_target:
            tj = db_target.query(models.Fila).filter_by(id=target_job_id).first()
            if tj:
                try:
                    res_dict = json.loads(tj.resultado) if isinstance(tj.resultado, str) else (tj.resultado or {})
                except Exception:
                    res_dict = {}
                res_dict["verificacao"] = report
                tj.resultado = json.dumps(res_dict, ensure_ascii=False)
                db_target.commit()

        return report
    except Exception as e:
        log(f"❌ Falha na verificação: {str(e)}")
        res_err = {"resultado": "ERRO", "logs": logs, "error": str(e)}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps(res_err, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        raise e


@celery_app.task(bind=True, name="tasks.corrigir_lancamento")
def corrigir_lancamento_task(self, target_job_id: int, fila_id: int = None):
    from database import SessionLocal
    import models
    from api import obter_config_valores
    from automation import MunkaAutomation

    logs = []

    def log(msg: str):
        logs.append(msg)
        self.update_state(state="PROGRESS", meta={"logs": logs})
        if fila_id:
            try:
                with SessionLocal() as db_log:
                    fj = db_log.query(models.Fila).filter_by(id=fila_id).first()
                    if fj and fj.status == "running":
                        fj.resultado = json.dumps({"resultado": "RUNNING", "logs": logs}, ensure_ascii=False)
                        db_log.commit()
            except Exception:
                pass

    if fila_id:
        with SessionLocal() as db:
            fila_job = db.query(models.Fila).filter_by(id=fila_id).first()
            if fila_job:
                fila_job.status = "running"
                fila_job.task_id = self.request.id
                fila_job.resultado = json.dumps({"resultado": "RUNNING", "logs": ["Iniciando automação de correção no portal..."]}, ensure_ascii=False)
                db.commit()

    try:
        log("⚡ Iniciando tarefa assíncrona de correção do lançamento no portal Munka...")
        with SessionLocal() as db:
            target_job = db.query(models.Fila).filter_by(id=target_job_id).first()
            if not target_job:
                raise ValueError(f"Tarefa da fila #{target_job_id} não encontrada.")

            commit = db.query(models.Commit).filter_by(id=target_job.commit_id).first()
            analise = db.query(models.Analise).filter_by(commit_id=target_job.commit_id).first()
            if not commit or not analise:
                raise ValueError(f"Commit ou análise não encontrados para {target_job.commit_id}")

            atividades = json.loads(analise.atividades_json) if analise.atividades_json else []
            atividade = {}
            if target_job.atividade_idx is not None and 0 <= target_job.atividade_idx < len(atividades):
                atividade = atividades[target_job.atividade_idx]

            cfg = obter_config_valores()
            commit_data_val = commit.data
            hora_inicio = cfg.get("MUNKA_DATA_INICIO", "08:00")
            hora_fim = cfg.get("MUNKA_DATA_FIM", "18:00")
            data_inicio_val = hora_inicio if " " in hora_inicio else f"{commit_data_val} {hora_inicio}"
            data_fim_val = hora_fim if " " in hora_fim else f"{commit_data_val} {hora_fim}"
            codigo_id = atividade.get("codigo_id") or atividade.get("codigo") or ""
            status_id = cfg.get("MUNKA_STATUS_ID", "20")

            expected = {
                "data_inicio": data_inicio_val,
                "data_fim": data_fim_val,
                "servico": codigo_id,
                "status_id": status_id,
                "commit": commit.id,
            }

            task_id_or_url = None
            if target_job.resultado:
                try:
                    res_dict = json.loads(target_job.resultado)
                    task_id_or_url = res_dict.get("task_id") or res_dict.get("task_url")
                except Exception:
                    pass

            if not task_id_or_url:
                task_id_or_url = str(target_job.id)

        auto = MunkaAutomation(
            username=cfg.get("MUNKA_USER", ""),
            password=cfg.get("MUNKA_PASS", ""),
            munka_url=cfg.get("MUNKA_URL", ""),
            headless=True,
            log_callback=log,
        )

        report = auto.corrigir_tarefa_portal(task_id_or_url, expected)
        report["logs"] = logs

        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "done"
                    f.resultado = json.dumps(report, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()

        with SessionLocal() as db_target:
            tj = db_target.query(models.Fila).filter_by(id=target_job_id).first()
            if tj:
                try:
                    res_dict = json.loads(tj.resultado) if isinstance(tj.resultado, str) else (tj.resultado or {})
                except Exception:
                    res_dict = {}
                res_dict["verificacao"] = report
                tj.resultado = json.dumps(res_dict, ensure_ascii=False)
                db_target.commit()

        return report
    except Exception as e:
        log(f"❌ Falha ao corrigir lançamento: {str(e)}")
        res_err = {"resultado": "ERRO", "logs": logs, "error": str(e)}
        if fila_id:
            with SessionLocal() as db_f:
                f = db_f.query(models.Fila).filter_by(id=fila_id).first()
                if f:
                    f.status = "error"
                    f.resultado = json.dumps(res_err, ensure_ascii=False)
                    f.concluido_em = datetime.now().isoformat()
                    db_f.commit()
        raise e


