#!/usr/bin/env python3
"""Der Ausführende auf der HomeStation — holt Aufträge aus dem Repo, führt sie aus, legt Ergebnisse ab.

Gedacht für: Ubuntu 24.04, RTX 5090 (32 GB), Ryzen 9 9950X, Modelle unter ``/ai``.

Aufruf
------
    git pull
    python3 tools/homeworker.py --repo . --liste          # was liegt an?
    python3 tools/homeworker.py --repo . --alle           # alles Unerledigte abarbeiten
    python3 tools/homeworker.py --repo . --auftrag auf-20260818-01
    git add auftraege/ergebnisse && git commit && git push

Die Hardware-Schranke
---------------------
Die RTX 5090 löst unter ungebremster Volllast die Netzteil-Schutzschaltung aus. Dieses
Skript startet einen GPU-Auftrag darum **nur**, wenn die Karte frei ist — und im Zweifel
gar nicht (fail-closed). Lässt sich der Zustand nicht feststellen, wird abgelehnt, nicht
geraten: Ein übersprungener Auftrag kostet Wartezeit, ein abgestürzter Rechner mehr.

Die Leistungsgrenze setzt dieses Skript **nicht** selbst — dafür braucht es
Administratorrechte (``nvidia-smi -pl 400``). Es prüft aber, ob sie gesetzt ist, und
sagt, was zu tun wäre.

Regel 3
-------
Zurück ins Repo gehen **nur Zahlen**: Messwerte, Urteile, Laufzeiten, Dateinamen. Die
Bilder bleiben hier. `auftrag.baue_ergebnis` weist eingebettete Bilddaten ab.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag as auf  # noqa: E402


# ── GPU-Zustand ──────────────────────────────────────────────────────────────────────

def gpu_zustand() -> dict:
    """Leistungsaufnahme, belegter Speicher und Leistungsgrenze der Karte.

    ``verfuegbar=False`` heisst: Zustand unbekannt. Das ist ausdrücklich **kein** grünes
    Licht — der Aufrufer behandelt es als Ablehnungsgrund.
    """
    if not shutil.which("nvidia-smi"):
        return {"verfuegbar": False, "grund": "nvidia-smi nicht gefunden"}
    try:
        roh = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,power.draw,memory.used,memory.total,power.limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        return {"verfuegbar": False, "grund": f"nvidia-smi nicht ausführbar: {e}"}
    if roh.returncode != 0:
        return {"verfuegbar": False, "grund": f"nvidia-smi Code {roh.returncode}"}

    teile = [t.strip() for t in roh.stdout.strip().splitlines()[0].split(",")]
    try:
        return {
            "verfuegbar": True,
            "name": teile[0],
            "leistung_w": float(teile[1]),
            "speicher_belegt_gb": float(teile[2]) / 1024.0,
            "speicher_gesamt_gb": float(teile[3]) / 1024.0,
            "leistungsgrenze_w": float(teile[4]),
        }
    except (IndexError, ValueError) as e:
        return {"verfuegbar": False, "grund": f"nvidia-smi unverständlich: {e}"}


def darf_starten(zustand: dict, auflagen: dict) -> tuple[bool, str]:
    """Fail-closed: Nur bei nachweislich freier Karte grünes Licht."""
    if not auflagen.get("nur_bei_leerlauf", True):
        return True, "Leerlauf-Gate im Auftrag abgeschaltet"
    if not zustand.get("verfuegbar"):
        return False, f"GPU-Zustand unbekannt ({zustand.get('grund')}) — im Zweifel nicht starten"

    grenze_w = auflagen.get("leerlauf_schwelle_w", auf.GPU_LEERLAUF_W)
    grenze_gb = auflagen.get("leerlauf_schwelle_mem_gb", auf.GPU_LEERLAUF_MEM_GB)
    if zustand["leistung_w"] >= grenze_w:
        return False, f"GPU zieht {zustand['leistung_w']:.0f} W (≥ {grenze_w} W) — nicht frei"
    if zustand["speicher_belegt_gb"] >= grenze_gb:
        return False, (f"GPU hat {zustand['speicher_belegt_gb']:.1f} GB belegt "
                       f"(≥ {grenze_gb} GB) — fremdes Modell geladen")

    soll = auflagen.get("leistungsgrenze_w", auf.LEISTUNGSGRENZE_W)
    if zustand.get("leistungsgrenze_w", 0) > soll + 1:
        return False, (f"Leistungsgrenze steht bei {zustand['leistungsgrenze_w']:.0f} W, "
                       f"gefordert sind {soll} W. Setzen mit:  sudo nvidia-smi -pl {soll}")
    return True, "GPU frei, Leistungsgrenze in Ordnung"


# ── Ausführung ───────────────────────────────────────────────────────────────────────

def _geometrie_bereitstellen(satz: dict, repo: Path) -> str:
    """Die Geometrie besorgen — erzeugen oder auf den Pfad verweisen.

    Bei ``synthetisch`` wird sie hier erzeugt; es reist nichts über das Repo (Regel 3).
    """
    geom = satz["geometrie"]
    if geom.get("synthetisch"):
        ziel = repo / "build" / "testbau.ifc"
        subprocess.run([sys.executable, str(repo / "tools" / "make_test_ifc.py"), str(ziel)],
                       check=True, capture_output=True, text=True)
        return str(ziel)
    pfad = geom.get("pfad")
    if not Path(pfad).is_file():
        raise FileNotFoundError(f"Geometrie nicht gefunden: {pfad}")
    return pfad


def fuehre_aus(satz: dict, repo: Path, *, _render_modell=None, _tiefen_modell=None) -> dict:
    """Einen Auftrag ausführen und ein Ergebnis bauen.

    Für ``multipass`` und ``qa`` genügt Blender; ``render`` braucht zusätzlich das
    Bildmodell und den Tiefenschätzer.

    Args:
        _render_modell, _tiefen_modell: Nähte für Tests — fertige Modelle, die
            durchgereicht statt geladen werden. Dieselbe Bauform wie ``modell`` in
            ``render.rendere`` und ``_starte`` in ``seams``. Ohne sie wäre dieses Skript
            nur auf einem Rechner mit GPU und 20 GB Gewichten prüfbar, also faktisch gar
            nicht — und ausgerechnet der Teil, der unbeaufsichtigt läuft, bliebe ungeprüft.
    """
    from aiimaging import seams

    beginn = time.monotonic()
    art = satz["art"]
    params = satz.get("params") or {}

    ifc = _geometrie_bereitstellen(satz, repo)
    aus = Path(params.get("out_dir") or (repo / "build" / satz["auftrag_id"]))
    aus.mkdir(parents=True, exist_ok=True)

    glb_bericht = seams.ifc_zu_glb(ifc, str(aus / "modell.glb"))
    if glb_bericht.get("status") != "ok":
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler",
            fehler=f"IFC→glb: {glb_bericht.get('error')}",
            dauer_s=round(time.monotonic() - beginn, 1))

    blender_bericht = seams.glb_zu_tiefenkarte(
        glb_bericht["glb_path"], aus, up_axis=glb_bericht["up_axis"],
        aufloesung=params.get("aufloesung", 512), samples=params.get("samples", 32))

    if art == "render":
        return _render_und_qa(satz, blender_bericht, glb_bericht, aus, params, beginn,
                              _render_modell=_render_modell,
                              _tiefen_modell=_tiefen_modell)

    # Nur Zahlen und Dateinamen — nie Bildinhalte (Regel 3).
    return auf.baue_ergebnis(
        auftrag_id=satz["auftrag_id"], status="ok",
        messwerte={
            "n_elements": glb_bericht.get("n_elements"),
            "n_triangles": glb_bericht.get("n_triangles"),
            "bbox_size_m": blender_bericht.get("bbox_size_m"),
            "n_meshes": blender_bericht.get("n_meshes"),
            "dateien": [Path(p).name for p in aus.glob("*") if p.is_file()],
        },
        urteil={"multipass": "ok"},
        dauer_s=round(time.monotonic() - beginn, 1),
        umgebung=_umgebung())


def _render_und_qa(satz: dict, blender_bericht: dict, glb_bericht: dict,
                   aus: Path, params: dict, beginn: float, *,
                   _render_modell=None, _tiefen_modell=None) -> dict:
    """Die Stufe, für die es diesen Rechner gibt: Bildmodell, dann Messung.

    Bis zum 18.08.2026 meldete `art: "render"` hier `uebersprungen` — der Adapter in
    `aiimaging.render` war gebaut, aber **nie ausgeführt**, weil im Entwicklungscontainer
    weder GPU noch Gewichte liegen. Das ist die offene Fläche, die dieser Weg schliesst.

    Vier Dinge werden hier zum ersten Mal gleichzeitig geprüft, und sie sind bewusst
    **einzeln** berichtet, damit ein Bruch in der Mitte nicht die Erkenntnis der ersten
    Hälfte mitnimmt:

    1. Lädt und läuft der diffusers-Adapter mit echten Gewichten überhaupt?
    2. Genügt Depth-Anything-V2-**Small** (das einzige unter Regel 1 zulässige) auf einem
       Architekturbild — oder braucht die Metrik ein Modell, das wir nicht nehmen dürfen?
    3. Liefert die Geometrie-Metrik auf einem **erzeugten** Bild plausible Zahlen? Bisher
       ist sie nur an synthetischen Karten belegt (treu 0.99, halluziniert 0.24).
    4. Trägt die Schwelle 0.65 auf dieser Naht? Sie ist an wenigen Fällen gesetzt und auf
       einem echten Render noch nie gemessen worden.

    Regel 3: Zurück reisen nur Zahlen, Urteile und **Dateinamen**. Die Bilder bleiben auf
    der HomeStation.
    """
    from aiimaging import bildlesen, render, tiefenschaetzer

    messwerte = {
        "bbox_size_m": blender_bericht.get("bbox_size_m"),
        "n_meshes": blender_bericht.get("n_meshes"),
        "n_triangles": glb_bericht.get("n_triangles"),
        "depth_exr_kanaele": blender_bericht.get("depth_exr_kanaele"),
        "depth_exr_format": blender_bericht.get("depth_exr_format"),
        "depth_png_fehler": blender_bericht.get("depth_png_fehler"),
    }

    depth_png = blender_bericht.get("depth_png")
    if not depth_png:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            fehler=("Kein `depth_png` — ohne Tiefenkarte gibt es keine Konditionierung, "
                    "und ein Render ohne sie wäre genau die erfundene Kubatur, gegen die "
                    "dieses Projekt antritt. Grund siehe `depth_png_fehler`."),
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    # ── 1 · Der Render ────────────────────────────────────────────────────────────────
    a = render.RenderAuftrag(
        depth_png=depth_png,
        prompt=params.get("prompt", ""),
        negativ_prompt=params.get("negativ_prompt", ""),
        backbone=params.get("backbone", render.VORGABE_BACKBONE),
        seed=params.get("seed", 0),
        schritte=params.get("schritte", 20),
        controlnet_staerke=params.get("controlnet_staerke", 0.8),
        denoise=params.get("denoise", 0.6),
        # Der Beauty-Pass als Anker macht daraus echtes Image-Edit statt txt2img. Er ist
        # optional, weil genau das eine der Fragen ist, die gemessen werden sollen.
        beauty_png=(blender_bericht.get("beauty_png")
                    if params.get("mit_beauty", True) else None),
        ausgabe_png=str(aus / "render.png"),
        modell_wurzel=params.get("modell_wurzel"),
    )
    r = render.rendere(a, modell=_render_modell)
    # Nur Zahlen und Dateinamen (Regel 3) — `bild_png` wäre ein Pfad auf der HomeStation
    # und ist als Name genug.
    messwerte["render"] = {
        "status": r["status"], "seed": r.get("seed"), "backbone": r.get("backbone"),
        "dauer_s": r.get("dauer_s"), "parameter": r.get("parameter"),
        "lizenz": r.get("lizenz"), "maengel": r.get("maengel"),
        "hinweise": r.get("hinweise"),
        "bild": Path(r["bild_png"]).name if r.get("bild_png") else None,
    }
    if r["status"] != "ok":
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            urteil={"render": r["status"], "grund": r.get("error") or r.get("maengel")},
            fehler=f"Render {r['status']}: {r.get('error') or r.get('maengel')}",
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    # ── 2 · Die Messung ───────────────────────────────────────────────────────────────
    # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die Silhouette
    # exakt (siehe `bildlesen`, Modul-Docstring). Das PNG war die Eingabe des Modells,
    # die EXR ist der Massstab.
    try:
        soll, breite, hoehe = bildlesen.tiefen_aus_report(blender_bericht)
    except Exception as e:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            fehler=f"Soll-Tiefenkarte nicht lesbar: {type(e).__name__}: {e}",
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    qa = tiefenschaetzer.qa_gegen_soll(
        r["bild_png"], soll, breite=breite, hoehe=hoehe, modell=_tiefen_modell,
        schaetzer=params.get("schaetzer", tiefenschaetzer.VORGABE_TIEFENSCHAETZER),
        schwelle=params.get("schwelle", None) or geometrie_schwelle(),
    )
    messwerte["geometrie_qa"] = qa

    # `status` des Auftrags bildet ab, ob **gemessen** wurde — nicht, ob das Bild besteht.
    # Ein Render, der die Schwelle reisst, ist ein gelungener Auftrag mit einem klaren
    # Befund; ihn als Fehler zu melden würde die Auftragsliste unlesbar machen.
    return auf.baue_ergebnis(
        auftrag_id=satz["auftrag_id"],
        status="ok" if qa["status"] == "ok" else "fehler",
        messwerte=messwerte,
        urteil={
            "render": "ok",
            "gemessen": qa["status"] == "ok",
            "bestanden": qa.get("bestanden"),
            "score": qa.get("score"),
            "begruendung": qa.get("begruendung"),
        },
        fehler=qa.get("error"),
        dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())


def geometrie_schwelle() -> float:
    """Die Bestehensgrenze der Geometrie-QA — aus dem Kern, nicht hier nochmal getippt.

    Eine zweite Stelle mit derselben Zahl wäre genau die Art stiller Abweichung, die
    dieses Projekt zu vermeiden versucht: Wer die Schwelle in der Schwellenstudie
    (Phase 4) ändert, änderte sonst nur die eine Hälfte.
    """
    from aiimaging import geometrie_qa
    return geometrie_qa.SCHWELLE_GEOMETRIE


def _umgebung() -> dict:
    """Was den Messwert später einordnen lässt. Ohne das ist eine Zahl wertlos."""
    z = gpu_zustand()
    return {
        "gpu": z.get("name") if z.get("verfuegbar") else "keine",
        "leistungsgrenze_w": z.get("leistungsgrenze_w"),
        "python": sys.version.split()[0],
        "blender": shutil.which("blender") or "/opt/blender/blender",
    }


# ── Kommandozeile ────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Aufträge aus dem Repo auf der HomeStation ausführen.")
    ap.add_argument("--repo", default=".", help="Repo-Wurzel")
    ap.add_argument("--liste", action="store_true", help="nur zeigen, was unerledigt ist")
    ap.add_argument("--alle", action="store_true", help="alles Unerledigte abarbeiten")
    ap.add_argument("--auftrag", default=None, help="einen bestimmten Auftrag")
    ap.add_argument("--gpu", action="store_true", help="nur den GPU-Zustand zeigen")
    a = ap.parse_args(argv)
    repo = Path(a.repo).resolve()

    if a.gpu:
        print(json.dumps(gpu_zustand(), indent=2, ensure_ascii=False))
        return 0

    offen = auf.unerledigt(repo)
    if a.auftrag:
        offen = [s for s in offen if s["auftrag_id"] == a.auftrag]
        if not offen:
            print(f"Kein unerledigter Auftrag {a.auftrag!r}.")
            return 1

    if a.liste or not (a.alle or a.auftrag):
        if not offen:
            print("Nichts unerledigt.")
            return 0
        print(f"{len(offen)} unerledigt:")
        for s in offen:
            print(f"  {s['auftrag_id']}  [{s['art']}]  {s['beschreibung'][:70]}")
        return 0

    zustand = gpu_zustand()
    for satz in offen:
        frei, grund = darf_starten(zustand, satz.get("auflagen") or {})
        print(f"\n=== {satz['auftrag_id']} [{satz['art']}] — {grund}")
        if not frei and satz["art"] == "render":
            ergebnis = auf.baue_ergebnis(auftrag_id=satz["auftrag_id"], status="abgelehnt",
                                         fehler=grund, umgebung=_umgebung())
        else:
            try:
                ergebnis = fuehre_aus(satz, repo)
            except Exception as e:                       # noqa: BLE001
                ergebnis = auf.baue_ergebnis(auftrag_id=satz["auftrag_id"], status="fehler",
                                             fehler=f"{type(e).__name__}: {e}",
                                             umgebung=_umgebung())
        pfad = auf.schreibe_ergebnis(ergebnis, repo)
        print(f"    → {ergebnis['status']}  ({pfad.relative_to(repo)})")

    print("\nFertig. Jetzt:  git add auftraege/ergebnisse && git commit -m '...' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
