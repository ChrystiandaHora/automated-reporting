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
        "counts": {
            "commits": len(data_export["commits"]),
            "analises": len(data_export["analises"]),
            "historico": len(data_export["historico"]),
            "fila": len(data_export["fila"]),
        },
        "files": {
            "json": json_file_latest,
            "sql": sql_file_latest,
            "json_timestamped": json_file_timestamped,
            "sql_timestamped": sql_file_timestamped,
        },
    }
    print(f"[Backup Nexus] Auto-save concluído com sucesso! Commits: {stats['counts']['commits']} | Fila: {stats['counts']['fila']} | Histórico: {stats['counts']['historico']}", flush=True)
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
