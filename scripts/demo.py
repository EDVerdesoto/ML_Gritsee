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

# Modelos ResNet para cada incidencia
MODELOS_RESNET = {
    "grasa": {
        "path": MODELOS_DIR / "resnet_grasa" / "resnet_grasa_finetuned.pth",
        "clases": ["no", "si"]
    },
    "burbujas": {
        "path": MODELOS_DIR / "resnet_burbujas" / "resnet_burbujas_finetuned.pth",
        "clases": ["no", "si"]
    },
    "bordes": {
        "path": MODELOS_DIR / "resnet_bordes" / "resnet_bordes_finetuned.pth",
        "clases": ["limpio", "sucio"]
    },
    "horneado": {
        "path": MODELOS_DIR / "resnet_horneado" / "resnet_horneado_FINETUNED.pth",
        "clases": ["alto", "bajo", "correcto", "excesivo", "insuficiente"]
    },
    "distribucion": {
        "path": MODELOS_DIR / "resnet_distribucion" / "resnet_distribucion_finetuned.pth",
        "clases": ["aceptable", "correcto", "deficiente", "mala", "media"]
    }
}

# 2. Carpeta de imágenes para probar
PATH_IMAGENES_TEST = BASE_DIR / "datasets" / "test_dataset"

# 3. Configuración Técnica
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CONF_YOLO = 0.9

# 4. Configuración de la interfaz
PANEL_HEIGHT = 180  # Altura del panel de reporte
IMG_DISPLAY_SIZE = 400  # Tamaño de la imagen mostrada
BORDER_SIZE = 10  # Borde negro alrededor de la imagen


