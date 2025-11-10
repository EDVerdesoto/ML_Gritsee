# 🍕 Guía: Usar YOLO para Clasificación de Pizzas

## 📌 ¿Qué es YOLO para Clasificación?

**YOLO (You Only Look Once)** originalmente es para detección de objetos, pero **YOLOv8** incluye un modo de **clasificación** perfecto para tu caso:

- ✅ **Entrada**: Imagen de pizza completa (sin necesidad de bounding boxes)
- ✅ **Salida**: Clase predicha + confianza para cada atributo
- ✅ **Ventaja**: Modelo más simple y rápido que redes convolucionales personalizadas

---

## 🚀 Instalación

```bash
# Instalar YOLOv8 (Ultralytics)
pip install ultralytics

# Verificar instalación
yolo version
```

---

## 📁 Estructura de Tu Proyecto

Actualmente tienes:
```
~/Practicas/Descarga_Pizzas/
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

El script `entrenar_yolo_clasificacion.py` creará automáticamente:
```
~/Practicas/YOLO_Pizza_Training/
├── burbujas/
│   ├── train/
│   │   ├── si/
│   │   └── no/
│   └── val/
│       ├── si/
│       └── no/
├── bordes/
│   └── ...
├── distribucion/
│   └── ...
├── horneado/
│   └── ...
├── grasa/
│   └── ...
└── runs/
    ├── burbujas/
    │   └── weights/
    │       ├── best.pt    ← Mejor modelo
    │       └── last.pt
    ├── bordes/
    ├── distribucion/
    ├── horneado/
    └── grasa/
```

---

## 🎯 Flujo de Trabajo Completo

### **Paso 1: Limpiar y Verificar Datos**
```bash
# 1. Limpiar duplicados (MISMO SCRIPT QUE YA TIENES)
python3 limpiar_duplicados.py

# 2. Verificar completitud
python3 verificar_con_csv.py

# 3. (Opcional) Augmentación si tienes clases muy desbalanceadas
python3 aumentar_imagenes.py
```

### **Paso 2: Entrenar Modelos YOLO**
```bash
# Entrenar los 5 clasificadores independientes
python3 entrenar_yolo_clasificacion.py
```

**Esto tomará un tiempo** (dependiendo de tu GPU/CPU y cantidad de imágenes):
- Con GPU: ~30-60 min por clasificador
- Sin GPU: ~2-4 horas por clasificador

### **Paso 3: Predecir en Nuevas Imágenes**
```bash
# Predecir una imagen individual
python3 predecir_pizza_yolo.py ~/Practicas/test_pizza.jpg

# Predecir todas las imágenes de una carpeta
python3 predecir_pizza_yolo.py ~/Practicas/Descarga_Pizzas/burbujas/si
```

---

## ⚙️ Parámetros de Entrenamiento

En `entrenar_yolo_clasificacion.py`, puedes ajustar:

```python
EPOCHS = 50      # Más épocas = mejor precisión (pero más tiempo)
BATCH = 16       # Ajusta según tu RAM/GPU:
                 # - GPU con 8GB: 32
                 # - GPU con 4GB: 16
                 # - CPU: 8
IMG_SIZE = 640   # Tamaño de imagen (640, 320, 224)
                 # Más grande = mejor precisión, más lento
```

**Recomendación para tu caso:**
```python
# Configuración balanceada
EPOCHS = 100
BATCH = 16
IMG_SIZE = 640

# Configuración rápida (para probar)
EPOCHS = 20
BATCH = 8
IMG_SIZE = 320
```

---

## 📊 Interpretar Resultados

Después del entrenamiento, verás gráficas en `~/Practicas/YOLO_Pizza_Training/runs/<nombre>/`:

- **confusion_matrix.png**: Matriz de confusión (errores del modelo)
- **results.png**: Gráficas de pérdida y precisión
- **val_batch_pred.jpg**: Ejemplos de predicciones

**Métricas importantes:**
- **Top-1 Accuracy**: % de predicciones correctas
- **Top-5 Accuracy**: % de veces que la clase correcta está en el top 5

**Valores buenos:**
- Top-1 > 90% → Excelente
- Top-1 > 80% → Bueno
- Top-1 > 70% → Aceptable
- Top-1 < 70% → Necesita más datos/augmentación

---

## 🔍 Ejemplo de Uso

### Entrenar:
```bash
cd ~/Practicas/Descarga\ de\ archivos
python3 entrenar_yolo_clasificacion.py
```

Salida esperada:
```
==================================================================
ENTRENAMIENTO YOLO PARA CLASIFICACIÓN DE PIZZAS
==================================================================

Este script realizará:
  1. Preparar estructura de datos para YOLO
  2. Entrenar 5 modelos independientes (uno por atributo)
  3. Evaluar modelos en dataset de validación
  4. Exportar modelos a formato ONNX

¿Continuar? (s/n): s

🔧 PASO 1: Preparando datos...

==================================================================
PREPARANDO ESTRUCTURA DE DATOS PARA YOLO
==================================================================

