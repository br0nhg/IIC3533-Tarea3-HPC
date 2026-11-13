# T3 — Pendientes para el equipo antes de cerrar el informe

> **Actualización:** los bugs (sección 1), la verificación (sección 2), los scripts SLURM (secciones 3 y 4) y los datos de hardware (sección 5) ya están resueltos en el código y en `slurm/`. **Para correr, seguir [INSTRUCCIONES.md](INSTRUCCIONES.md).** Este archivo queda como registro de lo que estaba mal en la primera versión.

Revisé el código, los scripts SLURM y las salidas de `kraken_export/`. Hay **dos bugs que invalidan los resultados distribuidos** y varias corridas que pide el enunciado y no están. El informe (`informe/informe.tex`) ya tiene toda la estructura y el análisis; donde faltan datos aparecen marcas rojas `[...]`.

Entrega: **lunes 16 de noviembre, 23:59**. Prioridad: 1 → 2 → 3 → 4.

---

## 1. Bugs en el código (arreglar antes de volver a correr)

### 1.1 `lu_distributed.py`: la actualización ignora los paneles recibidos (CRÍTICO)

En el paso 3 (líneas 126–140) se hacen los `Bcast` de `buf_U` y `buf_L`, pero esos buffers **se descartan**: se sobrescriben en cada vuelta del `for` y nunca se usan. En el paso 4 (líneas 144–152) se actualiza solo si `mycol == c_k` **y** `myrow == r_k`, es decir, **solo el proceso dueño de A_kk actualiza sus bloques**. El resto nunca actualiza.

Consecuencias:
- Con p > 1 la factorización es **incorrecta**.
- `T_comp` sale muy subestimado y el speedup/GFLOP/s, inflados. Ejemplo: en 2×2 con b=512, el rank 0 midió T_comp = 1.77 s ≈ 12.7/8 s, que calza con que solo actualiza en la mitad de los pasos (en un grid cuadrado, el dueño de A_kk siempre está en la diagonal del grid: los ranks (0,1) y (1,0) **nunca** actualizan).

Arreglo sugerido (es además lo que pide el enunciado: "la actualización es una sola multiplicación"):
- Los procesos de la fila `r_k` arman su panel U (todas sus columnas de bloque J > k, contiguas en el arreglo local) en un arreglo `b × (nJ·b)`; un **solo** `col_comm.Bcast(panel_U, root=r_k)`.
- Los procesos de la columna `c_k` arman su panel L (todas sus filas de bloque I > k) en un arreglo `(nI·b) × b`; un **solo** `row_comm.Bcast(panel_L, root=c_k)`.
- Todos los procesos actualizan: `A_local[i0:, j0:] -= panel_L @ panel_U`, donde `i0`/`j0` es el primer índice local con bloque global > k.

### 1.2 `lu_serial.py` y `lu_distributed.py`: panel L mal calculado

`solve_triangular(U_kk, A_ik.T, lower=False).T` resuelve `U X = A_ikᵀ`, o sea calcula `A_ik U⁻ᵀ`, no `A_ik U⁻¹`. Lo correcto es resolver `Uᵀ X = A_ikᵀ`:

```
scipy.linalg.solve_triangular(U_kk, A_ik.T, lower=False, trans='T').T
```

(línea 38 de `lu_serial.py` y línea 122 de `lu_distributed.py`). No cambia el número de FLOP, así que los tiempos de la parte (a) deberían cambiar poco, pero la factorización hoy está mal también en serial.

### 1.3 Otros detalles del código
- **Tiempos por proceso**: hoy solo imprime el rank 0, y el enunciado pide los tiempos de *cada* proceso (partes b y f). Hacer `comm.gather((t_comp, t_comm, t_total))` e imprimir una línea por rank (o min/máx/promedio).
- **Pivoteo**: `lu_factor` devuelve `piv` y se descarta. Verificar que `piv == arange(b)` (con esta matriz debería cumplirse siempre, pero hay que comprobarlo y decirlo en el informe).
- **`run_experimento_a.py`** no fija `OMP_NUM_THREADS=1`; el enunciado pide un thread. Confirmar o repetir con `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`.

## 2. Verificación de correctitud (parte b, no está hecha)

Con N=2048, b=128 en el PC, grids 1×1, 1×2, 2×1 y 2×2:
1. Juntar los arreglos locales en el rank 0 (`comm.gather`) y reconstruir la matriz global deshaciendo la distribución bloque-cíclica.
2. Comparar contra `lu_serial.py` (misma semilla): `max |A_dist − A_serial|`.
3. Residuo: extraer L (tril con 1 en la diagonal) y U (triu), calcular `‖A − LU‖_F / ‖A‖_F` con la A original.

