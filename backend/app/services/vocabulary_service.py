import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.models.vocabulary import (
    VocabularyCreate,
    VocabularyBatchCreate,
    VocabularyUpdate,
    VocabularyResponse,
    ExtractedVocabularyItem,
    ExtractVocabularyResponse
)
from app.database import get_db
from app.security import current_user_id

logger = logging.getLogger("german_app.vocabulary")

# Curated reference dictionary for linguistically accurate rule-based extraction
VERIFIED_GERMAN_LEXICON: Dict[str, Dict[str, Any]] = {
    # A1 & A2 Core Nouns
    "apfel": {"word": "der Apfel", "article": "der", "plural": "die Äpfel", "meaning_en": "apple", "level": "A1", "topic": "Food & Drink"},
    "brot": {"word": "das Brot", "article": "das", "plural": "die Brote", "meaning_en": "bread", "level": "A1", "topic": "Food & Drink"},
    "kaffee": {"word": "der Kaffee", "article": "der", "plural": "die Kaffees", "meaning_en": "coffee", "level": "A1", "topic": "Food & Drink"},
    "tee": {"word": "der Tee", "article": "der", "plural": "die Tees", "meaning_en": "tea", "level": "A1", "topic": "Food & Drink"},
    "wasser": {"word": "das Wasser", "article": "das", "plural": "die Wasser", "meaning_en": "water", "level": "A1", "topic": "Food & Drink"},
    "buch": {"word": "das Buch", "article": "das", "plural": "die Bücher", "meaning_en": "book", "level": "A1", "topic": "Studies & School"},
    "zeitung": {"word": "die Zeitung", "article": "die", "plural": "die Zeitungen", "meaning_en": "newspaper", "level": "A1", "topic": "Media"},
    "tisch": {"word": "der Tisch", "article": "der", "plural": "die Tische", "meaning_en": "table", "level": "A1", "topic": "Home & Living"},
    "stuhl": {"word": "der Stuhl", "article": "der", "plural": "die Stühle", "meaning_en": "chair", "level": "A1", "topic": "Home & Living"},
    "lampe": {"word": "die Lampe", "article": "die", "plural": "die Lampen", "meaning_en": "lamp", "level": "A1", "topic": "Home & Living"},
    "auto": {"word": "das Auto", "article": "das", "plural": "die Autos", "meaning_en": "car", "level": "A1", "topic": "Travel & Transport"},
    "zug": {"word": "der Zug", "article": "der", "plural": "die Züge", "meaning_en": "train", "level": "A1", "topic": "Travel & Transport"},
    "bahnhof": {"word": "der Bahnhof", "article": "der", "plural": "die Bahnhöfe", "meaning_en": "train station", "level": "A1", "topic": "Travel & Directions"},
    "arzt": {"word": "der Arzt", "article": "der", "plural": "die Ärzte", "meaning_en": "doctor", "level": "A1", "topic": "Health"},
    "bruder": {"word": "der Bruder", "article": "der", "plural": "die Brüder", "meaning_en": "brother", "level": "A1", "topic": "Family"},
    "schwester": {"word": "die Schwester", "article": "die", "plural": "die Schwestern", "meaning_en": "sister", "level": "A1", "topic": "Family"},
    "vater": {"word": "der Vater", "article": "der", "plural": "die Väter", "meaning_en": "father", "level": "A1", "topic": "Family"},
    "mutter": {"word": "die Mutter", "article": "die", "plural": "die Mütter", "meaning_en": "mother", "level": "A1", "topic": "Family"},
    "haus": {"word": "das Haus", "article": "das", "plural": "die Häuser", "meaning_en": "house", "level": "A1", "topic": "Home & Living"},
    "wohnung": {"word": "die Wohnung", "article": "die", "plural": "die Wohnungen", "meaning_en": "apartment", "level": "A1", "topic": "Home & Living"},
    "stadt": {"word": "die Stadt", "article": "die", "plural": "die Städte", "meaning_en": "city / town", "level": "A1", "topic": "City & Travel"},
    "sprache": {"word": "die Sprache", "article": "die", "plural": "die Sprachen", "meaning_en": "language", "level": "A1", "topic": "Studies & School"},
    "zeit": {"word": "die Zeit", "article": "die", "plural": "die Zeiten", "meaning_en": "time", "level": "A1", "topic": "Daily Routine"},
    "tag": {"word": "der Tag", "article": "der", "plural": "die Tage", "meaning_en": "day", "level": "A1", "topic": "Daily Routine"},
    "woche": {"word": "die Woche", "article": "die", "plural": "die Wochen", "meaning_en": "week", "level": "A1", "topic": "Daily Routine"},
    # Verbs
    "sprechen": {"word": "sprechen", "article": "", "plural": "", "meaning_en": "to speak", "level": "A1", "topic": "Communication"},
    "lernen": {"word": "lernen", "article": "", "plural": "", "meaning_en": "to learn", "level": "A1", "topic": "Studies & School"},
    "arbeiten": {"word": "arbeiten", "article": "", "plural": "", "meaning_en": "to work", "level": "A1", "topic": "Work & Career"},
    "wohnen": {"word": "wohnen", "article": "", "plural": "", "meaning_en": "to reside / live", "level": "A1", "topic": "Home & Living"},
    "verstehen": {"word": "verstehen", "article": "", "plural": "", "meaning_en": "to understand", "level": "A1", "topic": "Communication"},
    "aufstehen": {"word": "aufstehen", "article": "", "plural": "", "meaning_en": "to get up", "level": "A2", "topic": "Daily Routine"},
    "einkaufen": {"word": "einkaufen", "article": "", "plural": "", "meaning_en": "to grocery shop", "level": "A2", "topic": "Shopping"},
    # B1 Intermediate
    "meinung": {"word": "die Meinung", "article": "die", "plural": "die Meinungen", "meaning_en": "opinion", "level": "B1", "topic": "Opinions & Debate"},
    "umwelt": {"word": "die Umwelt", "article": "die", "plural": "", "meaning_en": "environment", "level": "B1", "topic": "Environment"},
    "erfahrung": {"word": "die Erfahrung", "article": "die", "plural": "die Erfahrungen", "meaning_en": "experience", "level": "B1", "topic": "Experiences"},
    "zukunft": {"word": "die Zukunft", "article": "die", "plural": "", "meaning_en": "future", "level": "B1", "topic": "Future Plans"}
}

