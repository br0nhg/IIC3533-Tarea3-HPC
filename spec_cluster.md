## Especificaciones y Límites del Clúster (Kraken)

| Parámetro | Valor / Límite | Detalle |
| :--- | :--- | :--- |
| **Partición** | `hpc-iic3533` | Estado: `UP` |
| **Nodos disponibles** | `ventress`, `yodaxico` | 2 nodos de cómputo en total |
| **CPUs físicas por nodo** | 40 CPUs | 80 CPUs totales en la partición |
| **Límite de CPUs por nodo (Partición)** | **8 CPUs** (`MaxCPUsPerNode=8`) | Máximo 16 CPUs en total usando ambos nodos |
| **RAM física por nodo** | ~192 GB (`192038+ MB`) | ~449.8 GB totales entre ambos nodos |
| **Límite de RAM por nodo (Partición)** | **4096 MB (4 GB)** (`MaxMemPerNode=4096`) | Máximo 8192 MB (8 GB) en total usando ambos nodos |
| **Tiempo máximo de ejecución** | **15 minutos** (`00:15:00`) | `MaxTime=00:15:00` |
