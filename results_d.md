## Resultados Parte (d): Análisis de Escalabilidad Fuerte ($P$)

Experimento ejecutado fijando el tamaño de matriz en $N = 8192$ y el tamaño de bloque óptimo en $b_{\text{opt}} = 512$, escalando el número total de procesos MPI desde $P = 1$ hasta $P = 16$ distribuidos en 2 nodos del clúster Kraken (`ventress` y `yodaxico`).

### Tabla de Rendimiento, Speedup y Eficiencia

| Procesos ($P$) | Grilla ($P_r \times P_c$) | Tiempo Cómputo ($T_{\text{comp}}$) | Tiempo Comunicación ($T_{\text{comm}}$) | Tiempo Total ($T_{\text{total}}$) | Rendimiento (GFLOP/s) | Speedup ($S_P$) | Eficiencia Paralela ($E_P$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `1x1` | 12.7250 s | 0.1121 s | 12.8652 s | 28.49 | 1.00x | 100.0% |
| **2** | `1x2` | 3.9689 s | 5.2657 s | 9.2845 s | 39.47 | 1.39x | 69.3% |
| **4** | `2x2` | 1.7745 s | 2.3395 s | 4.2235 s | 86.78 | 3.05x | 76.2% |
| **8** | `2x4` | **0.5784 s** | **2.2640 s** | **2.9682 s** | **123.48** | **4.33x** | **54.2%** |
| **16** | `4x4` | 0.5504 s | 2.5592 s | 3.4402 s | 106.54 | 3.74x | 23.4% |

### Interpretación de los Resultados

* **Punto óptimo de escalabilidad ($P = 8$, grilla `2x4`):** Se alcanza el tiempo mínimo de ejecución (`2.9682 s`) y el máximo rendimiento (`123.48 GFLOP/s`), logrando un speedup de **4.33x** respecto a la ejecución secuencial (`1x1`).
* **Salto entre $P = 1$ y $P = 2$:** Al pasar a 2 procesos distribuidos entre nodos (`--map-by ppr:1:node`), aparece por primera vez la comunicación de red (`T_comm` sube de `0.1121 s` a `5.2657 s`), lo que limita la eficiencia inicial al `69.3%`, aunque la eficiencia repunta al `76.2%` en `2x2` gracias al reparto bidimensional más equilibrado.
* **Saturación en $P = 16$ (grilla `4x4`):** Al duplicar de 8 a 16 procesos, el tiempo de cómputo apenas se reduce en `0.028 s` (de `0.5784 s` a `0.5504 s`), mientras que la comunicación multinodo aumenta a `2.5592 s` (representando el **74.4%** del tiempo total). El sistema entra en régimen limitado por latencia y ancho de banda de red (*communication-bound*), reduciendo el rendimiento a `106.54 GFLOP/s`.
