"""
Starter collection of German Reading (Lesen) Practice Exercises for CEFR A1, A2, and B1.
Includes authentic German texts, vocabulary hints with English definitions, and objective comprehension questions.
"""

STARTING_READING_EXERCISES = [
    # ==================== CEFR A1 (Beginner) ====================
    {
        "id": "read-a1-1",
        "is_seeded": True,
        "title": "Im Café am Marktplatz (At the Marketplace Café)",
        "cefr_level": "A1",
        "topic": "Food, Drinks & Ordering",
        "difficulty": "Easy",
        "text_type": "dialogue",
        "passage_de": (
            "Kellner: Guten Tag! Was möchten Sie bestellen?\n"
            "Anna: Guten Tag. Ich möchte bitte eine Tasse Kaffee mit Milch und Zucker.\n"
            "Kellner: Gerne. Und möchten Sie auch etwas essen?\n"
            "Anna: Ja, haben Sie Apfelkuchen?\n"
            "Kellner: Ja, unser Apfelkuchen ist heute ganz frisch gebacken.\n"
            "Anna: Wunderbar, dann nehme ich ein Stück Apfelkuchen.\n"
            "Kellner: Kommt sofort! Zusammen macht das 6 Euro 50.\n"
            "Anna: Danke schön."
        ),
        "translation_en": (
            "Waiter: Good day! What would you like to order?\n"
            "Anna: Good day. I would like a cup of coffee with milk and sugar, please.\n"
            "Waiter: With pleasure. And would you also like something to eat?\n"
            "Anna: Yes, do you have apple cake?\n"
            "Waiter: Yes, our apple cake was freshly baked today.\n"
            "Anna: Wonderful, then I will take a piece of apple cake.\n"
            "Waiter: Coming right away! Together that comes to 6 euros 50.\n"
            "Anna: Thank you very much."
        ),
        "vocabulary_hints": [
            {"word": "bestellen", "article": "", "meaning_en": "to order (verb)", "part_of_speech": "verb"},
            {"word": "die Tasse", "article": "die", "meaning_en": "the cup", "part_of_speech": "noun"},
            {"word": "der Kaffee", "article": "der", "meaning_en": "the coffee", "part_of_speech": "noun"},
            {"word": "frisch", "article": "", "meaning_en": "fresh", "part_of_speech": "adjective"},
            {"word": "das Stück", "article": "das", "meaning_en": "the piece / slice", "part_of_speech": "noun"},
            {"word": "Zusammen", "article": "", "meaning_en": "together / in total", "part_of_speech": "adverb"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Was trinkt Anna?",
                "type": "multiple_choice",
                "options": ["Tee mit Zitrone", "Kaffee mit Milch und Zucker", "Wasser mit Eis", "Orangensaft"],
                "correct_answer": "Kaffee mit Milch und Zucker",
                "explanation_en": "Anna specifically requests: 'eine Tasse Kaffee mit Milch und Zucker'."
            },
            {
                "id": "q2",
                "question": "True or False: Der Apfelkuchen ist alt.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "The waiter states that the apple cake is 'ganz frisch gebacken' (freshly baked today)."
            },
            {
                "id": "q3",
                "question": "Wie viel kostet die Bestellung insgesamt?",
                "type": "multiple_choice",
                "options": ["4 Euro 50", "5 Euro", "6 Euro 50", "8 Euro"],
                "correct_answer": "6 Euro 50",
                "explanation_en": "The waiter informs Anna: 'Zusammen macht das 6 Euro 50'."
            }
        ]
    },
    {
        "id": "read-a1-2",
        "is_seeded": True,
        "title": "Mein Mitbewohner Lukas (My Flatmate Lukas)",
        "cefr_level": "A1",
        "topic": "Daily Life & Routines",
        "difficulty": "Easy",
        "text_type": "passage",
        "passage_de": (
            "Das ist mein Mitbewohner Lukas. Er kommt aus Österreich und studiert Informatik in München. "
            "Lukas steht jeden Morgen um sieben Uhr auf. Zuerst geht er joggen, danach frühstückt er Müsli mit Joghurt. "
            "Am Nachmittag hat er Vorlesungen an der Universität. "
            "Am Abend kochen wir oft zusammen in unserer Küche. Er kocht sehr gut Pasta und Gemüse."
        ),
        "translation_en": (
            "This is my flatmate Lukas. He comes from Austria and studies computer science in Munich. "
            "Lukas gets up every morning at seven o'clock. First he goes jogging, afterwards he eats muesli with yogurt for breakfast. "
            "In the afternoon he has lectures at the university. "
            "In the evening we often cook together in our kitchen. He cooks pasta and vegetables very well."
        ),
        "vocabulary_hints": [
            {"word": "der Mitbewohner", "article": "der", "meaning_en": "the flatmate / roommate", "part_of_speech": "noun"},
            {"word": "aufstehen", "article": "", "meaning_en": "to get up (separable verb)", "part_of_speech": "verb"},
            {"word": "frühstücken", "article": "", "meaning_en": "to eat breakfast", "part_of_speech": "verb"},
            {"word": "die Vorlesung", "article": "die", "meaning_en": "the university lecture", "part_of_speech": "noun"},
            {"word": "zusammen", "article": "", "meaning_en": "together", "part_of_speech": "adverb"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Woher kommt Lukas?",
                "type": "multiple_choice",
                "options": ["Deutschland", "Österreich", "der Schweiz", "Spanien"],
                "correct_answer": "Österreich",
                "explanation_en": "The text states: 'Er kommt aus Österreich'."
            },
            {
                "id": "q2",
                "question": "Wann steht Lukas jeden Morgen auf?",
                "type": "multiple_choice",
                "options": ["Um 6 Uhr", "Um 7 Uhr", "Um 8 Uhr", "Um 9 Uhr"],
                "correct_answer": "Um 7 Uhr",
                "explanation_en": "The passage confirms: 'Lukas steht jeden Morgen um sieben Uhr auf'."
            },
            {
                "id": "q3",
                "question": "True or False: Lukas frühstückt vor dem Joggen.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "He jogs first, then eats: 'Zuerst geht er joggen, danach frühstückt er'."
            }
        ]
    },
    {
        "id": "read-a1-3",
        "is_seeded": True,
        "title": "Aushang: Öffnungszeiten der Stadtbibliothek (Library Hours Notice)",
        "cefr_level": "A1",
        "topic": "Public Notices & Schedules",
        "difficulty": "Easy",
        "text_type": "notice",
        "passage_de": (
            "Stadtbibliothek Frankfurt — Öffnungszeiten\n"
            "Montag bis Freitag: 09:00 – 19:00 Uhr\n"
            "Samstag: 10:00 – 16:00 Uhr\n"
            "Sonntag und Feiertage: Geschlossen.\n\n"
            "Hinweis für Besucher: Die Rückgabe von Büchern ist über den Automaten am Eingang 24 Stunden möglich. "
            "Kostenloses WLAN steht im gesamten Lesesaal zur Verfügung."
        ),
        "translation_en": (
            "Frankfurt City Library — Opening Hours\n"
            "Monday to Friday: 09:00 – 19:00\n"
            "Saturday: 10:00 – 16:00\n"
            "Sunday and Public Holidays: Closed.\n\n"
            "Notice for visitors: Returning books is possible 24 hours a day via the machine at the entrance. "
            "Free Wi-Fi is available throughout the reading room."
        ),
        "vocabulary_hints": [
            {"word": "die Öffnungszeiten", "article": "die", "meaning_en": "the opening hours", "part_of_speech": "noun"},
            {"word": "geschlossen", "article": "", "meaning_en": "closed", "part_of_speech": "adjective"},
            {"word": "die Rückgabe", "article": "die", "meaning_en": "the return / returning", "part_of_speech": "noun"},
            {"word": "kostenlos", "article": "", "meaning_en": "free of charge", "part_of_speech": "adjective"},
            {"word": "zur Verfügung stehen", "article": "", "meaning_en": "to be available", "part_of_speech": "phrase"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Wann öffnet die Bibliothek am Samstag?",
                "type": "multiple_choice",
                "options": ["Um 09:00 Uhr", "Um 10:00 Uhr", "Um 12:00 Uhr", "Sie ist geschlossen"],
                "correct_answer": "Um 10:00 Uhr",
                "explanation_en": "The schedule states: 'Samstag: 10:00 – 16:00 Uhr'."
            },
            {
                "id": "q2",
                "question": "True or False: Man kann am Sonntag Bücher über den Automaten zurückgeben.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation_en": "The notice states the return machine is available 24 hours a day ('24 Stunden möglich')."
            },
            {
                "id": "q3",
                "question": "Wann kann man Bücher am Automaten zurückgeben?",
                "type": "short_answer",
                "options": [],
                "correct_answer": "24 Stunden am Tag",
                "acceptable_alternatives": ["rund um die Uhr", "jederzeit", "24 Stunden"],
                "explanation_en": "The notice says that book returns are possible 24 hours a day."
            }
        ]
    },

    # ==================== CEFR A2 (Elementary) ====================
    {
        "id": "read-a2-1",
        "is_seeded": True,
        "title": "Einladung zum Sommerfest (Invitation to the Summer Party)",
        "cefr_level": "A2",
        "topic": "Social Invitations & Messages",
        "difficulty": "Moderate",
        "text_type": "email",
        "passage_de": (
            "Liebe Nachbarn und Freunde,\n\n"
            "am Samstag, den 15. Juli, feiern wir unser jährliches Sommerfest im Garten hinter dem Haus! "
            "Wir fangen um 16:00 Uhr an. Für Grillfleisch, Würstchen und kühle Getränke haben wir bereits gesorgt. "
            "Wenn ihr Zeit habt, bringt bitte einen Salat oder ein Dessert mit. "
            "Bei schlechtem Wetter können wir in den Gemeinschaftsraum im Erdgeschoss umziehen.\n\n"
            "Bitte gebt uns bis Mittwoch Bescheid, ob ihr kommt und wie viele Personen ihr seid.\n\n"
            "Herzliche Grüße,\n"
            "Monika und Stefan"
        ),
        "translation_en": (
            "Dear neighbors and friends,\n\n"
            "on Saturday, July 15th, we are celebrating our annual summer party in the garden behind the house! "
            "We will begin at 16:00. We have already taken care of grilled meat, sausages, and cool drinks. "
            "If you have time, please bring a salad or a dessert along. "
            "In case of bad weather, we can move into the community room on the ground floor.\n\n"
            "Please let us know by Wednesday whether you are coming and how many people you will be.\n\n"
            "Warm regards,\n"
            "Monika and Stefan"
        ),
        "vocabulary_hints": [
            {"word": "die Einladung", "article": "die", "meaning_en": "the invitation", "part_of_speech": "noun"},
            {"word": "sorgen für", "article": "", "meaning_en": "to provide / care for (+ Akkusativ)", "part_of_speech": "verb"},
            {"word": "mitbringen", "article": "", "meaning_en": "to bring along (separable verb)", "part_of_speech": "verb"},
            {"word": "der Gemeinschaftsraum", "article": "der", "meaning_en": "the common/community room", "part_of_speech": "noun"},
            {"word": "Bescheid geben", "article": "", "meaning_en": "to let someone know / inform", "part_of_speech": "phrase"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Was sollen die Gäste mitbringen?",
                "type": "multiple_choice",
                "options": ["Getränke und Fleisch", "Einen Salat oder ein Dessert", "Teller und Besteck", "Einen Grill"],
                "correct_answer": "Einen Salat oder ein Dessert",
                "explanation_en": "Monika and Stefan write: 'bringt bitte einen Salat oder ein Dessert mit'."
            },
            {
                "id": "q2",
                "question": "Was passiert, wenn es regnet?",
                "type": "multiple_choice",
                "options": [
                    "Das Fest fällt aus.",
                    "Sie feiern im Restaurant.",
                    "Sie ziehen in den Gemeinschaftsraum um.",
                    "Sie verschieben das Fest auf Sonntag."
                ],
                "correct_answer": "Sie ziehen in den Gemeinschaftsraum um.",
                "explanation_en": "The email states: 'Bei schlechtem Wetter können wir in den Gemeinschaftsraum ... umziehen'."
            },
            {
                "id": "q3",
                "question": "Bis wann sollen die Nachbarn antworten?",
                "type": "multiple_choice",
                "options": ["Bis Freitag", "Bis Mittwoch", "Bis Samstag", "Bis Sonntag"],
                "correct_answer": "Bis Mittwoch",
                "explanation_en": "The hosts request: 'Bitte gebt uns bis Mittwoch Bescheid'."
            }
        ]
    },
    {
        "id": "read-a2-2",
        "is_seeded": True,
        "title": "Ein Wochenende am Bodensee (A Weekend at Lake Constance)",
        "cefr_level": "A2",
        "topic": "Travel & Past Experiences (Perfekt)",
        "difficulty": "Moderate",
        "text_type": "story",
        "passage_de": (
            "Letztes Wochenende sind Julia und David mit dem Zug an den Bodensee gefahren. "
            "Die Fahrt hat etwa zweieinhalb Stunden gedauert. In Lindau haben sie in einem kleinen, gemütlichen Hotel gewohnt. "
            "Am Samstag haben sie Fahrräder gemietet und sind um einen Teil des Sees geradelt. "
            "Das Wetter war herrlich und die Sonne hat den ganzen Tag geschienen. "
            "Am Nachmittag sind sie im See geschwommen, obwohl das Wasser noch etwas kühl war. "
            "Am Sonntagabend sind sie glücklich und gut erholt nach Stuttgart zurückgekehrt."
        ),
        "translation_en": (
            "Last weekend, Julia and David traveled by train to Lake Constance. "
            "The journey took about two and a half hours. In Lindau, they stayed in a small, cozy hotel. "
            "On Saturday, they rented bicycles and cycled around part of the lake. "
            "The weather was wonderful and the sun shone the entire day. "
            "In the afternoon they swam in the lake, even though the water was still somewhat cool. "
            "On Sunday evening they returned to Stuttgart happy and well-rested."
        ),
        "vocabulary_hints": [
            {"word": "dauern", "article": "", "meaning_en": "to last / take time", "part_of_speech": "verb"},
            {"word": "gemütlich", "article": "", "meaning_en": "cozy / comfortable", "part_of_speech": "adjective"},
            {"word": "mieten", "article": "", "meaning_en": "to rent", "part_of_speech": "verb"},
            {"word": "scheinen", "article": "", "meaning_en": "to shine", "part_of_speech": "verb"},
            {"word": "zurückkehren", "article": "", "meaning_en": "to return / come back", "part_of_speech": "verb"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Wie sind Julia und David an den Bodensee gereist?",
                "type": "multiple_choice",
                "options": ["Mit dem Auto", "Mit dem Flugzeug", "Mit dem Zug", "Mit dem Bus"],
                "correct_answer": "Mit dem Zug",
                "explanation_en": "The story opens: '...sind Julia und David mit dem Zug an den Bodensee gefahren'."
            },
            {
                "id": "q2",
                "question": "True or False: Am Samstag hat es geregnet.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "The text notes: 'Das Wetter war herrlich und die Sonne hat den ganzen Tag geschienen'."
            },
            {
                "id": "q3",
                "question": "Was haben sie am Samstagnachmittag gemacht?",
                "type": "multiple_choice",
                "options": ["Ein Museum besucht", "Im See geschwommen", "Einen Film gesehen", "Ein Boot gekauft"],
                "correct_answer": "Im See geschwommen",
                "explanation_en": "The text says: 'Am Nachmittag sind sie im See geschwommen'."
            }
        ]
    },

    # ==================== CEFR B1 (Intermediate) ====================
    {
        "id": "read-b1-1",
        "is_seeded": True,
        "title": "Fahrradstädte: Mobilität und Umweltschutz (Cycling Cities & Mobility)",
        "cefr_level": "B1",
        "topic": "Environment & Modern Society",
        "difficulty": "Challenging",
        "text_type": "passage",
        "passage_de": (
            "Immer mehr deutsche Großstädte investieren in den Ausbau sicherer Radwege, weil der Straßenverkehr "
            "zu erheblichen Schadstoffbelastungen führt. Städte wie Münster und Freiburg gelten seit Jahren als Vorbilder, "
            "da dort mehr als ein Drittel aller täglichen Wege mit dem Fahrrad zurückgelegt werden.\n\n"
            "Experten betonen, dass gut ausgebaute Radschnellwege nicht nur die Umwelt schonen, sondern auch Staus "
            "im Berufsverkehr verringern. Allerdings fordern Verkehrsinitiativen mehr finanzielle Mittel von der Politik, "
            "obwohl in den letzten Jahren bereits deutliche Fortschritte erzielt wurden. "
            "Wenn sichere Abstellplätze und Ampelschaltungen für Radfahrende geschaffen werden, entscheiden sich auch "
            "immer mehr Berufspendler gegen das eigene Auto."
        ),
        "translation_en": (
            "More and more major German cities are investing in expanding safe bicycle lanes because road traffic "
            "causes substantial pollutant emissions. Cities like Münster and Freiburg have been considered role models for years, "
            "as more than a third of all daily journeys there are completed by bicycle.\n\n"
            "Experts emphasize that well-developed cycle expressways not only protect the environment, but also reduce "
            "traffic jams during rush hour. However, transport initiatives demand more financial resources from policymakers, "
            "even though significant progress has already been achieved in recent years. "
            "When safe parking spaces and traffic light coordination are created for cyclists, more and more commuters "
            "decide against using their own car."
        ),
        "vocabulary_hints": [
            {"word": "der Ausbau", "article": "der", "meaning_en": "expansion / extension", "part_of_speech": "noun"},
            {"word": "erheblich", "article": "", "meaning_en": "substantial / considerable", "part_of_speech": "adjective"},
            {"word": "zurücklegen", "article": "", "meaning_en": "to cover (a distance)", "part_of_speech": "verb"},
            {"word": "schonen", "article": "", "meaning_en": "to protect / spare", "part_of_speech": "verb"},
            {"word": "der Berufspendler", "article": "der", "meaning_en": "daily commuter", "part_of_speech": "noun"},
            {"word": "erzielen", "article": "", "meaning_en": "to achieve / attain", "part_of_speech": "verb"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Warum gelten Münster und Freiburg als Vorbilder für den Radverkehr?",
                "type": "multiple_choice",
                "options": [
                    "Autos sind dort komplett verboten.",
                    "Über ein Drittel der täglichen Wege wird dort mit dem Fahrrad zurückgelegt.",
                    "Fahrräder sind dort für alle Bürger kostenlos.",
                    "Es gibt dort keine Ampeln mehr."
                ],
                "correct_answer": "Über ein Drittel der täglichen Wege wird dort mit dem Fahrrad zurückgelegt.",
                "explanation_en": "The text states: '...da dort mehr als ein Drittel aller täglichen Wege mit dem Fahrrad zurückgelegt werden'."
            },
            {
                "id": "q2",
                "question": "Welche Vorteile bieten gut ausgebaute Radschnellwege laut Experten?",
                "type": "multiple_choice",
                "options": [
                    "Sie erhöhen die Benzinpreise.",
                    "Sie schonen die Umwelt und verringern Staus im Berufsverkehr.",
                    "Sie ersetzen die Straßenbahn komplett.",
                    "Sie sind billiger als Fußgängerwege."
                ],
                "correct_answer": "Sie schonen die Umwelt und verringern Staus im Berufsverkehr.",
                "explanation_en": "Experts state that they: 'nicht nur die Umwelt schonen, sondern auch Staus im Berufsverkehr verringern'."
            },
            {
                "id": "q3",
                "question": "True or False: Verkehrsinitiativen sind der Meinung, dass bereits genug Geld investiert wurde.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "Traffic initiatives demand MORE financial resources ('fordern mehr finanzielle Mittel von der Politik')."
            }
        ]
    },
    {
        "id": "read-b1-2",
        "is_seeded": True,
        "title": "Bewerbung auf eine Mietwohnung (Apartment Application Inquiry)",
        "cefr_level": "B1",
        "topic": "Housing & Formal Correspondence",
        "difficulty": "Challenging",
        "text_type": "email",
        "passage_de": (
            "Sehr geehrte Frau Dr. Wagner,\n\n"
            "mit großem Interesse habe ich Ihre Anzeige für die 2-Zimmer-Wohnung in der Humboldtstraße gelesen. "
            "Da ich ab dem 1. November als wissenschaftlicher Mitarbeiter an der Technischen Universität angestellt bin, "
            "suche ich eine ruhige und zentral gelegene Unterkunft.\n\n"
            "Ich verfüge über ein unbefristetes Arbeitsverhältnis mit geregeltem Einkommen und habe weder Haustiere "
            "noch spiele ich ein Musikinstrument. Eine aktuelle SCHUFA-Auskunft sowie Einkommensnachweise der letzten drei Monate "
            "kann ich Ihnen jederzeit gerne vorlegen.\n\n"
            "Über eine Einladung zu einem Besichtigungstermin würde ich mich sehr freuen.\n\n"
            "Mit freundlichen Grüßen,\n"
            "Maximilian Schwarz"
        ),
        "translation_en": (
            "Dear Dr. Wagner,\n\n"
            "with great interest I read your advertisement for the 2-room apartment on Humboldtstraße. "
            "Since I will be employed as a research associate at the Technical University starting November 1st, "
            "I am looking for quiet and centrally located accommodation.\n\n"
            "I have a permanent employment contract with steady income and have neither pets nor do I play a musical instrument. "
            "I would be glad to submit an up-to-date credit report (SCHUFA) as well as proof of income for the last three months at any time.\n\n"
            "I would be very pleased to receive an invitation to a viewing appointment.\n\n"
            "Yours sincerely,\n"
            "Maximilian Schwarz"
        ),
        "vocabulary_hints": [
            {"word": "die Unterkunft", "article": "die", "meaning_en": "accommodation / lodging", "part_of_speech": "noun"},
            {"word": "unbefristet", "article": "", "meaning_en": "permanent / indefinite", "part_of_speech": "adjective"},
            {"word": "der Einkommensnachweis", "article": "der", "meaning_en": "proof of income", "part_of_speech": "noun"},
            {"word": "der Besichtigungstermin", "article": "der", "meaning_en": "apartment viewing appointment", "part_of_speech": "noun"},
            {"word": "vorlegen", "article": "", "meaning_en": "to present / submit documents", "part_of_speech": "verb"}
        ],
        "questions": [
            {
                "id": "q1",
                "question": "Welche berufliche Tätigkeit übt Maximilian ab November aus?",
                "type": "multiple_choice",
                "options": [
                    "Architekt bei einer Baufirma",
                    "Wissenschaftlicher Mitarbeiter an der Technischen Universität",
                    "Lehrer an einem Gymnasium",
                    "Kellner in einem Café"
                ],
                "correct_answer": "Wissenschaftlicher Mitarbeiter an der Technischen Universität",
                "explanation_en": "He writes: 'Da ich ab dem 1. November als wissenschaftlicher Mitarbeiter an der Technischen Universität angestellt bin...'"
            },
            {
                "id": "q2",
                "question": "True or False: Maximilian hat eine Katze.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "He specifically notes: '...und habe weder Haustiere noch spiele ich ein Musikinstrument'."
            }
        ]
    }
]
