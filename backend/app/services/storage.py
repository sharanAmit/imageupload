import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile
from backend.app.config import settings

class StorageService(ABC):
    @abstractmethod
    def upload(self, file: UploadFile, storage_key: str) -> str:
        """Uploads a file to the storage provider and returns the storage key or URL."""
        pass

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        """Deletes a file from the storage provider."""
        pass

    @abstractmethod
    def get_url(self, storage_key: str) -> str:
        """Returns the public access URL for a given storage key."""
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """Returns the local file path (mostly for LocalStorage download)."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.UPLOAD_DIR
        # Ensure the base upload directory exists
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, storage_key: str) -> str:
        # Prevent path traversal attacks by resolving key
        clean_key = storage_key.replace("..", "").lstrip("\\/")
        return os.path.join(self.base_dir, clean_key)

    def upload(self, file: UploadFile, storage_key: str) -> str:
        dest_path = self._resolve_path(storage_key)
        # Create directories if they do not exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Write file content
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return storage_key

    def delete(self, storage_key: str) -> bool:
        file_path = self._resolve_path(storage_key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
        return False

    def get_url(self, storage_key: str) -> str:
        # In LocalStorage, we mount the upload folder at '/uploads'
        # So files are accessible via relative path /uploads/{storage_key}
        clean_key = storage_key.replace("\\", "/")
        return f"/uploads/{clean_key}"

    def get_file_path(self, storage_key: str) -> str:
        return self._resolve_path(storage_key)


# Dependency Provider
# In the future, this can check environment configuration and return S3StorageService instead
def get_storage_service() -> StorageService:
    return LocalStorageService()
