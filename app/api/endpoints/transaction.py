from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.exceptions import InvalidTransactionAmountError
from app.core.logger import logger
from app.dependencies import get_transaction_service
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionRequest, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Transactions"],
    responses={
        200: {"description": "Transação já existente retornada"},
        201: {"description": "Transação criada com sucesso"},
        400: {"description": "Valor de transação inválido"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def create_transaction(
    request: TransactionRequest,
    response: Response,
    service: TransactionService = Depends(get_transaction_service),
):
    logger.info(f"Requisição de transação recebida, external_id={request.external_id}")

    transaction = Transaction(
        external_id=request.external_id,
        amount=request.amount,
        kind=request.kind,
        account_id=request.account_id,
    )

    try:
        transaction, created = await service.create_transaction(transaction)

        if not created:
            response.status_code = status.HTTP_200_OK

        return TransactionResponse.model_validate(transaction)
    except InvalidTransactionAmountError:
        logger.error(
            f"Valor de transação inválido, external_id={request.external_id}, amount={request.amount}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor de transação deve ser maior que zero",
        )
    except Exception as e:
        logger.error(
            f"Erro ao processar transação, external_id={request.external_id}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar transação",
        )
