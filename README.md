# Performance Test - Comparação de Servidores Web

Este projeto realiza testes de desempenho (performance tests) comparando três configurações de servidores web:
- **NGINX** (latest)
- **Apache HTTP Server** com MPM Prefork
- **Apache HTTP Server** com MPM Event

## 📋 Descrição

O projeto utiliza **K6** (ferramenta de teste de carga) para executar testes de stress nos servidores web configurados via Docker Compose. Os testes avaliam métricas como throughput (RPS), latência, uso de CPU e memória sob diferentes cargas de trabalho.

## 🚀 Funcionalidades

- Execução automatizada de testes de carga com diferentes níveis de usuários virtuais (VUs)
- Coleta de métricas de desempenho do K6 (RPS, latência, erros)
- Monitoramento de recursos dos containers (CPU e memória)
- Análise e visualização de resultados através de gráficos
- Comparação de desempenho entre diferentes servidores

## 📦 Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado:

- [Docker](https://docs.docker.com/get-docker/) (versão 20.10 ou superior)
- [Docker Compose](https://docs.docker.com/compose/install/) (versão 2.0 ou superior)
- [Python 3](https://www.python.org/downloads/) (versão 3.7 ou superior)
- Bibliotecas Python:
  ```bash
  pip install pandas matplotlib seaborn
  ```

## 🏗️ Estrutura do Projeto

```
.
├── docker-compose.yml          # Configuração dos containers
├── test.sh                     # Script principal de execução dos testes
├── analyze.py                  # Script de análise e geração de gráficos
├── nginx/                      # Configurações do NGINX
│   └── default.conf
├── apache/                     # Configurações do Apache
│   ├── httpd-prefork.conf
│   └── httpd-event.conf
├── k6/                         # Scripts de teste K6
│   └── test.js
├── static/                     # Arquivos estáticos servidos
│   └── file1.txt
├── results-*/                  # Diretórios com resultados dos testes
└── plots-all/                  # Diretório com gráficos gerados
```

## 🔧 Configuração

### Servidores Web

Os servidores são configurados para servir um arquivo estático (`file1.txt`) de 1000 linhas:

- **NGINX**: Porta 8081
- **Apache Prefork**: Porta 8082
- **Apache Event**: Porta 8083

### Parâmetros de Teste

Os testes são configurados no arquivo `test.sh`:

```bash
LOADS=(100 1000 5000 10000)  # Número de usuários virtuais (VUs)
DURATION="10s"                # Duração de cada teste
```

Você pode ajustar estes valores conforme necessário.

## ▶️ Execução

### 1. Executar os Testes

Execute o script principal para iniciar todos os testes:

```bash
./test.sh
```

O script irá:
1. Iniciar os containers Docker (NGINX, Apache Prefork, Apache Event, K6)
2. Executar testes de carga para cada servidor com diferentes níveis de VUs
3. Coletar métricas de desempenho e uso de recursos
4. Salvar os resultados em um diretório `results-<timestamp>/`

### 2. Analisar os Resultados

Após a execução dos testes, analise os resultados com o script Python:

```bash
python3 analyze.py
```

Durante a execução, você será solicitado a escolher:

1. **Tipo de plot**:
   - `1` - Cada execução separada (mostra todas as execuções individuais)
   - `2` - Média de todas as execuções por servidor/carga (recomendado)

2. **Gerar CSV**:
   - `s` - Gera um arquivo CSV com o resumo das métricas
   - `n` - Não gera CSV

### 3. Visualizar os Resultados

Os gráficos são salvos no diretório `plots-all/` com os seguintes arquivos:

- `throughput_vs_load-*.png` - Throughput (RPS) vs Carga
- `latency_vs_load-*.png` - Latência P95 vs Carga
- `cpu_vs_load-*.png` - Uso de CPU vs Carga
- `mem_vs_load-*.png` - Uso de Memória vs Carga

Se optou por gerar o CSV, também encontrará:
- `summary-*.csv` - Resumo de todas as métricas

## 📊 Métricas Coletadas

### K6 Metrics
- **RPS (Requests Per Second)**: Taxa de requisições por segundo
- **Latência Média**: Tempo médio de resposta em milissegundos
- **Latência P95**: 95º percentil da latência
- **Erros**: Número de requisições falhadas
- **Checks**: Validações bem-sucedidas

### Docker Stats
- **CPU (%)**: Percentual de uso de CPU do container
- **Memória (MB)**: Uso de memória RAM do container

## 🛠️ Customização

### Modificar Carga de Teste

Edite o arquivo `test.sh` e ajuste o array `LOADS`:

```bash
LOADS=(50 100 500 1000 5000)  # Adicione ou remova cargas conforme necessário
DURATION="30s"                 # Ajuste a duração do teste
```

### Modificar Script de Teste K6

Edite o arquivo `k6/test.js` para customizar o comportamento do teste:

```javascript
export default function () {
  const target = __ENV.TARGET || "http://nginx:80/file1.txt";
  let res = http.get(target);
  latency.add(res.timings.duration);
  check(res, { "status is 200": (r) => r.status === 200 });
}
```

### Ajustar Configurações dos Servidores

- **NGINX**: Edite `nginx/default.conf`
- **Apache**: Edite `apache/httpd-prefork.conf` ou `apache/httpd-event.conf`

## 🧹 Limpeza

Para remover os containers após os testes:

```bash
docker compose down
```

Para remover também os volumes e redes:

```bash
docker compose down -v
```

## 📝 Notas

- Os testes são executados dentro de containers Docker para garantir isolamento
- Cada teste coleta métricas em tempo real enquanto o K6 está executando
- Os resultados são organizados por timestamp para facilitar comparações históricas
- O arquivo `file1.txt` contém 1000 linhas de texto de teste

## 🤝 Contribuindo

Sinta-se à vontade para:
1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto é open source e está disponível para uso educacional e profissional.

## 👤 Autor

DevBrunoRafael

---

**Dica**: Para obter resultados mais precisos, execute os testes múltiplas vezes e use a opção de média do `analyze.py`.
