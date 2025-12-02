import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from pathlib import Path
import time
import copy
from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd

# --- CONFIGURACIÓN ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # scripts/resnet -> scripts -> ML_Gritsee
DATA_DIR = BASE_DIR / "datasets" / "dataset_resnet_horneado"
MODEL_DIR = BASE_DIR / "modelos" / "resnet_horneado"

# 1. CARGAMOS EL MODELO PREVIO (El de 76%)
PREVIOUS_MODEL_PATH = MODEL_DIR / "resnet_horneado_best.pth"

# 2. GUARDAMOS UNO NUEVO (El refinado)
NEW_MODEL_PATH = MODEL_DIR / "resnet_horneado_FINETUNED.pth"
PLOT_PATH = MODEL_DIR / "graficas_finetuning.png"

# --- HIPERPARÁMETROS DE AFINADO ---
BATCH_SIZE = 16       # Bajamos un poco el batch por seguridad (ocupa más memoria al descongelar)
EPOCHS = 10           # Pocas épocas, es solo pulir
LEARNING_RATE = 1e-4  # 0.0001 (10 veces más lento que antes. CRÍTICO.)
IMG_SIZE = 224

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Fine-Tuning en: {device}")

    # Transformaciones (Las mismas)
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15), # Un poquito más de rotación para forzarlo
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    print("[INFO] Cargando datos...")
    image_datasets = {x: datasets.ImageFolder(str(DATA_DIR / x), data_transforms[x])
                      for x in ['train', 'val']}
    
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=BATCH_SIZE,
                                                 shuffle=True, num_workers=2)
                   for x in ['train', 'val']}
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes
    print(f"[INFO] Clases: {class_names}")

    # --- CARGAR EL MODELO PREVIO ---
    print(f"[INFO] Cargando pesos de: {PREVIOUS_MODEL_PATH}")
    
    # 1. Reconstruir la arquitectura original
    model = models.resnet50(weights=None) # No descargamos ImageNet, usamos el nuestro
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    
    # 2. Inyectar los pesos entrenados
    model.load_state_dict(torch.load(PREVIOUS_MODEL_PATH))
    model = model.to(device)

    # --- DESCONGELAR (UNFREEZE) ---
    print("[INFO] Descongelando capas para ajuste fino...")
    for param in model.parameters():
        param.requires_grad = True  # <--- ESTA ES LA CLAVE. Ahora todo el cerebro aprende.

    # Usamos LR muy bajo (1e-4)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    # Historial
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    
    # Variables para el mejor modelo
    best_acc = 0.0
    # Importante: Empezamos asumiendo que el modelo actual ya tiene una precisión base
    # Pero lo mediremos en la primera época.

    print(f"\n[INFO] Iniciando Fine-Tuning ({EPOCHS} épocas)...")

    for epoch in range(EPOCHS):
        print(f'\nEpoca {epoch + 1}/{EPOCHS}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            pbar = tqdm(dataloaders[phase], desc=f"{phase}")
            
            for inputs, labels in pbar:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                
                pbar.set_postfix({'loss': loss.item()})

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            history[f'{phase}_loss'].append(epoch_loss)
            history[f'{phase}_acc'].append(epoch_acc.item())

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                torch.save(model.state_dict(), NEW_MODEL_PATH)
                print(f"--> ¡Mejora detectada! Guardado en {NEW_MODEL_PATH.name}")

    print(f'\n[FIN] Mejor Accuracy Final: {best_acc:.4f}')
    
    # Graficar
    plt.figure(figsize=(10, 5))
    plt.plot(history['train_acc'], label='Train Acc')
    plt.plot(history['val_acc'], label='Val Acc')
    plt.title(f'Fine Tuning (LR={LEARNING_RATE})')
    plt.legend()
    plt.grid(True)
    plt.savefig(PLOT_PATH)
    print(f"[INFO] Gráfica guardada en: {PLOT_PATH}")

if __name__ == "__main__":
    main()