import cv2
import os
import glob


### NO OLVIDAR INSTALAR OPENCV: pip install opencv-python



# --- CONFIGURACIÓN ---
# Apunta a tu carpeta de TRAIN recién creada
IMG_DIR = r'C:\Practicas_YOLO\dataset_yolo_final\train\images'
LABEL_DIR = r'C:\Practicas_YOLO\dataset_yolo_final\train\labels'

def draw_yolo_box(img, line):
    h, w, _ = img.shape
    # Formato YOLO: class x_center y_center width height
    try:
        _, x, y, bw, bh = map(float, line.split())
    except ValueError:
        return img # Si la linea esta vacia o malformada
    
    # Convertir coordenadas relativas (0-1) a pixeles
    l = int((x - bw / 2) * w)
    r = int((x + bw / 2) * w)
    t = int((y - bh / 2) * h)
    b = int((y + bh / 2) * h)
    
    # Dibujar
    cv2.rectangle(img, (l, t), (r, b), (0, 255, 0), 2)
    cv2.putText(img, "Pizza", (l, t-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return img

def main():
    img_paths = glob.glob(os.path.join(IMG_DIR, "*.jpg"))
    if not img_paths:
        print("No encontré imágenes. Revisa la ruta IMG_DIR.")
        return

    print(f"Revisando {len(img_paths)} imágenes... Presiona CUALQUIER TECLA para avanzar, 'q' para salir.")
    
    for img_path in img_paths:
        base_name = os.path.basename(img_path).replace('.jpg', '.txt')
        txt_path = os.path.join(LABEL_DIR, base_name)
        
        img = cv2.imread(img_path)
        if img is None: continue
        
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    img = draw_yolo_box(img, line)
        else:
            cv2.putText(img, "SIN ETIQUETA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Redimensionar para que quepa en tu pantalla si es muy grande
        img_show = cv2.resize(img, (800, 800))
        cv2.imshow('Auditoria YOLO (Presiona tecla para siguiente)', img_show)
        
        key = cv2.waitKey(0)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()