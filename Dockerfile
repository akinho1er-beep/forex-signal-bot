FROM python:3.11-slim

LABEL maintainer="Forex Signal Bot"
LABEL description="Bot d'analyse technique Forex avec alertes Telegram"

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le répertoire de logs
RUN mkdir -p /app/logs

# Variable d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Santé check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('https://api.telegram.org')" || exit 1

# Commande par défaut
CMD ["python", "main.py"]
