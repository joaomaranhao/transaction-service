import json
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.core.config import settings


class RabbitMQPublisher:
    _connection: Optional[AbstractRobustConnection] = None
    _channel: Optional[AbstractChannel] = None

    @classmethod
    async def get_channel(cls) -> AbstractChannel:
        if cls._connection is None or cls._connection.is_closed:
            cls._connection = await aio_pika.connect_robust(settings.rabbitmq_url)

        if cls._channel is None or cls._channel.is_closed:
            cls._channel = await cls._connection.channel()
            await cls._channel.declare_queue("transactions", durable=True)

        return cls._channel

    @classmethod
    async def close(cls) -> None:
        if cls._channel and not cls._channel.is_closed:
            await cls._channel.close()
        if cls._connection and not cls._connection.is_closed:
            await cls._connection.close()
        cls._channel = None
        cls._connection = None


async def publish_transaction(transaction_id: int):
    channel = await RabbitMQPublisher.get_channel()

    message = aio_pika.Message(
        body=json.dumps({"transaction_id": transaction_id}).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await channel.default_exchange.publish(
        message,
        routing_key="transactions",
    )
