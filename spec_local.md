=== Entorno de Ejecución Local (WSL2) ===
• Procesador (CPU): Intel(R) Pentium(R) CPU 4417U @ 2.30GHz
• Arquitectura de Núcleos: 2 núcleos físicos / 4 hilos (Hyper-Threading: 2 threads/core)
• Memoria RAM asignada a WSL: 1.8 GiB
• Jerarquía de Cachés:
  - Caché L1 Data: 64 KiB (32 KiB por núcleo)
  - Caché L2: 512 KiB (256 KiB por núcleo)
  - Caché L3 (Compartida): 2 MiB
• Sistema Operativo: WSL2 en Windows (Ubuntu 22.04 LTS)

PD: para ejecutar la parte b) tuve que añadir --oversubscribe a la línea de comando.

'''
(base) alvar@LAPTOP-8C52V2GC:~/uc/hpc/tareas/T3$ mpirun -n 4 python lu_distributed.py --N 2048 --b 128 --pr 2 --pc 2
--------------------------------------------------------------------------
There are not enough slots available in the system to satisfy the 4
slots that were requested by the application:

  python
...
'''