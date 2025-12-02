#!/usr/bin/env python3
"""
Entrenamiento de YOLOv8 para clasificación multi-atributo de pizzas.
Adaptado para tu estructura de carpetas con 5 clasificadores independientes.
"""

from ultralytics import YOLO
from pathlib import Path
import shutil
import yaml

BASE_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"
YOLO_DIR = Path.home() / "Practicas" / "YOLO_Pizza_Training"

# ============================================
# PASO 1: Preparar estructura de datos para YOLO
# ============================================

def preparar_estructura_yolo():
    """
    YOLO Classification espera estructura:
    datasets/
      train/
        clase1/
          img1.jpg
          img2.jpg
        clase2/
          ...
      val/
        clase1/
        clase2/
    """
    print("\n" + "="*70)
    print("PREPARANDO ESTRUCTURA DE DATOS PARA YOLO")
    print("="*70 + "\n")
    
    # Crear carpetas base para cada clasificador
    clasificadores = {
        'burbujas': ['si', 'no'],
        'bordes': ['limpio', 'sucio'],
        'distribucion': ['correcto', 'aceptable', 'media', 'mala', 'deficiente'],
        'horneado': ['correcto', 'alto', 'bajo', 'insuficiente', 'excesivo'],
        'grasa': ['si', 'no']
    }
    
    for clasificador, clases in clasificadores.items():
        print(f"\n📁 Preparando dataset para: {clasificador}")
        
        dataset_dir = YOLO_DIR / clasificador
        train_dir = dataset_dir / "train"
        val_dir = dataset_dir / "val"
        
        # Crear estructura
        for clase in clases:
            (train_dir / clase).mkdir(parents=True, exist_ok=True)
            (val_dir / clase).mkdir(parents=True, exist_ok=True)
        
        # Copiar imágenes con split 80/20
        for clase in clases:
            origen = BASE_DIR / clasificador / clase
            
            if not origen.exists():
                print(f"  ⚠️  Carpeta no existe: {origen}")
                continue
            
            imagenes = list(origen.glob("*.png")) + list(origen.glob("*.jpg"))
            
            if not imagenes:
                print(f"  ⚠️  Sin imágenes en: {clase}")
                continue
            
            # Split 80% train, 20% val
            n_train = int(len(imagenes) * 0.8)
            train_imgs = imagenes[:n_train]
            val_imgs = imagenes[n_train:]
            
            # Copiar a train
            for img in train_imgs:
                dest = train_dir / clase / img.name
                if not dest.exists():
                    shutil.copy(img, dest)
            
            # Copiar a val
            for img in val_imgs:
                dest = val_dir / clase / img.name
                if not dest.exists():
                    shutil.copy(img, dest)
            
            print(f"  ✓ {clase}: {len(train_imgs)} train, {len(val_imgs)} val")
    
    print(f"\n✅ Estructura preparada en: {YOLO_DIR}")

# ============================================
# PASO 2: Entrenar modelos individuales
# ============================================

def entrenar_clasificador(nombre, clases, epochs=50, batch=16, img_size=640):
    """
    Entrena un clasificador YOLO para un atributo específico.
    
    Args:
        nombre: Nombre del clasificador (burbujas, grasa, etc.)
        clases: Lista de clases para este clasificador
        epochs: Número de épocas
        batch: Tamaño de batch
        img_size: Tamaño de imagen
    """
    print("\n" + "="*70)
    print(f"ENTRENANDO CLASIFICADOR: {nombre.upper()}")
    print("="*70 + "\n")
    
    # Ruta del dataset
    dataset_dir = YOLO_DIR / nombre
    
    if not dataset_dir.exists():
        print(f"❌ Dataset no encontrado: {dataset_dir}")
        return None
    
    # Inicializar modelo (YOLOv8 nano para clasificación)
    # Opciones: yolov8n-cls.pt (nano), yolov8s-cls.pt (small), yolov8m-cls.pt (medium)
    model = YOLO('yolov8n-cls.pt')  # Descargar modelo preentrenado
    
    # Entrenar
    results = model.train(
        data=str(dataset_dir),
        epochs=epochs,
        batch=batch,
        imgsz=img_size,
        project=str(YOLO_DIR / "runs"),
        name=nombre,
        patience=10,  # Early stopping si no mejora en 10 épocas
        save=True,
        plots=True,
        verbose=True
    )
    
    print(f"\n✅ Entrenamiento completado: {nombre}")
    print(f"   Modelo guardado en: {YOLO_DIR / 'runs' / nombre}")
    
    return model

# ============================================
# PASO 3: Evaluar todos los modelos
# ============================================

def evaluar_modelos():
    """
    Evalúa los 5 modelos entrenados en sus datasets de validación.
    """
    print("\n" + "="*70)
    print("EVALUANDO MODELOS")
    print("="*70 + "\n")
    
    clasificadores = ['burbujas', 'bordes', 'distribucion', 'horneado', 'grasa']
    
    resultados = {}
    
    for nombre in clasificadores:
        print(f"\n📊 Evaluando: {nombre}")
        
        # Cargar mejor modelo entrenado
        model_path = YOLO_DIR / "runs" / nombre / "weights" / "best.pt"
        
        if not model_path.exists():
            print(f"  ⚠️  Modelo no encontrado: {model_path}")
            continue
        
        model = YOLO(str(model_path))
        
        # Validar
        val_results = model.val(
            data=str(YOLO_DIR / nombre),
            split='val'
        )
        
        # Extraer métricas
        top1_acc = val_results.top1  # Accuracy top-1
        top5_acc = val_results.top5  # Accuracy top-5
        
        resultados[nombre] = {
            'top1': top1_acc,
            'top5': top5_acc
        }
        
        print(f"  ✓ Top-1 Accuracy: {top1_acc:.4f}")
        print(f"  ✓ Top-5 Accuracy: {top5_acc:.4f}")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70 + "\n")
    
    for nombre, metricas in resultados.items():
        print(f"{nombre:15} | Top-1: {metricas['top1']:.4f} | Top-5: {metricas['top5']:.4f}")
    
    return resultados

