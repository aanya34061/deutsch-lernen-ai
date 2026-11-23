"""Copy local material uploads to private S3-compatible storage without deleting originals.

Run from backend/ after setting the S3_* variables. Default is a dry run; pass --apply to copy and update metadata.
"""
import argparse
import asyncio
import logging
from pathlib import Path

from bson import ObjectId

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, get_db
from app.services.storage_service import ObjectStorage


async def main(apply: bool) -> int:
    if settings.STORAGE_PROVIDER.lower() not in {"s3", "r2", "s3-compatible"} or not ObjectStorage.configured():
        raise RuntimeError("Set STORAGE_PROVIDER=s3 and configure all required S3_* variables first.")
    await connect_to_mongo()
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    cursor = get_db().materials.find({
        "source_type": "upload",
        "storage_key": {"$in": [None, ""]},
        "storage_filename": {"$nin": [None, ""]},
    })
    scanned = copied = skipped = 0
    try:
        async for material in cursor:
            scanned += 1
            owner = material.get("user_id")
            if not owner:
                skipped += 1
                print(f"SKIP {material['_id']}: owner is missing; assign ownership before migration")
                continue
            recorded = Path(material.get("file_path") or material["storage_filename"]).expanduser()
            source = recorded.resolve() if recorded.is_absolute() else (upload_root / recorded.name).resolve()
            if not source.exists() or not source.is_file() or not source.is_relative_to(upload_root):
                source = (upload_root / Path(material["storage_filename"]).name).resolve()
            if not source.exists() or not source.is_file() or not source.is_relative_to(upload_root):
                skipped += 1
                print(f"SKIP {material['_id']}: local upload was not found safely under {upload_root}")
                continue
            key = f"{owner}/{material['_id']}/{Path(material['storage_filename']).name}"
            print(f"{'COPY' if apply else 'WOULD COPY'} {material['_id']}: {source.name} -> {key}")
            if apply:
                await ObjectStorage.upload_file(source, key, material.get("original_filename") or source.name)
                await get_db().materials.update_one(
                    {"_id": material["_id"], "user_id": owner, "storage_key": {"$in": [None, ""]}},
                    {"$set": {"storage_key": key, "storage_provider": "s3", "file_path": None}},
                )
                copied += 1
    finally:
        await close_mongo_connection()
    print(f"Scanned {scanned}; copied {copied}; skipped {skipped}; mode={'apply' if apply else 'dry-run'}.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Upload files and update metadata. Source files are retained.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(asyncio.run(main(args.apply)))
