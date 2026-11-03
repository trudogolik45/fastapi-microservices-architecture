import json
import os
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
ORDER_QUEUE = "order_events"

# Global connection variable
rabbitmq_connection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection
    # Connect to RabbitMQ container
    rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    print("Connected to RabbitMQ!")

    # The queue (with its dead-letter settings) is declared by the inventory
    # service. Redeclaring it here without the same arguments would fail.
    yield
    # Cleanup on shutdown
    await rabbitmq_connection.close()


app = FastAPI(lifespan=lifespan)


@app.post("/orders/")
async def place_order(product_id: int, user_id: int):
    # 1. Create the event data
    order_event = {
        "event": "OrderPlaced",
        "product_id": product_id,
        "user_id": user_id,
        "status": "pending",
    }

    # 2. Publish to RabbitMQ
    async with rabbitmq_connection.channel() as channel:
        message = aio_pika.Message(body=json.dumps(order_event).encode())
        await channel.default_exchange.publish(message, routing_key=ORDER_QUEUE)

    # 3. Return instantly!
    return {"message": "Order received and is being processed in the background."}
