from sqlalchemy.orm import Session
from sqlalchemy import func, extract, Integer, case
from datetime import datetime, timedelta
from app.models.inspeccion import Inspeccion
from app.schemas.dashboard_schema import (
    ResumenGeneral, 
    ComparacionSemanal, 
    MuestrasPorHora, 
    IncidentesPorDia,
    ResumenPorLocacion,
    DashboardResponse,
    DistribucionClases,
    HorneadoClases,
    PeriodoTendencia,
    TendenciaHistoricaResponse
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
        """Calcula el resumen general de métricas usando agregaciones SQL (optimizado)"""
        
        # Base query con filtros
        filters = []
        if fecha_inicio:
            filters.append(Inspeccion.fecha_hora >= fecha_inicio)
        if fecha_fin:
            filters.append(Inspeccion.fecha_hora <= fecha_fin)
        if locacion:
            filters.append(Inspeccion.locacion == locacion)
        
        # Query agregada - todo en una sola consulta SQL
        result = self.db.query(
            func.count(Inspeccion.id).label('total'),
            func.sum(case((Inspeccion.veredicto == "PASS", 1), else_=0)).label('correctas'),
            func.avg(Inspeccion.puntaje_total).label('promedio'),
            func.sum(case((Inspeccion.tiene_burbujas == True, 1), else_=0)).label('con_burbujas'),
            func.sum(case((Inspeccion.tiene_grasa == True, 1), else_=0)).label('con_grasa'),
            func.sum(case((Inspeccion.bordes_sucios == True, 1), else_=0)).label('bordes_sucios'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'deficiente', 1), else_=0)).label('dist_deficiente'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'mala', 1), else_=0)).label('dist_mala'),
        ).filter(*filters).first()
        
        total = result.total or 0
        
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
        
        correctas = result.correctas or 0
        incorrectas = total - correctas
        promedio = result.promedio or 0
        con_burbujas = result.con_burbujas or 0
        con_grasa = result.con_grasa or 0
        bordes_sucios = result.bordes_sucios or 0
        dist_deficiente = result.dist_deficiente or 0
        dist_mala = result.dist_mala or 0
        
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
            # CHECK 1: Agregar diferenciales de grasa y bordes
            comparacion.diferencial_grasa = round(
                (resumen_actual.pizzas_con_grasa / max(resumen_actual.total_muestras, 1) * 100) -
                (resumen_anterior.pizzas_con_grasa / max(resumen_anterior.total_muestras, 1) * 100), 2
            )
            comparacion.diferencial_bordes = round(
                (resumen_actual.pizzas_bordes_sucios / max(resumen_actual.total_muestras, 1) * 100) -
                (resumen_anterior.pizzas_bordes_sucios / max(resumen_anterior.total_muestras, 1) * 100), 2
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
        
        # CHECK 2: Calcular hora crítica (moda de hora con más fallos) para cada día
        dias_con_hora = []
        for r in resultados:
            hora_critica = self._obtener_hora_critica_del_dia(r.fecha, locacion)
            dias_con_hora.append(
                IncidentesPorDia(
                    fecha=r.fecha,
                    total_muestras=r.total,
                    total_incidentes=r.incidentes or 0,
                    porcentaje_incidentes=round(((r.incidentes or 0) / r.total) * 100, 2),
                    hora_critica=hora_critica
                )
            )
        
        return dias_con_hora
    
    def _obtener_hora_critica_del_dia(self, fecha, locacion: str = None) -> int:
        """CHECK 2: Obtiene la hora (0-23) con más fallos para un día específico"""
        query = self.db.query(
            extract('hour', Inspeccion.fecha_hora).label('hora'),
            func.count(Inspeccion.id).label('fallos')
        ).filter(
            func.date(Inspeccion.fecha_hora) == fecha,
            Inspeccion.veredicto == "FAIL"
        )
        
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
        
        resultado = query.group_by('hora').order_by(
            func.count(Inspeccion.id).desc()
        ).first()
        
        return int(resultado.hora) if resultado else None
    
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
        
        # CHECK 3: Obtener distribución de clases para gráficos de donas
        distribucion_clases = self.obtener_distribucion_clases(locacion=locacion)
        horneado_clases = self.obtener_horneado_clases(locacion=locacion)
        
        # Calcular período de semana basado en los datos de la BD (última fecha registrada)
        query_fechas = self.db.query(func.max(Inspeccion.fecha_hora), func.min(Inspeccion.fecha_hora))
        if locacion:
            query_fechas = query_fechas.filter(Inspeccion.locacion == locacion)
        fecha_max, fecha_min = query_fechas.first()
        
        meses_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        if fecha_max:
            # Tomar la última semana de datos (7 días antes de la fecha más reciente)
            fin_semana = fecha_max
            inicio_semana = fin_semana - timedelta(days=6)
            periodo_semana = f"{meses_es[inicio_semana.month-1]} {inicio_semana.day} - {meses_es[fin_semana.month-1]} {fin_semana.day}"
        else:
            periodo_semana = "Sin datos"
        
        return DashboardResponse(
            resumen_general=resumen_general,
            comparacion_semanal=comparacion,
            top_5_horas_muestras=top_horas,
            top_5_dias_incidentes=top_dias,
            por_locacion=por_locacion,
            distribucion_clases=distribucion_clases,
            horneado_clases=horneado_clases,
            periodo_semana=periodo_semana
        )
    
    # ==========================================
    # CHECK 3: MÉTODOS PARA GRÁFICOS DE DONAS
    # ==========================================
    def obtener_distribucion_clases(self, locacion: str = None) -> DistribucionClases:
        """
        CHECK 3: Devuelve TODAS las clases de distribución usando agregación SQL (optimizado).
        Garantiza que el JSON siempre tenga las 5 claves.
        """
        filters = [Inspeccion.locacion == locacion] if locacion else []
        
        # Query agregada en SQL
        result = self.db.query(
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'correcto', 1), else_=0)).label('correcto'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'aceptable', 1), else_=0)).label('aceptable'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'media', 1), else_=0)).label('media'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'mala', 1), else_=0)).label('mala'),
            func.sum(case((func.lower(Inspeccion.distribucion_clase) == 'deficiente', 1), else_=0)).label('deficiente'),
        ).filter(*filters).first()
        
        return DistribucionClases(
            correcto=result.correcto or 0,
            aceptable=result.aceptable or 0,
            media=result.media or 0,
            mala=result.mala or 0,
            deficiente=result.deficiente or 0
        )
    
    def obtener_horneado_clases(self, locacion: str = None) -> HorneadoClases:
        """
        CHECK 3: Devuelve TODAS las clases de horneado usando agregación SQL (optimizado).
        Garantiza que el JSON siempre tenga las 5 claves.
        """
        filters = [Inspeccion.locacion == locacion] if locacion else []
        
        # Query agregada en SQL
        result = self.db.query(
            func.sum(case((func.lower(Inspeccion.horneado_clase) == 'correcto', 1), else_=0)).label('correcto'),
            func.sum(case((func.lower(Inspeccion.horneado_clase) == 'alto', 1), else_=0)).label('alto'),
            func.sum(case((func.lower(Inspeccion.horneado_clase) == 'bajo', 1), else_=0)).label('bajo'),
            func.sum(case((func.lower(Inspeccion.horneado_clase) == 'insuficiente', 1), else_=0)).label('insuficiente'),
            func.sum(case((func.lower(Inspeccion.horneado_clase) == 'excesivo', 1), else_=0)).label('excesivo'),
        ).filter(*filters).first()
        
        return HorneadoClases(
            correcto=result.correcto or 0,
            alto=result.alto or 0,
            bajo=result.bajo or 0,
            insuficiente=result.insuficiente or 0,
            excesivo=result.excesivo or 0
        )
    
    def obtener_top_inspecciones_semana(self, top: int = 10, locacion: str = None) -> list:
        """
        Devuelve las top N inspecciones de la última semana de datos,
        ordenadas por puntaje_total descendente.
        La semana se calcula basada en la última fecha en la BD.
        Mejores: puntaje >= 70, Peores: puntaje < 70
        """
        # Obtener la fecha más reciente de los datos
        query_fecha = self.db.query(func.max(Inspeccion.fecha_hora))
        if locacion:
            query_fecha = query_fecha.filter(Inspeccion.locacion == locacion)
        fecha_max = query_fecha.scalar()
        
        if not fecha_max:
            return {"mejores": [], "peores": []}
        
        # Calcular inicio de la semana (7 días antes de la última fecha)
        inicio_semana = fecha_max - timedelta(days=6)
        
        # Base query filtrada por semana y locación
        base_query = self.db.query(Inspeccion).filter(
            Inspeccion.fecha_hora >= inicio_semana,
            Inspeccion.fecha_hora <= fecha_max
        )
        
        if locacion:
            base_query = base_query.filter(Inspeccion.locacion == locacion)
        
        # Top mejores: puntaje >= 70, ordenadas desc
        mejores = base_query.filter(
            Inspeccion.puntaje_total >= 70
        ).order_by(Inspeccion.puntaje_total.desc()).limit(top).all()
        
        # Top peores: puntaje < 70, ordenadas asc
        peores = base_query.filter(
            Inspeccion.puntaje_total < 70
        ).order_by(Inspeccion.puntaje_total.asc()).limit(top).all()
        
        # Función helper para convertir a dict
        def to_dict(i):
            return {
                "id": i.id,
                "aws_link": i.aws_link,
                "puntaje_total": i.puntaje_total,
                "fecha_hora": i.fecha_hora.isoformat() if i.fecha_hora else None,
                "locacion": i.locacion,
                "veredicto": i.veredicto
            }
        
        return {
            "mejores": [to_dict(i) for i in mejores],
            "peores": [to_dict(i) for i in peores]
        }
    
    # ==========================================
    # CHECK 6: TENDENCIAS HISTÓRICAS
    # ==========================================
    def obtener_tendencia_historica(
        self, 
        group_by: str = "week",  # "week" o "month"
        locacion: str = None,
        ultimos_periodos: int = 12  # Por defecto últimas 12 semanas o meses
    ) -> TendenciaHistoricaResponse:
        """
        CHECK 6: Agrupa puntajes y defectos dinámicamente por Semana o Mes.
        Devuelve lista cronológica para graficar líneas de tendencia.
        
        Args:
            group_by: "week" para agrupar por semana ISO, "month" para mes
            locacion: Filtro opcional por locación
            ultimos_periodos: Cuántos períodos hacia atrás incluir
        
        Returns:
            TendenciaHistoricaResponse con lista de PeriodoTendencia
        """
        ahora = datetime.now()
        periodos_resultado = []
        
        if group_by == "week":
            # Iterar últimas N semanas
            for i in range(ultimos_periodos - 1, -1, -1):
                # Calcular inicio y fin de cada semana
                fecha_ref = ahora - timedelta(weeks=i)
                # Lunes de esa semana
                inicio_semana = fecha_ref - timedelta(days=fecha_ref.weekday())
                inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
                fin_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                # Obtener datos de esa semana
                periodo_data = self._calcular_periodo(inicio_semana, fin_semana, locacion)
                if periodo_data:
                    periodo_data.periodo = f"Sem {inicio_semana.isocalendar()[1]}"
                    periodos_resultado.append(periodo_data)
        
        elif group_by == "month":
            # Iterar últimos N meses
            for i in range(ultimos_periodos - 1, -1, -1):
                # Calcular mes objetivo
                mes_actual = ahora.month - i
                año_actual = ahora.year
                
                while mes_actual <= 0:
                    mes_actual += 12
                    año_actual -= 1
                
                # Primer día del mes
                inicio_mes = datetime(año_actual, mes_actual, 1, 0, 0, 0)
                
                # Último día del mes
                if mes_actual == 12:
                    fin_mes = datetime(año_actual + 1, 1, 1) - timedelta(seconds=1)
                else:
                    fin_mes = datetime(año_actual, mes_actual + 1, 1) - timedelta(seconds=1)
                
                # Obtener datos de ese mes
                periodo_data = self._calcular_periodo(inicio_mes, fin_mes, locacion)
                if periodo_data:
                    # Nombre del mes en español
                    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    periodo_data.periodo = meses_es[mes_actual - 1]
                    periodos_resultado.append(periodo_data)
        
        return TendenciaHistoricaResponse(
            agrupacion=group_by,
            periodos=periodos_resultado
        )
    
    def _calcular_periodo(
        self, 
        fecha_inicio: datetime, 
        fecha_fin: datetime, 
        locacion: str = None
    ) -> PeriodoTendencia:
        """Calcula las métricas agregadas para un período específico"""
        query = self.db.query(Inspeccion).filter(
            Inspeccion.fecha_hora >= fecha_inicio,
            Inspeccion.fecha_hora <= fecha_fin
        )
        
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
        
        inspecciones = query.all()
        total = len(inspecciones)
        
        if total == 0:
            return None  # No hay datos para este período
        
        # Calcular métricas
        correctas = sum(1 for i in inspecciones if i.veredicto == "PASS")
        suma_puntajes = sum(i.puntaje_total for i in inspecciones)
        con_burbujas = sum(1 for i in inspecciones if i.tiene_burbujas)
        con_grasa = sum(1 for i in inspecciones if i.tiene_grasa)
        bordes_sucios = sum(1 for i in inspecciones if i.bordes_sucios)
        dist_deficiente = sum(1 for i in inspecciones if i.distribucion_clase.lower() == "deficiente")
        dist_mala = sum(1 for i in inspecciones if i.distribucion_clase.lower() == "mala")
        
        return PeriodoTendencia(
            periodo="",  # Se asigna después
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_muestras=total,
            promedio_puntaje=round(suma_puntajes / total, 2),
            porcentaje_correctas=round((correctas / total) * 100, 2),
            porcentaje_burbujas=round((con_burbujas / total) * 100, 2),
            porcentaje_grasa=round((con_grasa / total) * 100, 2),
            porcentaje_bordes_sucios=round((bordes_sucios / total) * 100, 2),
            porcentaje_dist_deficiente=round((dist_deficiente / total) * 100, 2),
            porcentaje_dist_mala=round((dist_mala / total) * 100, 2)
        )
