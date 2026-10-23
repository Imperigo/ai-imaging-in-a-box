"""BELICHTUNG — misst, was ein Bild an Helligkeit tut, und vergleicht es mit einem Stil.

Warum dieses Modul überhaupt entsteht
-------------------------------------
Der alte Bestand hat eine Belichtungsprüfung, wir hatten keine. Beim Öffnen jener Datei
(``archviz_exposure_check.py``, 19.08.2026) fiel jedoch etwas auf, das wichtiger ist als
die fehlende Prüfung:

.. code-block:: python

    HIGHLIGHT_WARN_PCT = 8.0    # > 8% geclippte Highlights = warning
    TARGET_LUMA_MIN, TARGET_LUMA_MAX = 0.30, 0.65

Diese Zahlen stehen dort als **feste Konstanten** und liefern ein Urteil mit der Schwere
``error`` und dem Wort „Überbelichtet". Am Vortag hatten wir 74 Werke unseres eigenen
Stilkorpus vermessen (`auf-20260818-14`), und der Anteil über 0.95 Helligkeit liegt dort
im Mittel bei **0.0755** — bei einer Streuung von **0.069** und einem Höchstwert von
**0.3001**.

**Der Mittelwert unseres Hausstils liegt damit knapp unter einer Schwelle, die ihn zum
Fehler erklären würde, und ein einzelnes Referenzwerk liegt fast beim Vierfachen.**

Ein sauberer Vorbehalt gehört dazu, sonst wäre der Satz zu bequem: Der Altbestand misst
den Anteil über **0.98**, unsere Messung lief gegen **0.95**. Die Zahlen sind also
*nicht* unmittelbar vergleichbar — bei 0.98 fiele unser Anteil niedriger aus, um wieviel
ist **ungemessen**. Was sich trotzdem sagen lässt, ohne zu raten: Mittelwert plus eine
Streuung ergibt 0.145, also fast das Doppelte jener Schwelle, und der Höchstwert 0.3001
liegt darüber, egal an welcher der beiden Grenzen man misst. *Wieviele* der 74 Werke die
Schwelle rissen, lässt sich aus Mittelwert, Streuung, Minimum und Maximum **nicht**
ausrechnen — das wäre eine Verteilungsannahme, und wir haben die Verteilung nicht.

Die Lehre, und sie ist der Bauplan dieses Moduls
------------------------------------------------
> **Eine Belichtungsschwelle ist keine Eigenschaft guter Belichtung, sondern eines Stils.**

Unsere eigene Messung sagt wörtlich: *oben hell, unten offen* — das Ausgefressene ist
**Absicht**, und der Himmelsbaustein in :mod:`aiimaging.prompts` sagt seit dem 19.08.
ausdrücklich ``allowed to clip``. Eine Prüfung mit fester Schwelle würde also genau das
als Fehler melden, was der Prompt bestellt hat. Sie prüft dann nicht das Bild, sondern
den Geschmack ihres Autors.

Darum hängen hier **alle** Schwellen an einem :class:`Rahmen`, und jeder Rahmen sagt,
**welche seiner Zahlen gemessen sind**. Daraus folgt die einzige harte Regel dieses
Moduls:

> **Eine ungemessene Schwelle darf nie ``error`` melden, höchstens ``warn``.**

Das ist keine Höflichkeit, sondern dieselbe Unterscheidung, die dieses Projekt an vier
anderen Stellen führt: *bestanden*, *durchgefallen* und *nicht gemessen* sind drei
Zustände und nicht zwei. Eine Zahl, die niemand nachgeprüft hat, kann ein Bild nicht
verurteilen.

Was dieses Modul ausdrücklich NICHT tut
---------------------------------------
Es **wählt nicht aus**. Der alte Bestand hängt an die Belichtungsprüfung eine
Auto-Best-Auswahl; das ist eine andere Frage, sie hat andere Fallen (siehe
``docs/`` zur Variantenbewertung), und sie gehört nicht in dieselbe Datei.

Es **verbietet nicht**. Wie der :func:`aiimaging.prompts.bauteilwaechter` meldet es und
überlässt die Entscheidung dem Aufrufer — manchmal ist ein weisser Himmel genau das
Bestellte, und das kann eine Kennzahl nicht wissen.

Abhängigkeiten: nur :mod:`aiimaging.bildlesen` (reine stdlib). Kein ``numpy``, kein
``PIL``, kein ``bpy`` — der Altbestand versucht für dasselbe drei Backends, von denen das
erste ``bpy`` ist und uns damit unter Regel 2 und Regel 4 verschlossen wäre.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import bildlesen

#: Die Grenze, an der wir „ausgefressen" messen. **0.95, nicht 0.98** — weil unsere
#: einzige echte Messung (`auf-20260818-14`) gegen 0.95 gelaufen ist und eine Schwelle
#: nur gegen die Zahlen etwas bedeutet, mit denen sie erhoben wurde. Wer sie auf 0.98
#: stellt, muss den Korpus neu messen; darum steht sie im :class:`Rahmen` und nicht hier
#: als Naturkonstante.
HELL_GRENZE = 0.95

#: Die Grenze für „zugelaufen". Ebenfalls aus derselben Messung.
DUNKEL_GRENZE = 0.05

#: Die drei Schweregrade. Dieselben Wörter wie in ``graph.pruefe_bedarf`` und
#: ``mcp_schemas.pruefe_verdrahtbarkeit``, damit alle Befunde dieses Projekts gleich
#: gelesen werden.
SCHWERE_OK = "ok"
SCHWERE_WARN = "warn"
SCHWERE_FEHLER = "error"


class BelichtungsError(ValueError):
    """Das Bild lässt sich nicht messen, oder ein Rahmen ist unbrauchbar.

    Erbt von ``ValueError`` — dieselbe Entscheidung wie bei allen Fehlerklassen dieses
    Projekts, damit bestehendes ``except ValueError`` greift.
    """


@dataclass(frozen=True)
class Rahmen:
    """Was ein bestimmter Stil an Helligkeit erwarten lässt.

    Attribute:
        slug: Kennung, üblicherweise die eines Stils aus :mod:`aiimaging.prompts`.
        name: Klartext für Berichte.
        luma_min, luma_max: Spanne der mittleren Helligkeit.
        hell_grenze: ab welchem Wert ein Pixel als ausgefressen zählt.
        hell_anteil_max: wieviel Fläche darüber liegen darf, als Anteil (nicht Prozent).
        dunkel_grenze, dunkel_anteil_max: dasselbe für die andere Seite.
        streuung_min: darunter ist das Bild flach.
        gemessen: **die Namen der Felder, die auf einer Messung beruhen.** Alles, was
            nicht darin steht, kann höchstens ``warn`` auslösen — siehe Modulkopf. Das
            ist die einzige harte Regel dieses Moduls, und sie ist hier erzwungen und
            nicht nur beschrieben.
        herkunft: woher die Zahlen kommen, im Klartext. Wandert in jeden Befund, damit
            niemand eine Schwelle nachschlagen muss, um ein rotes Urteil einzuordnen.

    Der Rahmen ist eingefroren: Eine Schwelle, die sich zur Laufzeit ändern lässt, ist
    zwei Läufe später nicht mehr dieselbe, und dann bedeutet der Vergleich zweier Bilder
    nichts mehr.
    """

    slug: str
    name: str
    luma_min: float
    luma_max: float
    hell_anteil_max: float
    dunkel_anteil_max: float
    streuung_min: float
    gemessen: tuple[str, ...] = ()
    herkunft: str = ""
    hell_grenze: float = HELL_GRENZE
    dunkel_grenze: float = DUNKEL_GRENZE

    def __post_init__(self) -> None:
        for name in ("luma_min", "luma_max", "hell_anteil_max", "dunkel_anteil_max",
                     "streuung_min", "hell_grenze", "dunkel_grenze"):
            wert = getattr(self, name)
            if isinstance(wert, bool) or not isinstance(wert, (int, float)):
                raise BelichtungsError(f"{self.slug}: {name} ist keine Zahl: {wert!r}")
            if not math.isfinite(float(wert)):
                raise BelichtungsError(f"{self.slug}: {name} ist nicht endlich: {wert!r}")
        if not (0.0 <= self.luma_min < self.luma_max <= 1.0):
            raise BelichtungsError(
                f"{self.slug}: Helligkeitsspanne {self.luma_min}–{self.luma_max} ist "
                f"keine Spanne in 0..1."
            )
        if not (0.0 < self.hell_grenze <= 1.0) or not (0.0 <= self.dunkel_grenze < 1.0):
            raise BelichtungsError(
                f"{self.slug}: Grenzen {self.dunkel_grenze}/{self.hell_grenze} liegen "
                f"nicht in 0..1."
            )
        if self.dunkel_grenze >= self.hell_grenze:
            raise BelichtungsError(
                f"{self.slug}: die Dunkelgrenze {self.dunkel_grenze} liegt nicht unter "
                f"der Hellgrenze {self.hell_grenze} — dann wäre jedes Pixel beides."
            )
        unbekannt = set(self.gemessen) - {
            "luma_min", "luma_max", "hell_anteil_max", "dunkel_anteil_max",
            "streuung_min",
        }
        if unbekannt:
            raise BelichtungsError(
                f"{self.slug}: 'gemessen' nennt Felder, die es nicht gibt: "
                f"{sorted(unbekannt)}. Ein Tippfehler hier würde eine ungemessene "
                f"Schwelle stillschweigend zu einer gemessenen machen — genau das, was "
                f"dieses Modul verhindern soll."
            )

    def ist_gemessen(self, feld: str) -> bool:
        """Beruht diese Schwelle auf einer Messung? Entscheidet ``warn`` gegen ``error``."""
        return feld in self.gemessen


#: Der Rahmen unseres Hausstils. **Die einzigen wirklich gemessenen Zahlen des Moduls.**
#:
#: Quelle: `auf-20260818-14`, 74 Werke des Referenzkorpus, gegen 0.95/0.05 gemessen.
#: Helligkeit 0.5744 ± 0.116 (min 0.2454, max 0.8147); Anteil über 0.95: 0.0755 ± 0.069
#: (max 0.3001); Anteil unter 0.05: 0.0053 ± 0.0255 (max 0.2162).
#:
#: Die Spannen sind **Mittelwert ± zwei Streuungen**, unten und oben auf 0..1 geklemmt —
#: dieselbe Regel wie bei ``stil_qa.K_STREUUNGEN``, damit nicht zwei Module dieses
#: Projekts zwei verschiedene Begriffe von „noch normal" führen.
HAUSSTIL_RAHMEN = Rahmen(
    slug="kosmo_standard",
    name="KosmoOrbit-Standard",
    luma_min=0.343,          # 0.5744 - 2*0.116
    luma_max=0.806,          # 0.5744 + 2*0.116
    hell_anteil_max=0.214,   # 0.0755 + 2*0.069
    dunkel_anteil_max=0.056,  # 0.0053 + 2*0.0255
    streuung_min=0.05,
    gemessen=("luma_min", "luma_max", "hell_anteil_max", "dunkel_anteil_max"),
    herkunft=(
        "auf-20260818-14, 74 Werke des Referenzkorpus, Grenzen 0.95/0.05, "
        "Mittelwert ± zwei Streuungen. NICHT gemessen: streuung_min."
    ),
)

#: Der Rahmen für den Messstil — den, auf dem die Geometrie-QA läuft. Er ist bewusst
#: **weit**: Ein Bild, das nur zum Messen entsteht, soll nicht wegen seiner Belichtung
#: durchfallen. Keine dieser Zahlen ist gemessen, also kann keine ``error`` auslösen.
MESS_RAHMEN = Rahmen(
    slug="messschnitt",
    name="Messschnitt",
    luma_min=0.10,
    luma_max=0.95,
    hell_anteil_max=0.50,
    dunkel_anteil_max=0.50,
    streuung_min=0.02,
    gemessen=(),
    herkunft=(
        "Nicht gemessen, bewusst weit gesetzt. Ein Bild, das nur zum Messen entsteht, "
        "soll nicht an seiner Belichtung scheitern. Alle Befunde bleiben darum 'warn'."
    ),
)

#: Der geerbte Rahmen des Altbestands — **zum Vergleich, nicht zum Gebrauch.**
#:
#: Wörtlich aus ``archviz_exposure_check.py``: ``TARGET_LUMA_MIN/MAX`` 0.30/0.65,
#: ``HIGHLIGHT_WARN_PCT`` 8 %, ``SHADOW_WARN_PCT`` 12 %,
#: ``LOW_CONTRAST_THRESHOLD`` 0.10. Seine Hellgrenze ist 0.98, nicht 0.95 — sie ist hier
#: übernommen, damit der Vergleich wenigstens seine eigene Grenze benutzt.
#:
#: Er steht hier, weil ein gemessener Widerspruch mehr wert ist als eine Behauptung: Wer
#: unseren Korpus gegen diesen Rahmen hält, sieht den Unterschied in Zahlen statt in
#: einem Satz. **`gemessen` ist leer** — wir haben diese Schwellen nicht erhoben und
#: wissen von ihrem Autor nur, dass sie im Quelltext stehen.
GEERBTER_RAHMEN = Rahmen(
    slug="geerbt_altbestand",
    name="Altbestand (nur zum Vergleich)",
    luma_min=0.30,
    luma_max=0.65,
    hell_anteil_max=0.08,
    dunkel_anteil_max=0.12,
    streuung_min=0.10,
    gemessen=(),
    hell_grenze=0.98,
    dunkel_grenze=0.02,
    herkunft=(
        "Feste Konstanten aus archviz_exposure_check.py des Altbestands, ohne Angabe "
        "einer Messung. NICHT zum Gebrauch: Unser Hausstil-Mittelwert (0.0755 über 0.95) "
        "liegt knapp unter der Schwelle 0.08, plus eine Streuung deutlich darüber, und "
        "ein einzelnes Referenzwerk erreicht 0.3001. Eine Belichtungsschwelle ist keine "
        "Eigenschaft guter Belichtung, sondern eines Stils."
    ),
)

#: Stil-Kürzel → Rahmen. Ein Stil, der hier fehlt, bekommt **keinen Ersatzrahmen**,
#: sondern eine benannte Lücke — siehe :func:`rahmen_fuer`.
RAHMEN: dict[str, Rahmen] = {
    HAUSSTIL_RAHMEN.slug: HAUSSTIL_RAHMEN,
    MESS_RAHMEN.slug: MESS_RAHMEN,
    GEERBTER_RAHMEN.slug: GEERBTER_RAHMEN,
}


def rahmen_fuer(stil: str) -> Rahmen | None:
    """Den Rahmen zu einem Stil-Kürzel, oder ``None``.

    Gibt **ausdrücklich ``None``** statt eines Rückfalls auf den Hausstil zurück. Ein
    stillschweigend untergeschobener Rahmen wäre ein Urteil über einen Stil anhand der
    Zahlen eines anderen — und es stünde nirgends, dass es so war.
    """
    return RAHMEN.get(stil)


def messe(pfad, *, rahmen: "Rahmen | None" = None) -> dict:
    """Ein Bild vermessen — **ohne jedes Urteil**.

    Die Trennung ist Absicht: Die Messung hängt nur am Bild, das Urteil am Stil. Wer
    beides in einer Funktion hat, kann eine Messung nicht wiederverwenden, wenn sich der
    Stil ändert — und misst dann zweimal, statt einmal zu messen und zweimal zu urteilen.

    Args:
        pfad: Pfad zu einem PNG. Farbe ist der Normalfall; gerechnet wird die
            Rec.709-Luminanz (:func:`aiimaging.bildlesen.lies_png_luminanz`).
        rahmen: Wenn angegeben, werden die Anteile gegen **dessen** Hell- und
            Dunkelgrenze gezählt statt gegen die Vorgabe. Das ist der einzige Weg, die
            Anteile zweier Rahmen mit verschiedenen Grenzen sauber zu vergleichen — der
            geerbte Rahmen zählt über 0.98, unserer über 0.95, und ein Anteil über 0.98
            ist zwangsläufig kleiner. Ohne diesen Parameter meldet :func:`pruefe` den
            Unterschied als Warnung, statt ihn zu verschlucken.

    Returns:
        ``{pfad, breite, hoehe, pixel, luminanz, streuung, anteil_hell, anteil_dunkel,
        hell_grenze, dunkel_grenze}``. ``anteil_*`` sind **Anteile von 0 bis 1**, keine
        Prozentzahlen — der Altbestand rechnet in Prozent, und zwei Einheiten für
        dieselbe Grösse sind eine Fehlerquelle ohne jeden Gegenwert.

    Raises:
        BelichtungsError: Das Bild lässt sich nicht lesen. Die ursprüngliche Meldung des
            Lesers bleibt erhalten — sie sagt genauer, was fehlt.
    """
    try:
        werte, breite, hoehe = bildlesen.lies_png_luminanz(pfad)
    except bildlesen.BildError as fehler:
        raise BelichtungsError(f"Belichtung nicht messbar: {fehler}") from fehler

    n = len(werte)
    if n == 0:
        raise BelichtungsError(f"{pfad}: kein einziges Pixel.")

    hell_grenze = HELL_GRENZE if rahmen is None else rahmen.hell_grenze
    dunkel_grenze = DUNKEL_GRENZE if rahmen is None else rahmen.dunkel_grenze

    mittel = sum(werte) / n
    # Zwei Durchläufe statt der Summenformel: Bei einem grossen, sehr hellen Bild
    # verliert `E[x²] - E[x]²` genau dort Stellen, wo die Streuung klein ist — also im
    # Fall „flaches Bild", den wir messen wollen.
    streuung = math.sqrt(sum((w - mittel) ** 2 for w in werte) / n)
    hell = sum(1 for w in werte if w > hell_grenze) / n
    dunkel = sum(1 for w in werte if w < dunkel_grenze) / n

    return {
        "pfad": str(pfad),
        "breite": breite,
        "hoehe": hoehe,
        "pixel": n,
        "luminanz": mittel,
        "streuung": streuung,
        "anteil_hell": hell,
        "anteil_dunkel": dunkel,
        "hell_grenze": hell_grenze,
        "dunkel_grenze": dunkel_grenze,
    }


def _befund(art: str, feld: str, rahmen: Rahmen, detail: str) -> dict:
    """Ein einzelner Befund — mit der Schwere, die die Herkunft der Schwelle zulässt."""
    schwer = rahmen.ist_gemessen(feld)
    return {
        "befund": art,
        "feld": feld,
        "schwere": SCHWERE_FEHLER if schwer else SCHWERE_WARN,
        "gemessen": schwer,
        "detail": detail if schwer else (
            f"{detail} — die Schwelle für '{feld}' ist bei diesem Rahmen NICHT gemessen, "
            f"der Befund bleibt darum eine Warnung und wird kein Fehler."
        ),
    }


def pruefe(messung: dict, rahmen: Rahmen) -> dict:
    """Eine Messung gegen einen Rahmen halten.

    Args:
        messung: Antwort von :func:`messe`.
        rahmen: der Massstab. Kein Vorgabewert — welcher Stil gilt, weiss der Aufrufer
            und nicht dieses Modul.

    Returns:
        ``{stil, rahmen_name, herkunft, befunde, schwere, bestanden, zusammenfassung,
        messung}``.

        ``befunde`` ist **leer, wenn nichts auffällt**, und nach Schwere sortiert. Alle
        Befunde stehen darin, nicht nur der erste — der Altbestand meldet nur den
        wichtigsten (``issues[0]``), und ein Bild, das gleichzeitig zu hell und zu flach
        ist, sieht dort aus wie eines, das nur zu hell ist.

    Der Rückgabewert trägt **kein einzelnes „OK"**. ``bestanden`` ist ``True``, wenn kein
    Befund die Schwere ``error`` hat — Warnungen halten nichts auf. Wer strenger sein
    will, liest ``befunde`` und entscheidet selbst; das ist billiger als ein zweiter
    Schalter, den irgendwann niemand mehr richtig setzt.
    """
    if not isinstance(rahmen, Rahmen):
        raise BelichtungsError(
            f"pruefe erwartet einen Rahmen, bekam {type(rahmen).__name__}. Ein "
            f"Wörterbuch mit denselben Feldern täte es nicht — der Rahmen prüft seine "
            f"Zahlen beim Bauen, ein Wörterbuch nicht."
        )
    for feld in ("luminanz", "streuung", "anteil_hell", "anteil_dunkel"):
        if feld not in messung:
            raise BelichtungsError(
                f"Der Messung fehlt '{feld}' — sie stammt nicht aus messe()."
            )

    befunde: list[dict] = []
    luma = float(messung["luminanz"])
    hell = float(messung["anteil_hell"])
    dunkel = float(messung["anteil_dunkel"])
    streuung = float(messung["streuung"])

    passende_grenzen = (
        math.isclose(messung.get("hell_grenze", HELL_GRENZE), rahmen.hell_grenze)
        and math.isclose(messung.get("dunkel_grenze", DUNKEL_GRENZE), rahmen.dunkel_grenze)
    )
    if not passende_grenzen:
        befunde.append({
            "befund": "grenzen-weichen-ab",
            "feld": "hell_grenze",
            "schwere": SCHWERE_WARN,
            "gemessen": False,
            "detail": (
                f"Gemessen wurde gegen {messung.get('hell_grenze')}/"
                f"{messung.get('dunkel_grenze')}, der Rahmen erwartet "
                f"{rahmen.hell_grenze}/{rahmen.dunkel_grenze}. Die Anteile sind damit "
                f"NICHT vergleichbar — ein Anteil über 0.98 ist zwangsläufig kleiner als "
                f"einer über 0.95, und der Unterschied sieht aus wie ein besseres Bild."
            ),
        })

    if hell > rahmen.hell_anteil_max:
        befunde.append(_befund(
            "zu-viel-ausgefressen", "hell_anteil_max", rahmen,
            f"{hell:.1%} der Fläche liegen über {rahmen.hell_grenze} — der Rahmen "
            f"{rahmen.slug!r} lässt bis {rahmen.hell_anteil_max:.1%} zu."))
    if dunkel > rahmen.dunkel_anteil_max:
        befunde.append(_befund(
            "zu-viel-zugelaufen", "dunkel_anteil_max", rahmen,
            f"{dunkel:.1%} der Fläche liegen unter {rahmen.dunkel_grenze} — der Rahmen "
            f"lässt bis {rahmen.dunkel_anteil_max:.1%} zu."))
    if luma > rahmen.luma_max:
        befunde.append(_befund(
            "zu-hell", "luma_max", rahmen,
            f"Mittlere Helligkeit {luma:.3f} über {rahmen.luma_max:.3f}."))
    elif luma < rahmen.luma_min:
        befunde.append(_befund(
            "zu-dunkel", "luma_min", rahmen,
            f"Mittlere Helligkeit {luma:.3f} unter {rahmen.luma_min:.3f}."))
    if streuung < rahmen.streuung_min:
        befunde.append(_befund(
            "flach", "streuung_min", rahmen,
            f"Streuung {streuung:.3f} unter {rahmen.streuung_min:.3f} — das Bild hat "
            f"wenig Zeichnung."))

    rang = {SCHWERE_FEHLER: 0, SCHWERE_WARN: 1, SCHWERE_OK: 2}
    befunde.sort(key=lambda b: (rang[b["schwere"]], b["feld"]))
    fehler = [b for b in befunde if b["schwere"] == SCHWERE_FEHLER]
    schwere = SCHWERE_FEHLER if fehler else (SCHWERE_WARN if befunde else SCHWERE_OK)

    if not befunde:
        zusammenfassung = (
            f"Belichtung im Rahmen {rahmen.slug!r}: Helligkeit {luma:.3f}, "
            f"{hell:.1%} über {rahmen.hell_grenze}, Streuung {streuung:.3f}."
        )
    else:
        zusammenfassung = "; ".join(b["detail"].split(" — ")[0] for b in befunde)

    return {
        "stil": rahmen.slug,
        "rahmen_name": rahmen.name,
        "herkunft": rahmen.herkunft,
        "befunde": tuple(befunde),
        "schwere": schwere,
        "bestanden": not fehler,
        "zusammenfassung": zusammenfassung,
        "messung": messung,
    }


def pruefe_bild(pfad, rahmen: Rahmen) -> dict:
    """Messen und urteilen in einem Griff — **gegen die Grenzen des Rahmens**.

    Bequemlichkeit, kein eigener Begriff. Wer die Messung wiederverwenden will, ruft
    :func:`messe` und :func:`pruefe` getrennt.
    """
    return pruefe(messe(pfad, rahmen=rahmen), rahmen)


# ======================================================================================
# Überstrahlung — wieviel des Hauses ist voll weiss? (auf-20261020-292, B1)
# ======================================================================================

#: Ab wann ein Bildpunkt als «voll weiss» zählt: alle drei Kanäle auf 255 (8 Bit). Dort trägt
#: der Punkt keine Zeichnung mehr — er sagt nur noch «hell», nicht mehr, was dort ist.
VOLL_WEISS = 255

#: Das Ziel der Stimmungen am Haus: weniger als 1 % voll weisse Bildpunkte (auf-20261020-292).
UEBERSTRAHLT_ZIEL = 0.01


def ueberstrahlt_anteil(farben, *, maske=None, schwelle: int = VOLL_WEISS) -> dict:
    """Der Anteil voll weisser Bildpunkte — am Haus, wenn eine Maske da ist.

    **Anlass (auf-20261020-292, B1):** Bei «mittag» war das Haus eine rein weisse Fläche
    (11,9 % der Bildpunkte = 255), ohne Kanten. Gemessen wird ohne Urteil über den Stil
    (siehe Moduldocstring): Die Zahl sagt, wieviel Zeichnung verloren ist; ob das Absicht
    ist, sagt sie nicht.

    Args:
        farben: ``[(r, g, b), …]`` in 0..255 (:func:`aiimaging.bildlesen.lies_png_farben`).
        maske: gleich lange Folge von Wahrheitswerten (die Bauwerksmaske) — ``None``: das
            ganze Bild.
        schwelle: ab welchem Wert ein Kanal als voll gilt (Vorgabe 255).

    Returns:
        ``{anteil, anteil_bild, n_weiss, n, schwelle, bezug, ziel, unter_ziel}`` — ``anteil``
        bezogen auf ``bezug`` (``"bauwerk"`` oder ``"bild"``); ``None`` bei leerer Maske.
    """
    farben = list(farben)
    n_bild = len(farben)
    if n_bild == 0:
        raise BelichtungsError("Überstrahlung nicht messbar: kein einziger Bildpunkt.")
    weiss = [min(p[0], p[1], p[2]) >= schwelle for p in farben]
    anteil_bild = sum(weiss) / n_bild
    if maske is not None:
        maske = list(maske)
        if len(maske) != n_bild:
            raise BelichtungsError(f"Überstrahlung: Maske mit {len(maske)} Punkten zu einem "
                                   f"Bild mit {n_bild}.")
        n = sum(1 for m in maske if m)
        n_weiss = sum(1 for w, m in zip(weiss, maske) if w and m)
        bezug = "bauwerk"
    else:
        n, n_weiss, bezug = n_bild, sum(weiss), "bild"
    anteil = (n_weiss / n) if n else None
    return {"anteil": None if anteil is None else round(anteil, 6),
            "anteil_bild": round(anteil_bild, 6), "n_weiss": n_weiss, "n": n,
            "schwelle": schwelle, "bezug": bezug, "ziel": UEBERSTRAHLT_ZIEL,
            "unter_ziel": None if anteil is None else anteil < UEBERSTRAHLT_ZIEL}


def ueberstrahlt_aus_png(pfad, *, maske=None) -> dict:
    """:func:`ueberstrahlt_anteil` für eine PNG-Datei — nie eine Ausnahme.

    Nicht messbar (Datei fehlt, unlesbar, Maske passt nicht): ``{anteil: None, grund}``. Eine
    Auskunft neben dem Bild ist kein Grund, ein gerechnetes Bild scheitern zu lassen.
    """
    if not pfad:
        return {"anteil": None, "grund": "Kein Schönbild — nicht gemessen."}
    try:
        farben, _b, _h = bildlesen.lies_png_farben(pfad)
        befund = ueberstrahlt_anteil(farben, maske=maske)
    except (bildlesen.BildError, BelichtungsError, OSError, ValueError) as fehler:
        return {"anteil": None, "grund": f"Überstrahlung nicht messbar: {fehler}"}
    befund["grund"] = "" if befund["anteil"] is not None else "Leere Bauwerksmaske."
    return befund


# ======================================================================================
# Kontrast Haus – Hintergrund — hebt sich das Haus ab? (auf-20261020-293, Punkt 1)
# ======================================================================================

#: Ab welcher Differenz (Grauwerte 0..255) das Haus als sichtbar gilt — dieselbe Zahl wie
#: ``stimmung.KONTRAST_SCHWELLE`` (dort begründet), hier wiederholt, damit dieses Modul ohne
#: ``stimmung`` auskommt; eine Probe hält beide gleich.
KONTRAST_SCHWELLE = 20.0

#: Ab welchem Kontrast AM UMRISS (:func:`kontrast_am_umriss`, ``betrag``, 0..255) das Haus als
#: sichtbar gilt. **Die Warnung «HAUS KAUM SICHTBAR» hängt seit Ergebnis auf-20261023-344
#: (K4) an dieser Zahl**, nicht mehr am Mittelwert: Mittags war das Haus von Auge klar zu
#: sehen, Mittel −19,6 / −5,0, Umriss 51,7 / 54,3 — Sonnenseite (114/150), Schattenseite,
#: Dach und Fenster mitteln sich auf den Hintergrund (106/108).
#:
#: **Woher die 15 — nachgerechnet, nicht am Gerät gemessen.** Die einzigen Fälle mit echtem
#: «kaum sichtbar» sind die acht Stimmungen aus auf-20261020-293 (Bilder im Repo,
#: ``auftraege/ergebnisse/auf-20261020-293-bilder/1-stimmung-*-sSE.png``). Ihr ID-Pass liegt
#: nicht im Repo; die Hausmaske ist darum aus dem kontrastreichen Abendbild derselben Kamera
#: geschnitten und auf alle acht gelegt (Mittelwerte damit auf 0,7–4 Grauwerte an den
#: gemeldeten). Umriss nach Augenurteil der HomeStation: winter 0,9 («praktisch
#: unsichtbar»), morgen 4,2 («verschwimmt fast»), nebel 6,1 («verschwimmt leicht»), bedeckt
#: 7,5 («Kanten schwach»), blaue Stunde 10,0 («nur schwach abgesetzt») — gegen abend 18,0
#: («lesbar»), weiss 19,2 («gut lesbar»), mittag 61,4 und 344 50,4–71,0 («klar zu sehen»).
#: Die Grenze liegt zwischen 10 und 18; 15 ist die Mitte. Die alte 20 hätte abend und weiss
#: fälschlich gewarnt. Die Probe ``tests/test_umriss_warnung_344.py`` rechnet es nach.
KONTRAST_UMRISS_SCHWELLE = 15.0
#: Woher :data:`KONTRAST_UMRISS_SCHWELLE` kommt — für Protokoll und Proben.
KONTRAST_UMRISS_HERKUNFT = ("nachgerechnet an den Bildern von auf-20261020-293 (Maske aus dem "
                            "Abendbild, nicht aus dem ID-Pass) und an auf-20261023-344; "
                            "nicht am Geraet gemessen")


def haus_kaum_sichtbar(mittel, umriss) -> tuple[bool | None, str]:
    """Ist das Haus kaum sichtbar? → ``(urteil, regel)`` mit ``regel`` ``"umriss"``,
    ``"mittelwert"`` oder ``""``.

    Es gilt der Kontrast am Umriss (:data:`KONTRAST_UMRISS_SCHWELLE`), weil er das Auge trifft
    (Ergebnis auf-20261023-344, K4). **Fehlt er** — alte Läufe vor 343, Haus grenzt nirgends
    an Hintergrund, Messung fehlgeschlagen —, gilt als Rückfall der Mittelwert
    (:data:`KONTRAST_SCHWELLE`), wie bis 344. Fehlen beide: ``(None, "")``.
    """
    def zahl(w):
        return isinstance(w, (int, float)) and not isinstance(w, bool)
    if zahl(umriss):
        return abs(umriss) < KONTRAST_UMRISS_SCHWELLE, "umriss"
    if zahl(mittel):
        return abs(mittel) < KONTRAST_SCHWELLE, "mittelwert"
    return None, ""

#: Wie weit «daneben» reicht: der Rahmen um das Haus, je Seite um diesen Anteil seiner
#: Breite bzw. Höhe vergrössert. Nur der Himmel in diesem Rahmen zählt — der Himmel in einer
#: fernen Bildecke sagt nicht, ob sich das Haus vor SEINEM Hintergrund abhebt.
KONTRAST_RAND = 0.5


def _grauwert(p) -> float:
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def kontrast_haus_hintergrund(farben, breite: int, hoehe: int, *, haus, hintergrund,
                              rand: float = KONTRAST_RAND,
                              schwelle: float = KONTRAST_SCHWELLE) -> dict:
    """Wie stark sich das Haus vom Hintergrund daneben abhebt — mittlerer Grauwert, Differenz.

    **Anlass (auf-20261020-293):** Bei winter (−0,5), morgen (−1,3), nebel (−7,5) und
    bedeckt (−8,6) war das Haus im Cycles-Bild praktisch unsichtbar; die HomeStation hat es
    von Hand nachgezählt. Jetzt steht die Zahl im Ergebnis.

    Args:
        farben: ``[(r, g, b), …]`` in 0..255 (das Cycles-Bild), zeilenweise von oben.
        haus: gleich lange Folge von Wahrheitswerten — die Bauwerksmaske.
        hintergrund: gleich lange Folge — wo die Kamera den Himmel sieht (im Material-ID-Pass
            schwarz: kein Objekt).
        rand: wie weit «daneben» reicht (:data:`KONTRAST_RAND`).

    Returns:
        ``{kontrast, haus, hintergrund, n_haus, n_hintergrund, schwelle, kaum_sichtbar,
        kaum_sichtbar_regel, kaum_sichtbar_mittelwert, grund, umriss}`` — ``kontrast`` = Haus
        minus Hintergrund (positiv: Haus heller); ``None`` mit ``grund``, wenn eine der beiden
        Flächen leer ist. ``kaum_sichtbar`` ist das Urteil von :func:`haus_kaum_sichtbar`
        (Umriss, Rückfall Mittelwert; ``kaum_sichtbar_regel`` sagt, welche Zahl galt) —
        dasselbe, an dem die Warnung hängt. ``kaum_sichtbar_mittelwert`` ist die Antwort des
        Mittelwerts allein (bis Ergebnis auf-20261023-345 der Schalter), nur als Auskunft.
    """
    farben = list(farben)
    n = len(farben)
    breite, hoehe = int(breite), int(hoehe)
    haus, hintergrund = list(haus), list(hintergrund)
    if n == 0 or breite * hoehe != n or len(haus) != n or len(hintergrund) != n:
        raise BelichtungsError(
            f"Kontrast: Bild {breite} x {hoehe} mit {n} Punkten, Maske {len(haus)}, "
            f"Hintergrund {len(hintergrund)} — passen nicht zusammen.")
    leer = {"kontrast": None, "haus": None, "hintergrund": None, "n_haus": 0,
            "n_hintergrund": 0, "schwelle": schwelle, "kaum_sichtbar": None}
    punkte = [i for i, m in enumerate(haus) if m]
    if not punkte:
        return dict(leer, grund="Leere Bauwerksmaske — kein Haus im Bild.")
    xs = [i % breite for i in punkte]
    ys = [i // breite for i in punkte]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    dx, dy = int((x1 - x0 + 1) * rand), int((y1 - y0 + 1) * rand)
    x0, x1 = max(0, x0 - dx), min(breite - 1, x1 + dx)
    y0, y1 = max(0, y0 - dy), min(hoehe - 1, y1 + dy)
    daneben = [y * breite + x for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
               if hintergrund[y * breite + x] and not haus[y * breite + x]]
    mittel_haus = sum(_grauwert(farben[i]) for i in punkte) / len(punkte)
    if not daneben:
        return dict(leer, haus=round(mittel_haus, 1), n_haus=len(punkte),
                    grund="Kein Himmel neben dem Haus (Haus füllt den Rahmen, oder Blick von "
                          "oben) — nicht gemessen.")
    mittel_grund = sum(_grauwert(farben[i]) for i in daneben) / len(daneben)
    kontrast = mittel_haus - mittel_grund
    umriss = kontrast_am_umriss(farben, breite, hoehe, haus=haus, hintergrund=hintergrund)
    # DER SCHALTER FOLGT DEMSELBEN URTEIL WIE DIE WARNUNG (Ergebnis auf-20261023-345, S7):
    # Bis dahin stand hier der Mittelwert allein — am echten R57-Export `kaum_sichtbar: true`
    # bei Mittel −15,7, während die Warnung am Umriss (55,5) richtig schwieg. Zwei Antworten
    # auf eine Frage im selben Befund. Jetzt `haus_kaum_sichtbar` (Umriss, Rückfall
    # Mittelwert); die Mittelwertantwort bleibt als Auskunft daneben.
    kaum, regel = haus_kaum_sichtbar(round(kontrast, 1), umriss.get("betrag"))
    if regel == "mittelwert":                   # die übergebene Schwelle gilt im Rückfall
        kaum = abs(kontrast) < schwelle
    return {"kontrast": round(kontrast, 1), "haus": round(mittel_haus, 1),
            "hintergrund": round(mittel_grund, 1), "n_haus": len(punkte),
            "n_hintergrund": len(daneben), "schwelle": schwelle,
            "kaum_sichtbar": kaum, "kaum_sichtbar_regel": regel,
            "kaum_sichtbar_mittelwert": abs(kontrast) < schwelle, "grund": "",
            "umriss": umriss}


def kontrast_am_umriss(farben, breite: int, hoehe: int, *, haus, hintergrund) -> dict:
    """Der Kontrast **am Umriss** — je Kantenstelle ein Hauspunkt innen gegen einen
    Hintergrundpunkt aussen, im Betrag gemittelt.

    **Anlass (Ergebnis auf-20261023-343, 5):** «HAUS KAUM SICHTBAR» stand in allen fünf Läufen,
    von Auge war das Haus ganz zu sehen. :func:`kontrast_haus_hintergrund` vergleicht
    MITTELWERTE: das ganze Haus (Sonnen- und Schattenseiten, dunkle Fenster) gegen den ganzen
    Hintergrund im Rahmen (Himmel, Dunst, die Bodenfortsetzung hinter der Platte). Ein Haus mit
    heller Sonnen- und dunkler Schattenseite vor mittelgrauem Himmel hat dort fast null —
    und ist doch deutlich zu sehen. Und bei gleichem Licht und gleichen Fassaden ergab dieselbe
    Blickrichtung −19,6 (Haus 21 % des Bilds) und −9,4 (Haus 69 %): Die Zahl hängt am
    Ausschnitt. Das Auge sieht das Haus an seiner Kante.

    Gemessen wird an jeder Stelle, an der ein Hauspunkt waagrecht oder senkrecht an
    Hintergrund grenzt: der Hauspunkt einen Schritt nach innen gegen den Hintergrundpunkt zwei
    Schritte nach aussen — der Punkt direkt an der Kante bleibt beidseits aussen vor, ihn mischt
    die Kantenglättung. ``betrag`` ist das Mittel der Beträge (beide Vorzeichen zählen als
    sichtbar), ``kontrast`` das Mittel mit Vorzeichen. **Seit Ergebnis auf-20261023-344 (K4)
    trägt diese Zahl die Warnung** (:func:`haus_kaum_sichtbar`, :data:`KONTRAST_UMRISS_SCHWELLE`);
    die Mittelwertzahl wird weiter berichtet und dient als Rückfall, wo der Umriss fehlt.

    Returns:
        ``{betrag, kontrast, n_stellen, grund}`` — ``None`` mit ``grund``, wenn das Haus nirgends
        an Hintergrund grenzt (füllt das Bild, steht nur vor Gelände).
    """
    breite, hoehe = int(breite), int(hoehe)
    unterschiede = []

    def grund_an(j):
        return hintergrund[j] and not haus[j]

    for i, m in enumerate(haus):
        if not m:
            continue
        x, y = i % breite, i // breite
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xi, yi = x - dx, y - dy                      # einen Schritt nach innen
            xa, ya = x + 2 * dx, y + 2 * dy              # zwei Schritte nach aussen
            if not (0 <= xi < breite and 0 <= yi < hoehe and 0 <= xa < breite
                    and 0 <= ya < hoehe):
                continue
            innen, kante, aussen = yi * breite + xi, (y + dy) * breite + (x + dx), ya * breite + xa
            if haus[innen] and grund_an(kante) and grund_an(aussen):
                unterschiede.append(_grauwert(farben[innen]) - _grauwert(farben[aussen]))
    if not unterschiede:
        return {"betrag": None, "kontrast": None, "n_stellen": 0,
                "grund": "Das Haus grenzt nirgends an Hintergrund — am Umriss nicht gemessen."}
    n = len(unterschiede)
    return {"betrag": round(sum(abs(d) for d in unterschiede) / n, 1),
            "kontrast": round(sum(unterschiede) / n, 1), "n_stellen": n, "grund": ""}


def kontrast_aus_pngs(schoen_png, material_id_png, *, maske) -> dict:
    """:func:`kontrast_haus_hintergrund` für das Cycles-Bild und seinen ID-Pass — nie eine Ausnahme.

    Hintergrund ist, wo der Material-ID-Pass schwarz ist (der Runner rechnet ihn vor
    schwarzem Grund, Farbwert 0 = «nichts»). Nicht messbar: ``{kontrast: None, grund}``.
    """
    if not schoen_png:
        return {"kontrast": None, "grund": "Kein Schönbild — nicht gemessen."}
    if not material_id_png or maske is None:
        return {"kontrast": None, "grund": "Ohne ID-Pass und Bauwerksmaske nicht messbar."}
    try:
        farben, b, h = bildlesen.lies_png_farben(schoen_png)
        kennung, kb, kh = bildlesen.lies_png_farben(material_id_png)
        if (kb, kh) != (b, h):
            raise BelichtungsError(f"Schönbild {b} x {h}, ID-Pass {kb} x {kh}.")
        himmel = [p[0] == 0 and p[1] == 0 and p[2] == 0 for p in kennung]
        return kontrast_haus_hintergrund(farben, b, h, haus=maske, hintergrund=himmel)
    except (bildlesen.BildError, BelichtungsError, OSError, ValueError) as fehler:
        return {"kontrast": None, "grund": f"Kontrast nicht messbar: {fehler}"}
