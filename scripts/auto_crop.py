import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from tqdm import tqdm

# --- CONFIGURACIÓN ---
MODEL_PATH = Path(r"C:\Proyectos\ML_Gritsee\modelos\runs\detect\modelo_pizza_v1\weights\best.pt")
INPUT_ROOT = Path(r"C:\Proyectos\ML_Gritsee\datasets\Descarga_Pizzas\Classification_ResNet_640")
OUTPUT_ROOT = Path(r"C:\Proyectos\ML_Gritsee\datasets\Dataset_Stage2_Crops_HighQuality") # Nueva carpeta limpia

# REGLA 1: Solo aceptamos predicciones de 0.9 para arriba
CONF_THRESHOLD = 0.94
BLACK_THRESHOLD = 5  # Valor de pixel (0-255) para considerar negro
TOUCH_TOLERANCE = 5  # Cuántos pixeles de margen para decir "está tocando"

def get_active_area(img):
    """
    Encuentra los límites de la imagen real (excluyendo barras negras).
    Retorna: y_min (arriba), y_max (abajo), x_min (izq), x_max (der)
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Crear máscara de todo lo que NO es negro
    _, mask = cv2.threshold(gray, BLACK_THRESHOLD, 255, cv2.THRESH_BINARY)
    
    # Encontrar coordenadas de todos los pixeles blancos
    coords = cv2.findNonZero(mask)
    
    if coords is None:
        # Si todo es negro, devolvemos la imagen completa por seguridad
        h, w = img.shape[:2]
        return 0, h, 0, w

    # Obtener el bounding rect de la zona activa
    x, y, w, h = cv2.boundingRect(coords)
    return y, y+h, x, x+w

def main():
    print(f"Cargando modelo: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    images = list(INPUT_ROOT.rglob("*.jpg"))
    print(f"Procesando {len(images)} imágenes con Lógica Anti-Letterbox...")

    count_saved = 0

    for img_path in tqdm(images):
        img = cv2.imread(str(img_path))
        if img is None: continue

        # 1. DETECTAR BARRAS NEGRAS (Límites de la zona útil)
        # valid_y1 = Donde empieza la imagen arriba
        # valid_y2 = Donde termina la imagen abajo
        # valid_x1, valid_x2 = Lo mismo horizontalmente (aunque suele ser vertical el padding)
        valid_y1, valid_y2, valid_x1, valid_x2 = get_active_area(img)

        # Inferencia
        results = model(img, imgsz=640, verbose=False, conf=CONF_THRESHOLD)
        boxes = results[0].boxes
        
        if len(boxes) == 0: continue

        candidates = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # 2. VERIFICAR SI TOCA EL LETTERBOX
            # Toca arriba o abajo?
            touching_v = (y1 <= valid_y1 + TOUCH_TOLERANCE) or (y2 >= valid_y2 - TOUCH_TOLERANCE)
            # Toca izquierda o derecha?
            touching_h = (x1 <= valid_x1 + TOUCH_TOLERANCE) or (x2 >= valid_x2 - TOUCH_TOLERANCE)

            is_touching_black = touching_v or touching_h
            
            candidates.append({
                'box': box,
                'conf': conf,
                'touching': is_touching_black
            })

        # --- LÓGICA DE DECISIÓN (TU REGLA) ---
        final_box = None

        if len(candidates) == 1:
            # CASO A: Solo hay una. La guardamos sea como sea.
            final_box = candidates[0]['box']
        else:
            # CASO B: Hay varias. Buscamos las que NO tocan lo negro.
            clean_candidates = [c for c in candidates if not c['touching']]
            
            if len(clean_candidates) > 0:
                # Si hay limpias, tomamos la de mayor confianza entre ellas
                clean_candidates.sort(key=lambda x: x['conf'], reverse=True)
                final_box = clean_candidates[0]['box']
            else:
                # Si TODAS tocan lo negro (qué mala suerte), tomamos la de mayor confianza
                candidates.sort(key=lambda x: x['conf'], reverse=True)
                final_box = candidates[0]['box']

        # --- GUARDAR ---
        if final_box:
            x1, y1, x2, y2 = map(int, final_box.xyxy[0])
            
            h, w, _ = img.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            crop = img[y1:y2, x1:x2]

            if crop.size > 0:
                rel_path = img_path.relative_to(INPUT_ROOT)
                save_path = OUTPUT_ROOT / rel_path
                save_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(save_path), crop)
                count_saved += 1

    print("\n✅ ¡Proceso Anti-Letterbox Terminado!")
    print(f"Se guardaron {count_saved} pizzas.")
    print(f"Ubicación: {OUTPUT_ROOT}")

if __name__ == "__main__":
    main()