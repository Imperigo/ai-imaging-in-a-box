"""VARIANTEN — mehrere Bilder zu einem Auftrag, und die Frage, ab wann ein Unterschied einer ist.

Warum das nicht der geerbte Variantenbewerter wird
---------------------------------------------------
Der Altbestand hat einen (``archviz_variant_scorer.py``, gelesen am 20.08.2026). Er
gewichtet vier Kennzahlen zu einem ``final``-Wert von 0 bis 100. Zwei Dinge daran sind
Fehler, die wir nicht wiederholen:

**Erstens normalisiert er min-max INNERHALB DER CHARGE.** Die beste Variante bekommt ~100
und die schlechteste ~0 — *auch wenn alle fünf unbrauchbar sind*. Bei einer einzelnen
Variante gibt es pauschal 50, unabhängig vom Bild.

    Eine Zahl, die absolut aussieht und eine Rangfolge ist, ist schlimmer als keine Zahl.

Zwei Chargen sind damit nicht vergleichbar, und „87 von 100" bedeutet nichts.

**Zweitens gewichtet er Schärfe mit 0.50.** Die Hälfte des Urteils hängt an der
Laplace-Varianz. Ein Nebel- oder Skizzenstil bekommt damit systematisch den schlechtesten
Platz — nicht weil er misslungen wäre, sondern weil er weich ist. Das ist derselbe Fehler
wie bei seiner Belichtungsprüfung, nur an einer anderen Achse: **ein Massstab, der einen
Stil für die Wahrheit hält.**

Dieses Modul bewertet darum **gar nicht neu**. Wir haben bereits Masse, die *absolut* sind
und deren Schwellen *gemessen* wurden: :mod:`aiimaging.geometrie_qa` (Score in ``[0,1]``,
Schwelle 0.65 am Gerät erhoben) und :mod:`aiimaging.belichtung` (Rahmen je Stil). Was
fehlte, ist die **Reihe** — und die Frage, ab wann ein Unterschied zwischen zwei Bildern
überhaupt einer ist.

Die zwei Reihenarten, und ihre Verwechslung macht beide wertlos
----------------------------------------------------------------
* Eine **Saatreihe** ändert **nur den Seed**. Sie misst, wie stark der Zufall allein
  streut — den **Rauschboden** der Kette.
* Eine **kontrollierte Reihe** ändert **genau eine** Grösse und hält den Seed **fest**.
  Sie misst die Wirkung dieser Grösse.

Wer beides mischt — mehrere Seeds *und* mehrere Stärken —, kann einen Unterschied keiner
Ursache mehr zuordnen. :func:`kontrollierte_reihe` weigert sich darum, den Seed mitlaufen
zu lassen.

Und daraus folgt die eigentliche Leistung dieses Moduls:

    **Ein Unterschied ist erst dann einer, wenn er den Rauschboden übersteigt.**

Das ist dieselbe Denkweise, mit der ``stil_qa`` seine Schwelle bekommen hat: Dort wurde
erst der Boden von SigLIP 2 gemessen (0.526), und erst danach war eine Schwelle darüber
überhaupt sinnvoll. Hier ist der Boden die Streuung über den Seed.
:func:`ist_unterschied_belegt` ist die Anwendung davon — und sie sagt ``False``, wo sie es
nicht weiss.

Abhängigkeiten: stdlib und :mod:`aiimaging.render`. Kein ``bpy``, kein ``torch``, keine
Oberfläche (Regeln 2 und 4). Rendern und Bewerten sind hereingereicht.
"""
from __future__ import annotations

import dataclasses
import math
from collections.abc import Sequence

from . import render

#: Wie viele Streuungen ein Unterschied gross sein muss, um als belegt zu gelten.
#:
#: **Zwei**, dieselbe Zahl wie ``stil_qa.K_STREUUNGEN`` — nicht aus Bequemlichkeit,
#: sondern damit dieses Projekt nicht zwei verschiedene Begriffe von „deutlich mehr als
#: Zufall" führt. Wer sie ändert, ändert sie an beiden Stellen oder begründet, warum
#: nicht.
K_STREUUNGEN = 2.0

#: Kleinste Saatreihe, aus der sich eine Streuung überhaupt schätzen lässt.
#:
#: Drei ist wenig und ehrlich wenig: Aus zwei Werten lässt sich eine Streuung ausrechnen,
#: aber sie sagt nichts. Unter dieser Zahl gibt :func:`rauschboden` ``None`` zurück und
#: **nicht** eine kleine Zahl, die nach Genauigkeit aussieht.
MIN_SAATREIHE = 3

#: Die **gemessene** Streuung über Startwerte bei sonst gleichen Einstellungen.
#:
#: Neun Läufe, derselbe Aufbau, nur der Startwert verschieden: Mittel −0.6644,
#: Standardabweichung **0.2269** (`docs/POLARITAET_UND_STAERKE_2026-08-22.md`,
#: 22.08.2026). Drei der neun erreichten die Schwelle, sechs nicht.
#:
#: Die Zahl stand bisher an **neun** Stellen dieses Repos in Prosa und an keiner als
#: Wert. Eine gemessene Grösse, die nur in Kommentaren lebt, kann nicht rechnen und
#: veraltet an acht Stellen gleichzeitig — darum steht sie jetzt hier.
#:
#: **Wozu sie NICHT taugt:** als Rauschboden für eine Reihe, die man gerade selbst
#: gemessen hat. Wer die Streuung derselben drei Werte benutzt, um deren Bestwert gegen
#: sie zu prüfen, prüft im Kreis. Diese Zahl ist ein **unabhängiger** Massstab, weil sie
#: aus einer anderen Reihe stammt — und genau deshalb ist sie brauchbar.
#:
#: Ihre Grenze gehört dazu: Sie ist an *einem* Aufbau gemessen. Ob sie für einen anderen
#: gilt, ist ungemessen. Sie taugt als Grössenordnung, nicht als Naturkonstante.
#:
#: .. danger::
#:    **Und seit dem 24.08.2026 ist gemessen, dass sie der KAMERALAGE gehört und nicht der
#:    Kette** (HomeStation, Nachtrag zu `auf-13`): *«Am selben Standort und Füllgrad, nur
#:    mit anderer Achsenlage, ist die Startwertstreuung 0,0088 gegen 0,1216 — Faktor 14.»*
#:
#:    Das ist dieselbe Fehlerart wie bei
#:    :data:`aiimaging.geometrie_qa.RAUSCHBODEN_UEBER_MASKE`, und sie hat dieselbe Ursache:
#:    das **Ortsfeld** des Tiefenschätzers. Eine Zahl, die man für eine Eigenschaft der
#:    Kette hält, ist eine Eigenschaft der Bildlage.
#:
#:    **Was daraus folgt:** Diese Zahl ist eine **Grössenordnung** und darf nicht als
#:    allgemeiner Rauschboden verrechnet werden. Wo es auf den Vergleich ankommt, gehört
#:    die Streuung **derselben Kameralage** gemessen — die Seedreihe läuft ohnehin je
#:    Kamera. Ausdrücklich gilt das auch für die 0,3155 aus `auf-35`.
GEMESSENE_SEED_STREUUNG = 0.2269

