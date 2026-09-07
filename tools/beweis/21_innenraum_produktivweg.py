#!/usr/bin/env python3
"""BEWEIS 21 — Die **automatisch abgeleitete Innenraumkamera** geht durch den
Produktivweg: IFC-Räume → `raumkamera` → **fremder Vertrag** (`CameraSpec`) →
`kosmo_szene.lies_szene` → `abholer.verarbeiter` → echter Blender-Lauf.

Warum dieser Beweis nötig war
-----------------------------
`docs/PLAN.md` führt seit dem 09.09.2026 die Zeile «die Innenansicht erreicht den
Produktivweg nicht — verdrahtet ist sie in `kette.py`, und das ruft niemand». Das ist
**zur Hälfte falsch**, und die Hälfte ist am Bild zu entscheiden:

* Die **Kamera** erreicht den Produktivweg sehr wohl. `kosmo_szene.spec_zu_kamera`
  übersetzt ihre ``position``/``target``/``fov`` in unsere ``auge``/``blick_auf``/
  ``brennweite_mm``, und `abholer.verarbeiter` reicht alle drei an
  `seams.glb_zu_multipass` weiter. Ein Innenstandpunkt ist also **heute schon
  bestellbar** — dieses Skript bestellt einen und zeigt das Ergebnis.
* Was den Produktivweg **nicht** erreicht, ist die **Ableitung**: Niemand rechnet dort
  aus den Räumen, wo die Kamera stehen soll. Und das ist kein vergessenes Kabel,
  sondern eine Vertragsfrage — der Renderweg bekommt eine **glb**
  (`kosmo_szene.DURCHGEREICHT["geometrie"]`: «abholer: Pfad der glb»), und Räume sind
  ``IfcSpace``, die es in der glb nicht mehr gibt.

Der Unterschied ist teuer: «nicht verdrahtet» hiesse, jemand müsste eine Zeile
schreiben. «Der Renderweg sieht die Räume nicht» heisst, dass die Zahlen **vorher**
gerechnet und mitgeschickt werden müssen — genau das tut dieses Skript, und genau das
täte auch KosmoOrbit.

Woran man es im Bild sieht
--------------------------
* ``01_raum_*.png`` — der Grundriss des Raums aus dem **echten** ``ifc_raeume``-Bericht,
  mit dem von `raumkamera.frontaler_standpunkt` gerechneten Auge (heller Punkt), der
  Blickrichtung und dem Sichtfeld bei 24 mm. Kein Wert ist gesetzt: Polygon, Auge,
  Zielpunkt und Öffnungswinkel kommen alle aus dem Aufruf.
* ``02_raum_*.png`` — dasselbe für `eck_standpunkt`. Dass die beiden Kegel verschieden
  liegen, ist der ganze Owner-Entscheid vom 22.08.2026 in einem Bild.
* ``03_..._beauty_*.png`` / ``04_..._tiefe_*.png`` — was Blender aus diesem Standpunkt
  **wirklich** gerendert hat, gefahren über `abholer.verarbeiter`. Der Weg ist derselbe,
  den ein Auftrag aus KosmoOrbit nimmt; nur `render`, `soll` und `qa` sind ersetzt, weil
  sie Gewichte brauchen, die hier nicht liegen.
* ``07_tiefenebenen_*.png`` — je Blickart, wieviel Prozent des **ganzen** Bildes auf der
  grössten einzelnen Tiefenebene liegen (auf 1 cm gerundet). Das ist die Messung vom
  09.09.2026, jetzt am Produktivweg statt an der Studie.

Was hier NICHT bewiesen wird
----------------------------
Das erzeugte Bild. `render.rendere` braucht torch, GPU und Gewichte — keins davon liegt
hier. Der Ersatz schreibt eine erkennbare Attrappe und behauptet nichts.

Aufruf:
    python3 tools/beweis/21_innenraum_produktivweg.py [ziel_verzeichnis]
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import abholer, bildlesen, bildschreiben, kosmo_szene, raumkamera, seams  # noqa: E402

import make_test_ifc  # noqa: E402
import studie_innenansicht  # noqa: E402

# DIESELBEN BILDMASSE WIE DIE STUDIE VOM 09.09.2026 (`tools/studie_innenansicht.py`,
# 800x496). Das ist keine Kosmetik: Der Anteil auf der groessten Tiefenebene haengt am
# Seitenverhaeltnis — bei 4:3 sieht eine Ueber-Eck-Aufnahme weniger zur Seite und faellt
# damit staerker auf eine Wand. Bei 384x288 gemessen kamen 21,6 % heraus, wo die Studie
# 0,6 % nennt. **Zwei Zahlen unter zwei Bedingungen sind keine zwei Messungen desselben.**
BREITE = 800
HOEHE = 496
SAMPLES = 8
BRENNWEITE_MM = 24.0

#: Farben des Grundrisses. Der Boden hell, die Wand dunkel, das Auge und der Kegel warm —
#: dieselbe Rolle wie in Beweis 01, damit die Reihe eine Handschrift hat.
GRUND = (243, 243, 241)
WAND = (60, 66, 74)
KEGEL = (232, 168, 58)
AUGE = (200, 60, 48)
ZIEL = (60, 110, 200)


def _leinwand(breite: int, hoehe: int, farbe=GRUND) -> list[list[int]]:
    return [list(farbe) for _ in range(breite * hoehe)]


def _setze(bild, breite, hoehe, x, y, farbe):
    if 0 <= x < breite and 0 <= y < hoehe:
        bild[y * breite + x] = list(farbe)


def _scheibe(bild, breite, hoehe, x, y, r, farbe):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                _setze(bild, breite, hoehe, x + dx, y + dy, farbe)


def _linie(bild, breite, hoehe, a, b, farbe):
    x0, y0 = a
    x1, y1 = b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        _setze(bild, breite, hoehe, round(x0 + (x1 - x0) * i / n),
               round(y0 + (y1 - y0) * i / n), farbe)


def _abbildung(polygon, breite, hoehe, rand=24):
    """Weltkoordinaten → Bildkoordinaten. Massstabstreu, y nach unten gespiegelt."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    spanne = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    m = (min(breite, hoehe) - 2 * rand) / spanne
    x0, y0 = min(xs), min(ys)

    def ab(p):
        return (round(rand + (p[0] - x0) * m), round(hoehe - rand - (p[1] - y0) * m))
    return ab


