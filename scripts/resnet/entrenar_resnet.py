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

# --- CONSTANTES ---
INCIDENTES_VALIDOS = ['horneado', 'distribucion', 'grasa', 'burbujas', 'bordes']
MODOS_VALIDOS = ['inicial', 'finetune']
IMG_SIZE = 224
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Raiz del proyecto

def plot_training_history(history, save_path, modo):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.plot(history['train_loss'], label='Train Loss')
    ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_title(f'Loss ({modo.upper()})')
    ax1.legend(); ax1.grid(True)

    ax2.plot(history['train_acc'], label='Train Acc')
    ax2.plot(history['val_acc'], label='Val Acc')
    ax2.set_title(f'Accuracy ({modo.upper()})')
    ax2.legend(); ax2.grid(True)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def seleccionar_opciones():
    """Solicita al usuario el incidente y modo de entrenamiento"""
    # 1. Seleccionar incidente
    print("\nSelecciona el incidente a entrenar:")
    print(f"Opciones: {', '.join(INCIDENTES_VALIDOS)}")
    
    while True:
        incidente = input(">>> ").strip().lower()
        if incidente in INCIDENTES_VALIDOS:
            break
        print(f"ERROR: '{incidente}' no es valido. Intenta de nuevo.")

    # 2. Seleccionar modo
    print("\nSelecciona el modo de entrenamiento:")
    print(f"Opciones: {', '.join(MODOS_VALIDOS)}")
    
    while True:
        modo = input(">>> ").strip().lower()
        if modo in MODOS_VALIDOS:
            break
        print(f"ERROR: '{modo}' no es valido. Intenta de nuevo.")
    
    return incidente, modo

def get_config(incidente, modo):
    """Retorna la configuracion segun el incidente y modo"""
    data_dir = BASE_DIR / "datasets" / f"dataset_resnet_{incidente}"
    model_save_dir = BASE_DIR / "modelos" / f"resnet_{incidente}"
    model_save_dir.mkdir(parents=True, exist_ok=True)
    
    if modo == "inicial":
        config = {
            'batch_size': 32,
            'epochs': 15,
            'learning_rate': 0.001,
            'load_pretrained': True,
            'freeze_layers': True,
            'model_filename': f"resnet_{incidente}_best.pth",
            'plot_filename': f"resnet_{incidente}_graficas_inicial.png",
            'csv_filename': f"resnet_{incidente}_historial_inicial.csv",
            'prev_model_path': None
        }
    else:  # finetune
        config = {
            'batch_size': 16,
            'epochs': 10,
            'learning_rate': 1e-4,
            'load_pretrained': False,
            'freeze_layers': False,
            'model_filename': f"resnet_{incidente}_finetuned.pth",
            'plot_filename': f"resnet_{incidente}_graficas_finetune.png",
            'csv_filename': f"resnet_{incidente}_historial_finetune.csv",
            'prev_model_path': model_save_dir / f"resnet_{incidente}_best.pth"
        }
    
    config['data_dir'] = data_dir
    config['model_save_dir'] = model_save_dir
    config['save_path'] = model_save_dir / config['model_filename']
    config['plot_path'] = model_save_dir / config['plot_filename']
    config['csv_path'] = model_save_dir / config['csv_filename']
    
    return config

def main():
    # Seleccion de opciones (solo se ejecuta en el proceso principal)
    incidente, modo = seleccionar_opciones()
    config = get_config(incidente, modo)
    

    
    print(f"\nINICIANDO: {incidente.upper()} (Modo: {modo.upper()})")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Dispositivo: {device}")

    # 1. Cargar Datos
    if not config['data_dir'].exists():
        print(f"ERROR: No existen datos en {config['data_dir']}")
        return

    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15 if modo == "finetune" else 10),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    image_datasets = {x: datasets.ImageFolder(str(config['data_dir'] / x), data_transforms[x])
                      for x in ['train', 'val']}
    
    # num_workers=0 para evitar problemas con multiprocessing en Windows
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=config['batch_size'],
                                                 shuffle=True, num_workers=0)
                   for x in ['train', 'val']}
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes
    
    print(f"[INFO] Clases: {class_names}")
    print(f"[INFO] Train: {dataset_sizes['train']} | Val: {dataset_sizes['val']}")

    # 2. Configurar Modelo
    model = models.resnet50(weights='DEFAULT' if config['load_pretrained'] else None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))

    if modo == "finetune":
        print(f"[INFO] Cargando pesos previos: {config['prev_model_path']}")
        if not config['prev_model_path'].exists():
            print("ERROR: No existe el modelo base para hacer fine-tuning.")
            return
        model.load_state_dict(torch.load(config['prev_model_path'], weights_only=True))

    model = model.to(device)

    # 3. Congelar / Descongelar
    if config['freeze_layers']:
        print("[INFO] Congelando capas base (Solo entrena el head)...")
        for name, param in model.named_parameters():
            if "fc" not in name:
                param.requires_grad = False
    else:
        print("[INFO] Descongelando TODO el modelo (Fine-Tuning profundo)...")
        for param in model.parameters():
            param.requires_grad = True

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), 
                          lr=config['learning_rate'])

    # 4. Entrenamiento
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    best_acc = 0.0
    best_model_wts = copy.deepcopy(model.state_dict())
    
    print(f"\n[INFO] Entrenando por {config['epochs']} epocas...")
    
    for epoch in range(config['epochs']):
        print(f'\nEpoca {epoch + 1}/{config["epochs"]}')
        print('-' * 30)

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
                pbar.set_postfix({'loss': f'{loss.item():.4f}'})

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            history[f'{phase}_loss'].append(epoch_loss)
            history[f'{phase}_acc'].append(epoch_acc.item())

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
                print(f"--> Mejor modelo guardado! ({best_acc:.4f})")

    # 5. Guardar Resultados
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), config['save_path'])
    print(f"\n[EXITO] Modelo guardado en: {config['save_path']}")
    
    pd.DataFrame(history).to_csv(config['csv_path'], index=False)
    plot_training_history(history, config['plot_path'], modo)
    print(f"[INFO] Graficas guardadas en: {config['plot_path']}")

if __name__ == "__main__":
    main()