"""
Script de migração: importa commits e análises do sistema de arquivos para o SQLite.
Execute uma vez: python migrate.py
"""
import glob
import json
import os
import re
from datetime import datetime

from database import engine, SessionLocal, Base
import models

Base.metadata.create_all(bind=engine)


def extrair_metadados(diff_text: str, filename: str) -> dict:
    """Extrai metadados de um arquivo de diff gerado pelo sistema legado.

    Analisa o conteúdo do arquivo diff usando expressões regulares para
    identificar SHA, data, projeto e autor do commit a partir do cabeçalho
    padronizado inserido durante a importação do GitLab.

    Args:
        diff_text: Conteúdo completo do arquivo .txt do diff, incluindo cabeçalho.
        filename: Nome do arquivo (ex: diff_commits_2026_06_10_abc123.txt),
            usado como fallback para extrair data e SHA.

    Returns:
        Dicionário com as chaves: sha, data (DD/MM/YYYY), projeto, autor, mensagem.
    """
    sha = "sem_sha"
    m = re.search(r'\b([0-9a-fA-F]{40})\b', diff_text)
    if m:
        sha = m.group(1)
    else:
        m = re.search(r'^commit\s+([0-9a-fA-F]{7,40})', diff_text, re.MULTILINE)
        if m:
            sha = m.group(1)

    data_formatada = None
    dm = re.search(r'Date:\s+(.+)', diff_text)
    if dm:
        date_str = dm.group(1).strip()
        for fmt in ("%a %b %d %H:%M:%S %Y", "%Y-%m-%d"):
            try:
                clean = re.sub(r'\s+[-+]\d{4}$', '', date_str)
                dt = datetime.strptime(clean, fmt)
                data_formatada = dt.strftime("%d/%m/%Y")
                break
            except Exception:
                continue
    if not data_formatada:
        fm = re.search(r'diff_commits_(\d{4})_(\d{2})_(\d{2})', filename)
        if fm:
            data_formatada = f"{fm.group(3)}/{fm.group(2)}/{fm.group(1)}"
        else:
            data_formatada = datetime.now().strftime("%d/%m/%Y")

    pm = re.search(r'Project:\s+(.+)', diff_text)
    projeto = pm.group(1).strip() if pm else ""

    am = re.search(r'Author:\s+(.+?)\s*<', diff_text)
    autor = am.group(1).strip() if am else ""

    sm = re.search(r'Subject:\s+(.+)', diff_text)
    mensagem = sm.group(1).strip() if sm else ""

    return {"sha": sha, "data": data_formatada, "projeto": projeto, "autor": autor, "mensagem": mensagem}


def main():
    """Executa a migração completa do sistema legado (arquivos) para o SQLite.

    Percorre todos os arquivos ``diff_commits_*.txt`` encontrados na pasta
    ``commits/`` (localizada automaticamente na raiz do projeto), cria registros
    na tabela ``commits`` e, quando existe o cache ``.json`` correspondente,
    também cria registros na tabela ``analises``. Por fim, migra o
    ``historico.csv`` para a tabela ``historico``.

    Registros já existentes no banco (mesmo SHA) são ignorados para evitar
    duplicatas em execuções repetidas.

    Raises:
        Exception: Erros de leitura de arquivo são capturados individualmente
            e impressos no stdout sem interromper a migração dos demais arquivos.
    """
    # Localiza a pasta de dados: tenta raiz do projeto (um nível acima de backend/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(script_dir)
    commits_dir = os.path.join(root, "commits")
    historico_csv = os.path.join(root, "historico.csv")
    if not os.path.isdir(commits_dir):
        # Fallback: pasta atual (execução a partir da raiz)
        commits_dir = "commits"
        historico_csv = "historico.csv"

    db = SessionLocal()
    arquivos = sorted(glob.glob(os.path.join(commits_dir, "diff_commits_*.txt")))
    print(f"Pasta de dados: {commits_dir}")
    print(f"Encontrados {len(arquivos)} arquivo(s) de commit.")

    commits_migrados = 0
    analises_migradas = 0

    for filepath in arquivos:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                diff_text = f.read()
        except Exception as e:
            print(f"  ERRO ao ler {filename}: {e}")
            continue

        meta = extrair_metadados(diff_text, filename)
        sha = meta["sha"]

        existing = db.query(models.Commit).filter(models.Commit.id.like(f"{sha[:8]}%")).first()
        if existing:
            print(f"  JÁ EXISTE: {filename} → {sha[:8]}")
            commit_id = existing.id
        else:
            commit = models.Commit(
                id=sha,
                data=meta["data"],
                projeto=meta["projeto"],
                autor=meta["autor"],
                mensagem=meta["mensagem"],
                diff_raw=diff_text,
                importado_em=datetime.now().isoformat(),
            )
            db.add(commit)
            db.flush()
            commit_id = sha
            commits_migrados += 1
            print(f"  COMMIT: {filename} → {sha[:8]}")

        # Verifica cache de análise correspondente
        cache_path = os.path.join(commits_dir, f"cache_{filename}.json")
        if not os.path.exists(cache_path):
            continue

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception as e:
            print(f"    ERRO ao ler cache {cache_path}: {e}")
            continue

        analise_existente = db.query(models.Analise).filter_by(commit_id=commit_id).first()
        if analise_existente:
            print(f"    ANÁLISE já existe para {sha[:8]}")
            continue

        atividades = cache.get("atividades", [])
        complexidade = cache.get("complexidade_global", "")

        nova_analise = models.Analise(
            commit_id=commit_id,
            complexidade_global=complexidade,
            atividades_json=json.dumps(atividades, ensure_ascii=False),
            analisado_em=datetime.now().isoformat(),
        )
        db.add(nova_analise)
        analises_migradas += 1
        print(f"    ANÁLISE: {len(atividades)} atividade(s) migrada(s)")

    # Migra histórico CSV
    hist_migrados = 0
    if os.path.exists(historico_csv):
        import csv
        with open(historico_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                commit_ref = row.get("Commit", "")
                sha_match = re.search(r'([0-9a-fA-F]{7,40})', commit_ref)
                commit_id_ref = sha_match.group(1) if sha_match else commit_ref

                hist = models.Historico(
                    commit_id=commit_id_ref,
                    titulo=row.get("Título", ""),
                    codigo=row.get("Código", ""),
                    hpa=float(row.get("HPA", 0) or 0),
                    status=row.get("Status", ""),
                    enviado_em=row.get("Data", datetime.now().isoformat()),
                )
                db.add(hist)
                hist_migrados += 1
        print(f"\nHistórico: {hist_migrados} registro(s) migrado(s)")

    db.commit()
    db.close()

    print(f"\nMigração concluída:")
    print(f"  Commits: {commits_migrados} novo(s)")
    print(f"  Análises: {analises_migradas} nova(s)")
    print(f"  Histórico: {hist_migrados} registro(s)")


if __name__ == "__main__":
    main()
