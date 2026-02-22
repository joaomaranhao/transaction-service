from fastapi import APIRouter, Depends, HTTPException

from app.core.exceptions import AccountNotFoundError
from app.core.logger import logger
from app.dependencies import get_account_service
from app.services.account_services import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/{account_id}/balance")
def get_balance(
    account_id: str,
    service: AccountService = Depends(get_account_service),
):
    try:
        balance = service.get_balance(account_id)

        return {
            "account_id": account_id,
            "balance": balance,
        }
    except AccountNotFoundError:
        raise HTTPException(status_code=404, detail="Account not found")
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
