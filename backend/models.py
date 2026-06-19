from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey
from database import Base


class Commit(Base):
    """Representa um commit importado do GitLab.

    Armazena os metadados e o conteúdo bruto do diff. O campo `diff_raw`
    contém o cabeçalho de metadados gerado na importação seguido do diff
    unificado do git, usado pelo Gemini e pelo gerador de evidências.

    Attributes:
        id: SHA completo do commit (40 caracteres hexadecimais), chave primária.
        data: Data do commit no formato DD/MM/YYYY.
        projeto: Caminho do projeto no GitLab (ex: grupo/projeto).
        autor: Nome do autor do commit.
        mensagem: Mensagem completa do commit.
        diff_raw: Conteúdo completo do diff com cabeçalho de metadados.
        importado_em: Timestamp ISO da importação (ex: 2026-06-14T10:30:00).
    """

    __tablename__ = "commits"

    id = Column(String, primary_key=True)
    data = Column(String)
    projeto = Column(String)
    autor = Column(String)
    mensagem = Column(String)
    diff_raw = Column(Text)
    importado_em = Column(String)


class Analise(Base):
    """Representa a análise de faturamento gerada pelo Gemini AI para um commit.

    Cada commit possui no máximo uma análise (relação 1:1). As atividades são
    armazenadas como JSON serializado para preservar a estrutura do Pydantic
    sem necessidade de tabelas adicionais.

    Attributes:
        commit_id: SHA do commit analisado, chave primária e chave estrangeira.
        complexidade_global: Texto descritivo da complexidade técnica da intervenção.
        atividades_json: Array JSON de objetos ``Atividade`` com etapa, titulo,
            descricao, codigo_id, hpa, arquivos e justificativa.
        analisado_em: Timestamp ISO da análise (ex: 2026-06-14T11:00:00).
    """

    __tablename__ = "analises"

    commit_id = Column(String, ForeignKey("commits.id"), primary_key=True)
    complexidade_global = Column(Text)
    atividades_json = Column(Text)
    analisado_em = Column(String)


class Historico(Base):
    """Registra cada atividade enviada com sucesso ao portal Munka.

    Um commit pode gerar múltiplos registros de histórico, um por atividade
    enviada. Registros são inseridos apenas após o Playwright confirmar o
    cadastro e homologação da tarefa no portal.

    Attributes:
        id: Identificador autoincremental, chave primária.
        commit_id: SHA do commit de origem da atividade.
        titulo: Título formal da atividade cadastrada no Munka.
        codigo: Código do catálogo de serviços (ex: 21a, 57b).
        hpa: Horas Previstas para Execução da Atividade faturadas.
        status: Status final da atividade (ex: Homologada).
        enviado_em: Timestamp ISO do envio bem-sucedido.
    """

    __tablename__ = "historico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_id = Column(String, ForeignKey("commits.id"))
    titulo = Column(String)
    codigo = Column(String)
    hpa = Column(Float)
    status = Column(String)
    enviado_em = Column(String)
