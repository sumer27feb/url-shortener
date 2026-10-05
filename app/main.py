from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from app.cache.redis import close_redis
from app.api.links import router as links_router
from app.api.redirects import router as redirects_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()

app = FastAPI(
    lifespan=lifespan,
)

app.include_router(links_router)
app.include_router(redirects_router)

@app.get("/")
def home():
    return {"message" : "URL shortener server is running"}

#python -m uvicorn app.main:app --reload