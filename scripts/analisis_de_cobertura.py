import cv2
import numpy as np
import json
from pathlib import Path
from ultralytics import YOLO

# ==========================================
# 🔧 CONFIGURACIÓN
# ==========================================

# 1. Rutas (AJUSTA ESTO SI ES NECESARIO)
BASE_DIR = Path(__file__).resolve().parent.parent
# Busca tu mejor modelo de YOLO entrenado
PATH_YOLO = BASE_DIR / "modelos" / "runs" / "detect" / "modelo_pizza_v1" / "weights" / "best.pt"

# 2. Configuración YOLO
CONF_THRESHOLD = 0.5  # Confianza mínima para detectar pizza

# 3. Configuración OpenCV (Análisis de Textura)
BLOCK_SIZE = 11
C_VAL = 2
UMBRAL_CORRECTO = 0.45
UMBRAL_DEFICIENTE = 0.20
DIFERENCIA_MITAD = 0.30

# ==========================================

def recortar_pizza_yolo(model, img_path):
    """
    Usa YOLO para encontrar la pizza y devolver solo el recorte (crop).
    """
    img = cv2.imread(str(img_path))
    if img is None: return None, None

    # Inferencia
    results = model(img, verbose=False, conf=CONF_THRESHOLD)
    
    if not results[0].boxes:
        print(f"YOLO no detectó pizza en: {img_path.name}")
        return None, img # Devolvemos la imagen original por si acaso, pero sin crop

    # Tomar la caja con mayor confianza
    boxes = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)
    best_box = boxes[0]
    
    # Coordenadas
    x1, y1, x2, y2 = map(int, best_box.xyxy[0])
    
    # Padding de seguridad (evitar errores de bordes)
    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    crop = img[y1:y2, x1:x2]
    return crop, img # Devolvemos el recorte y la original (para dibujar luego si queremos)

def analizar_distribucion_crop(crop, nombre_archivo):
    """
    Recibe un recorte (numpy array) y aplica la lógica de OpenCV.
    """
    if crop is None or crop.size == 0:
        return

    # Redimensionar para estandarizar el análisis
    img_analisis = cv2.resize(crop, (640, 640))
    h, w = img_analisis.shape[:2]

    # --- LÓGICA DE TEXTURA (ADAPTIVE THRESHOLD) ---
    gray = cv2.cvtColor(img_analisis, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    thresh = cv2.adaptiveThreshold(blurred, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 
                                   blockSize=BLOCK_SIZE, 
                                   C=C_VAL)

    # Limpieza
    kernel = np.ones((3,3), np.uint8)
    mask_ingredientes = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # --- CÁLCULO POR CUADRANTES ---
    cy, cx = h // 2, w // 2
    quads = [
        mask_ingredientes[0:cy, 0:cx],   # Q1
        mask_ingredientes[0:cy, cx:w],   # Q2
        mask_ingredientes[cy:h, 0:cx],   # Q3
        mask_ingredientes[cy:h, cx:w]    # Q4
    ]

    area_util = ((h//2) * (w//2)) * 0.78 # Ajuste circular
    coberturas = []
    
    for q in quads:
        pixeles = cv2.countNonZero(q)
        ratio = min(1.0, pixeles / area_util)
        coberturas.append(ratio)

    # --- EVALUACIÓN ---
    promedio_izq = (coberturas[0] + coberturas[2]) / 2
    promedio_der = (coberturas[1] + coberturas[3]) / 2
    score_final = np.mean(coberturas)
    
    tipo = "ESTANDAR"
    if abs(promedio_izq - promedio_der) > DIFERENCIA_MITAD:
        tipo = "MITAD Y MITAD"
        score_final = max(promedio_izq, promedio_der)

    if score_final >= UMBRAL_CORRECTO:
        calidad = "CORRECTA"
        color = (0, 255, 0)
    elif score_final >= UMBRAL_DEFICIENTE:
        calidad = "REGULAR"
        color = (0, 255, 255)
    else:
        calidad = "MALA / SOLO QUESO"
        color = (0, 0, 255)

    # --- JSON OUTPUT ---
    reporte = {
        "archivo": nombre_archivo,
        "yolo_detectado": True,
        "analisis": {
            "tipo": tipo,
            "calidad": calidad,
            "densidad": round(score_final, 2)
        },
        "cuadrantes": [round(c, 2) for c in coberturas]
    }
    print(json.dumps(reporte, indent=2))

    # --- VISUALIZACIÓN ---
    display = img_analisis.copy()
    cv2.line(display, (cx, 0), (cx, h), (255, 0, 0), 2)
    cv2.line(display, (0, cy), (w, cy), (255, 0, 0), 2)
    
    # Textos
    offsets = [(-80, -40), (20, -40), (-80, 40), (20, 40)]
    for i, ratio in enumerate(coberturas):
        cv2.putText(display, f"{ratio*100:.0f}%", (cx + offsets[i][0], cy + offsets[i][1]), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.rectangle(display, (0,0), (w, 60), (0,0,0), -1)
    cv2.putText(display, f"{tipo} | {calidad}", (10, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Mostrar lado a lado: Máscara vs Resultado
    mask_bgr = cv2.cvtColor(mask_ingredientes, cv2.COLOR_GRAY2BGR)
    final_view = np.hstack((mask_bgr, display))
    
    cv2.imshow("YOLO + OpenCV Distribucion", final_view)
    return cv2.waitKey(0)

def main():
    print(f"[INFO] Cargando YOLO desde: {PATH_YOLO}")
    try:
        model = YOLO(PATH_YOLO)
    except Exception as e:
        print(f"Error cargando YOLO: {e}")
        return


    TEST_FOLDER = BASE_DIR / "datasets" / "test_dataset" 

    print(f"[INFO] Buscando imágenes en: {TEST_FOLDER}")
    images = list(TEST_FOLDER.glob("*.png"))
    
    if not images:
        print("No hay imágenes. Ajusta la ruta TEST_FOLDER en el script.")
        return

    print("------------------------------------------------")
    print(" [ESPACIO] -> Siguiente | [Q] -> Salir")
    print("------------------------------------------------")

    for img_path in images:
        # 1. YOLO DETECTA Y RECORTA
        crop, original = recortar_pizza_yolo(model, img_path)
        
        if crop is not None:
            # 2. OPENCV ANALIZA EL RECORTE
            key = analizar_distribucion_crop(crop, img_path.name)
            if key == ord('q'):
                break
        else:
            # Si YOLO falla, mostramos la original rápido
            cv2.imshow("YOLO + OpenCV Distribucion", cv2.resize(original, (640, 480)))
            if cv2.waitKey(1000) == ord('q'): break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()