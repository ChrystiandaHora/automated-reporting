"""Classificador POR ARQUIVO do diff -> código do catálogo, agrupado em tarefas por commit.

Por que por arquivo: 92% dos arquivos das tarefas aprovadas pertencem a uma única tarefa.
Classificar cada arquivo (pela estrutura do próprio diff dele) e depois agrupar dá muito mais
exemplos de treino que classificar o commit inteiro, e resolve a quantidade de tarefas.

Treino: tarefas aprovadas (historico, antes de CORTE) casadas com as atividades da análise
(mesmo título) -> arquivos de cada tarefa. Arquivo do diff que não está em nenhuma tarefa = "nenhum".

Agrupamento (teto medido com rótulos perfeitos: ~77% dos commits exatos):
  1 tarefa por código; 22b = 1 tarefa por diretório.

Confiança: o commit só é respondido sozinho se TODOS os arquivos tiverem probabilidade
>= CONFIANCA e o código previsto tiver base (>= MIN_EXEMPLOS). Senão vai para REVISÃO.

    python por_arquivo.py avaliar     # validação cruzada por commit + curva confiança x cobertura
    python por_arquivo.py treinar     # treina com tudo e salva OUT_DIR/modelo-arquivos.joblib
"""
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import MaxAbsScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from catalogo_hpa import carregar_tabela_hpa, hpa_por_codigo, normalizar_codigo  # noqa: E402

DB_PATH = os.environ.get("DB_PATH", "/data/nexus.db")
DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/docs-base"))
OUT_DIR = Path(os.environ.get("OUT_DIR", "/out"))
CORTE = os.environ.get("CORTE", "2026-11")
MIN_EXEMPLOS = int(os.environ.get("MIN_EXEMPLOS", "5"))
CONFIANCA = float(os.environ.get("CONFIANCA", "0.6"))
PESO_MENSAGEM = float(os.environ.get("PESO_MENSAGEM", "0.3"))
C_REG = float(os.environ.get("C_REG", "4.0"))
FOLDS = int(os.environ.get("FOLDS", "10"))
MAX_BLOCO = 20000
NENHUM = "nenhum"
POR_DIRETORIO = {"22b"}  # códigos cuja quantidade segue o nº de diretórios

RE_TESTE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|(_test|\.test|\.spec|test_)[^/]*$", re.I)
EXT_FRONT = {".vue", ".tsx", ".jsx", ".ts", ".js", ".html", ".css", ".scss"}
EXT_BACK = {".py", ".java", ".php", ".go", ".cs", ".kt"}


# --- Diff -> blocos por arquivo --------------------------------------------------
def blocos(diff: str):
    out = []
    for b in re.split(r"(?m)^(?=diff --git )", diff):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", b)
        if not m:
            continue
        st = "novo" if re.search(r"(?m)^new file mode", b) else \
             "removido" if re.search(r"(?m)^deleted file mode", b) else "alterado"
        out.append({"arquivo": m.group(2), "status": st, "bloco": b[:MAX_BLOCO]})
    return out


def casa(caminho: str, lista) -> bool:
    return any(caminho == f or caminho.endswith("/" + f) or f.endswith("/" + caminho) for f in lista)


