"""Canonical, stable-ID curriculum manifest and lesson-content materializer."""
from copy import deepcopy
from app.data.curriculum_a1 import A1_LESSONS as OLD_A1
from app.data.curriculum_a2 import A2_LESSONS as OLD_A2
from app.data.curriculum_b1 import B1_LESSONS as OLD_B1

LEGACY_LESSONS = {x['id']: deepcopy(x) for x in [*OLD_A1, *OLD_A2, *OLD_B1]}


def topic(slug, title, focus, rule, pattern, examples, vocabulary, mistake, correction, reason, blank, answer, false_claim, can_do=None):
    return dict(slug=slug, title=title, focus=focus, rule=rule, pattern=pattern, examples=examples,
                vocabulary=vocabulary, mistake=mistake, correction=correction, reason=reason,
                blank=blank, answer=answer, false_claim=false_claim, can_do=can_do)


def legacy(lesson_id, title):
    return {"legacy_id": lesson_id, "title": title}


def _exercise(lesson_id, number, kind, question, prompt, answer, explanation, options=None, correct_sentence=None):
    item = {"id": f"{lesson_id}-ex{number}", "type": kind, "skill": "grammar", "difficulty": "beginner",
            "question": question, "prompt": prompt, "correct_answer": answer, "explanation_en": explanation}
    if options is not None:
        item["options"] = options
    if correct_sentence:
        item["correct_sentence_de"] = correct_sentence
    return item


def _build_topic(module, spec, topic_order):
    lesson_id = spec.get("_stable_lesson_id") or f"{module['level'].lower()}-{module['id'][-2:]}-{spec['slug']}"
    examples = [{"german": de, "english": en} for de, en in spec["examples"]]
    vocabulary = [{"word": word, "article": article, "plural": plural, "meaning_en": meaning}
                  for word, article, plural, meaning in spec["vocabulary"]]
    exercises = [
        _exercise(lesson_id, 1, "fill_blank", f"Complete the sentence using {spec['title']}.", spec["blank"], spec["answer"],
                  f"{spec['reason']} Correct form: {spec['answer']}.", correct_sentence=spec["blank"].replace("____", spec["answer"])),
        _exercise(lesson_id, 2, "translate", "Translate this short sentence into German.", examples[0]["english"], examples[0]["german"],
                  f"The lesson model is: {examples[0]['german']}", correct_sentence=examples[0]["german"]),
        _exercise(lesson_id, 3, "true_false", f"True or false: {spec['false_claim']}", "Choose True or False.", "False",
                  f"This claim is incorrect. {spec['reason']}", ["True", "False"], spec["correction"]),
    ]
    return {
        "id": lesson_id, "lesson_id": lesson_id,
        "topic_id": spec.get("_stable_topic_id") or f"{module['id']}-{spec['slug']}",
        "module_id": module["id"], "module_title": module["title"], "title": spec["title"], "topic": spec["title"],
        "cefr_level": module["level"], "order": module["order"] * 100 + topic_order, "topic_order": topic_order,
        "estimated_minutes": 20 if module["level"] == "A1" else 25,
        "objectives": [spec.get("can_do") or f"Use {spec['title'].lower()} to complete a practical communication task.", f"Use the pattern {spec['pattern']} in context.", "Review and correct a common communication error."],
        "introduction_en": spec["focus"],
        "explanation_en": f"{spec['focus']} {spec['rule']} Study the examples as complete sentence models. Compare the common mistake with its correction, then practice changing one part of the sentence while keeping the pattern.",
        "grammar_rules": [{"name": f"Core pattern: {spec['title']}", "explanation": spec["rule"], "pattern": spec["pattern"],
                           "table": [{"German": x["german"], "English": x["english"]} for x in examples[:2]]}],
        "sentence_patterns": [spec["pattern"]], "examples": examples,
        "practical_dialogue": [{"speaker": "A", **examples[0]}, {"speaker": "B", **examples[1]}],
        "vocabulary": vocabulary,
        "common_mistakes": [{"wrong": spec["mistake"], "correct": spec["correction"], "explanation": spec["reason"]}],
        "important_notes": [spec["reason"]], "summary_en": f"Remember: {spec['rule']} Pattern: {spec['pattern']}",
        "exercises": exercises, "publication_status": "published", "content_source": "manifest",
        "content_version": 1, "is_manually_edited": False,
    }


def _build_legacy(module, ref, topic_order):
    item = deepcopy(LEGACY_LESSONS[ref["legacy_id"]])
    main_rule = item.get("grammar_rules", [{}])[0]
    rule_detail = main_rule.get("explanation", "")
    item["explanation_en"] = (
        item.get("explanation_en", "")
        + f"\n\nStudy the {main_rule.get('name', item['topic'])} pattern step by step: identify the subject, choose the matching form, and check the example before you answer. {rule_detail} "
        + "Compare the examples with the common-mistake correction, then try the exercises without looking at the key."
    )
    while len(item.get("exercises", [])) < 3:
        number = len(item.get("exercises", [])) + 1
        item.setdefault("exercises", []).append(_exercise(
            item["id"], number, "true_false", f"True or false: {item['summary_en']}", "Choose True or False.", "True",
            f"This statement summarizes the lesson: {item['summary_en']}", ["True", "False"],
        ))
    item.update({"lesson_id": item["id"], "module_id": module["id"], "module_title": module["title"],
                 "topic_id": f"{module['id']}-{item['id']}", "topic_order": topic_order,
                 "order": module["order"] * 100 + topic_order,
                 "introduction_en": item.get("explanation_en", ""),
                 "sentence_patterns": [x.get("pattern", "") for x in item.get("grammar_rules", []) if x.get("pattern")],
                 "practical_dialogue": [{"speaker": "A", **x} for x in item.get("examples", [])[:2]],
                 "important_notes": [x["explanation"] for x in item.get("common_mistakes", [])[:2]],
                 "publication_status": "published", "content_source": "manifest", "content_version": 1,
                 "is_manually_edited": False})
    return item


def get_curriculum_manifest():
    """Return modules, topics, and full lessons in deterministic curriculum order."""
    modules, topics, lessons = [], [], []
    for module in ALL_MODULES:
        topic_ids = []
        for order, spec in enumerate(module["topics"], 1):
            lesson = _build_legacy(module, spec, order) if "legacy_id" in spec else _build_topic(module, spec, order)
            lesson["module_id"], lesson["module_title"] = module["id"], module["title"]
            lesson["topic_id"] = spec.get("_stable_topic_id") or f"{module['id']}-{spec.get('slug', lesson['id'])}"
            lesson["topic_order"], lesson["order"] = order, module["order"] * 100 + order
            lessons.append(lesson)
            topic_ids.append(lesson["topic_id"])
            topics.append({"topic_id": lesson["topic_id"], "module_id": module["id"], "level": module["level"],
                           "order": lesson["order"], "title": lesson["topic"], "lesson_id": lesson["id"],
                           "publication_status": "published", "content_source": "manifest"})
        modules.append({"module_id": module["id"], "level": module["level"], "order": module["order"],
                        "title": module["title"], "description": module["description"], "topic_ids": topic_ids,
                        "publication_status": "published", "content_source": "manifest"})
    return {"modules": modules, "topics": topics, "lessons": lessons}


