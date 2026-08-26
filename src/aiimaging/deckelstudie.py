"""Warum ``geom_iou`` deckelt — und woran es **nicht** liegt.

Der Befund, der diese Datei nötig gemacht hat
---------------------------------------------
``geometrie_qa.IOU_DECKEL`` hält fest, dass ``geom_iou`` an einer echten Szene bei
**0.256** (``wie_soll``) bzw. **0.406** (``ohne_randberuehrung``) deckelt. Nötig für die
Schwelle 0.65 wären **0.4225**. *Selbst ein perfektes Bild kommt dort auf höchstens
0.634* — die Schwelle ist damit arithmetisch unerreichbar.

Daraus wurde in ``docs/PLAN.md`` eine offene Aufgabe: *«Den Rest des Deckels — trägt eine
Kombination (`ohne_randberuehrung` plus `rand_10`)?»* **Sie zielt auf die Regel.**

Am 26.08.2026 hier gemessen, ohne GPU, an im Repo erzeugter Geometrie: **Die Regel ist es
nicht.**

Was gemessen wurde
------------------
Ein **perfekter Schätzer** lässt sich nachstellen: Blenders eigene Tiefenkarte, aus dem
normalisierten PNG gelesen. Sie trägt die richtigen Werte und — wie jede Schätzerkarte —
**keine Hintergrundmarke**. Genau das ist der Unterschied zur EXR, und genau darum geht es.

Ergebnis über drei Szenen (400 × 400, Kamera ``sSE``):

======================  ================  =============  ======================
Szene                   Geometrieanteil   ``wie_soll``   ``ohne_randberuehrung``
======================  ================  =============  ======================
Quader                  0.1111            0.9999         0.9999
Hochbau                 0.1730            0.9998         0.9999
Hochbau mit Gelände     0.0822            0.9977         0.9989
======================  ================  =============  ======================

**Die Regel erreicht 0.9999, wo die Produktion bei 0.406 deckelt.** Der Verlust liegt
also vollständig im Schätzer.

Und woran im Schätzer — zwei Fehlerquellen, sauber getrennt
------------------------------------------------------------
Die naheliegende Erklärung wäre Ordnungsrauschen: Der Schätzer ordnet die Tiefen
ungenauer. Sie trägt **nicht**, und das lässt sich zeigen, indem man die beiden möglichen
Fehler einzeln aufbringt (:func:`rauschen_auf_geometrie`, :func:`hintergrund_verschieben`):

**A — Rauschen nur auf der Geometrie**, Hintergrund bleibt perfekt:

    |rho| über die Geometrie   1.000   0.974   0.825   0.583   0.393
    IoU                        0.9998  0.9995  0.9846  0.9016  0.7653

*Selbst bei einer fast zerstörten Ordnung (|rho| 0.393) bleibt IoU bei 0.765.* Die Regel
ist gegen Ordnungsfehler **innerhalb** der Geometrie robust.

**B — der Hintergrund rückt in den Wertebereich des Bauwerks**, Geometrie unangetastet:

    Hintergrund bei … des Bauwerksbereichs   0 %     25 %    50 %    75 %    100 %
    |rho| über die Geometrie                 1.0000  1.0000  1.0000  1.0000  1.0000
    IoU                                      0.9998  0.9036  0.4983  0.1849  0.0000

*Die Rangkorrelation bleibt bei **exakt 1.0**, und IoU fällt auf null.*

Die Erklärung, und sie passt auf die Zahl
------------------------------------------
Gemessen wurde in der Produktion |spearman| **0.990** bei geom_iou **0.406**
(``auf-20260819-15``). Nach Fall A gehörte zu |rho| 0.99 ein IoU von rund 0.99; nach Fall
B gehört zu IoU 0.41 ein Hintergrund bei rund **55–60 %** des Bauwerksbereichs.

    **Der Schätzer legt den Himmel mitten in die Tiefenspanne des Bauwerks.**

Das ist keine Ungenauigkeit, sondern eine Eigenschaft relativer Tiefenschätzer: Sie
bilden auf einen beschränkten Bereich ab und haben für *unendlich weit* keinen Wert.

Was daraus folgt — und was ausdrücklich NICHT
-----------------------------------------------
**Keine Silhouettenregel, die allein die Werte des Schätzers liest, kann das beheben.**
``ohne_randberuehrung`` hebt 0.256 auf 0.406, weil sie randberührende Flächen verwirft —
das ist ein Teilausweg und erklärt genau die Grössenordnung des Gewinns.

Was hier **nicht** entschieden wird: was stattdessen zu tun ist. Drei Wege stehen offen,
und die Wahl berührt die Forschungsfrage selbst — sie gehört dem Owner:

1. Eine **Hintergrundtrennung, die nicht aus den Schätzerwerten kommt** (Segmentierung des
   erzeugten Bildes). Ein zusätzliches Modell, mit Lizenzfrage.
2. ``geom_iou`` **normalisieren** gegen den je Szene erreichbaren Deckel —
   ``geometrie_qa.erreichbarkeit`` rechnet ihn bereits.
3. ``geom_iou`` **aus dem Score nehmen** und auf die maskierte Rangkorrelation
   (``rho_maske``) stützen. *Fall B zeigt, dass sie von diesem Fehler gar nicht betroffen
   ist* — sie bleibt bei 1.0, während IoU zusammenbricht.

Was diese Datei nicht ist
-------------------------
Kein Ersatz für eine Messung am Gerät. Der perfekte Schätzer ist **nachgestellt**, nicht
gelaufen; was ein echter Schätzer auf einem *erzeugten* Bild tut, ist damit nicht gemessen.
Die Vorhersage — Himmel bei 55–60 % — ist zur Prüfung beauftragt.
"""
from __future__ import annotations

