import os
import uuid
import logging

logger = logging.getLogger("trader-storefront")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


def upload_image(file_bytes: bytes, folder: str = "trader-storefront") -> str:
    """Save image locally and return the URL path.

    Tries Cloudinary first if credentials are set.
    Falls back to local file storage.
    """
    # Check if Cloudinary is configured
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    if cloud_name:
        return _upload_cloudinary(file_bytes, folder)
    return _upload_local(file_bytes, folder)


def _upload_cloudinary(file_bytes: bytes, folder: str) -> str:
    import io
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
        api_key=os.getenv("CLOUDINARY_API_KEY", ""),
        api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
        secure=True,
    )
    result = cloudinary.uploader.upload(
        io.BytesIO(file_bytes),
        folder=folder,
        transformation=[{"quality": "auto", "fetch_format": "auto"}],
    )
    return result["secure_url"]


def _upload_local(file_bytes: bytes, folder: str) -> str:
    """Save image to local uploads/ folder and return a URL path."""
    import uuid

    # Create folder structure: uploads/<folder>/
    save_dir = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(save_dir, exist_ok=True)

    # Generate unique filename
    ext = ".jpg"
    filename = str(uuid.uuid4())[:8] + ext
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    # Return URL path that the browser can access
    url = f"/uploads/{folder}/{filename}"
    logger.info(f"Saved image locally: {filepath}")
    return url
