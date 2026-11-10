"""Zufallsvergleich der Formprüfung je Baukörper gegen die Deckung von heute (A0300).

**Wozu.** Ein eigener Satz, an dem eine Lösung alles trifft, belegt wenig. Dieser Vergleich
würfelt Anlagen quer durch alle Regler des Erzeugers (Art, Fleckanteil, fehlende und
dazugemalte Öffnungen, glatte Bauten, welcher Bau aufgelöst wird, Einzelhaus) und stellt je
Fall das Urteil von heute (``varianten.deckung`` über das ganze Haus) neben das neue
(``formtreue``). Jede Abweichung wird eingeordnet, und zwar nach dem, was im Bild WIRKLICH
geschah (``fall["bauten"]``: wie viele Öffnungen je Bau erhalten sind), nicht nach den Reglern.

**Die Wahrheit je Fall.**

* ``einzelhaus`` / ``keine_anlage``: weniger als zwei Bauten von je 1 % der Bildfläche. Das
  neue Urteil muss das alte sein.
* ``klar_schlecht``: Ein Bau mit mindestens sechs Öffnungen hat weniger als ein Viertel davon
  behalten. Das neue Urteil soll «Form weicht ab» sein.
* ``klar_gut``: Jeder Bau mit mindestens sechs Öffnungen hat mindestens 70 % behalten, und die
  KI hat höchstens so viele dazugemalt, wie da waren. Das neue Urteil darf nicht strenger
  sein als das alte.
* ``uebergang``: alles dazwischen. Hier gibt es keine Wahrheit, die die Daten allein tragen;
  gezählt wird, nicht geurteilt.

**Gemessen am 10.11.2026, 3200 Fälle** (``python tests/anlagen_vergleich.py 3200``, rund fünf
Minuten auf vier Kernen): kein Fall milder als heute; 456 Einzelhäuser, alle gleich; 749 klar
gute, keiner beanstandet; 1125 klar schlechte, 1124 beanstandet (heute: keiner); 870 im
Übergang, davon 308 beanstandet. Der eine klar schlechte, der besteht (Fall 2309): ein
Nebenbau mit zehn Öffnungen, zwei erhalten, an den übrigen treffen Fleckränder zufällig die
alten Kanten (Kanten-Deckung im Inneren 0,29, über der Schwelle).

Kein Probenmodul (der Name beginnt nicht mit ``test_``): ``tests/test_formtreue_a0300.py``
fährt die ersten Fälle mit, der grosse Lauf ist ein Aufruf von Hand.
"""
from __future__ import annotations

import random
import sys
from collections import Counter

import anlagen_erzeuger as erz

#: Ab so vielen Öffnungen im Grundbild zählt ein Bau für die Wahrheit (sechs Öffnungen geben
#: rund 170 Kantenpunkte; die Prüfung urteilt ab 150, ``formtreue.KOERPER_MIN_KANTEN``).
OEFFNUNGEN_MIN = 6
KLAR_SCHLECHT_UNTER = 0.25
KLAR_GUT_AB = 0.70
KLAR_GUT_DAZU_BIS = 1.0


def wuerfle(nummer: int) -> tuple[int, str, dict]:
    """Die Regler des Falls ``nummer``: ``(startwert, art, weitere Regler)``."""
    rng = random.Random(f"zufall-{nummer}")
    art = rng.choice([erz.ART_INTAKT, erz.ART_INTAKT, erz.ART_FLECKEN, erz.ART_PLATTE,
                      erz.ART_VERFLECKT, erz.ART_VERFLECKT])
    regler: dict = {"einzelhaus": rng.random() < 0.15}
    if art == erz.ART_VERFLECKT:
        regler["fleck_anteil"] = round(rng.random(), 3)
    if rng.random() < 0.5:
        regler["weg"] = round(rng.uniform(0, 0.3), 3)
    if rng.random() < 0.6:
        regler["dazu"] = round(rng.uniform(0, 1.5), 3)
    if not regler["einzelhaus"]:
        if rng.random() < 0.25:
            regler["glatt"] = tuple(sorted(rng.sample(range(0, 4), rng.randint(1, 2))))
        if regler.get("glatt") and rng.random() < 0.6:
            regler["ki_malt_auf_glatt"] = round(rng.random(), 3)
        if art != erz.ART_INTAKT:
            regler["fleck_auf"] = rng.choice([0, 0, 0, 1, 2])
    return 1000 + nummer, art, regler


