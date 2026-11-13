## Resultados Parte (c): Análisis de Tamaño de Bloque ($b$)

Experimento ejecutado para una matriz de tamaño $N = 8192$ sobre una grilla de procesos $P_r \times P_c = 2 \times 2$ ($P = 4$ procesos MPI) en el clúster Kraken (partición `hpc-iic3533`, límite de 4096 MB de RAM por nodo).

### Tabla de Rendimiento y Tiempos

| Tamaño de bloque ($b$) | Tiempo Cómputo ($T_{\text{comp}}$) | Tiempo Comunicación ($T_{\text{comm}}$) | Tiempo Total ($T_{\text{total}}$) | Rendimiento (GFLOP/s) | Observación |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **8192** | — | — | OOM Killed | — | El 100% de la matriz recae en `rank 0`, superando los 4 GB/nodo |
| **4096** | 4.7042 s | 1.2054 s | 16.3851 s | 22.37 | Alto desbalance de carga y latencia por mensajes masivos |
| **2048** | 2.8455 s | 1.5115 s | 5.9798 s | 61.29 | Mejora el reparto, pero pocos bloques activos por iteración |
| **1024** | 2.4226 s | 0.8184 s | 3.5529 s | 103.16 | Alto aprovechamiento de BLAS-3 y buena distribución |
| **512** | **2.4230 s** | **1.0186 s** | **3.5326 s** | **103.75** | **Tamaño de bloque óptimo ($b_{\text{opt}}$)** |
| **256** | 2.6469 s | 1.4850 s | 4.1588 s | 88.13 | Aumenta la sobrecarga de comunicación MPI (`T_comm`) |
| **128** | 3.2987 s | 2.3568 s | 5.6740 s | 64.59 | Granularidad fina; mayor cantidad de broadcasts y menor eficiencia de caché |
| **64** | 6.5379 s | 5.1950 s | 11.7482 s | 31.20 | Dominado por la latencia de mensajes MPI y llamadas pequeñas a BLAS |

### Interpretación de los Resultados

* **Bloque óptimo ($b_{\text{opt}} = 512$):** Logra el menor tiempo total de ejecución (`3.5326 s`) y el máximo rendimiento (`103.75 GFLOP/s`), equilibrando la eficiencia de operaciones matriciales locales (BLAS-3) con el costo de comunicación por iteración.
* **Bloques muy pequeños ($b \le 256$):** Incrementan el número total de iteraciones ($N/b$) y de mensajes `MPI_Bcast`, haciendo que la latencia de red y la pérdida de localidad de caché degraden el rendimiento.
* **Bloques muy grandes ($b \ge 2048$):** Reducen el paralelismo efectivo en la distribución *2D block-cyclic*. Para $b = 4096$ solo participan bloques grandes con fuerte desbalance de carga, y para $b = 8192$ ($b = N$) la matriz completa se asigna exclusivamente al proceso `rank 0`, provocando un error *Out Of Memory (OOM)* al exceder los 4 GB disponibles en el nodo.
