"""Parte (a): LU serial con N = 4096 y un thread, variando b.

Uso (desde la carpeta del repositorio):
    python run_experimento_a.py

Guarda la salida cruda en resultados/parte_a_local.out y un resumen en
resultados/parte_a_local.csv (una fila por repetición).
"""
import os
import subprocess
import sys

N = 4096
BLOCKS = [4096, 2048, 1024, 512, 256, 128, 64]
REPS = 3

os.makedirs("resultados", exist_ok=True)
raw_path = "resultados/parte_a_local.out"
csv_path = "resultados/parte_a_local.csv"

# Un solo thread de BLAS, como pide el enunciado.
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")

with open(raw_path, "w") as raw, open(csv_path, "w") as csv:
    csv.write("N,b,T,rep,tiempo_seg,gflops,pivots\n")
    print("=== Parte (a): LU serial, N=4096, 1 thread ===")
    for b in BLOCKS:
        cmd = [sys.executable, "lu_serial.py", "--N", str(N), "--b", str(b), "--reps", str(REPS)]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        raw.write(res.stdout + res.stderr)
        raw.flush()
        if res.returncode != 0:
            print(f"b={b}: ERROR\n{res.stderr}")
            continue
        for line in res.stdout.splitlines():
            if line.startswith("SERIAL|"):
                print(line)
                f = dict(kv.split("=") for kv in line.split("|")[1:])
                csv.write(f"{f['N']},{f['b']},{f['T']},{f['rep']},{f['t']},{f['gflops']},{f['pivots']}\n")

print(f"\nListo: {raw_path} y {csv_path}")
