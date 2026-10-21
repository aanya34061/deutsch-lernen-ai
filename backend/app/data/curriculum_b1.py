"""
B1 Intermediate German Curriculum and Lesson Data
"""

B1_LESSONS = [
    {
        "id": "b1-lesson-1",
        "title": "Nebensätze und Verbstellung (Subordinate Clauses: weil, dass, obwohl)",
        "cefr_level": "B1",
        "module_title": "Module 1: Complex Sentence Structures",
        "topic": "Subordinate Clauses & Word Order",
        "order": 1,
        "estimated_minutes": 25,
        "objectives": [
            "Understand how subordinating conjunctions change word order",
            "Send the conjugated verb to the absolute end of the subordinate clause",
            "Express causes and opinions using 'weil', 'dass', and 'obwohl'"
        ],
        "explanation_en": "In German main clauses, the conjugated verb is in Position 2. But when introducing a subordinate clause with conjunctions such as **weil** (because), **dass** (that), **obwohl** (although), or **wenn** (if/when), the conjugated verb is pushed to the very end of that clause!",
        "grammar_rules": [
            {
                "name": "The Verb-at-the-End Rule",
                "explanation": "Conjunction + Subject + ... + Conjugated Verb at the end:",
                "pattern": "[Main clause], weil [Subject] ... [Verb at End].",
                "table": [
                    {"conjunction": "weil (because)", "example": "Ich lerne Deutsch, weil ich in Berlin arbeiten will."},
                    {"conjunction": "dass (that)", "example": "Ich weiß, dass Deutsch logisch ist."},
                    {"conjunction": "obwohl (although)", "example": "Er geht spazieren, obwohl es regnet."}
                ]
            }
        ],
        "examples": [
            {"german": "Ich bleibe zu Hause, weil ich krank bin.", "english": "I am staying at home because I am sick."},
            {"german": "Sie freut sich, dass du kommst.", "english": "She is happy that you are coming."},
            {"german": "Obwohl er müde ist, liest er ein Buch.", "english": "Although he is tired, he is reading a book."}
        ],
        "vocabulary": [
            {"word": "weil", "article": "", "plural": "", "meaning_en": "because (kicks verb to end)", "example_de": "Ich lerne, weil es Spaß macht.", "example_en": "I study because it is fun."},
            {"word": "dass", "article": "", "plural": "", "meaning_en": "that (subordinating conjunction)", "example_de": "Ich glaube, dass er recht hat.", "example_en": "I believe that he is right."},
            {"word": "obwohl", "article": "", "plural": "", "meaning_en": "although / even though", "example_de": "Obwohl es kalt ist, geht er raus.", "example_en": "Although it's cold, he goes out."},
            {"word": "die Meinung", "article": "die", "plural": "die Meinungen", "meaning_en": "the opinion", "example_de": "Meiner Meinung nach ist das wichtig.", "example_en": "In my opinion that is important."}
        ],
        "common_mistakes": [
            {
                "wrong": "Ich lerne Deutsch, weil ich will in Berlin arbeiten.",
                "correct": "Ich lerne Deutsch, weil ich in Berlin arbeiten will.",
                "explanation": "In 'weil' clauses, the conjugated modal verb 'will' must go to the very end of the clause."
            }
        ],
        "summary_en": "Subordinating conjunctions (weil, dass, obwohl, wenn) send the conjugated verb to the end of the subordinate clause.",
        "exercises": [
            {
                "id": "b1-l1-ex1",
                "type": "sentence_order",
                "skill": "writing",
                "difficulty": "intermediate",
                "question": "Arrange the words into a correct German subordinate clause with 'weil':",
                "options": ["krank", "bleibe", "zu Hause", "ich", "weil", "Ich", "bin"],
                "correct_answer": "Ich bleibe zu Hause weil ich krank bin",
                "acceptable_alternatives": [
                    "ich bleibe zu hause weil ich krank bin"
                ],
                "explanation_en": "Main clause: 'Ich bleibe zu Hause'. Subordinate clause: 'weil ich krank bin' (verb 'bin' at end).",
                "correct_sentence_de": "Ich bleibe zu Hause, weil ich krank bin."
            },
            {
                "id": "b1-l1-ex2",
                "type": "multiple_choice",
                "skill": "grammar",
                "difficulty": "intermediate",
                "question": "Which sentence has correct B1 German word order?",
                "options": [
                    "Ich weiß, dass er heute kommt.",
                    "Ich weiß, dass er kommt heute.",
                    "Ich weiß, dass kommt er heute."
                ],
                "correct_answer": "Ich weiß, dass er heute kommt.",
                "explanation_en": "In a 'dass'-clause, the conjugated verb ('kommt') must be at the very end.",
                "correct_sentence_de": "Ich weiß, dass er heute kommt."
            }
        ]
    },
    {
        "id": "b1-lesson-2",
        "title": "Passiv Präsens Grundlagen (Passive Voice Foundations)",
        "cefr_level": "B1",
        "module_title": "Module 2: Advanced Expression & Grammar",
        "topic": "Passive Voice",
        "order": 2,
        "estimated_minutes": 25,
        "objectives": [
            "Understand the purpose of the passive voice (focusing on the action rather than the actor)",
            "Form Vorgangspassiv Präsens: werden (conjugated) + Partizip II at the end",
            "Identify agent marker 'von' + Dative"
        ],
        "explanation_en": "In the passive voice, the object of an action becomes the subject of the sentence. In German, the present passive (**Vorgangspassiv**) is formed using the auxiliary verb **werden** in Position 2 and the **Partizip II** (past participle) at the end.",
        "grammar_rules": [
            {
                "name": "Conjugation of 'werden' in the Present Tense",
                "explanation": "werden is irregular in the 2nd and 3rd person singular:",
                "table": [
                    {"pronoun": "ich", "form": "werde"},
                    {"pronoun": "du", "form": "wirst"},
                    {"pronoun": "er / sie / es", "form": "wird"},
                    {"pronoun": "wir", "form": "werden"},
                    {"pronoun": "ihr", "form": "werdet"},
                    {"pronoun": "sie / Sie", "form": "werden"}
                ]
            },
            {
                "name": "Passive Formula",
                "explanation": "Subject (former object) + werden (conjugated) + [von + Dativ] + Partizip II at end.",
                "pattern": "Das Haus wird gebaut.",
                "table": [
                    {"active": "Der Bäcker backt das Brot.", "passive": "Das Brot wird (vom Bäcker) gebacken."}
                ]
            }
        ],
        "examples": [
            {"german": "Das Auto wird repariert.", "english": "The car is being repaired."},
            {"german": "Die E-Mail wird heute geschickt.", "english": "The email is being sent today."},
            {"german": "Deutsch wird in vielen Ländern gesprochen.", "english": "German is spoken in many countries."}
        ],
        "vocabulary": [
            {"word": "werden", "article": "", "plural": "", "meaning_en": "to become / passive auxiliary", "example_de": "Das Haus wird renoviert.", "example_en": "The house is being renovated."},
            {"word": "repariert", "article": "", "plural": "", "meaning_en": "repaired (Partizip II)", "example_de": "Der Computer wird repariert.", "example_en": "The computer is being repaired."},
            {"word": "gesprochen", "article": "", "plural": "", "meaning_en": "spoken (Partizip II of sprechen)", "example_de": "Hier wird Deutsch gesprochen.", "example_en": "German is spoken here."}
        ],
        "common_mistakes": [
            {
                "wrong": "Das Brot ist gebacken von Bäcker.",
                "correct": "Das Brot wird vom Bäcker gebacken.",
                "explanation": "Present passive requires 'werden', not 'sein'."
            }
        ],
        "summary_en": "Passive Voice = conjugated 'werden' + Partizip II at the end of the sentence.",
        "exercises": [
            {
                "id": "b1-l2-ex1",
                "type": "fill_blank",
                "skill": "grammar",
                "difficulty": "advanced",
                "question": "Complete the passive sentence with the correct form of 'werden':",
                "prompt": "Das Auto __________ in der Werkstatt repariert.",
                "correct_answer": "wird",
                "explanation_en": "'Das Auto' is third person singular (es), so 'werden' conjugates to 'wird'.",
                "correct_sentence_de": "Das Auto wird in der Werkstatt repariert."
            }
        ]
    }
]