#: Der Rauschboden aus :data:`GEMESSENE_SEED_STREUUNG`, in der Form, die
#: :func:`ist_unterschied_belegt` erwartet.
GEMESSENER_BODEN = {
    "n": 9, "n_ungemessen": 0, "mittel": -0.6644,
    "streuung": GEMESSENE_SEED_STREUUNG, "spanne": None, "belastbar": True,
    "begruendung": ("9 Läufe desselben Aufbaus, nur der Startwert verschieden: Mittel "
                    "-0.664, Streuung 0.227 (POLARITAET_UND_STAERKE_2026-08-22.md). "
                    "UNABHÄNGIG von der Reihe, gegen die hier geprüft wird. ACHTUNG: "
                    "Diese Streuung gehört der KAMERALAGE — an derselben Stelle mit "
                    "anderer Achsenlage sind es 0.0088 statt 0.1216, Faktor 14 "
                    "(24.08.2026). Als allgemeiner Boden ist sie ZU GROSS und weist "
                    "damit echte Unterschiede ab; wer sie benutzt, urteilt vorsichtig "
                    "und nicht falsch — aber er urteilt an der Lage vorbei."),
}

#: Die Felder eines Renderauftrags, die eine kontrollierte Reihe sinnvoll durchfahren kann.
#:
#: ``seed`` steht bewusst **nicht** darin — er ist der Gegenstand der Saatreihe, und ihn in
#: einer kontrollierten Reihe mitlaufen zu lassen hiesse, zwei Ursachen zugleich zu ändern.
#: ``ausgabe_png`` auch nicht: Das ist keine Grösse, sondern ein Ablageort.
FAHRBARE_FELDER = (
    "controlnet_staerke", "denoise", "fuehrung", "schritte", "prompt",
    "negativ_prompt", "backbone",
)


class VariantenError(ValueError):
    """Eine Reihe ist nicht sinnvoll gebaut. Erbt von ``ValueError`` wie alles hier."""


# ======================================================================================
# Reihen bauen
# ======================================================================================

def saatreihe(basis: render.RenderAuftrag, anzahl: int, *,
              erster_seed: int | None = None) -> list[render.RenderAuftrag]:
    """``anzahl`` Aufträge, die sich **nur im Seed** unterscheiden.

    Der Seed läuft von ``erster_seed`` aufwärts um eins — dieselbe Vorschrift wie im
    Altbestand (``seed = basis + nummer``), und sie ist gut: Sie ist wiederholbar,
    lückenlos und aus dem Bericht ablesbar.

    Args:
        basis: der Auftrag, dessen Seed durchgezählt wird.
        anzahl: wie viele. Muss positiv sein.
        erster_seed: Startwert. ``None`` nimmt den Seed des Basisauftrags.

    Die Ausgabepfade werden **durchnummeriert**, sonst überschriebe jede Variante die
    vorige — und am Ende läge ein Bild da, wo fünf erwartet werden.

    Raises:
        VariantenError: ``anzahl`` unbrauchbar, oder ein Seed fiele aus dem zulässigen
            Bereich. Ein überlaufender Seed wird **nicht** umgebrochen: Zwei Varianten mit
            demselben Seed wären dasselbe Bild unter zwei Namen.
    """
    _pruefe_anzahl(anzahl)
    start = basis.seed if erster_seed is None else erster_seed
    if isinstance(start, bool) or not isinstance(start, int):
        raise VariantenError(f"erster_seed muss eine ganze Zahl sein: {start!r}")
    letzter = start + anzahl - 1
    if start < 0 or letzter > render.MAX_SEED:
        raise VariantenError(
            f"Die Reihe liefe von {start} bis {letzter} und fiele damit aus dem "
            f"zulässigen Bereich 0..{render.MAX_SEED}. Umgebrochen wird NICHT — zwei "
            f"Varianten mit demselben Seed wären dasselbe Bild unter zwei Namen."
        )
    return [
        dataclasses.replace(basis, seed=start + i,
                            ausgabe_png=_nummeriert(basis.ausgabe_png, i))
        for i in range(anzahl)
    ]


def kontrollierte_reihe(basis: render.RenderAuftrag, feld: str,
                        werte: Sequence) -> list[render.RenderAuftrag]:
    """Aufträge, die sich in **genau einem** Feld unterscheiden — bei **festem Seed**.

    Der feste Seed ist der ganze Punkt. Läuft er mit, ist ein Unterschied zwischen zwei
    Bildern nicht mehr zuzuordnen: Er könnte vom Parameter kommen oder vom Zufall, und die
    Reihe beantwortet die Frage nicht, für die sie gefahren wurde.

    Args:
        feld: Name eines Felds aus :data:`FAHRBARE_FELDER`.
        werte: die Werte, die durchfahren werden. Mindestens zwei — eine Reihe aus einem
            Wert ist keine Reihe, sondern ein Lauf.

    Raises:
        VariantenError: unbekanntes oder nicht fahrbares Feld, zu wenige Werte, oder
            doppelte Werte. Ein doppelter Wert ergibt zweimal dasselbe Bild und sieht in
            der Auswertung wie eine Bestätigung aus.
    """
    if feld == "seed":
        raise VariantenError(
            "Der Seed gehört in eine SAATREIHE und nicht in eine kontrollierte Reihe. "
            "Läuft er hier mit, ändern sich zwei Ursachen zugleich, und ein Unterschied "
            "zwischen zwei Bildern lässt sich keiner von beiden zuordnen — die Reihe "
            "beantwortet dann die Frage nicht, für die sie gefahren wurde."
        )
    if feld not in FAHRBARE_FELDER:
        bekannt = {f.name for f in dataclasses.fields(render.RenderAuftrag)}
        if feld in bekannt:
            raise VariantenError(
                f"{feld!r} ist ein Feld des Auftrags, aber keine Grösse, die man sinnvoll "
                f"durchfährt. Fahrbar sind: {', '.join(FAHRBARE_FELDER)}."
            )
        raise VariantenError(
            f"{feld!r} ist kein Feld eines Renderauftrags. Fahrbar sind: "
            f"{', '.join(FAHRBARE_FELDER)}."
        )
    werte = list(werte)
    if len(werte) < 2:
        raise VariantenError(
            f"Eine Reihe über {feld!r} braucht mindestens zwei Werte, bekam {len(werte)}. "
            f"Ein einzelner Wert ist keine Reihe, sondern ein Lauf."
        )
    doppelt = [w for i, w in enumerate(werte) if w in werte[:i]]
    if doppelt:
        raise VariantenError(
            f"Doppelte Werte in der Reihe über {feld!r}: {doppelt}. Bei festem Seed ergibt "
            f"derselbe Wert zweimal dasselbe Bild — in der Auswertung sähe das wie eine "
            f"Bestätigung aus und ist keine."
        )
    return [
        dataclasses.replace(basis, **{feld: wert},
                            ausgabe_png=_nummeriert(basis.ausgabe_png, i))
        for i, wert in enumerate(werte)
    ]


def _pruefe_anzahl(anzahl) -> None:
    if isinstance(anzahl, bool) or not isinstance(anzahl, int):
        raise VariantenError(f"anzahl muss eine ganze Zahl sein: {anzahl!r}")
    if anzahl < 1:
        raise VariantenError(f"anzahl muss mindestens 1 sein, war {anzahl}.")


def _nummeriert(pfad, i: int):
    """``bild.png`` → ``bild_00.png``. ``None`` bleibt ``None`` — dann wählt der Renderer."""
    if not pfad:
        return None
    text = str(pfad)
    if "." in text.rsplit("/", 1)[-1]:
        stamm, punkt, endung = text.rpartition(".")
        return f"{stamm}_{i:02d}{punkt}{endung}"
    return f"{text}_{i:02d}"


# ======================================================================================
# Der Rauschboden — das eigentliche Werkzeug
# ======================================================================================

