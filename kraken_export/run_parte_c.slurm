#!/bin/bash
#SBATCH --job-name=lu_parte_c
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --comment="Barrido de tamaño de bloque b para LU distribuido"
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=2
#SBATCH --time=00:15:00
#SBATCH --mem=4096M
#SBATCH --output=salida_parte_c.out

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

export PATH="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin:$PATH"

for b in 8192 4096 2048 1024 512 256 128 64; do
    /home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/mpirun -n 4 /home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/python lu_distributed.py --N 8192 --b $b --pr 2 --pc 2
done
