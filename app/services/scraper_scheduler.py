import asyncio
import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.session import SessionLocal
from app.services import scraper_service

logger = logging.getLogger(__name__)


async def _run_with_session(scraper_job):
    db = SessionLocal()
    try:
        await scraper_job(db)
    finally:
        db.close()


async def _run_all_scrapers() -> None:
    results = await asyncio.gather(
        _run_with_session(scraper_service.run_nouvelair_job),
        _run_with_session(scraper_service.run_tunisair_job),
        return_exceptions=True,
    )

    for job_name, result in zip(("Nouvelair", "Tunisair"), results):
        if isinstance(result, BaseException):
            logger.error("%s scheduled scraper failed: %r", job_name, result)


def run_scheduled_scrapers() -> None:
    """Run both async scrapers from APScheduler's worker thread."""
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_all_scrapers())
    finally:
        loop.close()


def create_scraper_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scheduled_scrapers,
        trigger=IntervalTrigger(hours=1),
        id="hourly-flight-scrape",
        name="Hourly flight scrape",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=15 * 60,
    )
    return scheduler
