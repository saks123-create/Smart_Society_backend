import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import HTTPException, UploadFile


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _clean_supabase_url() -> str:
    configured = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    if configured:
        return configured

    database_url = os.getenv("DATABASE_URL", "").strip()
    parsed = urlparse(database_url)
    host = parsed.hostname or ""
    if host.startswith("db.") and host.endswith(".supabase.co"):
        project_ref = host.removeprefix("db.").removesuffix(".supabase.co")
        return f"https://{project_ref}.supabase.co"

    username = parsed.username or ""
    if username.startswith("postgres."):
        project_ref = username.removeprefix("postgres.")
        if project_ref:
            return f"https://{project_ref}.supabase.co"
    return ""


def _supabase_service_key() -> str:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def _complaint_bucket() -> str:
    return os.getenv("SUPABASE_COMPLAINT_IMAGES_BUCKET", "complaint-images").strip()


def _require_supabase_storage_config() -> tuple[str, str, str]:
    supabase_url = _clean_supabase_url()
    service_key = _supabase_service_key()
    bucket = _complaint_bucket()
    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL or Supabase DATABASE_URL")
    if not service_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not bucket:
        missing.append("SUPABASE_COMPLAINT_IMAGES_BUCKET")
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Supabase Storage is not configured: {', '.join(missing)}",
        )
    return supabase_url, service_key, bucket


def _extension_for_upload(upload: UploadFile) -> str:
    content_type = (upload.content_type or "").lower()
    if content_type in ALLOWED_IMAGE_CONTENT_TYPES:
        return ALLOWED_IMAGE_CONTENT_TYPES[content_type]

    suffix = Path(upload.filename or "").suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix

    raise HTTPException(
        status_code=400,
        detail="Only JPG, PNG, or WEBP complaint images are allowed",
    )


def _read_upload_bytes(upload: UploadFile) -> bytes:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    max_mb = int(os.getenv("COMPLAINT_IMAGE_MAX_MB", "5"))
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Complaint image must be {max_mb}MB or smaller",
        )
    return data


def save_complaint_image(resident_id: int, upload: UploadFile) -> str:
    """Upload complaint image to Supabase Storage and return its public URL."""
    ext = _extension_for_upload(upload)
    data = _read_upload_bytes(upload)
    supabase_url, service_key, bucket = _require_supabase_storage_config()
    object_path = f"complaints/resident-{resident_id}/complaint_{uuid4().hex}{ext}"
    upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{object_path}"
    content_type = upload.content_type or "application/octet-stream"

    try:
        response = httpx.post(
            upload_url,
            content=data,
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": content_type,
                "x-upsert": "false",
            },
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Supabase image upload failed: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Supabase image upload failed",
        ) from exc

    return f"{supabase_url}/storage/v1/object/public/{bucket}/{object_path}"
