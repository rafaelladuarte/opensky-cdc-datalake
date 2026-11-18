import json
import logging
import time

import config
from consumer import create_consumer, create_producer
from processor import extract_payload, process_batch

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("opensky-consumer")


def send_to_dlq(producer, batch, error):
    """Envia cada registro do lote ao tópico dead-letter e aguarda a entrega."""
    for record in batch:
        producer.produce(
            config.DLQ_TOPIC,
            value=json.dumps(record, default=str).encode("utf-8"),
            headers={"error": str(error)[:500]},
        )
    remaining = producer.flush(30)
    if remaining:
        raise RuntimeError(f"{remaining} mensagens não entregues ao DLQ")


def flush_batch(batch, consumer, producer):
    """
    Grava o lote no data lake com número limitado de tentativas.
    Esgotadas as tentativas, envia ao DLQ. O offset só é commitado depois do
    upload (ou do DLQ) bem-sucedido -> semântica at-least-once.
    """
    last_error = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            process_batch(batch)
            consumer.commit()
            logger.info("Lote salvo no DataLake e offsets commitados.")
            return
        except Exception as e:
            last_error = e
            logger.warning("Falha ao processar o batch (tentativa %d/%d): %s",
                           attempt, config.MAX_RETRIES, e)
            time.sleep(config.RETRY_BACKOFF_SEC * 2 ** (attempt - 1))

    logger.error("Tentativas esgotadas; enviando %d registros ao DLQ '%s'.",
                 len(batch), config.DLQ_TOPIC)
    send_to_dlq(producer, batch, last_error)  # se falhar, propaga e não commita
    consumer.commit()


def main():
    consumer = create_consumer()
    producer = create_producer()

    batch = []
    last_batch_time = time.time()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is not None:
                if msg.error():
                    logger.error("Consumer error: %s", msg.error())
                    continue

                data = extract_payload(msg.value())
                if data:
                    batch.append(data)

            size_reached = len(batch) >= config.BATCH_SIZE
            timeout_reached = (time.time() - last_batch_time >= config.BATCH_TIMEOUT_SEC
                               and len(batch) > 0)

            if size_reached or timeout_reached:
                reason = "SIZE" if size_reached else "TIMEOUT"
                logger.info("Realizando flush (Razão: %s) - %d mensagens acumuladas.",
                            reason, len(batch))
                flush_batch(batch, consumer, producer)
                batch = []
                last_batch_time = time.time()

    except KeyboardInterrupt:
        logger.info("Encerramento solicitado pelo usuário.")
    finally:
        consumer.close()


if __name__ == "__main__":
    logger.info("Iniciando Consumidor Python OpenSky...")
    main()
