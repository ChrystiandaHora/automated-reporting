FROM python:3.12-slim

# Evita o buffering dos logs do Python no console do Docker
ENV PYTHONUNBUFFERED=1

# Dependências do sistema necessárias para o Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python primeiro (cache de camada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala Chromium para o Playwright
RUN playwright install chromium && playwright install-deps chromium

# Copia o código do backend
COPY . .

# Diretório de dados persistido via volume
RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
