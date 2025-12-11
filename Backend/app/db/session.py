from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# 1. Definir dónde se guardará el archivo .db
# Se guardará en la carpeta 'backend/data/'
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "production.db"

# Crear la URL de conexión para SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 2. Crear el Motor (Engine)
# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Crear la Fábrica de Sesiones
# Cada vez que alguien pida datos, usaremos una instancia de SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#autoflush=False significa que los cambios no se enviarán automáticamente a la base de datos hasta que se llame a .commit()
#autocommit=False significa que las transacciones no se confirmarán automáticamente hasta llamar a .commit()
#bind=engine conecta esta sesión con nuestro motor de base de datos creado arriba

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