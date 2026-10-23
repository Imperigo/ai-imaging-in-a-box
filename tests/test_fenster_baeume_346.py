"""Ergebnis auf-20261023-346: zwei Befunde, nachgezogen ohne GPU.

1. **F3 (ROT):** Die Fensterprüfung v1 nannte das übermalte OG-Band der Vorschau «gehalten»
   (0,641 über 0,5). Die helle graue Lattung (KI 142/142/143) lag näher am hellblauen Glas des
   Grundbilds (158/178/190) als am dunklen Median der KI-«Fassade» (99/94/93), der Bäume, Weg
   und Terrasse mitzählte. Seit v2 prüft der Farbton mit (Blau minus Rot), und der
   Fassaden-Median zählt nur Bauwerk.
2. **F5:** Bäume lagen ganz in der Bauwerksmaske (``Baum_Laub``/``Baum_Stamm`` in
   ``bauwerk_namen``, ``umfeld_namen`` leer). Seit 346 sind Vegetationswörter Umfeld.

Die Farben unten sind die Mittelwerte aus 346 (Kamera sSE, «haus-am-hang», synthetisch).
"""
from __future__ import annotations

import pytest

from aiimaging import maske, varianten

B, H = 60, 40
GLAS_ID, BETON_ID, LAUB_ID, STAMM_ID, TERRASSE_ID = (
    (10, 200, 30), (200, 10, 10), (10, 10, 200), (200, 200, 10), (200, 10, 200))
TABELLE = [
    {"index": 0, "name": "Sichtbeton", "farbe_srgb_8bit": list(BETON_ID)},
    {"index": 1, "name": "Glas_Fensterband", "farbe_srgb_8bit": list(GLAS_ID)},
    {"index": 2, "name": "Baum_Laub", "farbe_srgb_8bit": list(LAUB_ID)},
    {"index": 3, "name": "Baum_Stamm", "farbe_srgb_8bit": list(STAMM_ID)},
    {"index": 4, "name": "Terrasse_Holzdeck", "farbe_srgb_8bit": list(TERRASSE_ID)},
]

# --- Farben aus 346 (Grundbild S1, volle Güte S2 V05, Vorschau S2m) -------------------------
GRUND = {"glas": (158, 178, 190), "beton": (118, 116, 114), "laub": (104, 136, 102),
         "stamm": (90, 75, 60), "terrasse": (120, 100, 80)}
VOLL = {"glas_og": (158, 176, 186), "glas_eg": (155, 171, 179), "beton": (117, 115, 113),
        "laub": (107, 135, 104), "stamm": (90, 76, 61), "terrasse": (121, 101, 81)}
VORSCHAU = {"glas_og": (142, 142, 143), "glas_eg": (163, 142, 101), "beton": (100, 95, 94),
            "laub": (85, 77, 80), "stamm": (70, 60, 58), "terrasse": (95, 85, 80)}


def _teil(x, y):
    """Was an (x, y) steht: Baum links, Haus mit OG-Band und EG-Glas, Terrasse davor."""
    if x < 14:
        return "stamm" if y >= 30 else "laub"
    if 16 <= x < 58 and 4 <= y < 32:
        if 18 <= x < 56 and 10 <= y < 15:
            return "glas_og"            # das OG-Band: 38 x 5 = 190 Punkte
        if 22 <= x < 50 and 22 <= y < 26:
            return "glas_eg"            # EG-Glas: 28 x 4 = 112 Punkte
        return "beton"
    if 16 <= x < 58 and 32 <= y < 37:
        return "terrasse"
    return None                          # Himmel/Gelaende: nicht im ID-Pass


KENNUNG = {"glas_og": GLAS_ID, "glas_eg": GLAS_ID, "beton": BETON_ID, "laub": LAUB_ID,
           "stamm": STAMM_ID, "terrasse": TERRASSE_ID}
HIMMEL = (170, 190, 215)


def _bild(farben, grund=False):
    aus = []
    for y in range(H):
        for x in range(B):
            t = _teil(x, y)
            if t is None:
                aus.append(HIMMEL)
            elif grund and t.startswith("glas"):
                aus.append(GRUND["glas"])
            else:
                aus.append(farben[t])
    return aus


KENN = [KENNUNG[t] if (t := _teil(x, y)) else (0, 0, 0) for y in range(H) for x in range(B)]
#: Die Maske wie am Mac vor 346: Bäume und Terrasse liegen darin.
MASKE_ALT = [k != (0, 0, 0) for k in KENN]
GRUNDBILD = _bild(GRUND, grund=True)
GLAS = varianten.glasfarben(TABELLE)


def _v1(ki, grund, kennung, glas, maske_):
    """Die Regel v1 (bis 346), nachgebaut: nur Helligkeit, Median über alles ausser Glas."""
    glas_i = [i for i, k in enumerate(kennung) if maske_[i] and k in glas]
    fassade = [i for i, k in enumerate(kennung) if maske_[i] and k not in glas]
    med = varianten._median_je_kanal([ki[i] for i in fassade])
    t = sum(1 for i in glas_i
            if varianten._abstand(ki[i], grund[i]) <= varianten._abstand(ki[i], med))
    return t / len(glas_i)


def test_die_regel_v1_haette_die_vorschau_gehalten_genannt():
    """Der Befund aus 346, an den 346-Farben nachgestellt: v1 über der Schwelle."""
    assert _v1(_bild(VORSCHAU), GRUNDBILD, KENN, GLAS, MASKE_ALT) >= 0.5


