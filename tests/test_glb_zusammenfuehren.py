"""Zwei glb zu einer — Situationsmodell und Umgebungsbauten (Vorbereitung 25.10.2026, ``tools/glb_zusammenfuehren.py``).

Alles synthetisch (Regel 3): das Situationsmodell aus ``make_test_glb.situationsszene`` (frei erfunden), die
Umgebungsbauten als hohe Quader daneben. Geprüft:

1. Die zweite Datei steht ganz in der ersten — jeder Knoten mit seiner Box, die Puffer heil (die Ecken eines
   Umgebungsbaus lesen sich im Ergebnis wie in der Quelle), die erste unverändert vorne.
2. Jeder Knoten der zweiten trägt ``extras.aiimaging_quelle = "umgebung"``, die Namen bleiben.
3. Die Kette nimmt die Umgebungsbauten als Bauten (Bauwerksbox, Umfeld-Cluster), und der Hauptbau des Umfelds
   bleibt der am Blickziel — auch wenn ein Umgebungsbau höher und grösser ist.
4. Der Bericht nennt nur Zahlen; das Werkzeug weist falsche Aufrufe ab.
"""
from __future__ import annotations

import importlib.util
import json
import struct
from pathlib import Path

import pytest

from aiimaging import glbbox, kameras, umfeld

WURZEL = Path(__file__).resolve().parents[1]


def _laden(name, datei):
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    m = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mg():
    return _laden("make_test_glb_zus", "make_test_glb.py")


@pytest.fixture(scope="module")
def zus():
    return _laden("glb_zusammenfuehren_pruefling", "glb_zusammenfuehren.py")


#: Umgebungsbauten (glTF: x, y oben, z): hoch, um die Anlage herum — der grösste höher als alles im Modell.
UMGEBUNG = (("IfcBuildingElementProxy_1", (-320.0, 0.0, -60.0), (-280.0, 86.0, -20.0)),
            ("IfcBuildingElementProxy_2", (290.0, 0.0, 30.0), (322.0, 24.0, 70.0)),
            ("IfcBuildingElementProxy_3", (-40.0, 0.0, 220.0), (0.0, 18.0, 245.0)))


def _paar(mg, tmp_path):
    a = tmp_path / "situation.glb"
    b = tmp_path / "umgebung.glb"
    a.write_bytes(mg.baue_glb(mg.situationsszene(), materialien=["Beton", "Glas"]))
    b.write_bytes(mg.baue_glb(UMGEBUNG, materialien=["Putz"]))
    return a, b


def test_die_zweite_steht_ganz_in_der_ersten(mg, zus, tmp_path):
    a, b = _paar(mg, tmp_path)
    neu, bericht = zus.fuehre_zusammen(a.read_bytes(), b.read_bytes())
    ziel = tmp_path / "zusammen.glb"
    ziel.write_bytes(neu)
    ja, jb, jz = (glbbox.lies_gltf_json(p) for p in (a, b, ziel))
    kz = {n: (lo, hi) for n, lo, hi in glbbox.knotenboxen(jz)["knoten"]}
    for js in (ja, jb):
        for name, lo, hi in glbbox.knotenboxen(js)["knoten"]:
            assert kz[name] == (lo, hi), name
    assert len(jz["nodes"]) == len(ja["nodes"]) + len(jb["nodes"])
    assert jz["nodes"][:len(ja["nodes"])] == ja["nodes"]                  # die erste unverändert vorne
    assert len(jz["materials"]) == len(ja["materials"]) + len(jb["materials"])
    # Die Puffer heil: die Ecken eines Umgebungsbaus aus dem Ergebnis gelesen = die aus der Quelle.
    assert _ecken(ziel, "IfcBuildingElementProxy_1") == _ecken(b, "IfcBuildingElementProxy_1")
    assert _ecken(ziel, "IfcSlab_Decke_0_0") == _ecken(a, "IfcSlab_Decke_0_0")
    assert bericht["knoten"] == {"situation": len(ja["nodes"]), "umgebung": 3, "zusammen": len(jz["nodes"])}
    assert bericht["liegen_uebereinander"] is False                       # die Umgebung liegt um die Anlage
    assert bericht["huellbox_gltf"]["zusammen"][1][1] == 86.0


