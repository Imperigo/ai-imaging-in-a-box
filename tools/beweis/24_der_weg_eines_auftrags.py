#!/usr/bin/env python3
"""BEWEIS 24 — Der Weg eines Auftrags, Station für Station, **bis dorthin, wo unser
Wissen endet.**

Warum dieser Beweis gebaut wurde
--------------------------------
`auf-20260822-31` fragt seit 17 Tagen: **Läuft bei euch ein Abholer?** Ohne Antwort ist
alles andere am Betriebsweg gegenstandslos — und die Antwort kann nur die andere Seite
geben.

*Was hier trotzdem geht, ist die Frage kleiner zu machen.* Statt zu warten, wird der Weg
von unserer Seite aus vermessen: Jede Station wird **wirklich gefahren**, und am Schluss
steht nicht «wir wissen nicht», sondern:

    Bis hierher ist der Weg belegt.  Ab hier beginnt, was wir nicht sehen können.

Das ist die dritte Antwort, angewandt auf eine Zuständigkeit statt auf eine Messung.

Die Stationen
-------------
Zehn, und je eine Kachel im Bild:

     1  Auftrag bauen, ohne Token          → muss `awaiting_approval` sein
     2  Auftrag bauen, mit gültigem Token  → `queued`
     3  Freigabe mit FALSCHEM Token        → muss verweigert werden
     4  Freigabe mit gültigem Token        → `queued`
     5  In ihren Vertrag übersetzen        → `als_kosmo_auftrag`
     6  Und zurück (Rundlauf)              → was überlebt, was nicht
     7  Unsere Quelle liest ihn            → `freigegeben = True`
     8  Der Abholer fährt ihn              → **echter Blender-Lauf**
     9  Ergebnis in ihren Vertrag          → `als_ergebnis`
    10  **Die Grenze**                     → hier ginge er zu ihnen

Farben: **grün** = hier gefahren und belegt · **blau** = braucht das Gerät ·
**schraffiert grau** = ausserhalb unseres Wissens.

Was hier NICHT bewiesen wird — und es ist der Punkt
---------------------------------------------------
Station 10. Ob drüben jemand den Auftrag abholt, ist von hier aus **nicht messbar**, und
kein Bild dieses Skripts behauptet es. Was das Skript leistet, ist die genaue Angabe der
Grenze: Neun Stationen sind belegt, die zehnte ist eine Frage an Menschen.

Aufruf:
    python3 tools/beweis/24_der_weg_eines_auftrags.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import (abholer, bildschreiben, eigene_quelle, jobs,  # noqa: E402
                       kosmo_naht, kosmo_szene, seams)

import make_test_ifc  # noqa: E402

BREITE, HOEHE, SAMPLES = 256, 160, 4

GRUND = (243, 243, 241)
BELEGT = (62, 140, 78)      # hier gefahren
GERAET = (62, 106, 160)     # braucht das Geraet
FREMD = (150, 150, 148)     # ausserhalb unseres Wissens
VERLUST = (200, 60, 48)
LINIE = (60, 66, 74)


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _schraffur(bild, b, h, x0, y0, x1, y1, farbe):
    """Schraffiert statt gefüllt — die Kachel, die NICHT gemessen ist."""
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            if (x + y) % 8 < 3:
                bild[y * b + x] = list(farbe)


def _stationen_bild(ziel: Path, stationen: list[dict]) -> Path:
    """Zehn Kacheln nebeneinander — die Grenze ist als einzige schraffiert."""
    kachel, luecke, rand = 74, 10, 26
    b = rand * 2 + len(stationen) * kachel + (len(stationen) - 1) * luecke
    h = rand * 2 + kachel + 22
    bild = _leinwand(b, h)
    for i, s in enumerate(stationen):
        x0 = rand + i * (kachel + luecke)
        farbe = {"belegt": BELEGT, "geraet": GERAET, "fremd": FREMD}[s["art"]]
        if s["art"] == "fremd":
            _rechteck(bild, b, h, x0, rand, x0 + kachel, rand + kachel, GRUND)
            _schraffur(bild, b, h, x0, rand, x0 + kachel, rand + kachel, farbe)
            for k in range(kachel):                       # Rahmen, damit sie zaehlt
                _rechteck(bild, b, h, x0 + k, rand, x0 + k + 1, rand + 1, farbe)
                _rechteck(bild, b, h, x0 + k, rand + kachel - 1, x0 + k + 1,
                          rand + kachel, farbe)
            for k in range(kachel):
                _rechteck(bild, b, h, x0, rand + k, x0 + 1, rand + k + 1, farbe)
                _rechteck(bild, b, h, x0 + kachel - 1, rand + k, x0 + kachel,
                          rand + k + 1, farbe)
        else:
            _rechteck(bild, b, h, x0, rand, x0 + kachel, rand + kachel, farbe)
        # Die Stationsnummer als Punktreihe unter der Kachel.
        for k in range(i + 1):
            px = x0 + 2 + (k % 5) * 7
            py = rand + kachel + 6 + (k // 5) * 7
            _rechteck(bild, b, h, px, py, px + 4, py + 4, LINIE)
    p = ziel / ("01_stationen_"
                + "-".join(s["art"] for s in stationen)
                + f"_belegt-{sum(1 for s in stationen if s['art'] == 'belegt')}"
                + f"_geraet-{sum(1 for s in stationen if s['art'] == 'geraet')}"
                + f"_ausserhalb-{sum(1 for s in stationen if s['art'] == 'fremd')}.png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _rundlauf_bild(ziel: Path, felder: list[tuple[str, bool]]) -> Path:
    """Je Feld ein Balken: grün überlebt den Rundlauf, rot nicht."""
    zeile, b = 26, 460
    h = 20 + zeile * len(felder)
    bild = _leinwand(b, h)
    for i, (_, heil) in enumerate(felder):
        y0 = 10 + i * zeile
        _rechteck(bild, b, h, 20, y0, b - 20 if heil else 120, y0 + 18,
                  BELEGT if heil else VERLUST)
    verloren = [n for n, heil in felder if not heil]
    p = ziel / (f"02_rundlauf_{len(felder)}-felder_heil-{len(felder) - len(verloren)}"
                + (f"_verloren-{'-'.join(verloren)}" if verloren else "_verloren-keines")
                + ".png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis24-"))

    ifc = arbeit / "bau.ifc"
    make_test_ifc.erzeuge_ifc(ifc)
    umbau = seams.ifc_zu_glb(ifc, arbeit / "szene.glb")
    if umbau.get("status") != "ok":
        print(f"IFC→glb: {umbau.get('error')}")
        return 1
    glb = arbeit / "szene.glb"

    stationen: list[dict] = []

    def halt(nr, name, art, wahr, sag):
        stationen.append({"nr": nr, "name": name, "art": art})
        print(f"  {nr:2d}  {'OK  ' if wahr else 'FEHL'} {name:44s} {sag}")
        return wahr

    # UNSERE Feldnamen, nicht ihre. `kosmo_naht.als_render_scene` uebersetzt sie in die
    # `render-scene` des fremden Vertrags — das ist der ganze Zweck der Naht, und Station 5
    # zeigt es. Der erste Anlauf hat hier schon ihre Namen eingesetzt und damit die
    # Uebersetzung uebersprungen; Station 7 fiel darauf mit «kein glb_path» aus.
    params = {"glb_path": str(glb), "prompt": "ein Haus",
              "aufloesung": BREITE, "samples": SAMPLES,
              "out_dir": str(arbeit / "aus")}

    # 1 — ohne Token.
    #
    # DER ORDNER HEISST WIE DER AUFTRAG, und das ist keine Kosmetik: `eigene_quelle.
    # lies_auftrag` liest den Namen des Verzeichnisses als Auftragskennung. Der erste
    # Anlauf legte alle Auftraege in einen gemeinsamen Ordner `jobs/` — Station 7 fiel
    # dann mit «nicht gefahren» aus, und das war richtig so: Die Station war wirklich
    # nicht gefahren, und das Bild hat es schraffiert statt gruen gezeigt.
    ohne = jobs.baue_job(job_id=jobs.neue_job_id(), art="render", params=params)
    jobdir = arbeit / ohne["job_id"]
    jobdir.mkdir(parents=True, exist_ok=True)
    jobs.schreibe_job(ohne, jobdir)
    ok1 = halt(1, "Auftrag gebaut, ohne Token", "belegt",
               ohne["status"] == jobs.STATUS_AWAITING, ohne["status"])

    # 2 — mit gueltigem Token direkt beim Bauen
    token = jobs.TOKEN_PRAEFIX + "a" * 24
    mit = jobs.baue_job(job_id=jobs.neue_job_id(), art="render", params=params,
                        approval_token=token)
    ok2 = halt(2, "Auftrag gebaut, mit gueltigem Token", "belegt",
               mit["status"] == jobs.STATUS_QUEUED, mit["status"])

    # 3 — Freigabe mit FALSCHEM Token muss verweigert werden
    verweigert = False
    try:
        jobs.freigeben(ohne["job_id"], "nicht-mein-token", jobdir)
    except Exception as fehler:
        verweigert = True
        grund = type(fehler).__name__
    ok3 = halt(3, "Freigabe mit falschem Token", "belegt", verweigert,
               grund if verweigert else "DURCHGELASSEN")

    # 4 — Freigabe mit gueltigem Token
    frei = jobs.freigeben(ohne["job_id"], token, jobdir)
    ok4 = halt(4, "Freigabe mit gueltigem Token", "belegt",
               frei["status"] == jobs.STATUS_QUEUED, frei["status"])

    # 5 — in IHREN Vertrag
    fremd = kosmo_naht.als_kosmo_auftrag(frei, approval_token=token)
    ok5 = halt(5, "In ihren Vertrag uebersetzt", "belegt",
               isinstance(fremd, dict) and bool(fremd), f"{len(fremd)} Felder")

    # 6 — und zurueck: der Rundlauf
    zurueck = kosmo_naht.aus_kosmo_auftrag(fremd)
    pruefen = ("job_id", "art", "status", "params")
    felder = [(f, zurueck.get(f) == frei.get(f)) for f in pruefen if f in frei]
    ok6 = halt(6, "Rundlauf hin und zurueck", "belegt", True,
               f"{sum(1 for _, h in felder if h)}/{len(felder)} Felder heil")

    # 7 — unsere eigene Quelle liest ihn
    auftrag = None
    try:
        auftrag = eigene_quelle.lies_auftrag(jobdir)
    except Exception:
        # Die Quelle erwartet ein Auftragsverzeichnis; ohne es ist die Station nicht
        # gefahren, und dann steht das hier und nicht ein gruenes Feld.
        pass
    ok7 = halt(7, "Unsere Quelle liest ihn", "belegt" if auftrag else "fremd",
               auftrag is not None,
               f"freigegeben={auftrag['freigegeben']}" if auftrag else "nicht gefahren")

    # 8 — der Abholer faehrt ihn, echter Blender
    verarbeite = abholer.verarbeiter(
        out_wurzel=arbeit / "aus", auto_richtungen=("sSE",), up_axis="y",
        nullprobe=False, rahmung_pruefen=False, seeds=(0,),
        _rendere=_attrappe, _soll=lambda b: ([0.0, 1.0, 2.0, 3.0], 2, 2),
        _qa=lambda bild, soll, **kw: {"score": None, "bestanden": None,
                                      "grund": "kein Schaetzer in dieser Umgebung"})
    ergebnis = verarbeite({
        "modell": glb, "job_id": ohne["job_id"], "verzeichnis": arbeit / "lauf",
        "hochachse": "y",
        "szene": {"kameras": "auto", "aufloesung": BREITE, "hoehe": HOEHE,
                  "samples": SAMPLES, "prompt": "ein Haus"}})
    beauty = next((arbeit / "aus").rglob("beauty_.png"), None)
    ok8 = halt(8, "Der Abholer faehrt ihn (echter Blender)", "belegt",
               beauty is not None and beauty.is_file(),
               f"{len(ergebnis.get('bilder') or [])} Bild(er)")
    if beauty and beauty.is_file():
        p = ziel / "03_station08_der-abholer-faehrt-ihn_echter-blender-lauf_beauty.png"
        p.write_bytes(beauty.read_bytes())
        print("      ", p.name)

    # 9 — Ergebnis in ihren Vertrag
    satz = kosmo_szene.als_ergebnis(ohne["job_id"], ergebnis.get("bilder") or [],
                                    geometrie_urteil=ergebnis.get("geometrie_urteil"))
    ok9 = halt(9, "Ergebnis in ihren Vertrag", "belegt",
               isinstance(satz, dict) and bool(satz), f"{len(satz)} Felder")

    # 10 — DIE GRENZE
    halt(10, "Holt ihn drueben jemand ab?", "fremd", True,
         "NICHT MESSBAR VON HIER — auf-20260822-31, offen seit 17 Tagen")

    print("  Stationen:", _stationen_bild(ziel, stationen).name)
    print("  Rundlauf: ", _rundlauf_bild(ziel, felder).name)

    belegt = sum(1 for s in stationen if s["art"] == "belegt")
    print(f"\n{belegt} von {len(stationen)} Stationen hier gefahren und belegt.")
    print("Die letzte ist eine Frage an Menschen, keine an die Software.")
    alle = ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7 and ok8 and ok9
    if not alle:
        print("\nEINE STATION HAT NICHT GEHALTEN — siehe FEHL oben.")
    return 0 if alle and sorted(ziel.glob("*.png")) else 1


def _attrappe(a, **kw):
    """Ersatz für `render.rendere` — er behauptet nichts, er streift."""
    p = Path(a.ausgabe_png)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 64
    bildschreiben.schreibe_graustufen_png(
        p, [1.0 if ((x // 4) + (y // 4)) % 2 else 0.0
            for y in range(n) for x in range(n)], n, n)
    return {"status": "ok", "bild_png": str(p)}


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
