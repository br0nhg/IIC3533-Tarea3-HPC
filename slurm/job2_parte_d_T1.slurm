#!/bin/bash
# Parte (d), T=1, un nodo: configuraciones 0 (1x1), 1 (1x2, 2x1), 2 (2x2) y 3 (2x4, 4x2).
# Uso: sbatch slurm/job2_parte_d_T1.slurm <b_c>    (b_c = mejor b de la parte c; por defecto 512)
#SBATCH --job-name=t3_d_T1
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --output=resultados/%x_%j.out

cd "$SLURM_SUBMIT_DIR"
source slurm/comun.sh
BS=$(valores_b "$1")
echo "### valores de b: $BS"

for b in $BS; do
    corrida 0 1 1 1 $b
    corrida 1 1 2 1 $b
    corrida 1 2 1 1 $b
    corrida 2 2 2 1 $b
    corrida 3 2 4 1 $b
    corrida 3 4 2 1 $b
done
