# Usa un'immagine Python leggera
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /usr/src/app

# Installa prima le dipendenze (layer cache più efficace)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia i file di progetto (config.json e data/ sono esclusi da .dockerignore
# e vengono montati come volume da docker-compose)
COPY . .

# Crea directory persistente per dati e log
RUN mkdir -p data/logs

# Avvia il bot
CMD ["python", "main.py"]
