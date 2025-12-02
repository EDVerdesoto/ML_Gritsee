# 📁 Estructura del Proyecto ML_Gritsee

```
ML_Gritsee/
│
├── 📂 scripts/                    # Scripts de procesamiento y entrenamiento
│   ├── auto_crop.py              # Recorte automático con anti-letterbox
│   ├── check_labels.py           # Verificación de etiquetas
│   ├── split_data.py             # División train/val/test
│   └── visualizar_prediccion.py  # Herramienta de debug visual
│
├── 📂 modelos/                    # Modelos pre-entrenados y entrenados
│   ├── yolo11n.pt                # YOLO 11 nano
│   ├── yolov8n.pt                # YOLO v8 nano
│   └── runs/                     # Modelos entrenados
│       └── detect/
│           └── modelo_pizza_v1/
│               └── weights/
│                   └── best.pt
│
├── 📂 datasets/                   # Todos los datasets del proyecto
│   ├── Descarga_Pizzas/          # Dataset raw descargado
│   │   └── Classification_ResNet_640/
│   ├── Dataset_Stage2_Crops_HighQuality/  # Crops procesados
│   ├── Img_entrenamiento/        # Imágenes procesadas para entrenamiento
│   │   └── Detection_Unique_640/
│   └── dataset_yolo_final/       # Dataset YOLO para entrenamiento
│       ├── train/
│       │   ├── images/
│       │   └── labels/
│       └── val/
│           ├── images/
│           └── labels/
│
├── 📂 procesamiento/              # Scripts de ETL y descarga
│   ├── Archivos/                 # Backups y CSV
│   ├── Augmentar/                # Scripts de data augmentation
│   ├── Descarga y limpieza/      # ETL y limpieza de datos
│   │   ├── descarga_archivos.py
│   │   ├── etl_pizzas.py
│   │   ├── limpiar_duplicados.py
│   │   └── verificar_con_csv.py
│   └── ScriptsEntrenamiento/
│       ├── entrenar_yolo_clasificacion.py
│       └── predecir_pizza_yolo.py
│
├── 📂 resultados/                 # Resultados de experimentos (vacío por ahora)
│
├── data.yaml                      # Configuración del dataset YOLO
├── README.md                      # Documentación principal
└── .gitignore                     # Archivos ignorados por git

```

## 🎯 Cambios Realizados

1. ✅ Scripts organizados en `scripts/`
2. ✅ Modelos centralizados en `modelos/`
3. ✅ Datasets agrupados en `datasets/`
4. ✅ Carpeta `procesamiento/` renombrada (sin espacios)
5. ✅ Rutas actualizadas en todos los scripts
6. ✅ Carpeta `resultados/` lista para experimentos futuros

## 📝 Rutas Actualizadas

- **Modelo entrenado**: `modelos/runs/detect/modelo_pizza_v1/weights/best.pt`
- **Dataset de entrada**: `datasets/Descarga_Pizzas/Classification_ResNet_640/`
- **Dataset procesado**: `datasets/Dataset_Stage2_Crops_HighQuality/`
- **Dataset YOLO**: `datasets/dataset_yolo_final/`
