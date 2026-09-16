"""SPRACHE — der Prompt ist deutsch, das Modell versteht englisch.

Der Befund, aus dem dieses Modul folgt
---------------------------------------
Die Oberfläche sammelt deutschen Text und legt ihn **wörtlich** in ``style.prompt``.
Die Bildmodelle sind ganz überwiegend an englischen Bild-Text-Paaren trainiert. Was
dazwischen passiert, ist nicht „etwas schlechter", sondern etwas anderes:

    Gepaart über 8 Startwerte, gemessen am Blauüberschuss des oberen Bildfünftels
    (HomeStation, ``9a33353``): deutsch **+40.1** (Streuung 32.0), englisch **+13.9**
    (Streuung 15.8). Deutsch war bei **8 von 8** gleichen Startwerten blauer.
    Einzeln nachgestellt: ``overcast sky`` +0.3 gegen ``bedeckter Himmel`` +17.8.

Ein deutscher Prompt, der „bedeckter Himmel" sagt, bekommt also einen blauen. Das
Modell macht nichts falsch — es versteht das Wort schlicht nicht und füllt mit dem,
was seine Trainingsbilder zu einem unverstandenen Prompt am häufigsten zeigen.

Der Entscheid des Owners (2026-08-21)
--------------------------------------
**Wir übersetzen — und deklarieren es.** Nicht heimlich, nicht ersatzweise: Im Ergebnis
stehen *beide* Fassungen nebeneinander, das Original und die Übersetzung. Wer später
ein Bild ansieht und sich fragt, warum dort steht, was dort steht, findet die Antwort
im Protokoll und muss sie nicht erraten.

Dazu, ebenfalls entschieden: **Die QA warnt**, wenn ein Prompt nicht englisch aussieht.
Eine Warnung, kein Verbot — aus demselben Grund wie beim
:func:`aiimaging.prompts.bauteilwaechter`: Dieses Modul sieht Text, keine Bedeutung.

Warum ein Glossar und kein Übersetzungsmodell
----------------------------------------------
Das Glossar ist die **Vorgabe**, nicht die einzige Möglichkeit. Es ist

* **bestimmt** — derselbe Text ergibt immer denselben Prompt. Ein Übersetzungsmodell,
  das heute anders übersetzt als gestern, macht jede Vergleichsreihe unlesbar, und
  Vergleichsreihen sind das Messwerkzeug dieses Projekts.
* **lizenzfrei** — keine Gewichte, keine Abhängigkeit, kein Regel-1-Problem. Die
  gängigen Übersetzungsmodelle sind ein eigenes Lizenzkapitel; das Glossar ist Text.
* **ohne Netz** — die HomeStation rendert auch ohne Verbindung.

Und es ist **ehrlich über seine Grenze**: Was es nicht kennt, meldet es als
``unbekannt``, statt es stillschweigend stehen zu lassen. Ein Übersetzer, der die Hälfte
übersetzt und nichts sagt, ist schlimmer als keiner — er erzeugt das Gefühl, übersetzt
worden zu sein.

Wer ein Modell will, hängt es an :func:`uebersetze` als ``uebersetzer`` ein. Die Naht
ist genau dafür da; sie ist der Grund, warum hier nicht die Glossarfunktion selbst
aufgerufen wird.

Was das Glossar kann, und wie viel — gemessen
----------------------------------------------
An dreizehn Prompts, wie sie aus der Oberfläche kommen könnten, waren mit dem blossen
Nachschlagewerk **eins von dreizehn** vollständig übersetzt. Das war deutlich weniger,
als die beiden Beispiele („langen", „Nordfassade") hatten ahnen lassen. Die Lücken
verteilten sich auf drei Klassen, und zwei davon sind mit je einer Regel erledigt —
:func:`grundform` für gebeugte Wörter, :func:`zerlege_kompositum` für zusammengesetzte.
Danach: **dreizehn von dreizehn.**

Was dabei NICHT behauptet wird: gutes Englisch. „die Fassaden der Stadt" wird zu „the
facade the city" — Mehrzahl und Genitiv gehen verloren. Für eine **Aufzählung durch
Kommata**, wie ein Bildprompt sie ist (siehe :func:`aiimaging.prompts.komponiere`),
trägt das; für einen Satz trüge es nicht. Wer ganze Sätze übersetzen will, hängt ein
Modell an die Naht.

Abhängigkeiten: keine. Reine stdlib, kein ``bpy``, aus Python heraus ohne Oberfläche
aufrufbar (Regel 4). Regel 3: keine Büro-, Kunden- oder Projektnamen — das Glossar
enthält Gattungsbegriffe der Architektur- und Fotosprache.
"""
from __future__ import annotations

import re

# --------------------------------------------------------------------------------------
# Das Glossar
# --------------------------------------------------------------------------------------