def rauschboden(werte: Sequence[float | None]) -> dict:
    """Wie stark streut eine Saatreihe **bei sonst gleichen Parametern**?

    Das ist der Massstab, an dem sich jeder spätere Unterschied messen lassen muss: Was
    innerhalb dieser Streuung liegt, ist Zufall und kein Befund.

    Dieselbe Denkweise, mit der ``stil_qa`` zu seiner Schwelle kam — dort wurde erst der
    Boden gemessen (0.526 an 4950 Bildpaaren), und erst danach war eine Schwelle darüber
    sinnvoll. Eine Schwelle unter dem Boden lässt alles durch, und ein Unterschied unter
    dem Rauschboden belegt nichts.

    Args:
        werte: die Scores der Saatreihe. ``None``-Einträge sind **ungemessene** Läufe und
            werden übersprungen — sie zählen aber in ``n_ungemessen``, damit niemand aus
            einer geschrumpften Reihe eine kleine Streuung liest.

    Returns:
        ``{n, n_ungemessen, mittel, streuung, spanne, belastbar, begruendung}``.
        ``streuung`` ist ``None``, wenn weniger als :data:`MIN_SAATREIHE` Werte vorliegen —
        **nicht** eine kleine Zahl, die nach Genauigkeit aussieht.
    """
    roh = list(werte)
    brauchbar = [float(w) for w in roh if w is not None]
    n = len(brauchbar)
    fehlend = len(roh) - n

    if n < MIN_SAATREIHE:
        return {
            "n": n, "n_ungemessen": fehlend, "mittel": None, "streuung": None,
            "spanne": None, "belastbar": False,
            "begruendung": (
                f"{n} messbare Läufe, mindestens {MIN_SAATREIHE} nötig. Aus weniger lässt "
                f"sich eine Streuung ausrechnen, aber sie sagt nichts — und eine Zahl, "
                f"die nichts sagt, wird hier nicht geliefert."
                + (f" {fehlend} Läufe waren ungemessen." if fehlend else "")
            ),
        }

    mittel = sum(brauchbar) / n
    streuung = math.sqrt(sum((w - mittel) ** 2 for w in brauchbar) / n)
    return {
        "n": n, "n_ungemessen": fehlend, "mittel": mittel, "streuung": streuung,
        "spanne": max(brauchbar) - min(brauchbar), "belastbar": True,
        "begruendung": (
            f"{n} Läufe, Mittel {mittel:.3f}, Streuung {streuung:.3f}, Spanne "
            f"{max(brauchbar) - min(brauchbar):.3f}."
            + (f" {fehlend} Läufe ungemessen und übersprungen." if fehlend else "")
        ),
    }


def ist_unterschied_belegt(a: float | None, b: float | None, boden: dict, *,
                           k: float = K_STREUUNGEN) -> dict:
    """Ist der Abstand zweier Scores grösser als der Zufall der Kette?

    Returns:
        ``{belegt, abstand, grenze, begruendung}``. ``belegt`` ist ``False``, wenn der
        Boden nicht belastbar ist oder ein Wert fehlt — **ungemessen ist nicht
        „kein Unterschied"**, und der Grund steht dabei.
    """
    if a is None or b is None:
        return {"belegt": False, "abstand": None, "grenze": None, "begruendung": (
            "Mindestens einer der beiden Läufe ist ungemessen. Daraus folgt KEIN "
            "Unterschied und auch keine Gleichheit — es folgt gar nichts.")}
    if not boden.get("belastbar"):
        return {"belegt": False, "abstand": abs(float(a) - float(b)), "grenze": None,
                "begruendung": (
                    f"Es gibt keinen belastbaren Rauschboden: {boden.get('begruendung')} "
                    f"Ohne ihn lässt sich nicht sagen, ob ein Abstand mehr ist als Zufall.")}
    abstand = abs(float(a) - float(b))
    grenze = k * boden["streuung"]
    if abstand > grenze:
        return {"belegt": True, "abstand": abstand, "grenze": grenze, "begruendung": (
            f"Abstand {abstand:.3f} übersteigt {k:g} × Rauschboden "
            f"({boden['streuung']:.3f}) = {grenze:.3f}.")}
    return {"belegt": False, "abstand": abstand, "grenze": grenze, "begruendung": (
        f"Abstand {abstand:.3f} liegt innerhalb von {k:g} × Rauschboden "
        f"({boden['streuung']:.3f}) = {grenze:.3f}. Das ist Zufall und kein Befund — wer "
        f"hier einen Effekt behauptet, behauptet ihn über das Rauschen der Kette.")}


# ======================================================================================
# Auswählen
# ======================================================================================

def waehle(bewertungen: Sequence[dict], *, schwelle: float,
           schluessel: str = "score") -> dict:
    """Die beste Variante — **oder die Feststellung, dass keine besteht.**

    Der Unterschied zum geerbten Bewerter steckt genau hier: Der liefert immer eine beste
    Variante, auch wenn alle unbrauchbar sind. Das ist die Sorte Antwort, die eine Frage
    beendet, ohne sie zu beantworten.

    Args:
        bewertungen: Liste von Wörterbüchern mit ``schluessel`` und beliebigem Beiwerk.
        schwelle: **absolut**, nicht aus der Charge gerechnet. Etwa
            ``geometrie_qa.SCHWELLE_GEOMETRIE``.

    Returns:
        ``{beste, index, bestanden, n_bestanden, n_ungemessen, begruendung}``.
        ``beste`` ist auch dann gesetzt, wenn sie die Schwelle reisst — dann steht in
        ``bestanden`` ``False``. Wer die beste von fünf schlechten sehen will, soll sie
        sehen; wer sie für gut hält, soll es an ``bestanden`` merken.
    """
    if not bewertungen:
        return {"beste": None, "index": None, "bestanden": False, "n_bestanden": 0,
                "n_ungemessen": 0, "begruendung": "Keine Variante vorgelegt."}

    messbar = [(i, b) for i, b in enumerate(bewertungen) if b.get(schluessel) is not None]
    ungemessen = len(bewertungen) - len(messbar)
    if not messbar:
        return {"beste": None, "index": None, "bestanden": False, "n_bestanden": 0,
                "n_ungemessen": ungemessen, "begruendung": (
                    (f"Die einzige Variante ist nicht gemessen — {schluessel!r} ist None."
                     if len(bewertungen) == 1 else
                     f"Keine der {len(bewertungen)} Varianten ist gemessen — alle "
                     f"{schluessel!r} sind None.")
                    + " Das heisst UNGEPRÜFT und nicht durchgefallen.")}

    index, beste = max(messbar, key=lambda p: p[1][schluessel])
    bestanden = [b for _, b in messbar if b[schluessel] >= schwelle]
    return {
        "beste": beste,
        "index": index,
        "bestanden": beste[schluessel] >= schwelle,
        "n_bestanden": len(bestanden),
        "n_ungemessen": ungemessen,
        "begruendung": (
            f"Beste Variante ist Nummer {index} mit {schluessel} "
            f"{beste[schluessel]:.3f}; {len(bestanden)} von {len(messbar)} gemessenen "
            f"erreichen die Schwelle {schwelle:.3f}."
            + (f" {ungemessen} ungemessen." if ungemessen else "")
            + ("" if beste[schluessel] >= schwelle else
               " KEINE Variante besteht — die beste ist die beste von schlechten, und das "
               "ist etwas anderes als eine gute.")
        ),
    }