class VocabularyService:
    @staticmethod
    async def list_vocabulary(
        level: Optional[str] = None,
        topic: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Retrieves user vocabulary with multi-criteria filtering."""
        db = get_db()
        query: Dict[str, Any] = {"user_id": current_user_id(), "is_seeded": False}

        if level:
            query["cefr_level"] = level.upper()
        if topic:
            query["topic"] = {"$regex": topic, "$options": "i"}
        if status:
            query["status"] = status.lower()
        if search:
            query["$or"] = [
                {"word": {"$regex": search, "$options": "i"}},
                {"meaning_en": {"$regex": search, "$options": "i"}},
                {"topic": {"$regex": search, "$options": "i"}}
            ]

        cursor = db.vocabulary.find(query).sort([("created_at", -1), ("word", 1)]).limit(limit)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            items.append(doc)
        return items

    @staticmethod
    async def create_vocabulary(data: VocabularyCreate) -> Dict[str, Any]:
        """Manually creates a new vocabulary entry."""
        db = get_db()
        doc = data.model_dump()
        doc["user_id"] = current_user_id()
        doc["is_seeded"] = False
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        doc["updated_at"] = doc["created_at"]
        doc["status"] = doc.get("status") or "new"

        res = await db.vocabulary.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        doc["_id"] = str(res.inserted_id)
        return doc

    @staticmethod
    async def batch_create_vocabulary(batch: VocabularyBatchCreate) -> int:
        """Saves a batch of vocabulary items from a lesson or reviewed material."""
        db = get_db()
        now = datetime.now(timezone.utc).isoformat()
        inserted_count = 0

        for w in batch.words:
            doc = w.model_dump()
            doc["user_id"] = current_user_id()
            doc["is_seeded"] = False
            doc["source_type"] = batch.source_type
            doc["source_id"] = batch.source_id
            doc["source_title"] = batch.source_title
            doc["created_at"] = now
            doc["updated_at"] = now
            doc["status"] = doc.get("status") or "new"

            result = await db.vocabulary.update_one(
                {"word": doc["word"], "user_id": current_user_id(), "is_seeded": False},
                {"$setOnInsert": doc},
                upsert=True
            )
            if result.upserted_id is not None:
                inserted_count += 1

        return inserted_count

    @staticmethod
    async def update_vocabulary(vocab_id: str, data: VocabularyUpdate) -> Optional[Dict[str, Any]]:
        """Updates vocabulary status, score, or metadata."""
        db = get_db()
        query = ({"_id": ObjectId(vocab_id)} if ObjectId.is_valid(vocab_id) else {"id": vocab_id})
        query["user_id"] = current_user_id()
        update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

        if update_fields.get("status") == "mastered":
            update_fields["mastery_score"] = 100
            update_fields["due_for_revision"] = False
        elif update_fields.get("status") == "learning":
            update_fields["mastery_score"] = 50

        await db.vocabulary.update_one(query, {"$set": update_fields})
        updated = await db.vocabulary.find_one(query)
        if updated:
            updated["id"] = str(updated["_id"])
        return updated

    @staticmethod
    async def delete_vocabulary(vocab_id: str) -> bool:
        """Removes a vocabulary card."""
        db = get_db()
        query = ({"_id": ObjectId(vocab_id)} if ObjectId.is_valid(vocab_id) else {"id": vocab_id})
        query["user_id"] = current_user_id()
        res = await db.vocabulary.delete_one(query)
        return res.deleted_count > 0

    @staticmethod
    def extract_vocabulary_from_text(
        text: str,
        material_id: Optional[str] = None,
        material_title: Optional[str] = None
    ) -> ExtractVocabularyResponse:
        """
        Rule-based German vocabulary extraction from study material.
        Extracts verified German words from lexicon, and flags any unverified
        capitalized nouns for learner review without fabricating articles.
        """
        if not text:
            return ExtractVocabularyResponse(items=[], total_found=0, material_id=material_id, material_title=material_title)

        found_items: Dict[str, ExtractedVocabularyItem] = {}

        # 1. Match against verified dictionary (exact and case-insensitive)
        words = re.findall(r'\b[A-Za-zÄÖÜäöüß]+\b', text)
        for w in words:
            w_lower = w.lower()
            if w_lower in VERIFIED_GERMAN_LEXICON and w_lower not in found_items:
                lex = VERIFIED_GERMAN_LEXICON[w_lower]
                # Find sentence context
                match = re.search(rf'([^.!?]*\b{re.escape(w)}\b[^.!?]*[.!?])', text, re.IGNORECASE)
                context = match.group(1).strip() if match else f"Found in {material_title or 'uploaded material'}"

                found_items[w_lower] = ExtractedVocabularyItem(
                    word=lex["word"],
                    article=lex.get("article", ""),
                    plural=lex.get("plural", ""),
                    meaning_en=lex["meaning_en"],
                    example_context=context[:140],
                    cefr_level=lex.get("level", "A1"),
                    topic=lex.get("topic", "General"),
                    confidence="high",
                    is_uncertain=False
                )

        # 2. Extract potential capitalized nouns not in lexicon for learner review
        # In German, nouns are capitalized. Rule: word starts with capital letter, len >= 4.
        capitalized_words = re.findall(r'\b[A-ZÄÖÜ][a-zäöüß]{3,}\b', text)
        for cw in capitalized_words:
            cw_lower = cw.lower()
            if cw_lower not in found_items and cw_lower not in ["Guten", "Heute", "Wann", "Sehr", "Nicht", "Wenn", "Aber", "Oder", "Und"]:
                # Check for grammatical ending clues
                article_hint = ""
                if cw.endswith("ung") or cw.endswith("heit") or cw.endswith("keit") or cw.endswith("schaft"):
                    article_hint = "die"
                elif cw.endswith("chen") or cw.endswith("lein"):
                    article_hint = "das"

                match = re.search(rf'([^.!?]*\b{re.escape(cw)}\b[^.!?]*[.!?])', text)
                context = match.group(1).strip() if match else f"Excerpt from {material_title or 'notes'}"

                found_items[cw_lower] = ExtractedVocabularyItem(
                    word=f"{article_hint + ' ' if article_hint else ''}{cw}".strip(),
                    article=article_hint,
                    plural="",
                    meaning_en="",  # Never invent English translations
                    example_context=context[:140],
                    cefr_level="A1",
                    topic="Uploaded Material",
                    confidence="needs_review",
                    is_uncertain=True,
                    review_note="Candidate German noun extracted from notes. Please review article & English translation before saving."
                )

        result_items = list(found_items.values())[:30]  # Cap at top 30
        return ExtractVocabularyResponse(
            items=result_items,
            total_found=len(result_items),
            material_id=material_id,
            material_title=material_title
        )
