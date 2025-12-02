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

# --- CONFIGURACION DE RUTAS Y PARAMETROS ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent # scripts/resnet -> scripts -> ML_Gritsee
DATA_DIR = BASE_DIR / "datasets" / "dataset_resnet_horneado"
MODEL_SAVE_DIR = BASE_DIR / "modelos" / "resnet_horneado"
MODEL_SAVE_PATH = MODEL_SAVE_DIR / "resnet_horneado_best.pth"
# Nuevos archivos de salida
PLOT_SAVE_PATH = MODEL_SAVE_DIR / "resnet_horneado_graficas.png"
CSV_SAVE_PATH = MODEL_SAVE_DIR / "resnet_horneado_historial.csv"

BATCH_SIZE = 32
EPOCHS = 15
LEARNING_RATE = 0.001
IMG_SIZE = 224

def plot_training_history(history, save_path):
    """
    Genera graficas de Loss y Accuracy y las guarda en un archivo PNG.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Grafica de Loss
    ax1.plot(history['train_loss'], label='Train Loss')
    ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_title('Curva de Perdida (Loss)')
    ax1.set_xlabel('Epocas')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)

    # Grafica de Accuracy
    ax2.plot(history['train_acc'], label='Train Acc')
    ax2.plot(history['val_acc'], label='Val Acc')
    ax2.set_title('Curva de Precision (Accuracy)')
    ax2.set_xlabel('Epocas')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(save_path)
    print(f"[INFO] Grafica guardada en: {save_path}")
    plt.close()

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Usando dispositivo: {device}")
    
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Transformaciones
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    print("[INFO] Cargando imagenes...")
    image_datasets = {x: datasets.ImageFolder(str(DATA_DIR / x), data_transforms[x])
                      for x in ['train', 'val']}
    
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=BATCH_SIZE,
                                                 shuffle=True, num_workers=2)
                   for x in ['train', 'val']}
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes
    
    print(f"[INFO] Clases: {class_names}")

    # Modelo
    print("[INFO] Descargando ResNet50...")
    model = models.resnet50(weights='DEFAULT')
    for param in model.parameters():
        param.requires_grad = False

    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=LEARNING_RATE)

    # --- HISTORIAL PARA GRAFICAS ---
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}

    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    print(f"\n[INFO] Iniciando entrenamiento ({EPOCHS} epocas)...")
    
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

            pbar = tqdm(dataloaders[phase], desc=f"{phase.capitalize()}")
            
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

            # Guardar datos en historial
            history[f'{phase}_loss'].append(epoch_loss)
            history[f'{phase}_acc'].append(epoch_acc.item())

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    time_elapsed = time.time() - since
    print(f'\n[FIN] Tiempo total: {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'[RESULTADO] Mejor Accuracy Validacion: {best_acc:4f}')

    # 1. Guardar Modelo
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"[INFO] Modelo guardado en: {MODEL_SAVE_PATH}")

    # 2. Guardar CSV (Excel)
    df = pd.DataFrame(history)
    df.to_csv(CSV_SAVE_PATH, index=False)
    print(f"[INFO] Historial guardado en: {CSV_SAVE_PATH}")

    # 3. Generar Grafica
    plot_training_history(history, PLOT_SAVE_PATH)

if __name__ == "__main__":
    main()