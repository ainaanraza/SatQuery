import os
import re
import uuid

from satquery.inputs.raster_loader import load_raster

ALLOWED_EXTENSIONS = (".tif", ".tiff", ".png", ".jpg", ".jpeg")
CHUNK_SIZE = 1024 * 1024


class UploadRejected(ValueError):
    """The upload is not acceptable; the message is safe to show to the client."""


def safe_filename(name: str) -> str:
    """Basename with anything but letters, digits, dot, dash and underscore replaced.

    The original name is kept (rather than a random one) because it may carry the
    acquisition date, e.g. Sentinel/Landsat product names.
    """
    base = os.path.basename(str(name or "").replace("\\", "/"))
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")
    return base[:200] or "upload"


def save_upload(fileobj, filename: str, upload_dir: str, max_bytes: int) -> dict:
    """Stream an uploaded raster to `upload_dir/<id>/<filename>` and confirm it is readable.

    Returns a summary including the server `path` to pass to /analyze. Raises UploadRejected
    (after removing any partial file) for bad extensions, oversize files, or unreadable rasters.
    """
    name = safe_filename(filename)
    if not name.lower().endswith(ALLOWED_EXTENSIONS):
        raise UploadRejected(f"Unsupported file type: {name}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    upload_id = uuid.uuid4().hex
    target_dir = os.path.join(upload_dir, upload_id)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, name)

    try:
        written = 0
        with open(path, "wb") as out:
            while True:
                chunk = fileobj.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise UploadRejected(f"File exceeds the {max_bytes // (1024 * 1024)} MB upload limit.")
                out.write(chunk)
        if written == 0:
            raise UploadRejected("Uploaded file is empty.")
        try:
            image = load_raster(path)
        except Exception as e:
            raise UploadRejected(f"Not a readable raster: {name} ({type(e).__name__})")
    except UploadRejected:
        if os.path.exists(path):
            os.remove(path)
        os.rmdir(target_dir)
        raise

    return {
        "upload_id": upload_id,
        "filename": name,
        "path": path.replace("\\", "/"),
        "size_bytes": written,
        "width": image.width,
        "height": image.height,
        "band_count": image.band_count,
        "crs": image.crs,
        "modality": image.modality,
        "acquisition_time": image.acquisition_time.isoformat() if image.acquisition_time else None,
    }


def is_within_roots(path: str, roots) -> bool:
    """True if `path` (relative paths resolve against the working directory) lies inside one of `roots`."""
    resolved = os.path.realpath(os.path.abspath(path))
    for root in roots:
        root = os.path.realpath(os.path.abspath(root))
        try:
            if os.path.commonpath([resolved, root]) == root:
                return True
        except ValueError:  # different drives on Windows
            continue
    return False
