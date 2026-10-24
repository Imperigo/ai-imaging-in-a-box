"""Entscheid 149 (Owner über die Zentrale, 24.10.2026, Antwort auf die Frage nach Messung 353, Option 1).

**Varianten rechnen ohne eigene Angabe mit Bildeingang 0,7 und «Umriss halten» im Lauf** (statt 0,5 nach
Entscheid 138); das erste Bild des Render-Knotens (ohne Grundlage) behält 0,5. Dazu ein bewusst
**«freies Bild»** (``vis.freies_bild: true``): ohne Grundbild als Start, ohne Umriss halten, für ein
Stimmungsbild — sichtbar gekennzeichnet bis ins Ergebnis (``freies_bild: true``, Satz «FREIES BILD»), die
Sätze zu Form und Fenster bleiben.

Dazu die kleinen Funde aus Ergebnis 351: B5 (nach «Freigeben» bleibt ein veralteter Zustand
``voll_grenze_erreicht`` stehen) und B6 (der Satz «wieder frei ab» schnitt die Sekunden ab).

Ohne GPU, alles synthetisch (Regel 3).
"""
from __future__ import annotations

from datetime import datetime, timezone

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene

from test_bildeingang_vorgabe_e138 import _lauf_mit
from test_varianten_vorgabe_e126 import _szene, himmel  # noqa: F401 — Fixture
from test_voll_ohne_klick import T0, _lege, _Uhr

GL = "gl-0a1b2c3d4e5f6071"


def _lies(**vis):
    return kosmo_szene.lies_szene(_szene(**vis), streng=False)


# ================================================================ die Stärke je Art

def test_variante_ohne_angabe_rechnet_mit_07_aus_der_vorgabe(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, guete="voll")
    assert not any("bildeingang" in m for m in s["maengel"])
    assert s["bildeingang"] == 0.7 == kosmo_szene.BILDEINGANG_VORGABE_VARIANTE
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}
    assert s["umriss_halten"] == "im_lauf"
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "vorgabe"}
    assert s["freies_bild"] is False
    assert abholer.angewandt_der_szene(s)["messschalter"]["bildeingang"] == {
        "wert": 0.7, "herkunft": "vorgabe"}


def test_erstes_bild_ohne_grundlage_behaelt_05(himmel):  # noqa: F811
    s = _lies()
    assert s["bildeingang"] == 0.5 == kosmo_szene.BILDEINGANG_VORGABE
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}


def test_eigene_staerke_gewinnt_auch_an_der_variante(himmel):  # noqa: F811
    for wert in (0.5, 0.6, 0.8):
        s = _lies(grundlage=GL, seed=7, bildeingang=wert)
        assert s["bildeingang"] == wert
        assert s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}


def test_ausnahmen_aus_138_bleiben_an_der_variante(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, guete="vorschau")
    assert s["bildeingang"] is None
    assert s["messschalter"]["bildeingang"]["herkunft"] == "vorgabe_entfaellt"
    s = _lies(grundlage=GL, seed=7, backbone="qwen-image-2.1")
    assert s["bildeingang"] is None
    assert s["messschalter"]["bildeingang"]["grund"].startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ)


# ================================================================ das freie Bild

def test_freies_bild_schaltet_bildeingang_und_umriss_aus_mit_herkunft(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, freies_bild=True)
    # (Eine fehlende Textur am Rechner der Probe gehört nicht zu dieser Frage.)
    assert not any("freies_bild" in m or "bildeingang" in m for m in s["maengel"])
    assert s["freies_bild"] is True
    assert s["bildeingang"] is None and s["umriss_halten"] is None
    assert s["messschalter"]["bildeingang"] == {"herkunft": "freies_bild"}
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "freies_bild"}
    # Was sonst Vorgabe ist (Stoff vorne, Himmel), bleibt.
    assert s["messschalter"]["himmel_sichtbar"] == {"herkunft": "vorgabe"}
    assert any(w.startswith(kosmo_szene.SATZ_FREIES_BILD) for w in s["warnungen"])
    angewandt = abholer.angewandt_der_szene(s)
    assert angewandt["freies_bild"]["satz"].startswith(kosmo_szene.SATZ_FREIES_BILD)
    assert angewandt["messschalter"]["bildeingang"] == {"wert": False, "herkunft": "freies_bild"}
    assert angewandt["messschalter"]["umriss_halten"] == {"wert": False, "herkunft": "freies_bild"}
    assert kosmo_szene.ergebnis_saetze_der_szene(angewandt)[-1].startswith(
        kosmo_szene.SATZ_FREIES_BILD)