T = topic
A1_MODULES = [
    { "id":"a1-m01", "level":"A1", "order":1, "title":"Starting Conversations: Sounds, Greetings, and Names",
      "description":"Handle first encounters: recognize common sounds, greet people, say your name, and spell it when needed.",
      "topics":[
        T("alphabet","The German Alphabet and Spelling","German uses the Latin alphabet plus ä, ö, ü, and ß. Learn letter names so you can spell names, addresses, and unfamiliar words. Umlauts are real spelling differences, not decoration.","Spell each letter by its German name. ß is called Eszett; ä, ö, and ü are separate vowel letters.","Wie schreibt man das? — B-E-R-L-I-N.",
          [("Wie schreibt man deinen Namen?","How do you spell your name?"),("Müller schreibt man M-Ü-L-L-E-R.","Müller is spelled M-Ü-L-L-E-R."),("Die Straße hat ein ß.","The street name has an ß.")],
          [("der Buchstabe","der","die Buchstaben","letter"),("der Umlaut","der","die Umlaute","umlaut"),("das Alphabet","das","die Alphabete","alphabet")],
          "Muller","Müller","The umlaut is part of the spelling and may distinguish words.","Wie schreibt man ______? (M-Ü-L-L-E-R)","Müller","ß is pronounced like the English letter B."),
        T("pronunciation","Pronunciation: Vowels, ch, sch, ie, and ei","German spelling is fairly regular. Learning a few sound patterns improves reading and speaking: ie is usually a long ee, ei sounds like eye, sch sounds like English sh, and ch varies with the preceding vowel.","Read ie as long ee and ei as eye. sch is one sound. ch after a, o, u is throaty; after e or i it is softer.","ie = long ee; ei = eye; sch = sh.",
          [("Sie spielt ein Spiel.","She plays a game."),("Der Wein ist heiß.","The wine is hot."),("Ich spreche Deutsch.","I speak German.")],
          [("spielen","","","to play"),("der Wein","der","die Weine","wine"),("sprechen","","","to speak")],
          "Ich spreche Deitsch.","Ich spreche Deutsch.","Deutsch is spelled with eu; learn the sound and spelling together.","Das Wort Schule beginnt mit dem Laut ____.","sch","The German pair ie sounds like English eye."),
        legacy("a1-lesson-1","Greetings and First Conversations"),
      ]},
    { "id":"a1-m02","level":"A1","order":2,"title":"Personal Details and Social Contacts",
      "description":"Exchange basic information, ask and answer personal questions, and introduce family members and friends.",
      "topics":[
        T("names-origins","Names, Countries, and Languages","Give your name, say where you come from, and name languages you speak. Learn common country phrases as units because country names use different prepositions.","Use Ich heiße… or Ich bin…; Ich komme aus…; Ich spreche…. German language names are nouns and are capitalized.","Ich heiße… / Ich komme aus… / Ich spreche…",
          [("Ich heiße Sara und komme aus Spanien.","My name is Sara and I come from Spain."),("Ich spreche Arabisch und Deutsch.","I speak Arabic and German."),("Woher kommst du?","Where are you from?")],
          [("das Land","das","die Länder","country"),("die Sprache","die","die Sprachen","language"),("die Herkunft","die","die Herkünfte","origin")],
          "Ich komme von Kanada.","Ich komme aus Kanada.","For a country of origin, the common phrase is aus + country.","Ich komme ______ Kanada.","aus","Use Ich spreche to ask where someone comes from."),
        T("questions-personal","Personal Questions and Question Words","Ask about names, age, home, work, and languages. German questions either start with a question word or with the conjugated verb.","W-questions use question word + verb + subject. Yes/no questions put the verb first.","Wie heißt du? / Wo wohnst du? / Sprichst du Deutsch?",
          [("Wie alt bist du? — Ich bin zwanzig Jahre alt.","How old are you? — I am twenty years old."),("Wo wohnst du? — Ich wohne in Hamburg.","Where do you live? — I live in Hamburg."),("Arbeitest du heute?","Are you working today?")],
          [("wer","","","who"),("wo","","","where"),("wie","","","how")],
          "Wo du wohnst?","Wo wohnst du?","In a W-question, the conjugated verb follows the question word.","______ wohnst du? — Ich wohne in Berlin.","Wo","A yes/no question puts the verb after the subject."),
        T("family-people","Family Members and People","Name family members and describe relationships. Learn every family noun with its article and plural; subject number also controls the verb form.","Use mein Bruder, meine Schwester, meine Eltern. A singular subject takes a singular verb; plural Eltern takes wohnen/sind.","Das ist meine Schwester. / Mein Vater heißt Ali.",
          [("Meine Eltern wohnen in Köln.","My parents live in Cologne."),("Mein Bruder ist Student.","My brother is a student."),("Das ist meine Großmutter.","This is my grandmother.")],
          [("die Schwester","die","die Schwestern","sister"),("der Bruder","der","die Brüder","brother"),("die Eltern","die","die Eltern","parents")],
          "Meine Bruder wohnt hier.","Mein Bruder wohnt hier.","Bruder is masculine singular; Eltern is plural.","Das ist mein ______. (brother)","Bruder","Eltern is singular and takes wohnt."),
        T("possessives","Possessive Words: mein, dein, sein, ihr","Possessives show who owns something. At A1, use them with familiar people and objects, and match the ending to the noun.","ich→mein, du→dein, er/es→sein, sie (she)→ihr. Before feminine and plural nouns use -e: meine Schwester, meine Bücher.","Das ist mein Buch. / Ist das deine Tasche?",
          [("Das ist mein Buch.","That is my book."),("Ist das deine Tasche?","Is that your bag?"),("Seine Schwester heißt Lina.","His sister is called Lina.")],
          [("mein","","","my"),("dein","","","your, informal singular"),("ihr","","","her")],
          "Das ist mein Mutter.","Das ist meine Mutter.","Mutter is feminine, so the possessive takes -e.","Das ist ______ Schwester. (my)","meine","The ending in mein never changes before feminine nouns."),
      ]},
    { "id":"a1-m03","level":"A1","order":3,"title":"Simple Sentences for Everyday Needs",
      "description":"Use articles, familiar verbs, simple word order, direct objects, and negation to talk about people and everyday things.",
      "topics":[
        legacy("a1-lesson-2","Articles, Gender, and Noun Plurals"),
        T("noun-plurals","Noun Plurals","German plurals add endings such as -e, -er, -(e)n, or -s; some also change the vowel. There is no single rule for every noun, so learn singular, article, and plural together.","The plural definite article is die for all genders. Learn pairs: der Tisch—die Tische; das Buch—die Bücher. A plural subject takes a plural verb.","der Tisch → die Tische; das Buch → die Bücher.",
          [("Der Tisch ist neu. Die Tische sind neu.","The table is new. The tables are new."),("Das Buch ist hier. Die Bücher sind hier.","The book is here. The books are here."),("Eine Frau wartet. Zwei Frauen warten.","A woman is waiting. Two women are waiting.")],
          [("der Tisch","der","die Tische","table"),("das Buch","das","die Bücher","book"),("die Frau","die","die Frauen","woman")],
          "Die Buch sind neu.","Die Bücher sind neu.","Plural die does not mean the noun stays unchanged.","das Buch → die ______","Bücher","Every plural noun adds -s."),
        T("pronouns-sein-haben","Subject Pronouns, sein, and haben","Pronouns replace names and nouns. sein (to be) and haben (to have) are irregular and appear in many basic conversations; memorize each form with its subject.","ich bin/habe; du bist/hast; er/sie/es ist/hat; wir sind/haben; ihr seid/habt; sie/Sie sind/haben. Formal Sie uses the plural verb and is capitalized.","Subject + matching form of sein/haben + complement.",
          [("Wir sind heute zu Hause.","We are at home today."),("Hast du einen Bruder?","Do you have a brother?"),("Sie hat ein neues Fahrrad.","She has a new bicycle.")],
          [("sein","","","to be"),("haben","","","to have"),("das Fahrrad","das","die Fahrräder","bicycle")],
          "Du haben Zeit.","Du hast Zeit.","The du forms are hast and bist.","Wir ______ heute müde. (to be)","sind","The pronoun wir takes ist."),
        legacy("a1-lesson-3","Present Tense Regular Verbs"),
        T("verb-position","Main Clauses and Verb Position Two","German main clauses place the conjugated verb in position two. Position means sentence element, not word: a time phrase can be first, followed by the verb and then the subject.","Statement: subject + verb + …; or time/place + verb + subject + …. Keep the conjugated verb immediately after the first sentence element.","Heute lerne ich Deutsch. / Ich lerne heute Deutsch.",
          [("Heute fährt Maria mit dem Bus.","Today Maria goes by bus."),("Am Abend kochen wir zusammen.","In the evening we cook together."),("Ich spiele morgen Fußball.","I am playing soccer tomorrow.")],
          [("heute","","","today"),("morgen","","","tomorrow"),("der Abend","der","die Abende","evening")],
          "Heute ich lerne Deutsch.","Heute lerne ich Deutsch.","When heute is first, the verb is second and the subject follows it.","Am Montag ______ wir Deutsch. (lernen)","lernen","When a time phrase starts a statement, the subject must come before the verb."),
        legacy("a1-lesson-4","Accusative Objects and Negation"),
      ]},
    { "id":"a1-m04","level":"A1","order":4,"title":"Daily Routine, Food, Shopping, and Time",
      "description":"Ask for goods, understand prices, talk about meals and routines, and arrange simple activities.",
      "topics":[
        T("numbers-time-date","Numbers, Dates, and Time","Use numbers for prices, ages, dates, and appointments. German dates use ordinal numbers; halb neun means halfway to nine (8:30), not 9:30.","Use um + time for an appointment. Say acht Uhr for 8:00; halb neun for 8:30. Dates commonly use am + ordinal number.","um acht Uhr; am dritten Mai; halb neun = 8:30.",
          [("Der Zug fährt um neun Uhr.","The train leaves at nine."),("Mein Geburtstag ist am zwölften Juni.","My birthday is on June 12."),("Es ist halb sieben.","It is 6:30.")],
          [("die Uhr","die","die Uhren","clock; o'clock"),("der Termin","der","die Termine","appointment"),("der Geburtstag","der","die Geburtstage","birthday")],
          "Halb sieben means 7:30.","Halb sieben means 6:30.","halb names the next hour and means half an hour before it.","Der Zug fährt um acht ______.","Uhr","halb acht means 7:30."),
        T("daily-routines","Daily Routines and Separable Verbs","Describe a normal day with present-tense verbs and time phrases. Common routine verbs such as aufstehen and einkaufen split in a main clause.","Conjugate the stem in position two and put the prefix at the end: aufstehen → Ich stehe um sieben Uhr auf.","Subject + conjugated stem + details + separable prefix.",
          [("Ich stehe um sieben Uhr auf.","I get up at seven."),("Nach der Arbeit kauft sie ein.","After work she shops."),("Wir sehen am Abend fern.","We watch television in the evening.")],
          [("aufstehen","","","to get up"),("einkaufen","","","to shop"),("fernsehen","","","to watch television")],
          "Ich aufstehe um sieben Uhr.","Ich stehe um sieben Uhr auf.","In a main clause the stem is second and the prefix closes the clause.","Er ruft seine Mutter ______.","an","The prefix stays joined to the verb in a main clause."),
        T("food-meals","Food, Meals, and Preferences","Name everyday food and describe what you like. Use essen and trinken in short present-tense sentences. gern after the verb means that you enjoy the activity.","Use Ich esse/trinke… for actions. gern follows the conjugated verb: Ich esse gern Brot. Möchten is a polite way to say would like.","Subject + conjugated verb + gern + object.",
          [("Zum Frühstück esse ich Brot und Käse.","For breakfast I eat bread and cheese."),("Ich trinke gern Wasser.","I like drinking water."),("Möchten Sie einen Tee?","Would you like a tea?")],
          [("das Brot","das","die Brote","bread; loaf"),("der Käse","der","—","cheese"),("das Wasser","das","—","water")],
          "Ich gern esse Brot.","Ich esse gern Brot.","The conjugated verb comes before gern.","Ich ______ gern Wasser. (trinke)","trinke","gern comes before the conjugated verb."),
        T("shopping-prices","Shopping, Quantities, and Prices","Ask for an item, understand a price, and say how much you need. Polite phrases and quantity words are useful at a market or shop.","Use Ich hätte gern… or Ich möchte… for a request. Ask Was kostet…? for a singular item. State the amount before Euro or other units.","Ich hätte gern + item. / Was kostet + singular noun?",
          [("Ich hätte gern ein Kilo Äpfel.","I would like one kilo of apples."),("Was kostet das Brot?","How much does the bread cost?"),("Das kostet drei Euro fünfzig.","That costs three euros fifty.")],
          [("der Preis","der","die Preise","price"),("das Kilo","das","die Kilos","kilo"),("der Apfel","der","die Äpfel","apple")],
          "Was kosten das Brot?","Was kostet das Brot?","Das Brot is singular, so use kostet.","Ich hätte gern ein ______ Äpfel.","Kilo","Use der Rechnung when asking for the price."),
      ]},
    { "id":"a1-m05","level":"A1","order":5,"title":"Requests, Appointments, and Getting Around",
      "description":"Make polite simple requests, order food, ask for a route, and arrange an appointment or meeting.",
      "topics":[
        T("modal-verbs","Modal Verbs: können and möchten","können expresses ability or possibility; möchten expresses a polite wish. A modal is conjugated while the second verb stays in the infinitive at the end.","Subject + modal in position two + … + infinitive at the end. Examples: Ich kann kommen; Ich möchte Tee trinken.","Ich kann heute kommen. / Ich möchte einen Kaffee trinken.",
          [("Kannst du mir helfen?","Can you help me?"),("Wir können morgen fahren.","We can go tomorrow."),("Ich möchte eine Suppe bestellen.","I would like to order a soup.")],
          [("können","","","can; to be able to"),("möchten","","","would like"),("helfen","","","to help")],
          "Ich kann sprechen Deutsch.","Ich kann Deutsch sprechen.","The infinitive follows the clause at the end.","Wir können heute nicht ______. (kommen)","kommen","After a modal verb, conjugate the second verb."),
        T("cafe","At a Café or Restaurant","Order food politely, ask for a menu, and request the bill. Use formal Sie with a server you do not know; please and thank you make requests natural.","Use Ich möchte… or Ich hätte gern… for an order. Die Rechnung, bitte requests the bill. Masculine accusative ein Kaffee becomes einen Kaffee.","Ich hätte gern…, bitte. / Die Rechnung, bitte.",
          [("Ich hätte gern einen Tee und ein Stück Kuchen.","I would like tea and a piece of cake."),("Die Speisekarte, bitte.","The menu, please."),("Können wir bitte bezahlen?","Can we pay, please?")],
          [("die Speisekarte","die","die Speisekarten","menu"),("die Rechnung","die","die Rechnungen","bill"),("das Stück","das","die Stücke","piece")],
          "Ich möchte ein Kaffee.","Ich möchte einen Kaffee.","Kaffee is masculine; its accusative article is einen.","Die ______, bitte. (the bill)","Rechnung","Say Der Rechnung, bitte."),
        T("directions-transport","Directions and Local Transport","Ask where a place is and understand simple directions. Learn links, rechts, geradeaus and familiar public-transport words.","Ask Wo ist…? or Wie komme ich zum/zur…? Give a polite direction: Gehen Sie geradeaus, dann links. zum combines zu + dem; zur combines zu + der.","Wie komme ich zum Bahnhof? — Gehen Sie geradeaus.",
          [("Wo ist die Bushaltestelle?","Where is the bus stop?"),("Gehen Sie an der Ampel nach links.","Go left at the traffic light."),("Der Zug fährt um zehn Uhr ab.","The train leaves at ten.")],
          [("der Bahnhof","der","die Bahnhöfe","train station"),("die Haltestelle","die","die Haltestellen","stop"),("geradeaus","","","straight ahead")],
          "Wie komme ich zur Bahnhof?","Wie komme ich zum Bahnhof?","Bahnhof is masculine; use zu dem → zum.","Gehen Sie ______, dann links. (straight ahead)","geradeaus","Use zur with a masculine destination."),
        T("appointments","Appointments and Simple Requests","Arrange a time, ask whether someone is available, and make a polite request. Say the day and clock time clearly.","Use Können Sie…? for a polite request; Haben Sie am… Zeit? for availability; um + time for the hour.","Haben Sie am Dienstag um zehn Uhr Zeit?",
          [("Ich möchte einen Termin vereinbaren.","I would like to make an appointment."),("Passt Ihnen Donnerstag um elf Uhr?","Does Thursday at eleven suit you?"),("Können Sie das bitte wiederholen?","Could you repeat that, please?")],
          [("der Termin","der","die Termine","appointment"),("die Zeit","die","die Zeiten","time"),("wiederholen","","","to repeat")],
          "Ich möchte ein Termin.","Ich möchte einen Termin.","Termin is masculine and accusative after möchte.","Haben Sie am Dienstag um zehn Uhr ______?","Zeit","Haben Sie Zeit? asks whether someone is free."),
      ]},
    { "id":"a1-m06","level":"A1","order":6,"title":"A1 Everyday Communication Review",
      "description":"Combine reading, listening, speaking, and writing to complete familiar beginner tasks in social and everyday settings.",
      "topics":[
        T("integrated-review","A1 Integrated Review","Combine introductions, present-tense verbs, articles, time phrases, and questions. Reliable sentence frames help you communicate while your vocabulary is still growing.","Review verb-second statements, verb-first yes/no questions, noun articles, and matching verb endings. Check one feature at a time when proofreading.","Ich heiße…; Ich wohne…; Was machst du gern?; Hast du…?",
          [("Ich heiße Noor und wohne in Bonn.","My name is Noor and I live in Bonn."),("Am Samstag kaufe ich Gemüse.","On Saturday I buy vegetables."),("Hast du heute Zeit?","Do you have time today?")],
          [("die Wiederholung","die","die Wiederholungen","review"),("die Frage","die","die Fragen","question"),("die Antwort","die","die Antworten","answer")],
          "Am Samstag ich kaufe Gemüse.","Am Samstag kaufe ich Gemüse.","Keep the conjugated verb in position two.","Hast du heute ______? (time: Zeit)","Zeit","In yes/no questions, the subject always precedes the verb."),
        T("reading-listening","A1 Reading and Listening Strategies","Understand a short message, sign, timetable, or familiar conversation. Look for known words, names, dates, times, and repeated information before translating.","Read or hear the task first, then scan for the requested detail. In listening, first identify the situation, then listen again for names, places, and numbers. Do not guess beyond the text.","Wer? Wo? Wann? Was? are useful detail questions.",
          [("Der Kurs beginnt am Montag um neun Uhr.","The course begins Monday at nine."),("Bitte hier warten.","Please wait here."),("Der Bus nach Bonn fährt um 14:20 Uhr.","The bus to Bonn leaves at 2:20 p.m.")],
          [("die Nachricht","die","die Nachrichten","message"),("der Fahrplan","der","die Fahrpläne","timetable"),("beginnen","","","to begin")],
          "Translate every unknown word before answering.","Find names, times, and familiar key words first.","Short beginner tasks often ask for one clear detail; full translation is unnecessary.","Der Kurs beginnt am ______. (Monday)","Montag","The first step is translating every unfamiliar word."),
        T("writing-speaking","A1 Writing and Speaking: Introduce Yourself","Write or say a short introduction with your name, origin, languages, home, and one interest. Keep sentences short and use familiar present-tense forms.","Plan a few facts, then join related ideas with und or aber. Start sentences with capitals and capitalize all German nouns.","Ich heiße… Ich komme aus… Ich spreche… Ich wohne…",
          [("Ich heiße Eva. Ich komme aus Polen.","My name is Eva. I come from Poland."),("Ich spreche Polnisch und ein bisschen Deutsch.","I speak Polish and a little German."),("In meiner Freizeit lese ich gern.","In my free time I like reading.")],
          [("die Freizeit","die","die Freizeiten","free time"),("ein bisschen","","","a little"),("lesen","","","to read")],
          "ich heiße eva und wohne in wien.","Ich heiße Eva und wohne in Wien.","Capitalize sentence beginnings and names.","Ich ______ aus Polen. (komme)","komme","German nouns and names are written in lowercase."),
      ]},
    { "id":"a1-m07","level":"A1","order":7,"title":"A1: Talk About People, Everyday Things, and Ownership",
      "description":"Use beginner language to describe people, talk about general habits, and handle familiar shopping and social situations. Grammar supports these practical tasks.",
      "topics":[
        T("cumulative-cases","Nominative, Accusative, and Dative Cases","German cases show what job a noun has in a sentence. Nominative marks the subject, accusative commonly marks the direct object, and dative commonly marks the receiver or the object required by a dative verb or preposition. The article changes with the case, gender, and number.","Nominative: der/die/das/die. Accusative: den/die/das/die. Dative: dem/der/dem/den; dative plural nouns usually add -n when possible. Ask Wer? for the subject, Wen?/Was? for the direct object, and Wem? for the indirect object.","Subject (Nominative) + verb + Dative recipient + Accusative thing.",
          [("Der Mann sieht den Hund.","The man sees the dog."),("Ich helfe dem Mann.","I help the man."),("Ich gebe der Frau das Buch.","I give the woman the book.")],
          [("der Hund","der","die Hunde","the dog"),("die Frau","die","die Frauen","the woman"),("das Buch","das","die Bücher","the book")],
          "Ich helfe den Mann.","Ich helfe dem Mann.","helfen takes a dative object, so masculine der changes to dem.","Ich sehe ___ Hund. (der)","den","The article is chosen only by the noun's gender, not by its role."),
        T("cumulative-demonstratives","Demonstratives and Question Words: dieser and welcher","The uploaded syllabus also reviews dieser (this/these) and welcher (which). They act like article words and take endings that match the noun's gender, number, and case. Use welcher to ask about a choice and dieser to point out a specific person or thing.","Follow the definite-article pattern: dieser Mann / diesen Mann / diesem Mann; diese Frau / dieser Frau; dieses Buch / diesem Buch; diese Bücher / diesen Büchern. Welcher uses the same endings: welcher, welchen, welchem, welche.","Welcher Film? — Diesen Film. / Welchem Mann hilfst du? — Diesem Mann.",
          [("Welcher Film gefällt dir? — Dieser Film.","Which film do you like? — This film."),("Welchen Film siehst du? — Diesen Film.","Which film are you watching? — This one."),("Welcher Frau gibst du das Buch? — Dieser Frau.","Which woman are you giving the book to? — This woman.")],
          [("dieser","","","this; this one"),("welcher","","","which; which one"),("der Film","der","die Filme","film")],
          "Welcher Mann hilfst du?","Welchem Mann hilfst du?","helfen takes dative, so welcher changes to welchem for a masculine noun.","___ Tasche kaufst du? (which)","Welche","Use the nominative ending welcher for every question."),
        T("cumulative-verb-cases","Verbs That Require Accusative or Dative","Some common verbs take an accusative object, while others require dative. Learn each verb together with its case. Accusative verbs in the images include sehen, kaufen, haben, lesen, hören, essen, trinken, and besuchen. Dative verbs include helfen, danken, gefallen, gehören, antworten, glauben, folgen, vertrauen, and schmecken.","Ask Wen?/Was? after an accusative verb and Wem? after a dative verb. With two objects, the person is often dative and the thing accusative: Ich gebe dem Kind das Buch.","Ich sehe den Hund. (Wen?) / Ich helfe dem Hund. (Wem?)",
          [("Sie kauft eine Tasche.","She buys a bag."),("Wir hören die Musik.","We hear the music."),("Das Buch gehört dem Schüler.","The book belongs to the student.")],
          [("helfen","","","to help; takes dative"),("sehen","","","to see; takes accusative"),("gehören","","","to belong to; takes dative")],
          "Ich danke die Lehrerin.","Ich danke der Lehrerin.","danken takes dative; feminine die changes to der.","Ich antworte ___ Lehrer. (der)","dem","All German verbs take the same case."),
        T("cumulative-fixed-prepositions","Prepositions With a Fixed Case","Some prepositions always choose a case. The uploaded syllabus separates fixed accusative prepositions from fixed dative prepositions. Memorize the case with each preposition, then choose the article ending to match the noun.","Accusative: durch, für, gegen, ohne, um. Dative: aus, bei, mit, nach, seit, von, zu. Useful contractions include zu dem = zum, zu der = zur, and von dem = vom.","für + Accusative: für den Kurs. / mit + Dative: mit dem Bus.",
          [("Das Geschenk ist für den Vater.","The gift is for the father."),("Wir fahren mit dem Zug.","We travel by train."),("Sie kommt aus der Schule.","She is coming from school.")],
          [("für","","","for; takes accusative"),("mit","","","with/by; takes dative"),("der Zug","der","die Züge","train")],
          "Ich fahre mit den Bus.","Ich fahre mit dem Bus.","mit always takes dative; masculine der becomes dem.","Das ist ___ meinen Bruder. (for)","für","mit takes accusative."),
        T("cumulative-two-way-prepositions","Two-Way Prepositions: Wo or Wohin?","The nine two-way prepositions are an, auf, hinter, in, neben, über, unter, vor, and zwischen. They can take accusative or dative. The case depends on whether the sentence describes a destination or a location, not simply on whether something is physically moving.","Ask Wohin? (where to?) for a change of location or destination: use accusative. Ask Wo? (where?) for a position or location: use dative. Pair movement verbs such as legen, stellen, and setzen with a destination; pair liegen, stehen, and sitzen with a location.","Wohin? Ich lege das Buch auf den Tisch. / Wo? Das Buch liegt auf dem Tisch.",
          [("Ich gehe in die Schule.","I am going to school."),("Ich bin in der Schule.","I am at school."),("Die Lampe steht neben dem Stuhl.","The lamp is next to the chair.")],
          [("wo?","","","where?; location uses dative"),("wohin?","","","where to?; destination uses accusative"),("liegen","","","to lie; be located")],
          "Das Buch liegt auf den Tisch.","Das Buch liegt auf dem Tisch.","The book is already located on the table, so wo? takes dative.","Ich lege das Buch auf ___ Tisch. (der)","den","Every sentence with physical movement uses accusative, even when no destination is named."),
        T("cumulative-time-prepositions","Time Expressions: ab, an, in, nach, seit, vor","The syllabus images teach six common time prepositions with dative forms. They express a starting time, a day or date, a point in the future, sequence, duration up to now, or a point in the past. The context tells you which meaning is intended.","ab = from/starting on; an = on a day/date (often am); in = after a future period (often in or im); nach = after; seit = since/for and continues now; vor = ago/before. In these uses, follow the preposition with dative: seit einem Jahr, nach dem Essen, vor zwei Tagen.","Ab Montag… / Am Freitag… / In einer Stunde… / Seit einem Jahr… / Vor zwei Tagen…",
          [("Wir treffen uns am Freitag.","We are meeting on Friday."),("Der Zug kommt in zehn Minuten.","The train arrives in ten minutes."),("Ich wohne seit einem Jahr in Berlin.","I have lived in Berlin for a year.")],
          [("seit","","","since; for a period continuing now"),("vor","","","ago; before"),("der Monat","der","die Monate","month")],
          "Seit zwei Stunden means after two hours in the future.","Seit zwei Stunden means for two hours up to now.","seit describes a situation that began in the past and continues now; in zwei Stunden means after two hours.","Der Film beginnt ___ zehn Minuten. (in)","in","Use vor for a future event after a period of time."),
        T("cumulative-pronoun-man","The Indefinite Pronoun man","Use man to make a general statement about people, similar to English one, people, or you in a general sense. It is a pronoun, not the noun Mann (a man). Even though it refers to people generally, man always takes the third-person singular verb form.","man + third-person singular verb: man spricht, man lernt, man muss. To negate, place nicht after the relevant phrase: Man raucht hier nicht.","Man spricht Deutsch. / Der Mann spricht Deutsch.",
          [("Man spricht Deutsch in Deutschland.","People speak German in Germany."),("Man muss pünktlich sein.","You have to be on time."),("Der Mann arbeitet im Krankenhaus.","The man works in the hospital.")],
          [("man","","","one; people in general"),("der Mann","der","die Männer","man; male person"),("sprechen","","","to speak")],
          "Man sprechen Deutsch.","Man spricht Deutsch.","man uses the same singular verb form as er/sie/es.","Man ___ jeden Tag. (lernen)","lernt","man means a male person and needs the noun article der."),
        T("cumulative-perfekt-extension","Syllabus Extension: Perfekt and Partizip II","Several uploaded pages teach the Perfekt, the common spoken past tense. Form it with a present-tense auxiliary (haben or sein) and a past participle. Most verbs use haben. Use sein especially with a change of location or state. The auxiliary is the finite verb; the participle usually goes at the end.","Regular participles often use ge- + stem + -t (lernen → gelernt). Many irregular participles change their stem and must be learned (sprechen → gesprochen). Separable verbs place ge after the prefix (einkaufen → eingekauft). Inseparable prefixes be-, emp-, ent-, er-, ge-, miss-, ver-, zer- and verbs ending in -ieren do not add ge-. Questions put the auxiliary first or after a W-word.","Subject + haben/sein + other information + Partizip II: Ich habe gestern gelernt. / Ich bin nach Berlin gefahren.",
          [("Ich habe Deutsch gelernt.","I learned German."),("Wir sind nach Berlin gefahren.","We went to Berlin."),("Er hat seine Oma besucht.","He visited his grandmother.")],
          [("haben","","","to have; auxiliary for most verbs"),("sein","","","to be; auxiliary for many movement/change verbs"),("das Partizip II","das","die Partizipien II","past participle")],
          "Every verb in the Perfekt uses haben.","Most verbs use haben; many verbs of movement or change use sein.","For example, gehen uses sein: Ich bin nach Hause gegangen.","Sie ___ einen Brief geschrieben. (haben)","hat","In a Perfekt statement, the auxiliary is in position two and the participle goes at the end."),
        T("cumulative-genitive-extension","Syllabus Extension: Genitive Possession","The uploaded syllabus includes the genitive case for possession and belonging. It answers Wessen? (whose?). Names usually take -s without an apostrophe; names ending in an s, ß, x, or z sound commonly take an apostrophe. With regular nouns, feminine and plural possessors use der; masculine and neuter possessors use des and add -s or -es to the noun.","Name + s: Marias Auto. Feminine/plural: die Tasche der Frau, die Farbe der Bücher. Masculine/neuter: das Auto des Mannes, die Farbe des Autos. A von phrase is a useful alternative in speech. This is a syllabus extension beyond the usual A1 core.","Wessen Auto? — Das Auto des Mannes. / Das ist Marias Auto.",
          [("Das ist Marias Auto.","That is Maria's car."),("Die Tasche der Frau ist neu.","The woman's bag is new."),("Das Auto des Mannes ist rot.","The man's car is red.")],
          [("der Genitiv","der","—","genitive case"),("der Mann","der","die Männer","man"),("das Auto","das","die Autos","car")],
          "German adds an apostrophe to a name to show possession.","German normally adds -s directly to a name: Marias Auto.","Regular names take -s without an apostrophe; names ending in an s, ß, x, or z sound commonly take an apostrophe.","Das Buch ___ Kindes ist neu. (the child)","des","Use an apostrophe with every German name showing possession."),
      ]},
]

