from fastapi import FastAPI
import pika

app = FastAPI()
payments = []

def callback(ch, method, properties, body):
    order = body.decode()
    payments.append({"order": order, "status": "paid"})
    print(f"Processed payment for order: {order}")

@app.on_event("startup")
def startup_event():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='orders')
    channel.basic_consume(queue='orders', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@app.get("/payments")
def list_payments():
    return {"payments": payments}