def wahrheit(fall: dict, regler: dict) -> str:
    """Die Klasse des Falls nach dem, was je Bau wirklich erhalten ist (siehe Modulkopf)."""
    n = fall["breite"] * fall["hoehe"]
    gross, richtbar = 0, []
    for bau in fall["bauten"]:
        k = bau["kasten"]
        flaeche = sum(1 for y in range(k[1], k[3]) for x in range(k[0], k[2])
                      if fall["maske"][y * fall["breite"] + x])
        if flaeche >= 0.01 * n:
            gross += 1
            if bau["oeffnungen"] >= OEFFNUNGEN_MIN:
                richtbar.append(bau["erhalten"] / bau["oeffnungen"])
    if regler.get("einzelhaus"):
        return "einzelhaus"
    if gross < 2:
        return "keine_anlage"
    if any(anteil < KLAR_SCHLECHT_UNTER for anteil in richtbar):
        return "klar_schlecht"
    if all(anteil >= KLAR_GUT_AB for anteil in richtbar) \
            and regler.get("dazu", erz.KI_DAZU[1]) <= KLAR_GUT_DAZU_BIS:
        return "klar_gut"
    return "uebergang"


def vergleiche_einen(nummer: int) -> dict:
    """Ein Fall: Regler, Wahrheit, Urteil von heute und neues Urteil."""
    from aiimaging import farbabgleich, formtreue, varianten
    startwert, art, regler = wuerfle(nummer)
    fall = erz.fall(startwert, art, **regler)
    ka, kb = farbabgleich.kantenkarten(fall["ki"], fall["grund"], fall["breite"], fall["hoehe"])
    alt = varianten.deckung(True, farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=fall["maske"]))
    neu = formtreue.formtreue_aus_karten(ka, kb, fall["maske"], fall["breite"], fall["hoehe"])
    return {"nummer": nummer, "art": art, "regler": regler, "wahrheit": wahrheit(fall, regler),
            "alt": alt["urteil"], "neu": neu["urteil"], "anlage": neu["anlage"],
            "zahl_gleich": neu["kanten_iou_haus"] == alt["kanten_iou"],
            "beanstandet": neu["aufgeloest"] + neu["verfleckt"],
            "nicht_entscheidbar": neu["nicht_entscheidbar"]}


def befund(ergebnisse: list[dict]) -> dict:
    """Die Zählung über viele Fälle: je Klasse, was heute und was neu gesagt wird.

    ``milder`` (heute «weicht ab», neu nicht), ``ungleich_ohne_anlage`` und ``gut_beanstandet``
    müssen leer sein; ``schlecht_besteht`` ist, was die Prüfung noch durchlässt.
    """
    from aiimaging import varianten
    ab = varianten.FORM_WEICHT_AB
    return {
        "faelle": len(ergebnisse),
        "klassen": dict(Counter((e["wahrheit"], e["alt"], e["neu"]) for e in ergebnisse)),
        "milder": [e["nummer"] for e in ergebnisse if e["alt"] == ab and e["neu"] != ab],
        "zahl_ungleich": [e["nummer"] for e in ergebnisse if not e["zahl_gleich"]],
        "ungleich_ohne_anlage": [e["nummer"] for e in ergebnisse
                                 if not e["anlage"] and e["alt"] != e["neu"]],
        "gut_beanstandet": [e["nummer"] for e in ergebnisse
                            if e["wahrheit"] == "klar_gut" and e["alt"] != ab and e["neu"] == ab],
        "schlecht_besteht": [e["nummer"] for e in ergebnisse
                             if e["wahrheit"] == "klar_schlecht" and e["neu"] != ab],
    }


if __name__ == "__main__":
    from multiprocessing import Pool
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    anzahl = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    with Pool() as becken:
        alle = becken.map(vergleiche_einen, range(anzahl), chunksize=16)
    zaehlung = befund(alle)
    for klasse in sorted(zaehlung.pop("klassen").items()):
        print(klasse)
    for name, wert in zaehlung.items():
        print(name, wert)
