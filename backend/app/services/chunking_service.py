import re
import hashlib
from typing import List, Dict, Any, Optional
from app.config import settings

class ChunkingService:
    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Compute SHA-256 hash of text content."""
        if not text:
            return ""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def _split_into_sentences_or_paragraphs(text: str) -> List[str]:
        """Split text into reasonable segments (paragraphs or sentences)."""
        # First split by double newlines (paragraphs)
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        segments = []
        for p in raw_paragraphs:
            if len(p) <= settings.RAG_CHUNK_SIZE:
                segments.append(p)
            else:
                # Split large paragraphs by sentences
                sentence_splits = re.split(r'(?<=[.!?])\s+', p)
                current = ""
                for s in sentence_splits:
                    if not current:
                        current = s
                    elif len(current) + len(s) + 1 <= settings.RAG_CHUNK_SIZE:
                        current += " " + s
                    else:
                        segments.append(current)
                        current = s
                if current:
                    segments.append(current)
        return segments if segments else [text]

    @classmethod
    def chunk_material(
        cls,
        material_id: str,
        text: str,
        title: str = "",
        original_filename: Optional[str] = None,
        cefr_level: str = "A1",
        topic: str = "General",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Split extracted material text into structured chunks with preserved metadata.
        Handles page-delimited texts (PDFs) and general text.
        """
        if not text or not text.strip():
            return []

        c_size = chunk_size or settings.RAG_CHUNK_SIZE
        c_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

        filename = original_filename or title or "document.txt"

        # Check if text contains page markers: "--- Page X ---"
        page_pattern = re.compile(r'---\s*Page\s+(\d+)\s*---', re.IGNORECASE)
        page_matches = list(page_pattern.finditer(text))

        sections: List[tuple[Optional[int], str]] = []

        if page_matches:
            for idx, m in enumerate(page_matches):
                page_num = int(m.group(1))
                start_pos = m.end()
                end_pos = page_matches[idx + 1].start() if idx + 1 < len(page_matches) else len(text)
                page_content = text[start_pos:end_pos].strip()
                if page_content:
                    sections.append((page_num, page_content))
        else:
            sections.append((None, text.strip()))

        chunks: List[Dict[str, Any]] = []
        global_index = 0

        for page_num, section_text in sections:
            segments = cls._split_into_sentences_or_paragraphs(section_text)
            current_chunk = ""

            for seg in segments:
                if not current_chunk:
                    current_chunk = seg
                elif len(current_chunk) + len(seg) + 1 <= c_size:
                    current_chunk += "\n\n" + seg
                else:
                    # Save chunk
                    chunk_text = current_chunk.strip()
                    if chunk_text:
                        chunks.append({
                            "material_id": str(material_id),
                            "chunk_index": global_index,
                            "text": chunk_text,
                            "filename": filename,
                            "page_number": page_num,
                            "cefr_level": cefr_level.upper() if cefr_level else "A1",
                            "topic": topic or "General",
                            "content_hash": cls.compute_content_hash(chunk_text),
                            "metadata": {
                                "source_title": title,
                                "original_filename": filename,
                                "page_number": page_num,
                                "char_count": len(chunk_text)
                            }
                        })
                        global_index += 1

                    # Create overlap from end of current_chunk
                    if c_overlap > 0 and len(current_chunk) > c_overlap:
                        overlap_seed = current_chunk[-c_overlap:]
                        # Try to start at a word boundary
                        first_space = overlap_seed.find(" ")
                        if first_space != -1:
                            overlap_seed = overlap_seed[first_space + 1:]
                        current_chunk = overlap_seed + "\n\n" + seg
                    else:
                        current_chunk = seg

            if current_chunk.strip():
                chunk_text = current_chunk.strip()
                chunks.append({
                    "material_id": str(material_id),
                    "chunk_index": global_index,
                    "text": chunk_text,
                    "filename": filename,
                    "page_number": page_num,
                    "cefr_level": cefr_level.upper() if cefr_level else "A1",
                    "topic": topic or "General",
                    "content_hash": cls.compute_content_hash(chunk_text),
                    "metadata": {
                        "source_title": title,
                        "original_filename": filename,
                        "page_number": page_num,
                        "char_count": len(chunk_text)
                    }
                })
                global_index += 1

        return chunks
