#!/bin/bash
#SBATCH --job-name=lu_parte_d
#SBATCH --partition=hpc-iic3533
#SBATCH --nodes=2
#SBATCH --ntasks=16
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --comment="Parte D escalabilidad con b_opt=512"
#SBATCH --output=salida_parte_d.out

export PATH="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin:$PATH"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

MPIRUN="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/mpirun"
PYTHON="/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin/python"
b_opt=512

# Escalabilidad para N=8192 (1x1, 1x2, 2x2, 2x4, 4x4)
$MPIRUN -n 1  --map-by ppr:1:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr 1 --pc 1
$MPIRUN -n 2  --map-by ppr:1:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr 1 --pc 2
$MPIRUN -n 4  --map-by ppr:2:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr 2 --pc 2
$MPIRUN -n 8  --map-by ppr:4:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr 2 --pc 4
$MPIRUN -n 16 --map-by ppr:8:node --bind-to none $PYTHON lu_distributed.py --N 8192 --b $b_opt --pr 4 --pc 4
EOF
