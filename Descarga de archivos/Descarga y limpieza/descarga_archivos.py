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
BASE_DIR = Path.home() / "Practicas" / "Descarga_Pizzas"
TEMP_DIR = BASE_DIR / "temp_downloads"
MAX_WORKERS = 32  # Descargas simultáneas
MAX_IMAGES_PER_FOLDER = 50000  # (Sin uso: límite eliminado)

# Mapeo de carpetas por categoría
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

# Bloqueos por carpeta para evitar exceder el límite en descargas concurrentes
_FOLDER_LOCKS: dict[str, Lock] = {}
_FOLDER_LOCKS_MUTEX = Lock()

def _get_folder_lock(folder: Path) -> Lock:
    """Obtiene (o crea) un candado por carpeta para operaciones atómicas de conteo+copiado."""
    key = str(folder.resolve())
    with _FOLDER_LOCKS_MUTEX:
        lock = _FOLDER_LOCKS.get(key)
        if lock is None:
            lock = Lock()
            _FOLDER_LOCKS[key] = lock
        return lock

def create_folders():
    # Crea todas las carpetas necesarias
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for category_dict in CATEGORY_FOLDERS.values():
        for folder_path in category_dict.values():
            full_path = BASE_DIR / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
    print(f"Estructura de carpetas lista en {BASE_DIR}")

# Índice de archivos existentes por nombre (para reanudar sin redescargar)
EXISTING_INDEX = defaultdict(list)  # filename -> [paths]
INDEX_LOCK = Lock() # Candado para acceso al índice

def build_existing_index():
    # Construye un índice de archivos ya existentes para evitar redescargar
    if not BASE_DIR.exists():
        return
    with INDEX_LOCK: # Construir índice
        EXISTING_INDEX.clear()
        for dirpath, _, files in os.walk(BASE_DIR):
            # Omitir carpeta temporal
            if str(dirpath).startswith(str(TEMP_DIR)):
                continue
            for fname in files:
                EXISTING_INDEX[fname].append(Path(dirpath) / fname)

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
    current_dir = Path.home() / "Practicas" / "Descarga de archivos" / "Archivos"
    csv_files = sorted(current_dir.glob("*.csv"))
    return csv_files

def list_images():
    # Lista todas las imágenes encontradas (no usada para verificación por prefijo)
    images = []
    for dirpath, _, files in os.walk(BASE_DIR):
        for fname in files:
            images.append(fname)
    return images

def compare_images(start_date, location):
    # Verifica si ya existen imágenes con el prefijo esperado en las carpetas de categoría
    # Prefijo: <location>-<start_date>-
    prefix = f"{location}-{start_date}-"
    # Buscar solo en las carpetas de categoría (más rápido que recorrer todo BASE_DIR)
    for category_dict in CATEGORY_FOLDERS.values():
        for rel in category_dict.values():
            folder = BASE_DIR / rel
            if not folder.exists():
                continue
            try:
                for fname in os.listdir(folder):
                    if fname.startswith(prefix):
                        return True
            except Exception:
                # Ignorar errores de lectura de directorio y continuar
                continue
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

def download_image(url, img_number, location, start_date):
    # Descarga UNA imagen y la guarda temporalmente
    try:
        session = _get_session()
        response = session.get(url, timeout=30, stream=True) # se usa sesion para acelerar
        response.raise_for_status() # lanza error si HTTP es error
        
        extension = '.png'
        temp_file = TEMP_DIR / f"{location}-{start_date}-{img_number}{extension}"
        total_bytes = 0
        start = time.perf_counter()
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                total_bytes += len(chunk)
        elapsed = max(time.perf_counter() - start, 1e-6)
        
        return temp_file, extension, total_bytes, elapsed
    except Exception as e:
        print(f"Error descargando imagen {img_number} desde {url}: {e}")
        return None, None, 0, 0.0

