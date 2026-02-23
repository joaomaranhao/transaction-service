import asyncio
import json

import aio_pika
from sqlmodel import Session

from app.core.config import settings
from app.core.database import engine
from app.core.logger import logger
from app.messaging.publisher import publish_to_dlq, publish_to_retry
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService


async def main():
    logger.info("Iniciando worker...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    # Configura fila de retry com DLX
    await channel.declare_queue(
        "transactions.retry",
        durable=True,
        arguments={
            "x-message-ttl": settings.retry_ttl_ms,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "transactions",
        },
    )

    # Dead Letter Queue
    await channel.declare_queue("transactions.dlq", durable=True)

    queue = await channel.declare_queue("transactions", durable=True)

    logger.info("Worker conectado ao RabbitMQ, aguardando mensagens...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body)
                transaction_id = data["transaction_id"]

                # Lê contador de retries do header
                retry_count: int = 0
                if message.headers and "x-retry-count" in message.headers:
                    retry_count = int(message.headers["x-retry-count"])  # type: ignore[arg-type]

                logger.info(
                    f"Mensagem recebida, transaction_id={transaction_id}, retry={retry_count}"
                )

                with Session(engine) as session:
                    repository = TransactionRepository(session)
                    service = TransactionService(repository)
                    is_last_attempt = retry_count >= settings.max_retries

                    try:
                        await service.process_transaction(
                            transaction_id, is_last_attempt=is_last_attempt
                        )
                    except Exception as e:
                        logger.error(
                            f"Erro ao processar transaction_id={transaction_id}: {e}"
                        )

                        if not is_last_attempt:
                            logger.info(
                                f"Enviando para retry ({retry_count + 1}/{settings.max_retries}), transaction_id={transaction_id}"
                            )
                            await publish_to_retry(transaction_id, retry_count + 1)
                        else:
                            logger.error(
                                f"Máximo de retries atingido, enviando para DLQ, transaction_id={transaction_id}"
                            )
                            await publish_to_dlq(transaction_id, retry_count, str(e))


if __name__ == "__main__":
    asyncio.run(main())
