import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# Carrega variáveis de ambiente
load_dotenv()

class Atividade(BaseModel):
    etapa: str = Field(
        description="Etapa da atividade, deve ser estritamente: Deleção, Inclusão, ou Alteração/Correção"
    )
    titulo: str = Field(
        description="Nome formal da tarefa. Título técnico da ação em primeira pessoa (ex: 'Inclusão de campo de data de nascimento no formulário de cadastro')"
    )
    descricao: str = Field(
        description="Descrição formal da tarefa. O que foi feito tecnicamente no código baseando-se estritamente no diff, escrito em primeira pessoa (ex: 'Eu incluí a coluna dt_nascimento no banco de dados e mapeei o campo no frontend')"
    )
    categoria: str = Field(
        description="Categoria correspondente no catálogo de serviços (ex: 'Manutenções em Sistemas Existentes')"
    )
    codigo_id: str = Field(
        description="Código/ID provável do catálogo de serviços (ex: '21a', '21b', '21c', '21d', '21e', '21g', '62b', '57a')"
    )
    hpa: int = Field(
        description="Horas Previstas para Execução da Atividade (HPA) associada a esta atividade específica"
    )
    arquivos: List[str] = Field(
        description="Lista de arquivos afetados por esta atividade presentes no diff"
    )
    justificativa: str = Field(
        description="Justificativa técnica em primeira pessoa do singular defendendo rigorosamente por que a alteração no código atende à categoria e ao ID do Catálogo de Serviços"
    )

class RelatorioFaturamento(BaseModel):
    complexidade_global: str = Field(
        description="Resumo de 1 ou 2 parágrafos detalhando a complexidade técnica e a narrativa global da intervenção em primeira pessoa do singular"
    )
    atividades: List[Atividade] = Field(
        description="Lista de atividades técnicas independentes identificadas no diff"
    )

MAP_MODELOS = {
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 3.5 Flash": "gemini-3.5-flash",
    "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
    "Gemini 3 Flash": "gemini-3-flash",
    "Gemini 3.1 Flash Lite": "gemini-3.1-flash-lite",
}

def analisar_diff(diff_content: str, prompt_path: str = "Docs/regras-medicao.md", catalogo_path: str = "Docs/catalogo-servicos.md", modelo: str = "Gemini 2.5 Flash") -> RelatorioFaturamento:
    """Send a Git diff to Gemini and return a structured billing report.

    Reads the measurement rules from ``prompt_path`` and the service catalogue
    from ``catalogo_path``, then passes them together with ``diff_content`` to
    the Gemini API using structured JSON output (``response_schema=RelatorioFaturamento``
    and ``temperature=0.1``).

    Model fallback order starts with the requested model, then tries standard models.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave de API do Gemini (GEMINI_API_KEY) não encontrada no arquivo .env")

    # Lê as regras e catálogo locais
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    except Exception as e:
        raise FileNotFoundError(f"Não foi possível carregar o arquivo de regras de {prompt_path}: {e}")

    try:
        with open(catalogo_path, "r", encoding="utf-8") as f:
            # Lemos os primeiros 50000 caracteres se o arquivo for muito grande, ou todo ele.
            # O catálogo completo tem 615 linhas (~97KB), que cabe perfeitamente no contexto do Gemini.
            catalog_text = f.read()
    except Exception as e:
        raise FileNotFoundError(f"Não foi possível carregar o arquivo do catálogo de {catalogo_path}: {e}")

    # Cria o cliente GenAI
    client = genai.Client(api_key=api_key)

    # Prepara o prompt do sistema / contexto
    instrucoes = (
        "Você é um engenheiro de software sênior responsável pelo faturamento de entregas técnicas.\n"
        "Seu papel é receber um Git Diff de alterações e cruzá-lo com o catálogo de faturamento para gerar as atividades.\n"
        "Cruze rigorosamente o catálogo e siga as regras de ouro: uso de primeira pessoa do singular e justificativa profunda.\n"
        "Retorne estritamente o JSON estruturado conforme o esquema definido."
    )

    # Executa a geração de conteúdo com fallback para contornar erros de 503 (alta demanda)
    model_id = MAP_MODELOS.get(modelo, modelo) or "gemini-2.5-flash"
    
    # Lista de fallbacks padrão
    fallbacks = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.5-flash", "gemini-2.5-pro"]
    modelos_para_tentar = [model_id] + [f for f in fallbacks if f != model_id]
    
    # Limpa duplicatas mantendo a ordem
    modelos_para_tentar = list(dict.fromkeys(modelos_para_tentar))
    ultimo_erro = None

    for nome_modelo in modelos_para_tentar:
        try:

            response = client.models.generate_content(
                model=nome_modelo,
                contents=[
                    instrucoes,
                    f"REGRAS DE CONTEXTO (prompt.txt):\n{prompt_text}",
                    f"CATÁLOGO DE SERVIÇOS (catalogo.txt):\n{catalog_text}",
                    f"GIT DIFF PARA ANALISAR:\n{diff_content}"
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RelatorioFaturamento,
                    temperature=0.1
                )
            )
            # Sucesso: Converte e retorna
            dados_json = json.loads(response.text)
            return RelatorioFaturamento(**dados_json)
        except Exception as e:
            msg_erro = str(e)
            # Se for erro de cota, taxa de requisições ou sobrecarga (503, 429, overloaded, etc.), tenta o próximo modelo
            if any(k in msg_erro.lower() for k in ["503", "429", "overloaded", "demand", "quota", "exhausted", "limit"]):
                ultimo_erro = e
                continue
            else:
                # Outros erros (ex: chave inválida, erro de schema) devem quebrar imediatamente
                raise e

    # Se todos falharem
    raise ultimo_erro
