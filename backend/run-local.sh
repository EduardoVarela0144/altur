#!/bin/bash

# Script para ejecutar el contenedor localmente

# Construir la imagen
echo "🔨 Construyendo la imagen..."
docker build --platform linux/amd64 -t ghcr.io/eduardovarela0144/bot-image .

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  ADVERTENCIA: No se encontró el archivo .env"
    echo "   Asegúrate de tener las variables de entorno configuradas:"
    echo "   - MONGO_URI"
    echo "   - MONGO_DB_NAME"
    echo "   - DISCORD_TOKEN (opcional)"
    echo "   - PORT (opcional, por defecto 5000)"
    echo ""
    echo "   Ejecutando sin .env (usando variables del sistema)..."
    ENV_FLAG=""
else
    echo "✅ Usando archivo .env"
    ENV_FLAG="--env-file .env"
fi

# Detener y eliminar contenedor si existe
echo "🧹 Limpiando contenedores anteriores..."
docker stop bot-scraping-api 2>/dev/null || true
docker rm bot-scraping-api 2>/dev/null || true

# Ejecutar el contenedor
echo "🚀 Iniciando el contenedor..."
docker run -d \
  --name bot-scraping-api \
  --platform linux/amd64 \
  -p 5000:5000 \
  --shm-size=2gb \
  -v "$(pwd)/storage:/app/storage" \
  -v "$(pwd)/data:/app/data" \
  $ENV_FLAG \
  ghcr.io/eduardovarela0144/bot-image

echo ""
echo "✅ Contenedor iniciado!"
echo "📊 Ver logs con: docker logs -f bot-scraping-api"
echo "🛑 Detener con: docker stop bot-scraping-api"
echo "🌐 Aplicación disponible en: http://localhost:5000"


