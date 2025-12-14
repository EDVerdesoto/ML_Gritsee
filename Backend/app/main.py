from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base
from app.models import inspeccion  # Importante: Importar los modelos para que SQLAlchemy los vea
from app.api.v1.endpoints import inspeccion_endpoints
from contextlib import asynccontextmanager
from app.core.model_loader import model_manager

# --- CREACIÓN DE TABLAS ---
# Si las tablas no existen, se crean basándose en los modelos definidos
Base.metadata.create_all(bind=engine)

# --- CICLO DE VIDA (LIFESPAN) ---
# Esta es la solución al error de Windows.
# Los modelos se cargarán SOLO UNA VEZ cuando el servidor arranque.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Al arrancar:
    print("Iniciando servidor y cargando modelos de IA")
    model_manager.load_models() # <--- AQUÍ CARGAMOS LOS MODELOS
    yield
    # 2. Al apagar:
    print("Apagando servidor")

# --- CONFIGURACIÓN DE LA API ---
app = FastAPI(
    title="API Control Calidad Pizzas",
    description="Sistema de inspección automatizada con Computer Vision",
    version="1.0.0"
)

# --- CONFIGURACIÓN CORS (CRÍTICO PARA FRONTEND) ---
# Comunicacion de react con bacvkend
origins = [
    "http://localhost",
    "http://localhost:3000", # Puerto común de React
    "http://localhost:5173", # Puerto común de Vite
    "*"                      # Permitir todo (solo para desarrollo/MVP) TODO !!!! borrar en producción !!!!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Quién puede llamar a la API  
    allow_credentials=True,
    allow_methods=["*"],         # Permitir todos los métodos (GET, POST, etc.) TODO !! MODIFICAR EN PRODUCCIÓN !!
    allow_headers=["*"],         # Permitir todos los headers TODO !! MODIFICAR EN PRODUCCIÓN !!
)

# --- RUTAS BÁSICAS ---

@app.get("/")
def read_root():
    """Endpoint raíz para verificar que la API está viva."""
    return {
        "sistema": "Gritsee Quality Control AI",
        "estado": "ONLINE",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Endpoint de salud para monitoreo."""
    return {"status": "ok", "db_connected": True}

# --- AQUÍ IMPORTAREMOS TUS FUTUROS ROUTERS ---
# TODO : Importar y agregar routers de endpoints aquí

app.include_router(
    inspeccion_endpoints.router,
    prefix="/api/v1/inspecciones", #control de versiones, si saco v2, solo cambio aqui
    tags=["Carga de Datos"]
)