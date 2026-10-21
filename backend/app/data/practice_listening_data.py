"""
Starter collection of German Listening (Hören) Practice Exercises for CEFR A1, A2, and B1.
Includes audio scripts, English translations, and comprehension questions.
Compatible with native/browser speech synthesis and optional local audio files.
"""

STARTING_LISTENING_EXERCISES = [
    # ==================== CEFR A1 (Beginner) ====================
    {
        "id": "listen-a1-1",
        "title": "Auf dem Wochenmarkt (At the Weekly Market)",
        "cefr_level": "A1",
        "topic": "Shopping & Food",
        "difficulty": "Easy",
        "audio_type": "dialogue",
        "script_de": (
            "Verkäufer: Guten Morgen! Was darf es sein?\n"
            "Kunde: Guten Morgen. Ich brauche ein Kilo Äpfel und ein Pfund Erdbeeren, bitte.\n"
            "Verkäufer: Sehr gern. Möchten Sie die süßen roten Äpfel oder die säuerlichen grünen?\n"
            "Kunde: Bitte die süßen roten Äpfel.\n"
            "Verkäufer: Gerne. Darf es sonst noch etwas sein? Wir haben heute frischen Spargel im Angebot.\n"
            "Kunde: Nein danke, das ist alles für heute.\n"
            "Verkäufer: Das macht dann zusammen vier Euro achtzig.\n"
            "Kunde: Hier sind fünf Euro. Stimmt so, vielen Dank!\n"
            "Verkäufer: Herzlichen Dank und einen schönen Tag noch!"
        ),
        "translation_en": (
            "Vendor: Good morning! What can I get for you?\n"
            "Customer: Good morning. I need one kilogram of apples and one pound of strawberries, please.\n"
            "Vendor: With pleasure. Would you like the sweet red apples or the tart green ones?\n"
            "Customer: The sweet red apples, please.\n"
            "Vendor: Certainly. Would you like anything else? We have fresh asparagus on special today.\n"
            "Customer: No thank you, that is all for today.\n"
            "Vendor: That comes to four euros eighty in total.\n"
            "Customer: Here are five euros. Keep the change, thank you very much!\n"
            "Vendor: Thank you kindly and have a wonderful day!"
        ),
        "questions": [
            {
                "id": "lq1",
                "question": "Welche Früchte kauft der Kunde?",
                "type": "multiple_choice",
                "options": ["Bananen und Kirschen", "Äpfel und Erdbeeren", "Zitronen und Orangen", "Nur Spargel"],
                "correct_answer": "Äpfel und Erdbeeren",
                "explanation_en": "The customer orders: 'ein Kilo Äpfel und ein Pfund Erdbeeren'."
            },
            {
                "id": "lq2",
                "question": "Welche Apfelsorte wählt der Kunde?",
                "type": "multiple_choice",
                "options": ["Die säuerlichen grünen", "Die süßen roten", "Gelbe Äpfel", "Bio-Birnen"],
                "correct_answer": "Die süßen roten",
                "explanation_en": "The customer specifies: 'Bitte die süßen roten Äpfel'."
            },
            {
                "id": "lq3",
                "question": "Wie viel kostet der Einkauf?",
                "type": "multiple_choice",
                "options": ["3,50 Euro", "4,80 Euro", "5,00 Euro", "6,20 Euro"],
                "correct_answer": "4,80 Euro",
                "explanation_en": "The seller states: 'Das macht dann zusammen vier Euro achtzig (4,80 €)'."
            }
        ]
    },
    {
        "id": "listen-a1-2",
        "title": "Nachricht auf der Mailbox: Verabredung (Voicemail: Meeting Up)",
        "cefr_level": "A1",
        "topic": "Appointments & Daily Life",
        "difficulty": "Easy",
        "audio_type": "voicemail",
        "script_de": (
            "Hallo Sarah! Hier ist Thomas. Ich rufe wegen unseres Treffens heute Abend an. "
            "Ich schaffe es leider nicht um 18 Uhr, weil mein Zug zehn Minuten Verspätung hat. "
            "Können wir uns stattdessen um halb sieben vor dem Kino treffen? "
            "Der Film fängt erst um zwanzig vor sieben an. "
            "Bitte ruf mich kurz zurück oder schreib mir eine WhatsApp. Bis später!"
        ),
        "translation_en": (
            "Hello Sarah! Thomas here. I am calling about our meeting tonight. "
            "Unfortunately I can't make it at 6 o'clock because my train is delayed by ten minutes. "
            "Can we meet instead at half past six in front of the cinema? "
            "The movie doesn't start until twenty to seven. "
            "Please call me back briefly or send me a WhatsApp message. See you later!"
        ),
        "questions": [
            {
                "id": "lq1",
                "question": "Warum kann Thomas nicht um 18:00 Uhr kommen?",
                "type": "multiple_choice",
                "options": [
                    "Er muss noch arbeiten.",
                    "Sein Zug hat Verspätung.",
                    "Er hat seinen Schlüssel verloren.",
                    "Er ist krank."
                ],
                "correct_answer": "Sein Zug hat Verspätung.",
                "explanation_en": "Thomas explains: '...weil mein Zug zehn Minuten Verspätung hat'."
            },
            {
                "id": "lq2",
                "question": "Um wie viel Uhr möchte sich Thomas treffen? ('halb sieben')",
                "type": "multiple_choice",
                "options": ["18:00 Uhr", "18:15 Uhr", "18:30 Uhr", "19:30 Uhr"],
                "correct_answer": "18:30 Uhr",
                "explanation_en": "In German, 'halb sieben' means 18:30 (half an hour before seven)."
            }
        ]
    },

    # ==================== CEFR A2 (Elementary) ====================
    {
        "id": "listen-a2-1",
        "title": "Durchsage am Bahnhof: Gleiswechsel (Station Announcement)",
        "cefr_level": "A2",
        "topic": "Travel & Transportation",
        "difficulty": "Moderate",
        "audio_type": "announcement",
        "script_de": (
            "Achtung an Gleis 4! Der Intercity-Express 584 nach Hamburg-Altona über Hannover, "
            "geplante Abfahrt 14 Uhr 22, fährt heute nicht von Gleis 4 ab. "
            "Ich wiederhole: Wegen einer technischen Störung an der Weiche fährt der ICE 584 heute von Gleis 7 ab. "
            "Bitte nutzen Sie die Unterführung zu Gleis 7. "
            "Wir bitten alle Fahrgäste um Verständnis für diese Unannehmlichkeit."
        ),
        "translation_en": (
            "Attention at Platform 4! The Intercity Express 584 to Hamburg-Altona via Hannover, "
            "scheduled departure 14:22, does not depart from Platform 4 today. "
            "I repeat: Due to a technical fault at the switch point, ICE 584 departs today from Platform 7. "
            "Please use the underpass to Platform 7. "
            "We ask all passengers for their understanding regarding this inconvenience."
        ),
        "questions": [
            {
                "id": "lq1",
                "question": "Wohin fährt der ICE 584?",
                "type": "multiple_choice",
                "options": ["Nach München", "Nach Hamburg-Altona", "Nach Berlin", "Nach Frankfurt"],
                "correct_answer": "Nach Hamburg-Altona",
                "explanation_en": "The loudspeaker announces: 'Der Intercity-Express 584 nach Hamburg-Altona...'"
            },
            {
                "id": "lq2",
                "question": "Von welchem Gleis fährt der Zug nun tatsächlich ab?",
                "type": "multiple_choice",
                "options": ["Gleis 4", "Gleis 5", "Gleis 7", "Gleis 9"],
                "correct_answer": "Gleis 7",
                "explanation_en": "The announcement states: '...fährt der ICE 584 heute von Gleis 7 ab'."
            },
            {
                "id": "lq3",
                "question": "Was ist der Grund für die Änderung?",
                "type": "multiple_choice",
                "options": ["Schlechtes Wetter", "Eine technische Störung an der Weiche", "Personalmangel", "Ein Streik"],
                "correct_answer": "Eine technische Störung an der Weiche",
                "explanation_en": "The announcer cites: 'Wegen einer technischen Störung an der Weiche'."
            }
        ]
    },
    {
        "id": "listen-a2-2",
        "title": "In der Arztpraxis: Termin vereinbaren (Making a Doctor's Appointment)",
        "cefr_level": "A2",
        "topic": "Health & Appointments",
        "difficulty": "Moderate",
        "audio_type": "dialogue",
        "script_de": (
            "Arzthelferin: Praxis Dr. Berger, guten Tag. Was kann ich für Sie tun?\n"
            "Patient: Guten Tag, mein Name ist Felix Meyer. Ich habe seit zwei Tagen starke Halsschmerzen und Fieber. "
            "Hätten Sie heute noch einen Termin frei?\n"
            "Arzthelferin: Guten Tag, Herr Meyer. Sind Sie gesetzlich oder privat versichert?\n"
            "Patient: Ich bin gesetzlich bei der Techniker Krankenkasse versichert.\n"
            "Arzthelferin: Gut. Wenn Sie etwas Wartezeit mitbringen, können Sie heute um 11:30 Uhr in die Notfallsprechstunde kommen. "
            "Bringen Sie bitte Ihre Versichertenkarte mit.\n"
            "Patient: Vielen Dank, 11:30 Uhr passt mir sehr gut. Bis später!"
        ),
        "translation_en": (
            "Medical Assistant: Practice Dr. Berger, good day. What can I do for you?\n"
            "Patient: Good day, my name is Felix Meyer. I have had a severe sore throat and fever for two days. "
            "Would you have an appointment available today?\n"
            "Medical Assistant: Good day, Mr. Meyer. Are you insured publicly or privately?\n"
            "Patient: I have statutory insurance with Techniker Krankenkasse.\n"
            "Medical Assistant: Good. If you can bring some waiting time along, you can come to the acute walk-in clinic at 11:30 today. "
            "Please bring your insurance card with you.\n"
            "Patient: Thank you very much, 11:30 suits me very well. See you later!"
        ),
        "questions": [
            {
                "id": "lq1",
                "question": "Welche Symptome hat Felix Meyer?",
                "type": "multiple_choice",
                "options": [
                    "Kopfschmerzen und Husten",
                    "Starke Halsschmerzen und Fieber",
                    "Magenschmerzen",
                    "Zahnschmerzen"
                ],
                "correct_answer": "Starke Halsschmerzen und Fieber",
                "explanation_en": "Felix states: 'Ich habe seit zwei Tagen starke Halsschmerzen und Fieber'."
            },
            {
                "id": "lq2",
                "question": "Wann ist sein Notfalltermin?",
                "type": "multiple_choice",
                "options": ["Um 09:00 Uhr", "Um 10:30 Uhr", "Um 11:30 Uhr", "Erst morgen"],
                "correct_answer": "Um 11:30 Uhr",
                "explanation_en": "The assistant proposes: '...können Sie heute um 11:30 Uhr in die Notfallsprechstunde kommen'."
            }
        ]
    },

    # ==================== CEFR B1 (Intermediate) ====================
    {
        "id": "listen-b1-1",
        "title": "Interview: Nachhaltiges Leben im Alltag (Sustainability in Daily Life)",
        "cefr_level": "B1",
        "topic": "Environment & Lifestyle",
        "difficulty": "Challenging",
        "audio_type": "interview",
        "script_de": (
            "Moderator: Herzlich willkommen zu unserem Podcast 'Zukunft Jetzt'. Heute sprechen wir mit Laura Becker, "
            "die seit über drei Jahren fast komplett ohne Plastikmüll lebt. Laura, wie hat das bei dir angefangen?\n"
            "Laura: Hallo! Bei mir begann alles nach einer Reise ans Meer, wo ich die enormen Mengen an Müll am Strand gesehen habe. "
            "Als ich nach Hause kam, beschloss ich, schrittweise Gewohnheiten zu ändern. "
            "Ich kaufe fast ausschließlich in verpackungsfreien Läden ein und nehme immer meine eigenen Glasbehälter mit.\n"
            "Moderator: Ist das im Alltag nicht sehr zeitaufwendig und teurer?\n"
            "Laura: Überraschenderweise nicht! Weil ich nur kaufe, was ich wirklich verbrauche, werfe ich kaum Lebensmittel weg. "
            "Man spart dadurch Geld, anstatt mehr auszugeben. Der größte Schritt ist einfach die Umstellung am Anfang."
        ),
        "translation_en": (
            "Host: Welcome warmly to our podcast 'Future Now'. Today we speak with Laura Becker, "
            "who has lived almost completely without plastic waste for over three years. Laura, how did that start for you?\n"
            "Laura: Hello! For me, everything began after a trip to the sea, where I saw the enormous amounts of garbage on the beach. "
            "When I returned home, I decided to gradually change habits. "
            "I shop almost exclusively in package-free zero-waste stores and always bring my own glass containers along.\n"
            "Host: Isn't that very time-consuming and more expensive in everyday life?\n"
            "Laura: Surprisingly not! Because I only buy what I actually consume, I hardly throw away any food. "
            "You save money as a result instead of spending more. The biggest step is simply the initial adjustment."
        ),
        "questions": [
            {
                "id": "lq1",
                "question": "Was war der Auslöser für Lauras Entscheidung, ohne Plastik zu leben?",
                "type": "multiple_choice",
                "options": [
                    "Ein Buch über Wirtschaft",
                    "Eine Reise ans Meer und die Müllmengen am Strand",
                    "Eine Schulaufgabe",
                    "Ein Verbot von Plastiktüten in ihrer Stadt"
                ],
                "correct_answer": "Eine Reise ans Meer und die Müllmengen am Strand",
                "explanation_en": "Laura explains: 'Bei mir begann alles nach einer Reise ans Meer, wo ich die enormen Mengen an Müll am Strand gesehen habe'."
            },
            {
                "id": "lq2",
                "question": "True or False: Laura findet ihren Lebensstil teurer als früher.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation_en": "Laura notes: 'Überraschenderweise nicht! ... Man spart dadurch Geld, anstatt mehr auszugeben'."
            }
        ]
    }
]
