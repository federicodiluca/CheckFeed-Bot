# Base
FROM python:3.12-slim

# Working directory dentro Docker
WORKDIR /usr/src/app

# Copia tutto
COPY . .

# Installa dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esegui main.py
CMD ["python", "main.py"]