A2_MODULES = [
    {"id":"a2-m01","level":"A2","order":1,"title":"Routines, Places, and Recent Events",
     "description":"Describe daily routines and recent experiences, explain where things are or are going, and use case and tense patterns in those situations.",
     "topics":[
        legacy("a2-lesson-1","Separable Verbs in Main Clauses and Infinitives"),
        legacy("a2-lesson-2","Perfekt: Spoken Past Tense"),
        T("dative-case","Dative Case: Indirect Objects and Dative Verbs","The dative commonly marks the person receiving something and follows several frequent verbs and prepositions. Learn the article changes and practice the forms in useful sentences.","Dative articles: der→dem, die→der, das→dem, plural die→den (often add -n to the noun). mit, nach, bei, seit, von, zu, aus take dative.","Subject + verb + dative recipient + accusative thing.",
          [("Ich gebe dem Kind das Buch.","I give the child the book."),("Wir fahren mit der Straßenbahn.","We travel by tram."),("Sie hilft ihrem Bruder.","She helps her brother.")],
          [("dem Kind","das","den Kindern","to the child"),("die Straßenbahn","die","die Straßenbahnen","tram"),("helfen","","","to help")],
          "Ich fahre mit den Bus.","Ich fahre mit dem Bus.","mit always takes the dative; masculine dem replaces der.","Ich fahre mit ______ Bus. (der)","dem","mit takes the accusative."),
        T("two-way-prepositions","Two-Way Prepositions: Location or Destination","The prepositions an, auf, hinter, in, neben, über, unter, vor, and zwischen can take dative or accusative. Ask wo? for location and wohin? for movement toward a destination.","Location (wo?) uses dative: Das Buch liegt auf dem Tisch. Direction (wohin?) uses accusative: Ich lege das Buch auf den Tisch.","wo? + dative; wohin? + accusative.",
          [("Die Tasche liegt neben dem Stuhl.","The bag is next to the chair."),("Ich stelle die Tasche neben den Stuhl.","I put the bag next to the chair."),("Wir gehen in die Küche.","We are going into the kitchen.")],
          [("die Richtung","die","die Richtungen","direction"),("liegen","","","to be lying; located"),("stellen","","","to put upright")],
          "Das Buch liegt auf den Tisch.","Das Buch liegt auf dem Tisch.","A stationary location answers wo? and uses dative.","Ich lege das Buch auf ______ Tisch. (der)","den","Movement toward a destination always uses dative."),
        T("reflexive-verbs","Reflexive Verbs in Everyday Routines","Some verbs use a reflexive pronoun that refers back to the subject. Learn the verb together with its pronoun, such as sich freuen or sich interessieren.","Accusative reflexive forms: mich, dich, sich, uns, euch, sich. The pronoun normally follows the conjugated verb in a main clause: Ich freue mich.","Subject + conjugated reflexive verb + reflexive pronoun + details.",
          [("Ich interessiere mich für Musik.","I am interested in music."),("Sie freut sich auf den Urlaub.","She is looking forward to the holiday."),("Wir treffen uns um acht Uhr.","We are meeting at eight.")],
          [("sich interessieren","","","to be interested"),("sich freuen","","","to be happy; look forward"),("sich treffen","","","to meet")],
          "Ich interessiere für Musik.","Ich interessiere mich für Musik.","This verb requires the reflexive pronoun mich for ich.","Wir treffen ______ um acht Uhr. (ourselves)","uns","Reflexive verbs never use a reflexive pronoun."),
     ]},
    {"id":"a2-m02","level":"A2","order":2,"title":"Home, Work, Health, and Travel",
     "description":"Complete familiar tasks involving housing, workplace routines, health appointments, accommodation, and travel plans.",
     "topics":[
        T("housing-household","Housing, Rooms, and Household Tasks","Describe a home, name rooms and furniture, and say what needs doing. Learn noun gender and plural with each new household word.","Use es gibt + accusative to say there is/are. Describe location with dative: Der Tisch steht im Wohnzimmer (in dem Wohnzimmer).","Es gibt + accusative; location wo? + dative.",
          [("In meiner Wohnung gibt es zwei Zimmer.","There are two rooms in my apartment."),("Der Schlüssel liegt auf dem Tisch.","The key is on the table."),("Am Samstag räume ich die Küche auf.","On Saturday I tidy the kitchen.")],
          [("die Wohnung","die","die Wohnungen","apartment"),("das Zimmer","das","die Zimmer","room"),("der Schlüssel","der","die Schlüssel","key")],
          "Es gibt der Küche.","Es gibt die Küche.","es gibt is followed by an accusative object.","Der Schlüssel liegt auf ______ Tisch. (der)","dem","A location after auf always uses accusative."),
        T("work-education","Work, Study, and Responsibilities","Talk about jobs, studies, schedules, and responsibilities. Combine present-tense clauses with time expressions and common workplace vocabulary.","Use arbeiten/lernen + place or subject: Ich arbeite bei…; Ich studiere…; Ich muss heute… Modal verbs send the infinitive to the end.","Ich arbeite bei… / Ich muss heute länger arbeiten.",
          [("Ich arbeite in einem Büro.","I work in an office."),("Meine Kollegin beginnt um acht Uhr.","My colleague starts at eight."),("Wir müssen die Aufgabe heute beenden.","We have to finish the task today.")],
          [("das Büro","das","die Büros","office"),("die Kollegin","die","die Kolleginnen","colleague"),("die Aufgabe","die","die Aufgaben","task")],
          "Wir müssen beenden die Aufgabe.","Wir müssen die Aufgabe beenden.","The infinitive follows the clause at the end after müssen.","Ich muss heute länger ______. (arbeiten)","arbeiten","After müssen, use the conjugated infinitive."),
        T("health-appointments","Health, Symptoms, and Appointments","Explain a simple symptom, ask for help, and arrange an appointment. Distinguish haben Schmerzen from sein krank and use polite questions with Sie.","Use Ich habe… Schmerzen or Mir tut… weh. For an appointment ask Haben Sie am… einen Termin frei? Body-part nouns are capitalized and learned with articles.","Ich habe + accusative plural pain; Mir tut + body part + weh.",
          [("Ich habe seit gestern Kopfschmerzen.","I have had a headache since yesterday."),("Mein Rücken tut weh.","My back hurts."),("Haben Sie morgen einen Termin frei?","Do you have an appointment available tomorrow?")],
          [("der Kopf","der","die Köpfe","head"),("der Rücken","der","die Rücken","back"),("die Gesundheit","die","—","health")],
          "Ich bin Kopfschmerzen.","Ich habe Kopfschmerzen.","Use haben with Schmerzen; do not translate English have/feel literally.","Mein Rücken tut ______.","weh","Use sein weh to describe pain."),
        T("travel-accommodation","Travel, Accommodation, and Plans","Ask about transport and accommodation, describe a trip, and handle simple travel changes. The Perfekt is common when recounting completed trips.","Use fahren/gehen with sein in Perfekt when describing movement to another place: Wir sind nach Wien gefahren. Ask Wo fährt der Zug ab? and Wann kommen wir an?","sein/haben in position two + Partizip II at the end.",
          [("Wir sind am Wochenende nach Wien gefahren.","We traveled to Vienna at the weekend."),("Das Hotel liegt neben dem Bahnhof.","The hotel is next to the station."),("Wann kommt der Zug an?","When does the train arrive?")],
          [("die Unterkunft","die","die Unterkünfte","accommodation"),("das Hotel","das","die Hotels","hotel"),("ankommen","","","to arrive")],
          "Wir haben nach Wien gefahren.","Wir sind nach Wien gefahren.","fahren for a change of location takes sein in the Perfekt.","Wir ______ nach Wien gefahren. (are: sind)","sind","Movement to a destination always takes haben."),
     ]},
    {"id":"a2-m03","level":"A2","order":3,"title":"Services, Requests, and Staying in Touch",
     "description":"Invite and respond, make polite service requests, discuss simple obligations, and handle short calls and messages.",
     "topics":[
        T("invitations","Invitations, Plans, and Responses","Invite someone, suggest a time, accept, or politely decline. State the activity and time clearly, and use a short reason when declining.","Use Hast du Lust, … zu…? or Möchtest du…? Accept with Ja, gern; decline with Leider kann ich nicht, weil… (the subordinate clause is an A2 preview).","Hast du Lust, am Samstag ins Kino zu gehen?",
          [("Möchtest du am Freitag mitkommen?","Would you like to come along on Friday?"),("Ja, gern. Um wie viel Uhr?","Yes, gladly. At what time?"),("Leider kann ich nicht, ich muss arbeiten.","Unfortunately I can't; I have to work.")],
          [("die Einladung","die","die Einladungen","invitation"),("mitkommen","","","to come along"),("leider","","","unfortunately")],
          "Hast du Lust am Samstag ins Kino gehen?","Hast du Lust, am Samstag ins Kino zu gehen?","The zu-infinitive phrase closes the invitation.","Hast du Lust, heute ______? (to come along: mitzukommen)","mitzukommen","Hast du Lust takes a conjugated verb immediately after Lust."),
        T("polite-requests","Polite Requests and Everyday Service","Ask for help, clarification, or an item in a shop or office. Modal verbs make requests less direct; bitte and danke support a polite tone.","Use Könnten Sie…? or Können Sie bitte…? for requests. In a subordinate infinitive phrase, the requested action remains at the end.","Könnten Sie mir bitte helfen? / Ich hätte gern…",
          [("Könnten Sie mir den Weg erklären?","Could you explain the way to me?"),("Können Sie das bitte wiederholen?","Can you repeat that, please?"),("Ich hätte gern einen Termin.","I would like an appointment.")],
          [("höflich","","","polite"),("erklären","","","to explain"),("die Bitte","die","die Bitten","request")],
          "Könnten Sie helfen mir?","Könnten Sie mir helfen?","The dative pronoun mir comes before the infinitive helfen.","Könnten Sie mir bitte ______? (help: helfen)","helfen","Use mir helfen Sie könnten as a question."),
        T("advice-obligation","Advice and Obligation: sollen, müssen, dürfen","Distinguish obligation, advice, and permission. müssen expresses necessity; sollen often reports advice or an instruction; dürfen means be allowed to.","The modal verb is conjugated in position two and the infinitive goes to the end. Negative nicht dürfen means must not; nicht müssen means do not have to.","Du solltest…; Du musst…; Hier darf man nicht…",
          [("Du sollst mehr Wasser trinken.","You should drink more water."),("Ich muss heute zum Arzt gehen.","I have to go to the doctor today."),("Hier darf man nicht rauchen.","You are not allowed to smoke here.")],
          [("sollen","","","should; be supposed to"),("müssen","","","must; have to"),("dürfen","","","may; be allowed to")],
          "Du darfst hier nicht rauchen means you do not have to smoke here.","Du darfst hier nicht rauchen means you must not smoke here.","nicht dürfen prohibits an action; nicht müssen removes the obligation.","Ich muss heute zum Arzt ______. (gehen)","gehen","nicht müssen means a strict prohibition."),
        T("phone-email","Phone Calls and Short Emails","Open and close a simple call or email, ask for a person, leave a message, and request a reply. Use formal greetings for unfamiliar contacts.","Formal email: Sehr geehrte Frau…; Guten Tag…; Mit freundlichen Grüßen. On the phone ask Kann ich bitte mit… sprechen? Use Sie with a new contact.","Greeting + reason for contact + request + closing.",
          [("Guten Tag, hier spricht Amir Khan.","Good day, Amir Khan speaking."),("Kann ich bitte mit Frau Weber sprechen?","May I speak with Ms. Weber, please?"),("Vielen Dank für Ihre Nachricht.","Thank you very much for your message.")],
          [("die Nachricht","die","die Nachrichten","message"),("sprechen","","","to speak"),("der Anruf","der","die Anrufe","phone call")],
          "Hallo Frau Weber, ich will Termin.","Guten Tag, Frau Weber. Ich möchte einen Termin vereinbaren.","A polite formal message uses a greeting and a complete request.","Kann ich bitte mit Frau Weber ______? (sprechen)","sprechen","Use du with a person you have never met in a formal call."),
     ]},
    {"id":"a2-m04","level":"A2","order":4,"title":"Understand and Create Practical Messages",
     "description":"Read notices, listen for instructions and sequence, write short useful emails, and report personal experiences.",
     "topics":[
        T("reading-practical","Reading Practical Messages and Notices","Read short emails, notices, menus, and schedules for purpose and detail. Identify sender, date, place, requested action, and important conditions.","Read the question first, then scan for matching names, dates, times, and modal words such as muss or darf. Separate what the text states from what you infer.","Who wrote it? What action is needed? By when?",
          [("Der Termin wurde auf Dienstag verschoben.","The appointment was moved to Tuesday."),("Bitte bringen Sie Ihren Ausweis mit.","Please bring your identification."),("Der Laden schließt heute um 18 Uhr.","The shop closes at 6 p.m. today.")],
          [("der Ausweis","der","die Ausweise","identification card"),("verschieben","","","to move; reschedule"),("schließen","","","to close")],
          "A notice says Dienstag; answer Donnerstag from memory.","Use the date stated in the notice: Dienstag.","Answer from the text, not from what usually happens.","Der Termin wurde auf ______ verschoben.","Dienstag","A reading answer may be guessed from personal experience."),
        T("listening-details","Listening for Details and Sequences","Follow a short announcement or conversation about a plan. Listen for time, place, change, and sequence words such as zuerst, danach, später, and schließlich.","First listen for the situation and speakers. On a second listen, note the key detail requested. If a speaker corrects an earlier time, use the final confirmed time.","zuerst → danach → später; write names, times, places.",
          [("Zuerst fahren wir zum Markt, danach gehen wir nach Hause.","First we go to the market, then we go home."),("Der Bus kommt zehn Minuten später.","The bus arrives ten minutes later."),("Der Treffpunkt ist vor dem Museum.","The meeting point is in front of the museum.")],
          [("zuerst","","","first"),("danach","","","after that"),("der Treffpunkt","der","die Treffpunkte","meeting point")],
          "Ignore a correction and keep the first time you hear.","Use the final time confirmed by the speaker.","A correction replaces the earlier detail.","Zuerst… und ______ gehen wir nach Hause.","danach","zuerst means after that."),
        T("writing-short-email","Writing a Clear Short Email","Write a short email to arrange or change a plan. Include a greeting, reason, date or request, and closing; keep sentences clear and check verb position.","Use a polite opening, one idea per sentence, and a suitable closing. Capitalize nouns and formal Sie/Ihr. In a main clause keep the conjugated verb in position two.","Greeting + purpose + detail/request + closing.",
          [("Ich schreibe Ihnen, weil ich den Termin ändern muss.","I am writing because I have to change the appointment."),("Passt Ihnen Donnerstag um zehn Uhr?","Does Thursday at ten suit you?"),("Vielen Dank und freundliche Grüße.","Thank you and kind regards.")],
          [("die E-Mail","die","die E-Mails","email"),("ändern","","","to change"),("freundlich","","","friendly; kind")],
          "Ich schreibe weil ich muss den Termin ändern.","Ich schreibe, weil ich den Termin ändern muss.","A weil clause sends the conjugated modal verb to the end.","Ich schreibe Ihnen, weil ich den Termin ändern ______. (muss)","muss","In a weil clause the verb stays in position two."),
        T("speaking-experiences","Speaking About Experiences and Plans","Give a connected short answer about a recent activity or an upcoming plan. Use time phrases and the Perfekt for completed past events.","Perfekt: haben/sein conjugated in position two + Partizip II at the end. Add zuerst, dann, and danach to make the sequence easy to follow.","Gestern habe ich…; Am Wochenende bin ich…",
          [("Am Samstag habe ich meine Freunde besucht.","On Saturday I visited my friends."),("Danach sind wir ins Café gegangen.","After that we went to the café."),("Nächstes Wochenende möchte ich wandern.","Next weekend I would like to hike.")],
          [("besuchen","","","to visit"),("wandern","","","to hike"),("das Wochenende","das","die Wochenenden","weekend")],
          "Am Samstag ich habe meine Freunde besucht.","Am Samstag habe ich meine Freunde besucht.","The auxiliary verb is second after the time phrase.","Danach ______ wir ins Café gegangen. (sind)","sind","In the Perfekt, put the auxiliary at the end."),
     ]},
    {"id":"a2-m05","level":"A2","order":5,"title":"A2 Integrated Everyday Tasks",
     "description":"Combine grammar, vocabulary, and the four language skills to complete practical everyday tasks.",
     "topics":[
        T("cases-prepositions-review","Reviewing Cases and Prepositions","Choose a case from the role a word plays and from the preposition. Practice nominative subjects, accusative direct objects, and frequent dative prepositions in whole phrases.","Who/what performs the action is nominative; the direct object is accusative; mit, nach, bei, seit, von, zu, aus take dative. Two-way prepositions use dative for location and accusative for destination.","Nominative subject + verb + accusative object; mit + dative.",
          [("Der Mann kauft einen Mantel.","The man buys a coat."),("Wir fahren mit dem Zug.","We travel by train."),("Das Kind stellt den Ball unter den Tisch.","The child puts the ball under the table.")],
          [("der Mantel","der","die Mäntel","coat"),("der Zug","der","die Züge","train"),("der Ball","der","die Bälle","ball")],
          "Wir fahren mit den Zug.","Wir fahren mit dem Zug.","mit requires dative masculine dem.","Ich fahre mit ______ Zug. (der)","dem","A two-way preposition always uses accusative."),
        T("past-review","Reviewing Perfekt and Past Events","Tell what happened with common regular and irregular participles. Select haben or sein, place the auxiliary in position two, and put the participle at the end.","Most verbs use haben. Movement between places and change of state often use sein. Regular participles often ge-…-t; many irregular forms must be learned.","Ich habe gelernt. / Ich bin gefahren.",
          [("Ich habe gestern lange gearbeitet.","I worked for a long time yesterday."),("Wir sind nach Hause gegangen.","We went home."),("Sie hat ihre Freundin angerufen.","She called her friend.")],
          [("gearbeitet","","","worked"),("gegangen","","","gone; went"),("angerufen","","","called")],
          "Wir haben nach Hause gegangen.","Wir sind nach Hause gegangen.","gehen describes movement to a destination and uses sein.","Sie hat ihre Freundin ______. (angerufen)","angerufen","Movement verbs always use haben."),
        T("a2-integrated-communication","A2 Integrated Everyday Task","Combine listening or reading details with a practical response: arrange a meeting, explain a change, ask for help, or recount a short event. Give enough detail for the listener to act.","Plan the key facts (who, when, where, why). Use a polite request, correct time phrase, and either present/future plan or Perfekt for a completed event.","Request + time/place detail + reason or response.",
          [("Könnten wir den Termin auf Freitag verschieben?","Could we move the appointment to Friday?"),("Ich komme um halb sechs am Bahnhof an.","I arrive at the station at 5:30."),("Gestern habe ich die Nachricht gelesen.","Yesterday I read the message.")],
          [("verschieben","","","to reschedule"),("ankommen","","","to arrive"),("die Einzelheit","die","die Einzelheiten","detail")],
          "Könnten wir verschieben den Termin?","Könnten wir den Termin verschieben?","The infinitive goes at the end after the modal verb.","Gestern ______ ich die Nachricht gelesen. (habe)","habe","In the Perfekt, the auxiliary follows the participle."),
     ]},
]

