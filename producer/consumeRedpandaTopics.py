import json
from confluent_kafka import Consumer

def main():
    # 1. Configure the Consumer
    conf = {
        'bootstrap.servers': '127.0.0.1:19092', # Change to your Docker-mapped port
        'broker.address.family': 'v4',
        'group.id': 'materialize-reader',
        'auto.offset.reset': 'earliest'         # Start from the beginning of the view
    }

    freight_jobs_consumer = Consumer(conf)
    freight_jobs_consumer.subscribe(['freight_jobs'])     # Use the topic from your CREATE SINK

    # freight_shipment_consumer = Consumer(conf)
    # freight_shipment_consumer.subscribe(['freight_shipment'])     # Use the topic from your CREATE SINK
        
    # freight_freight_consumer = Consumer(conf)
    # freight_freight_consumer.subscribe(['freight_freight'])     # Use the topic from your CREATE SINK

    # freight_invoice_consumer = Consumer(conf)
    # freight_invoice_consumer.subscribe(['freight_invoice'])     # Use the topic from your CREATE SINK

    # freight_purchaseorder_consumer = Consumer(conf)
    # freight_purchaseorder_consumer.subscribe(['freight_purchaseorder'])     # Use the topic from your CREATE SINK

    print("Reading from Redpanda... Press Ctrl+C to stop.")

    try:
        while True:
            msg = freight_jobs_consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Freight_jobs_consumer error: {msg.error()}")
                continue

            # Decode the Key (The unique ID from your SINK)
            key = msg.key().decode('utf-8') if msg.key() else "No Key"
            
            # Decode the Value (The Row Data)
            if msg.value() is None:
                # This is a "Tombstone" - the row was deleted in Materialize
                print(f"\nDELETE: Row with Key {key} was removed.")
            else:
                data = json.loads(msg.value().decode('utf-8'))
                print(f"\nUPDATE/INSERT: Key {key} | Data: {data}")

    except KeyboardInterrupt:
        pass
    finally:
        freight_jobs_consumer.close()

if __name__ == '__main__':
    main()