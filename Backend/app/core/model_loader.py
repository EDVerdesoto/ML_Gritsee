import torch
from ultralytics import YOLO
from torchvision import models
import torch.nn as nn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # Raíz
MODEL_DIR = BASE_DIR / "modelos"

class ModelManager:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Dispositivo seleccionado para modelos: {self.device}")

        # Inicializar variables vacías
        self.yolo = None
        self.resnet_horneado = None
        self.resnet_distribucion = None
        self.resnet_bordes = None
        self.resnet_burbujas = None
        self.resnet_grasa = None
        # Deteccion de GPU o CPU

    # se usa self para referirse a la instancia actual de la clase
    def load_models(self):
        print(f"Cargando modelos en {self.device}")

        # Cargar YOLO 
        path_yolo = MODEL_DIR / "runs" / "detect" / "modelo_pizza_v1" / "weights" / "best.pt"
        if path_yolo.exists():
            self.yolo = YOLO(str(path_yolo))
            print("YOLO cargado")
        else:
            print(f"ERROR: No encontré el modelo YOLO en {path_yolo}")

        #Cargar modelos ResNet
        # Horneado (5 clases: Correcto, Alto, Bajo, Insuf, Excesivo)
        self.resnet_horneado = self._load_resnet_custom("resnet_horneado", 5)
        
        # Burbujas (2 clases: Si, No)
        self.resnet_burbujas = self._load_resnet_custom("resnet_burbujas", 2)
        
        # Bordes (2 clases: Limpios, Sucios)
        self.resnet_bordes = self._load_resnet_custom("resnet_bordes", 2)
        
        # Grasa (2 clases: Si, No)
        self.resnet_grasa = self._load_resnet_custom("resnet_grasa", 2)
        
        # Distribución ( 5 clases: Correcto, Alto, Bajo, Insuf, Excesivo)
        self.resnet_distribucion = self._load_resnet_custom("resnet_distribucion", 5)
    
    def _load_resnet_custom(self, folder_name, num_classes):
        # Buscamos el archivo finetuned (el mejor) o best.pth
        model_path = MODEL_DIR / folder_name
        
        # Prioridad: finetuned > best > cualquier otro
        finetuned = list(model_path.glob("*finetuned*.pth")) + list(model_path.glob("*FINETUNED*.pth"))
        best = list(model_path.glob("*best*.pth"))
        all_weights = list(model_path.glob("*.pth"))
        
        if finetuned:
            weight_file = finetuned[0]
        elif best:
            weight_file = best[0]
        elif all_weights:
            weight_file = all_weights[0]
        else:
            print(f"No encontré pesos .pth en {folder_name}")
            return None
        
        print(f">>>> Cargando: {weight_file.name}")
        
        try:
            # Reconstruir arquitectura
            model = models.resnet50(weights=None)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
            
            # Cargar pesos
            state_dict = torch.load(weight_file, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval() # Modo evaluación (apaga dropout, etc)
            
            print(f">>>> {folder_name} cargado ({num_classes} clases)")
            return model
        except Exception as e:
            print(f"Error cargando {folder_name}: {e}")
            return None
        
# Ejecuta la línea a penas se cargue el servidor 
model_manager = ModelManager()

model_manager.load_models()