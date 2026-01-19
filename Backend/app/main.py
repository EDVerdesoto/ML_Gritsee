from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base
from app.models import inspeccion  
from app.models import user 
from app.api.v1.endpoints import inspeccion_endpoints, dashboard_endpoints, auth_endpoints 
from contextlib import asynccontextmanager
from app.core.model_loader import model_manager

# --- CREACIÓN DE TABLAS ---
# Al importar 'user' arriba, SQLAlchemy ya sabe que debe crear la tabla 'users'
Base.metadata.create_all(bind=engine)

# --- CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando servidor y cargando modelos de IA")
    model_manager.load_models() 
    yield
    print("Apagando servidor")

# --- CONFIGURACIÓN DE LA API ---
app = FastAPI(
    title="API Control Calidad Pizzas",
    description="Sistema de inspección automatizada con Computer Vision",
    version="1.0.0",
    lifespan=lifespan 
)

# --- CONFIGURACIÓN CORS ---
# 2. En production, 'origins' NO puede ser ["*"], debe ser el dominio real.
origins = [
    "http://localhost:5173", 
    "http://localhost:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# --- RUTAS BÁSICAS ---

@app.get("/")
def read_root():
    return {
        "sistema": "Gritsee Quality Control AI",
        "estado": "ONLINE",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "db_connected": True}

# --- ROUTERS DE LA API ---

# 1. Router de Inspecciones
app.include_router(
    inspeccion_endpoints.router,
    prefix="/api/v1/inspecciones",
    tags=["Inspecciones"]
)

# 2. Router de Dashboard
app.include_router(
    dashboard_endpoints.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

# 3. Router de Autenticación
app.include_router(
    auth_endpoints.router,
    prefix="/api/v1/auth", 
    tags=["Auth"]
)