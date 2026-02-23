from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.main import app
from app.models.transaction import Transaction  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    # Mock do publisher para não depender do RabbitMQ
    with patch(
        "app.services.transaction_service.publish_transaction",
        new_callable=AsyncMock,
    ):
        yield TestClient(app)

    app.dependency_overrides.clear()
