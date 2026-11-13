"""Factorización LU por bloques distribuida en un grid 2D de procesos (mpi4py).

Uso:
    mpirun -n 4 python lu_distributed.py --N 8192 --b 512 --pr 2 --pc 2 --reps 3
    mpirun -n 4 python lu_distributed.py --N 1024 --b 128 --pr 2 --pc 2 --verify

Salida (una línea por repetición y por proceso, impresa por el rank 0):
    RES|N=..|b=..|grid=PRxPC|p=..|T=..|rep=..|t_total=..|t_comp_max=..|t_comm_max=..
        |t_comp_mean=..|t_comm_mean=..|gflops=..
    PROC|N=..|b=..|grid=..|T=..|rep=..|rank=..|row=..|col=..|host=..|t_comp=..|t_comm=..|t_total=..
Con --verify, además:
    VERIFY|N=..|b=..|grid=..|max_rel_diff_vs_serial=..|residuo=..|pivots=..|OK/FALLA
"""
import argparse
import os

import numpy as np
import scipy.linalg
from mpi4py import MPI

from lu_serial import gen_block, generate_matrix, lu_serial_blocked, residual


def local_blocks(nb, p, me):
    """Índices globales de bloque que tiene el proceso de fila/columna `me`."""
    return list(range(me, nb, p))


def n_done(k, p, me):
    """Cuántos de mis bloques (fila o columna) tienen índice global <= k."""
    return 0 if k < me else (k - me) // p + 1


def build_local(N, b, my_I, my_J):
    """Genera el arreglo local con los bloques (I, J) de este proceso."""
    A = np.empty((len(my_I) * b, len(my_J) * b), dtype=np.float64)
    for li, I in enumerate(my_I):
        for lj, J in enumerate(my_J):
            A[li * b:(li + 1) * b, lj * b:(lj + 1) * b] = gen_block(N, b, I, J)
    return A


