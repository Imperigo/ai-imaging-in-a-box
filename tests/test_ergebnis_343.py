"""Ergebnis 343 — das Höhenurteil auf dem richtigen Bezug, die Rolle «ground» im Bildweg, der
Kontrast am Umriss.

**Ergebnis auf-20261023-343 (Heim-PC, Demohaus mit Gelände, E-NEU und Auto-Kamera sSE):**

1. ``referenzpunkt: okff`` kam im Kamerabericht an und wirkte nicht: E-NEU (Auge 1,60 m über
   OK EG = Weltnull, 1,62 über dem Gelände) hiess «2.00 m … zu hoch» über der
   Hüllbox-Unterkante (−0,40).
2. Umgekehrt hiess die Auto-Kamera sSE «1.70 m … augenhoch», stand aber 1,32 m über dem Boden.
   Die Geländefläche reicht nicht unter die Standpunkte (Haus + 8 m), also fiel das Urteil auf
   die Hüllbox-Unterkante zurück. Jetzt gilt eine Reihenfolge der Bezüge: Gelände am Standpunkt
   (gemessen) → referenzpunkt der Bestellung → Gelände in der Nähe (mit Abstand) → Hüllbox.
3. «GELAENDESTAND NICHT FESTSTELLBAR» stand nur im Kamerabericht, nicht in den Hinweisen.
4. ``extras.role ground`` wurde in der Bauwerksbox des Runners nicht gelesen («entschieden_durch
   name»).
5. «HAUS KAUM SICHTBAR» in allen Läufen — die Mittelwertzahl sieht ein zweifarbiges Haus nicht;
   daneben steht jetzt der Kontrast am Umriss (Auskunft, die Warnung bleibt).

Jede Probe ist gegen den alten Stand rot. Regel 3: alle Zahlen synthetisch.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aiimaging import abholer, belichtung, kameras, kosmo_szene

from test_grundlage_varianten import _mit_schoenbild
from test_kamerahoehe_341 import _block_341, _mesh as _flaechenmesh, _runner
from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_rahmung_vor_render import _mesh as _boxmesh, _runner_mit_objekten


def _e_neu(**mehr):
    """Der Kamerablock von E-NEU aus 343 (Welt, Z oben): bestellt, okff, kein Gelände darunter."""
    k = {"weg": "vorgegeben", "auge": [7.4, -26.443, 1.6], "blick_auf": [7.4, 4.49, 3.212],
         "gelaende_z": -0.4, "gelaende_bezug": "huellbox_unterkante",
         "gelaende_am_standpunkt_z": None, "referenzpunkt": "okff"}
    k.update(mehr)
    return k


def _sse(**mehr):
    """Die Auto-Kamera sSE aus 343: 1,30 über Weltnull, Gelände (−0,02) nicht darunter."""
    k = {"auge": [26.9068, -23.3686, 1.3], "gelaende_z": -0.4,
         "gelaende_bezug": "huellbox_unterkante", "gelaende_am_standpunkt_z": None,
         "gelaende_nahe_z": -0.02, "gelaende_nahe_abstand_m": 14.2}
    k.update(mehr)
    return k


# ====================================================================== 1 · referenzpunkt okff

def test_okff_traegt_das_urteil_der_bestellten_kamera():
    """GEGEN ALT ROT: «Standpunkt 2.00 m ueber der Huellbox-Unterkante — … zu hoch»."""
    befund = kameras.augenhoehe_befund(_e_neu())
    assert befund["augenhoch"] is True
    assert befund["bezug"] == "okff"
    assert befund["kamerahoehe_m"] == pytest.approx(1.60)
    assert befund["bezug_z"] == 0.0
    assert "1.60 m ueber OK EG" in befund["grund"]
    assert "Weltnull angenommen" in befund["grund"], "die Annahme steht im Satz"
    assert "2.00 m" in befund["grund"], "die Höhe über der Hüllbox-Unterkante steht daneben"
    assert befund["ueber_bezug_m"] == pytest.approx(2.0)


def test_okff_mit_eg_kote_aus_der_szene():
    befund = kameras.augenhoehe_befund(_e_neu(okff_z=0.3, auge=[7.4, -26.443, 1.95]))
    assert befund["kamerahoehe_m"] == pytest.approx(1.65) and befund["augenhoch"] is True
    assert "z = 0.30 m (aus der Szene)" in befund["grund"]
    assert "Weltnull angenommen" not in befund["grund"]


def test_weltnull_ist_null():
    befund = kameras.augenhoehe_befund(_e_neu(referenzpunkt="weltnull"))
    assert befund["bezug"] == "weltnull" and befund["augenhoch"] is True


def test_gemessenes_gelaende_schlaegt_den_referenzpunkt():
    befund = kameras.augenhoehe_befund(_e_neu(gelaende_am_standpunkt_z=0.2))
    assert befund["bezug"] == "terrain_an_kamera"
    assert befund["kamerahoehe_m"] == pytest.approx(1.40) and befund["augenhoch"] is False


def test_referenzpunkt_schlaegt_das_gelaende_in_der_naehe():
    befund = kameras.augenhoehe_befund(_e_neu(gelaende_nahe_z=-0.02,
                                              gelaende_nahe_abstand_m=10.0))
    assert befund["bezug"] == "okff"


def test_die_reihenfolge_steht_an_einer_stelle():
    assert kameras.BEZUGSFOLGE_AUGENHOEHE == (
        "terrain_an_kamera", "referenzpunkt", "gelaende_in_der_naehe", "huellbox_unterkante")


# ====================================================================== 2 · Gelände in der Nähe

def test_die_auto_kamera_ist_ueber_dem_gelaende_in_der_naehe_zu_tief():
    """GEGEN ALT ROT: sSE hiess «1.70 m ueber der Huellbox-Unterkante — augenhoch»."""
    befund = kameras.augenhoehe_befund(_sse())
    assert befund["bezug"] == "gelaende_in_der_naehe"
    assert befund["kamerahoehe_m"] == pytest.approx(1.32)
    assert befund["augenhoch"] is False and "zu tief" in befund["grund"]
    assert "Gelaende in der Naehe" in befund["grund"]
    assert "14.2 m vom Standpunkt" in befund["grund"]
    assert "NICHT am Standpunkt gemessen" in befund["grund"]
    assert befund["ueber_gelaende_m"] is None, "in der Nähe ist nicht am Standpunkt"


def test_zu_fernes_gelaende_zaehlt_nicht():
    befund = kameras.augenhoehe_befund(
        _sse(gelaende_nahe_abstand_m=kameras.GELAENDE_NAHE_MAX_M + 1))
    assert befund["bezug"] == "huellbox_unterkante"


def test_gesetztes_gelaende_bleibt_vor_der_naehe():
    """Nur die unzuverlässige Hüllbox-Unterkante wird durch die Nähe ersetzt."""
    befund = kameras.augenhoehe_befund(_sse(gelaende_bezug="gesetzt", gelaende_z=-0.02))
    assert befund["bezug"] == "gesetzt"


def test_naechster_punkt_der_gelaendeflaeche():
    platte = [[(-1, -1, -0.02), (15, -1, -0.02), (15, 10, 0.5), (-1, 10, 0.5)]]
    rand = kameras.gelaende_naechster_punkt(platte, 7, -21)
    assert rand["abstand_m"] == pytest.approx(20.0)
    assert rand["z"] == pytest.approx(-0.02) and rand["punkt"] == pytest.approx([7, -1])
    innen = kameras.gelaende_naechster_punkt(platte, 7, 4.5)
    assert innen["abstand_m"] == 0.0 and innen["z"] == pytest.approx(0.24)
    schuerze = [[(0, 0, 0), (10, 0, 0), (10, 0, -1), (0, 0, -1)]]
    assert kameras.gelaende_naechster_punkt(schuerze, 5, 5) is None
    assert kameras.gelaende_naechster_punkt([], 0, 0) is None


def test_der_runner_meldet_das_gelaende_in_der_naehe(monkeypatch):
    """GEGEN ALT ROT: Ohne Fläche unter dem Standpunkt gab es keine Zahl, nur den Satz."""
    platte = _flaechenmesh("gelaendeflaeche gewachsen",
                           [(-1, -1, 0), (15, -1, 0), (15, 10, 0), (-1, 10, 0)],
                           [(0, 1, 2, 3)], dz=-0.02)
    befund = _runner(monkeypatch, [platte])._gelaende_am_standpunkt([7.4, -21.0, 1.3])
    assert befund["gelaende_am_standpunkt_z"] is None
    assert befund["gelaende_nahe_z"] == pytest.approx(-0.02)
    assert befund["gelaende_nahe_abstand_m"] == pytest.approx(20.0)
    darunter = _runner(monkeypatch, [platte])._gelaende_am_standpunkt([3, 3, 1.3])
    assert darunter["gelaende_am_standpunkt_z"] == pytest.approx(-0.02)
    assert darunter["gelaende_nahe_z"] is None, "gemessen: die Nähe braucht es nicht"


# ====================================================================== 3 · in die Hinweise

def _vermerk(block, kuerzel="sSE"):
    bericht = {"kamera": block}
    return abholer.kamerahoehe_vermerk(abholer._komposition_vor_dem_render(bericht),
                                       bericht, kuerzel)


def _warnung(auge_z=1.3):
    return [kameras.GELAENDE_UNBEKANNT.format(fuss=-0.4, auge_z=auge_z, augenhoehe=1.7)]


def test_gelaendestand_reist_auch_bei_augenhoch_mit():
    """GEGEN ALT ROT: «augenhoch» über der Hüllbox-Unterkante — kein Satz, die Warnung blieb im
    Kamerabericht. Ohne Gelände in der Nähe (alter Runner) ist das genau der Fall aus 343."""
    block = dict(_block_341("sSE"), gelaende_am_standpunkt_z=None, warnungen=_warnung())
    vermerk = _vermerk(block)
    assert vermerk is not None
    assert vermerk["satz"].startswith(f"{kosmo_szene.SATZ_KAMERAHOEHE}, Kamera 'sSE': ")
    assert "augenhoch" in vermerk["satz"]
    assert "GELAENDESTAND NICHT FESTSTELLBAR" in vermerk["satz"]


def test_mit_gelaende_in_der_naehe_zu_tief_und_gelaendestand():
    block = dict(_block_341("sSE"), gelaende_am_standpunkt_z=None, gelaende_nahe_z=-0.02,
                 gelaende_nahe_abstand_m=14.2, warnungen=_warnung())
    satz = _vermerk(block)["satz"]
    assert "zu tief" in satz and "Gelaende in der Naehe" in satz
    assert "GELAENDESTAND NICHT FESTSTELLBAR" in satz


def test_ohne_warnung_und_augenhoch_bleibt_es_still():
    """Die bestellte Kamera (ohne Gelaendestand-Warnung) auf 1,60 m über OK EG: kein Satz."""
    assert _vermerk(_e_neu(), "Eingang") is None


def test_der_gelaendestand_steht_im_ergebnis(tmp_path):
    """GEGEN ALT ROT: im Lauf (Attrappenkette) stand kein Satz in ``qa.verdict.hinweise``."""
    def block(kuerzel):
        return dict(_block_341(kuerzel), gelaende_am_standpunkt_z=None, warnungen=_warnung())

    _protokoll, attrappen = _kette(tmp_path, kamerablock=block)
    ordner = _auftragsordner(tmp_path, skip=True)
    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    hinweise = antwort["ergebnis"]["qa"]["verdict"].get("hinweise") or []
    hoehe = [h for h in hinweise if h.startswith(kosmo_szene.SATZ_KAMERAHOEHE)]
    assert hoehe and all("GELAENDESTAND NICHT FESTSTELLBAR" in h for h in hoehe), hinweise


# ====================================================================== 4 · role ground

def _mit_rolle(mesh, rolle):
    eigen = {"role": rolle}
    return SimpleNamespace(**vars(mesh), get=eigen.get)


def test_die_rolle_entscheidet_vor_dem_namen(monkeypatch):
    """GEGEN ALT ROT: «gelaendeflaeche gewachsen» mit ``role ground`` hiess «name»."""
    modul = _runner_mit_objekten(monkeypatch, [
        _mit_rolle(_boxmesh("gelaendeflaeche gewachsen [lobf29]", (-30, -30, -2.0),
                            (30, 30, 0.0)), "ground"),
        _boxmesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])
    lo, hi, note, _schrumpfung, form = modul._bbox_bauwerk()
    assert (lo, hi) == ([0, 0, 0], [8, 5, 7])
    assert form == {"entschieden_durch": "role",
                    "gelaende_namen": ("gelaendeflaeche gewachsen [lobf29]",)}


def test_die_rolle_traegt_auch_einen_namen_ohne_gelaendewort(monkeypatch):
    """«Platte» nennt kein Gelände — mit ``role terrain`` ist sie es doch."""
    modul = _runner_mit_objekten(monkeypatch, [
        _mit_rolle(_boxmesh("Platte", (-30, -30, -2.0), (30, 30, 0.0)), "Terrain"),
        _boxmesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])
    lo, hi, _note, _s, form = modul._bbox_bauwerk()
    assert (lo, hi) == ([0, 0, 0], [8, 5, 7])
    assert form["entschieden_durch"] == "role" and form["gelaende_namen"] == ("Platte",)


def test_ohne_rolle_bleibt_es_der_name(monkeypatch):
    modul = _runner_mit_objekten(monkeypatch, [
        _boxmesh("gelaendeflaeche gewachsen", (-30, -30, -2.0), (30, 30, 0.0)),
        _boxmesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])
    assert modul._bbox_bauwerk()[-1]["entschieden_durch"] == "name"


def test_eine_fremde_rolle_ist_kein_gelaende(monkeypatch):
    modul = _runner_mit_objekten(monkeypatch, [
        _mit_rolle(_boxmesh("Platte", (-30, -30, -2.0), (30, 30, 0.0)), "building"),
        _boxmesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])
    assert modul._bbox_bauwerk()[-1]["entschieden_durch"] != "role"


# ====================================================================== 5 · Kontrast am Umriss

def _zweifarbig(b=40, h=30, hell=200, dunkel=60, himmel=130):
    """Ein Haus in der Bildmitte, linke Hälfte sonnig, rechte im Schatten, vor grauem Himmel."""
    farben, haus = [], []
    for y in range(h):
        for x in range(b):
            drin = 10 <= x < 30 and 10 <= y < h
            haus.append(drin)
            g = (hell if x < 20 else dunkel) if drin else himmel
            farben.append((g, g, g))
    return farben, haus, [not m for m in haus]


def test_die_mittelwertzahl_sieht_das_zweifarbige_haus_nicht():
    """Der Befund: Mittel Haus (200+60)/2 = 130 = Himmel → «kaum sichtbar». Das Auge sieht es."""
    farben, haus, grund = _zweifarbig()
    aus = belichtung.kontrast_haus_hintergrund(farben, 40, 30, haus=haus, hintergrund=grund)
    assert abs(aus["kontrast"]) < 1.0 and aus["kaum_sichtbar"] is True


def test_der_umriss_sieht_es():
    """GEGEN ALT ROT: ``umriss`` gab es nicht."""
    farben, haus, grund = _zweifarbig()
    aus = belichtung.kontrast_haus_hintergrund(farben, 40, 30, haus=haus, hintergrund=grund)
    umriss = aus["umriss"]
    assert umriss["betrag"] == pytest.approx(70.0, abs=0.5)
    assert abs(umriss["kontrast"]) < 15, "mit Vorzeichen hebt es sich zum Teil auf"
    assert umriss["n_stellen"] > 0


def test_der_umriss_ohne_hintergrund_ist_nicht_gemessen():
    aus = belichtung.kontrast_am_umriss([(9, 9, 9)] * 4, 2, 2, haus=[True] * 4,
                                        hintergrund=[False] * 4)
    assert aus["betrag"] is None and aus["grund"]


def test_der_umriss_steht_im_ergebnis_und_im_satz():
    """GEGEN ALT ROT: ``qa.kontrast_umriss_haus_hintergrund`` fehlte; die Warnung bleibt."""
    urteil = {"kamera": "Eingang", "score": None, "bestanden": None,
              "kontrast": {"kontrast": -19.6, "umriss": {"betrag": 48.3, "kontrast": -12.0}}}
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=urteil,
                                 je_kamera=[{"kamera": "Eingang", "geometrie_urteil": urteil}])
    assert e["qa"]["kontrast_haus_hintergrund"] == -19.6
    assert e["qa"][kosmo_szene.FELD_KONTRAST_UMRISS] == 48.3
    assert e["qa_je_kamera"][0][kosmo_szene.FELD_KONTRAST_UMRISS] == 48.3
    satz = next(h for h in e["hinweise"] if h.startswith(kosmo_szene.SATZ_KAUM_SICHTBAR))
    assert "Am Umriss" in satz and "48.3" in satz
    ohne = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                    geometrie_urteil={"kontrast": {"kontrast": -3.0}})
    assert kosmo_szene.FELD_KONTRAST_UMRISS not in ohne["qa"], "kein null"
