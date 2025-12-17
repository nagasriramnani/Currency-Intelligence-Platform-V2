"""
Cloud Startup Validation for Cloud Run

Validates that the application is ready to serve requests.
Performs model loading, health checks, and fail-fast validation.

This module should be called during FastAPI lifespan startup.
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .gcs_loader import ensure_models_available, is_gcs_configured

logger = logging.getLogger(__name__)

# Global startup state
_startup_status: Dict[str, Any] = {
    "initialized": False,
    "healthy": False,
    "started_at": None,
    "models_loaded": False,
    "model_source": None,
    "model_count": 0,
    "errors": [],
    "warnings": []
}


def validate_startup(
    models_dir: str = "trained_models",
    fail_fast: bool = True
) -> Dict[str, Any]:
    """
    Validate that the application is ready to start.
    
    This should be called during FastAPI lifespan startup.
    Will download models from GCS if configured.
    
    Args:
        models_dir: Directory for trained models
        fail_fast: If True, raise exception on critical errors
        
    Returns:
        Startup status dict
        
    Raises:
        RuntimeError: If fail_fast=True and critical errors occur
    """
    global _startup_status
    
    start_time = time.time()
    _startup_status["started_at"] = datetime.utcnow().isoformat()
    _startup_status["errors"] = []
    _startup_status["warnings"] = []
    
    logger.info("=" * 60)
    logger.info("Starting Currency Intelligence Platform")
    logger.info("=" * 60)
    
    # Check environment
    env_status = _validate_environment()
    if env_status["errors"]:
        _startup_status["errors"].extend(env_status["errors"])
    if env_status["warnings"]:
        _startup_status["warnings"].extend(env_status["warnings"])
    
    # Ensure models are available
    logger.info("Validating trained models...")
    model_result = ensure_models_available(models_dir)
    
    if model_result["success"]:
        _startup_status["models_loaded"] = True
        _startup_status["model_source"] = model_result["source"]
        _startup_status["model_count"] = model_result["model_count"]
        logger.info(f"Models loaded: {model_result['model_count']} from {model_result['source']}")
    else:
        _startup_status["errors"].extend(model_result.get("errors", []))
        logger.error(f"Model loading failed: {model_result.get('errors')}")
    
    # Determine health status
    critical_errors = [e for e in _startup_status["errors"] if "model" in e.lower()]
    
    if critical_errors and fail_fast:
        error_msg = f"STARTUP FAILED: {critical_errors}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    _startup_status["healthy"] = len(critical_errors) == 0
    _startup_status["initialized"] = True
    
    elapsed = time.time() - start_time
    logger.info(f"Startup completed in {elapsed:.2f}s")
    logger.info(f"Health status: {'HEALTHY' if _startup_status['healthy'] else 'DEGRADED'}")
    logger.info("=" * 60)
    
    return _startup_status


def _validate_environment() -> Dict[str, Any]:
    """Validate required environment variables."""
    result = {"errors": [], "warnings": []}
    
    # Required for production
    required_in_cloud = [
        ("SUPABASE_URL", "Database URL"),
        ("SUPABASE_KEY", "Database key"),
    ]
    
    # Optional but recommended
    optional = [
        ("FMP_API_KEY", "Financial Modeling Prep API"),
        ("SLACK_WEBHOOK_URL", "Slack notifications"),
    ]
    
    # Check if running in Cloud Run
    is_cloud_run = os.getenv("K_SERVICE") is not None
    
    if is_cloud_run:
        logger.info("Running in Cloud Run environment")
        
        # In Cloud Run, these are critical
        for var, description in required_in_cloud:
            if not os.getenv(var):
                result["warnings"].append(f"{var} not set - {description} disabled")
    
    # Check optional vars
    for var, description in optional:
        if not os.getenv(var):
            result["warnings"].append(f"{var} not set - {description} disabled")
    
    # Check GCS configuration
    if is_gcs_configured():
        logger.info(f"GCS configured: bucket={os.getenv('MODEL_BUCKET')}")
    else:
        logger.info("GCS not configured, using local models")
    
    return result


def get_startup_status() -> Dict[str, Any]:
    """Get current startup status for health checks."""
    return _startup_status.copy()


def get_health_check() -> Dict[str, Any]:
    """
    Get health check response.
    
    Returns:
        Dict suitable for /health endpoint response
    """
    status = get_startup_status()
    
    # Determine overall health
    if not status["initialized"]:
        health = "starting"
        http_status = 503
    elif status["healthy"]:
        health = "healthy"
        http_status = 200
    else:
        health = "degraded"
        http_status = 200  # Still serving requests
    
    return {
        "status": health,
        "http_status": http_status,
        "initialized": status["initialized"],
        "models_loaded": status["models_loaded"],
        "model_count": status["model_count"],
        "model_source": status["model_source"],
        "started_at": status["started_at"],
        "errors": status["errors"][:5] if status["errors"] else [],  # Limit for response size
        "cloud_run": os.getenv("K_SERVICE") is not None
    }
