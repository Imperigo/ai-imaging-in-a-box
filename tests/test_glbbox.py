"""Weg (b): die Bauwerksbox aus der glb, ohne Blender.

Der Schalter ``--kamera-huellbox`` war seit dem 26.08.2026 verdrahtet und wirkungslos,
weil niemand die Box liefern konnte. ``abholer.py`` führt am Aufrufort drei Wege mit
Preisschild; **(b) — ein leichter Läufer — stand dort als „existiert nicht, geschätzt
1–2 s"**. Diese Datei prüft ihn.

Was hier NICHT geprüft wird und warum
-------------------------------------
**Die Laufzeit.** Sie ist gemessen (0,08 s an einer echten Bestandsdatei mit 4771 Meshes
und 25 MB, gegen +40 s je Kamera für Weg (a)), aber eine Zusicherung über Sekunden auf
einer geteilten Maschine ist eine Zusicherung über die Maschine. Geprüft wird stattdessen
der **Grund** für die Geschwindigkeit, und der ist strukturell: dass die Dreiecke gar nicht
gelesen werden. Siehe ``test_der_binaerblock_wird_nicht_angefasst`` — eine Datei mit
zerstörtem Binärblock liefert dieselbe Box. *Ein Zeitmass misst den Rechner, ein
Strukturmass die Behauptung.*

**Regel 3:** Alle Geometrie hier ist synthetisch und mit ``tools/make_test_glb.py`` im
Repo erzeugt. Die Zahlen aus der Bestandsdatei stehen als Kommentar, die Datei nicht.
"""
from __future__ import annotations

import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

from aiimaging import glbbox, kameras, maske

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"


