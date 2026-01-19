from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard_schema import DashboardResponse, TendenciaHistoricaResponse

router = APIRouter()

@router.get("/resumen", response_model=DashboardResponse)
def obtener_dashboard(
    locacion: str = Query(None, description="Filtrar por locación específica"),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal del dashboard con todas las métricas:
    
    - **Resumen general**: Total de muestras, pizzas correctas/incorrectas, promedios, incidentes
    - **Comparación semanal**: Semana actual vs anterior con diferenciales
    - **Top 5 horas**: Horas del día con más muestras
    - **Top 5 días**: Días con más incidentes
    - **Por locación**: Resumen específico si se filtra por locación
    
    ### Ejemplos de uso:
    - `/api/v1/dashboard/resumen` - Dashboard completo (todas las locaciones)
    - `/api/v1/dashboard/resumen?locacion=Molino` - Solo locación "Molino"
    """
    service = DashboardService(db)
    return service.generar_dashboard_completo(locacion=locacion)

@router.get("/metricas/basicas")
def obtener_metricas_basicas(
    locacion: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint simplificado con solo los totales básicos:
    - Total de muestras
    - Pizzas correctas/incorrectas
    - Calificación promedio
    """
    service = DashboardService(db)
    resumen = service.calcular_resumen_general(locacion=locacion)
    
    return {
        "total_muestras": resumen.total_muestras,
        "pizzas_correctas": resumen.pizzas_correctas,
        "pizzas_incorrectas": resumen.pizzas_incorrectas,
        "porcentaje_correctas": resumen.porcentaje_correctas,
        "calificacion_promedio": resumen.calificacion_promedio
    }

@router.get("/comparacion/semanal")
def obtener_comparacion_semanal(
    locacion: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Compara semana actual vs anterior con diferenciales de:
    - % Pizzas correctas
    - Calificación promedio
    - % Pizzas con burbujas
    - % Distribución deficiente/mala
    """
    service = DashboardService(db)
    return service.calcular_comparacion_semanal(locacion=locacion)

@router.get("/horas/top")
def obtener_top_horas(
    top: int = Query(5, ge=1, le=24, description="Número de horas a mostrar"),
    locacion: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Top N horas del día con más muestras tomadas
    """
    service = DashboardService(db)
    return service.obtener_muestras_por_hora(top=top, locacion=locacion)

@router.get("/dias/incidentes")
def obtener_dias_incidentes(
    top: int = Query(5, ge=1, le=30, description="Número de días a mostrar"),
    locacion: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Top N días con más incidentes (pizzas FAIL)
    Incluye hora_critica: la hora (0-23) con más fallos ese día
    """
    service = DashboardService(db)
    return service.obtener_dias_con_mas_incidentes(top=top, locacion=locacion)


@router.get("/top-inspecciones")
def obtener_top_inspecciones_semana(
    top: int = Query(10, ge=1, le=50, description="Número de inspecciones a mostrar"),
    locacion: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Top N inspecciones de la última semana de datos, ordenadas por puntaje (desc).
    Toma la semana basada en la última fecha registrada en la BD.
    """
    service = DashboardService(db)
    return service.obtener_top_inspecciones_semana(top=top, locacion=locacion)


# ==========================================
# CHECK 6: ENDPOINT DE TENDENCIAS HISTÓRICAS
# ==========================================
@router.get("/tendencias", response_model=TendenciaHistoricaResponse)
def obtener_tendencias_historicas(
    group_by: Literal["week", "month"] = Query("week", description="Agrupar por 'week' o 'month'"),
    periodos: int = Query(12, ge=1, le=52, description="Número de períodos a incluir"),
    locacion: str = Query(None, description="Filtrar por locación"),
    db: Session = Depends(get_db)
):
    """
    CHECK 6: Tendencias históricas para gráficos de líneas.
    
    Devuelve una lista cronológica de períodos con métricas agregadas:
    - promedio_puntaje: Para graficar evolución de calidad
    - porcentaje_correctas: Tasa de éxito
    - Desglose de defectos: burbujas, grasa, bordes, distribución
    
    ### Ejemplos de uso:
    - `/api/v1/dashboard/tendencias?group_by=week&periodos=12` - Últimas 12 semanas
    - `/api/v1/dashboard/tendencias?group_by=month&periodos=6` - Últimos 6 meses
    - `/api/v1/dashboard/tendencias?group_by=month&locacion=Molino` - Por locación
    
    ### Respuesta ejemplo:
    ```json
    {
        "agrupacion": "month",
        "periodos": [
            {"periodo": "Octubre", "promedio_puntaje": 78.5, "porcentaje_correctas": 65.2, ...},
            {"periodo": "Noviembre", "promedio_puntaje": 82.1, "porcentaje_correctas": 71.8, ...}
        ]
    }
    ```
    """
    service = DashboardService(db)
    return service.obtener_tendencia_historica(
        group_by=group_by,
        locacion=locacion,
        ultimos_periodos=periodos
    )
