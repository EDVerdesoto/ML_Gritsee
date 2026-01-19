from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# 1. Definir dónde se guardará el archivo .db
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "production.db"

# Crear la URL de conexión para SQLite  

# CAMBIAR EN PRODUCCIÓN 
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 2. Crear el Motor (Engine)
# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Crear la Fábrica de Sesiones
# Cada vez que alguien pida datos, usaremos una instancia de SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base para los modelos
Base = declarative_base()
#declarative_base() crea una clase base que nuestros modelos de base de datos heredarán

# Función de dependencia para obtener la DB en cada endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
        # se usa yield db para que FastAPI pueda manejar la apertura y cierre de la sesión automáticamente
    finally:
        db.close()
        # se asegura que la sesión se cierre al final