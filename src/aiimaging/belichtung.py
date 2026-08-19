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
