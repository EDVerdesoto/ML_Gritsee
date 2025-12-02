# Guía de Uso - Sistema de Descarga y Gestión de Imágenes

## 📁 Archivos del Sistema

1. **descarga_archivos.py** - Script principal de descarga
2. **limpiar_duplicados.py** - Limpiador de duplicados por hash SHA256
3. **verificar_con_csv.py** - Verificador de completitud

---

## 🔄 Flujo de Trabajo Recomendado

### Escenario 1: Limpiar Duplicados Existentes

Si ya tienes imágenes descargadas con duplicados (~700 en tu caso):

```bash
# 1. Limpiar duplicados (DRY-RUN primero - NO mueve archivos)
python3 limpiar_duplicados.py --dry-run

# 2. Si el resultado se ve bien, ejecutar la limpieza real
python3 limpiar_duplicados.py

# 3. Verificar completitud después de limpiar
python3 verificar_con_csv.py
```

### Escenario 2: Descarga Inicial o Re-descarga

Si estás descargando por primera vez o quieres rehacer:

```bash
# 1. Ejecutar descarga (con numeración corregida)
python3 descarga_archivos.py

# 2. Verificar completitud
python3 verificar_con_csv.py

# 3. Si detectas duplicados (no debería pasar), limpia
python3 limpiar_duplicados.py
```

---

## 📝 Detalles de Cada Script

### `limpiar_duplicados.py`

**Propósito:** Encuentra y elimina imágenes duplicadas basándose en contenido (hash SHA256), no en nombres.

**IMPORTANTE:** Una misma imagen **DEBE** estar en múltiples carpetas (burbujas, bordes, distribución, horneado, grasa) porque cada imagen tiene múltiples clasificaciones. Esto NO son duplicados.

**Duplicados REALES:** Son imágenes con el **mismo contenido** y **diferentes números** en la **MISMA carpeta**.

**Ejemplo:**
```
✅ NO ES DUPLICADO (comportamiento correcto):
   burbujas/si/Cumbres-9_15-175.png
   bordes/limpio/Cumbres-9_15-175.png
   distribucion/mala/Cumbres-9_15-175.png
   → Misma imagen en diferentes categorías (CORRECTO)

❌ SÍ ES DUPLICADO (error a corregir):
   burbujas/si/Cumbres-9_15-175.png
   burbujas/si/Cumbres-9_15-812.png
   → Mismo contenido, misma carpeta, diferentes números (DUPLICADO)
```

**Funcionamiento:**
1. Escanea todas las imágenes y calcula hash SHA256 de cada una
2. Agrupa imágenes con el mismo contenido EN LA MISMA CARPETA
3. Para cada grupo de duplicados:
   - Lee el CSV correspondiente para determinar el rango válido (1 a N)
   - Identifica qué imagen tiene el número más bajo dentro del rango válido
   - Mueve las demás a `DUPLICADOS/` (mantiene estructura de carpetas)

**Modo Dry-Run:**
```bash
python3 limpiar_duplicados.py --dry-run
```
- NO mueve archivos
- Solo muestra lo que haría
- Genera log de depuración

**Modo Real:**
```bash
python3 limpiar_duplicados.py
```
- Mueve archivos a `DUPLICADOS/`
- Genera `log_limpieza_duplicados.txt`

**Ejemplo de Log:**
```
[Cumbres-9_15] [burbujas/si] - Hash: abc123...
  Duplicados en la misma carpeta: 2
  CSV: Backup 9_15 9_21 Evaluación Pizzas HQ - Cumbres.csv
  Rango válido: 1 a 368
  ✓ MANTENER: Cumbres-9_15-175.png (número 175)
    Ubicación: burbujas/si
  ✗ MOVER: Cumbres-9_15-812.png (número 812, fuera de rango)
    Desde: burbujas/si
    → DUPLICADOS/burbujas/si/
```

---

### `verificar_con_csv.py`

**Propósito:** Verifica que todas las imágenes esperadas según los CSVs estén descargadas y en las carpetas correctas.

**Numeración:** Cada imagen se numera según: `número_imagen = fila_csv - 2`
- Fila 3 del CSV = imagen 1
- Fila 4 del CSV = imagen 2
- etc.

**Uso Interactivo:**
```bash
python3 verificar_con_csv.py
```

Mostrará menú:
```
Archivos CSV encontrados: 5

  [1] Backup 9_15 9_21 Evaluación Pizzas HQ - Cumbres.csv
  [2] Backup 9_22 9_28 Evaluación Pizzas HQ - Cumbres.csv
  ...

Opciones:
  - Ingresa un número para verificar un archivo específico
  - Ingresa 'todos' para verificar todos
  - Ingresa '0' para salir
```