#: Deutsch → Englisch, für die Sprache, die in einem Prompt-Feld tatsächlich vorkommt.
#:
#: Was hier steht und was nicht, folgt einer Regel: Aufgenommen ist, was **das Bild
#: verändert** — Wetter, Licht, Tageszeit, Material, Stimmung, Bildcharakter, Umgebung,
#: und die Bauteilwörter. Nicht aufgenommen ist allgemeiner deutscher Wortschatz. Dieses
#: Glossar ist kein Wörterbuch und will keines werden: Ein halbes Wörterbuch übersetzt
#: Sätze halb, und halb übersetzte Sätze sind schlechter als unübersetzte, weil sie das
#: Modell zwischen zwei Sprachen stehen lassen.
#:
#: Die Bauteilwörter stehen mit drin, obwohl der :func:`aiimaging.prompts.bauteilwaechter`
#: von ihnen abrät. Der Grund ist nicht Zustimmung, sondern Sichtbarkeit: Ein deutsches
#: „Dach" im Prompt wirkt ohnehin (schwach und unkontrolliert). Übersetzt wird es zu
#: ``roof`` — und *dann* schlägt der Wächter an, der englisch am zuverlässigsten prüft.
#: Nicht zu übersetzen hiesse, den Fund zu verstecken.
#:
#: Mehrwortwendungen zuerst nachschlagen — siehe :func:`glossar_uebersetzung`.
GLOSSAR: dict[str, str] = {
    # --- Himmelsrichtungen und Lage ---------------------------------------------------
    # Sie stehen hier vor allem als **Kompositionsteile**: „Nordfassade", „Südseite".
    # Ohne sie bleibt jede Himmelsrichtung im Prompt deutsch stehen — und die
    # Himmelsrichtung ist bei einem Gebäude selten Beiwerk.
    "nord": "north",
    "norden": "north",
    "nördlich": "northern",
    "süd": "south",
    "sued": "south",
    "süden": "south",
    "südlich": "southern",
    "ost": "east",
    "osten": "east",
    "östlich": "eastern",
    "west": "west",
    "westen": "west",
    "westlich": "western",
    "seite": "side",
    "ecke": "corner",
    "mitte": "middle",
    "grund": "ground",
    "davor": "in front",
    "dahinter": "behind",
    "daneben": "beside",
    "gegenüber": "opposite",

    # --- Jahreszeiten -------------------------------------------------------------------
    "sommer": "summer",
    "winter": "winter",
    "frühling": "spring",
    "herbst": "autumn",
    "jahreszeit": "season",

    # --- Himmel und Wetter ------------------------------------------------------------
    "bedeckter himmel": "overcast sky",
    "bedeckt": "overcast",
    "bewölkt": "cloudy",
    "wolkenlos": "cloudless",
    "klarer himmel": "clear sky",
    "blauer himmel": "blue sky",
    "grauer himmel": "grey sky",
    "himmel": "sky",
    "wolken": "clouds",
    "wolke": "cloud",
    "hohe wolken": "high thin clouds",
    "tiefe wolken": "low clouds",
    "regen": "rain",
    "nach dem regen": "after rain",
    "regnerisch": "rainy",
    "nass": "wet",
    "trocken": "dry",
    "schnee": "snow",
    "nebel": "fog",
    "neblig": "foggy",
    "dunst": "haze",
    "diesig": "hazy",
    "wind": "wind",
    "windig": "windy",
    "sonne": "sun",
    "sonnig": "sunny",
    "sonnenschein": "sunshine",
    "wetter": "weather",

    # --- Licht und Tageszeit ----------------------------------------------------------
    "licht": "light",
    "beleuchtung": "lighting",
    "tageslicht": "daylight",
    "weiches licht": "soft light",
    "weich": "soft",
    "hart": "hard",
    "hartes licht": "hard light",
    "diffuses licht": "diffuse light",
    "gegenlicht": "backlight",
    "seitenlicht": "side light",
    "kunstlicht": "artificial light",
    "schatten": "shadows",
    "lange schatten": "long shadows",
    "kein schatten": "no shadows",
    "morgen": "morning",
    "vormittag": "morning",
    "mittag": "midday",
    "nachmittag": "afternoon",
    "abend": "evening",
    "abendlicht": "evening light",
    "morgenlicht": "morning light",
    # Aus einem echten Lauf der Oberflaeche (HomeStation, auf-vis-20260826-16,
    # 26.08.2026): Sie liess 3 von 7 Begriffen deutsch stehen, und zwei davon stehen
    # hier. Das Glossar hat die Bausteine ("nachmittag", "licht") und nicht das Wort —
    # eine zusammengesetzte Form faellt zwischen sie.
    "nachmittagslicht": "afternoon light",
    "vormittagslicht": "morning light",
    "mittagslicht": "midday light",
    "dämmerung": "dusk",
    "blaue stunde": "blue hour",
    "goldene stunde": "golden hour",
    "sonnenaufgang": "sunrise",
    "sonnenuntergang": "sunset",
    "nacht": "night",
    "nachts": "at night",
    "tag": "day",
    "tagsüber": "during the day",
    "hell": "bright",
    "dunkel": "dark",
    "warm": "warm",
    "kühl": "cool",
    "kalt": "cold",

    # --- Material und Oberfläche ------------------------------------------------------
    "material": "material",
    "materialien": "materials",
    "oberfläche": "surface",
    "struktur": "texture",
    "strukturiert": "textured",
    "oberflächen": "surfaces",
    "beton": "concrete",
    "sichtbeton": "exposed concrete",
    "holz": "wood",
    "holzverkleidung": "timber cladding",
    "ziegel": "brick",
    "backstein": "brick",
    "klinker": "facing brick",
    "stein": "stone",
    "naturstein": "natural stone",
    "putz": "render",
    "verputzt": "rendered",
    "glas": "glass",
    "metall": "metal",
    "stahl": "steel",
    "aluminium": "aluminium",
    "kupfer": "copper",
    "zink": "zinc",
    "blech": "sheet metal",
    "matt": "matte",
    "glänzend": "glossy",
    "rau": "rough",
    "glatt": "smooth",
    "fein": "fine",
    "grob": "coarse",
    "verwittert": "weathered",
    "bewittert": "weathered",
    "patina": "patina",
    "neu": "new",
    "alt": "old",
    "gealtert": "aged",
    "farbe": "colour",
    "farben": "colours",
    "farbig": "coloured",
    "weiss": "white",
    "weiß": "white",
    "schwarz": "black",
    "grau": "grey",
    "rot": "red",
    "blau": "blue",
    "grün": "green",
    "gelb": "yellow",
    "braun": "brown",
    "beige": "beige",
    "hell gestrichen": "painted in a pale tone",
    "gesättigt": "saturated",
    "entsättigt": "desaturated",

    # --- Umgebung und Beiwerk ---------------------------------------------------------
    "umgebung": "surroundings",
    "landschaft": "landscape",
    "gelände": "terrain",
    "boden": "ground",
    "wiese": "meadow",
    "gras": "grass",
    "rasen": "lawn",
    "bäume": "trees",
    "baum": "tree",
    "baumbestand": "mature trees",
    "sträucher": "shrubs",
    "busch": "bush",
    "hecke": "hedge",
    "bewuchs": "vegetation",
    "vegetation": "vegetation",
    "bepflanzung": "planting",
    "garten": "garden",
    "hof": "courtyard",
    "platz": "square",
    "strasse": "street",
    "straße": "street",
    "weg": "path",
    "stadt": "city",
    "dorf": "village",
    "land": "countryside",
    "berge": "mountains",
    "wasser": "water",
    "see": "lake",
    "fluss": "river",
    "menschen": "people",
    "leute": "people",
    "person": "person",
    "personen": "people",
    "keine menschen": "no people",
    "figuren": "figures",
    "fahrrad": "bicycle",
    "auto": "car",
    "autos": "cars",

    # --- Bildcharakter und Aufnahme ---------------------------------------------------
    "foto": "photograph",
    "fotografie": "photography",
    "aufnahme": "photograph",
    "detailaufnahme": "close-up photograph",
    "architekturfoto": "architectural photograph",
    "architekturfotografie": "architectural photography",
    "modellfoto": "photograph of an architectural model",
    "modell": "model",
    "visualisierung": "visualisation",
    "rendering": "rendering",
    "zeichnung": "drawing",
    "skizze": "sketch",
    "skizzenhaft": "sketchy",
    "aquarell": "watercolour",
    "bleistift": "pencil",
    "schwarzweiss": "black and white",
    "schwarzweiß": "black and white",
    "objektiv": "lens",
    "weitwinkel": "wide angle",
    "teleobjektiv": "telephoto lens",
    "brennweite": "focal length",
    "schärfe": "sharpness",
    "scharf": "sharp",
    "unscharf": "out of focus",
    "tiefenschärfe": "depth of field",
    "körnung": "grain",
    "korn": "grain",
    "film": "film",
    "kontrast": "contrast",
    "kontrastreich": "high contrast",
    "kontrastarm": "low contrast",
    "belichtung": "exposure",
    "überbelichtet": "overexposed",
    "unterbelichtet": "underexposed",
    "vordergrund": "foreground",
    "hintergrund": "background",
    "mittelgrund": "middle ground",
    "augenhöhe": "eye level",
    "froschperspektive": "low viewpoint",
    "vogelperspektive": "aerial view",
    "ansicht": "view",
    "blick": "view",
    "blick von": "view from",
    "detail": "detail",
    "übersicht": "overview",
    "innenraum": "interior",
    "innen": "interior",
    "aussen": "exterior",
    "außen": "exterior",
    "innenaufnahme": "interior photograph",
    "aussenaufnahme": "exterior photograph",
    "außenaufnahme": "exterior photograph",
    # Ebenfalls aus auf-vis-20260826-16: Die Oberflaeche schickt "Aussenperspektive",
    # und "aussen" + "perspektive" stehen beide im Glossar — das zusammengesetzte Wort
    # aber nicht.
    "aussenperspektive": "exterior view",
    "außenperspektive": "exterior view",
    "innenperspektive": "interior view",
    "perspektive": "view",

    # --- Stimmung ---------------------------------------------------------------------
    "stimmung": "mood",
    "atmosphäre": "atmosphere",
    "ruhig": "quiet",
    "still": "still",
    "belebt": "busy",
    "leer": "empty",
    "einladend": "welcoming",
    "nüchtern": "sober",
    "zurückhaltend": "restrained",
    "dramatisch": "dramatic",
    "freundlich": "friendly",
    "streng": "austere",
    "gemütlich": "cosy",
    "modern": "modern",
    "zeitgenössisch": "contemporary",
    "traditionell": "traditional",
    "ländlich": "rural",
    "städtisch": "urban",
    "dokumentarisch": "documentary",
    "realistisch": "realistic",
    "fotorealistisch": "photorealistic",
    # Der dritte der drei aus auf-vis-20260826-16. "foto" stand da, die Adjektivform
    # nicht — und ein Prompt sagt "fotografisch", nicht "foto".
    "fotografisch": "photographic",
    "photografisch": "photographic",
    "photographisch": "photographic",

    # --- Gebäude und Bauteile ---------------------------------------------------------
    # Siehe die Begründung oben: übersetzt, damit der Bauteilwächter sie sieht.
    "gebäude": "building",
    "haus": "house",
    "wohnhaus": "residential building",
    "bauwerk": "building",
    "baukörper": "volume",
    "neubau": "new building",
    "altbau": "old building",
    "anbau": "extension",
    "dach": "roof",
    "flachdach": "flat roof",
    "satteldach": "gable roof",
    "dächer": "roofs",
    "fenster": "window",
    "fensterband": "ribbon window",
    "tür": "door",
    "türen": "doors",
    "eingang": "entrance",
    "balkon": "balcony",
    "balkone": "balconies",
    "terrasse": "terrace",
    "loggia": "loggia",
    "fassade": "facade",
    "wand": "wall",
    "wände": "walls",
    "mauer": "wall",
    "stütze": "column",
    "stützen": "columns",
    "säule": "column",
    "säulen": "columns",
    "treppe": "stair",
    "treppen": "stairs",
    "geländer": "railing",
    "brüstung": "parapet",
    "attika": "parapet",
    "kamin": "chimney",
    "gaube": "dormer",
    "vordach": "canopy",
    "gesims": "cornice",
    "giebel": "gable",
    "traufe": "eaves",
    "oberlicht": "skylight",
    "geschoss": "storey",
    "geschosse": "storeys",
    "erdgeschoss": "ground floor",
    "obergeschoss": "upper floor",
    "dachgeschoss": "attic floor",
    "keller": "basement",
    "sockel": "plinth",
    "laibung": "reveal",
    "decke": "ceiling",
    "wohnzimmer": "living room",
    "küche": "kitchen",
    "raum": "room",
    "räume": "rooms",

    # --- Zahlwörter -------------------------------------------------------------------
    # **Der Anlass ist die zweite Hälfte eines gemeldeten Prompts** (HomeStation,
    # 12.09.2026): Im Feld stand «vier, betonwaende». Die Ersatzschreibung war am
    # 12.09. behoben, `betonwaende` wurde seither zu `concrete walls` — und `vier`
    # blieb deutsch stehen. Ein deutsches Wort im englischen Prompt ist genau der
    # halbdeutsche Zustand, gegen den dieses Modul gebaut ist: Am 21.08.2026 über
    # 8 gepaarte Startwerte gemessen, fiel der deutsche Prompt messbar schlechter aus
    # (Blauüberschuss +40.1 gegen +13.9, 8 von 8 Mal schlechter).
    #
    # Eine Zahl im Prompt ist auch kein Beiwerk: «vier Geschosse» ist eine Aussage über
    # das Gebäude, und das Modell soll sie verstehen.
    #
    # **Was hier NICHT steht, und warum — jedes Wort einzeln geprüft** (16.09.2026,
    # differenziell gemessen: Glossareintrag versuchsweise gesetzt, dann geprüft, was
    # sich an englischem Text ändert; Korpus war `_ENGLISCHER_WORTSCHATZ` plus kurze
    # englische Prompts ohne Signalwörter):
    #
    # * **`elf` fehlt.** Es ist im Englischen ein Fabelwesen und damit ein echter
    #   falscher Freund — der einzige der zwölf. Gemessen: 3 englische Eingaben kippten,
    #   `elf statue` wurde zu `eleven statue` und galt zugleich als deutsch. Alle
    #   übrigen Zahlwörter änderten an englischem Text **genau nichts** ausser sich
    #   selbst. Eine `11` schreibt ohnehin, wer elf meint.
    # * **`acht` fehlt.** Nicht wegen des Englischen — dort ist es sauber —, sondern
    #   wegen der eigenen Beugungsregel: `achte` und `achten` streifen ihre Endung ab
    #   und landen auf `acht`. Damit übersetzte der Eintrag durch die Hintertür die
    #   **Ordnungszahl** (`achte` = eighth, nicht eight) und den Verbstamm von «achten».
    #   Es ist das einzige Zahlwort, dem das passiert; bei `zweite`, `vierte`, `zehnte`
    #   bleibt nach dem Abstreifen `zweit`, `viert`, `zehnt` übrig, und das ist kein
    #   Eintrag. Ein stehengebliebenes `acht` wird als `unbekannt` gemeldet und kostet
    #   einen Blick — ein stilles `achte` → `eight` kostet ein Bild.
    # * **`ein` und `eine` bleiben Artikel.** Sie stehen weiter unten schon, und zwar
    #   als `a`. Das ist im Prompt fast immer richtig: «ein Wohnhaus» ist *a residential
    #   building*, nicht *one residential building*. Wer wirklich die Zahl meint,
    #   schreibt `eins` — und das steht hier.
    # * **Ordnungszahlen fehlen ganz** (`erste`, `zweite`, …). Bewusste Grenze: Sie sind
    #   gebeugt, und im Englischen greift die Wortstellung anders («the second floor»
    #   gegen «zweites Geschoss»). Für eine Aufzählung durch Kommata, wie ein Bildprompt
    #   sie ist, trägt eine Grundzahl; eine gebeugte Ordnungszahl trüge nicht. Sie
    #   bleiben stehen und werden gemeldet.
    #
    # Die Ersatzschreibung (`fuenf`, `zwoelf`) braucht **keine eigenen Einträge**:
    # :func:`_umlaut_kandidaten` löst sie auf, und :func:`grundform` schlägt die
    # Umlautform hier nach. Nachgemessen am 16.09.2026 — `fuenf` und `fünf` ergeben
    # beide `five`. Ein zweiter Eintrag wäre eine zweite Stelle, die mitgepflegt
    # werden müsste, ohne etwas zu können.
    "eins": "one",
    "zwei": "two",
    "drei": "three",
    "vier": "four",
    "fünf": "five",
    "sechs": "six",
    "sieben": "seven",
    "neun": "nine",
    "zehn": "ten",
    "zwölf": "twelve",

    # --- Häufige Funktionswörter, die sonst als „unbekannt" stehenblieben -------------
    # Sie tragen nichts zum Bild bei, aber ein stehengebliebenes „mit" macht aus einem
    # übersetzten Prompt wieder einen halbdeutschen.
    "und": "and",
    "oder": "or",
    "mit": "with",
    "ohne": "without",
    "von": "from",
    "aus": "of",
    "für": "for",
    "über": "above",
    "unter": "below",
    "vor": "in front of",
    "hinter": "behind",
    "neben": "next to",
    "zwischen": "between",
    "durch": "through",
    "gegen": "against",
    "auf": "on",
    "bei": "at",
    "der": "the",
    "die": "the",
    "das": "the",
    "den": "the",
    "dem": "the",
    "des": "of the",
    "ein": "a",
    "eine": "a",
    "einem": "a",
    "einen": "a",
    "einer": "a",
    "eines": "of a",
    "im": "in the",
    "in": "in",
    "am": "at the",
    "kein": "no",
    "keine": "no",
    "keinen": "no",
    "nicht": "not",
    "sehr": "very",
    "etwas": "slightly",
    "viel": "much",
    "viele": "many",
    "wenig": "little",
    "wenige": "few",
    "leicht": "slight",
    "stark": "strong",
    "gross": "large",
    "groß": "large",
    "klein": "small",
    "hoch": "tall",
    # STÄMME, keine Wörter. Sie stehen hier, weil die Endungsregel etwas zum
    # Nachschlagen braucht: Deutsch beugt `hoch` zu `hohe/hohen/hoher/hohes/hohem` und
    # `dunkel` zu `dunkle/dunklen`. Abgestreift bleibt `hoh` bzw. `dunkl` übrig — kein
    # Wort, aber der Schlüssel, unter dem alle fünf Formen zu finden sind. Ein Eintrag
    # statt fünf, und die Unregelmässigkeit steht an genau einer Stelle.
    "hoh": "tall",
    "dunkl": "dark",
    "niedrig": "low",
    "weit": "wide",
    "eng": "narrow",
    "lang": "long",
    "kurz": "short",
    "oben": "above",
    "unten": "below",
    "links": "on the left",
    "rechts": "on the right",
    "vorne": "at the front",
    "hinten": "at the back",
}

