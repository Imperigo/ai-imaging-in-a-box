"""KONTEXT ALS NETZ — die rechnerische Hälfte der Splat-Brücke (Owner-Entscheid 79, 13.10.2026).

Warum es dieses Modul gibt
--------------------------
Bis zum 13.10.2026 zeichnete Blender den Splat als **harte Kugeln**
(``runners/blender_depth_stage._kontext_laden``): Drehung und Form der Gaussians fielen weg,
70 % der Punkte am echten Splat lagen unter der Deckkraftschwelle und wurden verworfen, und das
Bildmodell malte aus der lückigen Streuung «Konfetti» (``auf-20261008-271`` bis ``-274``,
9 von 9 Bildern, auch nach dem Glätten). Der Fehler lag bei uns (``docs/SPLAT_WEGE_2026-10-13.md``).

Der neue Weg (Entscheid 79): **gsplat** (Apache-2.0) rendert den Splat richtig — weiche,
gedrehte Ellipsoide, Farbe je Blickrichtung — aus vielen Blickwinkeln, mit Farbe und
**erwarteter Tiefe**. **Open3D** (MIT) verschmilzt diese Tiefenbilder per **TSDF** zu einem
farbigen Dreiecksnetz. Blender lädt danach das Netz wie ein gewöhnliches Umgebungsobjekt.

gsplat, Open3D und torch laufen **nur** in einer eigenen Umgebung ``.venv-splat`` hinter der
Prozessgrenze (``runners/splat_zu_netz_runner.py``, aufgerufen von
:func:`aiimaging.seams.splat_zu_netz`). Regel 4: Im Produkt-venv liegt keines davon.

Was hier steht — und warum nur die Standardbibliothek
-----------------------------------------------------
Die **reine Rechnung**, die über das Bild entscheidet: PLY-Kopf lesen, SH-Grad bestimmen,
Quaternion zu Drehung, Blickwinkel und Kameraintrinsik erzeugen, die Lage («oben», Massstab)
aus der Verortungsmatrix ableiten — und seit dem 13.10.2026 die COLMAP-Aufnahme lesen, aus ihr
Blickwinkel wählen und urteilen, ob sie zum Splat passt (Abschnitt «Die Aufnahme lesen»). Dieselbe Begründung wie bei :mod:`aiimaging.kontext`: *Was
hinter der Prozessgrenze steht, erreicht keine Probe.* Hier steht es diesseits und ist im
Produkt-venv prüfbar.

**Der Runner lädt diese Datei über ihren Pfad**, nicht als Teil des Pakets
(Entscheid 13.10.2026, statt einer Doppelung mit Gleichheitsprobe wie bei
``ifc_to_glb_runner.GELAENDE_TYPEN``). Begründung: Eine Doppelung lohnt, wo eine Liste kurz
ist und ihr Abgleich trivial; hier sind es Blickwinkel, Matrizen und ein Dateikopf — zwei
Fassungen davon gegeneinander zu prüfen hiesse, jede Rechnung zweimal zu schreiben und
einmal zu vergessen. Damit das Laden über den Pfad trägt, **importiert dieses Modul nichts
aus ``aiimaging``** und nichts ausserhalb der Standardbibliothek; ``tests/test_splat_zu_netz.py``
wacht darüber. Wer hier ``numpy`` oder ``aiimaging.kontext`` importiert, bricht den Runner.

Koordinaten
-----------
Alles in diesem Modul gilt im **Koordinatensystem des Splats**, wie es in der Datei steht —
das Netz kommt im selben System heraus, ohne Matrix; die Verortungsmatrix wendet weiter
Blender an (:func:`aiimaging.kontext.matrix_nach_blender`). Darum braucht der Runner
zwei Angaben aus der Matrix: wo im Splat **oben** ist und welcher **Massstab** gilt
(:func:`oben_und_massstab`) — Augenhöhe und Voxelgrösse sind Meter der Welt.

Die Kameras folgen der Konvention von gsplat und Open3D (wie OpenCV): ``x`` rechts, ``y``
unten, ``z`` in Blickrichtung; die Ansichtsmatrix bildet die Welt in die Kamera ab.

Was gesetzt und nicht gemessen ist
----------------------------------
Alle Zahlen unter «GESETZT» unten. Welche Blickwinkel, welche Voxelgrösse und welche Auflösung
an echten Splats das beste Netz geben, ist am Heim-PC zu messen (GPU).
"""
from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

__all__ = [
    "AUFLOESUNG_PX", "AUFNAHME_BLICKE_MAX", "AUGENHOEHE_M", "BLICKWINKEL_JE_KREIS",
    "BLOECKE_MAX", "DECKKRAFT_DICHT", "DECKKRAFT_LEER", "DECKUNG_ABSTAND_VOXEL", "FASSUNG",
    "GEWICHT_MIN", "GLEICH_MEDIAN_MAX", "GLEICH_P90_MAX", "HUELLE_RAND", "INSEL_MIN_DREIECKE",
    "KAMERAS_INNEN_MIN", "KontextNetzError", "QUELLE_NETZ", "QUELLE_SPLAT",
    "RING_NEIGUNGEN_GRAD", "SATZ_KUGELN_GESCHEITERT", "SATZ_KUGELN_NICHT_EINGERICHTET",
    "SDF_TRUNC_VOXEL", "SICHTFELD_GRAD", "TIEFE_MAX_FAKTOR", "UMLAUF_ABSTAND_FAKTOR",
    "UMLAUF_ERHEBUNG_GRAD", "VOXEL_M", "ZIEL_DREIECKE",
    "ansicht_matrix", "anteil_innen", "art_der_datei", "aufnahme_blickwinkel",
    "aufnahme_fingerabdruck", "aufnahme_kandidaten", "bildhoehe", "blickwinkel",
    "dichter_bereich", "gleichheit_befund", "huelle_erweitert", "intrinsik",
    "intrinsik_skaliert", "ist_aufnahme_ordner", "ist_netz", "kamerazentrum", "lies_aufnahme",
    "lies_ply_kopf", "lies_punkte3d", "netz_kennzahlen", "netz_parameter", "oben_und_massstab",
    "pose_zu_ansicht", "quaternion_zu_matrix", "schreibe_netz_ply", "sh_grad",
    "sh_grad_aus_kopf", "voxel_fuer_bloecke", "waehle_augenblicke",
]


class KontextNetzError(ValueError):
    """Diese Angabe zur Splat-Brücke lässt sich nicht deuten — und ein Ersatzwert wäre schlimmer."""


# ======================================================================================
# GESETZT — nicht gemessen (13.10.2026). Messauftrag am Heim-PC.
# ======================================================================================

#: Augenhöhe des Kamerarings über dem Boden, in Metern der Welt. GESETZT.
#: Ein Splat vom Gehweg ist aus Augenhöhe aufgenommen — von dort sieht er am besten aus,
#: und von dort sind die Flächen belegt.
AUGENHOEHE_M = 1.6

#: Blickwinkel je Kreis (Azimute). GESETZT. 16 heisst alle 22,5°: Bei
#: :data:`SICHTFELD_GRAD` 90° überlappen Nachbarn zu drei Vierteln — jede Fläche wird aus
#: mehreren Richtungen gesehen, und die TSDF mittelt Fehler einzelner Ansichten heraus.
BLICKWINKEL_JE_KREIS = 16

#: Die Neigungen des Rings, in Grad (positiv = nach oben). GESETZT.
#: +5° fasst Fassaden und Kronen bis über Augenhöhe, −25° den Boden bis zu den Füssen.
#: Senkrecht nach unten fehlt mit Absicht: Dort steht im Splat meist der Aufnehmende.
RING_NEIGUNGEN_GRAD = (5.0, -25.0)

#: Die Umlaufbahn von aussen nach innen: Abstand als Vielfaches des Halbmessers der dichten
#: Punkte, und Erhebung in Grad. GESETZT. Sie fasst, was der Ring von innen nicht sieht:
#: Dächer, Rückseiten, den Boden zwischen den Dingen.
UMLAUF_ABSTAND_FAKTOR = 1.2
UMLAUF_ERHEBUNG_GRAD = 35.0

#: Waagrechtes Sichtfeld der Blickwinkel, in Grad. GESETZT. Weit, damit wenige Bilder viel
#: fassen; die TSDF braucht Überlappung, keine Schönheit.
SICHTFELD_GRAD = 90.0

#: Bildbreite in Bildpunkten; die Höhe ist drei Viertel davon (:func:`bildhoehe`). GESETZT.
AUFLOESUNG_PX = 640

