#!/bin/bash
#SBATCH --comment="Experimentos factorizacion LU distribuida Tarea 3 IIC3533"
# Parte (e), dos nodos, T=1: configuracion 4 (2x4, 4 procesos por nodo)
# y configuracion 5 (4x4, 8 procesos por nodo). La configuracion 3 sale del job2.
# Uso: sbatch slurm/job4_parte_e.slurm <b_c>    (por defecto 512)
#SBATCH --job-name=t3_e
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --nodes=2
#SBATCH --ntasks=16
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --output=resultados/%x_%j.out

cd "$SLURM_SUBMIT_DIR"
source slurm/comun.sh
BS=$(valores_b "$1")
echo "### valores de b: $BS"
info_nodo

for b in $BS; do
    corrida 4 2 4 1 $b --map-by ppr:4:node
    corrida 5 4 4 1 $b --map-by ppr:8:node
done