# ======================================================================================
# Die gepaarte Reihe — dasselbe Paar über viele Startwerte
# ======================================================================================
#
# :func:`kontrollierte_reihe` hält **einen** Startwert fest. Das schliesst aus, dass ein
# Unterschied vom Zufall des Startwerts kommt — aber nur für *diesen einen* Startwert. Ob
# der Parameter allgemein wirkt oder ausgerechnet dort, bleibt offen.
#
# **Zweimal an einem Tag ist genau daran eine Messung gescheitert** (22.08.2026):
#
# * `auf-20260822-28`: qwen gegen z-image-turbo, Abstand 0.165 — etwa **eine**
#   Standardabweichung der Startwert-Streuung. An drei Bildern nicht entscheidbar.
# * Der Sprachbefund: bei n = 3 trug er nicht (Abstand 25.5 gegen Streuung 20.7, die
#   Bereiche überlappten). **Erst das Paaren über acht Startwerte entschied** — bei
#   gleichem Startwert gewann der deutsche Prompt 8 von 8 Mal.
#
# Die Streuung über Startwerte (0.2269) ist in diesem Projekt **grösser als jeder gemessene
# Parametereffekt** (0.10–0.14). Ein Mittelwertvergleich braucht deshalb sehr viele Läufe;
# ein **Paarvergleich** braucht wenige, weil er den Startwert herausrechnet, statt gegen
# ihn anzumessen.
#
# > Gleicher Startwert, eine Sache anders, zählen wer gewinnt.

#: Kleinste gepaarte Reihe, die überhaupt etwas belegen kann.
#:
#: Bei fünf Paaren liegt die Wahrscheinlichkeit, dass eine Seite **alle** gewinnt, ohne
#: dass ein Unterschied besteht, bei 6.25 % — knapp über der üblichen Fünfprozentmarke.
#: Ab sechs Paaren sind es 3.1 %. Vier Paare können also selbst im besten Fall nichts
#: belegen, und eine Reihe, die im besten Fall nichts belegen kann, ist verschwendete
#: Rechenzeit.
MIN_PAARE = 6


def gepaarte_reihe(basis: render.RenderAuftrag, feld: str, werte: Sequence,
                   seeds: Sequence[int]) -> list[list[render.RenderAuftrag]]:
    """Je Startwert **eine** vollständige kontrollierte Reihe.

    Returns:
        Eine Liste je Startwert, darin ein Auftrag je Wert — also ``len(seeds)`` Gruppen
        zu ``len(werte)`` Aufträgen. Die Gruppierung ist die Aussage: Verglichen wird
        **innerhalb** einer Gruppe, nie über Gruppen hinweg.

    Raises:
        VariantenError: zu wenige Startwerte, doppelte Startwerte, oder dieselben Gründe
            wie bei :func:`kontrollierte_reihe`.

    **Warum doppelte Startwerte abgewiesen werden:** Zwei Gruppen mit demselben Startwert
    sind keine zwei Paare, sondern dasselbe Paar zweimal. Sie zu zählen behauptete eine
    Sicherheit, die nicht da ist — und genau das soll dieses Verfahren verhindern.
    """
    seeds = list(seeds)
    if len(seeds) < MIN_PAARE:
        raise VariantenError(
            f"{len(seeds)} Startwerte sind zu wenige, nötig sind {MIN_PAARE}. Bei fünf "
            f"Paaren läge die Wahrscheinlichkeit, dass eine Seite zufällig alle gewinnt, "
            f"bei 6.25 % — eine Reihe, die im besten Fall nichts belegen kann, ist "
            f"verschwendete Rechenzeit.")
    if len(set(seeds)) != len(seeds):
        raise VariantenError(
            "Doppelte Startwerte. Zwei Gruppen mit demselben Startwert sind nicht zwei "
            "Paare, sondern dasselbe Paar zweimal — sie zu zählen behauptete eine "
            "Sicherheit, die nicht da ist.")
    gruppen = []
    for seed in seeds:
        mit_seed = dataclasses.replace(basis, seed=int(seed))
        gruppen.append(kontrollierte_reihe(mit_seed, feld, werte))
    return gruppen


def zaehle_siege(gruppen_bewertungen: Sequence[Sequence[float | None]]) -> dict:
    """Wer gewinnt wie oft — der Vorzeichentest über gepaarte Gruppen.

    Args:
        gruppen_bewertungen: je Gruppe eine Folge von Bewertungen, in derselben
            Reihenfolge wie die Werte. **Höher ist besser.** ``None`` heisst *nicht
            gemessen*; eine Gruppe mit einer fehlenden Bewertung wird **ganz**
            übersprungen — ein halbes Paar ist kein Paar.

    Returns:
        ``{siege, n_paare, n_uebersprungen, gewinner, p_zufall, belegt, begruendung}``.

        ``p_zufall`` ist die **zweiseitige** Wahrscheinlichkeit, dass der Gewinner rein
        zufällig mindestens so oft gewinnt. Zweiseitig, weil vorher nicht feststand,
        welche Seite gewinnen würde — einseitig zu rechnen, nachdem man das Ergebnis
        gesehen hat, halbiert die Zahl und die Ehrlichkeit gleich mit.

    **Was dieses Verfahren NICHT sagt:** wie gross der Unterschied ist. Es zählt Siege,
    nicht Abstände. Acht von acht Siegen belegen, **dass** eine Seite besser ist, und sagen
    nichts darüber, **um wieviel** — dafür braucht es die Bewertungen selbst.
    """
    vollstaendig = [g for g in gruppen_bewertungen
                    if g and all(w is not None for w in g)]
    n_uebersprungen = len(list(gruppen_bewertungen)) - len(vollstaendig)
    antwort = {"siege": [], "n_paare": len(vollstaendig),
               "n_uebersprungen": n_uebersprungen, "gewinner": None,
               "p_zufall": None, "belegt": False, "begruendung": ""}
    if not vollstaendig:
        antwort["begruendung"] = (
            "Keine vollständige Gruppe. Ein halbes Paar ist kein Paar — NICHT GEMESSEN.")
        return antwort

    breite = len(vollstaendig[0])
    if any(len(g) != breite for g in vollstaendig):
        raise VariantenError(
            "Die Gruppen sind unterschiedlich breit. Verglichen wird innerhalb einer "
            "Gruppe; unterschiedlich viele Werte je Gruppe hiesse, verschiedene Fragen "
            "zu vermengen.")

    siege = [0] * breite
    for gruppe in vollstaendig:
        bester = max(range(breite), key=lambda i: gruppe[i])
        siege[bester] += 1
    antwort["siege"] = siege

    n = len(vollstaendig)
    beste = max(range(breite), key=lambda i: siege[i])
    antwort["gewinner"] = beste
    p = _binomial_zweiseitig(siege[beste], n, 1.0 / breite)
    antwort["p_zufall"] = p
    antwort["belegt"] = p < 0.05 and n >= MIN_PAARE
    antwort["begruendung"] = (
        f"{siege[beste]} von {n} Paaren gewinnt Wert {beste}. Zufällig wäre das in "
        f"{p:.2%} der Fälle. "
        + ("BELEGT." if antwort["belegt"] else
           f"NICHT BELEGT — {'zu wenige Paare' if n < MIN_PAARE else 'zu häufig zufällig'}. "
           f"Das heisst NICHT, dass kein Unterschied besteht; es heisst, dass diese Reihe "
           f"keinen zeigt.")
        + (f" {n_uebersprungen} Gruppe(n) übersprungen, weil eine Bewertung fehlte."
           if n_uebersprungen else ""))
    return antwort


