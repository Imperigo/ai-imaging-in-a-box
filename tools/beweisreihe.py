#!/usr/bin/env python3
"""DER BEWEISGANG ALS BILDSERIE — sechs Kameras, je sieben Bildstellen.

Was hier laeuft, ist woertlich der Produktivweg (`tools/homeworker._render_und_qa`):
Multipass, Maske, Soll-Karte aus der EXR, Render, `qa_gegen_soll` MIT Maske, Nullprobe.
Neu ist nur, dass **jede Zwischenstufe als eigenes PNG stehen bleibt** statt bloss als
Zahl in einem Bericht.

Sieben Bildstellen je Kamera, in der Reihenfolge des Weges durch die Software::

    S1  beauty.png       was Blender sieht
    S2  tiefe.png        die Fuehrung (aus der EXR, ueber bildschreiben.tiefe_exr_zu_png)
    S3  material_id.png  der Material-ID-Pass, wie er faellt
    S4  maske.png        die Bauwerksmaske aus S3
    S5  erzeugt_s0/1/2   drei Startwerte, drei einzelne Dateien
    S6  kontroll_s0.png  das erzeugte Bild mit der Maskenkontur aus S4
    S7  nullanker.png    weisses Rauschen ueber derselben Maskenlage

Keine Montage, kein Zuschnitt, keine Nachbearbeitung: S1, S3 und S7 werden **kopiert**,
S2 und S4 von den Kernfunktionen geschrieben, S5 vom Bildmodell. S6 ist die einzige
Stelle, an der zwei Bilder uebereinanderliegen — und sie ist als **Kontrolle** bestellt
und nicht als Beweisbild.

Laufbefehl::

    AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \\
        .venv-render/bin/python tools/beweisreihe.py build/beweis

Regel 3: Es wird nichts ins Repo geschrieben — `build/` ist ignoriert. Die Bilder
bleiben auf dem Geraet, zurueck reisen nur Zahlen und Dateinamen.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import (abholer, backbone, bildlesen, bildschreiben,  # noqa: E402
                       geometrie_qa, glbbox, kameras, kette,
                       maske as maske_modul, prompts, raumkamera, render, seams,
                       tiefenschaetzer)

SEEDS = (0, 1, 2)
AUFLOESUNG = 512
SAMPLES = 32
SCHRITTE = 20
CONTROLNET_STAERKE = 0.8
DENOISE = 0.6

#: Vier Aussenkameras — die ersten vier der Rangfolge aus `kameras.standpunkte`.
ANZAHL_AUSSEN = 4

#: Die zwei Innenstandpunkte. Raum-Nord, frontal und ueber Eck.
INNEN = (("innen_frontal", "Raum-Nord", raumkamera.ART_FRONTAL),
         ("innen_ueber_eck", "Raum-Nord", raumkamera.ART_UEBER_ECK))

BRENNWEITE_INNEN_MM = 24.0

#: Innenraum statt Aussenansicht — derselbe Prompt wie in `tools/studie_innenmessung.py`,
#: damit die zwei Innenbilder mit der Messung vom 09.09. vergleichbar bleiben.
PROMPT_INNEN = ("photorealistic architectural interior view of a simple modern room, "
                "plain plastered walls, matte concrete floor, soft indirect daylight, "
                "no furniture, no people, eye-level interior view")

#: Die Kontur wird in Magenta gezogen — eine Farbe, die in keinem Architekturbild
#: vorkommt. Ein Grau waere im Bild nicht von ihm zu unterscheiden.
FARBE_KONTUR = (255, 0, 255)


# ── Die sieben Bildstellen ───────────────────────────────────────────────────────────

def _lege_ab(quelle, ziel: Path) -> str | None:
    """Ein fertiges Bild an seine Bildstelle **kopieren** — nicht bearbeiten."""
    if not quelle or not Path(quelle).is_file():
        return None
    shutil.copyfile(quelle, ziel)
    return ziel.name


def schreibe_maske(maske, breite: int, hoehe: int, ziel: Path) -> str:
    """S4 — die Bauwerksmaske schwarz/weiss. Genau die Flaeche, ueber der rho laeuft."""
    bildschreiben.schreibe_graustufen_png(
        ziel, [1.0 if m else 0.0 for m in maske], breite, hoehe, bittiefe=8)
    return ziel.name


def _kontur(maske, breite: int, hoehe: int) -> list[int]:
    """Die Randpixel der Maske — innen liegend, vier Nachbarn.

    Der Bildrand zaehlt als Aussen: Eine Maske, die am Bildrand abgeschnitten ist, hat
    dort eine Kontur, und sie zu verschweigen hiesse, den Beschnitt zu verstecken.
    """
    rand = []
    for y in range(hoehe):
        for x in range(breite):
            i = y * breite + x
            if not maske[i]:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= breite or ny >= hoehe:
                    rand.append(i)
                    break
                if not maske[ny * breite + nx]:
                    rand.append(i)
                    break
    return rand


def schreibe_kontrollbild(bild_png, maske, breite: int, hoehe: int, ziel: Path) -> dict:
    """S6 — das erzeugte Bild mit der Maskenkontur darueber.

    **Es wird nicht skaliert.** Passt das erzeugte Bild nicht auf die Maske, entsteht
    kein Kontrollbild, sondern ein Befund: Ein hochgerechnetes Bild wuerde die Frage
    «steht das Bauwerk an der richtigen Stelle» mit einer Rechnung beantworten, die
    genau diese Stelle verschiebt.
    """
    farben, b, h = bildlesen.lies_png_farben(bild_png)
    if (b, h) != (breite, hoehe):
        return {"geschrieben": None, "grund": (
            f"Erzeugtes Bild ist {b}x{h}, die Maske {breite}x{hoehe}. Es wird NICHT "
            f"skaliert — eine Umrechnung verschoebe genau das, was hier gezeigt werden "
            f"soll.")}
    aus = [tuple(f) for f in farben]
    rand = _kontur(maske, breite, hoehe)
    for i in rand:
        aus[i] = FARBE_KONTUR
    bildschreiben.schreibe_farb_png(ziel, aus, breite, hoehe)
    return {"geschrieben": ziel.name, "n_konturpixel": len(rand), "grund": ""}


# ── Ein Durchgang ────────────────────────────────────────────────────────────────────

def fahre_kamera(name: str, glb: dict, auge, blick_auf, brennweite, prompt: str,
                 negativ: str, wurzel: Path, *, render_modell, tiefen_modell,
                 stil_cn=None) -> dict:
    """Eine Kamera: Multipass, Maske, Soll, drei Renderlaeufe, QA, Nullprobe."""
    arbeit = wurzel / "arbeit" / name
    beweis = wurzel / name
    arbeit.mkdir(parents=True, exist_ok=True)
    beweis.mkdir(parents=True, exist_ok=True)

    z: dict = {"kamera": name,
               "auge": [float(v) for v in auge],
               "blick_auf": [float(v) for v in blick_auf],
               "brennweite_bestellt_mm": float(brennweite),
               "waagrecht": float(auge[2]) == float(blick_auf[2]),
               "stil_controlnet_staerke": stil_cn,
               "bildstellen": {}, "zeiten_s": {}}

    t0 = time.monotonic()
    bericht = seams.glb_zu_multipass(
        glb["glb_path"], arbeit, up_axis=glb["up_axis"],
        aufloesung=AUFLOESUNG, samples=SAMPLES,
        auge=list(auge), blick_auf=list(blick_auf), brennweite=float(brennweite))
    z["zeiten_s"]["multipass"] = round(time.monotonic() - t0, 1)
    z["multipass_status"] = bericht.get("status")
    kam = bericht.get("kamera") or {}
    z["kamera_bericht"] = {k: v for k, v in kam.items()
                           if k not in ("bild_png", "depth_png", "beauty_png")}
    if bericht.get("status") != "ok" or not bericht.get("depth_png"):
        z["fehler"] = bericht.get("error") or bericht.get("depth_png_fehler")
        return z

    # S1 · was Blender sieht
    z["bildstellen"]["S1_beauty"] = _lege_ab(bericht.get("beauty_png"),
                                             beweis / "S1_beauty.png")
    # S2 · die Fuehrung, aus der EXR, mit UNSERER Normalisierung
    norm = bildschreiben.tiefe_exr_zu_png(bericht["depth_exr"], beweis / "S2_tiefe.png")
    z["bildstellen"]["S2_tiefe"] = "S2_tiefe.png"
    z["tiefe_normalisierung"] = {k: v for k, v in norm.items()}
    z["tiefe_gleich_wie_multipass"] = (
        {k: norm.get(k) for k in ("min_m", "max_m")}
        == {k: (bericht.get("depth_normalisierung") or {}).get(k)
            for k in ("min_m", "max_m")})
    # S3 · der Material-ID-Pass, wie er faellt
    z["bildstellen"]["S3_material_id"] = _lege_ab(bericht.get("material_id_png"),
                                                  beweis / "S3_material_id.png")

    # S4 · die Bauwerksmaske daraus
    maskenbefund = maske_modul.maske_aus_bericht(bericht, gelaende_erwartet=True)
    maske = maskenbefund.get("maske")
    z["maskenbefund"] = {k: v for k, v in maskenbefund.items()
                         if k not in ("maske", "material_id_png")}
    soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    z["breite"], z["hoehe"] = breite, hoehe
    if maske is not None:
        z["bildstellen"]["S4_maske"] = schreibe_maske(maske, breite, hoehe,
                                                      beweis / "S4_maske.png")
        z["anteil_maske_am_bild"] = round(sum(1 for m in maske if m) / len(maske), 4)
    else:
        z["bildstellen"]["S4_maske"] = None

    # S5 · drei Startwerte, drei Dateien
    schwelle = geometrie_qa.SCHWELLE_GEOMETRIE
    laeufe = []
    t_render = t_qa = 0.0
    for seed in SEEDS:
        a = render.RenderAuftrag(
            depth_png=bericht["depth_png"], prompt=prompt, negativ_prompt=negativ,
            backbone=render.VORGABE_BACKBONE, seed=seed, schritte=SCHRITTE,
            controlnet_staerke=CONTROLNET_STAERKE, denoise=DENOISE,
            beauty_png=bericht.get("beauty_png"),
            ausgabe_png=str(beweis / f"S5_erzeugt_s{seed}.png"))
        t1 = time.monotonic()
        r = render.rendere(a, modell=render_modell)
        t_render += time.monotonic() - t1
        eintrag = {"seed": seed, "render_status": r["status"],
                   "render_s": r.get("dauer_s"),
                   "bild": Path(r["bild_png"]).name if r.get("bild_png") else None}
        z["bildstellen"][f"S5_erzeugt_s{seed}"] = eintrag["bild"]
        if r["status"] != "ok":
            eintrag["fehler"] = r.get("error") or r.get("maengel")
            laeufe.append(eintrag)
            continue
        z.setdefault("backbone", {"name": r.get("backbone"), "lizenz": r.get("lizenz")})
        t1 = time.monotonic()
        qa = tiefenschaetzer.qa_gegen_soll(
            r["bild_png"], soll, breite=breite, hoehe=hoehe, modell=tiefen_modell,
            schwelle=schwelle, maske=maske)
        t_qa += time.monotonic() - t1
        eintrag["qa"] = {k: v for k, v in qa.items() if k != "bild_png"}
        laeufe.append(eintrag)
    z["laeufe"] = laeufe
    z["zeiten_s"]["erzeugung"] = round(t_render, 1)
    z["zeiten_s"]["qa"] = round(t_qa, 1)

    # S6 · die Maskenkontur ueber dem Bild zum Startwert 0
    erst = beweis / "S5_erzeugt_s0.png"
    if maske is not None and erst.is_file():
        befund = schreibe_kontrollbild(erst, maske, breite, hoehe,
                                       beweis / "S6_kontroll_s0.png")
        z["bildstellen"]["S6_kontroll_s0"] = befund["geschrieben"]
        z["kontrollbild"] = befund
    else:
        z["bildstellen"]["S6_kontroll_s0"] = None

    # S7 · der Nullanker: weisses Rauschen ueber derselben Maskenlage
    t1 = time.monotonic()
    anker, maskenanker = abholer._nullprobe(
        arbeit, soll, breite, hoehe, bildschreiben=bildschreiben,
        messen=tiefenschaetzer.qa_gegen_soll, grenze=schwelle,
        tiefen_modell=tiefen_modell, maske=maske)
    z["zeiten_s"]["nullprobe"] = round(time.monotonic() - t1, 1)
    z["nullanker_score"] = anker
    z["nullanker_maske"] = maskenanker
    z["bildstellen"]["S7_nullanker"] = _lege_ab(arbeit / "nullprobe_rauschen.png",
                                                beweis / "S7_nullanker.png")

    z["zeiten_s"]["gesamt"] = round(
        sum(v for k, v in z["zeiten_s"].items() if k != "gesamt"), 1)
    return z


def zahlen_datei(z: dict) -> dict:
    """Was neben die Bilder gelegt wird — getrennt, nicht verrechnet."""
    je_seed = {}
    for lauf in z.get("laeufe") or []:
        qa = lauf.get("qa") or {}
        je_seed[f"s{lauf['seed']}"] = {
            "render_status": lauf.get("render_status"),
            "qa_status": qa.get("status"),
            "rho_maske": qa.get("rho_maske"),
            "kante": qa.get("kante"),
            "kantenanteil": qa.get("kantenanteil"),
            "score_ganzes_bild": qa.get("score"),
            "bestanden": qa.get("bestanden"),
            "paarurteil": qa.get("paarurteil"),
        }
    return {
        "kamera": z["kamera"],
        "auge": z.get("auge"), "blick_auf": z.get("blick_auf"),
        "waagrecht": z.get("waagrecht"),
        "brennweite_bestellt_mm": z.get("brennweite_bestellt_mm"),
        "kamera_brennweite_mm_aus_multipass": (z.get("kamera_bericht") or {}).get(
            "brennweite_mm"),
        "kamera_bericht": z.get("kamera_bericht"),
        "je_startwert": je_seed,
        "nullanker_score": z.get("nullanker_score"),
        "nullanker_maske": z.get("nullanker_maske"),
        "anteil_maske_am_bild": z.get("anteil_maske_am_bild"),
        "maskenbefund": z.get("maskenbefund"),
        "backbone": z.get("backbone"),
        "tiefe_normalisierung": z.get("tiefe_normalisierung"),
        "zeiten_s": z.get("zeiten_s"),
        "bildstellen": z.get("bildstellen"),
        "aufloesung": [z.get("breite"), z.get("hoehe")],
        "samples": SAMPLES,
        "schritte": SCHRITTE,
        # Gefahren wird mit der Vorgabe des Produktivwegs (`homeworker`, 0.8) und nicht
        # mit der des Stils. Beide stehen hier, damit die Abweichung sichtbar bleibt
        # statt zwischen zwei Vorgaben zu verschwinden.
        "controlnet_staerke": CONTROLNET_STAERKE,
        "controlnet_staerke_des_stils": z.get("stil_controlnet_staerke"),
        "denoise": DENOISE,
        "fehler": z.get("fehler"),
    }


# ── Kommandozeile ────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0] if argv and not argv[0].startswith("--") else "build/beweis")
    nur = [a.split("=", 1)[1] for a in argv if a.startswith("--nur=")]
    wurzel.mkdir(parents=True, exist_ok=True)

    bau_ifc = wurzel / "bau.ifc"
    raeume_ifc = wurzel / "raeume.ifc"
    for ziel, schalter in ((bau_ifc, []), (raeume_ifc, ["--raeume"])):
        if not ziel.exists():
            import subprocess
            subprocess.run([sys.executable, str(WURZEL / "tools" / "make_test_ifc.py"),
                            str(ziel), *schalter], check=True, capture_output=True)

    bau_glb = seams.ifc_zu_glb(str(bau_ifc), str(wurzel / "bau.glb"))
    raeume_glb = seams.ifc_zu_glb(str(raeume_ifc), str(wurzel / "raeume.glb"))
    for n, g in (("bau", bau_glb), ("raeume", raeume_glb)):
        if g.get("status") != "ok":
            raise SystemExit(f"IFC->glb {n}: {g.get('error')}")

    box = glbbox.bauwerksbox(bau_glb["glb_path"], up_axis=bau_glb["up_axis"])
    wahl = kameras.standpunkte(box["bbox_bauwerk"], anzahl=ANZAHL_AUSSEN,
                               bauwerk_bbox=box["bbox_bauwerk"],
                               gelaende_z=float(box["bbox_bauwerk"][0][2]))
    aussen = []
    for i, k in enumerate(wahl["standpunkte"], start=1):
        aussen.append((f"aussen_{i:02d}", k))

    innen = []
    raum_bericht = kette._raeume_lesen(str(raeume_ifc))
    for name, raum, art in INNEN:
        g = raumkamera.waehle(raum_bericht, raum=raum, art=art)
        if not g["gefunden"]:
            print(f"{name}: kein Standpunkt — {g.get('grund')}", flush=True)
            continue
        innen.append((name, g["standpunkt"]))

    stand = prompts.komponiere(prompts.MESS_STIL)
    aufstellung = {
        "aussen": [{"name": n, "kuerzel": k["kuerzel"],
                    "azimut_grad": k["azimut_grad"],
                    "auge": [float(v) for v in k["auge"]],
                    "blick_auf": [float(v) for v in k["blick_auf"]],
                    "brennweite_mm": k.get("brennweite_mm"),
                    "flaechenanteil": k.get("flaechenanteil")} for n, k in aussen],
        "innen": [{"name": n, "auge": [float(v) for v in s["auge"]],
                   "blick_auf": [float(v) for v in s["blick_auf"]],
                   "sichtfeld": s["sichtfeld"]} for n, s in innen],
        "bauwerksbox": box["bbox_bauwerk"], "szenenbox": box["bbox_szene"],
        "streuung_grad": wahl["streuung_grad"], "wahl_wert": wahl["wert"],
        "verworfen": [list(v) for v in wahl["verworfen"]],
        "warnungen": list(wahl["warnungen"]),
        "prompt_aussen": stand["prompt"],
        "negativ_aussen": stand["negativ_prompt"],
        "prompt_innen": PROMPT_INNEN,
        "stil_aussen": stand["stil"],
    }
    (wurzel / "aufstellung.json").write_text(
        json.dumps(aufstellung, indent=1, ensure_ascii=False), encoding="utf-8")

    print("Modelle laden …", flush=True)
    t0 = time.monotonic()
    render_modell = render.lade_modell(render.VORGABE_BACKBONE)
    tiefen_modell = tiefenschaetzer.lade_modell(tiefenschaetzer.VORGABE_TIEFENSCHAETZER)
    ladezeit = round(time.monotonic() - t0, 1)
    print(f"geladen in {ladezeit} s (weg: {getattr(render_modell, 'ladeweg', None)}, "
          f"geraet: {getattr(render_modell, 'geraet', None)})", flush=True)

    lizenz = backbone.pruefe_lizenz(render.VORGABE_BACKBONE)
    (wurzel / "backbone.json").write_text(
        json.dumps({"gewaehlt": render.VORGABE_BACKBONE,
                    "kommerziell_erste_wahl": backbone.waehle(kommerziell=True)[0].name,
                    "lizenz": lizenz, "ladezeit_s": ladezeit,
                    "ladeweg": getattr(render_modell, "ladeweg", None),
                    "geraet": str(getattr(render_modell, "geraet", None)),
                    "schaetzer": tiefenschaetzer.VORGABE_TIEFENSCHAETZER},
                   indent=1, ensure_ascii=False), encoding="utf-8")

    zeilen = []
    sammel = wurzel / "roh.json"
    if sammel.exists():
        zeilen = json.loads(sammel.read_text(encoding="utf-8"))
    fertig = {z["kamera"] for z in zeilen}

    auftraege = ([(n, bau_glb, k["auge"], k["blick_auf"], k.get("brennweite_mm"),
                   stand["prompt"], stand["negativ_prompt"]) for n, k in aussen]
                 + [(n, raeume_glb, s["auge"], s["blick_auf"], BRENNWEITE_INNEN_MM,
                     PROMPT_INNEN, "") for n, s in innen])

    for name, glb, auge, blick, brenn, prompt, negativ in auftraege:
        if nur and name not in nur:
            continue
        if name in fertig:
            print(f"{name}: liegt vor, uebersprungen", flush=True)
            continue
        print(f"{name} …", flush=True)
        z = fahre_kamera(name, glb, auge, blick, brenn, prompt, negativ, wurzel,
                         render_modell=render_modell, tiefen_modell=tiefen_modell,
                         stil_cn=stand.get("controlnet_staerke"))
        zeilen.append(z)
        (wurzel / name / "zahlen.json").write_text(
            json.dumps(zahlen_datei(z), indent=1, ensure_ascii=False), encoding="utf-8")
        sammel.write_text(json.dumps(zeilen, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        print(f"{name}: fertig, {z.get('zeiten_s')}", flush=True)

    print(f"geschrieben: {sammel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
