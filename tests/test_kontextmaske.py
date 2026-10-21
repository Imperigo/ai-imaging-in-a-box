"""Die Kontextmaske (Video-Befund L4-5, 21.10.2026) — synthetisch, ohne Blender.

Geprüft wird, was ``maske.kontextmaske`` verspricht: drei Quellen (Splat, Umfeld, Bestand)
mit Namen und Zählung, ``None`` statt einer leeren Maske, wenn der Entwurf allein steht. Seit
auf-20261021-313 (B1: Bestand 35,9 % der Bauwerksmaske) fällt der Bestand aus der Bauwerksmaske
und steht nur noch in der Kontextmaske; seit 313 B2 entsteht sie auch bei «nur Grundlage».
"""
from __future__ import annotations

from pathlib import Path

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


def test_der_bestand_faellt_aus_der_bauwerksmaske_das_umfeld_wie_bisher():
    """313 B1: Bestand ist Kontext, nicht Entwurf — er steht in der Kontextmaske, nicht im Bauwerk."""
    b = maske.bauwerksmaske(FARBEN, TABELLE)
    assert b["maske"][:3] == [True] * 3                        # das Bauwerk bleibt
    assert b["maske"][5] is False and b["maske"][6] is False   # Bestand: draussen
    assert b["maske"][7] is False                              # Umfeld: wie bisher draussen
    assert b["maske"][8] is False                              # Splat: wie bisher draussen
    assert b["bestand_namen"] == ["Bestand"] and "Bestand" not in b["bauwerk_namen"]
    assert b["n_bauwerk"] == 3
    k = maske.kontextmaske(FARBEN, TABELLE)
    assert k["maske"][5] and k["maske"][6]


def test_bestandsknoten_nach_namen_fallen_aus_der_bauwerksmaske_wie_in_313():
    """313 A: die Knoten heissen wie Bauteile (IfcBuildingElementProxy_Bestand_A) — nur die
    Namen aus der glb (``bestand_namen``) erkennen sie."""
    tab = _tabelle(("IfcWall_Hauptbau", ROT, "objekt"), ("IfcSite_Boden", GRUEN, "objekt"),
                   ("IfcBuildingElementProxy_Bestand_A", BLAU, "objekt"))
    farben = [ROT, ROT, BLAU, GRUEN]
    ohne = maske.bauwerksmaske(farben, tab)
    assert ohne["maske"] == [True, True, True, False]          # ohne Namen nicht erkannt
    mit = maske.bauwerksmaske(farben, tab,
                              bestand_namen=("IfcBuildingElementProxy_Bestand_A",))
    assert mit["maske"] == [True, True, False, False]
    assert mit["bestand_namen"] == ["IfcBuildingElementProxy_Bestand_A"]
    assert mit["gelaende_erkannt"] is True


def test_der_maskenweg_des_abholers_reicht_die_bestandsnamen_durch(tmp_path):
    from aiimaging import abholer, bildschreiben
    tab = _tabelle(("IfcWall_Hauptbau", ROT, "objekt"), ("IfcSite_Boden", GRUEN, "objekt"),
                   ("Halle_Nord", BLAU, "objekt"))
    png = tmp_path / "material_id.png"
    bildschreiben.schreibe_farb_png(png, [ROT, BLAU, GRUEN, SCHWARZ], 2, 2)
    bericht = {"material_id_png": str(png), "material_id_tabelle": tab}
    befund = abholer._maske_bauen(bericht, bestand_namen=abholer._bestandsnamen(
        {"namen": ["Halle_Nord"]}))
    assert befund["maske"] == [True, False, False, False]
    assert abholer._bestandsnamen(None) == () and abholer._bestandsnamen({}) == ()


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


def test_nur_grundlage_traegt_die_kontextmaske_313_b2(tmp_path):
    """313 B2: Die Kontextmaske liest nur den Material-ID-Pass und gehört zur Grundlage — sie
    entsteht jetzt auch bei «Grundlage rendern», mit Datei und Vermerk wie im KI-Lauf."""
    import json

    from aiimaging import abholer, bildschreiben
    from test_kettenlauf_26august import MINI_PNG, _auftragsordner, _kette, _lauf

    ordner = _auftragsordner(tmp_path / "a", skip=True)
    _protokoll, attrappen = _kette(tmp_path)
    alt = attrappen["_multipass"]

    def multipass(glb, aus, **kw):
        bericht = alt(glb, aus, **kw)
        png = Path(aus) / "material_id.png"
        bildschreiben.schreibe_farb_png(png, FARBEN, 5, 2)
        schoen = Path(aus) / "schoen.png"
        schoen.write_bytes(MINI_PNG)
        return dict(bericht, material_id_png=str(png), material_id_tabelle=TABELLE,
                    beauty_png=str(schoen))

    antwort = _lauf(tmp_path, ordner, dict(attrappen, _multipass=multipass))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    urteile = [json.loads(p.read_text(encoding="utf-8"))
               for p in (tmp_path / "aus").rglob("urteil.json")]
    assert urteile
    for u in urteile:
        km = u["urteil"]["kontext_maske"]
        assert km["n_kontext"] == 4 and km["datei"].endswith("__kontext_maske.png")
