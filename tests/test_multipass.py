"""Der Multipass: vier Ausgaben aus zwei Renderdurchgängen — und was ohne Blender prüfbar ist.

Zwei Sorten Tests, bewusst getrennt
-----------------------------------
1. **Ohne Blender.** Die Aufrufkonstruktion über die Testnaht ``_starte``. Sie läuft
   überall, auch in einer CI ohne Blender, und ist der Teil, der bei jeder Änderung an
   ``seams.py`` sofort anschlägt.
2. **Mit Blender** (``@pytest.mark.skipif``). Ein echter Lauf über die Prozessgrenze auf
   einer im Test selbst erzeugten glb. Nur hier lässt sich prüfen, ob in den Dateien
   wirklich etwas steht — und genau das ist die Frage, an der ein Renderer scheitert,
   ohne einen Fehlercode zu melden.

Warum die Testdaten hier entstehen und nicht daneben liegen
-----------------------------------------------------------
Regel 3: keine echten Projektdaten. Die glb wird als glTF 2.0 von Hand geschrieben —
zwei Quader in unterschiedlicher Entfernung, mit **zwei benannten Materialien**. Die
Entfernung ist der Prüfstein für die Konvention *nah = hell*, die Materialien der für
den Material-ID-Pass. Beides bräuchte sonst `ifcopenshell` (LGPL, im eigenen venv) und
wäre damit an eine zweite Voraussetzung geknüpft.

Warum ein eigener PNG-Leser
---------------------------
Das Produkt hat keine Bildbibliothek und soll keine bekommen (Regel 1: jede Abhängigkeit
ist eine Lizenzentscheidung). PNG ist aber mit ``zlib`` aus der Standardbibliothek
vollständig lesbar. Die dreissig Zeilen unten sind der Preis dafür, dass diese Tests
ohne Pillow, ohne numpy und ohne Blender-Import auskommen.
"""
from __future__ import annotations

import json
import shutil
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import seams
from aiimaging.seams import (
    baue_kommando_multipass,
    baue_kommando_tiefenkarte,
    glb_zu_multipass,
    glb_zu_tiefenkarte,
)

#: Der Runner jenseits der Grenze. Wird hier **gelesen**, nie importiert — er braucht
#: ``bpy``, und der Import wäre genau der Vertragsbruch aus Regel 2.
RUNNER_QUELLE = seams.BLENDER_RUNNER.read_text(encoding="utf-8")

#: Klein und wenige Samples: Diese Tests prüfen Inhalte, nicht Bildqualität. Auf CPU-
#: Cycles kostet jeder Pixel Zeit, und ein Test, der Minuten braucht, wird abgeschaltet.
AUFLOESUNG = 96
SAMPLES = 4


def blender_fehlt() -> bool:
    """Ist in dieser Umgebung ein Blender-Binary erreichbar?"""
    try:
        return not Path(seams.finde_blender()).exists()
    except seams.SeamError:
        return True


ohne_blender = pytest.mark.skipif(
    blender_fehlt(), reason="Blender nicht vorhanden — der Lauf über die Prozessgrenze entfällt"
)


# ======================================================================================
# Werkzeuge: glTF schreiben, PNG lesen — beides reine Standardbibliothek
# ======================================================================================

