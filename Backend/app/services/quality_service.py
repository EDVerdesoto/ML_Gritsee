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
        
        # Transformación estándar para ResNet (La misma del entrenamiento)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def procesar_lista_con_metadata(self, lista_datos, locacion_manual):
        """
        Procesa lista de dicts: [{'link': '...', 'fecha': datetime}, ...]
        """
        resultados = []
        errores = 0
        procesados = 0
        
        print(f"🚀 Iniciando procesamiento de {len(lista_datos)} imágenes para {locacion_manual}...")

        for index, item in enumerate(lista_datos):
            link = item['link']
            fecha = item['fecha']
            
            # --- PASO 1: DESCARGA ---
            img_path = self._descargar_imagen(link)
            if not img_path:
                print(f"❌ Falló descarga: {link[-15:]}")
                errores += 1
                continue

            try:
                # --- PASO 2: ANÁLISIS ---
                datos_ia = self._analizar_imagen(img_path)
                
                # --- PASO 3: SCORING ---
                scores = calcular_puntaje(datos_ia)

                # --- PASO 4: PERSISTENCIA ---
                nueva_inspeccion = Inspeccion(
                    aws_link=link,
                    locacion=locacion_manual, # <--- USAMOS LA QUE VINO DEL FRONT
                    fecha_hora=fecha,         # <--- USAMOS LA DEL CSV
                    
                    # ... (RESTO DE CAMPOS IGUAL QUE ANTES: tiene_burbujas, scores, etc.)
                    tiene_burbujas=datos_ia['tiene_burbujas'],
                    bordes_sucios=datos_ia['bordes_sucios'],
                    distribucion_clase=datos_ia['distribucion'],
                    horneado_clase=datos_ia['horneado'],
                    tiene_grasa=datos_ia['tiene_grasa'],
                    
                    score_burbujas=scores['burbujas'],
                    score_bordes=scores['bordes'],
                    score_distribucion=scores['distribucion'],
                    score_horneado=scores['horneado'],
                    score_grasa=scores['grasa'],
                    
                    puntaje_total=scores['total'],
                    veredicto=scores['veredicto']
                )
                
                self.db.add(nueva_inspeccion)
                self.db.commit()
                
                procesados += 1
                resultados.append({
                    "id": index + 1,
                    "veredicto": scores['veredicto'],
                    "score": scores['total']
                })
                print(f"✅ [{index+1}] {locacion_manual} - {scores['total']}pts")

            except Exception as e:
                print(f"⚠️ Error: {e}")
                errores += 1
                self.db.rollback()
            
            finally:
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except: pass
        
        return resultados

    def _descargar_imagen(self, url):
        """Descarga segura con Timeouts"""
        try:
            # Timeout de 5s para conexión, 10s para lectura
            response = requests.get(url, stream=True, timeout=(5, 10))
            if response.status_code == 200:
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp.write(response.content)
                temp.close()
                return temp.name
        except Exception:
            return None
        return None

    def _analizar_imagen(self, img_path):
        """Pipeline de Visión Artificial"""
        img_cv2 = cv2.imread(img_path)
        if img_cv2 is None: raise Exception("Imagen corrupta/no leíble")

        # A. YOLO CROP (Recortar la pizza)
        crop = img_cv2
        if model_manager.yolo:
            # Confianza baja (0.25) para asegurar que detecte algo
            results = model_manager.yolo(img_cv2, verbose=False, conf=0.25) 
            if results[0].boxes:
                box = sorted(results[0].boxes, key=lambda x: x.conf[0], reverse=True)[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Padding de seguridad (agrandar un poco el recorte)
                h, w = img_cv2.shape[:2]
                x1, y1 = max(0, x1-20), max(0, y1-20)
                x2, y2 = min(w, x2+20), min(h, y2+20)
                crop = img_cv2[y1:y2, x1:x2]

        # B. PREPARAR TENSOR
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(crop_rgb)
        img_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        # C. PREDECIR
        predicciones = {
            # Horneado: clases en orden alfabético como fueron entrenadas
            "horneado": self._predict_resnet(model_manager.resnet_horneado, img_tensor, 
                                             ['alto', 'bajo', 'correcto', 'excesivo', 'insuficiente']),
            
            # Burbujas: carpetas [no, si] -> índice 1 = tiene burbujas
            "tiene_burbujas": self._predict_resnet_bool(model_manager.resnet_burbujas, img_tensor),
            
            # Bordes: carpetas [limpio, sucio] -> índice 1 = sucio
            "bordes_sucios": self._predict_bordes_sucios(model_manager.resnet_bordes, img_tensor),
            
            # Grasa: carpetas [no, si] -> índice 1 = tiene grasa
            "tiene_grasa": self._predict_resnet_bool(model_manager.resnet_grasa, img_tensor),
            
            # Distribución: clases en orden alfabético como fueron entrenadas
            "distribucion": self._predict_resnet(model_manager.resnet_distribucion, img_tensor,
                                                ['aceptable', 'correcto', 'deficiente', 'mala', 'media']),
        }
        
        # Campo auxiliar para el scoring (inverso de bordes_sucios)
        predicciones["bordes_limpios"] = not predicciones["bordes_sucios"]
        
        # DEBUG: Mostrar predicciones individuales
        print(f"\n---Predicciones:\nhorneado={predicciones['horneado']}\n"
            f"burbujas={predicciones['tiene_burbujas']}\n"
            f"bordes_sucios={predicciones['bordes_sucios']}\n"
            f"grasa={predicciones['tiene_grasa']}\n"
            f"dist={predicciones['distribucion']}\n------------------")
        
        return predicciones

    def _predict_resnet(self, model, tensor, class_names):
        if not model: 
            print(f"Modelo no cargado, usando default: {class_names[0]}")
            return class_names[0]
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidence, preds = torch.max(probs, 1)
            result = class_names[preds.item()]
            return result

    def _predict_resnet_bool(self, model, tensor):
        """
        Para modelos binarios con carpetas [no, si] en orden alfabético:
        - Índice 0 = 'no' -> False
        - Índice 1 = 'si' -> True
        """
        if not model: 
            print(f"Modelo bool no cargado")
            return False
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidence, preds = torch.max(probs, 1)
            result = preds.item() == 1
            return result
    
    def _predict_bordes_sucios(self, model, tensor):
        """
        Para modelo de bordes con carpetas [limpio, sucio]:
        - Índice 0 = 'limpio' -> False (no sucio)
        - Índice 1 = 'sucio' -> True
        """
        if not model: 
            print(f"Modelo bordes no cargado")
            return False
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidence, preds = torch.max(probs, 1)
            result = preds.item() == 1
            return result