from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard_schema import DashboardResponse

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
    """
    service = DashboardService(db)
    return service.obtener_dias_con_mas_incidentes(top=top, locacion=locacion)