def _erzeuger():
    """``tools/make_test_glb.py`` über den Dateipfad laden — es ist kein Paketmodul."""
    spez = importlib.util.spec_from_file_location("make_test_glb_pruefling", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


#: Bauwerk 12 × 9 × 15 m (Welt) auf einer Geländeplatte 40 × 30 m, in glTF-Koordinaten.
#:
#: Die Umrechnung steht hier **von Hand** daneben und nicht als Aufruf von
#: ``glbbox.nach_welt``: Sonst prüfte der Test die Umrechnung gegen sich selbst.
SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


@pytest.fixture
def szene_glb(tmp_path):
    pfad = tmp_path / "szene.glb"
    pfad.write_bytes(_erzeuger().baue_glb(SZENE))
    return pfad


# --------------------------------------------------------------------------------------
# 1 · Die Box selbst
# --------------------------------------------------------------------------------------

def test_die_gelaendeplatte_faellt_aus_der_bauwerksbox(szene_glb):
    """Der Zweck des Ganzen: Die Box der gebauten Substanz ist kleiner als die der Szene."""
    aus = glbbox.bauwerksbox(szene_glb)

    def masse(box):
        return [round(box[1][i] - box[0][i], 3) for i in range(3)]

    assert masse(aus["bbox_szene"]) == [40.0, 30.0, 15.5], aus["bbox_szene"]
    assert masse(aus["bbox_bauwerk"]) == [12.0, 9.0, 15.0], aus["bbox_bauwerk"]
    assert aus["n_gelaende"] == 1
    assert aus["n_bauwerk"] == 1
    assert aus["note"] == "", aus["note"]


def test_mit_der_bauwerksbox_steht_die_kamera_naeher(szene_glb):
    """**Die Abnahmebedingung**: Der Abstand muss belegbar kleiner werden.

    Gerechnet mit derselben Funktion, die auch der Runner benutzt — nicht mit einer
    Näherung fürs Testen. Auf der echten Bestandsdatei ist derselbe Vergleich
    358,02 m → 350,33 m; hier fällt er deutlicher aus, weil die synthetische Platte das
    Bauwerk wirklich überragt und die echte ihr Gelände nicht „Gelände" nennt.
    """
    aus = glbbox.bauwerksbox(szene_glb)

    def abstand(box):
        m = [box[1][i] - box[0][i] for i in range(3)]
        return kameras.abstand_aus_bildwinkel(
            m, 145.0, hoehe_ueber_grund=m[2] * kameras.ZIEL_ANTEIL_HOEHE)["abstand_m"]

    weit = abstand(aus["bbox_szene"])
    nah = abstand(aus["bbox_bauwerk"])
    assert nah < weit, (nah, weit)
    # Nicht nur „kleiner", sondern deutlich: Ein Prozent waere kein Ergebnis.
    #
    # Die Schranke stand bis zum 01.09.2026 bei 0.75 und ist an diesem Tag auf 0.80 gegangen —
    # nicht, weil die Bauwerksbox weniger brächte, sondern weil `abstand_aus_bildwinkel` seither
    # die seitliche Silhouette richtig projiziert und BEIDE Abstaende kleiner geworden sind.
    # Gemessen an dieser Szene: 84,99 m (Szenenbox) gegen 66,39 m (Bauwerksbox), Verhaeltnis
    # 0.781. Die Bauwerksbox holt die Kamera also weiter um knapp 22 % naeher heran.
    assert nah < 0.80 * weit, (nah, weit)


def test_der_knoten_wird_mit_seiner_matrix_verschoben(tmp_path):
    """glTF speichert ``matrix`` SPALTENWEISE. Wer transponiert liest, merkt es nie.

    Bei einer reinen Verschiebung — dem häufigsten Fall — steht der Verschiebungsvektor
    in der letzten *Spalte*. Zeilenweise gelesen landet er in der letzten *Zeile*, wo die
    Rechnung ihn ignoriert: Die Box käme unverschoben und trotzdem plausibel zurück.
    Darum wird hier um einen Betrag verschoben, den keine Symmetrie zurückholt.
    """
    js = json.loads(_json_teil(_erzeuger().baue_glb(
        (("IfcWall_Aussenwand_2xY", (0.0, 0.0, 0.0), (2.0, 3.0, 4.0)),))))
    js["nodes"][0]["matrix"] = [1, 0, 0, 0,
                                0, 1, 0, 0,
                                0, 0, 1, 0,
                                100.0, 200.0, 300.0, 1]          # spaltenweise: T in Spalte 4
    gefunden = glbbox.knotenboxen(js)["knoten"]
    assert len(gefunden) == 1
    _, lo, hi = gefunden[0]
    assert [round(v, 3) for v in lo] == [100.0, 200.0, 300.0], lo
    assert [round(v, 3) for v in hi] == [102.0, 203.0, 304.0], hi


def test_ein_knoten_ohne_min_max_verweigert_die_box_statt_sie_zu_schrumpfen(tmp_path):
    """Kein Rückfall auf eine kleinere Box — die waere die gefaehrlichere Antwort.

    Eine zu kleine Bauwerksbox zieht die Kamera naeher heran, als das Bauwerk gross ist;
    das Bild waere angeschnitten, und der Zahl saehe man nichts an. Dieselbe Haltung wie
    ``blender_depth_stage._bbox_bauwerk``, das ebenfalls ``None`` liefert statt der
    Szenenbox.
    """
    roh = _erzeuger().baue_glb(SZENE)
    js = json.loads(_json_teil(roh))
    del js["accessors"][0]["min"]
    with pytest.raises(glbbox.GlbError) as fehler:
        glbbox.bauwerksbox(_neu_schreiben(tmp_path / "kaputt.glb", js, roh))
    assert "min/max" in str(fehler.value)
    assert "KEINE Box" in str(fehler.value)


# --------------------------------------------------------------------------------------
# 2 · Warum es schnell ist — strukturell statt in Sekunden
# --------------------------------------------------------------------------------------

def test_der_binaerblock_wird_nicht_angefasst(tmp_path, szene_glb):
    """Die Behauptung „0,08 s statt 40 s", als Struktur geprüft.

    Der Grund für die Geschwindigkeit ist nicht schneller Code, sondern **weniger Arbeit**:
    glTF 2.0 verlangt ``min``/``max`` an jedem POSITION-Accessor, also steht die Hüllbox
    im JSON-Kopf und die Dreiecke werden nie gelesen. Bei der Bestandsdatei sind das 2,8
    von 25 MB.

    Wenn das stimmt, muss eine Datei mit **zerstoertem Binaerblock** dieselbe Box liefern.
    Tut sie es nicht, wird doch Geometrie gelesen — und die Zeitschaetzung im Modulkopf
    ist Zufall.
    """
    erwartet = glbbox.bauwerksbox(szene_glb)

    roh = bytearray(szene_glb.read_bytes())
    js_laenge = struct.unpack("<I", roh[12:16])[0]
    beginn_bin = 12 + 8 + js_laenge + 8
    assert beginn_bin < len(roh), "Testaufbau: die Datei hat gar keinen Binaerblock"
    for i in range(beginn_bin, len(roh)):
        roh[i] ^= 0xFF                                    # jedes Byte der Geometrie kippen
    kaputt = tmp_path / "nur_kopf.glb"
    kaputt.write_bytes(bytes(roh))

    assert glbbox.bauwerksbox(kaputt)["bbox_bauwerk"] == erwartet["bbox_bauwerk"]


# --------------------------------------------------------------------------------------
# 3 · Die Regel wird geliehen, nicht nachgebaut
# --------------------------------------------------------------------------------------

def test_es_ist_genau_die_maskenregel_und_keine_zweite():
    """Eine Regel an zwei Stellen ist an einer davon bereits falsch.

    Geprüft wird die **Identität des Objekts**, nicht gleiches Verhalten an Beispielen:
    Verhalten kann zufällig übereinstimmen und beim nächsten Schärfen auseinanderlaufen —
    und die Geländeregel ist im August 2026 zweimal geschärft worden.
    """
    import inspect

    unterschrift = inspect.signature(glbbox.bauwerksbox)
    assert unterschrift.parameters["regel"].default is maske.ist_gelaende


def test_eine_wirkungslose_regel_wird_als_solche_gemeldet(tmp_path):
    """Der Befund vom 01.09.2026: Die Namensregel kann greifen und trotzdem nichts bewirken.

    An einer echten Bestandsdatei sortierte sie acht ``IfcSite``-Knoten aus — und die
    Rahmung wurde davon **2,3 %** enger, weil das eigentliche Gelände ein ``IfcCovering``
    namens ``Toposolid_1`` ist und keines der vier Wörter aus ``maske.GELAENDE_WOERTER``
    trägt. Der Aufruf sah erfolgreich aus.

    Ohne ``schrumpfung`` waere dieser Fall im Bericht nicht von einem zu unterscheiden,
    in dem die Regel wirklich das Gelände entfernt hat.
    """
    szene = (
        # Ein winziges Gelaendestueck, das die Rahmung nicht aendert …
        ("IfcSite_Randstein_0aBcDeFgHiJkLmNoPqR", (0.0, 0.0, 0.0), (0.5, 0.2, 0.5)),
        # … und ein grosses Stueck Gelaende, das die Regel NICHT kennt.
        ("IfcCovering_Toposolid_1aBcDeFgHiJkLmNo", (-30.0, -0.5, -30.0), (30.0, 0.0, 30.0)),
        ("IfcWall_Aussenwand_2aBcDeFgHiJkLmNoPqR", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
    )
    pfad = tmp_path / "toposolid.glb"
    pfad.write_bytes(_erzeuger().baue_glb(szene))

    aus = glbbox.bauwerksbox(pfad)
    assert aus["n_gelaende"] == 1, "der IfcSite-Knoten muss gefunden werden"
    assert aus["schrumpfung"] < glbbox.GERINGE_SCHRUMPFUNG, aus["schrumpfung"]
    assert "wirkt" in aus["note"] and "Toposolid" in aus["note"], aus["note"]


def test_ohne_gelaende_wird_nicht_stillschweigend_die_szenenbox_gemeldet(tmp_path):
    """Gleiche Box, aber mit Vorbehalt — der Unterschied ist der ganze Punkt."""
    pfad = tmp_path / "ohne.glb"
    pfad.write_bytes(_erzeuger().baue_glb(
        (("IfcWall_Aussenwand_3xY", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),)))
    aus = glbbox.bauwerksbox(pfad)
    assert aus["bbox_bauwerk"] == aus["bbox_szene"]
    assert "nicht feststellbar" in aus["note"].lower(), aus["note"]


def test_nur_gelaende_liefert_keine_box(tmp_path):
    """Wortgleich mit ``blender_depth_stage._bbox_bauwerk``: kein Rueckfall, ein Befund."""
    pfad = tmp_path / "nur_gelaende.glb"
    pfad.write_bytes(_erzeuger().baue_glb(
        (("IfcSlab_Gelaende_4xY", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),)))
    aus = glbbox.bauwerksbox(pfad)
    assert aus["bbox_bauwerk"] is None
    assert aus["bbox_szene"] is not None, "die Szene selbst ist ja messbar"
    assert "NICHT auf die Szenenbox zurueckgefallen" in aus["note"]


# --------------------------------------------------------------------------------------
# 4 · Die Achsenfrage — lieber keine Antwort als eine geratene
# --------------------------------------------------------------------------------------

def test_z_up_wird_verweigert_statt_geraten(szene_glb):
    """Dieses Projekt zählt drei unvereinbare Kameraverträge. Ein vierter entsteht hier nicht.

    Der Produktivweg liefert immer ``Y``. Was ``--rotiere-z-up`` in Blender wirklich
    ergibt, ist nicht gemessen — und eine geratene Achsenkonvention sähe im Bericht
    genauso plausibel aus wie eine richtige.
    """
    with pytest.raises(glbbox.GlbError) as fehler:
        glbbox.bauwerksbox(szene_glb, up_axis="Z")
    assert "NICHT GEMESSEN" in str(fehler.value)


def test_die_umrechnung_nach_welt_dreht_wirklich():
    """Y-up → Z-up, an drei ungleichen Kanten, damit eine Verwechslung auffällt.

    An der Bestandsdatei ergibt dieselbe Umrechnung ``[135.75, 136.50, 25.60]`` — genau
    die ``bbox_size_m`` des Blender-Laufs vom 28.08.2026 — und daraus dessen Abstand von
    358,02 m. Hier steht die Probe symbolisch, damit sie ohne jene Datei laufen kann.
    """
    lo, hi = glbbox.nach_welt([1.0, 2.0, 3.0], [11.0, 22.0, 33.0])
    assert lo == [1.0, -33.0, 2.0]
    assert hi == [11.0, -3.0, 22.0]


# --------------------------------------------------------------------------------------
# Hilfsmittel
# --------------------------------------------------------------------------------------

def _json_teil(roh: bytes) -> bytes:
    laenge = struct.unpack("<I", roh[12:16])[0]
    return roh[20:20 + laenge]


def _neu_schreiben(pfad: Path, js: dict, vorlage: bytes) -> Path:
    """Denselben Binärblock, ein geändertes JSON — für gezielt kaputte Dateien."""
    js_laenge = struct.unpack("<I", vorlage[12:16])[0]
    rest = vorlage[20 + js_laenge:]
    neu = json.dumps(js, separators=(",", ":")).encode("utf-8")
    neu += b" " * (-len(neu) % 4)
    kopf = struct.pack("<III", glbbox.GLB_MAGIC, 2, 12 + 8 + len(neu) + len(rest))
    pfad.write_bytes(kopf + struct.pack("<II", len(neu), glbbox.CHUNK_JSON) + neu + rest)
    return pfad
