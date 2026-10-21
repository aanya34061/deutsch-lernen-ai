"""
A1 Beginner German Curriculum and Lesson Data
"""

A1_LESSONS = [
    {
        "id": "a1-lesson-1",
        "title": "Begrüßungen und Vorstellungen (Greetings & Introductions)",
        "cefr_level": "A1",
        "module_title": "Module 1: First Steps in German",
        "topic": "Greetings & Introductions",
        "order": 1,
        "estimated_minutes": 15,
        "objectives": [
            "Greet people formally and informally at different times of day",
            "Introduce yourself with your name and say goodbye",
            "Understand the difference between informal 'du' and formal 'Sie'",
            "Conjugate the irregular verb 'sein' (to be) in the present tense"
        ],
        "explanation_en": "In German, how you greet someone depends on the time of day and how well you know the person. With friends, family, and peers, use informal German ('du'). In professional or polite everyday situations (like speaking to a stranger, shopkeeper, or teacher), use formal German ('Sie'). Notice that formal 'Sie' is always capitalized!",
        "grammar_rules": [
            {
                "name": "Conjugation of 'sein' (to be)",
                "explanation": "'sein' is the most important irregular verb in German. You must memorize its forms:",
                "pattern": "Pronoun + Verb form",
                "table": [
                    {"pronoun": "ich (I)", "verb": "bin (am)"},
                    {"pronoun": "du (you, informal)", "verb": "bist (are)"},
                    {"pronoun": "er / sie / es (he/she/it)", "verb": "ist (is)"},
                    {"pronoun": "wir (we)", "verb": "sind (are)"},
                    {"pronoun": "ihr (you all)", "verb": "seid (are)"},
                    {"pronoun": "sie / Sie (they / You, formal)", "verb": "sind (are)"}
                ]
            },
            {
                "name": "Introducing Yourself with 'heißen'",
                "explanation": "To state your name, use 'Ich heiße [Name]' (literally: I am called...) or 'Ich bin [Name]' (I am...).",
                "pattern": "Ich heiße ... / Mein Name ist ...",
                "table": [
                    {"german": "Wie heißen Sie?", "english": "What is your name? (formal)"},
                    {"german": "Wie heißt du?", "english": "What is your name? (informal)"},
                    {"german": "Ich heiße Anna.", "english": "My name is Anna."}
                ]
            }
        ],
        "examples": [
            {"german": "Guten Tag! Ich bin Lukas.", "english": "Good day! I am Lukas."},
            {"german": "Hallo! Wie geht es dir?", "english": "Hello! How are you? (informal)"},
            {"german": "Guten Abend! Wie heißen Sie?", "english": "Good evening! What is your name? (formal)"},
            {"german": "Auf Wiedersehen! Bis bald.", "english": "Goodbye! See you soon."}
        ],
        "vocabulary": [
            {"word": "Hallo", "article": "", "plural": "", "meaning_en": "hello / hi", "example_de": "Hallo, wie geht's?", "example_en": "Hi, how are you?"},
            {"word": "Guten Morgen", "article": "", "plural": "", "meaning_en": "good morning", "example_de": "Guten Morgen, Frau Müller!", "example_en": "Good morning, Mrs. Müller!"},
            {"word": "Guten Tag", "article": "", "plural": "", "meaning_en": "good day / hello", "example_de": "Guten Tag allerseits!", "example_en": "Good day everyone!"},
            {"word": "Guten Abend", "article": "", "plural": "", "meaning_en": "good evening", "example_de": "Guten Abend, mein Name ist Schmidt.", "example_en": "Good evening, my name is Schmidt."},
            {"word": "Auf Wiedersehen", "article": "", "plural": "", "meaning_en": "goodbye (formal)", "example_de": "Auf Wiedersehen, Herr Weber!", "example_en": "Goodbye, Mr. Weber!"},
            {"word": "Tschüss", "article": "", "plural": "", "meaning_en": "bye (informal)", "example_de": "Tschüss, bis morgen!", "example_en": "Bye, see you tomorrow!"},
            {"word": "der Name", "article": "der", "plural": "die Namen", "meaning_en": "the name", "example_de": "Mein Name ist David.", "example_en": "My name is David."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich bin heiße Peter.",
                "correct": "Ich heiße Peter. (or: Ich bin Peter.)",
                "explanation": "Do not combine 'bin' and 'heiße'. Use either 'Ich heiße...' or 'Ich bin...'."
            },
            {
                "wrong": "Auf wiedersehen (lowercase W)",
                "correct": "Auf Wiedersehen",
                "explanation": "'Wiedersehen' is a noun in this greeting and must always be capitalized."
            }
        ],
        "summary_en": "In this lesson you learned key greetings (Guten Morgen, Guten Tag, Guten Abend, Hallo), formal vs. informal addresses (Sie vs. du), the present tense of 'sein', and how to introduce yourself and say farewell (Auf Wiedersehen, Tschüss).",
        "exercises": [
            {
                "id": "a1-l1-ex1",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Which form of 'sein' correctly completes the sentence: 'Ich ___ Markus.'?",
                "options": ["bin", "bist", "ist", "sind"],
                "correct_answer": "bin",
                "explanation_en": "With the first-person singular pronoun 'ich', the correct form of 'sein' is 'bin'.",
                "correct_sentence_de": "Ich bin Markus."
            },
            {
                "id": "a1-l1-ex2",
                "type": "fill_blank",
                "skill": "vocabulary",
                "difficulty": "beginner",
                "question": "Fill in the blank with the polite formal goodbye:",
                "prompt": "Auf __________, Herr Becker!",
                "correct_answer": "Wiedersehen",
                "acceptable_alternatives": ["wiedersehen"],
                "explanation_en": "'Auf Wiedersehen' is the standard polite formal farewell in German.",
                "correct_sentence_de": "Auf Wiedersehen, Herr Becker!"
            },
            {
                "id": "a1-l1-ex3",
                "type": "sentence_order",
                "skill": "writing",
                "difficulty": "beginner",
                "question": "Arrange these words into a grammatically correct German sentence:",
                "options": ["Tag", "heiße", "Ich", "Guten", "Laura"],
                "correct_answer": "Guten Tag Ich heiße Laura",
                "acceptable_alternatives": [
                    "Guten Tag ich heiße Laura",
                    "Ich heiße Laura Guten Tag"
                ],
                "explanation_en": "'Guten Tag' is the greeting placed first, followed by Subject + Verb ('Ich heiße Laura').",
                "correct_sentence_de": "Guten Tag, ich heiße Laura."
            },
            {
                "id": "a1-l1-ex4",
                "type": "matching",
                "skill": "vocabulary",
                "difficulty": "beginner",
                "question": "Match the German greeting with its correct English meaning:",
                "matching_pairs": [
                    {"german": "Guten Morgen", "english": "Good morning"},
                    {"german": "Guten Abend", "english": "Good evening"},
                    {"german": "Tschüss", "english": "Bye (informal)"},
                    {"german": "Auf Wiedersehen", "english": "Goodbye (formal)"}
                ],
                "correct_answer": {
                    "Guten Morgen": "Good morning",
                    "Guten Abend": "Good evening",
                    "Tschüss": "Bye (informal)",
                    "Auf Wiedersehen": "Goodbye (formal)"
                },
                "explanation_en": "Standard German greetings correspond to specific times of day and social contexts."
            },
            {
                "id": "a1-l1-ex5",
                "type": "true_false",
                "skill": "reading",
                "difficulty": "beginner",
                "question": "In German, the formal pronoun 'Sie' is always capitalized when addressing someone politely.",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation_en": "Formal 'Sie' (and its possessive 'Ihr') is always written with a capital letter to distinguish it from 'sie' (she or they).",
                "correct_sentence_de": "Wie heißen Sie?"
            }
        ]
    },
    {
        "id": "a1-lesson-2",
        "title": "Bestimmte und unbestimmte Artikel (German Articles: der, die, das)",
        "cefr_level": "A1",
        "module_title": "Module 1: First Steps in German",
        "topic": "Articles & Gender",
        "order": 2,
        "estimated_minutes": 20,
        "objectives": [
            "Learn the three grammatical genders: masculine (der), feminine (die), and neuter (das)",
            "Use indefinite articles: ein, eine",
            "Understand that all German nouns are always capitalized",
            "Identify gender clues from common noun endings"
        ],
        "explanation_en": "Every German noun has a grammatical gender: masculine (der), feminine (die), or neuter (das). In the plural, ALL genders share the definite article 'die'. In English, you only have 'the', but in German you must learn the article alongside every noun! In this app, we color-code articles: der = blue, die = red, das = green.",
        "grammar_rules": [
            {
                "name": "Definite vs. Indefinite Articles (Nominative)",
                "explanation": "The Nominative case is the subject of the sentence:",
                "table": [
                    {"gender": "Masculine (der)", "definite": "der Mann (the man)", "indefinite": "ein Mann (a man)"},
                    {"gender": "Feminine (die)", "definite": "die Frau (the woman)", "indefinite": "eine Frau (a woman)"},
                    {"gender": "Neuter (das)", "definite": "das Kind (the child)", "indefinite": "ein Kind (a child)"},
                    {"gender": "Plural (die)", "definite": "die Kinder (the children)", "indefinite": "— (Kinder)"}
                ]
            },
            {
                "name": "Helpful Gender Endings",
                "explanation": "Certain noun endings reliably indicate gender:",
                "table": [
                    {"ending": "-ung, -heit, -keit, -schaft, -ei", "gender": "Almost always feminine (die)", "example": "die Zeitung, die Freiheit"},
                    {"ending": "-chen, -lein, -ment, -um", "gender": "Almost always neuter (das)", "example": "das Mädchen, das Zentrum"},
                    {"ending": "-ling, -or, -ist, -ismus", "gender": "Almost always masculine (der)", "example": "der Motor, der Optimismus"}
                ]
            }
        ],
        "examples": [
            {"german": "Das Buch ist interessant.", "english": "The book is interesting."},
            {"german": "Der Tisch ist neu.", "english": "The table is new."},
            {"german": "Die Lampe ist hell.", "english": "The lamp is bright."},
            {"german": "Das ist ein Stuhl und eine Tasche.", "english": "That is a chair and a bag."}
        ],
        "vocabulary": [
            {"word": "der Tisch", "article": "der", "plural": "die Tische", "meaning_en": "the table", "example_de": "Der Tisch steht in der Küche.", "example_en": "The table is in the kitchen."},
            {"word": "der Stuhl", "article": "der", "plural": "die Stühle", "meaning_en": "the chair", "example_de": "Der Stuhl ist bequem.", "example_en": "The chair is comfortable."},
            {"word": "die Lampe", "article": "die", "plural": "die Lampen", "meaning_en": "the lamp", "example_de": "Die Lampe ist an.", "example_en": "The lamp is on."},
            {"word": "die Tasche", "article": "die", "plural": "die Taschen", "meaning_en": "the bag", "example_de": "Wo ist meine Tasche?", "example_en": "Where is my bag?"},
            {"word": "das Buch", "article": "das", "plural": "die Bücher", "meaning_en": "the book", "example_de": "Das Buch liegt auf dem Tisch.", "example_en": "The book is lying on the table."},
            {"word": "das Auto", "article": "das", "plural": "die Autos", "meaning_en": "the car", "example_de": "Das Auto fährt schnell.", "example_en": "The car drives fast."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich lese das zeitung.",
                "correct": "Ich lese die Zeitung.",
                "explanation": "1) 'Zeitung' ends in '-ung' so it is feminine ('die'). 2) All nouns must be capitalized."
            },
            {
                "wrong": "ein Frau",
                "correct": "eine Frau",
                "explanation": "Feminine nouns take 'eine' for the indefinite article in the nominative case."
            }
        ],
        "summary_en": "German has three genders: der (masculine), die (feminine), das (neuter). Their indefinite counterparts are ein, eine, ein. Always memorize every noun with its article and capitalize the first letter.",
        "exercises": [
            {
                "id": "a1-l2-ex1",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "What is the correct definite article for 'Buch' (book)?",
                "options": ["der", "die", "das"],
                "correct_answer": "das",
                "explanation_en": "'Buch' is neuter in German: 'das Buch'.",
                "correct_sentence_de": "Das Buch ist gut."
            },
            {
                "id": "a1-l2-ex2",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Fill in the blank with the correct indefinite article (ein or eine):",
                "prompt": "Das ist __________ Lampe.",
                "correct_answer": "eine",
                "explanation_en": "'Lampe' is feminine ('die Lampe'), so its indefinite article is 'eine'.",
                "correct_sentence_de": "Das ist eine Lampe."
            },
            {
                "id": "a1-l2-ex3",
                "type": "translate",
                "skill": "writing",
                "difficulty": "beginner",
                "question": "Translate into German: 'The table is new.'",
                "correct_answer": "Der Tisch ist neu.",
                "acceptable_alternatives": [
                    "Der Tisch ist neu",
                    "der tisch ist neu"
                ],
                "explanation_en": "'Table' is masculine in German ('der Tisch'), and 'neu' means 'new'. Remember to capitalize Tisch!",
                "correct_sentence_de": "Der Tisch ist neu."
            },
            {
                "id": "a1-l2-ex4",
                "type": "sentence_order",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Arrange these words into the correct German sentence order:",
                "options": ["ist", "sehr", "Das", "interessant", "Buch"],
                "correct_answer": "Das Buch ist sehr interessant",
                "acceptable_alternatives": [
                    "das buch ist sehr interessant"
                ],
                "explanation_en": "Subject ('Das Buch') + Verb ('ist') + Predicate ('sehr interessant'). Verb takes position 2.",
                "correct_sentence_de": "Das Buch ist sehr interessant."
            }
        ]
    },
    {
        "id": "a1-lesson-3",
        "title": "Regelmäßige Verben im Präsens (Regular Present Tense Verbs)",
        "cefr_level": "A1",
        "module_title": "Module 2: Everyday Actions & Sentences",
        "topic": "Verbs & Sentence Structure",
        "order": 3,
        "estimated_minutes": 20,
        "objectives": [
            "Learn the regular German verb conjugation endings: -e, -st, -t, -en, -t, -en",
            "Conjugate common verbs: kommen, wohnen, lernen, machen, trinken",
            "Master the golden German rule: Verb is in Position 2 in statements"
        ],
        "explanation_en": "Most German verbs end in '-en' in their infinitive (base) form. To conjugate a regular verb in the present tense, remove '-en' to find the verb stem, and attach the ending that matches the subject pronoun.",
        "grammar_rules": [
            {
                "name": "Regular Verb Endings Table (e.g., 'lernen' - to learn)",
                "explanation": "Stem: lern-",
                "pattern": "Stem + Ending",
                "table": [
                    {"pronoun": "ich (I)", "ending": "-e", "example": "ich lerne"},
                    {"pronoun": "du (you)", "ending": "-st", "example": "du lernst"},
                    {"pronoun": "er / sie / es (he/she/it)", "ending": "-t", "example": "er lernt"},
                    {"pronoun": "wir (we)", "ending": "-en", "example": "wir lernen"},
                    {"pronoun": "ihr (you all)", "ending": "-t", "example": "ihr lernt"},
                    {"pronoun": "sie / Sie (they/You)", "ending": "-en", "example": "sie lernen"}
                ]
            },
            {
                "name": "Verb in Position 2",
                "explanation": "In standard German declarative sentences, the conjugated verb ALWAYS sits in position 2, even if time or place is put first!",
                "table": [
                    {"position_1": "Ich", "position_2 (Verb)": "lerne", "rest": "heute Deutsch."},
                    {"position_1": "Heute", "position_2 (Verb)": "lerne", "rest": "ich Deutsch."}
                ]
            }
        ],
        "examples": [
            {"german": "Ich komme aus Deutschland.", "english": "I come from Germany."},
            {"german": "Wo wohnst du?", "english": "Where do you live?"},
            {"german": "Wir trinken Kaffee.", "english": "We drink coffee."},
            {"german": "Er macht Sport am Nachmittag.", "english": "He does sports in the afternoon."}
        ],
        "vocabulary": [
            {"word": "kommen", "article": "", "plural": "", "meaning_en": "to come", "example_de": "Woher kommst du?", "example_en": "Where do you come from?"},
            {"word": "wohnen", "article": "", "plural": "", "meaning_en": "to live / reside", "example_de": "Ich wohne in Berlin.", "example_en": "I live in Berlin."},
            {"word": "lernen", "article": "", "plural": "", "meaning_en": "to learn / study", "example_de": "Wir lernen Deutsch.", "example_en": "We are learning German."},
            {"word": "trinken", "article": "", "plural": "", "meaning_en": "to drink", "example_de": "Trinkst du Tee?", "example_en": "Do you drink tea?"},
            {"word": "machen", "article": "", "plural": "", "meaning_en": "to do / make", "example_de": "Was machst du heute?", "example_en": "What are you doing today?"}
        ],
        "common_mistakes": [
            {
                "wrong": "Heute ich lerne Deutsch.",
                "correct": "Heute lerne ich Deutsch.",
                "explanation": "In German, the conjugated verb must remain in Position 2! When 'Heute' takes position 1, the subject moves to position 3."
            }
        ],
        "summary_en": "Remove -en from the infinitive to get the stem, then add: -e (ich), -st (du), -t (er/sie/es), -en (wir), -t (ihr), -en (sie/Sie). In statements, the conjugated verb is always in Position 2.",
        "exercises": [
            {
                "id": "a1-l3-ex1",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Conjugate the verb 'wohnen' for 'du':",
                "prompt": "Wo __________ du?",
                "correct_answer": "wohnst",
                "explanation_en": "The ending for 'du' with regular verbs is '-st': wohn- + st = wohnst.",
                "correct_sentence_de": "Wo wohnst du?"
            },
            {
                "id": "a1-l3-ex2",
                "type": "sentence_order",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Arrange these words obeying the Verb-in-Position-2 rule:",
                "options": ["in", "Berlin", "Heute", "wohne", "ich"],
                "correct_answer": "Heute wohne ich in Berlin",
                "acceptable_alternatives": [
                    "Ich wohne heute in Berlin",
                    "ich wohne heute in berlin"
                ],
                "explanation_en": "When an adverb like 'Heute' is placed first, the verb 'wohne' takes position 2, followed immediately by subject 'ich'.",
                "correct_sentence_de": "Heute wohne ich in Berlin."
            },
            {
                "id": "a1-l3-ex3",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Which verb form completes: 'Wir ___ fleißig Deutsch.'?",
                "options": ["lerne", "lernst", "lernt", "lernen"],
                "correct_answer": "lernen",
                "explanation_en": "The pronoun 'wir' takes the regular ending '-en': wir lernen.",
                "correct_sentence_de": "Wir lernen fleißig Deutsch."
            }
        ]
    },
    {
        "id": "a1-lesson-4",
        "title": "Der Akkusativ und Negation (Accusative Case & Negation: nicht vs. kein)",
        "cefr_level": "A1",
        "module_title": "Module 2: Everyday Actions & Sentences",
        "topic": "Accusative & Negation",
        "order": 4,
        "estimated_minutes": 25,
        "objectives": [
            "Understand the Accusative case for direct objects",
            "Learn how masculine 'der/ein' changes to 'den/einen' while feminine and neuter stay unchanged",
            "Master the difference between 'nicht' (negates verbs/adjectives) and 'kein' (negates nouns with ein/zero article)"
        ],
        "explanation_en": "When a noun is the direct object (the thing being acted upon or received), it is in the Accusative case. The wonderful secret of the German accusative is that ONLY masculine nouns change! Feminine (die/eine), neuter (das/ein), and plural (die) look exactly the same as in the Nominative.",
        "grammar_rules": [
            {
                "name": "Nominative vs. Accusative Articles",
                "explanation": "Notice that only masculine transforms (der -> den, ein -> einen):",
                "table": [
                    {"gender": "Masculine", "nominative": "der / ein Tisch", "accusative": "den / einen Tisch"},
                    {"gender": "Feminine", "nominative": "die / eine Suppe", "accusative": "die / eine Suppe"},
                    {"gender": "Neuter", "nominative": "das / ein Brot", "accusative": "das / ein Brot"},
                    {"gender": "Plural", "nominative": "die Äpfel", "accusative": "die Äpfel"}
                ]
            },
            {
                "name": "Negation: 'kein' vs. 'nicht'",
                "explanation": "Rule of thumb:\n• Use 'kein' where you could say 'ein' or with uncounted nouns.\n• Use 'nicht' to negate verbs, adjectives, adverbs, or specific definite nouns.",
                "table": [
                    {"type": "Noun with 'ein'", "positive": "Ich habe einen Hund.", "negative": "Ich habe keinen Hund."},
                    {"type": "Verb / Adjective", "positive": "Ich verstehe.", "negative": "Ich verstehe nicht."}
                ]
            }
        ],
        "examples": [
            {"german": "Ich habe einen Bruder.", "english": "I have a brother. (masculine accusative)"},
            {"german": "Möchtest du einen Kaffee?", "english": "Would you like a coffee?"},
            {"german": "Ich trinke keinen Kaffee, ich trinke Tee.", "english": "I drink no coffee, I drink tea."},
            {"german": "Das Buch ist nicht teuer.", "english": "The book is not expensive."}
        ],
        "vocabulary": [
            {"word": "haben", "article": "", "plural": "", "meaning_en": "to have (takes accusative)", "example_de": "Ich habe einen Hund.", "example_en": "I have a dog."},
            {"word": "brauchen", "article": "", "plural": "", "meaning_en": "to need", "example_de": "Ich brauche einen Stift.", "example_en": "I need a pen."},
            {"word": "der Kaffee", "article": "der", "plural": "die Kaffees", "meaning_en": "the coffee", "example_de": "Der Kaffee schmeckt gut.", "example_en": "The coffee tastes good."},
            {"word": "der Apfel", "article": "der", "plural": "die Äpfel", "meaning_en": "the apple", "example_de": "Er isst einen Apfel.", "example_en": "He is eating an apple."},
            {"word": "das Brot", "article": "das", "plural": "die Brote", "meaning_en": "the bread", "example_de": "Wir kaufen frisches Brot.", "example_en": "We buy fresh bread."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich habe ein Hund.",
                "correct": "Ich habe einen Hund.",
                "explanation": "'Hund' is masculine ('der Hund') and is the direct object of 'haben', so it takes the accusative ending: 'einen Hund'."
            },
            {
                "wrong": "Ich habe nicht Hund.",
                "correct": "Ich habe keinen Hund.",
                "explanation": "Nouns that would take 'ein' are negated with 'kein / keine / keinen'."
            }
        ],
        "summary_en": "Direct objects take the Accusative case. Only masculine changes (der -> den, ein -> einen, kein -> keinen). Feminine and neuter remain identical to nominative. Use 'kein' to negate nouns, and 'nicht' for verbs and adjectives.",
        "exercises": [
            {
                "id": "a1-l4-ex1",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Which article correctly completes: 'Ich möchte ___ Kaffee, bitte.' (der Kaffee)?",
                "options": ["ein", "eine", "einen"],
                "correct_answer": "einen",
                "explanation_en": "'Kaffee' is masculine ('der Kaffee') and acts as direct object here, requiring accusative 'einen'.",
                "correct_sentence_de": "Ich möchte einen Kaffee, bitte."
            },
            {
                "id": "a1-l4-ex2",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "beginner",
                "question": "Fill in the blank with 'keinen' or 'nicht':",
                "prompt": "Ich habe leider __________ Zeit.",
                "correct_answer": "keine",
                "acceptable_alternatives": ["Keine"],
                "explanation_en": "'Zeit' is feminine ('die Zeit'), so its negation is 'keine'.",
                "correct_sentence_de": "Ich habe leider keine Zeit."
            },
            {
                "id": "a1-l4-ex3",
                "type": "translate",
                "skill": "writing",
                "difficulty": "beginner",
                "question": "Translate: 'He is eating an apple.' (der Apfel)",
                "correct_answer": "Er isst einen Apfel.",
                "acceptable_alternatives": [
                    "Er isst einen Apfel",
                    "er isst einen apfel"
                ],
                "explanation_en": "'Apfel' is masculine accusative, so 'ein' becomes 'einen'. Remember to capitalize Apfel!",
                "correct_sentence_de": "Er isst einen Apfel."
            }
        ]
    }
]
