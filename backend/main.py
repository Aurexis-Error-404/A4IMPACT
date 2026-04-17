from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Settings
from data.loader import load
from routers import health, commodities, series, insights, recommendation

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = load(settings.data_path)
    yield


app = FastAPI(title="KrishiCFO Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(FileNotFoundError)
async def not_found_handler(_request: Request, exc: FileNotFoundError):
    return JSONResponse(status_code=404, content={"error": "not_found", "detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "bad_request", "detail": str(exc)})


@app.exception_handler(Exception)
async def generic_handler(_request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": str(exc)})


app.include_router(health.router)
app.include_router(commodities.router)
app.include_router(series.router)
app.include_router(insights.router)
app.include_router(recommendation.router)
