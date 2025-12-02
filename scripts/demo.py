import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from ultralytics import YOLO
from pathlib import Path
from PIL import Image
import numpy as np

# --- CONFIGURACIÓN MAESTRA ---
BASE_DIR = Path(__file__).resolve().parent.parent
MODELOS_DIR = BASE_DIR / "modelos"

# 1. Rutas de los Modelos
PATH_YOLO = MODELOS_DIR / "runs" / "detect" / "modelo_pizza_v1" / "weights" / "best.pt"
PATH_RESNET = MODELOS_DIR / "resnet_horneado" / "resnet_horneado_FINETUNED.pth" # Tu modelo de 88%

# 2. Carpeta de imágenes para probar (Usa las originales o una carpeta de Test)
PATH_IMAGENES_TEST = BASE_DIR / "datasets" / "test_dataset" 
# 3. Las Clases de Horneado (EN ORDEN ALFABÉTICO EXACTO como están tus carpetas)
# Revisa tus carpetas: alto, bajo, correcto, excesivo, insuficiente
CLASES_HORNEADO = ['alto', 'bajo', 'correcto', 'excesivo', 'insuficiente']

# 4. Configuración Técnica
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CONF_YOLO = 0.9  # Umbral para detectar pizza

def cargar_resnet():
    print(f"[INFO] Cargando ResNet desde: {PATH_RESNET}")
    # Reconstruir la arquitectura
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(CLASES_HORNEADO))
    
    # Cargar pesos
    model.load_state_dict(torch.load(PATH_RESNET))
    model = model.to(DEVICE)
    model.eval() # Modo evaluación (congela dropout, etc)
    return model

def preprocesar_para_resnet(img_crop_cv2):
    """
    Convierte el recorte de OpenCV (BGR) a lo que espera ResNet (Tensor Normalizado).
    """
    # 1. Convertir BGR a RGB
    img_rgb = cv2.cvtColor(img_crop_cv2, cv2.COLOR_BGR2RGB)
    # 2. Convertir a PIL Image
    pil_img = Image.fromarray(img_rgb)
    
    # 3. Transformaciones (IGUAL QUE EN ENTRENAMIENTO)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    img_tensor = transform(pil_img).unsqueeze(0) # Añadir dimensión de batch (1, 3, 224, 224)
    return img_tensor.to(DEVICE)

def main():
    # 1. Cargar Modelos
    yolo = YOLO(PATH_YOLO)
    resnet = cargar_resnet()
    
    # 2. Buscar imágenes
    print("[INFO] Buscando imágenes de prueba...")
    imagenes = list(PATH_IMAGENES_TEST.rglob("*.png")) + list(PATH_IMAGENES_TEST.rglob("*.jpg"))
    
    if not imagenes:
        print(f"ERROR: No se encontraron imágenes en {PATH_IMAGENES_TEST}")
        return
    
    # Ordenar numéricamente por el número en el nombre del archivo
    def extract_number(path):
        # Extrae el número del formato: location-fecha-NUMERO.png
        try:
            name = path.stem  # Nombre sin extensión
            parts = name.split('-')
            return int(parts[-1])  # Último elemento es el número
        except:
            return 0
    
    imagenes = sorted(imagenes, key=extract_number)
    
    print(f"[INFO] Se encontraron {len(imagenes)} imágenes")
    # random.shuffle(imagenes) # Descomenta si quieres verlas al azar
    
    print("------------------------------------------------")
    print(" CONTROLES:")
    print(" [ESPACIO] -> Siguiente Pizza")
    print(" [Q]       -> Salir")
    print("------------------------------------------------")

    for img_path in imagenes:
        frame = cv2.imread(str(img_path))
        if frame is None: continue
        
        # Copia para dibujar
        display_frame = frame.copy()
        
        # --- A. DETECCIÓN (YOLO) ---
        results = yolo(frame, verbose=False, conf=CONF_YOLO)
        
        # Tomar la mejor caja (podrías usar tu lógica de centrado aquí si quieres)
        best_box = None
        if len(results[0].boxes) > 0:
            # Ordenar por confianza
            boxes = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)
            best_box = boxes[0]

        if best_box is not None:
            # Coordenadas
            x1, y1, x2, y2 = map(int, best_box.xyxy[0])
            
            # --- B. RECORTE ---
            h, w, _ = frame.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            crop = frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                # --- C. CLASIFICACIÓN (ResNet) ---
                tensor = preprocesar_para_resnet(crop)
                
                with torch.no_grad():
                    outputs = resnet(tensor)
                    # Convertir a probabilidades (Softmax)
                    probs = torch.nn.functional.softmax(outputs, dim=1)
                    conf_score, pred_idx = torch.max(probs, 1)
                    
                    clase_detectada = CLASES_HORNEADO[pred_idx.item()]
                    probabilidad = conf_score.item() * 100

                # --- D. DIBUJAR RESULTADO ---
                # Color del borde según calidad
                if clase_detectada == "correcto":
                    color = (0, 255, 0) # Verde
                elif clase_detectada in ["alto", "bajo"]:
                    color = (0, 255, 255) # Amarillo
                else: 
                    color = (0, 0, 255) # Rojo (Excesivo/Insuficiente)

                # Caja
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
                
                # Texto (Fondo negro para leer bien)
                label = f"Horneado: {clase_detectada.upper()} ({probabilidad:.1f}%)"
                (w_text, h_text), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(display_frame, (x1, y1 - 30), (x1 + w_text, y1), color, -1)
                cv2.putText(display_frame, label, (x1, y1 - 8), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Mostrar nombre del archivo en la parte superior
        img_name = img_path.name
        cv2.putText(display_frame, img_name, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Redimensionar si es muy grande para tu pantalla
        if display_frame.shape[0] > 800:
            scale = 800 / display_frame.shape[0]
            dim = (int(display_frame.shape[1] * scale), 800)
            display_frame = cv2.resize(display_frame, dim)

        # Mostrar
        cv2.imshow("DEMO MVP - PIZZA QUALITY CONTROL", display_frame)
        
        key = cv2.waitKey(0)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()