from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

# --- Esquema para Resumen General ---
class ResumenGeneral(BaseModel):
    """Estadísticas globales del sistema"""
    total_muestras: int
    pizzas_correctas: int
    pizzas_incorrectas: int
    porcentaje_correctas: float
    calificacion_promedio: float
    
    # Desglose de incidentes
    pizzas_con_burbujas: int
    pizzas_con_grasa: int
    pizzas_bordes_sucios: int
    distribucion_deficiente: int
    distribucion_mala: int
    
    # Porcentajes de incidentes
    porcentaje_burbujas: float
    porcentaje_distribucion_deficiente: float
    porcentaje_distribucion_mala: float

# --- Esquema para Comparación Temporal ---
class ComparacionSemanal(BaseModel):
    """Comparación entre semana actual y anterior"""
    semana_actual: ResumenGeneral
    semana_anterior: Optional[ResumenGeneral] = None
    
    # Diferenciales (%) - TODOS los defectos para barras de progreso del Dashboard
    diferencial_correctas: Optional[float] = None
    diferencial_promedio: Optional[float] = None
    diferencial_burbujas: Optional[float] = None
    diferencial_grasa: Optional[float] = None           # CHECK 1: Exceso de Grasa
    diferencial_bordes: Optional[float] = None          # CHECK 1: Bordes Sucios
    diferencial_dist_deficiente: Optional[float] = None
    diferencial_dist_mala: Optional[float] = None

# --- Esquema para Agrupación por Hora ---
class MuestrasPorHora(BaseModel):
    """Muestras agrupadas por hora del día"""
    hora: int  # 0-23
    cantidad_muestras: int
    pizzas_correctas: int
    pizzas_incorrectas: int
    calificacion_promedio: float

# --- Esquema para Agrupación por Día ---
class IncidentesPorDia(BaseModel):
    """Incidentes agrupados por día"""
    fecha: datetime
    total_muestras: int
    total_incidentes: int
    porcentaje_incidentes: float
    hora_critica: Optional[int] = None  # CHECK 2: Hora (0-23) con más fallos ese día

# --- Esquema para Agrupación por Locación ---
class ResumenPorLocacion(BaseModel):
    """Resumen filtrado por locación"""
    locacion: str
    periodo_inicio: datetime
    periodo_fin: datetime
    resumen: ResumenGeneral
    top_horas_muestras: list[MuestrasPorHora]
    top_dias_incidentes: list[IncidentesPorDia]

# --- CHECK 3: Esquema para distribución de clases (Gráficos de Donas) ---
class DistribucionClases(BaseModel):
    """Conteo de cada clase de distribución - SIEMPRE devuelve todas las claves"""
    correcto: int = 0
    aceptable: int = 0
    media: int = 0
    mala: int = 0
    deficiente: int = 0

class HorneadoClases(BaseModel):
    """Conteo de cada clase de horneado - SIEMPRE devuelve todas las claves"""
    correcto: int = 0
    alto: int = 0
    bajo: int = 0
    insuficiente: int = 0
    excesivo: int = 0

# --- CHECK 6: Esquema para Tendencias Históricas ---
class PeriodoTendencia(BaseModel):
    """Un punto en la línea de tendencia"""
    periodo: str              # "Semana 45", "Noviembre", "2024-W45", etc.
    fecha_inicio: datetime
    fecha_fin: datetime
    total_muestras: int
    promedio_puntaje: float
    porcentaje_correctas: float
    # Desglose de defectos para análisis detallado
    porcentaje_burbujas: float
    porcentaje_grasa: float
    porcentaje_bordes_sucios: float
    porcentaje_dist_deficiente: float
    porcentaje_dist_mala: float

class TendenciaHistoricaResponse(BaseModel):
    """Respuesta de tendencias para gráficos de líneas"""
    agrupacion: str           # "week" o "month"
    periodos: list[PeriodoTendencia]

# --- Esquema Principal (Respuesta del Endpoint) ---
class DashboardResponse(BaseModel):
    """Respuesta completa del dashboard con todas las métricas"""
    resumen_general: ResumenGeneral
    comparacion_semanal: Optional[ComparacionSemanal] = None
    top_5_horas_muestras: list[MuestrasPorHora]
    top_5_dias_incidentes: list[IncidentesPorDia]
    por_locacion: Optional[ResumenPorLocacion] = None
    # CHECK 3: Distribución de clases para gráficos de donas
    distribucion_clases: Optional[DistribucionClases] = None
    horneado_clases: Optional[HorneadoClases] = None
    # Período de la semana actual para mostrar en el header
    periodo_semana: Optional[str] = None
