import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone

import boto3
import pandas as pd

import config

logger = logging.getLogger(__name__)

_s3_client = None


def get_s3_client():
    """Cliente S3/MinIO criado sob demanda."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name='us-east-1'  # Exigido pelo boto3, ignorado pelo MinIO
        )
    return _s3_client


def extract_payload(message_value):
    """
    Decodifica a mensagem do Kafka (JSON Debezium) e extrai o campo 'after'.
    Retorna o dicionário de dados ou None se for uma exclusão/tombstone.
    """
    if not message_value:
        return None

    try:
        data = json.loads(message_value.decode('utf-8'))
        payload = data.get('payload', data)  # Às vezes o Debezium vem com wrap de schema

        if payload.get('op') == 'd':
            return None

        return payload.get('after')
    except Exception as e:
        logger.error("Erro ao parsear a mensagem: %s", e)
        return None


def event_dates(df):
    """
    Data do evento de cada registro (UTC), a partir de last_contact (epoch s),
    com fallback para time_position e time (snapshot). Sem nenhum, usa a data atual.
    """
    ts = pd.Series(float('nan'), index=df.index, dtype='float64')
    for col in ('last_contact', 'time_position', 'time'):
        if col in df.columns:
            ts = ts.fillna(pd.to_numeric(df[col], errors='coerce'))
    dates = pd.to_datetime(ts, unit='s', utc=True, errors='coerce')
    return dates.fillna(pd.Timestamp.now(tz=timezone.utc))


def process_batch(messages):
    """
    Converte as mensagens em DataFrame e grava Parquet no MinIO, particionado
    por data do evento (year=/month=/day=). Retorna a lista de chaves S3 gravadas.
    Levanta exceção em caso de falha.
    """
    if not messages:
        return []

    df = pd.DataFrame(messages)
    df = df.replace('NaN', float('nan'))

    dates = event_dates(df)
    keys = []
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    for day, part in df.groupby(dates.dt.strftime("year=%Y/month=%m/day=%d")):
        filename = f"opensky_states_{timestamp_str}_{uuid.uuid4().hex[:8]}.parquet"
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        s3_key = f"{config.MINIO_PREFIX}{day}/{filename}"
        try:
            part.to_parquet(temp_path, index=False, engine='pyarrow')
            logger.info("Upload de %d registros para s3://%s/%s",
                        len(part), config.MINIO_BUCKET, s3_key)
            get_s3_client().upload_file(temp_path, config.MINIO_BUCKET, s3_key)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        keys.append(s3_key)

    return keys