def copy_to_folders(source_file, img_number, extension, classifications, location, start_date):
    # Copia la imagen a todas las carpetas correspondientes
    if not source_file or not Path(source_file).exists():
        return 0

    # Cambiar nombre del archivo para identificación 
    filename = f"{location}-{start_date}-{img_number}{extension}"
    folders_to_save = []

    # Determinar carpetas destino dependiendo de las columnas del CSV
    if classifications['burbujas'] in ['Sí', 'No']:
        folders_to_save.append(CATEGORY_FOLDERS['burbujas'][classifications['burbujas']])
    
    if classifications['bordes'] in ['Sí', 'No']:
        folders_to_save.append(CATEGORY_FOLDERS['bordes'][classifications['bordes']])
    
    if classifications['distribucion'] in CATEGORY_FOLDERS['distribucion']:
        folders_to_save.append(CATEGORY_FOLDERS['distribucion'][classifications['distribucion']])
    
    if classifications['horneado'] in CATEGORY_FOLDERS['horneado']:
        folders_to_save.append(CATEGORY_FOLDERS['horneado'][classifications['horneado']])
    
    if classifications['grasa'] in ['Sí', 'No']:
        folders_to_save.append(CATEGORY_FOLDERS['grasa'][classifications['grasa']])
    
    saved = 0

    for folder in folders_to_save:
        dest_dir = BASE_DIR / folder
        # Operación con candado por carpeta para evitar carreras de E/S
        lock = _get_folder_lock(dest_dir)
        with lock:
            dest_path = dest_dir / filename
            # Evitar duplicados si el archivo ya existe
            if dest_path.exists():
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, dest_path)
            register_created_file(filename, dest_path)
            saved += 1

    return saved

def process_single_image(row, img_number, starting_number, location, start_date):
    # Descarga y copia una sola imagen, viendo la fila del csv
    photo_link = row.get('Photo Link', '').strip()
    
    # Validar enlace 
    if not photo_link or not photo_link.startswith('http'):
        return None
    
    # Obtener clasificaciones
    classifications = {
        'burbujas': row.get('Tiene Burbuja', '').strip(),
        'bordes': row.get('Bordes Limpios', '').strip(),
        'distribucion': row.get('Distribución de Ingredientes', '').strip(),
        'horneado': row.get('Nivel de Horneado', '').strip(),
        'grasa': row.get('Grasa en Superficie', '').strip()
    }
    
    # Número de imagen real
    actual_img_number = starting_number + img_number
    
    filename = f"{location}-{start_date}-{actual_img_number}.png"

    # Reanudar: si ya existe en alguna carpeta, reutilizar y completar donde falte
    existing_source = find_existing_image(filename)
    if existing_source and Path(existing_source).exists():
        folders_saved = copy_to_folders(existing_source, actual_img_number, '.png', classifications, location, start_date)
        return {
            'number': actual_img_number,
            'folders': folders_saved,
            'success': True,
            'cached': True,
            'mbps': None
        }

    # Descargar imagen nueva
    temp_file, extension, total_bytes, elapsed = download_image(photo_link, actual_img_number, location, start_date)
    
    if temp_file:
        # Copiar a carpetas correspondientes
        folders_saved = copy_to_folders(temp_file, actual_img_number, extension, classifications, location, start_date)
        
        # Eliminar archivo temporal
        try:
            temp_file.unlink()
        except Exception:
            pass
        
        mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
        return {
            'number': actual_img_number,
            'folders': folders_saved,
            'success': True,
            'cached': False,
            'mbps': mbps
        }
    
    return {
        'number': actual_img_number,
        'folders': 0,
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
    
    # Descarga paralela con barra de progreso
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Crear futures
        futures = {
            executor.submit(process_single_image, row, idx, starting_number, location, start_date): idx
            for idx, row in enumerate(rows)
        }
        
        # Barra de progreso con tqdm (dentro del contexto del executor para ver avances en vivo)
        with tqdm(total=total_rows, desc="Descargando", 
                unit="img", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}',
                dynamic_ncols=True, colour='green') as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result and result['success']:
                    successful += 1
                    if result.get('cached'):
                        pbar.set_postfix_str(f"img{result['number']} cache → {result['folders']} carpetas")
                    else:
                        mbps = result.get('mbps')
                        if mbps is not None:
                            pbar.set_postfix_str(f"img{result['number']} → {result['folders']} carpetas | {mbps:.2f} MB/s")
                        else:
                            pbar.set_postfix_str(f"img{result['number']} → {result['folders']} carpetas")
                elif result:
                    failed += 1
                    pbar.set_postfix_str(f"img{result['number']} falló")
                
                pbar.update(1)
    
    print(f"\n{'='*60}")
    print(f"Resumen: {successful} exitosas, {failed} fallidas")
    print(f"{'='*60}\n")

def main():
    # Mostrar menú y obtener archivos seleccionados
    selected_files = show_menu()
    
    # Salir si no hay archivos seleccionados
    if not selected_files:
        return
    
    # Crear estructura de carpetas
    create_folders()
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
    
    # Limpiar carpeta temporal
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    
    print(f"\n{'='*60}")
    print(f"PROCESO COMPLETO!!")
    print(f"Ubicación: {BASE_DIR}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
