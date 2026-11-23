# DeutschLernen AI — Personal German Learning Web Application

A lightweight, fully functional personal German-learning web application built using **React**, **Vite**, **Bootstrap 5**, **Python FastAPI**, **MongoDB**, and local open-source AI models.

The app supports CEFR levels from **A1 through C2** (prioritizing A1, A2, and B1), with support for study-material uploads, structured curriculum lessons, reusable practice exercises, a vocabulary management deck, and learning from uploaded class notes.

---

## Architecture & Technology Stack

- **Frontend**:
  - React 18 with Vite
  - React Router v6
  - Bootstrap 5 & Bootstrap Icons
  - Native Web Speech Synthesis API (`de-DE` pronunciation, 100% free and local)
  - Axios HTTP Client with `VITE_API_BASE_URL` configuration
  - Reusable components (`Header`, `Sidebar`, `Card`, `ProgressBar`, `LoadingState`, `AlertMessage`, `LevelSelector`, `UploadDropzone`, `AddLinkForm`, `MaterialCard`, `MaterialTable`, `MaterialDetailModal`, `EditMaterialModal`, `ExerciseRunner`)
  - 10 distinct views: Dashboard, Study Library, German Lessons (`/lessons`), Lesson Details (`/lessons/:id`), Vocabulary Deck (`/vocabulary`), German Levels, Lesen, Hören, Schreiben, Sprechen, Progress, Settings
  - Custom German gender article color badges (`der` = blue, `die` = red, `das` = green)
- **Backend**:
  - Python FastAPI (v0.115+)
  - Pydantic v2 validation and settings management
  - Motor (Async Python MongoDB driver)
  - Modular service and API structure under `/api/v1`:
    - `/api/v1/health`: Real-time health check for backend, MongoDB, and local Ollama engine
    - `/api/v1/levels`: Supported CEFR levels catalog (A1-C2) with core topics and grammar outlines
    - `/api/v1/dashboard`: Single-learner summary calculated from saved records and level update
    - `/api/v1/library`: Study Library ingestion, extraction, and management
    - `/api/v1/lessons`: Curriculum lessons catalog, single lesson details, completion status, and material-to-lesson generation
    - `/api/v1/exercises`: Practice engine endpoints serving learner views and evaluating submissions
    - `/api/v1/vocabulary`: CRUD vocabulary deck, batch save, and rule-based vocabulary extraction from materials
    - `/api/v1/tutor`: AI German Tutor with local AI, RAG grounded in uploaded notes, multi-turn chat, and exercise generation
    - `/api/v1/practice`: Reading, listening, writing, speaking, and persisted practice progress
  - Local file storage in `./backend/uploads`
- **Database (MongoDB)**:
  - Collections: `users`, `materials`, `knowledge_chunks`, `lessons`, `exercises`, `exercise_attempts`, `conversations`, `vocabulary`, `progress`
  - Automatic indexing and idempotent authored practice-content seeding; no learner activity or uploads are seeded

---

## Phase 4: AI German Tutor with Local AI & Retrieval-Augmented Generation (RAG)

Phase 4 implements a personal, beginner-friendly AI German tutor (named **Klara**) powered by free, 100% local open-source AI (Ollama) and a lightweight local Retrieval-Augmented Generation (RAG) vector engine.

### 1. Pedagogical German Tutor Features
- **Patient Beginner Focus**: Specifically tuned for CEFR A1, A2, and B1 learners, avoiding confusing jargon.
- **Clear Explanations**: Explains grammar in simple English with natural German examples and translations.
- **Structured Error Corrections**:
  1. Original sentence
  2. Corrected sentence
  3. What was wrong (article, case, ending, word order)
  4. Simple grammatical explanation
  5. Additional example
- **Grammar Rule Explanations**:
  1. Simple rule
  2. German examples with translations
  3. Common mistake to avoid
  4. Mini-exercise
- **Interactive Practice**: Gives one question at a time and waits for learner responses.
- **Audio Pronunciation**: Free native German speech synthesis via browser Web Speech API.

