#!/usr/bin/env python3
import json
import csv
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

print("Escolha o tipo de plot:")
print("1 - Cada execução separada")
print("2 - Média de todas as execuções por servidor/carga")
opcao = input("Digite 1 ou 2: ").strip()
if opcao not in ("1", "2"):
    raise ValueError("Opção inválida!")

gerar_csv = input("Deseja gerar summary CSV? (s/n): ").strip().lower()
if gerar_csv not in ("s", "n"):
    raise ValueError("Resposta inválida (esperado s/n).")

SUFIXO = "-media" if opcao == "2" else "-runs"

results_dirs = sorted(Path(".").glob("results-*"))
if not results_dirs:
    raise RuntimeError("Nenhuma pasta results-* encontrada.")

print("Encontradas pastas:")
for d in results_dirs:
    print(" -", d)

def parse_k6_summary(path):
    with open(path) as f:
        data = json.load(f)
    metrics = data.get("metrics", {})

    http_reqs = metrics.get("http_reqs", {})
    http_req_failed = metrics.get("http_req_failed", {})
    req_duration = metrics.get("http_req_duration", metrics.get("latency", {}))
    checks = metrics.get("checks", {})

    return {
        "rps": http_reqs.get("rate", 0),
        "requests": http_reqs.get("count", 0),
        "latency_avg_ms": req_duration.get("avg", 0),
        "latency_p95": req_duration.get("p(95)", 0),
        "errors": http_req_failed.get("fails", 0),
        "checks_passed": checks.get("passes", 0),
        "checks_total": checks.get("fails", 0) + checks.get("passes", 0),
    }

def parse_docker_stats(path):
    mem_vals = []
    cpu_vals = []

    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            cpu_str = data.get("CPUPerc", "0").strip().strip("%")

            try:
                cpu_vals.append(float(cpu_str))
            except:
                pass

            mem_str = data.get("MemUsage", "")
            m = re.match(r"([\d\.]+)([KMG]i?)B", mem_str)
            if m:
                val, unit = float(m.group(1)), m.group(2)
                if unit.startswith("K"):
                    mem_vals.append(val / 1024)
                elif unit.startswith("M"):
                    mem_vals.append(val)
                elif unit.startswith("G"):
                    mem_vals.append(val * 1024)

    return {
        "mem_mb": sum(mem_vals)/len(mem_vals) if mem_vals else None,
        "cpu_perc": sum(cpu_vals)/len(cpu_vals) if cpu_vals else None
    }

rows = []

for rd in results_dirs:
    print(f"\nProcessando: {rd}")
    k6_files = sorted(rd.glob("*.k6.summary.json"))

    for kf in k6_files:
        name_ts = kf.name.replace(".k6.summary.json", "")
        parts = name_ts.split("-")
        if len(parts) < 2:
            continue

        load_str = parts[-2]
        server = "-".join(parts[:-2])
        ts = parts[-1]

        try:
            load = int(load_str)
        except ValueError:
            print(f"Falha ao converter load para int: {kf.name}")
            continue

        k6m = parse_k6_summary(kf)
        stats_files = list(rd.glob(f"{server}-{load}-{ts}*.dockerstats.json"))
        statsm = parse_docker_stats(stats_files[0]) if stats_files else {"mem_mb": None, "cpu_perc": None}

        if k6m["requests"] == 0:
            print(f"Ignorando {kf.name} com requests=0")
            continue

        rows.append({
            "run_id": rd.name,
            "server": server,
            "load": load,
            "rps": k6m["rps"],
            "requests": k6m["requests"],
            "latency_avg_ms": k6m["latency_avg_ms"],
            "latency_p95": k6m["latency_p95"],
            "errors": k6m["errors"],
            "checks_passed": k6m["checks_passed"],
            "checks_total": k6m["checks_total"],
            "mem_mb": statsm["mem_mb"],
            "cpu_perc": statsm["cpu_perc"]
        })

df = pd.DataFrame(rows)
df["load"] = df["load"].astype(int)

PLOTS_DIR = Path("plots-all")
PLOTS_DIR.mkdir(exist_ok=True)

if opcao == "2":
    numeric_cols = ["rps", "requests", "latency_avg_ms", "latency_p95", "errors",
                    "checks_passed", "checks_total", "mem_mb", "cpu_perc"]

    df = df.groupby(["server", "load"], as_index=False)[numeric_cols].mean()
    print("Gerando gráficos com médias por servidor/carga...")

if gerar_csv == "s":
    csv_path = PLOTS_DIR / f"summary{SUFIXO}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nCSV gerado em: {csv_path}")

def plot_line(x, y, hue, style=None, title="", xlabel="", ylabel="", filename="plot.png",
              ylim=None, yticks=None, xticks=None):
    plt.figure(figsize=(8,5))
    sns.lineplot(data=df, x=x, y=y, hue=hue, style=style, marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if ylim:
        plt.ylim(ylim)
    if yticks:
        plt.yticks(range(ylim[0], ylim[1]+1, yticks))
    if xticks:
        plt.xticks(xticks)

    legend_fontsize = 7
    plt.legend(title=hue, fontsize=legend_fontsize, title_fontsize=legend_fontsize)
    plt.savefig(PLOTS_DIR / filename, dpi=150)
    plt.close()

RPS_MIN, RPS_MAX, RPS_STEP = 0, 40000, 5000
LAT_MIN, LAT_MAX, LAT_STEP = 0, 1000, 100
CPU_MIN, CPU_MAX, CPU_STEP = 0, 400, 100
MEM_MIN, MEM_MAX, MEM_STEP = 0, 100, 10

VUS_TICKS = [100, 1000, 5000, 10000]

plot_line("load", "rps", "server", style="run_id" if opcao=="1" else None,
          title="Throughput (RPS) vs Carga",
          xlabel="VUs", ylabel="RPS", filename=f"throughput_vs_load{SUFIXO}.png",
          ylim=(RPS_MIN, RPS_MAX), yticks=RPS_STEP, xticks=VUS_TICKS)

plot_line("load", "latency_p95", "server", style="run_id" if opcao=="1" else None,
          title="Latência p95 vs Carga",
          xlabel="VUs", ylabel="ms", filename=f"latency_vs_load{SUFIXO}.png",
          ylim=(LAT_MIN, LAT_MAX), yticks=LAT_STEP, xticks=VUS_TICKS)

plot_line("load", "cpu_perc", "server", style="run_id" if opcao=="1" else None,
          title="CPU (%) vs Carga",
          xlabel="VUs", ylabel="%", filename=f"cpu_vs_load{SUFIXO}.png",
          ylim=(CPU_MIN, CPU_MAX), yticks=CPU_STEP, xticks=VUS_TICKS)

plot_line("load", "mem_mb", "server", style="run_id" if opcao=="1" else None,
          title="Memória (MB) vs Carga",
          xlabel="VUs", ylabel="MB", filename=f"mem_vs_load{SUFIXO}.png",
          ylim=(MEM_MIN, MEM_MAX), yticks=MEM_STEP, xticks=VUS_TICKS)

print(f"\nGráficos salvos em: {PLOTS_DIR}")
