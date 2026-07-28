import os
import shutil
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///nexus.db")


def _migrar_banco_antigo_se_necessario(db_url: str):
    """Garante a migração do banco SQLite de munka.db para nexus.db sem perda de dados.

    Procura por arquivos munka.db existentes (no diretório do banco, no diretório
    de trabalho ou em /data) e copia para nexus.db caso este ainda não exista ou
    esteja vazio.
    """
    if db_url.startswith("sqlite:///"):
        # Normaliza o caminho do banco SQLite (suporta sqlite:/// e sqlite:////)
        caminho_db = db_url.replace("sqlite:///", "/") if db_url.startswith("sqlite:////") else db_url.replace("sqlite:///", "")
        
        diretorio = os.path.dirname(caminho_db) or "."
        nome_arquivo = os.path.basename(caminho_db)

        # Se o banco nexus.db não existe ou está com 0 bytes, precisa migrar do munka.db
        nexus_inexistente_ou_vazio = not os.path.exists(caminho_db) or (os.path.exists(caminho_db) and os.path.getsize(caminho_db) == 0)

        if nome_arquivo == "nexus.db" and nexus_inexistente_ou_vazio:
            locais_possiveis = [
                os.path.join(diretorio, "munka.db"),
                "./munka.db",
                "/data/munka.db",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "munka.db"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "munka.db"),
            ]

            for caminho_antigo in locais_possiveis:
                if os.path.exists(caminho_antigo) and os.path.getsize(caminho_antigo) > 0:
                    try:
                        os.makedirs(diretorio, exist_ok=True)
                        shutil.copy2(caminho_antigo, caminho_db)
                        print(
                            f"[Nexus Migration] SUCCESS: Banco de dados legado '{caminho_antigo}' ({os.path.getsize(caminho_antigo)} bytes) copiado com sucesso para '{caminho_db}'.",
                            flush=True,
                        )
                        break
                    except Exception as e:
                        print(
                            f"[Nexus Migration] ERROR: Falha ao copiar '{caminho_antigo}' para '{caminho_db}': {e}",
                            flush=True,
                        )


_migrar_banco_antigo_se_necessario(DATABASE_URL)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _aplicar_migracoes(engine_ref):
    """Detecta colunas definidas nos models mas ausentes no banco e as adiciona.

    Percorre todas as tabelas registradas no metadata do SQLAlchemy, compara as
    colunas definidas no modelo Python com as colunas reais no banco SQLite e
    executa ALTER TABLE ADD COLUMN para cada coluna faltante.
    """
    insp = inspect(engine_ref)
    with engine_ref.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            if not insp.has_table(table_name):
                continue

            colunas_existentes = {c["name"] for c in insp.get_columns(table_name)}

            for col in table.columns:
                if col.name in colunas_existentes:
                    continue

                # Mapeia o tipo SQLAlchemy para tipo SQL compatível com SQLite
                col_type = col.type.compile(dialect=engine_ref.dialect)
                default_clause = ""
                if col.default is not None:
                    val = col.default.arg
                    if isinstance(val, bool):
                        default_clause = f" DEFAULT {1 if val else 0}"
                    elif isinstance(val, (int, float)):
                        default_clause = f" DEFAULT {val}"
                    elif isinstance(val, str):
                        default_clause = f" DEFAULT '{val}'"

                sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(
                        f"[Nexus Migration] ADD COLUMN: {table_name}.{col.name} ({col_type}){default_clause}",
                        flush=True,
                    )
                except Exception as e:
                    print(
                        f"[Nexus Migration] SKIP: {table_name}.{col.name} — {e}",
                        flush=True,
                    )


def get_db():
    """Gerador de sessão do banco de dados para injeção de dependência no FastAPI.

    Cria uma sessão SQLAlchemy, a disponibiliza para a rota e garante o fechamento
    ao final da requisição, mesmo que ocorra uma exceção.

    Yields:
        Session: Sessão ativa do SQLAlchemy pronta para uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
