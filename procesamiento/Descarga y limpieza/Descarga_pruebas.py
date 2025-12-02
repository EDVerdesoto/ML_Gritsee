import csv
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
from tqdm import tqdm
from threading import Lock
import threading
import time
from collections import defaultdict
from requests.adapters import HTTPAdapter

# Configuración
MAIN_DIR = Path(__file__).resolve().parent.parent.parent  # Descarga_pruebas.py -> Descarga y limpieza -> procesamiento -> ML_Gritsee
BASE_DIR = MAIN_DIR / "datasets" / "test_dataset"
MAX_WORKERS = 32  # Descargas simultáneas

# Índice de archivos existentes por nombre (para reanudar sin redescargar)
EXISTING_INDEX = defaultdict(list)  # filename -> [paths]
INDEX_LOCK = Lock() # Candado para acceso al índice

def build_existing_index():
    # Construye un índice de archivos ya existentes para evitar redescargar
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        return
    with INDEX_LOCK: # Construir índice
        EXISTING_INDEX.clear()
        for fname in os.listdir(BASE_DIR):
            if fname.endswith(('.png', '.jpg', '.jpeg')):
                EXISTING_INDEX[fname].append(BASE_DIR / fname)

def find_existing_image(filename: str):
    with INDEX_LOCK: # Buscar en el índice de existentes
        paths = EXISTING_INDEX.get(filename)
        if paths:
            return paths[0]
    return None

def register_created_file(filename: str, path: Path):
    with INDEX_LOCK: # Registrar nuevo archivo en el índice
        EXISTING_INDEX[filename].append(path)

def list_csv_files():
    # Lista todos los archivos CSV en el directorio actual
    current_dir = MAIN_DIR / "procesamiento" / "Archivos"
    csv_files = sorted(current_dir.glob("*.csv"))
    return csv_files

def compare_images(start_date, location):
    # Verifica si ya existen imágenes con el prefijo esperado
    # Prefijo: <location>-<start_date>-
    prefix = f"{location}-{start_date}-"
    
    if not BASE_DIR.exists():
        return False
    
    try:
        for fname in os.listdir(BASE_DIR):
            if fname.startswith(prefix):
                return True
    except Exception:
        pass
    
    return False

