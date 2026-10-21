"""BAUMASSE — baut das Bildmodell über den Umriss des Hauses hinaus?

**Anlass (auf-20261020-294, B6):** Bei «voll» machte das Bildmodell aus der von der Seite
gesehenen Geländeplatte ein Gebäude über die ganze Bildbreite; nur der Mittelteil lag im
Umriss. Die Zahlen sahen das nicht: ``geom_iou`` (0,51) misst die Überdeckung zweier
Silhouetten, die per Bauart gleich gross gewählt sind, und die Umriss-IoU der HomeStation
zählte nur in einem Streifen von 30 Bildpunkten um die Maske. Was weiter weg gebaut wurde,
stand in keiner Zahl.

**Die Zahl (geeicht an auf-20261021-297, 21.10.2026):** Wieviel *neue Baumasse oder andere
Struktur* das Bild dort zeigt, wo das Modell Himmel hat — gelesen an der Karte, die der
Tiefenschätzer aus dem KI-Bild liest:

* **Bereich** sind die Bildpunkte, an denen das Soll **Hintergrund** ist (kein Bauteil, keine
  Platte), ohne den gedachten Boden (``trennhilfe``; ohne ihn: nur Zeilen über dem Fuss des
  Hauses), ohne ausgeblendete Umgebung und ohne einen Rand von :func:`rand_px` Punkten um
  die Soll-Silhouette (dort verwischt jeder Schätzer die Kante).
* **Neu** ist ein Punkt des Bereichs, der **nicht Himmel** ist: Seine Nähe liegt über
  :data:`HIMMEL_NAEHE_ANTEIL` (ein Zwanzigstel) der Nähe, ab der das Haus beginnt (das ferne
  :data:`HAUS_QUANTIL` der Nähe auf dem Haus). Depth Anything V2 legt den Himmel und die Wolken
  auf null oder darunter (an den Bildern aus 295–297: kleinster Wert −0,29 bis −0,11 dieser
  Grenze, der Himmelsanteil des Bereichs ändert sich zwischen 0,01 und 0,15 um weniger als
  drei Hundertstel). Eine Häuserzeile, die hinter dem Haus zurückweicht, zählt damit mit —
  ebenso Bäume, Hecken und ferne Hügel, wie in der Nachzählung der HomeStation.
* **Rückfall, wenn das Bild keinen Himmel hat:** Liegt weniger als
  :data:`MINDEST_HIMMEL_ANTEIL` (2 %) des Bereichs am Himmel, hat das Bildmodell den Himmel
  durch eine geschlossene Wand ersetzt — beim Gipsmodell «weiss» eine Studio-, Fels- oder
  Höhlenwand. «Nicht Himmel» wäre dort alles (4,65-mal die Hausfläche), obwohl kein Gebäude
  daneben steht. Dann zählt, wie bis 297, nur, was **so nah wie das Haus** ist (Nähe ≥ der
  Grenze des Hauses), ``verfahren`` sagt welcher Weg, ``verfahren_grund`` warum.
* ``anteil_haus`` = neu ÷ Punkte des Hauses — «so viel Baumasse ausserhalb, wie das Haus
  selbst gross ist» (1,0) —, ``anteil_hintergrund`` = neu ÷ Bereich. Daneben stehen zum
  Vergleich ``anteil_haus_nah`` (die alte Zählung «so nah wie das Haus») und
  ``himmel_anteil``.

**Warum die alte Zählung zu klein war (auf-20261021-297, N2):** Sie zählte nur, was näher
als das ferne Fünftel des Hauses lag. Die Nähe auf dem Haus liegt aber eng beisammen (3d:
2,04 bis 2,47), und eine Zeile, die nur wenig hinter dem Haus steht (3d: 2,0 bis 2,1), fiel
durch: 0,30 gemeldet, nachgezählt 2,22. Ein breiteres Band hilft nicht — bei 0,7 der Grenze
zählt das Gipsmodell 4z schon 2,93 (Felswand), 3d erst 1,37. Die Eichungstabelle steht im
Protokoll 74 §169.

**Wie gross die Zahl werden kann (geprüft an auf-20261020-295, 21.10.2026):** ``anteil_haus``
ist auf die Fläche des **Hauses** bezogen, nicht auf das Bild — er ist darum **grösser als 1**,
sobald ausserhalb mehr gebaut ist, als das Haus selbst Fläche hat, und höchstens
``n_bereich ÷ n_haus`` (bei der 960-Grundlage von 295: 271'498 ÷ 58'589 ≈ 4,6). Die Werte 0,68–2,09
aus 295 sind so zu lesen: 0,7- bis 2-mal die Hausfläche. Was nicht mitzählt, steht oben: Die
Platte ist Soll-Geometrie, der Boden unter dem Fuss des Hauses liegt ausserhalb des Bereichs.
Nachgezählt an den Bildern von 295 (Bildpunkte im Bereich, die nicht Himmel sind): 49–55 % des
Bereichs bei mittag und winter, gemeldet waren bis 297 15–23 % (``anteil_hintergrund``) — die
alte Zählung zählte **zu wenig**; seit der Eichung sind es 44–49 % (2,0–2,3 der Hausfläche).
Dass alle sieben KI-Bilder über 0,25 lagen, stimmt mit dem Bild überein: Alle bauen sichtbar
über die ganze Bildbreite.

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

__all__ = ["HAUS_QUANTIL", "HIMMEL_NAEHE_ANTEIL", "MINDEST_HIMMEL_ANTEIL", "RAND_ANTEIL",
           "RAND_MIN_PX", "SCHWELLE_ANTEIL_HAUS", "HERKUNFT", "VERFAHREN", "VERFAHREN_RUECKFALL",
           "rand_px", "erweitere", "ausserhalb_umriss"]

#: Ab welcher Nähe ein Punkt «so nah wie das Haus» ist: das ferne Fünftel der Nähe auf dem
#: Haus. Nicht das Minimum — ein einzelner falsch geschätzter Punkt auf dem Haus zöge sonst
#: die ganze Schwelle in den Himmel.
HAUS_QUANTIL = 0.20
#: Unter welchem Bruchteil der Hausgrenze ein Punkt Himmel ist: ein Zwanzigstel. Geeicht an
#: auf-20261021-297: Der Himmel liegt bei Depth Anything V2 bei null oder darunter, die
#: fernste Wand eines Gipsmodell-Bilds (296 4a) bei 0,14 — 0,05 liegt sicher dazwischen.
HIMMEL_NAEHE_ANTEIL = 0.05
#: Unter diesem Himmelsanteil des Bereichs hat das Bild keinen Himmel (Studio-, Fels- oder
#: Höhlenwand); dann gilt der Rückfall. Gemessen: Gipsmodelle 0,000, Aussenbilder 0,078 (abend
#: voll, unter einem Vordach) bis 0,58.
MINDEST_HIMMEL_ANTEIL = 0.02
#: Der Rand um die Soll-Silhouette, der nicht zählt — als Anteil der langen Bildseite.
RAND_ANTEIL = 0.02
RAND_MIN_PX = 3
#: Ab welchem Anteil (Baumasse ausserhalb ÷ Haus) der Satz im Ergebnis steht.
SCHWELLE_ANTEIL_HAUS = 0.25
#: Woher die Schwellen kommen.
HERKUNFT = ("Schwelle 0,25 gesetzt, nicht gemessen (auf-20261020-294, B6), an 295–297 "
            "geprüft; die Zählung «nicht Himmel» geeicht an der Nachzählung aus "
            "auf-20261021-297 (Protokoll 74 §169)")
#: Der Weg seit 297: alles, was im Soll-Hintergrund nicht Himmel ist.
VERFAHREN = "nicht_himmel_aus_tiefe_im_soll_hintergrund"
#: Der Weg bis 297, heute der Rückfall ohne Himmel: was so nah wie das Haus ist.
VERFAHREN_RUECKFALL = "tiefe_naeher_als_haus_im_soll_hintergrund"


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
        haus_quantil, verfahren, herkunft, grund, himmel_grenze, himmel_anteil, n_nah,
        anteil_haus_nah, verfahren_grund}`` — die Anteile ``None`` mit ``grund``, wenn nicht
        messbar. ``verfahren`` ist :data:`VERFAHREN` («nicht Himmel») oder
        :data:`VERFAHREN_RUECKFALL` («so nah wie das Haus», ohne Himmel im Bild).
    """
    b, h = int(breite), int(hoehe)
    n = b * h
    aus = {"anteil_haus": None, "anteil_hintergrund": None, "n_neu": None,
           "n_bereich": None, "n_haus": None, "rand_px": rand_px(b, h),
           "schwelle_naehe": None, "haus_quantil": HAUS_QUANTIL, "verfahren": VERFAHREN,
           "herkunft": HERKUNFT, "grund": "", "himmel_grenze": None, "himmel_anteil": None,
           "n_nah": None, "anteil_haus_nah": None, "verfahren_grund": ""}
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
    # Himmel nur, wenn die Grenze des Hauses positiv ist (Disparitaet: Himmel bei null).
    himmel_grenze = HIMMEL_NAEHE_ANTEIL * schwelle if schwelle > 0 else None
    bereich = 0
    nah = 0
    himmel = 0
    nicht_himmel = 0
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
        if not math.isfinite(wert):
            if wert == -math.inf:
                himmel += 1                     # unendlich fern: Himmel
            continue
        if wert >= schwelle:
            nah += 1
        if himmel_grenze is not None:
            if wert < himmel_grenze:
                himmel += 1
            else:
                nicht_himmel += 1
    himmel_anteil = (himmel / bereich) if bereich else None
    if himmel_grenze is None:
        neu, verfahren = nah, VERFAHREN_RUECKFALL
        grund_weg = ("Die Nähe auf dem Haus ist nicht positiv — ohne Disparität kein Himmel "
                     "bei null; gezählt ist, was so nah wie das Haus ist.")
    elif himmel_anteil is not None and himmel_anteil >= MINDEST_HIMMEL_ANTEIL:
        neu, verfahren, grund_weg = nicht_himmel, VERFAHREN, ""
    else:
        neu, verfahren = nah, VERFAHREN_RUECKFALL
        grund_weg = (f"Kein Himmel im Bild (unter {MINDEST_HIMMEL_ANTEIL * 100:.0f} % des "
                     f"Bereichs): Das Bildmodell hat ihn durch eine Wand ersetzt (Studio, Fels); "
                     f"gezählt ist, was so nah wie das Haus ist.")
    aus.update(n_neu=neu, n_bereich=bereich, n_haus=len(haus_naehe),
               schwelle_naehe=round(schwelle, 6),
               anteil_haus=round(neu / len(haus_naehe), 4),
               anteil_hintergrund=(round(neu / bereich, 4) if bereich else None),
               verfahren=verfahren, verfahren_grund=grund_weg,
               himmel_grenze=(round(himmel_grenze, 6) if himmel_grenze is not None else None),
               himmel_anteil=(round(himmel_anteil, 4) if himmel_anteil is not None else None),
               n_nah=nah, anteil_haus_nah=round(nah / len(haus_naehe), 4))
    if not bereich:
        aus["grund"] = "Kein Hintergrund neben dem Haus — der Anteil am Hintergrund fehlt."
    return aus
