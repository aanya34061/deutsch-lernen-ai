import asyncio
import logging
import mimetypes
import tempfile
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger("german_app.storage")


class StorageConfigurationError(RuntimeError):
    pass


class ObjectStorage:
    @staticmethod
    def configured() -> bool:
        if settings.STORAGE_PROVIDER.strip().lower() == "vercel-blob":
            return bool(settings.BLOB_READ_WRITE_TOKEN)
        return all((settings.S3_BUCKET, settings.S3_ACCESS_KEY_ID, settings.S3_SECRET_ACCESS_KEY))

    @staticmethod
    def _uses_vercel_blob() -> bool:
        return settings.STORAGE_PROVIDER.strip().lower() == "vercel-blob"

    @staticmethod
    def _client():
        if not ObjectStorage.configured():
            raise StorageConfigurationError("Persistent file storage is not configured.")
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    @classmethod
    async def upload_file(cls, local_path: Path, object_key: str, filename: str) -> None:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        if cls._uses_vercel_blob():
            from vercel import blob

            async def read_chunks():
                with local_path.open("rb") as source:
                    while chunk := await asyncio.to_thread(source.read, 64 * 1024):
                        yield chunk

            try:
                await blob.put_blob(
                    object_key,
                    read_chunks(),
                    access="private",
                    content_length=local_path.stat().st_size,
                    content_type=content_type,
                )
            except Exception as exc:
                logger.warning("Vercel Blob upload failed (%s).", type(exc).__name__)
                raise RuntimeError("Persistent file storage could not save this upload.") from exc
            return

        def _upload():
            try:
                cls._client().upload_file(
                    str(local_path), settings.S3_BUCKET, object_key,
                    ExtraArgs={"ContentType": content_type},
                )
            except (BotoCoreError, ClientError) as exc:
                logger.warning("Object storage upload failed (%s).", type(exc).__name__)
                raise RuntimeError("Persistent file storage could not save this upload.") from exc

        await asyncio.to_thread(_upload)

    @classmethod
    async def download_to_temp(cls, object_key: str) -> Path:
        suffix = Path(object_key).suffix
        handle = tempfile.NamedTemporaryFile(prefix="deutsch-file-", suffix=suffix, delete=False)
        target = Path(handle.name)
        handle.close()

        if cls._uses_vercel_blob():
            from vercel import blob

            try:
                async with blob.stream_blob(object_key, access="private") as download:
                    with target.open("wb") as destination:
                        async for chunk in download:
                            await asyncio.to_thread(destination.write, chunk)
                return target
            except Exception as exc:
                target.unlink(missing_ok=True)
                logger.warning("Vercel Blob download failed (%s).", type(exc).__name__)
                raise RuntimeError("The stored file is temporarily unavailable.") from exc

        def _download():
            try:
                cls._client().download_file(settings.S3_BUCKET, object_key, str(target))
            except (BotoCoreError, ClientError) as exc:
                target.unlink(missing_ok=True)
                logger.warning("Object storage download failed (%s).", type(exc).__name__)
                raise RuntimeError("The stored file is temporarily unavailable.") from exc

        try:
            await asyncio.to_thread(_download)
            return target
        except Exception:
            target.unlink(missing_ok=True)
            raise

    @classmethod
    async def presigned_download_url(cls, object_key: str, filename: str) -> str:
        if cls._uses_vercel_blob():
            raise RuntimeError("Private Vercel Blob files must be served through the authenticated library file endpoint.")

        def _sign():
            try:
                return cls._client().generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": settings.S3_BUCKET,
                        "Key": object_key,
                        "ResponseContentDisposition": f'inline; filename="{Path(filename).name}"',
                        "ResponseContentType": mimetypes.guess_type(filename)[0] or "application/octet-stream",
                    },
                    ExpiresIn=settings.S3_PRESIGNED_URL_SECONDS,
                )
            except (BotoCoreError, ClientError) as exc:
                logger.warning("Object storage URL signing failed (%s).", type(exc).__name__)
                raise RuntimeError("The stored file is temporarily unavailable.") from exc

        return await asyncio.to_thread(_sign)

    @classmethod
    async def delete_file(cls, object_key: str) -> None:
        if cls._uses_vercel_blob():
            from vercel import blob

            try:
                await blob.delete_blob(object_key)
            except Exception as exc:
                logger.warning("Vercel Blob deletion failed (%s).", type(exc).__name__)
                raise RuntimeError("Persistent file storage could not delete this file.") from exc
            return

        def _delete():
            try:
                cls._client().delete_object(Bucket=settings.S3_BUCKET, Key=object_key)
            except (BotoCoreError, ClientError) as exc:
                logger.warning("Object storage deletion failed (%s).", type(exc).__name__)
                raise RuntimeError("Persistent file storage could not delete this file.") from exc

        await asyncio.to_thread(_delete)