# ============================================
# PASO 4: Inferencia en nuevas imágenes
# ============================================

def predecir_pizza(imagen_path, modelos_dir=None):
    """
    Predice todos los atributos de una imagen de pizza.
    
    Args:
        imagen_path: Ruta a la imagen
        modelos_dir: Directorio con los modelos entrenados
    
    Returns:
        dict con predicciones de cada atributo
    """
    if modelos_dir is None:
        modelos_dir = YOLO_DIR / "runs"
    
    clasificadores = ['burbujas', 'bordes', 'distribucion', 'horneado', 'grasa']
    predicciones = {}
    
    print(f"\n🔍 Analizando: {Path(imagen_path).name}\n")
    
    for nombre in clasificadores:
        model_path = modelos_dir / nombre / "weights" / "best.pt"
        
        if not model_path.exists():
            print(f"  ⚠️  Modelo {nombre} no encontrado")
            continue
        
        # Cargar modelo
        model = YOLO(str(model_path))
        
        # Predecir
        results = model.predict(
            source=str(imagen_path),
            verbose=False
        )
        
        # Extraer predicción
        pred_class = results[0].names[results[0].probs.top1]
        confidence = results[0].probs.top1conf.item()
        
        predicciones[nombre] = {
            'clase': pred_class,
            'confianza': confidence
        }
        
        print(f"  {nombre:15} → {pred_class:15} (confianza: {confidence:.2%})")
    
    return predicciones

# ============================================
# PASO 5: Exportar modelos para producción
# ============================================

def exportar_modelos(formato='onnx'):
    """
    Exporta los modelos a formato optimizado para producción.
    
    Args:
        formato: 'onnx', 'torchscript', 'tflite', etc.
    """
    print("\n" + "="*70)
    print(f"EXPORTANDO MODELOS A {formato.upper()}")
    print("="*70 + "\n")
    
    clasificadores = ['burbujas', 'bordes', 'distribucion', 'horneado', 'grasa']
    
    for nombre in clasificadores:
        print(f"\n📦 Exportando: {nombre}")
        
        model_path = YOLO_DIR / "runs" / nombre / "weights" / "best.pt"
        
        if not model_path.exists():
            print(f"  ⚠️  Modelo no encontrado")
            continue
        
        model = YOLO(str(model_path))
        
        # Exportar
        export_path = model.export(format=formato)
        
        print(f"  ✓ Exportado a: {export_path}")
    
    print("\n✅ Exportación completada")

# ============================================
# MAIN: Flujo completo
# ============================================

def main():
    """
    Flujo completo de entrenamiento.
    """
    print("\n" + "="*70)
    print("ENTRENAMIENTO YOLO PARA CLASIFICACIÓN DE PIZZAS")
    print("="*70 + "\n")
    
    print("Este script realizará:")
    print("  1. Preparar estructura de datos para YOLO")
    print("  2. Entrenar 5 modelos independientes (uno por atributo)")
    print("  3. Evaluar modelos en dataset de validación")
    print("  4. Exportar modelos a formato ONNX\n")
    
    choice = input("¿Continuar? (s/n): ").strip().lower()
    if choice != 's':
        print("Operación cancelada.")
        return
    
    # Paso 1: Preparar datos
    print("\n🔧 PASO 1: Preparando datos...")
    preparar_estructura_yolo()
    
    # Paso 2: Entrenar modelos
    print("\n🚀 PASO 2: Entrenando modelos...\n")
    
    clasificadores_config = {
        'burbujas': ['si', 'no'],
        'bordes': ['limpio', 'sucio'],
        'distribucion': ['correcto', 'aceptable', 'media', 'mala', 'deficiente'],
        'horneado': ['correcto', 'alto', 'bajo', 'insuficiente', 'excesivo'],
        'grasa': ['si', 'no']
    }
    
    # Parámetros de entrenamiento
    EPOCHS = 50  # Ajusta según necesites
    BATCH = 16   # Ajusta según tu GPU/RAM
    IMG_SIZE = 640
    
    for nombre, clases in clasificadores_config.items():
        entrenar_clasificador(nombre, clases, epochs=EPOCHS, batch=BATCH, img_size=IMG_SIZE)
    
    # Paso 3: Evaluar
    print("\n📊 PASO 3: Evaluando modelos...")
    resultados = evaluar_modelos()
    
    # Paso 4: Exportar
    print("\n📦 PASO 4: Exportando modelos...")
    exportar_modelos(formato='onnx')
    
    print("\n" + "="*70)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("="*70)
    print(f"\nModelos guardados en: {YOLO_DIR / 'runs'}")
    print(f"Modelos ONNX para producción: {YOLO_DIR / 'runs' / '<nombre>' / 'weights'}")
    print("\nPara usar los modelos, ejecuta:")
    print("  python3 predecir_pizza_yolo.py <ruta_imagen>")

if __name__ == "__main__":
    main()