def _grundriss(ziel: Path, raum: dict, stand: dict, art: str) -> Path:
    """Der Raum, das Auge, der Blick und das Sichtfeld — alles aus dem Aufruf."""
    polygon = raumkamera._als_polygon(raum["grundriss_m"])
    ab = _abbildung(polygon, BREITE, HOEHE)
    bild = _leinwand(BREITE, HOEHE)

    for i in range(len(polygon)):
        _linie(bild, BREITE, HOEHE, ab(polygon[i]), ab(polygon[(i + 1) % len(polygon)]),
               WAND)

    auge, blick = stand["auge"], stand["blick_auf"]
    # DER ÖFFNUNGSWINKEL WIRD GERECHNET UND NICHT GEMALT: aus der Brennweite, die im
    # Standpunkt steht, über dieselbe Sensorbreite wie `kosmo_szene.brennweite_zu_fov`.
    f = (stand.get("sichtfeld") or {}).get("brennweite_mm") or BRENNWEITE_MM
    halb = math.atan(18.0 / f)
    richtung = math.atan2(blick[1] - auge[1], blick[0] - auge[0])
    weite = math.dist(auge[:2], blick[:2]) * 1.6
    for seite in (-1, 1):
        w = richtung + seite * halb
        _linie(bild, BREITE, HOEHE, ab(auge[:2]),
               ab((auge[0] + weite * math.cos(w), auge[1] + weite * math.sin(w))), KEGEL)
    _linie(bild, BREITE, HOEHE, ab(auge[:2]), ab(blick[:2]), ZIEL)
    _scheibe(bild, BREITE, HOEHE, *ab(blick[:2]), 3, ZIEL)
    _scheibe(bild, BREITE, HOEHE, *ab(auge[:2]), 4, AUGE)

    name = (f"{'01' if art == 'frontal' else '02'}_raum-{_rein(raum.get('name'))}"
            f"_{art}_auge-{auge[0]:.2f}-{auge[1]:.2f}-{auge[2]:.2f}"
            f"_ziel-{blick[0]:.2f}-{blick[1]:.2f}_brennweite-{f:.0f}mm.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, bild, BREITE, HOEHE)
    return pfad


def _rein(text) -> str:
    return "".join(c if c.isalnum() else "-" for c in str(text or "ohne-name"))


def _ebenenanteil(bericht) -> tuple[float, int]:
    """Anteil des **ganzen Bildes** auf der grössten einzelnen Tiefenebene (1 cm).

    **Gerechnet wird das hier nicht zum zweiten Mal.** `tools/studie_innenansicht.py`
    rechnet dieselbe Zahl seit dem 09.09.2026; sie wird von dort geholt.

    Der erste Anlauf dieses Skripts hat sie nachgebaut, und der Nachbau war falsch: Er
    schloss den Hintergrund über ``w in (inf, -inf)`` aus, während der Runner ihn als
    **endliche** ~1e10 m zurückgibt. Der ganze Himmel fiel damit in EINEN Kübel, und die
    Über-Eck-Aufnahme kam auf 15,8 % statt 0,6 % — eine Zahl, die genau in die Richtung
    log, in die man sie gern hätte. Die frontale Aufnahme stimmte dabei aufs Zehntel
    (78,8 %), und das ist das Tückische daran: Ein Nachbau, der in einem von zwei Fällen
    exakt trifft, sieht geprüft aus.
    """
    kennzahlen = studie_innenansicht._kennzahlen(bericht)
    return kennzahlen["groesste_ebene_anteil"] or 0.0, kennzahlen["stufen"]


def _balken(ziel: Path, werte: list[tuple[str, float]], name: str) -> Path:
    breite, hoehe = 520, 60 * len(werte) + 40
    bild = _leinwand(breite, hoehe)
    for i, (_, anteil) in enumerate(werte):
        y0 = 20 + i * 60
        laenge = max(2, round((breite - 60) * anteil))
        farbe = AUGE if anteil >= 0.5 else (70, 130, 90)
        for y in range(y0, y0 + 40):
            for x in range(30, 30 + laenge):
                _setze(bild, breite, hoehe, x, y, farbe)
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, bild, breite, hoehe)
    return pfad