B1_MODULES = [
    {"id":"b1-m01","level":"B1","order":1,"title":"Connected Explanations and Polite Communication",
     "description":"Explain reasons and conditions, add information, report processes, and make tactful requests using connected language.",
     "topics":[
        legacy("b1-lesson-1","Subordinate Clauses and Verb Position"),
        legacy("b1-lesson-2","Present Passive and Agent Phrases"),
        T("relative-clauses","Relative Clauses: Adding Information About Nouns","Relative clauses add detail about a person or thing. The relative pronoun agrees in gender and number with the noun it refers to, while its case depends on its role inside the clause.","A relative clause follows its noun and is set off by commas. The finite verb moves to the end: Das ist der Kollege, der neben mir arbeitet. Use dative forms when required by a verb or preposition.","Noun + comma + relative pronoun + details + verb at end.",
          [("Das ist die Frau, die bei uns arbeitet.","That is the woman who works with us."),("Ich lese ein Buch, das sehr spannend ist.","I am reading a book that is very exciting."),("Der Mann, mit dem ich gesprochen habe, ist Arzt.","The man with whom I spoke is a doctor.")],
          [("der Kollege","der","die Kollegen","colleague"),("die Beschreibung","die","die Beschreibungen","description"),("sich beziehen auf","","","to refer to")],
          "Das ist die Frau, die arbeitet bei uns.","Das ist die Frau, die bei uns arbeitet.","A subordinate relative clause sends the conjugated verb to the end.","Das ist der Kollege, der neben mir ______. (arbeitet)","arbeitet","The verb stays in position two inside the relative clause."),
        T("konjunktiv-ii","Konjunktiv II: Polite Requests and Hypothetical Situations","Konjunktiv II softens a request and describes an unreal or imagined situation. Frequent forms include wäre, hätte, könnte, and würde + infinitive.","Use Könnten Sie…? for a polite request. Use Wenn ich Zeit hätte, würde ich reisen for a hypothetical condition and result. Common forms like wäre and hätte are often preferred to würde + sein/haben.","Wenn + subject + Konjunktiv II…, würde + infinitive.",
          [("Könnten Sie mir bitte helfen?","Could you help me, please?"),("Wenn ich mehr Zeit hätte, würde ich öfter lesen.","If I had more time, I would read more often."),("An deiner Stelle würde ich mit ihr sprechen.","If I were you, I would talk to her.")],
          [("der Wunsch","der","die Wünsche","wish"),("höflich","","","polite"),("an deiner Stelle","","","if I were you")],
          "Wenn ich hätte Zeit, würde ich reisen.","Wenn ich Zeit hätte, würde ich reisen.","The finite verb stands at the end of a wenn-clause.","Könnten Sie mir bitte ______? (help: helfen)","helfen","Könnten Sie… is less polite than Kannst du…"),
        T("connectors-word-order","Connectors and Word Order: weil, obwohl, trotzdem","Choose a connector that expresses cause, contrast, or addition. Connectors influence where the conjugated verb appears, so group them by clause structure.","weil, dass, obwohl, wenn send the conjugated verb to the end. aber, und, denn keep ordinary main-clause order; trotzdem and deshalb can begin a main clause followed by the verb.","weil/obwohl + verb at end; trotzdem/deshalb + verb in position two.",
          [("Ich bleibe zu Hause, weil ich krank bin.","I am staying home because I am ill."),("Obwohl es regnet, gehen wir spazieren.","Although it is raining, we are going for a walk."),("Es regnet. Trotzdem gehen wir spazieren.","It is raining. Nevertheless, we are going for a walk.")],
          [("der Grund","der","die Gründe","reason"),("der Gegensatz","der","die Gegensätze","contrast"),("trotzdem","","","nevertheless")],
          "Ich bin müde, obwohl ich gehe ins Bett.","Ich gehe ins Bett, obwohl ich müde bin.","The verb of the obwohl-clause goes at the end.","Ich bleibe zu Hause, weil ich krank ______. (bin)","bin","trotzdem sends its verb to the end of the sentence."),
     ]},
    {"id":"b1-m02","level":"B1","order":2,"title":"Work, Media, Environment, and Society",
     "description":"Understand and discuss work and education, media, mobility, environmental choices, and social questions with relevant examples.",
     "topics":[
        T("work-education-b1","Work, Education, and Career Paths","Discuss qualifications, responsibilities, career plans, and workplace experience. Use precise nouns and verbs to explain what you do, what you have done, and what you hope to do.","Use als + profession without an article in many job statements: Ich arbeite als Ingenieurin. Use sich bewerben um + accusative and Erfahrung mit + dative.","Ich arbeite als…; Ich habe Erfahrung mit…; Ich bewerbe mich um…",
          [("Ich habe mich um eine Stelle beworben.","I applied for a position."),("Sie hat viel Erfahrung mit Projektarbeit.","She has a lot of experience with project work."),("Nach dem Studium möchte er sich weiterbilden.","After his studies he wants to continue his education.")],
          [("die Stelle","die","die Stellen","position"),("die Erfahrung","die","die Erfahrungen","experience"),("sich bewerben","","","to apply")],
          "Ich bewerbe mich für eine Stelle um.","Ich bewerbe mich um eine Stelle.","The verb phrase is sich bewerben um + accusative.","Sie hat viel Erfahrung ______ Projektarbeit. (mit)","mit","Use Erfahrung auf + accusative for experience with a field."),
        T("media-technology","Media, Technology, and Reliable Information","Describe how people use media, compare sources, and explain advantages or concerns about technology. Distinguish reported information from your own opinion.","Use berichten über + accusative, sich informieren über + accusative, and the passive when the actor is unknown or unimportant. Attribute a claim: Laut dem Artikel…","Der Bericht informiert über… / Laut der Quelle…",
          [("Laut dem Bericht nutzen viele Menschen digitale Medien.","According to the report, many people use digital media."),("Man sollte die Quelle sorgfältig prüfen.","One should check the source carefully."),("Die Daten werden regelmäßig aktualisiert.","The data are updated regularly.")],
          [("die Quelle","die","die Quellen","source"),("der Bericht","der","die Berichte","report"),("zuverlässig","","","reliable")],
          "Ich informiere mich der Quelle.","Ich informiere mich über die Quelle.","Use sich informieren über + accusative.","Man sollte die Quelle sorgfältig ______. (prüfen)","prüfen","Laut introduces a reported source; it proves the claim is true."),
        T("environment-society","Environment, Mobility, and Shared Responsibility","Discuss everyday environmental choices and community issues without claiming that one action solves a complex problem. Compare options and explain likely effects.","Use comparative forms with als: Der Zug ist oft günstiger als das Auto. Use weil/da for reasons and modal verbs for suggestions: Man könnte…","Option + comparative + als + alternative; suggestion + könnte.",
          [("Mit dem Zug zu fahren ist oft umweltfreundlicher.","Traveling by train is often more environmentally friendly."),("Wir könnten öfter Dinge wiederverwenden.","We could reuse things more often."),("Viele Menschen trennen ihren Müll.","Many people sort their waste.")],
          [("die Umwelt","die","—","environment"),("die Verantwortung","die","die Verantwortungen","responsibility"),("wiederverwenden","","","to reuse")],
          "Der Zug ist mehr umweltfreundlich als das Auto.","Der Zug ist umweltfreundlicher als das Auto.","Short adjectives commonly form the comparative with -er.","Wir könnten Dinge öfter ______. (reuse: wiederverwenden)","wiederverwenden","Every environmental action guarantees a complete solution."),
        T("opinions-emotions","Opinions, Feelings, and Nuanced Vocabulary","Explain how you feel and why, and distinguish a personal view from a fact. Use a range of opinion phrases and give a reason or example.","State Mein Eindruck ist… or Meiner Meinung nach…. Use sich freuen über for a current reason and sich freuen auf for an anticipated event.","Viewpoint + claim + reason/example.",
          [("Meiner Meinung nach ist der Vorschlag sinnvoll.","In my opinion the suggestion is sensible."),("Ich freue mich über deine Nachricht.","I am happy about your message."),("Sie freut sich auf den Besuch.","She is looking forward to the visit.")],
          [("der Eindruck","der","die Eindrücke","impression"),("der Vorschlag","der","die Vorschläge","suggestion"),("sinnvoll","","","sensible; useful")],
          "Meiner Meinung der Plan ist gut.","Meiner Meinung nach ist der Plan gut.","Meiner Meinung nach is followed by verb-second word order.","Ich freue mich ______ den Besuch. (looking forward to)","auf","sich freuen auf is for a completed past event."),
     ]},
    {"id":"b1-m03","level":"B1","order":3,"title":"Opinions, Problems, and Negotiation",
     "description":"Give reasons for a position, handle disagreement, explain a problem, and agree on a constructive next step.",
     "topics":[
        T("expressing-opinions","Expressing and Supporting an Opinion","State a view clearly, give a reason, and support it with an example. A useful answer distinguishes opinion from evidence and acknowledges another perspective.","Use Meiner Ansicht nach…, weil…; Ein Beispiel dafür ist…; Ich verstehe den Einwand, aber…. In a weil-clause the verb goes to the end.","Opinion + reason + example or qualification.",
          [("Meiner Ansicht nach sollte der Kurs später beginnen.","In my view the course should begin later."),("Ein Beispiel dafür ist der lange Arbeitsweg.","One example is the long commute."),("Ich verstehe den Einwand, aber die Lösung ist praktisch.","I understand the objection, but the solution is practical.")],
          [("die Ansicht","die","die Ansichten","view"),("der Einwand","der","die Einwände","objection"),("der Arbeitsweg","der","die Arbeitswege","commute")],
          "Ich finde, dass die Lösung ist praktisch.","Ich finde, dass die Lösung praktisch ist.","A dass-clause sends the conjugated verb to the end.","Ich finde, dass der Vorschlag sinnvoll ______. (ist)","ist","After dass, keep the finite verb in position two."),
        T("discussion-debate","Agreeing, Disagreeing, and Comparing Arguments","Respond to another person's point respectfully. Agree partly, disagree with a reason, and compare advantages and disadvantages instead of repeating a simple yes/no.","Use Einerseits…, andererseits…; Ich stimme teilweise zu, weil…; Dagegen spricht, dass…. Preserve verb-final order after weil and dass.","Einerseits + point A, andererseits + point B.",
          [("Ich stimme teilweise zu, weil der Plan Zeit spart.","I partly agree because the plan saves time."),("Einerseits ist die Wohnung zentral, andererseits ist sie teuer.","On one hand the apartment is central; on the other it is expensive."),("Dagegen spricht, dass der Weg sehr lang ist.","Against it is the fact that the journey is very long.")],
          [("einerseits","","","on one hand"),("andererseits","","","on the other hand"),("teilweise","","","partly")],
          "Einerseits ist es billig, andererseits es dauert lange.","Einerseits ist es billig, andererseits dauert es lange.","The second main clause needs verb-second order.","Ich stimme teilweise zu, weil der Plan Zeit ______. (spart)","spart","After andererseits, place the subject before the verb."),
        T("complaints-problem-solving","Complaints, Problems, and Constructive Solutions","Describe a problem, state what outcome you need, and suggest a practical next step. Keep a complaint factual and polite, especially in a service setting.","Use Leider…, Das Problem besteht darin, dass…; Könnten Sie bitte…? Offer a solution with Vielleicht könnten wir…","Problem + effect + polite request or proposal.",
          [("Leider funktioniert die Heizung seit gestern nicht.","Unfortunately the heating has not worked since yesterday."),("Könnten Sie bitte einen Techniker schicken?","Could you please send a technician?"),("Vielleicht könnten wir einen neuen Termin vereinbaren.","Perhaps we could arrange a new appointment.")],
          [("die Heizung","die","die Heizungen","heating"),("der Techniker","der","die Techniker","technician"),("vereinbaren","","","to arrange")],
          "Ich beschwere mich, schicken Sie Techniker.","Ich möchte mich beschweren. Könnten Sie bitte einen Techniker schicken?","Separate the problem statement and phrase the request politely.","Könnten Sie bitte einen Techniker ______? (schicken)","schicken","Use Schick mir sofort as a polite formal request."),
        T("formal-communication","Formal Communication and Negotiation","Communicate with a landlord, employer, or service provider. Explain the reason for writing, ask for a specific action, and close appropriately.","Use formal Sie/Ihr capitalization and a suitable greeting/closing. In negotiation, state a proposal and condition: Ich könnte…, wenn…; keep verb-final order after wenn.","Formal greeting + purpose + proposal/request + closing.",
          [("Sehr geehrte Frau Roth, ich schreibe Ihnen wegen des Termins.","Dear Ms. Roth, I am writing to you about the appointment."),("Könnten wir einen späteren Zeitpunkt vereinbaren?","Could we arrange a later time?"),("Ich wäre Ihnen für eine kurze Rückmeldung dankbar.","I would be grateful for a brief reply.")],
          [("die Rückmeldung","die","die Rückmeldungen","response"),("der Zeitpunkt","der","die Zeitpunkte","point in time"),("wegen","","","because of; regarding")],
          "Sehr geehrte Frau Roth, ich schreibe ihnen.","Sehr geehrte Frau Roth, ich schreibe Ihnen.","Formal Sie/Ihnen is capitalized.","Ich wäre Ihnen für eine kurze Rückmeldung ______. (dankbar)","dankbar","Formal pronouns are always lowercase."),
     ]},
    {"id":"b1-m04","level":"B1","order":4,"title":"Understand Articles and Real-World Messages",
     "description":"Identify main claims, speaker purpose, evidence, and useful details in longer written and spoken communication.",
     "topics":[
        T("reading-structure","Reading Articles for Structure and Main Ideas","Read a longer article by identifying its subject, paragraph roles, claim, and supporting details. Headings and linking words reveal how information is organized.","Skim title and opening for topic; scan paragraph openings; then read evidence around a relevant detail. Mark contrast and cause connectors rather than translating every word.","Topic → claim → evidence → conclusion.",
          [("Der Artikel beschreibt zunächst das Problem und nennt danach zwei Lösungen.","The article first describes the problem and then gives two solutions."),("Im letzten Absatz fasst die Autorin ihre Ergebnisse zusammen.","In the last paragraph the author summarizes her findings."),("Der folgende Abschnitt enthält ein Beispiel.","The following section contains an example.")],
          [("der Abschnitt","der","die Abschnitte","section"),("das Ergebnis","das","die Ergebnisse","result"),("zusammenfassen","","","to summarize")],
          "The first paragraph is always the conclusion.","Identify the function of each paragraph from its content and connectors.","An article's organization varies; use textual evidence.","Im letzten Absatz fasst die Autorin die Ergebnisse ______. (zusammen)","zusammen","Every article uses the same paragraph structure."),
        T("reading-inference","Inferring Meaning from Context","Use nearby sentences, examples, and contrast markers to infer an unfamiliar word or implication. Label an inference as an interpretation rather than a directly stated fact.","Check the sentence before and after the unknown phrase. Contrast markers such as jedoch and obwohl may reverse an expectation; examples often define a term.","Clue + surrounding context → cautious inference.",
          [("Die Nachfrage sank; dennoch blieb der Preis stabil.","Demand fell; nevertheless the price remained stable."),("Der Text nennt keine Ursache, legt aber einen Zusammenhang nahe.","The text gives no cause but suggests a connection."),("Aus dem Beispiel lässt sich schließen, dass…","From the example one can conclude that…")],
          [("die Nachfrage","die","die Nachfragen","demand"),("dennoch","","","nevertheless"),("nahelegen","","","to suggest")],
          "A suggested connection is always proven causation.","State what the text suggests and distinguish it from what it proves.","Correlation or implication does not by itself establish cause.","Der Text legt einen Zusammenhang ______. (nahe)","nahe","A suggested connection is proof of cause."),
        T("listening-main-ideas","Listening for Main Ideas and Speaker Purpose","Follow a longer conversation or report by identifying its topic, purpose, and speaker attitude. Note signposts for a change of view or a new argument.","First listen for who is speaking and why. Track signposts such as zunächst, allerdings, deshalb, and abschließend. Do not confuse an example with the speaker's main claim.","Speaker + purpose + main claim + supporting point.",
          [("Zunächst erklärt der Sprecher das Ziel des Projekts.","First the speaker explains the project's goal."),("Allerdings nennt er auch einige Schwierigkeiten.","However he also mentions some difficulties."),("Abschließend empfiehlt sie eine neue Lösung.","In conclusion she recommends a new solution.")],
          [("der Sprecher","der","die Sprecher","speaker"),("die Schwierigkeit","die","die Schwierigkeiten","difficulty"),("abschließend","","","in conclusion")],
          "The last example mentioned is always the main idea.","Separate the speaker's central claim from examples and details.","A speaker may use examples to support a broader point.","Abschließend ______ sie eine neue Lösung. (empfiehlt)","empfiehlt","A supporting example is always the main claim."),
        T("listening-notes","Listening for Details and Taking Useful Notes","Capture names, dates, reasons, and changes without trying to write every word. A compact note can preserve the decision and what happens next.","Use short keywords and symbols while listening; afterward rebuild complete sentences. If a speaker revises information, record the final confirmed detail.","Keyword notes → verify sequence → summarize in full sentences.",
          [("Der Zug fällt aus; ein Ersatzbus fährt um zehn Uhr.","The train is canceled; a replacement bus leaves at ten."),("Der Treffpunkt wurde von zwölf auf halb eins verschoben.","The meeting point was moved from twelve to 12:30."),("Notieren Sie Grund, neue Zeit und Treffpunkt.","Note the reason, new time, and meeting point.")],
          [("der Ersatzbus","der","die Ersatzbusse","replacement bus"),("verschieben","","","to reschedule"),("notieren","","","to note down")],
          "Keep the first time heard even after a correction.","Record the last confirmed time: halb eins.","Later corrections replace earlier details.","Der Treffpunkt wurde auf halb eins ______. (verschoben)","verschoben","The first time mentioned is always final."),
     ]},
    {"id":"b1-m05","level":"B1","order":5,"title":"Write Formal and Connected Texts",
     "description":"Write requests, replies, complaints, opinions, and reports with clear structure and supporting reasons.",
     "topics":[
        T("formal-email-b1","Formal Emails: Requests, Replies, and Complaints","Write a formal email with a clear subject, polite opening, reason for writing, specific request, and suitable closing. Keep the tone respectful but direct.","Address with Sehr geehrte/r…; capitalize Sie/Ihnen/Ihr. Use a paragraph per purpose and close with Mit freundlichen Grüßen. Explain a request with weil + verb-final clause.","Subject + greeting + purpose + request + closing.",
          [("Ich wende mich an Sie, weil ich eine Frage zum Vertrag habe.","I am contacting you because I have a question about the contract."),("Könnten Sie mir bitte bis Freitag antworten?","Could you please reply by Friday?"),("Mit freundlichen Grüßen","Kind regards")],
          [("der Vertrag","der","die Verträge","contract"),("sich wenden an","","","to contact"),("die Antwort","die","die Antworten","reply")],
          "Sehr geehrte Frau, ich wende mich weil ich habe eine Frage.","Sehr geehrte Frau…, ich wende mich an Sie, weil ich eine Frage habe.","Use a complete greeting, and move the finite verb to the end after weil.","Ich wende mich an Sie, weil ich eine Frage ______. (habe)","habe","After weil, keep the verb in position two."),
        T("opinion-text","Writing an Opinion Text with Reasons and Examples","Develop a clear position, give reasons, add a relevant example, and acknowledge a limitation or alternative. Separate paragraphs by their function.","State the position early; use weil/da for reasons and zum Beispiel for evidence. Use einerseits/andererseits to compare. End by returning to the main point.","Position → reason → example → qualification → conclusion.",
          [("Ich bin dafür, weil die Maßnahme den Verkehr reduziert.","I support it because the measure reduces traffic."),("Zum Beispiel könnten mehr Busse eingesetzt werden.","For example, more buses could be used."),("Andererseits entstehen dadurch zusätzliche Kosten.","On the other hand, this creates additional costs.")],
          [("die Maßnahme","die","die Maßnahmen","measure"),("der Verkehr","der","—","traffic"),("die Kosten","die","die Kosten","costs")],
          "Ich bin dafür, weil die Maßnahme reduziert Verkehr.","Ich bin dafür, weil die Maßnahme den Verkehr reduziert.","The direct object needs its article and the weil-clause ends with the verb.","Ich bin dafür, weil die Maßnahme den Verkehr ______. (reduziert)","reduziert","After weil, put the finite verb in position two."),
        T("report-narrative","Writing a Report or Short Narrative","Describe an event or experience in a clear sequence. Include where and when it happened, the important events, and the outcome; avoid unrelated details.","Use past tense consistently: Perfekt is common in personal accounts; Präteritum is frequent for sein/haben and in written narration. Connect sequence with zuerst, danach, schließlich.","Setting → event sequence → result/reflection.",
          [("Zuerst haben wir den Raum vorbereitet.","First we prepared the room."),("Danach begann die Veranstaltung pünktlich.","After that the event began on time."),("Am Ende waren alle zufrieden.","At the end everyone was satisfied.")],
          [("die Veranstaltung","die","die Veranstaltungen","event"),("pünktlich","","","on time"),("schließlich","","","finally")],
          "Zuerst haben wir den Raum vorbereitet. Danach die Veranstaltung begann.","Zuerst haben wir den Raum vorbereitet. Danach begann die Veranstaltung.","A main clause after danach keeps the verb in position two.","Danach ______ die Veranstaltung pünktlich. (begann)","begann","After danach, put the subject before the verb."),
        T("cohesion-connectors","Cohesion: Linking Ideas Across Paragraphs","Make writing easier to follow with reference words, repeated key terms, and connectors. Use a connector that matches the logical relation instead of adding one to every sentence.","Cause: deshalb/daher; contrast: trotzdem/jedoch; addition: außerdem; sequence: anschließend. deshalb and trotzdem begin a main clause followed by verb-second order.","Idea A. Connector + verb + subject + idea B.",
          [("Der Bus war verspätet. Deshalb kamen wir später an.","The bus was delayed. Therefore we arrived later."),("Die Aufgabe war schwierig. Trotzdem beendeten wir sie.","The task was difficult. Nevertheless we finished it."),("Außerdem fehlte eine wichtige Information.","In addition an important piece of information was missing.")],
          [("der Zusammenhang","der","die Zusammenhänge","connection"),("außerdem","","","in addition"),("jedoch","","","however")],
          "Es regnete. Trotzdem wir gingen spazieren.","Es regnete. Trotzdem gingen wir spazieren.","trotzdem starts a main clause, so the verb is second.","Es war spät. Deshalb ______ wir ein Taxi. (nahmen)","nahmen","After deshalb, keep the conjugated verb at the end."),
     ]},
    {"id":"b1-m06","level":"B1","order":6,"title":"Speak, Present, and Keep Conversations Moving",
     "description":"Present a view, compare options, take part in service and work conversations, and clarify misunderstandings.",
     "topics":[
        T("short-presentation","Giving a Short Organized Presentation","Present a familiar topic with a clear opening, two or three connected points, and a brief conclusion. Signpost sections so listeners can follow.","Open with Heute möchte ich über… sprechen. Order points with zuerst, außerdem, zum Schluss. Support one point with an example and signal the conclusion.","Opening → points → example → conclusion.",
          [("Heute möchte ich über nachhaltige Mobilität sprechen.","Today I would like to talk about sustainable mobility."),("Ein wichtiger Vorteil ist die gute Verbindung.","One important advantage is the good connection."),("Zum Schluss fasse ich die wichtigsten Punkte zusammen.","To finish I will summarize the most important points.")],
          [("der Vorteil","der","die Vorteile","advantage"),("die Mobilität","die","—","mobility"),("zusammenfassen","","","to summarize")],
          "Zum Schluss ich fasse die Punkte zusammen.","Zum Schluss fasse ich die Punkte zusammen.","When a phrase is first, the conjugated verb follows it.","Heute möchte ich über das Thema ______. (sprechen)","sprechen","After Zum Schluss, the verb remains after the subject."),
        T("compare-options","Comparing Options and Recommending One","Compare two choices using relevant criteria such as cost, time, convenience, and impact. Make a recommendation that follows from those criteria.","Comparative + als compares unequal things; genauso…wie compares equality. Explain a recommendation with weil or denn and cite the criterion.","Option A is… als option B; recommendation + reason.",
          [("Der Zug ist schneller als der Bus.","The train is faster than the bus."),("Das Fahrrad ist genauso praktisch wie der Bus.","The bicycle is just as practical as the bus."),("Ich würde den Zug nehmen, weil er direkt fährt.","I would take the train because it goes directly.")],
          [("der Vergleich","der","die Vergleiche","comparison"),("praktisch","","","practical"),("direkt","","","direct")],
          "Der Zug ist schneller wie der Bus.","Der Zug ist schneller als der Bus.","Use als after a comparative; wie follows genauso.","Das Fahrrad ist genauso praktisch ______ der Bus.","wie","Use als after genauso praktisch."),
        T("roleplay-services","Role-Plays: Services, Work, and Everyday Problems","Take a role in a practical exchange: explain a need, ask a follow-up question, respond to a problem, and agree on a next step. Use polite forms with unfamiliar people.","Clarify the problem with Was genau…?; request action with Könnten Sie…?; confirm with Dann machen wir es so. Use Sie consistently in formal service situations.","Need/problem → clarification → request → confirmation.",
          [("Was genau funktioniert nicht?","What exactly is not working?"),("Könnten Sie mir einen Ersatz anbieten?","Could you offer me a replacement?"),("Dann vereinbaren wir einen neuen Termin.","Then we will arrange a new appointment.")],
          [("der Ersatz","der","die Ersatzteile","replacement"),("vereinbaren","","","to arrange"),("genau","","","exactly")],
          "Könntest du mir einen Ersatz anbieten? (to a formal service contact)","Könnten Sie mir einen Ersatz anbieten?","Use formal Sie with an unfamiliar service contact.","Könnten Sie mir einen Ersatz ______? (anbieten)","anbieten","Use informal du with an unfamiliar person in a formal service situation."),
        T("conversation-repair","Conversation Strategies: Clarifying and Rephrasing","Keep a conversation going when you miss a word or need time. Ask for repetition, check your understanding, and rephrase instead of abandoning the message.","Useful phrases include Könnten Sie das wiederholen?; Meinen Sie…?; Wie sagt man… auf Deutsch?; Ich meine, dass…. A subordinate dass-clause sends the verb to the end.","Clarification request → check understanding → rephrase.",
          [("Könnten Sie die letzte Frage wiederholen?","Could you repeat the last question?"),("Meinen Sie, dass der Termin heute ist?","Do you mean that the appointment is today?"),("Wie sagt man dieses Wort auf Deutsch?","How do you say this word in German?")],
          [("wiederholen","","","to repeat"),("meinen","","","to mean"),("das Verständnis","das","die Verständnisse","understanding")],
          "Meinen Sie, dass der Termin ist heute?","Meinen Sie, dass der Termin heute ist?","In a dass-clause the conjugated verb goes to the end.","Könnten Sie die letzte Frage ______? (wiederholen)","wiederholen","Use dass to keep the verb in position two."),
     ]},
    {"id":"b1-m07","level":"B1","order":7,"title":"B1 Integrated Communication and Examination Preparation",
     "description":"Consolidate B1 grammar and skills with original practice tasks. These are learning activities, not claims about an official examination.",
     "topics":[
        T("b1-grammar-review","B1 Grammar Review: Clauses, Passive, and Konjunktiv II","Review subordinate and relative clauses, present passive, and Konjunktiv II in context. Choose structures by purpose and check where the finite verb belongs.","Subordinate clauses end in the finite verb; passive uses werden + Partizip II; polite/hypothetical forms use könnte/wäre/hätte or würde + infinitive.","Clause type → verb placement → meaning.",
          [("Ich glaube, dass die Entscheidung bald getroffen wird.","I believe that the decision will be made soon."),("Wenn ich mehr Zeit hätte, würde ich teilnehmen.","If I had more time, I would participate."),("Das ist der Bericht, den ich gestern gelesen habe.","That is the report that I read yesterday.")],
          [("die Entscheidung","die","die Entscheidungen","decision"),("teilnehmen","","","to participate"),("treffen","","","to make; meet")],
          "Ich glaube, dass die Entscheidung wird bald getroffen.","Ich glaube, dass die Entscheidung bald getroffen wird.","The finite passive auxiliary closes the dass-clause.","Ich glaube, dass der Bericht interessant ______. (ist)","ist","A dass-clause keeps the verb in position two."),
        T("b1-integrated-comprehension","Integrated Reading and Listening Practice","Combine a short written source and spoken information to compare details. Identify agreement, contradiction, and information that appears in only one source.","Record each source's claim and evidence separately. Check dates, quantities, and contrasts; do not combine statements into a fact unless both sources support it.","Source A says…; Source B adds/contradicts…",
          [("Der Artikel nennt steigende Kosten.","The article mentions rising costs."),("Im Gespräch wird zusätzlich die lange Wartezeit erwähnt.","The conversation additionally mentions the long waiting time."),("Beide Quellen stimmen beim Datum überein.","Both sources agree on the date.")],
          [("die Quelle","die","die Quellen","source"),("übereinstimmen","","","to agree"),("zusätzlich","","","additionally")],
          "Both sources mention a detail even when only one includes it.","Attribute the detail to the source that actually contains it.","Keep source claims separate when details differ.","Im Gespräch wird die lange Wartezeit ______. (erwähnt)","erwähnt","Combine all details as though each source stated them."),
        T("b1-integrated-production","Integrated Writing and Speaking Practice","Prepare a short response from notes: explain the issue, state your position, support it with a reason, and respond to one question. Revise for clarity rather than length.","Plan keywords, organize a position and supporting example, then use connectors. After speaking or writing, check verb placement, case after prepositions, and noun capitalization.","Issue → view → reason/example → response/conclusion.",
          [("Das Thema ist wichtig, weil es viele Menschen betrifft.","The topic is important because it affects many people."),("Ein Beispiel dafür ist der öffentliche Verkehr.","One example is public transport."),("Zusammenfassend halte ich die Lösung für sinnvoll.","In summary I consider the solution sensible.")],
          [("betreffen","","","to affect"),("der öffentliche Verkehr","der","—","public transport"),("zusammenfassend","","","in summary")],
          "Das Thema ist wichtig, weil es betrifft viele Menschen.","Das Thema ist wichtig, weil es viele Menschen betrifft.","The weil-clause puts the conjugated verb at the end.","Das Thema ist wichtig, weil es viele Menschen ______. (betrifft)","betrifft","After weil, the verb remains in position two."),
     ]},
]