def cargar_resnet(path, num_clases):
    """Carga un modelo ResNet con el número de clases especificado"""
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_clases)
    model.load_state_dict(torch.load(path, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()
    return model


def cargar_todos_los_modelos():
    """Carga todos los modelos ResNet"""
    modelos = {}
    for nombre, config in MODELOS_RESNET.items():
        print(f"[INFO] Cargando modelo: {nombre}...")
        try:
            modelos[nombre] = {
                "model": cargar_resnet(config["path"], len(config["clases"])),
                "clases": config["clases"]
            }
        except Exception as e:
            print(f"[WARN] No se pudo cargar {nombre}: {e}")
    return modelos


def preprocesar_para_resnet(img_crop_cv2):
    """Convierte el recorte de OpenCV (BGR) a tensor para ResNet"""
    img_rgb = cv2.cvtColor(img_crop_cv2, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    img_tensor = transform(pil_img).unsqueeze(0)
    return img_tensor.to(DEVICE)


def clasificar_con_modelo(modelo_dict, tensor):
    """Clasifica una imagen con un modelo específico"""
    with torch.no_grad():
        outputs = modelo_dict["model"](tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        conf_score, pred_idx = torch.max(probs, 1)
        
        clase = modelo_dict["clases"][pred_idx.item()]
        confianza = conf_score.item() * 100
        
    return clase, confianza


def obtener_color_resultado(nombre, clase):
    """Devuelve el color según el resultado de la predicción"""
    # Resultados "buenos" -> Verde
    buenos = {
        "grasa": "no",
        "burbujas": "no",
        "bordes": "limpio",
        "horneado": "correcto",
        "distribucion": "correcto"
    }
    # Resultados "aceptables" -> Amarillo
    aceptables = {
        "horneado": ["alto", "bajo"],
        "distribucion": ["aceptable", "media"]
    }
    
    if clase == buenos.get(nombre):
        return (0, 200, 0)  # Verde
    elif nombre in aceptables and clase in aceptables[nombre]:
        return (0, 200, 200)  # Amarillo
    else:
        return (0, 0, 200)  # Rojo


def dibujar_panel_reporte(resultados, ancho):
    """Crea el panel de reporte con todos los resultados"""
    panel = np.zeros((PANEL_HEIGHT, ancho, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30)  # Fondo gris oscuro
    
    # Línea separadora arriba (dorada)
    cv2.line(panel, (0, 1), (ancho, 1), (0, 180, 255), 2)
    
    # Título centrado
    titulo = "REPORTE DE CALIDAD"
    cv2.putText(panel, titulo, (ancho // 2 - 80, 22), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Los 5 modelos en una sola fila, distribuidos uniformemente
    orden = ["grasa", "burbujas", "bordes", "horneado", "distribucion"]
    y_linea1 = 55  # Nombre del modelo
    y_linea2 = 80  # Predicción
    y_linea3 = 100  # Confianza
    
    espacio = ancho // 5
    
    for i, nombre in enumerate(orden):
        if nombre in resultados:
            clase, confianza = resultados[nombre]
            color = obtener_color_resultado(nombre, clase)
            
            # Centro de cada columna
            x_centro = (i * espacio) + (espacio // 2)
            
            # Nombre del modelo (gris claro, pequeño)
            texto_nombre = nombre.upper()
            (tw, _), _ = cv2.getTextSize(texto_nombre, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.putText(panel, texto_nombre, (x_centro - tw // 2, y_linea1), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            
            # Predicción (con color, más grande)
            texto_pred = clase.upper()
            (tw, _), _ = cv2.getTextSize(texto_pred, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.putText(panel, texto_pred, (x_centro - tw // 2, y_linea2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Confianza (pequeño, debajo)
            texto_conf = f"{confianza:.1f}%"
            (tw, _), _ = cv2.getTextSize(texto_conf, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.putText(panel, texto_conf, (x_centro - tw // 2, y_linea3), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1)
    
    # Línea separadora
    cv2.line(panel, (0, 115), (ancho, 115), (60, 60, 60), 1)
    
    # Leyenda de colores abajo
    y_leyenda = 140
    cv2.circle(panel, (30, y_leyenda), 6, (0, 200, 0), -1)
    cv2.putText(panel, "OK", (42, y_leyenda + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    
    cv2.circle(panel, (90, y_leyenda), 6, (0, 200, 200), -1)
    cv2.putText(panel, "ACEPTABLE", (102, y_leyenda + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    
    cv2.circle(panel, (200, y_leyenda), 6, (0, 0, 200), -1)
    cv2.putText(panel, "PROBLEMA", (212, y_leyenda + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    
    # Nota sobre el porcentaje
    cv2.putText(panel, "% = Confianza del modelo en su prediccion", (10, PANEL_HEIGHT - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (100, 100, 100), 1)
    
    return panel


def main():
    # 1. Cargar Modelos
    print("[INFO] Cargando modelo YOLO...")
    yolo = YOLO(PATH_YOLO)
    
    modelos_resnet = cargar_todos_los_modelos()
    
    if not modelos_resnet:
        print("ERROR: No se cargó ningún modelo ResNet")
        return
    
    print(f"[INFO] Se cargaron {len(modelos_resnet)} modelos ResNet")
    
    # 2. Buscar imágenes
    print("[INFO] Buscando imágenes de prueba...")
    imagenes = list(PATH_IMAGENES_TEST.rglob("*.png")) + list(PATH_IMAGENES_TEST.rglob("*.jpg"))
    
    if not imagenes:
        print(f"ERROR: No se encontraron imágenes en {PATH_IMAGENES_TEST}")
        return
    
    def extract_number(path):
        try:
            name = path.stem
            parts = name.split('-')
            return int(parts[-1])
        except:
            return 0
    
    imagenes = sorted(imagenes, key=extract_number)
    
    print(f"[INFO] Se encontraron {len(imagenes)} imágenes")
    
    print("------------------------------------------------")
    print(" CONTROLES:")
    print(" [ESPACIO] -> Siguiente Pizza")
    print(" [Q]       -> Salir")
    print("------------------------------------------------")

    for img_path in imagenes:
        frame = cv2.imread(str(img_path))
        if frame is None: 
            continue
        
        resultados = {}
        crop = None
        
        # --- A. DETECCIÓN (YOLO) ---
        results = yolo(frame, verbose=False, conf=CONF_YOLO)
        
        best_box = None
        if len(results[0].boxes) > 0:
            boxes = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)
            best_box = boxes[0]

        if best_box is not None:
            x1, y1, x2, y2 = map(int, best_box.xyxy[0])
            h, w, _ = frame.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            crop = frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                # --- B. CLASIFICACIÓN CON TODOS LOS MODELOS ---
                tensor = preprocesar_para_resnet(crop)
                
                for nombre, modelo_dict in modelos_resnet.items():
                    clase, confianza = clasificar_con_modelo(modelo_dict, tensor)
                    resultados[nombre] = (clase, confianza)
        
        # --- C. CREAR INTERFAZ ---
        # Redimensionar imagen para mostrar
        if crop is not None and crop.size > 0:
            # Mostrar el recorte de la pizza
            display_img = cv2.resize(crop, (IMG_DISPLAY_SIZE, IMG_DISPLAY_SIZE))
        else:
            # Si no hay detección, mostrar imagen original redimensionada
            h, w = frame.shape[:2]
            scale = IMG_DISPLAY_SIZE / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            display_img = cv2.resize(frame, (new_w, new_h))
            # Centrar en un canvas cuadrado
            canvas = np.zeros((IMG_DISPLAY_SIZE, IMG_DISPLAY_SIZE, 3), dtype=np.uint8)
            y_offset = (IMG_DISPLAY_SIZE - new_h) // 2
            x_offset = (IMG_DISPLAY_SIZE - new_w) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = display_img
            display_img = canvas
        
        # Agregar borde negro alrededor de la imagen
        display_img = cv2.copyMakeBorder(
            display_img, 
            BORDER_SIZE, BORDER_SIZE, BORDER_SIZE, BORDER_SIZE, 
            cv2.BORDER_CONSTANT, 
            value=(0, 0, 0)
        )
        
        # Nombre del archivo en la imagen (ajustado por el borde)
        img_name = img_path.name
        cv2.putText(display_img, img_name, (BORDER_SIZE + 5, BORDER_SIZE + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(display_img, img_name, (BORDER_SIZE + 5, BORDER_SIZE + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Crear panel de reporte (ancho = imagen + bordes)
        ancho_total = IMG_DISPLAY_SIZE + (BORDER_SIZE * 2)
        if resultados:
            panel = dibujar_panel_reporte(resultados, ancho_total)
        else:
            panel = np.zeros((PANEL_HEIGHT, ancho_total, 3), dtype=np.uint8)
            panel[:] = (30, 30, 30)
            cv2.putText(panel, "NO SE DETECTO PIZZA", (ancho_total//2 - 100, PANEL_HEIGHT//2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)
        
        # Combinar imagen y panel verticalmente
        combined = np.vstack((display_img, panel))
        
        # Mostrar
        cv2.imshow("PIZZA QUALITY CONTROL - DEMO", combined)
        
        key = cv2.waitKey(0)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()