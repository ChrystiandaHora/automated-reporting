"""Benchmark de LLM local (Ollama) contra as análises já feitas pelo Gemini.

Só lê o banco (SQLite em mode=ro). Gera relatório em OUT_DIR.
O schema e as instruções espelham backend/gemini_service.py — manter em sincronia.
"""
import json
import os
import random
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

import ollama
from pydantic import BaseModel, Field, ValidationError
from rank_bm25 import BM25Okapi

from catalogo_hpa import (carregar_tabela_hpa, codigo_base, complexidade_do_sistema,
                          hpa_por_codigo, normalizar_codigo)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DB_PATH = os.environ.get("DB_PATH", "/data/nexus.db")
DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/docs-base"))
OUT_DIR = Path(os.environ.get("OUT_DIR", "/out"))
MODELOS = [m.strip() for m in os.environ.get("MODELOS", "qwen2.5-coder:14b").split(",") if m.strip()]
MODOS = [m.strip() for m in os.environ.get("MODOS", "compacto").split(",") if m.strip()]
N_COMMITS = int(os.environ.get("N_COMMITS", "10"))
NUM_CTX = int(os.environ.get("NUM_CTX", "20480"))
MAX_DIFF_CHARS = int(os.environ.get("MAX_DIFF_CHARS", "24000"))
TOP_K_SERVICOS = int(os.environ.get("TOP_K_SERVICOS", "5"))
# Exemplos reais (diff + classificação do Gemini) dos commits mais parecidos, fora do conjunto testado
N_EXEMPLOS = int(os.environ.get("N_EXEMPLOS", "3"))
EXEMPLO_DIFF_CHARS = int(os.environ.get("EXEMPLO_DIFF_CHARS", "1500"))
# Teto de saída: sem ele o modelo pode entrar em loop e gerar dezenas de milhares de tokens
NUM_PREDICT = int(os.environ.get("NUM_PREDICT", "4096"))
MAX_ATIVIDADES = int(os.environ.get("MAX_ATIVIDADES", "10"))


# --- Schema (espelho de backend/gemini_service.py) --------------------------
class Atividade(BaseModel):
    etapa: str = Field(description="Estritamente: Deleção, Inclusão, ou Alteração/Correção")
    titulo: str = Field(description="Título técnico da ação em primeira pessoa")
    descricao: str = Field(description="O que foi feito tecnicamente, baseado estritamente no diff, em primeira pessoa")
    categoria: str = Field(description="Categoria no catálogo de serviços")
    codigo_id: str = Field(description="Código do catálogo, exatamente como na lista de códigos válidos")
    # Sem 'hpa': o HPA é calculado pelo código (catalogo_hpa.hpa_por_codigo), não pelo modelo.
    arquivos: List[str] = Field(description="Arquivos do diff afetados por esta atividade")
    justificativa: str = Field(description="Justificativa técnica em primeira pessoa")


class RelatorioFaturamento(BaseModel):
    complexidade_global: str = Field(description="Resumo de 1 ou 2 parágrafos em primeira pessoa")
    atividades: List[Atividade] = Field(description="Atividades técnicas independentes identificadas no diff")


INSTRUCOES = (
    "Você é um engenheiro de software sênior responsável pelo faturamento de entregas técnicas.\n"
    "Seu papel é receber um Git Diff de alterações e cruzá-lo com o catálogo de faturamento para gerar as atividades.\n"
    "Cruze rigorosamente o catálogo e siga as regras de ouro: uso de primeira pessoa do singular e justificativa profunda.\n"
    "Para cada atividade, escolha o 'codigo_id' EXCLUSIVAMENTE entre os códigos da Tabela de HPA. "
    "Serviços que variam por complexidade usam sufixo: a = Baixa, b = Média, c = Alta. "
    "Não informe horas: o HPA é calculado pelo sistema a partir do código.\n"
    "REGRA DE CLASSIFICAÇÃO: alteração em arquivo que JÁ EXISTIA é MANUTENÇÃO (21a a 21h): "
    "21b para labels/textos/estilos/elementos estáticos, 21e para correção de bug, 21a para atributo/campo, "
    "21d para regra de negócio, 21c para validação. Use itens de criação (57, 58, 59, 60, 61, 62a, 62b, 14, 15, 16) "
    "SOMENTE quando o diff cria arquivos novos (marcados como NOVO na lista de arquivos).\n"
    "Agrupe: um mesmo código aparece no máximo UMA vez por commit; liste todos os arquivos dele nessa atividade.\n"
    "Use SOMENTE informações presentes no diff. Não invente arquivos, funções ou comportamentos. "
    "Em 'arquivos', cite apenas caminhos que aparecem no diff.\n"
    "Retorne estritamente o JSON estruturado conforme o esquema definido."
)


