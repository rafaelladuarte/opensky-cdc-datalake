import time
from consumer import create_consumer
from processor import extract_payload, process_batch
import config

def main():
    consumer = create_consumer()
    
    batch = []
    last_batch_time = time.time()
    
    try:
        while True:
            # Poll espera até 1.0 segundo por mensagens
            msg = consumer.poll(1.0)
            
            if msg is not None:
                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue
                
                # Extrai a entidade do evento CDC
                data = extract_payload(msg.value())
                if data:
                    batch.append(data)
            
            # Condições de flush do batch:
            # 1. Tamanho do batch atingiu BATCH_SIZE
            # 2. Timeout de espera atingido e há mensagens no batch
            time_since_last_batch = time.time() - last_batch_time
            size_reached = len(batch) >= config.BATCH_SIZE
            timeout_reached = time_since_last_batch >= config.BATCH_TIMEOUT_SEC and len(batch) > 0
            
            if size_reached or timeout_reached:
                reason = "SIZE" if size_reached else "TIMEOUT"
                print(f"Realizando flush (Razão: {reason}) - {len(batch)} mensagens acumuladas.")
                
                try:
                    # Envia para MinIO
                    process_batch(batch)
                    
                    # Comita offsets no Kafka apenas se o upload foi bem-sucedido
                    consumer.commit()
                    print("Lote salvo no DataLake e offsets commitados.")
                except Exception as e:
                    print(f"Falha ao processar o batch. Tentando novamente mais tarde. Erro: {e}")
                    # Não limpamos o batch, nem commitamos, para não perder dados. 
                    # Numa app real, implementaríamos retries ou dead-letter queue.
                    time.sleep(5) # Backoff simples
                    continue
                
                # Reseta estado do batch
                batch = []
                last_batch_time = time.time()
                
    except KeyboardInterrupt:
        print("Encerramento solicitado pelo usuário.")
    finally:
        consumer.close()

if __name__ == "__main__":
    print("Iniciando Consumidor Python OpenSky...")
    main()
