# Guía para construir el tablero en Power BI Desktop

**Archivo de datos:** `data/processed/ordenes_para_bi.csv` (se genera en la sección 5 del notebook)
**Nombre sugerido del archivo de Power BI:** `bi/tablero_cumplimiento_programa.pbix`

El tablero responde la misma pregunta analítica del proyecto con funciones propias de BI: **tarjetas KPI, segmentadores (filtros), formato condicional y un tooltip personalizado**.

---

## 1. Cargar los datos

1. Abre Power BI Desktop y elige **Inicio → Obtener datos → Texto/CSV**.
2. Selecciona `ordenes_para_bi.csv`.
3. En la ventana de vista previa, verifica que **Origen del archivo** sea `65001: Unicode (UTF-8)` para que se vean bien los acentos.
4. Haz clic en **Transformar datos** y revisa los tipos de cada columna:

| Columna | Tipo en Power BI |
|---|---|
| Orden, Maquina, Operacion, Estado, Rango_disponibilidad, Categoria_eficiencia | Texto |
| Fecha | Fecha |
| Hora, Incumplimiento, Tiempo_proceso_min, Disponibilidad_pct | Número entero |
| Retraso_inicio_min, Energia | Número decimal |

> Si los decimales aparecen mal (por ejemplo, 8.56 se lee como 856), en Power Query elige la columna y usa **Cambiar tipo → Usar configuración regional → Número decimal → Inglés (Estados Unidos)**.

5. Haz clic en **Cerrar y aplicar**. No se hace ninguna otra transformación en Power BI: toda la limpieza está documentada en el notebook.

---

## 2. Crear las medidas (DAX)

En el panel **Datos**, haz clic derecho sobre la tabla `ordenes_para_bi` → **Nueva medida** y crea una por una:

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
```

Da formato de **porcentaje con 1 decimal** a las medidas que empiezan con %, y de **número con 1 decimal** a las otras dos.

*Definiciones:* el retraso promedio solo considera órdenes ejecutadas, porque las fallidas no tienen inicio real (AVERAGE ignora los vacíos). El incumplimiento incluye retrasadas y fallidas.

---

## 3. Armar la página "Cumplimiento del programa"

Usa un lienzo de 16:9 con fondo blanco. Distribución sugerida:

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

**a) Tarjetas KPI (5 objetos "Tarjeta"):** `Total ordenes`, `% Completadas`, `% Retrasadas`, `% Fallidas` y `Retraso promedio (min)`.

**b) Segmentadores (3 objetos "Segmentación de datos"):**
- `Operacion` con estilo **Lista desplegable**.
- `Maquina` con estilo **Mosaico** (botones M01 a M05).
- `Fecha` con estilo **Entre** (rango de fechas).

**c) Gráfico de barras 100 % apiladas horizontal:**
- Eje Y: `Maquina` · Eje X: `Total ordenes` · Leyenda: `Estado`.
- Colores (Formato → Columnas): Completada `#3A6EA5`, Retrasada `#E09A2B` y Fallida `#B8322A`. Son los mismos colores del notebook, para mantener la consistencia (teoría 3.4.11).
- Activa **Etiquetas de datos**.
- Ordena las máquinas por `% Incumplimiento` de forma descendente.

**d) Gráfico de líneas:**
- Eje X: `Fecha` (tipo **Categoría**, no jerarquía de fechas) · Eje Y: `% Retrasadas` y `% Fallidas`.
- Colores: naranja y rojo, como en el punto anterior. El eje Y debe iniciar en 0 %.

**e) Matriz como mapa de calor:**
- Filas: `Maquina` · Columnas: `Operacion` · Valores: `% Incumplimiento`.
- Formato → **Elementos de celda → Color de fondo → activado**, con escala de **blanco a naranja oscuro** (`#FFFFFF` a `#C2410C`), igual que la Figura 3 del Avance 2.

---

## 4. Tooltip personalizado

1. Crea una página nueva llamada **Tooltip máquina**.
2. En **Formato de página → Información de página**, activa **Permitir uso como información sobre herramientas**. En **Configuración de lienzo**, elige el tipo **Información sobre herramientas**.
3. Agrega 3 tarjetas: `Total ordenes`, `Retraso promedio (min)` y `Horas programadas`, más una tabla pequeña con `Estado` y `Total ordenes`.
4. Regresa a la página principal, selecciona el gráfico de barras y, en **Formato → Información sobre herramientas**, elige **Tipo: Página de informe** y **Página: Tooltip máquina**.

Al pasar el cursor sobre la barra de una máquina, aparece un resumen de esa máquina que respeta los filtros activos.

---

## 5. Capturas para el documento

Toma 2 capturas (tecla **Windows + Shift + S**):

1. **Vista general:** el tablero completo, sin filtros.
2. **Vista filtrada:** con `Operacion = Rectificado` seleccionado y el cursor sobre la barra de M03, para que se vea el tooltip personalizado.

Guárdalas en `docs/capturas/` como `bi_vista_general.png` y `bi_filtro_rectificado.png`, e insértalas en el documento en las Figuras 7 y 8.

**Valores para verificar (sin filtros):** 1,000 órdenes · 67.3 % completadas · 19.8 % retrasadas · 12.9 % fallidas · retraso promedio 4.5 min.
**Con filtro Rectificado:** 208 órdenes. En M03 el incumplimiento debe ser 47.2 %.

---

## Alternativa: Tableau Public

Si prefieres Tableau Public, porque genera un enlace público, los equivalentes son:

| Power BI | Tableau |
|---|---|
| Medidas DAX | Campos calculados, por ejemplo `SUM([Incumplimiento]) / COUNT([Orden])` |
| Segmentadores | Filtros mostrados en el tablero (*Show Filter*) |
| Tarjetas KPI | Hojas con un solo número (*Text*) |
| Tooltip personalizado | *Viz in Tooltip* |
| Formato condicional | Color continuo en la marca *Square* |

Publica con **File → Save to Tableau Public** y copia el enlace en el documento.
