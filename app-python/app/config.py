import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "opensky.public.opensky_api_states_all")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "python-parquet-consumer")

# Configurações do MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datalake")
MINIO_PREFIX = os.getenv("MINIO_PREFIX", "silver/opensky/")

# Parâmetros de Lote (Batching)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
BATCH_TIMEOUT_SEC = int(os.getenv("BATCH_TIMEOUT_SEC", "30"))
