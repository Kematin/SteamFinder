from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from celery_app import app as celery_app
from celery_app import configure_schedule
from config import CONFIG, configure_logger
from src.routes import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    configure_schedule(celery_app)
    yield


app = FastAPI(lifespan=lifespan, title="Steam service")

for router in routes:
    app.include_router(router, prefix="/steam")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.api.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(
        "app:app", host=CONFIG.api.host, port=CONFIG.api.port, reload=CONFIG.debug
    )