# --- Contexto ----------------------------------------------------------------
def carregar_docs():
    regras = (DOCS_DIR / "regras-medicao.md").read_text(encoding="utf-8")
    catalogo = (DOCS_DIR / "catalogo-servicos.md").read_text(encoding="utf-8")
    return regras, catalogo


def tokenizar(texto: str) -> List[str]:
    return re.findall(r"[a-zà-ú0-9]{3,}", texto.lower())


def secoes_servicos(regras: str) -> List[str]:
    """Quebra o detalhamento do catálogo em uma seção por serviço (### [N] ...)."""
    partes = re.split(r"(?m)^(?=### \[)", regras)
    return [p for p in partes if p.startswith("### [")]


def base_conhecimento_compacta(catalogo: str) -> str:
    """Do catálogo/prompt fica só o que serve para JSON: complexidade, tabela de HPA,
    regras de mapeamento e regras gerais. Sai tudo que é formato HTML/batch/GitLab."""
    ini = catalogo.find("## Base de Conhecimento")
    fim = catalogo.find("## Formato de Saída")
    gerais = catalogo.find("## Regras Gerais")
    trecho = catalogo[ini:fim] if ini >= 0 and fim > ini else catalogo
    if gerais >= 0:
        trecho += "\n" + catalogo[gerais:]
    return trecho


def montar_contexto(modo: str, diff: str, regras: str, catalogo: str) -> str:
    if modo == "completo":
        return f"REGRAS DE CONTEXTO:\n{regras}\n\nCATÁLOGO DE SERVIÇOS:\n{catalogo}"
    secoes = secoes_servicos(regras)
    bm25 = BM25Okapi([tokenizar(s) for s in secoes])
    scores = bm25.get_scores(tokenizar(diff))
    top = sorted(range(len(secoes)), key=lambda i: scores[i], reverse=True)[:TOP_K_SERVICOS]
    # Manutenção (21) é o item mais comum: sempre presente
    for i, s in enumerate(secoes):
        if s.startswith("### [21]") and i not in top:
            top.append(i)
    servicos = "\n".join(secoes[i] for i in sorted(top))
    return (
        f"BASE DE CONHECIMENTO (complexidade, HPA e regras):\n{base_conhecimento_compacta(catalogo)}\n\n"
        f"SERVIÇOS DO CATÁLOGO MAIS RELEVANTES PARA ESTE DIFF:\n{servicos}"
    )


# --- Métricas ----------------------------------------------------------------
def arquivos_do_diff(diff: str) -> set:
    arqs = set()
    for a, b in re.findall(r"^diff --git a/(\S+) b/(\S+)", diff, flags=re.M):
        arqs.update({a, b})
    for p in re.findall(r"^(?:\+\+\+|---) [ab]/(\S+)", diff, flags=re.M):
        arqs.add(p)
    return arqs


def status_arquivos(diff: str) -> str:
    """Lista determinística NOVO/ALTERADO/REMOVIDO por arquivo, a partir dos cabeçalhos do diff."""
    linhas = []
    for bloco in re.split(r"(?m)^(?=diff --git )", diff):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", bloco)
        if not m:
            continue
        if re.search(r"(?m)^new file mode", bloco):
            st = "NOVO"
        elif re.search(r"(?m)^deleted file mode", bloco):
            st = "REMOVIDO"
        else:
            st = "ALTERADO"
        linhas.append(f"- {st}: {m.group(2)}")
    return "\n".join(linhas) or "- (sem cabeçalhos de arquivo no diff)"


def consolidar(rel: RelatorioFaturamento) -> RelatorioFaturamento:
    """Junta atividades com o mesmo código: o HPA conta uma vez (regra de não multiplicar)."""
    por_codigo = {}
    for a in rel.atividades:
        cod = normalizar_codigo(a.codigo_id)
        if cod in por_codigo:
            atual = por_codigo[cod]
            atual.arquivos = list(dict.fromkeys(atual.arquivos + a.arquivos))
        else:
            por_codigo[cod] = a.model_copy(update={"codigo_id": cod})
    return rel.model_copy(update={"atividades": list(por_codigo.values())})


