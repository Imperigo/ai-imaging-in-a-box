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
2. **Blickwinkel:** Ring auf Augenhöhe nach aussen, Umlauf von aussen nach innen
   (:func:`aiimaging.kontext_netz.blickwinkel`).
3. **Rendern** mit ``gsplat.rasterization(..., render_mode="RGB+ED")``: Farbe und
   **erwartete Tiefe** je Bildpunkt. Wo die akkumulierte Deckkraft unter
   ``DECKKRAFT_LEER`` liegt, gilt der Punkt als leer.
4. **Verschmelzen:** Open3D-TSDF (``VoxelBlockGrid``), ein Dreiecksnetz mit Eckpunktfarben.
5. **Aufräumen:** kleine Inseln weg, bei Bedarf vereinfachen.
6. **Schreiben:** PLY (binär, Eckpunktfarben) im **Koordinatensystem des Splats** — ohne
   Matrix; die Verortung wendet weiter Blender an. Dazu ein Bericht als JSON.

Die rechnerischen Teile stehen in ``aiimaging/kontext_netz.py`` (nur Standardbibliothek)
und werden **über den Dateipfad** geladen, nicht als Paket importiert — Begründung dort im
Modulkopf. Ein Paketimport zöge ``aiimaging/__init__.py`` und damit das Produkt in diese
Umgebung.

Der CPU-Ersatzrenderer (nur für Proben)
--------------------------------------
``--renderer cpu-probe`` ersetzt gsplat durch einen einfachen Punkt-Renderer mit
Tiefenpuffer: jeder dichte Gaussian ein Quadrat in der Grösse seiner projizierten Achsen,
SH-Grad 0, ohne weiche Mischung. **Er ist keine Alternative zu gsplat**, sondern die Naht,
an der sich Blickwinkel, TSDF, Inselentfernung und PLY-Ausgabe ohne Grafikkarte prüfen
lassen (13.10.2026: in der Cloud-Sitzung gibt es kein CUDA, gsplat rendert dort nicht).
Der Bericht trägt ``renderer: "cpu-probe"`` — ein solches Netz darf nie für ein echtes gelten.

Aufruf (immer über ``aiimaging.seams.splat_zu_netz``):
    .venv-splat/bin/python splat_zu_netz_runner.py <splat.ply> <netz.ply> [--report r.json]
        [--aufloesung 640] [--blickwinkel 16] [--voxel-m 0.05] [--oben 0,1,0]
        [--massstab 1.0] [--renderer gsplat|cpu-probe] [--geraet cuda|cpu]
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

#: Wie viele dichte Punkte höchstens für Mitte, Boden und Halbmesser gelesen werden.
STICHPROBE_BEREICH = 20000


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
# 3 · Rendern — gsplat (echt) und der Ersatzrenderer (nur Proben)
# --------------------------------------------------------------------------------------

def _gsplat_ansichten(g: dict, ansichten, ki: dict, geraet: str, nah: float, fern: float,
                      kn):
    """Je Blickwinkel ``(rgb uint8 HxWx3, tiefe float32 HxW, gefuellt-Anteil)``."""
    import numpy as np
    import torch
    from gsplat import rasterization

    if geraet.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("gsplat rendert nur mit CUDA (NVIDIA-Grafikkarte); hier ist "
                           "keine erreichbar. Fuer Proben ohne Karte: --renderer cpu-probe.")
    dev = torch.device(geraet)
    w = g["endlich"]
    zu = lambda a: torch.from_numpy(np.ascontiguousarray(a[w])).float().to(dev)  # noqa: E731
    means, quats, scales = zu(g["lage"]), zu(g["quat"]), zu(g["skala"])
    opac, sh = zu(g["deckkraft"]), zu(g["sh"])
    b, h = ki["breite"], ki["hoehe"]
    K = torch.tensor(ki["K"], dtype=torch.float32, device=dev).reshape(3, 3)
    for start in range(0, len(ansichten), GSPLAT_JE_DURCHGANG):
        teil = ansichten[start:start + GSPLAT_JE_DURCHGANG]
        views = torch.tensor([a["ansicht"] for a in teil], dtype=torch.float32,
                             device=dev).reshape(-1, 4, 4)
        with torch.no_grad():
            bild, alpha, _ = rasterization(
                means, quats, scales, opac, sh, views, K.expand(len(teil), 3, 3), b, h,
                near_plane=nah, far_plane=fern, sh_degree=g["sh_grad"],
                render_mode="RGB+ED")
        bild, alpha = bild.cpu().numpy(), alpha[..., 0].cpu().numpy()
        for j in range(len(teil)):
            a = alpha[j]
            leer = a < kn.DECKKRAFT_LEER
            # Ohne Hintergrund ist die Farbe mit der Deckkraft vorgemischt; zurückteilen.
            rgb = np.clip(bild[j, ..., :3] / np.maximum(a, 1e-6)[..., None], 0.0, 1.0)
            tiefe = bild[j, ..., 3].astype(np.float32)
            tiefe[leer | ~np.isfinite(tiefe)] = 0.0
            yield (np.round(rgb * 255.0).astype(np.uint8), tiefe, float((~leer).mean()))


