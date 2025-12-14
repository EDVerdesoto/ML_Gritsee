from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
import pandas as pd
import io

from app.db.session import get_db
from app.models.inspeccion import Inspeccion
from app.schemas.inspeccion_schema import InspeccionResponse, InspeccionUpdate
from app.services.quality_service import QualityService
from app.services.scoring_logic import calcular_puntaje

router = APIRouter()

# ==========================================
# 1. CARGA MASIVA (BATCH UPLOAD)
# ==========================================
@router.post("/batch-upload")
async def cargar_csv_inspecciones(
    file: UploadFile = File(...),
    locacion: str = Form(...), # <--- AQUÍ RECIBIMOS LA LOCACIÓN DEL FRONT
    db: Session = Depends(get_db)
):
    # 1. Validación
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo archivos CSV o Excel")

    # 2. Lectura
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df_raw = pd.read_csv(io.BytesIO(contents), header=None)  
        else:
            df_raw = pd.read_excel(io.BytesIO(contents), header=None)
    except Exception as e:
        print(f"Error lectura: {e}")
        raise HTTPException(status_code=400, detail="Archivo corrupto")

    # 3. Header Discovery (Buscar dónde empieza)
    header_row_index = -1
    for i, row in df_raw.head(20).iterrows():
        row_str = row.astype(str).str.lower().tolist()
        if any("link" in s for s in row_str): # Buscamos "Photo Link" o similar
            header_row_index = i
            break
    
    if header_row_index == -1:
        raise HTTPException(status_code=400, detail="No encontré cabeceras (Photo Link)")

    # 4. Limpieza y Asignación de columnas
    df_raw.columns = df_raw.iloc[header_row_index]
    df = df_raw.iloc[header_row_index + 1 :].reset_index(drop=True)
    
    # Identificar columna Link y Columna Fecha
    col_link = next((c for c in df.columns if "link" in str(c).lower()), None)
    col_fecha = next((c for c in df.columns if "fecha" in str(c).lower() or "date" in str(c).lower()), None)

    if not col_link:
        raise HTTPException(status_code=400, detail="No encontré columna de Links")

    # 5. PREPARAR DATOS PARA EL SERVICIO
    # En lugar de mandar solo links, mandamos una lista de diccionarios con fecha
    datos_procesar = []
    
    for _, row in df.iterrows():
        link = str(row[col_link]).strip()
        if not link.startswith("http"): continue
        
        # Intentar parsear fecha, si no existe o falla, usa HOY
        fecha_obj = datetime.now()
        if col_fecha and pd.notna(row[col_fecha]):
            try:
                # Pandas es inteligente parseando fechas
                fecha_obj = pd.to_datetime(row[col_fecha]).to_pydatetime()
            except:
                pass # Si falla el parseo, se queda con la fecha de hoy
        
        datos_procesar.append({
            "link": link,
            "fecha": fecha_obj
        })

    # 6. INVOCAR AL SERVICIO
    servicio = QualityService(db)
    # OJO: Tienes que actualizar tu quality_service para que acepte este nuevo formato
    # (Ver instrucciones abajo)
    resultados = servicio.procesar_lista_con_metadata(datos_procesar, locacion)

    return {
        "status": "OK",
        "total_procesados": len(resultados),
        "detalle": resultados
    }


# ==========================================
# 2. LISTADO Y FILTROS (GET)
# ==========================================
@router.get("/", response_model=List[InspeccionResponse])
def leer_inspecciones(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    locacion: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    veredicto: Optional[str] = None
):
    query = db.query(Inspeccion)
    
    if locacion:
        query = query.filter(Inspeccion.locacion == locacion)
    if veredicto:
        query = query.filter(Inspeccion.veredicto == veredicto)
    if fecha_inicio:
        query = query.filter(Inspeccion.fecha_hora >= fecha_inicio)
    if fecha_fin:
        # Truco: Sumar 1 día o asegurar que cubra hasta el final del día
        query = query.filter(Inspeccion.fecha_hora <= datetime.combine(fecha_fin, datetime.max.time()))

    registros = query.order_by(Inspeccion.id.desc()).offset(skip).limit(limit).all()
    return registros


# ==========================================
# 3. DETALLE ÚNICO (GET)
# ==========================================
@router.get("/{id}", response_model=InspeccionResponse)
def leer_inspeccion_detalle(id: int, db: Session = Depends(get_db)):
    inspeccion = db.query(Inspeccion).filter(Inspeccion.id == id).first()
    if not inspeccion:
        raise HTTPException(status_code=404, detail="Inspección no encontrada")
    return inspeccion


# ==========================================
# 4. CORRECCIÓN HUMANA (PATCH)
# ==========================================
@router.patch("/{id}", response_model=InspeccionResponse)
def corregir_inspeccion(
    id: int,
    datos_update: InspeccionUpdate,
    db: Session = Depends(get_db)
):
    inspeccion = db.query(Inspeccion).filter(Inspeccion.id == id).first()
    if not inspeccion:
        raise HTTPException(status_code=404, detail="Inspección no encontrada")

    update_data = datos_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inspeccion, key, value)

    # RE-SCORING
    datos_para_scoring = {
        "tiene_burbujas": inspeccion.tiene_burbujas,
        "bordes_sucios": inspeccion.bordes_sucios, 
        "tiene_grasa": inspeccion.tiene_grasa,
        "horneado": inspeccion.horneado_clase,
        "distribucion": inspeccion.distribucion_clase,
        "bordes_limpios": not inspeccion.bordes_sucios 
    }
    
    nuevos_scores = calcular_puntaje(datos_para_scoring)
    
    inspeccion.score_burbujas = nuevos_scores['burbujas']
    inspeccion.score_bordes = nuevos_scores['bordes']
    inspeccion.score_grasa = nuevos_scores['grasa']
    inspeccion.score_horneado = nuevos_scores['horneado']
    inspeccion.score_distribucion = nuevos_scores['distribucion']
    inspeccion.puntaje_total = nuevos_scores['total']
    inspeccion.veredicto = nuevos_scores['veredicto']
    
    db.commit()
    db.refresh(inspeccion)
    return inspeccion


# ==========================================
# 5. OPCIONES PARA FILTROS (METADATA)
# ==========================================
@router.get("/opciones/metadata")
def obtener_opciones_filtro(db: Session = Depends(get_db)):
    """
    Esto alimenta el Dropdown del Frontend.
    """
    locaciones = db.query(Inspeccion.locacion).distinct().all()
    lista_locaciones = [loc[0] for loc in locaciones if loc[0]]
    return {"locaciones": sorted(lista_locaciones)} # Ordenado alfabéticamente