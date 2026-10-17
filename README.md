# Cumplimiento del programa de producción

Proyecto de visualización de datos de la maestría (Unidades 1 a 4). Analiza **1,000 órdenes de trabajo** de un sistema de manufactura híbrida para responder:

> ¿Qué máquinas y tipos de operación concentran los retrasos y las fallas de las órdenes de trabajo, y cómo se relacionan estos incumplimientos con la disponibilidad de la máquina, el tiempo de proceso y el consumo de energía?

**Audiencia:** planeadores y supervisores de producción, jefes de mantenimiento y gerencia de operaciones.

---

## Estructura del proyecto

```
proyecto_visualizacion_manufactura/
├── README.md                         ← este archivo
├── requirements.txt                  ← bibliotecas de Python necesarias
├── data/
│   ├── raw/
│   │   └── hybrid_manufacturing_raw.csv       ← datos originales de Kaggle (NO se modifican)
│   └── processed/
│       ├── hybrid_manufacturing_clean.csv     ← datos limpios + variables derivadas
│       └── ordenes_para_bi.csv                ← datos para Power BI / Tableau
├── notebooks/
│   └── avance3_visualizacion_manufactura.ipynb   ← flujo completo: carga → limpieza → EDA → visualizaciones finales → BI
├── src/
│   └── eda_avance2.py                ← regenera las 6 figuras exploratorias del Avance 2
├── outputs/
│   ├── figures/
│   │   ├── avance2/f1.png … f6.png
│   │   └── fig_estatica_retrasos_por_dia.png  ← visualización estática final
│   └── interactive/
│       └── interactiva_estado_por_maquina.html ← visualización interactiva (abrir en el navegador)
├── bi/
│   ├── guia_power_bi.md              ← pasos, medidas DAX y diseño del tablero
│   └── tablero_cumplimiento_programa.pbix  ← (agregar) archivo de Power BI
└── docs/
    └── capturas/                     ← (agregar) capturas del tablero de BI
```

## Cómo reproducir los resultados

1. Instala Python 3.10 o superior.
2. Desde la carpeta del proyecto, instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Abre `notebooks/avance3_visualizacion_manufactura.ipynb` en Jupyter o VS Code y ejecuta **Run All**. El notebook:
   - lee `data/raw/hybrid_manufacturing_raw.csv`,
   - genera los dos archivos de `data/processed/`,
   - crea la visualización estática (PNG) y la interactiva (HTML) en `outputs/`,
   - valida al final que las cifras clave coincidan con el reporte.
4. (Opcional) Regenera las figuras del Avance 2:
   ```
   python src/eda_avance2.py
   ```
5. Para el tablero de BI, sigue `bi/guia_power_bi.md`.

Todas las rutas son relativas, así que el proyecto funciona en cualquier computadora sin cambiar el código.

## Fuente de datos

| Campo | Valor |
|---|---|
| Dataset | Manufacturing Production Data (archivo `hybrid_manufacturing_categorical.csv`) |
| Autor / plataforma | ziya07 · Kaggle |
| Enlace | https://www.kaggle.com/datasets/ziya07/manufacturing-production-data |
| Fecha de descarga | octubre de 2026 |
| Periodo | 18 al 25 de marzo de 2023 |
| Tamaño | 1,000 filas × 13 columnas |
| Unidades | tiempo en minutos; disponibilidad en %; energía y material sin unidad declarada (se suponen kWh y kg) |
| Limitaciones | probablemente datos simulados; una semana de datos; sin operadores, turnos ni causas de falla |

## Transformaciones (todas en el notebook, sección 2)

| # | Transformación |
|---|---|
| T1 | Fechas y horas convertidas a `datetime` |
| T2 | Vacíos en `Actual_Start` y `Actual_End` conservados: corresponden exactamente a las 129 órdenes fallidas (se valida con `assert`) |
| T3 | `Retraso_inicio_min` = `Actual_Start` − `Scheduled_Start` |
| T4 | `Incumplimiento` = 1 si la orden está retrasada o fallida |
| T5 | `Fecha` y `Hora` a partir de `Scheduled_Start` |
| T6 | `Estado` y `Operacion` traducidos al español (se conservan las columnas originales) |
| T7 | `Rango_disponibilidad` en 4 rangos |

No se elimina ninguna fila.

## Convenciones visuales

- Mismos colores en todas las herramientas: Completada `#3A6EA5`, Retrasada `#E09A2B`, Fallida `#B8322A`. Se verificó que son distinguibles para personas con daltonismo.
- Ejes de porcentaje desde 0 %, tamaño de muestra (n) visible y fuente en cada gráfica.

## Autor

[Nombre del estudiante] · [Maestría / Institución] · 2026
