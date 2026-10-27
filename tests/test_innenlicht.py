"""Innenkamera schwarz (Generalprobe auf-20261027-373, S9 / B8) — Lage, Raumleuchte, Helligkeit.

Der IFC-Weg mit Innenraum lief durch, das Schönbild der Kamera «Innenraum» war schwarz
(1 von 255): Fenster und Türen der Probe-IFC sind deckende Quader, der Raum ist eine
geschlossene Kiste, und der Runner beleuchtet nur von aussen. Geprüft wird hier:

* die reine Rechnung in :mod:`aiimaging.innenlicht` — Lage aus zehn Strahlen (innen, aussen,
  in einem Bauteil), Lichtplan, Nachstellen, Helligkeit, Vermerk mit «INNENBILD ZU DUNKEL»;
* die Strahlen an einem **synthetischen** Haus aus Quadern (Masse wie das Erdgeschoss der
  Probe, Regel 3) — ein kleiner Strahlenschuss in reinem Python ersetzt Blenders
  ``scene.ray_cast``; dazu ein Standpunkt aus ``raumkamera`` im Raum, nicht in der Wand;
* der Runner statisch (er braucht Blender): Aufruf, Reihenfolge, Bericht, unsichtbare Leuchte.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from aiimaging import innenlicht, kosmo_szene, raumkamera

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")


# ── Ein Haus aus Quadern und ein Strahlenschuss in reinem Python ──────────────────────────

def _haus(*, offene_tuer: bool = False, vordach: bool = False) -> list:
    """Ein Raum 4,2 x 4,5 m, Decke bei 2,4 m, Wände 0,36 m; Fenster/Tür deckend (wie r57)."""
    boxen = [((-0.5, -0.5, -0.4), (5.0, 5.0, 0.0)),          # Bodenplatte
             ((-0.5, -0.5, 2.4), (5.0, 5.0, 2.8)),           # Decke
             ((-0.18, 0.0, 0.0), (0.18, 4.5, 2.4)),          # Wand West
             ((4.11, 0.0, 0.0), (4.29, 4.5, 2.4)),           # Wand Ost
             ((0.0, 4.41, 0.0), (4.2, 4.59, 2.4))]           # Wand Nord
    if offene_tuer:
        # Süd-Wand mit einer offenen Tür (0,35–1,85): zwei Stücke, die Öffnung leer.
        boxen += [((-0.18, -0.18, 0.0), (0.35, 0.18, 2.4)),
                  ((1.85, -0.18, 0.0), (4.29, 0.18, 2.4))]
    else:
        # Süd-Wand mit DECKENDEM Fenster und deckender Tür — der Fall der Probe.
        boxen.append(((-0.18, -0.18, 0.0), (4.29, 0.18, 2.4)))
    if vordach:
        boxen.append(((-0.5, -3.0, 2.6), (5.0, -0.18, 2.8)))
    return boxen


def _strahl_box(o, r, lo, hi):
    """Eintritt/Austritt eines Strahls in einen Quader — ``(t, rueckseite)`` oder ``None``."""
    t0, t1 = -math.inf, math.inf
    for i in range(3):
        if abs(r[i]) < 1e-12:
            if not lo[i] <= o[i] <= hi[i]:
                return None
            continue
        a, b = (lo[i] - o[i]) / r[i], (hi[i] - o[i]) / r[i]
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    if t1 < max(t0, 0.0):
        return None
    if t0 > 1e-9:
        return t0, False                                     # von aussen: Vorderseite
    return t1, True                                          # Auge im Quader: Rückseite


def _strahlen(auge, boxen, weite=31.0) -> dict:
    treffer = {}
    for name, r in innenlicht.STRAHLEN.items():
        beste = None
        for lo, hi in boxen:
            t = _strahl_box(auge, r, lo, hi)
            if t is not None and t[0] <= weite and (beste is None or t[0] < beste[0]):
                beste = t
        treffer[name] = (None if beste is None else
                         {"abstand_m": round(beste[0], 4), "rueckseite": beste[1]})
    return treffer


# ── Lage ──────────────────────────────────────────────────────────────────────────────

def test_kamera_der_probe_steht_innen():
    """Der Standpunkt «Innenraum» aus 373 (KosmoOrbit [0.84, 1.6, -0.9], y oben) im Raum."""
    auge = (0.84, 0.9, 1.6)
    befund = innenlicht.lage(_strahlen(auge, _haus()))
    assert befund["lage"] == innenlicht.LAGE_INNEN, befund
    assert befund["decke_m"] == pytest.approx(0.8)
    assert befund["waende"] == 8
    assert befund["rueckseiten"] == 0


def test_offene_tuer_bleibt_innen():
    befund = innenlicht.lage(_strahlen((0.84, 0.9, 1.6), _haus(offene_tuer=True)))
    assert befund["lage"] == innenlicht.LAGE_INNEN, befund


def test_aussenkamera_bleibt_aussen():
    """Der Standpunkt «Eingang» (26 m vor dem Haus): keine Decke — kein Licht, keine Änderung."""
    befund = innenlicht.lage(_strahlen((7.4, -26.4, 1.6), _haus()))
    assert befund["lage"] == innenlicht.LAGE_AUSSEN
    assert befund["decke_m"] is None


def test_unter_dem_vordach_bleibt_aussen():
    """Decke über dem Auge, aber Wände nur zur Fassade hin — das ist kein Raum."""
    befund = innenlicht.lage(_strahlen((2.0, -1.5, 1.6), _haus(vordach=True)))
    assert befund["decke_m"] is not None
    assert befund["lage"] == innenlicht.LAGE_AUSSEN, befund


def test_kamera_in_der_wand():
    befund = innenlicht.lage(_strahlen((0.0, 2.0, 1.6), _haus()))
    assert befund["lage"] == innenlicht.LAGE_IN_BAUTEIL, befund


def test_ohne_strahlen_unbekannt_nie_aussen():
    assert innenlicht.lage(None)["lage"] == innenlicht.LAGE_UNBEKANNT
    assert innenlicht.lage({})["lage"] == innenlicht.LAGE_UNBEKANNT


def test_standpunkt_aus_raumkamera_im_raum_nicht_in_der_wand():
    """Die Standpunkte des Raumlesers liegen im Umriss, mit Wandabstand — und die Strahlen
    sagen innen, nicht «in einem Bauteil»."""
    raum = {"name": "Wohnen", "grundriss_m": [[0.18, 0.18], [4.11, 0.18], [4.11, 4.41],
                                              [0.18, 4.41]],
            "hoehe_m": 2.4, "z_unten_m": 0.0}
    alle = raumkamera.standpunkte(raum)
    assert alle["n_brauchbar"] == 2
    for st in alle["standpunkte"]:
        x, y, z = st["auge"]
        assert raumkamera.ist_innen((x, y), raum["grundriss_m"])
        assert raumkamera.abstand_zum_rand((x, y), raum["grundriss_m"]) >= \
            raumkamera.WANDABSTAND_INNEN_M - 1e-6
        befund = innenlicht.lage(_strahlen((x, y, z), _haus()))
        assert befund["lage"] == innenlicht.LAGE_INNEN, (st["art"], befund)


# ── Lichtplan und Nachstellen ─────────────────────────────────────────────────────────

def test_lichtplan_unter_der_decke_ueber_der_raummitte():
    auge = (0.84, 0.9, 1.6)
    plan = innenlicht.lichtplan(auge, _strahlen(auge, _haus()))
    x, y, z = plan["ort"]
    # Mitte zwischen den Innenflächen (0,18 … 4,11 / 0,18 … 4,41), knapp unter 2,4 m.
    assert x == pytest.approx((0.18 + 4.11) / 2, abs=1e-3)
    assert y == pytest.approx((0.18 + 4.41) / 2, abs=1e-3)
    assert z == pytest.approx(2.4 - innenlicht.LEUCHTE_UNTER_DECKE_M, abs=1e-3)
    bx, by = plan["groesse_m"]
    assert bx < 4.11 - 0.18 and by < 4.41 - 0.18
    assert innenlicht.LEISTUNG_MIN_W <= plan["leistung_w"] <= innenlicht.LEISTUNG_MAX_W


def test_lichtplan_ohne_decke_verweigert():
    with pytest.raises(ValueError):
        innenlicht.lichtplan((7.4, -26.4, 1.6), _strahlen((7.4, -26.4, 1.6), _haus()))


def test_nachstellen_schwarz_hellt_maximal_auf():
    n = innenlicht.nachstellen(0.0, 1000.0)
    assert n["faktor"] == innenlicht.FAKTOR_GRENZE and not n["fertig"]
    assert n["leistung_w"] == pytest.approx(16000.0)


def test_nachstellen_am_ziel_fertig_und_zu_hell_dunkler():
    assert innenlicht.nachstellen(innenlicht.ZIEL_255, 800.0)["fertig"]
    hell = innenlicht.nachstellen(250.0, 800.0)
    assert hell["faktor"] < 1.0 and hell["leistung_w"] < 800.0
    dunkel = innenlicht.nachstellen(40.0, 800.0)
    assert 1.0 < dunkel["faktor"] <= innenlicht.FAKTOR_GRENZE


def test_nachstellen_ohne_messung_laesst_stehen():
    n = innenlicht.nachstellen(None, 500.0)
    assert n == {"faktor": 1.0, "leistung_w": 500.0, "abweichung_ev": None, "fertig": True}


# ── Helligkeit und Vermerk ────────────────────────────────────────────────────────────

def test_helligkeit_in_grauwerten():
    schwarz = [1 / 255, 1 / 255, 1 / 255, 1.0] * 100
    assert innenlicht.helligkeit(schwarz)["mittel_255"] == pytest.approx(1.0)
    weiss = [1.0, 1.0, 1.0, 0.0] * 50                      # Alpha zählt nicht
    assert innenlicht.helligkeit(weiss)["mittel_255"] == pytest.approx(255.0)
    assert innenlicht.helligkeit([])["mittel_255"] is None
    gross = [0.5, 0.5, 0.5] * 200000
    h = innenlicht.helligkeit(gross, 3)
    assert h["n"] <= innenlicht.HELLIGKEIT_HOECHSTENS_PUNKTE + 1
    assert h["mittel_255"] == pytest.approx(127.5)
    with pytest.raises(ValueError):
        innenlicht.helligkeit([0.0, 0.0], 2)


def _bericht(lage, mittel, leistung=900.0):
    return {"innenlicht": {"lage": lage, "grund": "Probe.",
                           "leuchte": {"leistung_w": leistung} if lage == "innen" else None},
            "helligkeit": {"mittel_255": mittel}}


def test_vermerk_innen_zu_dunkel_ist_eine_warnung():
    v = innenlicht.vermerk(_bericht("innen", 1.0), "Innenraum")
    assert v["zu_dunkel"] is True
    assert v["satz"].startswith(innenlicht.SATZ_ZU_DUNKEL)
    assert "1 von 255" in v["satz"] and "'Innenraum'" in v["satz"]


def test_vermerk_innen_hell_ist_eine_auskunft():
    v = innenlicht.vermerk(_bericht("innen", 112.0), "Innenraum")
    assert v["zu_dunkel"] is False
    assert v["satz"].startswith(innenlicht.SATZ_INNENLICHT)
    assert "900 W" in v["satz"] and "112 von 255" in v["satz"]


def test_vermerk_aussen_schweigt_und_bauteil_warnt():
    assert innenlicht.vermerk(_bericht("aussen", 3.0), "Eingang") is None
    assert innenlicht.vermerk({}, "Eingang") is None
    assert innenlicht.vermerk(None, "Eingang") is None
    v = innenlicht.vermerk(_bericht("in_bauteil", 0.0), "Innenraum")
    assert v["satz"].startswith(innenlicht.SATZ_IN_BAUTEIL)


def test_satz_erreicht_verdict_hinweise():
    v = innenlicht.vermerk(_bericht("innen", 1.0), "Innenraum")
    saetze = kosmo_szene._aufsicht_saetze(
        None, [{"kamera": "Innenraum", kosmo_szene.URTEIL_INNENLICHT: v}])
    assert any(s.startswith("INNENBILD ZU DUNKEL") for s in saetze)


# ── Der Runner, statisch (er braucht Blender) ─────────────────────────────────────────

@pytest.fixture(scope="module")
def quelle() -> str:
    return RUNNER.read_text(encoding="utf-8")


def _main(quelle: str) -> str:
    return quelle[quelle.index("def main() -> int:"):]


def test_runner_prueft_die_lage_vor_dem_schoenbild(quelle):
    m = _main(quelle)
    i = m.index("innen_befund = _innenlicht_setzen(")
    assert i < m.index("bpy.ops.render.render(write_still=not a.ohne_beauty)")
    # nach Materialwahl und Glas — die Vorprobe misst mit ihnen
    assert m.index("_glas_klar()") < i
    assert m.index("_materialien_setzen(a") < i


def test_runner_stellt_den_hintergrund_innen_nicht_nach(quelle):
    m = _main(quelle)
    block = m[m.index("innen_befund = _innenlicht_setzen("):m.index("beauty_png = out_dir")]
    assert 'innen_befund.get("lage") == "innen"' in block
    assert "_hintergrund_abstimmen(" in block


def test_runner_leuchte_nur_innen_und_unsichtbar(quelle):
    f = quelle[quelle.index("def _innenlicht_setzen("):quelle.index("def _helligkeit_messen(")]
    assert 'if befund.get("lage") != "innen":\n        return befund' in f
    leuchte = quelle[quelle.index("def _innenleuchte_setzen("):
                     quelle.index("def _innenlicht_abstimmen(")]
    assert 'type="AREA"' in leuchte
    assert "visible_camera = False" in leuchte


def test_runner_strahlen_uebergehen_umfeld_umgebung_gelaende(quelle):
    f = quelle[quelle.index("def _innenraum_pruefen("):quelle.index("def _innenleuchte_setzen(")]
    for teil in ("_ist_umfeld_objekt(obj)", "_ist_kontext(obj)", "_ist_gelaende_objekt(obj"):
        assert teil in f


def test_runner_bericht_traegt_helligkeit_und_lage(quelle):
    m = _main(quelle)
    assert 'report["helligkeit"] = ' in m
    assert 'report["innenlicht"] = innen_befund' in m
    assert "_helligkeit_messen(beauty_png)" in m


def test_innenlicht_ist_rein():
    text = (Path(innenlicht.__file__)).read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import|from)\s+bpy", text, re.M)