Pasarme los dos números por grid (tabla 3 del informe).

## 3. Corridas que faltan en el cluster (todas con el código corregido)

N = 8192 en todas. b_a = 128 (parte a), b_c = el óptimo que salga de la parte (c) repetida (hoy 512).
Idealmente **3 repeticiones** por configuración (reporto la mediana): la misma config 2×4/2 nodos/b=512 dio 2.97, 3.60 y 3.48 s.

| Parte | Configuración | Grids y T | Nodos | `--ntasks-per-node` | b |
|---|---|---|---|---|---|
| (a) | PC, 1 thread | 1×1 | – | – | 4096…64 (si cambia algo tras el fix 1.2) |
| (c) | Config 2 | 2×2, T=2 | 1 | 4 | 4096, 2048, 1024, 512, 256, 128, 64 |
| (d) | Config 0 | 1×1, T=1,2,4,8 | 1 | 1 | b_a y b_c |
| (d) | Config 1 | 1×2 y 2×1, T=1,2,4 | 1 | 2 | b_a y b_c |
| (d) | Config 2 | 2×2, T=1,2 | 1 | 4 | b_a y b_c |
| (d) | Config 3 | 2×4 y 4×2, T=1 | 1 | 8 | b_a y b_c |
| (e) | Config 4 | 2×4, T=1 | 2 | 4 | b_a y b_c |
| (e) | Config 5 | 4×4, T=1 | 2 | 8 | b_a y b_c |
| (f) | 2×2 | b=4096 y b=512, misma config para ambos (p. ej. 1 nodo, T=2) | 1 | 4 | 4096, 512 |

Notas:
- **Config 1, 2 y 3 son en UN nodo.** En `run_parte_d.slurm`, 1×2 y 2×2 se corrieron con `--map-by ppr:1:node`/`ppr:2:node` (repartidos en 2 nodos) y 2×4 con `ppr:4:node` (eso es la config 4, no la 3). La config 3 nunca se corrió, y es justo la comparación central de la parte (e).
- `--cpus-per-task=T` y `--ntasks-per-node` deben coincidir con la tabla del enunciado; procesos × T ≤ 8 por nodo (cuidado con oversubscription).
- Para config 0–3 con distintos T conviene un job por T (porque `--cpus-per-task` es del job).
- Para (e), confirmar qué ranks quedan en qué nodo: `mpirun --report-bindings` o imprimir `MPI.Get_processor_name()` por rank.
- Para (f), b = 8192 (= N) se cae por memoria en 1 nodo; no lo pide la (f), pero en la (c) dejar anotado el OOM.
- Para (c) con b=4096: en 1 nodo también se cayó por memoria. Si vuelve a pasar con el código corregido, avisar (se puede bajar memoria evitando copias de `A_full` en el rank 0).

## 4. Scripts SLURM a corregir para la entrega (.zip)

- `run_parte_c_big.slurm` **no tiene** `--qos=hpc-iic3533` ni `--account=default-account` (el enunciado dice que son obligatorios).
- `run_parte_d.slurm` tiene un `EOF` suelto al final (`line 28: EOF: command not found`).
- Ningún script de 2 nodos exporta `OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` (está fijo en 1); dejarlo con la variable para que sea consistente.

## 5. Datos de hardware que necesito para la tabla 1

En el cluster (dentro de un job): `lscpu`, `mpirun --version`, `python -c "import numpy, scipy, mpi4py; numpy.show_config(); print(scipy.__version__, mpi4py.__version__)"`, y el tipo de red entre nodos (`ibstat` o `ip link`).
En el PC: versiones de Python, NumPy/BLAS y Open MPI.

## Qué partes de los `.md` actuales no responden el enunciado

- `results_d.md`: escalabilidad 1→16 procesos mezclando 1 y 2 nodos y sin variar T → no es la parte (d).
- `results_e.md`: compara formas 1×8/2×4/4×2/8×1 en 2 nodos → no es la parte (e) (la (e) es config 3 vs 4 vs 5). Se puede dejar como anexo.
- `results_f.md`: 2×4 con b ∈ {2048, 512, 128} → no es la parte (f) (que es 2×2 con b=4096 vs b=512).
- `results_c.md`: la fila b=4096 viene de otra configuración (2 nodos, T=1).
