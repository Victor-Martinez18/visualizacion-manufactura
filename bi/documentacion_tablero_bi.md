# Documentación del tablero de BI: Cumplimiento del programa de producción

| Campo | Valor |
|---|---|
| Herramienta | Power BI Desktop |
| Archivo | `bi/tablero_cumplimiento_programa.pbix` |
| Fuente de datos | `data/processed/ordenes_para_bi.csv` (generado en la sección 5 del notebook) |
| Periodo | 18 al 25 de marzo de 2023 · 1,000 órdenes de trabajo |
| Audiencia | Supervisores de producción y gerencia de operaciones (monitoreo recurrente) |
| Capturas | `docs/capturas/bi_vista_general.png`, `docs/capturas/bi_filtro_rectificado.png`, `docs/capturas/bi_seleccion_M02.png` |

## 1. Conexión y preparación de datos

El tablero se conecta directamente al CSV preparado por el notebook. En Power BI **no se aplican transformaciones adicionales**: toda la limpieza está en código (notebook, sección 2), por lo que si cambian los datos basta con volver a ejecutar el notebook y actualizar el tablero (**Inicio → Actualizar**).

Tipos de columna asignados en Power Query:

| Columna | Tipo |
|---|---|
| Orden, Maquina, Operacion, Estado, Rango_disponibilidad, Categoria_eficiencia | Texto |
| Fecha | Fecha |
| Hora, Incumplimiento, Tiempo_proceso_min, Disponibilidad_pct | Número entero |
| Retraso_inicio_min, Energia | Número decimal |

Codificación del archivo: UTF-8 (65001). **Configuración regional para importación: Inglés (Estados Unidos)** (Archivo → Opciones → Archivo actual → Configuración regional). Las columnas `Retraso_inicio_min` y `Energia` se convierten a número decimal con esa configuración regional; con la configuración en español, el punto decimal se interpreta como separador de miles (por ejemplo, 5.0 se leería como 50 y el retraso promedio daría 44.7 en lugar de 4.5).

## 2. Medidas DAX

```DAX
Total ordenes = COUNTROWS ( ordenes_para_bi )

% Completadas =
DIVIDE ( CALCULATE ( [Total ordenes], ordenes_para_bi[Estado] = "Completada" ), [Total ordenes] )

% Retrasadas =
DIVIDE ( CALCULATE ( [Total ordenes], ordenes_para_bi[Estado] = "Retrasada" ), [Total ordenes] )

% Fallidas =
DIVIDE ( CALCULATE ( [Total ordenes], ordenes_para_bi[Estado] = "Fallida" ), [Total ordenes] )

% Incumplimiento = AVERAGE ( ordenes_para_bi[Incumplimiento] )

Retraso promedio (min) = AVERAGE ( ordenes_para_bi[Retraso_inicio_min] )

Horas programadas = DIVIDE ( SUM ( ordenes_para_bi[Tiempo_proceso_min] ), 60 )

Total ordenes (texto) = FORMAT ( [Total ordenes], "#,0" )
```

| Medida | Definición | Formato |
|---|---|---|
| Total ordenes | Número de órdenes en el contexto de filtro activo | Entero |
| % Completadas / Retrasadas / Fallidas | Proporción de órdenes en cada estado | Porcentaje, 1 decimal |
| % Incumplimiento | Retrasadas + fallidas | Porcentaje, 1 decimal |
| Retraso promedio (min) | Promedio del retraso en el inicio; solo órdenes ejecutadas (AVERAGE ignora los vacíos de las fallidas) | Decimal, 1 decimal |
| Horas programadas | Suma del tiempo de proceso en horas | Decimal, 1 decimal |
| Total ordenes (texto) | Total ordenes con separador de miles; se usa en la tarjeta KPI porque el objeto *Tarjeta* abrevia automáticamente a "1 mil" | Texto |

## 3. Diseño de la página "Cumplimiento del programa"

```
┌──────────────────────────────────────────────────────────────────────┐
│ Título: Cumplimiento del programa de producción · 18–25 mar 2023     │
│ [Segmentador Operación ▼]  [Segmentador Máquina]  [Segmentador Fecha]│
├───────────┬───────────┬───────────┬───────────┬──────────────────────┤
│ Total     │ % Complet.│ % Retras. │ % Fallidas│ Retraso promedio     │
│ órdenes   │           │           │           │ (min)                │
├───────────┴───────────┴───────┬───┴───────────┴──────────────────────┤
│ Barras 100 % apiladas:        │ Líneas: % Retrasadas y % Fallidas    │
│ Máquina × Estado              │ por Fecha                            │
├───────────────────────────────┴──────────────────────────────────────┤
│ Matriz (mapa de calor): Máquina × Operación, % Incumplimiento        │
│ Fuente: ziya07 (s.f.), Kaggle · Datos: ordenes_para_bi.csv           │
└──────────────────────────────────────────────────────────────────────┘
```

| Objeto | Configuración | Pregunta que responde |
|---|---|---|
| Tarjetas KPI (5) | Total ordenes (texto), % Completadas, % Retrasadas, % Fallidas, Retraso promedio (min) | ¿Cuál es el nivel general de cumplimiento? |
| Segmentadores (3) | Operación (lista desplegable), Máquina (mosaico), Fecha (rango) | Filtran de forma coordinada todos los objetos de la página |
| Barras 100 % apiladas | Eje Y: Maquina · Valores: Total ordenes · Leyenda: Estado · Orden: % Incumplimiento descendente | ¿Qué máquinas tienen más retrasos y fallas? |
| Gráfico de líneas | Eje X: Fecha (categoría) · Valores: % Retrasadas, % Fallidas · Eje Y desde 0 % | ¿Cómo cambia el incumplimiento en la semana? |
| Matriz con formato condicional | Filas: Maquina · Columnas: Operacion · Valores: % Incumplimiento · Color de fondo de #FFFFFF a #C2410C | ¿Qué combinaciones de máquina y operación concentran el incumplimiento? |

Formato adicional: líneas con interpolación lineal (sin suavizado) y eje Y desde 0 %; etiquetas de datos activadas en las barras.

**Paleta**, la misma del notebook y de Plotly: Completada `#3A6EA5`, Retrasada `#E09A2B`, Fallida `#B8322A`.

## 4. Tooltip personalizado

Página **"Tooltip máquina"** configurada como información sobre herramientas, asignada al gráfico de barras. Contiene el nombre de la máquina, tarjetas con Total ordenes, Retraso promedio (min) y Horas programadas, y una tabla Estado × Total ordenes. Respeta los filtros activos de la página principal y el segmento señalado: sobre la parte naranja de una barra muestra solo las órdenes retrasadas de esa máquina.

## 5. Validación

Valores del tablero comparados con los del notebook (sección 3):

| Vista | Indicador | Valor esperado |
|---|---|---|
| Sin filtros | Total ordenes | 1,000 |
| Sin filtros | % Completadas / Retrasadas / Fallidas | 67.3 % / 19.8 % / 12.9 % |
| Sin filtros | Retraso promedio (min) | 4.5 |
| Operación = Rectificado | Total ordenes | 208 |
| Operación = Rectificado | % Completadas / Retrasadas / Fallidas | 65.9 % / 22.1 % / 12.0 % |
| Operación = Rectificado | % Incumplimiento de M03 (matriz) | 47.2 % |
| Rectificado · tooltip M01 · Retrasada | Total ordenes / Horas programadas / Retraso promedio | 11 / 14.7 / 18.6 min |
| Selección de M02 en la matriz | Total ordenes / % Completadas | 210 / 69.5 % |

Las capturas de `docs/capturas/` corresponden a estas vistas.