📁 Preparando dataset para: burbujas
  ✓ si: 354 train, 88 val
  ✓ no: 1762 train, 440 val

[... más output ...]

🚀 PASO 2: Entrenando modelos...

==================================================================
ENTRENANDO CLASIFICADOR: BURBUJAS
==================================================================

Ultralytics YOLOv8.0.20 🚀 Python-3.10.12 torch-2.0.1+cu118
Epoch    GPU_mem   train/loss   val/loss   metrics/accuracy_top1
  1/50     0.5G      1.234       0.876      0.654
  2/50     0.5G      0.987       0.743      0.721
  ...
 50/50     0.5G      0.123       0.234      0.943

✅ Entrenamiento completado: burbujas
   Modelo guardado en: ~/Practicas/YOLO_Pizza_Training/runs/burbujas
```

### Predecir:
```bash
python3 predecir_pizza_yolo.py ~/test_pizza.jpg
```

Salida esperada:
```
==================================================================
🍕 ANÁLISIS DE PIZZA: test_pizza.jpg
==================================================================

✅ BURBUJAS        → no              (94.3%)
✅ BORDES          → limpio          (87.1%)
⚠️  DISTRIBUCION   → aceptable       (62.4%)
   Alternativas:
     - correcta       (31.2%)
     - media          (6.4%)
✅ HORNEADO        → correcto        (91.8%)
✅ GRASA           → no              (88.5%)

==================================================================
RESUMEN DE EVALUACIÓN
==================================================================

✅ PIZZA ACEPTABLE (85.2/100)
```

---

## 🎛️ Diferencias con tus Scripts Anteriores

| Aspecto | Scripts Anteriores | YOLOv8 |
|---------|-------------------|--------|
| **Framework** | PyTorch manual | Ultralytics (PyTorch + extras) |
| **Arquitectura** | Definir tú mismo | Preentrenada (ImageNet) |
| **Data Augmentation** | Albumentations manual | Integrado en YOLO |
| **Class Balancing** | WeightedRandomSampler | Integrado (auto-weight) |
| **Complejidad** | Alta (código custom) | Baja (API simple) |
| **Velocidad** | Depende | Optimizado (C++/CUDA) |
| **Export** | Manual | ONNX/TensorRT automático |

---

## 💡 Ventajas de YOLO para tu Caso

1. **Más simple**: No necesitas definir arquitecturas ni loss functions
2. **Preentrenado**: Modelos vienen con conocimiento de ImageNet
3. **Optimizado**: Ultralytics está muy optimizado (más rápido)
4. **Auto-balancing**: YOLO calcula pesos automáticamente
5. **Export fácil**: Un comando para ONNX (producción)
6. **Monitoreo**: TensorBoard integrado para ver entrenamiento

---

## 🚨 Desventajas (pocas)

1. **Multi-label**: YOLO Classification es single-label, por eso necesitas 5 modelos
2. **Tamaño**: 5 modelos ocupan más espacio (~50-200MB total)
3. **Latencia**: Inferencia en 5 modelos es ~5x más lenta que un modelo multi-output

**Alternativa avanzada** (si necesitas velocidad extrema):
- Entrenar 1 modelo YOLOv8 custom con 5 cabezas de clasificación
- Requiere modificar la arquitectura de YOLO (más complejo)

---

## 📚 Recursos Adicionales

- **Documentación oficial**: https://docs.ultralytics.com/tasks/classify/
- **Tutorial de clasificación**: https://docs.ultralytics.com/tasks/classify/#train
- **GitHub Ultralytics**: https://github.com/ultralytics/ultralytics

---

## ❓ FAQ

**Q: ¿Necesito GPU?**
A: No es obligatorio, pero **altamente recomendado**. Sin GPU el entrenamiento será 10-50x más lento.

**Q: ¿Cuánto espacio en disco necesito?**
A: ~2-5 GB para los datasets + ~200-500 MB para modelos entrenados.

**Q: ¿Puedo usar mis scripts anteriores de augmentación?**
A: Sí, pero YOLO ya incluye augmentación automática. Solo úsalos si tienes clases MUY desbalanceadas.

**Q: ¿Cómo uso los modelos en producción?**
A: Exporta a ONNX con `exportar_modelos()`, luego usa ONNX Runtime para inferencia rápida.

**Q: ¿Por qué 5 modelos en vez de 1?**
A: Porque cada atributo es independiente. Para un modelo único multi-output necesitarías modificar YOLOv8 (complejo).

---

## 🎯 Próximos Pasos

1. ✅ Instalar: `pip install ultralytics`
2. ✅ Verificar datos limpios: `python3 verificar_con_csv.py`
3. 🚀 Entrenar: `python3 entrenar_yolo_clasificacion.py`
4. 🔍 Evaluar: Ver gráficas en `~/Practicas/YOLO_Pizza_Training/runs/`
5. 🍕 Probar: `python3 predecir_pizza_yolo.py test.jpg`

**¡Suerte con el entrenamiento!** 🚀
