from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.cache.redis import close_redis
from app.kafka.producer import ClickEventPublisher
from app.api.links import router as links_router
from app.api.redirects import router as redirects_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher = ClickEventPublisher()
    publisher.start()
    print("[KAFKA DEBUG] Producer startup completed", flush=True)

    app.state.click_event_publisher = publisher

    try:
        yield
    finally:
        try:
            await publisher.close()
        finally:
            await close_redis()

app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(links_router)
app.include_router(redirects_router)

@app.get("/")
def home():
    return {"message" : "URL shortener server is running"}

#python -m uvicorn app.main:app --reload
#python -m app.workers.click_flush_worker
#python -m uvicorn app.main:app --port 8001 --loop asyncio:SelectorEventLoop
#python -m uvicorn app.main:app --port 8002 --loop asyncio:SelectorEventLoop
#docker run -d --name url-shortener-nginx -p 127.0.0.1:8080:80 --mount "type=bind,source=%cd%\nginx\default.conf,target=/etc/nginx/conf.d/default.conf,readonly" nginx:stable