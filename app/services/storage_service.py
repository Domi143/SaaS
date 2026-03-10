from __future__ import annotations

import os
import pathlib
import secrets
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import settings


@dataclass(frozen=True)
class StoredFile:
    path: str
    size_bytes: int
    content_type: str | None
    original_name: str


class StorageService:
    """
    MVP: local filesystem storage.
    Production: swap implementation to S3/R2/B2 behind this interface.
    """

    def __init__(self) -> None:
        if settings.file_storage_backend != "local":
            raise NotImplementedError("Only local storage backend is implemented in MVP")
        self.base_path = pathlib.Path(settings.file_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _user_root(self, user_id: int) -> pathlib.Path:
        p = self.base_path / f"user_{user_id}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    async def save_upload(self, user_id: int, upload: UploadFile) -> StoredFile:
        user_root = self._user_root(user_id)
        safe_name = secrets.token_hex(16)
        ext = pathlib.Path(upload.filename or "").suffix[:10]
        filename = f"{safe_name}{ext}"
        dest = user_root / filename

        size = 0
        with dest.open("wb") as f:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                size += len(chunk)

        return StoredFile(
            path=str(dest.relative_to(self.base_path)).replace(os.sep, "/"),
            size_bytes=size,
            content_type=upload.content_type,
            original_name=upload.filename or filename,
        )