def show_menu():
    # Menu para seleccionar los CSV dentro de la carpeta 
    print("\n" + "="*60)
    print("  DESCARGADOR DE IMÁGENES DE PIZZAS")
    print("="*60)
    
    csv_files = list_csv_files()
    
    if not csv_files:
        print("\nNo se encontraron archivos CSV en el directorio actual.")
        print(f"Directorio actual: {Path.cwd()}")
        return []
    
    print(f"\nArchivos CSV encontrados en: {Path.cwd()}\n")
    
    for idx, file in enumerate(csv_files, 1):
        file_size = file.stat().st_size / 1024  # Tamaño en KB
        print(f"  [{idx}] {file.name:<50} ({file_size:.1f} KB)")
    
    print("="*60)
    
    selected_files = []
    
    while True:
        print("\nOpciones:")
        print("  - Ingresa un número para seleccionar un archivo")
        print("  - Ingresa varios números separados por comas (ej: 1,2,3)")
        print("  - Ingresa 'todos' para procesar todos los archivos")
        print("  - Ingresa '0' para salir")
        
        choice = input("\nOpción: ").strip().lower()
        
        if choice == '0':
            print("\nSaliendo...")
            return []
        
        if choice == 'todos':
            selected_files = csv_files
            break
        
        # Procesar selección múltiple
        try:
            selections = [int(x.strip()) for x in choice.split(',')]
            selected_files = []
            
            for sel in selections:
                if 1 <= sel <= len(csv_files):
                    selected_files.append(csv_files[sel - 1])
                else:
                    print(f"ERROR: Número {sel} fuera de rango de los archivos almacenados.")
                    selected_files = []
                    break
            
            if selected_files:
                break
                
        except ValueError:
            print("Entrada inválida. Usa números separados por comas.")
    
    # Confirmar selección
    print("\n" + "="*60)
    print("Archivos seleccionados:")
    for idx, file in enumerate(selected_files, 1):
        print(f"  {idx}. {file.name}")
    print("="*60)
    
    confirm = input("\n¿Proceder con la descarga? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("\nOperación cancelada.")
        show_menu()
    
    return selected_files

_thread_local = threading.local()

def _get_session():
    # Sesión por hilo con pool de conexiones para acelerar descargas
    session = getattr(_thread_local, 'session', None)
    if session is None:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        _thread_local.session = session
    return session

def process_single_image(row, img_number, starting_number, location, start_date):
    # Descarga y copia una sola imagen, viendo la fila del csv
    photo_link = row.get('Photo Link', '').strip()
    
    # Validar enlace 
    if not photo_link or not photo_link.startswith('http'):
        return None
    
    # Número de imagen real
    actual_img_number = starting_number + img_number
    
    filename = f"{location}-{start_date}-{actual_img_number}.png"

    existing_path = find_existing_image(filename)
    if existing_path and Path(existing_path).exists():
        return {
            'number': actual_img_number,
            'success': True,
            'cached': True,
            'mbps': None
        }
    # Descargar directamente a BASE_DIR
    final_path = BASE_DIR / filename
    
    try:
        session = _get_session()
        response = session.get(photo_link, timeout=30, stream=True)
        response.raise_for_status()
        
        total_bytes = 0
        start = time.perf_counter()
        
        with open(final_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
        
        elapsed = max(time.perf_counter() - start, 1e-6)
        mbps = (total_bytes / (1024 * 1024)) / elapsed
        
        # Registrar en el índice
        register_created_file(filename, final_path)
        
        return {
            'number': actual_img_number,
            'success': True,
            'cached': False,
            'mbps': mbps
        }
        
    except Exception as e:
        # Si falla, eliminar archivo parcial
        if final_path.exists():
            final_path.unlink()
        print(f"Error descargando imagen {actual_img_number}: {e}")
        return {
            'number': actual_img_number,
            'success': False,
            'cached': False,
            'mbps': None
        }

def process_csv(csv_file, starting_number=1, location=None, start_date=None):
    # Procesa un CSV con descarga paralela y barra de progreso
    print(f"\n{'='*60}")
    print(f"Procesando: {csv_file.name}")
    print(f"{'='*60}")
    
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        # Saltar primera línea de encabezado si existe
        next(csvfile)
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    
    total_rows = len(rows)
    print(f"Total de imágenes a procesar: {total_rows}")
    print(f"Numeración: {location}-{start_date}-{starting_number} a {location}-{start_date}-{starting_number + total_rows - 1}\n")
    
    successful = 0
    failed = 0
    cached = 0
    
    # Descarga paralela con barra de progreso
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Crear futures
        futures = {
            executor.submit(process_single_image, row, idx, starting_number, location, start_date): idx
            for idx, row in enumerate(rows)
        }
        
        # Barra de progreso con tqdm (dentro del contexto del executor para ver avances en vivo)
        with tqdm(total=total_rows, desc="Descargando", 
                unit="img", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
                dynamic_ncols=True, colour='green') as pbar:
            
            for future in as_completed(futures):
                result = future.result()
                
                if result and result['success']:
                    successful += 1
                    if result.get('cached'):
                        cached += 1
                    else:
                        mbps = result.get('mbps')
                        if mbps:
                            pbar.set_postfix_str(f"{mbps:.2f} MB/s")
                elif result:
                    failed += 1
                
                pbar.update(1)
    
    print(f"\n{'='*60}")
    print(f"Resumen: {successful} exitosas ({cached} en caché), {failed} fallidas")
    print(f"{'='*60}\n")

def main():
    # Mostrar menú y obtener archivos seleccionados
    selected_files = show_menu()
    
    # Salir si no hay archivos seleccionados
    if not selected_files:
        return
    
    # Construir índice de existentes para reanudar sin duplicar
    build_existing_index()

    # Personalizar nombre de los archivos descargados
    for csv_file in selected_files:
        base_name, extension = os.path.splitext(csv_file.name)
        parts = base_name.split(' - ')
        location = parts[1]
        info_parts = parts[0].split(' ')
        start_date = info_parts[1]
        # Si ya existe al menos UNA imagen de esta locación+fecha, omitir el CSV completo
        if compare_images(start_date, location):
            print(f"\n{'='*60}")
            print(f"Se detectó al menos una imagen para {location}-{start_date}. Se omite {csv_file.name}.")
            print(f"{'='*60}\n")
            continue
        # Cada CSV tiene numeración independiente empezando en 1
        process_csv(csv_file, starting_number=1, location=location, start_date=start_date)
    
    print(f"\n{'='*60}")
    print(f"PROCESO COMPLETO!!")
    print(f"Ubicación: {BASE_DIR}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
