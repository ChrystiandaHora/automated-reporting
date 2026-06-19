import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///munka.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
