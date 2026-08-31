# 🗺️ ROADMAP do Projeto: OpenSky CDC DataLake

Este documento organiza as pendências do projeto em formato de Kanban. As tarefas estão classificadas por ordem lógica de execução (Prioridade) e relevância no pipeline geral (Impacto).

---

## 📋 TODO (A Fazer)
*(Nenhuma tarefa pendente)*

---

## ⏳ DOING (Em Andamento)
*(Nenhuma tarefa em andamento no momento)*

---

## ✅ DONE (Concluído)

### ✅ [Card 5] Desenvolvimento do Consumidor Python
* **Conclusão:** Módulos do consumidor desenvolvidos e integrados com Pandas e Pyarrow para limpar os dados CDC do Debezium e salvá-los no formato otimizado Parquet. O serviço Python foi adicionado ao `docker-compose.yaml`, executando a exportação no MinIO (`silver/opensky/`) através de lotes (batching).


### ✅ [Card 4] Configuração do Conector Sink (Kafka -> MinIO)
* **Conclusão:** Configuração `conector-minio.json` criada e registrada com sucesso. O conector `io.confluent.connect.s3.S3SinkConnector` está ativo consumindo o tópico `opensky.public.opensky_api_states_all` e gravando os arquivos JSON particionados no bucket `datalake` do MinIO.

### ✅ [Card 3] Ajuste do Conector Source (Debezium/PostgreSQL)
* **Conclusão:** Configuração `conector-postgres.json` finalizada e registrada. O Debezium está monitorando o log do PostgreSQL via slot de replicação e transmitindo as alterações da tabela `opensky_api_states_all` para o Kafka em tempo real.

### ✅ [Card 2] Correção do Script de Ingestão e Variáveis de Ambiente
* **Conclusão:** Script `insert_data_postgres.py` refatorado e funcional. Corrigidos 8 bugs (chamada de função inexistente, incompatibilidade de tipos, coluna ausente, typo, credenciais hardcoded, tabela sem DDL, deps faltando, .env exposto no git). Ambiente virtual criado com `uv`. **13.068 registros de voos inseridos no PostgreSQL com sucesso.**

### ✅ [Card 1] Configuração da Infraestrutura Base
* **Descrição:** Escrever o `docker-compose.yaml` com os serviços necessários (PostgreSQL, Kafka, Zookeeper, Kafka Connect, Debezium e MinIO).
* **Conclusão:** `docker-compose.yaml` populado e testado. Contêineres rodando e plugins do Kafka Connect instalados corretamente.

* **Estrutura Base do Repositório:** Pastas e arquivos iniciais criados.
* **Documentação (README):** Visão geral e objetivos definidos.
