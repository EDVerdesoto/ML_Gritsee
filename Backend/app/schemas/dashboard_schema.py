from pydantic import BaseModel
from typing import Optional
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
    
    # Diferenciales (%)
    diferencial_correctas: Optional[float] = None
    diferencial_promedio: Optional[float] = None
    diferencial_burbujas: Optional[float] = None
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

# --- Esquema para Agrupación por Locación ---
class ResumenPorLocacion(BaseModel):
    """Resumen filtrado por locación"""
    locacion: str
    periodo_inicio: datetime
    periodo_fin: datetime
    resumen: ResumenGeneral
    top_horas_muestras: list[MuestrasPorHora]
    top_dias_incidentes: list[IncidentesPorDia]

# --- Esquema Principal (Respuesta del Endpoint) ---
class DashboardResponse(BaseModel):
    """Respuesta completa del dashboard con todas las métricas"""
    resumen_general: ResumenGeneral
    comparacion_semanal: Optional[ComparacionSemanal] = None
    top_5_horas_muestras: list[MuestrasPorHora]
    top_5_dias_incidentes: list[IncidentesPorDia]
    por_locacion: Optional[ResumenPorLocacion] = None
