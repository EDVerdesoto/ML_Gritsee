#!/usr/bin/env python3
"""
Limpiador de imágenes duplicadas basado en hash SHA256.
Detecta imágenes con contenido idéntico EN LA MISMA CARPETA y mantiene solo la correcta.
Una misma imagen puede existir en múltiples carpetas (categorías) sin ser considerada duplicada.
Mueve duplicados a DUPLICADOS/ manteniendo estructura de categorías.
"""
import os
import csv
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"
CSV_DIR = Path.home() / "Practicas" / "Descarga de archivos" / "Archivos"
DUPLICADOS_DIR = BASE_DIR / "DUPLICADOS"
LOG_FILE = Path.home() / "Practicas" / "Descarga de archivos" / "log_limpieza_duplicados.txt"

CATEGORY_FOLDERS = {
    'burbujas': ['burbujas/si', 'burbujas/no'],
    'bordes': ['bordes/limpio', 'bordes/sucio'],
    'distribucion': ['distribucion/correcto', 'distribucion/aceptable', 
                    'distribucion/media', 'distribucion/mala', 'distribucion/deficiente'],
    'horneado': ['horneado/correcto', 'horneado/alto', 'horneado/bajo', 
                'horneado/insuficiente', 'horneado/excesivo'],
    'grasa': ['grasa/si', 'grasa/no']
}

def get_all_category_folders():
    """Devuelve lista de todas las carpetas de categoría absolutas."""
    folders = []
    for paths in CATEGORY_FOLDERS.values():
        folders.extend([BASE_DIR / p for p in paths])
    return folders

def calculate_hash(file_path):
    """Calcula hash SHA256 de un archivo."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        print(f"Error calculando hash de {file_path}: {e}")
        return None

def get_csv_for_location_date(location, start_date):
    """Encuentra el CSV correspondiente a una location-date."""
    # Buscar CSV que contenga location y start_date en el nombre
    for csv_file in CSV_DIR.glob("*.csv"):
        if location in csv_file.name and start_date in csv_file.name:
            return csv_file
    return None

def get_valid_range_from_csv(csv_file):
    """Lee el CSV y retorna el rango válido de números (1 a N)."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            next(f)  # Saltar primera línea
            reader = csv.DictReader(f)
            rows = list(reader)
            return len(rows)  # Números válidos: 1 a len(rows)
    except Exception as e:
        print(f"Error leyendo CSV {csv_file.name}: {e}")
        return None

def scan_and_hash_images():
    """Escanea todas las imágenes y calcula sus hashes."""
    print(f"\n{'='*70}")
    print("ESCANEANDO Y CALCULANDO HASHES DE IMÁGENES")
    print(f"{'='*70}\n")
    
    # file_path -> (hash, location, date, number, folder_rel)
    image_data = {}
    
    folders = get_all_category_folders()
    total_folders = len(folders)
    
    for idx, folder in enumerate(folders, 1):
        if not folder.exists():
            continue
        
        folder_rel = folder.relative_to(BASE_DIR)
        print(f"[{idx}/{total_folders}] Escaneando {folder_rel}...")
        
        for fname in os.listdir(folder):
            fpath = folder / fname
            if not fpath.is_file() or not fname.endswith('.png'):
                continue
            
            # Extraer location-date-number del nombre
            # Formato esperado: Location-Date-Number.png
            parts = fname.rsplit('-', 1)
            if len(parts) != 2:
                continue
            
            prefix = parts[0]  # Location-Date
            num_str = parts[1].replace('.png', '')
            
            try:
                number = int(num_str)
            except ValueError:
                continue
            
            # Separar location y date
            prefix_parts = prefix.split('-')
            if len(prefix_parts) < 2:
                continue
            
            location = prefix_parts[0]
            start_date = '-'.join(prefix_parts[1:])  # Puede tener múltiples guiones
            
            # Calcular hash
            file_hash = calculate_hash(fpath)
            if not file_hash:
                continue
            
            image_data[str(fpath)] = {
                'hash': file_hash,
                'location': location,
                'date': start_date,
                'number': number,
                'folder_rel': str(folder_rel),
                'filename': fname
            }
    
    print(f"\n✓ Total de imágenes escaneadas: {len(image_data)}\n")
    return image_data

def group_by_hash(image_data):
    """Agrupa imágenes por hash + carpeta (encuentra duplicados en la MISMA carpeta)."""
    # Clave: (hash, folder_rel) para detectar duplicados solo en la misma carpeta
    hash_folder_groups = defaultdict(list)
    
    for fpath, data in image_data.items():
        key = (data['hash'], data['folder_rel'])
        hash_folder_groups[key].append((fpath, data))
    
    # Filtrar solo grupos con más de una imagen (duplicados)
    duplicates = {k: imgs for k, imgs in hash_folder_groups.items() if len(imgs) > 1}
    
    return duplicates

