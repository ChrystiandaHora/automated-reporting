"""Classificador de commits -> códigos do catálogo (com quantidade), treinado nas tarefas aprovadas.

Uso (dentro do container):
    python classificador.py avaliar     # validação cruzada: acerto, cobertura, erro de HPA
    python classificador.py treinar     # treina com tudo e salva o modelo em OUT_DIR/modelo.joblib

Ideia:
  * Cada commit vira um vetor de características: texto (mensagem + caminhos + linhas +/-)
    em TF-IDF, mais sinais estruturais do diff (arquivos novos/alterados/removidos, testes,
    frontend/backend, SQL, config...).
  * Para cada código com base suficiente (>= MIN_EXEMPLOS commits), um classificador binário
    diz se o código está presente; um segundo modelo prevê QUANTAS vezes (1, 2, 3+...).
  * Confiança: se algum código fica na "zona de dúvida" de probabilidade, ou o commit se parece
    pouco com qualquer commit aprovado, a resposta é marcada como REVISAR (sinaliza o usuário).
  * HPA sai da tabela do catálogo (catalogo_hpa.py), nunca do modelo.
"""
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold
from sklearn.preprocessing import MaxAbsScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from catalogo_hpa import carregar_tabela_hpa, hpa_por_codigo, normalizar_codigo  # noqa: E402

DB_PATH = os.environ.get("DB_PATH", "/data/nexus.db")
DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/docs-base"))
OUT_DIR = Path(os.environ.get("OUT_DIR", "/out"))
CORTE = os.environ.get("CORTE", "2026-11")
MIN_EXEMPLOS = int(os.environ.get("MIN_EXEMPLOS", "4"))
LIMIAR_SIM = float(os.environ.get("LIMIAR_SIM", "0.5"))     # prob >= -> código presente
ZONA_DUVIDA = float(os.environ.get("ZONA_DUVIDA", "0.25"))  # |prob - 0.5| < zona -> dúvida
SIM_MINIMA = float(os.environ.get("SIM_MINIMA", "0.10"))    # similaridade mínima com algum aprovado
FOLDS = int(os.environ.get("FOLDS", "10"))
SEMENTE = int(os.environ.get("SEMENTE", "7"))
# A mensagem do commit é só contexto auxiliar (regra do catálogo: quem decide é o diff).
# Fica num bloco separado com peso ajustável; 0 = ignora a mensagem.
PESO_MENSAGEM = float(os.environ.get("PESO_MENSAGEM", "0.5"))
MAX_TEXTO = 60000  # caracteres do diff usados no texto (diffs gigantes são cortados)


# --- Dados -------------------------------------------------------------------
def carregar():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    rows = con.execute(
        """SELECT c.id, c.projeto, c.mensagem, c.diff_raw, h.codigo
             FROM historico h JOIN commits c ON c.id = h.commit_id
            WHERE h.enviado_em < ? AND h.codigo IS NOT NULL AND c.diff_raw IS NOT NULL
            ORDER BY c.id, h.id""", (CORTE,)).fetchall()
    con.close()
    commits = {}
    for cid, proj, msg, diff, cod in rows:
        e = commits.setdefault(cid, {"id": cid, "projeto": proj or "", "mensagem": msg or "",
                                     "diff": diff, "codigos": Counter()})
        e["codigos"][normalizar_codigo(cod)] += 1
    return list(commits.values())


# --- Características -----------------------------------------------------------
RE_TESTE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|(_test|\.test|\.spec|test_)[^/]*$", re.I)
EXT_FRONT = {".vue", ".tsx", ".jsx", ".ts", ".js", ".html", ".css", ".scss"}
EXT_BACK = {".py", ".java", ".php", ".go", ".cs", ".kt"}


def arquivos(diff: str):
    out = []
    for bloco in re.split(r"(?m)^(?=diff --git )", diff):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", bloco)
        if not m:
            continue
        st = "novo" if re.search(r"(?m)^new file mode", bloco) else \
             "removido" if re.search(r"(?m)^deleted file mode", bloco) else "alterado"
        add = len(re.findall(r"(?m)^\+(?!\+\+)", bloco))
        rem = len(re.findall(r"(?m)^-(?!--)", bloco))
        out.append((m.group(2), st, add, rem))
    return out