#: Kantenlänge eines Voxels der TSDF, in Metern der Welt. GESETZT. 5 cm war gedacht: fein genug für
#: Bordsteine und Stufen, grob genug, dass ein Strassenraum von 100 m in den Speicher passt.
#: **Von 0,05 auf 0,07 m nach ``auf-20261013-275``:** Bei 5 cm stuerzte Open3D 0.20 am echten
#: Splat in ``extract_triangle_mesh`` ab (SIGSEGV; ~435 000 aktive Bloecke, Grenze gemessen bei
#: ~300 000: 324 000 stuerzt, 245 000 geht). Mit 7 cm lief es (499 999 Dreiecke, 14,5 s).
VOXEL_M = 0.07

#: Die Abschneidedistanz der TSDF in Voxeln. GESETZT (die Faustregel aus der Open3D-Dokumentation
#: ist 3–5 Voxel).
SDF_TRUNC_VOXEL = 4.0

#: Ab welchem Gewicht ein Voxel beim Herausziehen zählt — das Gewicht ist die Zahl der
#: Blickwinkel, die ihn gesehen haben. GESETZT. 1 heisst: einmal gesehen genügt. Die
#: Vorgabe von Open3D (3) ist für Handscans mit Hunderten Bildern gedacht; bei unseren
#: wenigen Blickwinkeln fielen damit Rückseiten und Ränder weg, die nur einer sieht.
GEWICHT_MIN = 1.0

#: Bis wohin eine Tiefe zählt: Vielfaches des Halbmessers der dichten Punkte. GESETZT.
#: Weiter entfernt sind es in echten Splats meist Wolken am Rand, die als Fläche das Netz
#: verstellen würden.
TIEFE_MAX_FAKTOR = 3.0

#: Unter dieser **akkumulierten** Deckkraft gilt ein Bildpunkt als leer. GESETZT.
#: Anders als ``kontext.DECKKRAFT_MIN`` (je Gaussian, für harte Kugeln) wird hier das
#: gemischte Bild beurteilt: Ein Punkt, durch den man zur Hälfte hindurchsieht, trägt keine
#: verlässliche Tiefe.
DECKKRAFT_LEER = 0.5

#: Ab welcher Deckkraft (``sigmoid(opacity)``) ein Gaussian zu den **dichten Punkten** zählt,
#: aus denen Mitte, Boden und Ausdehnung bestimmt werden. GESETZT, gleich
#: ``kontext.DECKKRAFT_MIN`` — die Schwebeteile des synthetischen Splats liegen darunter.
DECKKRAFT_DICHT = 0.10

#: Zusammenhängende Netzstücke mit weniger Dreiecken werden entfernt («Inseln»). GESETZT.
#:
#: **Geprüft am 13.10.2026, bleibt absolut** (``auf-20261013-275``: am echten Splat fielen 42 %
#: der Dreiecke so weg). Am synthetischen Strassenraum (CPU-Ersatzrenderer, 0,15-m-Voxel)
#: warf 200 mit den Ring-Blickwinkeln 7,9 % weg, 0,1 % aller Dreiecke (336) 8,7 %, 1 % der
#: grössten Komponente 10,0 % — fast gleich, aber **ein relativer Wert wächst mit der Szene**
#: und würfe an einem grossen, zerstückelten Netz mehr weg. Und die Inseln sind keine
#: Störung, sondern **schlecht gesehene echte Fläche**: Die Deckung fiel durch das Entfernen
#: von 76 % auf 71 %. Mit den Blickwinkeln der Aufnahme blieben 75 statt 2547 Stücke, und 200
#: warf nur 0,35 % weg. Die Ursache sind die Blickwinkel, nicht die Schwelle; die Zahl der
#: Dreiecke ist an den Voxel gebunden und meint damit eine Fläche (200 Dreiecke ≈ 100 Voxel²,
#: bei 7 cm ≈ 0,5 m²). Der Bericht zählt die Inseln (``netz.inseln``), damit die HomeStation
#: sieht, ob es am echten Splat ebenso ist.
INSEL_MIN_DREIECKE = 200

#: Hat das Netz mehr Dreiecke, wird es darauf vereinfacht. GESETZT. Blender rendert eine
#: halbe Million Dreiecke ohne Mühe; mehr kostet Ladezeit je Kamera.
ZIEL_DREIECKE = 500_000

#: Anteile für den **robusten** Bereich der dichten Punkte (Perzentile): Ein einzelner
#: Ausreisser in 200 m Höhe soll weder die Mitte noch den Boden bestimmen. GESETZT.
ANTEIL_UNTEN, ANTEIL_OBEN = 0.02, 0.98

#: Der Codestand der Brücke. Hochzählen, wenn bei gleichen Parametern ein anderes Netz
#: entsteht — die Zahl steht im Speicherschlüssel (:func:`netz_parameter`), sonst käme ein
#: altes Netz als Treffer zurück. **2 seit 13.10.2026:** Blickwinkel aus der Aufnahme,
#: Blockwache und Deckungsmass.
FASSUNG = 2


# --------------------------------------------------------------------------------------
# Blickwinkel aus der Aufnahme (13.10.2026, nach auf-20261013-275)
# --------------------------------------------------------------------------------------
# **Anlass:** Am echten Splat deckte das Netz nur 21–26 % der Fläche neben dem Bauwerk, in
# Fetzen; seine Hüllbox mass ~60 × 60 × 47 m bei einem Splat von ~151 × 215 × 266 m. Der Ring
# im Zentrum und der Umlauf sehen den Splat nicht dort, wo die Aufnahme ihn sah. Gaussians
# sind nur aus den Richtungen verlässlich, aus denen sie trainiert wurden — also nimmt die
# Brücke, wo es sie gibt, **die Kameras der Aufnahme** (COLMAP) als Blickwinkel.

#: Höchstzahl der Blickwinkel aus der Aufnahme. GESETZT. 240 heisst am echten Splat (4 Rig-
#: Kameras × 240 Augenblicke) jeder vierte Augenblick mit allen vier Kameras — fünfmal so viele
#: Bilder wie der Ring (48); gsplat rendert sie in Sekunden, die TSDF in Minuten.
AUFNAHME_BLICKE_MAX = 240

#: Gleichheitsprüfung Aufnahme ↔ Splat: Median und 90-%-Perzentil des Abstands der COLMAP-
#: Punkte zur nächsten dichten Splat-Mitte, **als Anteil der Diagonale** des dichten Bereichs
#: (P2–P98) — relativ, weil die Einheiten des Splats keine Meter sind (am echten Splat
#: 1 Einheit ≈ 6,22 m). GESETZT. Die HomeStation mass am echten Splat (13.10.2026, CPU)
#: Median 0,25 % und P90 ~0,8 % der Diagonale; die Schwellen lassen das Vierfache bzw.
#: Fünffache durch und weisen eine Verschiebung um ein Zehntel der Szene sicher ab.
GLEICH_MEDIAN_MAX = 0.01
GLEICH_P90_MAX = 0.04

#: Mindestanteil der Kamerazentren in der um :data:`HUELLE_RAND` erweiterten Box der dichten
#: Punkte (P2–P98). GESETZT. Am echten Splat liegen 89 % schon in der unerweiterten Box; wer
#: aus einer anderen Szene stammt, steht draussen. Der Rand ist ein Anteil der Kantenlänge je
#: Achse.
KAMERAS_INNEN_MIN = 0.5
HUELLE_RAND = 0.25

#: Wie nah (in Voxeln) ein dichter Splat-Punkt an einer Netzfläche liegen muss, um als
#: **gedeckt** zu zählen. GESETZT: drei Voxel — näher kann die TSDF eine Fläche nicht legen,
#: weiter weg ist es eine andere Fläche.
DECKUNG_ABSTAND_VOXEL = 3.0

#: Wie viele aktive Blöcke die TSDF höchstens haben darf, bevor der Voxel vergrössert wird.
#: GESETZT nach ``auf-20261013-275``: Open3D 0.20 stürzte in ``extract_triangle_mesh`` bei
#: ~324 000 Blöcken ab und lief bei ~245 000. Mehr Blickwinkel aus der Aufnahme sehen mehr
#: Fläche — die Blockzahl steigt, und ein Absturz kommt ohne Bericht.
BLOECKE_MAX = 250_000

#: Die Dateien einer Aufnahme, deren Inhalt den Speicherschlüssel des Netzes bestimmt.
#: ``points3D`` fehlt mit Absicht: gross, und es ändert sich nie ohne ``images``.
AUFNAHME_DATEIEN = ("cameras", "images", "frames", "rigs")

#: Die Quelle im Block ``kontext`` des Blender-Berichts: woraus die Umgebung gezeichnet wurde.
QUELLE_SPLAT = "splat-ply"
QUELLE_NETZ = "netz-ply"