def lu_distributed(A, N, b, pr, pc, myrow, mycol, row_comm, col_comm):
    """LU por bloques sobre el arreglo local A (en el lugar).

    Devuelve (t_comp, t_comm, n_pivots) de este proceso.
    t_comm incluye el empaquetado de los paneles y la espera en los Bcast.
    """
    nb = N // b
    nbr, nbc = A.shape[0] // b, A.shape[1] // b   # bloques locales (filas, columnas)
    wtime = MPI.Wtime
    t_comp = t_comm = 0.0
    n_piv = 0
    Akk = np.empty((b, b), dtype=np.float64)

    for k in range(nb):
        r, c = k % pr, k % pc                      # dueño de A_kk
        i0 = n_done(k, pr, myrow)                  # primera fila local con I > k
        j0 = n_done(k, pc, mycol)                  # primera columna local con J > k
        kr, kc = k // pr, k // pc                  # posición local de la fila/columna k
        nrows = (nbr - i0) * b                     # alto de mi parte de la submatriz
        ncols = (nbc - j0) * b                     # ancho de mi parte de la submatriz

        # ---- 1. Factorizar A_kk en (r, c) ------------------------------
        if myrow == r and mycol == c:
            t0 = wtime()
            lu, piv = scipy.linalg.lu_factor(
                A[kr * b:(kr + 1) * b, kc * b:(kc + 1) * b], check_finite=False)
            if np.any(piv != np.arange(b)):
                n_piv += 1
            A[kr * b:(kr + 1) * b, kc * b:(kc + 1) * b] = lu
            Akk[:] = lu
            t_comp += wtime() - t0

        # ---- Difundir A_kk en la fila r (raíz c) y en la columna c (raíz r)
        t0 = wtime()
        if myrow == r:
            row_comm.Bcast(Akk, root=c)
        if mycol == c:
            col_comm.Bcast(Akk, root=r)
        t_comm += wtime() - t0

        # ---- 2a. Panel U (fila r): U_kj = L_kk^{-1} A_kj, j > k ---------
        if myrow == r and ncols > 0:
            t0 = wtime()
            rs = slice(kr * b, (kr + 1) * b)
            A[rs, j0 * b:] = scipy.linalg.solve_triangular(
                Akk, A[rs, j0 * b:], lower=True, unit_diagonal=True, check_finite=False)
            t_comp += wtime() - t0

        # ---- 2b. Panel L (columna c): L_ik = A_ik U_kk^{-1}, i > k ------
        if mycol == c and nrows > 0:
            t0 = wtime()
            cs = slice(kc * b, (kc + 1) * b)
            A[i0 * b:, cs] = scipy.linalg.solve_triangular(
                Akk, A[i0 * b:, cs].T, lower=False, trans='T', check_finite=False).T
            t_comp += wtime() - t0

        # ---- 3. Difundir paneles: U por columnas (raíz r), L por filas (raíz c)
        t0 = wtime()
        Upan = Lpan = None
        if ncols > 0:     # igual para todos los procesos de mi columna del grid
            if myrow == r:
                Upan = np.ascontiguousarray(A[kr * b:(kr + 1) * b, j0 * b:])
            else:
                Upan = np.empty((b, ncols), dtype=np.float64)
            col_comm.Bcast(Upan, root=r)
        if nrows > 0:     # igual para todos los procesos de mi fila del grid
            if mycol == c:
                Lpan = np.ascontiguousarray(A[i0 * b:, kc * b:(kc + 1) * b])
            else:
                Lpan = np.empty((nrows, b), dtype=np.float64)
            row_comm.Bcast(Lpan, root=c)
        t_comm += wtime() - t0

        # ---- 4. Actualización: una sola multiplicación sobre el sub-arreglo
        if nrows > 0 and ncols > 0:
            t0 = wtime()
            A[i0 * b:, j0 * b:] -= Lpan @ Upan
            t_comp += wtime() - t0

    return t_comp, t_comm, n_piv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=2048, help="Tamaño N x N")
    parser.add_argument("--b", type=int, default=128, help="Tamaño de bloque b")
    parser.add_argument("--pr", type=int, default=2, help="Filas del grid de procesos")
    parser.add_argument("--pc", type=int, default=2, help="Columnas del grid de procesos")
    parser.add_argument("--reps", type=int, default=1, help="Repeticiones")
    parser.add_argument("--verify", action="store_true",
                        help="Compara contra lu_serial y calcula el residuo (N pequeño)")
    args = parser.parse_args()
    N, b, pr, pc = args.N, args.b, args.pr, args.pc

    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()
    if pr * pc != size or N % b != 0:
        if rank == 0:
            print(f"ERROR: se requiere pr*pc == procesos ({pr}x{pc} vs {size}) "
                  f"y N múltiplo de b ({N}, {b})", flush=True)
        comm.Abort(1)

    myrow, mycol = rank // pc, rank % pc
    row_comm = comm.Split(myrow, mycol)   # rank en row_comm = mycol
    col_comm = comm.Split(mycol, myrow)   # rank en col_comm = myrow
    host = MPI.Get_processor_name()
    T = os.environ.get("OMP_NUM_THREADS", "?")
    tag = f"N={N}|b={b}|grid={pr}x{pc}"

    nb = N // b
    my_I = local_blocks(nb, pr, myrow)
    my_J = local_blocks(nb, pc, mycol)

    for rep in range(args.reps):
        A = build_local(N, b, my_I, my_J)      # generación fuera del tiempo medido

        comm.Barrier()
        t_start = MPI.Wtime()
        t_comp, t_comm, n_piv = lu_distributed(A, N, b, pr, pc, myrow, mycol,
                                               row_comm, col_comm)
        t_mine = MPI.Wtime() - t_start          # cuándo terminé yo
        comm.Barrier()
        t_total = MPI.Wtime() - t_start         # cuándo terminaron todos

        info = comm.gather((rank, myrow, mycol, host, t_comp, t_comm, t_mine), root=0)
        tot_piv = comm.reduce(n_piv, op=MPI.SUM, root=0)
        if rank == 0:
            comps = [x[4] for x in info]
            comms = [x[5] for x in info]
            gflops = (2.0 / 3.0) * N ** 3 / (t_total * 1e9)
            print(f"RES|{tag}|p={size}|T={T}|rep={rep}|t_total={t_total:.4f}"
                  f"|t_comp_max={max(comps):.4f}|t_comm_max={max(comms):.4f}"
                  f"|t_comp_mean={np.mean(comps):.4f}|t_comm_mean={np.mean(comms):.4f}"
                  f"|gflops={gflops:.2f}|pivots={tot_piv}", flush=True)
            for (rk, rw, cl, hs, tc, tm, tt) in info:
                print(f"PROC|{tag}|T={T}|rep={rep}|rank={rk}|row={rw}|col={cl}|host={hs}"
                      f"|t_comp={tc:.4f}|t_comm={tm:.4f}|t_total={tt:.4f}", flush=True)

    # ---- Verificación (usa la matriz de la última repetición) ----------
    if args.verify:
        pieces = comm.gather((myrow, mycol, A), root=0)
        if rank == 0:
            F = np.empty((N, N), dtype=np.float64)
            for (rw, cl, Al) in pieces:
                for li, I in enumerate(local_blocks(nb, pr, rw)):
                    for lj, J in enumerate(local_blocks(nb, pc, cl)):
                        F[I * b:(I + 1) * b, J * b:(J + 1) * b] = \
                            Al[li * b:(li + 1) * b, lj * b:(lj + 1) * b]
            A0 = generate_matrix(N, b)
            S = A0.copy()
            lu_serial_blocked(S, b)
            diff = np.max(np.abs(F - S)) / np.max(np.abs(S))
            res = residual(A0, F)
            ok = diff < 1e-10 and res < 1e-12 and tot_piv == 0
            print(f"VERIFY|{tag}|max_rel_diff_vs_serial={diff:.3e}|residuo={res:.3e}"
                  f"|pivots={tot_piv}|{'OK' if ok else 'FALLA'}", flush=True)

    row_comm.Free()
    col_comm.Free()


if __name__ == "__main__":
    main()
