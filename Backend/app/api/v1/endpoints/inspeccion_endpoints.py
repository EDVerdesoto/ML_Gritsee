from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.quality_service import QualityService

import pandas as pd 
import io 


router = APIRouter()

#se usa @ porque es un decorador que muestra que la funcion se activa al hacer POST
@router.post("/batch-upload")
async def cargar_csv_inspecciones( 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validar que el archivo sea CSV o Excel
    if not file.filename.endswith(('.csv', '.xlsx')): 
        raise HTTPException(status_code=400, detail="Solo archivos CSV o Excel")

    # ler el contenido del archivo 
    contents = await file.read() # await porque es async y debe esperar que el archivo sea procesado

    # Convertir a DataFrame de pandas
    # io envuelve los bytes y disfraza el contenido para que parezca un archivo
    try: 
        if file.filename.endswith('.csv'):
            df_raw = pd.read_csv(io.BytesIO(contents), header=None)  
        else:
            df_raw = pd.read_excel(io.BytesIO(contents), header=None)
    except Exception as e:
        print(f"Error al leer el archivo: {e}") # ver en consola
        raise HTTPException(status_code=400, detail=f"Archivo corrupto o ilegible ")

    header_row_index = -1

    #recorrer las primeras filas para encontrar los headers
    for i, row in df_raw.head(10).iterrows():
        row_str = row.astype(str).str.lower().tolist()
        if any("link" in s for s in row_str) and any("fecha" in s for s in row_str):
            header_row_index = i
            break
    
    if header_row_index == -1:
        raise HTTPException(status_code=400, detail="No encontré los encabezados (Photo Link, Fecha) en las primeras filas.")
    
    #asignar los nombres de las columnas
    df_raw.columns = df_raw.iloc[header_row_index]

    #eliminar filas basura
    df = df_raw.iloc[header_row_index + 1 :].reset_index(drop=True)

    # INVOCAR AL SERVICIO
    servicio = QualityService(db)
    resultados = servicio.procesar_batch(df)

    return {
        "status": "OK",
        "total_procesados": len(resultados),
        "detalle": resultados
    }