def bloco_exemplos(exemplos: list) -> str:
    partes = []
    for i, e in enumerate(exemplos, 1):
        diff = e["diff"][:EXEMPLO_DIFF_CHARS] + ("\n[... diff truncado ...]" if len(e["diff"]) > EXEMPLO_DIFF_CHARS else "")
        cls = "\n".join(f"  - {a.get('codigo_id')}: {a.get('titulo', '')}" for a in e["gabarito"])
        partes.append(f"EXEMPLO {i}\nArquivos:\n{status_arquivos(e['diff'])}\nDiff:\n{diff}\nClassificação correta:\n{cls}")
    return "EXEMPLOS REAIS JÁ CLASSIFICADOS (siga o mesmo critério):\n\n" + "\n\n".join(partes)


def vram_mb(client, modelo):
    """VRAM ocupada pelo modelo, segundo o próprio Ollama (/api/ps)."""
    try:
        for m in client.ps().models:
            if m.model == modelo or m.name == modelo:
                return (m.size_vram or 0) // (1024 * 1024)
    except Exception:
        pass
    return None


def schema_com_codigos(codigos_validos: List[str]) -> dict:
    """Schema JSON com 'codigo_id' travado na lista do catálogo (o Ollama restringe a geração)."""
    # Schema inline (sem $ref/$defs): o Ollama só aplica o enum de forma confiável assim.
    atividade = Atividade.model_json_schema()
    atividade.pop("title", None)
    atividade["properties"]["codigo_id"] = {"type": "string", "enum": codigos_validos}
    return {
        "type": "object",
        "properties": {
            "complexidade_global": {"type": "string"},
            "atividades": {"type": "array", "items": atividade, "minItems": 1, "maxItems": MAX_ATIVIDADES},
        },
        "required": ["complexidade_global", "atividades"],
    }


def comparar(local: RelatorioFaturamento, gabarito_atvs: list, diff: str, tabela) -> dict:
    cod_l = Counter(normalizar_codigo(a.codigo_id) for a in local.atividades)
    cod_g = Counter(normalizar_codigo(str(a.get("codigo_id", ""))) for a in gabarito_atvs)
    total = max(sum(cod_g.values()), 1)
    base_l = Counter(codigo_base(c) for c in cod_l.elements())
    base_g = Counter(codigo_base(c) for c in cod_g.elements())
    arqs_reais = arquivos_do_diff(diff)
    citados = [f for a in local.atividades for f in a.arquivos]
    inventados = [f for f in citados if arqs_reais and not any(f.endswith(r) or r.endswith(f) for r in arqs_reais)]
    hpas = [hpa_por_codigo(tabela, a.codigo_id) for a in local.atividades]
    return {
        "acerto_codigos": round(sum((cod_l & cod_g).values()) / total, 2),
        "acerto_servico": round(sum((base_l & base_g).values()) / total, 2),
        "hpa_local": round(sum(h or 0 for h in hpas), 2),
        "hpa_gabarito": round(sum(float(a.get("hpa", 0) or 0) for a in gabarito_atvs), 2),
        "codigos_sem_hpa": sum(h is None for h in hpas),
        "n_atv_local": len(local.atividades),
        "n_atv_gabarito": len(gabarito_atvs),
        "arquivos_inventados": len(inventados),
        "arquivos_citados": len(citados),
        "codigos_local": sorted(cod_l.elements()),
        "codigos_gabarito": sorted(cod_g.elements()),
    }


# --- Execução ----------------------------------------------------------------
GABARITO = os.environ.get("GABARITO", "historico")   # historico = tarefas aprovadas | analises = saída do Gemini
CORTE = os.environ.get("CORTE", "2026-11")            # só tarefas lançadas ANTES deste mês (aprovadas)
SEMENTE = int(os.environ.get("SEMENTE", "7"))
# 1 = commits com diff > MAX_DIFF_CHARS também entram no banco de exemplos (nunca no teste)
INCLUIR_GRANDES = os.environ.get("INCLUIR_GRANDES", "0") == "1"