def schreibe_test_glb(ziel: Path) -> Path:
    """Zwei Quader mit zwei Materialien als glb (Y-up, glTF-2.0-konform).

    Der zweite Quader steht deutlich weiter hinten. Er ist der Gegenpol, an dem sich die
    Tiefenkonvention überhaupt erst prüfen lässt: Ein einzelner Körper wäre in jeder
    Konvention irgendwie hell.
    """
    # Einheitswürfel, Kantenlänge 2. Eckindex = 4*i + 2*j + k mit (x,y,z) = (2i, 2j, 2k).
    ecken = [(2.0 * ((n >> 2) & 1), 2.0 * ((n >> 1) & 1), 2.0 * (n & 1)) for n in range(8)]
    dreiecke = [
        (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5),
        (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
        (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
    ]

    indizes = b"".join(struct.pack("<H", i) for d in dreiecke for i in d)   # 36 × uint16
    positionen = b"".join(struct.pack("<fff", *e) for e in ecken)           # 8 × vec3
    binaer = indizes + positionen                                          # 72 + 96 = 168
    assert len(indizes) % 4 == 0, "Ausrichtung: der Positions-BufferView muss auf 4 liegen"

    gltf = {
        "asset": {"version": "2.0", "generator": "aiimaging Testfixture"},
        "scene": 0,
        "scenes": [{"nodes": [0, 1]}],
        # glTF ist Y-up; Blender bildet (x, y, z) auf (x, −z, y) ab. Ein Versatz in −z
        # schiebt den Quader in Blender nach +y, also von der Kamera weg.
        "nodes": [
            {"name": "QuaderNah", "mesh": 0, "translation": [0.0, 0.0, 0.0]},
            {"name": "QuaderFern", "mesh": 1, "translation": [0.0, 0.0, -6.0]},
        ],
        "meshes": [
            {"name": "QuaderNah",
             "primitives": [{"attributes": {"POSITION": 1}, "indices": 0, "material": 0}]},
            {"name": "QuaderFern",
             "primitives": [{"attributes": {"POSITION": 1}, "indices": 0, "material": 1}]},
        ],
        "materials": [
            # Helle, wenig gesättigte Farben: Der Beauty-Test misst Licht und Schatten,
            # und eine dunkle Fassade drückte den Unterschied unter die Messschwelle,
            # ohne dass mit der Beleuchtung etwas falsch wäre.
            {"name": "MatNah",
             "pbrMetallicRoughness": {"baseColorFactor": [0.85, 0.80, 0.75, 1.0],
                                      "metallicFactor": 0.0, "roughnessFactor": 0.8}},
            {"name": "MatFern",
             "pbrMetallicRoughness": {"baseColorFactor": [0.75, 0.78, 0.85, 1.0],
                                      "metallicFactor": 0.0, "roughnessFactor": 0.8}},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5123, "count": len(dreiecke) * 3,
             "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": len(ecken), "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [2.0, 2.0, 2.0]},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(indizes), "target": 34963},
            {"buffer": 0, "byteOffset": len(indizes), "byteLength": len(positionen),
             "target": 34962},
        ],
        "buffers": [{"byteLength": len(binaer)}],
    }

    json_bytes = json.dumps(gltf).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)          # Chunks liegen auf 4 Bytes
    binaer += b"\x00" * (-len(binaer) % 4)

    gesamt = 12 + 8 + len(json_bytes) + 8 + len(binaer)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, gesamt))
        fh.write(struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes)
        fh.write(struct.pack("<I4s", len(binaer), b"BIN\x00") + binaer)
    return ziel


