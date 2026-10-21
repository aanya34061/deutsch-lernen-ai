"""
Starter collection of German Speaking (Sprechen) Scenarios and Role-Play Guides for CEFR A1, A2, and B1.
Configures persona prompts, tutor initial turns, learner guidance, and suggested vocabulary.
"""

STARTING_SPEAKING_SCENARIOS = [
    # ==================== CEFR A1 (Beginner) ====================
    {
        "id": "speak-a1-1",
        "title": "Im Café bestellen (Ordering at the Café)",
        "cefr_level": "A1",
        "topic": "Food, Drinks & Ordering",
        "activity_type": "role_play",
        "role_learner": "Kunde im Café (Customer)",
        "role_tutor": "Kellner / Barista (Waiter)",
        "initial_prompt_de": "Guten Tag! Willkommen im Café Sonnenschein. Was darf ich Ihnen heute bringen?",
        "initial_translation_en": "Good day! Welcome to Café Sonnenschein. What can I get for you today?",
        "scenario_guide": "Order a drink (Kaffee, Tee, Wasser) and ask for a snack or cake (Kuchen, Croissant). Then ask for the bill (die Rechnung).",
        "suggested_phrases": [
            {"german": "Ich möchte bitte einen Kaffee...", "english": "I would like a coffee, please..."},
            {"german": "Haben Sie auch Apfelkuchen?", "english": "Do you also have apple cake?"},
            {"german": "Was kostet das?", "english": "How much does that cost?"},
            {"german": "Ich möchte bitte zahlen.", "english": "I would like to pay, please."}
        ]
    },
    {
        "id": "speak-a1-2",
        "title": "Sich selbst und die Familie vorstellen (Introducing Yourself & Family)",
        "cefr_level": "A1",
        "topic": "Personal & Family Information",
        "activity_type": "introduction",
        "role_learner": "Sprachschüler (German Learner)",
        "role_tutor": "Deutschlehrer Klara (German Tutor)",
        "initial_prompt_de": "Hallo! Schön, dich kennenzulernen. Wie heißt du, und woher kommst du?",
        "initial_translation_en": "Hello! Nice to meet you. What is your name, and where do you come from?",
        "scenario_guide": "Tell Klara your name, where you are from, what city you live in, and briefly mention your family or pets.",
        "suggested_phrases": [
            {"german": "Ich heiße ... und komme aus ...", "english": "My name is ... and I come from ..."},
            {"german": "Ich wohne jetzt in ...", "english": "I live now in ..."},
            {"german": "Meine Familie ist groß / klein.", "english": "My family is big / small."},
            {"german": "Ich habe einen Bruder / eine Schwester.", "english": "I have a brother / a sister."}
        ]
    },

    # ==================== CEFR A2 (Elementary) ====================
    {
        "id": "speak-a2-1",
        "title": "Am Bahnhof: Zugfahrkarte kaufen (At the Train Station Counter)",
        "cefr_level": "A2",
        "topic": "Travel & Transportation",
        "activity_type": "role_play",
        "role_learner": "Reisender am Schalter (Traveler)",
        "role_tutor": "Bahnbeamter am Schalter (Railway Counter Agent)",
        "initial_prompt_de": "Guten Tag! Willkommen am DB-Reisezentrum. Wie kann ich Ihnen bei Ihrer Reise helfen?",
        "initial_translation_en": "Good day! Welcome to the DB Travel Center. How can I help you with your journey?",
        "scenario_guide": "Ask for a train ticket to Berlin or Munich, inquire about direct connections, departure times, and seat reservations.",
        "suggested_phrases": [
            {"german": "Ich möchte eine Fahrkarte nach Berlin, bitte.", "english": "I would like a train ticket to Berlin, please."},
            {"german": "Fährt der Zug direkt oder muss ich umsteigen?", "english": "Does the train run direct or do I need to transfer?"},
            {"german": "Von welchem Gleis fährt der Zug ab?", "english": "Which platform does the train depart from?"},
            {"german": "Ich möchte einen Sitzplatz reservieren.", "english": "I would like to reserve a seat."}
        ]
    },
    {
        "id": "speak-a2-2",
        "title": "Über das vergangene Wochenende sprechen (Talking About Your Weekend)",
        "cefr_level": "A2",
        "topic": "Past Experiences (Perfekt)",
        "activity_type": "description",
        "role_learner": "Gesprächspartner (Conversation Partner)",
        "role_tutor": "Sprachpartner Klara (Language Partner)",
        "initial_prompt_de": "Hallo! Wie war dein Wochenende? Was hast du Schönes gemacht?",
        "initial_translation_en": "Hello! How was your weekend? What nice things did you do?",
        "scenario_guide": "Describe 2-3 activities you did last weekend using the Perfekt tense (ich habe gemacht, ich bin gegangen).",
        "suggested_phrases": [
            {"german": "Am Samstag habe ich lange geschlafen.", "english": "On Saturday I slept in for a long time."},
            {"german": "Danach bin ich mit Freunden in den Park gegangen.", "english": "Afterwards I went to the park with friends."},
            {"german": "Wir haben im Restaurant gegessen.", "english": "We ate in a restaurant."},
            {"german": "Das Wetter war leider nicht so gut.", "english": "The weather was unfortunately not so good."}
        ]
    },

    # ==================== CEFR B1 (Intermediate) ====================
    {
        "id": "speak-b1-1",
        "title": "Bewerbungsgespräch für ein Praktikum (Internship Interview)",
        "cefr_level": "B1",
        "topic": "Career & Professional Life",
        "activity_type": "role_play",
        "role_learner": "Bewerber (Applicant)",
        "role_tutor": "Personalchef Herr Weber (HR Manager)",
        "initial_prompt_de": "Guten Tag! Nehmen Sie bitte Platz. Vielen Dank für Ihr Interesse an unserer Firma. Warum möchten Sie dieses Praktikum bei uns absolvieren?",
        "initial_translation_en": "Good day! Please take a seat. Thank you for your interest in our company. Why would you like to complete this internship with us?",
        "scenario_guide": "Explain your educational background, why this industry interests you, your strengths, and how you deal with challenges.",
        "suggested_phrases": [
            {"german": "Ich studiere derzeit und möchte praktische Erfahrung sammeln.", "english": "I am currently studying and would like to gain practical experience."},
            {"german": "Eine meiner größten Stärken ist Teamfähigkeit.", "english": "One of my greatest strengths is the ability to work in a team."},
            {"german": "Weil Ihr Unternehmen international tätig ist...", "english": "Because your enterprise operates internationally..."},
            {"german": "Ich kann mich schnell in neue Themen einarbeiten.", "english": "I can quickly familiarize myself with new topics."}
        ]
    },
    {
        "id": "speak-b1-2",
        "title": "Vor- und Nachteile des Lebens in der Großstadt (Living in the Big City)",
        "cefr_level": "B1",
        "topic": "Society & Lifestyle Discussion",
        "activity_type": "opinion",
        "role_learner": "Diskussionsteilnehmer (Discussion Participant)",
        "role_tutor": "Moderator Klara (Discussion Host)",
        "initial_prompt_de": "Hallo! Viele Menschen lieben das pulsierende Leben in der Metropole, andere bevorzugen die Ruhe auf dem Land. Was sind Ihrer Meinung nach die größten Vor- und Nachteile des Stadtlebens?",
        "initial_translation_en": "Hello! Many people love vibrant life in the metropolis, others prefer quiet in the countryside. In your opinion, what are the greatest advantages and disadvantages of city life?",
        "scenario_guide": "Discuss public transit, cultural events vs. high rent, noise and lack of green space. Use B1 connectors (einerseits / andererseits, obwohl, da, meiner Ansicht nach).",
        "suggested_phrases": [
            {"german": "Einerseits bietet die Stadt viele Freizeitmöglichkeiten...", "english": "On the one hand the city offers many leisure opportunities..."},
            {"german": "Andererseits sind die Mieten in den letzten Jahren stark gestiegen.", "english": "On the other hand rents have risen sharply in recent years."},
            {"german": "Meiner Ansicht nach ist der öffentliche Nahverkehr ein großer Vorteil.", "english": "In my view public transit is a major advantage."},
            {"german": "Obwohl es manchmal laut ist, lebe ich gern hier.", "english": "Even though it is loud at times, I enjoy living here."}
        ]
    }
]
