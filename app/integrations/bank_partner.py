import asyncio
import uuid

from app.core.logger import logger


async def bank_partner_request(
    external_id: uuid.UUID,
    amount: float,
    kind: str,
) -> str:
    """Simula integração com banco parceiro."""
    logger.info(
        f"Enviando requisição para banco parceiro, external_id={external_id}, amount={amount}, kind={kind}"
    )
    await asyncio.sleep(0.2)

    return str(uuid.uuid4())
