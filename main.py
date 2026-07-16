import os
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import (
    airline,
    flight,
    flight_price_history,
    subscription,
    airport,
    user,
)
from app.services.scraper_scheduler import create_scraper_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Main backend service starting up...")
    scraper_scheduler = create_scraper_scheduler()
    scraper_scheduler.start()
    logger.info("Hourly scraper scheduler started.")
    try:
        yield
    finally:
        scraper_scheduler.shutdown(wait=False)
        logger.info("Hourly scraper scheduler stopped.")
    logger.info("🛑 Main backend service shutting down.")


app = FastAPI(lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping():
    return {"status": "alive"}


app.include_router(user.router)
app.include_router(airline.router)
app.include_router(flight.router)
app.include_router(flight_price_history.router)
app.include_router(subscription.router)
app.include_router(airport.router)
