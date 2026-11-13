#!/bin/bash
# Funciones comunes para los jobs de la Tarea 3. Se carga con: source slurm/comun.sh

PYENV=/home/grupo18-iic3533/miniconda3/envs/hpc_mpi/bin
export PATH="$PYENV:$PATH"
MPIRUN="$PYENV/mpirun"
PYTHON="$PYENV/python"
N=8192
REPS=3

# corrida <config> <pr> <pc> <T> <b> [opciones extra de mpirun]
# Ejecuta lu_distributed.py con p = pr*pc procesos y T threads de BLAS por proceso.
corrida () {
    local conf=$1 pr=$2 pc=$3 T=$4 b=$5
    shift 5
    local p=$((pr * pc))
    export OMP_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T MKL_NUM_THREADS=$T
    echo "### conf=$conf grid=${pr}x${pc} p=$p T=$T b=$b extra='$*' inicio=$(date +%T)"
    "$MPIRUN" -n "$p" --bind-to none "$@" \
        -x OMP_NUM_THREADS -x OPENBLAS_NUM_THREADS -x MKL_NUM_THREADS \
        "$PYTHON" lu_distributed.py --N "$N" --b "$b" --pr "$pr" --pc "$pc" --reps "$REPS"
    local rc=$?
    echo "### fin=$(date +%T) codigo=$rc"
}

info_nodo () {
    echo "===== INFO $(hostname) $(date) ====="
    lscpu
    echo "--- memoria"; free -g
    echo "--- red"; ip -br link 2>/dev/null; ibstat 2>/dev/null | head -30
    echo "--- versiones"
    "$MPIRUN" --version | head -2
    "$PYTHON" -c "import sys, numpy, scipy, mpi4py; print('python', sys.version.split()[0]); print('numpy', numpy.__version__, 'scipy', scipy.__version__, 'mpi4py', mpi4py.__version__); numpy.show_config()"
    echo "===== FIN INFO ====="
}
