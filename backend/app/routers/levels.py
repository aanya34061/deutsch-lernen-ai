from fastapi import APIRouter, HTTPException, status
from app.models.level import LevelDetail, LevelSummaryResponse, GrammarConcept, LessonOutline
from app.database import get_db

router = APIRouter(prefix="/levels", tags=["German CEFR Levels"])

CEFR_LEVELS_CATALOG: list[LevelDetail] = [
    LevelDetail(
        code="A1",
        name="A1 - Absolute Beginner (Grundstufe 1)",
        description="Foundational German: greetings, personal introductions, basic vocabulary, simple everyday questions and requests.",
        status="active",
        is_available=True,
        core_topics=[
            "Begrüßungen und Höflichkeit (Greetings & Politeness)",
            "Familie und Freunde (Family & Friends)",
            "Essen und Trinken (Food & Dining)",
            "Wohnen und Umgebung (Living & Home)",
            "Zahlen, Uhrzeit und Kalender (Numbers, Time & Calendar)"
        ],
        grammar_concepts=[
            GrammarConcept(name="Definite & Indefinite Articles", explanation="der, die, das (the) and ein, eine (a/an) with noun capitalization"),
            GrammarConcept(name="Present Tense Verb Conjugation", explanation="Regular -en verb endings and common irregular verbs (sein, haben, sprechen)"),
            GrammarConcept(name="The Accusative Case", explanation="Direct objects changing masculine 'der'/'ein' to 'den'/'einen'"),
            GrammarConcept(name="Negation (nicht vs kein)", explanation="'kein' negates nouns with indefinite/zero articles; 'nicht' negates verbs/adjectives"),
            GrammarConcept(name="Modal Verbs (können, möchten)", explanation="Expressing ability and polite requests with infinitive at sentence end")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Hallo und Auf Wiedersehen", topic="Greetings", grammar=["Personal Pronouns", "Verb heißen"]),
            LessonOutline(order=2, title="Wer bist du?", topic="Introductions", grammar=["Verb sein", "Question words: wer, wo, wie"]),
            LessonOutline(order=3, title="Im Supermarkt", topic="Shopping & Food", grammar=["der/die/das", "ein/eine/kein", "Akkusativ"]),
            LessonOutline(order=4, title="Mein Tagesablauf", topic="Daily Routine", grammar=["Separable Verbs", "Time expressions"]),
            LessonOutline(order=5, title="Freizeit und Hobbys", topic="Hobbies", grammar=["Modalverb können", "gern/nicht gern"])
        ]
    ),
    LevelDetail(
        code="A2",
        name="A2 - Elementary (Grundstufe 2)",
        description="Everyday communication, past events (Perfekt), simple navigation, routines, and familiar environments.",
        status="active",
        is_available=True,
        core_topics=[
            "Vergangenheit und Erlebnisse (Past Events)",
            "Reisen und Wegbeschreibung (Travel & Directions)",
            "Arbeit und Beruf (Work & Professions)",
            "Gesundheit und Körper (Health & Body)",
            "Einkaufen und Kleidung (Shopping & Clothing)"
        ],
        grammar_concepts=[
            GrammarConcept(name="Perfekt Tense", explanation="Conversational past with haben/sein + Partizip II"),
            GrammarConcept(name="The Dative Case", explanation="Indirect objects, dative prepositions (aus, bei, mit, nach, seit, von, zu)"),
            GrammarConcept(name="Two-way Prepositions (Wechselpräpositionen)", explanation="Accusative for movement/direction; Dative for static location"),
            GrammarConcept(name="Reflexive Verbs", explanation="Verbs using sich, mich, dich")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Trennbare Verben im Alltag", topic="Separable Verbs", grammar=["aufstehen", "einkaufen", "anrufen"]),
            LessonOutline(order=2, title="Das Perfekt: Vergangenheit im Gespräch", topic="Past Tense (Perfekt)", grammar=["haben/sein + Partizip II"])
        ]
    ),
    LevelDetail(
        code="B1",
        name="B1 - Intermediate (Zertifikat Deutsch)",
        description="Independent language use: expressing opinions, describing hopes, dreams, ambitions, and connecting sentences logically.",
        status="active",
        is_available=True,
        core_topics=[
            "Meinungen und Diskussionen (Opinions & Debate)",
            "Medien und Technologie (Media & Tech)",
            "Umwelt und Natur (Environment)",
            "Kultur und Gesellschaft (Culture & Society)"
        ],
        grammar_concepts=[
            GrammarConcept(name="Subordinate Conjunctions", explanation="weil, dass, obwohl, wenn sending the finite verb to the end"),
            GrammarConcept(name="Konjunktiv II", explanation="Polite requests and hypothetical scenarios (würde, hätte, wäre)"),
            GrammarConcept(name="Passive Voice (Passiv Präsens)", explanation="werden + Partizip II")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Nebensätze und Verbstellung", topic="Subordinate Clauses & Word Order", grammar=["weil", "dass", "obwohl"]),
            LessonOutline(order=2, title="Passiv Präsens Grundlagen", topic="Passive Voice", grammar=["werden + Partizip II"])
        ]
    ),
    LevelDetail(
        code="B2",
        name="B2 - Upper Intermediate",
        description="Complex professional and abstract discussions, nuanced arguments, and spontaneous fluent conversations.",
        status="planned",
        is_available=False,
        core_topics=["Berufswelt & Verhandlungen", "Wissenschaft & Forschung", "Politik & Gesellschaft"],
        grammar_concepts=[
            GrammarConcept(name="Relativsätze in all cases", explanation="Complex relative clauses with prepositions"),
            GrammarConcept(name="Zustandspassiv", explanation="sein + Partizip II"),
            GrammarConcept(name="Partizipialattribute", explanation="Extended participial phrases")
        ],
        lesson_outlines=[]
    ),
    LevelDetail(
        code="C1",
        name="C1 - Advanced (Fachsprache)",
        description="Demanding, long texts with implicit meanings, flexible and effective language for academic and professional purposes.",
        status="planned",
        is_available=False,
        core_topics=["Akademischer Diskurs", "Literatur & Philosophie", "Recht & Wirtschaft"],
        grammar_concepts=[
            GrammarConcept(name="Nominalstil", explanation="Converting verbal expressions to noun phrases"),
            GrammarConcept(name="Konjunktiv I", explanation="Indirect speech in journalism and reporting")
        ],
        lesson_outlines=[]
    ),
    LevelDetail(
        code="C2",
        name="C2 - Mastery / Native Fluency",
        description="Effortless understanding of virtually everything heard or read, subtle shades of meaning, and idiomatic expression.",
        status="planned",
        is_available=False,
        core_topics=["Nuancierte Rhetorik", "Klassische Literatur", "Dialekte & Idiome"],
        grammar_concepts=[
            GrammarConcept(name="Stilistische Feinheiten", explanation="Stylistic variations, modal particles, and historic German syntax")
        ],
        lesson_outlines=[]
    )
]

@router.get("", response_model=LevelSummaryResponse)
async def get_all_levels():
    """Retrieve all supported CEFR German learning levels with metadata."""
    active_code = "A1"
    db = get_db()
    user = await db.users.find_one({"is_seeded": {"$ne": True}})
    if user and "current_level" in user:
        active_code = user["current_level"]

    return LevelSummaryResponse(
        levels=CEFR_LEVELS_CATALOG,
        active_level=active_code,
        total_levels=len(CEFR_LEVELS_CATALOG)
    )

@router.get("/{level_code}", response_model=LevelDetail)
async def get_level_by_code(level_code: str):
    """Retrieve curriculum details for a specific CEFR level code."""
    code_upper = level_code.upper()
    for lvl in CEFR_LEVELS_CATALOG:
        if lvl.code == code_upper:
            return lvl
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"CEFR level '{level_code}' not found. Supported levels: A1, A2, B1, B2, C1, C2"
    )
