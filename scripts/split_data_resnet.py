import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

# Configuracion de rutas relativas al proyecto
# El script se ejecuta desde ML_Gritsee/scripts/
# BASE_DIR apunta a la raiz del proyecto (ML_Gritsee)
BASE_DIR = Path(__file__).resolve().parent.parent

# 1. Ruta de origen: Donde estan los recortes de horneado (dentro de HighQuality)
INPUT_ROOT = BASE_DIR / "datasets" / "Dataset_Stage2_Crops_HighQuality" / "horneado_balanced"

# 2. Ruta de destino: Donde se creara el dataset final estructurado para ResNet
OUTPUT_ROOT = BASE_DIR / "datasets" / "dataset_resnet_horneado"

# 3. Configuracion del Split (80% entrenamiento, 20% validacion)
TRAIN_RATIO = 0.8

def main():
    print(f"Iniciando preparacion de dataset desde: {INPUT_ROOT}")
    
    # Validacion de existencia del directorio de entrada
    if not INPUT_ROOT.exists():
        print(f"[ERROR CRITICO] No se encuentra el directorio de entrada.")
        print(f"Verifica la ruta: {INPUT_ROOT}")
        return

    # Limpieza del directorio de destino si ya existe para evitar mezcla de datos
    if OUTPUT_ROOT.exists():
        print("[INFO] El directorio de destino existe. Eliminando para regenerar...")
        shutil.rmtree(OUTPUT_ROOT)

    # Identificacion de clases basada en subcarpetas (alto, bajo, correcto, etc.)
    classes = [d.name for d in INPUT_ROOT.iterdir() if d.is_dir()]
    print(f"[INFO] Clases identificadas: {classes}")

    if not classes:
        print("[ERROR] No se encontraron subcarpetas de clases. Verifica la estructura de entrada.")
        return

    # Proceso de division y copia por cada clase
    for class_name in classes:
        # Definicion de rutas de destino
        train_dir = OUTPUT_ROOT / 'train' / class_name
        val_dir = OUTPUT_ROOT / 'val' / class_name

        # Creacion de directorios
        train_dir.mkdir(parents=True, exist_ok=True)
        val_dir.mkdir(parents=True, exist_ok=True)

        # Listado de imagenes (soporte para jpg, png, jpeg)
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            images.extend(list((INPUT_ROOT / class_name).glob(ext)))

        # Aleatorizacion para garantizar independencia estadistica
        random.shuffle(images)

        # Calculo del punto de corte
        split_idx = int(len(images) * TRAIN_RATIO)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        print(f"Procesando '{class_name}': {len(train_imgs)} imagenes para Train, {len(val_imgs)} imagenes para Val")

        # Copia de archivos a carpeta de entrenamiento
        for img in train_imgs:
            shutil.copy(img, train_dir / img.name)
        
        # Copia de archivos a carpeta de validacion
        for img in val_imgs:
            shutil.copy(img, val_dir / img.name)

    print("\n[EXITO] Dataset de clasificacion generado correctamente.")
    print(f"Directorio de salida: {OUTPUT_ROOT}")
    print("El dataset esta listo para el entrenamiento de ResNet.")

if __name__ == "__main__":
    main()