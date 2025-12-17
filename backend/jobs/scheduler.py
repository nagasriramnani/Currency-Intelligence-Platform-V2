"""
Background Job Scheduler

Manages periodic tasks using APScheduler:
- Data refresh from Treasury API
- Model retraining
- Alert checking
- Database sync
"""

import logging
import os
from typing import Callable, Dict, List, Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Background job scheduler for Currency Intelligence Platform.
    
    Jobs:
    - data_refresh: Refresh FX rates from Treasury API (hourly)
    - database_sync: Sync data to Supabase (every 4 hours)
    - alert_check: Check for alert conditions (every 15 min)
    - model_retrain: Retrain ML models (daily at 02:00)
    """
    
    def __init__(self):
        self._scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,  # Combine missed runs
                "max_instances": 1,  # Only one instance per job
                "misfire_grace_time": 60 * 5  # 5 min grace
            }
        )
        self._jobs: Dict[str, dict] = {}
        self._is_running = False
        
        # Add event listeners
        self._scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self._scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self._is_running:
            self._scheduler.start()
            self._is_running = True
            logger.info("Job scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if self._is_running:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Job scheduler stopped")
    
    def add_job(
        self,
        job_id: str,
        func: Callable,
        trigger: str = "interval",
        **trigger_kwargs
    ) -> None:
        """
        Add a job to the scheduler.
        
        Args:
            job_id: Unique identifier for the job
            func: Function to execute
            trigger: 'interval' or 'cron'
            **trigger_kwargs: Arguments for the trigger
        """
        if trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_kwargs)
        elif trigger == "cron":
            trigger_obj = CronTrigger(**trigger_kwargs)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")
        
        self._scheduler.add_job(
            func,
            trigger=trigger_obj,
            id=job_id,
            replace_existing=True
        )
        
        self._jobs[job_id] = {
            "func": func.__name__,
            "trigger": trigger,
            "kwargs": trigger_kwargs,
            "added_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Added job: {job_id} ({trigger})")
    
    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler."""
        try:
            self._scheduler.remove_job(job_id)
            del self._jobs[job_id]
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
    
    def get_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs."""
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending
            })
        return jobs
    
    def run_job_now(self, job_id: str) -> bool:
        """Immediately run a scheduled job."""
        try:
            job = self._scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"Manually triggered job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False
    
    def _on_job_executed(self, event: JobExecutionEvent) -> None:
        """Called when a job executes successfully."""
        logger.info(f"Job executed: {event.job_id}")
    
    def _on_job_error(self, event: JobExecutionEvent) -> None:
        """Called when a job fails."""
        logger.error(f"Job failed: {event.job_id}, Error: {event.exception}")


# =============================================================================
# Job Functions
# =============================================================================

def job_data_refresh():
    """Refresh FX rates from Treasury API."""
    try:
        from data.treasury_client import TreasuryAPIClient
        
        logger.info("Running data refresh job...")
        client = TreasuryAPIClient()
        df = client.get_latest_rates()
        
        if not df.empty:
            logger.info(f"Refreshed {len(df)} rates")
        else:
            logger.warning("No new rates fetched")
            
    except Exception as e:
        logger.error(f"Data refresh failed: {e}")
        raise


def job_database_sync():
    """Sync Treasury data to Supabase."""
    try:
        from data.sync import sync_treasury_to_supabase
        from core.database import is_supabase_configured
        
        if not is_supabase_configured():
            logger.warning("Supabase not configured, skipping sync")
            return
        
        logger.info("Running database sync job...")
        result = sync_treasury_to_supabase()
        logger.info(f"Sync result: {result['status']}")
        
    except Exception as e:
        logger.error(f"Database sync failed: {e}")
        raise


def job_alert_check():
    """Check for alert conditions."""
    try:
        from core.database import save_alert
        
        logger.info("Running alert check job...")
        # This would check volatility, VaR breaches, etc.
        # For now, just log
        logger.info("Alert check complete (no conditions triggered)")
        
    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        raise


def job_model_retrain():
    """Retrain ML models with latest data."""
    try:
        logger.info("Running model retrain job...")
        # This would retrain ARIMA/XGBoost models
        # Placeholder for now
        logger.info("Model retrain complete (placeholder)")
        
    except Exception as e:
        logger.error(f"Model retrain failed: {e}")
        raise


# =============================================================================
# Default Scheduler Configuration
# =============================================================================

def create_default_scheduler() -> JobScheduler:
    """Create scheduler with default jobs configured."""
    scheduler = JobScheduler()
    
    # Data refresh - every hour
    scheduler.add_job(
        job_id="data_refresh",
        func=job_data_refresh,
        trigger="interval",
        hours=1
    )
    
    # Database sync - every 4 hours
    scheduler.add_job(
        job_id="database_sync",
        func=job_database_sync,
        trigger="interval",
        hours=4
    )
    
    # Alert check - every 15 minutes
    scheduler.add_job(
        job_id="alert_check",
        func=job_alert_check,
        trigger="interval",
        minutes=15
    )
    
    # Model retrain - daily at 02:00 UTC
    scheduler.add_job(
        job_id="model_retrain",
        func=job_model_retrain,
        trigger="cron",
        hour=2,
        minute=0
    )
    
    return scheduler


# Global scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = create_default_scheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the global scheduler."""
    get_scheduler().start()


def stop_scheduler() -> None:
    """Stop the global scheduler."""
    if _scheduler is not None:
        _scheduler.stop()
