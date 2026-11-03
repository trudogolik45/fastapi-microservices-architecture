import json
import os
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
ORDER_QUEUE = "order_events"

# Mock database for inventory
inventory_db = {
    99: {"name": "Super Fast Laptop", "stock": 10},
}


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    try:
        event_data = json.loads(message.body.decode())
        print(f"Received event: {event_data}")

        product_id = event_data.get("product_id")

        # Simulate a fatal error
        if product_id == 999:
            print("Fatal error: simulated crash! Rejecting message.")
            # Reject the message and do NOT requeue it.
            # This triggers the Dead Letter Exchange (DLX).
            await message.reject(requeue=False)
            return

        # Normal business logic
        if product_id in inventory_db and inventory_db[product_id]["stock"] > 0:
            inventory_db[product_id]["stock"] -= 1
            print(
                f"Stock reduced! Remaining stock for product {product_id}: "
                f"{inventory_db[product_id]['stock']}"
            )
        else:
            print(f"Out of stock or invalid product: {product_id}")

        # Manually acknowledge the message was processed successfully
        await message.ack()
    except Exception as e:
        print(f"Error processing message: {e}")
        # If any Python error occurs, safely dead-letter the message
        await message.reject(requeue=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Connect to RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # 2. Declare the dead letter exchange (DLX) and dead letter queue (DLQ)
    dlx = await channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
    dlq = await channel.declare_queue(f"{ORDER_QUEUE}_dlq", durable=True)
    await dlq.bind(dlx, routing_key=ORDER_QUEUE)

    # 3. Declare the main queue and tell it to route failures to the DLX
    arguments = {
        "x-dead-letter-exchange": "dlx",
        "x-dead-letter-routing-key": ORDER_QUEUE,
    }
    queue = await channel.declare_queue(ORDER_QUEUE, durable=True, arguments=arguments)

    # 4. Consume messages
    await queue.consume(process_message)
    print("Inventory Service is now listening for order events...")

    yield

    await connection.close()


app = FastAPI(lifespan=lifespan)


# A simple endpoint to check current stock
@app.get("/inventory/{product_id}")
def get_stock(product_id: int):
    return inventory_db.get(product_id, {"error": "Product not found"})
