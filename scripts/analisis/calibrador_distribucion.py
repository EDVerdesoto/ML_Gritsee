import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

def nada(x):
    pass

# --- CONFIGURACIÓN ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMG_FOLDER = BASE_DIR / "datasets" / "test_dataset"  # Carpeta con imágenes
MODEL_PATH = BASE_DIR / "modelos" / "runs" / "detect" / "modelo_pizza_v1" / "weights" / "best.pt"
CONF_THRESHOLD = 0.9

def recortar_pizza_yolo(model, img_path):
    """
    Usa YOLO para encontrar la pizza y devolver solo el recorte (crop).
    """
    img = cv2.imread(str(img_path))
    if img is None: 
        return None

    # Inferencia
    results = model(img, verbose=False, conf=CONF_THRESHOLD)
    
    if not results[0].boxes:
        return None

    # Tomar la caja con mayor confianza
    boxes = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)
    best_box = boxes[0]
    
    # Coordenadas
    x1, y1, x2, y2 = map(int, best_box.xyxy[0])
    
    # Padding de seguridad
    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    crop = img[y1:y2, x1:x2]
    return crop

def extract_number(path):
    """Extrae el número del nombre del archivo para ordenar"""
    try:
        name = path.stem
        parts = name.split('-')
        return int(parts[-1])
    except:
        return 0

# Cargar modelo YOLO
print("[INFO] Cargando modelo YOLO...")
yolo_model = YOLO(MODEL_PATH)

# Buscar todas las imágenes en la carpeta
print(f"[INFO] Buscando imágenes en: {IMG_FOLDER}")
image_paths = list(IMG_FOLDER.glob("*.png")) + list(IMG_FOLDER.glob("*.jpg"))
image_paths = sorted(image_paths, key=extract_number)

if not image_paths:
    print("ERROR: No se encontraron imágenes en la carpeta.")
    exit()

print(f"[INFO] Se encontraron {len(image_paths)} imágenes")
print("[INFO] Procesando y recortando pizzas con YOLO...")

# Procesar todas las imágenes y guardar los crops válidos
imagenes_procesadas = []
nombres_imagenes = []

for img_path in image_paths:
    crop = recortar_pizza_yolo(yolo_model, img_path)
    if crop is not None:
        img_resized = cv2.resize(crop, (640, 640))
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        imagenes_procesadas.append((img_resized, gray))
        nombres_imagenes.append(img_path.name)

if not imagenes_procesadas:
    print("ERROR: YOLO no detectó pizzas en ninguna imagen.")
    exit()

print(f"[INFO] {len(imagenes_procesadas)} pizzas detectadas correctamente")
total_imagenes = len(imagenes_procesadas)

# Configuración de Ventana
cv2.namedWindow("Calibrador HIBRIDO")
cv2.createTrackbar("Blur", "Calibrador HIBRIDO", 7, 21, nada)
cv2.createTrackbar("Block Size", "Calibrador HIBRIDO", 15, 51, nada) 
cv2.createTrackbar("C (Contraste)", "Calibrador HIBRIDO", 5, 30, nada)         
cv2.createTrackbar("Erosion", "Calibrador HIBRIDO", 1, 10, nada) 
cv2.createTrackbar("Radio Util %", "Calibrador HIBRIDO", 85, 100, nada)
cv2.createTrackbar("Saturacion Min", "Calibrador HIBRIDO", 40, 255, nada)
cv2.createTrackbar("Imagen", "Calibrador HIBRIDO", 0, total_imagenes - 1, nada)  # Índice de 0 a N-1

print("\n" + "="*50)
print("CONTROLES:")
print("  - Deslizadores: Ajustar parámetros")
print("  - ESC: Salir y mostrar valores finales")
print("="*50 + "\n")

while True:
    # 1. Leer valores de las barras
    blur_val = cv2.getTrackbarPos("Blur", "Calibrador HIBRIDO")
    block_val = cv2.getTrackbarPos("Block Size", "Calibrador HIBRIDO")
    c_val = cv2.getTrackbarPos("C (Contraste)", "Calibrador HIBRIDO")
    eros_val = cv2.getTrackbarPos("Erosion", "Calibrador HIBRIDO")
    radio_pct = cv2.getTrackbarPos("Radio Util %", "Calibrador HIBRIDO")
    sat_min = cv2.getTrackbarPos("Saturacion Min", "Calibrador HIBRIDO")
    img_idx = cv2.getTrackbarPos("Imagen", "Calibrador HIBRIDO")
    
    # Seleccionar imagen actual
    img, gray = imagenes_procesadas[img_idx]
    nombre_actual = nombres_imagenes[img_idx]

    h, w = img.shape[:2]

    # Correcciones de impares
    if blur_val % 2 == 0: blur_val += 1
    if block_val < 3: block_val = 3
    if block_val % 2 == 0: block_val += 1

    # 2. Algoritmo de Textura Base
    blurred = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 
                                   blockSize=block_val, 
                                   C=c_val)
    
    # 2.5 Máscara de Saturación (HSV) - Detectar ingredientes por color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, sat, _ = cv2.split(hsv)
    _, mask_sat = cv2.threshold(sat, sat_min, 255, cv2.THRESH_BINARY)
    
    # Combinar textura + saturación
    thresh = cv2.bitwise_or(thresh, mask_sat)

    # 3. MÁSCARA CIRCULAR (Cortar Bordes)
    mask_borde = np.zeros_like(thresh)
    centro = (w // 2, h // 2)
    radio_real = int((min(h, w) // 2) * (radio_pct / 100.0))
    cv2.circle(mask_borde, centro, radio_real, 255, -1)
    
    # Solo mantenemos lo que esté DENTRO del círculo
    thresh_sin_bordes = cv2.bitwise_and(thresh, thresh, mask=mask_borde)

    # 4. Limpieza (Erosión) - APLICADA DESPUÉS DE CORTAR BORDES
    kernel = np.ones((3,3), np.uint8)
    mask_limpia = cv2.erode(thresh_sin_bordes, kernel, iterations=eros_val)
    mask_final = cv2.dilate(mask_limpia, kernel, iterations=eros_val)

    # 5. Visualización
    mask_bgr = cv2.cvtColor(mask_final, cv2.COLOR_GRAY2BGR)
    
    # Dibujar el círculo verde en la imagen original
    display = img.copy()
    cv2.circle(display, centro, radio_real, (0, 255, 0), 2)
    
    combined = np.hstack((display, mask_bgr))
    
    # Calcular cobertura real (Solo dentro del círculo)
    area_circulo = np.pi * (radio_real ** 2)
    pixeles_ingredientes = cv2.countNonZero(mask_final)
    
    if area_circulo > 0:
        cobertura = (pixeles_ingredientes / area_circulo) * 100
    else:
        cobertura = 0

    # Info en pantalla
    cv2.putText(combined, f"[{img_idx+1}/{total_imagenes}] {nombre_actual}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(combined, f"Cobertura: {cobertura:.1f}%", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Calibrador HIBRIDO", combined)

    if cv2.waitKey(1) == 27: break

cv2.destroyAllWindows()
print(f"\nVALORES FINALES -> Blur: {blur_val} | Block: {block_val} | C: {c_val} | Erosion: {eros_val} | Radio: {radio_pct}% | Sat Min: {sat_min}")