#: Die Sätze für ``verdict.hinweise``, wenn die Umgebung als Notlösung gezeichnet wurde
#: (Owner-Auftrag 13.10.2026: «deutlich»). Zwei, weil die Ursachen zwei verschiedene
#: Handgriffe verlangen: einrichten oder nachsehen.
SATZ_KUGELN_NICHT_EINGERICHTET = (
    "UMGEBUNG ALS NOTLOESUNG (Kugeln) gezeichnet — Splat-Bruecke nicht eingerichtet "
    "(.venv-splat fehlt, siehe betrieb/SPLAT_BRUECKE.md); Konfetti im Bild moeglich.")
SATZ_KUGELN_GESCHEITERT = (
    "UMGEBUNG ALS NOTLOESUNG (Kugeln) gezeichnet — die Splat-Bruecke ist gescheitert "
    "(Grund im Befund unter kontext.netz_grund); Konfetti im Bild moeglich.")


# ======================================================================================
# PLY lesen und schreiben
# ======================================================================================

#: PLY-Typ → (struct-Zeichen, Bytes). Beide Schreibweisen der Norm.
PLY_TYPEN = {
    "char": ("b", 1), "int8": ("b", 1), "uchar": ("B", 1), "uint8": ("B", 1),
    "short": ("h", 2), "int16": ("h", 2), "ushort": ("H", 2), "uint16": ("H", 2),
    "int": ("i", 4), "int32": ("i", 4), "uint": ("I", 4), "uint32": ("I", 4),
    "float": ("f", 4), "float32": ("f", 4), "double": ("d", 8), "float64": ("d", 8),
}

#: Wie weit der Kopf höchstens reicht. Ein echter 3DGS-Kopf hat um 2 kB; mehr ist keine PLY.
KOPF_HOECHSTENS = 1 << 16


def lies_ply_kopf(pfad) -> dict:
    """Den Kopf einer PLY-Datei lesen — ohne die Daten.

    Returns:
        ``{format, elemente, kopf_bytes}``. ``elemente`` ist eine Liste
        ``{name, anzahl, eigenschaften}``; eine Eigenschaft ist ``{name, typ}`` oder, für
        Listen (die Ecken einer Fläche), ``{name, typ: "list", zaehler, eintrag}``.

    Raises:
        KontextNetzError: keine PLY, Kopf ohne Ende, unbekanntes Format oder unbekannter Typ.
    """
    p = Path(pfad)
    try:
        with open(p, "rb") as datei:
            roh = datei.read(KOPF_HOECHSTENS)
    except OSError as fehler:
        raise KontextNetzError(f"{p.name!r} ist nicht lesbar: {fehler}") from fehler
    if not roh.startswith(b"ply\n") and not roh.startswith(b"ply\r\n"):
        raise KontextNetzError(f"{p.name!r} ist keine PLY-Datei (erste Zeile nicht 'ply').")
    ende = roh.find(b"end_header\n")
    if ende < 0:
        raise KontextNetzError(f"{p.name!r}: Der PLY-Kopf endet nicht in den ersten "
                               f"{KOPF_HOECHSTENS} Bytes.")
    kopf_bytes = ende + len(b"end_header\n")
    zeilen = roh[:ende].decode("ascii", errors="replace").splitlines()
    form = None
    elemente: list[dict] = []
    for zeile in zeilen[1:]:
        teile = zeile.split()
        if not teile or teile[0] in ("comment", "obj_info"):
            continue
        if teile[0] == "format":
            form = teile[1] if len(teile) > 1 else None
        elif teile[0] == "element" and len(teile) == 3:
            try:
                anzahl = int(teile[2])
            except ValueError as fehler:
                raise KontextNetzError(f"{p.name!r}: Elementzahl {teile[2]!r}.") from fehler
            elemente.append({"name": teile[1], "anzahl": anzahl, "eigenschaften": []})
        elif teile[0] == "property" and elemente:
            if teile[1] == "list" and len(teile) == 5:
                for t in teile[2:4]:
                    if t not in PLY_TYPEN:
                        raise KontextNetzError(f"{p.name!r}: unbekannter Typ {t!r}.")
                elemente[-1]["eigenschaften"].append(
                    {"name": teile[4], "typ": "list", "zaehler": teile[2], "eintrag": teile[3]})
            elif len(teile) == 3 and teile[1] in PLY_TYPEN:
                elemente[-1]["eigenschaften"].append({"name": teile[2], "typ": teile[1]})
            else:
                raise KontextNetzError(f"{p.name!r}: Eigenschaft nicht lesbar: {zeile!r}.")
    if form not in ("binary_little_endian", "binary_big_endian", "ascii"):
        raise KontextNetzError(f"{p.name!r}: PLY-Format {form!r} unbekannt.")
    return {"format": form, "elemente": elemente, "kopf_bytes": kopf_bytes}


def _element(kopf: dict, name: str) -> dict | None:
    return next((e for e in kopf.get("elemente", ()) if e["name"] == name), None)


def ist_netz(kopf: dict) -> bool:
    """Trägt diese PLY Flächen (``element face`` mit mindestens einer)?

    Daran — und nur daran — erkennt die Blender-Stufe, ob die Kontextdatei ein **Netz** ist
    (laden wie ein Objekt) oder ein Splat (Kugel-Notlösung). Ein Splat hat nie Flächen.
    """
    flaeche = _element(kopf, "face")
    return bool(flaeche and flaeche["anzahl"] > 0)


def art_der_datei(pfad) -> str:
    """``"netz"``, ``"splat"`` oder ``"punkte"`` — was in einer PLY steht.

    Ein Splat ist eine Punktwolke mit Deckkraft und Skala je Punkt (3DGS); eine gewöhnliche
    Punktwolke hat keine von beiden.
    """
    kopf = lies_ply_kopf(pfad)
    if ist_netz(kopf):
        return "netz"
    ecken = _element(kopf, "vertex")
    namen = {e["name"] for e in (ecken or {}).get("eigenschaften", ())}
    if {"opacity", "scale_0", "scale_1", "scale_2"} <= namen:
        return "splat"
    return "punkte"


def sh_grad(n_f_rest: int) -> int:
    """Der SH-Grad aus der Zahl der ``f_rest_*``-Spalten.

    Je Farbkanal hat Grad ``d`` insgesamt ``(d + 1)²`` Koeffizienten, einer davon ist
    ``f_dc``. Die übrigen stehen als ``f_rest`` da, drei Kanäle: ``3 · ((d + 1)² − 1)`` —
    0, 9, 24, 45 für die Grade 0 bis 3.

    Raises:
        KontextNetzError: Die Zahl passt zu keinem Grad. Geraten wird nicht — ein falscher
            Grad liest die Farben aus den falschen Spalten.
    """
    n = int(n_f_rest)
    for grad in range(0, 5):
        if 3 * ((grad + 1) ** 2 - 1) == n:
            return grad
    raise KontextNetzError(
        f"{n} f_rest-Spalten passen zu keinem SH-Grad (erwartet 0, 9, 24, 45 oder 72).")


def sh_grad_aus_kopf(kopf: dict) -> int:
    ecken = _element(kopf, "vertex") or {"eigenschaften": []}
    return sh_grad(sum(1 for e in ecken["eigenschaften"] if e["name"].startswith("f_rest_")))


def schreibe_netz_ply(pfad, ecken, farben, dreiecke) -> dict:
    """Ein farbiges Dreiecksnetz als binäre PLY schreiben — dieselbe Form, die Open3D schreibt.

    Gebraucht von den Proben (ein synthetisches Netz für die Blender-Stufe) und als Beleg,
    welche Form die Blender-Stufe erwartet: ``x y z`` als float, ``red green blue`` als
    uchar, Flächen als Liste ``uchar``/``int``.

    Args:
        ecken: ``[(x, y, z), …]``.
        farben: ``[(r, g, b), …]`` als 0..255.
        dreiecke: ``[(i, j, k), …]``.
    """
    if len(ecken) != len(farben):
        raise KontextNetzError(f"{len(ecken)} Ecken, aber {len(farben)} Farben.")
    n = len(ecken)
    for d in dreiecke:
        if len(d) != 3 or not all(0 <= int(i) < n for i in d):
            raise KontextNetzError(f"Dreieck {d!r} zeigt auf keine Ecke.")
    kopf = ("ply\nformat binary_little_endian 1.0\n"
            "comment Visbox kontext_netz (synthetisch oder Splat-Bruecke)\n"
            f"element vertex {n}\nproperty float x\nproperty float y\nproperty float z\n"
            "property uchar red\nproperty uchar green\nproperty uchar blue\n"
            f"element face {len(dreiecke)}\nproperty list uchar int vertex_indices\n"
            "end_header\n").encode("ascii")
    p = Path(pfad)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as datei:
        datei.write(kopf)
        for (x, y, z), (r, g, b) in zip(ecken, farben):
            datei.write(struct.pack("<fffBBB", float(x), float(y), float(z),
                                    int(r), int(g), int(b)))
        for i, j, k in dreiecke:
            datei.write(struct.pack("<Biii", 3, int(i), int(j), int(k)))
    return {"ecken": n, "dreiecke": len(dreiecke)}


