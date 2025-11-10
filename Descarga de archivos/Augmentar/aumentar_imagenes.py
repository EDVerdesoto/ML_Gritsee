# ============================================
# CÓDIGO 1: Augmentación dirigida de imágenes
# ============================================
# Instalar primero: pip install albumentations opencv-python

import os
import cv2
import albumentations as A
from pathlib import Path
import shutil

BASE_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"

# Configuración de augmentación
transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.3),
    A.Rotate(limit=30, p=0.7),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
    A.GaussNoise(var_limit=(10.0, 50.0), mean=0, p=0.3),  # Agregado 'mean'
    A.GaussianBlur(blur_limit=(3, 7), p=0.3),
    A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.4),
    A.RandomGamma(gamma_limit=(80, 120), p=0.3),
    A.CoarseDropout(max_holes=8, max_h=32, max_w=32, p=0.3),  # max_height → max_h, max_width → max_w
])

def augmentar_imagenes(carpeta_origen, carpeta_destino, num_augmentaciones, transform):
    """
    Genera copias aumentadas de imágenes de una carpeta.
    
    Args:
        carpeta_origen: Ruta de la carpeta con imágenes originales
        carpeta_destino: Ruta donde guardar imágenes aumentadas
        num_augmentaciones: Cuántas copias generar por cada imagen original
        transform: Pipeline de Albumentations
    """
    Path(carpeta_destino).mkdir(parents=True, exist_ok=True)
    
    # Primero, copiar imágenes originales
    imagenes = list(Path(carpeta_origen).glob('*.jpg')) + \
                list(Path(carpeta_origen).glob('*.png')) + \
                list(Path(carpeta_origen).glob('*.jpeg'))
    
    print(f"Procesando {len(imagenes)} imágenes de {carpeta_origen}...")
    
    for img_path in imagenes:
        # Copiar original
        shutil.copy(str(img_path), str(Path(carpeta_destino) / img_path.name))
        
        # Generar augmentaciones
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        for i in range(num_augmentaciones):
            augmented = transform(image=image)
            aug_image = augmented['image']
            aug_image = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
            
            # Guardar con nombre único
            nombre_base = img_path.stem
            extension = img_path.suffix
            nuevo_nombre = f"{nombre_base}_aug_{i+1}{extension}"
            cv2.imwrite(str(Path(carpeta_destino) / nuevo_nombre), aug_image)
    
    total_final = len(list(Path(carpeta_destino).glob('*')))
    print(f"✓ Completado: {total_final} imágenes en {carpeta_destino}")

# ============================================
# USO: Augmentar clases críticas
# ============================================

# HORNEADO - Clases extremadamente minoritarias
print("\n=== AUGMENTANDO HORNEADO ===")
augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'horneado/insuficiente',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'horneado_balanced/insuficiente',
    num_augmentaciones=15,  # 7 originales → ~112 totales
    transform=transform
)

augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'horneado/excesivo',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'horneado_balanced/excesivo',
    num_augmentaciones=15,  # 9 originales → ~144 totales
    transform=transform
)

augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'horneado/bajo',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'horneado_balanced/bajo',
    num_augmentaciones=5,   # 106 originales → ~636 totales
    transform=transform
)

augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'horneado/alto',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'horneado_balanced/alto',
    num_augmentaciones=3,   # 234 originales → ~936 totales
    transform=transform
)

# Copiar "Correcto" sin aumentar (ya tiene suficientes)
print("\nCopiando horneado/correcto sin augmentación...")
shutil.copytree(BASE_DIR / 'horneado/correcto', BASE_DIR / 'horneado_balanced/correcto', dirs_exist_ok=True)

# GRASA - Augmentar "Sí"
print("\n=== AUGMENTANDO GRASA ===")
augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'grasa/si',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'grasa_balanced/si',
    num_augmentaciones=3,   # 352 originales → ~1408 totales
    transform=transform
)

# Copiar "No" sin aumentar
print("\nCopiando grasa/no sin augmentación...")
shutil.copytree(BASE_DIR / 'grasa/no', BASE_DIR / 'grasa_balanced/no', dirs_exist_ok=True)

# BURBUJAS - Augmentación ligera opcional
print("\n=== AUGMENTANDO BURBUJAS (OPCIONAL) ===")
augmentar_imagenes(
    carpeta_origen=BASE_DIR / 'burbujas/si',  # Ruta absoluta
    carpeta_destino=BASE_DIR / 'burbujas_balanced/si',
    num_augmentaciones=2,   # 442 originales → ~1326 totales
    transform=transform
)

# Copiar "No" sin aumentar
print("\nCopiando burbujas/no sin augmentación...")
shutil.copytree(BASE_DIR / 'burbujas/no', BASE_DIR / 'burbujas_balanced/no', dirs_exist_ok=True)

print("\n✅ AUGMENTACIÓN COMPLETADA")
print("Usa las carpetas *_balanced para entrenar tu modelo.")
