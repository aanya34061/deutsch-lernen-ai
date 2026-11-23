import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.config import settings
from app.database import get_db
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("german_app.retrieval")

class RetrievalService:
    @classmethod
    async def index_material(cls, material_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Extract chunks, generate embeddings, and persist in knowledge_chunks collection.
        Uses content hashing to avoid redundant re-indexing unless force=True.
        """
        db = get_db()
        try:
            m_id = ObjectId(material_id) if ObjectId.is_valid(material_id) else material_id
        except Exception:
            m_id = material_id

        doc = await db.materials.find_one({"_id": m_id} if isinstance(m_id, ObjectId) else {"id": str(m_id)})
        if not doc:
            raise ValueError(f"Material '{material_id}' not found.")

        raw_text = doc.get("extracted_text") or ""
        if not raw_text.strip() or doc.get("status") == "failed":
            await db.materials.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "indexing_status": "not_indexed",
                        "indexing_error": "No extracted text available to index",
                        "chunks_count": 0
                    }
                }
            )
            return {"status": "not_indexed", "chunks_count": 0, "message": "No extracted text available"}

        # Compute content hash
        current_hash = ChunkingService.compute_content_hash(raw_text)
        existing_hash = doc.get("content_hash")
        existing_status = doc.get("indexing_status")

        # Skip if already indexed with identical content hash
        if not force and existing_hash == current_hash and existing_status == "indexed":
            chunk_count = await db.knowledge_chunks.count_documents({"material_id": str(doc["_id"])})
            if chunk_count > 0:
                logger.info(f"Material '{doc.get('title')}' content unchanged; skipping redundant indexing.")
                return {
                    "status": "indexed",
                    "chunks_count": chunk_count,
                    "skipped": True,
                    "message": "Content hash unchanged; already indexed."
                }

        # Mark as indexing
        await db.materials.update_one(
            {"_id": doc["_id"]},
            {"$set": {"indexing_status": "indexing", "indexing_error": None}}
        )

        try:
            # 1. Chunk document
            chunks = ChunkingService.chunk_material(
                material_id=str(doc["_id"]),
                text=raw_text,
                title=doc.get("title") or "Study Note",
                original_filename=doc.get("original_filename") or doc.get("title"),
                cefr_level=doc.get("cefr_level", "A1"),
                topic=doc.get("topic", "General"),
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP
            )

            if not chunks:
                await db.materials.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"indexing_status": "not_indexed", "chunks_count": 0}}
                )
                return {"status": "not_indexed", "chunks_count": 0, "message": "No valid chunks produced."}

            # 2. Generate embeddings
            texts_to_embed = [c["text"] for c in chunks]
            embeddings = await EmbeddingService.embed_texts(texts_to_embed)

            now_iso = datetime.now(timezone.utc).isoformat()
            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i] if i < len(embeddings) else []
                chunk["created_at"] = now_iso
                chunk_docs.append(chunk)

            # 3. Clean up existing chunks for this material
            await db.knowledge_chunks.delete_many({"material_id": str(doc["_id"])})

            # 4. Insert new chunks
            if chunk_docs:
                await db.knowledge_chunks.insert_many(chunk_docs)

            # 5. Update material status
            await db.materials.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "indexing_status": "indexed",
                        "chunks_count": len(chunk_docs),
                        "content_hash": current_hash,
                        "indexed_at": now_iso,
                        "indexing_error": None
                    }
                }
            )

            logger.info(f"Successfully indexed material '{doc.get('title')}' with {len(chunk_docs)} chunks.")
            return {
                "status": "indexed",
                "chunks_count": len(chunk_docs),
                "material_id": str(doc["_id"]),
                "content_hash": current_hash
            }

        except Exception as e:
            logger.error(f"Error indexing material {material_id}: {e}")
            await db.materials.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "indexing_status": "failed",
                        "indexing_error": str(e)
                    }
                }
            )
            return {"status": "failed", "error": str(e)}

    @classmethod
    async def delete_material_chunks(cls, material_id: str) -> int:
        """Remove all knowledge chunks associated with a deleted material."""
        db = get_db()
        result = await db.knowledge_chunks.delete_many({"material_id": str(material_id)})
        logger.info(f"Deleted {result.deleted_count} chunks for material {material_id}")
        return result.deleted_count

    @classmethod
    async def update_material_metadata_in_chunks(
        cls,
        material_id: str,
        title: Optional[str] = None,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None
    ) -> int:
        """Update metadata on existing chunks when material is edited."""
        db = get_db()
        updates: Dict[str, Any] = {}
        if cefr_level:
            updates["cefr_level"] = cefr_level.upper()
        if topic:
            updates["topic"] = topic
        if title:
            updates["metadata.source_title"] = title

        if not updates:
            return 0

        res = await db.knowledge_chunks.update_many(
            {"material_id": str(material_id)},
            {"$set": updates}
        )
        return res.modified_count

    @classmethod
    async def retrieve_relevant_chunks(
        cls,
        query: str,
        cefr_level: Optional[str] = None,
        material_id: Optional[str] = None,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find and rank the most relevant study chunks for a user query.
        Applies level and source filters strictly.
        """
        if not query or not query.strip():
            return []

        limit_k = top_k or settings.RAG_MAX_CHUNKS
        threshold = min_similarity if min_similarity is not None else settings.RAG_SIMILARITY_THRESHOLD

        db = get_db()
        owner_materials = await db.materials.find(
            {"user_id": "default", "is_seeded": {"$ne": True}, "indexing_status": "indexed"},
            {"_id": 1},
        ).to_list(length=10000)
        owner_ids = [str(item["_id"]) for item in owner_materials]
        if not owner_ids:
            return []
        filter_query: Dict[str, Any] = {"material_id": {"$in": owner_ids}}

        # Material filter (selected source)
        if material_id and material_id.strip():
            requested_id = str(material_id).strip()
            if requested_id not in owner_ids:
                return []
            filter_query["material_id"] = requested_id

        # Query MongoDB
        cursor = db.knowledge_chunks.find(filter_query)
        candidates = await cursor.to_list(length=200)

        if not candidates:
            return []

        # Embed user query
        query_vec = await EmbeddingService.embed_text(query)

        scored_chunks = []
        for doc in candidates:
            chunk_vec = doc.get("embedding")
            if not chunk_vec:
                continue

            sim = EmbeddingService.cosine_similarity(query_vec, chunk_vec)

            # Level preference bonus: small boost if chunk matches learner CEFR level
            if cefr_level and doc.get("cefr_level", "").upper() == cefr_level.upper():
                sim += 0.03

            if sim >= threshold or (material_id and sim >= (threshold * 0.7)):
                scored_chunks.append({
                    "chunk_id": str(doc.get("_id", "")),
                    "material_id": str(doc.get("material_id", "")),
                    "source_title": doc.get("metadata", {}).get("source_title") or doc.get("filename") or "Study Note",
                    "filename": doc.get("filename") or "document.txt",
                    "page_number": doc.get("page_number"),
                    "cefr_level": doc.get("cefr_level", "A1"),
                    "topic": doc.get("topic", "General"),
                    "chunk_index": doc.get("chunk_index", 0),
                    "text": doc.get("text", ""),
                    "similarity_score": round(sim, 4)
                })

        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:limit_k]

    @classmethod
    async def get_index_status(cls) -> Dict[str, Any]:
        """Aggregate statistics about indexed materials and chunks."""
        db = get_db()
        total_materials = await db.materials.count_documents({})
        indexed_materials = await db.materials.count_documents({"indexing_status": "indexed"})
        failed_materials = await db.materials.count_documents({"indexing_status": "failed"})
        indexing_in_progress = await db.materials.count_documents({"indexing_status": "indexing"})
        not_indexed = await db.materials.count_documents({"indexing_status": {"$in": ["not_indexed", None]}})
        total_chunks = await db.knowledge_chunks.count_documents({})

        return {
            "total_materials": total_materials,
            "indexed_materials": indexed_materials,
            "failed_materials": failed_materials,
            "indexing_in_progress": indexing_in_progress,
            "not_indexed": not_indexed,
            "total_chunks": total_chunks,
            "is_indexed": total_chunks > 0
        }

    @classmethod
    async def rebuild_all_indexes(cls, force: bool = False) -> Dict[str, Any]:
        """Trigger re-indexing for all materials that have extracted text."""
        db = get_db()
        cursor = db.materials.find({"extracted_text": {"$ne": None}})
        materials = await cursor.to_list(length=500)

        results = []
        for m in materials:
            res = await cls.index_material(str(m["_id"]), force=force)
            results.append({"material_id": str(m["_id"]), "title": m.get("title"), "result": res})

        return {
            "total_processed": len(results),
            "details": results
        }