def _binomial_zweiseitig(treffer: int, n: int, p_einzeln: float) -> float:
    """Wahrscheinlichkeit, mindestens so viele Treffer zu sehen — auf beide Seiten.

    Reine Rechnung mit ``math.comb``; kein ``scipy``, weil dieses Modul überall laufen
    muss, wo der Kern läuft (Regel 4).
    """
    def genau(k: int) -> float:
        return math.comb(n, k) * (p_einzeln ** k) * ((1.0 - p_einzeln) ** (n - k))

    beobachtet = genau(treffer)
    # Zweiseitig nach der üblichen Konvention: alle Ausgänge, die mindestens so
    # unwahrscheinlich sind wie der beobachtete.
    return min(1.0, sum(genau(k) for k in range(n + 1)
                        if genau(k) <= beobachtet * (1 + 1e-12)))


# ═══════════════════════════════════════════════════════════════════════════════════════
# DECKUNGSGLEICH — gleiche Grundlage UND gleiche Form (Video-Befund L4-1, 21.10.2026)
# ═══════════════════════════════════════════════════════════════════════════════════════
#
# WARUM: «Deckungsgleich» hiess bis hierher nur «gleiche Grundlage» (Tiefe, Pose, Startwert,
# Nr. 85). Das KI-Bild kann darauf trotzdem eine andere Form malen — und zwei Varianten, die
# nebeneinander stehen, sehen dann aus wie ein Vergleich, der keiner ist. Abgestimmt mit der
# HomeStation: deckungsgleich heisst gleiche Grundlage UND Kanten-IoU des KI-Bilds gegen das
# Grundbild über einer Schwelle; darunter «gleiche Grundlage, Form weicht ab», mit Warnung.

#: **GESETZT AUS auf-20261021-317 (VIER LÄUFE)** — vorher 0,30, gesetzt, nicht gemessen.
#: 312/313 rechneten alle txt2img (Kanten-IoU 0,024–0,051) und trennten nichts. 317 hat erstmals
#: Läufe mit Augenurteil zur Form auf derselben Grundlage (sSE, Seed 482913, 960 x 600):
#:
#:   ====  ===========  ==========================================
#:   Lauf  Kanten-IoU   Augenurteil «Form wie Grundlage»
#:   ====  ===========  ==========================================
#:   K     0,033        nein — anderer Bau, Ausschnitt viel näher
#:   M2    0,197        ja — Fenster und Fugen neu, Baukörper gleich
#:   BI55  0,635        ja
#:   BI40  0,739        ja
#:   ====  ===========  ==========================================
#:
#: 0,30 stufte M2 (Form ja) als «Form weicht ab» ein: M2 malt Fenster und Fugen dazu — Kanten,
#: die das graue Grundbild nicht hat; das senkt die Kanten-IoU, ohne dass die Form wandert. Die
#: Lücke zwischen «nein» und «ja» liegt zwischen 0,033 und 0,197. 0,10 liegt in ihrer Mitte auf
#: logarithmischer Skala (Wurzel aus 0,033 · 0,197 ≈ 0,08) und rundet auf eine Zahl, die man sich
#: merken kann; nach unten bleibt der Faktor drei Abstand (K), nach oben der Faktor zwei (M2). **Schmal**: vier Bilder,
#: ein Seed, eine Kamera, eine Grundlage — die Setzung wandert mit in jedes Ergebnis.
#:
#: **ANGEHOBEN AUF 0,25 (22.10.2026, Ergebnisse 337 und 339).** 0,10 nannte die Läufe ohne
#: Bildeingang «deckungsgleich», obwohl die Form nicht hielt: 337 K 0,213 (Fenster weg, flacher
#: First), 337 K-S 0,216, 339 KS 0,142 (ein anderes Haus, Flachdach-Kubus). Die Läufe vom
#: Grundbild aus hielten Giebel und Fenster: 337 BI65 0,296 und BI65-S 0,294, BI50 0,367,
#: 339 BS50 0,481 (Kanten-IoU über das ganze Bild, wie sie hier gerechnet wird). Die Lücke liegt
#: zwischen 0,216 und 0,294; 0,25 ist ihre Mitte auf logarithmischer Skala (Wurzel aus
#: 0,216 · 0,294 ≈ 0,252). **Der Massstab ist damit strenger:** «Form wie Grundbild» heisst seit
#: 337 auch «Fensterteilung wie im Grundbild». M2 aus 317 (0,197, «Fenster und Fugen neu,
#: Baukörper gleich») hiesse heute «Form weicht ab» — nach diesem Massstab zu Recht. **Schmal**:
#: neun Bilder, ein Haus, eine Kamera; die Zahl hängt an den Texturkanten des Grundbilds (339:
#: Beton hat halb so viele wie Holz).
#:
#: **GEMESSEN NUR IM HAUS (24.10.2026, Ergebnis 347).** In der Vorschau von 347 stieg die
#: Kanten-IoU über das ganze Bild von 0,202 (346) auf 0,297 und damit über 0,25 — nicht, weil
#: die KI das Haus besser hielt (das OG-Band blieb zugemalt), sondern weil die Bäume seit 0.3.52
#: als Umfeld aus dem Cycles-Bild kommen und ihre Kanten decken. Der Satz «FORM WEICHT VOM
#: GRUNDBILD AB» fiel weg; ein übermaltes Haus ohne Glas im ID-Pass bliebe ganz still. Gemessen
#: wird darum seither nur im Haus: in der Bauwerksmaske, ohne die Einträge, die nach Namen Umfeld
#: oder Gelände sind (:func:`nicht_fassade_farben`, dieselbe Regel wie die Fensterprüfung).
#: **Die Schwelle bleibt 0,25** — gegengeprüft an den Haus-Werten derselben Läufe (Kanten-IoU in
#: der Bauwerksmaske, wie die HomeStation sie mass): Form nein 0,094 (346 Vorschau), 0,103 (347
#: Vorschau), 0,115 (339 KS), 0,207 (337 K, 340 V-0), 0,210 (337 K-S); Form ja 0,270 (337
#: BI65-S), 0,273 (BI65), 0,334 (BI50), 0,375 (340 V-A), 0,438 (339 BS50), 0,525–0,745 (346 voll),
#: 0,678 (347 voll). Die Lücke liegt zwischen 0,210 und 0,270, ihre logarithmische Mitte bei
#: 0,238; 0,25 liegt in ihr (Faktor 1,19 nach unten, 1,08 nach oben). Sie bleibt, weil die
#: Oberfläche dieselbe Zahl als Rückfall führt (``DECKUNG_SCHWELLE`` drüben) und eine neue
#: Zahl ohne neue Messung nur eine zweite Setzung wäre. **Schmal nach oben:** BI65-S liegt 0,02
#: darüber — und BI65 malte an der Traufe Fenster dazu, sein «Form ja» war knapp.
DECKUNG_KANTEN_IOU_SCHWELLE = 0.25
DECKUNG_HERKUNFT = ("gesetzt aus auf-20261022-337 und -339, seit 347 nur im Haus gemessen "
                    "(Form nein 0,094-0,210, Form ja 0,270-0,745)")
#: Wo die Deckung gemessen wurde: im Haus (Bauwerksmaske ohne Umfeld und Gelände) oder — ohne
#: brauchbare Maske — über das ganze Bild wie bis 0.3.52.
DECKUNG_BEREICH_HAUS = "haus"
DECKUNG_BEREICH_GANZ = "ganz"
#: So viel des Bilds muss das Haus mindestens decken, damit dort gemessen wird; darunter (oder
#: ohne Maske) zählt das ganze Bild. Gesetzt: 1 % — bei 1600 x 1000 sind das 16 000 Bildpunkte;
#: das Haus in 347 deckte 11,7 % (186 956).
DECKUNG_HAUS_MIN_ANTEIL = 0.01

