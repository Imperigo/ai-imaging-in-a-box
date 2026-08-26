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
#: Sorte Risiko aus und ist keine: Der reguläre Plural der Femininа bildet sich mit ``n``
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

#: Verfahrensnamen für das Protokoll. Was durch eine REGEL übersetzt wurde und nicht
#: durch einen Eintrag, soll unterscheidbar bleiben — eine Regel irrt anders als ein
#: Nachschlagewerk.
ART_EINTRAG = "eintrag"
ART_BEUGUNG = "beugung"
ART_KOMPOSITUM = "kompositum"


def _entumlautet(wort: str) -> str:
    return "".join(_ENTUMLAUTUNG.get(z, z) for z in wort)


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
    for endung in ENDUNGEN:
        if not klein.endswith(endung) or len(klein) - len(endung) < 3:
            continue
        stamm = klein[: -len(endung)]
        for kandidat in (stamm, _entumlautet(stamm)):
            if kandidat in GLOSSAR:
                return kandidat
    return None


def zerlege_kompositum(wort: str) -> tuple[str, ...] | None:
    """Ein zusammengesetztes Wort in seine Glossarteile — oder ``None``.

    Deutsch setzt **kopf-final** zusammen: ``Holz`` + ``Fassade``. Englisch stellt in
    diesen Fällen genauso — ``wood facade`` —, weshalb die Übersetzung der Teile in
    derselben Reihenfolge stehenbleiben darf. Für Fälle, in denen das nicht gilt, gibt es
    diese Regel nicht; es gibt einen Glossareintrag.

    Zerlegt wird in **genau zwei** Teile, beide mindestens :data:`MIN_TEILLAENGE` lang,
    beide im Glossar. Der zweite Teil darf gebeugt sein (``Nordfassaden``).

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
            continue
        hinten_grund = hinten if hinten in GLOSSAR else grundform(hinten)
        if hinten_grund:
            return (vorn, hinten_grund)
    return None


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

    return {
        "text": neu,
        "verfahren": VERFAHREN_GLOSSAR,
        "ersetzt": tuple(ersetzt),
        # Was eine REGEL übersetzt hat, steht getrennt von dem, was ein EINTRAG
        # übersetzt hat. Eine Regel irrt anders als ein Nachschlagewerk — sie kann ein
        # Kompositum zerlegen, das keines ist —, und wer das Ergebnis prüft, soll die
        # beiden Sorten auseinanderhalten können, ohne den Code zu lesen.
        "regeln": tuple(regeln),
        "unbekannt": _nicht_englisch(neu),
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
        ``{original, uebersetzt, noetig, ersetzt, unbekannt, vollstaendig, verfahren,
        erkennung, warnungen}``.

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
    "grundform", "ist_deutsch", "sieht_englisch_aus", "sprachwarnung", "uebersetze",
    "zerlege_kompositum",
]
