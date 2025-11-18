from typing import List, Optional
import os
import uuid
import json
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import aio_pika
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("service-order")

app = FastAPI(title="service-order")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
RABBIT_EXCHANGE = os.getenv("RABBIT_EXCHANGE", "orders")
RABBIT_ROUTING_KEY = os.getenv("RABBIT_ROUTING_KEY", "order.created")

# in-memory store (substituir por DB em produção)
_orders: List[dict] = []

# RabbitMQ resources
_rabbit_connection: Optional[aio_pika.RobustConnection] = None
_rabbit_channel: Optional[aio_pika.Channel] = None
_rabbit_exchange: Optional[aio_pika.Exchange] = None
_rabbit_lock = asyncio.Lock()


class OrderIn(BaseModel):
    customer_id: str = Field(..., example="cust_123")
    items: List[dict] = Field(..., example=[{"sku": "ABC", "qty": 2}])
    total: float = Field(..., example=123.45)


class Order(OrderIn):
    id: str
    created_at: datetime


async def _connect_rabbitmq():
    global _rabbit_connection, _rabbit_channel, _rabbit_exchange
    async with _rabbit_lock:
        if _rabbit_connection and not _rabbit_connection.is_closed:
            return
        try:
            logger.info("Conectando ao RabbitMQ em %s", RABBITMQ_URL)
            _rabbit_connection = await aio_pika.connect_robust(RABBITMQ_URL)
            _rabbit_channel = await _rabbit_connection.channel()
            _rabbit_exchange = await _rabbit_channel.declare_exchange(
                RABBIT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info("Conectado ao RabbitMQ, exchange=%s", RABBIT_EXCHANGE)
        except Exception as e:
            logger.exception("Falha ao conectar ao RabbitMQ: %s", e)
            # limpar para tentar reconectar depois
            _rabbit_connection = None
            _rabbit_channel = None
            _rabbit_exchange = None


async def _close_rabbitmq():
    global _rabbit_connection
    if _rabbit_connection:
        try:
            await _rabbit_connection.close()
            logger.info("Conexão RabbitMQ fechada")
        except Exception:
            logger.exception("Erro ao fechar conexão RabbitMQ")
    _rabbit_connection = None


async def _publish_order_message(order: dict):
    # tenta garantir conexão; se não conseguir, loga e segue (não falhar o request)
    await _connect_rabbitmq()
    if not _rabbit_exchange:
        logger.warning("RabbitMQ não disponível — mensagem não publicada: %s", order.get("id"))
        return
    try:
        body = json.dumps(order, default=str).encode()
        message = aio_pika.Message(body, content_type="application/json")
        await _rabbit_exchange.publish(message, routing_key=RABBIT_ROUTING_KEY)
        logger.info("Mensagem publicada para order %s", order.get("id"))
    except Exception:
        logger.exception("Erro ao publicar mensagem para order %s", order.get("id"))


@app.on_event("startup")
async def startup_event():
    # tenta conectar mas não falha o app se RabbitMQ ausente
    await _connect_rabbitmq()


@app.on_event("shutdown")
async def shutdown_event():
    await _close_rabbitmq()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/orders", response_model=List[Order])
async def list_orders():
    return _orders


@app.post("/orders", response_model=Order, status_code=201)
async def create_order(order_in: OrderIn):
    order = {
        "id": str(uuid.uuid4()),
        "customer_id": order_in.customer_id,
        "items": order_in.items,
        "total": order_in.total,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _orders.append(order)
    # publica mensagem sem bloquear a resposta (podemos aguardar se preferir)
    asyncio.create_task(_publish_order_message(order))
    return order
