from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.logger import logger
from app.models.transaction import Transaction  # noqa: F401

engine = create_engine(settings.database_url, echo=False)


def init_db():
    logger.info("Inicializando o banco de dados...")
    SQLModel.metadata.create_all(engine)
    logger.info(f"Tabelas criadas: {list(SQLModel.metadata.tables.keys())}")
    logger.info("Banco de dados inicializado com sucesso!")


def get_session():
    with Session(engine) as session:
        yield session
