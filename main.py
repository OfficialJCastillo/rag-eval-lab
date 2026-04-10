from app.api.routes import router
from fastapi import FastAPI


app = FastAPI(
    title="rag-eval-lab",
    description="Grounded QA and evaluation scaffold for public document corpora.",
    version="0.1.0",
)
app.include_router(router)

