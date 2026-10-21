"""
A2 Elementary German Curriculum and Lesson Data
"""

A2_LESSONS = [
    {
        "id": "a2-lesson-1",
        "title": "Trennbare Verben im Alltag (Separable Verbs in Daily Life)",
        "cefr_level": "A2",
        "module_title": "Module 1: Routines & Actions in A2",
        "topic": "Separable Verbs",
        "order": 1,
        "estimated_minutes": 20,
        "objectives": [
            "Recognize common separable prefixes: auf-, an-, aus-, mit-, ein-, ab-",
            "Master sentence structure: prefix splits and goes to the absolute end of the clause",
            "Learn daily routine verbs: aufstehen, einkaufen, anrufen, mitkommen"
        ],
        "explanation_en": "In German, many verbs have prefixes that detach in the present tense. The verb stem stays in Position 2 and conjugates as usual, while the detached prefix flies all the way to the very end of the main clause. Common separable prefixes are: ab-, an-, auf-, aus-, ein-, mit-, vor-, zu-.",
        "grammar_rules": [
            {
                "name": "Sentence Bracket (Satzklammer)",
                "explanation": "The conjugated verb stem is in position 2, and the separable prefix is at the end:",
                "pattern": "Subject + [Stem in Pos 2] + ... + [Prefix at End]",
                "table": [
                    {"verb": "aufstehen (to get up)", "example": "Ich stehe um 7 Uhr auf."},
                    {"verb": "einkaufen (to shop)", "example": "Wir kaufen im Supermarkt ein."},
                    {"verb": "anrufen (to call)", "example": "Er ruft seine Mutter an."}
                ]
            }
        ],
        "examples": [
            {"german": "Wann stehst du morgens auf?", "english": "When do you get up in the morning?"},
            {"german": "Ich kaufe heute Abend im Supermarkt ein.", "english": "I am shopping at the supermarket tonight."},
            {"german": "Rufst du mich später an?", "english": "Will you call me later?"}
        ],
        "vocabulary": [
            {"word": "aufstehen", "article": "", "plural": "", "meaning_en": "to get up / wake up", "example_de": "Ich stehe früh auf.", "example_en": "I get up early."},
            {"word": "einkaufen", "article": "", "plural": "", "meaning_en": "to grocery shop", "example_de": "Samstags kaufe ich ein.", "example_en": "On Saturdays I go shopping."},
            {"word": "anrufen", "article": "", "plural": "", "meaning_en": "to call on the phone", "example_de": "Er ruft den Arzt an.", "example_en": "He calls the doctor."},
            {"word": "fernsehen", "article": "", "plural": "", "meaning_en": "to watch TV", "example_de": "Sie sieht abends fern.", "example_en": "She watches TV in the evening."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich aufstehe um 7 Uhr.",
                "correct": "Ich stehe um 7 Uhr auf.",
                "explanation": "In main clauses, you must separate the prefix 'auf' and send it to the end."
            }
        ],
        "summary_en": "Separable verbs split in the present tense: conjugated stem in Position 2, prefix at the very end of the sentence.",
        "exercises": [
            {
                "id": "a2-l1-ex1",
                "type": "sentence_order",
                "skill": "grammar",
                "difficulty": "intermediate",
                "question": "Arrange the words into the correct German separable verb order:",
                "options": ["stehe", "Ich", "auf", "7 Uhr", "um"],
                "correct_answer": "Ich stehe um 7 Uhr auf",
                "acceptable_alternatives": [
                    "ich stehe um 7 uhr auf",
                    "Um 7 Uhr stehe ich auf"
                ],
                "explanation_en": "Stem 'stehe' is in position 2; prefix 'auf' goes to the end of the sentence.",
                "correct_sentence_de": "Ich stehe um 7 Uhr auf."
            },
            {
                "id": "a2-l1-ex2",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "intermediate",
                "question": "Complete the sentence with the detached prefix of 'anrufen':",
                "prompt": "Lisa ruft ihren Bruder __________.",
                "correct_answer": "an",
                "explanation_en": "The prefix of 'anrufen' is 'an', which separates and moves to the end.",
                "correct_sentence_de": "Lisa ruft ihren Bruder an."
            }
        ]
    },
    {
        "id": "a2-lesson-2",
        "title": "Das Perfekt: Vergangenheit im Gespräch (The Perfect Tense in Spoken German)",
        "cefr_level": "A2",
        "module_title": "Module 2: Describing Past Events",
        "topic": "Past Tense (Perfekt)",
        "order": 2,
        "estimated_minutes": 25,
        "objectives": [
            "Understand that Perfekt is the primary past tense used in spoken German",
            "Form Perfekt using auxiliary verb (haben or sein) + Partizip II at the end",
            "Know when to use 'sein' (verbs of movement or change of state) vs 'haben'"
        ],
        "explanation_en": "In everyday conversational German, past actions are almost always expressed using the **Perfekt** tense. It consists of two parts:\n1. An auxiliary verb ('haben' or 'sein') conjugated in Position 2.\n2. The past participle (**Partizip II**, usually starting with ge-) at the very end of the sentence.",
        "grammar_rules": [
            {
                "name": "Choosing 'haben' vs. 'sein'",
                "explanation": "• Use 'sein' with verbs of movement (gehen, fahren, kommen) or change of condition (aufwachen, sterben), plus 'sein' and 'bleiben'.\n• Use 'haben' with all transitive verbs (verbs taking an accusative object) and most other verbs.",
                "table": [
                    {"auxiliary": "haben", "example": "Ich habe Deutsch gelernt.", "meaning": "I learned German."},
                    {"auxiliary": "sein", "example": "Ich bin nach Berlin gefahren.", "meaning": "I traveled to Berlin."}
                ]
            }
        ],
        "examples": [
            {"german": "Was hast du gestern gemacht?", "english": "What did you do yesterday?"},
            {"german": "Wir haben eine Pizza gegessen.", "english": "We ate a pizza."},
            {"german": "Sie ist nach Hause gegangen.", "english": "She went home."}
        ],
        "vocabulary": [
            {"word": "gestern", "article": "", "plural": "", "meaning_en": "yesterday", "example_de": "Gestern war Sonntag.", "example_en": "Yesterday was Sunday."},
            {"word": "gemacht", "article": "", "plural": "", "meaning_en": "done / made (Partizip II)", "example_de": "Ich habe die Hausaufgaben gemacht.", "example_en": "I did the homework."},
            {"word": "gegangen", "article": "", "plural": "", "meaning_en": "gone / walked (Partizip II of gehen)", "example_de": "Er ist nach Hause gegangen.", "example_en": "He went home."},
            {"word": "gefahren", "article": "", "plural": "", "meaning_en": "traveled / driven (Partizip II of fahren)", "example_de": "Wir sind mit dem Zug gefahren.", "example_en": "We traveled by train."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich habe nach Hause gegangen.",
                "correct": "Ich bin nach Hause gegangen.",
                "explanation": "'gehen' is a verb of movement and requires 'sein' as its auxiliary verb in the Perfekt."
            }
        ],
        "summary_en": "Perfekt = conjugated haben/sein in Position 2 + Partizip II at the end of the sentence. Use 'sein' for movement or state change.",
        "exercises": [
            {
                "id": "a2-l2-ex1",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "intermediate",
                "question": "Which auxiliary verb correctly completes: 'Wir ___ gestern nach München gefahren.'?",
                "options": ["haben", "sind", "hat", "ist"],
                "correct_answer": "sind",
                "explanation_en": "'fahren' describes motion from one place to another, so it takes 'sein' ('wir sind').",
                "correct_sentence_de": "Wir sind gestern nach München gefahren."
            },
            {
                "id": "a2-l2-ex2",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "intermediate",
                "question": "Type the correct auxiliary verb (habe or bin):",
                "prompt": "Ich __________ heute viel Deutsch gelernt.",
                "correct_answer": "habe",
                "explanation_en": "'lernen' takes 'haben': 'Ich habe gelernt'.",
                "correct_sentence_de": "Ich habe heute viel Deutsch gelernt."
            }
        ]
    }
]
