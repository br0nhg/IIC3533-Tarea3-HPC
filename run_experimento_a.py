import os
import subprocess

blocks = [4096, 2048, 1024, 512, 256, 128, 64]
N = 4096

output_file = "resultados_parte_a.csv"

with open(output_file, "w") as f:
    f.write("N,b,tiempo_seg,gflops\n")

print("=== Ejecutando Experimento Parte (a) en WSL ===")
for b in blocks:
    cmd = f"python lu_serial.py --N {N} --b {b}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = res.stdout.strip()
    print(out)
    
    # Extraer métricas de la salida
    if "Tiempo:" in out:
        parts = out.split("|")
        tiempo = parts[1].split(":")[1].replace("s", "").strip()
        gflops = parts[2].split(":")[1].replace("GFLOP/s", "").strip()
        with open(output_file, "a") as f:
            f.write(f"{N},{b},{tiempo},{gflops}\n")

print(f"\n¡Listo! Resultados guardados exitosamente en '{output_file}'")
