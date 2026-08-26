"""Sonnenstand → Blender-Drehung. Reine Arithmetik, diesseits der Prozessgrenze.

Warum es dieses Modul gibt
--------------------------
**Der Sonnenstand einer Bestellung wurde bis zum 26.08.2026 gar nicht bedient.** Der
Runner setzte eine feste Sonne, und ein Auftrag mit Abendstand wurde gerendert, als wäre
er nicht gestellt worden — mit einem sauberen, gut belichteten, **falschen** Bild. Das ist
der gefährlichste der stehengebliebenen Felder gewesen, weil nichts daran nach einem
Fehler aussieht (`kosmo_szene.STEHENGEBLIEBEN`).

Gemeldet hat es die HomeStation aus dem ersten vollständigen Kettenlauf
(`auf-vis-20260825-15`, Posten 5.3, und `auf-vis-20260826-16`).

**Warum die Rechnung hier steht und nicht im Runner** (Regel 4): Sie ist reine
Trigonometrie. Im Runner wäre sie eine Fähigkeit, die ohne Blender niemand hätte — und
ohne Blender auch niemand prüfen könnte. Der Runner ruft sie auf, wenn er dieses Modul
erreicht, und sagt es im Bericht, wenn nicht.

Der Fund, der beim Bauen abfiel
-------------------------------
Die feste Sonne stand im Runner als ``rotation_euler = (radians(50), 0, radians(35))``,
mit dem Kommentar *«50° Höhe und 35° Azimut»*. **Die 50° sind nicht die Höhe.**

Eine Blender-Sonne strahlt in Richtung ``−Z`` ihrer eigenen Achsen. Eine Drehung um X
kippt diese Richtung, und der Winkel über dem Horizont ist danach ``90° − rx``. Die feste
Sonne stand also auf **40°** über dem Horizont, nicht auf 50. Ein Kommentar ist keine
Rechnung — dasselbe wie ein Docstring, der eine Prüfung behauptet.

Die offene Frage, und sie ist nicht unsere
------------------------------------------
Woher der **Azimut** zählt, sagt nur der fremde Vertrag. Zwei Konventionen sind üblich
und unterscheiden sich um 180 Grad, was Vormittag und Nachmittag vertauscht:

* :data:`AZIMUT_VON_SUEDEN` — 0° = Süden, positiv nach Westen. Die Konvention der
  Architektur und der Bauphysik.
* :data:`AZIMUT_VON_NORDEN` — 0° = Norden, positiv nach Osten. Die Konvention der
  Meteorologie und der meisten Karten.

**Geraten wird nicht.** Es gilt :data:`VORGABE_KONVENTION`, und die benutzte Konvention
wandert **in den Bericht**. Wer später ein Bild ansieht, sieht ihm an, unter welcher
Annahme es entstand — und ein falsch gewählter Nullpunkt ist damit auffindbar statt
unsichtbar. Gefragt ist er bei KosmoOrbit.

Das Weltsystem, das hier vorausgesetzt wird
-------------------------------------------
``+Y`` ist Norden, ``+X`` ist Osten, ``+Z`` ist oben — Blenders Z-up nach der Drehung,
die der Runner vornimmt. Das ist eine **Setzung**, keine Messung; sie steht in
:data:`WELTSYSTEM` und wandert ebenfalls in den Bericht.
"""
from __future__ import annotations

import math

#: Azimut zählt von **Süden**, positiv nach Westen (Architektur, Bauphysik).
AZIMUT_VON_SUEDEN = "von_sueden"

#: Azimut zählt von **Norden**, positiv nach Osten (Meteorologie, Karten).
AZIMUT_VON_NORDEN = "von_norden"

KONVENTIONEN = (AZIMUT_VON_SUEDEN, AZIMUT_VON_NORDEN)

#: Welche Konvention gilt, solange der fremde Vertrag es nicht sagt.
#:
#: **Süden**, weil die feste Sonne des Runners so gemeint war. Die Vorgabe hält damit das
#: bisherige Verhalten ein, statt jedes Bild dieses Projekts um 180 Grad zu drehen.
#:
#: Es ist eine **Setzung und keine Messung** — siehe Modulkopf.
VORGABE_KONVENTION = AZIMUT_VON_SUEDEN

