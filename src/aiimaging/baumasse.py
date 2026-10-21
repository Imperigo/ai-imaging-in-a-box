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
           "rand_px", "erweitere", "ausserhalb_umriss",
           "HAUS_BAND_OBEN", "VERFAHREN_HAUS_IM_BILD", "HERKUNFT_HAUS_IM_BILD",
           "VERFAHREN_HAUS_IM_BILD_BAND", "WEIT_UNTEN", "WEIT_OBEN", "STUFE", "BODEN_STEIGUNG",
           "RAHMUNG_FAKTOR", "RAHMUNG_MINDEST_PUNKTE", "haus_im_bild", "rahmt_anders"]

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


# --------------------------------------------------------------------------------------
# DER HAUSANTEIL IM KI-BILD (Video-Befund L4-2, 21.10.2026)
# --------------------------------------------------------------------------------------
#
# Die Pruefung meldete «Das Haus fuellt nur 2.9 %» direkt neben einem KI-Bild, in dem das
# Haus sichtbar 15–20 % fuellt. Beide stimmten: Gemessen war nur die GRUNDLAGE (``anteil_soll``,
# aus der Blender-Tiefe), und die KI hatte den Ausschnitt «naeher» erfunden. Die Zahl sprach
# also ueber ein anderes Bild als das, neben dem sie stand. Seither stehen zwei Zahlen da.

#: Obere Grenze des Nähe-Bands, als Vielfaches des nahen Quantils (95 %) der Nähe auf dem
#: Haus: 10 % näher als die nächsten Punkte des Hauses zählt noch mit, Boden davor nicht mehr.
#: **Gesetzt, nicht gemessen.** Seit auf-20261021-312 nur noch der KERN, von dem aus gewachsen
#: wird (:data:`VERFAHREN_HAUS_IM_BILD`), und die alte Zahl ``n_band`` zum Vergleich.
HAUS_BAND_OBEN = 1.10
#: Das nahe Quantil der Nähe auf dem Haus — nicht das Maximum (ein Ausreisser zöge das Band
#: bis in den Vordergrund).
HAUS_QUANTIL_NAH = 0.95
#: DAS WEITE BAND, in dem das Haus wachsen darf (auf-20261021-312, B1): von der Hälfte des
#: fernen Fünftels bis 1,6 × des nahen Zwanzigstels. Ein Haus, das die KI grösser malt, reicht
#: mit seinen Flügeln weit vor und zurück — das enge Band schnitt sie ab (0,15 gemeldet gegen
#: 0,43 nachgezählt). **Gesetzt, nicht gemessen.**
WEIT_UNTEN = 0.5
WEIT_OBEN = 1.6
#: Wie viel sich die Nähe von einem Bildpunkt zum Nachbarn höchstens ändern darf, damit er
#: zum selben Körper zählt (Anteil der grösseren Nähe). Eine Fassade ändert sich stetig, die
#: Kante zu Hecke, Himmel oder fernem Bau springt. **Gesetzt, nicht gemessen.**
STUFE = 0.03
#: Ab welcher Steigung der Nähe je Bildzeile (abwärts, Anteil) ein Punkt BODEN ist: Eine
#: senkrechte Wand ändert ihre Nähe von Zeile zu Zeile kaum (bei 15° Neigung rund 0,03 %),
#: ebener Boden um 1 ÷ (Zeilen unter dem Horizont), also 0,3–1 %. **Gesetzt, nicht gemessen.**
BODEN_STEIGUNG = 0.0015
#: Über wie viele Zeilen die Steigung gemittelt wird — Anteil der Bildhöhe, mindestens 2.
BODEN_FENSTER_ANTEIL = 0.01
#: Der Weg, als Wort.
VERFAHREN_HAUS_IM_BILD = "stetig_gewachsen_vom_haus_ohne_boden_und_himmel"
#: Der Weg bis auf-20261021-312 — heute nur noch ``n_band`` zum Vergleich.
VERFAHREN_HAUS_IM_BILD_BAND = "naeheband_des_hauses_zusammenhaengend_mit_dem_soll"
#: Woher die Grenzen kommen.
HERKUNFT_HAUS_IM_BILD = (
    "Kern im Band [fernes Fuenftel, 1,10 x nahes Zwanzigstel] der Naehe auf der Bauwerksmaske "
    "(ohne Platte); gewachsen ueber Nachbarn mit hoechstens 3 % Naehesprung im Band "
    "[0,5 x, 1,6 x], ohne Himmel und ohne Boden (Steigung je Zeile ab 0,15 %); gesetzt, nicht "
    "gemessen (auf-20261021-312 B1/B2, synthetisch nachgestellt)")