DECKUNGSGLEICH = "deckungsgleich"
FORM_WEICHT_AB = "form_weicht_ab"
ANDERE_GRUNDLAGE = "andere_grundlage"
DECKUNG_UNGEMESSEN = "ungemessen"

DECKUNG_SATZ = {
    DECKUNGSGLEICH: "deckungsgleich — gleiche Grundlage, gleiche Form",
    FORM_WEICHT_AB: "gleiche Grundlage, Form weicht ab",
    ANDERE_GRUNDLAGE: "andere Grundlage — nicht deckungsgleich",
    DECKUNG_UNGEMESSEN: "gleiche Grundlage, Form nicht gemessen",
}


def deckung(gleiche_grundlage: bool, kanten_iou_grundlage: float | None, *,
            schwelle: float = DECKUNG_KANTEN_IOU_SCHWELLE) -> dict:
    """Ist ein KI-Bild mit seiner Grundlage deckungsgleich?

    Args:
        gleiche_grundlage: Steht das Bild auf derselben Grundlage (Tiefe, Pose, Startwert)?
        kanten_iou_grundlage: Kanten-IoU des KI-Bilds gegen das Grundbild
            (:func:`aiimaging.farbabgleich.kanten_iou`); ``None`` = nicht gemessen.

    Returns:
        ``{urteil, satz, warnung, kanten_iou, schwelle, herkunft}``. ``warnung`` ist wahr bei
        «Form weicht ab». Ohne Messung heisst es nie «deckungsgleich» — nur «nicht gemessen».
    """
    if not 0.0 <= float(schwelle) <= 1.0:
        raise ValueError(f"Schwelle {schwelle!r} liegt nicht in 0..1.")
    if not gleiche_grundlage:
        urteil = ANDERE_GRUNDLAGE
    elif kanten_iou_grundlage is None:
        urteil = DECKUNG_UNGEMESSEN
    elif float(kanten_iou_grundlage) >= schwelle:
        urteil = DECKUNGSGLEICH
    else:
        urteil = FORM_WEICHT_AB
    return {"urteil": urteil, "satz": DECKUNG_SATZ[urteil], "warnung": urteil == FORM_WEICHT_AB,
            "kanten_iou": None if kanten_iou_grundlage is None else round(float(kanten_iou_grundlage), 4),
            "schwelle": schwelle, "herkunft": DECKUNG_HERKUNFT}


def hausbereich(maske, n: int, *, kennung=None, tabelle=None) -> tuple[list | None, str | None]:
    """Der Bereich, in dem die Deckung misst: Bauwerksmaske ohne Umfeld und Gelände.

    Args:
        maske: die Bauwerksmaske (Wahrheitswerte je Bildpunkt) oder ``None``.
        n: Bildpunkte des Bilds.
        kennung, tabelle: Material-ID-Pass (Farben je Bildpunkt) und seine Tabelle — damit
            fallen Einträge heraus, die nach Namen Umfeld oder Gelände sind
            (:func:`nicht_fassade_farben`), auch wenn sie in der Maske liegen.

    Returns:
        ``(bereich, None)`` oder ``(None, grund)``, wenn nicht im Haus gemessen werden kann.
    """
    if maske is None:
        return None, "keine Bauwerksmaske"
    if len(maske) != n:
        return None, f"Bauwerksmaske hat {len(maske)} Punkte, das Bild {n}"
    bereich = [bool(m) for m in maske]
    ausser = nicht_fassade_farben(tabelle) if tabelle else set()
    if ausser and kennung is not None and len(kennung) == n:
        bereich = [m and tuple(k[:3]) not in ausser for m, k in zip(bereich, kennung)]
    if not n or sum(bereich) / n < DECKUNG_HAUS_MIN_ANTEIL:
        return None, (f"Haus deckt {sum(bereich)} Bildpunkte, unter "
                      f"{DECKUNG_HAUS_MIN_ANTEIL:.0%} des Bilds")
    return bereich, None


def deckung_aus_bildern(ki_png, grundbild_png, gleiche_grundlage: bool, *, maske=None,
                        material_id_png=None, tabelle=None,
                        schwelle: float = DECKUNG_KANTEN_IOU_SCHWELLE) -> dict:
    """Wie :func:`deckung`, aus den beiden Bilddateien. Ungleiche Masse = nicht gemessen (mit Grund).

    Mit ``maske`` (Bauwerksmaske) misst die Kanten-IoU nur im Haus (:func:`hausbereich`; mit
    ``material_id_png`` und ``tabelle`` ohne Umfeld und Gelände) — Ergebnis 347: Bäume aus dem
    Cycles-Bild decken sonst ihre Kanten und heben die Zahl über die Schwelle, während das Haus
    übermalt ist. Ohne brauchbare Maske misst sie über das ganze Bild und sagt es
    (``bereich: "ganz"``, ``bereich_grund``). ``kanten_iou_ganz`` steht immer daneben.
    """
    from pathlib import Path  # noqa: PLC0415
    from . import bildlesen, farbabgleich  # noqa: PLC0415
    if not grundbild_png or not Path(grundbild_png).is_file():
        return dict(deckung(gleiche_grundlage, None, schwelle=schwelle), grund="kein Grundbild")
    a, ba, ha = bildlesen.lies_png_farben(ki_png)
    b, bb, hb = bildlesen.lies_png_farben(grundbild_png)
    if (ba, ha) != (bb, hb):
        return dict(deckung(gleiche_grundlage, None, schwelle=schwelle),
                    grund=f"KI-Bild {ba}x{ha}, Grundbild {bb}x{hb}: ungleiche Masse")
    kennung = None
    if material_id_png and tabelle and Path(material_id_png).is_file():
        try:
            kennung, bi, hi = bildlesen.lies_png_farben(material_id_png)
            if (bi, hi) != (ba, ha):
                kennung = None
        except (bildlesen.BildError, OSError, ValueError):
            kennung = None
    bereich, grund = hausbereich(maske, ba * ha, kennung=kennung, tabelle=tabelle)
    ka, kb = farbabgleich.kantenkarten(a, b, ba, ha)     # einmal gerechnet, zweimal gezählt
    ganz = farbabgleich.kanten_iou_aus_karten(ka, kb)
    if bereich is None:
        return dict(deckung(gleiche_grundlage, ganz, schwelle=schwelle),
                    bereich=DECKUNG_BEREICH_GANZ, bereich_grund=grund,
                    kanten_iou_ganz=None if ganz is None else round(ganz, 4))
    haus = farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=bereich)
    return dict(deckung(gleiche_grundlage, haus, schwelle=schwelle),
                bereich=DECKUNG_BEREICH_HAUS, n_haus=sum(bereich),
                kanten_iou_ganz=None if ganz is None else round(ganz, 4))


