import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

# --- CONFIGURACION ---
# Incidente a procesar: horneado, distribucion, grasa, burbujas, bordes
INCIDENTES_VALIDOS = ['horneado', 'distribucion', 'grasa', 'burbujas', 'bordes']
print("\nSelecciona el incidente a entrenar:")
print(f"Opciones: {', '.join(INCIDENTES_VALIDOS)}")

while True:
    INCIDENTE_ACTUAL = input(">>> ").strip().lower()
    if INCIDENTE_ACTUAL in INCIDENTES_VALIDOS:
        break
    print(f"ERROR: '{INCIDENTE_ACTUAL}' no es valido. Intenta de nuevo.")

# Mapeo de nombre logico a nombre real de carpeta
# Se asume que las carpetas en origen ya no tienen sufijos como '_balanced'
TRAIN_RATIO = 0.8

# --- RUTAS ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_ROOT = BASE_DIR / "datasets" / "Dataset_Stage2_Crops_HighQuality" / INCIDENTE_ACTUAL
OUTPUT_ROOT = BASE_DIR / "datasets" / f"dataset_resnet_{INCIDENTE_ACTUAL}"

def main():
    print(f"Procesando dataset para: {INCIDENTE_ACTUAL}")
    print(f"Origen: {INPUT_ROOT}")
    
    if not INPUT_ROOT.exists():
        print(f"Error: No se encuentra el directorio de origen.")
        return

    if OUTPUT_ROOT.exists():
        print("El directorio de destino existe. Eliminando...")
        shutil.rmtree(OUTPUT_ROOT)

    classes = [d.name for d in INPUT_ROOT.iterdir() if d.is_dir()]
    print(f"Clases detectadas: {classes}")

    if not classes:
        print("Error: No se encontraron subcarpetas de clases.")
        return

    total_imgs = 0
    for class_name in classes:
        (OUTPUT_ROOT / 'train' / class_name).mkdir(parents=True, exist_ok=True)
        (OUTPUT_ROOT / 'val' / class_name).mkdir(parents=True, exist_ok=True)

        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            images.extend(list((INPUT_ROOT / class_name).glob(ext)))

        random.shuffle(images)

        split_idx = int(len(images) * TRAIN_RATIO)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        print(f" - {class_name}: {len(train_imgs)} train | {len(val_imgs)} val")
        total_imgs += len(images)

        for img in train_imgs:
            shutil.copy(img, OUTPUT_ROOT / 'train' / class_name / img.name)
        
        for img in val_imgs:
            shutil.copy(img, OUTPUT_ROOT / 'val' / class_name / img.name)

    print("Proceso finalizado correctamente.")
    print(f"Total imagenes: {total_imgs}")
    print(f"Destino: {OUTPUT_ROOT}")

if __name__ == "__main__":
    main()