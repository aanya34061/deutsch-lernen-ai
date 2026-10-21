"""
Starter collection of German Writing (Schreiben) Practice Prompts for CEFR A1, A2, and B1.
Includes instructions, guide points, suggested lengths, sample solutions, and vocabulary help.
"""

STARTING_WRITING_PROMPTS = [
    # ==================== CEFR A1 (Beginner) ====================
    {
        "id": "write-a1-1",
        "title": "Sich selbst vorstellen (Introducing Yourself)",
        "cefr_level": "A1",
        "topic": "Personal Information",
        "task_type": "sentence_construction",
        "instruction_en": "Write 3–4 sentences introducing yourself in German.",
        "guide_points": [
            "State your name (Name)",
            "Where you come from (Herkunft: aus...)",
            "Where you currently live (Wohnort: in...)",
            "What language you are learning (Sprache: Deutsch)"
        ],
        "suggested_word_count": "20–35 words",
        "sample_solution_de": "Hallo! Ich heiße Sarah. Ich komme aus Kanada, aber ich wohne jetzt in Berlin. Ich lerne seit drei Monaten Deutsch.",
        "sample_solution_en": "Hello! My name is Sarah. I come from Canada, but I live in Berlin now. I have been learning German for three months.",
        "vocabulary_help": [
            {"german": "heißen", "english": "to be called"},
            {"german": "kommen aus", "english": "to come from"},
            {"german": "wohnen in", "english": "to live in"},
            {"german": "lernen", "english": "to learn / study"}
        ]
    },
    {
        "id": "write-a1-2",
        "title": "Mein Tagesablauf (My Daily Routine)",
        "cefr_level": "A1",
        "topic": "Daily Routine",
        "task_type": "routine",
        "instruction_en": "Describe what you do during a normal day in German.",
        "guide_points": [
            "What time you wake up (aufstehen)",
            "What you have for breakfast (frühstücken)",
            "When you work or study (arbeiten / studieren)",
            "What you do in the evening (am Abend: kochen, lesen, schlafen)"
        ],
        "suggested_word_count": "25–45 words",
        "sample_solution_de": "Ich stehe jeden Tag um sieben Uhr auf. Zum Frühstück trinke ich einen Kaffee und esse ein Brötchen. Von neun bis fünf Uhr arbeite ich im Büro. Am Abend koche ich und gehe um elf Uhr schlafen.",
        "sample_solution_en": "I get up every day at seven o'clock. For breakfast I drink a coffee and eat a bread roll. From nine to five o'clock I work in the office. In the evening I cook and go to sleep at eleven o'clock.",
        "vocabulary_help": [
            {"german": "aufstehen", "english": "to get up (separable)"},
            {"german": "das Frühstück", "english": "the breakfast"},
            {"german": "arbeiten", "english": "to work"},
            {"german": "schlafen gehen", "english": "to go to sleep"}
        ]
    },
    {
        "id": "write-a1-3",
        "title": "Kurze Nachricht: Treffen verschieben (Short Message: Rescheduling)",
        "cefr_level": "A1",
        "topic": "Messages & Appointments",
        "task_type": "informal_message",
        "instruction_en": "Write a short SMS/message to your friend Michael saying you cannot meet at 15:00 and suggest meeting at 17:00 instead.",
        "guide_points": [
            "Greet your friend informally (Lieber Michael...)",
            "Apologize and explain you cannot come at 15:00 (Es tut mir leid...)",
            "Propose the new time: 17:00 at the café",
            "Say goodbye (Bis später / Viele Grüße)"
        ],
        "suggested_word_count": "20–35 words",
        "sample_solution_de": "Lieber Michael, es tut mir sehr leid, aber ich kann um 15 Uhr leider nicht kommen. Hast du vielleicht um 17 Uhr Zeit? Treffen wir uns im Café am Park? Viele Grüße, David",
        "sample_solution_en": "Dear Michael, I am very sorry, but unfortunately I cannot come at 15:00. Do you perhaps have time at 17:00? Shall we meet at the café by the park? Best regards, David",
        "vocabulary_help": [
            {"german": "Es tut mir leid", "english": "I am sorry"},
            {"german": "leider", "english": "unfortunately"},
            {"german": "sich treffen", "english": "to meet each other"}
        ]
    },

    # ==================== CEFR A2 (Elementary) ====================
    {
        "id": "write-a2-1",
        "title": "Antwort auf eine Geburtstagseinladung (Replying to a Birthday Invitation)",
        "cefr_level": "A2",
        "topic": "Social Invitations",
        "task_type": "email",
        "instruction_en": "Your colleague Julia invited you to her birthday party on Saturday. Write an email accepting or declining, thanking her, and offering to bring something.",
        "guide_points": [
            "Thank Julia warmly for the invitation (Vielen Dank für die Einladung)",
            "State whether you can come or explain why not (Ich komme sehr gern... / Leider kann ich nicht...)",
            "Ask what you can bring along to eat or drink (Kann ich etwas mitbringen?)",
            "Ask if anyone else is coming or if she needs help setting up"
        ],
        "suggested_word_count": "40–60 words",
        "sample_solution_de": "Liebe Julia,\n\nvielen Dank für die liebe Einladung zu deinem Geburtstag! Ich freue mich sehr und komme am Samstag gerne vorbei. Soll ich einen Salat oder einen Kuchen mitbringen? Sag mir einfach Bescheid, wenn du noch Hilfe bei den Vorbereitungen brauchst.\n\nBis Samstag und liebe Grüße,\nMarkus",
        "sample_solution_en": "Dear Julia,\n\nthank you so much for the lovely invitation to your birthday! I am looking forward to it and will gladly come by on Saturday. Should I bring a salad or a cake along? Just let me know if you still need help with the preparations.\n\nSee you Saturday and warm regards,\nMarkus",
        "vocabulary_help": [
            {"german": "sich freuen auf", "english": "to look forward to (+ Akkusativ)"},
            {"german": "vorbeikommen", "english": "to drop by / come over"},
            {"german": "die Vorbereitung", "english": "the preparation"},
            {"german": "Bescheid sagen", "english": "to let someone know"}
        ]
    },
    {
        "id": "write-a2-2",
        "title": "Mein letztes Wochenende (My Last Weekend in Perfekt)",
        "cefr_level": "A2",
        "topic": "Past Experiences (Perfekt)",
        "task_type": "past_experience",
        "instruction_en": "Write a short paragraph about what you did last weekend using the German conversational past tense (Perfekt with haben/sein + Partizip II).",
        "guide_points": [
            "Where you went and with whom (z.B. mit Freunden, in den Park, ins Restaurant)",
            "What you ate, drank, or bought",
            "How the weather was (Das Wetter war schön / hat geregnet)",
            "How you felt on Sunday evening"
        ],
        "suggested_word_count": "45–70 words",
        "sample_solution_de": "Letztes Wochenende habe ich viel unternommen. Am Samstag bin ich mit Freunden in den Schwarzwald gefahren. Wir haben eine lange Wanderung gemacht und in einer Hütte traditionelle Maultaschen gegessen. Das Wetter hat gut mitgespielt, die Sonne hat geschienen. Am Sonntag bin ich zu Hause geblieben und habe ein Buch gelesen. Es war ein wirklich schönes Wochenende!",
        "sample_solution_en": "Last weekend I did a lot. On Saturday I drove to the Black Forest with friends. We went on a long hike and ate traditional Maultaschen in a cabin. The weather played along well, the sun shone. On Sunday I stayed at home and read a book. It was a genuinely nice weekend!",
        "vocabulary_help": [
            {"german": "unternehmen (hat unternommen)", "english": "to undertake / do activities"},
            {"german": "wandern (ist gewandert)", "english": "to hike"},
            {"german": "bleiben (ist geblieben)", "english": "to stay / remain"},
            {"german": "mitspielen", "english": "to play along (weather)"}
        ]
    },

    # ==================== CEFR B1 (Intermediate) ====================
    {
        "id": "write-b1-1",
        "title": "Meinung äußern: Homeoffice vs. Büro (Opinion: Remote vs. Office Work)",
        "cefr_level": "B1",
        "topic": "Work & Modern Society",
        "task_type": "opinion",
        "instruction_en": "Express your opinion on working from home compared to working in an office. Use subordinate conjunctions (weil, obwohl, dass, wenn).",
        "guide_points": [
            "State your personal point of view clearly (Meiner Meinung nach... / Ich bin der Ansicht, dass...)",
            "Give one advantage of working from home (e.g. no commuting time)",
            "Give one disadvantage or advantage of the office (e.g. direct exchange with colleagues)",
            "Conclude with your preferred model (e.g. hybrid model)"
        ],
        "suggested_word_count": "70–110 words",
        "sample_solution_de": "Meiner Meinung nach bietet das Arbeiten im Homeoffice zahlreiche Vorteile, da man keine Zeit im täglichen Berufsverkehr verliert. Man kann konzentrierter arbeiten, wenn man eine ruhige Umgebung zu Hause hat. Allerdings darf man nicht vergessen, dass der persönliche Kontakt zu Kolleginnen und Kollegen im Büro sehr wichtig ist, um Ideen schnell auszutauschen. Obwohl Homeoffice flexibler ist, fühlen sich manche Menschen manchmal isoliert. Daher halte ich ein hybrides Modell mit zwei bis drei Tagen im Büro für die beste Lösung.",
        "sample_solution_en": "In my opinion, working from home offers numerous advantages, as one loses no time in daily rush-hour traffic. One can work more focused when having a quiet environment at home. However, one must not forget that personal contact with colleagues in the office is very important for exchanging ideas quickly. Even though remote work is more flexible, some people sometimes feel isolated. Therefore, I consider a hybrid model with two to three days in the office to be the best solution.",
        "vocabulary_help": [
            {"german": "Meiner Meinung nach", "english": "in my opinion (inverts word order)"},
            {"german": "zahlreich", "english": "numerous"},
            {"german": "der Berufsverkehr", "english": "rush hour / commuter traffic"},
            {"german": "auszutauschen", "english": "to exchange (ideas)"},
            {"german": "halten für", "english": "to consider to be"}
        ]
    },
    {
        "id": "write-b1-2",
        "title": "Beschwerdebrief: Mängel in einer Ferienwohnung (Formal Complaint Letter)",
        "cefr_level": "B1",
        "topic": "Consumer Rights & Travel",
        "task_type": "email",
        "instruction_en": "Write a formal letter of complaint to a travel agency regarding problems with your vacation rental (heating broken, no Wi-Fi, cleanliness issues). Request an appropriate reimbursement.",
        "guide_points": [
            "Formal greeting and booking details (Sehr geehrte Damen und Herren, Buchungsnummer...)",
            "Describe the discrepancies between the description and reality (Heizung defekt, kein WLAN)",
            "Explain that you reported it on site but it was not resolved",
            "Set a deadline and request a partial refund (Rückerstattung von 20%)"
        ],
        "suggested_word_count": "80–120 words",
        "sample_solution_de": "Sehr geehrte Damen und Herren,\n\nich wende mich an Sie bezüglich meines Aufenthalts in der Ferienwohnung 'Alpenblick' (Buchungsnummer #84920). Leider entsprach die Unterkunft keineswegs den Angaben auf Ihrer Website. Bei unserer Ankunft funktionierte die Heizung nicht, und das zugesagte WLAN stand während des gesamten Aufenthalts nicht zur Verfügung. Trotz mehrmaliger Beschwerde bei der Rezeption vor Ort wurden die Mängel nicht behoben. Aus diesem Grund fordere ich eine angemessene Minderung des Reisepreises in Höhe von 20 Prozent. Bitte überweisen Sie den Betrag von 140 Euro bis zum 15. November auf mein Konto.\n\nMit freundlichen Grüßen,\nThomas Winter",
        "sample_solution_en": "Dear Sir or Madam,\n\nI am contacting you regarding my stay at the holiday apartment 'Alpenblick' (Booking number #84920). Unfortunately, the accommodation in no way matched the details on your website. Upon our arrival, the heating was not working, and the promised Wi-Fi was not available during the entire stay. Despite repeated complaints to the local reception, the deficiencies were not rectified. For this reason, I demand an appropriate price reduction of 20 percent. Please transfer the amount of 140 euros to my account by November 15th.\n\nYours faithfully,\nThomas Winter",
        "vocabulary_help": [
            {"german": "sich wenden an", "english": "to turn / address oneself to"},
            {"german": "entsprechen", "english": "to correspond / match (+ Dativ)"},
            {"german": "keineswegs", "english": "by no means"},
            {"german": "die Mängel", "english": "the defects / deficiencies"},
            {"german": "beheben", "english": "to rectify / resolve a problem"},
            {"german": "die Minderung", "english": "the reduction"}
        ]
    }
]
