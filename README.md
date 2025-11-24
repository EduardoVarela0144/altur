# Altur - Call Transcription Service

Sistema completo de transcripción y análisis de llamadas con backend, frontend y base de datos MongoDB.

## 🚀 Inicio Rápido con Docker Compose

La forma más fácil de ejecutar todo el sistema es usando Docker Compose desde la raíz del proyecto:

```bash
docker-compose up -d
```

Esto iniciará:
- **MongoDB** en puerto 27017
- **Backend** (Flask) en puerto 5000
- **Frontend** (React) en puerto 5173

### Detener los servicios

```bash
docker-compose down
```

### Ver logs

```bash
docker-compose logs -f
```

### Reconstruir imágenes

```bash
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
altur/
├── backend/              # Servicio Flask (Python)
│   ├── controllers/      # Controladores de API
│   ├── services/         # Servicios (STT, LLM, DB, Auth)
│   ├── routes/           # Rutas de API
│   ├── middleware/       # Middleware de autenticación
│   ├── tests/            # Tests automatizados
│   └── .env              # Variables de entorno (crear desde .env.example)
│
├── frontend/             # Aplicación React (TypeScript)
│   ├── src/
│   │   ├── components/   # Componentes React
│   │   ├── pages/        # Páginas
│   │   ├── hooks/         # React Query hooks
│   │   ├── services/     # Servicios API
│   │   └── types/         # Tipos TypeScript
│   └── .env              # Variables de entorno
│
├── Dockerfile.backend    # Dockerfile para backend
├── Dockerfile.frontend   # Dockerfile para frontend
├── docker-compose.yml    # Orquestación de servicios
└── README.md             # Este archivo
```

## 🔧 Configuración

### Backend

1. Copiar archivo de ejemplo:
```bash
cp backend/.env.example backend/.env
```

2. Editar `backend/.env` con tus credenciales:
```
MONGO_URI=mongodb://mongodb:27017/
MONGO_DB_NAME=call_transcription
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-3.5-turbo
WHISPER_MODEL=base
UPLOAD_FOLDER=uploads
PORT=5000
SECRET_KEY=tu_secret_key_aqui
```

### Frontend

1. Copiar archivo de ejemplo:
```bash
cp frontend/.env.example frontend/.env
```

2. Editar `frontend/.env`:
```
VITE_API_URL=http://localhost:5000
```

## 🏃 Ejecución Local (sin Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentación

- [Backend README](./backend/README.md) - Documentación completa del backend
- [Frontend README](./frontend/README.md) - Documentación del frontend

## 🧪 Testing

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

## 🔐 Autenticación

El sistema incluye autenticación básica:

1. **Registrarse**: Ir a `/login` y hacer clic en "Register"
2. **Iniciar sesión**: Usar las credenciales creadas
3. El token se guarda automáticamente en localStorage

## 📦 Características

### Backend
- ✅ Transcripción de audio con Whisper
- ✅ Análisis con LLM (summary, tags, roles, emotions, intent, mood, insights)
- ✅ API RESTful completa
- ✅ Autenticación básica
- ✅ Filtros por tag y fecha
- ✅ Exportación JSON
- ✅ Analytics endpoint

### Frontend
- ✅ Lista de llamadas con filtros
- ✅ Detalle completo de llamadas
- ✅ Dashboard de analytics
- ✅ Edición de tags (override)
- ✅ Autenticación
- ✅ Diseño responsive con Material UI

## 🐳 Docker

### Construir imágenes individuales

**Backend:**
```bash
docker build -f Dockerfile.backend -t altur-backend .
```

**Frontend:**
```bash
docker build -f Dockerfile.frontend -t altur-frontend .
```

### Ejecutar servicios individuales

Ver `docker-compose.yml` para la configuración completa.

## 📝 Notas

- Los archivos de audio se guardan en `backend/uploads/`
- MongoDB persiste datos en volumen Docker `mongodb_data`
- Los tokens de autenticación expiran después de 24 horas (configurable)

## 🛠️ Troubleshooting

### MongoDB no conecta
- Verificar que el servicio esté corriendo: `docker-compose ps`
- Verificar logs: `docker-compose logs mongodb`

### Backend no inicia
- Verificar variables de entorno en `backend/.env`
- Verificar que OpenAI API key sea válida
- Ver logs: `docker-compose logs backend`

### Frontend no conecta al backend
- Verificar que `VITE_API_URL` en `frontend/.env` apunte al backend correcto
- En Docker: usar `http://backend:5000` en lugar de `http://localhost:5000`

## 📄 Licencia

[Tu licencia aquí]

