
# OpenSky CDC DataLake

<p align="center">
<img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/seu-usuario/opensky-cdc-datalake?style=plastic">
<img alt="GitHub repo file count" src="https://img.shields.io/github/directory-file-count/seu-usuario/opensky-cdc-datalake?style=plastic">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/seu-usuario/opensky-cdc-datalake?style=plastic">
</p>

<img src="https://opensky-network.org/images/coverage.png">

<p align="center">
<img src="https://img.shields.io/static/v1?label=Status&message=Em_Andamento&color=orange&style=for-the-badge"/>
</p>

## Descrição do Projeto

O **OpenSky CDC DataLake** é um projeto de estudo voltado para a captura e replicação de dados de tráfego aéreo em tempo real. Utilizando **Change Data Capture (CDC)**, o objetivo é armazenar os dados de voos da [OpenSky Network](https://opensky-network.org/data) em um Data Lake para posterior análise e visualização.

Este projeto será baseado no repositório [fia-vestival-cdc-lake](https://github.com/Labdata-FIA/fia-vestival-cdc-lake) do minicurso **"Hands-on - Replicando Informações em Realtime para o DataLake utilizando CDC"** da FIA Labdata. O desenvolvimento do projeto está previsto para começar em **junho**.

## Objetivo

Este projeto visa demonstrar o uso de **CDC para ingestão de dados de fluxo contínuo**, garantindo armazenamento eficiente e permitindo análises avançadas. O pipeline inclui:

- **Captura de dados** da OpenSky Network.
- **Armazenamento temporário** em PostgreSQL.
- **Replicação de mudanças** usando Debezium e Kafka.
- **Processamento de dados** com Python.
- **Persistência** no Data Lake (mIMO - armazenamento em Parquet).
- **Consultas otimizadas** via Trino/Iceberg.

## Tecnologias Utilizadas

- **PostgreSQL + Debezium**: Captura de mudanças nos dados.
- **Kafka**: Streaming de eventos em tempo real.
- **Python**: Coleta e processamento dos dados.
- **mIMO**: Data Lake para armazenamento otimizado.
- **Docker**: Infraestrutura para testes locais.

## Estrutura do Pipeline

1. **Coleta de Dados**
   - API da OpenSky Network fornece dados de tráfego aéreo em tempo real.
   - Dados são armazenados temporariamente no PostgreSQL.

2. **CDC e Streaming**
   - Debezium detecta novas inserções e atualizações.
   - Kafka transmite eventos para o pipeline.

3. **Processamento e Transformação**
   - Python formata e otimiza os dados.
   - Escrita no Data Lake (mIMO) em formato Parquet.

4. **Consulta e Visualização**
   - Trino permite consultas SQL nos dados armazenados.
   - Análises de tráfego aéreo e padrões de voo.

## Autor

Desenvolvido por Rafaella Duarte.