# ================================================================ hält das KI-Bild die Fenster?
#
# **Anlass (Mac-Nachprüfung 23.10.2026, Visbox 0.3.50, synthetische Mappe «haus-am-hang»):**
# Variante mit Bildeingang 0,5, Kamera sSE — das Fensterband im OG fehlt, die KI malt dort
# geschlossene Lattung, und die QA meldete «bestanden». Keine Prüfung sah es: Die Geometrie-QA
# misst die Tiefe (die Lattung liegt in derselben Ebene wie das Glas), und die Deckung
# (:func:`deckung`, Kanten-IoU über das GANZE Bild, Schwelle 0,25) verliert an einem schmalen
# Band nur wenige Kantenpunkte. Am Demohaus (337/340/342) hielt 0,5 die Fenster — dort sind sie
# gross. Gezählt wird darum, was am Glas selbst geschieht: an den Glas-Bildpunkten des
# Material-ID-Passes.
#
# **Die Regel je Glas-Bildpunkt:** gehalten, wenn das KI-Bild dort dem Grundbild näher ist als
# der mittleren Fassadenfarbe des KI-Bilds (Median je Kanal über die Bauwerksmaske ohne Glas).
# Malt die KI Lattung über das Glas, sieht der Punkt aus wie die Fassade daneben; hält sie das
# Glas, bleibt er dem Grundbild nah — auch bei einer anderen Stimmung meist näher als an der
# Fassade, weil Glas dunkler oder spiegelnd bleibt. **Eine Auskunft mit einem Satz, kein Tor:**
# ``bestanden`` und ``deckung`` bleiben, wie sie sind.
#
# **Nachgeschärft nach Ergebnis auf-20261023-346 (F3, ROT):** Die Vorschau am Mac hatte das
# OG-Band mit heller grauer Lattung zugemalt (KI 142/142/143), und die Regel nannte es
# «gehalten» (0,641 über 0,5): Die helle Lattung liegt näher am hellblauen Glas des Grundbilds
# (158/178/190) als am dunklen Median der KI-«Fassade» (99/94/93) — und der zählte Bäume,
# Weg, Terrasse und Schattenseite mit. **Helligkeit allein trennt dort nicht, der Farbton
# schon:** Glas ist im Grundbild bläulicher als die Fassade (Blau minus Rot +32 gegen etwa −5),
# die übermalte Stelle nicht mehr (+1,6); bei voller Güte bleibt sie es (+28). Darum zwei
# Änderungen, v2:
#
# 1. **Der Fassaden-Median nur aus Bauwerk:** Einträge, die nach der Maskenregel Umfeld oder
#    Gelände sind (``maske.ist_umfeld``/``ist_gelaende`` am Namen, seit 346 auch Bäume am
#    Namenswort), zählen nicht zur Fassade, auch wenn sie in der übergebenen Maske liegen.
# 2. **Der Farbton als zweite Bedingung:** Ist das Glas im Grundbild um mindestens
#    :data:`FENSTER_FARBTON_TRENNUNG_MIN` bläulicher als die Fassade, gilt ein Glaspunkt nur
#    als gehalten, wenn er AUCH im KI-Bild mindestens :data:`FENSTER_FARBTON_ANTEIL` dieses
#    Vorsprungs behält — gemessen gegen die KI-Fassade, damit eine wärmere Stimmung (alles
#    röter) das Glas nicht verliert. Ist das Glas im Grundbild nicht bläulicher (dunkles,
#    graues Glas), gilt die Helligkeitsregel allein wie bisher.

#: Wörter, an denen ein Materialname als Scheibe gilt — dieselben wie im Runner
#: (``runners.blender_depth_stage.GLAS_WOERTER``; eine Probe hält beide gleich). Der Runner
#: erkennt Glas zusätzlich am Durchlass; das sieht die Tabelle des ID-Passes nicht.
GLAS_WOERTER = ("glas", "glass", "verglasung", "glazing")

#: Unter diesem Anteil gehaltener Glas-Bildpunkte steht der Satz. Gesetzt (die Hälfte); in
#: auf-20261023-346 hielten die vollen Varianten 0,957–0,989 — die Vorschau kam mit der Regel v1
#: auf 0,641 und damit darüber; dass sie seit v2 (Farbton) darunter fällt, bestätigt 347.
FENSTER_GEHALTEN_SCHWELLE = 0.5
#: So viel des Bilds muss Glas sein, damit gemessen wird — darunter schweigt die Prüfung
#: (keine Warnungsflut an einem Haus mit zwei kleinen Fenstern). Gesetzt: 0,2 %, bei
#: 1600 x 1000 also 3200 Bildpunkte, ein Band von 2 x 1600 Punkten.
FENSTER_MIN_ANTEIL_BILD = 0.002
#: Wie weit sich Glas und Fassade im GRUNDBILD mindestens unterscheiden müssen (Abstand im
#: 8-Bit-RGB, Median über das Glas) — sonst lässt sich am KI-Bild nicht trennen, was was ist.
#: Gesetzt: 24 (knapp ein Zehntel der Skala).
FENSTER_TRENNUNG_MIN = 24.0
#: Wie viel bläulicher (Blau minus Rot, 8 Bit, Median über das Glas) das Glas im GRUNDBILD
#: mindestens sein muss als die Fassade, damit der Farbton mitprüft. Gesetzt: 12 — an «haus-am-hang»
#: (346) waren es rund 36, bei grauem Glas wäre es nahe null, dann prüft nur die Helligkeit.
FENSTER_FARBTON_TRENNUNG_MIN = 12.0
#: So viel seines Farbton-Vorsprungs muss ein Glaspunkt im KI-Bild behalten. **Mit 346 geeicht**
#: (Mittelwerte im OG): volle Güte behält rund 0,86 (+32 von +37), die Vorschau rund 0,2 (+7,6) —
#: die Hälfte liegt dazwischen, mit Abstand zu beiden.
FENSTER_FARBTON_ANTEIL = 0.5
METHODE_FENSTER = ("Anteil der Glas-Bildpunkte (Material-ID-Pass, Name mit Glaswort, in der "
                   "Bauwerksmaske), an denen das KI-Bild dem Grundbild naeher ist als dem Median "
                   "der KI-Fassade (Bauwerksmaske ohne Glas, ohne Umfeld und Gelaende) und — wo "
                   "das Glas im Grundbild blaeulicher ist als die Fassade — mindestens die Haelfte "
                   "dieses Farbton-Vorsprungs (Blau minus Rot) behaelt, v2 (auf-20261023-346)")
SATZ_FENSTER_NICHT_GEHALTEN = "FENSTER IM KI-BILD NICHT GEHALTEN"


def glasfarben(tabelle) -> set:
    """Die Kennfarben (8 Bit) der Einträge des ID-Passes, deren Name ein Glaswort trägt."""
    farben = set()
    for eintrag in tabelle or ():
        if not isinstance(eintrag, dict):
            continue
        name = str(eintrag.get("name") or "").lower()
        farbe = eintrag.get("farbe_srgb_8bit")
        if any(w in name for w in GLAS_WOERTER) and isinstance(farbe, (list, tuple)) \
                and len(farbe) >= 3:
            farben.add(tuple(int(k) for k in farbe[:3]))
    return farben


def nicht_fassade_farben(tabelle) -> set:
    """Die Kennfarben der Einträge, die nicht zur Fassade zählen: Umfeld und Gelände nach Namen.

    Dieselbe Regel wie die Bauwerksmaske (``maske.ist_umfeld``, ``maske.ist_gelaende``) — hier
    nur für den Fassaden-Median der Fensterprüfung, damit Bäume, Weg und Gelände ihn nicht
    verdunkeln, auch wenn sie in der übergebenen Maske liegen (Ergebnis auf-20261023-346).
    Glas zählt nie hierher.
    """
    from . import maske as _maske  # noqa: PLC0415
    farben = set()
    for eintrag in tabelle or ():
        if not isinstance(eintrag, dict):
            continue
        name = str(eintrag.get("name") or "")
        farbe = eintrag.get("farbe_srgb_8bit")
        if any(w in name.lower() for w in GLAS_WOERTER):
            continue
        if (_maske.ist_umfeld(name) or _maske.ist_gelaende(name)) \
                and isinstance(farbe, (list, tuple)) and len(farbe) >= 3:
            farben.add(tuple(int(k) for k in farbe[:3]))
    return farben


