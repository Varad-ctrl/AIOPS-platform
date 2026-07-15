"""
Runs AlertService.evaluate_thresholds() on a fixed interval so alerts fire
even without Alertmanager configured (e.g. local dev). In production,
Alertmanager's own rule evaluation (monitoring/prometheus/alert_rules.yml)
is the primary path via the /alerts/webhook receiver; this poller is a
lightweight, dependency-free backstop.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.logging_config import get_logger
from app.db.session import SessionLocal
from app.services.alert_service import AlertService

logger = get_logger("scheduler")

scheduler = AsyncIOScheduler()

POLL_INTERVAL_SECONDS = 60


async def poll_thresholds() -> None:
    db = SessionLocal()
    try:
        notify_email = settings.SMTP_FROM_EMAIL if settings.SMTP_HOST else None
        service = AlertService(db, notify_email=notify_email)
        raised = await service.evaluate_thresholds()
        if raised:
            logger.info("threshold_poll_raised_alerts", count=len(raised))
    except Exception as exc:  # never let the scheduler die
        logger.error("threshold_poll_failed", error=str(exc))
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        poll_thresholds,
        "interval",
        seconds=POLL_INTERVAL_SECONDS,
        id="threshold_poll",
        next_run_time=None,  # first run waits one interval; avoids startup race with DB migrations
    )
    scheduler.start()
    logger.info("scheduler_started", interval_seconds=POLL_INTERVAL_SECONDS)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