_a1_syllabus = next(module for module in A1_MODULES if module["id"] == "a1-m07")
_uploaded_topics = {spec["slug"]: spec for spec in _a1_syllabus["topics"]}

# The uploaded grammar topics are sequenced by what learners need to do in the
# BAMF integration-course framework. Basic personal and shopping exchanges are
# A1; managing places, appointments, services, and recent events is A2. The
# uploaded course syllabus places Genitive in its A1 sequence, so it stays there.
_uploaded_topics["cumulative-genitive-extension"].update({
    "title": "Possession: Genitive in Names and Nouns",
    "focus": "Use the genitive patterns from your A1 syllabus to say who owns something. Practice them with familiar people and objects in short descriptions.",
    "rule": "Names usually take -s without an apostrophe: Marias Auto. With nouns, use der for feminine and plural possessors and des + -s/-es for masculine and neuter possessors. A von phrase is also common in everyday speech.",
    "can_do": "Say who something belongs to and understand simple possession phrases in descriptions of people, family, and home.",
})
_a1_syllabus["topics"] = [
    T("a1-nominative-accusative", "Talking About People and Things: Nominative and Accusative",
      "Use simple sentences to identify people and say what you see, have, need, buy, eat, or read. The nominative marks who or what the sentence is about; the accusative commonly marks the thing affected by the action.",
      "Nominative articles: der/die/das/die. Accusative articles: den/die/das/die. The most visible change is masculine der → den. Ask Wer? for the subject and Wen?/Was? for the direct object.",
      "Subject (Nominative) + verb + thing/person (Accusative).",
      [("Der Mann kauft den Apfel.", "The man buys the apple."), ("Ich lese das Buch.", "I am reading the book."), ("Sie trinkt einen Kaffee.", "She is drinking a coffee.")],
      [("der Apfel", "der", "die Äpfel", "apple"), ("das Buch", "das", "die Bücher", "book"), ("kaufen", "", "", "to buy")],
      "Ich sehe der Hund.", "Ich sehe den Hund.", "sehen takes a direct object; masculine der changes to den in the accusative.",
      "Ich kaufe ___ Apfel. (der)", "den", "The accusative changes the article for every gender.",
      can_do="Give simple information about people and familiar things, and say what you need or choose while shopping."),
    _uploaded_topics["cumulative-pronoun-man"],
    T("a1-direct-object-actions", "Shopping and Everyday Choices: Common Accusative Verbs",
      "Use common verbs to ask for and talk about familiar goods, food, and activities. Many everyday action verbs take an accusative direct object; learn a useful sentence with each verb.",
      "Common accusative verbs in the uploaded syllabus include haben, kaufen, sehen, hören, lesen, essen, trinken, brauchen, besuchen, and suchen. Match the article to the direct object: Ich brauche einen Computer; Sie besucht ihre Oma.",
      "Ich brauche + Accusative. / Was kaufst du? — Ich kaufe eine Tasche.",
      [("Ich brauche einen Computer.", "I need a computer."), ("Wir besuchen den Arzt.", "We are visiting the doctor."), ("Sie liest das Buch.", "She is reading the book.")],
      [("brauchen", "", "", "to need"), ("besuchen", "", "", "to visit"), ("die Tasche", "die", "die Taschen", "bag")],
      "Ich kaufe ein Computer.", "Ich kaufe einen Computer.", "Computer is masculine and is a direct object, so use accusative einen.",
      "Wir ___ die Musik. (hören)", "hören", "Every action verb takes dative.",
      can_do="Ask for goods and state simple needs or choices in shops, cafés, and familiar appointments."),
    _uploaded_topics["cumulative-genitive-extension"],
]
_a1_syllabus["description"] = "Beginner communication for social contact and familiar everyday needs. This course syllabus also introduces Genitive possession in short descriptions."
_uploaded_topics["cumulative-pronoun-man"]["can_do"] = "Make general statements about everyday life and understand the difference between man (people in general) and Mann (a male person)."

