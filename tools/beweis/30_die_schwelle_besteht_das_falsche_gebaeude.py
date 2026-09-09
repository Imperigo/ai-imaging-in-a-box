#!/usr/bin/env python3
"""BEWEIS 30 — Die Schwelle besteht auch das **falsche** Gebäude.

Woher die Zahlen kommen — und warum das hier oben steht
------------------------------------------------------
**Dieser Beweis misst nicht selbst.** Er zeichnet eine Messung, die die HomeStation am
08.09.2026 gefahren hat (`auf-20260909-92`, RTX 5090, 36 Renderläufe). Hier liegen weder
Gewichte noch GPU; nachfahren lässt sich das an dieser Stelle nicht.

Was hier trotzdem gilt: **Jede Zahl in jedem Bild ist eine gemessene**, gelesen aus
`auftraege/ergebnisse/auf-20260909-92-tabelle.json` — kein Wert ist rekonstruiert,
geschätzt oder für die Darstellung gewählt. Der Dateiname jedes Bildes sagt, wer gemessen
hat und wann. *Beweis 28 hat gezeigt, warum dieser Absatz nötig ist: Dort war eine
Darstellung in den Dateinamen geraten, als wäre sie eine Messung.*

Der Befund
----------
Die Kernfrage dieses Projekts lautete: *Gibt es ein erzeugtes Bild, das die
Geometrie-Schwelle 0,65 besteht?* Die Antwort ist **zwölf von zwölf**, Scores 0,8965 bis
0,9884.

Und dann die Probe, die eine Bestätigung nicht sein kann:

> **Dieselben zwölf Bilder bestehen die Schwelle auch gegen die FALSCHE Soll-Karte.**

Das Bild des fünfgeschossigen Baus wird gegen die Tiefenkarte einer 8 × 5 × 3 m grossen
Schachtel gemessen und umgekehrt — zwei Bauwerke, die nichts gemein haben ausser dem
Standpunkt. **12 von 12 bestehen auch dort.**

Damit ist das Prüfverfahren an dieser Stelle **schwächer als das Erzeugungsverfahren.**
Bei 56 % Geometrieanteil trägt der Score im Wesentlichen den Boden-Himmel-Aufbau, den
jedes Architekturbild auf Augenhöhe hat.

Was die Bilder zeigen
---------------------
* ``01_…`` — die zwölf Scores gegen die **richtige** Karte, mit der Schwelle als Linie.
* ``02_…`` — dieselben zwölf, je zwei Balken: richtige Karte gegen falsche. **Beide über
  der Linie.** Das ist der Beweis.
* ``03_…`` — dieselben zwölf Paare, aber `rho_maske` statt Score. Hier trennt es — nicht
  vollständig (die Bänder überlappen, und das bleibt sichtbar), aber es trennt.
* ``04_…`` — die Stärkeprobe: `rho_maske` bei ControlNet-Stärke 1,00 / 0,75 / 0,30. Bei
  0,30 liegt es bei null, das Bild hat mit dem Modell nichts mehr zu tun — und **elf von
  zwölf bestehen die Schwelle immer noch.**

Der Selbstcheck
---------------
Er rechnet jede Behauptung aus der Tabelle **nach** und hält an, wenn eine nicht trägt:
12 bestanden gegen die richtige Karte, 12 gegen die falsche, 11 bei Stärke 0,30, und
`rho_maske` dort betragsmässig unter 0,10. Steht in der Tabelle etwas anderes, wird kein
Bild geschrieben.

Aufruf:
    python3 tools/beweis/30_die_schwelle_besteht_das_falsche_gebaeude.py [ziel]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben  # noqa: E402

TABELLE = WURZEL / "auftraege" / "ergebnisse" / "auf-20260909-92-tabelle.json"
HERKUNFT = "HOMESTATION-MESSUNG-auf92-08.09.2026"

GRUND = (243, 243, 241)
RICHTIG = (62, 106, 160)       # gegen die richtige Soll-Karte
FALSCH = (216, 122, 40)        # gegen die falsche
SCHWELLE_F = (176, 58, 58)
LINIE = (60, 66, 74)
GRAU = (150, 150, 150)

SCHWELLE = 0.65

#: Was die Tabelle sagen MUSS. Der Selbstcheck prueft genau das.
SOLL = {"bestanden_richtig": 12, "bestanden_falsch": 12,
        "bestanden_staerke_030": 11, "rho_030_hoechstens": 0.10}


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _balkenbild(ziel, name, gruppen, *, hoechst, schwelle=None, nulllinie=False):
    """Gruppen von Balken auf gemeinsamer Achse. Ein Balken je Wert, nichts gemittelt."""
    breit, luft, rand = 22, 14, 40
    n = sum(len(werte) for werte, _ in gruppen)
    b = rand * 2 + n * breit + (len(gruppen) - 1) * luft
    h = 300
    bild = _leinwand(b, h)
    boden = h - rand if not nulllinie else h // 2
    hoch = (boden - rand) if not nulllinie else (h // 2 - rand)

    x = rand
    for werte, farbe in gruppen:
        for wert in werte:
            laenge = round(hoch * min(1.0, abs(wert) / hoechst))
            if wert >= 0:
                _rechteck(bild, b, h, x + 2, boden - laenge, x + breit - 2, boden, farbe)
            else:
                _rechteck(bild, b, h, x + 2, boden, x + breit - 2, boden + laenge, farbe)
            x += breit
        x += luft

    if nulllinie:
        _rechteck(bild, b, h, rand // 2, boden - 1, b - rand // 2, boden + 1, LINIE)
    if schwelle is not None:
        y = boden - round(hoch * schwelle / hoechst)
        _rechteck(bild, b, h, rand // 2, y - 1, b - rand // 2, y + 1, SCHWELLE_F)
    p = Path(ziel) / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _paare(ziel, name, paare, *, hoechst, schwelle=None):
    """Je Bild zwei Balken nebeneinander: richtige Karte gegen falsche."""
    breit, luft, rand = 16, 12, 40
    b = rand * 2 + len(paare) * (2 * breit + luft)
    h = 300
    bild = _leinwand(b, h)
    boden, hoch = h - rand, h - 2 * rand
    x = rand
    for r, f in paare:
        for wert, farbe in ((r, RICHTIG), (f, FALSCH)):
            laenge = round(hoch * min(1.0, max(0.0, wert) / hoechst))
            _rechteck(bild, b, h, x + 1, boden - laenge, x + breit - 1, boden, farbe)
            if wert < 0:
                _rechteck(bild, b, h, x + 1, boden, x + breit - 1, boden + 6, GRAU)
            x += breit
        x += luft
    if schwelle is not None:
        y = boden - round(hoch * schwelle / hoechst)
        _rechteck(bild, b, h, rand // 2, y - 1, b - rand // 2, y + 1, SCHWELLE_F)
    p = Path(ziel) / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)

    if not TABELLE.is_file():
        print(f"Die Messtabelle fehlt: {TABELLE.relative_to(WURZEL)}")
        return 1
    daten = json.loads(TABELLE.read_text(encoding="utf-8"))

    reihe = daten["reihen"]["staerke_1.00"]
    vertausch = daten["vertauschprobe"]
    reihe_030 = daten["reihen"]["staerke_0.30"]
    reihe_075 = daten["reihen"]["staerke_0.75"]

    # ── Die Paare bilden, ueber (fall, seed) — nicht ueber die Reihenfolge ──
    richtig = {(z["fall"], z["seed"]): z for z in vertausch if z["gegen"] == "richtig"}
    falsch = {(z["fall"], z["seed"]): z for z in vertausch if z["gegen"] == "falsch"}
    schluessel = sorted(richtig)
    if sorted(falsch) != schluessel:
        print("Die Vertauschprobe ist nicht vollstaendig gepaart.")
        return 1

    # ── Der Selbstcheck: jede Behauptung aus der Tabelle nachgerechnet ──
    n_richtig = sum(1 for k in schluessel if richtig[k]["bestanden"])
    n_falsch = sum(1 for k in schluessel if falsch[k]["bestanden"])
    n_030 = sum(1 for z in reihe_030 if z["bestanden"])
    rho_030 = [z["rho_maske"] for z in reihe_030]
    fehler = []
    if n_richtig != SOLL["bestanden_richtig"]:
        fehler.append(f"gegen die richtige Karte bestehen {n_richtig}, "
                      f"erwartet {SOLL['bestanden_richtig']}")
    if n_falsch != SOLL["bestanden_falsch"]:
        fehler.append(f"gegen die FALSCHE Karte bestehen {n_falsch}, "
                      f"erwartet {SOLL['bestanden_falsch']} — ohne das traegt dieser "
                      f"Beweis nichts")
    if n_030 != SOLL["bestanden_staerke_030"]:
        fehler.append(f"bei Staerke 0,30 bestehen {n_030}, "
                      f"erwartet {SOLL['bestanden_staerke_030']}")
    if max(abs(w) for w in rho_030) > SOLL["rho_030_hoechstens"]:
        fehler.append(f"bei Staerke 0,30 liegt rho_maske bei bis zu "
                      f"{max(abs(w) for w in rho_030):.4f} — dann ist das Bild nicht "
                      f"'ohne Bezug zum Modell', und der schaerfste Satz faellt weg")
    if fehler:
        print("DIE TABELLE SAGT ETWAS ANDERES ALS DIESER BEWEIS:")
        for z in fehler:
            print("  -", z)
        return 1

    scores_r = [richtig[k]["score"] for k in schluessel]
    scores_f = [falsch[k]["score"] for k in schluessel]
    rho_r = [richtig[k]["rho_maske"] for k in schluessel]
    rho_f = [falsch[k]["rho_maske"] for k in schluessel]

    print(f"  richtige Karte: {n_richtig}/12 bestanden, "
          f"Score {min(scores_r):.4f}–{max(scores_r):.4f}")
    print(f"  FALSCHE Karte:  {n_falsch}/12 bestanden, "
          f"Score {min(scores_f):.4f}–{max(scores_f):.4f}")
    print(f"  rho_maske:      richtig {min(rho_r):.3f}–{max(rho_r):.3f}, "
          f"falsch {min(rho_f):.3f}–{max(rho_f):.3f}")
    print(f"  Staerke 0,30:   {n_030}/12 bestanden, "
          f"rho_maske {min(rho_030):+.3f}…{max(rho_030):+.3f}")

    # ── Die Bilder ──
    p1 = _balkenbild(
        ziel,
        f"01_zwoelf-erzeugte-bilder_richtige-karte_alle-zwoelf-bestehen"
        f"_score-{min(scores_r):.4f}-bis-{max(scores_r):.4f}"
        f"_schwelle-{SCHWELLE}_{HERKUNFT}.png",
        [(scores_r, RICHTIG)], hoechst=1.0, schwelle=SCHWELLE)

    p2 = _paare(
        ziel,
        f"02_dieselben-zwoelf_blau-richtige-karte_orange-FALSCHE-karte"
        f"_bestanden-{n_richtig}-und-{n_falsch}-von-12"
        f"_beide-ueber-der-schwelle_{HERKUNFT}.png",
        list(zip(scores_r, scores_f)), hoechst=1.0, schwelle=SCHWELLE)

    p3 = _paare(
        ziel,
        f"03_rho-maske-statt-score_richtig-{min(rho_r):.3f}-bis-{max(rho_r):.3f}"
        f"_falsch-{min(rho_f):.3f}-bis-{max(rho_f):.3f}"
        f"_es-trennt-und-ueberlappt_keine-schwelle-vorhanden_{HERKUNFT}.png",
        list(zip(rho_r, rho_f)), hoechst=1.0, schwelle=None)

    rho_100 = [z["rho_maske"] for z in reihe]
    rho_075 = [z["rho_maske"] for z in reihe_075]
    n_075 = sum(1 for z in reihe_075 if z["bestanden"])
    n_100 = sum(1 for z in reihe if z["bestanden"])
    p4 = _balkenbild(
        ziel,
        f"04_staerkeprobe_rho-maske_bei-1.00-und-0.75-und-0.30"
        f"_bestanden-{n_100}-{n_075}-{n_030}-von-12"
        f"_bei-0.30-liegt-rho-bei-null_{HERKUNFT}.png",
        [(rho_100, RICHTIG), (rho_075, GRAU), (rho_030, FALSCH)],
        hoechst=1.0, nulllinie=True)

    for p in (p1, p2, p3, p4):
        print("  Bild:", p.name)

    print(f"\nZWOELF VON ZWOELF BESTEHEN — UND ZWOELF VON ZWOELF BESTEHEN AUCH GEGEN DIE "
          f"FALSCHE KARTE.\nDie Pruefung ist an dieser Stelle schwaecher als die "
          f"Erzeugung.")
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