def test_die_vorschau_faellt_auf():
    befund = varianten.fenster_gehalten(_bild(VORSCHAU), GRUNDBILD, KENN, GLAS, maske=MASKE_ALT,
                                        ausser=varianten.nicht_fassade_farben(TABELLE))
    assert befund["farbton"] is True and befund["farbton_trennung"] >= 30
    assert befund["gehalten"] is False and befund["anteil"] < 0.2, befund


def test_volle_guete_haelt():
    befund = varianten.fenster_gehalten(_bild(VOLL), GRUNDBILD, KENN, GLAS, maske=MASKE_ALT,
                                        ausser=varianten.nicht_fassade_farben(TABELLE))
    assert befund["gehalten"] is True and befund["anteil"] >= 0.95, befund


def test_auch_ohne_ausser_trennt_der_farbton():
    """Selbst mit Bäumen im Median (alte Maske, ohne ``ausser``) trennt der Farbton."""
    vorschau = varianten.fenster_gehalten(_bild(VORSCHAU), GRUNDBILD, KENN, GLAS, maske=MASKE_ALT)
    voll = varianten.fenster_gehalten(_bild(VOLL), GRUNDBILD, KENN, GLAS, maske=MASKE_ALT)
    assert vorschau["gehalten"] is False and voll["gehalten"] is True


def test_graues_glas_prueft_nur_die_helligkeit():
    """Ist das Glas im Grundbild nicht bläulicher als die Fassade, prüft der Farbton nicht mit."""
    grau = (40, 40, 42)
    grund = [grau if KENN[i] == GLAS_ID else p for i, p in enumerate(GRUNDBILD)]
    befund = varianten.fenster_gehalten(grund, grund, KENN, GLAS, maske=MASKE_ALT)
    assert befund["farbton"] is False and befund["gehalten"] is True


def test_waermere_stimmung_behaelt_das_glas():
    """Abendlicht: alles röter — gegen die KI-Fassade gemessen bleibt das Glas bläulicher."""
    def abend(p):
        return (min(255, p[0] + 30), p[1], max(0, p[2] - 30))
    ki = [abend(p) for p in _bild(VOLL)]
    befund = varianten.fenster_gehalten(ki, GRUNDBILD, KENN, GLAS, maske=MASKE_ALT,
                                        ausser=varianten.nicht_fassade_farben(TABELLE))
    assert befund["gehalten"] is True, befund


def test_aus_den_dateien_zaehlen_baeume_nicht_zur_fassade(tmp_path):
    from aiimaging import bildschreiben
    pfade = {}
    for name, farben in (("ki", _bild(VORSCHAU)), ("grund", GRUNDBILD), ("id", KENN)):
        pfade[name] = tmp_path / f"{name}.png"
        bildschreiben.schreibe_farb_png(pfade[name], farben, B, H)
    befund = varianten.fenster_aus_bildern(pfade["ki"], pfade["grund"], pfade["id"], TABELLE,
                                           maske=MASKE_ALT)
    assert befund["gehalten"] is False and "v2" in befund["methode"]


def test_nicht_fassade_sind_baeume_und_gelaende_nie_glas():
    tabelle = TABELLE + [{"name": "Gelaende_Hang", "farbe_srgb_8bit": [1, 2, 3]},
                         {"name": "Glas_Baum_Vitrine", "farbe_srgb_8bit": [4, 5, 6]}]
    farben = varianten.nicht_fassade_farben(tabelle)
    assert farben == {LAUB_ID, STAMM_ID, (1, 2, 3)}


# ============================================================ 2 · Bäume als Umfeld

@pytest.mark.parametrize("name", [
    "Baum_Laub", "Baum_Stamm", "Baum_Laub.001", "Tree", "tree_02", "Hecke Nord", "Strauch-3",
    "Bush", "Vegetation", "Pflanze_Topf", "Bäume", "IfcGeographicElement_Baum_01",
])
def test_vegetation_ist_umfeld(name):
    assert maske.ist_umfeld(name) is True


@pytest.mark.parametrize("name", [
    "Laubengang", "Stammhaus", "Baumeister",
    "Gelaender_Balkon", "Plant_Room", "Gras", "Wiese", "Sichtbeton", "Mauerkrone",
    "Gelaende_Baum",          # das Geländewort geht vor (wie R56)
])
def test_kein_umfeld(name):
    assert maske.ist_umfeld(name) is False


def test_die_wortliste_bleibt_klein_und_ohne_abgelehnte_woerter():
    assert len(maske.UMFELD_WOERTER) <= 20
    assert not set(maske.UMFELD_WOERTER) & set(maske.WOERTER_AUSDRUECKLICH_NICHT)
    assert not set(maske.UMFELD_WOERTER) & set(maske.GELAENDE_WOERTER)


def test_baeume_liegen_nicht_mehr_in_der_bauwerksmaske():
    """346 F5: ``umfeld_namen`` war leer, ``Baum_Laub`` stand unter ``bauwerk_namen``."""
    ergebnis = maske.bauwerksmaske(KENN, TABELLE, gelaende_erwartet=False)
    assert set(ergebnis["umfeld_namen"]) == {"Baum_Laub", "Baum_Stamm"}
    assert "Baum_Laub" not in ergebnis["bauwerk_namen"]
    assert "Sichtbeton" in ergebnis["bauwerk_namen"]
    baum = [i for i, k in enumerate(KENN) if k in (LAUB_ID, STAMM_ID)]
    assert baum and not any(ergebnis["maske"][i] for i in baum)
    assert any("UMFELD AUSGESCHLOSSEN" in w and "Baum_Laub" in w for w in ergebnis["warnungen"])


def test_die_kontextmaske_zaehlt_die_baeume_als_umfeld():
    k = maske.kontextmaske(KENN, TABELLE)
    assert sorted(k["namen"]["umfeld"]) == ["Baum_Laub", "Baum_Stamm"]
