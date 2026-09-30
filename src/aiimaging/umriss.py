"""Umrisstreue aus den Bildkanten — ein Geometriemass OHNE Tiefenschätzer.

**Anlass (Owner-Entscheid «b», 30.09.2026).** Die HomeStation hat gemessen
(``auf-20260929-175``), dass ρ über der Bauwerksmaske an erzeugten Bildern weder frontal
noch diagonal trennt; das Paarurteil urteilt seither nicht mehr
(``geometrie_qa.PAARURTEIL_URTEILT``). Alle bisherigen Masse laufen über einen monokularen
Tiefenschätzer, und der hat ein **festes Ortsfeld** (``auf-vis-20260824-10``): Er legt in
jedes Bild eine Grundordnung, die mit dem Bild nichts zu tun hat. Eine graue Fläche bekam
darum in der «Ordnung an Tiefensprüngen» die Bestnote (``auf-20260924-172``).

**Die Frage dieses Moduls ist bescheidener und darum prüfbar:** Hat das erzeugte Bild dort
**Kanten**, wo die Soll-Geometrie **Sprünge** hat — am Umriss des Gebäudes und an den
Kanten zwischen Flächen verschiedener Tiefe? Gelesen wird nur das Bild selbst (Helligkeit,
Sobel-Gradient) und die Soll-Tiefenkarte aus Blender. Kein Schätzer, kein Ortsfeld.

Was zurückkommt, und wie es zu lesen ist
----------------------------------------
* ``trefferquote`` — welcher Anteil der Soll-Sprungkanten im Bild eine Kante in höchstens
  ``toleranz_px`` Pixeln Abstand hat.
* ``kantendichte`` — welcher Anteil **aller** Pixel im Bild Kante ist. Das ist der Zufall:
  Ein Bild aus lauter Kanten trifft jeden Umriss.
* ``abhebung`` — ``trefferquote / zufall``, wobei ``zufall`` die Trefferquote ist, die ein
  Bild mit derselben Kantendichte **ohne** Bezug zum Umriss hätte (die Dichte, aufgeweitet
  um die Toleranz). **Um 1 heisst: nicht besser als Zufall.** Eine graue Fläche hat keine
  Kanten und bekommt 0 — das ist der Unterschied zur «Ordnung an Tiefensprüngen».
* ``praezision`` — welcher Anteil der Bildkanten nahe an einer Soll-Sprungkante liegt.

**Nicht geeicht, nicht urteilend.** Ob und wo eine Schwelle trennt, misst erst die
HomeStation; bis dahin ist dies eine **Auskunft**. Gegen die graue und die verrauschte
Nullprobe ist es hier geprüft (``tests/test_umriss.py``).

Reine stdlib, kein numpy — dieselbe Regel wie ``geometrie_qa`` (Regel 4: der Kern ist
überall aufrufbar).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

#: Relativer Tiefensprung zwischen zwei Nachbarpixeln, ab dem eine Soll-Kante gilt: 5 %.
#: Eine Wandecke in 20 m Abstand mit 1 m Versatz springt um 5 %; eine schräg gesehene
#: Fläche ändert sich von Pixel zu Pixel um weit weniger. **Gesetzt, nicht gemessen.**
SPRUNG_RELATIV = 0.05

#: Werte an oder über dieser Grenze gelten als Hintergrund (Blender schreibt dort 1e10).
HINTERGRUND_AB_M = 1.0e6

#: Das Quantil der Gradientenstärken, über dem ein Bildpixel als Kante gilt. Adaptiv je
#: Bild, damit ein kontrastarmes Bild nicht kantenlos und ein kontrastreiches nicht nur
#: Kante ist. **Gesetzt, nicht gemessen.**
KANTEN_QUANTIL = 0.85

#: Kleinste Gradientenstärke (Helligkeit 0..1), die überhaupt Kante sein kann. Ohne sie
#: machte das Quantil aus Bildrauschen auf einer fast grauen Fläche Kanten.
KANTEN_MINDESTSTAERKE = 0.04

#: Abstand in Pixeln, in dem eine Bildkante eine Soll-Kante noch trifft (Schachbrettmass).
TOLERANZ_PX = 2

#: Das Verfahren, als Satz — für Berichte, damit eine Zahl ihre Herkunft mitträgt.
METHODE = ("umriss aus bildkanten: sobel auf luminanz, kanten ueber dem 0.85-quantil; "
           "soll-kanten an 5-%-tiefenspruengen; treffer innerhalb 2 px; abhebung = "
           "trefferquote / zufallserwartung; v1, nicht geeicht")


def _ist_hintergrund(wert: float) -> bool:
    return not math.isfinite(wert) or wert >= HINTERGRUND_AB_M


def sprungkanten(soll: Sequence[float], breite: int, hoehe: int, *,
                 sprung_relativ: float = SPRUNG_RELATIV) -> list[bool]:
    """Wo die Soll-Tiefenkarte springt: Umriss gegen Hintergrund und Tiefenstufen.

    Ein Pixel ist Kante, wenn es Geometrie trägt und ein Vierernachbar entweder Hintergrund
    ist oder um mehr als ``sprung_relativ`` (bezogen auf die nähere Tiefe) abweicht.
    """
    n = breite * hoehe
    if len(soll) != n:
        raise ValueError(f"Soll hat {len(soll)} Werte, erwartet {breite}x{hoehe}={n}.")
    kante = [False] * n
    for y in range(hoehe):
        for x in range(breite):
            i = y * breite + x
            d = soll[i]
            if _ist_hintergrund(d):
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < breite and 0 <= ny < hoehe):
                    continue
                q = soll[ny * breite + nx]
                if _ist_hintergrund(q) or abs(d - q) > sprung_relativ * min(d, q):
                    kante[i] = True
                    break
    return kante


def bildkanten(luminanz: Sequence[float], breite: int, hoehe: int, *,
               quantil: float = KANTEN_QUANTIL,
               mindeststaerke: float = KANTEN_MINDESTSTAERKE) -> list[bool]:
    """Sobel-Kanten auf der Helligkeit, adaptiv je Bild — Randpixel sind nie Kante."""
    n = breite * hoehe
    if len(luminanz) != n:
        raise ValueError(f"Bild hat {len(luminanz)} Werte, erwartet {breite}x{hoehe}={n}.")
    staerke = [0.0] * n
    L = luminanz
    for y in range(1, hoehe - 1):
        o, m, u = (y - 1) * breite, y * breite, (y + 1) * breite
        for x in range(1, breite - 1):
            gx = (L[o + x + 1] + 2 * L[m + x + 1] + L[u + x + 1]
                  - L[o + x - 1] - 2 * L[m + x - 1] - L[u + x - 1])
            gy = (L[u + x - 1] + 2 * L[u + x] + L[u + x + 1]
                  - L[o + x - 1] - 2 * L[o + x] - L[o + x + 1])
            staerke[m + x] = math.hypot(gx, gy) / 4.0
    kandidaten = sorted(s for s in staerke if s >= mindeststaerke)
    if not kandidaten:
        return [False] * n
    # Das Quantil über ALLE Pixel, nicht nur über die Kandidaten — sonst würde ein Bild
    # mit wenigen, starken Kanten auf 15 % davon heruntergerechnet.
    rang = min(len(kandidaten) - 1,
               max(0, int(math.ceil(quantil * n)) - (n - len(kandidaten))))
    schwelle = max(mindeststaerke, kandidaten[rang] if rang >= 0 else mindeststaerke)
    return [s >= schwelle and s > 0 for s in staerke]


def _aufgeweitet(maske: list[bool], breite: int, hoehe: int, r: int) -> list[bool]:
    aus = [False] * (breite * hoehe)
    for i, an in enumerate(maske):
        if not an:
            continue
        y, x = divmod(i, breite)
        for ny in range(max(0, y - r), min(hoehe, y + r + 1)):
            zeile = ny * breite
            for nx in range(max(0, x - r), min(breite, x + r + 1)):
                aus[zeile + nx] = True
    return aus


def umriss_treue(luminanz: Sequence[float], soll: Sequence[float], breite: int,
                 hoehe: int, *, toleranz_px: int = TOLERANZ_PX) -> dict:
    """Trifft das Bild die Sprungkanten der Soll-Geometrie? — Siehe Moduldocstring.

    Returns:
        ``{status, trefferquote, kantendichte, zufall, abhebung, praezision,
        n_soll_kanten, n_bild_kanten, toleranz_px, methode, urteilt}``. ``urteilt`` ist
        immer ``False``: Die Zahl ist eine Auskunft, bis eine Messung eine Schwelle trägt.
        ``status`` ist ``"ok"``, ``"keine_soll_kanten"`` (nichts zu treffen — dann sind
        die Quoten ``None``) oder ``"keine_bildkanten"`` (Quoten 0, Abhebung 0).
    """
    soll_kante = sprungkanten(soll, breite, hoehe)
    bild_kante = bildkanten(luminanz, breite, hoehe)
    n = breite * hoehe
    n_soll = sum(soll_kante)
    n_bild = sum(bild_kante)
    antwort = {"status": "ok", "trefferquote": None, "kantendichte": n_bild / n,
               "zufall": None, "abhebung": None, "praezision": None,
               "n_soll_kanten": n_soll, "n_bild_kanten": n_bild,
               "toleranz_px": toleranz_px, "methode": METHODE, "urteilt": False}
    if n_soll == 0:
        antwort["status"] = "keine_soll_kanten"
        return antwort
    if n_bild == 0:
        antwort.update(status="keine_bildkanten", trefferquote=0.0, zufall=0.0,
                       abhebung=0.0, praezision=0.0)
        return antwort
    bild_nah = _aufgeweitet(bild_kante, breite, hoehe, toleranz_px)
    soll_nah = _aufgeweitet(soll_kante, breite, hoehe, toleranz_px)
    treffer = sum(1 for i in range(n) if soll_kante[i] and bild_nah[i])
    trefferquote = treffer / n_soll
    # DER ZUFALL, gleich gerechnet: Wie viele Pixel liegen in Toleranz-Nähe IRGENDEINER
    # Bildkante? Genau so oft trifft ein Umriss, der mit dem Bild nichts zu tun hat.
    zufall = sum(bild_nah) / n
    antwort.update(
        trefferquote=trefferquote, zufall=zufall,
        abhebung=(trefferquote / zufall) if zufall > 0 else 0.0,
        praezision=sum(1 for i in range(n) if bild_kante[i] and soll_nah[i]) / n_bild)
    return antwort


def umriss_aus_dateien(bild_png, soll: Sequence[float], breite: int, hoehe: int, *,
                       toleranz_px: int = TOLERANZ_PX) -> dict:
    """Dasselbe, mit dem Bild als Datei. Eine andere Bildgrösse ist ein Befund, kein Fehler."""
    from aiimaging import bildlesen

    luminanz, b, h = bildlesen.lies_png_luminanz(bild_png)
    if (b, h) != (breite, hoehe):
        return {"status": "groesse_passt_nicht", "urteilt": False, "methode": METHODE,
                "grund": f"Bild {b}x{h}, Soll {breite}x{hoehe} — verglichen wird indexweise, "
                         f"und Zuschneiden wäre eine stille Reparatur."}
    return umriss_treue(luminanz, soll, breite, hoehe, toleranz_px=toleranz_px)


__all__ = ["HINTERGRUND_AB_M", "KANTEN_MINDESTSTAERKE", "KANTEN_QUANTIL", "METHODE",
           "SPRUNG_RELATIV", "TOLERANZ_PX", "bildkanten", "sprungkanten",
           "umriss_aus_dateien", "umriss_treue"]
