"""BAUMASSE — baut das Bildmodell über den Umriss des Hauses hinaus?

**Anlass (auf-20261020-294, B6):** Bei «voll» machte das Bildmodell aus der von der Seite
gesehenen Geländeplatte ein Gebäude über die ganze Bildbreite; nur der Mittelteil lag im
Umriss. Die Zahlen sahen das nicht: ``geom_iou`` (0,51) misst die Überdeckung zweier
Silhouetten, die per Bauart gleich gross gewählt sind, und die Umriss-IoU der HomeStation
zählte nur in einem Streifen von 30 Bildpunkten um die Maske. Was weiter weg gebaut wurde,
stand in keiner Zahl.

**Die Zahl:** Wieviel *neue Baumasse* das Bild dort zeigt, wo das Modell Himmel hat —
gemessen an der Tiefe, die der Tiefenschätzer aus dem KI-Bild liest:

* **Bereich** sind die Bildpunkte, an denen das Soll **Hintergrund** ist (kein Bauteil, keine
  Platte), ohne den gedachten Boden (``trennhilfe``; ohne ihn: nur Zeilen über dem Fuss des
  Hauses), ohne ausgeblendete Umgebung und ohne einen Rand von :func:`rand_px` Punkten um
  die Soll-Silhouette (dort verwischt jeder Schätzer die Kante).
* **Neu** ist ein Punkt des Bereichs, den der Schätzer **so nah wie das Haus** sieht: näher
  als das ferne :data:`HAUS_QUANTIL` der Nähe, die er auf dem Haus selbst misst. Ein Berg
  oder Wolken stehen weiter weg und zählen nicht; ein angebauter Flügel steht daneben und
  zählt.
* ``anteil_haus`` = neu ÷ Punkte des Hauses — «so viel Baumasse ausserhalb, wie das Haus
  selbst gross ist» (1,0) —, ``anteil_hintergrund`` = neu ÷ Bereich.

**Was die Zahl nicht ist:** kein Tor. Sie steht im Ergebnis als ``qa.ausserhalb_umriss_anteil``
mit einem Satz ab :data:`SCHWELLE_ANTEIL_HAUS` — gesetzt, nicht gemessen (Herkunft in
:data:`HERKUNFT`); ``auf-20261020-295`` misst sie an Bildern, die man ansehen kann. Ein
Schätzerfehler ist hier von einer Zutat des Bildmodells nicht zu unterscheiden (dieselbe
Grenze wie bei ``geom_iou``).

Reine Standardbibliothek, ohne Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math
from typing import Sequence

__all__ = ["HAUS_QUANTIL", "RAND_ANTEIL", "RAND_MIN_PX", "SCHWELLE_ANTEIL_HAUS", "HERKUNFT",
           "VERFAHREN", "rand_px", "erweitere", "ausserhalb_umriss"]

#: Ab welcher Nähe ein Punkt «so nah wie das Haus» ist: das ferne Fünftel der Nähe auf dem
#: Haus. Nicht das Minimum — ein einzelner falsch geschätzter Punkt auf dem Haus zöge sonst
#: die ganze Schwelle in den Himmel.
HAUS_QUANTIL = 0.20
#: Der Rand um die Soll-Silhouette, der nicht zählt — als Anteil der langen Bildseite.
RAND_ANTEIL = 0.02
RAND_MIN_PX = 3
#: Ab welchem Anteil (Baumasse ausserhalb ÷ Haus) der Satz im Ergebnis steht.
SCHWELLE_ANTEIL_HAUS = 0.25
#: Woher die Schwellen kommen.
HERKUNFT = ("gesetzt, nicht gemessen (auf-20261020-294, B6); die HomeStation misst in "
            "auf-20261020-295")
VERFAHREN = "tiefe_naeher_als_haus_im_soll_hintergrund"


def rand_px(breite: int, hoehe: int) -> int:
    """Der Rand in Bildpunkten: 2 % der langen Seite, mindestens 3 (960 px: 19, 480 px: 10)."""
    return max(RAND_MIN_PX, int(round(RAND_ANTEIL * max(int(breite), int(hoehe)))))


def erweitere(maske: Sequence[bool], breite: int, hoehe: int, r: int) -> list[bool]:
    """Eine Maske um ``r`` Punkte in jede Richtung erweitert (Quadrat, zwei Durchgänge).

    Je Zeile, dann je Spalte, mit laufender Summe — linear in der Bildgrösse, auch bei
    960 × 600 unter einer Sekunde.
    """
    b, h, r = int(breite), int(hoehe), int(r)
    if r <= 0:
        return [bool(v) for v in maske]
    zeilen = [False] * (b * h)
    for y in range(h):
        basis = y * b
        summe = sum(1 for x in range(min(r + 1, b)) if maske[basis + x])
        for x in range(b):
            zeilen[basis + x] = summe > 0
            rein, raus = x + r + 1, x - r
            if rein < b and maske[basis + rein]:
                summe += 1
            if raus >= 0 and maske[basis + raus]:
                summe -= 1
    aus = [False] * (b * h)
    for x in range(b):
        summe = sum(1 for y in range(min(r + 1, h)) if zeilen[y * b + x])
        for y in range(h):
            aus[y * b + x] = summe > 0
            rein, raus = y + r + 1, y - r
            if rein < h and zeilen[rein * b + x]:
                summe += 1
            if raus >= 0 and zeilen[raus * b + x]:
                summe -= 1
    return aus


def _quantil(werte, q: float):
    werte = sorted(werte)
    if not werte:
        return None
    i = min(len(werte) - 1, max(0, int(math.floor(q * (len(werte) - 1)))))
    return werte[i]


def ausserhalb_umriss(naehe: Sequence[float], soll_silhouette: Sequence[bool],
                      breite: int, hoehe: int, *, haus: Sequence[bool] | None = None,
                      trennhilfe: Sequence[bool] | None = None,
                      ausgeblendet: Sequence[bool] | None = None) -> dict:
    """Neue Baumasse ausserhalb des Umrisses — reine Rechnung, nie eine Ausnahme.

    Args:
        naehe: die geschätzte Karte des KI-Bilds, **grösser = näher** (Disparität; eine
            Tiefe vorher negieren), zeilenweise von oben.
        soll_silhouette: ``True``, wo das Soll Geometrie hat (Haus und Platte).
        haus: die Bauwerksmaske; ohne sie gilt die Soll-Silhouette als Haus.
        trennhilfe: der gedachte Boden (``abholer._mit_messboden``) — zählt nicht.
        ausgeblendet: ausgeblendete Umgebung (Splat) — zählt nicht.

    Returns:
        ``{anteil_haus, anteil_hintergrund, n_neu, n_bereich, n_haus, rand_px, schwelle_naehe,
        haus_quantil, verfahren, herkunft, grund}`` — die Anteile ``None`` mit ``grund``, wenn
        nicht messbar.
    """
    b, h = int(breite), int(hoehe)
    n = b * h
    aus = {"anteil_haus": None, "anteil_hintergrund": None, "n_neu": None,
           "n_bereich": None, "n_haus": None, "rand_px": rand_px(b, h),
           "schwelle_naehe": None, "haus_quantil": HAUS_QUANTIL, "verfahren": VERFAHREN,
           "herkunft": HERKUNFT, "grund": ""}
    if n <= 0 or len(naehe) != n or len(soll_silhouette) != n:
        aus["grund"] = "Karten und Bildgrösse passen nicht zusammen — nicht gemessen."
        return aus
    for name, liste in (("haus", haus), ("trennhilfe", trennhilfe),
                        ("ausgeblendet", ausgeblendet)):
        if liste is not None and len(liste) != n:
            aus["grund"] = f"{name} hat {len(liste)} statt {n} Werte — nicht gemessen."
            return aus
    hausmaske = [bool(v) for v in (haus if haus is not None else soll_silhouette)]
    haus_naehe = [float(naehe[i]) for i in range(n)
                  if hausmaske[i] and math.isfinite(float(naehe[i]))]
    if not haus_naehe:
        aus["grund"] = "Kein Haus im Bild — nichts, woran die Nähe zu messen wäre."
        return aus
    schwelle = _quantil(haus_naehe, HAUS_QUANTIL)
    rand = erweitere([bool(v) for v in soll_silhouette], b, h, aus["rand_px"])
    # Ohne gedachten Boden: nur ueber dem Fuss des Hauses — darunter malt jedes Bild Boden,
    # und der Boden vor dem Haus ist naeher als das Haus.
    fuss = max(i // b for i in range(n) if hausmaske[i])
    bereich = 0
    neu = 0
    for i in range(n):
        if rand[i] or soll_silhouette[i]:
            continue
        if ausgeblendet is not None and ausgeblendet[i]:
            continue
        if trennhilfe is not None:
            if trennhilfe[i]:
                continue
        elif i // b > fuss:
            continue
        bereich += 1
        wert = float(naehe[i])
        if math.isfinite(wert) and wert >= schwelle:
            neu += 1
    aus.update(n_neu=neu, n_bereich=bereich, n_haus=len(haus_naehe),
               schwelle_naehe=round(schwelle, 6),
               anteil_haus=round(neu / len(haus_naehe), 4),
               anteil_hintergrund=(round(neu / bereich, 4) if bereich else None))
    if not bereich:
        aus["grund"] = "Kein Hintergrund neben dem Haus — der Anteil am Hintergrund fehlt."
    return aus
