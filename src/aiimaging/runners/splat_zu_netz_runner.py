#!/usr/bin/env python3
"""RUNNER — Splat (3DGS-PLY) → farbiges Dreiecksnetz. Läuft im `.venv-splat`, nie im Produkt.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
Owner-Entscheid 79 (13.10.2026): Der Splat wird nicht mehr als harte Kugeln gezeichnet,
sondern **richtig gerendert** und zu einem Netz verschmolzen. Dafür braucht es gsplat
(Apache-2.0), Open3D (MIT) und PyTorch (BSD-3) — alle drei permissiv, aber schwer: torch zieht
auf Linux die CUDA-Laufzeit nach (siehe ``NOTICE``), gsplat rendert nur mit CUDA. Nichts davon
gehört in ein Produkt-venv, das laut ``pyproject.toml`` ohne Laufzeitabhängigkeit auskommt
(Regel 4). Dieselbe Grenze wie bei Blender und IfcOpenShell — hier nicht aus Lizenzgründen,
sondern wegen des Gewichts und der Grafikkarte.

**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden.**
`tests/test_prozessgrenze.py` und `tests/test_splat_zu_netz.py` wachen darüber.

Der Ablauf
----------
1. **Lesen:** Gaussians aus der PLY — Lage, Skala (log), Drehung (Quaternion ``wxyz``),
   Deckkraft (logit), Farbe als Kugelflächenfunktion (``f_dc``, ``f_rest`` bis Grad 3).
2. **Blickwinkel:** mit ``--aufnahme`` die Kameras der COLMAP-Aufnahme, wenn sie zum Splat
   passt (Gleichheitsprüfung, seit 13.10.2026); sonst ein Ring auf Augenhöhe nach aussen und
   ein Umlauf von aussen nach innen (:func:`aiimaging.kontext_netz.blickwinkel`).
3. **Rendern** mit ``gsplat.rasterization(..., render_mode="RGB+ED")``: Farbe und
   **erwartete Tiefe** je Bildpunkt. Wo die akkumulierte Deckkraft unter
   ``DECKKRAFT_LEER`` liegt, gilt der Punkt als leer.
3a. **Tiefe sieben** (seit 13.10.2026, nach ``auf-20261013-276``): akkumulierte Deckkraft,
   Sprenkel gegen den Median der Nachbarn, Streuung entlang des Strahls (zweiter Durchgang von
   gsplat), Nahbereich, Weg der Aufnahme, Masken der Aufnahme (:func:`_tiefe_filtern`, Zahlen
   in ``kontext_netz``, Abschnitt «Der Tiefenfilter»).
4. **Verschmelzen:** Open3D-TSDF (``VoxelBlockGrid``), ein Dreiecksnetz mit Eckpunktfarben.
   Über ``BLOECKE_MAX`` aktiven Blöcken wird mit grösserem Voxel neu verschmolzen.
5. **Aufräumen:** Netz in feste Reihenfolge bringen, kleine Inseln weg, bei Bedarf
   vereinfachen; die **Deckung** zählen.
6. **Schreiben:** PLY (binär, Eckpunktfarben) im **Koordinatensystem des Splats** — ohne
   Matrix; die Verortung wendet weiter Blender an. Dazu ein Bericht als JSON.

Die rechnerischen Teile stehen in ``aiimaging/kontext_netz.py`` (nur Standardbibliothek)
und werden **über den Dateipfad** geladen, nicht als Paket importiert — Begründung dort im
Modulkopf. Ein Paketimport zöge ``aiimaging/__init__.py`` und damit das Produkt in diese
Umgebung.

Der CPU-Ersatzrenderer (nur für Proben)
--------------------------------------
``--renderer cpu-probe`` ersetzt gsplat durch einen einfachen Punkt-Renderer: jeder
Gaussian mit Deckkraft ab ``DECKKRAFT_LEER`` ein Quadrat in der Grösse seiner projizierten
Achsen, Tiefe auf seiner Scheibe, SH-Grad 0. Seit 13.10.2026 (nach ``auf-20261013-276``)
mischt er wie gsplat von vorn nach hinten: akkumulierte Deckkraft und **erwartete** Tiefe
statt der nächsten Scheibe — sonst sähe die Probe die Wolke vor der Kamera nicht so, wie
gsplat sie liefert. **Er ist keine Alternative zu gsplat**, sondern die Naht,
an der sich Blickwinkel, TSDF, Inselentfernung und PLY-Ausgabe ohne Grafikkarte prüfen
lassen (13.10.2026: in der Cloud-Sitzung gibt es kein CUDA, gsplat rendert dort nicht).
Der Bericht trägt ``renderer: "cpu-probe"`` — ein solches Netz darf nie für ein echtes gelten.

Aufruf (immer über ``aiimaging.seams.splat_zu_netz``):
    .venv-splat/bin/python splat_zu_netz_runner.py <splat.ply> <netz.ply> [--report r.json]
        [--aufloesung 640] [--blickwinkel 16] [--voxel-m 0.05] [--oben 0,1,0]
        [--massstab 1.0] [--aufnahme=<sparse/0>] [--masken=<ordner>|keine]
        [--tiefenfilter=deckkraft,maske,nah,sprenkel|keine] [--renderer gsplat|cpu-probe]
        [--geraet cuda|cpu]

COLMAP wird mit der Standardbibliothek gelesen (``kontext_netz.lies_aufnahme``), nicht mit
pycolmap: Das PyPI-Rad von pycolmap bindet GPL-2.0+-Teile von SuiteSparse statisch ein
(Begründung in ``kontext_netz``, Abschnitt «Die Aufnahme lesen»).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

#: Wo die stdlib-Hälfte liegt — neben ``runners/``, im Paket. Ein Pfad, kein Import.
KONTEXT_NETZ_DATEI = Path(__file__).resolve().parents[1] / "kontext_netz.py"

#: Die Renderer. ``cpu-probe`` nur für Proben (siehe Modulkopf).
RENDERER = ("gsplat", "cpu-probe")

#: Wie viele Blickwinkel gsplat auf einmal rendert. Mehr spart Aufrufe, kostet Grafikspeicher.
GSPLAT_JE_DURCHGANG = 4

#: Die grösste Fussabdruck-Halbbreite des Ersatzrenderers, in Bildpunkten. Darüber hinaus
#: wird gekappt — die Probe soll Sekunden dauern, nicht Minuten.
PROBE_RADIUS_MAX_PX = 12

#: Wie viele dichte Punkte höchstens für Mitte, Boden und Halbmesser gelesen werden. Das
#: Deckungsmass zählt seit 13.10.2026 eine eigene, grössere Stichprobe über alle dichten
#: Punkte (``kontext_netz.DECKUNG_STICHPROBE``, ``auf-20261013-276`` Fehler 4).
STICHPROBE_BEREICH = 20000

#: Wie viele COLMAP-Punkte höchstens gegen den Splat geprüft werden. Der Median braucht nicht
#: alle; am echten Splat sind es Hunderttausende.
STICHPROBE_PUNKTE3D = 20000

#: Wie oft die TSDF mit grösserem Voxel neu versucht wird, wenn sie zu viele Blöcke hat.
VOXEL_VERSUCHE = 4


def _kontext_netz():
    """``kontext_netz.py`` über den Dateipfad laden — ohne ``aiimaging`` zu importieren."""
    spez = importlib.util.spec_from_file_location("visbox_kontext_netz", KONTEXT_NETZ_DATEI)
    if spez is None or spez.loader is None:
        raise RuntimeError(f"{KONTEXT_NETZ_DATEI.name} ist nicht ladbar.")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _drei(text: str) -> tuple[float, float, float]:
    teile = [t.strip() for t in str(text).split(",")]
    if len(teile) != 3:
        raise argparse.ArgumentTypeError(f"drei Zahlen 'x,y,z' erwartet, war {text!r}")
    return tuple(float(t) for t in teile)


# --------------------------------------------------------------------------------------
# 1 · Lesen
# --------------------------------------------------------------------------------------

def lies_splat(pfad: Path, kn) -> dict:
    """Die Gaussians als numpy-Felder. Nur binäre PLY — so schreiben sie alle Trainer."""
    import numpy as np

    kopf = kn.lies_ply_kopf(pfad)
    if kopf["format"] == "ascii":
        raise RuntimeError(f"{pfad.name!r} ist eine ASCII-PLY; gelesen werden binäre.")
    ecken = next((e for e in kopf["elemente"] if e["name"] == "vertex"), None)
    if ecken is None or ecken["anzahl"] == 0:
        raise RuntimeError(f"{pfad.name!r} hat keine Punkte.")
    if any(e["typ"] == "list" for e in ecken["eigenschaften"]):
        raise RuntimeError(f"{pfad.name!r}: Listen in den Punkten — das ist kein Splat.")
    if kn.ist_netz(kopf):
        raise RuntimeError(f"{pfad.name!r} ist schon ein Netz, kein Splat.")
    namen = [e["name"] for e in ecken["eigenschaften"]]
    noetig = ["x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2", "opacity",
              "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    fehlend = [n for n in noetig if n not in namen]
    if fehlend:
        raise RuntimeError(f"{pfad.name!r} ist kein 3DGS-Splat: Es fehlen {fehlend}.")
    ende = "<" if kopf["format"] == "binary_little_endian" else ">"
    dtype = np.dtype([(e["name"], ende + kn.PLY_TYPEN[e["typ"]][0])
                      for e in ecken["eigenschaften"]])
    daten = np.fromfile(pfad, dtype=dtype, count=ecken["anzahl"], offset=kopf["kopf_bytes"])
    if len(daten) != ecken["anzahl"]:
        raise RuntimeError(f"{pfad.name!r} ist kürzer als sein Kopf sagt "
                           f"({len(daten)} statt {ecken['anzahl']} Punkte).")
    spalte = lambda n: daten[n].astype(np.float64)      # noqa: E731
    grad = kn.sh_grad_aus_kopf(kopf)
    k_rest = (grad + 1) ** 2 - 1
    dc = np.stack([spalte(f"f_dc_{i}") for i in range(3)], axis=1)
    if k_rest:
        rest = np.stack([spalte(f"f_rest_{i}") for i in range(3 * k_rest)], axis=1)
        # Kanalweise gespeichert (erst alle R, dann G, dann B) — so schreiben es die Trainer.
        rest = rest.reshape(-1, 3, k_rest).transpose(0, 2, 1)
        sh = np.concatenate([dc[:, None, :], rest], axis=1)
    else:
        sh = dc[:, None, :]
    lage = np.stack([spalte(n) for n in ("x", "y", "z")], axis=1)
    skala = np.exp(np.stack([spalte(f"scale_{i}") for i in range(3)], axis=1))
    quat = np.stack([spalte(f"rot_{i}") for i in range(4)], axis=1)
    with np.errstate(over="ignore"):
        deckkraft = 1.0 / (1.0 + np.exp(-spalte("opacity")))
    laenge = np.linalg.norm(quat, axis=1)
    endlich = (np.isfinite(lage).all(1) & np.isfinite(skala).all(1) & np.isfinite(quat).all(1)
               & np.isfinite(sh).all((1, 2)) & np.isfinite(deckkraft) & (laenge > 1e-12))
    quat = quat / np.where(laenge > 1e-12, laenge, 1.0)[:, None]
    return {"n": int(ecken["anzahl"]), "endlich": endlich, "lage": lage, "skala": skala,
            "quat": quat, "deckkraft": deckkraft, "sh": sh, "sh_grad": grad}


# --------------------------------------------------------------------------------------
# 2 · Blickwinkel aus der Aufnahme — mit Gleichheitsprüfung (13.10.2026)
# --------------------------------------------------------------------------------------

def _aufnahme_pruefen(ordner: Path, g: dict, dicht, ki_breite: int, kn) -> dict:
    """Die Blickwinkel einer COLMAP-Aufnahme — oder ein Grund, warum sie nicht taugen.

    **Anlass** (``auf-20261013-275``): Ring und Umlauf sahen den echten Splat nicht dort, wo die
    Aufnahme ihn sah; das Netz deckte 21–26 % der Fläche, in Fetzen. Die Kameras der Aufnahme
    sehen jede Fläche, aus der die Gaussians gelernt wurden.

    **Erst prüfen, dann glauben.** Dass der Splat im System seiner COLMAP-Aufnahme liegt, ist
    bei Brush die Regel — aber ein umgerechneter oder zugeschnittener Splat liegt anders, und
    Kameras an der falschen Stelle sähen ins Leere. Geprüft werden die COLMAP-Punkte gegen die
    dichten Splat-Mitten und die Kamerazentren gegen den Bereich des Splats
    (:func:`aiimaging.kontext_netz.gleichheit_befund`).

    Returns:
        ``{taugt, ansichten, auswahl, gleichheit, grund}``.
    """
    import numpy as np
    import open3d as o3d

    aus = {"taugt": False, "ansichten": None, "auswahl": None, "gleichheit": None,
           "grund": None, "zentren": None}
    try:
        aufnahme = kn.lies_aufnahme(ordner)
        ansichten, auswahl = kn.aufnahme_blickwinkel(aufnahme, breite=ki_breite,
                                                     hoechstens=kn.AUFNAHME_BLICKE_MAX)
        punkte = np.array(kn.lies_punkte3d(ordner, STICHPROBE_PUNKTE3D), dtype=np.float64)
    except kn.KontextNetzError as fehler:
        aus["grund"] = f"Aufnahme nicht verwendbar: {fehler}"
        return aus
    aus["auswahl"] = auswahl
    lage_dicht = g["lage"][dicht]
    lo = np.percentile(lage_dicht, 100 * kn.ANTEIL_UNTEN, axis=0)
    hi = np.percentile(lage_dicht, 100 * kn.ANTEIL_OBEN, axis=0)
    diagonale = float(np.linalg.norm(hi - lo))
    median = p90 = None
    punkte = punkte[np.isfinite(punkte).all(1)] if len(punkte) else punkte
    if len(punkte):
        # Ein Suchbaum über ALLE dichten Mitten (am echten Splat Hunderttausende): Die
        # Standardbibliothek bräuchte dafür Minuten, Open3D braucht Sekundenbruchteile.
        suche = o3d.core.nns.NearestNeighborSearch(
            o3d.core.Tensor(np.ascontiguousarray(lage_dicht, dtype=np.float32)))
        suche.knn_index()
        _, d2 = suche.knn_search(o3d.core.Tensor(np.ascontiguousarray(punkte,
                                                                      dtype=np.float32)), 1)
        abstand = np.sqrt(np.maximum(d2.numpy().ravel().astype(np.float64), 0.0))
        median, p90 = float(np.median(abstand)), float(np.percentile(abstand, 90))
    # Alle Kamerazentren, nicht nur die gewählten: Die Frage ist, ob die AUFNAHME passt.
    zentren = [kn.kamerazentrum(b["q"], b["t"]) for b in aufnahme["bilder"].values()]
    elo, ehi = kn.huelle_erweitert(lo.tolist(), hi.tolist())
    befund = kn.gleichheit_befund(median=median, p90=p90, diagonale=diagonale,
                                  kameras_innen=kn.anteil_innen(zentren, elo, ehi),
                                  n_punkte=len(punkte), n_kameras=len(zentren))
    befund["median"] = None if median is None else round(median, 6)
    befund["p90"] = None if p90 is None else round(p90, 6)
    befund["diagonale"] = round(diagonale, 6)
    aus["gleichheit"] = befund
    if not befund["gleich"]:
        aus["grund"] = befund["grund"]
        return aus
    aus.update(taugt=True, ansichten=ansichten, zentren=zentren)
    return aus


# --------------------------------------------------------------------------------------
# 3 · Rendern — gsplat (echt) und der Ersatzrenderer (nur Proben)
# --------------------------------------------------------------------------------------

def _gsplat_ansichten(g: dict, ansichten, geraet: str, nah: float, fern: float, kn, *,
                      streuung_an: bool = True, streuung_fehler: list | None = None):
    """Je Blickwinkel ``(rgb uint8 HxWx3, tiefe float32 HxW, alpha float32 HxW, streuung)``.

    ``alpha`` ist die **akkumulierte Deckkraft** (``1 − Π(1 − αᵢ)`` entlang des Strahls), wie
    gsplat sie zurückgibt; die Tiefenfilter (:func:`_tiefe_filtern`) brauchen sie.

    ``streuung`` (float32 HxW oder ``None``): die Standardabweichung der Tiefe **entlang des
    Strahls**, gewichtet wie die erwartete Tiefe (13.10.2026, nach ``auf-20261013-276``). Ein
    zweiter Durchgang von gsplat mischt statt der Farbe zwei Merkmale je Kamera und Gaussian,
    ``z`` und ``z²`` (die Tiefe seiner Mitte in dieser Kamera — dieselbe, die gsplat für ED
    mischt): ``E[z²] − E[z]²``. **Nur am Heim-PC prüfbar** (CUDA); scheitert der Durchgang,
    bleibt ``streuung`` ``None``, der Filter setzt aus und der Bericht sagt es — die Brücke
    selbst bricht daran nicht ab.

    Jeder Blickwinkel trägt seine eigene Intrinsik (``ki``): Die Kameras einer Aufnahme dürfen
    verschieden sein. Gerendert wird je Durchgang nur, was dieselbe Bildgrösse hat.
    """
    import numpy as np
    import torch
    from gsplat import rasterization

    if geraet.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("gsplat rendert nur mit CUDA (NVIDIA-Grafikkarte); hier ist "
                           "keine erreichbar. Fuer Proben ohne Karte: --renderer cpu-probe.")
    dev = torch.device(geraet)
    streuung_fehler = [] if streuung_fehler is None else streuung_fehler
    w = g["endlich"]
    zu = lambda a: torch.from_numpy(np.ascontiguousarray(a[w])).float().to(dev)  # noqa: E731
    means, quats, scales = zu(g["lage"]), zu(g["quat"]), zu(g["skala"])
    opac, sh = zu(g["deckkraft"]), zu(g["sh"])
    start = 0
    while start < len(ansichten):
        groesse = (ansichten[start]["ki"]["breite"], ansichten[start]["ki"]["hoehe"])
        teil = [ansichten[start]]
        while (len(teil) < GSPLAT_JE_DURCHGANG and start + len(teil) < len(ansichten)
               and (ansichten[start + len(teil)]["ki"]["breite"],
                    ansichten[start + len(teil)]["ki"]["hoehe"]) == groesse):
            teil.append(ansichten[start + len(teil)])
        start += len(teil)
        b, h = groesse
        views = torch.tensor([a["ansicht"] for a in teil], dtype=torch.float32,
                             device=dev).reshape(-1, 4, 4)
        Ks = torch.tensor([a["ki"]["K"] for a in teil], dtype=torch.float32,
                          device=dev).reshape(-1, 3, 3)
        with torch.no_grad():
            bild, alpha, _ = rasterization(
                means, quats, scales, opac, sh, views, Ks, b, h,
                near_plane=nah, far_plane=fern, sh_degree=g["sh_grad"],
                render_mode="RGB+ED")
            momente = None
            if streuung_an and not streuung_fehler:
                try:
                    # z je Kamera und Gaussian: dritte Zeile der Ansicht mal Lage plus t_z.
                    z = torch.einsum("nk,ck->cn", means, views[:, 2, :3]) + views[:, 2, 3:4]
                    merkmale = torch.stack([z, z * z], dim=-1)          # [C, N, 2]
                    momente, _, _ = rasterization(
                        means, quats, scales, opac, merkmale, views, Ks, b, h,
                        near_plane=nah, far_plane=fern, sh_degree=None, render_mode="RGB")
                    momente = momente.cpu().numpy()
                except Exception as fehler:                 # noqa: BLE001 — Filter setzt aus
                    streuung_fehler.append(f"{type(fehler).__name__}: {fehler}"[:300])
                    momente = None
        bild, alpha = bild.cpu().numpy(), alpha[..., 0].cpu().numpy()
        for j in range(len(teil)):
            a = alpha[j].astype(np.float32)
            # Ohne Hintergrund ist die Farbe mit der Deckkraft vorgemischt; zurückteilen.
            rgb = np.clip(bild[j, ..., :3] / np.maximum(a, 1e-6)[..., None], 0.0, 1.0)
            tiefe = bild[j, ..., 3].astype(np.float32)
            tiefe[~np.isfinite(tiefe)] = 0.0
            streuung = None
            if momente is not None:
                geteilt = np.maximum(a, 1e-6)
                ez, ez2 = momente[j, ..., 0] / geteilt, momente[j, ..., 1] / geteilt
                streuung = np.sqrt(np.maximum(ez2 - ez * ez, 0.0)).astype(np.float32)
            yield (np.round(rgb * 255.0).astype(np.uint8), tiefe, a, streuung)


def _probe_ansichten(g: dict, ansichten, kn):
    """Der Ersatzrenderer: Punkte mit Tiefenpuffer. NUR FÜR PROBEN (Modulkopf).

    Je Blickwinkel ``(rgb, tiefe, alpha, streuung)`` wie :func:`_gsplat_ansichten`. **Die akkumulierte
    Deckkraft** (13.10.2026, nach ``auf-20261013-276``): Bis hierher gab der Ersatz nur Farbe
    und Tiefe; der Tiefenfilter braucht ``alpha``. Gerechnet wie bei gsplat als
    ``1 − Π(1 − oᵢ · gᵢ)`` über alle Gaussians, deren Scheibe der Strahl trifft — ``oᵢ`` die
    Deckkraft, ``gᵢ = exp(−½ d²/σ²)`` der Abfall in der Scheibe (``σ`` die längste Achse).
    Tiefe und Farbe werden wie bei gsplat von vorn nach hinten gemischt (Gewicht
    ``oᵢ gᵢ · Tᵢ``, ``Tᵢ`` der Durchlass davor) und durch die Summe der Gewichte geteilt: die
    **erwartete** Tiefe. Vereinfacht gegen gsplat: ein runder Abfall mit der längsten Achse
    statt der projizierten Ellipse, und nur innerhalb von 2σ.
    """
    import numpy as np

    w = g["endlich"] & (g["deckkraft"] >= kn.DECKKRAFT_LEER)
    lage = g["lage"][w]
    deckkraft = g["deckkraft"][w]
    farbe = np.clip(0.5 + 0.28209479177387814 * g["sh"][w][:, 0, :], 0.0, 1.0)
    farbe8 = np.round(farbe * 255.0).astype(np.uint8)
    # Die drei Achsen je Gaussian in der Welt: Drehung mal Skala. Die Drehung kommt aus der
    # stdlib-Hälfte, damit Probe und Produktseite dieselbe Formel benutzen.
    achsen = np.empty((len(lage), 3, 3))
    for i, (q, s) in enumerate(zip(g["quat"][w], g["skala"][w])):
        r = np.array(kn.quaternion_zu_matrix(*q))
        achsen[i] = (r * s[None, :]).T                   # Zeile k = Achse k
    # DIE TIEFE AUF DER EBENE DES GAUSSIANS (13.10.2026): Bis hierher trug jedes Quadrat die
    # Tiefe seiner Mitte, und der Tiefenpuffer nahm je Bildpunkt die nächste. Bei flachem Blick
    # auf den Boden hob das die Fläche zur Kamera hin an — das Netz lag 3 Voxel über dem Boden,
    # eine Wand von zwei Seiten gesehen doppelt (am synthetischen Splat gemessen; die TSDF
    # allein legt eine Ebene exakt). Jetzt schneidet jeder Bildpunkt seinen Sehstrahl mit der
    # Ebene des Gaussians (Normale = kürzeste Achse) — gsplat liefert ohnehin die erwartete
    # Tiefe, der Ersatz soll dem nahekommen, sonst misst die Deckung den Ersatz statt der Wege.
    laengen = np.linalg.norm(achsen, axis=2)
    kurz = np.argmin(laengen, axis=1)
    normale = achsen[np.arange(len(lage)), kurz] / np.maximum(
        laengen[np.arange(len(lage)), kurz], 1e-12)[:, None]
    for ansicht in ansichten:
        ki = ansicht["ki"]
        b, h, fx, fy, cx, cy = (ki[k] for k in ("breite", "hoehe", "fx", "fy", "cx", "cy"))
        v = np.array(ansicht["ansicht"]).reshape(4, 4)
        p = lage @ v[:3, :3].T + v[:3, 3]
        z = p[:, 2]
        vorn = z > 1e-3
        u = np.floor(fx * p[vorn, 0] / z[vorn] + cx).astype(np.int64)
        vv = np.floor(fy * p[vorn, 1] / z[vorn] + cy).astype(np.int64)
        zz = z[vorn]
        n_cam = normale[vorn] @ v[:3, :3].T
        mitte = p[vorn]
        nc = np.einsum("ij,ij->i", n_cam, mitte)          # n · Mitte, je Gaussian
        reichweite = 2.0 * laengen[vorn].max(axis=1)      # 2σ der längsten Achse
        a_cam = achsen[vorn] @ v[:3, :3].T               # Achsen in Kamerakoordinaten
        quer = np.sqrt(a_cam[..., 0] ** 2 + a_cam[..., 1] ** 2).max(axis=1)
        radius = np.minimum(np.ceil(2.0 * quer * fx / zz), PROBE_RADIUS_MAX_PX).astype(np.int64)
        reihe = np.argsort(radius, kind="stable")
        u, vv, zz, radius, c = u[reihe], vv[reihe], zz[reihe], radius[reihe], farbe8[vorn][reihe]
        n_cam, nc, mitte, reichweite = n_cam[reihe], nc[reihe], mitte[reihe], reichweite[reihe]
        o_v = deckkraft[vorn][reihe]
        idx_l, z_l, c_l, log_l = [], [], [], []
        for dy in range(-PROBE_RADIUS_MAX_PX, PROBE_RADIUS_MAX_PX + 1):
            for dx in range(-PROBE_RADIUS_MAX_PX, PROBE_RADIUS_MAX_PX + 1):
                ab = int(np.searchsorted(radius, max(abs(dx), abs(dy))))
                if ab >= len(radius):
                    continue
                uu, vy = u[ab:] + dx, vv[ab:] + dy
                ok = (uu >= 0) & (uu < b) & (vy >= 0) & (vy < h)
                strahl_x = (uu[ok] + 0.5 - cx) / fx
                strahl_y = (vy[ok] + 0.5 - cy) / fy
                n = n_cam[ab:][ok]
                nd = n[:, 0] * strahl_x + n[:, 1] * strahl_y + n[:, 2]
                with np.errstate(divide="ignore", invalid="ignore"):
                    zt = nc[ab:][ok] / nd
                # Nur wo der Strahl die Ebene INNERHALB des Gaussians trifft (2σ): Bei
                # streifendem Blick trifft er sie sonst weit hinter dem Gaussian, und das Netz
                # wüchse über den Splat hinaus.
                m = mitte[ab:][ok]
                abw2 = ((zt * strahl_x - m[:, 0]) ** 2 + (zt * strahl_y - m[:, 1]) ** 2
                        + (zt - m[:, 2]) ** 2)
                gut = np.isfinite(zt) & (zt > 0) & (abw2 <= reichweite[ab:][ok] ** 2)
                idx_l.append((vy[ok] * b + uu[ok])[gut])
                z_l.append(zt[gut])
                c_l.append(c[ab:][ok][gut])
                sigma2 = (0.5 * reichweite[ab:][ok][gut]) ** 2
                beitrag = o_v[ab:][ok][gut] * np.exp(-0.5 * abw2[gut] / np.maximum(sigma2,
                                                                                   1e-24))
                log_l.append(np.log1p(-np.minimum(beitrag, 0.999999)))
        tiefe = np.zeros(b * h, dtype=np.float32)
        rgb = np.zeros((b * h, 3), dtype=np.uint8)
        alpha = np.zeros(b * h, dtype=np.float32)
        streuung = np.zeros(b * h, dtype=np.float32)
        if idx_l:
            idx, zs, cs = np.concatenate(idx_l), np.concatenate(z_l), np.concatenate(c_l)
            la = np.concatenate(log_l)
            folge = np.lexsort((zs, idx))                # je Bildpunkt von vorn nach hinten
            idx, zs, cs, la = idx[folge], zs[folge], cs[folge], la[folge]
            alpha = (1.0 - np.exp(np.bincount(idx, weights=la, minlength=b * h))
                     ).astype(np.float32)
            # ERWARTETE TIEFE WIE GSPLAT (13.10.2026, nach auf-20261013-276): Bis hierher
            # nahm der Ersatz je Bildpunkt die NAECHSTE Scheibe. gsplat mischt von vorn nach
            # hinten, Gewicht w = a · T (T = Durchlass davor), und teilt durch die Summe der
            # Gewichte. Erst so steht eine halb durchsichtige Wolke vor einer Wand dort, wo
            # 276 sie sah: als Tiefe irgendwo dazwischen, in der Luft — mit dem naechsten
            # Treffer laege sie sauber auf der Wolke, und die Probe saehe den Fehler nicht.
            erste, gruppe = np.unique(idx, return_index=True, return_inverse=True)[1:]
            summe = np.cumsum(la)
            davor = (summe - la) - (summe[erste] - la[erste])[gruppe]
            gewicht = (1.0 - np.exp(la)) * np.exp(davor)
            w_sum = np.bincount(idx, weights=gewicht, minlength=b * h)
            belegt = w_sum > 1e-12
            tiefe64 = np.zeros(b * h)
            tiefe64[belegt] = (np.bincount(idx, weights=gewicht * zs, minlength=b * h)[belegt]
                               / w_sum[belegt])
            tiefe[belegt] = tiefe64[belegt]
            farbe_w = np.stack([np.bincount(idx, weights=gewicht * cs[:, k], minlength=b * h)
                                for k in range(3)], axis=1)
            rgb[belegt] = np.clip(np.round(farbe_w[belegt] / w_sum[belegt, None]), 0,
                                  255).astype(np.uint8)
            # Die Streuung entlang des Strahls, mit denselben Gewichten (wie gsplat, dort im
            # zweiten Durchgang): E[z²] − E[z]².
            ez2 = (np.bincount(idx, weights=gewicht * zs * zs, minlength=b * h)[belegt]
                   / w_sum[belegt])
            streuung[belegt] = np.sqrt(np.maximum(ez2 - tiefe64[belegt] ** 2, 0.0))
        yield (rgb.reshape(h, b, 3), tiefe.reshape(h, b), alpha.reshape(h, b),
               streuung.reshape(h, b))


# --------------------------------------------------------------------------------------
# 3a · Tiefe sieben — Deckkraft, Sprenkel, Nahbereich, Masken (13.10.2026, nach 276)
# --------------------------------------------------------------------------------------

def _median_3x3(tiefe):
    """Der Median der 3 × 3 Nachbarn je Bildpunkt (Rand: die Nachbarn ausserhalb zählen 0).

    ``np.partition`` statt ``np.median``: Gebraucht wird nur das fünfte von neun, und das
    halbiert die Zeit (240 Bilder à 640 × 640 je Lauf).
    """
    import numpy as np

    h, b = tiefe.shape
    rand = np.pad(tiefe, 1)
    stapel = np.stack([rand[dy:dy + h, dx:dx + b] for dy in range(3) for dx in range(3)])
    return np.partition(stapel, 4, axis=0)[4]


def _weg_naehe(tiefe, kandidat, ansicht, zentren, weg_min: float):
    """Welche Bildpunkte (unter ``kandidat``) näher als ``weg_min`` an einer der ``zentren``
    liegen — als Punkte der Welt aus Tiefe, Intrinsik und Ansicht zurückgerechnet."""
    import numpy as np

    aus = np.zeros(tiefe.shape, dtype=bool)
    if zentren is None or not len(zentren) or not kandidat.any():
        return aus
    ki = ansicht["ki"]
    v = np.array(ansicht["ansicht"], dtype=np.float64).reshape(4, 4)
    r, t = v[:3, :3], v[:3, 3]
    zeile, spalte = np.nonzero(kandidat)
    z = tiefe[zeile, spalte].astype(np.float64)
    kamera = np.stack([(spalte + 0.5 - ki["cx"]) / ki["fx"] * z,
                       (zeile + 0.5 - ki["cy"]) / ki["fy"] * z, z], axis=1)
    welt = (kamera - t) @ r                               # Rᵀ (p − t), zeilenweise
    nah = np.zeros(len(welt), dtype=bool)
    for k in range(0, len(zentren), 32):                  # in Stücken: Speicher begrenzt
        d2 = ((welt[:, None, :] - zentren[None, k:k + 32, :]) ** 2).sum(axis=2)
        nah |= (d2 < weg_min * weg_min).any(axis=1)
    aus[zeile[nah], spalte[nah]] = True
    return aus


def _tiefe_filtern(tiefe, alpha, *, filter_: set, nah: float, behalten, kn,
                   ansicht=None, zentren=None, weg_min: float = 0.0,
                   weg_reichweite: float = 0.0, streuung=None):
    """Die Tiefe eines Blickwinkels sieben; verworfene Bildpunkte tragen danach Tiefe 0.

    **Anlass** (``auf-20261013-276``): gesprenkelte erwartete Tiefe und die gefilmte Person
    als Wolke nah vor der Kamera; die TSDF machte daraus 497 497 Stücke (Begründung und
    Schwellen in ``kontext_netz``, Abschnitt «Der Tiefenfilter»). Jeder Filter wird **für
    sich** gezählt — ein Bildpunkt, den zwei verwerfen, zählt bei beiden —, damit der Bericht
    sagt, welcher wie viel trägt; ``verworfen`` zählt jeden Bildpunkt einmal.

    Args:
        filter_: die eingeschalteten Filter (``kontext_netz.TIEFENFILTER``).
        nah: Mindesttiefe in Einheiten des Splats (``kontext_netz.nah_min_splat``).
        behalten: bool HxW aus der Maske (True = behalten) oder ``None``.
        ansicht, zentren, weg_min, weg_reichweite: für den Filter ``weg`` — die Kamerazentren
            der Aufnahme (Nx3, Splat-Einheiten) und die Abstände in Splat-Einheiten.
        streuung: Standardabweichung der Tiefe entlang des Strahls (HxW) oder ``None`` — dann
            setzt der Filter ``streuung`` aus.

    Returns:
        ``(tiefe, zaehler)`` — ``zaehler`` mit ``mit_tiefe`` (Bildpunkte, die vorher Tiefe
        trugen), je Filter die Zahl der verworfenen und ``verworfen`` gesamt.
    """
    import numpy as np

    basis = (tiefe > 0) & np.isfinite(tiefe)
    leer = np.zeros_like(basis)
    weg = {}
    weg["deckkraft"] = (basis & (alpha < kn.DECKKRAFT_TIEFE)
                        if "deckkraft" in filter_ else leer)
    if "sprenkel" in filter_:
        roh = np.where(basis, tiefe, 0.0).astype(np.float32)
        weg["sprenkel"] = basis & (np.abs(roh - _median_3x3(roh))
                                   > kn.TIEFE_SPRUNG_REL * roh)
    else:
        weg["sprenkel"] = leer
    weg["streuung"] = (basis & (streuung > kn.TIEFE_STREUUNG_REL * tiefe)
                       if ("streuung" in filter_ and streuung is not None) else leer)
    weg["nah"] = basis & (tiefe < nah) if "nah" in filter_ else leer
    if "weg" in filter_ and zentren is not None and ansicht is not None:
        # Nur Zentren in Reichweite der rendernden Kamera, nur Bildpunkte, die eines davon
        # erreichen können (Tiefe ≤ Reichweite + weg_min): Das hält die Rechnung klein.
        v = np.array(ansicht["ansicht"], dtype=np.float64).reshape(4, 4)
        hier = -v[:3, :3].T @ v[:3, 3]
        nahe = zentren[((zentren - hier) ** 2).sum(axis=1) < weg_reichweite ** 2]
        weg["weg"] = _weg_naehe(tiefe, basis & (tiefe < weg_reichweite + weg_min), ansicht,
                                nahe, weg_min)
    else:
        weg["weg"] = leer
    weg["maske"] = (basis & ~behalten if ("maske" in filter_ and behalten is not None)
                    else leer)
    alle = (weg["deckkraft"] | weg["sprenkel"] | weg["streuung"] | weg["nah"] | weg["weg"]
            | weg["maske"])
    aus = np.where(basis & ~alle, tiefe, 0.0).astype(np.float32)
    zaehler = {"mit_tiefe": int(basis.sum()), "verworfen": int(alle.sum())}
    zaehler.update({k: int(v.sum()) for k, v in weg.items()})
    return aus, zaehler


def _maske_lesen(pfad: Path, breite: int, hoehe: int):
    """Eine Maske als Grauwert 0..255 (uint8), auf ``breite × hoehe`` gebracht — oder ``None``.

    Gelesen mit Open3D (``o3d.io.read_image``, PNG/JPG), **keine neue Abhängigkeit**.
    Graustufen direkt; RGB als Mittel der Kanäle; RGBA mit nicht einheitlichem Alpha über
    den Alphakanal. Skaliert wird nach dem nächsten Nachbarn: Eine Maske hat Kanten, keine
    Zwischentöne, und eine Mittelung erfände sie.
    """
    import numpy as np
    import open3d as o3d

    bild = np.asarray(o3d.io.read_image(str(pfad)))
    if bild.size == 0:
        return None
    if bild.dtype != np.uint8:                           # 16 Bit: auf 0..255
        bild = (bild.astype(np.float64) / max(1.0, float(np.iinfo(bild.dtype).max))
                * 255.0).round().astype(np.uint8)
    if bild.ndim == 3:
        if bild.shape[2] == 4 and bild[..., 3].min() != bild[..., 3].max():
            bild = bild[..., 3]
        else:
            bild = bild[..., :3].mean(axis=2).round().astype(np.uint8)
    h0, b0 = bild.shape
    zeilen = np.minimum(((np.arange(hoehe) + 0.5) * h0 / hoehe).astype(np.int64), h0 - 1)
    spalten = np.minimum(((np.arange(breite) + 0.5) * b0 / breite).astype(np.int64), b0 - 1)
    return bild[zeilen][:, spalten]


def _masken_vorbereiten(ansichten, masken_ordner, aufnahme: Path | None, kn) -> dict:
    """Die Masken der gewählten Blickwinkel laden und die Polarität bestimmen.

    Returns:
        ``{je_bild: {bildnummer: bool HxW (True = behalten)}, bericht}`` — ``bericht`` ohne
        Pfad: gefunden, Zahl gefunden/benutzt, Lage, Polarität und ihre Quelle.
    """
    import numpy as np

    bericht = {"gefunden": False, "anzahl": 0, "benutzt": 0, "lage": None,
               "polaritaet": None, "polaritaet_quelle": None, "weiss_anteil": None,
               "warnung": None, "unlesbar": 0}
    if aufnahme is None or masken_ordner == "keine":
        bericht["grund"] = "keine Aufnahme" if aufnahme is None else "keine Masken"
        return {"je_bild": {}, "bericht": bericht}
    namen = [a["name"] for a in ansichten if a.get("name")]
    fund = kn.finde_masken(aufnahme, namen,
                           None if masken_ordner in (None, "auto") else Path(masken_ordner))
    bericht.update(gefunden=fund["gefunden"], anzahl=len(fund["dateien"]), lage=fund["art"])
    if not fund["gefunden"]:
        return {"je_bild": {}, "bericht": bericht}
    grau = {}
    for a in ansichten:
        pfad = fund["dateien"].get(a.get("name"))
        if pfad is None:
            continue
        m = _maske_lesen(pfad, a["ki"]["breite"], a["ki"]["hoehe"])
        if m is None:
            bericht["unlesbar"] += 1
            continue
        grau[a["bild"]] = m >= kn.MASKE_SCHWELLE           # True = weiss
    if not grau:
        bericht["gefunden"] = False
        return {"je_bild": {}, "bericht": bericht}
    weiss = float(np.mean([m.mean() for m in grau.values()]))
    aus_json = None
    if fund["json"] is not None:
        try:
            aus_json = kn.polaritaet_aus_json(json.loads(fund["json"].read_text(
                encoding="utf-8")))
        except (OSError, ValueError):
            bericht["warnung"] = "maske.json nicht lesbar"
    pol = kn.masken_polaritaet(weiss, aus_json)
    bericht.update(benutzt=len(grau),
                   polaritaet="weiss = behalten" if pol["weiss_behalten"] else
                   "schwarz = behalten",
                   polaritaet_quelle=pol["quelle"], weiss_anteil=pol["weiss_anteil"],
                   warnung=pol["warnung"] or bericht["warnung"])
    je_bild = {nr: (m if pol["weiss_behalten"] else ~m) for nr, m in grau.items()}
    return {"je_bild": je_bild, "bericht": bericht}


def _gesiebt(bilder, ansichten, *, filter_: set, nah: float, masken: dict, summe: dict, kn,
             zentren=None, weg_min: float = 0.0, weg_reichweite: float = 0.0):
    """Die Bilder eines Renderers durch :func:`_tiefe_filtern` — je Blickwinkel
    ``(rgb, tiefe, gefuellt-Anteil)`` für die TSDF; die Zähler wandern in ``summe``."""
    import numpy as np

    for ansicht, (rgb, tiefe, alpha, streuung) in zip(ansichten, bilder):
        leer = alpha < kn.DECKKRAFT_LEER
        tiefe = np.where(leer, 0.0, tiefe).astype(np.float32)
        tiefe, zaehler = _tiefe_filtern(tiefe, alpha, filter_=filter_, nah=nah,
                                        behalten=masken.get(ansicht.get("bild")), kn=kn,
                                        ansicht=ansicht, zentren=zentren, weg_min=weg_min,
                                        weg_reichweite=weg_reichweite, streuung=streuung)
        if streuung is not None:
            summe["streuung_bilder"] = summe.get("streuung_bilder", 0) + 1
        for k, v in zaehler.items():
            summe[k] = summe.get(k, 0) + v
        summe["bildpunkte"] = summe.get("bildpunkte", 0) + int(tiefe.size)
        yield rgb, tiefe, float((~leer).mean())


def _filter_bericht(summe: dict, filter_: set, nah: float, kn, *, weg_aktiv: bool,
                    massstab: float, streuung_fehler=()) -> dict:
    """Die Zähler als Anteile — je Filter: welcher Anteil der Bildpunkte mit Tiefe verworfen."""
    n = max(1, summe.get("mit_tiefe", 0))
    return {"eingeschaltet": sorted(filter_),
            "bildpunkte_mit_tiefe": int(summe.get("mit_tiefe", 0)),
            "verworfen_anteil": round(summe.get("verworfen", 0) / n, 4),
            "je_filter": {k: round(summe.get(k, 0) / n, 4) for k in kn.TIEFENFILTER},
            "schwellen": {"deckkraft_tiefe": kn.DECKKRAFT_TIEFE,
                          "tiefe_sprung_rel": kn.TIEFE_SPRUNG_REL,
                          "tiefe_streuung_rel": kn.TIEFE_STREUUNG_REL,
                          "nah_min_m": kn.NAH_MIN_M,
                          "nah_min_splat_einheiten": round(float(nah), 6),
                          "weg_min_m": kn.WEG_MIN_M,
                          "weg_min_splat_einheiten": round(kn.WEG_MIN_M / massstab, 6),
                          "weg_reichweite_m": kn.WEG_REICHWEITE_M,
                          "maske_schwelle": kn.MASKE_SCHWELLE},
            # «weg» braucht die Kameras der Aufnahme; mit dem Ring wirkt er nicht.
            "weg_aktiv": bool(weg_aktiv),
            # «streuung» braucht den zweiten Durchgang von gsplat; scheitert er, setzt der
            # Filter aus, und hier steht warum.
            "streuung_bilder": int(summe.get("streuung_bilder", 0)),
            "streuung_fehler": (list(streuung_fehler)[:1] or None)}


# --------------------------------------------------------------------------------------
# 4 · Verschmelzen — mit Blockwache
# --------------------------------------------------------------------------------------

#: Was ein Lauf bis zu einem Abbruch weiss — fuer den Fehlerbericht (siehe `main`).
_ZWISCHENSTAND: dict = {}


class _ZuVieleBloecke(Exception):
    """Die TSDF hat mehr aktive Blöcke als ``BLOECKE_MAX`` — mit diesem Voxel nicht weiter."""

    def __init__(self, bloecke: int):
        super().__init__(bloecke)
        self.bloecke = bloecke


def _verschmelzen(bilder, ansichten, *, voxel: float, tiefe_max: float, spanne: float,
                  bloecke_max: int, kn):
    """Die Tiefenbilder in eine TSDF integrieren; bricht ab, sobald zu viele Blöcke aktiv sind.

    **Die Blockwache** (13.10.2026, nach ``auf-20261013-275``): Open3D 0.20 stürzt in
    ``extract_triangle_mesh`` ab, wenn zu viele Blöcke aktiv sind — ohne Bericht, als
    SIGSEGV. Mit den Blickwinkeln der Aufnahme sieht die Brücke mehr Fläche als mit dem Ring,
    die Blockzahl steigt. Darum wird nach jedem Bild gezählt; über ``BLOECKE_MAX`` bricht der
    Lauf ab, und der Aufrufer versucht es mit grösserem Voxel (:func:`voxel_fuer_bloecke`).
    """
    import numpy as np
    import open3d as o3d

    # VOXELBLOCKGRID STATT ScalableTSDFVolume (13.10.2026, an Open3D 0.20 gemessen): Die
    # alte Klasse gab fuer eine frontal gesehene Ebene NULL Dreiecke zurueck — integriert
    # wurde, herausgezogen nichts. Die neue Klasse integriert gleich und zieht mit einer
    # ausdruecklichen Gewichtsschwelle heraus (ihre Vorgabe 3,0 verlangte drei Blicke je
    # Voxel und lieferte an derselben Ebene ebenfalls nichts).
    o3c = o3d.core
    cpu = o3c.Device("CPU:0")
    bloecke = int(min(400_000, max(20_000, 4.0 * (2.0 * spanne / (8.0 * voxel)) ** 2)))
    volumen = o3d.t.geometry.VoxelBlockGrid(
        attr_names=("tsdf", "weight", "color"),
        attr_dtypes=(o3c.float32, o3c.float32, o3c.float32),
        attr_channels=((1), (1), (3)), voxel_size=float(voxel), block_resolution=8,
        block_count=bloecke, device=cpu)
    gefuellt: list[float] = []
    uebersprungen = {"leer": 0, "gescheitert": 0}
    t_render = t_tsdf = 0.0
    t0 = time.monotonic()
    for ansicht, (rgb, tiefe, anteil) in zip(ansichten, bilder):
        t1 = time.monotonic()
        t_render += t1 - t0
        # DER FUELLANTEIL NACH DEM SIEBEN (auf-20261013-277 Fehler 2): `anteil` wurde vor den
        # Tiefenfiltern gemessen; ein danach leeres Bild liess Open3D abbrechen. Gezaehlt
        # wird, was wirklich Tiefe traegt — leere und gescheiterte Bilder werden uebersprungen.
        tiefe_np = np.asarray(tiefe)
        rest = float(np.count_nonzero(tiefe_np > 0.0)) / max(1, tiefe_np.size)
        gefuellt.append(rest)
        if rest <= 0.0:
            uebersprungen["leer"] += 1
        else:
            kamera = o3c.Tensor(np.array(ansicht["ki"]["K"], dtype=np.float64).reshape(3, 3))
            tiefe_bild = o3d.t.geometry.Image(o3c.Tensor(np.ascontiguousarray(
                tiefe, dtype=np.float32)))
            farb_bild = o3d.t.geometry.Image(o3c.Tensor(np.ascontiguousarray(
                rgb, dtype=np.float32) / 255.0))
            aussen = o3c.Tensor(np.array(ansicht["ansicht"], dtype=np.float64).reshape(4, 4))
            try:
                bl = volumen.compute_unique_block_coordinates(
                    tiefe_bild, kamera, aussen, 1.0, float(tiefe_max),
                    trunc_voxel_multiplier=kn.SDF_TRUNC_VOXEL)
                volumen.integrate(bl, tiefe_bild, farb_bild, kamera, kamera, aussen, 1.0,
                                  float(tiefe_max), trunc_voxel_multiplier=kn.SDF_TRUNC_VOXEL)
            except RuntimeError:
                # «No block is touched»: wenige Resttiefen jenseits der Reichweite. Ein Bild,
                # das nichts beitraegt, darf den Lauf nicht kosten (277: 17 solche Bilder).
                uebersprungen["gescheitert"] += 1
            else:
                aktiv = int(volumen.hashmap().size())
                if aktiv > bloecke_max:
                    raise _ZuVieleBloecke(aktiv)
        t0 = time.monotonic()
        t_tsdf += t0 - t1
    if not volumen.hashmap().size():
        raise RuntimeError(f"Kein Bild hat Tiefe beigetragen ({uebersprungen['leer']} leer, "
                           f"{uebersprungen['gescheitert']} gescheitert von {len(gefuellt)}) — "
                           f"Tiefenfilter zu streng?")
    return volumen, (gefuellt, uebersprungen), t_render, t_tsdf, int(volumen.hashmap().size())


# --------------------------------------------------------------------------------------
# Der ganze Lauf
# --------------------------------------------------------------------------------------

def _versionen() -> dict:
    aus = {"python": platform.python_version()}
    for name in ("numpy", "torch", "gsplat", "open3d"):
        try:
            aus[name] = __import__(name).__version__
        except Exception:                                  # noqa: BLE001 — Bericht, kein Abbruch
            aus[name] = None
    return aus


def _deckung(netz, punkte, abstand: float, *, dicht_gesamt: int) -> dict:
    """Welcher Anteil der dichten Splat-Punkte höchstens ``abstand`` von einer Netzfläche liegt.

    **Das Mass für die Löcher** (13.10.2026): ``auf-20261013-275`` sah die Löcher nur im Bild
    (21–26 % der Fläche neben dem Bauwerk). Hier wird es am Netz selbst gezählt, ohne Kamera —
    damit Ring und Aufnahme vergleichbar sind und die HomeStation es am echten Splat misst.
    ``punkte`` ist seit ``auf-20261013-276`` (Fehler 4) eine gleichmässige Zufallsstichprobe
    über **alle** dichten Punkte (``kontext_netz.stichprobe_indizes``); ``dicht_gesamt`` sagt,
    aus wie vielen.
    """
    import numpy as np
    import open3d as o3d

    szene = o3d.t.geometry.RaycastingScene()
    szene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(netz))
    d = szene.compute_distance(o3d.core.Tensor(np.ascontiguousarray(punkte,
                                                                    dtype=np.float32))).numpy()
    return {"anteil": round(float((d <= abstand).mean()), 4),
            "abstand_median": round(float(np.median(d)), 6),
            "abstand_splat_einheiten": round(float(abstand), 6), "punkte": int(len(punkte)),
            "dicht_gesamt": int(dicht_gesamt), "stichprobe": "zufall, fester startwert"}


def _netz_ordnen(netz):
    """Ecken und Dreiecke in eine feste Reihenfolge bringen — das Netz wird reproduzierbar.

    **Anlass** (``auf-20261013-276``, Fehler 3): Bei gleichem Schlüssel war die Netz-sha256
    zweier Läufe verschieden, Deckung, Stücke und Blockzahl gleich. Hier nachgestellt (CPU,
    Ersatzrenderer, drei Läufe, 13.10.2026): drei verschiedene sha256, aber nach Lage
    sortiert **dieselben Ecken**. Die Ursache ist nicht gsplat, sondern Open3D: Die Hashtabelle
    der ``VoxelBlockGrid`` füllt sich parallel, und in ihrer Reihenfolge kommen die Dreiecke
    heraus. Die Geometrie ist dieselbe, die Datei nicht — und die Vereinfachung
    (``simplify_quadric_decimation``) hängt an der Reihenfolge, also wird **vor** ihr geordnet.

    Ecken nach Lage (dann Farbe), jedes Dreieck mit der kleinsten Ecke vorn (Umlaufsinn
    bleibt), die Dreiecke danach sortiert.
    """
    import numpy as np
    import open3d as o3d

    ecken = np.asarray(netz.vertices)
    farben = np.asarray(netz.vertex_colors) if netz.has_vertex_colors() else None
    dreiecke = np.asarray(netz.triangles)
    schluessel = [ecken[:, 2], ecken[:, 1], ecken[:, 0]]
    if farben is not None:
        schluessel = [farben[:, 2], farben[:, 1], farben[:, 0]] + schluessel
    folge = np.lexsort(schluessel)
    neu = np.empty_like(folge)
    neu[folge] = np.arange(len(folge))
    d = neu[dreiecke]
    dreh = np.argmin(d, axis=1)
    zeilen = np.arange(len(d))[:, None]
    d = d[zeilen, (dreh[:, None] + np.arange(3)[None, :]) % 3]
    d = d[np.lexsort((d[:, 2], d[:, 1], d[:, 0]))]
    aus = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(ecken[folge]),
                                    o3d.utility.Vector3iVector(d.astype(np.int32)))
    if farben is not None:
        aus.vertex_colors = o3d.utility.Vector3dVector(farben[folge])
    return aus


def splat_zu_netz(splat: Path, ziel: Path, *, aufloesung: int, je_kreis: int, voxel_m: float,
                  oben, massstab: float, renderer: str, geraet: str,
                  aufnahme: Path | None = None, bloecke_max: int | None = None,
                  masken: str | None = None, tiefenfilter=None) -> dict:
    zeiten: dict[str, float] = {}
    beginn = time.monotonic()
    # DIE BIBLIOTHEKEN ZUERST LADEN UND MESSEN (13.10.2026, auf-20261013-276 Fehler 2): Im
    # Erstlauf fehlten 34 s, die in keiner Teilzeit standen — das erste Laden von torch,
    # gsplat und CUDA fiel bis dahin ungezählt in den ersten Renderdurchgang.
    import numpy as np
    import open3d as o3d  # noqa: F401 — hier geladen, damit das Laden gezählt wird
    if renderer == "gsplat":
        import gsplat  # noqa: F401
        import torch  # noqa: F401
    zeiten["bibliotheken_s"] = round(time.monotonic() - beginn, 3)

    t1 = time.monotonic()
    kn = _kontext_netz()
    parameter = kn.netz_parameter(aufloesung=aufloesung, je_kreis=je_kreis, voxel_m=voxel_m,
                                  oben=oben, massstab=massstab, renderer=renderer,
                                  tiefenfilter=tiefenfilter)
    filter_ = set(parameter["tiefenfilter"])

    g = lies_splat(splat, kn)
    dicht = g["endlich"] & (g["deckkraft"] >= kn.DECKKRAFT_DICHT)
    if int(dicht.sum()) < 4:
        raise RuntimeError(f"Vom Splat {splat.name!r} sind nur {int(dicht.sum())} Punkte "
                           f"dicht (Deckkraft >= {kn.DECKKRAFT_DICHT}) — kein Netz moeglich.")
    lage_dicht = g["lage"][dicht]
    schritt = max(1, len(lage_dicht) // STICHPROBE_BEREICH)
    stichprobe = lage_dicht[::schritt]
    bereich = kn.dichter_bereich([tuple(p) for p in stichprobe], oben=parameter["oben"])
    deckung_punkte = lage_dicht[np.array(kn.stichprobe_indizes(len(lage_dicht)),
                                         dtype=np.int64)]
    zeiten["lesen_s"] = round(time.monotonic() - t1, 3)

    # BLICKWINKEL: aus der Aufnahme, wenn sie da ist und zum Splat passt — sonst der Ring.
    t1 = time.monotonic()
    aufnahme_bericht = {"angegeben": aufnahme is not None, "verwendet": False}
    ansichten = None
    weg_zentren = None
    if aufnahme is not None:
        geprueft = _aufnahme_pruefen(aufnahme, g, dicht, parameter["aufloesung"], kn)
        aufnahme_bericht.update({"auswahl": geprueft["auswahl"],
                                 "gleichheit": geprueft["gleichheit"],
                                 "grund": geprueft["grund"]})
        if geprueft["taugt"]:
            ansichten = geprueft["ansichten"]
            aufnahme_bericht["verwendet"] = True
            # ALLE Kamerazentren der Aufnahme, nicht nur die gewählten: Die Person stand an
            # jedem Augenblick neben der Kamera (Filter «weg»).
            weg_zentren = np.unique(np.round(np.array(geprueft["zentren"], dtype=np.float64),
                                             6), axis=0)
    zeiten["aufnahme_s"] = round(time.monotonic() - t1, 3)
    if ansichten is None:
        quelle = "ring"
        ki = kn.intrinsik(parameter["aufloesung"], parameter["hoehe"], kn.SICHTFELD_GRAD)
        ansichten = kn.blickwinkel(bereich, oben=parameter["oben"], massstab=massstab,
                                   je_kreis=je_kreis)
        for a in ansichten:
            a["ansicht"] = kn.ansicht_matrix(a["auge"], a["ziel"], parameter["oben"])
            a["ki"] = ki
    else:
        quelle = "aufnahme"
    spanne = max(bereich["halbmesser"], bereich["decke"] - bereich["boden"])
    tiefe_max = kn.TIEFE_MAX_FAKTOR * spanne * kn.UMLAUF_ABSTAND_FAKTOR
    nah = 0.05 / massstab
    nah_filter = kn.nah_min_splat(massstab)

    # MASKEN nur, wenn die Blickwinkel aus der Aufnahme kommen: Eine Maske gehört zu einem
    # Bild der Aufnahme, ein Ring-Blickwinkel hat keins.
    streuung_fehler: list[str] = []
    t1 = time.monotonic()
    masken_geladen = _masken_vorbereiten(ansichten, masken,
                                         aufnahme if quelle == "aufnahme" else None, kn)
    if quelle != "aufnahme" and aufnahme is not None:
        masken_geladen["bericht"]["grund"] = "Aufnahme nicht verwendet (Ring)"
    # Gefunden heisst nicht angewandt: Mit ausgeschaltetem Filter «maske» (Vergleichslauf)
    # werden die Masken gezählt, aber nicht benutzt.
    masken_geladen["bericht"]["angewandt"] = bool(masken_geladen["je_bild"]
                                                 and "maske" in filter_)
    zeiten["masken_s"] = round(time.monotonic() - t1, 3)

    def bilder(summe):
        if renderer == "gsplat":
            roh = _gsplat_ansichten(g, ansichten, geraet, nah, tiefe_max * 2.0, kn,
                                    streuung_an="streuung" in filter_,
                                    streuung_fehler=streuung_fehler)
        elif renderer == "cpu-probe":
            roh = _probe_ansichten(g, ansichten, kn)
        else:
            raise RuntimeError(f"Renderer {renderer!r} unbekannt, bekannt sind "
                               f"{list(RENDERER)}.")
        return _gesiebt(roh, ansichten, filter_=filter_, nah=nah_filter,
                        masken=masken_geladen["je_bild"], summe=summe, kn=kn,
                        zentren=weg_zentren, weg_min=kn.WEG_MIN_M / massstab,
                        weg_reichweite=kn.WEG_REICHWEITE_M / massstab)

    hoechstens = int(bloecke_max or kn.BLOECKE_MAX)
    voxel_angefragt = voxel_m / massstab                 # in Einheiten des Splats
    voxel = voxel_angefragt
    versuche = []
    for _ in range(VOXEL_VERSUCHE):
        # JEDER VERSUCH MIT SEINER ZEIT (auf-20261013-276 Fehler 2): Ein abgebrochener Versuch
        # der Blockwache kostete am echten Splat Sekunden, die bis hierher nirgends standen.
        t_versuch = time.monotonic()
        summe: dict = {}
        _ZWISCHENSTAND.update(tiefenfilter_summe=summe, voxel=float(voxel),
                              filter=sorted(filter_))
        try:
            volumen, (gefuellt, uebersprungen), t_render, t_tsdf, n_bloecke = _verschmelzen(
                bilder(summe), ansichten, voxel=voxel, tiefe_max=tiefe_max, spanne=spanne,
                bloecke_max=hoechstens, kn=kn)
            versuche.append({"voxel": round(float(voxel), 9), "bloecke": n_bloecke,
                             "dauer_s": round(time.monotonic() - t_versuch, 3)})
            break
        except _ZuVieleBloecke as zu_viel:
            _ZWISCHENSTAND["versuche"] = versuche
            versuche.append({"voxel": round(float(voxel), 9), "bloecke": zu_viel.bloecke,
                             "abgebrochen": True,
                             "dauer_s": round(time.monotonic() - t_versuch, 3)})
            voxel = kn.voxel_fuer_bloecke(voxel, zu_viel.bloecke, hoechstens)
    else:
        raise RuntimeError(f"Auch nach {VOXEL_VERSUCHE} Versuchen mehr als {hoechstens} "
                           f"TSDF-Bloecke ({versuche}) — Open3D wuerde abstuerzen.")
    zeiten["blockwache_verworfen_s"] = round(sum(v["dauer_s"] for v in versuche
                                                 if v.get("abgebrochen")), 3)
    zeiten["rendern_s"] = round(t_render, 3)
    zeiten["verschmelzen_s"] = round(t_tsdf, 3)
    filter_bericht = _filter_bericht(summe, filter_, nah_filter, kn,
                                     weg_aktiv=weg_zentren is not None, massstab=massstab,
                                     streuung_fehler=streuung_fehler)

    t1 = time.monotonic()
    netz = volumen.extract_triangle_mesh(weight_threshold=kn.GEWICHT_MIN).to_legacy()
    n_roh = len(netz.triangles)
    if n_roh == 0:
        raise RuntimeError("Die Verschmelzung ergab kein einziges Dreieck — keine Tiefe in "
                           "den Blickwinkeln (Blickwinkel, Deckkraft, Tiefenfilter oder "
                           "Massstab pruefen).")
    netz = _netz_ordnen(netz)
    cluster, n_je_cluster, _ = netz.cluster_connected_triangles()
    cluster, n_je_cluster = np.asarray(cluster), np.asarray(n_je_cluster)
    insel = n_je_cluster[cluster] < kn.INSEL_MIN_DREIECKE
    inseln = {"komponenten": int(len(n_je_cluster)),
              "groesste": int(n_je_cluster.max()),
              "entfernt": int((n_je_cluster < kn.INSEL_MIN_DREIECKE).sum()),
              "entfernt_dreiecke_anteil": round(float(insel.mean()), 4)}
    netz.remove_triangles_by_mask(insel)
    netz.remove_unreferenced_vertices()
    n_nach_inseln = len(netz.triangles)
    vereinfacht = False
    if n_nach_inseln > kn.ZIEL_DREIECKE:
        netz = netz.simplify_quadric_decimation(target_number_of_triangles=kn.ZIEL_DREIECKE)
        netz = _netz_ordnen(netz)
        vereinfacht = True
    if not netz.has_vertex_colors() or len(netz.triangles) == 0:
        was = "keine Farbe" if len(netz.triangles) else "kein Dreieck"
        raise RuntimeError(f"Nach dem Aufraeumen bleibt {was} "
                           f"({n_roh} roh, {n_nach_inseln} nach den Inseln).")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if not o3d.io.write_triangle_mesh(str(ziel), netz, write_ascii=False,
                                      write_vertex_normals=False, write_vertex_colors=True):
        raise RuntimeError(f"Open3D konnte {ziel.name!r} nicht schreiben.")
    zeiten["aufraeumen_s"] = round(time.monotonic() - t1, 3)
    t1 = time.monotonic()
    deckung = _deckung(netz, deckung_punkte, kn.DECKUNG_ABSTAND_VOXEL * voxel,
                       dicht_gesamt=len(lage_dicht))
    zeiten["deckung_s"] = round(time.monotonic() - t1, 3)
    zeiten["gesamt_s"] = round(time.monotonic() - beginn, 3)
    # Was in keiner Teilzeit steht — gross heisst: eine Stelle wird nicht gemessen.
    zeiten["ungezaehlt_s"] = round(zeiten["gesamt_s"] - sum(
        v for k, v in zeiten.items() if k != "gesamt_s"), 3)

    ecken = np.asarray(netz.vertices)
    farben = np.asarray(netz.vertex_colors)
    return {
        "status": "ok",
        "error": None,
        "renderer": renderer,
        "nur_probe": renderer == "cpu-probe",
        "geraet": geraet if renderer == "gsplat" else "cpu",
        "blickwinkel_quelle": quelle,
        "splat": {"datei": splat.name, "punkte": g["n"], "dicht": int(dicht.sum()),
                  "ungueltig": int((~g["endlich"]).sum()), "sh_grad": g["sh_grad"],
                  # Mittelpunkte der dichten Gaussians, Splat-Koordinaten.
                  "huellbox_dicht": [[round(float(v), 6) for v in lage_dicht.min(0)],
                                     [round(float(v), 6) for v in lage_dicht.max(0)]],
                  "bereich": {k: (int(v) if k == "n"
                                  else [round(float(x), 6) for x in v] if isinstance(v, tuple)
                                  else round(float(v), 6)) for k, v in bereich.items()}},
        "blickwinkel": {"quelle": quelle,
                        "ring": sum(1 for a in ansichten if a["art"] == "ring"),
                        "umlauf": sum(1 for a in ansichten if a["art"] == "umlauf"),
                        "aufnahme": sum(1 for a in ansichten if a["art"] == "aufnahme"),
                        "gesamt": len(ansichten),
                        "bildgroessen": sorted([list(s) for s in {
                            (a["ki"]["breite"], a["ki"]["hoehe"]) for a in ansichten}]),
                        "gefuellt_mittel": round(float(np.mean(gefuellt)), 4),
                        "gefuellt_min": round(float(np.min(gefuellt)), 4),
                        "uebersprungen": uebersprungen},
        "aufnahme": aufnahme_bericht,
        "masken": masken_geladen["bericht"],
        "tiefenfilter": filter_bericht,
        "deckung": deckung,
        "netz": {"datei": ziel.name, "ecken": int(len(ecken)),
                 "dreiecke": int(len(netz.triangles)), "dreiecke_roh": int(n_roh),
                 "dreiecke_nach_inseln": int(n_nach_inseln), "vereinfacht": vereinfacht,
                 "inseln": inseln, "reihenfolge": "fest (nach Lage geordnet)",
                 "huellbox": [[round(float(v), 6) for v in ecken.min(0)],
                              [round(float(v), 6) for v in ecken.max(0)]],
                 "farbe_mittel": [round(float(v), 4) for v in farben.mean(0)]},
        "voxel": {"angefragt_splat_einheiten": round(float(voxel_angefragt), 9),
                  "benutzt_splat_einheiten": round(float(voxel), 9),
                  "vergroessert": len(versuche) > 1, "versuche": versuche,
                  "bloecke_max": hoechstens,
                  "grund": (None if len(versuche) == 1 else
                            f"mehr als {hoechstens} TSDF-Bloecke — Open3D 0.20 stuerzt "
                            f"darueber ab (auf-20261013-275); Voxel vergroessert")},
        "voxel_splat_einheiten": round(float(voxel), 9),
        "tiefe_max_splat_einheiten": round(float(tiefe_max), 6),
        "koordinaten": "die des Splats, ohne Matrix — die Verortung wendet Blender an",
        "parameter": parameter,
        "zeiten_s": zeiten,
        "versionen": _versionen(),
    }


def _parser() -> argparse.ArgumentParser:
    """Die Schalter — eigene Funktion, damit eine Probe das Lesen der Werte pruefen kann
    (auf-20261013-275: eine Hochachse mit Minus brach argparse ab)."""
    ap = argparse.ArgumentParser(description="Splat (3DGS-PLY) → farbiges Netz (PLY). "
                                             "Läuft im .venv-splat.")
    ap.add_argument("splat")
    ap.add_argument("netz")
    ap.add_argument("--report", default=None)
    ap.add_argument("--aufloesung", type=int, default=None,
                    help="Bildbreite je Blickwinkel; Vorgabe kontext_netz.AUFLOESUNG_PX")
    ap.add_argument("--blickwinkel", type=int, default=None,
                    help="Azimute je Kreis (Ring und Umlauf); Vorgabe "
                         "kontext_netz.BLICKWINKEL_JE_KREIS")
    ap.add_argument("--voxel-m", dest="voxel_m", type=float, default=None,
                    help="Voxelkante der TSDF in Metern der Welt; Vorgabe kontext_netz.VOXEL_M")
    ap.add_argument("--oben", type=_drei, default=(0.0, 1.0, 0.0),
                    help="Hochrichtung im Splat, 'x,y,z' (aus der Verortungsmatrix)")
    ap.add_argument("--massstab", type=float, default=1.0,
                    help="Massstab der Verortung: ein Meter der Welt = 1/massstab Einheiten")
    ap.add_argument("--aufnahme", default=None,
                    help="COLMAP-Ordner der Aufnahme (sparse/0): Blickwinkel aus ihren Kameras, "
                         "wenn sie zum Splat passt; sonst der Ring")
    ap.add_argument("--bloecke-max", dest="bloecke_max", type=int, default=None,
                    help="Blockwache der TSDF; Vorgabe kontext_netz.BLOECKE_MAX (für Proben "
                         "und um die Grenze von Open3D zu messen)")
    ap.add_argument("--masken", default=None,
                    help="Ordner der Masken zur Aufnahme, oder 'keine'; ohne Angabe neben der "
                         "Aufnahme suchen (kontext_netz.masken_kandidaten)")
    ap.add_argument("--tiefenfilter", default=None,
                    help="eingeschaltete Tiefenfilter, z. B. 'deckkraft,nah' oder 'keine'; "
                         "Vorgabe alle (kontext_netz.TIEFENFILTER)")
    ap.add_argument("--renderer", choices=RENDERER, default="gsplat",
                    help="gsplat (echt, CUDA) oder cpu-probe (NUR für Proben)")
    ap.add_argument("--geraet", default="cuda", help="torch-Gerät für gsplat")
    return ap


def main(argv=None) -> int:
    ap = _parser()
    a = ap.parse_args(argv)

    try:
        kn = _kontext_netz()
        rep = splat_zu_netz(
            Path(a.splat), Path(a.netz),
            aufloesung=a.aufloesung or kn.AUFLOESUNG_PX,
            je_kreis=a.blickwinkel or kn.BLICKWINKEL_JE_KREIS,
            voxel_m=a.voxel_m or kn.VOXEL_M, oben=a.oben, massstab=a.massstab,
            renderer=a.renderer, geraet=a.geraet,
            aufnahme=Path(a.aufnahme) if a.aufnahme else None, bloecke_max=a.bloecke_max,
            masken=a.masken, tiefenfilter=a.tiefenfilter)
    except Exception as e:                                # Fehler als Bericht, nicht als Traceback
        rep = {"status": "error", "error": f"{type(e).__name__}: {e}",
               "renderer": a.renderer, "netz": None, "versionen": _versionen(),
               # Was bis zum Abbruch gezaehlt war (auf-20261013-277 Fehler 3: ohne dies fehlten
               # gerade die Filteranteile, die den Abbruch erklaeren).
               "zwischenstand": _ZWISCHENSTAND or None}

    text = json.dumps(rep, indent=2, ensure_ascii=False)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
