"""Catálogo único dos status de tarefa do Munka (fonte única do backend)."""

# (id, rótulo no portal, concluída?)
CATALOGO_STATUS = [
    ("15", "Backlog", False),
    ("16", "Backlog Prioritário", False),
    ("17", "Pendente", False),
    ("18", "Desenvolvimento", False),
    ("19", "Concluído para o Supervisor", True),
    ("20", "Homologação", False),
    ("21", "Concluído", True),
    ("22", "Arquivado", False),
    ("35", "Evidência com Pendência", False),
]

# Rótulo gravado em Historico.status: o 17 é "Enviado ao Munka" (estado local).
STATUS_MAP = {sid: rotulo for sid, rotulo, _ in CATALOGO_STATUS}
STATUS_MAP["17"] = "Enviado ao Munka"


def listar_catalogo() -> list:
    return [{"id": sid, "rotulo": rotulo, "concluida": conc} for sid, rotulo, conc in CATALOGO_STATUS]


def eh_concluido(status: str) -> bool:
    s = (status or "").strip().lower()
    return (
        "conclu" in s
        or s in ("19", "21")
        or "supervisor" in s
        or "aprovad" in s
        or "finalizad" in s
    )
