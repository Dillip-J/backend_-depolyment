# utils/storage.py
import os
import uuid
import shutil
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

# ==========================================
# 🚨 CLOUDINARY CONFIGURATION
# ==========================================
# In production, these should be loaded from a .env file using os.getenv()
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)

class StorageEngine:
    def __init__(self):
        # Change this to "s3", "cloudinary", or "local" via Env Vars
        self.provider = os.getenv("STORAGE_PROVIDER", "cloudinary") 

    def upload_file(self, file_bytes: bytes, file_extension: str, folder_name: str) -> str:
        """Universal uploader for any provider"""
        
        # --- CASE 1: CLOUDINARY ---
        if self.provider == "cloudinary":
            try:
                result = cloudinary.uploader.upload(
                    file_bytes, 
                    folder=f"eterna/{folder_name}", 
                    resource_type="auto"
                )
                return result.get("secure_url")
            except Exception as e:
                print(f"Cloudinary Upload Error: {e}")
                return ""

        # --- CASE 2: AWS S3 (Placeholder) ---
        if self.provider == "s3":
            # Just a placeholder if no S3 is actually implemented
            unique_name = f"{uuid.uuid4().hex}.{file_extension}"
            return f"https://my-bucket.s3.amazonaws.com/{folder_name}/{unique_name}"

        # --- CASE 3: LOCAL FALLBACK ---
        unique_name = f"{uuid.uuid4().hex}.{file_extension}"
        path = f"uploads/{folder_name}/{unique_name}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "wb") as buffer:
            buffer.write(file_bytes)
        return f"/{path}"

    def delete_file(self, file_url: str) -> bool:
        """Universal deleter"""
        if not file_url: 
            return False

        # --- CASE 1: CLOUDINARY ---
        if "cloudinary" in file_url or self.provider == "cloudinary":
            try:
                public_id = self._extract_public_id(file_url)
                if public_id:
                    cloudinary.uploader.destroy(public_id)
                return True
            except Exception as e:
                print(f"Cloudinary Delete Error: {e}")
                return False

        # --- CASE 2: LOCAL FALLBACK ---
        if file_url.startswith("/uploads/"):
            local_path = file_url.lstrip("/")
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
                
        return False

    def _extract_public_id(self, url: str) -> str:
        """Helper to get 'folder/filename' from a full Cloudinary URL"""
        parts = url.split('/')
        try:
            upload_index = parts.index("upload")
            path_parts = parts[upload_index + 2:] 
            full_id = "/".join(path_parts)
            return os.path.splitext(full_id)[0]
        except (ValueError, IndexError):
            return ""

# Export a single instance to be used by all your routers
storage = StorageEngine()