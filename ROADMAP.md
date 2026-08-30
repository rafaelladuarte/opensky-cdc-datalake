# 🗺️ ROADMAP do Projeto: OpenSky CDC DataLake

Este documento organiza as pendências do projeto em formato de Kanban. As tarefas estão classificadas por ordem lógica de execução (Prioridade) e relevância no pipeline geral (Impacto).

---

## 📋 TODO (A Fazer)

### 🐍 [Card 2] Correção do Script de Ingestão e Variáveis de Ambiente
* **Descrição:** Refatorar o `insert_data_postgres.py`. Ajustar a função de insert para aceitar um DataFrame do Pandas ou a lista retornada pela API. Corrigir a chamada da função que está errada (`execute_insert(df)` vs `postgres_insert(data)`). Configurar e utilizar o `.env` para as credenciais do banco.
* **Prioridade:** 🔴 Alta (Bloqueante)
* **Impacto:** 💥 Alto (Garante a entrada dos dados reais no PostgreSQL)

### 🔌 [Card 3] Ajuste do Conector Source (Debezium/PostgreSQL)
* **Descrição:** Atualizar o `conector-postgres.json` para escutar o schema e a tabela corretos dos dados da OpenSky (`opensky_api_states_all`), ao invés do schema genérico `inventory` herdado do repositório base.
* **Prioridade:** 🟡 Média (Depende do Card 2)
* **Impacto:** 💥 Alto (Inicia o streaming dos eventos de mudança)

### 📥 [Card 4] Configuração do Conector Sink (Kafka -> MinIO)
* **Descrição:** Escrever o `conector-minio.json` (atualmente vazio) para definir como o Kafka Connect irá despejar os eventos dentro do bucket MinIO.
* **Prioridade:** 🟡 Média (Depende do Card 3)
* **Impacto:** 🔸 Médio (Estabelece a primeira camada do Data Lake)

### ⚙️ [Card 5] Desenvolvimento do Consumidor Python
* **Descrição:** Desenvolver o código dos arquivos vazios na pasta `app-python/app/` (`main.py`, `consumer.py`, `processor.py`, `config.py`). Esta aplicação consumirá os tópicos do Kafka, fará processamentos se necessário e salvará em formato final (ex: Parquet) no Data Lake.
* **Prioridade:** 🟢 Baixa (Pode ser feito por último)
* **Impacto:** 💥 Alto (Entrega o valor final: dados prontos para análise)

---

## ⏳ DOING (Em Andamento)
*(Nenhuma tarefa em andamento no momento)*

---

## ✅ DONE (Concluído)
### 🗄️ [Card 1] Configuração da Infraestrutura Base
* **Descrição:** Escrever o `docker-compose.yaml` com os serviços necessários (PostgreSQL, Kafka, Zookeeper, Kafka Connect, Debezium e MinIO).
* **Conclusão:** `docker-compose.yaml` populado e testado. Contêineres rodando e plugins do Kafka Connect instalados corretamente.

* **Estrutura Base do Repositório:** Pastas e arquivos iniciais criados.
* **Documentação (README):** Visão geral e objetivos definidos.
