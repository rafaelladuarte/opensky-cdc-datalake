from confluent_kafka import Consumer, KafkaError
import config

def create_consumer():
    """Cria e configura a instância do consumidor Kafka."""
    conf = {
        'bootstrap.servers': config.KAFKA_BROKER,
        'group.id': config.KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }

    print(f"[{config.KAFKA_GROUP_ID}] Conectando ao Kafka: {config.KAFKA_BROKER}")
    consumer = Consumer(conf)
    consumer.subscribe([config.KAFKA_TOPIC])
    return consumer
