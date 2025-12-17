"""
GCS Model Loader for Cloud Run

Downloads trained models from Google Cloud Storage on startup.
Supports both local development (models in trained_models/) and
production (models in GCS bucket).

Environment Variables:
    MODEL_BUCKET: GCS bucket name (e.g., "currency-intelligence-models")
    MODEL_PREFIX: Path prefix in bucket (e.g., "trained_models/")
    
If MODEL_BUCKET is not set, falls back to local trained_models/ directory.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import GCS client
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not installed. GCS downloads disabled.")


def is_gcs_configured() -> bool:
    """Check if GCS is configured via environment variables."""
    return bool(os.getenv("MODEL_BUCKET")) and GCS_AVAILABLE


def get_gcs_client() -> Optional["storage.Client"]:
    """Get GCS client. Returns None if not available."""
    if not GCS_AVAILABLE:
        return None
    try:
        # On Cloud Run, this uses the service account automatically
        return storage.Client()
    except Exception as e:
        logger.error(f"Failed to create GCS client: {e}")
        return None


def download_models_from_gcs(
    target_dir: str = "trained_models",
    bucket_name: Optional[str] = None,
    prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download trained models from GCS bucket.
    
    Args:
        target_dir: Local directory to download models to
        bucket_name: GCS bucket name (defaults to MODEL_BUCKET env var)
        prefix: Path prefix in bucket (defaults to MODEL_PREFIX env var)
        
    Returns:
        Dict with download status, files downloaded, and any errors
    """
    result = {
        "success": False,
        "source": "gcs",
        "files_downloaded": [],
        "errors": [],
        "message": ""
    }
    
    # Get bucket config
    bucket_name = bucket_name or os.getenv("MODEL_BUCKET")
    prefix = prefix or os.getenv("MODEL_PREFIX", "trained_models/")
    
    if not bucket_name:
        result["message"] = "MODEL_BUCKET not configured"
        result["source"] = "local"
        return result
    
    if not GCS_AVAILABLE:
        result["errors"].append("google-cloud-storage package not installed")
        result["message"] = "GCS not available"
        return result
    
    try:
        client = get_gcs_client()
        if not client:
            result["errors"].append("Failed to create GCS client")
            return result
        
        bucket = client.bucket(bucket_name)
        
        # Ensure target directory exists
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # List and download all blobs with prefix
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            result["errors"].append(f"No files found in gs://{bucket_name}/{prefix}")
            result["message"] = "No models in GCS bucket"
            return result
        
        downloaded = []
        for blob in blobs:
            # Skip directories
            if blob.name.endswith('/'):
                continue
                
            # Get relative filename
            filename = blob.name.replace(prefix, "").lstrip("/")
            if not filename:
                continue
                
            local_path = target_path / filename
            
            # Create parent directories
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download
            logger.info(f"Downloading {blob.name} to {local_path}")
            blob.download_to_filename(str(local_path))
            downloaded.append(filename)
        
        result["success"] = True
        result["files_downloaded"] = downloaded
        result["message"] = f"Downloaded {len(downloaded)} files from GCS"
        logger.info(f"Successfully downloaded {len(downloaded)} model files from GCS")
        
    except Exception as e:
        result["errors"].append(str(e))
        result["message"] = f"GCS download failed: {e}"
        logger.error(f"GCS download failed: {e}")
    
    return result


def ensure_models_available(
    models_dir: str = "trained_models",
    required_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ensure trained models are available, downloading from GCS if needed.
    
    This is the main function to call on startup.
    
    Args:
        models_dir: Directory containing models
        required_files: List of required files (default: model_registry.json)
        
    Returns:
        Dict with status information
    """
    if required_files is None:
        required_files = ["model_registry.json"]
    
    result = {
        "success": False,
        "source": "unknown",
        "models_dir": models_dir,
        "registry_loaded": False,
        "model_count": 0,
        "errors": []
    }
    
    models_path = Path(models_dir)
    registry_path = models_path / "model_registry.json"
    
    # Check if models already exist locally
    if registry_path.exists():
        logger.info("Models found locally, skipping GCS download")
        result["source"] = "local"
    else:
        # Try to download from GCS
        if is_gcs_configured():
            logger.info("Downloading models from GCS...")
            download_result = download_models_from_gcs(models_dir)
            
            if not download_result["success"]:
                result["errors"].extend(download_result.get("errors", []))
                result["errors"].append("Failed to download models from GCS")
                return result
            
            result["source"] = "gcs"
        else:
            # No GCS and no local models - fail fast
            result["errors"].append(
                "No models found locally and GCS not configured. "
                "Set MODEL_BUCKET and MODEL_PREFIX environment variables, "
                "or ensure trained_models/ directory exists with model files."
            )
            return result
    
    # Validate registry exists
    if not registry_path.exists():
        result["errors"].append(f"model_registry.json not found at {registry_path}")
        return result
    
    # Load and validate registry
    try:
        with open(registry_path) as f:
            registry = json.load(f)
        
        result["registry_loaded"] = True
        
        # Count models
        model_files = list(models_path.glob("*.pkl"))
        result["model_count"] = len(model_files)
        
        if result["model_count"] == 0:
            result["errors"].append("No .pkl model files found")
            return result
        
        # Validate required model files exist
        missing_models = []
        for currency, info in registry.get("active_models", {}).items():
            model_file = info.get("model_path", "")
            if model_file and not (models_path / model_file).exists():
                # Try just the filename
                filename = Path(model_file).name
                if not (models_path / filename).exists():
                    missing_models.append(model_file)
        
        if missing_models:
            result["errors"].append(f"Missing model files: {missing_models}")
            return result
        
        result["success"] = True
        logger.info(f"Models validated: {result['model_count']} files, source={result['source']}")
        
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid model_registry.json: {e}")
    except Exception as e:
        result["errors"].append(f"Error loading registry: {e}")
    
    return result


def upload_models_to_gcs(
    source_dir: str = "trained_models",
    bucket_name: Optional[str] = None,
    prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload trained models to GCS bucket.
    
    This is a helper for deploying models after local training.
    
    Args:
        source_dir: Local directory containing models
        bucket_name: GCS bucket name
        prefix: Path prefix in bucket
        
    Returns:
        Dict with upload status
    """
    result = {
        "success": False,
        "files_uploaded": [],
        "errors": []
    }
    
    bucket_name = bucket_name or os.getenv("MODEL_BUCKET")
    prefix = prefix or os.getenv("MODEL_PREFIX", "trained_models/")
    
    if not bucket_name:
        result["errors"].append("MODEL_BUCKET not set")
        return result
    
    if not GCS_AVAILABLE:
        result["errors"].append("google-cloud-storage not installed")
        return result
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        
        source_path = Path(source_dir)
        
        # Upload all files
        for file_path in source_path.iterdir():
            if file_path.is_file() and (file_path.suffix in ['.pkl', '.json']):
                blob_name = f"{prefix.rstrip('/')}/{file_path.name}"
                blob = bucket.blob(blob_name)
                
                logger.info(f"Uploading {file_path} to gs://{bucket_name}/{blob_name}")
                blob.upload_from_filename(str(file_path))
                result["files_uploaded"].append(file_path.name)
        
        result["success"] = True
        logger.info(f"Uploaded {len(result['files_uploaded'])} files to GCS")
        
    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"GCS upload failed: {e}")
    
    return result