def test_ausdruecklicher_umriss_gewinnt_auch_im_freien_bild(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, freies_bild=True, umriss_halten="im_lauf")
    assert s["freies_bild"] is True and s["umriss_halten"] == "im_lauf"
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "bestellt"}


def test_ausgeschalteter_bildeingang_ist_auch_ein_freies_bild(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, bildeingang=False)
    assert s["freies_bild"] is True
    assert s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}
    assert abholer.angewandt_der_szene(s)["freies_bild"]["herkunft"] == "bestellt"


def test_ohne_schalter_kein_freies_bild_und_kein_feld(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7)
    assert s["freies_bild"] is False
    angewandt = abholer.angewandt_der_szene(s)
    assert "freies_bild" not in angewandt
    ergebnis = kosmo_szene.als_ergebnis("vis-1792000000-abcdef", [], angewandt=angewandt)
    assert "freies_bild" not in ergebnis


def test_widersprueche_sind_endgueltige_maengel(himmel):  # noqa: F811
    for vis, wort in (({"freies_bild": True, "bildeingang": 0.7}, "widerspricht"),
                      ({"freies_bild": True, "skip": True}, "Nur Grundlage"),
                      ({"freies_bild": "ja"}, "erwartet war true")):
        s = _lies(**vis)
        assert any(wort in m for m in s["maengel"]), (vis, s["maengel"])
        assert s["freies_bild"] is False


def test_freies_bild_im_lauf_bis_ins_ergebnis(tmp_path):
    """lies_szene → Abholer → render-result: Kennzeichen oben, Vermerk, Satz; FORM/FENSTER bleiben."""
    antwort, protokoll = _lauf_mit(tmp_path, freies_bild=True)
    assert protokoll["render"] and all(a.bildeingang_staerke is None for a in protokoll["render"])
    ergebnis = antwort["ergebnis"]
    assert ergebnis["freies_bild"] is True
    assert ergebnis["angewandt"]["freies_bild"]["satz"].startswith(kosmo_szene.SATZ_FREIES_BILD)
    assert ergebnis["angewandt"]["messschalter"]["bildeingang"]["herkunft"] == "freies_bild"
    hinweise = ergebnis["qa"]["verdict"]["hinweise"]
    assert any(h.startswith(kosmo_szene.SATZ_FREIES_BILD) for h in hinweise)
    # Der Rückfall-Satz nennt den abgeschalteten Bildeingang, nicht «bestellt image_edit».
    ki = ergebnis["angewandt"]["ki"]
    assert ki["modus"] == "txt2img"
    assert "abgeschaltet" in ki["warnungen"][0]


def test_freies_bild_unterdrueckt_form_und_fenster_nicht():
    """Die Sätze zu Form und Fenster entstehen aus dem Urteil, unabhängig vom freien Bild — der Satz
    des freien Bilds kommt hinzu, er ersetzt nichts."""
    angewandt = {"freies_bild": {"satz": kosmo_szene.freies_bild_satz()},
                 "variante": {"satz": "FORM WEICHT VOM GRUNDBILD AB, Kamera 'sSE'"}}
    saetze = kosmo_szene.ergebnis_saetze_der_szene(angewandt)
    assert saetze[0].startswith("FORM WEICHT") and saetze[1].startswith(kosmo_szene.SATZ_FREIES_BILD)
    assert "Form und Fenster bleiben stehen" in kosmo_szene.freies_bild_satz()