#: Ab welchem Verhältnis (gross ÷ klein) der Satz «KI-BILD RAHMT ANDERS» steht: doppelt.
#: **Gesetzt; 312 widerspricht nicht** (nachgezählt: Seed 11 Faktor 1,1 bei gleichem
#: Ausschnitt, die drei anders gerahmten 2,6 / 3,8 / 4,7) — aber alle vier rechneten txt2img.
RAHMUNG_FAKTOR = 2.0
#: Und erst ab so vielen Prozentpunkten Unterschied — 1 % gegen 2,5 % sagt noch nichts.
RAHMUNG_MINDEST_PUNKTE = 0.05


def _bodenpunkte(naehe: Sequence[float], b: int, h: int) -> list[bool]:
    """``True``, wo die Nähe abwärts so steigt wie auf ebenem Boden (:data:`BODEN_STEIGUNG`)."""
    k = max(2, int(round(BODEN_FENSTER_ANTEIL * h)))
    boden = [False] * (b * h)
    for y in range(k, h - k):
        for x in range(b):
            i = y * b + x
            oben_w, unten_w, w = (float(naehe[i - k * b]), float(naehe[i + k * b]),
                                  float(naehe[i]))
            if not (math.isfinite(oben_w) and math.isfinite(unten_w) and math.isfinite(w)) \
                    or w <= 0:
                continue
            # Nur stetig: An der Kante zu Himmel oder Hecke springt die Nähe im Fenster —
            # das ist eine Kante, kein Boden.
            if abs(unten_w - w) > STUFE * k * w or abs(w - oben_w) > STUFE * k * w:
                continue
            boden[i] = (unten_w - oben_w) / (2 * k * w) >= BODEN_STEIGUNG
    return boden


