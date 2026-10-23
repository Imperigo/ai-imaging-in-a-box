"""Ergebnisse 341 und 342 — die Höhe der Kamera ehrlich berichtet, und drei Reste der Variante.

**Ergebnis auf-20261022-341 (Heim-PC, Auto-Kameras am Demohaus mit Gelände):** Die Auge-Höhe
lag 1,30 m über Weltnull, 1,32 m über dem Gelände (−0,02). Der Kern meldete «Standpunkt 1.70
m ueber Gelaende — KEINE Augenhoehe, zu hoch», gemessen aber über der Hüllbox-Unterkante
(−0,40, Unterkante Bodenplatte). Dazu:

(a) Der Satz nennt jetzt den Bezug, über dem gemessen ist. Erkennt der Runner ein Gelände unter
    dem Standpunkt, MISST er dessen Höhe (``gelaende_am_standpunkt_z``), und das Urteil stützt
    sich darauf. Die Kamera steht, wo sie stand — Gelände als Boden ist eine Owner-Frage.
(b) ``1.7000000059604645`` fiel durch das Zahlenformat aus dem Band 1,60–1,70 → Toleranz.
(c) Die Warnungen zur Höhe kommen ins Ergebnis (``qa.verdict.hinweise``, «KAMERAHOEHE»).
(d) «GELAENDESTAND NICHT FESTSTELLBAR» steht im Kamerabericht (Warnung des ganzen Satzes).
(e) ``referenzpunkt`` der Bestellung steht im Kamerabericht.

**Ergebnis auf-20261022-342 (Licht der Variante):**

(f) «evening mood» auf Licht mittag meldet ``licht_der_grundlage`` «mittag», nicht ``null``.
(g) «evening mood» steht im Prompt nicht mehr doppelt.
(h) Bei ``vis.bildeingang: false`` sagt auch der zweite Teil der Warnung nicht mehr «bestellt
    'image_edit'», und ``denoise_bestellt`` ist ``None`` statt der 0,6 des Registers. Ursache:
    Der Fix aus §258 änderte nur den Anfang; der angehängte Satz aus ``modus_satz`` und das
    Feld kamen aus der Vorgabe des Registers. Die Probe von §258 rief ``ki_vermerk`` ohne
    ``modus_satz`` — anders als der Lauf.

Jede Probe ist gegen den alten Stand rot. Regel 3: alle Zahlen synthetisch.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import abholer, kameras, kosmo_szene, stimmung

from test_grundlage_varianten import _mit_schoenbild
from test_kettenlauf_26august import _auftragsordner, _kette, _lauf

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")


def _kamera_341(auge_z=1.3, gelaende=-0.02, **mehr):
    """Der Kamerablock einer Auto-Kamera aus Ergebnis 341 (Welt, Z oben)."""
    k = {"auge": [5.82, -26.07, auge_z], "gelaende_z": -0.4,
         "gelaende_bezug": "huellbox_unterkante"}
    if gelaende is not None:
        k["gelaende_am_standpunkt_z"] = gelaende
    k.update(mehr)
    return k


# ====================================================================== (a) der Bezug im Satz

def test_ohne_gelaende_nennt_der_satz_die_huellbox_unterkante():
    """GEGEN ALT ROT: Dort stand «ueber Gelaende», gemessen war die Hüllbox-Unterkante."""
    befund = kameras.augenhoehe_befund(_kamera_341(gelaende=None))
    assert "ueber der Huellbox-Unterkante" in befund["grund"]
    assert "ueber Gelaende" not in befund["grund"]
    assert "NICHT gemessen" in befund["grund"]
    assert befund["bezug"] == "huellbox_unterkante"
    assert befund["ueber_gelaende_m"] is None


def test_mit_gemessenem_gelaende_urteilt_sie_ueber_dem_gelaende():
    """Der Fall aus 341: 1,32 m über dem Gelände — zu TIEF, nicht zu hoch."""
    befund = kameras.augenhoehe_befund(_kamera_341())
    assert befund["kamerahoehe_m"] == pytest.approx(1.32)
    assert befund["ueber_gelaende_m"] == pytest.approx(1.32)
    assert befund["ueber_bezug_m"] == pytest.approx(1.70)
    assert befund["bezug"] == "terrain_an_kamera"
    assert befund["augenhoch"] is False
    assert "zu tief" in befund["grund"] and "zu hoch" not in befund["grund"]
    assert "1.32 m ueber dem Gelaende am Standpunkt" in befund["grund"]
    assert "1.70 m ueber der Huellbox-Unterkante" in befund["grund"]


def test_eingang_neu_ist_ueber_dem_gelaende_augenhoch():
    """E-NEU aus 341: Auge 1,60 über Weltnull, Gelände −0,02 → 1,62 m, augenhoch. Der Kern
    meldete «2.00 m, zu hoch» (über der Hüllbox-Unterkante)."""
    befund = kameras.augenhoehe_befund(_kamera_341(auge_z=1.6))
    assert befund["augenhoch"] is True
    assert befund["kamerahoehe_m"] == pytest.approx(1.62)


def test_ohne_bezug_bleibt_die_alte_rechnung():
    """Ein Bericht ohne ``gelaende_bezug`` (ältere Läufe) rechnet wie bisher über gelaende_z."""
    befund = kameras.augenhoehe_befund({"auge": [0, 0, -1.65], "gelaende_z": -3.30})
    assert befund["augenhoch"] is True
    assert "gelaende_z" in befund["grund"]


# ------------------------------------------------------------- die Messung am Gelände

def test_gelaende_hoehe_am_punkt_misst_die_oberste_flaeche():
    eben = [[(0, 0, -0.02), (10, 0, -0.02), (10, 10, -0.02)],
            [(0, 0, -0.02), (10, 10, -0.02), (0, 10, -0.02)]]
    assert kameras.gelaende_hoehe_am_punkt(eben, 3, 4) == pytest.approx(-0.02)
    assert kameras.gelaende_hoehe_am_punkt(eben, 30, 4) is None, "ausserhalb: keine Zahl"
    hang = [[(0, 0, 0.0), (10, 0, 1.0), (10, 10, 1.0), (0, 10, 0.0)]]   # Viereck, Fächer
    assert kameras.gelaende_hoehe_am_punkt(hang, 5, 5) == pytest.approx(0.5)
    schuerze = [[(0, 0, -0.02), (10, 0, -0.02), (10, 0, -1.02), (0, 0, -1.02)]]
    assert kameras.gelaende_hoehe_am_punkt(schuerze, 5, 0) is None, "senkrecht zählt nicht"
    unterseite = [[(0, 0, -1.0), (10, 0, -1.0), (0, 10, -1.0)]]
    assert kameras.gelaende_hoehe_am_punkt(eben + unterseite, 1, 1) == pytest.approx(-0.02)


def _runner(monkeypatch, objekte):
    bpy = mock.MagicMock()
    bpy.data.objects = objekte
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "mathutils", SimpleNamespace(Vector=list))
    spez = importlib.util.spec_from_file_location("blender_pruefling_341", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


class _Welt:
    """``matrix_world`` als Verschiebung — so viel ``mathutils.Matrix``, wie gebraucht."""

    def __init__(self, dz=0.0):
        self.dz = dz

    def __matmul__(self, co):
        return (co[0], co[1], co[2] + self.dz)


def _mesh(name, ecken, flaechen, *, rolle=None, dz=0.0):
    eigen = {"role": rolle} if rolle else {}
    return SimpleNamespace(
        name=name, type="MESH", matrix_world=_Welt(dz), get=eigen.get,
        data=SimpleNamespace(vertices=[SimpleNamespace(co=c) for c in ecken],
                             polygons=[SimpleNamespace(vertices=f) for f in flaechen]))


def test_der_runner_misst_das_gelaende_am_standpunkt(monkeypatch):
    """Namensregel, Rolle und Weltlage — und das Bauwerk zählt nicht als Boden."""
    platte = _mesh("gelaendeflaeche gewachsen",
                   [(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)], [(0, 1, 2, 3)],
                   dz=-0.02)
    haus = _mesh("Wand EG", [(-50, -50, 5), (50, -50, 5), (50, 50, 5)], [(0, 1, 2)])
    modul = _runner(monkeypatch, [platte, haus])
    befund = modul._gelaende_am_standpunkt([5.82, -26.07, 1.3])
    assert befund["gelaende_am_standpunkt_z"] == pytest.approx(-0.02)
    assert befund["gelaende_am_standpunkt"]["objekte"] == ["gelaendeflaeche gewachsen"]

    boden = _mesh("boden", [(-50, -50, 0.1), (50, -50, 0.1), (0, 50, 0.1)], [(0, 1, 2)],
                  rolle="ground")
    modul = _runner(monkeypatch, [boden, haus])
    assert modul._gelaende_am_standpunkt([0, 0, 1.7])["gelaende_am_standpunkt_z"] == \
        pytest.approx(0.1), "extras.role 'ground' zählt"

    modul = _runner(monkeypatch, [haus])
    ohne = modul._gelaende_am_standpunkt([0, 0, 1.7])
    assert ohne["gelaende_am_standpunkt_z"] is None
    assert "NICHT GEMESSEN" in ohne["gelaende_am_standpunkt"]["grund"]
    weit = _runner(monkeypatch, [platte])._gelaende_am_standpunkt([500, 0, 1.7])
    assert weit["gelaende_am_standpunkt_z"] is None, "Standpunkt neben dem Gelände"


def test_die_rollen_stehen_an_einer_stelle():
    from aiimaging import maske
    assert kosmo_szene.GELAENDE_ROLLEN is maske.GELAENDE_ROLLEN
    assert "ground" in maske.GELAENDE_ROLLEN


# ====================================================================== (b) die Toleranz

def test_die_eigene_setzhoehe_faellt_nicht_durch_das_zahlenformat():
    """GEGEN ALT ROT: 1.7000000059604645 hiess «zu hoch»."""
    for z in (1.7000000059604645, 1.3 + 0.4, 1.5999999):
        assert kameras.augenhoehe_befund({"auge": [0, 0, z], "gelaende_z": 0.0})["augenhoch"]
    assert kameras.augenhoehe_befund({"auge": [0, 0, 1.7002], "gelaende_z": 0.0})[
        "augenhoch"] is False, "die Toleranz ist kein zweites Band"


# ====================================================================== (d) die Satz-Warnung

def test_die_warnung_des_satzes_gehoert_keiner_kamera():
    satz = kameras.kamerasatz([[0, 0, -0.4], [15, 9, 8.6]], kuerzel=["s", "sSE"])
    eigen = kameras.satzwarnungen(satz)
    assert any(w.startswith("GELAENDESTAND NICHT FESTSTELLBAR") for w in eigen)
    assert not any(w.startswith(("s: ", "sSE: ")) for w in eigen)


def test_der_kamerabericht_traegt_den_gelaendestand(monkeypatch, tmp_path):
    """GEGEN ALT ROT: Am Runner (Attrappe von ``bpy``) stand die Warnung nicht im Bericht."""
    from test_deckungsgrad_wirkt_nur_abgeleitet import _bericht
    bericht = _bericht(monkeypatch, tmp_path, "--kamera", "sSE")
    assert bericht["kamera"]["weg"] == "abgeleitet"
    assert any(str(w).startswith("GELAENDESTAND NICHT FESTSTELLBAR")
               for w in bericht["kamera"]["warnungen"])
    # Die Attrappe hat kein Gelände: gemessen ist nichts, und das steht da.
    assert bericht["kamera"]["gelaende_am_standpunkt_z"] is None
    assert bericht["kamera"]["gelaende_am_standpunkt"]["grund"]


# ====================================================================== (c) ins Ergebnis

def _block_341(kuerzel):
    return {"weg": "abgeleitet", "kuerzel": kuerzel,
            "auge": [5.82, -26.07, 1.3], "blick_auf": [7.4, 4.49, 1.3],
            "abstand_m": 30.6, "brennweite_mm": 35.0, "seitenverhaeltnis": 1.6,
            "shift_mm": 0.0, "neigung_grad": 0.0,
            "gelaende_z": -0.4, "gelaende_bezug": "huellbox_unterkante",
            "gebaeudehoehe_m": 9.03, "gelaende_am_standpunkt_z": -0.02,
            "warnungen": [kameras.GELAENDE_UNBEKANNT.format(fuss=-0.4, auge_z=1.3,
                                                            augenhoehe=1.7)]}


def test_der_vermerk_sagt_zu_tief_und_den_bezug():
    bericht = {"kamera": _block_341("s")}
    vermerk = abholer.kamerahoehe_vermerk(abholer._komposition_vor_dem_render(bericht),
                                          bericht, "s")
    assert vermerk["satz"].startswith(f"{kosmo_szene.SATZ_KAMERAHOEHE}, Kamera 's': ")
    assert "zu tief" in vermerk["satz"]
    # Gemessen: der Gelaendestand-Satz kommt nicht dazu, die Hoehe darueber sagt es.
    assert "GELAENDESTAND" not in vermerk["satz"]
    # Ohne gemessenes Gelaende und ausserhalb des Bands (z. B. 2,10 m ueber der Unterkante)
    # reist der Gelaendestand-Satz mit. Innerhalb des Bands gibt es keinen Satz (unten).
    ohne = dict(bericht["kamera"], gelaende_am_standpunkt_z=None, auge=[5.82, -26.07, 1.7])
    vermerk = abholer.kamerahoehe_vermerk(
        abholer._komposition_vor_dem_render({"kamera": ohne}), {"kamera": ohne}, "s")
    assert "GELAENDESTAND NICHT FESTSTELLBAR" in vermerk["satz"]
    augenhoch = dict(bericht["kamera"], auge=[5.82, -26.07, 1.6])
    assert abholer.kamerahoehe_vermerk(abholer._komposition_vor_dem_render(
        {"kamera": augenhoch}), {"kamera": augenhoch}, "s") is None, "augenhoch: kein Satz"


@pytest.mark.parametrize("skip", [False, True])
def test_der_satz_steht_im_ergebnis(tmp_path, skip):
    """GEGEN ALT ROT: Der Satz zur Höhe stand nur in befund.json. Mit KI-Lauf und «nur
    Grundlage» (so rechnete 341)."""
    protokoll, attrappen = _kette(tmp_path, kamerablock=_block_341)
    ordner = _auftragsordner(tmp_path, skip=skip)
    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    hinweise = antwort["ergebnis"]["qa"]["verdict"].get("hinweise") or []
    hoehe = [h for h in hinweise if h.startswith(kosmo_szene.SATZ_KAMERAHOEHE)]
    assert hoehe, hinweise
    assert all("zu tief" in h for h in hoehe)


# ====================================================================== (e) der Referenzpunkt

def test_der_referenzpunkt_steht_im_kamerabericht(tmp_path):
    """GEGEN ALT ROT: ``okff`` stand nur in der abgelegten Bestellung."""
    gesehen = []

    def block(kuerzel):
        return dict(_block_341(kuerzel), weg="vorgegeben")

    protokoll, attrappen = _kette(tmp_path, kamerablock=block)
    ordner = _auftragsordner(tmp_path, skip=True)
    pfad = ordner / "render-scene.json"
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["cameras"] = [{"name": "Eingang", "position": [7.4, 1.6, 14.16],
                         "target": [7.4, 3.212, -4.49], "fov": 55, "up_axis": "y",
                         "referenzpunkt": "okff"}]
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    echt = abholer._komposition_vor_dem_render

    def lauscher(bericht):
        gesehen.append(bericht)
        return echt(bericht)

    with mock.patch.object(abholer, "_komposition_vor_dem_render", lauscher):
        antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert [b["kamera"].get("referenzpunkt") for b in gesehen] == ["okff"]
    befund = (ordner / "befund.json").read_text(encoding="utf-8")
    assert '"referenzpunkt": "okff"' in befund


def test_ohne_referenzpunkt_bleibt_der_bericht_derselbe():
    bericht = {"kamera": {"auge": [0, 0, 1]}}
    assert abholer._referenzpunkt_eintragen(bericht, None) is bericht
    neu = abholer._referenzpunkt_eintragen(bericht, "okff")
    assert neu["kamera"]["referenzpunkt"] == "okff" and "referenzpunkt" not in bericht["kamera"]


# ====================================================================== (f) und (g)

KENNUNG = "gl-0123456789abcdef"


def _mittag():
    return kosmo_szene.umgebung_aus_szene({"preset": "mittag"}, grundlage=KENNUNG)["umgebung"]


def _lies(prompt, environment, **wie):
    from test_n6_stimmung_der_variante import _szene
    return kosmo_szene.lies_szene(_szene(prompt, environment, grundlage=KENNUNG),
                                  streng=False, **wie)


def test_evening_mood_auf_mittag_nennt_das_licht_der_grundlage(tmp_path, monkeypatch):
    """(f) GEGEN ALT ROT: ``licht_der_grundlage`` war ``None``."""
    from test_n6_stimmung_der_variante import _alle_himmel
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("evening mood", {"preset": "mittag"}, umgebung_der_grundlage=_mittag())
    v = s["stimmung_der_variante"]
    assert v["quelle"] == kosmo_szene.STIMMUNG_QUELLE_WORT
    assert v["licht_der_grundlage"] == "mittag"
    # Unbekannt bleibt unbekannt — nicht geraten.
    assert _lies("evening mood", {"preset": "mittag"})["stimmung_der_variante"] is None or \
        _lies("evening mood", {"preset": "mittag"})["stimmung_der_variante"][
            "licht_der_grundlage"] is None


@pytest.mark.parametrize("prompt", ["evening mood", "Abendstimmung, ein Haus am Hang"])
def test_evening_mood_steht_nur_einmal_im_prompt(tmp_path, monkeypatch, prompt):
    """(g) GEGEN ALT ROT: «…, evening mood, evening mood, warm low sunlight, …»."""
    from test_n6_stimmung_der_variante import _alle_himmel
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(prompt, {"preset": "abend"}, umgebung_der_grundlage=_mittag())
    assert s["prompt"].lower().count("evening mood") == 1, s["prompt"]
    zusatz = next(z for z in s["prompt_zusaetze"] if z["art"] == "stimmung")
    assert zusatz["doppelt_herausgenommen"] == ["evening mood"]


def test_ohne_teile_des_satzes_laesst_den_rest_wort_fuer_wort():
    satz = stimmung.STIMMUNGEN["abend"]["prompt_en"]
    assert stimmung.ohne_teile_des_satzes("warm light, a house", satz) == ("warm light, a house", ())
    assert stimmung.ohne_teile_des_satzes("a house, Evening Mood", satz) == (
        "a house", ("Evening Mood",))


# ====================================================================== (h) der zweite Teil

def test_der_ganze_satz_bei_abgeschaltetem_bildeingang():
    """GEGEN ALT ROT: Die Warnung trug hinten «bestellt 'image_edit'», ``denoise_bestellt`` 0,6.
    Geprüft wie der Lauf ruft: MIT dem Satz aus ``modus_satz``."""
    erg = {"modus_bestellt": "image_edit", "modus_gerechnet": "txt2img",
           "modus_abweichung": True, "parameter": {"denoise": 0.6}}
    modus = abholer.modus_vermerk(erg)
    satz = kosmo_szene.modus_satz("sSE", modus, "z-image-turbo", umriss_im_lauf=True,
                                  bildeingang_abgeschaltet=True)
    ki = abholer.ki_vermerk(erg, umriss_im_lauf=True, modus_satz=satz,
                            bildeingang_abgeschaltet=True)
    assert "image_edit" not in ki["warnung"] and "0.6" not in ki["warnung"]
    assert ki["denoise_bestellt"] is None
    assert "bestellt 'vis.bildeingang: false'" in satz and "image_edit" not in satz
    assert "hier nicht gerechnet" not in satz, "abgeschaltet ist nicht vergessen"
    # Ohne den Schalter bleibt alles, wie es war.
    alt = kosmo_szene.modus_satz("sSE", modus, "z-image-turbo", umriss_im_lauf=True)
    assert "bestellt 'image_edit'" in alt
    assert abholer.ki_vermerk(erg, modus_satz=alt)["denoise_bestellt"] == 0.6