### 2. Retrieval-Augmented Generation (RAG) Pipeline
- **Automatic Document Chunking**: Extracted text from uploaded study documents (PDF, DOCX, TXT, OCR) is split into boundary-aware, overlapping chunks with preserved metadata (material ID, title, filename, page numbers, CEFR level, topic).
- **Local Vector Embeddings**: Uses high-dimensional deterministic local vectors with cosine similarity, compatible with Ollama neural embeddings (`nomic-embed-text`) or lightweight in-process vectorization.
- **Content Hashing (`SHA-256`)**: Detects unchanged documents and skips redundant embedding.
- **Strict Grounding & Citation**:
  - Prioritizes selected study material when filtered.
  - Returns structured source citations (document title, page number, snippet preview) with answers.
  - If no notes match the question, explicitly informs the learner that standard German grammar knowledge is being used.
  - Treats reference documents as untrusted content to guard against prompt injection.
- **Lifecycle Synchronization**: Deleting a material automatically cleans up all associated knowledge chunks; editing material metadata updates chunk tags.

### 3. AI-Generated Practice Exercises
- Allows generating 3-5 structured practice questions from any lesson or uploaded note.
- Supports all 6 engine exercise types: Multiple Choice, Fill in the Blank, Sentence Ordering, Translation, True/False, and Matching.
- Validates model output against Pydantic schemas, strips markdown formatting, and falls back to validated curriculum exercises if model output is malformed.
- Generated questions plug directly into the reusable `ExerciseRunner` and record learner scores in learning progress.

### 4. Local AI Runtime (Ollama) Configuration
- **Default Recommended Model**: `qwen2.5:3b` (fast, lightweight, excellent multilingual & instruction-following performance on standard laptops with 8GB RAM).
- **Alternative Models**:
  - `llama3.2:3b` (~2.0 GB RAM): Lightweight, excellent English-German explanation quality.
  - `gemma2:2b` (~1.6 GB RAM): Ultra-low memory usage for older machines.
  - `mistral:7b` (~4.5 GB RAM): High quality for machines with 16GB+ RAM.
- **Embedding Model**: `nomic-embed-text` (~274 MB) for neural embeddings, or instant built-in vectorization.
- **Status Indicator**: Reports `Ready`, `Ollama not running`, `Model not installed`, `Generating response`, or `Request failed`.
- **Offline / Non-AI Resilience**: If Ollama is offline or not installed, the entire web application (Dashboard, Curriculum, Library, Vocabulary Deck, Practice Engine) remains 100% operational. The AI Tutor displays clear setup instructions without crashing.

---

## Phase 3: German Learning Engine (A1, A2, B1)

Phase 3 implements a complete structured curriculum for A1, A2, and B1 with a 10-point lesson layout, reusable 6-type practice engine, vocabulary management deck, and material integration.

### 1. Curriculum Structure
- **A1 — Beginner**: Greetings & Introductions (`sein`, `heißen`, formal *Sie* vs. informal *du*), Articles & Gender (`der, die, das`, `ein, eine`), Regular Present Tense Verbs & Verb in Position 2, Accusative Case & Negation (`den/die/das`, `kein/nicht`, `haben`, `möchten`).
- **A2 — Elementary**: Separable Verbs (`trennbare Verben` with prefix at end), Conversational Past Tense (*Perfekt* with *haben/sein* + *Partizip II*), Dative prepositions, and two-way prepositions (*Wechselpräpositionen*).
- **B1 — Intermediate**: Subordinate clauses and word order (*weil, dass, obwohl, wenn* sending conjugated verb to the end), Passive Voice foundations (*Passiv Präsens* with *werden* + *Partizip II*).

### 2. Reusable 10-Point Lesson Interface
1. Lesson title and CEFR level badge
2. Learning objectives checklist
3. Simple explanation in English
4. German examples with English translations and native audio pronunciation button
5. Important vocabulary cards with quick "Add to Vocabulary" action
6. Grammar rules and structured conjugation/gender tables
7. Common mistakes and explanations
8. Short lesson summary
9. Practice exercises powered by the interactive Practice Engine
10. "Mark as Completed" with progress tracking and next lesson navigation

### 3. Practice Engine (6 Exercise Types)
The engine presents exercises without revealing the correct answer beforehand and supports:
1. **Multiple choice**: Radio/button selection with options
2. **Fill in the blank**: Text input for missing words
3. **Translate short sentence**: Full sentence translation validation
4. **Sentence order**: Interactive word chip builder (drag/click chips in order with reset option and alternative order validation)
5. **Matching**: Pairing German terms with English meanings
6. **True or False**: Simple binary comprehension verification

