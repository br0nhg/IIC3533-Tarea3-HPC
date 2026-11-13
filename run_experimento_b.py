"""Parte (b): verificación de correctitud y prueba local de lu_distributed.py.

Uso (desde la carpeta del repositorio):
    python run_experimento_b.py

1. Verifica el residuo de lu_serial.py (N = 1024).
2. Para los grids 1x1, 1x2, 2x1 y 2x2 (N = 1024, b = 128) compara
   lu_distributed.py contra lu_serial.py y calcula ||A - LU|| / ||A||.
3. Prueba de tiempos en el grid 2x2 con N = 2048, b = 128 (con oversubscribe,
   solo para comprobar que corre y que imprime los tiempos de cada proceso).

Guarda todo en resultados/parte_b_local.out. Si alguna línea dice FALLA o hay
un error, avisar ANTES de correr en el cluster.
"""
import os
import subprocess
import sys

os.makedirs("resultados", exist_ok=True)
raw_path = "resultados/parte_b_local.out"
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
py = sys.executable


def run(cmd, raw):
    print("$ " + " ".join(cmd))
    raw.write("$ " + " ".join(cmd) + "\n")
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    raw.write(res.stdout + res.stderr + "\n")
    raw.flush()
    for line in res.stdout.splitlines():
        if line.startswith(("VERIFY|", "CHECK|", "RES|", "PROC|", "ERROR")):
            print("   " + line)
    if res.returncode != 0:
        print(f"   ERROR (código {res.returncode}):\n{res.stderr}")
    return res


all_ok = True
with open(raw_path, "w") as raw:
    print("=== 1. Serial ===")
    r = run([py, "lu_serial.py", "--N", "1024", "--b", "128", "--check"], raw)
    all_ok &= r.returncode == 0

    print("\n=== 2. Verificación distribuida (N=1024, b=128) ===")
    for pr, pc in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        r = run(["mpirun", "--oversubscribe", "-n", str(pr * pc), py, "lu_distributed.py",
                 "--N", "1024", "--b", "128", "--pr", str(pr), "--pc", str(pc), "--verify"], raw)
        all_ok &= r.returncode == 0 and "|OK" in r.stdout

    print("\n=== 3. Prueba de tiempos 2x2 (N=2048, b=128) ===")
    r = run(["mpirun", "--oversubscribe", "-n", "4", py, "lu_distributed.py",
             "--N", "2048", "--b", "128", "--pr", "2", "--pc", "2", "--reps", "3"], raw)
    all_ok &= r.returncode == 0

print(f"\nSalida completa en {raw_path}")
print("TODO OK: se puede pasar al cluster." if all_ok else
      "HAY PROBLEMAS: mandar resultados/parte_b_local.out antes de correr en el cluster.")
