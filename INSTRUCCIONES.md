# T3: instrucciones para correr los experimentos

El código está corregido (ver "Qué cambió" al final). Solo hay que correrlo **sin modificar nada** y subir las salidas al repositorio. Los números no se pasan a tablas a mano: con los `.out` crudos se arma el informe.

Plazo: **lunes 16 de noviembre, 23:59**. Idealmente todo corrido el domingo.

---

## Paso 0: bajar el repositorio

```bash
git clone git@github.com:br0nhg/IIC3533-Tarea3-HPC.git
cd IIC3533-Tarea3-HPC
```

(Si ya lo tienen: `git pull`.)

## Paso 1: computador personal — YA HECHO

Las partes (a) y (b) ya se corrieron en el Mac de Bruno (Apple M5) y sus resultados están en `resultados/parte_a_local.*` y `resultados/parte_b_local.out`. La verificación dio **OK en los 4 grids** (residuo 4.2e-16, idéntico a la versión serial, sin pivoteo), así que el código está validado. También se revisó la memoria con N=8192: el peor caso (1×1) usa ~1.7 GB, por debajo del límite de 4 GB por nodo.

**No hay que correr nada en el computador. Solo el Paso 2.**

## Paso 2: en el cluster

```bash
ssh kraken
git clone git@github.com:br0nhg/IIC3533-Tarea3-HPC.git   # o git pull si ya está
cd IIC3533-Tarea3-HPC
```

(Si en el cluster no tienen llave SSH para GitHub, usen `git clone https://github.com/br0nhg/IIC3533-Tarea3-HPC.git`, o copien la carpeta con `scp`.)

**Todos los `sbatch` se lanzan desde la raíz del repositorio** (los scripts usan rutas relativas y escriben en `resultados/`).

### 2.1 Primero el job de la parte (c)

```bash
sbatch slurm/job1_parte_c_f.slurm
```

Cuando termine (`squeue -u $USER` ya no lo muestra), ver cuál b fue el más rápido:

```bash
grep '^RES' resultados/t3_c_f_*.out
```

Mirar la columna `t_total`: el b con menor tiempo (en las 3 repeticiones) es **b_c**.

### 2.2 Después, los otros tres jobs, pasando b_c como argumento

Si b_c = 512 (el valor por defecto):

```bash
sbatch slurm/job2_parte_d_T1.slurm 512
sbatch slurm/job3_parte_d_Tvar.slurm 512
sbatch slurm/job4_parte_e.slurm 512
```

Si b_c salió distinto (por ejemplo 1024), cambiar el `512` por ese valor en los tres comandos. Si están apurados, se pueden mandar los tres con 512 de inmediato sin esperar al job1.

Se pueden encolar los tres juntos: el límite es 4 en cola y 1 en ejecución, y se ejecutan de a uno. Cada job dura menos de 15 minutos.

### 2.3 Revisar y subir

```bash
ls resultados/
grep -c '^RES' resultados/*.out      # cada .out debe tener líneas RES
grep -iE 'error|killed|oom' resultados/*.out
```

- Que b = 8192 al final del job1 se caiga por memoria (OOM) es esperable; no hay que repetirlo.
- Cualquier otro error: avisar con el `.out`.

```bash
git add resultados/
git commit -m "Resultados cluster"
git push
```

(Si no pueden hacer push desde el cluster, copien `resultados/` al computador con `scp -r kraken:IIC3533-Tarea3-HPC/resultados .` y súbanlo desde ahí.)

---

## Qué corre cada job

| Job | Partes | Nodos | Corridas |
|---|---|---|---|
| `job1_parte_c_f` | c, f | 1 | Grid 2×2 (config 2), T=2, b = 4096 … 64 (y 8192 al final). Incluye b=N/2 y b=N/16 de la parte (f), con los tiempos de cada proceso. También guarda `lscpu` y las versiones. |
| `job2_parte_d_T1` | d (y config 3 para e) | 1 | T=1: 1×1, 1×2, 2×1, 2×2, 2×4, 4×2, con b=128 y b_c. |
| `job3_parte_d_Tvar` | d | 1 | 1×1 con T=2, 4, 8; 1×2 y 2×1 con T=2, 4; con b=128 y b_c. |
| `job4_parte_e` | e | 2 | Config 4 (2×4, 4 por nodo) y config 5 (4×4, 8 por nodo), T=1, b=128 y b_c. También registra la red. |

Todas las corridas usan N = 8192 y 3 repeticiones.

## Formato de la salida

- `RES|...`: una línea por corrida y repetición, con el tiempo total, el máximo y el promedio de `t_comp` y `t_comm` entre procesos, y los GFLOP/s.
- `PROC|...`: una línea por proceso, con su nodo (`host`), `t_comp`, `t_comm` y `t_total`.
- `### conf=... grid=... T=... b=...`: marca qué configuración se está corriendo.

## Qué cambió en el código

1. **Bug de la actualización:** antes los paneles recibidos por `Bcast` se descartaban y solo actualizaba el dueño de A_kk. Ahora cada proceso actualiza toda su submatriz con una sola multiplicación: `A[i0:, j0:] -= L_panel @ U_panel`.
2. **Panel L:** faltaba `trans='T'` en `solve_triangular` (en el serial y en el distribuido).
3. **Un solo `Bcast` por panel**, en lugar de uno por bloque.
4. **Tiempos de cada proceso:** se imprimen todos, no solo los del rank 0.
5. **Verificación (`--verify`):** compara contra `lu_serial.py` y calcula `‖A−LU‖/‖A‖`. También revisa que `lu_factor` no haya pivoteado.
6. **Generación de la matriz:** cada proceso genera sus propios bloques (entradas uniformes en (−1,1) y diagonal N, estrictamente diagonal dominante). El rank 0 ya no arma la matriz completa, lo que evita los errores de memoria.
7. **Scripts SLURM:** todos llevan qos, partition y account, `--ntasks-per-node`, los threads de BLAS fijados explícitamente en cada corrida (y propagados a todos los procesos con `-x`) y `--bind-to none`, para que los T threads de un proceso no queden en un solo core. Las configuraciones de un nodo ahora corren realmente en un nodo.
