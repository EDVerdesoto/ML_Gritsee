#!/usr/bin/env python3
"""
Verificador de completitud usando los archivos CSV.
Lee los CSVs y verifica que existan las imágenes esperadas.
"""
import csv
import os
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"
CSV_DIR = Path.home() / "Practicas" / "Descarga de archivos" / "Archivos"

CATEGORY_FOLDERS = {
    'burbujas': {
        'Sí': 'burbujas/si',
        'No': 'burbujas/no'
    },
    'bordes': {
        'Sí': 'bordes/limpio',
        'No': 'bordes/sucio'
    },
    'distribucion': {
        'Correcta': 'distribucion/correcto',
        'Aceptable': 'distribucion/aceptable',
        'Media': 'distribucion/media',
        'Mala': 'distribucion/mala',
        'Deficiente': 'distribucion/deficiente'
    },
    'horneado': {
        'Correcto': 'horneado/correcto',
        'Alto': 'horneado/alto',
        'Bajo': 'horneado/bajo',
        'Insuficiente': 'horneado/insuficiente',
        'Excesivo': 'horneado/excesivo'
    },
    'grasa': {
        'Sí': 'grasa/si',
        'No': 'grasa/no'
    }
}

def get_expected_folders(classifications):
    """Devuelve lista de carpetas donde debería estar una imagen según sus clasificaciones."""
    folders = []
    if classifications['burbujas'] in ['Sí', 'No']:
        folders.append(CATEGORY_FOLDERS['burbujas'][classifications['burbujas']])
    if classifications['bordes'] in ['Sí', 'No']:
        folders.append(CATEGORY_FOLDERS['bordes'][classifications['bordes']])
    if classifications['distribucion'] in CATEGORY_FOLDERS['distribucion']:
        folders.append(CATEGORY_FOLDERS['distribucion'][classifications['distribucion']])
    if classifications['horneado'] in CATEGORY_FOLDERS['horneado']:
        folders.append(CATEGORY_FOLDERS['horneado'][classifications['horneado']])
    if classifications['grasa'] in ['Sí', 'No']:
        folders.append(CATEGORY_FOLDERS['grasa'][classifications['grasa']])
    return folders

