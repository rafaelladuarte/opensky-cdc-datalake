import json
import uuid
import boto3
import pandas as pd
import tempfile
import os
import config
from datetime import datetime

# Configuração do cliente S3/MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=config.MINIO_ENDPOINT,
    aws_access_key_id=config.MINIO_ACCESS_KEY,
    aws_secret_access_key=config.MINIO_SECRET_KEY,
    region_name='us-east-1' # Required by boto3, but ignored by MinIO
)

def extract_payload(message_value):
    """
    Decodifica a mensagem do Kafka (JSON Debezium) e extrai o campo 'after'.
    Retorna o dicionário de dados ou None se for uma exclusão/tombstone.
    """
    if not message_value:
        return None
        
    try:
        data = json.loads(message_value.decode('utf-8'))
        payload = data.get('payload', data) # Às vezes o Debezium vem com wrap de schema
        
        # Ignora deleções (op == 'd')
        if payload.get('op') == 'd':
            return None
            
        return payload.get('after')
    except Exception as e:
        print(f"Erro ao parsear a mensagem: {e}")
        return None

def process_batch(messages):
    """
    Processa uma lista de mensagens extraídas, converte para DataFrame e
    salva como arquivo Parquet no MinIO.
    Retorna o caminho do arquivo gerado se sucesso, ou levanta uma exceção.
    """
    if not messages:
        return None

    df = pd.DataFrame(messages)
    
    # Tratamento de valores 'NaN' que podem vir como string do Debezium
    df.replace('NaN', float('nan'), inplace=True)
    
    # Prepara o caminho temporário
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = str(uuid.uuid4())[:8]
    filename = f"opensky_states_{timestamp_str}_{file_id}.parquet"
    
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    
    # Escreve como Parquet
    df.to_parquet(temp_path, index=False, engine='pyarrow')
    
    # Organiza em partições por data lógica no S3
    date_path = datetime.now().strftime("year=%Y/month=%m/day=%d")
    s3_key = f"{config.MINIO_PREFIX}{date_path}/{filename}"
    
    try:
        # Verifica se o bucket existe (criar se não existir - opcional)
        # s3_client.head_bucket(Bucket=config.MINIO_BUCKET)
        
        # Upload
        print(f"[{datetime.now().isoformat()}] Fazendo upload de {len(df)} registros para s3://{config.MINIO_BUCKET}/{s3_key}")
        s3_client.upload_file(temp_path, config.MINIO_BUCKET, s3_key)
    except Exception as e:
        print(f"Falha ao enviar arquivo para o MinIO: {e}")
        raise e
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return s3_key
