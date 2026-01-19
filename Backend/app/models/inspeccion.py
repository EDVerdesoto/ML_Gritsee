from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Index
from datetime import datetime
from app.db.session import Base

class Inspeccion(Base):
    __tablename__ = "inspecciones"

    # --- 1. IDENTIFICACIÓN ---
    id = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, default=datetime.now, index=True) # Índice para ordenar por fecha
    locacion = Column(String, index=True) # Local 
    aws_link = Column(String) # Link de la foto/video
    # se usa index=True porque se puede filtrar por locacion 
    # se usa nullable=False para campos obligatorios
    
    # --- 2. RESULTADOS DE LA IA (LO QUE VIO EL MODELO) ---
    # ResNet Burbujas (Si/No)
    tiene_burbujas = Column(Boolean, default=True)
    
    # ResNet Bordes (Limpios/Sucios) - OJO: True = Sucios (Incidente)
    bordes_sucios = Column(Boolean, default=True)
    
    # OpenCV Distribución (Correcta, Aceptable, media, mala, deficiente)
    distribucion_clase = Column(String, default="Deficiente")
    
    # ResNet Horneado (Correcto, Alto, Bajo, Insuficiente, Excesivo)
    horneado_clase = Column(String, default="Insuficiente")
    
    # ResNet Grasa (Si/No) - True = Tiene Grasa
    tiene_grasa = Column(Boolean, default=True)

    # --- 3. PUNTAJES CALCULADOS (LAS REGLAS DE NEGOCIO) ---
    score_burbujas = Column(Integer, default=0)      # 30 o 0
    score_bordes = Column(Integer, default=0)        # 15 o 0
    score_distribucion = Column(Integer, default=0)  # 30, 20, 15, 5, 0
    score_horneado = Column(Integer, default=0)      # 15, 5, 5, 0, 0
    score_grasa = Column(Integer, default=0)         # 10 o 0
    
    # --- 4. VEREDICTO FINAL ---
    puntaje_total = Column(Integer, default=0, index=True)  # Índice para ordenar por puntaje
    veredicto = Column(String, default="FAIL")       # PASS / FAIL
    
    # Índice compuesto para consultas frecuentes (locacion + fecha)
    __table_args__ = (
        Index('idx_locacion_fecha', 'locacion', 'fecha_hora'),
    )