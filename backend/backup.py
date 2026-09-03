import os
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone

import time

BACKUP_DIR = "/data/backups"
_ULTIMO_BACKUP_TIMESTAMP = 0.0


def obter_diretorio_backup() -> str:
    """Retorna o caminho do diretório de backup garantindo sua criação."""
    caminho = BACKUP_DIR if os.path.exists("/data") else "./backups"
    os.makedirs(caminho, exist_ok=True)
    return caminho


def verificar_e_executar_auto_backup_20min(forcar: bool = False) -> dict | None:
    """Gera backup automático a cada 20 minutos (1200s) quando houver movimentação ou se forcar=True."""
    global _ULTIMO_BACKUP_TIMESTAMP
    now = time.time()
    intervalo = 20 * 60  # 20 minutos

    if forcar or (now - _ULTIMO_BACKUP_TIMESTAMP >= intervalo):
        res = gerar_backup_json_e_sql()
        _ULTIMO_BACKUP_TIMESTAMP = now
        return res
    return None


def gerar_backup_json_e_sql() -> dict:
    """Gera arquivos de backup automáticos em formato JSON e SQL contendo todas as tabelas.

    Retorna um dicionário com estatísticas do backup e os caminhos dos arquivos gerados.
    """
    from database import SessionLocal
    import models

    dir_backup = obter_diretorio_backup()
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file_timestamped = os.path.join(dir_backup, f"backup_nexus_{now_str}.json")
    json_file_latest = os.path.join(dir_backup, "backup_nexus_latest.json")
    sql_file_timestamped = os.path.join(dir_backup, f"backup_nexus_{now_str}.sql")
    sql_file_latest = os.path.join(dir_backup, "backup_nexus_latest.sql")

    data_export = {
        "timestamp": datetime.now().isoformat(),
        "versao": "2.0",
        "commits": [],
        "analises": [],
        "fila": [],
        "historico": [],
        "fila_logs_historico": [],
        "git_accounts": [],
    }

    sql_lines = [
        "-- NEXUS AUTO-BACKUP SQL DUMP",
        f"-- Data de Geracao: {datetime.now().isoformat()}",
        "BEGIN TRANSACTION;",
    ]

    with SessionLocal() as db:
        # 1. Commits
        commits = db.query(models.Commit).all()
        for c in commits:
            data_export["commits"].append({
                "id": c.id,
                "data": c.data,
                "projeto": c.projeto,
                "autor": c.autor,
                "mensagem": c.mensagem,
                "diff_raw": c.diff_raw,
                "importado_em": c.importado_em,
            })
            val_id = (c.id or "").replace("'", "''")
            val_data = (c.data or "").replace("'", "''")
            val_proj = (c.projeto or "").replace("'", "''")
            val_autor = (c.autor or "").replace("'", "''")
            val_msg = (c.mensagem or "").replace("'", "''")
            val_diff = (c.diff_raw or "").replace("'", "''")
            val_imp = (c.importado_em or "").replace("'", "''")
            sql_lines.append(
                f"INSERT OR REPLACE INTO commits (id, data, projeto, autor, mensagem, diff_raw, importado_em) "
                f"VALUES ('{val_id}', '{val_data}', '{val_proj}', '{val_autor}', '{val_msg}', '{val_diff}', '{val_imp}');"
            )

        # 2. Analises
        analises = db.query(models.Analise).all()
        for a in analises:
            data_export["analises"].append({
                "commit_id": a.commit_id,
                "complexidade_global": a.complexidade_global,
                "atividades_json": a.atividades_json,
                "analisado_em": a.analisado_em,
            })
            val_cid = (a.commit_id or "").replace("'", "''")
            val_comp = (a.complexidade_global or "").replace("'", "''")
            val_ati = (a.atividades_json or "").replace("'", "''")
            val_ana = (a.analisado_em or "").replace("'", "''")
            sql_lines.append(
                f"INSERT OR REPLACE INTO analises (commit_id, complexidade_global, atividades_json, analisado_em) "
                f"VALUES ('{val_cid}', '{val_comp}', '{val_ati}', '{val_ana}');"
            )

        # 3. Historico
        historicos = db.query(models.Historico).all()
        for h in historicos:
            data_export["historico"].append({
                "id": h.id,
                "commit_id": h.commit_id,
                "titulo": h.titulo,
                "codigo": h.codigo,
                "hpa": h.hpa,
                "status": h.status,
                "enviado_em": h.enviado_em,
                "tem_data_fim": h.tem_data_fim,
            })
            val_cid = (h.commit_id or "").replace("'", "''")
            val_tit = (h.titulo or "").replace("'", "''")
            val_cod = (h.codigo or "").replace("'", "''")
            val_hpa = h.hpa or 0.0
            val_st = (h.status or "").replace("'", "''")
            val_env = (h.enviado_em or "").replace("'", "''")
            val_df = 1 if h.tem_data_fim else 0
            sql_lines.append(
                f"INSERT OR REPLACE INTO historico (id, commit_id, titulo, codigo, hpa, status, enviado_em, tem_data_fim) "
                f"VALUES ({h.id}, '{val_cid}', '{val_tit}', '{val_cod}', {val_hpa}, '{val_st}', '{val_env}', {val_df});"
            )

        # 4. Fila
        jobs = db.query(models.Fila).all()
        for f in jobs:
            data_export["fila"].append({
                "id": f.id,
                "tipo": f.tipo,
                "commit_id": f.commit_id,
                "atividade_idx": f.atividade_idx,
                "modelo": f.modelo,
                "status": f.status,
                "task_id": f.task_id,
                "resultado": f.resultado,
                "criado_em": f.criado_em,
                "concluido_em": f.concluido_em,
            })
            val_tp = (f.tipo or "").replace("'", "''")
            val_cid = (f.commit_id or "").replace("'", "''")
            val_aidx = f.atividade_idx if f.atividade_idx is not None else "NULL"
            val_mod = f"'{f.modelo}'" if f.modelo else "NULL"
            val_st = (f.status or "").replace("'", "''")
            val_tid = f"'{f.task_id}'" if f.task_id else "NULL"
            val_res = f"'{f.resultado.replace('\'', '\'\'')}'" if f.resultado else "NULL"
            val_cr = (f.criado_em or "").replace("'", "''")
            val_conc = f"'{f.concluido_em}'" if f.concluido_em else "NULL"
            sql_lines.append(
                f"INSERT OR REPLACE INTO fila (id, tipo, commit_id, atividade_idx, modelo, status, task_id, resultado, criado_em, concluido_em) "
                f"VALUES ({f.id}, '{val_tp}', '{val_cid}', {val_aidx}, {val_mod}, '{val_st}', {val_tid}, {val_res}, '{val_cr}', {val_conc});"
            )

        # 5. Fila Logs Histórico
        fila_logs = db.query(models.FilaLogsHistorico).all()
        for fl in fila_logs:
            data_export["fila_logs_historico"].append({
                "id": fl.id,
                "fila_id": fl.fila_id,
                "tipo": fl.tipo,
                "commit_id": fl.commit_id,
                "atividade_idx": fl.atividade_idx,
                "tentativa": fl.tentativa,
                "status": fl.status,
                "logs": fl.logs,
                "criado_em": fl.criado_em,
            })
            val_fl_tp = (fl.tipo or "").replace("'", "''")
            val_fl_cid = f"'{fl.commit_id.replace('\'', '\'\'')}'" if fl.commit_id else "NULL"
            val_fl_aidx = fl.atividade_idx if fl.atividade_idx is not None else "NULL"
            val_fl_tent = fl.tentativa or 1
            val_fl_st = (fl.status or "").replace("'", "''")
            val_fl_logs = f"'{fl.logs.replace('\'', '\'\'')}'" if fl.logs else "NULL"
            val_fl_cr = (fl.criado_em or "").replace("'", "''")
            sql_lines.append(
                f"INSERT OR REPLACE INTO fila_logs_historico (id, fila_id, tipo, commit_id, atividade_idx, tentativa, status, logs, criado_em) "
                f"VALUES ({fl.id}, {fl.fila_id}, '{val_fl_tp}', {val_fl_cid}, {val_fl_aidx}, {val_fl_tent}, '{val_fl_st}', {val_fl_logs}, '{val_fl_cr}');"
            )

        # 6. Git Accounts
        git_accs = db.query(models.GitAccount).all()
        for ga in git_accs:
            data_export["git_accounts"].append({
                "id": ga.id,
                "nome": ga.nome,
                "url": ga.url,
                "token": ga.token,
                "padrao": ga.padrao,
                "criado_em": ga.criado_em,
            })
            val_ga_nome = (ga.nome or "").replace("'", "''")
            val_ga_url = (ga.url or "").replace("'", "''")
            val_ga_token = (ga.token or "").replace("'", "''")
            val_ga_pad = 1 if ga.padrao else 0
            val_ga_cr = (ga.criado_em or "").replace("'", "''")
            sql_lines.append(
                f"INSERT OR REPLACE INTO git_accounts (id, nome, url, token, padrao, criado_em) "
                f"VALUES ({ga.id}, '{val_ga_nome}', '{val_ga_url}', '{val_ga_token}', {val_ga_pad}, '{val_ga_cr}');"
            )

    sql_lines.append("COMMIT;")

    # Salva arquivos JSON
    json_str = json.dumps(data_export, ensure_ascii=False, indent=2)
    with open(json_file_timestamped, "w", encoding="utf-8") as f:
        f.write(json_str)
    with open(json_file_latest, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Salva arquivos SQL
    sql_str = "\n".join(sql_lines)
    with open(sql_file_timestamped, "w", encoding="utf-8") as f:
        f.write(sql_str)
    with open(sql_file_latest, "w", encoding="utf-8") as f:
        f.write(sql_str)

    # Rotação de backups antigos: mantém apenas os 2 últimos backups com timestamp
    _rotacionar_backups(dir_backup, max_backups=2)

    stats = {
        "ok": True,
        "timestamp": data_export["timestamp"],
        "arquivo_sql": os.path.basename(sql_file_latest),
        "arquivo_json": os.path.basename(json_file_latest),
        "counts": {
            "commits": len(data_export["commits"]),
            "analises": len(data_export["analises"]),
            "historico": len(data_export["historico"]),
            "fila": len(data_export["fila"]),
            "fila_logs_historico": len(data_export["fila_logs_historico"]),
            "git_accounts": len(data_export["git_accounts"]),
        },
        "files": {
            "json": json_file_latest,
            "sql": sql_file_latest,
            "json_timestamped": json_file_timestamped,
            "sql_timestamped": sql_file_timestamped,
        },
    }
    print(f"[Backup Nexus] Auto-save concluído com sucesso! Commits: {stats['counts']['commits']} | Fila: {stats['counts']['fila']} | Histórico: {stats['counts']['historico']} | Logs: {stats['counts']['fila_logs_historico']} | GitAccounts: {stats['counts']['git_accounts']}", flush=True)
    return stats


def _rotacionar_backups(dir_backup: str, max_backups: int = 2):
    """Remove backups antigos mantendo apenas os 2 mais recentes."""
    try:
        arquivos_json = sorted([
            os.path.join(dir_backup, f) for f in os.listdir(dir_backup)
            if f.startswith("backup_nexus_2") and f.endswith(".json")
        ])
        arquivos_sql = sorted([
            os.path.join(dir_backup, f) for f in os.listdir(dir_backup)
            if f.startswith("backup_nexus_2") and f.endswith(".sql")
        ])

        while len(arquivos_json) > max_backups:
            antigo = arquivos_json.pop(0)
            if os.path.exists(antigo):
                os.remove(antigo)

        while len(arquivos_sql) > max_backups:
            antigo = arquivos_sql.pop(0)
            if os.path.exists(antigo):
                os.remove(antigo)
    except Exception as e:
        print(f"[Backup Nexus] Erro ao rotacionar backups: {e}", flush=True)


def verificar_ping_munka(munka_url: str, timeout: int = 6) -> tuple[bool, str]:
    """Testa a conectividade com o portal Munka realizando uma requisição HTTP rápida.

    Retorna (True, "OK") se o portal estiver acessível, ou (False, "Motivo") caso contrário.
    """
    if not munka_url or not munka_url.startswith("http"):
        return False, "URL do Munka não configurada ou inválida."

    target_url = f"{munka_url.rstrip('/')}/tarefamodelview/list/?"
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nexus-PingCheck/2.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status in (200, 301, 302):
                return True, "Portal Munka respondendo com sucesso."
            return False, f"Portal Munka retornou status HTTP {response.status}."
    except Exception as e:
        return False, f"Falha de conexão com o portal Munka: {str(e)}"
