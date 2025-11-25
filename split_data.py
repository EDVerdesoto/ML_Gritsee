import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

# Ruta RELATIVA (porque el script está en PRACTICAS y la carpeta está "ahí abajo")
INPUT_FOLDER = Path("Descarga_Pizzas/00_Datasets_Procesados/Detection_Unique_640")

# Ruta de SALIDA (Se creará en PRACTICAS)
OUTPUT_FOLDER = Path("dataset_yolo_final")

# Porcentaje de entrenamiento (0.8 = 80% train, 20% validation)
TRAIN_RATIO = 0.8

def main():
    # Crear estructura de carpetas YOLO
    for split in ['train', 'val']:
        for kind in ['images', 'labels']:
            (OUTPUT_FOLDER / split / kind).mkdir(parents=True, exist_ok=True)

    # Obtener lista de imágenes que TIENEN su etiqueta .txt
    images = [f for f in INPUT_FOLDER.glob("*.jpg") if (INPUT_FOLDER / f"{f.stem}.txt").exists()]
    
    # Aleatorizar la lista
    random.shuffle(images)
    
    # Calcular punto de corte
    split_idx = int(len(images) * TRAIN_RATIO)
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]
    
    print(f"Total imágenes etiquetadas: {len(images)}")
    print(f"Entrenamiento (Train): {len(train_imgs)}")
    print(f"Validación (Val): {len(val_imgs)}")
    print("Copiando archivos.")

    # 5. Función de copiado
    def copy_files(file_list, split_name):
        for img_path in tqdm(file_list, desc=f"Copiando a {split_name}"):
            txt_path = INPUT_FOLDER / f"{img_path.stem}.txt"
            
            # Copiar imagen y etiqueta a su nueva casa
            shutil.copy(img_path, OUTPUT_FOLDER / split_name / "images" / img_path.name)
            shutil.copy(txt_path, OUTPUT_FOLDER / split_name / "labels" / txt_path.name)

    # 6. Ejecutar
    copy_files(train_imgs, 'train')
    copy_files(val_imgs, 'val')

    print("\n✅ ¡LISTO! Dataset organizado.")
    print(f"Tu nuevo dataset está en: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    main()