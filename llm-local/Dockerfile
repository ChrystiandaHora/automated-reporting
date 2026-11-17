FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir "ollama>=0.4" "pydantic>=2" "rank_bm25>=0.2.2"
RUN useradd -m -u 1000 bench
WORKDIR /app
COPY benchmark_llm_local.py catalogo_hpa.py ./
USER bench
CMD ["python", "benchmark_llm_local.py"]
