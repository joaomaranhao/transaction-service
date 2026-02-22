from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Serviço para gerenciamento de transações financeiras",
)

app.include_router(router)
