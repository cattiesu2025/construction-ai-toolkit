"""APScheduler-based runner — runs the delay agent for all active projects on a schedule."""
import json
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from delay_agent import config
from delay_agent.agent import run_delay_agent
from core_tools import data_layer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run_all_projects() -> None:
    projects = data_layer.projects()
    project_ids = projects["project_id"].tolist()
    log.info(f"Starting delay scan for {len(project_ids)} projects")

    for project_id in project_ids:
        try:
            log.info(f"Scanning {project_id}...")
            result = run_delay_agent(project_id)
            log.info(
                f"{project_id} done — {result['iterations']} iterations, "
                f"${result['token_usage']['estimated_cost_usd']:.4f}, "
                f"{result['elapsed_seconds']}s"
            )
            log.info(f"{project_id} summary: {result['summary'][:200]}")
        except Exception as exc:
            log.error(f"Agent failed for {project_id}: {exc}")


def main() -> None:
    scheduler = BlockingScheduler()
    cron_parts = config.SCHEDULE_CRON.split()
    trigger = CronTrigger(
        minute=cron_parts[0],
        hour=cron_parts[1],
        day=cron_parts[2],
        month=cron_parts[3],
        day_of_week=cron_parts[4],
    )
    scheduler.add_job(run_all_projects, trigger)
    log.info(f"Scheduler started — cron: {config.SCHEDULE_CRON}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
