"""PROMPTS — was der Prompt sagen darf, und was die Geometrie sagt.

Der eine Satz, aus dem dieses Modul folgt
------------------------------------------
    **Ein Prompt, der Bauteile nennt, die die Geometrie nicht hat, ist eine
    Aufforderung zur Halluzination.**

Das ist am Gerät gelernt (`auf-20260818-09`, 18.08.2026): Ich schrieb „clean flat roof"
für einen oben offenen Quader, und das Bildmodell lieferte ein Dach. Es hat nichts falsch
gemacht — es tat, was dastand. Der Fehler war meiner, und er ist die teuerste Sorte, weil
das Ergebnis *gut aussieht*.

Daraus folgt die Arbeitsteilung dieses Moduls:

* **Die Tiefenkarte sagt, WAS gebaut ist.** Kubatur, Öffnungen, Vor- und Rücksprünge.
* **Der Prompt sagt, WIE es aussieht.** Licht, Wetter, Tageszeit, Material, Umgebung,
  Bildcharakter — alles, was die Geometrie *nicht* trägt.

Warum die sieben Kategorien schon stimmen
------------------------------------------
Sie sind aus dem älteren KosmoVis-Bestand übernommen (`archviz_prompt_library.py`, sieben
Kategorien; die Inhalte lagen ausserhalb des Repos und fehlen). Beim Übernehmen fiel auf,
was ihre eigentliche Qualität ist:

    ``vegetation``, ``people``, ``atmosphere``, ``light_time``, ``sky``,
    ``material_detail``, ``composition``

**Keine einzige davon nennt ein Bauteil.** Sie beschreiben ausnahmslos das, was um das
Gebäude herum und auf seinen Oberflächen liegt — nie das Gebäude selbst. Die Einteilung
ist damit nicht bloss eine Ordnung, sondern genau die Regel von oben, in Fächer gegossen.
Sie wurde hier nicht erfunden; sie wurde erkannt.

Was dieses Modul deshalb NICHT anbietet
----------------------------------------
Es gibt keine Kategorie für Bauteile, und es wird keine geben. Wer ein Dach im Bild will,
baut es in die Geometrie. Der :func:`bauteilwaechter` prüft freien Text darauf und meldet
Funde — er verbietet nichts, denn manchmal *hat* die Geometrie das genannte Bauteil, und
das kann dieses Modul nicht wissen. Er sagt nur, wo das Risiko liegt.

Sprache
-------
Die Bausteine sind **englisch**. Nicht aus Bequemlichkeit: Die Bildmodelle sind ganz
überwiegend an englischen Bild-Text-Paaren trainiert, und ein deutscher Prompt landet
messbar schlechter. Die *Namen* und Erklärungen bleiben deutsch, weil sie für Menschen
sind — dieselbe Trennung wie im ganzen Projekt.

Abhängigkeiten: keine. Reine stdlib, kein ``bpy``, aus Python heraus ohne Oberfläche
aufrufbar (Regel 4). Regel 3: keine Büro-, Kunden- oder Projektnamen — die Stile sind
gattungsmässig beschrieben, nicht an einem Haus abgeschrieben.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------------------
# Die sieben Kategorien
# --------------------------------------------------------------------------------------

#: Die Kategorien in der Reihenfolge, in der sie im Prompt erscheinen.
#:
#: Die Reihenfolge ist nicht beliebig. Bildmodelle gewichten frühe Wörter stärker, und
#: was zuerst steht, prägt das Bild am meisten. Darum vorne, was die Erscheinung des
#: Bauwerks bestimmt (Bildcharakter, Licht, Material), und hinten, was Beiwerk ist
#: (Menschen, Bewuchs). Wer die Reihenfolge umdreht, bekommt ein Bild über einen Baum,
#: in dem zufällig ein Haus steht.
KATEGORIEN = ("composition", "light_time", "sky", "atmosphere",
              "material_detail", "vegetation", "people")

#: Was jede Kategorie beschreiben darf — für Menschen, und als Prüfstein beim Erweitern.
KATEGORIE_ERKLAERUNG = {
    "composition": "Bildcharakter und Aufnahmeart: Objektiv, Film, Schärfe, Kontrast. "
                   "NICHT der Bildausschnitt — den bestimmt die Kamera (`kameras.py`).",
    "light_time": "Tageszeit und Lichtrichtung: weich, hart, Gegenlicht, Stunde.",
    "sky": "Der Himmel als Fläche: bedeckt, klar, Wolkenart. Er ist im Bild meist das "
           "Grösste nach dem Bauwerk und färbt alles mit.",
    "atmosphere": "Was zwischen Kamera und Bauwerk liegt: Dunst, Nebel, Regen, Klarheit.",
    "material_detail": "Wie die Oberflächen wirken: Rauheit, Alter, Feuchte, Glanz. "
                       "NICHT welches Bauteil aus welchem Stoff besteht.",
    "vegetation": "Bewuchs ringsum. Beiwerk, das Massstab gibt.",
    "people": "Menschen im Bild. Geben Massstab und Leben — und sind die Kategorie mit "
              "dem grössten Halluzinationsrisiko, weil Bildmodelle sie gern erfinden.",
}


@dataclass(frozen=True)
class Baustein:
    """Ein einzelner wählbarer Textbaustein.

    ``frozen=True`` wie überall in diesem Projekt: Die Bibliothek ist ein
    Nachschlagewerk, kein Zustand.

    Args:
        slug: Schlüssel, stabil. Er landet im Protokoll eines Laufs — ein umbenannter
            Slug macht alte Läufe unlesbar.
        name: Menschenlesbar, deutsch.
        text: Der englische Prompt-Baustein. **Kleingeschrieben und ohne Satzpunkt**,
            damit die Bausteine sich zu einem Satz fügen lassen.
        hinweis: Wann er passt und wann nicht.
    """

    slug: str
    name: str
    text: str
    hinweis: str = ""


def _b(slug, name, text, hinweis=""):
    return Baustein(slug=slug, name=name, text=text, hinweis=hinweis)


#: Die Bausteine je Kategorie.
#:
#: Bewusst **wenige und gute** statt vieler. Eine Liste mit dreissig Lichtstimmungen sieht
#: reich aus und ist unbenutzbar: Niemand vergleicht dreissig Läufe, und die Unterschiede
#: zwischen benachbarten Einträgen verschwinden im Rauschen des Modells.
#:
#: Was hier NICHT steht, und zwar mit Absicht: ``masterpiece``, ``best quality``, ``8k``,
#: ``highly detailed``, ``trending on artstation``. Diese Formeln stammen aus der
#: SD-1.5-Zeit und aus Bilddatenbanken mit Schlagwortlisten. Die heutigen Modelle —
#: Z-Image, Qwen-Image, SD 3.5 — sind an **natürlicher Sprache** trainiert; dort ist eine
#: Schlagwortkette bestenfalls wirkungslos und schlimmstenfalls ein Stilbefehl in Richtung
#: Fantasy-Illustration. Ein beschreibender Satz schlägt jede Adjektivkette.
BAUSTEINE: dict[str, tuple[Baustein, ...]] = {
    "composition": (
        _b("architekturfoto", "Architekturfotografie",
           "architectural photograph, shift lens, vertical lines kept parallel, "
           "even sharpness across the frame",
           "Die Vorgabe. Entspricht dem, was die Kamera dieses Projekts tut: Augenhöhe, "
           "stürzende Linien vermieden."),
        _b("reportage", "Reportage",
           "documentary photograph, 35mm, natural perspective, slight grain",
           "Weniger streng, wirkt beiläufig-echt. Gut, wenn Menschen im Bild sind."),
        _b("grossformat", "Grossformat",
           "large format photograph, 4x5 film, extremely fine detail, deep depth of field",
           "Ruhig und detailreich. Braucht saubere Geometrie — jede Kante wird sichtbar."),
        _b("modellfoto", "Modellfoto",
           "photograph of a physical architectural model, studio backdrop, "
           "shallow depth of field, visible material of the model",
           "Löst das Bauwerk bewusst aus der Wirklichkeit. Sehr geometrietreu, weil "
           "das Modell keine erfundenen Details verträgt."),
        _b("dokumentarisch_ruhig", "Dokumentarisch, ruhig",
           "quiet documentary photograph, film tonality, shadows kept open and never "
           "crushed, something in the near foreground giving depth",
           "AM KORPUS GEMESSEN (`auf-20260818-14`): Hier stand zuerst die Anweisung "
           "einer weichen Lichterzeichnung, mit der Begründung, das verhindere den "
           "ausgefressenen HDR-Look. "
           "**Die Referenzen fressen aber aus** — 7.5 % der Fläche über 95 % Helligkeit "
           "gegen 1.3 % bei gewöhnlichen Fotos. Zugelaufen sind sie dagegen kaum (0.5 % "
           "unter 5 %). Die Handschrift ist also nicht Clippingfreiheit, sondern "
           "**oben hell, unten offen** — und genau das steht jetzt da. Das feine Korn ist "
           "ebenfalls raus: Die Kornmessung war nicht entscheidbar (die Streuung der "
           "Streuung war so gross wie der Wert), und was ungemessen ist, wird nicht "
           "behauptet."),
        _b("skizzenhaft", "Skizzenhaft",
           "loose architectural sketch, graphite and light watercolour wash, "
           "visible pencil strokes, unfinished edges",
           "Die 'Einskizzierung' der Demo. ACHTUNG: Verwischt die Silhouette und senkt "
           "damit die Geometrie-Treue systematisch — siehe `treue_geeignet`."),
    ),
    "light_time": (
        _b("weich_bedeckt", "Weich, bedeckt",
           "soft even daylight, no direct sun, shadows barely visible",
           "Die ehrlichste Beleuchtung: Sie versteckt nichts und erfindet nichts. "
           "Vorgabe für jede Messung."),
        _b("vormittag", "Vormittag",
           "clear morning sunlight from a low angle, long soft shadows",
           ""),
        _b("mittag", "Mittag",
           "high midday sun, short hard shadows, bright surfaces",
           "Härteste Kontraste. Fassaden im Schatten laufen leicht zu."),
        _b("abendlicht", "Abendlicht",
           "warm low evening sun, long shadows, golden light on the surfaces",
           "Die schmeichelhafteste Stunde — und die, in der Bildmodelle am meisten "
           "dazuerfinden, weil ihre Trainingsbilder davon voll sind."),
        _b("daemmerung", "Dämmerung",
           "blue hour after sunset, cool ambient light, warm light spilling from inside",
           "Setzt Innenlicht voraus. Ohne Öffnungen in der Geometrie wirkt es leer."),
    ),
    "sky": (
        _b("bedeckt_gleichmaessig", "Gleichmässig bedeckt",
           "uniform overcast sky, neutral grey",
           "Vorgabe. Ein gleichmässiger Himmel ist die einzige Fläche, die der "
           "Tiefenschätzer verlässlich als 'fern' erkennt."),
        _b("klar", "Klar",
           "clear sky, deep blue, no clouds", ""),
        _b("hohe_wolken", "Hohe Wolken",
           "high thin cirrus clouds, mostly open sky", ""),
        _b("zugezogen", "Zugezogen",
           "heavy low clouds, diffuse dark grey sky", ""),
        _b("hell_diffus", "Hell und diffus",
           "bright luminous overcast sky, close to white and allowed to clip, "
           "soft cloud structure, no blue",
           "AM KORPUS GEMESSEN und BESTÄTIGT (`auf-20260818-14`): Himmelshelligkeit "
           "**0.782 ± 0.132** bei einer Gesamthelligkeit von 0.574 — deutlich heller als "
           "das übrige Bild und nahe an Weiss, nicht bei Neutralgrau (das wäre rund 0.5). "
           "Dazu ein Befund, der einer anderen Behauptung widersprach: **7.5 %** der "
           "Fläche liegen über 95 % Helligkeit, bei gewöhnlichen Fotos nur 1.3 %. Die "
           "Referenzen fressen also aus — sechsfach —, und zwar oben. `allowed to clip` "
           "steht darum ausdrücklich da: Es ist Absicht, kein Fehler."),
    ),
    "atmosphere": (
        _b("klar", "Klar",
           "clear air, no haze", "Vorgabe. Nichts zwischen Kamera und Bauwerk."),
        _b("leichter_dunst", "Leichter Dunst",
           "slight atmospheric haze in the distance",
           "Gibt Tiefe, ohne die Silhouette zu verlieren."),
        _b("morgennebel", "Morgennebel",
           "low morning fog around the base, upper parts clear",
           "ACHTUNG: Verdeckt den Fuss des Bauwerks — die Silhouette wird unten unscharf "
           "und die Geometrie-Treue sinkt messbar."),
        _b("nach_regen", "Nach dem Regen",
           "wet ground with reflections, air washed clear after rain",
           "Reflexionen im Boden geben ein zweites, gespiegeltes Bauwerk — schön, aber "
           "eine Erfindung des Modells und nicht der Geometrie."),
    ),
    "material_detail": (
        _b("neutral", "Neutral",
           "matte surfaces, true material colour, no gloss",
           "Vorgabe. Sagt bewusst nicht, WELCHES Material — das gehört ins Modell, nicht "
           "in den Prompt."),
        _b("fein_strukturiert", "Fein strukturiert",
           "fine surface texture visible, subtle grain and tooling marks", ""),
        _b("bewittert", "Bewittert",
           "weathered surfaces, subtle patina and water staining",
           "Nimmt dem Bild das Neubauhafte."),
        _b("gedaempft", "Zurückhaltend",
           "restrained colour held to a narrow range, no area louder than the rest, "
           "matte surfaces throughout, nothing glossy, no reflections used as an effect",
           "AM KORPUS GEMESSEN (`auf-20260818-14`, 74 Werke): Der frühere Name war "
           "falsch begründet. Die Sättigung der Referenzen liegt bei **0.193**, die "
           "gewöhnlicher Fotos bei **0.197** — praktisch gleich. Sie sind NICHT blasser. "
           "Was sich deutlich unterscheidet, ist die STREUUNG: 0.072 gegen 0.162. Die "
           "Referenzen sind **einheitlicher**, nicht farbärmer — und genau das steht "
           "jetzt im Text. Für eine Stilvorgabe ist Beständigkeit ohnehin die brauchbarere "
           "Grösse als ein Pegel."),
        _b("praezise", "Präzise",
           "crisp clean surfaces, sharp arrises, precise joints",
           "Für Wettbewerbsbilder. Betont die Kanten der Geometrie — und macht damit "
           "jeden Fehler in ihr sichtbar."),
    ),
    "vegetation": (
        _b("keine", "Keine",
           "no vegetation",
           "Vorgabe für jede Messung: Bewuchs verdeckt das Bauwerk und verfälscht die "
           "Silhouette."),
        _b("sparsam", "Sparsam",
           "a few low shrubs at a distance, no trees near the building", ""),
        _b("vordergrund", "Im Vordergrund",
           "wild meadow grass and mature trees in the near foreground, partly framing "
           "the view, the building set back behind them",
           "Der auffälligste Griff des KosmoOrbit-Stils: Es steht IMMER etwas davor. Das "
           "Bauwerk posiert nicht, es ist verortet. ACHTUNG: Bewuchs im Vordergrund "
           "verdeckt die Silhouette und senkt die Geometrie-Treue."),
        _b("baumbestand", "Baumbestand",
           "mature trees in the surroundings, none blocking the view",
           "'none blocking the view' steht dort mit Absicht — ohne diesen Zusatz stellt "
           "das Modell gern einen Baum vor die Fassade."),
    ),
    "people": (
        _b("keine", "Keine",
           "no people",
           "Vorgabe für jede Messung. Menschen sind die Kategorie mit dem grössten "
           "Halluzinationsrisiko."),
        _b("einzelne_ferne", "Einzelne, fern",
           "one or two people in the distance, small in frame, giving scale",
           "Massstab ohne Ablenkung. 'small in frame' ist der wichtige Teil."),
        _b("alltag", "Alltag",
           "small groups of people going about ordinary everyday activity, "
           "all of them small in the frame, none posing",
           "Nicht dasselbe wie 'belebt': 'none posing' und 'small in the frame' sind der "
           "Unterschied zwischen einem Ort, an dem Leute sind, und einem Werbebild."),
        _b("belebt", "Belebt",
           "several people walking, natural everyday activity",
           "Nur für Präsentationsbilder. Für die QA unbrauchbar."),
    ),
}


# --------------------------------------------------------------------------------------
# Der Bauteilwächter
# --------------------------------------------------------------------------------------

#: Wörter, die ein **Bauteil** benennen — englisch und deutsch.
#:
#: Sie sind nicht verboten. Sie sind der Ort, an dem der teuerste Fehler dieses Projekts
#: entstanden ist: Ein Prompt nennt ein Bauteil, die Geometrie hat es nicht, das Modell
#: erfindet es, und das Ergebnis sieht gut aus. Wer eines dieser Wörter schreibt, soll
#: einmal nachdenken, ob die Geometrie es trägt.
#:
#: Deutsch steht mit dabei, weil das Eingabefeld im Knoten keinen Sprachzwang hat und ein
#: Wächter, der nur die halbe Eingabe sieht, schlimmer ist als keiner — er erzeugt das
#: Gefühl, geprüft worden zu sein.
BAUTEILWOERTER = (
    # englisch
    "roof", "rooftop", "window", "windows", "door", "doors", "balcony", "balconies",
    "terrace", "facade", "façade", "wall", "walls", "column", "columns", "pillar",
    "pillars", "stair", "stairs", "staircase", "railing", "balustrade", "chimney",
    "dormer", "canopy", "awning", "pergola", "cornice", "gable", "eaves", "parapet",
    "skylight", "storey", "storeys", "story", "basement", "entrance", "porch", "arch",
    "arcade", "tower", "atrium", "shutters", "gutter", "downpipe",
    # deutsch
    "dach", "dächer", "fenster", "tür", "türen", "balkon", "balkone", "terrasse",
    "fassade", "wand", "wände", "stütze", "stützen", "säule", "säulen", "treppe",
    "treppen", "geländer", "kamin", "gaube", "vordach", "gesims", "giebel", "traufe",
    "attika", "oberlicht", "geschoss", "keller", "eingang", "bogen", "turm", "laibung",
)

_BAUTEIL_MUSTER = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(w) for w in BAUTEILWOERTER) + r")(?![\w-])",
    re.IGNORECASE,
)


def bauteilwaechter(text: str) -> dict:
    """Nennt dieser Text Bauteile? — melden, nicht verbieten.

    **Warum nicht verbieten:** Manchmal *hat* die Geometrie das genannte Bauteil, und
    dann ist die Nennung richtig und sogar nützlich. Ob sie es hat, kann dieses Modul
    nicht wissen — es sieht nur Text. Ein Verbot wäre eine Behauptung über eine Datei,
    die hier gar nicht vorliegt.

    **Warum überhaupt melden:** Weil der Fehler sonst unsichtbar ist. Ein erfundenes Dach
    sieht aus wie ein Dach. Der Lauf schlägt nicht fehl, die QA meldet nur eine schlechte
    Zahl, und niemand käme auf den Prompt.

    Returns:
        ``{gefunden, woerter, hinweis}``. ``gefunden`` ist ein bool, ``woerter`` die
        Fundstellen in der Reihenfolge des Textes, ohne Doppelungen.

    Grenze, die dazugehört: Der Wächter kennt Wörter, keine Bedeutung. „a wall of fog"
    schlägt an, obwohl keine Wand gemeint ist. Ein Fehlalarm kostet einen Blick, ein
    übersehener Fund ein Bild — die Richtung ist gewollt.
    """
    if not isinstance(text, str):
        return {"gefunden": False, "woerter": (), "hinweis": ""}

    treffer: list[str] = []
    for fund in _BAUTEIL_MUSTER.finditer(text):
        wort = fund.group(1).lower()
        if wort not in treffer:
            treffer.append(wort)

    if not treffer:
        return {"gefunden": False, "woerter": (), "hinweis": ""}

    return {
        "gefunden": True,
        "woerter": tuple(treffer),
        "hinweis": (
            f"Der Prompt nennt Bauteile: {', '.join(treffer)}. Hat die Geometrie sie "
            f"wirklich? Wenn nicht, ist das eine Aufforderung zur Halluzination — das "
            f"Modell liefert sie, das Bild sieht gut aus, und die Geometrie-QA fällt "
            f"durch, ohne dass jemand den Prompt verdächtigt. (So entstand am "
            f"18.08.2026 ein Dach auf einem oben offenen Quader.) Trägt die Geometrie "
            f"sie, ist die Nennung richtig — dann diesen Hinweis übergehen."
        ),
    }


# --------------------------------------------------------------------------------------
# Renderstile
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Stil:
    """Ein Renderstil: eine Auswahl je Kategorie plus eine Handschrift.

    Args:
        slug: Stabiler Schlüssel, landet im Protokoll.
        name: Menschenlesbar, deutsch.
        beschreibung: Wofür er da ist — und wofür nicht.
        bausteine: Kategorie → Baustein-Slug. Kategorien, die fehlen, bleiben leer.
        handschrift: Ein zusätzlicher englischer Satz, der diesen Stil ausmacht und sich
            nicht in eine Kategorie fügt. Steht am Anfang des Prompts.
        negativ: Negativ-Prompt. **Wirkt nur oberhalb einer Führung von 1.0** — bei
            destillierten Turbo-Modellen also gar nicht; siehe :func:`komponiere`.
        treue_geeignet: Ob dieser Stil für die Geometrie-QA taugt. ``False`` heisst nicht
            „schlecht", sondern: Er verändert die Silhouette **von sich aus**, und ein
            niedriger `geom_iou` misst dann den Stil und nicht das Modell.
        empfohlene_controlnet_staerke: Wie streng die Tiefenkarte binden sollte, damit
            dieser Stil überhaupt entstehen kann. Ein Skizzenstil bei Stärke 1.0 bleibt
            ein Foto mit Bleistiftfilter.
        seitenverhaeltnis: Breite geteilt durch Höhe. ``None`` heisst „egal".

            **Das ist keine Kosmetik.** Es geht bis in die Kamerarechnung: Der vertikale
            Bildwinkel folgt aus dem Seitenverhältnis (:func:`aiimaging.kameras.bildwinkel`),
            und damit auch der Abstand, aus dem ein Bauwerk gerahmt wird. Wer einen
            hochformatigen Stil in einem 16:9-Rahmen rechnet, bekommt eine Kamera, die zu
            weit weg steht — und ein Bild, das mit dem Stil nichts mehr zu tun hat.
    """

    slug: str
    name: str
    beschreibung: str
    bausteine: dict[str, str]
    handschrift: str = ""
    negativ: str = ""
    treue_geeignet: bool = True
    empfohlene_controlnet_staerke: float = 0.9
    seitenverhaeltnis: float | None = None
    warnung: str = ""


#: Die Renderstile.
#:
#: **Erster Entwurf, ausdrücklich zur Widerrede.** Sie sind gattungsmässig gebaut — aus
#: dem, was Architekturbilder allgemein leisten müssen, nicht aus einem bestimmten Haus
#: (Regel 3). Was daran „Hausstil" werden soll, entscheidet der Owner; die Form steht,
#: der Geschmack fehlt.
#:
#: Die Auswahl ist bewusst klein. Sechs Stile, die man auseinanderhalten kann, sind mehr
#: wert als zwanzig, die ineinander übergehen — und jeder zusätzliche Stil ist eine
#: Vergleichsreihe mehr, die niemand fährt.
STILE: dict[str, Stil] = {}


def _stil(s: Stil) -> Stil:
    STILE[s.slug] = s
    return s


_stil(Stil(
    slug="messschnitt",
    name="Messschnitt (neutral)",
    beschreibung=(
        "Der Bezugsstil. Er erfindet so wenig wie möglich: bedeckt, schattenlos, ohne "
        "Menschen, ohne Bewuchs, matte Oberflächen ohne Materialaussage. Damit misst die "
        "Geometrie-QA wirklich das Bildmodell und nicht die Bildstimmung. "
        "**Jede Schwellenmessung dieses Projekts gehört auf diesen Stil.**"
    ),
    bausteine={"composition": "architekturfoto", "light_time": "weich_bedeckt",
               "sky": "bedeckt_gleichmaessig", "atmosphere": "klar",
               "material_detail": "neutral", "vegetation": "keine", "people": "keine"},
    handschrift="a plain, undramatic photograph of a building, "
                "the subject centred and fully visible",
    negativ="dramatic lighting, lens flare, heavy vignette, oversaturated colours",
    treue_geeignet=True,
    empfohlene_controlnet_staerke=1.0,
))

_stil(Stil(
    slug="wettbewerb",
    name="Wettbewerbsbild",
    beschreibung=(
        "Das Bild, das ein Projekt verkaufen soll, ohne es zu verfälschen: klarer "
        "Himmel, tiefstehende Vormittagssonne, präzise Oberflächen, Massstab durch "
        "wenige ferne Menschen. Streng genug für eine Abgabe, freundlich genug für eine "
        "Jury."
    ),
    bausteine={"composition": "architekturfoto", "light_time": "vormittag",
               "sky": "klar", "atmosphere": "leichter_dunst",
               "material_detail": "praezise", "vegetation": "sparsam",
               "people": "einzelne_ferne"},
    handschrift="a calm, precise architectural photograph, "
                "the building clearly readable against the sky",
    negativ="cluttered foreground, distorted perspective, oversaturated sky",
    treue_geeignet=True,
    empfohlene_controlnet_staerke=0.9,
))

_stil(Stil(
    slug="modellfoto",
    name="Modellfoto",
    beschreibung=(
        "Das Bauwerk als physisches Modell auf einem Studiotisch. Der ehrlichste Stil "
        "für einen frühen Stand: Er behauptet keine Wirklichkeit und lädt das Modell "
        "darum auch nicht ein, Details zu erfinden, die es noch nicht gibt."
    ),
    bausteine={"composition": "modellfoto", "light_time": "weich_bedeckt",
               "sky": "bedeckt_gleichmaessig", "atmosphere": "klar",
               "material_detail": "fein_strukturiert", "vegetation": "keine",
               "people": "keine"},
    # Die Handschrift ergänzt den Kompositionsbaustein, sie wiederholt ihn nicht: Der
    # sagt schon „physical architectural model, studio backdrop". Hier steht, was er
    # NICHT sagt — dass das Modell einfarbig ist.
    handschrift="the model built in a single pale material, no applied colour",
    negativ="photorealistic environment, sky background, people",
    treue_geeignet=True,
    empfohlene_controlnet_staerke=0.95,
))

_stil(Stil(
    slug="abendstimmung",
    name="Abendstimmung",
    beschreibung=(
        "Warmes, tiefstehendes Licht, lange Schatten. Das schmeichelhafteste Bild — und "
        "das mit dem grössten Erfindungsdruck, weil die Trainingsbilder der Modelle voll "
        "von goldenen Stunden sind. Für Präsentationen, nicht für Messungen."
    ),
    bausteine={"composition": "reportage", "light_time": "abendlicht",
               "sky": "hohe_wolken", "atmosphere": "leichter_dunst",
               "material_detail": "bewittert", "vegetation": "sparsam",
               "people": "einzelne_ferne"},
    handschrift="a warm evening photograph, low sun raking across the surfaces",
    negativ="midday light, flat lighting, empty grey sky",
    treue_geeignet=False,
    empfohlene_controlnet_staerke=0.85,
    warnung="Lange Schatten legen sich über die Silhouette und über das Gelände. Der "
            "Tiefenschätzer liest einen Schlagschatten leicht als Fläche — `geom_iou` "
            "sinkt dadurch, ohne dass das Bildmodell etwas falsch gemacht hätte.",
))

_stil(Stil(
    slug="morgennebel",
    name="Morgennebel",
    beschreibung=(
        "Tiefer Nebel um den Fuss, oben klar. Gibt einem Baukörper Tiefe und "
        "Massstab — und verdeckt genau das, was die Geometrie-QA misst."
    ),
    # `weich_bedeckt` und nicht `vormittag`: Eine tiefstehende Sonne UND schwere tiefe
    # Wolken UND Bodennebel schliessen sich gegenseitig aus. Ein widersprüchlicher Prompt
    # wird nicht etwa gemittelt — das Modell entscheidet sich für eine Lesart, und zwar
    # für die, die in seinen Trainingsbildern häufiger war. Welche das ist, weiss niemand.
    bausteine={"composition": "grossformat", "light_time": "weich_bedeckt",
               "sky": "zugezogen", "atmosphere": "morgennebel",
               "material_detail": "bewittert", "vegetation": "baumbestand",
               "people": "keine"},
    handschrift="a quiet photograph in early morning fog, "
                "the upper part of the building emerging clearly",
    negativ="clear air, harsh sunlight",
    treue_geeignet=False,
    empfohlene_controlnet_staerke=0.8,
    warnung="Der Nebel verdeckt den Fuss des Bauwerks. Die untere Silhouettenkante "
            "verschwindet, und `geom_iou` misst danach den Nebel. Für die QA ungeeignet — "
            "nicht weil das Bild schlecht wäre, sondern weil die Zahl es nicht mehr trifft.",
))

_stil(Stil(
    slug="einskizziert",
    name="Einskizziert",
    beschreibung=(
        "Die 'Einskizzierung' aus der Demo: lockere Handzeichnung mit lasierter Farbe, "
        "sichtbare Striche, offene Kanten. Für frühe Stände, in denen ein fotorealistisches "
        "Bild eine Genauigkeit behauptete, die der Entwurf noch nicht hat."
    ),
    bausteine={"composition": "skizzenhaft", "light_time": "weich_bedeckt",
               "sky": "bedeckt_gleichmaessig", "atmosphere": "klar",
               "material_detail": "neutral", "vegetation": "sparsam",
               "people": "einzelne_ferne"},
    handschrift="drawn by hand on textured paper, the drawing fading out "
                "towards the edges of the sheet",
    negativ="photorealistic, photographic texture, sharp photographic detail",
    treue_geeignet=False,
    empfohlene_controlnet_staerke=0.6,
    warnung="Offene Kanten und lasierte Flächen sind der ZWECK dieses Stils — und genau "
            "das, was `geom_iou` als Silhouettenfehler liest. Eine niedrige Zahl ist hier "
            "kein Befund, sondern die Beschreibung des Stils. Ausserdem braucht er eine "
            "gelockerte ControlNet-Stärke: Bei 1.0 entsteht ein Foto mit Bleistiftfilter.",
))

_stil(Stil(
    slug="kosmo_standard",
    name="KosmoOrbit-Standard",
    beschreibung=(
        "Der Hausstil des Ökosystems — ruhig, bedeckt, entsättigt, dokumentarisch. Das "
        "Bauwerk steht ZURÜCK: Es ist immer etwas davor, und die Menschen sind klein und "
        "beiläufig. Kein Heldenbild, sondern ein Ort, an dem jemand vorbeigekommen ist "
        "und fotografiert hat.\n\n"
        "Abgeleitet aus veröffentlichten Wettbewerbsvisualisierungen, die der Owner als "
        "Richtung vorgegeben hat (2026-08-18), und am 74 Werke umfassenden Korpus "
        "nachgemessen (`auf-20260818-14`). **Was übernommen wurde, sind Eigenschaften, "
        "kein Werk:** bedecktes Licht, sehr heller Himmel (0.782 gegen 0.574 im übrigen "
        "Bild), **einheitliche statt blasser Farbe** (die Sättigung ist so hoch wie bei "
        "gewöhnlichen Fotos — nur ihre Streuung ist halb so gross), oben hell bis zum "
        "Ausfressen und unten offen, Vordergrundbewuchs, kleine Figuren im Alltag, matte "
        "Materialien, kein Breitbild. "
        "Diese Eigenschaften gehören niemandem — sie sind fotografische und "
        "architektonische Konvention. Der Stil trägt darum auch keinen fremden Namen: "
        "Ein Studioname als Produkt-Preset wäre eine Anmassung, und die Bilder selbst "
        "sind fremdes Urheberrecht und liegen nicht in diesem Repo."
    ),
    bausteine={"composition": "dokumentarisch_ruhig", "light_time": "weich_bedeckt",
               "sky": "hell_diffus", "atmosphere": "leichter_dunst",
               "material_detail": "gedaempft", "vegetation": "vordergrund",
               "people": "alltag"},
    handschrift="an ordinary moment at a place someone happened to walk past",
    negativ="dramatic lighting, saturated colours, glossy reflections, "
            "heavy contrast, posed figures, empty showroom feeling",
    treue_geeignet=False,
    empfohlene_controlnet_staerke=0.85,
    # AM KORPUS GEMESSEN (`auf-20260818-14`, 74 Werke) — und meine Behauptung war in
    # dieser Schärfe FALSCH. Ich hatte an fünf Bildern gesehen: „alle quadratisch oder
    # hochformatig, keines 16:9". Gemessen sind 18 hochformatig und 23 quadratisch
    # (zusammen gut die Hälfte), aber **30 sind leicht quer** (1.15–1.6). Richtig ist
    # allein: **16:9 ist die Ausnahme** — 3 von 74.
    #
    # 1.0 bleibt trotzdem der Vorgabewert: Es ist die grösste einzelne Gruppe, und ein
    # Stil braucht EINEN Wert, um benutzbar zu sein. Aber er ist eine Vereinfachung eines
    # Korpus, der von hochformatig bis leicht quer reicht — und das gehört hierher und
    # nicht in eine Fussnote. Wer ein liegendes Bauwerk rahmt, darf ohne schlechtes
    # Gewissen auf 1.4 gehen; was der Stil ausschliesst, ist Breitbild.
    #
    # Die Falle, in die ich ohne die Messung gelaufen wäre: Die Vorlagen sind
    # BILDSCHIRMFOTOS, alle 2560×1440. Wer die Dateimasse misst, misst den Bildschirm und
    # nicht die Arbeit — und hätte die Behauptung scheinbar widerlegt, ohne sie geprüft
    # zu haben.
    seitenverhaeltnis=1.0,
    warnung="Der Vordergrundbewuchs ist der ZWECK dieses Stils — und genau das, was die "
            "Silhouette verdeckt. `geom_iou` sinkt dadurch systematisch, ohne dass das "
            "Bildmodell etwas falsch gemacht hätte. Für die Präsentation gebaut, nicht "
            "für die Messung: Zum Messen `messschnitt` nehmen und den Stil danach "
            "wechseln.",
))

#: Der Stil, auf dem jede Messung dieses Projekts gefahren wird.
MESS_STIL = "messschnitt"

#: Der Hausstil — was ohne andere Angabe erzeugt wird.
#:
#: Zwei verschiedene Vorgaben, und das ist Absicht: Gemessen wird auf dem Stil, der am
#: wenigsten erfindet; ausgeliefert wird der, der aussieht wie das Büro. Wer beides in
#: einen Stil zwingt, bekommt entweder unbrauchbare Bilder oder unbrauchbare Zahlen.
HAUS_STIL = "kosmo_standard"


# --------------------------------------------------------------------------------------
# Zusammensetzen
# --------------------------------------------------------------------------------------

class PromptError(ValueError):
    """Ein Stil, eine Kategorie oder ein Baustein ist unbekannt.

    Erbt von ``ValueError`` — dieselbe Entscheidung wie bei :class:`geometrie_qa.QaError`
    und :class:`backbone.BackboneError`, damit bestehendes ``except ValueError`` greift.
    """


def baustein(kategorie: str, slug: str) -> Baustein:
    """Einen Baustein nachschlagen — oder mit der Auswahl im Fehler antworten.

    Raises:
        PromptError: Kategorie oder Slug unbekannt. Die Meldung nennt, was es gibt; eine
            Fehlermeldung, die nur „unbekannt" sagt, zwingt zum Nachschlagen im Code.
    """
    if kategorie not in BAUSTEINE:
        raise PromptError(
            f"Unbekannte Kategorie {kategorie!r}. Bekannt: {', '.join(KATEGORIEN)}."
        )
    for b in BAUSTEINE[kategorie]:
        if b.slug == slug:
            return b
    verfuegbar = ", ".join(b.slug for b in BAUSTEINE[kategorie])
    raise PromptError(
        f"Unbekannter Baustein {slug!r} in {kategorie!r}. Bekannt: {verfuegbar}."
    )


def hole_stil(slug: str) -> Stil:
    """Einen Renderstil nachschlagen.

    Raises:
        PromptError: unbekannter Stil, mit der Liste der bekannten.
    """
    if slug not in STILE:
        raise PromptError(
            f"Unbekannter Renderstil {slug!r}. Bekannt: {', '.join(sorted(STILE))}."
        )
    return STILE[slug]


def komponiere(stil: str = MESS_STIL, *, freitext: str = "",
               ersetzungen: dict[str, str] | None = None,
               fuehrung: float | None = None) -> dict:
    """Aus einem Stil und dem freien Feld des Knotens einen fertigen Prompt bauen.

    Args:
        stil: Slug aus :data:`STILE`.
        freitext: Was im Prompt-Feld des Knotens steht. Wird **an den Anfang** gestellt,
            direkt nach der Handschrift des Stils — was eine Person eigens hinschreibt,
            ist ihr wichtiger als jede Vorgabe, und frühe Wörter wiegen im Bildmodell
            schwerer.
        ersetzungen: Kategorie → Baustein-Slug, um einzelne Fächer des Stils zu tauschen,
            ohne ihn zu verlassen. Das ist der Knopf für „wie der Wettbewerbsstil, aber
            ohne Menschen".
        fuehrung: Die ``guidance_scale`` des Laufs, wenn bekannt. Nur zur **Auskunft**:
            Unterhalb von 1.0 ist der Negativ-Prompt wirkungslos, und dann soll das hier
            stehen und nicht erst im Renderergebnis auffallen.

    Returns:
        ``{prompt, negativ_prompt, stil, bausteine, controlnet_staerke, treue_geeignet,
        hinweise}``.

        ``hinweise`` ist der Teil, der zählt: Bauteilfunde im Freitext, die Warnung eines
        nicht messtauglichen Stils, und ein wirkungsloser Negativ-Prompt. Alle drei sind
        Dinge, die sonst erst am fertigen Bild auffallen — oder gar nicht.

    Raises:
        PromptError: unbekannter Stil, unbekannte Kategorie oder unbekannter Baustein.

    Der Prompt ist eine **Aufzählung durch Kommata**, kein Satzgefüge. Das ist kein
    Stilmangel: Bildmodelle trennen an Kommata in Sinnabschnitte, und ein Nebensatz
    („a building that stands in a park where…") verwischt genau diese Trennung. Die
    einzelnen Abschnitte sind dafür ganze Wendungen und keine Einzelwörter — siehe die
    Begründung bei :data:`BAUSTEINE`.
    """
    s = hole_stil(stil)
    gewaehlt = dict(s.bausteine)
    for kategorie, slug in (ersetzungen or {}).items():
        if kategorie not in BAUSTEINE:
            raise PromptError(
                f"Unbekannte Kategorie {kategorie!r} in ersetzungen. "
                f"Bekannt: {', '.join(KATEGORIEN)}."
            )
        gewaehlt[kategorie] = slug

    teile: list[str] = []
    if s.handschrift:
        teile.append(s.handschrift)
    text = (freitext or "").strip().rstrip(",").strip()
    if text:
        teile.append(text)
    for kategorie in KATEGORIEN:
        slug = gewaehlt.get(kategorie)
        if slug:
            teile.append(baustein(kategorie, slug).text)

    hinweise: list[str] = []

    fund = bauteilwaechter(text)
    if fund["gefunden"]:
        hinweise.append(fund["hinweis"])

    if not s.treue_geeignet:
        hinweise.append(
            f"Der Stil '{s.name}' ist für die Geometrie-QA nicht geeignet. "
            + (s.warnung or "")
            + f" Für Messungen den Stil '{MESS_STIL}' nehmen — sonst misst die Zahl den "
              f"Stil und nicht das Bildmodell."
        )

    if s.negativ and fuehrung is not None and fuehrung <= 1.0:
        hinweise.append(
            f"Der Negativ-Prompt dieses Stils bleibt bei einer Führung von {fuehrung} "
            f"WIRKUNGSLOS: Unterhalb von 1.0 rechnet diffusers nicht mehr doppelt, und "
            f"genau davon lebt der negative Teil. Er steht dann im Protokoll und nicht "
            f"im Bild. Destillierte Turbo-Modelle laufen mit 0.0 — dort ist er nie wirksam."
        )

    return {
        "prompt": ", ".join(teile),
        "negativ_prompt": s.negativ,
        "stil": s.slug,
        "bausteine": gewaehlt,
        "controlnet_staerke": s.empfohlene_controlnet_staerke,
        "seitenverhaeltnis": s.seitenverhaeltnis,
        "treue_geeignet": s.treue_geeignet,
        "hinweise": tuple(hinweise),
    }


def uebersicht() -> dict:
    """Alles, was eine Oberfläche zum Bauen ihrer Auswahlfelder braucht — als reine Daten.

    Regel 4 in einer Funktion: Der Knoten im Cockpit ist eine **dünne Schicht** über
    dieser Auskunft. Er füllt seine Aufklappfelder daraus und schickt eine Auswahl
    zurück; entscheiden tut er nichts. Wer keine Oberfläche hat, ruft dasselbe aus
    Python und bekommt dieselbe Antwort.
    """
    return {
        "kategorien": [
            {"slug": k, "erklaerung": KATEGORIE_ERKLAERUNG[k],
             "bausteine": [{"slug": b.slug, "name": b.name, "hinweis": b.hinweis}
                           for b in BAUSTEINE[k]]}
            for k in KATEGORIEN
        ],
        "stile": [
            {"slug": s.slug, "name": s.name, "beschreibung": s.beschreibung,
             "treue_geeignet": s.treue_geeignet, "warnung": s.warnung,
             "controlnet_staerke": s.empfohlene_controlnet_staerke,
             "seitenverhaeltnis": s.seitenverhaeltnis,
             "bausteine": dict(s.bausteine)}
            for s in STILE.values()
        ],
        "mess_stil": MESS_STIL,
        "haus_stil": HAUS_STIL,
        "freitextfeld": (
            "Freier Prompt-Text. Er steht im fertigen Prompt VORNE und wiegt damit am "
            "schwersten. Was hier Bauteile nennt — Dach, Fenster, Balkon —, wird gemeldet: "
            "Hat die Geometrie sie nicht, erfindet das Bildmodell sie."
        ),
    }


__all__ = [
    "BAUSTEINE", "BAUTEILWOERTER", "KATEGORIEN", "KATEGORIE_ERKLAERUNG", "MESS_STIL",
    "HAUS_STIL", "STILE", "Baustein", "PromptError", "Stil", "baustein",
    "bauteilwaechter",
    "hole_stil", "komponiere", "uebersicht",
]
