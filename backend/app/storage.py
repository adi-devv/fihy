import hashlib
import hmac
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote

import anyio

from .config import Settings, get_settings

log = logging.getLogger(__name__)


class ObjectStore(ABC):
    @abstractmethod
    async def put_jpeg(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def signed_url(self, key: str, ttl_seconds: int) -> str: ...

    @abstractmethod
    async def get(self, key: str) -> bytes | None: ...

    @abstractmethod
    async def delete(self, keys: list[str]) -> None: ...


class R2ObjectStore(ObjectStore):
    """Cloudflare R2 over its S3-compatible API.

    Objects stay private; reads always go through a presigned GET so a leaked
    URL expires on its own.
    """

    def __init__(self, settings: Settings) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = settings.r2_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.resolved_r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    async def put_jpeg(self, key: str, data: bytes) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType="image/jpeg",
                CacheControl="private, max-age=600",
            )
        )

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=ttl_seconds,
        )

    async def get(self, key: str) -> bytes | None:
        def read() -> bytes | None:
            try:
                response = self._client.get_object(Bucket=self._bucket, Key=key)
            except self._client.exceptions.NoSuchKey:
                return None
            return response["Body"].read()

        return await anyio.to_thread.run_sync(read)

    async def delete(self, keys: list[str]) -> None:
        if not keys:
            return
        await anyio.to_thread.run_sync(
            lambda: self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": key} for key in keys]},
            )
        )


class LocalObjectStore(ObjectStore):
    """Disk-backed stand-in for R2, served by the /media route."""

    def __init__(self, root: Path, secret: str, base_url: str) -> None:
        self._root = root
        self._secret = secret.encode()
        self._base_url = base_url.rstrip("/")

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root.resolve()):
            raise ValueError("key escapes the media root")
        return path

    async def put_jpeg(self, key: str, data: bytes) -> None:
        def write() -> None:
            path = self._path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await anyio.to_thread.run_sync(write)

    def sign(self, key: str, expires_at: int) -> str:
        message = f"{key}:{expires_at}".encode()
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()[:32]

    def verify(self, key: str, expires_at: int, signature: str) -> bool:
        if expires_at < int(time.time()):
            return False
        return hmac.compare_digest(self.sign(key, expires_at), signature)

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        expires_at = int(time.time()) + ttl_seconds
        signature = self.sign(key, expires_at)
        return (
            f"{self._base_url}/media/{quote(key)}"
            f"?expires={expires_at}&signature={signature}"
        )

    async def get(self, key: str) -> bytes | None:
        def read() -> bytes | None:
            path = self._path(key)
            return path.read_bytes() if path.is_file() else None

        return await anyio.to_thread.run_sync(read)

    async def delete(self, keys: list[str]) -> None:
        def remove() -> None:
            for key in keys:
                self._path(key).unlink(missing_ok=True)

        await anyio.to_thread.run_sync(remove)


_store: ObjectStore | None = None


def get_store() -> ObjectStore:
    global _store
    if _store is None:
        settings = get_settings()
        if settings.storage_configured:
            _store = R2ObjectStore(settings)
        else:
            log.warning(
                "R2 is not configured; storing images under %s and serving them "
                "from /media. Do not run this way outside development.",
                settings.media_root,
            )
            _store = LocalObjectStore(
                Path(settings.media_root),
                settings.secret_key,
                settings.public_base_url,
            )
    return _store


def set_store(store: ObjectStore | None) -> None:
    global _store
    _store = store
