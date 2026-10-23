"""Mac-Befund 23.10.2026 («haus-am-hang», synthetisch): Fensterband übermalt, QA «bestanden».

Bei Bildeingang 0,5 (Vorgabe E138) malte die KI das schmale Fensterband im OG mit Lattung zu.
Drei Teile, alle ohne GPU geprüft:

1. **«Fenster gehalten»** (``varianten.fenster_gehalten``): Anteil der Glas-Bildpunkte des
   ID-Passes, die im KI-Bild dem Grundbild näher sind als der KI-Fassade — mit einem Satz in
   ``qa.verdict.hinweise`` unter der (gesetzten) Schwelle, sonst still. Kein Tor.
2. **``vis.glas_satz``** — Messschalter, Vorgabe aus: ein Glassatz ohne Bauteilwort vorne.
3. **``vis.material_vorne_nennungen``** — Messschalter, Vorgabe 3: der Stoff vorne seltener.

Und der Messauftrag auf-20261023-346, der die drei am Heim-PC misst.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from aiimaging import abholer, auftrag, bildschreiben, kosmo_szene, prompts, varianten

WURZEL = Path(__file__).resolve().parents[1]

# ============================================================ 1 · ein synthetisches Haus

B, H = 40, 30
GLAS_ID, LATTE_ID = (10, 200, 30), (200, 10, 10)
LATTUNG = (170, 130, 90)       # helles Holz
GLAS = (40, 60, 90)            # dunkles, bläuliches Glas
HIMMEL = (150, 190, 230)
TABELLE = [{"index": 0, "name": "Lattung Fichte", "farbe_srgb_8bit": list(LATTE_ID)},
           {"index": 1, "name": "Glas", "farbe_srgb_8bit": list(GLAS_ID)}]


def _haus(x, y):
    return 5 <= x < 35 and 5 <= y < 28


def _band(x, y):
    """Das Fensterband im OG: drei Zeilen über fast die ganze Breite."""
    return 7 <= x < 33 and 10 <= y < 13


def _bild(farbe_von):
    return [farbe_von(x, y) for y in range(H) for x in range(B)]


def _latte(x, y):
    # Lattung mit Fugen, damit das Bild Kanten hat wie eine echte Holzfassade.
    return (120, 90, 60) if x % 3 == 0 else LATTUNG


def _grundbild(x, y):
    if not _haus(x, y):
        return HIMMEL
    return GLAS if _band(x, y) else _latte(x, y)


def _ki_uebermalt(x, y):
    """Die KI malt Lattung über das Band — wie am Mac."""
    return _latte(x, y) if _haus(x, y) else HIMMEL


def _kennung(x, y):
    if not _haus(x, y):
        return (0, 0, 0)
    return GLAS_ID if _band(x, y) else LATTE_ID


MASKE = _bild(_haus)


def test_gehaltenes_glas_zaehlt_ganz():
    befund = varianten.fenster_gehalten(_bild(_grundbild), _bild(_grundbild), _bild(_kennung),
                                        varianten.glasfarben(TABELLE), maske=MASKE)
    assert befund["anteil"] == 1.0 and befund["gehalten"] is True
    assert befund["n_glas"] == 26 * 3 and befund["trennung"] >= varianten.FENSTER_TRENNUNG_MIN


def test_uebermaltes_glas_faellt_auf():
    befund = varianten.fenster_gehalten(_bild(_ki_uebermalt), _bild(_grundbild),
                                        _bild(_kennung), varianten.glasfarben(TABELLE),
                                        maske=MASKE)
    assert befund["anteil"] == 0.0 and befund["gehalten"] is False


def test_andere_stimmung_haelt_das_glas_trotzdem():
    """Abendlicht: alles wärmer und dunkler — das Glas bleibt dunkler als die Fassade."""
    def abend(x, y):
        r, g, b = _grundbild(x, y)
        return (min(255, r + 30), max(0, g - 20), max(0, b - 40))
    befund = varianten.fenster_gehalten(_bild(abend), _bild(_grundbild), _bild(_kennung),
                                        varianten.glasfarben(TABELLE), maske=MASKE)
    assert befund["gehalten"] is True


def test_die_deckung_sieht_das_uebermalte_band_nicht():
    """Der Grund des Befunds: Die Kanten über das ganze Bild nennen das Bild deckungsgleich."""
    from aiimaging import farbabgleich
    iou = farbabgleich.kanten_iou(_bild(_ki_uebermalt), _bild(_grundbild), B, H)
    assert varianten.deckung(True, iou)["urteil"] == varianten.DECKUNGSGLEICH, iou


@pytest.mark.parametrize("tabelle, kennung_von, wort", [
    ([TABELLE[0]], _kennung, "Kein Glas"),
    (TABELLE, lambda x, y: GLAS_ID if (x, y) == (20, 11) else _kennung(x, y)
     if not _band(x, y) else LATTE_ID, "Zu wenig Glas"),
])
def test_ohne_genug_glas_wird_nicht_gemessen(tabelle, kennung_von, wort):
    befund = varianten.fenster_gehalten(_bild(_ki_uebermalt), _bild(_grundbild),
                                        _bild(kennung_von), varianten.glasfarben(tabelle),
                                        maske=MASKE)
    assert befund["gehalten"] is None and befund["anteil"] is None and wort in befund["grund"]


def test_glas_wie_fassade_im_grundbild_wird_nicht_gemessen():
    """Ist das Glas im Cycles-Bild hell wie die Lattung, laesst sich nichts trennen."""
    grund = _bild(lambda x, y: (LATTUNG if _band(x, y) else _grundbild(x, y)))
    befund = varianten.fenster_gehalten(_bild(_ki_uebermalt), grund, _bild(_kennung),
                                        varianten.glasfarben(TABELLE), maske=MASKE)
    assert befund["gehalten"] is None and "wie die Fassade" in befund["grund"]


def test_glaswoerter_wie_im_runner():
    text = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(
        encoding="utf-8")
    zeile = re.search(r"^GLAS_WOERTER = (\(.*\))$", text, re.M)
    assert zeile and eval(zeile.group(1)) == varianten.GLAS_WOERTER  # noqa: S307


def _png(pfad, farbe_von):
    bildschreiben.schreibe_farb_png(pfad, _bild(farbe_von), B, H)
    return str(pfad)


def test_aus_den_dateien_und_am_kameraurteil(tmp_path):
    bericht = {"beauty_png": _png(tmp_path / "grund.png", _grundbild),
               "material_id_png": _png(tmp_path / "id.png", _kennung),
               "material_id_tabelle": TABELLE}
    ki = _png(tmp_path / "ki.png", _ki_uebermalt)
    befund = abholer.fenster_der_kamera(ki, bericht, MASKE)
    assert befund["gehalten"] is False and befund["anteil"] == 0.0
    # Ohne Glas im ID-Pass: kein Feld am Urteil.
    assert abholer.fenster_der_kamera(ki, dict(bericht, material_id_tabelle=TABELLE[:1]),
                                      MASKE) is None
    # Falsche Groesse: nicht gemessen, mit Grund — keine Ausnahme.
    bildschreiben.schreibe_farb_png(tmp_path / "klein.png", [(0, 0, 0)] * 4, 2, 2)
    schief = abholer.fenster_der_kamera(str(tmp_path / "klein.png"), bericht, MASKE)
    assert schief["gehalten"] is None and "Masse" in schief["grund"]


def _eintrag(kamera, fenster):
    return {"kamera": kamera, "geometrie_urteil": {"kamera": kamera,
                                                   kosmo_szene.URTEIL_FENSTER: fenster}}


def test_ein_satz_nur_unter_der_schwelle():
    je_kamera = [_eintrag("sSE", {"anteil": 0.12, "gehalten": False, "schwelle": 0.5}),
                 _eintrag("nNW", {"anteil": 0.9, "gehalten": True, "schwelle": 0.5}),
                 _eintrag("eE", {"anteil": None, "gehalten": None, "grund": "Zu wenig Glas"})]
    hinweise = []
    kosmo_szene._fenster_eintragen(None, je_kamera, hinweise)
    kosmo_szene._fenster_eintragen(None, je_kamera, hinweise)
    assert len(hinweise) == 1, "ein Satz je Kamera, nicht doppelt, nichts bei gehalten/ungemessen"
    assert hinweise[0].startswith(varianten.SATZ_FENSTER_NICHT_GEHALTEN + ", Kamera 'sSE'")
    assert "12%" in hinweise[0] and "gesetzt" in hinweise[0]


# ============================================================ 2 · die beiden Prompt-Schalter

PROMPT = "contemporary house on a slope, architectural photography"
HOLZ = "spruce timber battens"


def _szene(**vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"samples": 8, "materialien": {"fassade": {"id": "holzlattung-fichte"}}},
            "style": {"prompt": PROMPT}, "vis": vis}


def _ohne_textur(maengel):
    return [m for m in maengel if "fehlt am Rechner" not in m]


def test_ohne_schalter_bleibt_der_prompt_wort_fuer_wort():
    szene = kosmo_szene.lies_szene(_szene(), streng=False)
    assert szene["prompt"] == (f"monolithic {HOLZ} building, made entirely of {HOLZ}, "
                               f"uniform {HOLZ} on all exterior surfaces, {PROMPT}")
    vorne = [z for z in szene["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert "nennungen_hoechstens" not in vorne[0]
    assert not [z for z in szene["prompt_zusaetze"] if z["art"] == "glas"]


def test_der_glassatz_steht_direkt_hinter_dem_stoff():
    szene = kosmo_szene.lies_szene(_szene(glas_satz=True), streng=False)
    assert szene["prompt"].startswith(
        f"monolithic {HOLZ} building, made entirely of {HOLZ}, uniform {HOLZ} on all "
        f"exterior surfaces, {kosmo_szene.GLAS_SATZ}, {PROMPT}")
    assert not _ohne_textur(szene["maengel"])


def test_der_glassatz_ohne_stoff_steht_ganz_vorne_und_einmal():
    fremd = _szene(glas_satz=True, material_vorne=False)
    fremd["style"]["prompt"] = "a house with clear glazing"
    szene = kosmo_szene.lies_szene(fremd, streng=False)
    assert szene["prompt"].count("glazing") == 1, "schon im Prompt — nicht doppelt"
    assert [z["schon_im_prompt"] for z in szene["prompt_zusaetze"] if z["art"] == "glas"] == [True]


def test_der_glassatz_nennt_kein_bauteil():
    """Ein Bauteilwort («windows») bestellte eine Form, die das Modell vielleicht nicht hat."""
    assert prompts.bauteilwaechter(kosmo_szene.GLAS_SATZ)["gefunden"] is False


@pytest.mark.parametrize("zahl, erwartet", [
    (1, f"monolithic {HOLZ} building, {PROMPT}"),
    (2, f"monolithic {HOLZ} building, made entirely of {HOLZ}, {PROMPT}"),
])
def test_der_stoff_vorne_seltener(zahl, erwartet):
    szene = kosmo_szene.lies_szene(_szene(material_vorne_nennungen=zahl), streng=False)
    assert szene["prompt"] == erwartet
    vorne = [z for z in szene["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert vorne[0]["nennungen_hoechstens"] == zahl


def test_beide_schalter_zusammen():
    szene = kosmo_szene.lies_szene(_szene(material_vorne_nennungen=1, glas_satz=True),
                                   streng=False)
    assert szene["prompt"] == f"monolithic {HOLZ} building, {kosmo_szene.GLAS_SATZ}, {PROMPT}"


@pytest.mark.parametrize("vis, wort, endgueltig", [
    ({"glas_satz": "ja"}, "'vis.glas_satz' ist", False),
    ({"glas_satz": True, "skip": True}, "zugleich", True),
    ({"material_vorne_nennungen": 0}, "'vis.material_vorne_nennungen' ist", False),
    ({"material_vorne_nennungen": True}, "'vis.material_vorne_nennungen' ist", False),
    ({"material_vorne_nennungen": 2.5}, "'vis.material_vorne_nennungen' ist", False),
])
def test_falsche_werte_sind_maengel(vis, wort, endgueltig):
    szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
    assert any(wort in m for m in szene["maengel"]), szene["maengel"]
    assert any(wort in m for m in szene["maengel_endgueltig"]) is endgueltig


def test_nennungen_ohne_stoff_vorne_sagt_es():
    szene = kosmo_szene.lies_szene(_szene(material_vorne=False, material_vorne_nennungen=1),
                                   streng=False)
    assert any("wirkt nicht" in w for w in szene["warnungen"])
    assert szene["prompt"].endswith(f"exterior surfaces of {HOLZ}")


def test_die_schalter_sind_bekannte_felder():
    assert {"glas_satz", "material_vorne_nennungen"} <= set(kosmo_szene.BEKANNTE_FELDER["vis"])


# ============================================================ 3 · der Messauftrag 346

def test_der_messauftrag_346_ist_gueltig_und_fragt_alle_punkte():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261023-346.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa"
    assert daten["geometrie"]["synthetisch"] is True and daten["geometrie"]["pfad"] is None
    text = daten["anweisung"]
    assert len(text) >= 1000
    for stichwort in ("haus-am-hang", "sSE", "0,4", "0,6", "glas_satz",
                      "material_vorne_nennungen", "fenster", "NICHT TUN", "Regel 3",
                      "1600", "Bauwerksmaske", "umfeld_namen", "Laufzeit"):
        assert stichwort in text, stichwort
