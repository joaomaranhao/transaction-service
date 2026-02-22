from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.database import init_db
from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando o serviço de transações...")
    # Inicializa o banco de dados
    init_db()
    yield
    logger.info("Encerrando o serviço de transações...")


app = FastAPI(
    title=settings.app_name,
    description="Serviço para gerenciamento de transações financeiras",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
