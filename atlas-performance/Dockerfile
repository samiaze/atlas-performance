# Image de base : Python 3.11 Slim (Légère et performante)
FROM python:3.11-slim

# Définition des variables d'environnement
# Empêche Python de créer des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Force la sortie standard à être non-bufferisée (logs en temps réel)
ENV PYTHONUNBUFFERED=1

# Répertoire de travail dans le conteneur
WORKDIR /app

# Installation des dépendances système
# gcc : nécessaire pour compiler certaines libs Python
# postgresql-client : utile pour debugger la DB depuis le conteneur app
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source (sera surchargé par le volume en dev, mais utile pour la prod)
COPY . .

# La commande de démarrage est gérée par docker-compose