## Resultados Parte (e): Impacto de la Geometría de la Grilla ($P_r \times P_c$)

Experimento ejecutado manteniendo constantes el tamaño de la matriz ($N = 8192$), el tamaño de bloque ($b_{\text{opt}} = 512$) y el número total de procesos ($P = 8$, repartidos como 4 procesos por nodo), variando únicamente la relación de aspecto de la grilla bidimensional $P_r \times P_c$.

### Tabla Comparativa de Topologías para $P = 8$

| Grilla ($P_r \times P_c$) | Geometría | Tiempo Cómputo ($T_{\text{comp}}$) | Tiempo Comunicación ($T_{\text{comm}}$) | Tiempo Total ($T_{\text{total}}$) | Rendimiento (GFLOP/s) | Observación |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **`1x8`** | Unidimensional (solo columnas) | 0.7275 s | 6.7290 s | 7.5452 s | 48.57 | Cuello de botella severo en broadcasts horizontales |
| **`2x4`** | **Rectangular balanceada ($P_r < P_c$)** | **1.2273 s** | **2.2104 s** | **3.6035 s** | **101.71** | **Mejor topología; minimiza el volumen de comunicación** |
| **`4x2`** | Rectangular vertical ($P_r > P_c$) | 1.2141 s | 3.4560 s | 4.8211 s | 76.02 | Mayor costo en factorización de panel y broadcast vertical |
| **`8x1`** | Unidimensional (solo filas) | 0.7965 s | 7.1784 s | 8.0559 s | 45.50 | Peor rendimiento; alta contención en comunicaciones verticales |

### Interpretación de los Resultados

* **Superioridad de las grillas 2D frente a 1D:** Las configuraciones bidimensionales (`2x4` y `4x2`) superan ampliamente a las unidimensionales (`1x8` y `8x1`), reduciendo el tiempo de comunicación en más de **3 veces** (`2.21 s` vs. `6.73 s - 7.18 s`). En una grilla 2D, cada mensaje de broadcast se restringe a subcomunicadores de fila o columna de tamaño $P_c$ o $P_r$, en lugar de involucrar a los $P = 8$ procesos simultáneamente.
* **Ventaja de $P_r < P_c$ (`2x4` vs. `4x2`):** La grilla `2x4` logra `101.71 GFLOP/s` frente a `76.02 GFLOP/s` de `4x2` (+33.8% más rápida). En la factorización LU por bloques, la factorización del panel vertical (ruta crítica secuencial por columna) se distribuye entre menos filas ($P_r = 2$), reduciendo la sincronización vertical antes de difundir los factores hacia la submatriz restante.