#: Glossareinträge, die **auch gewöhnliche englische Wörter** sind.
#:
#: Sie werden übersetzt, sobald feststeht, dass ein Text deutsch ist — aber sie dürfen
#: nie das sein, WORAUS das festgestellt wird. Sonst liest sich ein englisches „I can see
#: the wind in the film" als deutsch und wird zu Unsinn übersetzt.
#:
#: Die Liste ist von Hand geprüft und beim Erweitern des Glossars mitzuführen. Der Test
#: :func:`tests.test_sprache.test_kollisionen_vollstaendig` hält sie fest, soweit
#: maschinell prüfbar.
ENGLISCH_AUCH = frozenset({
    "in", "am", "die", "hell", "rot", "tag", "land", "see", "gross", "matt", "warm",
    "wind", "film", "material", "detail", "modern", "person", "patina", "beige",
    "loggia", "vegetation", "aluminium", "still", "alt", "stark", "wand", "auto",
    "rau", "fein",
})

#: Name des Vorgabeverfahrens. Er landet im Protokoll — ein Ergebnis, das nicht sagt,
#: WOMIT übersetzt wurde, ist in einem Jahr nicht mehr einzuordnen.
VERFAHREN_GLOSSAR = "glossar"

#: Was zurückkommt, wenn gar nicht übersetzt wurde.
VERFAHREN_KEINE = "keine"


# --------------------------------------------------------------------------------------
# Sieht der Text englisch aus?
# --------------------------------------------------------------------------------------

#: Deutsche Signalwörter für die Spracherkennung.
#:
#: **Kuratiert gegen Zusammenstösse.** Nicht aufgenommen sind deutsche Wörter, die auch
#: englische sind: ``die`` (engl. sterben), ``in``, ``an``, ``am``, ``war`` (engl. Krieg),
#: ``so``, ``man``, ``bald`` (engl. kahl), ``gross`` (engl. brutto), ``hell`` (engl.
#: Hölle), ``hat``, ``rot`` (engl. Fäulnis), ``fast``, ``bar``, ``rain`` … Ein Signalwort,
#: das in beiden Sprachen vorkommt, ist kein Signal, sondern ein Fehlalarm mit Anlauf.
DEUTSCHE_SIGNALWOERTER = frozenset({
    "der", "das", "den", "dem", "des", "eine", "einem", "einen", "einer", "eines",
    "und", "oder", "aber", "mit", "ohne", "von", "vom", "zum", "zur", "beim", "im",
    "ins", "für", "über", "unter", "vor", "hinter", "neben", "zwischen", "durch",
    "gegen", "nach", "bei", "aus", "auf", "ist", "sind", "waren", "wird", "werden",
    "wurde", "nicht", "kein", "keine", "keinen", "auch", "sehr", "etwas", "nichts",
    "alles", "viel", "viele", "wenig", "wenige", "oben", "unten", "links", "rechts",
    "vorne", "hinten", "innen", "aussen", "außen", "dunkel", "klein", "hoch",
    "niedrig", "weit", "eng", "lang", "kurz", "wie", "wo", "wer", "warum", "dann",
    "dort", "hier", "immer", "nie", "schon", "noch", "einem", "welche", "welcher",
})

#: Englische Signalwörter.
#:
#: Dieselbe Regel andersherum: ``was`` (dt. Fragewort), ``will`` (dt. wollen), ``hat``,
#: ``an``, ``in``, ``am``, ``so``, ``bald``, ``gift``, ``rat``, ``fast``, ``bar``, ``arm``
#: und ``hell`` fehlen mit Absicht.
ENGLISCHE_SIGNALWOERTER = frozenset({
    "the", "and", "with", "without", "of", "from", "for", "into", "onto", "over",
    "under", "behind", "between", "through", "against", "towards", "toward", "is",
    "are", "were", "not", "no", "some", "all", "very", "more", "few", "above",
    "below", "left", "right", "front", "back", "inside", "outside", "bright", "dark",
    "large", "small", "near", "far", "seen", "looking", "photograph", "photo",
    "view", "building", "house", "light", "sky", "shadow", "shadows", "clouds",
    "grey", "gray", "white", "black", "quiet", "soft", "hard", "warm", "cool",
    "there", "here", "which", "that", "this", "these", "those", "its", "their",
})

#: Umlaute und Eszett — das stärkste Einzelmerkmal, das ein kurzer Text tragen kann.
_UMLAUTE = re.compile(r"[äöüÄÖÜß]")

#: Wortgrenzen für die Zerlegung. Bindestrichwörter bleiben zusammen („Nord-Fassade"),
#: weil ein zerlegtes Bindestrichwort zwei falsche Treffer statt eines richtigen gibt.
_WORT = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)

#: Name des Verfahrens der Spracherkennung. Steht im Ergebnis, damit niemand sie für
#: mehr hält, als sie ist.
VERFAHREN_ERKENNUNG = "signalwoerter+umlaute"


def _woerter(text: str) -> list[str]:
    """Den Text in kleingeschriebene Wörter zerlegen — Zahlen und Zeichen fallen weg."""
    return [w.lower() for w in _WORT.findall(text or "")]


