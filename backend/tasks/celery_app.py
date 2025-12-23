"""
Celery Application Configuration

Uses SQLite as the message broker (no Redis required).
For production, consider using Redis.
"""

import os
from celery import Celery

# Celery configuration
# Using SQLite as broker for simplicity (works without Redis)
BROKER_URL = os.getenv('CELERY_BROKER_URL', 'sqla+sqlite:///celery_broker.db')
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'db+sqlite:///celery_results.db')

# Create Celery app
celery_app = Celery(
    'eis_newsletter',
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=['tasks.newsletter_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'send-scheduled-newsletters': {
            'task': 'tasks.newsletter_tasks.send_scheduled_newsletters',
            'schedule': 3600.0,  # Every hour
        },
        'refresh-stale-cache': {
            'task': 'tasks.newsletter_tasks.refresh_stale_cache',
            'schedule': 7200.0,  # Every 2 hours
        },
    }
)

# For environments without Celery, provide a synchronous fallback
class SyncTaskRunner:
    """Synchronous task runner for when Celery is not available."""
    
    @staticmethod
    def run_sync(task_func, *args, **kwargs):
        """Run a task synchronously."""
        return task_func(*args, **kwargs)


def get_celery_app():
    """Get the Celery app instance."""
    return celery_app
