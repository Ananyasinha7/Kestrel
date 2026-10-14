from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from src.engine import Engine

STATIC = Path(__file__).parent / "static"


class Order(BaseModel):
    model_config = ConfigDict(extra="allow")

    order_id: str | int
    order_placed_at: str | None = None
    customer_id: str | int | None = None
    sku: str
    sales_channel: str
    payment_mode: str
    discount_pct: float = Field(0, ge=0, le=100)
    qty: int = Field(1, ge=1)
    order_value_inr: float | None = Field(None, ge=0)
    promised_delivery_days: int | None = Field(None, ge=0)
    delivery_pincode: str | int | None = None
    is_gift: bool = False
    is_shield: bool | None = None
    customer_prior_orders: int | None = Field(None, ge=0)
    customer_prior_returns: int | None = Field(None, ge=0)
    delivery_note: str | None = None


class Reason(BaseModel):
    factor: str
    direction: str
    text: str


class ScoreResponse(BaseModel):
    order_id: str | int | None
    score: float
    risk_tier: str
    action: str
    reasons: list[Reason]
    data_warnings: list[str]
    model_version: str


@lru_cache
def get_engine():
    try:
        return Engine.load()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


app = FastAPI(title="Kestrel Home return risk")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(RequestValidationError)
async def invalid_request(_, exc):
    details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The order could not be read. Check the listed fields.",
                "details": details,
            }
        },
    )


@app.get("/")
def screen():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health(engine: Engine = Depends(get_engine)):
    return {"status": "ok", "model_version": engine.version}


@app.post("/score", response_model=ScoreResponse)
def score(order: Order, engine: Engine = Depends(get_engine)):
    return engine.score([order.model_dump()])[0]
