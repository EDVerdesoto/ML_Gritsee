import cv2
from ultralytics import YOLO
from pathlib import Path
import random

# --- CONFIGURACIÓN ---
MODEL_PATH = Path(r"C:\Proyectos\ML_Gritsee\modelos\runs\detect\modelo_pizza_v1\weights\best.pt")
# Pon aquí la carpeta donde están las fotos que quieres revisar (pueden ser las originales)
INPUT_ROOT = Path(r"C:\Proyectos\ML_Gritsee\datasets\Descarga_Pizzas\Classification_ResNet_640\bordes\limpio")

# El mismo umbral que usaste en el otro script (para ver por qué falla)
CONF_THRESHOLD = 0.9

def main():
    print(f"Cargando modelo: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)

    # Buscar imágenes
    images = list(INPUT_ROOT.glob("*.jpg"))
    
    print("---------------------------------------------------------")
    print("CONTROLES:")
    print(" [ESPACIO] -> Siguiente foto")
    print(" [Q]       -> Salir")
    print("---------------------------------------------------------")

    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None: continue
        
        # Hacemos una copia para dibujar encima
        debug_img = img.copy()

        # Inferencia (bajamos un poco el conf del modelo para ver QUÉ MÁS detecta)
        # Ponemos conf=0.1 para que YOLO nos muestre todo, incluso lo que duda.
        results = model(img, imgsz=640, verbose=False, conf=0.1)

        best_conf = -1.0
        best_box = None

        # 1. Primero buscamos cuál es la ganadora según tu lógica anterior
        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf >= CONF_THRESHOLD and conf > best_conf:
                    best_conf = conf
                    best_box = box

        # 2. Ahora dibujamos todo para que veas qué pasa
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                label = f"{conf:.4f}"

                # LÓGICA DE COLORES
                if box == best_box:
                    # VERDE GRUESO: Esta es la que se recortaría
                    color = (0, 255, 0) 
                    thickness = 3
                    text_info = f"GANADORA ({label})"
                elif conf >= CONF_THRESHOLD:
                    # AMARILLO: Pasó el filtro, pero había una mejor
                    color = (0, 255, 255)
                    thickness = 2
                    text_info = f"Casi... ({label})"
                else:
                    # ROJO: No pasó el umbral (basura o duda)
                    color = (0, 0, 255)
                    thickness = 1
                    text_info = f"Ignorada ({label})"

                # Dibujar caja
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, thickness)
                # Poner texto (con fondito negro para leer bien)
                cv2.putText(debug_img, text_info, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Mostrar en ventana
        # Si la imagen es muy grande, la achicamos para tu pantalla
        if debug_img.shape[0] > 800:
            scale = 800 / debug_img.shape[0]
            dim = (int(debug_img.shape[1] * scale), 800)
            debug_img = cv2.resize(debug_img, dim)

        cv2.imshow("EL OJO DE THUNDERA (Debug YOLO)", debug_img)

        # Esperar tecla
        key = cv2.waitKey(0) 
        if key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()