import random
from collections.abc import Sequence

from aiimaging import geometrie_qa, tiefenschaetzer

#: Die Polarität des normalisierten Tiefen-PNG: **nah = hell**, also wie eine Disparität.
#: Sie wird nicht geraten — der Runner schreibt es so, und ``markiere_hintergrund``
#: verlangt die Angabe aus genau dem Grund, aus dem sie hier als Konstante steht.
POLARITAET_TIEFEN_PNG = "disparitaet"


class DeckelError(ValueError):
    """Die Eingabe lässt keine Deckelmessung zu."""


def _pruefe(soll, karte, name: str) -> None:
    if len(soll) != len(karte):
        raise DeckelError(
            f"{name}: Soll-Karte und Schätzkarte sind unterschiedlich lang "
            f"({len(soll)} vs. {len(karte)}). Verglichen wird punktweise."
        )
    if not soll:
        raise DeckelError(f"{name}: leere Karte — es gibt nichts zu messen.")


def teile_auf(soll: Sequence[float]) -> dict:
    """Welche Punkte tragen Geometrie, welche Hintergrund? — aus der **Soll**-Karte.

    Die Soll-Karte kommt aus der EXR und trägt ``inf`` für den Hintergrund; sie ist damit
    die einzige Quelle, die es exakt weiss. Jede Aussage dieser Studie hängt daran.
    """
    silhouette = geometrie_qa.silhouette(soll)
    return {
        "silhouette": silhouette,
        "geometrie": [i for i, s in enumerate(silhouette) if s],
        "hintergrund": [i for i, s in enumerate(silhouette) if not s],
        "n_geometrie": sum(silhouette),
        "anteil": sum(silhouette) / len(silhouette),
    }


def iou_gegen_soll(soll: Sequence[float], karte: Sequence[float], *,
                   breite: int, hoehe: int, strategie: str = "wie_soll") -> dict:
    """IoU einer Schätzkarte gegen die Soll-Silhouette, unter einer Silhouettenregel.

    Returns:
        ``{iou, rho_geometrie, strategie, anteil_hintergrund}``.

        ``rho_geometrie`` ist die Rangkorrelation **nur über die Geometriepunkte** — das
        Gegenstück zu ``rho_maske`` im Produktivweg. Über die ganze Karte gerechnet wäre
        sie wertlos: Die Hintergrundpunkte der Soll-Karte sind alle ``inf`` und damit
        rangleich, und schon geringes Rauschen darauf lässt die Zahl einbrechen, ohne dass
        sich an der Geometrie etwas geändert hätte. *Diesen Fehler habe ich beim ersten
        Anlauf gemacht.*
    """
    _pruefe(soll, karte, "iou_gegen_soll")
    lage = teile_auf(soll)
    markiert = tiefenschaetzer.markiere_hintergrund(
        karte, polaritaet=POLARITAET_TIEFEN_PNG, strategie=strategie,
        n_geometrie=lage["n_geometrie"], breite=breite, hoehe=hoehe)
    rho = geometrie_qa.spearman([soll[i] for i in lage["geometrie"]],
                                [karte[i] for i in lage["geometrie"]])
    return {
        "iou": geometrie_qa.iou(lage["silhouette"],
                                geometrie_qa.silhouette(markiert["tiefen"])),
        "rho_geometrie": abs(rho),
        "strategie": strategie,
        "anteil_hintergrund": markiert["anteil_hintergrund"],
    }


