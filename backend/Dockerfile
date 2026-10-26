FROM python:3.12-slim

# Evita o buffering dos logs do Python no console do Docker
ENV PYTHONUNBUFFERED=1

# Garante que o Playwright armazene navegadores em local acessível globalmente
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 1. Dependências do sistema + ca-certificates para revogar a CA eMudhra
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libxext6 \
    fonts-liberation \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Atualiza o pip para remover a raiz comprometida embutida nele
RUN pip install --no-cache-dir --upgrade "pip>=26.2.2"

# 3. Instala dependências Python (lembre de ter certifi>=2026.10.19 no requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Instala Chromium para o Playwright no diretório compartilhado
RUN mkdir -p /ms-playwright && playwright install chromium && chmod -R 755 /ms-playwright

# Copia o código do backend
COPY . .

# 5. Cria usuário sem privilégios e configura permissões
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /app /data && \
    chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]