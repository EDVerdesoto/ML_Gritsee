#!/usr/bin/env python3
"""
Script para predecir atributos de pizzas usando modelos YOLO entrenados.
Uso: python3 predecir_pizza_yolo.py <ruta_imagen>
"""

import sys
from pathlib import Path
from ultralytics import YOLO

YOLO_DIR = Path.home() / "Practicas" / "YOLO_Pizza_Training"

def predecir_pizza(imagen_path):
    """
    Predice todos los atributos de una imagen de pizza.
    """
    if not Path(imagen_path).exists():
        print(f"Imagen no encontrada: {imagen_path}")
        return None
    
    clasificadores = ['burbujas', 'bordes', 'distribucion', 'horneado', 'grasa']
    modelos_dir = YOLO_DIR / "runs"
    
    print("\n" + "="*70)
    print(f"ANÁLISIS DE PIZZA: {Path(imagen_path).name}")
    print("="*70 + "\n")
    
    predicciones = {}
    
    for nombre in clasificadores:
        model_path = modelos_dir / nombre / "weights" / "best.pt"
        
        if not model_path.exists():
            print(f" Modelo {nombre} no encontrado en: {model_path}")
            continue
        
        # Cargar modelo
        model = YOLO(str(model_path))
        
        # Predecir
        results = model.predict(
            source=str(imagen_path),
            verbose=False,
            conf=0.25  # Umbral de confianza mínimo
        )
        
        # Extraer predicción
        pred_class = results[0].names[results[0].probs.top1]
        confidence = results[0].probs.top1conf.item()
        
        # Obtener top 3 predicciones
        top3_indices = results[0].probs.top5[:3]
        top3_confs = results[0].probs.top5conf[:3]
        
        predicciones[nombre] = {
            'clase': pred_class,
            'confianza': confidence,
            'top3': [(results[0].names[idx.item()], conf.item()) 
                     for idx, conf in zip(top3_indices, top3_confs)]
        }
        
        # Mostrar resultado
        emoji = "✅" if confidence > 0.7 else "⚠️" if confidence > 0.5 else "❌"
        print(f"{emoji} {nombre.upper():15} → {pred_class:15} ({confidence:.1%})")
        
        # Mostrar top 3 si la confianza es baja
        if confidence < 0.7:
            print(f"   Alternativas:")
            for clase, conf in predicciones[nombre]['top3'][1:]:
                print(f"     - {clase:15} ({conf:.1%})")
    
    print("\n" + "="*70)
    print("RESUMEN DE EVALUACIÓN")
    print("="*70 + "\n")
    
    # Evaluar calidad general
    score = 0
    max_score = len(predicciones)
    
    for nombre, pred in predicciones.items():
        if pred['confianza'] > 0.7:
            score += pred['confianza']
        else:
            score += pred['confianza'] * 0.5  # Penalizar confianza baja
    
    calidad_general = (score / max_score) * 100
    
    if calidad_general >= 80:
        print(f"PIZZA DE ALTA CALIDAD ({calidad_general:.1f}/100)")
    elif calidad_general >= 60:
        print(f"PIZZA ACEPTABLE ({calidad_general:.1f}/100)")
    elif calidad_general >= 40:
        print(f"PIZZA CON DEFECTOS ({calidad_general:.1f}/100)")
    else:
        print(f"PIZZA DEFICIENTE ({calidad_general:.1f}/100)")
    
    print()
    
    return predicciones

def predecir_batch(directorio):
    """
    Predice atributos para todas las imágenes en un directorio.
    """
    directorio = Path(directorio)
    
    if not directorio.exists():
        print(f"Directorio no encontrado: {directorio}")
        return
    
    imagenes = list(directorio.glob("*.png")) + \
               list(directorio.glob("*.jpg")) + \
               list(directorio.glob("*.jpeg"))
    
    if not imagenes:
        print(f"No se encontraron imágenes en: {directorio}")
        return
    
    print(f"\nProcesando {len(imagenes)} imágenes de: {directorio}\n")
    
    resultados = []
    
    for img in imagenes:
        pred = predecir_pizza(str(img))
        if pred:
            resultados.append({
                'imagen': img.name,
                'predicciones': pred
            })
        print()  # Línea en blanco entre imágenes
    
    # Guardar resultados en CSV
    output_csv = directorio / "predicciones_yolo.csv"
    
    import csv
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Imagen', 'Burbujas', 'Confianza_Burbujas', 
                        'Bordes', 'Confianza_Bordes',
                        'Distribucion', 'Confianza_Distribucion',
                        'Horneado', 'Confianza_Horneado',
                        'Grasa', 'Confianza_Grasa'])
        
        for r in resultados:
            row = [r['imagen']]
            for clasificador in ['burbujas', 'bordes', 'distribucion', 'horneado', 'grasa']:
                if clasificador in r['predicciones']:
                    row.append(r['predicciones'][clasificador]['clase'])
                    row.append(f"{r['predicciones'][clasificador]['confianza']:.4f}")
                else:
                    row.extend(['N/A', '0'])
            writer.writerow(row)
    
    print(f"✅ Resultados guardados en: {output_csv}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 predecir_pizza_yolo.py <ruta_imagen_o_directorio>")
        print("\nEjemplos:")
        print("  python3 predecir_pizza_yolo.py pizza.jpg")
        print("  python3 predecir_pizza_yolo.py ~/Practicas/Descarga_Pizzas/burbujas/si")
        sys.exit(1)
    
    ruta = Path(sys.argv[1])
    
    if ruta.is_dir():
        predecir_batch(ruta)
    elif ruta.is_file():
        predecir_pizza(str(ruta))
    else:
        print(f"Ruta no válida: {ruta}")
        sys.exit(1)

if __name__ == "__main__":
    main()
