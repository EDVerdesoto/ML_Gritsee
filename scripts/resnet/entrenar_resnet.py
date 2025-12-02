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
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Rutas de modelos
BASE_MODEL_PATH = MODEL_DIR / "resnet_horneado_best.pth"
FINETUNED_MODEL_PATH = MODEL_DIR / "resnet_horneado_FINETUNED.pth"

IMG_SIZE = 224

def plot_training_history(history, save_path, title="Training History"):
    """
    Genera gráficas de Loss y Accuracy y las guarda en un archivo PNG.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Gráfica de Loss
    ax1.plot(history['train_loss'], label='Train Loss')
    ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_title('Curva de Pérdida (Loss)')
    ax1.set_xlabel('Épocas')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)

    # Gráfica de Accuracy
    ax2.plot(history['train_acc'], label='Train Acc')
    ax2.plot(history['val_acc'], label='Val Acc')
    ax2.set_title('Curva de Precisión (Accuracy)')
    ax2.set_xlabel('Épocas')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    ax2.grid(True)

    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"[INFO] Gráfica guardada en: {save_path}")
    plt.close()

def train_from_scratch():
    """
    Entrena un modelo ResNet50 desde cero (Transfer Learning con capas congeladas)
    """
    print("\n" + "="*60)
    print("ENTRENAMIENTO DESDE CERO (Transfer Learning)")
    print("="*60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Usando dispositivo: {device}")
    
    # Hiperparámetros
    BATCH_SIZE = 32
    EPOCHS = 15
    LEARNING_RATE = 0.001
    
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

    print("[INFO] Cargando imágenes...")
    image_datasets = {x: datasets.ImageFolder(str(DATA_DIR / x), data_transforms[x])
                      for x in ['train', 'val']}
    
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=BATCH_SIZE,
                                                 shuffle=True, num_workers=2)
                   for x in ['train', 'val']}
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes
    
    print(f"[INFO] Clases: {class_names}")
    print(f"[INFO] Train: {dataset_sizes['train']} | Val: {dataset_sizes['val']}")

    # Modelo
    print("[INFO] Descargando ResNet50 pre-entrenado...")
    model = models.resnet50(weights='DEFAULT')
    
    # Congelar capas base
    for param in model.parameters():
        param.requires_grad = False

    # Modificar última capa
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=LEARNING_RATE)

    # Historial
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}

    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    print(f"\n[INFO] Iniciando entrenamiento ({EPOCHS} épocas)...")
    
    for epoch in range(EPOCHS):
        print(f'\n📊 Época {epoch + 1}/{EPOCHS}')
        print('-' * 50)

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

            history[f'{phase}_loss'].append(epoch_loss)
            history[f'{phase}_acc'].append(epoch_acc.item())

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
                print(f"Nueva mejor precisión: {best_acc:.4f}")

    time_elapsed = time.time() - since
    print(f'\nTiempo total: {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Mejor Accuracy Validación: {best_acc:.4f}')

    # Guardar modelo
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), BASE_MODEL_PATH)
    print(f"Modelo guardado en: {BASE_MODEL_PATH}")

    # Guardar CSV
    csv_path = MODEL_DIR / "resnet_horneado_historial.csv"
    df = pd.DataFrame(history)
    df.to_csv(csv_path, index=False)
    print(f"Historial guardado en: {csv_path}")

    # Generar gráfica
    plot_path = MODEL_DIR / "resnet_horneado_graficas.png"
    plot_training_history(history, plot_path, "Transfer Learning - Training History")

def fine_tune_model():
    """
    Fine-tuning del modelo pre-entrenado (descongelando todas las capas)
    """
    print("\n" + "="*60)
    print("FINE-TUNING (Ajuste Fino)")
    print("="*60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Usando dispositivo: {device}")
    
    # Verificar que existe el modelo base
    if not BASE_MODEL_PATH.exists():
        print(f"ERROR: No se encontró el modelo base en {BASE_MODEL_PATH}")
        print("   Primero debes entrenar el modelo desde cero (opción 1)")
        return
    
    # Hiperparámetros para fine-tuning
    BATCH_SIZE = 16
    EPOCHS = 10
    LEARNING_RATE = 1e-4  # Learning rate muy bajo
    
    # Transformaciones (con más augmentation para fine-tuning)
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
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

    # Cargar modelo pre-entrenado
    print(f"[INFO] Cargando pesos de: {BASE_MODEL_PATH}")
    
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    model.load_state_dict(torch.load(BASE_MODEL_PATH, weights_only=True))
    model = model.to(device)

    # DESCONGELAR todas las capas
    print("[INFO] Descongelando todas las capas...")
    for param in model.parameters():
        param.requires_grad = True

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    # Historial
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    best_acc = 0.0

    print(f'\n[INFO] Iniciando Fine-Tuning ({EPOCHS} épocas con LR={LEARNING_RATE})...')

    for epoch in range(EPOCHS):
        print(f'\nÉpoca {epoch + 1}/{EPOCHS}')
        print('-' * 50)

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

            history[f'{phase}_loss'].append(epoch_loss)
            history[f'{phase}_acc'].append(epoch_acc.item())

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                torch.save(model.state_dict(), FINETUNED_MODEL_PATH)
                print(f"Nueva mejor precisión: {best_acc:.4f}")

    print(f'\nMejor Accuracy Final: {best_acc:.4f}')
    print(f"Modelo guardado en: {FINETUNED_MODEL_PATH}")
    
    # Guardar CSV
    csv_path = MODEL_DIR / "resnet_horneado_finetuning_historial.csv"
    df = pd.DataFrame(history)
    df.to_csv(csv_path, index=False)
    print(f"Historial guardado en: {csv_path}")
    
    # Generar gráfica
    plot_path = MODEL_DIR / "resnet_horneado_finetuning_graficas.png"
    plot_training_history(history, plot_path, f"Fine-Tuning (LR={LEARNING_RATE})")

def show_menu():
    """
    Muestra el menú principal y retorna la opción seleccionada
    """
    print("\n" + "="*60)
    print("ENTRENAMIENTO RESNET - CLASIFICACIÓN DE HORNEADO")
    print("="*60)
    print("\nOpciones:")
    print("  1. Entrenar desde cero (Transfer Learning)")
    print("     └─ Usa ResNet50 pre-entrenado con capas congeladas")
    print("     └─ ~15 épocas, más rápido")
    print()
    print("  2. Fine-Tuning (Ajuste Fino)")
    print("     └─ Requiere modelo base ya entrenado")
    print("     └─ Descongela todas las capas para máxima precisión")
    print("     └─ ~10 épocas con learning rate bajo")
    print()
    print("  3. Salir")
    print("\n" + "="*60)
    
    while True:
        try:
            choice = input("\nSelecciona una opción (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("Opción inválida. Por favor selecciona 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n\nPrograma interrumpido por el usuario.")
            return '3'

def main():
    while True:
        choice = show_menu()
        
        if choice == '1':
            train_from_scratch()
            input("\nPresiona ENTER para continuar...")
            
        elif choice == '2':
            fine_tune_model()
            input("\nPresiona ENTER para continuar...")
            
        elif choice == '3':
            print("\n¡Hasta luego!")
            break

if __name__ == "__main__":
    main()
