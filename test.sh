#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  echo
  echo "Finalizando... Derrubando containers (docker compose down)"
  docker compose down || true
}

trap cleanup EXIT INT TERM

TIMESTAMP=$(date +%Y%m%dT%H%M%S)
RESULTS_DIR="./results-$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

export RESULTS_DIR 

# Definir as cargas (VUs) e duração dos testes aqui:
LOADS=(100 1000 5000) #10000
DURATION="10s"        # 30s

SERVERS=(
  "nginx|http://nginx:80/file1.txt|nginx-server"
  "apache-prefork|http://apache-prefork:80/file1.txt|apache-prefork"
  "apache-event|http://apache-event:80/file1.txt|apache-event"
)

echo "Subindo containers..."
docker compose up -d
sleep 5
echo "Aguardando containers estarem saudáveis..."
sleep 5

for srv in "${SERVERS[@]}"; do
  IFS="|" read -r name url container <<< "$srv"
  echo "=== Testando $name ($url) ==="

  for load in "${LOADS[@]}"; do
    ts=$(date +%Y%m%dT%H%M%S)
    filename="${name}-${load}-${ts}.k6.summary.json"
    out_json="${RESULTS_DIR}/${filename}"
    stats_json="${RESULTS_DIR}/${name}-${load}-${ts}.dockerstats.json"

    echo "-> carga: ${load}, saída k6 agregada: ${out_json}"

    docker compose exec -T --user root k6 sh -c "mkdir -p /results && chmod 777 /results"

    echo "Iniciando teste k6..."

    docker compose exec -T --user root \
      -e TARGET="${url}" \
      k6 k6 run \
        --vus "${load}" \
        --duration "${DURATION}" \
        /scripts/test.js \
        --summary-export "/results/${filename}" &

    K6_PID=$!

    > "$stats_json"
    while kill -0 $K6_PID 2>/dev/null; do
      docker stats --no-stream --format "{{json .}}" "${container}" >> "$stats_json"
      sleep 0.1
    done

    wait $K6_PID

    echo "Salvo: k6 -> ${out_json}, docker stats -> ${stats_json}"
    sleep 2
  done
done

echo "Todos os testes finalizados. Resultados em ${RESULTS_DIR}"