class Png:
    """Ein eingelesenes PNG: Kopfdaten und Pixelwerte, ohne Bildbibliothek."""

    KANAELE = {0: 1, 2: 3, 4: 2, 6: 4}                   # Grau, RGB, Grau+A, RGBA

    def __init__(self, pfad: Path):
        daten = Path(pfad).read_bytes()
        assert daten[:8] == b"\x89PNG\r\n\x1a\n", f"{pfad} ist kein PNG"
        kopf, idat, pos = None, b"", 8
        while pos < len(daten):
            laenge = int.from_bytes(daten[pos:pos + 4], "big")
            typ = daten[pos + 4:pos + 8]
            inhalt = daten[pos + 8:pos + 8 + laenge]
            pos += 12 + laenge                           # 4 Länge + 4 Typ + Inhalt + 4 CRC
            if typ == b"IHDR":
                kopf = struct.unpack(">IIBBBBB", inhalt)
            elif typ == b"IDAT":
                idat += inhalt
            elif typ == b"IEND":
                break
        self.breite, self.hoehe, self.bittiefe, self.farbtyp, _, _, interlace = kopf
        assert interlace == 0, "verschränkte PNGs kommen hier nicht vor"
        self.kanaele = self.KANAELE[self.farbtyp]
        self.werte = self._entfiltern(zlib.decompress(idat))

    def _entfiltern(self, roh: bytes) -> list[int]:
        """Die fünf PNG-Zeilenfilter rückgängig machen (Spezifikation, Kapitel 9)."""
        bpp = self.kanaele * (self.bittiefe // 8)        # Bytes pro Pixel
        zeilenlaenge = self.breite * bpp
        vorherige = bytearray(zeilenlaenge)
        aus = bytearray()
        p = 0
        for _ in range(self.hoehe):
            art, p = roh[p], p + 1
            zeile = bytearray(roh[p:p + zeilenlaenge])
            p += zeilenlaenge
            for i in range(zeilenlaenge):
                links = zeile[i - bpp] if i >= bpp else 0
                oben = vorherige[i]
                schraeg = vorherige[i - bpp] if i >= bpp else 0
                if art == 0:
                    zusatz = 0
                elif art == 1:
                    zusatz = links
                elif art == 2:
                    zusatz = oben
                elif art == 3:
                    zusatz = (links + oben) >> 1
                elif art == 4:                            # Paeth
                    p_a, p_b, p_c = (abs(oben - schraeg), abs(links - schraeg),
                                     abs(links + oben - 2 * schraeg))
                    zusatz = links if (p_a <= p_b and p_a <= p_c) else (
                        oben if p_b <= p_c else schraeg)
                else:
                    raise AssertionError(f"unbekannter PNG-Filter {art}")
                zeile[i] = (zeile[i] + zusatz) & 0xFF
            aus += zeile
            vorherige = zeile
        if self.bittiefe == 8:
            return list(aus)
        return [int.from_bytes(aus[i:i + 2], "big") for i in range(0, len(aus), 2)]

    @property
    def maximalwert(self) -> int:
        return (1 << self.bittiefe) - 1

    def pixel(self, i: int) -> tuple:
        """Die Kanäle des i-ten Pixels (zeilenweise von oben)."""
        s = i * self.kanaele
        return tuple(self.werte[s:s + self.kanaele])

    def farben(self) -> dict[tuple, int]:
        """Wie oft kommt welche Farbe vor? (Alphakanal bleibt aussen vor.)"""
        zaehler: dict[tuple, int] = {}
        n = self.breite * self.hoehe
        sichtbar = min(self.kanaele, 3)
        for i in range(n):
            s = i * self.kanaele
            schluessel = tuple(self.werte[s:s + sichtbar])
            zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
        return zaehler


# ======================================================================================
# 1 · Ohne Blender — die Aufrufkonstruktion an der Naht
# ======================================================================================

class Ergebnis:
    """Doppelgänger eines ``subprocess.CompletedProcess``."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Aufrufer:
    """Ersatz für ``_starte``: merkt sich das Kommando und legt einen Report ab."""

    def __init__(self, report: dict | None = None):
        self.report = {"status": "ok"} if report is None else report
        self.kommandos: list[list[str]] = []

    def __call__(self, cmd, timeout):
        self.kommandos.append(list(cmd))
        Path(cmd[cmd.index("--out") + 1], "blender-report.json").write_text(
            json.dumps(self.report), encoding="utf-8")
        return Ergebnis()

    @property
    def kommando(self) -> list[str]:
        assert len(self.kommandos) == 1
        return self.kommandos[0]


def test_vorgabe_rendert_alle_paesse():
    """Rückwärtskompatibel: Ein Aufruf wie bisher schaltet nichts ab."""
    cmd = baue_kommando_multipass("bau.glb", "out", up_axis="Y")
    assert "--ohne-beauty" not in cmd
    assert "--ohne-material-id" not in cmd


def test_material_id_laesst_sich_abschalten():
    """Der zweite Durchgang kostet einen vollen Render — er muss verzichtbar sein."""
    cmd = baue_kommando_multipass("bau.glb", "out", up_axis="Y", material_id=False)
    assert "--ohne-material-id" in cmd
    assert "--ohne-beauty" not in cmd, "die eine Flagge darf die andere nicht mitziehen"


def test_beauty_laesst_sich_abschalten():
    """Gegenprobe: Beauty aus, Material-ID bleibt."""
    cmd = baue_kommando_multipass("bau.glb", "out", up_axis="Y", beauty=False)
    assert "--ohne-beauty" in cmd
    assert "--ohne-material-id" not in cmd


def test_abschalter_vertragen_sich_mit_der_drehflagge():
    """Die Flaggen sind unabhängig — die Up-Achse darf von ihnen nicht berührt werden."""
    cmd = baue_kommando_multipass("bau.glb", "out", up_axis="Z",
                                  beauty=False, material_id=False)
    assert {"--rotiere-z-up", "--ohne-beauty", "--ohne-material-id"} <= set(cmd)


def test_lauf_und_trockenlauf_bauen_dasselbe_kommando(tmp_path, monkeypatch):
    """Sonst prüften die Tests ein Kommando, das so nie gestartet wird.

    ``baue_kommando_multipass`` ist nur dann eine brauchbare Naht, wenn es dieselben
    Argumente erzeugt wie der echte Lauf. Verglichen wird alles hinter ``--`` — davor
    steht der Binärpfad, der sich naturgemäss unterscheidet.
    """
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    aufrufer = Aufrufer()
    glb_zu_multipass("bau.glb", tmp_path / "out", up_axis="Z", aufloesung=128, samples=3,
                     material_id=False, _starte=aufrufer)

    trocken = baue_kommando_multipass("bau.glb", tmp_path / "out", up_axis="Z",
                                      aufloesung=128, samples=3, material_id=False)
    echt = aufrufer.kommando
    assert echt[echt.index("--") + 1:] == trocken[trocken.index("--") + 1:]
    assert echt[0] == "/attrappe/blender", "der echte Lauf nimmt das gefundene Binary"


def test_alter_name_zeigt_auf_dieselbe_funktion():
    """Der Alias ist kein zweiter Codepfad, sondern derselbe — sonst driftete er weg."""
    assert glb_zu_tiefenkarte is glb_zu_multipass
    assert baue_kommando_tiefenkarte is baue_kommando_multipass


def test_report_wird_durchgereicht_bis_auf_die_tiefen_nachbearbeitung(tmp_path, monkeypatch):
    """Die Naht deutet den Report nicht — mit **einer** benannten Ausnahme.

    Seit dem 18.08.2026 rechnet `seams` das normalisierte PNG selbst aus der EXR
    (Blender 5.2 kann seine eigene Multilayer-EXR nicht zurücklesen). Damit ist der
    Report nicht mehr wortgleich durchgereicht, und dieser Test hält fest, **wie weit**
    die Ausnahme reicht: Jedes andere Feld bleibt unangetastet, und die drei
    Tiefenfelder sind belegt statt beliebig.
    """
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    report = {"status": "ok", "beauty_png": "b.png", "material_id_png": "m.png",
              "depth_exr": "t.exr", "depth_png": "t.png", "n_materialien": 2,
              "depth_normalisierung": {"min_m": 1.0, "max_m": 9.0}}

    zurueck = glb_zu_multipass("bau.glb", tmp_path / "out", up_axis="Y",
                               _starte=Aufrufer(dict(report)))

    unberuehrt = {k: v for k, v in report.items()
                  if k not in ("depth_png", "depth_normalisierung")}
    assert {k: zurueck[k] for k in unberuehrt} == unberuehrt

    # `t.exr` existiert nicht — die Nachbearbeitung sagt das, statt zu raten oder zu
    # sterben. Der Lauf bleibt gültig: massgeblich ist die EXR, nicht ihre Ableitung.
    assert zurueck["depth_png"] is None
    assert zurueck["depth_normalisierung"] is None
    assert "t.exr" in zurueck["depth_png_fehler"]


# ======================================================================================
# 2 · Ohne Blender — was am Runner schon durch Lesen prüfbar ist
# ======================================================================================

def test_runner_rendert_genau_zweimal():
    """Der Material-ID-Pass braucht einen **eigenen** Durchgang.

    Liefe er im selben Render wie Beauty, färbte der Emissions-Override das Beauty-Bild
    flach ein. Zwei Aufrufe von ``render.render`` sind die knappste Fassung dieser Zusage
    — und die einzige, die ohne Blender prüfbar ist.
    """
    assert RUNNER_QUELLE.count("bpy.ops.render.render(") == 2


def test_runner_verteilt_die_farben_ueber_den_goldenen_winkel():
    """Die Konstante steht im Runner — mit der Genauigkeit, auf die es ankommt."""
    assert "0.618033988749895" in RUNNER_QUELLE


@pytest.mark.parametrize("anzahl", [2, 5, 12, 64])
def test_goldener_winkel_haelt_benachbarte_indizes_auseinander(anzahl):
    """Die Eigenschaft, wegen der der Goldene Winkel gewählt wurde.

    Aufeinanderfolgende Material-Indizes bekommen weit auseinanderliegende Farbtöne —
    und zwar ohne dass die Gesamtzahl vorher bekannt sein muss. Geprüft wird der Abstand
    auf dem Farbkreis (er ist zyklisch, deshalb der Umweg über ``min(d, 1-d)``).
    """
    goldener_winkel = 0.618033988749895
    toene = [(i * goldener_winkel) % 1.0 for i in range(anzahl)]

    for i in range(len(toene) - 1):
        d = abs(toene[i + 1] - toene[i])
        assert min(d, 1.0 - d) > 0.3, f"Index {i} und {i+1} liegen zu nah beieinander"

    sortiert = sorted(toene)
    kleinster = min(min(b - a, 1.0 - (b - a)) for a, b in zip(sortiert, sortiert[1:]))
    assert kleinster > 0.5 / anzahl, "die Töne häufen sich statt sich zu verteilen"


# ======================================================================================
# 3 · Mit Blender — ein echter Lauf über die Prozessgrenze
# ======================================================================================

@pytest.fixture(scope="module")
def lauf(tmp_path_factory):
    """Ein einziger echter Multipass-Lauf für alle Inhaltstests.

    Modulweit, nicht pro Test: Zwei Cycles-Durchgänge auf CPU sind das Teuerste, was
    diese Testsammlung tut. Was danach geprüft wird, sind Dateien — die ändern sich nicht
    mehr.
    """
    if blender_fehlt():
        pytest.skip("Blender nicht vorhanden")
    ordner = tmp_path_factory.mktemp("multipass")
    glb = schreibe_test_glb(ordner / "zwei_quader.glb")

    report = glb_zu_multipass(glb, ordner / "out", up_axis="Y",
                              aufloesung=AUFLOESUNG, samples=SAMPLES, timeout=900)
    assert report["status"] == "ok", report.get("error")
    return report


@ohne_blender
def test_alle_vier_ausgaben_entstehen(lauf):
    """Vier Dateien, alle nicht leer. Der Report darf keine davon nur behaupten."""
    for feld in ("beauty_png", "material_id_png", "depth_exr", "depth_png"):
        pfad = Path(lauf[feld])
        assert pfad.exists(), f"{feld} steht im Report, aber die Datei fehlt: {pfad}"
        assert pfad.stat().st_size > 0, f"{feld} ist leer"


@ohne_blender
def test_bestandsfelder_behalten_ihre_bedeutung(lauf):
    """Rückwärtskompatibilität: Was ``seams.py`` und die alten Tests lesen, steht weiter da."""
    assert lauf["status"] == "ok"
    assert lauf["error"] is None
    assert lauf["n_meshes"] == 2
    assert lauf["aufloesung"] == AUFLOESUNG
    assert lauf["rotiert"] is False
    # HomeStation-Befund 18.08. (auf-20260818-06): Hier stand `startswith("4.")` — eine
    # Versionsnummer-Abfrage, und damit genau das, was die Auflage dieses Projekts
    # verbietet («die Weiche prueft Faehigkeiten, nicht Versionsnummern»). Auf der
    # HomeStation laeuft Blender 5.2.0 LTS; der Test schlug dort fehl, obwohl nichts
    # kaputt war — er mass den Rechner, nicht das Verhalten.
    #
    # Was der Test laut seinem eigenen Docstring sichern soll, ist die Rueckwaerts-
    # kompatibilitaet der FELDER: dass `blender` noch da ist und eine Version traegt.
    # Genau das wird jetzt geprueft — auf 4.2 wie auf 5.2.
    assert isinstance(lauf["blender"], str) and lauf["blender"][:1].isdigit(), lauf["blender"]
    assert len(lauf["bbox"]) == 2 and len(lauf["bbox_size_m"]) == 3
    assert Path(lauf["depth_exr"]).suffix == ".exr"


@ohne_blender
def test_beauty_ist_beleuchtet_und_nicht_schwarz(lauf):
    """Der Kern der Sache: Ohne Licht ist ein Beauty-Pass ein schwarzes Rechteck.

    Geprüft wird nicht Schönheit, sondern dass überhaupt Licht auf Flächen fällt — und
    dass das Bild nicht ins andere Extrem gekippt ist. Ein durchgehend weisses Bild wäre
    genauso wertlos wie ein schwarzes.
    """
    bild = Png(Path(lauf["beauty_png"]))
    assert bild.breite == bild.hoehe == AUFLOESUNG
    assert bild.bittiefe == 8

    helligkeiten = [sum(bild.pixel(i)[:3]) / 3.0 / bild.maximalwert
                    for i in range(bild.breite * bild.hoehe)]
    mittel = sum(helligkeiten) / len(helligkeiten)

    assert 0.05 < mittel < 0.95, f"mittlere Helligkeit {mittel:.3f} — schwarz oder ausgebrannt"
    assert max(helligkeiten) - min(helligkeiten) > 0.15, \
        "kein Kontrast im Bild: Licht und Schatten sind nicht unterscheidbar"
    assert len({round(h * 255) for h in helligkeiten}) > 20, \
        "zu wenige Helligkeitsstufen — das sieht nach einer Farbfläche aus, nicht nach Render"


@ohne_blender
def test_material_id_traegt_je_material_genau_eine_farbe(lauf):
    """Zwei Materialien, zwei Farben, plus schwarzer Grund — und keine vierte.

    Die Zahl ist der eigentliche Test. Kämen mehr Farben heraus, wären sie an den Kanten
    entstanden (Filter, Dithering, Rauschen) — und jede solche Mischfarbe wäre eine
    Material-ID, die es nicht gibt.
    """
    assert lauf["n_materialien"] == 2
    assert lauf["material_id_quelle"] == ["material"], \
        "die glb bringt Materialien mit — der Objekt-Rückfall darf hier nicht greifen"

    tabelle = {e["name"]: e for e in lauf["material_id_tabelle"]}
    assert set(tabelle) == {"MatNah", "MatFern"}

    farben = Png(Path(lauf["material_id_png"])).farben()
    assert len(farben) == 3, f"erwartet: 2 IDs + Hintergrund, gefunden: {sorted(farben)}"
    assert (0, 0, 0) in farben, "der Hintergrund muss schwarz sein, sonst kollidiert er mit einer ID"

    for name, eintrag in tabelle.items():
        soll = tuple(eintrag["farbe_srgb_8bit"])
        assert soll in farben, f"{name}: Farbe {soll} aus dem Report kommt im Bild nicht vor"
        assert farben[soll] > 20, f"{name} ist mit {farben[soll]} Pixeln praktisch unsichtbar"


@ohne_blender
def test_material_id_farben_stehen_weit_auseinander(lauf):
    """Zwei IDs müssen mit blossem Vergleich trennbar sein, nicht nur rechnerisch."""
    farben = [tuple(e["farbe_srgb_8bit"]) for e in lauf["material_id_tabelle"]]
    for i, a in enumerate(farben):
        for b in farben[i + 1:]:
            assert max(abs(x - y) for x, y in zip(a, b)) > 60, f"{a} und {b} sind zu ähnlich"


@ohne_blender
def test_tiefenkarte_ist_16_bit_graustufen(lauf):
    """8 Bit teilten die Bautiefe in 256 Stufen — sichtbare Terrassen auf jeder Schräge."""
    bild = Png(Path(lauf["depth_png"]))
    assert bild.bittiefe == 16
    assert bild.kanaele == 1, "Graustufen, kein RGB — die Tiefe hat nur eine Dimension"
    assert bild.breite == bild.hoehe == AUFLOESUNG
    assert len(set(bild.werte)) > 256, \
        "nicht mehr Stufen als 8 Bit hergäben — dann wäre die 16-Bit-Datei nur Ballast"


@ohne_blender
def test_tiefe_meldet_ihre_normalisierung_in_metern(lauf):
    """Ohne min/max kann die QA das PNG nicht in Meter zurückrechnen — es wäre dann Deko."""
    norm = lauf["depth_normalisierung"]
    assert 0.0 < norm["min_m"] < norm["max_m"] < 1.0e6
    assert norm["max_m"] - norm["min_m"] > 0.1, "die beiden Quader stehen unterschiedlich weit weg"
    assert "nah = hell" in norm["konvention"]


@ohne_blender
def test_tiefenkarte_ist_nah_hell(lauf):
    """Die ControlNet-Konvention, geprüft an zwei Körpern in bekannter Reihenfolge.

    Das ist der Test, der eine vertauschte Konvention wirklich fängt: Der Material-ID-Pass
    sagt, **welche** Pixel zum vorderen Quader gehören, die Tiefenkarte sagt, **wie hell**
    sie sind. Ein einzelnes Bild könnte man in beiden Konventionen für richtig halten.
    """
    ids = Png(Path(lauf["material_id_png"]))
    tiefe = Png(Path(lauf["depth_png"]))
    assert (ids.breite, ids.hoehe) == (tiefe.breite, tiefe.hoehe)

    tabelle = {e["name"]: tuple(e["farbe_srgb_8bit"]) for e in lauf["material_id_tabelle"]}

    def mittlere_helligkeit(farbe) -> float:
        werte = [tiefe.werte[i] for i in range(ids.breite * ids.hoehe)
                 if ids.pixel(i)[:3] == farbe]
        assert werte, f"kein Pixel der Farbe {farbe} — die Masken passen nicht zusammen"
        return sum(werte) / len(werte) / tiefe.maximalwert

    nah = mittlere_helligkeit(tabelle["MatNah"])
    fern = mittlere_helligkeit(tabelle["MatFern"])

    assert nah > fern, f"nah={nah:.3f} ist nicht heller als fern={fern:.3f} — Konvention verdreht"
    assert nah - fern > 0.1, f"Abstand {nah - fern:.3f} zu gering, um Konvention zu belegen"


@ohne_blender
def test_hintergrund_der_tiefenkarte_ist_schwarz(lauf):
    """Unendlich fern ist der Grenzfall von dunkel, kein Sonderwert.

    Läge der Hintergrund hell, hielte ein ControlNet den leeren Himmel für die nächste
    Fläche vor der Kamera.
    """
    ids = Png(Path(lauf["material_id_png"]))
    tiefe = Png(Path(lauf["depth_png"]))
    hintergrund = [tiefe.werte[i] for i in range(ids.breite * ids.hoehe)
                   if ids.pixel(i)[:3] == (0, 0, 0)]

    assert hintergrund, "die Testszene hat keinen freien Himmel — dann prüft das hier nichts"
    assert max(hintergrund) == 0


@ohne_blender
def test_ohne_material_id_entsteht_kein_zweiter_pass(tmp_path):
    """Der Abschalter im Vollzug: kein Material-ID-Bild, aber die drei anderen Ausgaben."""
    glb = schreibe_test_glb(tmp_path / "zwei_quader.glb")

    report = glb_zu_multipass(glb, tmp_path / "out", up_axis="Y",
                              aufloesung=64, samples=1, material_id=False, timeout=900)

    assert report["status"] == "ok", report.get("error")
    assert report["material_id_png"] is None
    assert report["material_id_tabelle"] == []
    for feld in ("beauty_png", "depth_exr", "depth_png"):
        assert Path(report[feld]).exists(), f"{feld} fehlt, obwohl nur die Material-ID entfiel"


@ohne_blender
def test_ohne_materialien_faellt_die_id_auf_objekte_zurueck(tmp_path):
    """Der Normalfall der heutigen Kette — und der Grund, warum die Herkunft im Report steht.

    ``ifc_to_glb_runner.py`` überträgt nur Geometrie, keine IfcMaterial-Zuordnung: In
    Blender kommt eine glb **ohne Materialien** an. Ohne Rückfall verschmölze die ganze
    Szene zu einer einzigen Fläche und die Maske wäre wertlos. Der Rückfall vergibt
    stattdessen objektweise IDs — und sagt das im Report, damit niemand eine Objekt-Maske
    für eine Material-Maske hält.
    """
    glb = tmp_path / "ohne_material.glb"
    schreibe_test_glb(glb)
    # Die Materialzuordnung wieder herausnehmen — so sieht die glb aus, die heute aus
    # der IFC-Kette kommt.
    roh = glb.read_bytes()
    laenge = struct.unpack("<I", roh[12:16])[0]
    daten = json.loads(roh[20:20 + laenge].decode("utf-8"))
    for netz in daten["meshes"]:
        for teil in netz["primitives"]:
            teil.pop("material", None)
    daten.pop("materials")
    neu = json.dumps(daten).encode("utf-8")
    neu += b" " * (-len(neu) % 4)
    binaer = roh[20 + laenge + 8:]
    glb.write_bytes(
        struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(neu) + 8 + len(binaer))
        + struct.pack("<I4s", len(neu), b"JSON") + neu
        + struct.pack("<I4s", len(binaer), b"BIN\x00") + binaer
    )

    report = glb_zu_multipass(glb, tmp_path / "out", up_axis="Y",
                              aufloesung=64, samples=1, timeout=900)

    assert report["status"] == "ok", report.get("error")
    assert report["n_materialien"] == 0, "die glb bringt keine Materialien mehr mit"
    assert report["material_id_quelle"] == ["objekt"]
    assert len(report["material_id_tabelle"]) == 2, "je Objekt eine ID, nicht eine für alles"
    assert len(Png(Path(report["material_id_png"])).farben()) == 3


# ======================================================================================
# 4 · Die Grenze bleibt, wo sie war
# ======================================================================================

def test_die_neue_faehigkeit_bleibt_jenseits_der_grenze():
    """Regel 2 für den Multipass: Alles Neue steht im Runner, nichts davon im Kern.

    Der Scan über den ganzen Kern liegt in ``test_prozessgrenze.py``. Hier geht es um die
    konkrete Versuchung dieser Aufgabe: Farbtabelle, Normalisierung und Emissionsfarben
    liessen sich bequem im Produkt rechnen und über die Naht hineinreichen. Genau dann
    stünde Blender-Wissen im Kern — und beim nächsten Schritt läge der Import nahe.
    """
    kern = Path(seams.__file__).read_text(encoding="utf-8")
    for begriff in ("ShaderNodeEmission", "GOLDENER_WINKEL", "colorsys", "_srgb_zu_linear"):
        assert begriff not in kern, f"{begriff} gehört in den Runner, nicht in seams.py"
        assert begriff in RUNNER_QUELLE, f"{begriff} fehlt im Runner"


def test_blender_wird_ohne_oberflaeche_und_ohne_benutzerprofil_gestartet():
    """Auch die neuen Flaggen ändern nichts an der Art des Aufrufs."""
    cmd = baue_kommando_multipass("bau.glb", "out", up_axis="Y", material_id=False)
    assert cmd[0] == "blender"
    assert "--background" in cmd and "--factory-startup" in cmd
    assert cmd[cmd.index("--python") + 1] == str(seams.BLENDER_RUNNER)
    assert cmd.index("--") > cmd.index("--python")


def test_shutil_which_ist_kein_ersatz_fuer_die_umgebungsvariable(monkeypatch):
    """``AIIMAGING_BLENDER`` hat Vorrang — so bleibt das Binary austauschbar (Regel 1)."""
    monkeypatch.setenv("AIIMAGING_BLENDER", "/anderswo/blender")
    monkeypatch.setattr(shutil, "which", lambda _n: "/usr/bin/blender")
    assert seams.finde_blender() == "/anderswo/blender"


# ── Regression aus Sitzung 05 ────────────────────────────────────────────────────────

def test_alte_ausgaben_werden_vor_dem_lauf_abgeraeumt(tmp_path):
    """Ein gescheiterter Lauf darf sich nicht an den Dateien des Vorlaufs gesundmelden.

    Sitzung 03 hat das fuer den Report behoben, Sitzung 05 fand dieselbe Luecke eine Datei
    weiter: Der Erfolg hing an der blossen Existenz einer `tiefe_*.exr`. Weil `out_dir`
    ueblicherweise wiederverwendet wird, verwies ein abgestuerzter Lauf auf das Bild von
    gestern. Existenz ist kein Beleg fuer Inhalt.
    """
    from aiimaging import seams

    ziel = tmp_path / "aus"
    ziel.mkdir()
    reste = ["tiefe_0001.exr", "tiefe_norm.png", "material_id.png", "beauty_.png"]
    for name in reste:
        (ziel / name).write_text("ALTER LAUF", encoding="utf-8")
    (ziel / "blender-report.json").write_text('{"status":"ok","aus":"ALTER LAUF"}',
                                              encoding="utf-8")

    class _Abbruch:
        def __init__(self):
            self.returncode, self.stdout, self.stderr = 137, "", "Killed"

    with pytest.raises(seams.SeamError):
        seams.glb_zu_multipass("bau.glb", ziel, up_axis="Y",
                               _starte=lambda cmd, timeout: _Abbruch())

    uebrig = sorted(p.name for p in ziel.iterdir())
    assert uebrig == [], f"Reste des Vorlaufs nicht abgeraeumt: {uebrig}"
