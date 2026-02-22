from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Transaction Service",
    description="Serviço para gerenciamento de transações financeiras",
)

app.include_router(router)
