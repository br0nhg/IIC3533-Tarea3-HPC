#!/bin/bash
#SBATCH --job-name=lu_parte_ef
#SBATCH --partition=hpc-iic3533
#SBATCH --nodes=2
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --comment="Partes E y F: evaluacion de topologias de grilla y comunicacion multinodo"
#SBATCH --output=salida_parte_ef.out

export PATH="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin:$PATH"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

MPIRUN="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/mpirun"
PYTHON="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/python"
b_opt=512

# Parte E: Comparacion de topologias de grilla para P=8 (N=8192, b=512)
for grid in "1 8" "2 4" "4 2" "8 1"; do
    set -- $grid
    $MPIRUN -n 8 --map-by ppr:4:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr $1 --pc $2
done

# Parte F: Efecto del tamano de bloque en comunicacion multinodo (grilla 2x4)
for b in 2048 512 128; do
    $MPIRUN -n 8 --map-by ppr:4:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b --pr 2 --pc 4
done
