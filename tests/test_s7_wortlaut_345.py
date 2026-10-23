"""Ergebnis 345, Nachtrag S7 — zwei Sätze im Befund, die dem Urteil widersprachen.

**Anlass (auf-20261023-345, S7, echter IFC-Export R57, alles grün):**

1. Die Bauwerksmaske meldete unter ``warnungen`` «Kein Gelände erwartet, aber die Datei weist
   […] selbst als Boden aus (extras.role 'ground') …». Das Gelände war richtig behandelt; der
   Schalter «kein Gelände erwartet» ist am Heim-PC eine Dauereinstellung
   (``tools/abholen.py --kein-gelaende``), keine Aussage über die Datei. Jetzt steht ein
   ruhiger Satz «Gelände aus der Datei: …» unter ``auskunft``, nicht unter ``warnungen``.
2. Der Kontrastbefund trug ``kaum_sichtbar: true`` (Mittelwert −15,7), während die Warnung am
   Umriss (55,5) richtig schwieg. Jetzt folgt der Schalter demselben Urteil
   (``belichtung.haus_kaum_sichtbar``: Umriss, Rückfall Mittelwert); die Mittelwertantwort
   steht als ``kaum_sichtbar_mittelwert`` daneben.

Jede Probe mit «GEGEN ALT ROT» ist gegen den alten Stand rot. Ohne GPU. Regel 3: synthetisch.
"""
from __future__ import annotations

from aiimaging import belichtung, kosmo_szene, maske

# ====================================================================== 1 · Gelände aus der Datei

ROT, GRUEN = (255, 38, 38), (38, 255, 38)
FLAECHE = "IfcGeographicElement_gelaendeflaeche_gewachse_X"
TABELLE = [{"index": 0, "name": "IfcWall_Wand_1", "quelle": "objekt",
            "farbe_srgb_8bit": list(ROT)},
           {"index": 1, "name": FLAECHE, "quelle": "objekt", "farbe_srgb_8bit": list(GRUEN)}]
FARBEN = [ROT, ROT, GRUEN, GRUEN, GRUEN, (0, 0, 0)]


def test_gelaende_mit_rolle_ist_keine_warnung_bei_kein_gelaende_erwartet():
    """GEGEN ALT ROT: der Satz «Kein Gelände erwartet, aber …» stand unter ``warnungen``."""
    m = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_erwartet=False, gelaende_rolle=(FLAECHE,))
    assert m["warnungen"] == []
    assert not any("Kein Gelände erwartet" in w for w in m["warnungen"])
    satz, = m["auskunft"]
    assert satz.startswith("Gelände aus der Datei:") and FLAECHE in satz
    # Gehandelt wird wie bisher: das Gelände ist nicht Bauwerk.
    assert m["maske"] == [True, True, False, False, False, False]
    assert m["gelaende_quelle"] == "name+rolle"


def test_derselbe_satz_auch_mit_erwartetem_gelaende():
    """Ob der Schalter steht oder nicht: dieselbe Datei, derselbe Befund."""
    ohne = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_erwartet=False,
                               gelaende_rolle=(FLAECHE,))
    mit = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_rolle=(FLAECHE,))
    assert mit["auskunft"] == ohne["auskunft"] and mit["warnungen"] == []
    assert mit["maske"] == ohne["maske"]


def test_ohne_rolle_bleibt_der_widerspruch_eine_warnung():
    """Die Namensregel gegen den Schalter ist weiter eine Abweichung — dort bleibt es laut."""
    tabelle = [dict(TABELLE[0]), dict(TABELLE[1], name="Gelaende")]
    m = maske.bauwerksmaske(FARBEN, tabelle, gelaende_erwartet=False)
    assert any("Eine der beiden Angaben stimmt nicht" in w for w in m["warnungen"])
    assert m["auskunft"] == []


def test_maske_aus_bericht_traegt_die_auskunft_mit(tmp_path):
    from aiimaging import bildschreiben
    png = tmp_path / "material_id.png"
    bildschreiben.schreibe_farb_png(png, FARBEN, 3, 2)
    bericht = {"material_id_png": str(png), "material_id_tabelle": TABELLE}
    aus = maske.maske_aus_bericht(bericht, gelaende_erwartet=False, gelaende_rolle=(FLAECHE,))
    assert aus["gemessen"] is True and aus["warnungen"] == []
    assert aus["auskunft"][0].startswith("Gelände aus der Datei:")


# ====================================================================== 2 · kaum_sichtbar folgt dem Umriss

def _s7_artig(b=40, h=30):
    """Haus mit heller Sonnen- und dunkler Schattenseite, Mittel etwas dunkler als der Himmel,
    am Umriss klar abgesetzt — dieselbe Lage wie S7 (Mittel −15,7, Umriss 55,5)."""
    farben, haus = [], []
    for y in range(h):
        for x in range(b):
            drin = 10 <= x < 30 and 10 <= y < h
            haus.append(drin)
            g = (180 if x < 20 else 50) if drin else 130
            farben.append((g, g, g))
    return farben, haus, [not m for m in haus]


def test_schalter_folgt_dem_umriss():
    """GEGEN ALT ROT: ``kaum_sichtbar`` war der Mittelwert allein (|−15| < 20 → true)."""
    farben, haus, grund = _s7_artig()
    k = belichtung.kontrast_haus_hintergrund(farben, 40, 30, haus=haus, hintergrund=grund)
    assert abs(k["kontrast"]) < belichtung.KONTRAST_SCHWELLE
    assert k["umriss"]["betrag"] > belichtung.KONTRAST_UMRISS_SCHWELLE
    assert k["kaum_sichtbar"] is False and k["kaum_sichtbar_regel"] == "umriss"
    assert k["kaum_sichtbar_mittelwert"] is True, "die Mittelwertantwort bleibt als Auskunft"


def test_schalter_und_warnung_sagen_dasselbe():
    """Befund und ``hinweise`` dürfen sich nicht widersprechen — gleiches Urteil, gleiche Zahl."""
    farben, haus, grund = _s7_artig()
    k = belichtung.kontrast_haus_hintergrund(farben, 40, 30, haus=haus, hintergrund=grund)
    urteil = {"kamera": "Eingang", "score": None, "bestanden": None, "kontrast": k}
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=urteil,
                                 je_kamera=[{"kamera": "Eingang", "geometrie_urteil": urteil}])
    gewarnt = any(h.startswith(kosmo_szene.SATZ_KAUM_SICHTBAR) for h in e["hinweise"])
    assert gewarnt is k["kaum_sichtbar"] is False


def test_ohne_umriss_gilt_der_mittelwert_als_rueckfall():
    """Grenzt das Haus nirgends an Himmel (Umriss None), entscheidet der Mittelwert wie bis 344."""
    b, h = 6, 4
    haus = [x < 4 for y in range(h) for x in range(b)]
    grund = [x == 5 for y in range(h) for x in range(b)]   # Gelände dazwischen, nie am Umriss
    farben = [(131, 131, 131) if m else (130, 130, 130) for m in haus]
    k = belichtung.kontrast_haus_hintergrund(farben, b, h, haus=haus, hintergrund=grund)
    assert k["umriss"]["betrag"] is None
    assert k["kaum_sichtbar"] is True and k["kaum_sichtbar_regel"] == "mittelwert"
    assert k["kaum_sichtbar"] == k["kaum_sichtbar_mittelwert"]