_a2_syllabus_topics = [
    _uploaded_topics[slug] for slug in (
        "cumulative-cases", "cumulative-demonstratives", "cumulative-verb-cases",
        "cumulative-fixed-prepositions", "cumulative-two-way-prepositions",
        "cumulative-time-prepositions", "cumulative-perfekt-extension",
    )
]
_a2_can_do = {
    "cumulative-cases": "Give and request information about familiar people, services, and objects using the case required by the sentence.",
    "cumulative-demonstratives": "Point out a specific item or ask which item someone means in a shop, home, or service interaction.",
    "cumulative-verb-cases": "Ask for help, give or receive information, and describe familiar actions with the right object forms.",
    "cumulative-fixed-prepositions": "Describe routes, appointments, and everyday relationships using the case required by a preposition.",
    "cumulative-two-way-prepositions": "Explain where something is and where it needs to go in a home, classroom, or travel situation.",
    "cumulative-time-prepositions": "Arrange a meeting and explain whether an event is starting, continuing, upcoming, or in the past.",
}
for _slug, _outcome in _a2_can_do.items():
    _uploaded_topics[_slug]["can_do"] = _outcome
_uploaded_topics["cumulative-perfekt-extension"].update({
    "title": "Reporting Recent Events: Perfekt and Partizip II",
    "focus": "Use the Perfekt to describe recent journeys, appointments, work, and personal experiences. These uploaded pages add participle patterns to the spoken-past lesson already in the A2 course.",
    "can_do": "Describe a recent event or journey and answer simple follow-up questions about when it happened and what happened.",
})
_a2_syllabus_topics.extend([
    T("a2-authorities-forms", "At an Office: Ask for Information and Complete a Form",
      "Handle a familiar visit to a public office: explain why you are there, ask which document is needed, understand a simple instruction, and enter personal details on a short form.",
      "Use polite Sie-questions (Können Sie mir sagen…? / Welche Unterlagen brauche ich?) and spell names and addresses. Use dative mir when asking someone to give or explain information.",
      "Reason for visit + polite question + personal details + confirmation.",
      [("Ich habe einen Termin. Welche Unterlagen brauche ich?", "I have an appointment. Which documents do I need?"), ("Können Sie mir bitte helfen?", "Could you please help me?"), ("Hier sind mein Pass und das Formular.", "Here are my passport and the form.")],
      [("der Termin", "der", "die Termine", "appointment"), ("das Formular", "das", "die Formulare", "form"), ("die Unterlage", "die", "die Unterlagen", "document")],
      "Kann Sie mir helfen?", "Können Sie mir helfen?", "In a polite request, conjugate können for Sie and use the dative pronoun mir.",
      "Welche Unterlagen ___ ich? (brauchen)", "brauche", "Use informal du with an unfamiliar office employee.",
      can_do="Ask for information at an office, understand a simple instruction, and complete a short personal-details form."),
    T("a2-job-search", "Work and Job Search: Explain Experience and Ask About a Position",
      "Talk about a current job or course, describe relevant experience, and ask basic questions about a position, schedule, or application. Use simple connected sentences and time expressions.",
      "Use present tense for current work and Perfekt for a past experience. Ask Können Sie mir etwas über die Arbeitszeiten sagen? Use seit + dative for a situation that continues from the past.",
      "Current situation + relevant experience + question about next steps.",
      [("Ich arbeite seit einem Jahr in einem Hotel.", "I have worked at a hotel for a year."), ("Ich habe in einem Geschäft gearbeitet.", "I worked in a shop."), ("Wann beginnt die Arbeit?", "When does the work start?")],
      [("die Stelle", "die", "die Stellen", "position; job"), ("die Arbeitszeit", "die", "die Arbeitszeiten", "working hours"), ("die Erfahrung", "die", "die Erfahrungen", "experience")],
      "Ich habe in einem Geschäft arbeiten.", "Ich habe in einem Geschäft gearbeitet.", "Use Perfekt haben + Partizip II for a completed past job; seit + dative describes work that continues now.",
      "Ich ___ in einem Geschäft gearbeitet. (haben)", "habe", "The Perfekt uses the infinitive after haben.",
      can_do="Give a short account of your work or learning background and ask practical questions about a job or course."),
    T("a2-school-childcare", "School and Childcare: Arrange a Meeting and Understand a Message",
      "Communicate with a school or childcare provider: ask about a meeting, understand a short note about time or materials, and explain a simple need concerning a child.",
      "Use a polite question with Sie, days and clock times for appointments, and dative forms after mit. Repeat or confirm the agreed date and time.",
      "Ask about the child + arrange a time + confirm what to bring.",
      [("Können wir am Dienstag um zehn Uhr sprechen?", "Can we talk on Tuesday at ten?"), ("Mia bringt ihre Sportsachen mit.", "Mia is bringing her sports things."), ("Der Termin ist bei der Lehrerin.", "The appointment is with the teacher.")],
      [("die Schule", "die", "die Schulen", "school"), ("die Lehrerin", "die", "die Lehrerinnen", "teacher"), ("der Termin", "der", "die Termine", "appointment")],
      "Ich habe einen Termin an den Dienstag.", "Ich habe einen Termin am Dienstag.", "Weekdays use an + dative; an dem contracts to am.",
      "Können wir ___ Dienstag sprechen? (on)", "am", "A weekday appointment uses an + accusative.",
      can_do="Arrange a school or childcare meeting and understand a short practical message about a child."),
    T("a2-banking-insurance", "Payments and Insurance: Understand a Bill and Ask About a Charge",
      "Handle a basic payment or insurance question: identify a date and amount on a bill, say what seems wrong, and ask a service worker to explain the next step.",
      "Use polite Sie-questions and simple connectors. Use the dative after mit and von; read amounts with euro and cents; repeat dates and reference numbers to confirm them.",
      "Name the bill or charge + describe the problem + ask for an explanation or correction.",
      [("Ich habe eine Frage zu dieser Rechnung.", "I have a question about this bill."), ("Können Sie mir die Gebühr erklären?", "Can you explain the fee to me?"), ("Die Zahlung ist am Montag angekommen.", "The payment arrived on Monday.")],
      [("die Rechnung", "die", "die Rechnungen", "bill"), ("die Gebühr", "die", "die Gebühren", "fee"), ("die Versicherung", "die", "die Versicherungen", "insurance")],
      "Können Sie mich die Gebühr erklären?", "Können Sie mir die Gebühr erklären?", "The person receiving an explanation is dative: mir.",
      "Ich habe eine Frage ___ dieser Rechnung. (about)", "zu", "The person receiving an explanation is accusative.",
      can_do="Ask for help understanding a simple bill, payment, or insurance notice and confirm the key details."),
])
A2_MODULES.append({
    "id": "a2-m06", "level": "A2", "order": 6,
    "title": "A2: Manage Places, Schedules, Services, and Recent Events",
    "description": "Build independent everyday communication across BAMF fields such as authorities, work, education and childcare, banking, mobility, housing, and social appointments. Case and tense choices support the task at hand.",
    "topics": _a2_syllabus_topics,
})


