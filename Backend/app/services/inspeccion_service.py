from sqlalchemy.orm import Session
from app.models.inspeccion import Inspeccion
from datetime import datetime
from typing import Optional

class InspeccionService:
    @staticmethod
    def aplicar_filtros(
        db: Session,
        id: Optional[str] = None,
        locacion: Optional[str] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        veredicto: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None
    ):
        """
        Genera la query base con todos los filtros aplicados.
        Devuelve el objeto 'query' de SQLAlchemy sin ejecutar (.all() o .count()).
        """
        # 1. Query Base
        query = db.query(Inspeccion)
        
        # 2. Aplicar filtros si existen
        if id:
            # Filtrar por ID (búsqueda parcial)
            query = query.filter(Inspeccion.id.like(f"%{id}%"))
        
        if locacion:
            query = query.filter(Inspeccion.locacion == locacion)
            
        if fecha_inicio and fecha_fin:
            query = query.filter(Inspeccion.fecha_hora >= fecha_inicio, Inspeccion.fecha_hora <= fecha_fin)
        
        # Filtro por veredicto (PASS/FAIL)
        if veredicto:
            if veredicto.upper() == "PASS":
                query = query.filter(Inspeccion.veredicto == "PASS")
            elif veredicto.upper() == "FAIL":
                query = query.filter(Inspeccion.veredicto == "FAIL")
            
        if min_score is not None:
            query = query.filter(Inspeccion.puntaje_total >= min_score)
            
        if max_score is not None:
            query = query.filter(Inspeccion.puntaje_total <= max_score)
            
        return query