def _probe_ansichten(g: dict, ansichten, ki: dict, kn):
    """Der Ersatzrenderer: Punkte mit Tiefenpuffer. NUR FÜR PROBEN (Modulkopf)."""
    import numpy as np

    w = g["endlich"] & (g["deckkraft"] >= kn.DECKKRAFT_LEER)
    lage = g["lage"][w]
    farbe = np.clip(0.5 + 0.28209479177387814 * g["sh"][w][:, 0, :], 0.0, 1.0)
    farbe8 = np.round(farbe * 255.0).astype(np.uint8)
    # Die drei Achsen je Gaussian in der Welt: Drehung mal Skala. Die Drehung kommt aus der
    # stdlib-Hälfte, damit Probe und Produktseite dieselbe Formel benutzen.
    achsen = np.empty((len(lage), 3, 3))
    for i, (q, s) in enumerate(zip(g["quat"][w], g["skala"][w])):
        r = np.array(kn.quaternion_zu_matrix(*q))
        achsen[i] = (r * s[None, :]).T                   # Zeile k = Achse k
    b, h, fx, fy, cx, cy = (ki[k] for k in ("breite", "hoehe", "fx", "fy", "cx", "cy"))
    for ansicht in ansichten:
        v = np.array(ansicht["ansicht"]).reshape(4, 4)
        p = lage @ v[:3, :3].T + v[:3, 3]
        z = p[:, 2]
        vorn = z > 1e-3
        u = np.floor(fx * p[vorn, 0] / z[vorn] + cx).astype(np.int64)
        vv = np.floor(fy * p[vorn, 1] / z[vorn] + cy).astype(np.int64)
        zz = z[vorn]
        a_cam = achsen[vorn] @ v[:3, :3].T               # Achsen in Kamerakoordinaten
        quer = np.sqrt(a_cam[..., 0] ** 2 + a_cam[..., 1] ** 2).max(axis=1)
        radius = np.minimum(np.ceil(2.0 * quer * fx / zz), PROBE_RADIUS_MAX_PX).astype(np.int64)
        reihe = np.argsort(radius, kind="stable")
        u, vv, zz, radius, c = u[reihe], vv[reihe], zz[reihe], radius[reihe], farbe8[vorn][reihe]
        idx_l, z_l, c_l = [], [], []
        for dy in range(-PROBE_RADIUS_MAX_PX, PROBE_RADIUS_MAX_PX + 1):
            for dx in range(-PROBE_RADIUS_MAX_PX, PROBE_RADIUS_MAX_PX + 1):
                ab = int(np.searchsorted(radius, max(abs(dx), abs(dy))))
                if ab >= len(radius):
                    continue
                uu, vy = u[ab:] + dx, vv[ab:] + dy
                ok = (uu >= 0) & (uu < b) & (vy >= 0) & (vy < h)
                idx_l.append(vy[ok] * b + uu[ok])
                z_l.append(zz[ab:][ok])
                c_l.append(c[ab:][ok])
        tiefe = np.zeros(b * h, dtype=np.float32)
        rgb = np.zeros((b * h, 3), dtype=np.uint8)
        if idx_l:
            idx, zs, cs = np.concatenate(idx_l), np.concatenate(z_l), np.concatenate(c_l)
            folge = np.lexsort((zs, idx))                # je Bildpunkt der nächste zuerst
            idx, zs, cs = idx[folge], zs[folge], cs[folge]
            erste = np.unique(idx, return_index=True)[1]
            tiefe[idx[erste]] = zs[erste]
            rgb[idx[erste]] = cs[erste]
        yield (rgb.reshape(h, b, 3), tiefe.reshape(h, b), float((tiefe > 0).mean()))


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