# --- Dados -------------------------------------------------------------------
def carregar():
    """Lista de commits: {id, mensagem, arquivos: [{arquivo, status, bloco, codigo}], gabarito: Counter}."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    analises = {cid: json.loads(j) for cid, j in con.execute("SELECT commit_id, atividades_json FROM analises")}
    rows = con.execute(
        """SELECT c.id, c.mensagem, c.diff_raw, h.titulo, h.codigo
             FROM historico h JOIN commits c ON c.id = h.commit_id
            WHERE h.enviado_em < ? AND h.codigo IS NOT NULL AND c.diff_raw IS NOT NULL
            ORDER BY c.id, h.id""", (CORTE,)).fetchall()
    con.close()
    commits = {}
    for cid, msg, diff, titulo, cod in rows:
        e = commits.setdefault(cid, {"id": cid, "mensagem": msg or "", "diff": diff,
                                     "tarefas": [], "gabarito": Counter()})
        cod = normalizar_codigo(cod)
        e["gabarito"][cod] += 1
        atv = next((a for a in analises.get(cid) or [] if (a.get("titulo") or "").strip() == (titulo or "").strip()), None)
        e["tarefas"].append((cod, (atv or {}).get("arquivos") or []))
    out = []
    for e in commits.values():
        arqs = blocos(e["diff"])
        for a in arqs:
            cods = [cod for cod, fs in e["tarefas"] if casa(a["arquivo"], fs)]
            a["codigo"] = Counter(cods).most_common(1)[0][0] if cods else NENHUM
        e["arquivos"] = arqs
        out.append(e)
    return out


# --- Características de um arquivo ----------------------------------------------
def texto_arquivo(a) -> str:
    caminho = re.sub(r"[/_.\-]", " ", a["arquivo"])
    add = " ".join(re.findall(r"(?m)^\+(?!\+\+)(.*)$", a["bloco"]))
    rem = " ".join(re.findall(r"(?m)^-(?!--)(.*)$", a["bloco"]))
    ext = os.path.splitext(a["arquivo"])[1].lower().lstrip(".") or "semext"
    return " ".join([f"st_{a['status']} ext_{ext}", caminho,
                     " ".join("add_" + t for t in re.findall(r"[a-zA-Z_]{3,}", add)[:1500]),
                     " ".join("rem_" + t for t in re.findall(r"[a-zA-Z_]{3,}", rem)[:1500])])


def estrut_arquivo(a, n_arquivos_commit: int) -> list:
    p, b = a["arquivo"], a["bloco"]
    ext = os.path.splitext(p)[1].lower()
    teste = bool(RE_TESTE.search(p))
    add = len(re.findall(r"(?m)^\+(?!\+\+)", b))
    rem = len(re.findall(r"(?m)^-(?!--)", b))
    return [a["status"] == "novo", a["status"] == "alterado", a["status"] == "removido", teste,
            ext in EXT_FRONT and not teste, ext in EXT_BACK and not teste,
            ext == ".sql" or "migration" in p.lower(),
            ext in {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg"} or "docker" in p.lower(),
            np.log1p(add), np.log1p(rem), add > 0 and rem == 0, rem > 0 and add == 0,
            len(re.findall(r"(?m)^@@", b)), np.log1p(n_arquivos_commit),
            len(re.findall(r"(?m)^\+\s*(def test_|it\(|test\()", b))]


def amostras(commits):
    X_txt, X_est, X_msg, y, grupo = [], [], [], [], []
    for gi, c in enumerate(commits):
        for a in c["arquivos"]:
            X_txt.append(texto_arquivo(a))
            X_est.append(estrut_arquivo(a, len(c["arquivos"])))
            X_msg.append(c["mensagem"].lower())
            y.append(a.get("codigo", NENHUM))
            grupo.append(gi)
    return X_txt, np.array(X_est, dtype=float), X_msg, np.array(y), np.array(grupo)


class ClassificadorArquivos:
    def fit(self, commits):
        txt, est, msg, y, _ = amostras(commits)
        freq = Counter(y)
        self.conhecidos = {k for k, v in freq.items() if v >= MIN_EXEMPLOS}
        y = np.array([k if k in self.conhecidos else "raro" for k in y])
        self.tf = TfidfVectorizer(min_df=2, max_features=30000, sublinear_tf=True, ngram_range=(1, 2))
        self.tf_msg = TfidfVectorizer(min_df=2, sublinear_tf=True)
        self.esc = MaxAbsScaler()
        X = self._x(txt, est, msg, fit=True)
        self.lr = LogisticRegression(C=C_REG, class_weight="balanced", solver="liblinear", max_iter=2000)
        from sklearn.multiclass import OneVsRestClassifier
        self.lr = OneVsRestClassifier(self.lr).fit(X, y)
        return self

    def _x(self, txt, est, msg, fit=False):
        f = (lambda v, d: v.fit_transform(d)) if fit else (lambda v, d: v.transform(d))
        partes = [f(self.tf, txt), csr_matrix(est)]
        if PESO_MENSAGEM > 0:
            partes.append(f(self.tf_msg, msg) * PESO_MENSAGEM)
        X = hstack(partes).tocsr()
        return f(self.esc, X)

    def prever_commit(self, c):
        """-> {codigos: Counter, revisar: bool, motivos: [...], por_arquivo: [...]}"""
        if not c["arquivos"]:
            return {"codigos": Counter(), "revisar": True, "motivos": ["diff sem arquivos"], "por_arquivo": []}
        txt = [texto_arquivo(a) for a in c["arquivos"]]
        est = np.array([estrut_arquivo(a, len(c["arquivos"])) for a in c["arquivos"]], dtype=float)
        P = self.lr.predict_proba(self._x(txt, est, [c["mensagem"].lower()] * len(txt)))
        P = P / P.sum(axis=1, keepdims=True)
        classes = self.lr.classes_
        por_arq, motivos = [], []
        arqs_por_codigo = defaultdict(list)
        for a, p in zip(c["arquivos"], P):
            k = int(np.argmax(p))
            cod, conf = classes[k], float(p[k])
            por_arq.append({"arquivo": a["arquivo"], "codigo": cod, "confianca": round(conf, 2)})
            if cod == "raro":
                motivos.append(f"{a['arquivo']}: tipo de alteração com pouca base aprovada")
            elif conf < CONFIANCA:
                motivos.append(f"{a['arquivo']}: incerto ({cod} {conf:.0%})")
            if cod not in (NENHUM, "raro"):
                arqs_por_codigo[cod].append(a["arquivo"])
        cods = Counter({cod: (len({os.path.dirname(f) for f in fs}) if cod in POR_DIRETORIO else 1)
                        for cod, fs in arqs_por_codigo.items()})
        if not cods:
            motivos.append("nenhum arquivo faturável identificado")
        return {"codigos": cods, "revisar": bool(motivos), "motivos": motivos, "por_arquivo": por_arq}


# --- Avaliação -----------------------------------------------------------------
def avaliar():
    commits = carregar()
    tabela = carregar_tabela_hpa((DOCS_DIR / "catalogo-servicos.md").read_text(encoding="utf-8"))
    H = lambda cods: sum((hpa_por_codigo(tabela, k) or 0) * v for k, v in cods.items())
    res, acertos_arq, total_arq = [], 0, 0
    idx = np.arange(len(commits))
    for tr, te in GroupKFold(FOLDS).split(idx, groups=idx):
        m = ClassificadorArquivos().fit([commits[i] for i in tr])
        for i in te:
            c = commits[i]
            p = m.prever_commit(c)
            for pa, a in zip(p["por_arquivo"], c["arquivos"]):
                total_arq += 1
                acertos_arq += pa["codigo"] == a["codigo"]
            confs = [pa["confianca"] for pa in p["por_arquivo"]] or [0]
            res.append({"commit": c["id"][:10], "gabarito": dict(c["gabarito"]), "previsto": dict(p["codigos"]),
                        "exato": p["codigos"] == c["gabarito"], "revisar": p["revisar"], "motivos": p["motivos"][:5],
                        "conf_min": min(confs), "erro_hpa": abs(H(p["codigos"]) - H(c["gabarito"]))})

    def bloco(rs):
        n = max(len(rs), 1)
        return {"commits": len(rs), "exato_%": round(100 * sum(r["exato"] for r in rs) / n, 1),
                "erro_hpa_medio": round(sum(r["erro_hpa"] for r in rs) / n, 2)}

    auto = [r for r in res if not r["revisar"]]
    curva = []
    for t in [0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]:
        sel = [r for r in res if r["conf_min"] >= t and not any("pouca base" in mm or "nenhum arquivo" in mm for mm in r["motivos"])]
        b = bloco(sel)
        curva.append({"confianca": t, "cobertura_%": round(100 * len(sel) / len(res), 1), **b})
    resumo = {"acerto_por_arquivo_%": round(100 * acertos_arq / max(total_arq, 1), 1),
              "todos": bloco(res), "respondidos_sozinho": {**bloco(auto), "cobertura_%": round(100 * len(auto) / len(res), 1)},
              "curva_confianca_x_cobertura": curva,
              "params": {"MIN_EXEMPLOS": MIN_EXEMPLOS, "CONFIANCA": CONFIANCA, "PESO_MENSAGEM": PESO_MENSAGEM, "C_REG": C_REG}}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "classificador-arquivos-avaliacao.json").write_text(
        json.dumps({"resumo": resumo, "commits": res}, ensure_ascii=False, indent=2))
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


def treinar():
    import joblib
    m = ClassificadorArquivos().fit(carregar())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(m, OUT_DIR / "modelo-arquivos.joblib")
    print(f"modelo salvo; códigos aprendidos: {sorted(m.conhecidos)}")


if __name__ == "__main__":
    {"avaliar": avaliar, "treinar": treinar}[sys.argv[1] if len(sys.argv) > 1 else "avaliar"]()