def _distribute_extra_module(modules, extra_module_id, destinations):
    """Fold supplementary topics into the published module set without changing their IDs."""
    extra = next(module for module in modules if module["id"] == extra_module_id)
    module_lookup = {module["id"]: module for module in modules if module["id"] != extra_module_id}
    for spec in extra["topics"]:
        destination_id = destinations[spec["slug"]]
        spec["_stable_lesson_id"] = f"{extra['level'].lower()}-{extra['id'][-2:]}-{spec['slug']}"
        spec["_stable_topic_id"] = f"{extra['id']}-{spec['slug']}"
        module_lookup[destination_id]["topics"].append(spec)
    modules.remove(extra)


# Keep the requested six A1 and five A2 modules while retaining the authored
# supplementary lessons and their stable IDs for existing learner progress.
_distribute_extra_module(A1_MODULES, "a1-m07", {
    "a1-nominative-accusative": "a1-m03",
    "cumulative-pronoun-man": "a1-m03",
    "a1-direct-object-actions": "a1-m04",
    "cumulative-genitive-extension": "a1-m02",
})
_distribute_extra_module(A2_MODULES, "a2-m06", {
    "cumulative-cases": "a2-m05",
    "cumulative-demonstratives": "a2-m05",
    "cumulative-verb-cases": "a2-m01",
    "cumulative-fixed-prepositions": "a2-m01",
    "cumulative-two-way-prepositions": "a2-m01",
    "cumulative-time-prepositions": "a2-m02",
    "cumulative-perfekt-extension": "a2-m05",
    "a2-authorities-forms": "a2-m03",
    "a2-job-search": "a2-m02",
    "a2-school-childcare": "a2-m02",
    "a2-banking-insurance": "a2-m03",
})

ALL_MODULES = [*A1_MODULES, *A2_MODULES, *B1_MODULES]