def carregar_gabarito():
    """Retorna (commits de teste, banco de exemplos). Um commit de teste nunca vira exemplo.

    historico: tarefas lançadas antes de CORTE (aprovadas pelo supervisor), agrupadas por commit.
    O teste é uma amostra sorteada com SEMENTE fixa, então todas as rodadas usam os mesmos commits.
    """
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    if GABARITO == "historico":
        rows = con.execute(
            """SELECT c.id, c.projeto, c.diff_raw, h.codigo, h.hpa, h.titulo
                 FROM historico h JOIN commits c ON c.id = h.commit_id
                WHERE h.enviado_em < ? AND h.codigo IS NOT NULL
                  AND c.diff_raw IS NOT NULL AND length(c.diff_raw) >= 200
                ORDER BY c.id, h.id""",
            (CORTE,),
        ).fetchall()
        por_commit = {}
        for cid, proj, diff, cod, hpa, tit in rows:
            e = por_commit.setdefault(cid, {"id": cid, "projeto": proj, "diff": diff, "gabarito": []})
            e["gabarito"].append({"codigo_id": cod, "hpa": hpa, "titulo": tit})
        cabem = [e for e in por_commit.values() if len(e["diff"]) <= MAX_DIFF_CHARS]
        grandes = [e for e in por_commit.values() if len(e["diff"]) > MAX_DIFF_CHARS]
        random.Random(SEMENTE).shuffle(cabem)
        con.close()
        return cabem[:N_COMMITS], cabem[N_COMMITS:] + (grandes if INCLUIR_GRANDES else [])
    else:
        rows = con.execute(
            """SELECT c.id, c.projeto, c.diff_raw, a.atividades_json
                 FROM analises a JOIN commits c ON c.id = a.commit_id
                WHERE c.diff_raw IS NOT NULL AND length(c.diff_raw) BETWEEN 200 AND ?
                  AND a.atividades_json IS NOT NULL AND a.atividades_json != '[]'""",
            (MAX_DIFF_CHARS,),
        ).fetchall()
        todos = [{"id": r[0], "projeto": r[1], "diff": r[2], "gabarito": json.loads(r[3])} for r in rows]
    con.close()
    random.Random(SEMENTE).shuffle(todos)
    return todos[:N_COMMITS], todos[N_COMMITS:]


def relatorio_knn(exemplos: list) -> str:
    """Referência sem LLM: copia a classificação do commit aprovado mais parecido."""
    atv = [{"etapa": "Alteração/Correção", "titulo": a.get("titulo") or "", "descricao": "", "categoria": "",
            "codigo_id": normalizar_codigo(str(a.get("codigo_id"))) or "21b", "arquivos": [], "justificativa": ""}
           for a in (exemplos[0]["gabarito"] if exemplos else [])]
    return json.dumps({"complexidade_global": "", "atividades": atv})


def escolher_exemplos(diff: str, banco: list, bm25) -> list:
    if not banco or N_EXEMPLOS <= 0:
        return []
    scores = bm25.get_scores(tokenizar(diff))
    top = sorted(range(len(banco)), key=lambda i: scores[i], reverse=True)[:N_EXEMPLOS]
    return [banco[i] for i in top]


def garantir_modelo(client, modelo):
    try:
        client.show(modelo)
    except ollama.ResponseError:
        print(f"[pull] baixando {modelo} ...", flush=True)
        client.pull(modelo)