def netz_kennzahlen(pfad) -> dict:
    """Name, Grösse, sha256 und Ecken/Dreiecke eines Netzes — **ohne Pfad** (Regel 3).

    Raises:
        KontextNetzError: Datei fehlt, ist leer oder trägt keine Flächen.
    """
    p = Path(pfad)
    if not p.is_file() or p.stat().st_size == 0:
        raise KontextNetzError(f"Netz {p.name!r} fehlt oder ist leer.")
    kopf = lies_ply_kopf(p)
    if not ist_netz(kopf):
        raise KontextNetzError(f"{p.name!r} trägt keine Flächen — das ist kein Netz.")
    summe = hashlib.sha256()
    with open(p, "rb") as datei:
        for stueck in iter(lambda: datei.read(1 << 20), b""):
            summe.update(stueck)
    return {"datei": p.name, "bytes": p.stat().st_size, "sha256": summe.hexdigest(),
            "ecken": (_element(kopf, "vertex") or {"anzahl": 0})["anzahl"],
            "dreiecke": _element(kopf, "face")["anzahl"]}


# ======================================================================================
# Vektoren, Drehung, Lage
# ======================================================================================

def _punkt(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _kreuz(a, b) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _einheit(v) -> tuple[float, float, float]:
    laenge = math.sqrt(_punkt(v, v))
    if not laenge > 1e-12 or not math.isfinite(laenge):
        raise KontextNetzError(f"Der Vektor {tuple(v)!r} hat keine Richtung.")
    return (v[0] / laenge, v[1] / laenge, v[2] / laenge)


def quaternion_zu_matrix(w, x, y, z) -> tuple[tuple[float, ...], ...]:
    """Eine Drehung als Quaternion ``(w, x, y, z)`` → 3×3-Matrix, zeilenweise.

    So steht sie im 3DGS-PLY: ``rot_0`` ist ``w``. Normiert wird vorher — die Trainings-
    programme speichern die Quaternion **unnormiert**, und gsplat normiert ebenso.

    Raises:
        KontextNetzError: Die Quaternion ist null oder nicht endlich.
    """
    q = (float(w), float(x), float(y), float(z))
    laenge = math.sqrt(sum(k * k for k in q))
    if not laenge > 1e-12 or not math.isfinite(laenge):
        raise KontextNetzError(f"Die Quaternion {q!r} beschreibt keine Drehung.")
    w, x, y, z = (k / laenge for k in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
            (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
            (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))


def oben_und_massstab(matrix=None) -> tuple[tuple[float, float, float], float]:
    """Wo im Splat **oben** ist und welcher **Massstab** gilt — aus der Verortungsmatrix.

    Die Matrix (16 Zahlen zeilenweise, geprüft von ``kontext.pruefe_matrix``) bildet den
    Splat in die glTF-Welt ab, in der **Y oben** ist. Oben im Splat ist darum die Richtung,
    die die Matrix auf Y abbildet: ``A⁻¹ · (0, 1, 0)``, normiert. Der Massstab ist
    ``|det A|^(1/3)`` wie in ``kontext.matrix_massstab``: Ein Meter der Welt sind
    ``1 / massstab`` Einheiten des Splats.

    Ohne Matrix gilt die Einheit: oben ist ``(0, 1, 0)``, der Massstab 1.

    Raises:
        KontextNetzError: nicht 16 Zahlen oder ein entarteter Drehteil.
    """
    if matrix is None:
        return (0.0, 1.0, 0.0), 1.0
    m = [float(w) for w in matrix]
    if len(m) != 16 or not all(math.isfinite(w) for w in m):
        raise KontextNetzError(f"Die Matrix hat {len(m)} Zahlen oder nicht endliche Werte.")
    a = (m[0:3], m[4:7], m[8:11])
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
           - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    if abs(det) < 1e-12:
        raise KontextNetzError("Der Drehteil der Matrix ist entartet (Determinante null).")
    # Zweite Spalte der Inversen = A⁻¹ · e_y, über die Adjunkte.
    spalte = ((a[0][2] * a[2][1] - a[0][1] * a[2][2]) / det,
              (a[0][0] * a[2][2] - a[0][2] * a[2][0]) / det,
              (a[0][1] * a[2][0] - a[0][0] * a[2][1]) / det)
    return _einheit(spalte), abs(det) ** (1.0 / 3.0)


def _basis(oben) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Zwei waagrechte Einheitsvektoren senkrecht zu ``oben`` — fest gewählt, damit zwei
    Läufe dieselben Blickwinkel bekommen."""
    o = _einheit(oben)
    achsen = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    e = min(achsen, key=lambda a: abs(_punkt(a, o)))
    s = _punkt(e, o)
    u1 = _einheit((e[0] - s * o[0], e[1] - s * o[1], e[2] - s * o[2]))
    u2 = _kreuz(o, u1)
    return u1, u2


def _perzentil(sortiert: list[float], anteil: float) -> float:
    if not sortiert:
        raise KontextNetzError("Keine Werte für ein Perzentil.")
    lage = anteil * (len(sortiert) - 1)
    unten = int(math.floor(lage))
    oben = min(unten + 1, len(sortiert) - 1)
    return sortiert[unten] + (sortiert[oben] - sortiert[unten]) * (lage - unten)


def dichter_bereich(punkte, *, oben=(0.0, 1.0, 0.0)) -> dict:
    """Mitte, Boden, Höhe und Halbmesser der **dichten** Punkte — robust über Perzentile.

    Args:
        punkte: ``[(x, y, z), …]`` — die Mittelpunkte der dichten Gaussians (der Runner
            reicht eine Stichprobe; die Perzentile brauchen nicht alle).
        oben: die Hochrichtung im Splat (:func:`oben_und_massstab`).

    Returns:
        ``{mitte, boden, decke, halbmesser, n}``: ``mitte`` ist der Median je Achse (Splat-
        Koordinaten), ``boden``/``decke`` das untere/obere Perzentil **entlang oben**,
        ``halbmesser`` das obere Perzentil des waagrechten Abstands zur Mitte.
    """
    liste = [tuple(float(k) for k in p) for p in punkte]
    if len(liste) < 4:
        raise KontextNetzError(f"Nur {len(liste)} dichte Punkte — zu wenig für Blickwinkel.")
    o = _einheit(oben)
    mitte = tuple(_perzentil(sorted(p[i] for p in liste), 0.5) for i in range(3))
    hoehen = sorted(_punkt(p, o) for p in liste)
    mitte_hoehe = _punkt(mitte, o)
    abstaende = []
    for p in liste:
        d = (p[0] - mitte[0], p[1] - mitte[1], p[2] - mitte[2])
        s = _punkt(d, o)
        abstaende.append(math.sqrt(max(0.0, _punkt(d, d) - s * s)))
    abstaende.sort()
    return {"mitte": mitte, "boden": _perzentil(hoehen, ANTEIL_UNTEN),
            "decke": _perzentil(hoehen, ANTEIL_OBEN), "mitte_hoehe": mitte_hoehe,
            "halbmesser": max(_perzentil(abstaende, ANTEIL_OBEN), 1e-6), "n": len(liste)}


def ansicht_matrix(auge, ziel, oben=(0.0, 1.0, 0.0)) -> tuple[float, ...]:
    """Welt → Kamera als 4×4, zeilenweise — Konvention von gsplat und Open3D (wie OpenCV).

    Kamera-``z`` zeigt zum Ziel, ``x`` nach rechts, ``y`` nach unten.

    Raises:
        KontextNetzError: Auge gleich Ziel, oder Blick genau entlang ``oben``.
    """
    vorn = _einheit((ziel[0] - auge[0], ziel[1] - auge[1], ziel[2] - auge[2]))
    rechts = _kreuz(vorn, _einheit(oben))
    if math.sqrt(_punkt(rechts, rechts)) < 1e-9:
        raise KontextNetzError("Der Blick geht genau nach oben oder unten — rechts ist "
                               "dann unbestimmt.")
    rechts = _einheit(rechts)
    unten = _kreuz(vorn, rechts)
    zeilen = (rechts, unten, vorn)
    t = tuple(-_punkt(z, auge) for z in zeilen)
    return (*zeilen[0], t[0], *zeilen[1], t[1], *zeilen[2], t[2], 0.0, 0.0, 0.0, 1.0)


def bildhoehe(breite: int) -> int:
    """Die Bildhöhe zur Breite: drei Viertel, gerade."""
    return max(2, int(round(int(breite) * 0.75 / 2.0)) * 2)


def intrinsik(breite: int, hoehe: int, sichtfeld_grad: float = SICHTFELD_GRAD) -> dict:
    """Die Lochkamera: Brennweite in Bildpunkten und Bildmitte, quadratische Pixel.

    ``fx = (breite / 2) / tan(sichtfeld / 2)`` mit dem **waagrechten** Sichtfeld.

    Raises:
        KontextNetzError: Masse nicht positiv oder Sichtfeld ausserhalb von (0°, 170°).
    """
    b, h = int(breite), int(hoehe)
    if b <= 0 or h <= 0:
        raise KontextNetzError(f"Bildmasse {b}×{h} sind nicht positiv.")
    if not 0.0 < float(sichtfeld_grad) < 170.0:
        raise KontextNetzError(f"Sichtfeld {sichtfeld_grad}° ausserhalb von (0°, 170°).")
    fx = (b / 2.0) / math.tan(math.radians(float(sichtfeld_grad)) / 2.0)
    cx, cy = b / 2.0, h / 2.0
    return {"breite": b, "hoehe": h, "fx": fx, "fy": fx, "cx": cx, "cy": cy,
            "K": (fx, 0.0, cx, 0.0, fx, cy, 0.0, 0.0, 1.0)}


def blickwinkel(bereich: dict, *, oben=(0.0, 1.0, 0.0), massstab: float = 1.0,
                je_kreis: int = BLICKWINKEL_JE_KREIS) -> list[dict]:
    """Die Blickwinkel, aus denen der Splat gerendert wird.

    **Ring** (die Umgebung ist meist von innen aufgenommen, vom Gehweg): im waagrechten
    Zentrum der dichten Punkte, auf :data:`AUGENHOEHE_M` über dem Boden, ``je_kreis``
    Richtungen nach aussen, je in den :data:`RING_NEIGUNGEN_GRAD`.

    **Umlauf** von aussen nach innen: ``je_kreis`` Kameras im Abstand
    ``UMLAUF_ABSTAND_FAKTOR × halbmesser`` um denselben Punkt, um
    :data:`UMLAUF_ERHEBUNG_GRAD` erhöht, auf ihn gerichtet.

    Args:
        bereich: :func:`dichter_bereich`.
        oben, massstab: :func:`oben_und_massstab` — die Augenhöhe gilt in Metern der Welt.
        je_kreis: Azimute je Kreis.

    Returns:
        ``[{art, azimut_grad, neigung_grad, auge, ziel}, …]`` — erst der Ring, dann der
        Umlauf; in Splat-Koordinaten.
    """
    n = int(je_kreis)
    if n < 1:
        raise KontextNetzError(f"je_kreis={je_kreis}: mindestens ein Blickwinkel je Kreis.")
    if not float(massstab) > 0.0:
        raise KontextNetzError(f"massstab={massstab} muss positiv sein.")
    o = _einheit(oben)
    u1, u2 = _basis(o)
    m = bereich["mitte"]
    # Die Mitte auf die Bodenhöhe schieben und dann um die Augenhöhe heben.
    hoehe = float(bereich["boden"]) + AUGENHOEHE_M / float(massstab)
    verschub = hoehe - _punkt(m, o)
    auge_ring = (m[0] + verschub * o[0], m[1] + verschub * o[1], m[2] + verschub * o[2])

    def richtung(az_grad, neig_grad):
        a, e = math.radians(az_grad), math.radians(neig_grad)
        return tuple(math.cos(e) * (math.cos(a) * u1[i] + math.sin(a) * u2[i])
                     + math.sin(e) * o[i] for i in range(3))

    ansichten: list[dict] = []
    for k in range(n):
        az = 360.0 * k / n
        for neigung in RING_NEIGUNGEN_GRAD:
            r = richtung(az, neigung)
            ansichten.append({"art": "ring", "azimut_grad": az, "neigung_grad": neigung,
                              "auge": auge_ring,
                              "ziel": tuple(auge_ring[i] + r[i] for i in range(3))})
    abstand = UMLAUF_ABSTAND_FAKTOR * float(bereich["halbmesser"])
    for k in range(n):
        # Um einen halben Schritt versetzt: Ring und Umlauf blicken nicht genau gleich.
        az = 360.0 * (k + 0.5) / n
        r = richtung(az, UMLAUF_ERHEBUNG_GRAD)
        auge = tuple(auge_ring[i] + abstand * r[i] for i in range(3))
        ansichten.append({"art": "umlauf", "azimut_grad": az,
                          "neigung_grad": -UMLAUF_ERHEBUNG_GRAD, "auge": auge,
                          "ziel": auge_ring})
    return ansichten


def netz_parameter(*, aufloesung: int = AUFLOESUNG_PX, je_kreis: int = BLICKWINKEL_JE_KREIS,
                   voxel_m: float = VOXEL_M, oben=(0.0, 1.0, 0.0), massstab: float = 1.0,
                   renderer: str = "gsplat") -> dict:
    """Alles, was das Netz bestimmt, als eine Tabelle — für Speicherschlüssel und Bericht.

    Die gesetzten Konstanten stehen mit darin: Wer eine davon ändert, bekommt einen anderen
    Schlüssel, ohne :data:`FASSUNG` hochzählen zu müssen.

    Raises:
        KontextNetzError: Auflösung, Blickwinkel oder Voxel nicht positiv.
    """
    if int(aufloesung) < 16:
        raise KontextNetzError(f"aufloesung={aufloesung}: mindestens 16 Bildpunkte breit.")
    if int(je_kreis) < 1:
        raise KontextNetzError(f"blickwinkel={je_kreis}: mindestens einer je Kreis.")
    if not (math.isfinite(float(voxel_m)) and float(voxel_m) > 0.0):
        raise KontextNetzError(f"voxel_m={voxel_m}: muss positiv sein.")
    o = _einheit(oben)
    return {
        "fassung": FASSUNG,
        "renderer": str(renderer),
        "aufloesung": int(aufloesung),
        "hoehe": bildhoehe(aufloesung),
        "blickwinkel_je_kreis": int(je_kreis),
        "voxel_m": float(voxel_m),
        "oben": [round(k, 9) + 0.0 for k in o],
        "massstab": round(float(massstab), 12),
        "gesetzt": {
            "augenhoehe_m": AUGENHOEHE_M, "ring_neigungen_grad": list(RING_NEIGUNGEN_GRAD),
            "umlauf_abstand_faktor": UMLAUF_ABSTAND_FAKTOR,
            "umlauf_erhebung_grad": UMLAUF_ERHEBUNG_GRAD, "sichtfeld_grad": SICHTFELD_GRAD,
            "sdf_trunc_voxel": SDF_TRUNC_VOXEL, "gewicht_min": GEWICHT_MIN,
            "tiefe_max_faktor": TIEFE_MAX_FAKTOR,
            "deckkraft_leer": DECKKRAFT_LEER, "deckkraft_dicht": DECKKRAFT_DICHT,
            "insel_min_dreiecke": INSEL_MIN_DREIECKE, "ziel_dreiecke": ZIEL_DREIECKE,
            "aufnahme_blicke_max": AUFNAHME_BLICKE_MAX,
            "gleich_median_max": GLEICH_MEDIAN_MAX, "gleich_p90_max": GLEICH_P90_MAX,
            "kameras_innen_min": KAMERAS_INNEN_MIN, "huelle_rand": HUELLE_RAND,
            "bloecke_max": BLOECKE_MAX,
        },
    }


# ======================================================================================
# Die Aufnahme lesen — COLMAP, mit der Standardbibliothek (13.10.2026)
# ======================================================================================
#
# **Warum ein eigener Leser und nicht pycolmap** (13.10.2026): pycolmap selbst steht unter
# BSD-3-Clause, COLMAP ebenso. Aber das Rad auf PyPI (4.2.1, hier geprüft) bindet SuiteSparse
# **statisch** ein, samt CHOLMOD/Supernodal, CHOLMOD/MatrixOps und SPQR — diese Module stehen
# unter **GPL-2.0+**. Das COPYING von COLMAP sagt es selbst: «Building COLMAP with these
# dependencies may affect the resulting COLMAP license.» Eine Bibliothek, die der Runner
# importiert, ist kein eigenständiges Programm wie Blender; Regel 1 lässt sie nicht zu.
# Gebraucht wird ohnehin nur das Lesen von drei einfachen Dateiformaten — und das hier geht
# ohne Abhängigkeit, ist im Produkt-venv prüfbar und dieselbe Fassung, die der Runner über den
# Pfad lädt. pycolmap diente in der Wegwerf-Umgebung nur als Gegenprobe des Formats.
#
# Das Format (COLMAP 4.x, an pycolmap 4.2.1 nachgeprüft): ``images.bin`` trägt je
# **registriertem** Bild die fertige Pose ``cam_from_world`` — auch mit Rig, dort schon aus
# Rig- und Sensorpose zusammengesetzt; nicht registrierte Bilder fehlen. ``frames.bin`` sagt,
# welche Bilder zu einem Augenblick gehören; ``rigs.bin`` braucht es zum Lesen nicht.
# Konvention wie OpenCV und gsplat: x rechts, y unten, z in Blickrichtung — die Pose IST
# die Ansichtsmatrix (:func:`pose_zu_ansicht`).

#: COLMAP-Kameramodelle: Nummer → (Name, Zahl der Parameter, perspektivisch).
#: Perspektivisch heisst: Brennweite und Bildmitte beschreiben eine Lochkamera, die Verzeichnung
#: kommt dazu — für einen **Blickwinkel** zählt sie nicht, gerendert wird ohne. Fischaugen und
#: Panoramen bildet keine Lochkamera ab; sie werden ausgelassen.
COLMAP_MODELLE = {
    0: ("SIMPLE_PINHOLE", 3, True), 1: ("PINHOLE", 4, True), 2: ("SIMPLE_RADIAL", 4, True),
    3: ("RADIAL", 5, True), 4: ("OPENCV", 8, True), 5: ("OPENCV_FISHEYE", 8, False),
    6: ("FULL_OPENCV", 12, True), 7: ("FOV", 5, False), 8: ("SIMPLE_RADIAL_FISHEYE", 4, False),
    9: ("RADIAL_FISHEYE", 5, False), 10: ("THIN_PRISM_FISHEYE", 12, False),
    11: ("RAD_TAN_THIN_PRISM_FISHEYE", 16, False), 12: ("SIMPLE_DIVISION", 4, True),
    13: ("DIVISION", 5, True), 14: ("SIMPLE_FISHEYE", 3, False), 15: ("FISHEYE", 4, False),
    16: ("EUCM", 6, False), 17: ("EQUIRECTANGULAR", 2, False),
}
_MODELL_NACH_NAME = {name: nr for nr, (name, _, _) in COLMAP_MODELLE.items()}

#: Modelle mit EINER Brennweite vorn (``f, cx, cy, …``); alle anderen perspektivischen tragen
#: ``fx, fy, cx, cy, …``.
_EINE_BRENNWEITE = {0, 2, 3, 8, 9, 12, 14}

#: Sensortyp «Kamera» in ``frames.bin`` (COLMAP: INVALID −1, CAMERA 0, IMU 1).
_SENSOR_KAMERA = 0


def _datei(ordner: Path, stamm: str) -> Path | None:
    for endung in (".bin", ".txt"):
        p = ordner / (stamm + endung)
        if p.is_file():
            return p
    return None


def ist_aufnahme_ordner(ordner) -> bool:
    """Liegt hier eine COLMAP-Rekonstruktion — ``images`` **und** ``cameras``, binär oder Text?"""
    o = Path(ordner)
    return o.is_dir() and _datei(o, "images") is not None and _datei(o, "cameras") is not None


def aufnahme_kandidaten(ply) -> list[Path]:
    """Wo neben einem Splat seine Aufnahme gesucht wird — in dieser Reihenfolge.

    ``<ordner>/sparse/0`` (so legt COLMAP es an, der Splat daneben),
    ``<ordner>/../sparse/0`` (der Splat in einem Unterordner wie ``exports/``), und
    ``<stamm>.colmap/`` (eine Aufnahme, die eigens zum Splat abgelegt wurde).
    """
    p = Path(ply)
    return [p.parent / "sparse" / "0", p.parent.parent / "sparse" / "0",
            p.parent / (p.stem + ".colmap")]


def aufnahme_fingerabdruck(ordner) -> dict:
    """sha256 der Dateien, die die Blickwinkel bestimmen (:data:`AUFNAHME_DATEIEN`) — ohne Pfad.

    Steht im Speicherschlüssel des Netzes: Eine andere Aufnahme ergibt ein anderes Netz.

    Raises:
        KontextNetzError: ``images`` fehlt.
    """
    o = Path(ordner)
    dateien: dict[str, str] = {}
    for stamm in AUFNAHME_DATEIEN:
        p = _datei(o, stamm)
        if p is None:
            continue
        summe = hashlib.sha256()
        with open(p, "rb") as datei:
            for stueck in iter(lambda: datei.read(1 << 20), b""):
                summe.update(stueck)
        dateien[p.name] = summe.hexdigest()
    if not any(n.startswith("images.") for n in dateien):
        raise KontextNetzError("Keine COLMAP-Aufnahme: images.bin/images.txt fehlt.")
    gesamt = hashlib.sha256("\n".join(f"{n} {h}" for n, h in sorted(dateien.items()))
                            .encode("ascii")).hexdigest()
    return {"dateien": dateien, "sha256": gesamt}


class _Leser:
    """Liest ein COLMAP-Binärformat Stück für Stück (little endian), ohne die Datei ganz zu
    laden — ``images.bin`` trägt alle 2D-Punkte und wird am echten Splat leicht 100 MB gross."""

    def __init__(self, datei):
        self.datei = datei

    def lies(self, form: str):
        groesse = struct.calcsize("<" + form)
        roh = self.datei.read(groesse)
        if len(roh) != groesse:
            raise KontextNetzError("COLMAP-Datei endet mitten in einem Eintrag.")
        return struct.unpack("<" + form, roh)

    def ueberspringe(self, n_bytes: int) -> None:
        self.datei.seek(n_bytes, 1)

    def name(self) -> str:
        teile = bytearray()
        while True:
            z = self.datei.read(1)
            if not z:
                raise KontextNetzError("COLMAP-Datei endet in einem Bildnamen.")
            if z == b"\x00":
                return teile.decode("utf-8", errors="replace")
            teile += z


def _textzeilen(p: Path) -> list[str]:
    return [z.rstrip("\r\n") for z in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if not z.startswith("#")]


def _kamera(nr: int, modell: int, breite: int, hoehe: int, params) -> dict:
    if modell not in COLMAP_MODELLE:
        raise KontextNetzError(f"Kamera {nr}: COLMAP-Modell {modell} unbekannt.")
    name, n, perspektivisch = COLMAP_MODELLE[modell]
    if len(params) != n:
        raise KontextNetzError(f"Kamera {nr} ({name}): {len(params)} statt {n} Parameter.")
    if n < 3:                                   # Panorama: keine Brennweite
        fx = fy = cx = cy = float("nan")
    elif modell in _EINE_BRENNWEITE:
        fx = fy = params[0]
        cx, cy = params[1], params[2]
    else:
        fx, fy, cx, cy = params[:4]
    return {"modell": name, "perspektivisch": perspektivisch, "breite": int(breite),
            "hoehe": int(hoehe), "fx": float(fx), "fy": float(fy), "cx": float(cx),
            "cy": float(cy)}


def _lies_kameras(p: Path) -> dict[int, dict]:
    kameras: dict[int, dict] = {}
    if p.suffix == ".bin":
        with open(p, "rb") as datei:
            le = _Leser(datei)
            (n,) = le.lies("Q")
            for _ in range(n):
                nr, modell, breite, hoehe = le.lies("IiQQ")
                if modell not in COLMAP_MODELLE:
                    raise KontextNetzError(f"Kamera {nr}: COLMAP-Modell {modell} unbekannt — "
                                           "ohne seine Parameterzahl ist die Datei nicht lesbar.")
                params = le.lies("d" * COLMAP_MODELLE[modell][1])
                kameras[nr] = _kamera(nr, modell, breite, hoehe, params)
        return kameras
    for zeile in _textzeilen(p):
        t = zeile.split()
        if not t:
            continue
        if t[1] not in _MODELL_NACH_NAME:
            raise KontextNetzError(f"Kamera {t[0]}: COLMAP-Modell {t[1]!r} unbekannt.")
        kameras[int(t[0])] = _kamera(int(t[0]), _MODELL_NACH_NAME[t[1]], int(t[2]), int(t[3]),
                                     [float(w) for w in t[4:]])
    return kameras


def _lies_bilder(p: Path) -> dict[int, dict]:
    bilder: dict[int, dict] = {}
    if p.suffix == ".bin":
        with open(p, "rb") as datei:
            le = _Leser(datei)
            (n,) = le.lies("Q")
            for _ in range(n):
                nr, qw, qx, qy, qz, tx, ty, tz, kamera = le.lies("I4d3dI")
                name = le.name()
                (n2d,) = le.lies("Q")
                le.ueberspringe(24 * n2d)        # x, y (double), point3D_id (uint64)
                bilder[nr] = {"name": name, "kamera": kamera, "q": (qw, qx, qy, qz),
                              "t": (tx, ty, tz)}
        return bilder
    zeilen = _textzeilen(p)
    for i in range(0, len(zeilen), 2):           # zwei Zeilen je Bild; die zweite darf leer sein
        t = zeilen[i].split()
        if not t:
            continue
        if len(t) < 10:
            raise KontextNetzError(f"images.txt: Zeile {zeilen[i][:60]!r} ist kein Bild.")
        bilder[int(t[0])] = {"name": " ".join(t[9:]), "kamera": int(t[8]),
                             "q": tuple(float(w) for w in t[1:5]),
                             "t": tuple(float(w) for w in t[5:8])}
    return bilder


def _lies_augenblicke(p: Path) -> dict[int, list[int]]:
    augenblicke: dict[int, list[int]] = {}
    if p.suffix == ".bin":
        with open(p, "rb") as datei:
            le = _Leser(datei)
            (n,) = le.lies("Q")
            for _ in range(n):
                nr, _rig = le.lies("II")
                le.ueberspringe(7 * 8)           # rig_from_world — die Bildpose steht schon da
                (n_daten,) = le.lies("I")
                ids = []
                for _ in range(n_daten):
                    typ, _sensor, daten = le.lies("iIQ")
                    if typ == _SENSOR_KAMERA:
                        ids.append(int(daten))
                augenblicke[nr] = ids
        return augenblicke
    for zeile in _textzeilen(p):
        t = zeile.split()
        if not t:
            continue
        n_daten = int(t[9])
        rest = t[10:]
        augenblicke[int(t[0])] = [int(rest[3 * k + 2]) for k in range(n_daten)
                                  if rest[3 * k] == "CAMERA"]
    return augenblicke


def lies_aufnahme(ordner) -> dict:
    """Eine COLMAP-Rekonstruktion (``sparse/0``) lesen: Kameras, Posen, Augenblicke.

    Returns:
        ``{format, kameras, bilder, augenblicke, rig}`` — ``kameras`` je Nummer
        ``{modell, perspektivisch, breite, hoehe, fx, fy, cx, cy}``; ``bilder`` je Nummer
        ``{name, kamera, q (w, x, y, z), t}`` als ``cam_from_world``; ``augenblicke`` eine
        Liste von Bildnummern-Listen in der Reihenfolge der Aufnahme (nach Augenblick, darin
        nach Kamera). Ohne ``frames`` (COLMAP 3) ist jedes Bild sein eigener Augenblick,
        nach Namen geordnet.

    Raises:
        KontextNetzError: kein Aufnahme-Ordner, unlesbare Datei, kein registriertes Bild.
    """
    o = Path(ordner)
    if not ist_aufnahme_ordner(o):
        raise KontextNetzError("Keine COLMAP-Aufnahme: images und cameras (.bin/.txt) fehlen.")
    p_bilder = _datei(o, "images")
    # Dieselbe Form für alle: COLMAP schreibt einen Satz ganz binär oder ganz als Text.
    endung = p_bilder.suffix
    p_kameras = o / ("cameras" + endung)
    p_rahmen = o / ("frames" + endung)
    if not p_kameras.is_file():
        raise KontextNetzError(f"images{endung} ohne cameras{endung}.")
    try:
        kameras = _lies_kameras(p_kameras)
        bilder = _lies_bilder(p_bilder)
        rahmen = _lies_augenblicke(p_rahmen) if p_rahmen.is_file() else None
    except (struct.error, ValueError, IndexError, OSError) as fehler:
        raise KontextNetzError(f"COLMAP-Aufnahme nicht lesbar: {type(fehler).__name__}: "
                               f"{fehler}") from fehler
    if not bilder:
        raise KontextNetzError("Die COLMAP-Aufnahme hat kein registriertes Bild.")
    fremd = sorted({b["kamera"] for b in bilder.values()} - set(kameras))
    if fremd:
        raise KontextNetzError(f"Bilder verweisen auf unbekannte Kameras {fremd[:5]}.")
    if rahmen:
        augenblicke = []
        for nr in sorted(rahmen):
            ids = sorted((i for i in rahmen[nr] if i in bilder),
                         key=lambda i: (bilder[i]["kamera"], i))
            if ids:                              # nicht registrierte Augenblicke fehlen
                augenblicke.append(ids)
    else:
        augenblicke = [[i] for i in sorted(bilder, key=lambda i: (bilder[i]["name"], i))]
    return {"format": endung.lstrip("."), "kameras": kameras, "bilder": bilder,
            "augenblicke": augenblicke, "rig": bool(rahmen)}


def lies_punkte3d(ordner, hoechstens: int = 20000) -> list[tuple[float, float, float]]:
    """Eine gleichmässige Stichprobe der COLMAP-Punkte (``points3D``) — höchstens ``hoechstens``.

    Für die Gleichheitsprüfung Aufnahme ↔ Splat (:func:`gleichheit_befund`). Fehlt die Datei,
    ist die Liste leer.

    Raises:
        KontextNetzError: Die Datei ist da, aber nicht lesbar.
    """
    o = Path(ordner)
    p = _datei(o, "points3D")
    if p is None:
        return []
    k = max(1, int(hoechstens))
    punkte: list[tuple[float, float, float]] = []
    try:
        if p.suffix == ".bin":
            with open(p, "rb") as datei:
                le = _Leser(datei)
                (n,) = le.lies("Q")
                schritt = max(1, -(-n // k))
                for i in range(n):
                    _nr, x, y, z, _r, _g, _b, _fehler, n_spur = le.lies("Q3d3BdQ")
                    le.ueberspringe(8 * n_spur)    # image_id, point2D_idx (je uint32)
                    if i % schritt == 0:
                        punkte.append((x, y, z))
        else:
            zeilen = [z.split() for z in _textzeilen(p) if z.strip()]
            schritt = max(1, -(-len(zeilen) // k))
            punkte = [(float(t[1]), float(t[2]), float(t[3])) for t in zeilen[::schritt]]
    except (struct.error, ValueError, IndexError, OSError) as fehler:
        raise KontextNetzError(f"points3D nicht lesbar: {type(fehler).__name__}: "
                               f"{fehler}") from fehler
    return punkte[:k]


# --------------------------------------------------------------------------------------
# Aus der Aufnahme Blickwinkel machen
# --------------------------------------------------------------------------------------

def pose_zu_ansicht(q, t) -> tuple[float, ...]:
    """COLMAP ``cam_from_world`` (Quaternion ``w, x, y, z`` und Verschiebung) → Ansichtsmatrix.

    Dieselbe Konvention wie :func:`ansicht_matrix` (OpenCV: x rechts, y unten, z Blick) — die
    Pose **ist** die Ansichtsmatrix, ohne Umklappen. Eine Probe hält beide gleich.
    """
    r = quaternion_zu_matrix(*q)
    return (*r[0], float(t[0]), *r[1], float(t[1]), *r[2], float(t[2]), 0.0, 0.0, 0.0, 1.0)


def kamerazentrum(q, t) -> tuple[float, float, float]:
    """Wo die Kamera in der Welt steht: ``−Rᵀ · t``."""
    r = quaternion_zu_matrix(*q)
    return tuple(-sum(r[k][i] * float(t[k]) for k in range(3)) for i in range(3))


def intrinsik_skaliert(kamera: dict, breite: int) -> dict:
    """Die Lochkamera einer Aufnahme-Kamera, auf ``breite`` Bildpunkte skaliert.

    Das Seitenverhältnis bleibt das des Bildes (am echten Splat 1086 × 1086, also quadratisch);
    Brennweite und Bildmitte wachsen mit demselben Faktor. Dieselbe Form wie :func:`intrinsik`.

    Raises:
        KontextNetzError: nicht perspektivisch, oder Masse und Brennweite nicht positiv.
    """
    if not kamera.get("perspektivisch"):
        raise KontextNetzError(f"Kameramodell {kamera.get('modell')!r} ist keine Lochkamera.")
    b0, h0 = int(kamera["breite"]), int(kamera["hoehe"])
    if b0 <= 0 or h0 <= 0 or not (kamera["fx"] > 0 and kamera["fy"] > 0) or int(breite) <= 0:
        raise KontextNetzError(f"Kamera {b0}×{h0}, f {kamera['fx']}: nicht positiv.")
    s = int(breite) / b0
    b, h = int(breite), max(2, int(round(h0 * s)))
    fx, fy, cx, cy = (kamera[k] * s for k in ("fx", "fy", "cx", "cy"))
    return {"breite": b, "hoehe": h, "fx": fx, "fy": fy, "cx": cx, "cy": cy,
            "K": (fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0), "faktor": s}


def waehle_augenblicke(n: int, hoechstens: int) -> list[int]:
    """``hoechstens`` Augenblicke aus ``n``, gleichmässig über die Aufnahme — mit erstem und letztem.

    Gleichmässig statt zufällig: Zwei Läufe sehen dieselben Bilder, und der Weg der Aufnahme
    wird ohne Lücke abgedeckt.
    """
    n, k = int(n), int(hoechstens)
    if n <= 0 or k <= 0:
        return []
    if k >= n:
        return list(range(n))
    if k == 1:
        return [n // 2]
    return [int(round(i * (n - 1) / (k - 1))) for i in range(k)]


def aufnahme_blickwinkel(aufnahme: dict, *, breite: int = AUFLOESUNG_PX,
                         hoechstens: int = AUFNAHME_BLICKE_MAX) -> tuple[list[dict], dict]:
    """Die Blickwinkel aus einer Aufnahme (:func:`lies_aufnahme`): Pose und Intrinsik je Bild.

    Gewählt werden ganze Augenblicke — **alle Rig-Kameras je gewähltem Augenblick** —, so viele,
    dass höchstens ``hoechstens`` Bilder herauskommen (:func:`waehle_augenblicke`).
    Nicht perspektivische Kameras werden ausgelassen und gezählt.

    Returns:
        ``(ansichten, auswahl)``: ``ansichten`` je ``{art: "aufnahme", bild, kamera, augenblick,
        auge, ansicht, ki}``; ``auswahl`` mit den Zahlen für den Bericht.

    Raises:
        KontextNetzError: Es bleibt kein Blickwinkel.
    """
    augenblicke = aufnahme["augenblicke"]
    je_augenblick = max((len(a) for a in augenblicke), default=1)
    gewaehlt = waehle_augenblicke(len(augenblicke), max(1, int(hoechstens) // je_augenblick))
    ansichten: list[dict] = []
    ausgelassen = 0
    ki_je_kamera: dict[int, dict] = {}
    for nr in gewaehlt:
        for bild in augenblicke[nr]:
            b = aufnahme["bilder"][bild]
            kamera = aufnahme["kameras"][b["kamera"]]
            if not kamera["perspektivisch"]:
                ausgelassen += 1
                continue
            if b["kamera"] not in ki_je_kamera:
                ki_je_kamera[b["kamera"]] = intrinsik_skaliert(kamera, breite)
            ansichten.append({"art": "aufnahme", "bild": bild, "kamera": b["kamera"],
                              "augenblick": nr, "auge": kamerazentrum(b["q"], b["t"]),
                              "ansicht": pose_zu_ansicht(b["q"], b["t"]),
                              "ki": ki_je_kamera[b["kamera"]]})
    if not ansichten:
        raise KontextNetzError("Aus der Aufnahme bleibt kein Blickwinkel (keine Lochkamera).")
    kameras = aufnahme["kameras"]
    return ansichten, {
        "bilder_gesamt": len(aufnahme["bilder"]), "augenblicke_gesamt": len(augenblicke),
        "augenblicke_gewaehlt": len(gewaehlt), "kameras_je_augenblick": je_augenblick,
        "ausgelassen_nicht_perspektivisch": ausgelassen, "rig": aufnahme["rig"],
        "kameramodelle": sorted({kameras[a["kamera"]]["modell"] for a in ansichten}),
        "bildgroessen_aufnahme": sorted([list(g) for g in {
            (kameras[a["kamera"]]["breite"], kameras[a["kamera"]]["hoehe"])
            for a in ansichten}])}


def huelle_erweitert(lo, hi, rand: float = HUELLE_RAND):
    """Eine Box ``(lo, hi)``, je Achse um ``rand`` × Kantenlänge nach aussen geschoben."""
    d = [float(hi[i]) - float(lo[i]) for i in range(3)]
    return (tuple(float(lo[i]) - rand * d[i] for i in range(3)),
            tuple(float(hi[i]) + rand * d[i] for i in range(3)))


def anteil_innen(punkte, lo, hi) -> float:
    """Welcher Anteil der Punkte in der Box liegt (Rand eingeschlossen); 0 ohne Punkte."""
    liste = list(punkte)
    if not liste:
        return 0.0
    drin = sum(1 for p in liste if all(lo[i] <= p[i] <= hi[i] for i in range(3)))
    return drin / len(liste)


def gleichheit_befund(*, median: float | None, p90: float | None, diagonale: float,
                      kameras_innen: float, n_punkte: int, n_kameras: int) -> dict:
    """Liegen Aufnahme und Splat im **selben** Koordinatensystem? Das Urteil aus den Zahlen.

    Die Zahlen misst der Runner (Abstände mit einem Suchbaum, dafür ist die Standardbibliothek
    zu langsam); hier steht nur die Entscheidung — prüfbar ohne torch und Open3D.

    Args:
        median, p90: Abstand der COLMAP-Punkte zur nächsten dichten Splat-Mitte (Einheiten des
            Splats); ``None`` ohne Punkte.
        diagonale: Diagonale des dichten Bereichs (P2–P98), Einheiten des Splats.
        kameras_innen: Anteil der Kamerazentren in der erweiterten Box (:func:`huelle_erweitert`).

    Returns:
        ``{gleich, median_rel, p90_rel, kameras_innen, n_punkte, n_kameras, schwellen, grund}``
        — ``grund`` sagt bei ``gleich=False``, welche Schwelle verfehlt wurde.

    **Ohne COLMAP-Punkte gilt die Aufnahme nicht als gleich** — «nicht prüfbar» ist nicht
    «bestanden»: Eine Kamera an der falschen Stelle sähe ins Leere, und das Netz bliebe leer,
    ohne dass es jemand merkt.

    **Was die Prüfung nicht sieht:** Eine Verschiebung **entlang** der grossen Flächen (eine
    Bodenplatte waagrecht verschoben liegt wieder auf der Bodenebene). Darum zählt auch das
    90-%-Perzentil — Wände und Kanten verschieben sich sichtbar —, und die Kamerazentren.
    """
    diag = float(diagonale)
    schwellen = {"median_rel_max": GLEICH_MEDIAN_MAX, "p90_rel_max": GLEICH_P90_MAX,
                 "kameras_innen_min": KAMERAS_INNEN_MIN, "huelle_rand": HUELLE_RAND}
    aus = {"gleich": False, "median_rel": None, "p90_rel": None,
           "kameras_innen": round(float(kameras_innen), 4), "n_punkte": int(n_punkte),
           "n_kameras": int(n_kameras), "schwellen": schwellen, "grund": None}
    if not (math.isfinite(diag) and diag > 0.0):
        aus["grund"] = "Der dichte Bereich des Splats hat keine Ausdehnung."
        return aus
    if median is None or p90 is None or int(n_punkte) == 0:
        aus["grund"] = ("Die Aufnahme hat keine COLMAP-Punkte (points3D) — ob sie zum Splat "
                        "passt, ist nicht pruefbar.")
        return aus
    aus["median_rel"] = round(float(median) / diag, 6)
    aus["p90_rel"] = round(float(p90) / diag, 6)
    gruende = []
    if aus["median_rel"] > GLEICH_MEDIAN_MAX:
        gruende.append(f"Median-Abstand der COLMAP-Punkte zum Splat {aus['median_rel']:.2%} der "
                       f"Diagonale (hoechstens {GLEICH_MEDIAN_MAX:.0%})")
    if aus["p90_rel"] > GLEICH_P90_MAX:
        gruende.append(f"P90-Abstand {aus['p90_rel']:.2%} der Diagonale "
                       f"(hoechstens {GLEICH_P90_MAX:.0%})")
    if float(kameras_innen) < KAMERAS_INNEN_MIN:
        gruende.append(f"nur {float(kameras_innen):.0%} der Kamerazentren im erweiterten "
                       f"Bereich des Splats (mindestens {KAMERAS_INNEN_MIN:.0%})")
    if gruende:
        aus["grund"] = ("Aufnahme und Splat liegen nicht im selben System: "
                        + "; ".join(gruende) + ".")
    else:
        aus["gleich"] = True
    return aus


def voxel_fuer_bloecke(voxel: float, bloecke: int, hoechstens: int = BLOECKE_MAX) -> float:
    """Der Voxel, mit dem die TSDF unter ``hoechstens`` aktiven Blöcken bleibt.

    Die Blöcke liegen auf Flächen; ihre Zahl wächst mit ``1 / voxel²``. Darüber wird der Voxel
    um die Wurzel des Verhältnisses vergrössert, mit 10 % Luft und mindestens um ein Viertel —
    damit ein zweiter Versuch sicher darunter landet.
    """
    if int(bloecke) <= int(hoechstens):
        return float(voxel)
    return float(voxel) * max(1.25, 1.1 * math.sqrt(int(bloecke) / int(hoechstens)))
