"""Tabela de HPA do catálogo como dados: códigos válidos e HPA calculado pelo código.

Lê a seção "Tabela de HPA por Serviço e Complexidade" de catalogo-servicos.md.
Serviços com HPA por complexidade (colunas Baixa/Média/Alta, ou "8h / 16h / 36h")
viram três códigos com sufixo: a = Baixa, b = Média, c = Alta (regra do catálogo).
Serviços de valor único mantêm o próprio código (21a, 56c, 62b...).
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional

SUFIXOS = ("a", "b", "c")  # Baixa, Média, Alta


@dataclass(frozen=True)
class ItemCatalogo:
    codigo: str
    servico: str
    hpa: float


def _horas(celula: str) -> Optional[float]:
    m = re.search(r"(\d+(?:,\d+)?)\s*h", celula)
    return float(m.group(1).replace(",", ".")) if m else None


def carregar_tabela_hpa(catalogo_md: str) -> Dict[str, ItemCatalogo]:
    ini = catalogo_md.find("### Tabela de HPA")
    fim = catalogo_md.find("## Regras de Mapeamento", ini)
    trecho = catalogo_md[ini:fim]
    itens: Dict[str, ItemCatalogo] = {}
    for linha in trecho.splitlines():
        cels = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(cels) < 3 or not re.fullmatch(r"\d+[a-z]?", cels[0]):
            continue
        codigo, servico, valores = cels[0], cels[1], cels[2:-1]  # última coluna = escopo
        if len(valores) == 1 and "/" in valores[0]:              # "8h / 16h / 36h"
            valores = [v.strip() for v in valores[0].split("/")]
        horas = [_horas(v) for v in valores]
        if len(horas) == 3 and sum(h is not None for h in horas) >= 2:
            # Varia por complexidade -> 57a/57b/57c
            for suf, h in zip(SUFIXOS, horas):
                if h is not None:
                    itens[codigo + suf] = ItemCatalogo(codigo + suf, servico, h)
        else:
            h = next((x for x in horas if x is not None), None)
            if h is not None:
                itens[codigo] = ItemCatalogo(codigo, servico, h)
    return itens


def normalizar_codigo(codigo: str) -> str:
    """'[21a]' / ' 21A - Manutenção' / '57 b' -> '21a' / '21a' / '57b'."""
    m = re.search(r"(\d+)\s*([a-z])?\b", (codigo or "").lower())
    return (m.group(1) + (m.group(2) or "")) if m else ""


def codigo_base(codigo: str) -> str:
    m = re.match(r"\d+", normalizar_codigo(codigo))
    return m.group(0) if m else ""


def _sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def complexidade_do_sistema(catalogo_md: str, projeto: str) -> Optional[str]:
    """Procura o projeto na tabela 'Complexidade por Sistema'. Retorna 'a'|'b'|'c' ou None."""
    alvo = _sem_acento(projeto or "")
    if not alvo:
        return None
    melhor = None
    for linha in catalogo_md.splitlines():
        m = re.match(r"\|\s*\*\*(Alta|Média|Baixa)\*\*\s*\|(.*)\|", linha)
        if not m:
            continue
        suf = {"Baixa": "a", "Média": "b", "Alta": "c"}[m.group(1)]
        for sistema in m.group(2).split(","):
            s = _sem_acento(sistema.strip())
            if s and (s in alvo or alvo in s):
                if melhor is None or len(s) > melhor[0]:
                    melhor = (len(s), suf)
    return melhor[1] if melhor else None


def hpa_por_codigo(tabela: Dict[str, ItemCatalogo], codigo: str) -> Optional[float]:
    item = tabela.get(normalizar_codigo(codigo))
    return item.hpa if item else None


def lista_para_prompt(tabela: Dict[str, ItemCatalogo]) -> List[str]:
    return [f"{c} — {i.servico}" for c, i in tabela.items()]
