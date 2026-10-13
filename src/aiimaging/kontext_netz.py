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
aus der Verortungsmatrix ableiten. Dieselbe Begründung wie bei :mod:`aiimaging.kontext`: *Was
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
    "AUFLOESUNG_PX", "AUGENHOEHE_M", "BLICKWINKEL_JE_KREIS", "DECKKRAFT_DICHT",
    "DECKKRAFT_LEER", "FASSUNG", "GEWICHT_MIN", "INSEL_MIN_DREIECKE", "KontextNetzError",
    "QUELLE_NETZ", "QUELLE_SPLAT", "RING_NEIGUNGEN_GRAD", "SATZ_KUGELN_GESCHEITERT",
    "SATZ_KUGELN_NICHT_EINGERICHTET", "SDF_TRUNC_VOXEL", "SICHTFELD_GRAD", "TIEFE_MAX_FAKTOR",
    "UMLAUF_ABSTAND_FAKTOR", "UMLAUF_ERHEBUNG_GRAD", "VOXEL_M", "ZIEL_DREIECKE",
    "ansicht_matrix", "art_der_datei", "bildhoehe", "blickwinkel", "dichter_bereich",
    "intrinsik", "ist_netz", "lies_ply_kopf", "netz_kennzahlen", "netz_parameter",
    "oben_und_massstab", "quaternion_zu_matrix", "schreibe_netz_ply", "sh_grad",
    "sh_grad_aus_kopf",
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

#: Kantenlänge eines Voxels der TSDF, in Metern der Welt. GESETZT. 5 cm: fein genug für
#: Bordsteine und Stufen, grob genug, dass ein Strassenraum von 100 m in den Speicher passt.
VOXEL_M = 0.05

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
INSEL_MIN_DREIECKE = 200

#: Hat das Netz mehr Dreiecke, wird es darauf vereinfacht. GESETZT. Blender rendert eine
#: halbe Million Dreiecke ohne Mühe; mehr kostet Ladezeit je Kamera.
ZIEL_DREIECKE = 500_000

#: Anteile für den **robusten** Bereich der dichten Punkte (Perzentile): Ein einzelner
#: Ausreisser in 200 m Höhe soll weder die Mitte noch den Boden bestimmen. GESETZT.
ANTEIL_UNTEN, ANTEIL_OBEN = 0.02, 0.98

#: Der Codestand der Brücke. Hochzählen, wenn bei gleichen Parametern ein anderes Netz
#: entsteht — die Zahl steht im Speicherschlüssel (:func:`netz_parameter`), sonst käme ein
#: altes Netz als Treffer zurück.
FASSUNG = 1

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
        },
    }
