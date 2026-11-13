import argparse
import time
import numpy as np
import scipy.linalg
from mpi4py import MPI

def generate_matrix(N, seed=42):
    """Genera la matriz completa en serial para distribuir[cite: 33]."""
    np.random.seed(seed)
    A = np.random.randn(N, N)
    np.fill_diagonal(A, np.sum(np.abs(A), axis=1) + 10.0)
    return A

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=2048, help="Tamaño N x N")
    parser.add_argument("--b", type=int, default=128, help="Tamaño de bloque b[cite: 33, 35]")
    parser.add_argument("--pr", type=int, default=2, help="Filas del grid MPI[cite: 33, 35]")
    parser.add_argument("--pc", type=int, default=2, help="Columnas del grid MPI[cite: 33, 35]")
    args = parser.parse_args()

    N, b, pr, pc = args.N, args.b, args.pr, args.pc

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    assert pr * pc == size, f"pr * pc ({pr}x{pc}) debe ser igual al total de procesos MPI ({size})[cite: 35]"

    myrow = rank // pc
    mycol = rank % pc

    # Crear comunicadores por fila y por columna del grid 2D[cite: 33]
    row_comm = comm.Split(color=myrow, key=mycol)
    col_comm = comm.Split(color=mycol, key=myrow)

    nb = N // b

    # Determinar qué bloques globales pertenecen a este proceso (bloque-cíclico)[cite: 33]
    my_I = [I for I in range(nb) if I % pr == myrow]
    my_J = [J for J in range(nb) if J % pc == mycol]

    # Asignar espacio para la matriz local[cite: 33]
    A_local = np.zeros((len(my_I) * b, len(my_J) * b), dtype=np.float64)

    # El proceso 0 genera y distribuye la matriz[cite: 33]
    if rank == 0:
        A_full = generate_matrix(N)
        for I_idx, I in enumerate(my_I):
            for J_idx, J in enumerate(my_J):
                A_local[I_idx*b:(I_idx+1)*b, J_idx*b:(J_idx+1)*b] = \
                    A_full[I*b:(I+1)*b, J*b:(J+1)*b]

        for p in range(1, size):
            p_row, p_col = p // pc, p % pc
            p_I = [I for I in range(nb) if I % pr == p_row]
            p_J = [J for J in range(nb) if J % pc == p_col]
            buf = np.zeros((len(p_I) * b, len(p_J) * b), dtype=np.float64)
            for I_idx, I in enumerate(p_I):
                for J_idx, J in enumerate(p_J):
                    buf[I_idx*b:(I_idx+1)*b, J_idx*b:(J_idx+1)*b] = \
                        A_full[I*b:(I+1)*b, J*b:(J+1)*b]
            comm.Send(buf, dest=p, tag=99)
    else:
        comm.Recv(A_local, source=0, tag=99)

    comm.Barrier()
    
    t_comp = 0.0
    t_comm = 0.0
    t0_total = MPI.Wtime()

    # Algoritmo LU distribuido paso a paso[cite: 33, 34]
    for k in range(nb):
        r_k = k % pr
        c_k = k % pc

        I_local_idx = k // pr if myrow == r_k else -1
        J_local_idx = k // pc if mycol == c_k else -1

        A_kk = np.zeros((b, b), dtype=np.float64)

        # 1. Factorizar bloque diagonal A_kk en el proceso (r_k, c_k)[cite: 33, 34]
        if myrow == r_k and mycol == c_k:
            tc0 = MPI.Wtime()
            A_kk_orig = A_local[I_local_idx*b:(I_local_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b]
            lu, _ = scipy.linalg.lu_factor(A_kk_orig)
            L_kk = np.tril(lu, -1) + np.eye(b)
            U_kk = np.triu(lu)
            A_kk = L_kk + U_kk - np.eye(b)
            A_local[I_local_idx*b:(I_local_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b] = A_kk
            t_comp += (MPI.Wtime() - tc0)

        # Difundir A_kk en la fila y columna del grid[cite: 34]
        tm0 = MPI.Wtime()
        if myrow == r_k:
            row_comm.Bcast(A_kk, root=c_k)
        if mycol == c_k:
            col_comm.Bcast(A_kk, root=r_k)
        t_comm += (MPI.Wtime() - tm0)

        L_kk = np.tril(A_kk, -1) + np.eye(b)
        U_kk = np.triu(A_kk)

        # 2a. Panel U en la fila r_k[cite: 34]
        if myrow == r_k:
            tc0 = MPI.Wtime()
            for J_idx, J in enumerate(my_J):
                if J > k:
                    A_kj = A_local[I_local_idx*b:(I_local_idx+1)*b, J_idx*b:(J_idx+1)*b]
                    A_local[I_local_idx*b:(I_local_idx+1)*b, J_idx*b:(J_idx+1)*b] = \
                        scipy.linalg.solve_triangular(L_kk, A_kj, lower=True)
            t_comp += (MPI.Wtime() - tc0)

        # 2b. Panel L en la columna c_k[cite: 34]
        if mycol == c_k:
            tc0 = MPI.Wtime()
            for I_idx, I in enumerate(my_I):
                if I > k:
                    A_ik = A_local[I_idx*b:(I_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b]
                    A_local[I_idx*b:(I_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b] = \
                        scipy.linalg.solve_triangular(U_kk, A_ik.T, lower=False).T
            t_comp += (MPI.Wtime() - tc0)

        # 3. Intercambio de paneles L y U entre procesos[cite: 34]
        tm0 = MPI.Wtime()
        for J_idx, J in enumerate(my_J):
            if J > k:
                buf_U = np.zeros((b, b), dtype=np.float64)
                if myrow == r_k:
                    buf_U = A_local[I_local_idx*b:(I_local_idx+1)*b, J_idx*b:(J_idx+1)*b].copy()
                col_comm.Bcast(buf_U, root=r_k)

        for I_idx, I in enumerate(my_I):
            if I > k:
                buf_L = np.zeros((b, b), dtype=np.float64)
                if mycol == c_k:
                    buf_L = A_local[I_idx*b:(I_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b].copy()
                row_comm.Bcast(buf_L, root=c_k)
        t_comm += (MPI.Wtime() - tm0)

        # 4. Actualización local de la submatriz[cite: 33, 34]
        tc0 = MPI.Wtime()
        for I_idx, I in enumerate(my_I):
            if I > k:
                L_ik = A_local[I_idx*b:(I_idx+1)*b, J_local_idx*b:(J_local_idx+1)*b] if mycol == c_k else None
                for J_idx, J in enumerate(my_J):
                    if J > k:
                        U_kj = A_local[I_local_idx*b:(I_local_idx+1)*b, J_idx*b:(J_idx+1)*b] if myrow == r_k else None
                        # Multiplicación mat-mat local[cite: 33]
                        if L_ik is not None and U_kj is not None:
                            A_local[I_idx*b:(I_idx+1)*b, J_idx*b:(J_idx+1)*b] -= L_ik @ U_kj
        t_comp += (MPI.Wtime() - tc0)

    comm.Barrier()
    t_total = MPI.Wtime() - t0_total

    # Imprimir resultados consolidados desde el Rank 0[cite: 35, 36]
    if rank == 0:
        gflops = ((2.0 / 3.0) * (N ** 3)) / (t_total * 1e9)
        print(f"RES|N={N}|b={b}|grid={pr}x{pc}|T_comp={t_comp:.4f}s|T_comm={t_comm:.4f}s|T_total={t_total:.4f}s|GFLOPs={gflops:.2f}")

if __name__ == "__main__":
    main()
