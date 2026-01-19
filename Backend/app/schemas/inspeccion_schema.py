from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 1. Esquema Base (Datos comunes)
# estos son datos comunes porque se usan en Create y Response
class InspeccionBase(BaseModel):
    locacion: str 
    aws_link: str

# 2. Esquema para CREAR (Lo que genera la IA internamente)
#este esquema es para crear instancias nuevas en la DB (POST)
class InspeccionCreate(InspeccionBase):
    # Resultados IA
    tiene_burbujas: bool
    bordes_sucios: bool
    distribucion_clase: str
    horneado_clase: str
    tiene_grasa: bool

    # Scores
    score_burbujas: int
    score_bordes: int
    score_distribucion: int
    score_horneado: int
    score_grasa: int
    
    # Final
    puntaje_total: int
    veredicto: str

# 3. Esquema para RESPONDER (Lo que ve el Frontend)
# este esquema toma todo lo de Create y agrega campos generados por la DB para que el frontend los vea y use
class InspeccionResponse(InspeccionCreate):
    id: int
    fecha_hora: datetime
    aws_link: Optional[str] = None
    horneado_clase: Optional[str] = None     
    distribucion_clase: Optional[str] = None 
    
    class Config:
        from_attributes = True # Antes se llamaba orm_mode

class InspeccionUpdate(BaseModel):
    tiene_burbujas: Optional[int] = None  # Acepta 0/1
    bordes_sucios: Optional[int] = None   # Acepta 0/1
    tiene_grasa: Optional[int] = None     # Acepta 0/1
    horneado_clase: Optional[str] = None
    distribucion_clase: Optional[str] = None
