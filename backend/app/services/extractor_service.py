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
            
            return {
                "text": combined_text,
                "pages": num_pages,
                "has_text": bool(page_texts),
                "summary": f"PDF document with {num_pages} pages.",
                "error": None if page_texts else "No embedded text found. The PDF may be scanned or empty."
            }
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            return {
                "text": "",
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

            return {
                "text": combined_text,
                "paragraphs_count": len(paragraphs),
                "has_text": bool(paragraphs),
                "summary": f"Word DOCX document with {len(paragraphs)} paragraphs/entries.",
                "error": None if paragraphs else "No readable text found in the DOCX document."
            }
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            return {
                "text": "",
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
            "text": cleaned,
            "lines_count": len(lines),
            "has_text": bool(cleaned),
            "summary": f"Text file with {len(lines)} lines.",
            "error": None if cleaned else "The text file is empty."
        }

    @staticmethod
    def extract_from_image(file_path: str) -> Dict[str, Any]:
        """Extract German and English text from supported images using local OCR."""
        from PIL import Image, ImageEnhance, ImageOps
        try:
            with Image.open(file_path) as img:
                image = ImageOps.exif_transpose(img).convert("RGB")
                width, height = image.size
                format_name = img.format or "Image"

            tesseract_path = shutil.which("tesseract")
            if not tesseract_path:
                return {
                    "text": "",
                    "ocr_available": False,
                    "has_text": False,
                    "error": "Tesseract OCR is not installed or is not available in the backend PATH.",
                    "summary": f"{format_name} image ({width}x{height}) stored. OCR setup optional."
                }

            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                available_languages = set(pytesseract.get_languages(config=""))
                selected_languages = [lang for lang in ("deu", "eng") if lang in available_languages]
                if not selected_languages:
                    raise RuntimeError("Tesseract is installed, but neither German (deu) nor English (eng) language data is available.")

                # Normalize camera orientation, small text, contrast, and sharpness.
                if image.width < 1800:
                    scale = 1800 / image.width
                    image = image.resize((1800, max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
                image = ImageOps.grayscale(image)
                image = ImageOps.autocontrast(image)
                image = ImageEnhance.Contrast(image).enhance(1.25)
                image = ImageEnhance.Sharpness(image).enhance(1.4)

                lang = "+".join(selected_languages)
                # Uploaded lesson photos vary between a single block, columns,
                # and scattered labels. Try several Tesseract page layouts and
                # retain the result with the strongest word confidence.
                candidates = []
                for psm in (6, 11, 4):
                    for candidate_image in (image, ImageOps.autocontrast(image.point(lambda px: 255 if px > 170 else 0))):
                        data = pytesseract.image_to_data(
                            candidate_image,
                            lang=lang,
                            config=f"--oem 3 --psm {psm}",
                            output_type=pytesseract.Output.DICT,
                        )
                        words = [word.strip() for word in data["text"] if word and word.strip()]
                        confidences = [
                            float(confidence)
                            for word, confidence in zip(data["text"], data["conf"])
                            if word and word.strip() and str(confidence).strip() not in ("", "-1")
                        ]
                        text = " ".join(words).strip()
                        if text:
                            # Confidence leads; a small length tie-breaker helps
                            # preserve complete notes when confidence is similar.
                            score = (sum(confidences) / max(1, len(confidences))) + min(len(text), 2000) / 2000
                            candidates.append((score, text, psm))
                _, cleaned, chosen_psm = max(candidates, default=(0, "", 6), key=lambda item: item[0])
                return {
                    "text": cleaned,
                    "dimensions": f"{width}x{height}",
                    "ocr_available": True,
                    "ocr_languages": selected_languages,
                    "ocr_page_segmentation": chosen_psm,
                    "has_text": bool(cleaned),
                    "summary": f"{format_name} image ({width}x{height}) processed with Tesseract OCR ({', '.join(selected_languages)}).",
                    "error": None if cleaned else "OCR found no readable text. A sharper, well-lit image with printed text may help."
                }
            except Exception as ocr_err:
                logger.warning("OCR execution failed for %s: %s", file_path, ocr_err)
                return {
                    "text": "",
                    "dimensions": f"{width}x{height}",
                    "ocr_available": True,
                    "has_text": False,
                    "error": str(ocr_err),
                    "summary": f"{format_name} image ({width}x{height})."
                }
        except Exception as e:
            logger.error(f"Error inspecting image {file_path}: {e}")
            return {
                "text": "",
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
            transcript_text = ""

        return {
            "title": title or f"YouTube Video ({video_id})",
            "video_id": video_id,
            "text": transcript_text,
            "has_text": has_transcript,
            "summary": f"YouTube video: {title or video_id}",
            "error": None if has_transcript else "No accessible transcript was found for this video. The link is saved, but it is not available as AI study content."
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
                        "text": "",
                        "has_text": False,
                        "error": f"HTTP {resp.status_code}: Unable to load this page."
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
                return {
                    "title": title,
                    "text": "",
                    "has_text": False,
                    "error": "The page did not contain readable text."
                }

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
                "text": "",
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
