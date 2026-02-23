import asyncio
import json

import aio_pika
from sqlmodel import Session

from app.core.config import settings
from app.core.database import engine
from app.core.logger import logger
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService


async def main():
    logger.info("Iniciando worker...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    queue = await channel.declare_queue("transactions", durable=True)

    logger.info("Worker conectado ao RabbitMQ, aguardando mensagens...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body)
                transaction_id = data["transaction_id"]
                logger.info(f"Mensagem recebida, transaction_id={transaction_id}")

                with Session(engine) as session:
                    repository = TransactionRepository(session)
                    service = TransactionService(repository)
                    await service.process_transaction(transaction_id)


if __name__ == "__main__":
    asyncio.run(main())
