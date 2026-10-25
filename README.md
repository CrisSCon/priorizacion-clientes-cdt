# Priorización de clientes para campañas de depósitos

Proyecto académico de despliegue de soluciones analíticas.

## Objetivo
Explorar los datos de Bank Marketing y desarrollar un modelo
de clasificación para apoyar la priorización de clientes.

## Dataset
Fuente oficial: https://archive.ics.uci.edu/dataset/222/bank+marketing

## Tecnologías
- Python
- Pandas
- Matplotlib
- Scikit-learn
- Git
- DVC

## Reproducir la exploración

Desde la raíz del repositorio, con Python 3.13 y un entorno virtual activo:

```bash
python -m pip install -r requirements.txt
dvc pull
jupyter notebook notebooks/01_eda_bank_marketing.ipynb
```

El remoto DVC es Google Drive y puede requerir acceso y autenticación. Si el CSV no está disponible, el notebook descarga la fuente pública UCI y exige que su MD5 y tamaño coincidan con `data/bank-full.csv.dvc`. No se analiza una versión distinta silenciosamente. En Colab, clonar primero el repositorio y establecer su carpeta como directorio de trabajo.

Reiniciar el kernel y ejecutar todas las celdas. Se comprueban integridad, dimensiones, nulos, categorías unknown, distribución objetivo y duplicados. Las figuras 1 a 4 del informe se exportan a `docs/figuras/`. `duration` se explora históricamente, pero no se usará como predictor antes de la llamada.