def _attrappe_rendern(a, **kw):
    """Ersatz für `render.rendere` — er behauptet nichts.

    Ein Streifenmuster, das man auf den ersten Blick als Attrappe erkennt. Ein
    Ersatz, der *wie ein Ergebnis aussieht*, wäre in diesem Projekt schon zweimal
    als eines gelesen worden.
    """
    p = Path(a.ausgabe_png)
    p.parent.mkdir(parents=True, exist_ok=True)
    breite = hoehe = 64
    werte = [1.0 if ((x // 4) + (y // 4)) % 2 else 0.0
             for y in range(hoehe) for x in range(breite)]
    bildschreiben.schreibe_graustufen_png(p, werte, breite, hoehe)
    return {"status": "ok", "bild_png": str(p)}


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis21-"))

    # 1 — Geometrie MIT Räumen, synthetisch und im Repo erzeugbar (Regel 3).
    ifc = arbeit / "raeume.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_raeumen=True)

    # 2 — Die Räume aus der ECHTEN Datei, über die Prozessgrenze (ifcopenshell im venv).
    raeume = seams.ifc_raeume(ifc)
    if raeume.get("status") != "ok" or not raeume.get("raeume"):
        print(f"ifc_raeume liefert nichts Brauchbares: {raeume.get('status')!r}")
        return 1

    # 3 — DIE ABLEITUNG. Beide Blickarten, gerechnet und nicht gewählt.
    raum = raeume["raeume"][0]
    beide = raumkamera.standpunkte(raum, brennweite_mm=BRENNWEITE_MM,
                                   seitenverhaeltnis=BREITE / HOEHE)
    stand = {s["art"]: s for s in beide["standpunkte"]}
    brauchbar = {a: s for a, s in stand.items() if s.get("auge")}
    if not brauchbar:
        print(f"Kein brauchbarer Standpunkt: {beide['befund']}")
        return 1
    for art, s in brauchbar.items():
        print("  Grundriss:", _grundriss(ziel, raum, s, art).name)

    # 4 — Dieselbe Geometrie als glb: das ist es, was der Renderweg bekommt.
    glb = arbeit / "szene.glb"
    # `ifc_zu_glb` schreibt **Y-up** (glTF-2.0-Standard). Das ist der Grund, warum die
    # Hochachse weiter unten `"y"` ist und nicht `"z"`: Sie beschreibt die DATEI. Der
    # Runner dreht sie beim Laden in Blenders Z-up — und damit stehen die Weltkoordinaten
    # wieder so, wie `raumkamera` sie aus der IFC gerechnet hat.
    umbau = seams.ifc_zu_glb(ifc, glb)
    if isinstance(umbau, dict) and umbau.get("status") not in (None, "ok"):
        print(f"ifc_zu_glb: {umbau.get('status')!r}")
        return 1

    # 5 — DER FREMDE VERTRAG. Aus unseren Standpunkten werden ihre CameraSpecs.
    specs = [kosmo_szene.kamera_zu_spec(
        {"kuerzel": art, "auge": s["auge"], "blick_auf": s["blick_auf"],
         "brennweite_mm": (s.get("sichtfeld") or {}).get("brennweite_mm", BRENNWEITE_MM)})
        for art, s in brauchbar.items()]
    fremd = {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": str(glb), "format": "glb"},
        "cameras": specs,
        "render": {"resolution": [BREITE, HOEHE], "samples": SAMPLES, "faithful": 0.8},
        "vis": {"backbone": "qwen"},
        "out": str(ziel / "_lauf"),
        "prompt": "Innenraum",
    }
    szene = kosmo_szene.lies_szene(fremd)
    if szene["maengel"]:
        print("Mängel des Vertrags:", "; ".join(szene["maengel"]))
        return 1

    # 6 — DER PRODUKTIVWEG. Multipass echt, der Rest ersetzt (Gewichte fehlen hier).
    verarbeite = abholer.verarbeiter(
        up_axis="y", nullprobe=False, rahmung_pruefen=False,
        _rendere=_attrappe_rendern,
        _soll=lambda bericht: ([0.0, 1.0, 2.0, 3.0], 2, 2),
        _qa=lambda bild, soll, **kw: {"score": None, "bestanden": None,
                                      "grund": "kein Schaetzer in dieser Umgebung"},
    )
    ergebnis = verarbeite({
        "szene": szene, "modell": glb, "verzeichnis": arbeit,
        "ausgabe": ziel / "_lauf", "hochachse": "y",
    })

    # 7 — WAS DER LAUF AUF DIE PLATTE GELEGT HAT. Gelesen wird der Ordner, nicht das
    # Rückgabewörterbuch: Ein Ergebnisfeld ist eine Behauptung über eine Datei, und in
    # diesem Projekt sind schon zweimal Behauptungen ohne Datei gezählt worden.
    import json
    anteile = []
    for ordner in sorted((ziel / "_lauf").glob("*")):
        if not ordner.is_dir():
            continue
        kuerzel = ordner.name
        report = ordner / "blender-report.json"
        bericht = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
        f = (bericht.get("kamera") or {}).get("brennweite_mm")
        weg = (bericht.get("kamera") or {}).get("weg")
        for nr, datei, was in (("03", "beauty_.png", "beauty"),
                               ("04", "tiefe_norm.png", "tiefe-normalisiert"),
                               ("06", "material_id.png", "material-id")):
            quelle = ordner / datei
            if quelle.is_file():
                neu_p = ziel / (f"{nr}_{_rein(kuerzel)}_{was}_produktivweg"
                                f"_brennweite-{f}mm_kameraweg-{_rein(weg)}.png")
                neu_p.write_bytes(quelle.read_bytes())
                print("  Blender:", neu_p.name)
        if (ordner / "tiefe_0001.exr").is_file():
            werte, b, h = bildlesen.tiefen_aus_report(bericht)
            anteil, stufen = _ebenenanteil(bericht)
            anteile.append((kuerzel, anteil))
            fp = ziel / (f"05_{_rein(kuerzel)}_tiefe-aus-exr"
                         f"_groesste-ebene-{anteil * 100:.1f}pct_stufen-{stufen}.png")
            grau, norm = bildschreiben.normalisiere_tiefe(werte)
            bildschreiben.schreibe_graustufen_png(fp, grau, b, h)
            print("  Tiefe:", fp.name)

    if anteile:
        name = ("07_tiefenebenen_" + "_".join(
            f"{_rein(k)}-{a * 100:.1f}pct" for k, a in anteile) + ".png")
        print("  Balken:", _balken(ziel, anteile, name).name)

    geschrieben = sorted(p.name for p in ziel.rglob("*.png"))
    print(f"\n{len(geschrieben)} Bilder in {ziel}")
    return 0 if geschrieben else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
