from app.api.routes import router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="rag-eval-lab",
    description="Grounded QA and evaluation scaffold for public document corpora.",
    version="0.1.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