def clean_duplicates(duplicates, image_data, dry_run=False):
    """Limpia duplicados manteniendo solo la imagen correcta (por carpeta)."""
    print(f"\n{'='*70}")
    print("PROCESANDO DUPLICADOS")
    print(f"{'='*70}\n")
    
    log_lines = []
    log_lines.append(f"={'='*70}\n")
    log_lines.append(f"LOG DE LIMPIEZA DE DUPLICADOS\n")
    log_lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_lines.append(f"Modo: {'DRY RUN' if dry_run else 'REAL'}\n")
    log_lines.append(f"{'='*70}\n\n")
    
    total_moved = 0
    total_kept = 0
    
    for (hash_val, folder_rel), images in duplicates.items():
        # Todos en este grupo tienen el mismo hash Y están en la misma carpeta
        location = images[0][1]['location']
        start_date = images[0][1]['date']
        loc_date_key = f"{location}-{start_date}"
        
        log_lines.append(f"\n[{loc_date_key}] [{folder_rel}] - Hash: {hash_val[:16]}...\n")
        log_lines.append(f"  Duplicados en la misma carpeta: {len(images)}\n")
        
        # Obtener CSV y rango válido
        csv_file = get_csv_for_location_date(location, start_date)
        if not csv_file:
            log_lines.append(f"  ⚠️  No se encontró CSV para {loc_date_key}, omitiendo grupo\n")
            continue
        
        valid_range = get_valid_range_from_csv(csv_file)
        if not valid_range:
            log_lines.append(f"  ⚠️  No se pudo leer rango válido del CSV, omitiendo grupo\n")
            continue
        
        log_lines.append(f"  CSV: {csv_file.name}\n")
        log_lines.append(f"  Rango válido: 1 a {valid_range}\n")
        
        # Separar en válidos e inválidos
        valid_images = [(fp, d) for fp, d in images if 1 <= d['number'] <= valid_range]
        invalid_images = [(fp, d) for fp, d in images if d['number'] > valid_range]
        
        # Determinar cuál mantener (menor número válido)
        if valid_images:
            valid_images.sort(key=lambda x: x[1]['number'])
            to_keep = valid_images[0]
            to_move = valid_images[1:] + invalid_images
        else:
            # Si no hay válidos, mantener el de menor número (aunque esté fuera de rango)
            images.sort(key=lambda x: x[1]['number'])
            to_keep = images[0]
            to_move = images[1:]
        
        # Log de decisión
        keep_fpath, keep_data = to_keep
        log_lines.append(f"  ✓ MANTENER: {keep_data['filename']} (número {keep_data['number']})\n")
        log_lines.append(f"    Ubicación: {keep_data['folder_rel']}\n")
        total_kept += 1
        
        # Mover duplicados
        for move_fpath, move_data in to_move:
            reason = "fuera de rango" if move_data['number'] > valid_range else f"duplicado de #{keep_data['number']}"
            log_lines.append(f"  ✗ MOVER: {move_data['filename']} (número {move_data['number']}, {reason})\n")
            log_lines.append(f"    Desde: {move_data['folder_rel']}\n")
            
            # Crear carpeta destino en DUPLICADOS
            dest_folder = DUPLICADOS_DIR / move_data['folder_rel']
            dest_path = dest_folder / move_data['filename']
            
            if not dry_run:
                dest_folder.mkdir(parents=True, exist_ok=True)
                
                # Mover archivo
                try:
                    os.rename(move_fpath, dest_path)
                    log_lines.append(f"    → {dest_folder.relative_to(BASE_DIR.parent)}\n")
                    total_moved += 1
                except Exception as e:
                    log_lines.append(f"    ⚠️  Error al mover: {e}\n")
            else:
                log_lines.append(f"    → (DRY RUN) {dest_folder.relative_to(BASE_DIR.parent)}\n")
                total_moved += 1
    
    # Resumen final
    summary = f"\n{'='*70}\n"
    summary += f"RESUMEN\n"
    summary += f"{'='*70}\n"
    summary += f"Grupos de duplicados procesados: {len(duplicates)}\n"
    summary += f"Imágenes mantenidas: {total_kept}\n"
    summary += f"Imágenes movidas a DUPLICADOS/: {total_moved}\n"
    
    if dry_run:
        summary += f"\n⚠️  MODO DRY RUN: No se movieron archivos realmente\n"
    
    log_lines.append(summary)
    
    # Escribir log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    
    print(summary)
    print(f"\n✓ Log guardado en: {LOG_FILE}\n")

def main():
    print(f"\n{'='*70}")
    print("LIMPIADOR DE DUPLICADOS BASADO EN HASH")
    print(f"{'='*70}\n")
    
    print("Este script:")
    print("  1. Escanea todas las imágenes y calcula sus hashes SHA256")
    print("  2. Agrupa imágenes con contenido idéntico EN LA MISMA CARPETA")
    print("  3. Para cada grupo, mantiene solo la imagen con el número menor válido")
    print("  4. Mueve los duplicados a DUPLICADOS/ manteniendo la estructura")
    print("  5. Genera un log detallado de todas las operaciones\n")
    
    choice = input("¿Proceder? (s/n): ").strip().lower()
    if choice != 's':
        print("\nOperación cancelada.")
        return
    
    dry_run_choice = input("\n¿Modo DRY RUN (simular sin mover archivos)? (s/n): ").strip().lower()
    dry_run = dry_run_choice == 's'
    
    # Paso 1: Escanear y calcular hashes
    image_data = scan_and_hash_images()
    
    if not image_data:
        print("No se encontraron imágenes para procesar.")
        return
    
    # Paso 2: Agrupar por hash
    duplicates = group_by_hash(image_data)
    
    if not duplicates:
        print("✓ No se encontraron duplicados (imágenes con contenido idéntico).\n")
        return
    
    print(f"Se encontraron {len(duplicates)} grupos de duplicados.\n")
    
    # Paso 3: Limpiar duplicados
    clean_duplicates(duplicates, image_data, dry_run=dry_run)

if __name__ == "__main__":
    main()