def sieht_englisch_aus(text: str) -> dict:
    """Eine **Heuristik**, und sie sagt es selbst.

    Returns:
        ``{englisch, sicher, deutsche_funde, englische_funde, umlaute, verfahren,
        begruendung}``.

        ``englisch`` ist bewusst dreiwertig:

        * ``True`` — englische Signale, keine deutschen.
        * ``False`` — deutsche Signale (Umlaute oder Signalwörter). Auch dann, wenn
          zugleich englische auftreten: Ein halbdeutscher Prompt ist genau der Fall,
          vor dem gewarnt werden soll.
        * ``None`` — **nicht entscheidbar**. Das ist kein Ausweichen, sondern der
          häufigste ehrliche Befund bei kurzen Eingaben: ``24mm f8``, ``beton``,
          ``concrete`` tragen kein einziges Signalwort. Wer hier ``True`` zurückgäbe,
          liesse die Warnung schweigen; wer ``False`` zurückgäbe, warnte vor jedem
          Fachwort. ``None`` warnt nicht und behauptet nicht.

        ``sicher`` unterscheidet einen Fund von einem starken Fund: ein einzelnes
        Signalwort ist ein Hauch, ein Umlaut oder zwei Signalwörter sind ein Befund.

    Die Grenze, die dazugehört: Das ist Wortzählung, keine Sprachbestimmung. Ein
    englischer Satz über einen Ort namens „Grünau" schlägt als deutsch an, und ein
    deutscher Prompt aus lauter Fremdwörtern („Loggia, Patina, Beton") schlägt gar nicht
    an. Ein Fehlalarm kostet einen Blick — deshalb ist die Richtung so gewählt.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "englisch": None, "sicher": False, "deutsche_funde": (),
            "englische_funde": (), "umlaute": False, "verfahren": VERFAHREN_ERKENNUNG,
            "begruendung": "Kein Text.",
        }

    umlaute = bool(_UMLAUTE.search(text))
    woerter = _woerter(text)
    deutsch = tuple(dict.fromkeys(w for w in woerter if w in DEUTSCHE_SIGNALWOERTER))
    englisch = tuple(dict.fromkeys(w for w in woerter if w in ENGLISCHE_SIGNALWOERTER))

    deutsches_gewicht = len(deutsch) + (2 if umlaute else 0)

    if deutsches_gewicht:
        urteil, sicher = False, deutsches_gewicht >= 2
        teile = []
        if umlaute:
            teile.append("Umlaute oder ß")
        if deutsch:
            teile.append("deutsche Signalwörter: " + ", ".join(deutsch))
        begruendung = "Deutsch erkannt (" + "; ".join(teile) + ")."
        if englisch:
            begruendung += (
                " Zugleich englische Signalwörter (" + ", ".join(englisch) +
                ") — der Text ist gemischt, und gemischt zählt als nicht englisch."
            )
    elif englisch:
        urteil, sicher = True, len(englisch) >= 2
        begruendung = "Englisch erkannt (" + ", ".join(englisch) + ")."
    else:
        urteil, sicher = None, False
        begruendung = (
            "Nicht entscheidbar: kein einziges Signalwort und kein Umlaut. Das ist bei "
            "kurzen Eingaben der Normalfall und keine Beanstandung."
        )

    return {
        "englisch": urteil,
        "sicher": sicher,
        "deutsche_funde": deutsch,
        "englische_funde": englisch,
        "umlaute": umlaute,
        "verfahren": VERFAHREN_ERKENNUNG,
        "begruendung": begruendung,
    }


# --------------------------------------------------------------------------------------
# Übersetzen
# --------------------------------------------------------------------------------------

#: Kleine geschlossene Klasse, die in keiner Glossarübersetzung vorkommt, aber in jedem
#: englischen Prompt: Artikel, Hilfsverben, Zahlwörter. Sie ergänzt den Wortschatz, aus
#: dem :func:`_nicht_englisch` schöpft.
_ENGLISCHE_ERGAENZUNG = frozenset({
    "a", "an", "the", "to", "by", "as", "it", "its", "be", "been", "being", "am",
    "was", "has", "have", "had", "do", "does", "did", "can", "could", "will", "would",
    "shall", "should", "may", "might", "must", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten", "up", "down", "out", "off", "across",
    "along", "around", "before", "after", "during", "while", "than", "then", "so",
    "such", "each", "every", "any", "both", "either", "neither", "other", "another",
    "same", "own", "just", "only", "also", "even", "still", "yet", "about", "like",
    "seen", "shot", "taken", "made", "set", "kept", "held", "given",
})


def _englischer_wortschatz() -> frozenset:
    """Woraus dieses Modul „das ist englisch" schöpft — und es ist wenig.

    Die Quellen: alle Wörter, die im Glossar auf der **englischen** Seite stehen, die
    englischen Signalwörter, und die geschlossene Klasse oben. Zusammen ein paar hundert
    Wörter, kein Wörterbuch.

    Das ist mit Absicht so klein. Der Wortschatz dient nur der Gegenprobe „ist nach der
    Übersetzung noch etwas Deutsches stehengeblieben?", und dort ist Übermelden die
    richtige Richtung: Ein zu Unrecht gemeldetes englisches Wort kostet einen Blick, ein
    übersehenes deutsches kostet ein Bild.
    """
    woerter = set(_ENGLISCHE_ERGAENZUNG) | set(ENGLISCHE_SIGNALWOERTER)
    for englisch in GLOSSAR.values():
        woerter.update(_WORT.findall(englisch.lower()))
    return frozenset(woerter)


_ENGLISCHER_WORTSCHATZ = _englischer_wortschatz()


def _nicht_englisch(text: str) -> tuple[str, ...]:
    """Wörter, die unser (kleiner) englischer Wortschatz nicht kennt.

    Wird **nur** auf Text angewendet, der schon als deutsch erkannt wurde. Dort heisst
    ein unbekanntes Wort mit hoher Wahrscheinlichkeit: nicht übersetzt. Auf beliebigen
    englischen Text losgelassen wäre dieselbe Funktion wertlos — sie kennt ja fast nichts.

    Warum es diese Funktion überhaupt braucht: Die erste Fassung meldete
    ``unbekannt = ()`` für „evening light with langen shadows". Sie suchte nur nach
    Umlauten und Signalwörtern, und ``langen`` hat weder. Ein halb übersetzter Prompt,
    der sich selbst als vollständig meldet, ist schlimmer als gar keine Übersetzung.
    """
    return tuple(dict.fromkeys(
        w for w in _woerter(text) if w not in _ENGLISCHER_WORTSCHATZ
    ))


# --------------------------------------------------------------------------------------
# Zwei Regeln gegen die Grammatik, die ein Glossar nicht hat
# --------------------------------------------------------------------------------------
#
# **Der Anlass ist eine Messung, und sie fiel schlecht aus.** An zwölf Prompts, wie sie
# aus der Oberfläche kommen könnten, war vor diesen beiden Regeln **einer von zwölf**
# vollständig übersetzt. Meine beiden Beispiele („langen", „Nordfassade") hatten das
# Ausmass nicht ahnen lassen; die Lücken verteilten sich auf drei Klassen, und zwei davon
# sind mit einer Regel je erledigt:
#
# * **Gebeugte Adjektive und Substantive** — 12 der 23 Lücken. ``langen``, ``feiner``,
#   ``ruhiges``, ``weichem``, ``bewölkter``, ``bäumen``. Der Stamm steht jeweils im
#   Glossar; nur die Endung fehlt dort.
# * **Komposita** — 5 der 23. ``Nordfassade``, ``Holzfassade``, ``Südseite``. Beide Teile
#   stehen im Glossar.
# * **Schlicht fehlende Wörter** — 5. Dagegen hilft keine Regel, nur ein Eintrag.

#: Deutsche Endungen, die an einen Stamm treten, in absteigender Länge.
#:
#: Die Liste ist **kurz und geschlossen**: Es sind die Endungen der Adjektivdeklination,
#: nicht ein Stemmer. Ein echter Stemmer riete; hier wird nur abgestreift und dann **im
#: Glossar nachgeschlagen** — schlägt das fehl, bleibt das Wort stehen und wird gemeldet.
#: Das ist der ganze Sicherheitsgurt.
#:
#: **``s`` stand zuerst mit dabei und ist wieder heraus.** Ein Test fing ``Dachs`` →
#: ``dach`` → ``roof``: Ein Dachs ist ein Tier. In einem Modul, das gegen erfundene
#: Dächer gebaut ist, ist das die denkbar falscheste Sorte Fehler. Was ``s`` einbrächte,
#: sind Fremdwortplurale wie ``Autos``; die bleiben jetzt stehen und werden gemeldet.
#: Ein gemeldetes Wort kostet einen Blick, ein falsch übersetztes ein Bild.
#:
#: **``n`` flog im selben Zug mit heraus und musste zurück.** Es sah nach derselben
#: Sorte Risiko aus und ist keine: Der reguläre Plural der Feminina bildet sich mit ``n``
#: — ``Fassade`` → ``Fassaden``, ``Terrasse`` → ``Terrassen``. Ohne diese eine Endung
#: bleibt jede Mehrzahl stehen. Die Gegenprobe über die englischen Wörter unserer
#: Übersetzungen fand genau einen gefährlichen Fall (``seen`` → ``see`` → ``lake``), und
#: den fängt der Wortschatz-Wächter in :func:`glossar_uebersetzung`.
ENDUNGEN = ("en", "em", "es", "er", "e", "n")

#: Umlaute, die beim Beugen entstehen: ``Baum`` → ``Bäume``, ``Haus`` → ``Häuser``.
_ENTUMLAUTUNG = {"ä": "a", "ö": "o", "ü": "u"}

#: Kleinste Länge eines Kompositumsteils.
#:
#: **Drei**, und zwar gemessen. Vier war der erste Wert und schien vorsichtiger — er
#: verliert aber genau die Himmelsrichtungen: ``süd``, ``ost``, ``west`` haben drei
#: Zeichen, und ``Südseite`` blieb damit unübersetzt. An dreissig zusammengesetzten
#: Wörtern nachgesehen, was drei zusätzlich zerlegt: **neunzehn Treffer, kein einziger
#: falsch**. Der Schutz liegt ohnehin nicht in der Länge, sondern in der Bedingung, dass
#: **beide** Teile im Glossar stehen.
MIN_TEILLAENGE = 3

#: Die Grundzahlen des Glossars — **gesperrt für die Kompositumsregel**.
#:
#: **Der Anlass ist eine Nachmessung** (16.09.2026, am Tag der Aufnahme): Mit den
#: Zahlwörtern im Glossar zerlegte :func:`zerlege_kompositum` plötzlich Wörter, die keine
#: Summe ihrer Teile sind. Über den Wortschatz dieses Repos gemessen (69'273 verschiedene
#: Wörter), **sechs** davon, und alle sechs still — ``unbekannt`` war leer,
#: ``vollstaendig`` war ``True``:
#:
#:     ``dreizehn``  → ``three ten``     (thirteen)
#:     ``vierzehn``  → ``four ten``      (fourteen)
#:     ``fünfzehn``  → ``five ten``      (fifteen)
#:     ``neunzehn``  → ``nine ten``      (nineteen)
#:     ``dreiecke``  → ``three corner``  (triangles)
#:     ``obendrein`` → ``above three``   (moreover)
#:
#: Deutsch zählt und bildet Formen **zusammengesetzt**, wo Englisch ein eigenes Wort hat.
#: Das ist die Klasse, die der Kompositumsregel entgeht: Sie prüft, ob beide Teile im
#: Glossar stehen, und bei einer Zahl stehen sie immer. Ohne Sperre trüge der Prompt eine
#: Zahl, die es nicht gibt — und *das* ist schlimmer als ein stehengebliebenes Wort:
#: ``dreizehn`` bleibt jetzt stehen und wird gemeldet.
#:
#: Gesperrt sind **beide** Stellen, vorn wie hinten — ``obendrein`` ist der Fall hinten.
#: Verloren geht dabei nichts: Über denselben Wortschatz gemessen, zerlegt die Regel mit
#: dieser Sperre **kein einziges** Wort weniger, das richtig zerlegt war.
ZAHLWOERTER = frozenset({
    "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "neun", "zehn", "zwölf",
})

#: Verfahrensnamen für das Protokoll. Was durch eine REGEL übersetzt wurde und nicht
#: durch einen Eintrag, soll unterscheidbar bleiben — eine Regel irrt anders als ein
#: Nachschlagewerk.
ART_EINTRAG = "eintrag"
ART_BEUGUNG = "beugung"
ART_KOMPOSITUM = "kompositum"


def _entumlautet(wort: str) -> str:
    return "".join(_ENTUMLAUTUNG.get(z, z) for z in wort)


#: Die Ersatzschreibung der Umlaute, wie sie jeder tippt, der keine deutsche Tastatur hat.
UMLAUTSCHREIBUNG = (("ae", "ä"), ("oe", "ö"), ("ue", "ü"))


def _umlaut_kandidaten(wort: str) -> tuple[str, ...]:
    """Mögliche Umlautformen eines in Ersatzschreibung getippten Wortes.

    **Der Anlass ist ein Ausfall an der Naht** (HomeStation, 12.09.2026): Im Prompt
    standen *«vier, betonwaende»*, und beide Wörter blieben deutsch stehen. Nachgemessen:

        ``betonwände``  → ``concrete walls``    (das Glossar kann es)
        ``betonwaende`` → ``betonwaende``       (dasselbe Wort, unberührt)

    Das Glossar ist auf echte Umlaute geschlüsselt. Wer ohne deutsche Tastatur tippt —
    oder aus einer Datei kommt, die keine Umlaute führt —, erreicht es nicht. *Dieses Repo
    selbst schreibt in jedem zweiten Kommentar «waende».*

    **Diese Regel kann nichts erfinden, sie kann nur finden** — dieselbe Zusage wie in
    :func:`grundform`. Zurückgegeben werden Kandidaten; ob einer gilt, entscheidet
    ausschliesslich, ob er **im Glossar steht**. ``blue`` wird zu ``blü`` und damit zu
    nichts, ``neue`` zu ``neü`` und damit zu nichts.
    """
    klein = (wort or "").lower()
    kandidaten: list[str] = []

    alle = klein
    for ersatz, umlaut in UMLAUTSCHREIBUNG:
        alle = alle.replace(ersatz, umlaut)
    if alle != klein:
        kandidaten.append(alle)

    # Und jede EINZELNE Stelle für sich — «Steuerhaus» darf nicht daran scheitern, dass
    # anderswo im selben Wort ein echtes «ue» steht.
    for ersatz, umlaut in UMLAUTSCHREIBUNG:
        stelle = klein.find(ersatz)
        while stelle >= 0:
            kandidat = klein[:stelle] + umlaut + klein[stelle + len(ersatz):]
            if kandidat not in kandidaten:
                kandidaten.append(kandidat)
            stelle = klein.find(ersatz, stelle + 1)
    return tuple(kandidaten)


def _bekannte_umlautform(wort: str) -> str | None:
    """Die erste Umlautform, die **im Glossar steht** — oder ``None``."""
    for kandidat in _umlaut_kandidaten(wort):
        if kandidat in GLOSSAR:
            return kandidat
    return None


def grundform(wort: str) -> str | None:
    """Die Glossarform eines gebeugten Wortes — oder ``None``.

    Abgestreift wird **nur**, was danach im Glossar steht. ``matter`` würde zu ``matt``
    und damit zu ``matte``; ``sommer`` bliebe ``sommer``, weil ``somm`` kein Eintrag ist.
    Die Regel kann also nichts erfinden, sie kann nur finden.

    Umlaute werden **nachrangig** aufgelöst: erst der Stamm wie er ist, dann entumlautet.
    ``bäumen`` → ``bäum`` (kein Eintrag) → ``baum`` (Eintrag). Und weil das nur bei
    Unbekanntem greift, wird aus ``grün`` nie ``grun``.
    """
    klein = (wort or "").lower()
    if not klein or klein in GLOSSAR:
        return klein if klein in GLOSSAR else None
    # Ersatzschreibung der Umlaute, VOR dem Abstreifen von Endungen: «waende» ist als
    # «wände» ein Eintrag, und kein Stamm davon ist einer.
    umlautform = _bekannte_umlautform(klein)
    if umlautform:
        return umlautform
    for endung in ENDUNGEN:
        if not klein.endswith(endung) or len(klein) - len(endung) < 3:
            continue
        stamm = klein[: -len(endung)]
        for kandidat in (stamm, _entumlautet(stamm),
                         _bekannte_umlautform(stamm) or ""):
            if kandidat and kandidat in GLOSSAR:
                return kandidat
    return None


def zerlege_kompositum(wort: str) -> tuple[str, ...] | None:
    """Ein zusammengesetztes Wort in seine Glossarteile — oder ``None``.

    Deutsch setzt **kopf-final** zusammen: ``Holz`` + ``Fassade``. Englisch stellt in
    diesen Fällen genauso — ``wood facade`` —, weshalb die Übersetzung der Teile in
    derselben Reihenfolge stehenbleiben darf. Für Fälle, in denen das nicht gilt, gibt es
    diese Regel nicht; es gibt einen Glossareintrag.

    Zerlegt wird in **genau zwei** Teile, beide mindestens :data:`MIN_TEILLAENGE` lang,
    beide im Glossar, und **keiner davon ein Zahlwort** (:data:`ZAHLWOERTER` — der Grund
    steht dort). Der zweite Teil darf gebeugt sein (``Nordfassaden``).

    **Was das falsch machen kann, und warum es trotzdem so steht.** Ein Kompositum ist
    nicht immer die Summe seiner Teile. Zwei echte Fälle aus unserem eigenen Glossar:
    ``Hochhaus`` wird zu ``tall house`` statt ``high-rise``, und ``Blaulicht`` zu
    ``blue light`` statt ``emergency light``. Beide sind nicht absurd, aber falsch.

    Der Schutz ist nicht Vermeidung, sondern **Sichtbarkeit**: Jede Zerlegung steht im
    Ergebnis unter ``regeln``, mit ihren Teilen. Wer den Prompt liest, sieht, was das
    Glossar sich gedacht hat — und ein Wort, das oft genug falsch zerlegt wird, bekommt
    einen eigenen Eintrag, der die Regel dann schlägt.
    """
    klein = (wort or "").lower()
    if len(klein) < 2 * MIN_TEILLAENGE or klein in GLOSSAR:
        return None
    for schnitt in range(MIN_TEILLAENGE, len(klein) - MIN_TEILLAENGE + 1):
        vorn, hinten = klein[:schnitt], klein[schnitt:]
        if vorn not in GLOSSAR:
            vorn = _bekannte_umlautform(vorn) or vorn
        if vorn not in GLOSSAR or vorn in ZAHLWOERTER:
            continue
        hinten_grund = hinten if hinten in GLOSSAR else grundform(hinten)
        if hinten_grund and hinten_grund not in ZAHLWOERTER:
            return (vorn, hinten_grund)
    return None


# --------------------------------------------------------------------------------------
# Die Mehrzahl — die einzige Regel dieses Moduls, die zwei Wörter zugleich sieht
# --------------------------------------------------------------------------------------
#
# **Der Anlass, heute gemessen** (16.09.2026):
#
#     ``zwoelf fenster``  →  ``twelve window``
#
# Die Zahl stimmt, das Hauptwort steht in der Einzahl. Das Glossar bildet je EIN Wort auf
# je ein englisches ab und sieht nie zwei Wörter zugleich; dass die Zahl davor das
# Hauptwort dahinter bestimmt, kann es darum nicht wissen. Die Zahlwörter vom Vormittag
# des 16.09. haben den Fall **sichtbar gemacht, nicht verursacht** — ``fenster`` →
# ``window`` stand schon vorher im Glossar, und «zwölf fenster» war schon vorher
# ``zwölf window``.
#
# Deutsch bräuchte die Regel nicht: «zwölf Fenster» ist im Deutschen schon Mehrzahl, und
# genau deshalb fällt beim Schreiben des Prompts nichts auf. Englisch braucht sie, und
# dieses Modul gibt es dafür, dass kein halbrichtiges Englisch ins Bildmodell geht.
#
# **Warum eine Regel und keine zweite Glossarspalte.** Ein Mehrzahleintrag je Hauptwort
# wäre die zweite Hälfte jedes Eintrags und träfe doch nur, was jemand eingetragen hat.
# Die Regel greift auch da, wo das englische Hauptwort erst durch :func:`grundform` oder
# :func:`zerlege_kompositum` entstanden ist — «vier betonwaende» geht durch die
# Kompositumsregel, und kein Eintrag der Welt sähe es kommen.
#
# **Warum sie trotzdem ein Verzeichnis ist und keine blosse Endungsregel.** Englische
# Mehrzahl ist nicht durchgängig «+s». Alle acht Zeilen unten stehen so im Glossar
# dieses Moduls, keine ist ausgedacht:
#
#     ``sketch``   → ``sketches``    (auf -ch)
#     ``bush``     → ``bushes``      (auf -sh)
#     ``lens``     → ``lenses``      (auf -s)
#     ``balcony``  → ``balconies``   (Mitlaut + y)
#     ``storey``   → ``storeys``     (Selbstlaut + y — NICHT ``storeies``)
#     ``person``   → ``people``      (unregelmässig)
#     ``concrete`` → ``concrete``    (nicht zählbar; ``two concretes`` gibt es nicht)
#     ``walls``    → ``walls``       (steht schon in der Mehrzahl)
#
# Die Endungsregel deckt die ersten fünf Zeilen ab. Die letzten drei deckt sie nicht, und
# keine Endungsregel der Welt könnte das: **ob ein Wort zählbar ist, steht nicht in seinen
# Buchstaben.** Darum wird nur gebeugt, was in :data:`ZAEHLBAR` steht — ein Verzeichnis,
# das am 16.09.2026 Eintrag für Eintrag durch alle 387 Glossareinträge gegangen ist
# (387 deutsche Einträge, darin 340 verschiedene englische Werte — nachgezählt).
#
# Was nicht darin steht, bleibt stehen. Ein unverändertes ``twelve window`` ist ein
# sichtbarer Schönheitsfehler; ein erfundenes ``twelve concretes`` liest sich wie richtiges
# Englisch und wird darum nie wieder als Fehler erkannt — die fünfte Regel dieses Repos,
# angewandt auf Grammatik.

#: Zahlwörter, die im **englischen** Text die Mehrzahl auslösen — alles ab zwei.
#:
#: Es sind die englischen Formen, nicht die deutschen: Die Regel läuft NACH dem
#: Nachschlagen, auf dem bereits übersetzten Text. Dort steht ``twelve``, nicht ``zwölf``.
#: Ziffern kommen dazu und werden gerechnet, nicht aufgezählt — ``12 fenster`` ist
#: dieselbe Aussage wie ``zwölf fenster`` (siehe :func:`_loest_mehrzahl_aus`).
#:
#: ``one`` fehlt, und ``a``/``an`` ebenfalls: «ein Wohnhaus» ist *a residential building*
#: und bleibt Einzahl. ``eight`` und ``eleven`` stehen mit drin, obwohl das Glossar sie
#: nicht erzeugen kann — ``acht`` und ``elf`` sind bewusst keine Glossareinträge, die
#: Gründe stehen oben bei den Zahlwörtern. Käme ein englisches ``eight`` doch einmal in
#: einem deutschen Prompt vor, wäre die Mehrzahl danach genauso richtig wie bei ``nine``.
MEHRZAHL_AUSLOESER = frozenset({
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
    "twelve",
})

#: Die englischen Hauptwörter des Glossars, die **zählbar** sind — nur sie werden gebeugt.
#:
#: Aufgenommen ist, was in einem Bildprompt wirklich gezählt wird: Bauteile, Baukörper,
#: Orte, Dinge im Bild, Bildsorten. Die Liste ist am 16.09.2026 von Hand durch alle
#: Glossarwerte gegangen; sie ist mit Absicht **kürzer als die Menge der Hauptwörter**.
#:
#: **Die Gegenprobe steckt im Glossar selbst.** Zu fünfzehn dieser Wörter führt das
#: Glossar die Mehrzahl als eigenen Eintrag — ``wände`` → ``walls``, ``dächer`` →
#: ``roofs``, ``balkone`` → ``balconies``, ``geschosse`` → ``storeys``, ``oberflächen`` →
#: ``surfaces``, ``personen`` → ``people`` und neun weitere. Die Endungsregel unten
#: liefert für alle fünfzehn genau die Form, die das Glossar unabhängig davon führt. Das
#: ist keine Schätzung, sondern ein gemessener Abgleich, und er läuft bei jedem Testlauf
#: mit: ``test_die_endungsregel_trifft_die_mehrzahlen_des_glossars``.
ZAEHLBAR = frozenset({
    # --- Baukörper und Räume ----------------------------------------------------------
    "building", "house", "volume", "extension", "basement", "floor", "storey",
    "room", "kitchen", "ceiling",
    # --- Bauteile ---------------------------------------------------------------------
    "roof", "window", "door", "entrance", "balcony", "terrace", "loggia", "facade",
    "wall", "column", "stair", "railing", "parapet", "chimney", "dormer", "canopy",
    "cornice", "gable", "skylight", "plinth", "reveal",
    # --- Umgebung ---------------------------------------------------------------------
    "tree", "bush", "hedge", "garden", "courtyard", "square", "street", "path",
    "city", "village", "lake", "river", "corner", "side", "season",
    # --- Was im Bild steht und sich zählen lässt ---------------------------------------
    "person", "bicycle", "car",
    # --- Bild und Aufnahme ------------------------------------------------------------
    "photograph", "drawing", "sketch", "rendering", "visualisation", "model", "view",
    "detail", "lens",
    # --- Übriges, das gezählt wird ----------------------------------------------------
    "cloud", "colour", "material", "surface",
})

#: Die unregelmässigen Formen. In diesem Glossar ist es **genau eine**.
#:
#: Nachgezählt am 16.09.2026 über alle Glossarwerte: ``person`` → ``people`` ist das
#: einzige Hauptwort, dessen Mehrzahl die Endungsregel verfehlen würde. ``roof`` →
#: ``roofs`` sieht nach einem zweiten Fall aus und ist keiner (``rooves`` ist veraltet) —
#: das Glossar führt ``dächer`` → ``roofs`` und bestätigt die regelmässige Form.
MEHRZAHL_UNREGELMAESSIG = {
    "person": "people",
}

#: Hauptwörter ohne Mehrzahl — **entschieden, nicht vergessen**.
#:
#: Stoffe (``concrete``, ``glass``, ``wood``, ``steel``), Wetter (``rain``, ``snow``,
#: ``fog``), Licht (``light``, ``daylight``) und Bildeigenschaften (``contrast``,
#: ``sharpness``, ``grain``) haben im Englischen keine Mehrzahl, jedenfalls nicht in der
#: Bedeutung, in der sie hier stehen. ``two concretes`` wäre schlimmer als der Fehler, den
#: diese Regel behebt.
#:
#: Die Liste ist für den Ablauf **nicht nötig** — gebeugt wird ohnehin nur, was in
#: :data:`ZAEHLBAR` steht. Sie steht hier aus zwei Gründen: Sie trennt im Befund das
#: «entschieden: keine Mehrzahl» vom «nicht entschieden» (siehe :func:`mehrzahl_befund`),
#: und sie ist der Stolperdraht für den nächsten, der :data:`ZAEHLBAR` erweitert — der
#: Test hält beide Mengen auseinander.
OHNE_MEHRZAHL = frozenset({
    # Stoffe
    "concrete", "glass", "wood", "steel", "metal", "aluminium", "copper", "zinc",
    "render", "cladding", "patina",
    # Wetter, Licht, Luft
    "rain", "snow", "water", "fog", "haze", "wind", "weather",
    "light", "daylight", "lighting", "sunshine",
    # Boden und Bewuchs
    "grass", "vegetation", "planting", "terrain", "countryside", "ground",
    # Bildeigenschaften und Bildzonen
    "contrast", "sharpness", "grain", "foreground", "background",
})

#: Glossarwerte, die **schon in der Mehrzahl** stehen.
#:
#: Das Glossar führt zu vielen Hauptwörtern beide Formen (``wand`` → ``wall``, ``wände``
#: → ``walls``), und mehrwortige Einträge enden teils auf einer Mehrzahl (``concrete
#: walls``, ``mature trees``, ``long shadows``). An ihnen ist nichts zu tun; eine zweite
#: Bildung ergäbe ``wallses``.
#:
#: Auch hier gilt: Für den Ablauf reicht, dass sie nicht in :data:`ZAEHLBAR` stehen. Die
#: Liste macht die Entscheidung sichtbar und prüfbar — und sie enthält mit ``eaves`` und
#: ``surroundings`` zwei Wörter, die im Englischen **nur** in der Mehrzahl vorkommen und
#: darum auch niemandem als Einzahl in :data:`ZAEHLBAR` rutschen dürfen.
SCHON_MEHRZAHL = frozenset({
    "balconies", "cars", "clouds", "colours", "columns", "doors", "eaves", "figures",
    "materials", "mountains", "people", "roofs", "rooms", "shadows", "shrubs",
    "stairs", "storeys", "surfaces", "surroundings", "trees", "walls",
})

#: Wörter, hinter denen die Wortgruppe der Zahl **endet**.
#:
#: Der Grund ist der Kopf der Gruppe. Deutsch wie Englisch stellen das Hauptwort ans Ende
#: einer Wortgruppe aus Beiwörtern (``residential building``, ``concrete wall``), und
#: genau dieses letzte Wort wird gebeugt. Ein Verhältniswort oder ein Bindewort beendet
#: die Gruppe aber: In ``two with garden`` gehört ``garden`` nicht zur Zwei, und
#: ``two with gardens`` wäre eine erfundene Aussage.
#:
#: Dasselbe für mehrwortige Glossareinträge, die kein Hauptwort am Ende haben —
#: ``in front of``, ``during the day``, ``out of focus``, ``black and white``,
#: ``painted in a pale tone``. Alle fünf enden hier an ihrem Funktionswort und werden
#: nicht angefasst. Bei vieren steht es vorne; bei ``black and white`` steht es an
#: zweiter Stelle, die Gruppe endet also erst nach ``black`` — auch das ist kein Kopf,
#: den ein Verzeichnis kennt, und auch dort geschieht darum nichts (nachgefahren am
#: 16.09.2026: ``zwei schwarzweiss`` → ``two black and white``).
_MEHRZAHL_TRENNER = frozenset({
    "a", "an", "the", "of", "in", "at", "on", "to", "from", "and", "or", "with",
    "without", "no", "not", "for", "above", "below", "behind", "beside", "between",
    "through", "against", "next", "opposite", "after", "before", "during", "over",
    "under", "near", "by", "into", "onto", "out", "off", "up", "down",
    "is", "are", "was", "were", "be", "seen", "taken", "painted", "very", "slightly",
})

#: Wie viele Wörter eine Zahl höchstens überspannen darf.
#:
#: **Drei**, und der Wert ist nicht geraten: Es ist die Länge des längsten mehrwortigen
#: Glossareintrags ohne Funktionswort (``high thin clouds``). Was länger ist, ist keine
#: Wortgruppe mehr, sondern ein halber Satz — und in einem halben Satz weiss diese Regel
#: nicht, welches Wort zur Zahl gehört. Sie lässt ihn dann in Ruhe.
MEHRZAHL_MAX_GRUPPE = 3

#: Die vier Ausgänge von :func:`mehrzahl_befund`, für das Protokoll und für die Tests.
MEHRZAHL_GEBEUGT = "gebeugt"
MEHRZAHL_UNZAEHLBAR = "nicht zaehlbar"
MEHRZAHL_SCHON = "schon mehrzahl"
MEHRZAHL_OFFEN = "nicht entschieden"

#: Wort ODER Ziffernfolge. Das reguläre :data:`_WORT` wirft Ziffern weg — hier sind sie
#: der halbe Fall («12 fenster»), und darum braucht die Mehrzahl ein eigenes Muster.
_ZAHL_ODER_WORT = re.compile(r"\d+|[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)


def _endungsregel(wort: str) -> str:
    """Die regelmässige englische Mehrzahl — gültig **nur** für :data:`ZAEHLBAR`.

    Drei Zeilen, und jede hat ihren Beleg im Glossar dieses Moduls:

    * auf ``s``, ``sh``, ``ch``, ``x`` → ``+es``: ``lens`` → ``lenses``, ``bush`` →
      ``bushes``, ``sketch`` → ``sketches``.
    * auf Mitlaut + ``y`` → ``ies``: ``balcony`` → ``balconies``, ``city`` → ``cities``.
      Auf **Selbstlaut** + ``y`` gilt das ausdrücklich nicht: ``storey`` → ``storeys``
      (das Glossar führt ``geschosse`` → ``storeys``), ``chimney`` → ``chimneys``.
    * sonst ``+s``.

    Auf ``z`` endet kein Wort in :data:`ZAEHLBAR`. Die Endung fehlt darum hier: Eine
    Regel, die dieses Repo nie ausführt, ist eine Regel, die niemand je prüft.
    """
    if wort.endswith(("s", "sh", "ch", "x")):
        return wort + "es"
    if len(wort) > 1 and wort.endswith("y") and wort[-2] not in "aeiou":
        return wort[:-1] + "ies"
    return wort + "s"


def mehrzahl_befund(wort: str) -> dict:
    """Was aus einem englischen Hauptwort wird, wenn eine Zahl davorsteht — mit Grund.

    Returns:
        ``{einzahl, mehrzahl, grund}``. ``mehrzahl`` ist **die dritte Antwort dieses
        Repos, auf Grammatik angewandt**:

        * eine Zeichenkette — gebeugt (``grund`` = ``"gebeugt"``).
        * ``None`` mit ``grund`` = ``"nicht zaehlbar"`` oder ``"schon mehrzahl"`` —
          **entschieden**, dass nicht gebeugt wird. Jemand hat hingesehen.
        * ``None`` mit ``grund`` = ``"nicht entschieden"`` — **nicht entschieden**. Weder
          Verzeichnis noch Ausnahme kennt dieses Wort. Das ist kein «in Ordnung»: Der
          Text bleibt zwar unverändert, aber er bleibt es aus Unwissen, und der Befund
          sagt das. So steht im Ergebnis, was diese Regel nicht konnte, statt dass es
          jemand am Bild suchen muss.
    """
    klein = (wort or "").lower()
    if not klein:
        return {"einzahl": klein, "mehrzahl": None, "grund": MEHRZAHL_OFFEN}
    if klein in SCHON_MEHRZAHL:
        return {"einzahl": klein, "mehrzahl": None, "grund": MEHRZAHL_SCHON}
    if klein in OHNE_MEHRZAHL:
        return {"einzahl": klein, "mehrzahl": None, "grund": MEHRZAHL_UNZAEHLBAR}
    if klein in MEHRZAHL_UNREGELMAESSIG:
        return {"einzahl": klein, "mehrzahl": MEHRZAHL_UNREGELMAESSIG[klein],
                "grund": MEHRZAHL_GEBEUGT}
    if klein in ZAEHLBAR:
        return {"einzahl": klein, "mehrzahl": _endungsregel(klein),
                "grund": MEHRZAHL_GEBEUGT}
    return {"einzahl": klein, "mehrzahl": None, "grund": MEHRZAHL_OFFEN}


def mehrzahl(wort: str) -> str | None:
    """Die englische Mehrzahl eines Wortes — oder ``None``, wenn nicht gebeugt wird.

    Der kurze Weg für den häufigen Fall. **Warum** nicht gebeugt wird, sagt nur
    :func:`mehrzahl_befund`; wer die drei Antworten auseinanderhalten muss, fragt dort.
    """
    return mehrzahl_befund(wort)["mehrzahl"]


def _loest_mehrzahl_aus(zeichen: str) -> bool:
    """Ist das eine Zahl grösser als eins?

    Ziffern werden **gerechnet**, nicht nachgeschlagen: ``12`` steht in keiner Liste, und
    eine Liste bis zwölf wäre genau die Sorte Grenze, die beim dreizehnten Fenster kippt.
    ``1`` löst nicht aus, ``0`` auch nicht — ``no window`` ist der Fall der Verneinung und
    hat mit dieser Regel nichts zu tun.
    """
    if zeichen.isdigit():
        return int(zeichen) >= 2
    return zeichen.lower() in MEHRZAHL_AUSLOESER


def _schliesst_an(luecke: str) -> bool:
    """Trägt diese Lücke zwischen zwei Fundstellen die Wortgruppe weiter?

    Nur ein **reiner Abstand** tut das, und die beiden Gegenfälle sind verschieden:

    * **Leer** — die beiden Stücke kleben aneinander. ``24mm`` ist eine Brennweite, keine
      Anzahl von Millimetern; ``3d`` ist eine Schreibweise, keine Anzahl von d. Ohne diese
      Hälfte ergibt ``24mm wand`` ein ``24mm walls`` — gemessen am 16.09.2026 an der
      entschärften Fassung, und `24mm f8` ist ausgerechnet der Prompt, den dieses Modul
      an zwei Stellen als Musterfall führt.
    * **Nicht leer und nicht nur Abstand** — dazwischen steht ein Satzzeichen. «vier,
      betonwaende» ist eine Aufzählung aus zwei Gliedern, kein Zahlwort vor seinem
      Hauptwort.

    Eigene Funktion statt zweier Bedingungen in der Schleife, damit eine Mutationsprobe
    genau diesen Wächter entschärfen kann und keinen zweiten mit.
    """
    return bool(luecke) and not luecke.strip()


def _ist_nachkommastelle(text: str, stuecke: list[re.Match], i: int) -> bool:
    """Ist diese Ziffernfolge die **Nachkommastelle** einer Zahl — und damit keine Anzahl?

    **Gemessener Fehler, gefunden in der Prüfung vom 16.09.2026:**

        ``f2.8 objektiv``  →  ``f2.8 lenses``

    :data:`_ZAHL_ODER_WORT` liest Ziffernfolgen, und ``2.8`` sind darin zwei Funde:
    ``2`` und ``8``. Die ``8`` steht unmittelbar vor ``objektiv`` → ``lens``, ist
    grösser als eins, und die Regel machte daraus pflichtschuldig eine Mehrzahl.
    Ebenso gemessen:
    ``f5.6 objektiv`` → ``f5.6 lenses``, ``f1.4 objektiv`` → ``f1.4 lenses``,
    ``16.09.2026 fenster`` → ``16.09.2026 windows``.

    Das ist genau die Sorte Fehler, gegen die die fünfte Regel dieses Repos steht:
    ``lenses`` liest sich wie richtiges Englisch, und ein Prompt mit einer Blendenzahl
    darin sieht heil aus. Die Blende ist aber keine Stückzahl — sie zählt gar nichts.

    Erkannt wird der Fall an seiner Form, nicht an einer Liste von Einheiten: Eine
    Ziffernfolge, vor der **unmittelbar** ein Punkt oder ein Komma steht und davor wieder
    eine Ziffernfolge, ist die zweite Hälfte einer Zahl und keine eigene. Das deckt die
    deutsche Schreibung (``2,8``) mit ab, ohne dass irgendwo ``mm``, ``f`` oder ``ISO``
    stehen müsste — eine Einheitenliste wäre wieder eine Grenze, die beim nächsten
    Kürzel kippt.

    Die vordere Hälfte (``2`` in ``f2.8``) braucht keine eigene Sperre: Ihre Wortgruppe
    endet ohnehin am Punkt, denn der ist kein Abstand (:func:`_schliesst_an`).
    """
    fund = stuecke[i]
    if i == 0 or not fund.group(0).isdigit():
        return False
    davor = stuecke[i - 1]
    if not davor.group(0).isdigit():
        return False
    return text[davor.end():fund.start()] in (".", ",")


def _mehrzahl_anwenden(text: str) -> tuple[str, tuple[dict, ...]]:
    """Die Regel auf den **schon übersetzten** Text anwenden.

    Der Ablauf, und er ist bewusst eng gefasst:

    1. Eine Zahl grösser eins finden (Wort oder Ziffer).
    2. Die Wortgruppe dahinter lesen — höchstens :data:`MEHRZAHL_MAX_GRUPPE` Wörter,
       **nur durch Leerzeichen getrennt** und keines davon aus :data:`_MEHRZAHL_TRENNER`.
    3. Das **letzte** Wort dieser Gruppe ist der Kopf. Nur er wird gebeugt.

    **Warum nur Leerzeichen trennen dürfen.** «vier, betonwaende» ist eine Aufzählung aus
    zwei Gliedern, kein Zahlwort vor seinem Hauptwort; das Komma sagt es. Der Auftrag
    verlangt «unmittelbar davor», und unmittelbar heisst hier wörtlich. Dieser Fall ist
    auch der Grund, dass die Einschränkung überhaupt auffiel: Er steht seit dem 12.09.2026
    als gemeldeter Prompt in den Tests dieses Moduls.

    **Warum die Gruppe an einem unbekannten Wort nicht endet.** ``twelve window frames``
    — ``frames`` kennt das Glossar nicht, aber es ist offensichtlich der Kopf. Endete die
    Gruppe davor, entstünde ``twelve windows frames``: falscher als vorher. Die Gruppe
    läuft darum bis zum Trennwort, und weil der Kopf dann ``frames`` heisst und in keinem
    Verzeichnis steht, geschieht nichts. Das ist die richtige Richtung.
    """
    stuecke = list(_ZAHL_ODER_WORT.finditer(text or ""))
    befunde: list[dict] = []
    ersetzungen: list[tuple[int, int, str]] = []
    # Welche Köpfe schon eine Zahl haben. Der Grund steht unten bei `behandelt.add`.
    behandelt: set[int] = set()

    # Von HINTEN nach vorn, damit bei zwei Zahlen vor demselben Kopf die NÄHERE gewinnt.
    for i in range(len(stuecke) - 1, -1, -1):
        zahlfund = stuecke[i]
        if not _loest_mehrzahl_aus(zahlfund.group(0)):
            continue
        # Eine Nachkommastelle ist keine Anzahl — `f2.8 objektiv` ergab `lenses`.
        if _ist_nachkommastelle(text, stuecke, i):
            continue

        gruppe: list[re.Match] = []
        j = i + 1
        while j < len(stuecke):
            if not _schliesst_an(text[stuecke[j - 1].end():stuecke[j].start()]):
                break
            wort = stuecke[j].group(0).lower()
            if wort.isdigit() or wort in _MEHRZAHL_TRENNER:
                break
            gruppe.append(stuecke[j])
            if len(gruppe) > MEHRZAHL_MAX_GRUPPE:
                break
            j += 1

        if not gruppe or len(gruppe) > MEHRZAHL_MAX_GRUPPE:
            # **Hier gab die Regel auf — und sagt es.** Vorher stand an dieser Stelle ein
            # blosses `continue`: Der Text blieb richtigerweise stehen, aber im Befund
            # stand danach gar nichts, und nichts liest sich wie «nichts zu tun». Eine
            # Zahl ohne lesbare Wortgruppe ist aber genau der NICHT-GEMESSEN-Fall dieses
            # Repos — «zwei, fenster» wäre mit einem Tippfehler weniger eine Mehrzahl,
            # und «drei grosse alte hohe fenster» ist der Regel schlicht zu lang.
            # `einzahl` ist `None`, weil es kein Wort gibt, auf das sich der Befund
            # bezöge; der Grund ist derselbe wie beim unbekannten Kopf.
            befunde.append({"zahl": zahlfund.group(0).lower(), "einzahl": None,
                            "mehrzahl": None, "grund": MEHRZAHL_OFFEN})
            continue

        kopf = gruppe[-1]
        # **Ein Kopf, eine Zahl** — und das ist keine Vorsichtsmassnahme, sondern ein
        # gemessener Fehler. In ``three ten window`` (so entsteht ein zerlegtes
        # «dreizehn», wenn man die Zahlwortsperre der Kompositumsregel entschärft) sind
        # BEIDE Zahlen Auslöser, beide fanden denselben Kopf, und beide beugten ihn:
        # ``three ten windowss``. Genau die doppelte Bildung, gegen die
        # :data:`SCHON_MEHRZAHL` steht — nur eine Ebene tiefer, im eigenen Durchgang.
        # Gefunden hat ihn die Mutationsprobe zur Zahlwortsperre, nicht das Nachdenken.
        if kopf.start() in behandelt:
            continue
        behandelt.add(kopf.start())

        befund = {"zahl": zahlfund.group(0).lower(), **mehrzahl_befund(kopf.group(0))}
        befunde.append(befund)
        if befund["mehrzahl"]:
            ersetzungen.append((kopf.start(), kopf.end(), befund["mehrzahl"]))

    # Von hinten, damit die vorderen Stellen gültig bleiben. Der Lauf oben ging schon
    # rückwärts, die Liste steht also bereits in dieser Reihenfolge.
    for anfang, ende, ersatz in ersetzungen:
        text = text[:anfang] + ersatz + text[ende:]
    # Der Befund dagegen soll in der Reihenfolge des Textes lesbar sein.
    return text, tuple(reversed(befunde))


def _glossar_muster() -> re.Pattern:
    """Ein Muster über alle Glossareinträge, **längste Wendung zuerst**.

    Die Reihenfolge ist der ganze Trick: Stünde ``himmel`` vor ``bedeckter himmel``,
    ergäbe „bedeckter Himmel" ein „bedeckter sky" — halb übersetzt, und genau die
    Zwischensprache, die das Modell am wenigsten versteht.
    """
    schluessel = sorted(GLOSSAR, key=lambda s: (-len(s), s))
    return re.compile(
        r"(?<![\w-])(" + "|".join(re.escape(s) for s in schluessel) + r")(?![\w-])",
        re.IGNORECASE,
    )


_GLOSSAR_MUSTER = _glossar_muster()


def glossar_uebersetzung(text: str) -> dict:
    """Die Vorgabe-Übersetzung: Nachschlagen, ersetzen, den Rest melden.

    Returns:
        ``{text, verfahren, ersetzt, unbekannt}``. ``ersetzt`` sind die gefundenen
        deutschen Wendungen in der Reihenfolge des Textes, ``unbekannt`` die Wörter, die
        **nach** der Ersetzung noch deutsch aussehen.

    ``unbekannt`` ist die eigentliche Leistung dieser Funktion. Ein Glossar, das
    unbekannte Wörter still stehenlässt, liefert einen Prompt, der übersetzt aussieht und
    es nicht ist — und der Fehler fällt erst am Bild auf, wenn überhaupt.

    Die Grenze dazu, ausdrücklich: ``unbekannt`` **übermeldet**. Es ist die Menge der
    Wörter, die unser kleiner englischer Wortschatz nicht kennt (:func:`_nicht_englisch`)
    — darunter fallen auch Eigennamen und englische Wörter, die schlicht nicht im
    Glossar vorkommen. Die Richtung ist gewollt: „Nordfassade" und „langen" müssen
    auffallen, und dafür darf „cantilevered" mit auffallen.
    """
    ersetzt: list[str] = []

    def _tausch(fund: re.Match) -> str:
        wort = fund.group(1)
        schluessel = wort.lower()
        if schluessel not in ersetzt:
            ersetzt.append(schluessel)
        # Immer kleingeschrieben — auch wenn das deutsche Wort gross war.
        #
        # Deutsch schreibt jedes Hauptwort gross. Wer das mitnimmt, bekommt
        # „a Residential building with Flat roof in the Fog": englische Wörter in
        # deutscher Rechtschreibung, und ein satzmittiges Grosswort liest sich im
        # Bildmodell als Eigenname. Die erste Fassung übernahm die Grossschreibung
        # wenigstens am Textanfang — auch das war falsch: Der Freitext steht im fertigen
        # Prompt NICHT am Anfang, sondern hinter der Handschrift des Stils. Er ist immer
        # satzmittig. Kleinschreibung ist ausserdem genau die Konvention der Bausteine
        # dieses Projekts (siehe `prompts.Baustein`), und der Freitext fügt sich in
        # dieselbe Aufzählung.
        return GLOSSAR[schluessel]

    neu = _GLOSSAR_MUSTER.sub(_tausch, text or "")

    # Zweiter Durchgang: Was das Nachschlagewerk nicht kannte, bekommen die beiden
    # Regeln. Sie laufen NUR über Wörter, die der englische Wortschatz nicht kennt —
    # damit können sie nichts anfassen, was der erste Durchgang schon übersetzt hat.
    regeln: list[dict] = []

    def _regel(fund: re.Match) -> str:
        wort = fund.group(0)
        if wort.lower() in _ENGLISCHER_WORTSCHATZ:
            return wort
        stamm = grundform(wort)
        if stamm:
            regeln.append({"wort": wort.lower(), "art": ART_BEUGUNG,
                           "teile": (stamm,), "englisch": GLOSSAR[stamm]})
            return GLOSSAR[stamm]
        teile = zerlege_kompositum(wort)
        if teile:
            englisch = " ".join(GLOSSAR[t] for t in teile)
            regeln.append({"wort": wort.lower(), "art": ART_KOMPOSITUM,
                           "teile": teile, "englisch": englisch})
            return englisch
        return wort

    neu = _WORT.sub(_regel, neu)

    # `unbekannt` wird VOR der Mehrzahl gemessen — und das ist kein Detail.
    #
    # Die Mehrzahlregel fasst ausschliesslich Wörter an, die bereits englisch sind, und
    # macht aus `window` ein `windows`. Der englische Wortschatz dieses Moduls
    # (`_ENGLISCHER_WORTSCHATZ`) kennt aber nur die Formen, die im Glossar stehen — ein
    # `windows` steht dort nicht. Nach der Beugung gemessen, meldete `unbekannt` also
    # ausgerechnet das Wort als «nicht übersetzt», das diese Regel gerade richtig
    # gestellt hat, und `vollstaendig` kippte auf False. Gemessen am 16.09.2026 an
    # «zwölf fenster»: vor dieser Zeile `unbekannt = ('windows',)`.
    unbekannt = _nicht_englisch(neu)

    neu, mehrzahlen = _mehrzahl_anwenden(neu)

    return {
        "text": neu,
        "verfahren": VERFAHREN_GLOSSAR,
        "ersetzt": tuple(ersetzt),
        # Was eine REGEL übersetzt hat, steht getrennt von dem, was ein EINTRAG
        # übersetzt hat. Eine Regel irrt anders als ein Nachschlagewerk — sie kann ein
        # Kompositum zerlegen, das keines ist —, und wer das Ergebnis prüft, soll die
        # beiden Sorten auseinanderhalten können, ohne den Code zu lesen.
        "regeln": tuple(regeln),
        # Die Mehrzahl steht getrennt von `regeln`, weil sie eine andere Sorte Eingriff
        # ist: `regeln` sagt, wie ein DEUTSCHES Wort zu seinem englischen kam; `mehrzahl`
        # sagt, was danach am ENGLISCHEN Wort noch geändert wurde. Und sie steht auch da,
        # wo nichts geändert wurde — ein Eintrag mit `mehrzahl: None` nennt den Grund.
        "mehrzahl": mehrzahlen,
        "unbekannt": unbekannt,
    }


def glossar_evidenz(text: str) -> tuple[str, ...]:
    """Deutsche Glossarwörter im Text, die **nicht** auch englisch sind.

    Der Grund, dass es diese Funktion gibt: ``Beton`` trägt kein Signalwort und keinen
    Umlaut. :func:`sieht_englisch_aus` sagt darum zu Recht „nicht entscheidbar" — und
    ohne diesen zweiten Blick bliebe genau der häufigste Fall der Oberfläche
    unübersetzt, nämlich das einzelne deutsche Fachwort.

    Umgekehrt darf ``see``, ``wind`` oder ``film`` hier nicht zählen: Sie stehen im
    Glossar, sind aber ebenso englisch. Was in beiden Sprachen vorkommt, beweist keine.
    Diese Ausnahmen stehen in :data:`ENGLISCH_AUCH`.
    """
    funde: list[str] = []
    for fund in _GLOSSAR_MUSTER.finditer(text or ""):
        wort = fund.group(1).lower()
        if wort not in ENGLISCH_AUCH and wort not in funde:
            funde.append(wort)

    # ZWEITER BLICK: Wörter, die kein EINTRAG sind, aber von den REGELN erreicht werden.
    #
    # **Der Anlass** (HomeStation, 12.09.2026): Im Prompt stand «vier, betonwaende», und
    # beides blieb deutsch stehen. `betonwaende` ist kein Glossareintrag — erst die Regeln
    # machen daraus `concrete walls`. Dieser Zeuge sah davon nichts, `ist_deutsch` sagte
    # nein, und die Übersetzung lief gar nicht erst an.
    #
    # *Ein Zeuge, der weniger kennt als der, für den er aussagt, spricht regelmässig frei.*
    # Gezählt wird darum genau das, was die Übersetzung auch WIRKLICH umsetzen könnte —
    # und nichts, was der englische Wortschatz kennt.
    for fund in _WORT.finditer(text or ""):
        wort = fund.group(0).lower()
        if wort in funde or wort in ENGLISCH_AUCH:
            continue
        if wort in _ENGLISCHER_WORTSCHATZ:
            continue
        if grundform(wort) or zerlege_kompositum(wort):
            funde.append(wort)
    return tuple(funde)


def ist_deutsch(text: str) -> bool:
    """Die Frage „ist das deutsch?" — mit **beiden** Zeugen, an einer einzigen Stelle.

    Zeuge eins ist :func:`sieht_englisch_aus` (Umlaute, Signalwörter) und trägt den ganzen
    Satz. Zeuge zwei ist :func:`glossar_evidenz` und trägt das einzelne Fachwort, das
    weder Umlaut noch Signalwort hat — ``Beton``, ``Sichtbeton``, ``Flachdach``.

    Warum das eine eigene Funktion ist und nicht dreimal derselbe Ausdruck: Die erste
    Fassung fragte an drei Stellen verschieden. :func:`uebersetze` kannte beide Zeugen,
    :func:`sprachwarnung` nur den ersten — und schwieg deshalb zu „Sichtbeton", das
    unmittelbar davor übersetzt worden wäre. Zwei Antworten auf dieselbe Frage im selben
    Programm sind immer ein Fehler; welche der beiden falsch ist, entscheidet der Zufall
    des Aufrufwegs.
    """
    befund = sieht_englisch_aus(text)
    if befund["englisch"] is False:
        return True
    return befund["englisch"] is None and bool(glossar_evidenz(text))


class SprachError(ValueError):
    """Ein eingehängter Übersetzer hält seinen Teil der Abmachung nicht ein.

    Erbt von ``ValueError`` wie :class:`aiimaging.prompts.PromptError` — damit
    bestehendes ``except ValueError`` greift.
    """


def uebersetze(text: str, *, uebersetzer=None) -> dict:
    """Deutschen Prompt-Text nach Englisch bringen — und beide Fassungen zurückgeben.

    Args:
        text: Was die Person geschrieben hat. Bleibt unangetastet im Ergebnis.
        uebersetzer: Die **Naht**. ``None`` nimmt :func:`glossar_uebersetzung`. Sonst
            ein Aufrufbares ``(text) -> dict`` mit den Schlüsseln ``text`` und
            ``verfahren``, wahlweise ``unbekannt`` und ``ersetzt``. Hier hängt ein
            Übersetzungsmodell ein, ohne dass ein einziger Aufrufer sich ändert.

    Returns:
        ``{original, uebersetzt, noetig, ersetzt, regeln, mehrzahl, unbekannt,
        vollstaendig, verfahren, erkennung, warnungen}``.

        ``noetig`` sagt, ob überhaupt Deutsch erkannt wurde. Ist es ``False``, bleibt
        ``uebersetzt`` gleich ``original`` und ``verfahren`` ist ``"keine"`` — ein
        englischer Prompt wird **nicht** durchs Glossar gedreht. Sonst würde aus einem
        englischen „in" ein englisches „in", aus „no people" aber womöglich Unsinn;
        vor allem aber wäre die Meldung „übersetzt" dann eine Unwahrheit.

    Raises:
        SprachError: Der eingehängte Übersetzer gibt nicht zurück, was verabredet ist.
            **Bewusst laut.** Ein Übersetzer, dessen Antwort nicht verstanden wird und
            der darum stillschweigend übergangen würde, liesse den deutschen Text
            durchlaufen — und alles hier stünde umsonst.
    """
    original = text if isinstance(text, str) else ""
    erkennung = sieht_englisch_aus(original)

    # Zwei Wege zu „das ist deutsch", und beide werden gebraucht:
    #   1. Die Erkennung sagt es (Umlaute, Signalwörter) — der Fall des ganzen Satzes.
    #   2. Sie kann es nicht entscheiden, aber das Glossar findet ein eindeutig deutsches
    #      Fachwort — der Fall der einzelnen Eingabe „Beton".
    # Ein `True` der Erkennung schlägt beides: Was englisch aussieht, wird nicht angefasst.
    if erkennung["englisch"] is False:
        anlass, evidenz = "erkennung", ()
    elif ist_deutsch(original):
        anlass, evidenz = "glossar", glossar_evidenz(original)
    else:
        anlass, evidenz = "keiner", ()

    if not original.strip() or anlass == "keiner":
        return {
            "original": original,
            "uebersetzt": original,
            "noetig": False,
            "anlass": "keiner",
            "evidenz": (),
            "ersetzt": (),
            "regeln": (),
            "mehrzahl": (),
            "unbekannt": (),
            "vollstaendig": True,
            "verfahren": VERFAHREN_KEINE,
            "erkennung": erkennung,
            "warnungen": (),
        }

    ergebnis = (uebersetzer or glossar_uebersetzung)(original)
    if not isinstance(ergebnis, dict) or not isinstance(ergebnis.get("text"), str) \
            or not isinstance(ergebnis.get("verfahren"), str):
        raise SprachError(
            "Der eingehängte Übersetzer muss ein Wörterbuch mit den Textschlüsseln "
            f"'text' und 'verfahren' liefern, kam aber mit {ergebnis!r}. Ohne diese "
            "beiden Angaben wüsste das Protokoll weder, was gerendert wurde, noch womit "
            "übersetzt wurde — und ein stilles Weiterreichen des deutschen Textes wäre "
            "der Fehler, gegen den dieses Modul gebaut ist."
        )

    unbekannt = tuple(ergebnis.get("unbekannt") or ())
    warnungen: list[str] = []
    if unbekannt:
        warnungen.append(
            f"Nicht übersetzt geblieben: {', '.join(unbekannt)}. Der Prompt ist damit "
            f"halb deutsch, und halb deutsch ist für das Bildmodell schlechter als ganz "
            f"deutsch — es steht zwischen zwei Sprachen. Entweder diese Wörter ins "
            f"Glossar aufnehmen oder den Prompt gleich englisch schreiben."
        )

    return {
        "original": original,
        "uebersetzt": ergebnis["text"],
        "noetig": True,
        "anlass": anlass,
        "evidenz": evidenz,
        "ersetzt": tuple(ergebnis.get("ersetzt") or ()),
        "regeln": tuple(ergebnis.get("regeln") or ()),
        # Ein eingehängter Übersetzer muss die Mehrzahl nicht kennen; er liefert den
        # Schlüssel dann schlicht nicht, und hier steht ein leeres Feld statt einer
        # Behauptung.
        "mehrzahl": tuple(ergebnis.get("mehrzahl") or ()),
        "unbekannt": unbekannt,
        "vollstaendig": not unbekannt,
        "verfahren": ergebnis["verfahren"],
        "erkennung": erkennung,
        "warnungen": tuple(warnungen),
    }


def sprachwarnung(text: str) -> str:
    """Die Warnung der QA für einen Prompt, der nicht englisch aussieht — oder ``""``.

    Der zweite Teil des Owner-Entscheids vom 21.08.2026: *„Ja, als Warnung im Ergebnis."*
    Sie steht dort, wo sie jemand liest — im Renderergebnis —, und nicht in einem
    Logfile, das niemand öffnet.

    Sie meldet nur den **entschiedenen** Fall. Wo weder Signalwörter noch ein deutsches
    Fachwort stehen, schweigt sie: Eine Warnung, die bei ``24mm f8`` anschlägt, wird nach
    dem dritten Mal weggeklickt, und danach auch die richtige.
    """
    if not ist_deutsch(text):
        return ""
    befund = sieht_englisch_aus(text)
    begruendung = befund["begruendung"]
    if befund["englisch"] is None:
        begruendung = (
            "Deutsche Fachwörter erkannt: " + ", ".join(glossar_evidenz(text)) + "."
        )
    return (
        f"Der Prompt sieht nicht englisch aus. {begruendung} Die Bildmodelle "
        f"sind an englischen Bild-Text-Paaren trainiert; ein deutscher Prompt wird nicht "
        f"schlechter verstanden, sondern anders. Am Gerät gemessen (8 gepaarte "
        f"Startwerte): 'bedeckter Himmel' ergab einen deutlich blaueren Himmel als "
        f"'overcast sky' — 8 von 8 Mal. Übersetzen (aiimaging.sprache.uebersetze) oder "
        f"gleich englisch schreiben."
    )


__all__ = [
    "DEUTSCHE_SIGNALWOERTER", "ENGLISCHE_SIGNALWOERTER", "GLOSSAR", "SprachError",
    "VERFAHREN_ERKENNUNG", "VERFAHREN_GLOSSAR", "VERFAHREN_KEINE",
    "ENGLISCH_AUCH", "glossar_evidenz", "glossar_uebersetzung",
    "ART_BEUGUNG", "ART_EINTRAG", "ART_KOMPOSITUM", "ENDUNGEN", "MIN_TEILLAENGE",
    "ZAHLWOERTER",
    "MEHRZAHL_AUSLOESER", "MEHRZAHL_GEBEUGT", "MEHRZAHL_MAX_GRUPPE", "MEHRZAHL_OFFEN",
    "MEHRZAHL_SCHON", "MEHRZAHL_UNREGELMAESSIG", "MEHRZAHL_UNZAEHLBAR",
    "OHNE_MEHRZAHL", "SCHON_MEHRZAHL", "ZAEHLBAR", "mehrzahl", "mehrzahl_befund",
    "grundform", "ist_deutsch", "sieht_englisch_aus", "sprachwarnung", "uebersetze",
    "zerlege_kompositum",
]