def rauschen_auf_geometrie(soll: Sequence[float], karte: Sequence[float], staerke: float,
                           *, saat: int = 1) -> list[float]:
    """**Fall A** — Rauschen nur auf die Geometriepunkte, Hintergrund bleibt perfekt.

    Bildet den Fehler nach, den man beim Schätzer zuerst vermutet: eine ungenauere
    Tiefenordnung *innerhalb* des Bauwerks. ``staerke`` ist ein Anteil der Wertespanne.
    """
    if staerke < 0:
        raise DeckelError(f"staerke darf nicht negativ sein: {staerke}")
    _pruefe(soll, karte, "rauschen_auf_geometrie")
    lage = teile_auf(soll)
    spanne = max(karte) - min(karte)
    wuerfel = random.Random(saat)
    neu = list(karte)
    for i in lage["geometrie"]:
        neu[i] += wuerfel.gauss(0, staerke * spanne)
    return neu


def hintergrund_verschieben(soll: Sequence[float], karte: Sequence[float],
                            anteil: float) -> list[float]:
    """**Fall B** — der Hintergrund rückt in den Wertebereich des Bauwerks.

    ``anteil`` 0.0 legt ihn an den fernsten Bauwerkswert, 1.0 an den nächsten. Die
    Geometriepunkte bleiben **unangetastet**; ihre Rangkorrelation bleibt exakt 1.0, und
    genau das ist der Punkt der Übung.

    Bildet nach, was relative Tiefenschätzer wirklich tun: Sie bilden auf einen
    beschränkten Bereich ab und haben für *unendlich weit* keinen Wert.
    """
    if not 0.0 <= anteil <= 1.0:
        raise DeckelError(f"anteil gehört in [0, 1], war {anteil}")
    _pruefe(soll, karte, "hintergrund_verschieben")
    lage = teile_auf(soll)
    if not lage["geometrie"] or not lage["hintergrund"]:
        raise DeckelError(
            "Diese Szene hat entweder keine Geometrie oder keinen Hintergrund — dann "
            "gibt es nichts zu verschieben."
        )
    werte = [karte[i] for i in lage["geometrie"]]
    # Bei Disparität ist NAH gross: der fernste Bauwerkswert ist das Minimum.
    ziel = min(werte) + anteil * (max(werte) - min(werte))
    neu = list(karte)
    for i in lage["hintergrund"]:
        neu[i] = ziel
    return neu


def wo_liegt_der_himmel(soll: Sequence[float], karte: Sequence[float]) -> dict:
    """Wo liegt der Hintergrund im Wertebereich des Bauwerks? — die eine Zahl.

    Sie ist die **Vorhersage dieser Studie und ihre Prüfgrösse**: Aus dem gemessenen
    ``geom_iou`` von 0.406 folgt nach Fall B ein Wert um 0.55–0.60. Wer den echten
    Schätzer laufen lässt, kann sie direkt nachrechnen.

    Returns:
        ``{lage, median_hintergrund, bauwerk_min, bauwerk_max, ausserhalb}``. ``lage`` ist
        0.0 am fernsten und 1.0 am nächsten Bauwerkswert; ``ausserhalb`` sagt, ob der
        Hintergrund ganz unterhalb liegt — dann ist er sauber getrennt und die Regel
        greift.
    """
    _pruefe(soll, karte, "wo_liegt_der_himmel")
    lage = teile_auf(soll)
    if not lage["geometrie"] or not lage["hintergrund"]:
        raise DeckelError("Ohne Geometrie oder ohne Hintergrund gibt es keine Lage.")
    werte = sorted(karte[i] for i in lage["geometrie"])
    hg = sorted(karte[i] for i in lage["hintergrund"])
    median = hg[len(hg) // 2]
    tief, hoch = werte[0], werte[-1]
    spanne = hoch - tief
    return {
        "lage": None if spanne == 0 else (median - tief) / spanne,
        "median_hintergrund": median,
        "bauwerk_min": tief,
        "bauwerk_max": hoch,
        "ausserhalb": median < tief,
    }


__all__ = [
    "POLARITAET_TIEFEN_PNG", "DeckelError",
    "hintergrund_verschieben", "iou_gegen_soll", "rauschen_auf_geometrie",
    "teile_auf", "wo_liegt_der_himmel",
]
