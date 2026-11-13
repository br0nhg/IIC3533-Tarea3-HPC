"""Factorización LU por bloques, versión serial (parte a).

Uso:
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        python lu_serial.py --N 4096 --b 128 --reps 3

Imprime una línea por repetición con el formato
    SERIAL|N=...|b=...|T=...|rep=...|t=...|gflops=...
"""
import argparse
import os
import time

import numpy as np
import scipy.linalg


# ----------------------------------------------------------------------
# Generación de la matriz
# ----------------------------------------------------------------------
def gen_block(N, b, I, J, seed=42):
    """Bloque (I, J) de b x b de la matriz de prueba.

    Entradas uniformes en (-1, 1) y diagonal igual a N. Como cada fila tiene
    N-1 entradas fuera de la diagonal con |a_ij| < 1, la suma es < N - 1 < N,
    así que la matriz es estrictamente diagonal dominante por filas y la LU
    existe sin pivoteo. Cada bloque depende solo de (seed, I, J), de modo que
    cada proceso MPI puede generar sus bloques sin comunicarse, y la versión
    serial genera exactamente la misma matriz (para el mismo b).
    """
    rng = np.random.default_rng([seed, I, J])
    blk = rng.uniform(-1.0, 1.0, size=(b, b))
    if I == J:
        np.fill_diagonal(blk, float(N))
    return blk


def generate_matrix(N, b, seed=42):
    """Matriz global N x N armada con gen_block."""
    nb = N // b
    A = np.empty((N, N), dtype=np.float64)
    for I in range(nb):
        for J in range(nb):
            A[I * b:(I + 1) * b, J * b:(J + 1) * b] = gen_block(N, b, I, J, seed)
    return A


# ----------------------------------------------------------------------
# LU por bloques
# ----------------------------------------------------------------------
def lu_serial_blocked(A, b):
    """Factoriza A = LU por bloques, en el lugar (sin pivoteo).

    Al terminar, el triángulo estrictamente inferior de A contiene L (con unos
    implícitos en la diagonal) y el triángulo superior contiene U.
    Devuelve el número de bloques diagonales en que lu_factor permutó filas
    (debe ser 0 para una matriz diagonal dominante).
    """
    N = A.shape[0]
    assert N % b == 0, "N debe ser múltiplo de b"
    nb = N // b
    n_pivots = 0

    for k in range(nb):
        s = slice(k * b, (k + 1) * b)      # filas/columnas del bloque k
        t = slice((k + 1) * b, N)          # filas/columnas restantes

        # 1. Factorizar el bloque diagonal: A_kk = L_kk U_kk
        lu, piv = scipy.linalg.lu_factor(A[s, s], check_finite=False)
        if np.any(piv != np.arange(b)):
            n_pivots += 1
        A[s, s] = lu

        if k == nb - 1:
            break

        # 2a. Panel U: U_kj = L_kk^{-1} A_kj  (todos los j > k a la vez)
        A[s, t] = scipy.linalg.solve_triangular(
            lu, A[s, t], lower=True, unit_diagonal=True, check_finite=False)

        # 2b. Panel L: L_ik = A_ik U_kk^{-1}  <=>  U_kk^T L_ik^T = A_ik^T
        A[t, s] = scipy.linalg.solve_triangular(
            lu, A[t, s].T, lower=False, trans='T', check_finite=False).T

        # 3. Actualización de la submatriz restante: A_ij <- A_ij - L_ik U_kj
        A[t, t] -= A[t, s] @ A[s, t]

    return n_pivots


def residual(A_orig, F):
    """||A - L U||_F / ||A||_F a partir de la matriz factorizada F."""
    L = np.tril(F, -1)
    np.fill_diagonal(L, 1.0)
    U = np.triu(F)
    return np.linalg.norm(A_orig - L @ U) / np.linalg.norm(A_orig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=4096, help="Tamaño de la matriz N x N")
    parser.add_argument("--b", type=int, default=256, help="Tamaño de bloque b")
    parser.add_argument("--reps", type=int, default=1, help="Repeticiones")
    parser.add_argument("--check", action="store_true",
                        help="Calcula el residuo ||A-LU||/||A|| (solo para N pequeño)")
    args = parser.parse_args()

    N, b = args.N, args.b
    T = os.environ.get("OMP_NUM_THREADS", "?")

    for rep in range(args.reps):
        A = generate_matrix(N, b)
        A0 = A.copy() if args.check else None

        t0 = time.perf_counter()
        n_piv = lu_serial_blocked(A, b)
        elapsed = time.perf_counter() - t0

        gflops = (2.0 / 3.0) * N ** 3 / (elapsed * 1e9)
        print(f"SERIAL|N={N}|b={b}|T={T}|rep={rep}|t={elapsed:.4f}|gflops={gflops:.2f}"
              f"|pivots={n_piv}", flush=True)
        if args.check:
            print(f"CHECK|N={N}|b={b}|residuo={residual(A0, A):.3e}", flush=True)


if __name__ == "__main__":
    main()