### 4. Vocabulary Deck & Study Library Integration
- Tracks German words with articles (`der`, `die`, `das`), plurals, example sentences, translations, topics, and statuses (`New`, `Learning`, `Mastered`).
- **Learning from Uploaded Materials**: From any material in the Study Library:
  - **Create Study Lesson**: Generates a tailored study lesson with comprehension exercises linked to the source material.
  - **Extract & Review Vocabulary**: Rule-based extractor identifies candidate German nouns/verbs without inventing translations; flags uncertain words for learner review before saving to the deck.

---

## Setup & Running Instructions

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+** and **npm**
- **MongoDB** running locally (`brew services start mongodb/brew/mongodb-community` or `mongodb://localhost:27017`)

### 3. Local AI Setup (Ollama - Free & 100% Local)

For local development, set `AI_PROVIDER=ollama` and run Ollama. AI is disabled by default in production unless a hosted provider is explicitly configured; all non-AI learning features remain available.

#### A. Install Ollama
- **macOS**: Download from [ollama.com](https://ollama.com) or run `brew install ollama`.
- **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
- **Windows**: Download installer from [ollama.com](https://ollama.com).

#### B. Start Ollama
```bash
ollama serve
```

#### C. Download Recommended Model (Small & Fast)
```bash
# Recommended lightweight model (runs comfortably on 8GB RAM laptops)
ollama pull qwen2.5:3b

# Optional: neural embedding model
ollama pull nomic-embed-text
```

#### D. Hardware Considerations & Alternative Models
- **Standard Laptop (8GB RAM)**:
  - `qwen2.5:3b` (Default, ~2.0 GB RAM): Fast, excellent German grammar and bilingual explanations.
  - `llama3.2:3b` (~2.2 GB RAM): Strong reasoning and conversational guidance.
  - `gemma2:2b` (~1.6 GB RAM): Ultra-low memory footprint.
- **High-Performance Machine (16GB+ RAM / Apple Silicon)**:
  - `mistral:7b` (~4.5 GB RAM): High vocabulary breadth and nuance.
- **Configuring Model via `.env`**:
  ```env
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=qwen2.5:3b
  OLLAMA_EMBED_MODEL=nomic-embed-text
  ```

---

### 4. Start Backend

```bash
cd backend

# Create & activate virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend automated tests
pytest -v

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- AI Tutor Status: `http://localhost:8000/api/v1/tutor/status`
- Lessons Endpoint: `http://localhost:8000/api/v1/lessons`
- Exercises Endpoint: `http://localhost:8000/api/v1/exercises`
- Vocabulary Endpoint: `http://localhost:8000/api/v1/vocabulary`
- Library Endpoint: `http://localhost:8000/api/v1/library`

### 5. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run frontend tests
npm test

# Start Vite development server
npm run dev
```
- App UI: `http://localhost:5173`
- AI German Tutor: `http://localhost:5173/tutor`
- Curriculum & Lessons: `http://localhost:5173/lessons`
- Vocabulary Deck: `http://localhost:5173/vocabulary`
- Study Library: `http://localhost:5173/library`

---

## Verification & Test Commands

Run backend tests from `backend/` with MongoDB available:

```bash
./.venv/bin/pytest -q
```

Run frontend checks from `frontend/`:

```bash
npm test
npm run build
```

The progress service has isolated tests for empty activity, user scoping, explicit real-activity markers, score aggregation, vocabulary totals, speaking-session counts, CEFR completion, and duplicate lesson completion. MongoDB-backed tests should be run with the configured database available; they must not be run against a database containing valuable data unless the test fixtures are isolated.

## Deployment Preparation

### Free Render preview

The repository includes a Render Blueprint (`render.yaml`) for a static React frontend and Python API. Create a MongoDB Atlas cluster and database user, then create a Blueprint in Render connected to this repository. Supply `MONGODB_URI` and the S3-compatible storage values when prompted. Render links the frontend origin to API CORS and supplies the API origin to Vite automatically. The backend refuses a local MongoDB URI and local Ollama provider in production.

The API requires login. Passwords are PBKDF2-SHA256 hashed, sessions are random opaque tokens stored as hashes in MongoDB, and the browser session cookie is HttpOnly, SameSite Strict, and Secure in production. All application API routes except health and account registration/login require a session. Learner data reads and writes are scoped to that authenticated account in backend queries. The first account on a database adopts the existing single-learner `default` records so current data is retained; use a new Atlas database for an empty deployment.

Uploaded files use private S3-compatible object storage when `STORAGE_PROVIDER=s3`. Provide a bucket, endpoint, and credentials in Render; the API returns file contents only after checking the authenticated owner. Existing local uploads can be copied without deleting originals by running the migration script first in dry-run mode, then with `--apply` after checking its output:

```bash
cd backend
python scripts/migrate_local_uploads_to_s3.py
python scripts/migrate_local_uploads_to_s3.py --apply
```

Render's free API service may sleep after inactivity, and its local filesystem is temporary; user uploads are stored outside it. AI is disabled in Render by default. Hosted AI can be configured later with backend-only `AI_PROVIDER=openai-compatible`, `AI_API_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` (and optionally `AI_EMBED_MODEL`). No AI vendor or paid provider is activated automatically.

The Render API health check is `/api/v1/health`. Required production settings include `APP_ENV=production`, a remote `MONGODB_URI`, explicit `CORS_ORIGINS`, `STORAGE_PROVIDER=s3`, and the `S3_*` settings. Configure the corresponding secrets in Render's Environment UI; do not add them to Git. The complete variable list and local development defaults are in `backend/.env.example`.

- Set `APP_ENV=production`, `DEBUG=false`, `MONGODB_URI`, `MONGODB_DB_NAME`, `UPLOAD_DIR`, `CORS_ORIGINS`, `STORAGE_PROVIDER`, and `S3_*` in the backend environment. Use a persistent MongoDB database and restrict CORS to the frontend's actual origin.
- Set `VITE_API_BASE_URL` at frontend build time. The default `/api/v1` expects the frontend host or reverse proxy to route that path to FastAPI; a separately hosted API can use its absolute API base URL.
- FastAPI health is available at `/api/v1/health`. A production process should bind to the host/port provided by the deployment environment and run without `--reload`.
- Uploaded documents are stored in the configured private S3-compatible bucket. `UPLOAD_DIR` is used only as a temporary staging area for processing on Render.
- Progress only counts records explicitly marked `is_seeded: false` for that single learner. Older records without a reliable source marker are retained but excluded from current totals; review them manually before classifying them. No progress or user records are automatically deleted.
- MongoDB and uploaded-file persistence are required for durable user data. Ollama and browser speech capabilities are optional; their unavailability should not prevent non-AI learning features.

This repository is prepared for a small public preview. Before broad production use, add operational controls such as rate limits, backups, and account recovery.

---

## End-to-End Manual Verification Guide

1. **AI Offline Resilience Check**:
   - Start backend (`uvicorn app.main:app`) without Ollama running.
   - Open `http://localhost:5173/tutor`.
   - Observe indicator showing **Ollama not running** with the **Setup Guide** modal explaining how to start Ollama.
   - Navigate to `/lessons`, `/library`, and `/vocabulary`: verify all non-AI features continue working smoothly.

2. **Local AI Inference (when Ollama is started)**:
   - Run `ollama serve` and `ollama pull qwen2.5:3b`.
   - Refresh the Tutor page: the badge switches to **Ready (qwen2.5:3b)**.
   - Click starter question: *"Explain the difference between nicht and kein."*
   - Verify Klara explains the rule clearly in simple English with German examples, translations, and common mistakes.
   - Click the audio speaker button to listen to native German speech synthesis.
   - Test sentence correction: *"Correct my German sentence: 'Ich habe gestern ein Buch lesen.'"*
   - Verify structured response: Original, Corrected (`gelesen`), What was wrong (Partizip II), and explanation.

3. **Study Library RAG Grounding**:
   - Go to `/library` and upload a German study note (e.g., text or PDF).
   - Verify material automatically indexes with green **Indexed** badge and chunk count.
   - Click **Ask AI Tutor (RAG)** on the material card or detail modal.
   - In `/tutor`, ask a question specific to the note's topic.
   - Verify the response includes the **Grounded in Uploaded Notes** source pill referencing the document and snippet.

4. **AI-Generated Interactive Exercises**:
   - Click **Practice Questions** in the Tutor header.
   - Select level (A1, A2, or B1) and optional lesson.
   - Answer the interactive questions directly in the `ExerciseRunner` modal.
   - Verify feedback, explanations, and that your score is saved to progress.
