FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN pip install --no-cache-dir "scikit-learn>=1.5" "numpy>=1.26" "scipy>=1.13" "joblib>=1.4"
RUN useradd -m -u 1000 app
WORKDIR /app
COPY catalogo_hpa.py /app/catalogo_hpa.py
COPY classificador/ /app/classificador/
USER app
ENTRYPOINT ["python"]
CMD ["/app/classificador/por_arquivo.py", "avaliar"]
