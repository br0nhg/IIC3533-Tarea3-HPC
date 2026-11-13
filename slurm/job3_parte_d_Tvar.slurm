#!/bin/bash
# Parte (d), T=2, 4 y 8, un nodo: configuraciones 0 (1x1) y 1 (1x2, 2x1).
# La asignacion es de 8 CPUs (2 tareas x 4 CPUs) y cada corrida usa exactamente
# p*T <= 8 CPUs, por lo que no hay oversubscription.
# El caso 2x2 con T=2 (configuracion 2) ya sale del job1.
# Uso: sbatch slurm/job3_parte_d_Tvar.slurm <b_c>    (por defecto 512)
#SBATCH --job-name=t3_d_Tvar
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --nodes=1
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=4
#SBATCH --mem=4096M
#SBATCH --time=00:15:00
#SBATCH --output=resultados/%x_%j.out

cd "$SLURM_SUBMIT_DIR"
source slurm/comun.sh
B_A=128
B_C=${1:-512}

for b in $B_A $B_C; do
    for T in 2 4; do
        corrida 0 1 1 $T $b
        corrida 1 1 2 $T $b
        corrida 1 2 1 $T $b
    done
    corrida 0 1 1 8 $b
done
