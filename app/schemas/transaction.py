import uuid

from pydantic import BaseModel

from app.models.transaction import KindEnum


class TransactionRequest(BaseModel):

    external_id: uuid.UUID
    amount: float
    kind: KindEnum


class TransactionResponse(BaseModel):

    id: int
    status: str

    model_config = {
        "from_attributes": True,
    }
