import re
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
from app.config import settings

SAFE_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

def validate_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False

def sanitize_filename(filename: str) -> str:
    # Strip any directory components
    clean_name = Path(filename).name
    # Replace spaces and unusual characters with underscore
    clean_name = re.sub(r"[^\w\.\-]", "_", clean_name)
    # Remove leading dots to prevent hidden files
    clean_name = clean_name.lstrip(".")
    if not clean_name:
        clean_name = f"image_{uuid.uuid4().hex[:8]}.jpg"
    return clean_name

def get_project_dir(project_id: str) -> Path:
    if not validate_uuid(project_id):
        raise ValueError(f"Invalid UUID: {project_id}")
    project_dir = settings.UPLOADS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir

async def save_uploaded_image(project_id: str, upload_file: UploadFile) -> tuple[str, Path]:
    """
    Validates and saves an uploaded image into the project's directory.
    Returns: (safe_filename, absolute_path)
    """
    raw_filename = upload_file.filename or "image.jpg"
    ext = Path(raw_filename).suffix.lower()
    
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed: {list(settings.ALLOWED_IMAGE_EXTENSIONS)}",
        )

    project_dir = get_project_dir(project_id)
    safe_name = sanitize_filename(raw_filename)
    
    # Avoid collisions
    target_path = project_dir / safe_name
    counter = 1
    stem = Path(safe_name).stem
    while target_path.exists():
        target_path = project_dir / f"{stem}_{counter}{ext}"
        counter += 1
    safe_name = target_path.name

    # Save to disk while checking size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_size = 0
    with open(target_path, "wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > max_bytes:
                target_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
                )
            f.write(chunk)

    # Validate that it's a genuine readable image using Pillow
    try:
        with Image.open(target_path) as img:
            img.verify()
    except Exception as e:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file is corrupted or not a valid image format: {str(e)}",
        )

    return safe_name, target_path

def cleanup_project_dir(project_id: str):
    try:
        project_dir = get_project_dir(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir)
    except Exception:
        pass
