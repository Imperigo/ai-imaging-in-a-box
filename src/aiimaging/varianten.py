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
                    f"Keine der {len(bewertungen)} Varianten ist gemessen — alle "
                    f"{schluessel!r} sind None. Das heisst UNGEPRÜFT und nicht "
                    f"durchgefallen.")}

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
