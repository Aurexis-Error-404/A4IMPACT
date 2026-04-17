import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import RateLimitError

from config import Settings
from data.loader import load
from routers import health, commodities, series, insights, recommendation, ws, alerts, demo, profit, dashboard

logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = load(settings.data_path)
    yield


app = FastAPI(title="KrishiCFO Backend", lifespan=lifespan)

_dev_origins = r"http://localhost:\d+"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_origin_regex=_dev_origins if settings.allowed_origin == "http://localhost:3000" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitError)
async def rate_limit_handler(_request: Request, _exc: RateLimitError):
    return JSONResponse(
        status_code=503,
        content={"error": "llm_rate_limited", "detail": "Groq rate limit reached — retry after 60s"},
    )


@app.exception_handler(FileNotFoundError)
async def not_found_handler(_request: Request, exc: FileNotFoundError):
    return JSONResponse(status_code=404, content={"error": "not_found", "detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "bad_request", "detail": str(exc)})


@app.exception_handler(Exception)
async def generic_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "internal_error"})


app.include_router(health.router)
app.include_router(commodities.router)
app.include_router(series.router)
app.include_router(insights.router)
app.include_router(recommendation.router)
app.include_router(ws.router)
app.include_router(alerts.router)
app.include_router(demo.router)
app.include_router(profit.router)
app.include_router(dashboard.router)
