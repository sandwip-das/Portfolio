import os
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

CLOUDINARY_DB_PUBLIC_ID = "sqlite_db/db.sqlite3"


def get_db_path():
    """Return the absolute path to the local SQLite database file."""
    db_config = settings.DATABASES.get("default", {})
    db_name = db_config.get("NAME")
    if db_name:
        return Path(db_name)
    return settings.BASE_DIR / "db.sqlite3"


def upload_db_to_cloudinary(db_path=None, public_id=CLOUDINARY_DB_PUBLIC_ID):
    """
    Uploads local db.sqlite3 to Cloudinary media storage.
    """
    import cloudinary.uploader

    if db_path is None:
        db_path = get_db_path()

    if not os.path.exists(db_path):
        logger.warning(f"SQLite database file not found at {db_path}. Skipping Cloudinary upload.")
        return False

    try:
        result = cloudinary.uploader.upload(
            str(db_path),
            public_id=public_id,
            resource_type="raw",
            overwrite=True,
            invalidate=True
        )
        logger.info(f"SQLite DB successfully backed up to Cloudinary: {result.get('secure_url')}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload SQLite DB to Cloudinary: {e}")
        return False


def download_db_from_cloudinary(db_path=None, public_id=CLOUDINARY_DB_PUBLIC_ID):
    """
    Downloads db.sqlite3 from Cloudinary media storage if present.
    """
    import cloudinary.api
    import urllib.request

    if db_path is None:
        db_path = get_db_path()

    try:
        # Get resource metadata from Cloudinary
        resource = cloudinary.api.resource(public_id, resource_type="raw")
        url = resource.get("secure_url") or resource.get("url")

        if url:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, str(db_path))
            logger.info(f"SQLite DB successfully restored from Cloudinary: {url}")
            return True
    except Exception as e:
        logger.warning(f"Could not download SQLite DB from Cloudinary (might not exist yet): {e}")

    return False
