# Immagine base leggera (da ECR Public invece che Docker Hub)
FROM public.ecr.aws/docker/library/python:3.12-slim

# Evita prompt interattivi
ENV DEBIAN_FRONTEND=noninteractive

# Installa dipendenze di sistema minime
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installa librerie Python
RUN pip install --no-cache-dir boto3 spotipy

# Copia il codice nello scraper
WORKDIR /app
COPY app.py .

# Imposta l'entrypoint
CMD ["python", "app.py"]
