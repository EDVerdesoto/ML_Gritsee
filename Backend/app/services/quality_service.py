import requests
import cv2
import numpy as np
import tempfile
import os
import torch
from PIL import Image
from torchvision import transforms
from sqlalchemy.orm import Session
from app.models.inspeccion import Inspeccion
from app.core.model_loader import model_manager
from app.services.scoring_logic import calcular_puntaje

class QualityService:
    def __init__(self, db: Session):
        self.db = db
        self.device = model_manager.device
        
        # Transformación estándar para ResNet
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def procesar_batch(self, df):
        resultados = []
        
        for index, row in df.iterrows():
            link = row.get("Photo Link")
            # Intenta leer locación y fecha del CSV, si no existen usa defaults
            locacion = row.get("Locacion", "Desconocida") 
            # Fecha vendría del CSV, aquí simplificamos
            
            if not link: continue
            
            # 1. DESCARGAR
            img_path = self._descargar_imagen(link)
            if not img_path: continue

            try:
                # 2. ANALIZAR (La Magia Real)
                datos_ia = self._analizar_imagen_real(img_path)
                
                # 3. CALCULAR PUNTAJE
                scores = calcular_puntaje(datos_ia)

                # 4. GUARDAR EN DB
                nueva_inspeccion = Inspeccion(
                    aws_link=link,
                    locacion=locacion,
                    
                    # Resultados IA
                    tiene_burbujas=datos_ia['tiene_burbujas'],
                    bordes_sucios=datos_ia['bordes_sucios'], # True = Sucios
                    distribucion_clase=datos_ia['distribucion'],
                    horneado_clase=datos_ia['horneado'],
                    tiene_grasa=datos_ia['tiene_grasa'],
                    
                    # Scores
                    score_burbujas=scores['burbujas'],
                    score_bordes=scores['bordes'],
                    score_distribucion=scores['distribucion'],
                    score_horneado=scores['horneado'],
                    score_grasa=scores['grasa'],
                    
                    # Totales
                    puntaje_total=scores['total'],
                    veredicto=scores['veredicto']
                )
                self.db.add(nueva_inspeccion)
                self.db.commit()
                
                resultados.append({
                    "link": link, 
                    "veredicto": scores['veredicto'], 
                    "score": scores['total']
                })

            except Exception as e:
                print(f"❌ Error procesando {link}: {e}")
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)
        
        return resultados

    def _descargar_imagen(self, url):
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp.write(response.content)
                temp.close()
                return temp.name
        except:
            return None

    def _analizar_imagen_real(self, img_path):
        """Orquestador de Modelos"""
        img_cv2 = cv2.imread(img_path)
        if img_cv2 is None: raise Exception("Imagen corrupta")

        # A. YOLO CROP
        # Si YOLO falla, usamos la imagen completa
        crop = img_cv2
        if model_manager.yolo:
            results = model_manager.yolo(img_cv2, verbose=False, conf=0.5)
            if results[0].boxes:
                # Tomar la caja más grande
                box = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                crop = img_cv2[y1:y2, x1:x2]

        # B. PREPARAR PARA RESNET (Tensor)
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(crop_rgb)
        img_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        # C. INFERENCIAS
        return {
            "horneado": self._predict_resnet(model_manager.resnet_horneado, img_tensor, 
                                             ['Alto', 'Bajo', 'Correcto', 'Excesivo', 'Insuficiente']),
            
            "tiene_burbujas": self._predict_resnet_bool(model_manager.resnet_burbujas, img_tensor),
            
            "bordes_sucios": self._predict_resnet_bool(model_manager.resnet_bordes, img_tensor), # Asumiendo clases [Limpios, Sucios]
            
            "tiene_grasa": self._predict_resnet_bool(model_manager.resnet_grasa, img_tensor),
            
            "distribucion": self._predict_resnet(model_manager.resnet_distribucion, img_tensor, 
                                                 ['Correcto', 'Aceptable', 'Media', 'Mala', 'Deficiente']),
            
            # Para la función de scoring que espera este campo:
            "bordes_limpios": not self._predict_resnet_bool(model_manager.resnet_bordes, img_tensor) 
        }

    def _predict_resnet(self, model, tensor, class_names):
        if not model: return class_names[0] # Fallback
        with torch.no_grad():
            outputs = model(tensor)
            _, preds = torch.max(outputs, 1)
            return class_names[preds.item()]

    def _predict_resnet_bool(self, model, tensor):
        # Asumiendo carpetas: 0=No, 1=Si (Ojo verifica el orden alfabético de tus carpetas!)
        if not model: return False
        with torch.no_grad():
            outputs = model(tensor)
            _, preds = torch.max(outputs, 1)
            # Si index 1 es "Si", devuelve True
            return True if preds.item() == 1 else False
