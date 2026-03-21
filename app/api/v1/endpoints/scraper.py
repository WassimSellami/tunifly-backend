import asyncio
import sys

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services import scraper_service

router = APIRouter(prefix="/scraper", tags=["scraper"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_scrapers_sync(db: Session):
    """Run in a fresh ProactorEventLoop — safe for Playwright on Windows."""
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            asyncio.gather(
                scraper_service.run_nouvelair_job(db),
                scraper_service.run_tunisair_job(db),
            )
        )
    finally:
        loop.close()


@router.get("/", status_code=202)
async def scrape(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(run_scrapers_sync, db)
    return {"message": "Scraper jobs started in the background."}
