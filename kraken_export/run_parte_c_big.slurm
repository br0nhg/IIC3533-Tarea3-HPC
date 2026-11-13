#!/bin/bash
#SBATCH --job-name=lu_c_big
#SBATCH --partition=hpc-iic3533
#SBATCH --nodes=2
#SBATCH --ntasks=4
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:10:00
#SBATCH --comment="Parte C bloques 8192 y 4096 en 2 nodos para evitar OOM"
#SBATCH --output=salida_parte_c_big.out

export PATH="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin:$PATH"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

for b in 8192 4096; do
    /home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/mpirun -n 4 --map-by ppr:2:node --bind-to none /home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/python lu_distributed.py --N 8192 --b $b --pr 2 --pc 2
done
