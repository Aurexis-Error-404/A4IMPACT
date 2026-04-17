import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.data.loader import load_dataset
from backend.models.schemas import ErrorBody, ErrorDetail
from backend.routers import commodities, groups, health, insights, series
from backend.store.repository import MissingParam, NotFound

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("krishi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = load_dataset(settings.data_dir)
    app.state.store = store
    log.info(
        "store ready: rows=%d groups=%d commodities=%d",
        len(store.rows),
        len(store.groups),
        sum(len(v) for v in store.commodities_by_group.values()),
    )
    yield


app = FastAPI(title="KrishiCFO Seasonal API", version="0.1.0", lifespan=lifespan)

# CORS MUST be registered before routers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)


def _error(code: str, message: str, status: int) -> JSONResponse:
    body = ErrorBody(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status, content=body.model_dump())


@app.exception_handler(NotFound)
async def _not_found_handler(_: Request, exc: NotFound) -> JSONResponse:
    return _error("NOT_FOUND", exc.message, 404)


@app.exception_handler(MissingParam)
async def _missing_param_handler(_: Request, exc: MissingParam) -> JSONResponse:
    return _error("MISSING_PARAM", exc.message, 400)


@app.exception_handler(RequestValidationError)
async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI raises this for missing/empty required query params too.
    missing = any(err.get("type") == "missing" for err in exc.errors())
    if missing:
        fields = [".".join(str(p) for p in err["loc"][1:]) for err in exc.errors() if err.get("type") == "missing"]
        return _error("MISSING_PARAM", f"Missing required parameter(s): {', '.join(fields)}", 400)
    return _error("INVALID_INPUT", "One or more parameters are invalid.", 422)


@app.exception_handler(Exception)
async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled exception: %s", exc)
    return _error("SERVER_ERROR", "Internal server error.", 500)


app.include_router(health.router)
app.include_router(groups.router)
app.include_router(commodities.router)
app.include_router(series.router)
app.include_router(insights.router)
