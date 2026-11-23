from fastapi import APIRouter, HTTPException, status
from app.models.level import LevelDetail, LevelSummaryResponse, GrammarConcept, LessonOutline
from app.database import get_db

router = APIRouter(prefix="/levels", tags=["German CEFR Levels"])

CEFR_LEVELS_CATALOG: list[LevelDetail] = [
    LevelDetail(
        code="A1",
        name="A1 - Absolute Beginner (Grundstufe 1)",
        description="Beginner communication for social contact and familiar everyday needs: introduce yourself, understand simple information, shop, get around, and ask for basic help.",
        status="active",
        is_available=True,
        core_topics=[
            "Personal details and social contacts",
            "Classroom communication and learning strategies",
            "Food, shopping, quantities, and prices",
            "Family relationships and ownership",
            "Housing, daily routines, and local orientation",
            "Appointments, time, mobility, and simple requests",
            "Basic health needs and asking for help"
        ],
        grammar_concepts=[
            GrammarConcept(name="Articles, gender, and plural", explanation="Learn common nouns with der/die/das and their plural; use ein/eine for simple descriptions and requests."),
            GrammarConcept(name="Present-tense statements and questions", explanation="Conjugate common verbs and use verb-second statements, W-questions, and yes/no questions in everyday exchanges."),
            GrammarConcept(name="Nominative and introductory accusative", explanation="Identify who is acting and name a familiar direct object; the clearest article change is masculine der → den."),
            GrammarConcept(name="Simple negation and general statements", explanation="Use nicht and kein in short responses; use man + third-person singular for general statements."),
            GrammarConcept(name="Genitive possession", explanation="Following your uploaded A1 syllabus, introduce names + -s and simple der/des possession phrases for familiar people and objects."),
            GrammarConcept(name="Polite requests and modal verbs", explanation="Use können and möchten with an infinitive to ask for help or make a simple request.")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Make contact and exchange personal details", topic="Social contacts", grammar=["greetings", "name and origin", "sein and heißen", "simple questions"]),
            LessonOutline(order=2, title="Ask for help and take part in class", topic="Classroom and learning", grammar=["W-questions", "polite requests", "clarification phrases"]),
            LessonOutline(order=3, title="Buy food and everyday items", topic="Shopping", grammar=["articles", "numbers and prices", "introductory accusative"]),
            LessonOutline(order=4, title="Talk about home and find a place", topic="Housing and mobility", grammar=["present tense", "time and place phrases", "simple directions"]),
            LessonOutline(order=5, title="Arrange an appointment and describe a basic need", topic="Health and services", grammar=["days and times", "können/möchten", "simple statements with man"]),
            LessonOutline(order=6, title="Say who familiar things belong to", topic="Family and home", grammar=["possessive names + -s", "simple Genitive phrases", "von as an everyday alternative"])
        ]
    ),
    LevelDetail(
        code="A2",
        name="A2 - Elementary (Grundstufe 2)",
        description="Handle a wider range of everyday interactions independently: public services, work and education, health, payments, housing, mobility, and recent experiences.",
        status="active",
        is_available=True,
        core_topics=[
            "Authorities, appointments, and forms",
            "Work, job search, and education or childcare",
            "Banking, insurance, shopping, and services",
            "Health, housing, mobility, and travel",
            "Past events, plans, and practical messages"
        ],
        grammar_concepts=[
            GrammarConcept(name="Dative and accusative in useful exchanges", explanation="Choose articles with common dative and accusative verbs, recipients, and prepositions."),
            GrammarConcept(name="Fixed-case and two-way prepositions", explanation="Use prepositions for travel, housing, and location; ask wo? for a location and wohin? for a destination."),
            GrammarConcept(name="Time expressions", explanation="Use ab, an, in, nach, seit, and vor to arrange appointments and describe when something happens."),
            GrammarConcept(name="Perfekt for recent events", explanation="Use haben/sein + Partizip II to report journeys, appointments, and personal experiences."),
            GrammarConcept(name="Demonstratives and polite forms", explanation="Use dieser/welcher with familiar people and objects; use Sie in service and official interactions."),
            GrammarConcept(name="Reflexive verbs and connected requests", explanation="Use common reflexive verbs and connect a short explanation to a request.")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Ask for information and complete an office form", topic="Authorities", grammar=["polite Sie-questions", "personal details", "dative mir"]),
            LessonOutline(order=2, title="Talk about work, training, and job experience", topic="Work and education", grammar=["present and Perfekt", "time expressions", "polite questions"]),
            LessonOutline(order=3, title="Arrange school, childcare, and health appointments", topic="Family and health", grammar=["days and times", "dative after mit", "confirming details"]),
            LessonOutline(order=4, title="Ask about a bill, payment, or insurance notice", topic="Banking and services", grammar=["dative recipient", "question forms", "numbers and dates"]),
            LessonOutline(order=5, title="Describe locations and destinations at home or while travelling", topic="Housing and mobility", grammar=["two-way prepositions", "wo?/wohin?", "dative/accusative"]),
            LessonOutline(order=6, title="Report a recent event and understand practical messages", topic="Past events and media", grammar=["Perfekt", "Partizip II", "reading and listening strategies"])
        ]
    ),
    LevelDetail(
        code="B1",
        name="B1 - Intermediate (Zertifikat Deutsch)",
        description="Participate more independently in work, education, public services, media, and social life: explain problems, support opinions, handle disagreement, and communicate in connected speech and writing.",
        status="active",
        is_available=True,
        core_topics=[
            "Work, job search, training, and workplace communication",
            "Authorities, housing, health, and service problems",
            "Opinions, feelings, disagreement, and social contacts",
            "Media, mobility, environment, and society",
            "Formal messages, reports, and connected accounts"
        ],
        grammar_concepts=[
            GrammarConcept(name="Connected reasons and conditions", explanation="Use weil, dass, obwohl, and wenn to explain, report, and qualify ideas with accurate verb placement."),
            GrammarConcept(name="Polite negotiation and possible solutions", explanation="Use Konjunktiv II forms such as könnte, würde, hätte, and wäre for requests and hypothetical options."),
            GrammarConcept(name="Reporting processes and information", explanation="Use passive forms and relative clauses when describing procedures, notices, and events."),
            GrammarConcept(name="Narrative and formal writing", explanation="Connect past events, reasons, examples, and outcomes in clear accounts and messages.")
        ],
        lesson_outlines=[
            LessonOutline(order=1, title="Explain a work or education problem and suggest a next step", topic="Work and education", grammar=["reasons and conditions", "polite requests", "connected explanations"]),
            LessonOutline(order=2, title="Discuss opinions and handle disagreement", topic="Social contacts and conflict", grammar=["opinion markers", "concessions", "clarifying questions"]),
            LessonOutline(order=3, title="Write a formal request, reply, or complaint", topic="Authorities and services", grammar=["formal register", "subordinate clauses", "clear requests"]),
            LessonOutline(order=4, title="Understand media and compare information", topic="Media and society", grammar=["main idea and evidence", "reported information", "relative clauses"]),
            LessonOutline(order=5, title="Present a connected account and support a recommendation", topic="Mobility and environment", grammar=["narrative sequence", "examples and reasons", "Konjunktiv II"])
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