def splat_zu_netz(splat: Path, ziel: Path, *, aufloesung: int, je_kreis: int, voxel_m: float,
                  oben, massstab: float, renderer: str, geraet: str) -> dict:
    import numpy as np
    import open3d as o3d

    zeiten: dict[str, float] = {}
    beginn = time.monotonic()
    kn = _kontext_netz()
    parameter = kn.netz_parameter(aufloesung=aufloesung, je_kreis=je_kreis, voxel_m=voxel_m,
                                  oben=oben, massstab=massstab, renderer=renderer)

    g = lies_splat(splat, kn)
    dicht = g["endlich"] & (g["deckkraft"] >= kn.DECKKRAFT_DICHT)
    if int(dicht.sum()) < 4:
        raise RuntimeError(f"Vom Splat {splat.name!r} sind nur {int(dicht.sum())} Punkte "
                           f"dicht (Deckkraft >= {kn.DECKKRAFT_DICHT}) — kein Netz moeglich.")
    lage_dicht = g["lage"][dicht]
    schritt = max(1, len(lage_dicht) // STICHPROBE_BEREICH)
    bereich = kn.dichter_bereich([tuple(p) for p in lage_dicht[::schritt]],
                                 oben=parameter["oben"])
    zeiten["lesen_s"] = round(time.monotonic() - beginn, 3)

    ki = kn.intrinsik(parameter["aufloesung"], parameter["hoehe"], kn.SICHTFELD_GRAD)
    ansichten = kn.blickwinkel(bereich, oben=parameter["oben"], massstab=massstab,
                               je_kreis=je_kreis)
    for a in ansichten:
        a["ansicht"] = kn.ansicht_matrix(a["auge"], a["ziel"], parameter["oben"])
    voxel = voxel_m / massstab                           # in Einheiten des Splats
    spanne = max(bereich["halbmesser"], bereich["decke"] - bereich["boden"])
    tiefe_max = kn.TIEFE_MAX_FAKTOR * spanne * kn.UMLAUF_ABSTAND_FAKTOR
    nah = 0.05 / massstab

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
    kamera = o3c.Tensor(np.array(ki["K"], dtype=np.float64).reshape(3, 3))
    if renderer == "gsplat":
        bilder = _gsplat_ansichten(g, ansichten, ki, geraet, nah, tiefe_max * 2.0, kn)
    elif renderer == "cpu-probe":
        bilder = _probe_ansichten(g, ansichten, ki, kn)
    else:
        raise RuntimeError(f"Renderer {renderer!r} unbekannt, bekannt sind {list(RENDERER)}.")
    gefuellt: list[float] = []
    t_render = t_tsdf = 0.0
    t0 = time.monotonic()
    for ansicht, (rgb, tiefe, anteil) in zip(ansichten, bilder):
        t1 = time.monotonic()
        t_render += t1 - t0
        gefuellt.append(anteil)
        if anteil > 0.0:
            tiefe_bild = o3d.t.geometry.Image(o3c.Tensor(np.ascontiguousarray(
                tiefe, dtype=np.float32)))
            farb_bild = o3d.t.geometry.Image(o3c.Tensor(np.ascontiguousarray(
                rgb, dtype=np.float32) / 255.0))
            aussen = o3c.Tensor(np.array(ansicht["ansicht"], dtype=np.float64).reshape(4, 4))
            bl = volumen.compute_unique_block_coordinates(
                tiefe_bild, kamera, aussen, 1.0, float(tiefe_max),
                trunc_voxel_multiplier=kn.SDF_TRUNC_VOXEL)
            volumen.integrate(bl, tiefe_bild, farb_bild, kamera, kamera, aussen, 1.0,
                              float(tiefe_max), trunc_voxel_multiplier=kn.SDF_TRUNC_VOXEL)
        t0 = time.monotonic()
        t_tsdf += t0 - t1
    zeiten["rendern_s"] = round(t_render, 3)
    zeiten["verschmelzen_s"] = round(t_tsdf, 3)

    t1 = time.monotonic()
    netz = volumen.extract_triangle_mesh(weight_threshold=kn.GEWICHT_MIN).to_legacy()
    n_roh = len(netz.triangles)
    if n_roh == 0:
        raise RuntimeError("Die Verschmelzung ergab kein einziges Dreieck — keine Tiefe in "
                           "den Blickwinkeln (Blickwinkel, Deckkraft oder Massstab pruefen).")
    cluster, n_je_cluster, _ = netz.cluster_connected_triangles()
    cluster, n_je_cluster = np.asarray(cluster), np.asarray(n_je_cluster)
    insel = n_je_cluster[cluster] < kn.INSEL_MIN_DREIECKE
    netz.remove_triangles_by_mask(insel)
    netz.remove_unreferenced_vertices()
    n_nach_inseln = len(netz.triangles)
    vereinfacht = False
    if n_nach_inseln > kn.ZIEL_DREIECKE:
        netz = netz.simplify_quadric_decimation(target_number_of_triangles=kn.ZIEL_DREIECKE)
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
    zeiten["gesamt_s"] = round(time.monotonic() - beginn, 3)

    ecken = np.asarray(netz.vertices)
    farben = np.asarray(netz.vertex_colors)
    return {
        "status": "ok",
        "error": None,
        "renderer": renderer,
        "nur_probe": renderer == "cpu-probe",
        "geraet": geraet if renderer == "gsplat" else "cpu",
        "splat": {"datei": splat.name, "punkte": g["n"], "dicht": int(dicht.sum()),
                  "ungueltig": int((~g["endlich"]).sum()), "sh_grad": g["sh_grad"],
                  # Mittelpunkte der dichten Gaussians, Splat-Koordinaten.
                  "huellbox_dicht": [[round(float(v), 6) for v in lage_dicht.min(0)],
                                     [round(float(v), 6) for v in lage_dicht.max(0)]],
                  "bereich": {k: (int(v) if k == "n"
                                  else [round(float(x), 6) for x in v] if isinstance(v, tuple)
                                  else round(float(v), 6)) for k, v in bereich.items()}},
        "blickwinkel": {"ring": sum(1 for a in ansichten if a["art"] == "ring"),
                        "umlauf": sum(1 for a in ansichten if a["art"] == "umlauf"),
                        "gesamt": len(ansichten),
                        "gefuellt_mittel": round(float(np.mean(gefuellt)), 4),
                        "gefuellt_min": round(float(np.min(gefuellt)), 4)},
        "netz": {"datei": ziel.name, "ecken": int(len(ecken)),
                 "dreiecke": int(len(netz.triangles)), "dreiecke_roh": int(n_roh),
                 "dreiecke_nach_inseln": int(n_nach_inseln), "vereinfacht": vereinfacht,
                 "huellbox": [[round(float(v), 6) for v in ecken.min(0)],
                              [round(float(v), 6) for v in ecken.max(0)]],
                 "farbe_mittel": [round(float(v), 4) for v in farben.mean(0)]},
        "voxel_splat_einheiten": round(float(voxel), 9),
        "tiefe_max_splat_einheiten": round(float(tiefe_max), 6),
        "koordinaten": "die des Splats, ohne Matrix — die Verortung wendet Blender an",
        "parameter": parameter,
        "zeiten_s": zeiten,
        "versionen": _versionen(),
    }


def main(argv=None) -> int:
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
    ap.add_argument("--renderer", choices=RENDERER, default="gsplat",
                    help="gsplat (echt, CUDA) oder cpu-probe (NUR für Proben)")
    ap.add_argument("--geraet", default="cuda", help="torch-Gerät für gsplat")
    a = ap.parse_args(argv)

    try:
        kn = _kontext_netz()
        rep = splat_zu_netz(
            Path(a.splat), Path(a.netz),
            aufloesung=a.aufloesung or kn.AUFLOESUNG_PX,
            je_kreis=a.blickwinkel or kn.BLICKWINKEL_JE_KREIS,
            voxel_m=a.voxel_m or kn.VOXEL_M, oben=a.oben, massstab=a.massstab,
            renderer=a.renderer, geraet=a.geraet)
    except Exception as e:                                # Fehler als Bericht, nicht als Traceback
        rep = {"status": "error", "error": f"{type(e).__name__}: {e}",
               "renderer": a.renderer, "netz": None, "versionen": _versionen()}

    text = json.dumps(rep, indent=2, ensure_ascii=False)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