def verify_csv(csv_file, starting_number=1):
    """Verifica que existan las imágenes esperadas según un CSV."""
    print(f"\n{'='*70}")
    print(f"VERIFICANDO: {csv_file.name}")
    print(f"{'='*70}\n")
    
    # Extraer location y start_date del nombre del CSV
    base_name, _ = os.path.splitext(csv_file.name)
    parts = base_name.split(' - ')
    if len(parts) < 2:
        print(f"❌ No se pudo extraer información del nombre del archivo CSV.")
        return
    
    location = parts[1]
    info_parts = parts[0].split(' ')
    if len(info_parts) < 2:
        print(f"❌ No se pudo extraer fecha del nombre del archivo CSV.")
        return
    
    start_date = info_parts[1]
    
    print(f"Location: {location}")
    print(f"Start Date: {start_date}")
    print(f"Numeración inicial: {starting_number}\n")
    
    # Leer CSV
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        next(csvfile)  # Saltar primera línea si es encabezado extra
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    
    total_rows = len(rows)
    print(f"Total de filas en CSV: {total_rows}\n")
    print(f"Rango de números esperados: 1 a {total_rows}\n")
    
    missing_images = []
    incomplete_images = []  # Imágenes que existen pero no en todas las carpetas esperadas
    complete_images = 0
    
    for idx, row in enumerate(rows):
        photo_link = row.get('Photo Link', '').strip()
        if not photo_link or not photo_link.startswith('http'):
            continue
        
        classifications = {
            'burbujas': row.get('Tiene Burbuja', '').strip(),
            'bordes': row.get('Bordes Limpios', '').strip(),
            'distribucion': row.get('Distribución de Ingredientes', '').strip(),
            'horneado': row.get('Nivel de Horneado', '').strip(),
            'grasa': row.get('Grasa en Superficie', '').strip()
        }
        
        # Numeración: cada imagen = índice de fila (empezando en 0) + 1
        actual_img_number = idx + 1
        filename = f"{location}-{start_date}-{actual_img_number}.png"
        expected_folders = get_expected_folders(classifications)
        
        # Verificar existencia en cada carpeta esperada
        found_in = []
        missing_in = []
        
        for folder_rel in expected_folders:
            full_path = BASE_DIR / folder_rel / filename
            if full_path.exists():
                found_in.append(folder_rel)
            else:
                missing_in.append(folder_rel)
        
        if not found_in:
            # No existe en ninguna carpeta
            missing_images.append((filename, expected_folders))
        elif missing_in:
            # Existe pero no en todas las carpetas esperadas
            incomplete_images.append((filename, found_in, missing_in))
        else:
            # Completa
            complete_images += 1
    
    # Reporte
    print(f"{'='*70}")
    print("RESULTADOS")
    print(f"{'='*70}\n")
    print(f"✅ Imágenes completas: {complete_images}/{total_rows}")
    print(f"⚠️  Imágenes incompletas: {len(incomplete_images)}")
    print(f"❌ Imágenes faltantes: {len(missing_images)}\n")
    
    if missing_images:
        print(f"{'='*70}")
        print("IMÁGENES FALTANTES (primeras 20)")
        print(f"{'='*70}\n")
        for fname, expected in missing_images[:20]:
            print(f"  - {fname}")
            print(f"    Debería estar en: {', '.join(expected)}")
    
    if incomplete_images:
        print(f"\n{'='*70}")
        print("IMÁGENES INCOMPLETAS (primeras 20)")
        print(f"{'='*70}\n")
        for fname, found, missing in incomplete_images[:20]:
            print(f"  - {fname}")
            print(f"    Encontrada en: {', '.join(found)}")
            print(f"    Falta en: {', '.join(missing)}")
    
    return {
        'total': total_rows,
        'complete': complete_images,
        'incomplete': len(incomplete_images),
        'missing': len(missing_images)
    }

def main():
    print(f"\n{'='*70}")
    print("VERIFICADOR DE IMÁGENES CON CSV")
    print(f"{'='*70}\n")
    
    csv_files = sorted(CSV_DIR.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ No se encontraron archivos CSV en {CSV_DIR}")
        return
    
    print(f"Archivos CSV encontrados: {len(csv_files)}\n")
    for idx, f in enumerate(csv_files, 1):
        print(f"  [{idx}] {f.name}")
    
    print("\nOpciones:")
    print("  - Ingresa un número para verificar un archivo específico")
    print("  - Ingresa 'todos' para verificar todos")
    print("  - Ingresa '0' para salir")
    
    choice = input("\nOpción: ").strip().lower()
    
    if choice == '0':
        return
    
    selected = []
    if choice == 'todos':
        selected = csv_files
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(csv_files):
                selected = [csv_files[idx - 1]]
            else:
                print("Número fuera de rango.")
                return
        except ValueError:
            print("Entrada inválida.")
            return
    
    # Verificar cada CSV (cada uno con numeración independiente desde 1)
    summary = []
    
    for csv_file in selected:
        result = verify_csv(csv_file, starting_number=1)
        if result:
            summary.append((csv_file.name, result))
    
    # Resumen general
    print(f"\n{'='*70}")
    print("RESUMEN GENERAL")
    print(f"{'='*70}\n")
    
    for csv_name, result in summary:
        status = "✅" if result['missing'] == 0 and result['incomplete'] == 0 else "⚠️"
        print(f"{status} {csv_name}: {result['complete']}/{result['total']} completas, "
              f"{result['incomplete']} incompletas, {result['missing']} faltantes")
    
    total_complete = sum(r['complete'] for _, r in summary)
    total_images = sum(r['total'] for _, r in summary)
    print(f"\nTotal general: {total_complete}/{total_images} imágenes completas")
    print(f"Porcentaje de completitud: {100 * total_complete / max(total_images, 1):.2f}%\n")

if __name__ == "__main__":
    main()