**Salida:**
- ✅ Imágenes completas: existen en todas las carpetas esperadas
- ⚠️ Imágenes incompletas: existen pero faltan en algunas carpetas
- ❌ Imágenes faltantes: no existen en ninguna carpeta

---

### `descarga_archivos.py`

**Propósito:** Descarga imágenes desde URLs en CSVs y las clasifica en carpetas según atributos.

**Numeración Corregida:** 
- Cada CSV tiene numeración **independiente** empezando en 1
- Ya NO acumula números entre CSVs
- CSV 1: imágenes 1-250
- CSV 2: imágenes 1-180 (NO 251-430)

**Características:**
- **Multi-threading:** 32 workers concurrentes
- **Reinicio inteligente:** Detecta CSVs ya descargados comparando imágenes existentes
- **Límite por carpeta:** 500 imágenes máximo en cada subcarpeta
- **Thread-safe:** Usa locks por carpeta para evitar race conditions
- **Progress bar:** Muestra velocidad de descarga en MB/s por imagen

**Estructura de Carpetas:**
```
BASE_DIR/
├── burbujas/
│   ├── si/
│   └── no/
├── bordes/
│   ├── limpio/
│   └── sucio/
├── distribucion/
│   ├── correcto/
│   ├── aceptable/
│   ├── media/
│   ├── mala/
│   └── deficiente/
├── horneado/
│   ├── correcto/
│   ├── alto/
│   ├── bajo/
│   ├── insuficiente/
│   └── excesivo/
└── grasa/
    ├── si/
    └── no/
```

---

## 🔍 Entendiendo la Numeración

### Sistema Anterior (INCORRECTO)
```
CSV 1 (100 imágenes): Cumbres-9_15-1 a Cumbres-9_15-100
CSV 2 (80 imágenes):  Cumbres-9_22-101 a Cumbres-9_22-180  ❌ MALO
                      ^^^^^^^^^^^^^^^ 101-180 causó duplicados
```

### Sistema Actual (CORRECTO)
```
CSV 1 (100 imágenes): Cumbres-9_15-1 a Cumbres-9_15-100
CSV 2 (80 imágenes):  Cumbres-9_22-1 a Cumbres-9_22-80   ✅ CORRECTO
                      ^^^^^^^^^^^^^^^ Cada CSV empieza en 1
```

**Fórmula:** `número_imagen = índice_fila + 1` (donde índice empieza en 0)
- Fila 3 del CSV (índice 0) → imagen 1
- Fila 4 del CSV (índice 1) → imagen 2

---

## ⚠️ Notas Importantes

1. **Backup antes de limpiar:** Aunque `limpiar_duplicados.py` mueve a `DUPLICADOS/`, considera hacer backup de `Descarga_Pizzas/` antes de la limpieza real.

2. **Dry-run es tu amigo:** Siempre ejecuta `--dry-run` primero para verificar qué se va a hacer.

3. **Logs:** Revisa `log_limpieza_duplicados.txt` después de la limpieza para ver decisiones detalladas.

4. **Tiempo de ejecución:** Con ~2444 imágenes, el cálculo de hashes puede tomar 2-5 minutos.

5. **CSVs en UTF-8:** Asegúrate que los CSVs estén en UTF-8 para evitar problemas de lectura.

---

## 🐛 Resolución de Problemas

### "No se encontraron archivos CSV"
- Verifica que los CSVs estén en: `~/Practicas/Descarga de archivos/Archivos/`

### "No such file or directory: Descarga_Pizzas"
- Las imágenes deben estar en: `~/Practicas/Descarga_Pizzas/`
- Si la carpeta no existe, `descarga_archivos.py` la crea automáticamente

### "Hash calculation taking too long"
- Normal para ~2500 imágenes (2-5 min)
- Si tarda más de 10 min, verifica que las imágenes sean PNG reales

### "Unexpected keyword argument 'expected_replacements'"
- Error en versión anterior del código, ya corregido

---

## 📊 Ejemplo Completo

```bash
# Situación inicial: 2444 imágenes, ~700 duplicados

# Paso 1: Simular limpieza
python3 limpiar_duplicados.py --dry-run
# Output: "[DRY-RUN] Se moverían 700 imágenes a DUPLICADOS/"

# Paso 2: Limpiar
python3 limpiar_duplicados.py
# Output: "700 imágenes movidas a DUPLICADOS/"

# Paso 3: Verificar completitud
python3 verificar_con_csv.py
# Elegir opción "todos"
# Output: "1744/1744 imágenes completas (100%)"

# Paso 4: Si faltara algo, re-descargar
python3 descarga_archivos.py
# Output: "CSV ya procesado, saltando..." (si todo está completo)
```

---

