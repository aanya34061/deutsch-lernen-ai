import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("german_app.extractor")

class ExtractorService:
    @staticmethod
    def extract_from_pdf(file_path: str) -> Dict[str, Any]:
        """Extract text from a PDF file using pypdf."""
        import pypdf
        try:
            reader = pypdf.PdfReader(file_path)
            num_pages = len(reader.pages)
            page_texts = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    page_texts.append(f"--- Page {i+1} ---\n{text.strip()}")
            
            combined_text = "\n\n".join(page_texts).strip()
            if not combined_text:
                combined_text = "[Scanned or empty PDF: No embedded text found]"
            
            return {
                "text": combined_text,
                "pages": num_pages,
                "has_text": bool(page_texts),
                "summary": f"PDF document with {num_pages} pages."
            }
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            return {
                "text": f"[Error reading PDF: {str(e)}]",
                "pages": 0,
                "has_text": False,
                "error": str(e)
            }

    @staticmethod
    def extract_from_docx(file_path: str) -> Dict[str, Any]:
        """Extract text from a Word DOCX file using python-docx."""
        import docx
        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        paragraphs.append(" | ".join(row_texts))

            combined_text = "\n\n".join(paragraphs).strip()
            if not combined_text:
                combined_text = "[Empty DOCX document: No text found]"

            return {
                "text": combined_text,
                "paragraphs_count": len(paragraphs),
                "has_text": bool(paragraphs),
                "summary": f"Word DOCX document with {len(paragraphs)} paragraphs/entries."
            }
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            return {
                "text": f"[Error reading DOCX: {str(e)}]",
                "paragraphs_count": 0,
                "has_text": False,
                "error": str(e)
            }

    @staticmethod
    def extract_from_txt(file_path: str) -> Dict[str, Any]:
        """Extract text from a plain TXT file with encoding fallbacks."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")

        cleaned = content.strip()
        lines = [line for line in cleaned.splitlines() if line.strip()]
        return {
            "text": cleaned if cleaned else "[Empty text file]",
            "lines_count": len(lines),
            "has_text": bool(cleaned),
            "summary": f"Text file with {len(lines)} lines."
        }

    @staticmethod
    def extract_from_image(file_path: str) -> Dict[str, Any]:
        """Extract text from JPG/PNG image using optional Tesseract OCR if installed."""
        from PIL import Image
        try:
            # Verify image file
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or "Image"

            has_tesseract = shutil.which("tesseract") is not None
            if has_tesseract:
                try:
                    import pytesseract
                    # Attempt German + English OCR, fallback to default if lang not found
                    try:
                        extracted = pytesseract.image_to_string(Image.open(file_path), lang="deu+eng")
                    except Exception:
                        extracted = pytesseract.image_to_string(Image.open(file_path))
                    
                    cleaned = extracted.strip()
                    return {
                        "text": cleaned if cleaned else "[Image OCR produced no readable text]",
                        "dimensions": f"{width}x{height}",
                        "ocr_available": True,
                        "has_text": bool(cleaned),
                        "summary": f"{format_name} image ({width}x{height}) processed with Tesseract OCR."
                    }
                except Exception as ocr_err:
                    logger.warning(f"OCR execution failed: {ocr_err}")
                    return {
                        "text": f"[OCR execution error: {str(ocr_err)}]",
                        "dimensions": f"{width}x{height}",
                        "ocr_available": True,
                        "has_text": False,
                        "summary": f"{format_name} image ({width}x{height})."
                    }
            else:
                return {
                    "text": "[Image uploaded successfully. Note: OCR engine requires system Tesseract ('brew install tesseract tesseract-lang'). Original image is preserved and ready for Phase 3.]",
                    "dimensions": f"{width}x{height}",
                    "ocr_available": False,
                    "has_text": False,
                    "summary": f"{format_name} image ({width}x{height}) stored. OCR setup optional."
                }
        except Exception as e:
            logger.error(f"Error inspecting image {file_path}: {e}")
            return {
                "text": f"[Invalid or unreadable image file: {str(e)}]",
                "ocr_available": False,
                "has_text": False,
                "error": str(e)
            }

    @staticmethod
    def parse_youtube_video_id(url: str) -> Optional[str]:
        """Extract 11-character YouTube video ID from various URL patterns."""
        patterns = [
            r"(?:v=|\/embed\/|\/17\/|youtu\.be\/|\/v\/|\/e\/|watch\?v=|shorts\/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @classmethod
    async def extract_from_youtube(cls, url: str) -> Dict[str, Any]:
        """Fetch YouTube video metadata and captions/transcript if accessible."""
        import httpx
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = cls.parse_youtube_video_id(url)
        if not video_id:
            return {
                "title": None,
                "text": "[Invalid YouTube URL: Video ID could not be identified]",
                "has_text": False,
                "error": "Invalid YouTube URL"
            }

        title = None
        # Try fetching oEmbed metadata for title
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                )
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title")
        except Exception as e:
            logger.debug(f"Could not retrieve oEmbed title for YouTube video {video_id}: {e}")

        # Try extracting captions/transcripts
        transcript_text = ""
        has_transcript = False
        try:
            yta = YouTubeTranscriptApi()
            transcript_obj = None
            try:
                transcript_obj = yta.fetch(video_id, languages=["de", "de-DE", "en", "en-US"])
            except Exception:
                # Try any available transcript
                try:
                    transcript_list = yta.list(video_id)
                    for t in transcript_list:
                        transcript_obj = t.fetch()
                        break
                except Exception:
                    transcript_obj = None

            if transcript_obj:
                raw_data = transcript_obj.to_raw_data() if hasattr(transcript_obj, "to_raw_data") else transcript_obj
                lines = []
                for item in raw_data:
                    start_sec = item.get("start", 0)
                    mins = int(start_sec // 60)
                    secs = int(start_sec % 60)
                    text_line = item.get("text", "").strip()
                    if text_line:
                        lines.append(f"[{mins:02d}:{secs:02d}] {text_line}")
                transcript_text = "\n".join(lines)
                has_transcript = bool(lines)
        except Exception as transcript_err:
            logger.info(f"YouTube transcript unavailable for {video_id}: {transcript_err}")

        if not transcript_text:
            transcript_text = (
                "[YouTube link saved. Automatic captions are disabled, unavailable, "
                "or access-restricted for this video. The URL is preserved for learning.]"
            )

        return {
            "title": title or f"YouTube Video ({video_id})",
            "video_id": video_id,
            "text": transcript_text,
            "has_text": has_transcript,
            "summary": f"YouTube video: {title or video_id}"
        }

    @staticmethod
    async def extract_from_web_url(url: str) -> Dict[str, Any]:
        """Fetch general learning webpage title and readable text excerpt."""
        import httpx
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) GermanLearningApp/1.0"
            }
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    return {
                        "title": url,
                        "text": f"[HTTP {resp.status_code}: Unable to load content from {url}]",
                        "has_text": False
                    }
                html = resp.text

            # Extract title
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else url

            # Basic clean of scripts, styles, and tags
            clean_html = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
            # Replace paragraph/break tags with newlines
            clean_html = re.sub(r"<(?:p|br|div|h[1-6]|li)[^>]*>", "\n", clean_html, flags=re.IGNORECASE)
            # Remove remaining tags
            text = re.sub(r"<[^>]+>", " ", clean_html)
            # Clean whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            extracted_text = "\n".join(lines)[:10000]  # cap at 10,000 characters

            if not extracted_text:
                extracted_text = f"[Web link saved: {url}]"

            return {
                "title": title,
                "text": extracted_text,
                "has_text": bool(lines),
                "summary": f"Web article: {title}"
            }
        except Exception as e:
            logger.warning(f"Error fetching web URL {url}: {e}")
            return {
                "title": url,
                "text": f"[Web link saved: {url}. Could not fetch content automatically: {str(e)}]",
                "has_text": False,
                "error": str(e)
            }

    @classmethod
    def extract_file_content(cls, file_path: str, file_type: str) -> Dict[str, Any]:
        """Dispatch text extraction based on file type."""
        normalized = file_type.lower()
        if normalized == "pdf":
            return cls.extract_from_pdf(file_path)
        elif normalized in ("docx", "doc"):
            return cls.extract_from_docx(file_path)
        elif normalized == "txt":
            return cls.extract_from_txt(file_path)
        elif normalized in ("image", "jpg", "jpeg", "png"):
            return cls.extract_from_image(file_path)
        else:
            return {
                "text": f"[No text extractor available for format: {file_type}]",
                "has_text": False
            }
