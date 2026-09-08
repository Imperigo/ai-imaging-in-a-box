#!/usr/bin/env python3
"""TRAEGT EINE FRONTALE INNENANSICHT EIN GEOMETRIE-URTEIL? — `auf-20260909-89`.

Die Gegenstelle hat die **Vorpruefung an der Soll-Karte** gemessen
(``tools/studie_innenansicht.py``, ohne Schaetzer, ohne GPU): frontal liegen 57-79 %
des Bildes auf **einem einzigen** Tiefenwert, ueber Eck 0,5-0,6 %. Offen blieb, ob
«von einer Flaeche beherrscht» auch heisst «rho misst dort nichts» — denn rho laeuft
ueber die **geschaetzte** Karte, und dafuer braucht es torch und die Karte.

Diese Studie aendert an der Vorpruefung **nichts** und haengt genau einen Schritt an:

    Aus dem gerenderten Bild wird eine Ist-Karte geschaetzt
    (``depth-anything-v2-small``) und ueber der **Bauwerksmaske aus dem
    Material-ID-Pass** gegen die Soll-Karte gehalten.

Vier Faelle, drei Startwerte je Fall, ein Bild je Lauf. Die Standpunkte werden **nicht
abgeschrieben**, sondern aus ``raumkamera.standpunkte`` ueber denselben
``ifc_raeume``-Bericht gerechnet — nur so kann die Gegenprobe (V5) ueberhaupt
widersprechen.

Der Ablauf je Fall ist woertlich der des Produktpfads
(``tools/homeworker._render_und_qa``): Multipass, Maske, Soll-Karte aus der EXR,
Render, ``qa_gegen_soll`` MIT Maske. Dazu kommt je Fall die **Nullprobe**
(``abholer._nullprobe``) — dieselbe Maskenlage, Bilder ohne jede Geometrie. Ohne sie
ist rho eine Zahl ohne Bezug.

Laufbefehl::

    AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \
        .venv-render/bin/python tools/studie_innenmessung.py build/innen

Ergebnis: ``roh.json`` im angegebenen Verzeichnis, je Fall eine Zeile mit allen drei
Startwerten, dem Nullanker und dem Kamerablock des Multipass-Berichts.

Regel 3: Zurueck ins Repo gehen nur Zahlen und Dateinamen. Die Bilder bleiben hier.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import (abholer, bildlesen, bildschreiben, geometrie_qa, kette,  # noqa: E402
                       maske as maske_modul, raumkamera, render, seams,
                       tiefenschaetzer)

#: Die vier Faelle. `raum`/`art` zeigen auf `raumkamera.standpunkte`; auge und blick_auf
#: werden **von dort geholt**, nicht hier eingetragen.
FAELLE = (
    ("A", "Raum-Nord", raumkamera.ART_FRONTAL),
    ("B", "Raum-Nord", raumkamera.ART_UEBER_ECK),
    ("C", "Raum-Sued", raumkamera.ART_FRONTAL),
    ("D", "Raum-Sued", raumkamera.ART_UEBER_ECK),
)

SEEDS = (0, 1, 2)
BRENNWEITE_MM = 24.0
AUFLOESUNG = 512
SAMPLES = 32

#: Innenraum statt Aussenansicht — der Standardprompt frueherer Laeufe beschreibt ein
#: Gebaeude von aussen und waere hier eine Bestellung, die zum Bild nicht passt.
PROMPT = ("photorealistic architectural interior view of a simple modern room, "
          "plain plastered walls, matte concrete floor, soft indirect daylight, "
          "no furniture, no people, eye-level interior view")


def standpunkte_aus_geometrie(ifc_pfad: str) -> dict:
    """Die vier Standpunkte, gerechnet — nicht abgeschrieben. Kostet keinen Renderlauf."""
    bericht = kette._raeume_lesen(ifc_pfad)
    aus = {}
    for kuerzel, raumname, art in FAELLE:
        gewaehlt = raumkamera.waehle(bericht, raum=raumname, art=art)
        if not gewaehlt["gefunden"]:
            aus[kuerzel] = {"gefunden": False, "grund": gewaehlt["grund"]}
            continue
        s = gewaehlt["standpunkt"]
        aus[kuerzel] = {
            "gefunden": True, "raum": raumname, "art": art,
            "auge": [float(v) for v in s["auge"]],
            "blick_auf": [float(v) for v in s["blick_auf"]],
            "brennweite_mm_sichtfeld": s["sichtfeld"]["brennweite_mm"],
        }
    return aus


def _kurz(pfad) -> str | None:
    return Path(pfad).name if pfad else None


def fahre_fall(kuerzel: str, punkt: dict, glb: dict, out: Path, *,
               render_modell, tiefen_modell, brennweite=BRENNWEITE_MM,
               breite_px=AUFLOESUNG, hoehe_px=None) -> dict:
    """Ein Fall: Multipass, Maske, Soll, drei Renderlaeufe, Nullprobe."""
    ordner = out / kuerzel
    ordner.mkdir(parents=True, exist_ok=True)
    zeile: dict = {"fall": kuerzel, "raum": punkt["raum"], "art": punkt["art"],
                   "auge": punkt["auge"], "blick_auf": punkt["blick_auf"],
                   "brennweite_bestellt_mm": brennweite,
                   "bildformat_bestellt": [breite_px, hoehe_px or breite_px]}

    t0 = time.monotonic()
    zusatz = {} if hoehe_px is None else {"hoehe": hoehe_px}
    bericht = seams.glb_zu_tiefenkarte(
        glb["glb_path"], ordner, up_axis=glb["up_axis"],
        aufloesung=breite_px, samples=SAMPLES, **zusatz,
        auge=punkt["auge"], blick_auf=punkt["blick_auf"], brennweite=brennweite)
    zeile["multipass_s"] = round(time.monotonic() - t0, 1)
    zeile["multipass_status"] = bericht.get("status")
    # V4 — was ist wirklich angekommen? Der Produktpfad `_render_und_qa` traegt diesen
    # Block NICHT in seine Messwerte; er ist nur hier zu sehen.
    kam = bericht.get("kamera") or {}
    zeile["kamera"] = {k: v for k, v in kam.items()
                       if k not in ("bild_png", "depth_png", "beauty_png")}
    if bericht.get("status") != "ok" or not bericht.get("depth_png"):
        zeile["fehler"] = bericht.get("error") or bericht.get("depth_png_fehler")
        return zeile

    maskenbefund = maske_modul.maske_aus_bericht(bericht, gelaende_erwartet=True)
    maske = maskenbefund.get("maske")
    zeile["maskenbefund"] = {k: v for k, v in maskenbefund.items()
                             if k not in ("maske", "material_id_png")}
    soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    zeile["breite"], zeile["hoehe"] = breite, hoehe

    # Die Vorpruefung der Gegenstelle, an DIESER Soll-Karte nachgerechnet: wieviel Bild
    # liegt auf einem einzigen Tiefenwert (1 cm gerundet)? Kostet nichts und sagt, ob
    # wir dieselbe Szene vor uns haben.
    endlich = [w for w in soll if w == w and abs(w) < 1e9]
    if endlich:
        stufen: dict[int, int] = {}
        for w in endlich:
            k = int(round(w * 100.0))
            stufen[k] = stufen.get(k, 0) + 1
        groesste = max(stufen.values())
        zeile["sollkarte"] = {
            "n_endlich": len(endlich), "n_bild": len(soll),
            "groesste_ebene_anteil_bild": round(groesste / len(soll), 4),
            "stufen": len(stufen),
            "spanne_m": round(max(endlich) - min(endlich), 3),
        }

    schwelle = geometrie_qa.SCHWELLE_GEOMETRIE
    laeufe = []
    for seed in SEEDS:
        a = render.RenderAuftrag(
            depth_png=bericht["depth_png"], prompt=PROMPT, negativ_prompt="",
            backbone=render.VORGABE_BACKBONE, seed=seed, schritte=20,
            controlnet_staerke=0.8, denoise=0.6,
            beauty_png=bericht.get("beauty_png"),
            ausgabe_png=str(ordner / f"render_seed{seed}.png"))
        r = render.rendere(a, modell=render_modell)
        eintrag = {"seed": seed, "render_status": r["status"],
                   "render_s": r.get("dauer_s"), "bild": _kurz(r.get("bild_png"))}
        if r["status"] != "ok":
            eintrag["fehler"] = r.get("error") or r.get("maengel")
            laeufe.append(eintrag)
            continue
        qa = tiefenschaetzer.qa_gegen_soll(
            r["bild_png"], soll, breite=breite, hoehe=hoehe, modell=tiefen_modell,
            schwelle=schwelle, maske=maske)
        eintrag["qa"] = {k: v for k, v in qa.items() if k != "bild_png"}
        laeufe.append(eintrag)
    zeile["laeufe"] = laeufe

    # V3 — der Nullanker aus derselben Nullprobe, ueber derselben Maskenlage.
    anker, maskenanker = abholer._nullprobe(
        ordner, soll, breite, hoehe, bildschreiben=bildschreiben,
        messen=tiefenschaetzer.qa_gegen_soll, grenze=schwelle,
        tiefen_modell=tiefen_modell, maske=maske)
    zeile["nullanker_score"] = anker
    zeile["nullanker_maske"] = maskenanker
    return zeile


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0] if argv else "build/innen")
    nur = [a.split("=", 1)[1] for a in argv if a.startswith("--fall=")]
    breite_px = next((int(a.split("=", 1)[1]) for a in argv if a.startswith("--breite=")),
                     AUFLOESUNG)
    hoehe_px = next((int(a.split("=", 1)[1]) for a in argv if a.startswith("--hoehe=")),
                    None)
    out.mkdir(parents=True, exist_ok=True)

    ifc = out / "raeume.ifc"
    if not ifc.exists():
        raise SystemExit(f"{ifc} fehlt — bitte tools/make_test_ifc.py --raeume laufen lassen.")

    punkte = standpunkte_aus_geometrie(str(ifc))
    (out / "standpunkte.json").write_text(
        json.dumps(punkte, indent=1, ensure_ascii=False), encoding="utf-8")

    glb = seams.ifc_zu_glb(str(ifc), str(out / "modell.glb"))
    if glb.get("status") != "ok":
        raise SystemExit(f"IFC→glb: {glb.get('error')}")

    print("Modelle laden …", flush=True)
    render_modell = render.lade_modell(render.VORGABE_BACKBONE)
    tiefen_modell = tiefenschaetzer.lade_modell(tiefenschaetzer.VORGABE_TIEFENSCHAETZER)

    zeilen = []
    ziel = out / "roh.json"
    if ziel.exists():
        zeilen = json.loads(ziel.read_text(encoding="utf-8"))
    fertig = {z["fall"] for z in zeilen}
    for kuerzel, _raum, _art in FAELLE:
        if nur and kuerzel not in nur:
            continue
        if kuerzel in fertig:
            print(f"{kuerzel}: liegt vor, uebersprungen", flush=True)
            continue
        p = punkte[kuerzel]
        if not p.get("gefunden"):
            zeilen.append({"fall": kuerzel, "fehler": p["grund"]})
            continue
        print(f"{kuerzel}: {p['raum']} {p['art']} …", flush=True)
        zeilen.append(fahre_fall(kuerzel, p, glb, out,
                                 render_modell=render_modell,
                                 tiefen_modell=tiefen_modell,
                                 breite_px=breite_px, hoehe_px=hoehe_px))
        ziel.write_text(json.dumps(zeilen, indent=1, ensure_ascii=False),
                        encoding="utf-8")
        print(f"{kuerzel}: fertig", flush=True)
    ziel.write_text(json.dumps(zeilen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"geschrieben: {ziel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