# ================================================================ Ergebnis 351, B5 und B6

def test_b5_nach_freigeben_ist_der_grenzzustand_ueberholt(tmp_path):
    uhr = _Uhr()
    for i in range(5):
        _lege(tmp_path, uhr, n=i)
    sechster = _lege(tmp_path, uhr, n=5)
    assert sechster[knotenweg.FELD_VOLL]["zustand"] == knotenweg.ZUSTAND_GRENZE
    frei = knotenweg.freigeben(tmp_path, sechster["job_id"], sechster["approval_token"])
    vermerk = frei[knotenweg.FELD_VOLL]
    assert vermerk["zustand"] == knotenweg.ZUSTAND_VON_HAND == "von_hand_freigegeben"
    assert vermerk["vorher"] == "voll_grenze_erreicht"
    assert "wieder_frei_ab" not in vermerk
    assert vermerk["am"] == frei[knotenweg.FELD_FREIGABE]["am"]
    # Der Klick zählt weiter nicht zur Grenze.
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["laeufe"] == 5


def test_b5_lizenzzustand_wird_ebenso_ueberholt(tmp_path):
    z = _lege(tmp_path, _Uhr(), backbone="qwen-image-2.1")
    assert z[knotenweg.FELD_VOLL]["zustand"] == knotenweg.ZUSTAND_LIZENZ
    frei = knotenweg.freigeben(tmp_path, z["job_id"], z["approval_token"])
    assert frei[knotenweg.FELD_VOLL]["vorher"] == knotenweg.ZUSTAND_LIZENZ


def test_b5_ohne_vollvermerk_aendert_freigeben_nichts_daran(tmp_path):
    z = _lege(tmp_path, _Uhr(), ohne_klick=False)
    frei = knotenweg.freigeben(tmp_path, z["job_id"], z["approval_token"])
    assert knotenweg.FELD_VOLL not in frei and frei["status"] == bruecke.STATUS_QUEUED


def test_b6_der_satz_rundet_auf_die_naechste_minute_die_iso_zeit_bleibt_genau(tmp_path):
    # Der erste Lauf 49 s nach einer vollen Minute: frei ab hh:mm:49 → im Satz die nächste Minute.
    start = (T0 // 60) * 60 + 49
    uhr = _Uhr(start)
    for i in range(5):
        _lege(tmp_path, uhr, n=i)
    stand = knotenweg.voll_stand(tmp_path, _uhr=uhr)
    genau = start + 3600
    assert stand["wieder_frei_ab"] == datetime.fromtimestamp(genau, timezone.utc).isoformat(
        timespec="seconds")
    aufgerundet = datetime.fromtimestamp(genau - 49 + 60).strftime("%H:%M")
    abgeschnitten = datetime.fromtimestamp(genau).strftime("%H:%M")
    assert aufgerundet != abgeschnitten
    assert f"wieder frei ab {aufgerundet}." in stand["satz"]


def test_b6_auf_die_minute_genau_bleibt_die_minute():
    ts = (T0 // 60) * 60
    assert knotenweg._uhrzeit(ts) == datetime.fromtimestamp(ts).strftime("%H:%M")


def test_b4_der_satz_sagt_dass_grundlage_rendern_mitzaehlt(tmp_path):
    uhr = _Uhr()
    for i in range(5):
        _lege(tmp_path, uhr, n=i)
    satz = knotenweg.voll_stand(tmp_path, _uhr=uhr)["satz"]
    assert "«Grundlage rendern» (nur Blender) zählt mit" in satz
    # Die Zählregel ist unverändert: ein Lauf nur mit Blender wartet bei erreichter Grenze.
    assert _lege(tmp_path, uhr, n=9, skip=True)[knotenweg.FELD_VOLL]["zustand"] == \
        knotenweg.ZUSTAND_GRENZE


# ================================================================ Claude erfährt es beim Handschlag

def test_die_spielregel_der_mac_app_nennt_das_freie_bild():
    from pathlib import Path
    wurzel = Path(__file__).resolve().parents[1]
    kern = (wurzel / "ipad" / "Visbox.swiftpm" / "Kern" / "Mcpkern.swift").read_text(encoding="utf-8")
    assert "freies_bild: true an vis_render oder vis_varianten" in kern
    assert "nie modelltreu" in kern
    wirt = (wurzel / "kosmovis" / "apps" / "visbox-knoten" / "src" / "ki-wirt.ts").read_text(
        encoding="utf-8")
    assert "freies_bild: true" in wirt


# ================================================================ 149 ergänzt: das Situationsmodell

import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "tools"))
import make_test_glb  # noqa: E402