def _ecken(pfad, name):
    js, binaer = _lies(pfad)
    i = next(k for k, n in enumerate(js["nodes"]) if n.get("name") == name)
    zugriff = js["accessors"][js["meshes"][js["nodes"][i]["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
    sicht = js["bufferViews"][zugriff["bufferView"]]
    start = int(sicht.get("byteOffset") or 0) + int(zugriff.get("byteOffset") or 0)
    return [struct.unpack_from("<3f", binaer, start + 12 * k) for k in range(zugriff["count"])]


def _lies(pfad):
    daten = Path(pfad).read_bytes()
    n = struct.unpack_from("<I", daten, 12)[0]
    js = json.loads(daten[20:20 + n])
    m = struct.unpack_from("<I", daten, 20 + n)[0]
    return js, daten[28 + n:28 + n + m]


def test_umgebung_ist_markiert_und_behaelt_die_namen(mg, zus, tmp_path):
    a, b = _paar(mg, tmp_path)
    neu, _ = zus.fuehre_zusammen(a.read_bytes(), b.read_bytes())
    (tmp_path / "z.glb").write_bytes(neu)
    js = glbbox.lies_gltf_json(tmp_path / "z.glb")
    umg = [n for n in js["nodes"] if (n.get("extras") or {}).get(zus.QUELLE_FELD) == zus.QUELLE_UMGEBUNG]
    assert sorted(n["name"] for n in umg) == [u[0] for u in UMGEBUNG]
    assert not any((n.get("extras") or {}).get(zus.QUELLE_FELD) for n in js["nodes"][:-3])
    assert set(js["scenes"][js.get("scene", 0)]["nodes"]) >= {len(js["nodes"]) - 3 + i for i in range(3)}


def test_die_kette_nimmt_die_umgebung_als_bauten_und_der_hauptbau_bleibt_am_blickziel(mg, zus, tmp_path):
    """Die Umgebungsbauten zählen in der Bauwerksbox und als Bauten im Umfeld; der Hauptbau ist der am Blickziel
    (der grosse Bau in der Mitte des Modells), nicht der 86-m-Umgebungsbau."""
    a, b = _paar(mg, tmp_path)
    neu, _ = zus.fuehre_zusammen(a.read_bytes(), b.read_bytes())
    ziel = tmp_path / "z.glb"
    ziel.write_bytes(neu)
    box = glbbox.bauwerksbox(ziel)
    assert box["bbox_bauwerk"][1][2] >= 86.0 - 1e-6, box                  # Welt: Z oben, der hohe Bau zählt
    gelesen = umfeld.lies_glb_umfeld(ziel)
    bauten = [c for c in umfeld.grundriss_cluster(gelesen["bauwerk_boxen"]) if c["bau"]]
    assert len(bauten) >= 6 + 3 - 1
    assert max(c["hoehe_m"] for c in bauten) >= 86.0 - 1e-6                 # der hohe Umgebungsbau ist ein Bau
    # Kamera auf den grossen Bau der Anlage (glTF x −10, z −20 → Welt x −10, y 20).
    kam = kameras.vogelschau([[-80.0, -40.0, 0.0], [60.0, 80.0, 25.0]], kuerzel="sSE")
    plan = umfeld.plane_fuer_glb(ziel, wunsch={"kategorien": ["baeume"], "dichte": "mittel", "seed": 0},
                                 kameras=[{"kuerzel": "zelle-sSE", "auge": kam["auge"], "blick_auf": [-10.0, 20.0, 5.0],
                                           "brennweite_mm": kam["brennweite_mm"],
                                           "seitenverhaeltnis": kam["seitenverhaeltnis"]}])
    hb = plan["hauptbau"]
    assert hb["gewaehlt"] == "blickziel"
    (x0, y0), (x1, y1) = hb["box"]
    assert x0 <= -10.0 <= x1 and y0 <= 20.0 <= y1, hb["box"]
    assert hb["flaeche_m2"] == pytest.approx(70.0 * 40.0)                   # der grosse Bau der Anlage, kein Umgebungsbau


def test_werkzeug_bericht_nur_zahlen_und_abweisungen(mg, zus, tmp_path, capsys):
    a, b = _paar(mg, tmp_path)
    ziel = tmp_path / "z.glb"
    assert zus.main([str(a), str(b), str(ziel)]) == 0
    text = capsys.readouterr().out
    bericht = json.loads(text)
    assert "IfcBuilding" not in text and "IfcSlab" not in text and str(tmp_path) not in text
    assert bericht["knoten"]["umgebung"] == 3
    assert bericht["situationsmodell"]["situation"]["ja"] is True
    assert bericht["situationsmodell"]["zusammen"]["ja"] is True and bericht["situationsmodell"]["satz"] is None
    assert zus.main([str(a), str(b), str(ziel)]) == 2                      # Ziel vorhanden
    assert zus.main([str(a), str(b), str(a)]) == 2                         # Ziel ist Eingabe
    assert zus.main([str(a), str(b), str(a), "--ueberschreiben"]) == 2
    assert zus.main([str(a), str(b), str(tmp_path / "z.gltf")]) == 2
    kaputt = tmp_path / "kaputt.glb"
    kaputt.write_bytes(b"nicht")
    assert zus.main([str(a), str(kaputt), str(tmp_path / "y.glb")]) == 1


def test_werkzeug_sagt_wenn_das_modell_kein_situationsmodell_mehr_ist(mg, zus, tmp_path, capsys):
    """86 m hohe Umgebungsbauten auf einer schmaleren Anlage: über 15 % der Breite — das Modell fiele aus der
    Vogelschau. Das Werkzeug sagt es (Bericht und Satz), statt still ein Haus daraus zu machen."""
    a = tmp_path / "situation.glb"
    b = tmp_path / "umgebung.glb"
    a.write_bytes(mg.baue_glb(mg.situationsszene()))
    b.write_bytes(mg.baue_glb((("IfcBuildingElementProxy_9", (-20.0, 0.0, -60.0), (20.0, 120.0, -20.0)),)))
    assert zus.main([str(a), str(b), str(tmp_path / "z.glb")]) == 0
    aus = capsys.readouterr()
    bericht = json.loads(aus.out)
    assert bericht["situationsmodell"]["situation"]["ja"] is True
    assert bericht["situationsmodell"]["zusammen"]["ja"] is False
    assert "nicht mehr als Situationsmodell" in aus.err
