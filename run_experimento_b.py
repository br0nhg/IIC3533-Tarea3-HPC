import subprocess

N = 2048
b = 128
pr = 2
pc = 2
output_file = "resultados_parte_b.csv"

# Encabezado del CSV
with open(output_file, "w") as f:
    f.write("N,b,pr,pc,t_comp,t_comm,t_total,gflops\n")

print("=== Ejecutando Experimento Parte (b) en WSL ===")
cmd = f"mpirun --oversubscribe -n 4 python lu_distributed.py --N {N} --b {b} --pr {pr} --pc {pc}"
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)

# Filtrar solo la línea con las métricas
for line in res.stdout.splitlines():
    if line.startswith("RES|"):
        print(line)
        parts = line.split("|")
        t_comp = parts[4].split("=")[1].replace("s", "")
        t_comm = parts[5].split("=")[1].replace("s", "")
        t_total = parts[6].split("=")[1].replace("s", "")
        gflops = parts[7].split("=")[1]
        
        with open(output_file, "a") as f:
            f.write(f"{N},{b},{pr},{pc},{t_comp},{t_comm},{t_total},{gflops}\n")

print(f"\n¡Listo! Resultado de la Parte (b) guardado en '{output_file}'")