def _variante_vorgabe():
    return {"bildeingang": 0.7, "messschalter": {"bildeingang": {"herkunft": "vorgabe"}}}


def test_situationsmodell_variante_rechnet_mit_05_und_sagt_warum(tmp_path):
    anlage = tmp_path / "anlage.glb"
    assert make_test_glb.main([str(anlage), "--situation"]) == 0
    situation = abholer.situation_des_modells(anlage, "Y")
    assert situation["ja"] is True
    neu = kosmo_szene.bildeingang_fuer_situationsmodell(_variante_vorgabe(), situation)
    assert neu["bildeingang"] == 0.5 == kosmo_szene.BILDEINGANG_VORGABE_SITUATION
    ms = neu["messschalter"]["bildeingang"]
    assert ms["herkunft"] == "vorgabe_situationsmodell" == kosmo_szene.HERKUNFT_VORGABE_SITUATION
    assert "SITUATIONSMODELL" in ms["grund"] and "Entscheid 149" in ms["grund"]
    assert abholer.angewandt_der_szene(neu)["messschalter"]["bildeingang"]["wert"] == 0.5


def test_haus_bleibt_bei_07(tmp_path):
    haus = tmp_path / "haus.glb"
    assert make_test_glb.main([str(haus)]) == 0
    situation = abholer.situation_des_modells(haus, "Y")
    assert situation["ja"] is False
    szene = _variante_vorgabe()
    assert kosmo_szene.bildeingang_fuer_situationsmodell(szene, situation) is szene


def test_ohne_modell_zaehlt_die_vogelschau_der_grundlage():
    situation = abholer.situation_des_modells(None, "Y", {"vogelschau-sSE": {}})
    assert situation["ja"] is True and "Vogelschau" in situation["grund"]
    assert abholer.situation_des_modells(None, "Y", {"sSE": {}}) is None
    neu = kosmo_szene.bildeingang_fuer_situationsmodell(_variante_vorgabe(), situation)
    assert neu["bildeingang"] == 0.5


def test_situationsmodell_eigene_staerke_und_freies_bild_gewinnen():
    ja = {"ja": True, "grund": "SITUATIONSMODELL (Probe)"}
    eigen = {"bildeingang": 0.7, "messschalter": {"bildeingang": {"herkunft": "bestellt"}}}
    assert kosmo_szene.bildeingang_fuer_situationsmodell(eigen, ja) is eigen
    frei = {"bildeingang": None, "messschalter": {"bildeingang": {"herkunft": "freies_bild"}}}
    assert kosmo_szene.bildeingang_fuer_situationsmodell(frei, ja) is frei
    erstes = {"bildeingang": 0.5, "messschalter": {"bildeingang": {"herkunft": "vorgabe"}}}
    assert kosmo_szene.bildeingang_fuer_situationsmodell(erstes, ja) is erstes
    unbekannt = {"ja": None, "grund": "NICHT BEURTEILT"}
    v = _variante_vorgabe()
    assert kosmo_szene.bildeingang_fuer_situationsmodell(v, unbekannt) is v
