import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger("german_app.database")

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db_instance = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=3000
        )
        # Verify connection
        await client.admin.command('ping')
        db_instance.client = client
        db_instance.db = client[settings.MONGODB_DB_NAME]
        logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        await init_db_indexes()
        await hide_legacy_demo_records()
        await seed_initial_data_if_empty()
        await seed_practice_data_if_empty()
    except Exception as e:
        db_instance.client = None
        db_instance.db = None
        logger.error("Failed to connect to MongoDB (%s).", type(e).__name__)

async def close_mongo_connection():
    if db_instance.client is not None:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_db() -> AsyncIOMotorDatabase:
    if db_instance.db is None:
        raise RuntimeError("Database connection not initialized")
    return db_instance.db

def get_collection(collection_name: str):
    return get_db()[collection_name]

async def check_db_health() -> dict:
    if db_instance.client is None:
        return {"status": "disconnected", "error": "Client not initialized"}
    try:
        await db_instance.client.admin.command('ping')
        return {"status": "connected", "database": settings.MONGODB_DB_NAME}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def init_db_indexes():
    """Ensure essential indexes for collections exist."""
    try:
        db = get_db()
        # users
        await db.users.create_index("username", unique=True)
        # materials
        await db.materials.create_index([("cefr_level", 1), ("topic", 1)])
        await db.materials.create_index("status")
        # chunks
        await db.knowledge_chunks.create_index("material_id")
        await db.knowledge_chunks.create_index([("cefr_level", 1), ("topic", 1)])
        # lessons
        await db.lessons.create_index([("cefr_level", 1), ("order", 1)])
        # exercises
        await db.exercises.create_index([("lesson_id", 1), ("skill", 1)])
        # attempts
        await db.exercise_attempts.create_index([("user_id", 1), ("timestamp", -1)])
        # vocabulary
        await db.vocabulary.create_index([("user_id", 1), ("word", 1)], unique=True)
        await db.vocabulary.create_index("next_review")
        # conversations
        await db.conversations.create_index([("user_id", 1), ("timestamp", -1)])
        # practice reading, listening, writing, speaking (Phase 5)
        await db.practice_reading.create_index([("cefr_level", 1), ("topic", 1)])
        await db.practice_listening.create_index([("cefr_level", 1), ("topic", 1)])
        await db.listening_resource_completions.create_index(
            [("user_id", 1), ("resource_id", 1)], unique=True
        )
        await db.practice_writing_prompts.create_index([("cefr_level", 1), ("topic", 1)])
        await db.writing_drafts.create_index([("prompt_id", 1), ("user_id", 1)])
        await db.writing_submissions.create_index([("user_id", 1), ("timestamp", -1)])
        await db.speaking_sessions.create_index([("user_id", 1), ("updated_at", -1)])
        logger.info("Database indexes initialized successfully.")
    except Exception as e:
        logger.warning(f"Error initializing indexes: {e}")

async def hide_legacy_demo_records():
    """Label legacy demo records without deleting any existing data."""
    try:
        db = get_db()
        legacy_titles = [
            "A1 Begrüßungen und Vorstellungen (Greetings Guide)",
            "Deutsche Artikel im Alltag (Articles in Daily Life)",
            "Im Café bestellen (Ordering in a German Café)",
        ]
        await db.materials.update_many({"title": {"$in": legacy_titles}}, {"$set": {"is_seeded": True}})
        # Earlier speaking sessions recorded a fixed score and fixed duration instead
        # of an evaluated result. Keep those records in MongoDB, but exclude them from
        # real learner metrics.
        await db.exercise_attempts.update_many(
            {"skill": "speaking", "exercise_id": {"$regex": "^spk_"}, "score": 90, "time_spent_seconds": 30},
            {"$set": {"is_seeded": True}},
        )
        legacy_user = await db.users.find_one({"username": "learner", "streak_days": 4})
        if legacy_user:
            legacy_user_id = str(legacy_user["_id"])
            await db.users.update_one({"_id": legacy_user["_id"]}, {"$set": {"is_seeded": True}})
            await db.progress.update_many({"user_id": legacy_user_id}, {"$set": {"is_seeded": True}})
            await db.vocabulary.update_many(
                {"user_id": legacy_user_id, "word": {"$in": ["der Apfel", "das Buch", "die Zeitung", "sprechen", "der Bahnhof"]}},
                {"$set": {"is_seeded": True}},
            )
    except Exception as e:
        logger.warning(f"Could not label legacy demo records: {e}")

async def seed_initial_data_if_empty():
    """Kept for compatibility; user data must only be created by explicit user actions."""
    return

async def seed_practice_data_if_empty():
    """Seeds starter reading, listening, writing, and speaking exercises if empty."""
    try:
        db = get_db()
        from app.data.practice_reading_data import STARTING_READING_EXERCISES
        from app.data.practice_listening_data import STARTING_LISTENING_EXERCISES
        from app.data.practice_writing_data import STARTING_WRITING_PROMPTS
        from app.data.practice_speaking_data import STARTING_SPEAKING_SCENARIOS

        # Keep starter reading content current for existing databases while preserving
        # any records explicitly marked as user-created.
        reading_seeded_count = 0
        for exercise in STARTING_READING_EXERCISES:
            existing = await db.practice_reading.find_one({"id": exercise["id"]})
            if existing and existing.get("is_seeded") is False:
                continue
            if existing:
                await db.practice_reading.update_one({"_id": existing["_id"]}, {"$set": exercise})
            else:
                await db.practice_reading.insert_one(exercise)
            reading_seeded_count += 1
        if reading_seeded_count:
            logger.info(f"Seeded or refreshed {reading_seeded_count} reading practice exercises.")

        if await db.practice_listening.count_documents({}) == 0:
            await db.practice_listening.insert_many([{**item, "is_seeded": True} for item in STARTING_LISTENING_EXERCISES])
            logger.info(f"Seeded {len(STARTING_LISTENING_EXERCISES)} listening practice exercises.")
        else:
            await db.practice_listening.update_many(
                {"id": {"$in": [item["id"] for item in STARTING_LISTENING_EXERCISES]}, "is_seeded": {"$exists": False}},
                {"$set": {"is_seeded": True}},
            )

        if await db.practice_writing_prompts.count_documents({}) == 0:
            await db.practice_writing_prompts.insert_many([{**item, "is_seeded": True} for item in STARTING_WRITING_PROMPTS])
            logger.info(f"Seeded {len(STARTING_WRITING_PROMPTS)} writing practice prompts.")
        else:
            await db.practice_writing_prompts.update_many(
                {"id": {"$in": [item["id"] for item in STARTING_WRITING_PROMPTS]}, "is_seeded": {"$exists": False}},
                {"$set": {"is_seeded": True}},
            )

        if await db.practice_speaking_scenarios.count_documents({}) == 0:
            await db.practice_speaking_scenarios.insert_many([{**item, "is_seeded": True} for item in STARTING_SPEAKING_SCENARIOS])
            logger.info(f"Seeded {len(STARTING_SPEAKING_SCENARIOS)} speaking practice scenarios.")
        else:
            await db.practice_speaking_scenarios.update_many(
                {"id": {"$in": [item["id"] for item in STARTING_SPEAKING_SCENARIOS]}, "is_seeded": {"$exists": False}},
                {"$set": {"is_seeded": True}},
            )

    except Exception as e:
        logger.error(f"Error seeding practice data: {e}")