def estruturais(c) -> list:
    arqs = arquivos(c["diff"])
    def n(f): return sum(1 for a in arqs if f(a))
    ext = lambda p: os.path.splitext(p)[1].lower()
    teste = lambda a: bool(RE_TESTE.search(a[0]))
    front = lambda a: ext(a[0]) in EXT_FRONT and not teste(a)
    back = lambda a: ext(a[0]) in EXT_BACK and not teste(a)
    v = [
        len(arqs), n(lambda a: a[1] == "novo"), n(lambda a: a[1] == "alterado"), n(lambda a: a[1] == "removido"),
        n(teste), n(lambda a: teste(a) and a[1] == "novo"), n(lambda a: teste(a) and a[1] == "alterado"),
        n(front), n(lambda a: front(a) and a[1] == "novo"), n(back), n(lambda a: back(a) and a[1] == "novo"),
        n(lambda a: ext(a[0]) == ".sql" or "migration" in a[0].lower()),
        n(lambda a: ext(a[0]) in {".yml", ".yaml", ".json", ".toml", ".ini", ".env", ".cfg"} or "docker" in a[0].lower()),
        sum(a[2] for a in arqs), sum(a[3] for a in arqs),
        len(re.findall(r"(?m)^\+\s*def test_|^\+\s*(it|test)\(", c["diff"])),  # nº de testes adicionados
    ]
    return [np.log1p(x) for x in v]


def texto_diff(c) -> str:
    """Texto vindo SÓ do diff: caminhos + status dos arquivos + tokens das linhas adicionadas/removidas."""
    caminhos = " ".join(re.sub(r"[/_.\-]", " ", a[0]) + f" st_{a[1]}" for a in arquivos(c["diff"]))
    d = c["diff"][:MAX_TEXTO]
    add = " ".join(re.findall(r"(?m)^\+(?!\+\+)(.*)$", d))
    rem = " ".join(re.findall(r"(?m)^-(?!--)(.*)$", d))
    return " ".join([caminhos,
                     " ".join("add_" + t for t in re.findall(r"[a-zA-Z_]{3,}", add)[:3000]),
                     " ".join("rem_" + t for t in re.findall(r"[a-zA-Z_]{3,}", rem)[:3000])])


def texto_mensagem(c) -> str:
    msg = c["mensagem"].lower()
    tipo = re.match(r"\s*(\w+)", msg)
    return (f"tipo_{tipo.group(1)} " if tipo else "") + msg


class Classificador:
    def __init__(self):
        self.tfidf = TfidfVectorizer(min_df=2, max_features=20000, sublinear_tf=True, ngram_range=(1, 2))
        self.tfidf_msg = TfidfVectorizer(min_df=2, sublinear_tf=True)
        self.escala = MaxAbsScaler()  # põe as características estruturais na mesma escala do texto
        self.presenca, self.qtd, self.codigos = {}, {}, []

    def _x(self, commits, fit=False):
        txt = [texto_diff(c) for c in commits]
        t = self.tfidf.fit_transform(txt) if fit else self.tfidf.transform(txt)
        e = csr_matrix(np.array([estruturais(c) for c in commits]))
        blocos = [t, e]
        if PESO_MENSAGEM > 0:
            msg = [texto_mensagem(c) for c in commits]
            m = self.tfidf_msg.fit_transform(msg) if fit else self.tfidf_msg.transform(msg)
            blocos.append(m * PESO_MENSAGEM)
        X = hstack(blocos).tocsr()
        X = self.escala.fit_transform(X) if fit else self.escala.transform(X)
        return X, t

    def treinar(self, commits):
        X, self._t_treino = self._x(commits, fit=True)
        freq = Counter(cod for c in commits for cod in c["codigos"])
        self.codigos = [k for k, v in freq.items() if v >= MIN_EXEMPLOS]
        self.raros = sorted(set(freq) - set(self.codigos))
        for cod in self.codigos:
            y = np.array([1 if cod in c["codigos"] else 0 for c in commits])
            self.presenca[cod] = LogisticRegression(C=4.0, class_weight="balanced", solver="liblinear").fit(X, y)
            idx = np.where(y == 1)[0]
            q = np.array([min(commits[i]["codigos"][cod], 4) for i in idx])
            if len(set(q)) > 1:
                self.qtd[cod] = Ridge(alpha=1.0).fit(X[idx], q)
            else:
                self.qtd[cod] = int(q[0]) if len(q) else 1
        return self

    def prever(self, commits):
        X, t = self._x(commits)
        sim_max = (t @ self._t_treino.T).max(axis=1).toarray().ravel()
        out = []
        for i in range(X.shape[0]):
            cods, duvidas = Counter(), []
            for cod in self.codigos:
                p = self.presenca[cod].predict_proba(X[i])[0, 1]
                if abs(p - 0.5) < ZONA_DUVIDA:
                    duvidas.append(f"{cod} ({p:.0%})")
                if p >= LIMIAR_SIM:
                    m = self.qtd[cod]
                    cods[cod] = int(np.clip(round(float(m.predict(X[i])[0])), 1, 4)) if hasattr(m, "predict") else m
            motivos = []
            if duvidas:
                motivos.append("dúvida em " + ", ".join(duvidas))
            if sim_max[i] < SIM_MINIMA:
                motivos.append(f"pouco parecido com a base aprovada (sim {sim_max[i]:.2f})")
            if not cods:
                motivos.append("nenhum código conhecido se aplica")
            out.append({"codigos": cods, "revisar": bool(motivos), "motivos": motivos})
        return out


