import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from pathlib import Path
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURACIÓN ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INCIDENTE = "distribucion" # Asegúrate de que apunte a tu modelo entrenado
DATA_DIR = BASE_DIR / "datasets" / f"dataset_resnet_{INCIDENTE}"
MODEL_PATH = BASE_DIR / "modelos" / f"resnet_{INCIDENTE}" / f"resnet_{INCIDENTE}_best.pth"
OUTPUT_PLOT = BASE_DIR / "modelos" / f"resnet_{INCIDENTE}" / "matriz_confusion.png"

IMG_SIZE = 224
BATCH_SIZE = 32

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Generando matriz para: {INCIDENTE}")

    # 1. Preparar Datos (Solo Validación)
    data_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    val_dir = DATA_DIR / "val"
    if not val_dir.exists():
        print("Error: No encuentro carpeta val.")
        return

    val_dataset = datasets.ImageFolder(str(val_dir), data_transforms)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    class_names = val_dataset.classes

    # 2. Cargar Modelo
    print(f"[INFO] Cargando modelo: {MODEL_PATH}")
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    
    # Cargar pesos (manejo de error por si se guardó diferente)
    try:
        model.load_state_dict(torch.load(MODEL_PATH))
    except:
        model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu'))
        
    model = model.to(device)
    model.eval()

    # 3. Predecir
    y_true = []
    y_pred = []

    print("[INFO] Ejecutando inferencia...")
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())

    # 4. Generar Matriz
    cm = confusion_matrix(y_true, y_pred)
    
    # Graficar con Seaborn
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicción del Modelo')
    plt.ylabel('Realidad (Etiqueta)')
    plt.title(f'Matriz de Confusión - {INCIDENTE.capitalize()}')
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    print(f"Matriz guardada en: {OUTPUT_PLOT}")

if __name__ == "__main__":
    main()