#: Welche Achse wohin zeigt. Setzung, keine Messung; wandert in den Bericht.
WELTSYSTEM = "+Y=Norden, +X=Osten, +Z=oben"

#: Die feste Sonne, die der Runner bis zum 26.08.2026 unbedingt setzte — in **richtigen**
#: Zahlen. Sie stand als ``rotation_euler = (radians(50), 0, radians(35))`` da, mit dem
#: Kommentar *«50° Höhe und 35° Azimut»*. **Beide Zahlen im Kommentar sind falsch**, und
#: der zweite Fehler ist nur durch Nachrechnen aufgefallen:
#:
#: * ``rx = 50°`` sind **40°** über dem Horizont, nicht 50 (siehe Modulkopf).
#: * ``rz = 35°`` stellt die Sonne 35° **östlich** von Süden. In der Süd-Konvention, die
#:   positiv nach Westen zählt, ist das **−35°** und nicht +35.
#:
#: Nachgerechnet und nicht geglaubt: `tests/test_sonne.py` misst die Strahlrichtung
#: zurück und hält beide Zahlen gegen die alte feste Drehung.
VORGABE_HOEHE_GRAD = 40.0
VORGABE_AZIMUT_GRAD = -35.0

#: Kurzform des Rechenwegs, wandert in jedes Ergebnis. Dieselbe Bauart wie
#: ``geometrie_qa.METHODE``.
METHODE = ("Sonnenrichtung = Blender-SUN strahlt -Z; rx = 90-Hoehe, rz aus Azimut nach "
           "Konvention, v1")


class SonnenError(ValueError):
    """Ein Sonnenstand, der so nicht gemeint sein kann."""


def _grad(wert, name: str) -> float:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise SonnenError(f"{name} muss eine Zahl in Grad sein, war {wert!r}.")
    zahl = float(wert)
    if zahl != zahl or zahl in (float("inf"), float("-inf")):
        raise SonnenError(f"{name} ist nan oder inf.")
    return zahl


def blender_euler(hoehe_grad, azimut_grad, *,
                  konvention: str = VORGABE_KONVENTION) -> tuple[float, float, float]:
    """``(rx, ry, rz)`` in **Radiant** für ``sonne.rotation_euler``.

    Args:
        hoehe_grad: Winkel **über dem Horizont**. 0 ist der Horizont, 90 der Zenit.
        azimut_grad: Himmelsrichtung nach ``konvention``.
        konvention: Einer von :data:`KONVENTIONEN`.

    Returns:
        Die drei Eulerwinkel in Blenders XYZ-Reihenfolge. ``ry`` ist immer ``0.0``: Eine
        Drehung um die eigene Strahlrichtung ändert bei einem Richtungslicht nichts.

    Raises:
        SonnenError: Höhe ausserhalb ``[-90, 90]``, unbekannte Konvention, oder eine der
            Angaben ist keine Zahl.

    .. note::
       **Eine negative Höhe ist zugelassen und wird nicht abgefangen.** Eine Sonne unter
       dem Horizont ist Nacht, und das ist eine gültige Bestellung — nur eben eine, die
       ein dunkles Bild ergibt. Wer sie verböte, entschiede über die Gestaltung; wer sie
       stillschweigend auf null höbe, lieferte etwas anderes als bestellt.
    """
    if konvention not in KONVENTIONEN:
        raise SonnenError(
            f"Unbekannte Azimutkonvention {konvention!r}. Bekannt: "
            f"{', '.join(KONVENTIONEN)}. Es gibt hier keinen stillen Rückfall — welche "
            f"gilt, entscheidet über Vormittag und Nachmittag.")

    hoehe = _grad(hoehe_grad, "hoehe_grad")
    azimut = _grad(azimut_grad, "azimut_grad")
    if not (-90.0 <= hoehe <= 90.0):
        raise SonnenError(
            f"hoehe_grad muss in [-90, 90] liegen, war {hoehe}. Grösser als 90 ist keine "
            f"höhere Sonne, sondern eine, die hinter dem Zenit wieder herunterkommt — "
            f"und das ist mit ziemlicher Sicherheit ein Vorzeichen- oder Einheitenfehler.")

    # Blenders SUN strahlt entlang -Z. rx kippt die Strahlrichtung aus der Senkrechten:
    # bei rx = 0 kommt das Licht von genau oben, bei rx = 90 waagrecht. Der Winkel ÜBER
    # dem Horizont ist darum 90 - rx.
    rx = math.radians(90.0 - hoehe)

    # rz dreht die waagrechte Komponente. Bei rz = 0 zieht das Licht nach +Y (Norden),
    # die Sonne steht also im SÜDEN. Das ist der Nullpunkt der Süd-Konvention; positives
    # rz schiebt die Sonne nach OSTEN, positiver Azimut aber nach Westen.
    if konvention == AZIMUT_VON_SUEDEN:
        # Positiver Azimut heisst hier nach WESTEN, rz schiebt nach Osten — daher das
        # Minus. Ohne es lägen Vormittag und Nachmittag vertauscht.
        rz = math.radians(-azimut)
    else:
        # Von Norden, positiv nach Osten: 0 im Norden ist 180 von Süden aus.
        rz = math.radians(180.0 - azimut)
    return (rx, 0.0, rz)


