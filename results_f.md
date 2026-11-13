## Resultados Parte (f): Tamaño de Bloque ($b$) en Entorno Multinodo

Experimento ejecutado sobre la topología óptima de 8 procesos (`2x4`, 4 procesos por nodo en `ventress` y `yodaxico`) para una matriz de $N = 8192$, evaluando cómo interactúa la granularidad del bloque ($b \in \{2048, 512, 128\}$) con la latencia y el ancho de banda de la red entre nodos.

### Tabla de Rendimiento Multinodo según Tamaño de Bloque

| Tamaño de bloque ($b$) | Grilla ($P_r \times P_c$) | Tiempo Cómputo ($T_{\text{comp}}$) | Tiempo Comunicación ($T_{\text{comm}}$) | Tiempo Total ($T_{\text{total}}$) | Rendimiento (GFLOP/s) | Factor Limitante |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2048** | `2x4` | 1.2844 s | 3.6707 s | 7.2898 s | 50.28 | Desbalance de carga y baja concurrencia en 8 procesos |
| **512** | `2x4` | **1.0392 s** | **2.2867 s** | **3.4793 s** | **105.34** | **Equilibrio óptimo entre latencia de red y BLAS-3** |
| **128** | `2x4` | 1.4156 s | 3.0438 s | 4.4880 s | 81.66 | Latencia de mensajes MPI entre nodos y menor caché |

### Interpretación de los Resultados

* **Estabilidad del bloque óptimo ($b_{\text{opt}} = 512$):** Incluso al duplicar los procesos y cruzar la frontera de red entre nodos (`ventress` $\leftrightarrow$ `yodaxico`), $b = 512$ se mantiene como el punto óptimo (`3.4793 s`, `105.34 GFLOP/s`), minimizando tanto $T_{\text{comp}}$ como $T_{\text{comm}}$.
* **Penalización severa en bloques grandes ($b = 2048$):** Con una matriz de $8192 \times 8192$, un bloque de $2048$ genera solo $4 \times 4 = 16$ bloques en total para repartir entre $8$ procesos. Esto provoca un fuerte desbalance de carga en las etapas finales de la factorización (donde varios procesos quedan inactivos) y genera tiempo muerto adicional fuera del cómputo puro (`T_total = 7.2898 s`), reduciendo el rendimiento a menos de la mitad (`50.28 GFLOP/s`).
* **Impacto de la latencia de red en bloques pequeños ($b = 128$):** Al aumentar el número de iteraciones de $16$ (para $b=512$) a $64$ (para $b=128$), se cuadruplica la frecuencia de llamadas `MPI_Bcast` que deben atravesar la interfaz de red entre nodos, elevando $T_{\text{comm}}$ de `2.2867 s` a `3.0438 s` y degradando el rendimiento en un `22.5%`.
