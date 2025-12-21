from sqlalchemy.orm import Session
from sqlalchemy import func, extract, Integer
from datetime import datetime, timedelta
from app.models.inspeccion import Inspeccion
from app.schemas.dashboard_schema import (
    ResumenGeneral, 
    ComparacionSemanal, 
    MuestrasPorHora, 
    IncidentesPorDia,
    ResumenPorLocacion,
    DashboardResponse
)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def calcular_resumen_general(
        self, 
        fecha_inicio: datetime = None, 
        fecha_fin: datetime = None,
        locacion: str = None
    ) -> ResumenGeneral:
        """Calcula el resumen general de métricas"""
        
        # Base query
        query = self.db.query(Inspeccion)
        
        # Filtros opcionales
        if fecha_inicio:
            query = query.filter(Inspeccion.fecha_hora >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Inspeccion.fecha_hora <= fecha_fin)
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
        
        inspecciones = query.all()
        total = len(inspecciones)
        
        if total == 0:
            return ResumenGeneral(
                total_muestras=0,
                pizzas_correctas=0,
                pizzas_incorrectas=0,
                porcentaje_correctas=0.0,
                calificacion_promedio=0.0,
                pizzas_con_burbujas=0,
                pizzas_con_grasa=0,
                pizzas_bordes_sucios=0,
                distribucion_deficiente=0,
                distribucion_mala=0,
                porcentaje_burbujas=0.0,
                porcentaje_distribucion_deficiente=0.0,
                porcentaje_distribucion_mala=0.0
            )
        
        # Contadores
        correctas = sum(1 for i in inspecciones if i.veredicto == "PASS")
        incorrectas = total - correctas
        suma_puntajes = sum(i.puntaje_total for i in inspecciones)
        promedio = suma_puntajes / total
        
        # Incidentes específicos
        con_burbujas = sum(1 for i in inspecciones if i.tiene_burbujas)
        con_grasa = sum(1 for i in inspecciones if i.tiene_grasa)
        bordes_sucios = sum(1 for i in inspecciones if i.bordes_sucios)
        dist_deficiente = sum(1 for i in inspecciones if i.distribucion_clase.lower() == "deficiente")
        dist_mala = sum(1 for i in inspecciones if i.distribucion_clase.lower() == "mala")
        
        return ResumenGeneral(
            total_muestras=total,
            pizzas_correctas=correctas,
            pizzas_incorrectas=incorrectas,
            porcentaje_correctas=round((correctas / total) * 100, 2),
            calificacion_promedio=round(promedio, 2),
            pizzas_con_burbujas=con_burbujas,
            pizzas_con_grasa=con_grasa,
            pizzas_bordes_sucios=bordes_sucios,
            distribucion_deficiente=dist_deficiente,
            distribucion_mala=dist_mala,
            porcentaje_burbujas=round((con_burbujas / total) * 100, 2),
            porcentaje_distribucion_deficiente=round((dist_deficiente / total) * 100, 2),
            porcentaje_distribucion_mala=round((dist_mala / total) * 100, 2)
        )
    
    def calcular_comparacion_semanal(self, locacion: str = None) -> ComparacionSemanal:
        """Compara métricas de semana actual vs anterior"""
        ahora = datetime.now()
        
        # Semana actual (últimos 7 días)
        inicio_actual = ahora - timedelta(days=7)
        resumen_actual = self.calcular_resumen_general(inicio_actual, ahora, locacion)
        
        # Semana anterior (días 8-14 hacia atrás)
        inicio_anterior = ahora - timedelta(days=14)
        fin_anterior = ahora - timedelta(days=7)
        resumen_anterior = self.calcular_resumen_general(inicio_anterior, fin_anterior, locacion)
        
        # Calcular diferenciales
        comparacion = ComparacionSemanal(
            semana_actual=resumen_actual,
            semana_anterior=resumen_anterior if resumen_anterior.total_muestras > 0 else None
        )
        
        if resumen_anterior.total_muestras > 0:
            comparacion.diferencial_correctas = round(
                resumen_actual.porcentaje_correctas - resumen_anterior.porcentaje_correctas, 2
            )
            comparacion.diferencial_promedio = round(
                resumen_actual.calificacion_promedio - resumen_anterior.calificacion_promedio, 2
            )
            comparacion.diferencial_burbujas = round(
                resumen_actual.porcentaje_burbujas - resumen_anterior.porcentaje_burbujas, 2
            )
            comparacion.diferencial_dist_deficiente = round(
                resumen_actual.porcentaje_distribucion_deficiente - 
                resumen_anterior.porcentaje_distribucion_deficiente, 2
            )
            comparacion.diferencial_dist_mala = round(
                resumen_actual.porcentaje_distribucion_mala - 
                resumen_anterior.porcentaje_distribucion_mala, 2
            )
        
        return comparacion
    
    def obtener_muestras_por_hora(self, top: int = 5, locacion: str = None) -> list[MuestrasPorHora]:
        """Agrupa muestras por hora del día y devuelve las top N horas con más muestras"""
        query = self.db.query(
            extract('hour', Inspeccion.fecha_hora).label('hora'),
            func.count(Inspeccion.id).label('total'),
            func.sum(func.cast(Inspeccion.veredicto == "PASS", Integer)).label('correctas'),
            func.avg(Inspeccion.puntaje_total).label('promedio')
        )
        
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
        
        resultados = query.group_by('hora').order_by(func.count(Inspeccion.id).desc()).limit(top).all()
        
        return [
            MuestrasPorHora(
                hora=int(r.hora),
                cantidad_muestras=r.total,
                pizzas_correctas=r.correctas or 0,
                pizzas_incorrectas=r.total - (r.correctas or 0),
                calificacion_promedio=round(r.promedio, 2) if r.promedio else 0.0
            )
            for r in resultados
        ]
    
    def obtener_dias_con_mas_incidentes(self, top: int = 5, locacion: str = None) -> list[IncidentesPorDia]:
        """Agrupa por día y devuelve los días con más incidentes (más pizzas FAIL)"""
        query = self.db.query(
            func.date(Inspeccion.fecha_hora).label('fecha'),
            func.count(Inspeccion.id).label('total'),
            func.sum(func.cast(Inspeccion.veredicto == "FAIL", Integer)).label('incidentes')
        )
        
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
        
        resultados = query.group_by('fecha').order_by(
            func.sum(func.cast(Inspeccion.veredicto == "FAIL", Integer)).desc()
        ).limit(top).all()
        
        return [
            IncidentesPorDia(
                fecha=r.fecha,
                total_muestras=r.total,
                total_incidentes=r.incidentes or 0,
                porcentaje_incidentes=round(((r.incidentes or 0) / r.total) * 100, 2)
            )
            for r in resultados
        ]
    
    def generar_dashboard_completo(self, locacion: str = None) -> DashboardResponse:
        """Genera el dashboard completo con todas las métricas"""
        
        # 1. Resumen general (todas las muestras históricas)
        resumen_general = self.calcular_resumen_general(locacion=locacion)
        
        # 2. Comparación semanal
        comparacion = self.calcular_comparacion_semanal(locacion=locacion)
        
        # 3. Top 5 horas con más muestras
        top_horas = self.obtener_muestras_por_hora(top=5, locacion=locacion)
        
        # 4. Top 5 días con más incidentes
        top_dias = self.obtener_dias_con_mas_incidentes(top=5, locacion=locacion)
        
        # 5. Si hay locación específica, agregar resumen detallado
        por_locacion = None
        if locacion:
            # Obtener rango de fechas
            primera = self.db.query(func.min(Inspeccion.fecha_hora)).filter(
                Inspeccion.locacion == locacion
            ).scalar()
            ultima = self.db.query(func.max(Inspeccion.fecha_hora)).filter(
                Inspeccion.locacion == locacion
            ).scalar()
            
            if primera and ultima:
                por_locacion = ResumenPorLocacion(
                    locacion=locacion,
                    periodo_inicio=primera,
                    periodo_fin=ultima,
                    resumen=resumen_general,
                    top_horas_muestras=top_horas,
                    top_dias_incidentes=top_dias
                )
        
        return DashboardResponse(
            resumen_general=resumen_general,
            comparacion_semanal=comparacion,
            top_5_horas_muestras=top_horas,
            top_5_dias_incidentes=top_dias,
            por_locacion=por_locacion
        )
