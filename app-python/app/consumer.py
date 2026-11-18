import logging

from confluent_kafka import Consumer, Producer

import config

logger = logging.getLogger(__name__)


def create_consumer():
    """Cria e configura a instância do consumidor Kafka."""
    conf = {
        'bootstrap.servers': config.KAFKA_BROKER,
        'group.id': config.KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }

    logger.info("[%s] Conectando ao Kafka: %s", config.KAFKA_GROUP_ID, config.KAFKA_BROKER)
    consumer = Consumer(conf)
    consumer.subscribe([config.KAFKA_TOPIC])
    return consumer


def create_producer():
    """Producer usado para enviar lotes que falharam ao tópico dead-letter."""
    return Producer({'bootstrap.servers': config.KAFKA_BROKER})
