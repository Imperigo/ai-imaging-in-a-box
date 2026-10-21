"""Die Kontextmaske (Video-Befund L4-5, 21.10.2026) — synthetisch, ohne Blender.

Geprüft wird, was ``maske.kontextmaske`` verspricht: drei Quellen (Splat, Umfeld, Bestand)
mit Namen und Zählung, ``None`` statt einer leeren Maske, wenn der Entwurf allein steht, und
dass die Bauwerksmaske dabei unverändert bleibt — ein Bestandskörper zählt dort weiter als
Bauwerk, bis die Messung am Heim-PC etwas anderes sagt.
"""
from __future__ import annotations

import pytest

from aiimaging import maske

ROT = (255, 38, 38)
GRUEN = (38, 255, 38)
BLAU = (38, 38, 255)
GELB = (255, 255, 38)
TUERKIS = (38, 255, 255)
SCHWARZ = (0, 0, 0)


def _tabelle(*eintraege):
    return [{"index": i, "name": n, "farbe_srgb_8bit": list(f), **({"quelle": q} if q else {})}
            for i, (n, f, q) in enumerate(eintraege)]


TABELLE = _tabelle(("IfcWall_Riegel", ROT, "objekt"), ("IfcSite_Boden", GRUEN, "objekt"),
                   ("Bestand", BLAU, "material"), ("IfcCivilElement_Nachbar", GELB, "objekt"),
                   ("Umgebung", TUERKIS, "kontext"))
#: Zehn Bildpunkte: 3 Bauwerk, 2 Boden, 2 Bestand, 1 Umfeld, 1 Splat, 1 Hintergrund.
FARBEN = [ROT, ROT, ROT, GRUEN, GRUEN, BLAU, BLAU, GELB, TUERKIS, SCHWARZ]


def test_drei_quellen_mit_namen_und_zahl():
    k = maske.kontextmaske(FARBEN, TABELLE)
    assert k["maske"] == [False] * 5 + [True] * 4 + [False]
    assert k["n_kontext"] == 4 and k["n_bildpunkte"] == 10
    assert k["anteil"] == pytest.approx(0.4)
    assert k["quellen"] == {"splat": 1, "umfeld": 1, "bestand": 2}
    assert k["namen"] == {"splat": ["Umgebung"], "umfeld": ["IfcCivilElement_Nachbar"],
                          "bestand": ["Bestand"]}


def test_entwurf_allein_heisst_keine_maske_nicht_leere():
    tab = _tabelle(("IfcWall_Riegel", ROT, "objekt"), ("IfcSite_Boden", GRUEN, "objekt"))
    k = maske.kontextmaske([ROT, GRUEN, SCHWARZ], tab)
    assert k["maske"] is None
    assert k["n_kontext"] == 0
    v = maske.kontext_vermerk(k)
    assert v["allein"] is True and v["anteil"] == 0.0
    assert "maske" not in v


def test_bestandsknoten_aus_der_glb_und_dublettensuffix():
    tab = _tabelle(("Halle_Nord", ROT, "objekt"), ("Bestand.001", BLAU, "material"),
                   ("Riegel", GRUEN, "objekt"))
    k = maske.kontextmaske([ROT, BLAU, GRUEN], tab, bestand_namen=("Halle_Nord",))
    assert k["maske"] == [True, True, False]
    assert k["namen"]["bestand"] == ["Bestand.001", "Halle_Nord"]


def test_kein_wortteil_bestandsaufnahme_ist_kein_koerper():
    assert not maske.ist_bestand("Bestandsaufnahme")
    assert maske.ist_bestand("BESTAND")
    assert maske.ist_bestand("Bestand.003")


def test_die_bauwerksmaske_bleibt_unveraendert():
    """Der Bestandskörper zählt in der Bauwerksmaske weiter als Bauwerk — das ändert erst eine Messung."""
    b = maske.bauwerksmaske(FARBEN, TABELLE)
    assert b["maske"][5] is True and b["maske"][6] is True     # Bestand: weiter Bauwerk
    assert b["maske"][7] is False                              # Umfeld: wie bisher draussen
    assert b["maske"][8] is False                              # Splat: wie bisher draussen


def test_farbkollision_zwischen_quellen_ist_ein_fehler():
    tab = _tabelle(("Bestand", BLAU, "material"), ("IfcCivilElement_X", BLAU, "objekt"))
    with pytest.raises(maske.MaskeError):
        maske.kontextmaske([BLAU], tab)


def test_vermerk_traegt_datei_und_keine_bildpunkte():
    v = maske.kontext_vermerk(maske.kontextmaske(FARBEN, TABELLE), "sSE__kontext_maske.png")
    assert v["datei"] == "sSE__kontext_maske.png"
    assert v["allein"] is False and v["anteil"] == 0.4
    assert maske.kontext_vermerk(None) is None


def test_aus_dem_lauf_liest_png_und_report(tmp_path):
    from aiimaging import bildschreiben
    png = tmp_path / "material_id.png"
    bildschreiben.schreibe_farb_png(png, FARBEN, 5, 2)
    k = maske.kontextmaske_aus_lauf(png, {"material_id_tabelle": TABELLE})
    assert (k["breite"], k["hoehe"]) == (5, 2)
    assert k["n_kontext"] == 4


def test_abholer_legt_die_maske_neben_die_kamera(tmp_path):
    """Am Heim-PC: Vermerk fürs Kameraurteil, Datei ``<kamera>__kontext_maske.png`` (weiss = Kontext)."""
    from aiimaging import abholer, bildlesen, bildschreiben
    png = tmp_path / "material_id.png"
    bildschreiben.schreibe_farb_png(png, FARBEN, 5, 2)
    bericht = {"material_id_png": str(png), "material_id_tabelle": TABELLE}
    v = abholer.kontextmaske_der_kamera(bericht, tmp_path, "sSE", {"namen": ["V1"]})
    assert v["datei"] == "sSE__kontext_maske.png" and v["n_kontext"] == 4
    werte, b, h = bildlesen.lies_png_graustufen(tmp_path / v["datei"])
    assert (b, h) == (5, 2)
    assert [w > 0.5 for w in werte] == [False] * 5 + [True] * 4 + [False]


def test_abholer_ohne_kontext_ohne_datei_und_ohne_pass_nichts(tmp_path):
    from aiimaging import abholer, bildschreiben
    png = tmp_path / "material_id.png"
    tab = _tabelle(("IfcWall_Riegel", ROT, "objekt"), ("IfcSite_Boden", GRUEN, "objekt"))
    bildschreiben.schreibe_farb_png(png, [ROT, GRUEN], 2, 1)
    v = abholer.kontextmaske_der_kamera({"material_id_png": str(png), "material_id_tabelle": tab}, tmp_path, "nNW")
    assert v["allein"] is True and "datei" not in v
    assert not list(tmp_path.glob("*kontext_maske*"))
    assert abholer.kontextmaske_der_kamera({}, tmp_path, "nNW") is None
    kaputt = abholer.kontextmaske_der_kamera({"material_id_png": str(png), "material_id_tabelle": []}, tmp_path, "x")
    assert kaputt["gemessen"] is False and "MaskeError" in kaputt["grund"]