def haus_im_bild(naehe: Sequence[float], soll_silhouette: Sequence[bool], breite: int,
                 hoehe: int, *, haus: Sequence[bool] | None = None,
                 trennhilfe: Sequence[bool] | None = None,
                 ausgeblendet: Sequence[bool] | None = None) -> dict:
    """Wieviel des KI-Bilds das Haus füllt — geschätzt aus der Tiefe, nie eine Ausnahme.

    **Warum nicht gezählt:** Für das KI-Bild gibt es keine Maske, nur die Karte des
    Tiefenschätzers.

    **Der Weg seit auf-20261021-312** (:data:`VERFAHREN_HAUS_IM_BILD`): Der KERN sind die Punkte
    der Bauwerksmaske (``haus``; ohne sie die Soll-Silhouette), deren Nähe im engen Band
    [fernes Fünftel, 1,10 × nahes Zwanzigstel] liegt. Von dort WÄCHST das Haus über Nachbarn
    (Vierer-Nachbarschaft), solange die Nähe stetig bleibt (:data:`STUFE`), im weiten Band
    (:data:`WEIT_UNTEN`, :data:`WEIT_OBEN`) liegt, kein Himmel ist (unter
    :data:`HIMMEL_NAEHE_ANTEIL` des fernen Fünftels) und kein Boden (:func:`_bodenpunkte`).

    **Warum (312 B1):** Bis dahin zählte nur, was im engen Band lag. Malt die KI das Haus
    grösser, reichen seine Flügel vor und zurück und fielen heraus: 0,153 / 0,159 / 0,180
    gemeldet gegen 0,435 / 0,305 / 0,474 nachgezählt; nur bei gleichem Ausschnitt (Seed 11)
    passte es. ``n_band`` trägt die alte Zahl zum Vergleich.

    **Und die Grundlage (312 B2):** ``anteil_grundlage``/``n_soll`` zählen die Bauwerksmaske,
    wenn sie da ist — die Soll-Silhouette trägt die Platte mit (60 m: 77016 = 66293 Haus +
    10723 Platte). ``grundlage_aus`` sagt, welche Fläche gezählt ist.

    Eine Schätzung — ein Fehler des Schätzers ist von einer Zutat des Bildmodells nicht zu
    unterscheiden. Hecken vor dem Haus fallen an der Kante heraus, ein anschliessender Bau gleicher
    Tiefe zählt mit; ein Steildach, das wie Boden ansteigt, fehlt.

    Returns:
        ``{anteil, anteil_grundlage, n_bild, n_soll, n_punkte, n_band, anteil_band, band,
        band_weit, grundlage_aus, verfahren, herkunft, grund}`` — ``anteil`` ``None`` mit
        ``grund``, wenn nicht messbar.
    """
    b, h = int(breite), int(hoehe)
    n = b * h
    aus = {"anteil": None, "anteil_grundlage": None, "n_bild": None, "n_soll": None,
           "n_punkte": n if n > 0 else None, "n_band": None, "anteil_band": None,
           "band": None, "band_weit": None, "grundlage_aus": None,
           "verfahren": VERFAHREN_HAUS_IM_BILD, "herkunft": HERKUNFT_HAUS_IM_BILD, "grund": ""}
    if n <= 0 or len(naehe) != n or len(soll_silhouette) != n:
        aus["grund"] = "Karten und Bildgrösse passen nicht zusammen — nicht gemessen."
        return aus
    for name, liste in (("haus", haus), ("trennhilfe", trennhilfe),
                        ("ausgeblendet", ausgeblendet)):
        if liste is not None and len(liste) != n:
            aus["grund"] = f"{name} hat {len(liste)} statt {n} Werte — nicht gemessen."
            return aus
    mit_maske = haus is not None and any(haus)
    soll = [bool(v) for v in (haus if mit_maske else soll_silhouette)]
    aus["grundlage_aus"] = "bauwerksmaske" if mit_maske else "soll_silhouette"
    n_soll = sum(soll)
    aus["n_soll"] = n_soll
    aus["anteil_grundlage"] = round(n_soll / n, 4)
    werte = [float(naehe[i]) for i in range(n) if soll[i] and math.isfinite(float(naehe[i]))]
    if not werte:
        aus["grund"] = "Kein Haus in der Grundlage — nichts, woran die Nähe zu messen wäre."
        return aus
    unten = _quantil(werte, HAUS_QUANTIL)
    nah = _quantil(werte, HAUS_QUANTIL_NAH)
    # Disparitaet: groesser = naeher. Ist die nahe Grenze nicht positiv, gibt es kein
    # «10 % naeher» — dann gilt sie selbst als obere Grenze (und das weite Band = das enge).
    positiv = nah > 0 and unten > 0
    oben = nah * HAUS_BAND_OBEN if nah > 0 else nah
    weit_unten, weit_oben = ((unten * WEIT_UNTEN, nah * WEIT_OBEN) if positiv
                             else (unten, oben))
    himmel = HIMMEL_NAEHE_ANTEIL * unten if unten > 0 else None
    aus["band"] = [round(unten, 6), round(oben, 6)]
    aus["band_weit"] = [round(weit_unten, 6), round(weit_oben, 6)]

    def frei(i: int) -> bool:
        return not ((trennhilfe is not None and trennhilfe[i])
                    or (ausgeblendet is not None and ausgeblendet[i]))

    def wert(i: int) -> float:
        return float(naehe[i])

    def im_band(i: int) -> bool:
        w = wert(i)
        return frei(i) and math.isfinite(w) and unten <= w <= oben

    def wachsen(start, darf) -> int:
        besucht = [False] * n
        stapel = list(start)
        for i in stapel:
            besucht[i] = True
        zahl = 0
        while stapel:
            i = stapel.pop()
            zahl += 1
            x, y = i % b, i // b
            for j, ok in ((i - 1, x > 0), (i + 1, x < b - 1), (i - b, y > 0),
                          (i + b, y < h - 1)):
                if ok and not besucht[j] and darf(i, j):
                    besucht[j] = True
                    stapel.append(j)
        return zahl

    kern = [i for i in range(n) if soll[i] and im_band(i)]
    # DIE ALTE ZAHL (bis 312), zum Vergleich: nur im engen Band, zusammenhaengend.
    n_band = wachsen(kern, lambda i, j: im_band(j))
    boden = _bodenpunkte(naehe, b, h) if positiv else [False] * n

    def stetig(i: int, j: int) -> bool:
        w = wert(j)
        if not (frei(j) and math.isfinite(w) and weit_unten <= w <= weit_oben):
            return False
        if boden[j] or (himmel is not None and w < himmel):
            return False
        gross = max(abs(w), abs(wert(i)))
        return gross > 0 and abs(w - wert(i)) <= STUFE * gross

    zahl = wachsen(kern, stetig) if positiv else n_band
    aus.update(n_bild=zahl, anteil=round(zahl / n, 4), n_band=n_band,
               anteil_band=round(n_band / n, 4))
    return aus


def rahmt_anders(anteil_grundlage, anteil_bild) -> bool | None:
    """Ob das KI-Bild das Haus deutlich anders rahmt als die Grundlage — ``None`` ohne Zahl.

    Ja ab :data:`RAHMUNG_FAKTOR` (doppelt oder halb so gross) **und**
    :data:`RAHMUNG_MINDEST_PUNKTE` Unterschied. Beides gesetzt, nicht gemessen.
    """
    zahlen = (anteil_grundlage, anteil_bild)
    if not all(isinstance(z, (int, float)) and not isinstance(z, bool) for z in zahlen):
        return None
    klein, gross = sorted(float(z) for z in zahlen)
    if gross - klein < RAHMUNG_MINDEST_PUNKTE:
        return False
    return klein <= 0 or gross / klein >= RAHMUNG_FAKTOR