def _blau(p) -> float:
    """Wie bläulich ein Bildpunkt ist: Blau minus Rot (8 Bit)."""
    return float(p[2]) - float(p[0])


def _abstand(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


#: Höchstens so viele Fassadenpunkte gehen in den Median (gleichmässig ausgedünnt) — bei
#: 1600 x 1000 ist die Fassade sonst eine Dreiviertelmillion Punkte, und der Median ändert
#: sich durch das Ausdünnen nicht merklich.
FASSADE_STICHPROBE = 20000


def _median_je_kanal(punkte: list) -> tuple:
    def med(werte):
        werte = sorted(werte)
        n = len(werte)
        return werte[n // 2] if n % 2 else (werte[n // 2 - 1] + werte[n // 2]) / 2.0
    return tuple(med([p[k] for p in punkte]) for k in range(3))


def fenster_gehalten(ki, grund, kennung, glas: set, *, maske=None, ausser=(),
                     schwelle: float = FENSTER_GEHALTEN_SCHWELLE) -> dict:
    """Wie viel vom Glas des Grundbilds im KI-Bild Glas geblieben ist.

    Args:
        ki, grund, kennung: Farben je Bildpunkt (gleich lang) — KI-Bild, Grundbild (Cycles)
            und Material-ID-Pass.
        glas: die Kennfarben des Glases (:func:`glasfarben`).
        maske: die Bauwerksmaske (Wahrheitswerte je Bildpunkt); ohne sie zählt jeder Punkt,
            der im ID-Pass nicht schwarz ist.
        ausser: Kennfarben, die nicht zur Fassade zählen (:func:`nicht_fassade_farben`:
            Umfeld, Gelände) — sie gehen nicht in den Fassaden-Median ein.

    Returns:
        ``{anteil, gehalten, n_glas, anteil_bild, trennung, farbton_trennung, farbton,
        schwelle, methode, grund?}`` — ``farbton`` sagt, ob der Farbton mitgeprüft hat.
        ``gehalten`` ist ``None``, wenn nicht gemessen wird (kein oder zu wenig Glas, Glas
        im Grundbild wie Fassade) — dann sagt ``grund`` warum. Nie eine Ausnahme bei
        fehlendem Glas: Ein Haus ohne Fenster ist kein Fehler.
    """
    n = len(kennung)
    if len(ki) != n or len(grund) != n or (maske is not None and len(maske) != n):
        raise ValueError(f"Ungleiche Laengen: KI {len(ki)}, Grundbild {len(grund)}, "
                         f"ID-Pass {n}, Maske {None if maske is None else len(maske)}.")
    aus = {"anteil": None, "gehalten": None, "n_glas": 0, "anteil_bild": 0.0,
           "trennung": None, "farbton_trennung": None, "farbton": False,
           "schwelle": schwelle, "methode": METHODE_FENSTER}
    ausser = {tuple(int(k) for k in f[:3]) for f in ausser or ()}
    if not glas:
        return dict(aus, grund="Kein Glas im ID-Pass (kein Materialname mit Glaswort).")
    glas_i, fassade_i = [], []
    schwarz = (0, 0, 0)
    for i, k in enumerate(kennung):
        k = k[:3] if len(k) > 3 else k
        if not (maske[i] if maske is not None else tuple(k) != schwarz):
            continue
        if tuple(k) in glas:
            glas_i.append(i)
        elif tuple(k) not in ausser:
            fassade_i.append(i)
    aus["n_glas"] = len(glas_i)
    aus["anteil_bild"] = round(len(glas_i) / n, 5) if n else 0.0
    if not n or len(glas_i) / n < FENSTER_MIN_ANTEIL_BILD:
        return dict(aus, grund=f"Zu wenig Glas im Bild ({len(glas_i)} Bildpunkte, unter "
                               f"{FENSTER_MIN_ANTEIL_BILD:.1%}) — nicht gemessen.")
    if not fassade_i:
        return dict(aus, grund="Keine Fassade neben dem Glas — nicht gemessen.")
    stich = fassade_i[::max(1, len(fassade_i) // FASSADE_STICHPROBE)]
    fassade_grund = _median_je_kanal([grund[i] for i in stich])
    trennung = sorted(_abstand(grund[i], fassade_grund) for i in glas_i)[len(glas_i) // 2]
    aus["trennung"] = round(trennung, 1)
    if trennung < FENSTER_TRENNUNG_MIN:
        return dict(aus, grund=f"Im Grundbild sieht das Glas aus wie die Fassade (Abstand "
                               f"{trennung:.1f} unter {FENSTER_TRENNUNG_MIN:.0f}) — nicht "
                               f"gemessen.")
    fassade_ki = _median_je_kanal([ki[i] for i in stich])
    # DER FARBTON (346): wie viel bläulicher das Glas im Grundbild ist als die Fassade.
    blau_fg, blau_fk = _blau(fassade_grund), _blau(fassade_ki)
    farbton_trennung = sorted(_blau(grund[i]) - blau_fg for i in glas_i)[len(glas_i) // 2]
    aus["farbton_trennung"] = round(farbton_trennung, 1)
    mit_farbton = farbton_trennung >= FENSTER_FARBTON_TRENNUNG_MIN
    aus["farbton"] = mit_farbton

    def gehalten(i) -> bool:
        if _abstand(ki[i], grund[i]) > _abstand(ki[i], fassade_ki):
            return False
        return (not mit_farbton or _blau(ki[i]) - blau_fk
                >= FENSTER_FARBTON_ANTEIL * (_blau(grund[i]) - blau_fg))

    treffer = sum(1 for i in glas_i if gehalten(i))
    anteil = treffer / len(glas_i)
    return dict(aus, anteil=round(anteil, 4), gehalten=anteil >= schwelle)


def fenster_aus_bildern(ki_png, grundbild_png, material_id_png, tabelle, *, maske=None) -> dict:
    """:func:`fenster_gehalten` aus den drei Bilddateien — nie eine Ausnahme.

    Fehlt eine Datei oder passen die Grössen nicht, ``{anteil: None, gehalten: None, grund}``.
    """
    from pathlib import Path  # noqa: PLC0415
    from . import bildlesen  # noqa: PLC0415
    leer = {"anteil": None, "gehalten": None, "methode": METHODE_FENSTER,
            "schwelle": FENSTER_GEHALTEN_SCHWELLE}
    glas = glasfarben(tabelle)
    if not glas:
        return dict(leer, grund="Kein Glas im ID-Pass (kein Materialname mit Glaswort).")
    for name, pfad in (("KI-Bild", ki_png), ("Grundbild", grundbild_png),
                       ("ID-Pass", material_id_png)):
        if not pfad or not Path(pfad).is_file():
            return dict(leer, grund=f"{name} fehlt — nicht gemessen.")
    try:
        ki, bk, hk = bildlesen.lies_png_farben(ki_png)
        grund, bg, hg = bildlesen.lies_png_farben(grundbild_png)
        kennung, bi, hi = bildlesen.lies_png_farben(material_id_png)
        if not (bk, hk) == (bg, hg) == (bi, hi):
            return dict(leer, grund=f"Ungleiche Masse: KI {bk}x{hk}, Grundbild {bg}x{hg}, "
                                    f"ID-Pass {bi}x{hi} — nicht gemessen.")
        return fenster_gehalten(ki, grund, kennung, glas, maske=maske,
                                ausser=nicht_fassade_farben(tabelle))
    except (bildlesen.BildError, OSError, ValueError) as fehler:
        return dict(leer, grund=f"Fenster nicht messbar: {fehler}")
