"""Umriss halten: ausserhalb des Hauses bleibt das Grundbild (Messschalter ``vis.umriss_halten``).

**Anlass** (Strang «Treue», 21.10.2026; Planblatt ``docs/PLAN_MATERIAL_UND_UMRISS_2026-10-21.md``):
Das Bildmodell baut fast immer über den Umriss hinaus — ``ausserhalb_umriss_anteil`` liegt
bei den Aussenbildern aus 295–300 bei rund 2,0–2,3, nur das Gipsmodell bleibt darin. Weder
der Zusatz «empty background, no other buildings» noch ``faithful`` 1,0 noch ein Negativprompt
(Führung 0,0) halten das Haus. Dieses Modul hält darum den Bereich **ausserhalb** des Hauses
fest: Dort gilt das Cycles-Bild der Grundlage (Himmel, Boden, Umgebung), innen malt die KI.

Zwei Arten, beide Messschalter, **Vorgabe aus**:

* ``nachher`` (:func:`halte_datei`) — Maskenmischung **nach** dem KI-Schritt. Rechnet ohne
  Grafikkarte, an jedem Bildmodell. Grenze: Die KI hat ohne Wissen um die Mischung gemalt;
  was sie neben das Haus gesetzt hat, wird abgeschnitten, nicht neu gemalt. An der Kante
  kann eine Naht stehen.
* ``im_lauf`` (:func:`halte_latenten`, angewandt in ``render._pipeline_adapter``) — der
  Hintergrund wird **in jedem Schritt** des Fahrplans auf das verrauschte Cycles-Bild
  zurückgesetzt (bekannt als «blended latent diffusion»). Das Modell sieht dabei in jedem
  Schritt, was neben dem Haus steht, und malt die Kante passend. Nur an Pipelines, die
  ``callback_on_step_end`` mit ``latents`` annehmen (Z-Image, gelesen an diffusers 0.39.0
  und am Stand 0.42.0.dev0).

**Was es nicht ist:** keine Formkorrektur **im** Haus. Was die KI innerhalb des Umrisses
falsch baut (Stufe Hauptbau/Anbau, Dachaufbau), bleibt. Und der Bereich ausserhalb ist danach
das Cycles-Bild — mit Stimmung ein Himmel mit Licht, ohne Stimmung der graue Hintergrund.

Die Bauwerksmaske kommt aus dem Material-ID-Pass (:func:`aiimaging.maske.maske_aus_bericht`):
``True``, wo das Bauwerk steht — ohne Gelände, ohne Umgebung (Splat). Gelände und Umgebung
sind Grundlage und bleiben damit, wie Cycles sie zeigt (E97: Grundlagen werden direkt
dargestellt). Um das Haus bleibt ein **Rand** frei (:data:`RAND_ANTEIL`, dieselbe Zahl, mit
der ``baumasse`` den Rand um die Silhouette auslässt), damit Dachkanten und Vorsprünge, die
die KI ein paar Bildpunkte versetzt, nicht abgeschnitten werden.

Abhängigkeiten: nur :mod:`aiimaging.bildlesen`, :mod:`aiimaging.bildschreiben`,
:mod:`aiimaging.baumasse` — reine stdlib, kein numpy (der Kern rechnet ohne). Die Rechnung
in :func:`halte_latenten` ist reine Arithmetik und nimmt torch-Tensoren wie Zahlen.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from . import baumasse, bildlesen, bildschreiben

#: Die beiden Arten des Schalters — wörtlich die Werte von ``vis.umriss_halten``.
ART_NACHHER = "nachher"
ART_IM_LAUF = "im_lauf"
ARTEN = (ART_NACHHER, ART_IM_LAUF)

#: Kennung der Methode im Vermerk.
METHODE_NACHHER = "maskenmischung_nach_dem_ki_schritt"
METHODE_IM_LAUF = "hintergrund_im_fahrplan_festgehalten"

#: Der freie Rand um das Haus, als Anteil der langen Bildseite. **Dieselbe Zahl wie
#: ``baumasse.RAND_ANTEIL``** (2 %): Was die Messung als Rand der Silhouette nicht zählt,
#: darf die KI auch malen. Gesetzt, nicht gemessen.
RAND_ANTEIL = baumasse.RAND_ANTEIL
RAND_MIN_PX = baumasse.RAND_MIN_PX

#: Der weiche Übergang ausserhalb des Rands, als Anteil der langen Bildseite (1 %, bei
#: 960 px rund 10 Bildpunkte). Gesetzt, nicht gemessen — gegen eine harte Naht.
WEICH_ANTEIL = 0.01

#: Unterordner neben den Kamerabildern, in dem das KI-Bild **ohne** Halten liegen bleibt —
#: für die Tafel und die Nachprüfung (wie beim Farbabgleich).
ORDNER_OHNE = "_ohne_umriss_halten"

#: Unterordner für die Freigabemaske der Art ``im_lauf`` (weiss = die KI malt).
ORDNER_MASKE = "_umriss_halten"

#: Der Anfang aller Sätze dieses Schalters — Proben und Auswerter suchen danach.
SATZ = "UMRISS HALTEN (Messschalter vis.umriss_halten)"


class UmrissHaltenError(ValueError):
    """Bild, Grundbild und Maske passen nicht zusammen (Grösse, leer)."""


def rand_px(breite: int, hoehe: int, anteil: float = RAND_ANTEIL) -> int:
    """Der freie Rand in Bildpunkten — mindestens :data:`RAND_MIN_PX`."""
    return max(RAND_MIN_PX, int(round(float(anteil) * max(int(breite), int(hoehe)))))


def weich_px(breite: int, hoehe: int, anteil: float = WEICH_ANTEIL) -> int:
    """Die Breite des weichen Übergangs in Bildpunkten (0 heisst harte Kante)."""
    return max(0, int(round(float(anteil) * max(int(breite), int(hoehe)))))


def _pruefe_maske(maske, breite: int, hoehe: int) -> None:
    if breite <= 0 or hoehe <= 0:
        raise UmrissHaltenError(f"Bildgroesse {breite} x {hoehe} ist leer.")
    if maske is None or len(maske) != breite * hoehe:
        raise UmrissHaltenError(
            f"Die Bauwerksmaske hat {0 if maske is None else len(maske)} Punkte, das Bild "
            f"{breite} x {hoehe} = {breite * hoehe}.")


def abstand_px(maske: Sequence[bool], breite: int, hoehe: int) -> list[float]:
    """Abstand jedes Bildpunkts zum nächsten Hauspunkt, in Bildpunkten (0 auf dem Haus).

    Zwei Durchgänge mit Gewichten 1 (gerade) und √2 (schräg) — eine Näherung des
    euklidischen Abstands auf wenige Prozent, ohne numpy. Ohne Hauspunkt überall ``inf``.
    """
    _pruefe_maske(maske, breite, hoehe)
    inf = math.inf
    d = [0.0 if m else inf for m in maske]
    s2 = math.sqrt(2.0)
    b = breite
    for y in range(hoehe):
        z = y * b
        for x in range(b):
            i = z + x
            v = d[i]
            if v == 0.0:
                continue
            if x > 0 and d[i - 1] + 1.0 < v:
                v = d[i - 1] + 1.0
            if y > 0:
                o = i - b
                if d[o] + 1.0 < v:
                    v = d[o] + 1.0
                if x > 0 and d[o - 1] + s2 < v:
                    v = d[o - 1] + s2
                if x < b - 1 and d[o + 1] + s2 < v:
                    v = d[o + 1] + s2
            d[i] = v
    for y in range(hoehe - 1, -1, -1):
        z = y * b
        for x in range(b - 1, -1, -1):
            i = z + x
            v = d[i]
            if v == 0.0:
                continue
            if x < b - 1 and d[i + 1] + 1.0 < v:
                v = d[i + 1] + 1.0
            if y < hoehe - 1:
                u = i + b
                if d[u] + 1.0 < v:
                    v = d[u] + 1.0
                if x < b - 1 and d[u + 1] + s2 < v:
                    v = d[u + 1] + s2
                if x > 0 and d[u - 1] + s2 < v:
                    v = d[u - 1] + s2
            d[i] = v
    return d


def freigabe(maske: Sequence[bool], breite: int, hoehe: int, *, rand: int,
             weich: int = 0) -> list[float]:
    """Wie viel vom KI-Bild je Bildpunkt gilt: 1 auf dem Haus und im Rand, 0 weit weg.

    Zwischen ``rand`` und ``rand + weich`` fällt der Wert linear ab. ``weich`` 0 heisst
    harte Kante (so für die Maske der Art ``im_lauf``, die danach ohnehin auf die Zellen des
    Modells gerundet wird).
    """
    abstand = abstand_px(maske, breite, hoehe)
    rand = float(max(0, rand))
    weich = float(max(0, weich))
    aus = []
    for d in abstand:
        if d <= rand:
            aus.append(1.0)
        elif weich > 0 and d < rand + weich:
            aus.append(1.0 - (d - rand) / weich)
        else:
            aus.append(0.0)
    return aus


def mische(ki: Sequence[Sequence[int]], grund: Sequence[Sequence[int]],
           anteil_ki: Sequence[float]) -> list[tuple[int, int, int]]:
    """Je Bildpunkt ``a·KI + (1−a)·Grund``, gerundet auf 8 Bit."""
    if not (len(ki) == len(grund) == len(anteil_ki)):
        raise UmrissHaltenError(
            f"Ungleiche Laengen: KI {len(ki)}, Grundbild {len(grund)}, Maske {len(anteil_ki)}.")
    aus = []
    for k, g, a in zip(ki, grund, anteil_ki):
        if a >= 1.0:
            aus.append((int(k[0]), int(k[1]), int(k[2])))
        elif a <= 0.0:
            aus.append((int(g[0]), int(g[1]), int(g[2])))
        else:
            aus.append(tuple(int(round(a * kk + (1.0 - a) * gg)) for kk, gg in zip(k[:3], g[:3])))
    return aus


def halte_datei(ki_png, grund_png, maske: Sequence[bool], breite: int, hoehe: int,
                ziel_png, *, rand: int | None = None, weich: int | None = None) -> dict:
    """Art ``nachher``: das KI-Bild ausserhalb des Hauses durch das Grundbild ersetzen.

    ``ki_png`` und ``grund_png`` müssen die Grösse der Maske haben (die Grundlage; das
    KI-Bild ist zu diesem Zeitpunkt schon auf sie zurückgebracht). ``ziel_png`` darf
    ``ki_png`` sein — gelesen wird zuerst, geschrieben am Ende.

    Returns:
        Der Vermerk ``{angewandt, art, methode, rand_px, weich_px, anteil_ki, anteil_grund,
        anteil_haus, punkte_geaendert}`` — ``punkte_geaendert`` zählt Bildpunkte, deren Farbe
        sich durch das Halten änderte (0 hiesse: die KI hatte ausserhalb schon das Grundbild).
    """
    _pruefe_maske(maske, breite, hoehe)
    ki, kb, kh = bildlesen.lies_png_farben(ki_png)
    grund, gb, gh = bildlesen.lies_png_farben(grund_png)
    if (kb, kh) != (breite, hoehe) or (gb, gh) != (breite, hoehe):
        raise UmrissHaltenError(
            f"Groessen passen nicht: KI-Bild {kb} x {kh}, Grundbild {gb} x {gh}, Maske "
            f"{breite} x {hoehe}.")
    if not any(maske):
        raise UmrissHaltenError("Die Bauwerksmaske ist leer — es gaebe nichts zu halten.")
    r = rand_px(breite, hoehe) if rand is None else int(rand)
    w = weich_px(breite, hoehe) if weich is None else int(weich)
    anteil = freigabe(maske, breite, hoehe, rand=r, weich=w)
    neu = mische(ki, grund, anteil)
    geaendert = sum(1 for a, b in zip(ki, neu) if tuple(a[:3]) != b)
    bildschreiben.schreibe_farb_png(ziel_png, neu, breite, hoehe)
    n = float(breite * hoehe)
    return {
        "angewandt": True,
        "art": ART_NACHHER,
        "methode": METHODE_NACHHER,
        "rand_px": r,
        "weich_px": w,
        "anteil_haus": round(sum(1 for m in maske if m) / n, 4),
        "anteil_ki": round(sum(1 for a in anteil if a > 0.0) / n, 4),
        "anteil_grund": round(sum(1 for a in anteil if a <= 0.0) / n, 4),
        "punkte_geaendert": geaendert,
    }


def schreibe_freigabe_png(ziel_png, maske: Sequence[bool], breite: int, hoehe: int, *,
                          rand: int | None = None) -> dict:
    """Art ``im_lauf``: die Freigabemaske als Graustufen-PNG (weiss = die KI malt).

    Hart, ohne Übergang: Das Bildmodell rundet sie ohnehin auf seine Zellen (16 Bildpunkte bei
    Z-Image) und gilt dort als frei, wo **irgendein** Punkt der Zelle frei ist
    (``render._umriss_halten_vorbereiten``). Den weichen Übergang malt das Modell selbst.
    """
    _pruefe_maske(maske, breite, hoehe)
    if not any(maske):
        raise UmrissHaltenError("Die Bauwerksmaske ist leer — es gaebe nichts freizugeben.")
    r = rand_px(breite, hoehe) if rand is None else int(rand)
    werte = freigabe(maske, breite, hoehe, rand=r, weich=0)
    Path(ziel_png).parent.mkdir(parents=True, exist_ok=True)
    bildschreiben.schreibe_graustufen_png(ziel_png, werte, breite, hoehe, bittiefe=8)
    return {"art": ART_IM_LAUF, "methode": METHODE_IM_LAUF, "rand_px": r,
            "anteil_frei": round(sum(werte) / float(breite * hoehe), 4)}


def halte_latenten(latenten, hintergrund, rauschen, frei, sigma: float):
    """Ein Schritt der Art ``im_lauf``: ausserhalb ``frei`` gilt das verrauschte Grundbild.

    ``frei·x + (1−frei)·(σ·Rauschen + (1−σ)·Grundbild)`` — dieselbe Verrauschung wie
    ``scale_noise`` des Fluss-Fahrplans von Z-Image (σ = 1 reines Rauschen, σ = 0 das Bild).
    Reine Arithmetik: torch-Tensoren, numpy-Felder und Zahlen gehen gleich.
    """
    s = float(sigma)
    return frei * latenten + (1.0 - frei) * (s * rauschen + (1.0 - s) * hintergrund)


__all__ = [
    "ART_IM_LAUF", "ART_NACHHER", "ARTEN", "METHODE_IM_LAUF", "METHODE_NACHHER", "ORDNER_MASKE",
    "ORDNER_OHNE", "RAND_ANTEIL", "RAND_MIN_PX", "SATZ", "UmrissHaltenError", "WEICH_ANTEIL",
    "abstand_px", "freigabe", "halte_datei", "halte_latenten", "mische", "rand_px",
    "schreibe_freigabe_png", "weich_px",
]
