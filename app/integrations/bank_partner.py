import asyncio
import random
import uuid

from app.core.exceptions import BankPartnerError
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

    # Simula erro aleatório do banco parceiro
    if random.random() < 0.3:
        logger.error(
            f"Erro ao processar transação no banco parceiro, external_id={external_id}"
        )
        raise BankPartnerError(
            f"Erro ao processar transação no banco parceiro, external_id={external_id}"
        )

    return str(uuid.uuid4())
