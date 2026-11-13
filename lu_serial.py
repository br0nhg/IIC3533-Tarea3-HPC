import argparse
import time
import numpy as np
import scipy.linalg

def generate_matrix(N, seed=42):
    """Genera una matriz diagonal dominante para garantizar LU sin pivoteo."""
    np.random.seed(seed)
    A = np.random.randn(N, N)
    np.fill_diagonal(A, np.sum(np.abs(A), axis=1) + 10.0)
    return A

def lu_serial_blocked(A, b):
    """Factorización LU por bloques secuencial[cite: 33, 35]."""
    N = A.shape[0]
    num_blocks = N // b
    
    for k in range(num_blocks):
        # 1. Factorizar el bloque diagonal A_kk[cite: 33]
        kk_slice = slice(k * b, (k + 1) * b)
        A_kk = A[kk_slice, kk_slice]
        lu, _ = scipy.linalg.lu_factor(A_kk)
        
        # Guardar L (triangular inferior con 1s en la diagonal) y U (triangular superior) en A_kk
        L_kk = np.tril(lu, -1) + np.eye(b)
        U_kk = np.triu(lu)
        A[kk_slice, kk_slice] = L_kk + U_kk - np.eye(b)
        
        for idx in range((k + 1) * b, N, b):
            j_slice = slice(idx, idx + b)
            
            # 2a. Calcular bloques del panel U (U_kj = L_kk^-1 * A_kj)[cite: 33]
            A_kj = A[kk_slice, j_slice]
            A[kk_slice, j_slice] = scipy.linalg.solve_triangular(L_kk, A_kj, lower=True)
            
            # 2b. Calcular bloques del panel L (L_ik = A_ik * U_kk^-1)[cite: 33]
            A_ik = A[j_slice, kk_slice]
            A[j_slice, kk_slice] = scipy.linalg.solve_triangular(U_kk, A_ik.T, lower=False).T
            
        # 3. Actualización de la submatriz restante A_ij <- A_ij - L_ik * U_kj[cite: 33]
        for i_idx in range((k + 1) * b, N, b):
            i_slice = slice(i_idx, i_idx + b)
            L_ik = A[i_slice, kk_slice]
            for j_idx in range((k + 1) * b, N, b):
                j_slice = slice(j_idx, j_idx + b)
                U_kj = A[kk_slice, j_slice]
                A[i_slice, j_slice] -= L_ik @ U_kj

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=4096, help="Tamaño de la matriz N x N")
    parser.add_argument("--b", type=int, default=256, help="Tamaño de bloque b x b[cite: 33, 35]")
    args = parser.parse_args()

    N, b = args.N, args.b
    A = generate_matrix(N)

    t0 = time.perf_counter()
    lu_serial_blocked(A, b)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    gflops = ((2.0 / 3.0) * (N ** 3)) / (elapsed * 1e9)
    print(f"N={N}, b={b} | Tiempo: {elapsed:.4f} s | Rendimiento: {gflops:.2f} GFLOP/s")

if __name__ == "__main__":
    main()