# --- Avaliação -----------------------------------------------------------------
def hpa(tabela, cods: Counter) -> float:
    return sum((hpa_por_codigo(tabela, c) or 0) * q for c, q in cods.items())


def avaliar():
    commits = carregar()
    tabela = carregar_tabela_hpa((DOCS_DIR / "catalogo-servicos.md").read_text(encoding="utf-8"))
    res = []
    for tr, te in KFold(FOLDS, shuffle=True, random_state=SEMENTE).split(commits):
        modelo = Classificador().treinar([commits[i] for i in tr])
        for i, p in zip(te, modelo.prever([commits[i] for i in te])):
            g = commits[i]["codigos"]
            res.append({"commit": commits[i]["id"][:10], "gabarito": dict(g), "previsto": dict(p["codigos"]),
                        "exato": p["codigos"] == g, "revisar": p["revisar"], "motivos": p["motivos"],
                        "erro_hpa": abs(hpa(tabela, p["codigos"]) - hpa(tabela, g)),
                        "acerto_codigos": sum((p["codigos"] & g).values()) / max(sum(g.values()), 1),
                        "tem_raro": any(c in modelo.raros or c not in modelo.codigos for c in g)})
    auto = [r for r in res if not r["revisar"]]
    pct = lambda xs, k: 100 * sum(r[k] for r in xs) / max(len(xs), 1)
    media = lambda xs, k: sum(r[k] for r in xs) / max(len(xs), 1)
    resumo = {
        "commits": len(res),
        "todos": {"exato_%": round(pct(res, "exato"), 1), "acerto_codigos_%": round(100 * media(res, "acerto_codigos"), 1),
                  "erro_hpa_medio": round(media(res, "erro_hpa"), 2)},
        "respondidos_sozinho": {"cobertura_%": round(100 * len(auto) / len(res), 1),
                                "exato_%": round(pct(auto, "exato"), 1),
                                "erro_hpa_medio": round(media(auto, "erro_hpa"), 2)},
        "sinalizados_para_revisao": len(res) - len(auto),
        "params": {"MIN_EXEMPLOS": MIN_EXEMPLOS, "LIMIAR_SIM": LIMIAR_SIM, "ZONA_DUVIDA": ZONA_DUVIDA,
                   "SIM_MINIMA": SIM_MINIMA, "FOLDS": FOLDS, "PESO_MENSAGEM": PESO_MENSAGEM},
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "classificador-avaliacao.json").write_text(json.dumps({"resumo": resumo, "commits": res},
                                                                     ensure_ascii=False, indent=2))
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


def treinar():
    import joblib
    modelo = Classificador().treinar(carregar())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, OUT_DIR / "modelo.joblib")
    print(f"modelo salvo: {len(modelo.codigos)} códigos aprendidos, raros (sempre revisão): {modelo.raros}")


if __name__ == "__main__":
    {"avaliar": avaliar, "treinar": treinar}[sys.argv[1] if len(sys.argv) > 1 else "avaliar"]()
