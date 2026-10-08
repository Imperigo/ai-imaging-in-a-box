"""MESSBODEN — eine gedachte Bodenfläche, nur für die Prüfung (Owner-Entscheid 78).

**Anlass ``auf-20261008-272``:** Die nähere Kamera zeigte die Halle auf 23–28 % des Bildes,
und ohne Umgebung sagte die Prüfung trotzdem «nicht messbar»: kein einziger gemeinsamer
Bildpunkt, bei einer Tiefenordnung auf dem Haus von 0,99. Das Modell hat keinen Boden, das
Bild aber schon; die Markierung des Hintergrunds nimmt den fernsten Anteil des Bildes, und
weil der Boden im Bild **näher** liegt als das Haus, wurde das Haus Hintergrund und der Boden
Geometrie. Synthetisch nachgestellt (Protokoll 74 §83): genau so, 0 gemeinsame Punkte.

**Entscheid 78 (Owner, 08.10.2026, per Auswahl): Messboden.** Hat das Modell keinen Boden,
rechnet die Prüfung mit einer gedachten Ebene auf Geländehöhe — **nur in der Soll-Karte der
Prüfung**. Das Tiefenbild für das Bildmodell bleibt, wie es ist; das Bild sieht die Ebene nie.

Die Rechnung ist reine Geometrie, ohne Blender (Regel 4): Für jeden Bildpunkt der Soll-Karte,
der Hintergrund ist, wird der Sehstrahl der Blender-Kamera mit der Ebene ``z = gelaende_z``
geschnitten. Die Kamera ist die des Berichts (``auge``, ``blick_auf``, Brennweite, Sensor
36 mm waagrecht, ``shift_y``) — dieselbe, die der Runner gestellt hat. Geprüft gegen echtes
Blender mit einer wirklichen Bodenplatte (``tests/test_messboden.py``).
"""
from __future__ import annotations

import math
from typing import Sequence

__all__ = ["MessbodenError", "mit_messboden", "sehstrahl"]

#: Ab dieser Entfernung gilt ein Schnittpunkt nicht mehr als Boden, sondern als Horizont.
#: GESETZT: dieselbe Grössenordnung wie die Hintergrundschranke der Tiefe, aber endlich
#: klein genug, dass ein streifender Strahl kurz unter dem Horizont nicht als «Boden in
#: 10 km» die Spanne der Soll-Karte bestimmt.
HORIZONT_M = 2000.0


class MessbodenError(ValueError):
    """Die Kamera des Berichts lässt sich nicht lesen — dann gibt es keinen Messboden."""


def _norm(v):
    n = math.sqrt(sum(c * c for c in v))
    if n == 0.0:
        raise MessbodenError("Nullvektor in der Kamera (Auge = Blickziel?).")
    return tuple(c / n for c in v)


def _kreuz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sehstrahl(kamera: dict, breite: int, hoehe: int, x: int, y: int):
    """Richtung (Welt, Z oben) durch die Mitte des Bildpunkts ``(x, y)``, oben links 0,0.

    Returns:
        ``(richtung_normiert, achse_normiert)`` — die zweite ist die Blickachse; mit ihr
        rechnet :func:`mit_messboden` die Tiefe als Abstand zur Bildebene.
    """
    auge = [float(v) for v in kamera["auge"]]
    ziel = [float(v) for v in kamera["blick_auf"]]
    f = float(kamera.get("brennweite_mm") or 50.0)
    sw = float(kamera.get("sensor_breite_mm") or 36.0)
    sh = sw * hoehe / breite
    shift = float(kamera.get("shift_y") or 0.0)
    vorn = _norm([z - a for z, a in zip(ziel, auge)])
    rechts = _norm(_kreuz(vorn, (0.0, 0.0, 1.0)))
    oben = _kreuz(rechts, vorn)
    px = ((x + 0.5) / breite - 0.5) * sw
    # Blenders shift ist ein Bruchteil der grösseren Sensorkante — hier waagrecht (sensor_fit).
    py = (0.5 - (y + 0.5) / hoehe) * sh + shift * sw
    d = [rechts[i] * px + oben[i] * py + vorn[i] * f for i in range(3)]
    return _norm(d), vorn


def mit_messboden(soll: Sequence[float], breite: int, hoehe: int, kamera: dict, *,
                  ebene_z: float | None = None, tiefe: str = "achse",
                  hintergrund_ab_m: float = 1.0e7) -> tuple[list[float], dict]:
    """Die Soll-Karte mit Messboden: Hintergrund unter dem Horizont wird Boden.

    Args:
        soll: flache Soll-Karte in Metern, zeilenweise von oben; Hintergrund ist, was nicht
            endlich ist oder ab ``hintergrund_ab_m`` liegt (Cycles schreibt ~1e10 ins Leere).
        kamera: der Kamerablock des Berichts.
        ebene_z: Höhe der Ebene; ``None`` nimmt ``kamera["gelaende_z"]``.
        tiefe: ``"achse"`` (Abstand zur Bildebene) oder ``"strahl"`` (Länge des Strahls) —
            je nachdem, was der Tiefenpass misst. Festgelegt am echten Blender-Lauf.

    Returns:
        ``(soll_neu, befund)`` mit ``befund = {ebene_z, n_boden, tiefe}``.
    """
    if len(soll) != breite * hoehe:
        raise MessbodenError(f"Soll hat {len(soll)} Werte, nicht {breite}×{hoehe}.")
    try:
        z0 = float(kamera["gelaende_z"] if ebene_z is None else ebene_z)
        auge = [float(v) for v in kamera["auge"]]
    except (KeyError, TypeError, ValueError) as fehler:
        raise MessbodenError(f"Kamera unvollständig: {fehler}") from fehler
    neu = list(soll)
    n = 0
    for y in range(hoehe):
        for x in range(breite):
            i = y * breite + x
            if math.isfinite(neu[i]) and 0.0 < neu[i] < hintergrund_ab_m:
                continue
            d, vorn = sehstrahl(kamera, breite, hoehe, x, y)
            if d[2] >= 0.0:
                continue                                    # über dem Horizont
            t = (z0 - auge[2]) / d[2]
            if t <= 0.0 or t > HORIZONT_M:
                continue
            neu[i] = t * sum(a * b for a, b in zip(d, vorn)) if tiefe == "achse" else t
            n += 1
    return neu, {"ebene_z": z0, "n_boden": n, "tiefe": tiefe}