def analisar(client, modelo, contexto, commit, schema, complexidade):
    dica = (f"COMPLEXIDADE DO SISTEMA: {complexidade} (use este sufixo nos serviços que variam por complexidade)\n"
            if complexidade else
            "COMPLEXIDADE DO SISTEMA: não identificada na tabela — use o sufixo 'b' (Média) nos serviços que variam por complexidade\n")
    msgs = [
        {"role": "system", "content": INSTRUCOES + "\n\n" + contexto},
        {"role": "user", "content": (
            f"SISTEMA: {commit['projeto']}\n{dica}\n"
            f"ARQUIVOS DO DIFF:\n{status_arquivos(commit['diff'])}\n\n"
            f"GIT DIFF PARA ANALISAR:\n{commit['diff']}")},
    ]
    t0 = time.time()
    resp = client.chat(
        model=modelo,
        messages=msgs,
        format=schema,
        think=False,  # qwen3 e similares: sem bloco de raciocínio, direto no JSON
        options={"temperature": 0, "seed": 42, "num_ctx": NUM_CTX,
                 "num_predict": NUM_PREDICT, "repeat_penalty": 1.1},
    )
    dur = time.time() - t0
    ev, ev_dur = resp.get("eval_count") or 0, (resp.get("eval_duration") or 0) / 1e9
    return resp["message"]["content"], {
        "segundos": round(dur, 1),
        "tokens_prompt": resp.get("prompt_eval_count"),
        "tokens_saida": ev,
        "tok_s": round(ev / ev_dur, 1) if ev_dur else None,
        "truncado": resp.get("done_reason") == "length",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = ollama.Client(host=OLLAMA_HOST)
    regras, catalogo = carregar_docs()
    commits, banco_exemplos = carregar_gabarito()
    bm25_exemplos = BM25Okapi([tokenizar(e["diff"]) for e in banco_exemplos]) if banco_exemplos else None
    tabela = carregar_tabela_hpa(catalogo)
    schema = schema_com_codigos(list(tabela))
    print(f"{len(commits)} commits de gabarito | {len(banco_exemplos)} no banco de exemplos (n={N_EXEMPLOS}) | modelos={MODELOS} modos={MODOS} num_ctx={NUM_CTX}", flush=True)

    resultados = []
    for modelo in MODELOS:
        if modelo != "knn":
            garantir_modelo(client, modelo)
        for modo in MODOS:
            for i, c in enumerate(commits, 1):
                ctx = montar_contexto(modo, c["diff"], regras, catalogo)
                exemplos = escolher_exemplos(c["diff"], banco_exemplos, bm25_exemplos)
                if exemplos:
                    ctx += "\n\n" + bloco_exemplos(exemplos)
                linha = {"modelo": modelo, "modo": modo, "commit": c["id"][:10]}
                try:
                    if modelo == "knn":
                        bruto, perf = relatorio_knn(exemplos), {"segundos": 0, "truncado": False}
                    else:
                      bruto, perf = analisar(client, modelo, ctx, c, schema,
                                           complexidade_do_sistema(catalogo, c["projeto"]))
                    linha.update(perf)
                    if perf["truncado"]:
                        raise RuntimeError(f"loop: atingiu {NUM_PREDICT} tokens sem fechar o JSON")
                    try:
                        rel = consolidar(RelatorioFaturamento.model_validate_json(bruto))
                        linha["json_valido"] = True
                        linha.update(comparar(rel, c["gabarito"], c["diff"], tabela))
                    except ValidationError as e:
                        linha["json_valido"] = False
                        linha["erro"] = str(e)[:300]
                except Exception as e:
                    linha["json_valido"] = False
                    linha["erro"] = f"{type(e).__name__}: {e}"[:300]
                linha["vram_mb"] = vram_mb(client, modelo)
                resultados.append(linha)
                print(f"[{modelo}|{modo}] {i}/{len(commits)} {json.dumps(linha, ensure_ascii=False)}", flush=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    (OUT_DIR / f"resultados-{stamp}.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    (OUT_DIR / f"resumo-{stamp}.md").write_text(resumo_md(resultados))
    print(resumo_md(resultados), flush=True)


def resumo_md(res):
    linhas = [
        "| Modelo | Modo | Commits | JSON válido | Acerto código exato | Acerto serviço | Δ HPA médio | Arq. inventados | s/diff | tok/s | VRAM pico (MB) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    grupos = {}
    for r in res:
        grupos.setdefault((r["modelo"], r["modo"]), []).append(r)
    for (m, modo), rs in grupos.items():
        ok = [r for r in rs if r.get("json_valido")]
        med = lambda k, xs: round(sum(x[k] for x in xs if x.get(k) is not None) / max(len([x for x in xs if x.get(k) is not None]), 1), 2)
        dhpa = round(sum(abs(r["hpa_local"] - r["hpa_gabarito"]) for r in ok) / max(len(ok), 1), 1)
        inv = sum(r["arquivos_inventados"] for r in ok)
        cit = sum(r["arquivos_citados"] for r in ok)
        vram = max((r["vram_mb"] for r in rs if r.get("vram_mb")), default="—")
        linhas.append(
            f"| {m} | {modo} | {len(rs)} | {len(ok)}/{len(rs)} | {med('acerto_codigos', ok)} | {med('acerto_servico', ok)} | {dhpa} "
            f"| {inv}/{cit} | {med('segundos', rs)} | {med('tok_s', rs)} | {vram} |"
        )
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    main()
