"""GLBBOX — die Hüllbox der gebauten Substanz, aus einer glb, ohne Blender.

Warum dieses Modul existiert
----------------------------
Der Schalter ``--kamera-huellbox`` ist seit dem 26.08.2026 durch die ganze Kette
verdrahtet, und seine Wirkung ist gemessen: Bauwerksanteil im Bild **0,0788 → 0,1730**,
Faktor 2,2 (``abholer.py``, am Aufrufort). Offen war nicht der Schalter, sondern die
**Herkunft der Box**. Drei Wege standen dort mit Preisschild:

* **(a) ein zweiter Blender-Lauf** — der erste liefert ``bbox_bauwerk``, der zweite rahmt
  danach. Rund **+40 s je Kamera**.
* **(b) ein leichter Läufer**, der die glb nur liest — *gab es nicht, geschätzt 1–2 s.*
* **(c) der IFC-Report** — auf dem gemessenen Fall falsch: Sein Typfilter ist
  ``("IfcSite",)``, die Geländeplatte ist ein ``IfcSlab`` namens ``Gelaende``.

Dies ist Weg (b), und die Schätzung war **um mehr als eine Zehnerpotenz zu pessimistisch**:
gemessen an einer echten Bestandsdatei mit 4771 Meshes und 25 MB liegt der ganze Durchgang
bei **0,06 s** (Datei lesen 0,02 s, Boxen rechnen 0,04 s). Das ist nicht die Hälfte von
(a), das ist sein Sechshundertstel.

Warum ohne jede Bibliothek — und warum das kein Geiz ist
--------------------------------------------------------
``pyproject.toml`` führt ``dependencies = []``. Der Kern dieses Projekts hat **keine
einzige Laufzeitabhängigkeit**, und das ist eine Lizenzentscheidung (Regel 1), keine
Sparsamkeit. Der naheliegende Griff wäre ``trimesh`` gewesen — es liegt im ``.venv-ifc``
und kann das. Nur läge dieses Modul dann **jenseits einer Prozessgrenze**, die es gar
nicht braucht, und der Abholer müsste einen Unterprozess starten, um eine Zahl zu
erfahren, die in den ersten drei Megabyte der Datei steht.

Denn das ist der Befund, auf dem alles hier steht: **glTF 2.0 verlangt für jeden
POSITION-Accessor ``min`` und ``max``** (Spezifikation, Abschnitt 3.6.2.1: *„POSITION
accessor **MUST** have its min and max properties defined"*). Die Hüllbox eines Knotens
steht also im **JSON-Kopf** der Datei; die Dreiecke selbst müssen nie angefasst werden.
An der Bestandsdatei nachgezählt: **4771 von 4771** POSITION-Accessors tragen beides.

Was passiert, wenn ein Erzeuger sich nicht daran hält, steht bei :func:`knotenboxen`: Es
gibt **keinen** Rückfall auf eine kleinere Box. Eine zu kleine Bauwerksbox zöge die Kamera
näher heran, als das Bauwerk gross ist — sie schnitte es an, und niemand sähe der Zahl an,
dass sie unvollständig ist.

Die Geländeregel wird geliehen, nicht nachgebaut
------------------------------------------------
Entschieden wird mit :func:`aiimaging.maske.ist_gelaende` — **derselben** Regel, mit der
später die Maske gebaut wird und mit der der Blender-Runner seine ``bbox_bauwerk``
rechnet. Sie steht an genau einer Stelle und wird hier importiert, nicht abgeschrieben.
*Eine Regel an zwei Stellen ist an einer davon bereits falsch.*

.. warning::
   **Gemessen am 01.09.2026 an einer echten Bestandsdatei: Die Namensregel greift dort
   fast nicht** — und das ist der wichtigste Befund dieses Moduls, wichtiger als seine
   Geschwindigkeit.

   Die Datei trägt ihr Gelände nicht als ein Objekt namens „Gelände", sondern als eine
   **Familie von Aussenflächen**: ein ``IfcCovering`` namens ``Toposolid_1``
   (135,50 × 130,12 m Grundfläche — das grösste Einzelobjekt der Szene), dazu
   ``Sub-Division``, ``Umgebung 15 - Gras``, ``Aussen - Gras``, Bäume als
   ``IfcGeographicElement`` und ein Nachbargebäude als ``IfcCivilElement``. Kein einziger
   dieser Namen enthält eines der vier Wörter aus
   :data:`aiimaging.maske.GELAENDE_WOERTER`.

   Was das kostet, in derselben Rechnung wie der Lauf vom 28.08.2026 (Kamera sSE, 1:1)::

       Szenenbox            135,75 × 136,50 × 25,60 m   →  Abstand 358,02 m
       Bauwerksbox (Regel)  135,75 × 130,12 × 25,60 m   →  Abstand 350,33 m   −2,1 %
       nur der Hochbau       94,50 ×  82,75 × 25,60 m   →  Abstand 234,43 m   −34,5 %

   Weg (b) liefert also, was er verspricht, und die Rahmung wird belegbar enger — aber
   **die Regel, die er befragt, sieht dieses Gelände nicht.** Darum führt das Ergebnis
   :func:`bauwerksbox` das Feld ``schrumpfung`` mit: wie viel die Box gegenüber der Szene
   überhaupt verloren hat. Eine Bauwerksbox, die 2 % kleiner ist als die Szene, ist keine
   Bauwerksbox — und ohne diese Zahl sähe sie im Bericht genauso aus wie eine, die trägt.

Abhängigkeiten: keine. Reine stdlib, kein numpy, kein ``bpy`` (Regel 2), aus Python heraus
ohne jede Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import json
import math
import struct
import time
from pathlib import Path

from .maske import ist_gelaende

#: ``glTF`` als vier Bytes, wie es im Dateikopf steht.
GLB_MAGIC = 0x46546C67

#: Kennung des JSON-Blocks (``JSON``) und des Binärblocks (``BIN\0``) einer glb.
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

#: Ab wann eine Bauwerksbox als „hat nicht gegriffen" gemeldet wird.
#:
#: **5 % ist eine Setzung und keine Messung**, und die Unterscheidung ist in diesem Projekt
#: keine Formalie. Belegt ist nur, was die Schwelle einrahmt: Am 28.08.2026 brachte die
#: Regel an einer Bestandsdatei **2,1 %** (wirkungslos), das Gelände dieser Datei richtig
#: erkannt hätte **34,5 %** gebracht, und am Testbau mit Geländeplatte vom 26.08.2026
#: waren es 40 % (0,0788 → 0,1730 Bauwerksanteil, Faktor 2,2). Zwischen 2 und 34 liegt
#: eine Grössenordnung; die Schwelle darf darum grob sein.
GERINGE_SCHRUMPFUNG = 0.05


#: Die Hochachsen, die dieses Modul in Weltkoordinaten umrechnen kann.
#:
#: **``"Z"`` fehlt hier mit Absicht, und die Lücke ist ehrlicher als eine Zahl.** Der
#: Produktivweg erzeugt ausschliesslich Y-up: ``ifc_to_glb_runner`` dreht −90° um X und
#: meldet ``up_axis: "Y"``. Für eine Z-up-Quelle setzt ``seams`` zusätzlich
#: ``--rotiere-z-up``, und was dabei in Blender **wirklich** herauskommt, ist hier nicht
#: gemessen — die Importkonvention und die nachgeschaltete Drehung ergeben je nach
#: Vorzeichen dieselbe Box oder eine um 180° gedrehte, und beide Antworten sähen im
#: Bericht gleich plausibel aus.
#:
#: Dieses Projekt zählt bereits drei unvereinbare Kameraverträge (``kameras`` §Modulkopf).
#: Eine geratene vierte Achsenkonvention danebenzustellen wäre derselbe Fehler noch
#: einmal. Wer Z-up braucht, misst einen Lauf und trägt die Umrechnung hier ein.
HOCHACHSEN = ("Y",)


class GlbError(ValueError):
    """Aus dieser Datei lässt sich keine Hüllbox lesen — und ein Ersatzwert wäre schlimmer.

    Erbt von ``ValueError``, dieselbe Wahl wie ``maske.MaskeError`` und
    ``geometrie_qa.QaError``: Bestehendes ``except ValueError`` greift weiter, und die
    Trennung der Klassen sagt trotzdem, *welche* Naht gerissen ist.
    """


def lies_gltf_json(pfad) -> dict:
    """Den JSON-Kopf einer ``.glb`` (oder einer ``.gltf``) lesen.

    Bei einer ``.glb`` wird **nur der erste Block** gelesen — bei der gemessenen
    Bestandsdatei sind das 2,8 von 25 MB, und die restlichen 22 MB Dreiecke werden nie
    angefasst. Das ist der ganze Grund, warum dieser Weg 0,02 s statt 40 s braucht.

    Raises:
        GlbError: Datei fehlt, Kopf unlesbar, oder der erste Block ist kein JSON.
    """
    p = Path(pfad)
    try:
        roh = p.read_bytes() if p.suffix.lower() == ".gltf" else None
    except OSError as e:
        raise GlbError(f"{p} nicht lesbar: {e}") from e
    if roh is not None:
        try:
            return json.loads(roh)
        except ValueError as e:
            raise GlbError(f"{p} ist kein lesbares glTF-JSON: {e}") from e

    try:
        with p.open("rb") as f:
            kopf = f.read(12)
            if len(kopf) < 12:
                raise GlbError(f"{p} ist mit {len(kopf)} Byte zu kurz für einen glb-Kopf.")
            magic, version, _ = struct.unpack("<III", kopf)
            if magic != GLB_MAGIC:
                raise GlbError(
                    f"{p} beginnt nicht mit der glb-Kennung 'glTF' (gelesen: {magic:#010x}). "
                    "Eine .gltf-Datei im JSON-Format wird an der Endung erkannt — diese "
                    "hier ist weder das eine noch das andere.")
            if version != 2:
                raise GlbError(
                    f"{p} ist glb-Version {version}; gelesen wird nur Version 2. Der "
                    "Vertrag über min/max am POSITION-Accessor, auf dem dieses Modul "
                    "steht, gilt erst ab glTF 2.0.")
            block = f.read(8)
            if len(block) < 8:
                raise GlbError(f"{p} bricht vor dem ersten Block ab.")
            laenge, art = struct.unpack("<II", block)
            if art != CHUNK_JSON:
                raise GlbError(
                    f"{p}: Der erste Block ist {art:#010x} und nicht JSON. Der glb-Vertrag "
                    "verlangt den JSON-Block an erster Stelle.")
            roh_js = f.read(laenge)
    except OSError as e:
        raise GlbError(f"{p} nicht lesbar: {e}") from e
    if len(roh_js) < laenge:
        raise GlbError(f"{p}: JSON-Block angekündigt mit {laenge} Byte, gelesen {len(roh_js)}.")
    try:
        return json.loads(roh_js.decode("utf-8"))
    except ValueError as e:
        raise GlbError(f"{p}: JSON-Block nicht lesbar: {e}") from e


def _mal(a, b):
    """Zwei 4×4-Matrizen als Zeilenlisten multiplizieren."""
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


_EINHEIT = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _knotenmatrix(knoten) -> list[list[float]]:
    """Die lokale Matrix eines glTF-Knotens — aus ``matrix`` oder aus ``T·R·S``.

    glTF speichert ``matrix`` **spaltenweise**; hier wird zeilenweise gerechnet, also
    transponiert eingelesen. Wer das verwechselt, bekommt bei reinen Verschiebungen
    (dem häufigsten Fall) eine Box, die *fast* stimmt — und merkt es nie.
    """
    m = knoten.get("matrix")
    if isinstance(m, (list, tuple)) and len(m) == 16:
        return [[float(m[c * 4 + r]) for c in range(4)] for r in range(4)]

    t = knoten.get("translation") or (0.0, 0.0, 0.0)
    r = knoten.get("rotation") or (0.0, 0.0, 0.0, 1.0)
    s = knoten.get("scale") or (1.0, 1.0, 1.0)
    x, y, z, w = (float(v) for v in r)
    sx, sy, sz = (float(v) for v in s)
    # Quaternion → Drehmatrix, Lehrbuchform. glTF speichert (x, y, z, w), nicht (w, x, y, z).
    dreh = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    skal = (sx, sy, sz)
    return [[dreh[i][j] * skal[j] for j in range(3)] + [float(t[i])] for i in range(3)] + \
           [[0.0, 0.0, 0.0, 1.0]]


def _mesh_grenzen(js: dict, index: int):
    """``(lo, hi)`` eines Meshes aus den POSITION-Accessors, oder ``None``.

    ``None`` heisst: **mindestens ein** Primitiv trägt kein ``min``/``max``. Nicht „das
    Mesh ist leer" — die Unterscheidung trägt der Aufrufer weiter.
    """
    try:
        mesh = js["meshes"][index]
    except (KeyError, IndexError, TypeError):
        return None
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for prim in mesh.get("primitives", []):
        stelle = (prim.get("attributes") or {}).get("POSITION")
        if stelle is None:
            continue
        try:
            acc = js["accessors"][stelle]
        except (KeyError, IndexError, TypeError):
            return None
        mn, mx = acc.get("min"), acc.get("max")
        if not isinstance(mn, (list, tuple)) or not isinstance(mx, (list, tuple)) \
                or len(mn) < 3 or len(mx) < 3:
            return None
        for i in range(3):
            lo[i] = min(lo[i], float(mn[i]))
            hi[i] = max(hi[i], float(mx[i]))
    return (lo, hi) if lo[0] < math.inf else None


def knotenboxen(js: dict) -> dict:
    """Alle Mesh-Knoten einer glTF-Struktur mit Name und Welt-Hüllbox — in glTF-Koordinaten.

    Der Szenengraph wird von den Wurzeln der aktiven Szene aus durchlaufen und die
    Elternmatrizen werden mitgeführt. Die acht Ecken der lokalen Box werden **einzeln**
    transformiert und danach neu eingehüllt; bei einer gedrehten Wand wäre alles andere
    zu klein.

    Returns:
        ``{"knoten": [(name, lo, hi), …], "ohne_grenzen": [name, …], "besucht": n}``.

        ``ohne_grenzen`` sind Knoten, deren Mesh kein ``min``/``max`` trug. Sie sind
        **nicht** in ``knoten`` enthalten, und :func:`bauwerksbox` verweigert daraufhin
        die Auskunft — siehe Modulkopf: eine zu kleine Box zöge die Kamera zu nah heran
        und schnitte das Bauwerk an, ohne dass es der Zahl anzusehen wäre.
    """
    knoten = js.get("nodes") or []
    szenen = js.get("scenes") or []
    nummer = js.get("scene", 0)
    if 0 <= nummer < len(szenen):
        wurzeln = list(szenen[nummer].get("nodes") or [])
    else:
        # Keine Szene benannt: alles nehmen, was kein Kind ist. Ein glTF ohne `scenes`
        # ist zulässig (die Datei ist dann eine Bibliothek von Knoten).
        kinder = {k for n in knoten for k in (n.get("children") or [])}
        wurzeln = [i for i in range(len(knoten)) if i not in kinder]

    gefunden: list[tuple[str, list[float], list[float]]] = []
    ohne: list[str] = []
    besucht = 0
    # Kein rekursiver Abstieg: 4771 Knoten sind harmlos, aber ein glTF mit einer Kette
    # von zehntausend Knoten sprengte die Rekursionsgrenze — und ein Zyklus (unzulässig,
    # aber schreibbar) liefe endlos. Beides fängt der eigene Stapel mit `gesehen`.
    stapel = [(i, _EINHEIT) for i in reversed(wurzeln)]
    gesehen: set[int] = set()
    while stapel:
        index, eltern = stapel.pop()
        if not isinstance(index, int) or not (0 <= index < len(knoten)) or index in gesehen:
            continue
        gesehen.add(index)
        besucht += 1
        n = knoten[index]
        welt = _mal(eltern, _knotenmatrix(n))
        if "mesh" in n:
            grenzen = _mesh_grenzen(js, n["mesh"])
            name = str(n.get("name") or "")
            if grenzen is None:
                ohne.append(name)
            else:
                lo, hi = grenzen
                elo = [math.inf] * 3
                ehi = [-math.inf] * 3
                for bx in (lo[0], hi[0]):
                    for by in (lo[1], hi[1]):
                        for bz in (lo[2], hi[2]):
                            for i in range(3):
                                v = (welt[i][0] * bx + welt[i][1] * by
                                     + welt[i][2] * bz + welt[i][3])
                                elo[i] = min(elo[i], v)
                                ehi[i] = max(ehi[i], v)
                gefunden.append((name, elo, ehi))
        for kind in reversed(n.get("children") or []):
            stapel.append((kind, welt))
    return {"knoten": gefunden, "ohne_grenzen": ohne, "besucht": besucht}


def nach_welt(lo, hi, up_axis: str = "Y"):
    """glTF-Koordinaten → Weltkoordinaten (Z oben), wie sie im Blender-Bericht stehen.

    Blenders glTF-Import rechnet Y-up nach Z-up um: ``welt = (x, −z, y)``. Die Umrechnung
    ist **nicht geraten, sondern nachgerechnet**: Auf die Bestandsdatei angewandt ergibt
    sie ``[135.75, 136.50, 25.60]`` — genau die ``bbox_size_m`` des Laufs vom 28.08.2026 —
    und daraus denselben Abstand von **358,02 m**, den der Bericht meldet.

    Raises:
        GlbError: ``up_axis`` ist nicht ``"Y"``. Siehe :data:`HOCHACHSEN`, warum hier
            keine geratene zweite Konvention steht.
    """
    achse = str(up_axis).strip().upper()
    if achse not in HOCHACHSEN:
        raise GlbError(
            f"up_axis={up_axis!r} wird von diesem Modul nicht umgerechnet; bekannt ist "
            f"{', '.join(HOCHACHSEN)}. Der Produktivweg (ifc_to_glb_runner) liefert "
            "immer 'Y'. Für Z-up setzt `seams` zusätzlich --rotiere-z-up, und was dabei "
            "in Blender herauskommt, ist NICHT GEMESSEN. Eine geratene Achsenkonvention "
            "wäre der vierte unvereinbare Vertrag in diesem Projekt.")
    return ([lo[0], -hi[2], lo[1]], [hi[0], -lo[2], hi[1]])


def _huelle(eintraege):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for _, l, h in eintraege:
        for i in range(3):
            lo[i] = min(lo[i], l[i])
            hi[i] = max(hi[i], h[i])
    return lo, hi


def bauwerksbox(pfad, *, up_axis: str = "Y", regel=ist_gelaende) -> dict:
    """Die Hüllbox der gebauten Substanz einer glb — Weg (b), ohne Blender.

    Das Gegenstück zu ``blender_depth_stage._bbox_bauwerk`` diesseits der Prozessgrenze:
    dieselbe Frage, dieselbe Regel, dieselbe Weigerung, auf die Szenenbox zurückzufallen —
    nur ohne die 40 s Blender.

    Args:
        pfad: Die ``.glb`` (oder ``.gltf``).
        up_axis: Hochachse der Datei. Nur ``"Y"`` — siehe :data:`HOCHACHSEN`.
        regel: Die Geländeregel. Vorgabe ist :func:`aiimaging.maske.ist_gelaende`, und
            der Parameter ist zum **Prüfen** da, nicht zum Ausweichen: Wer hier eine
            eigene Regel übergibt, hat eine zweite Regel, und dann ist eine von beiden
            falsch.

    Returns:
        dict mit

        * ``bbox_szene`` / ``bbox_bauwerk`` — ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` in
          **Weltkoordinaten**, unmittelbar an ``kamerasatz`` oder ``--kamera-huellbox``
          übergebbar. ``bbox_bauwerk`` ist ``None``, wenn nichts feststellbar war.
        * ``note`` — **warum** ``None``, oder welcher Vorbehalt an der Box klebt. Leer
          heisst: nichts anzumerken.
        * ``schrumpfung`` — wie viel Grundriss-Breite die Bauwerksbox gegenüber der Szene
          verloren hat, als Anteil (``0.0`` = die Regel hat nichts gefunden, was die
          Rahmung ändert). **Die Zahl, an der man sieht, ob die Regel überhaupt
          gegriffen hat** — siehe die Warnung im Modulkopf.
        * ``n_bauwerk`` / ``n_gelaende`` / ``gelaende_namen`` — was wohin gezählt wurde.
        * ``dauer_s`` — gemessen, nicht geschätzt.

    Raises:
        GlbError: Datei unlesbar, ``up_axis`` unbekannt, oder ein Mesh ohne ``min``/``max``
            (siehe :func:`knotenboxen`).
    """
    beginn = time.monotonic()
    js = lies_gltf_json(pfad)
    gelesen = knotenboxen(js)
    if gelesen["ohne_grenzen"]:
        fehlend = gelesen["ohne_grenzen"]
        raise GlbError(
            f"{len(fehlend)} Mesh-Knoten tragen keinen POSITION-Accessor mit min/max, "
            f"zuerst: {fehlend[:3]}. glTF 2.0 verlangt beides (Abschnitt 3.6.2.1); diese "
            "Datei hält den Vertrag nicht. Es wird KEINE Box aus dem Rest gebildet: Sie "
            "wäre zu klein, die Kamera stünde zu nah, und das Bauwerk wäre angeschnitten "
            "— ohne dass der Zahl etwas anzusehen wäre. Wer diese Datei rahmen will, "
            "nimmt den Blender-Weg (a).")

    alle = gelesen["knoten"]
    ergebnis = {"bbox_szene": None, "bbox_bauwerk": None, "note": "",
                "schrumpfung": None, "n_bauwerk": 0, "n_gelaende": 0,
                "gelaende_namen": (), "n_knoten": len(alle),
                "dauer_s": 0.0, "up_axis": str(up_axis).strip().upper()}

    if not alle:
        ergebnis["note"] = (
            "Die Datei trägt keinen einzigen Mesh-Knoten. Das ist kein Gelände-Befund, "
            "sondern eine leere Szene — und über eine leere Szene sagt keine Rahmung etwas.")
        ergebnis["dauer_s"] = time.monotonic() - beginn
        return ergebnis

    ergebnis["bbox_szene"] = [list(v) for v in nach_welt(*_huelle(alle), up_axis=up_axis)]

    gelaende = [k for k in alle if regel(k[0])]
    bauwerk = [k for k in alle if not regel(k[0])]
    ergebnis["n_gelaende"] = len(gelaende)
    ergebnis["n_bauwerk"] = len(bauwerk)
    ergebnis["gelaende_namen"] = tuple(n for n, _, _ in gelaende)

    if not bauwerk:
        # Wortgleich mit `blender_depth_stage._bbox_bauwerk`, und das ist Absicht: Zwei
        # Wege zur selben Zahl sollen bei derselben Lage dieselbe Auskunft geben.
        ergebnis["note"] = (
            f"Kein einziger Mesh-Knoten blieb nach der Gelaenderegel uebrig "
            f"({len(gelaende)} als Gelaende erkannt). Entweder besteht die Szene nur aus "
            f"Gelaende — dann ist der Auftrag ohne Bauwerk —, oder die Namen tragen die "
            f"Unterscheidung nicht. Es wird NICHT auf die Szenenbox zurueckgefallen.")
        ergebnis["dauer_s"] = time.monotonic() - beginn
        return ergebnis

    ergebnis["bbox_bauwerk"] = [list(v) for v in nach_welt(*_huelle(bauwerk), up_axis=up_axis)]

    # Die Zahl, die einen wirkungslosen Filter von einem wirksamen unterscheidet.
    #
    # Gemessen an der **Grundriss-Diagonale**, und die Wahl ist hergeleitet, nicht bequem:
    # Den Abstand setzt `sichtbare_breite = |dx·sin a| + |dy·cos a|`, und deren Grösstwert
    # über alle Blickrichtungen ist genau `sqrt(dx² + dy²)`. Die Diagonale ist also die
    # Kante, an der die weiteste der zwölf Kameras hängt.
    #
    # `max(dx, dy)` — die Form, die `rahmungsverhaeltnis` benutzt — wäre hier irreführend:
    # An der Bestandsdatei vom 28.08.2026 schrumpft nur dy (136,50 → 130,12), dx bleibt.
    # Über `max` gemessen ergäbe das **0,5 %**, über die Diagonale **2,3 %** — und die
    # zweite Zahl ist die, die zur gemessenen Abstandsänderung von 2,1 % passt.
    def breite(box):
        return math.hypot(box[1][0] - box[0][0], box[1][1] - box[0][1])

    b_szene = breite(ergebnis["bbox_szene"])
    b_bau = breite(ergebnis["bbox_bauwerk"])
    ergebnis["schrumpfung"] = (1.0 - b_bau / b_szene) if b_szene > 0.0 else 0.0

    if not gelaende:
        ergebnis["note"] = (
            "Kein Knoten wurde als Gelaende erkannt; die Bauwerksbox ist hier gleich der "
            "Szenenbox. Das ist ein gueltiges Ergebnis und kein Rueckfall — aber ein "
            "Bruch zwischen Rahmung und Messung ist damit auch nicht feststellbar.")
    elif ergebnis["schrumpfung"] < GERINGE_SCHRUMPFUNG:
        ergebnis["note"] = (
            f"Die Gelaenderegel hat {len(gelaende)} Knoten aussortiert, die Rahmung wird "
            f"davon aber nur um {ergebnis['schrumpfung']:.1%} enger — unter "
            f"{GERINGE_SCHRUMPFUNG:.0%}. Das SIEHT nach einer Bauwerksbox aus und wirkt "
            f"wie keine. Am 01.09.2026 gemessen: Eine Bestandsdatei trug ihr Gelaende als "
            f"'Toposolid', 'Sub-Division' und 'Umgebung - Gras' — kein einziger dieser "
            f"Namen enthaelt eines der vier Woerter aus maske.GELAENDE_WOERTER, und der "
            f"Abstand sank um 2,1 % statt um 34,5 %. Wer hier eine wirksame Box braucht, "
            f"ergaenzt die REGEL an ihrer einen Stelle — nicht diesen Aufruf.")

    ergebnis["dauer_s"] = time.monotonic() - beginn
    return ergebnis


def _main(argv=None) -> int:                              # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(
        description="Hüllbox der gebauten Substanz aus einer glb — ohne Blender.")
    ap.add_argument("glb")
    ap.add_argument("--up-axis", default="Y")
    ap.add_argument("--nur-huellbox", action="store_true",
                    help="Nur die sechs Zahlen für --kamera-huellbox, sonst nichts.")
    a = ap.parse_args(argv)

    try:
        aus = bauwerksbox(a.glb, up_axis=a.up_axis)
    except GlbError as e:
        print(str(e), flush=True)
        return 2
    if a.nur_huellbox:
        if aus["bbox_bauwerk"] is None:
            print(aus["note"], flush=True)
            return 1
        lo, hi = aus["bbox_bauwerk"]
        print(",".join(f"{v:.6f}" for v in (*lo, *hi)), flush=True)
        return 0
    aus = dict(aus)
    aus["gelaende_namen"] = list(aus["gelaende_namen"])[:20]
    print(json.dumps(aus, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(_main())
