#!/bin/bash
# Partes (c) y (f): grid 2x2 (configuracion 2), T=2, un nodo, barrido de b.
# El barrido incluye b=N/2=4096 y b=N/16=512, que son los dos casos de la parte (f)
# (los tiempos de cada proceso salen en las lineas PROC).
#SBATCH --job-name=t3_c_f
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=2
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --output=resultados/%x_%j.out

cd "$SLURM_SUBMIT_DIR"
source slurm/comun.sh
info_nodo

for b in 4096 2048 1024 512 256 128 64; do
    corrida 2 2 2 2 $b
done
# b = N: un solo bloque, todo en un proceso (puede quedarse sin memoria; va al final)
REPS=1 corrida 2 2 2 2 8192
