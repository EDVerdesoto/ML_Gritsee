import cv2
import os
import hashlib
import shutil
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Configuracion de directorios y parametros
NPUT_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"
OUTPUT_ROOT = Path.home() / "Practicas" / "Datasets_Procesados"
OUTPUT_YOLO = OUTPUT_ROOT / "Detection_Unique_640"       # Para LabelImg / YOLO
OUTPUT_CLS = OUTPUT_ROOT / "Classification_ResNet_640"

TARGET_SIZE = 640
COLOR_PAD = (0, 0, 0)
VALID_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def calcular_hash(image_path):
    # Genera hash MD5 para identificar imagenes duplicadas
    hasher = hashlib.md5()
    with open(image_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def resize_letterbox(img, new_shape=(640, 640), color=(0, 0, 0)):
    # Redimensiona la imagen manteniendo la relacion de aspecto y agrega padding
    shape = img.shape[:2]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    
    # Calcular nuevas dimensiones
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    
    if shape[::-1] != new_unpad:  
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    
    # Calcular padding necesario
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    top, bottom = dh // 2, dh - (dh // 2)
    left, right = dw // 2, dw - (dw // 2)
    
    # Agregar bordes
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    
    return img

def procesar_para_deteccion_yolo():
    # Modulo 1: Extraer imagenes unicas para dataset YOLO
    if not OUTPUT_YOLO.exists():
        OUTPUT_YOLO.mkdir(parents=True, exist_ok=True)
    
    hashes_vistos = set()
    archivos = [p for p in INPUT_DIR.rglob("*") if p.suffix.lower() in VALID_EXT]
    
    print(f"Procesando {len(archivos)} archivos para dataset YOLO (unicos)...")
    
    for archivo in tqdm(archivos, desc="Filtrando duplicados"):
        file_hash = calcular_hash(archivo)
        
        if file_hash not in hashes_vistos:
            hashes_vistos.add(file_hash)
            
            img = cv2.imread(str(archivo))
            if img is None: continue
            
            img_resized = resize_letterbox(img, (TARGET_SIZE, TARGET_SIZE))
            
            # Guardar con hash como nombre
            nuevo_nombre = OUTPUT_YOLO / f"{file_hash}.jpg"
            cv2.imwrite(str(nuevo_nombre), img_resized)

def procesar_para_clasificacion_resnet():
    # Modulo 2: Replicar estructura y redimensionar para dataset Clasificacion
    archivos = [p for p in INPUT_DIR.rglob("*") if p.suffix.lower() in VALID_EXT]
    
    print(f"Procesando {len(archivos)} archivos para dataset Clasificacion...")
    
    for archivo in tqdm(archivos, desc="Transformando imagenes"):
        rel_path = archivo.relative_to(INPUT_DIR)
        dest_path = OUTPUT_CLS / rel_path
        
        if not dest_path.parent.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        img = cv2.imread(str(archivo))
        if img is None: continue
        
        img_resized = resize_letterbox(img, (TARGET_SIZE, TARGET_SIZE), COLOR_PAD)
        
        # Guardar manteniendo estructura original
        dest_final = dest_path.with_suffix(".jpg")
        cv2.imwrite(str(dest_final), img_resized)

if __name__ == "__main__":
    if not INPUT_DIR.exists():
        print(f"Error: Directorio de entrada '{INPUT_DIR}' no encontrado.")
        exit()

    procesar_para_deteccion_yolo()
    print("Dataset YOLO generado.")
    
    procesar_para_clasificacion_resnet()
    print("Dataset Clasificacion generado.")
    
    print("Proceso finalizado.")