def lage(hoehe_grad=None, azimut_grad=None, *,
         konvention: str = VORGABE_KONVENTION) -> dict:
    """Der vollständige Sonnenbefund für den Bericht — auch wenn nichts bestellt war.

    Fehlende Angaben werden mit :data:`VORGABE_HOEHE_GRAD` und
    :data:`VORGABE_AZIMUT_GRAD` gefüllt, und ``bestellt`` sagt, was davon wirklich
    bestellt war. **Der Unterschied gehört in den Bericht:** Ein Bild mit der Vorgabe
    sieht genauso aus wie eines mit einer zufällig gleichen Bestellung, und nur dieses
    Feld unterscheidet sie.

    Returns:
        ``{hoehe_grad, azimut_grad, konvention, bestellt, euler, weltsystem, methode}``.
    """
    bestellt = tuple(name for name, wert in
                     (("hoehe", hoehe_grad), ("azimut", azimut_grad)) if wert is not None)
    hoehe = VORGABE_HOEHE_GRAD if hoehe_grad is None else hoehe_grad
    azimut = VORGABE_AZIMUT_GRAD if azimut_grad is None else azimut_grad
    euler = blender_euler(hoehe, azimut, konvention=konvention)
    return {"hoehe_grad": float(hoehe), "azimut_grad": float(azimut),
            "konvention": konvention, "bestellt": bestellt, "euler": euler,
            "weltsystem": WELTSYSTEM, "methode": METHODE}


def aus_bestellung(sonne, *, konvention: str = VORGABE_KONVENTION) -> dict:
    """Der Sonnenblock des fremden Vertrags (``{elevation, azimuth}``) → :func:`lage`.

    ``None`` oder ein leerer Block ergeben die Vorgabe mit ``bestellt = ()``. Ein Block
    mit unbrauchbaren Zahlen wirft — **nicht** stillschweigend die Vorgabe: Wer eine
    Sonne bestellt und eine andere bekommt, merkt es am Bild nicht.
    """
    if not isinstance(sonne, dict):
        return lage(konvention=konvention)
    return lage(sonne.get("elevation"), sonne.get("azimuth"), konvention=konvention)


__all__ = [
    "AZIMUT_VON_NORDEN", "AZIMUT_VON_SUEDEN", "KONVENTIONEN", "METHODE",
    "SonnenError", "VORGABE_AZIMUT_GRAD", "VORGABE_HOEHE_GRAD", "VORGABE_KONVENTION",
    "WELTSYSTEM", "aus_bestellung", "blender_euler", "lage",
]
