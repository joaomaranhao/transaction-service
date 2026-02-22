import uuid
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class KindEnum(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Transaction(SQLModel, table=True):
    __tablename__: str = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: uuid.UUID = Field(index=True)
    amount: float
    kind: KindEnum
    status: str = Field(default="pending")
