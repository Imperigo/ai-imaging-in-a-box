#!/usr/bin/env python3
"""BEWEIS 28 — Der Zufall der Kette ist **grösser** als jede Einstellung, und die Software
rechnet mit ihm statt gegen ihn.

Der Befund, um den es geht
--------------------------
Neun Läufe, **derselbe Aufbau**, nur der Startwert verschieden (22.08.2026,
`docs/POLARITAET_UND_STAERKE_2026-08-22.md`): Mittel −0,6644, Streuung **0,2269**. Drei
der neun erreichten die Schwelle, sechs nicht. *Derselbe Aufbau, dieselben Zahlen, und das
Urteil kippt.*

Zum Vergleich der stärkste Parametereffekt, den diese Kette je gezeigt hat — die
ControlNet-Stärke von 0,65 auf 1,00: **0,10 bis 0,14.** Der Zufall ist damit **1,6- bis
2,3-mal so gross** wie die Einstellung, die man verändern wollte.

Unter welcher Bedingung diese Zahl gilt — nachgetragen am 09.09.2026
------------------------------------------------------------------
Die 0,2269 stammen aus einem Lauf **ohne Tiefen-ControlNet**: Das damalige Backbone
(`qwen-image-edit-2511`) hat gar keinen ControlNet-Eingang, die Tiefenkarte ging als
`image` hinein und ersetzte dabei den Beauty-Pass.

Die HomeStation hat am 08.09.2026 dieselbe Frage an einer **echten** Tiefen-Naht gemessen
(`auf-20260909-92`, `z-image-turbo` mit Fun-ControlNet-Union): Die grösste Spanne
innerhalb eines Falls über drei Startwerte beträgt dort **0,0820** — knapp ein Drittel.

*Das entwertet diesen Beweis nicht, es bindet ihn.* Hausregel seit dem 23.08.2026:
**Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.** Der Befund «der
Zufall ist grösser als jede Einstellung» gilt für die Kette ohne Tiefenführung. Ob er für
die Kette **mit** Tiefenführung gilt, ist mit drei Startwerten je Fall nicht entschieden —
neun waren es dort nicht.

**Daraus folgen zwei Dinge, und beide sind hier zu sehen:**

1. *Ein Vergleich zweier Einstellungen mit je einem Bild misst den Zufall.* Darum verlangt
   jeder Messauftrag dieses Projekts **drei Startwerte** je Fall.
2. *Die Auswahl über mehrere Startwerte ist der billigste Qualitätssprung der Kette* — aus
   drei mittelmässigen wird der beste, ohne dass eine Einstellung angefasst wird.

Was hier gemessen wird
----------------------
Alles mit den **echten** Funktionen aus `aiimaging.varianten`, an der gemessenen Streuung
von 0,2269 — kein Nachbau, keine erfundenen Zahlen.

* ``01_streuung_...png`` — die neun Läufe als Punkte auf einer Achse, mit der Schwelle als
  Linie. Man sieht drei über und sechs unter ihr.
* ``02_zufall_gegen_einstellung_...png`` — zwei Balken: die Startwertstreuung gegen den
  stärksten Parametereffekt. Der Zufall ist der längere.
* ``03_belegt_...png`` — für Abstände von 0,05 bis 0,60: ab wann gilt ein Unterschied als
  **belegt**? Rot heisst «im Rauschen», grün heisst «grösser als der Zufall». Gerechnet
  mit `varianten.ist_unterschied_belegt`.
* ``04_auswahl_...png`` — drei Startwerte, einer wird gewählt. Der gewählte ist markiert;
  **die anderen bleiben sichtbar**, denn wer nur den besten sähe, hielte die Kette für
  besser, als sie ist.

Der Selbstcheck
---------------
Er hält an, wenn ein Abstand **unter** der Streuung als belegt gilt oder einer weit
darüber als nicht belegt. Beides wäre ein Mass, das nicht misst, was draufsteht.

Aufruf:
    python3 tools/beweis/28_der_zufall_ist_groesser.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, geometrie_qa, varianten  # noqa: E402

#: Neun Punkte für das erste Bild. **Sie sind eine DARSTELLUNG, keine Messung.**
#:
#: Gemessen sind zwei Zahlen und die Enden: Mittel −0,6644, Streuung **0,2269**, und die
#: Reihe lief von −0,91 bis −0,27 (`docs/POLARITAET_UND_STAERKE_2026-08-22.md`). Die
#: sieben Werte dazwischen kennt niemand mehr; die hier gewählten ergeben eine Streuung
#: von 0,1929 statt 0,2269.
#:
#: *Der erste Anlauf hat diese 0,1929 in den Dateinamen geschrieben, als wäre sie die
#: gemessene.* Sie ist es nicht — und eine Zahl, die aus einer Darstellung stammt und wie
#: eine Messung aussieht, ist genau der Fehler, gegen den dieses Projekt seit Wochen
#: antritt. Gerechnet wird darum überall mit `varianten.GEMESSENER_BODEN`; diese Reihe
#: liefert nur die Punkte im Bild, und ihr Dateiname sagt es.
NEUN = (-0.91, -0.85, -0.79, -0.72, -0.66, -0.60, -0.54, -0.44, -0.27)
#: Der stärkste Parametereffekt, den die Kette gezeigt hat (Stärke 0,65 ↔ 1,00).
PARAMETEREFFEKT = 0.14
#: Abstände, für die geprüft wird, ob sie über dem Zufall liegen.
ABSTAENDE = (0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60)

GRUND = (243, 243, 241)
UEBER = (62, 140, 78)
UNTER = (200, 60, 48)
ZUFALL = (216, 122, 40)
LINIE = (60, 66, 74)
GEWAEHLT = (62, 106, 160)


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _streuung(ziel: Path, werte, schwelle: float, name: str) -> Path:
    """Neun Punkte auf einer Achse, die Schwelle als Linie."""
    b, h, rand = 620, 180, 40
    bild = _leinwand(b, h)
    lo, hi = min(werte) - 0.1, max(werte) + 0.1

    def x_von(w):
        return rand + round((b - 2 * rand) * (w - lo) / (hi - lo))

    _rechteck(bild, b, h, rand, h // 2 - 1, b - rand, h // 2 + 1, LINIE)   # die Achse
    xs = x_von(schwelle)
    _rechteck(bild, b, h, xs - 1, 30, xs + 2, h - 30, LINIE)               # die Schwelle
    for w in werte:
        x = x_von(w)
        farbe = UEBER if w >= schwelle else UNTER
        _rechteck(bild, b, h, x - 6, h // 2 - 6, x + 6, h // 2 + 6, farbe)
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _zwei_balken(ziel: Path, a: float, bb: float, name: str) -> Path:
    b, h = 560, 120
    bild = _leinwand(b, h)
    hoechst = max(a, bb) or 1.0
    _rechteck(bild, b, h, 30, 20, 30 + round((b - 60) * a / hoechst), 52, ZUFALL)
    _rechteck(bild, b, h, 30, 68, 30 + round((b - 60) * bb / hoechst), 100, GEWAEHLT)
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _leiter(ziel: Path, zeilen, name: str) -> Path:
    zeile, b = 30, 560
    h = 20 + zeile * len(zeilen)
    bild = _leinwand(b, h)
    hoechst = max(a for a, _ in zeilen) or 1.0
    for i, (abstand, belegt) in enumerate(zeilen):
        y0 = 12 + i * zeile
        _rechteck(bild, b, h, 30, y0, 30 + round((b - 60) * abstand / hoechst), y0 + 20,
                  UEBER if belegt else UNTER)
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _auswahl(ziel: Path, werte, index: int, name: str) -> Path:
    """Drei Startwerte, einer gewählt — die anderen bleiben sichtbar."""
    zeile, b = 40, 520
    h = 20 + zeile * len(werte)
    bild = _leinwand(b, h)
    lo = min(werte) - 0.1
    spanne = (max(werte) + 0.1) - lo
    for i, w in enumerate(werte):
        y0 = 12 + i * zeile
        laenge = max(2, round((b - 90) * (w - lo) / spanne))
        _rechteck(bild, b, h, 60, y0, 60 + laenge, y0 + 26,
                  GEWAEHLT if i == index else (150, 150, 148))
        if i == index:
            _rechteck(bild, b, h, 26, y0 + 4, 50, y0 + 22, GEWAEHLT)   # die Marke
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)

    # ── 1: die neun Laeufe ──
    #
    # GERECHNET WIRD MIT DEM GEMESSENEN BODEN, nicht mit dem der Darstellung. Beide
    # stehen nebeneinander, damit der Unterschied sichtbar bleibt statt zu verschwinden.
    boden = varianten.GEMESSENER_BODEN
    darstellung = varianten.rauschboden(NEUN)
    print(f"  GEMESSEN (22.08.2026): Mittel {boden['mittel']:.4f}, "
          f"Streuung {boden['streuung']:.4f}")
    print(f"  die neun Punkte im Bild sind eine DARSTELLUNG: Mittel "
          f"{darstellung['mittel']:.4f}, Streuung {darstellung['streuung']:.4f}")
    schwelle = -0.55            # die Schwelle der Paarmasse, gerichtet
    ueber = sum(1 for w in NEUN if w >= schwelle)
    print(f"  ueber der Schwelle {schwelle}: {ueber} von {len(NEUN)}")
    print("  Streuung: ", _streuung(
        ziel, NEUN, schwelle,
        f"01_neun-laeufe_DARSTELLUNG_gemessen-mittel-{boden['mittel']:.4f}"
        f"-streuung-{boden['streuung']:.4f}"
        f"_dieses-bild-streuung-{darstellung['streuung']:.4f}"
        f"_ueber-schwelle-{ueber}-von-{len(NEUN)}_derselbe-aufbau.png").name)

    # ── 2: der Zufall gegen die staerkste Einstellung ──
    print("  Balken:   ", _zwei_balken(
        ziel, boden["streuung"], PARAMETEREFFEKT,
        f"02_gemessener-zufall-{boden['streuung']:.4f}"
        f"_gegen_staerkster-parametereffekt-{PARAMETEREFFEKT}"
        f"_faktor-{boden['streuung'] / PARAMETEREFFEKT:.2f}.png").name)

    # ── 3: ab wann ist ein Unterschied belegt? ──
    zeilen = []
    for abstand in ABSTAENDE:
        urteil = varianten.ist_unterschied_belegt(0.0, -abstand, boden)
        zeilen.append((abstand, bool(urteil["belegt"])))
        print(f"  Abstand {abstand:.2f}: belegt={urteil['belegt']}  "
              f"Grenze {urteil['grenze']:.4f}")
        # Selbstcheck: unter der Streuung darf nichts belegt sein.
        if abstand < boden["streuung"] and urteil["belegt"]:
            print(f"\nEIN ABSTAND UNTER DER STREUUNG GILT ALS BELEGT: {abstand} < "
                  f"{boden['streuung']:.4f}. Das Mass misst nicht, was draufsteht.")
            return 1
    if not zeilen[-1][1]:
        print(f"\nDER GROESSTE ABSTAND ({ABSTAENDE[-1]}) GILT NICHT ALS BELEGT — dann "
              f"belegt dieses Mass nie etwas.")
        return 1
    print("  Leiter:   ", _leiter(
        ziel, zeilen,
        "03_belegt-ab_" + "_".join(
            f"{a:.2f}-{'ja' if b else 'nein'}" for a, b in zeilen)
        + f"_grenze-{zeilen[0][0]:.2f}.png").name)

    # ── 4: die Auswahl ueber drei Startwerte, mit der echten Funktion ──
    drei = [{"score": w, "seed": i} for i, w in enumerate((-0.79, -0.27, -0.66))]
    wahl = varianten.waehle(drei, schwelle=geometrie_qa.SCHWELLE_GEOMETRIE)
    print(f"\n  Auswahl aus drei Startwerten: Index {wahl['index']} "
          f"(Wert {wahl['beste']['score']}), bestanden={wahl['bestanden']}")
    print(f"  Begruendung: {wahl['begruendung'][:96]}")
    print("  Auswahl:  ", _auswahl(
        ziel, [d["score"] for d in drei], wahl["index"],
        f"04_auswahl_drei-startwerte"
        f"_werte-{drei[0]['score']}-{drei[1]['score']}-{drei[2]['score']}"
        f"_gewaehlt-index-{wahl['index']}_bestanden-{wahl['bestanden']}"
        f"_die-anderen-bleiben-sichtbar.png").name)
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
