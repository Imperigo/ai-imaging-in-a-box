"""Entscheid 149 (Owner über die Zentrale, 24.10.2026, Antwort auf die Frage nach Messung 353, Option 1).

**Varianten rechnen ohne eigene Angabe mit Bildeingang 0,7 und «Umriss halten» im Lauf** (statt 0,5 nach
Entscheid 138); das erste Bild des Render-Knotens (ohne Grundlage) behält 0,5. Dazu ein bewusst
**«freies Bild»** (``vis.freies_bild: true``): ohne Grundbild als Start, ohne Umriss halten, für ein
Stimmungsbild — sichtbar gekennzeichnet bis ins Ergebnis (``freies_bild: true``, Satz «FREIES BILD»), die
Sätze zu Form und Fenster bleiben.

Dazu die kleinen Funde aus Ergebnis 351: B5 (nach «Freigeben» bleibt ein veralteter Zustand
``voll_grenze_erreicht`` stehen) und B6 (der Satz «wieder frei ab» schnitt die Sekunden ab).

**Seit dem 30.10.2026 aufgehoben, soweit es das freie Bild betrifft** (Owner-Entscheid Masstreue, A0051:
«jedes bild muss basierend auf blender render und multipasses laufen»): ``vis.freies_bild: true`` ist ein
endgültiger Mangel (``kosmo_szene.SATZ_MASSTREUE``), an der Brücke 400. Die Proben dazu stehen unten mit dem
neuen Soll; die Stärken je Art, B5/B6 und das Situationsmodell gelten weiter. Siehe auch
``test_masstreue_a0051.py``.

Ohne GPU, alles synthetisch (Regel 3).
"""
from __future__ import annotations

from datetime import datetime, timezone

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene

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
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): die Vorschau ist keine Ausnahme mehr,
    # sie startet vom Grundbild mit der Staerke der Variante.
    s = _lies(grundlage=GL, seed=7, guete="vorschau")
    assert s["bildeingang"] == kosmo_szene.BILDEINGANG_VORGABE_VARIANTE
    assert s["messschalter"]["bildeingang"]["herkunft"] == "vorgabe"
    s = _lies(grundlage=GL, seed=7, backbone="qwen-image-2.1")
    assert s["bildeingang"] is None
    assert s["messschalter"]["bildeingang"]["grund"].startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ)


# ================================================================ das freie Bild

def test_freies_bild_ist_seit_der_masstreue_ein_endgueltiger_mangel(himmel):  # noqa: F811
    """Masstreue (30.10.2026, A0051) statt Entscheid 149: kein freies Bild, die Vorgabe der Variante bleibt."""
    s = _lies(grundlage=GL, seed=7, freies_bild=True)
    assert s["freies_bild"] is False
    assert any(m.startswith(kosmo_szene.SATZ_MASSTREUE) for m in s["maengel_endgueltig"])
    assert s["bildeingang"] == 0.7 and s["umriss_halten"] == "im_lauf"
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "vorgabe"}
    assert s["messschalter"]["himmel_sichtbar"] == {"herkunft": "vorgabe"}
    assert not any(w.startswith(kosmo_szene.SATZ_FREIES_BILD) for w in s["warnungen"])
    assert "freies_bild" not in abholer.angewandt_der_szene(s)


def test_freies_bild_mit_umriss_bleibt_abgewiesen(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7, freies_bild=True, umriss_halten="im_lauf")
    assert s["freies_bild"] is False and s["umriss_halten"] == "im_lauf"
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "bestellt"}
    assert any(m.startswith(kosmo_szene.SATZ_MASSTREUE) for m in s["maengel_endgueltig"])


def test_ausgeschalteter_bildeingang_ist_auch_ein_freies_bild(himmel):  # noqa: F811
    # Masstreue (A0051, Gegenlesen Runde 2): das freie Bild unter anderem Namen — abgewiesen.
    s = _lies(grundlage=GL, seed=7, bildeingang=False)
    assert s["freies_bild"] is False
    assert s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}
    assert kosmo_szene.masstreue_satz_bildeingang_aus() in s["maengel_endgueltig"]


def test_ohne_schalter_kein_freies_bild_und_kein_feld(himmel):  # noqa: F811
    s = _lies(grundlage=GL, seed=7)
    assert s["freies_bild"] is False
    angewandt = abholer.angewandt_der_szene(s)
    assert "freies_bild" not in angewandt
    ergebnis = kosmo_szene.als_ergebnis("vis-1792000000-abcdef", [], angewandt=angewandt)
    assert "freies_bild" not in ergebnis


def test_widersprueche_sind_endgueltige_maengel(himmel):  # noqa: F811
    # Seit der Masstreue (A0051) sagt jede Lage mit `true` denselben Satz; ein falscher Wert bleibt Mangel.
    for vis, wort in (({"freies_bild": True, "bildeingang": 0.7}, kosmo_szene.SATZ_MASSTREUE),
                      ({"freies_bild": True, "skip": True}, kosmo_szene.SATZ_MASSTREUE),
                      ({"freies_bild": "ja"}, "erwartet war true")):
        s = _lies(**vis)
        assert any(wort in m for m in s["maengel"]), (vis, s["maengel"])
        assert s["freies_bild"] is False


def test_freies_bild_im_lauf_wird_abgewiesen_ohne_blender_und_bildmodell(tmp_path):
    """lies_szene → Abholer: seit der Masstreue (A0051) kein Lauf — weder Blender noch Bildmodell."""
    import json as _json
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = _json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"]["freies_bild"] = True
    pfad.write_text(_json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert kosmo_szene.SATZ_MASSTREUE in str(antwort["grund"])
    assert protokoll["render"] == [] and protokoll["multipass"] == []


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
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): ohne Skizze nimmt die Bruecke qwen-image-2.1 gar
    # nicht an — es gibt keinen Lizenzzustand mehr zu ueberholen.
    with pytest.raises(knotenweg.KnotenwegError, match="MASSTREUE"):
        _lege(tmp_path, _Uhr(), backbone="qwen-image-2.1")


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
    # Masstreue (A0051): die Spielregel am iPad bietet das freie Bild nicht mehr an.
    assert "freies_bild: true" not in kern
    assert "Jedes Bild rechnet auf der Blender-Grundlage" in kern
    # Die Kopie der Knotenansicht (Mac) folgt nach A0049/A0050 aus KosmoOrbit — bis dahin nennt sie es
    # noch; die Brücke weist es ab (`test_masstreue_a0051.py`).
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


# ================================================================ Ergebnis 357: drei kleine Funde

import pytest  # noqa: E402

from test_voll_ohne_klick import SZENE as _SZENE  # noqa: E402


@pytest.mark.parametrize("vis, wort", [({"freies_bild": True, "bildeingang": 0.7}, "MASSTREUE"),
                                       ({"freies_bild": True, "skip": True}, "MASSTREUE")])
def test_357_1_widerspruch_wird_schon_an_der_bruecke_abgewiesen(tmp_path, vis, wort):
    """S3 Gegenprobe: angenommen (200, wartet auf Freigabe) und erst nach «Freigeben» abgewiesen. Jetzt 400
    beim Annehmen, mit dem Satz des Abholers — und kein Ordner angelegt."""
    szene = dict(_SZENE, vis={**_SZENE["vis"], **vis})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, szene, b"glTF-bytes", "model.glb", kennung="vis-1790000000-00aa01")
    assert fehler.value.code == 400
    assert str(fehler.value).startswith("Der Auftrag hat Mängel, die einen Lauf verbieten:\n- ")
    assert wort in str(fehler.value) and "'vis.freies_bild'" in str(fehler.value)
    assert not (tmp_path / "vis-1790000000-00aa01").exists()


def test_357_1_freies_bild_allein_wird_seit_der_masstreue_abgewiesen(tmp_path):
    szene = dict(_SZENE, vis={**_SZENE["vis"], "freies_bild": True})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, szene, b"glTF-bytes", "model.glb", kennung="vis-1790000000-00aa02")
    assert fehler.value.code == 400 and kosmo_szene.SATZ_MASSTREUE in str(fehler.value)
    assert not (tmp_path / "vis-1790000000-00aa02").exists()
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == [kosmo_szene.masstreue_satz_freies_bild()]
    # Dieselbe Pruefung wie im Lauf, keine zweite: die Saetze sind wortgleich.
    gegen = dict(_SZENE, vis={**_SZENE["vis"], "freies_bild": True, "bildeingang": 0.7},
                 geometry={"path": "modell.glb", "format": "glb"})
    s = kosmo_szene.lies_szene(gegen, streng=False)
    assert set(kosmo_szene.widersprueche_beim_annehmen(gegen)) <= set(s["maengel_endgueltig"])


def _hinweise_mit(vermerk):
    ergebnis = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"kamera": "sSE", abholer.URTEIL_BILDEINGANG: {
            "staerke": vermerk.pop("staerke"), "weg": "eigener_start", "modus_bestellt": "bild_und_tiefe",
            "modus_gerechnet": "bild_und_tiefe", "modus_abweichung": False, **vermerk}})
    return [h for h in ergebnis["qa"]["verdict"]["hinweise"] if h.startswith(kosmo_szene.SATZ_BILDEINGANG)]


def test_357_2_die_variante_mit_vorgabe_07_traegt_ihren_satz():
    """S2: kein Satz «BILDEINGANG …» (in S2b schon, dort mit «Bestellt.»). Jetzt beide, mit Herkunft."""
    s2 = _hinweise_mit({"staerke": 0.7, "vorgabe": True, "herkunft": "vorgabe", "art": "variante"})
    assert len(s2) == 1 and "Staerke 0.7" in s2[0]
    assert s2[0].endswith("Vorgabe fuer Varianten (herkunft vorgabe, Entscheid 149).")
    s2b = _hinweise_mit({"staerke": 0.5, "vorgabe": True, "herkunft": "vorgabe_situationsmodell",
                         "art": "variante"})
    assert len(s2b) == 1 and s2b[0].endswith(
        "Vorgabe fuer ein Situationsmodell (herkunft vorgabe_situationsmodell, Entscheid 149, ergaenzt).")
    bestellt = _hinweise_mit({"staerke": 0.65})
    assert bestellt[0].endswith("Bestellt.")


def test_357_2_der_abholer_vermerkt_die_herkunft_auch_am_situationsmodell():
    """Der Vermerk am Kameraurteil kennt beide Vorgaben — vorher galt nur «vorgabe» als Vorgabe."""
    quelle = (_Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "abholer.py").read_text(
        encoding="utf-8")
    assert "_kosmo_szene.HERKUNFT_VORGABE_SITUATION):" in quelle
    assert 'urteil[URTEIL_BILDEINGANG]["herkunft"] = herkunft_bi' in quelle


def test_357_3_am_nach_dem_freigeben_kommt_aus_derselben_uhr(tmp_path):
    """S4: ``am`` trug die echte Uhrzeit, nicht die feste Uhr der Probe (freigeben kannte kein _uhr)."""
    uhr = _Uhr()
    for i in range(5):
        _lege(tmp_path, uhr, n=i)
    sechster = _lege(tmp_path, uhr, n=5)
    uhr.t += 125
    frei = knotenweg.freigeben(tmp_path, sechster["job_id"], sechster["approval_token"], _uhr=uhr)
    erwartet = datetime.fromtimestamp(uhr.t, timezone.utc).isoformat(timespec="seconds")
    assert frei[knotenweg.FELD_VOLL]["am"] == erwartet
    assert frei[knotenweg.FELD_FREIGABE]["am"] == erwartet == frei["updated_at"]
    assert sechster["created_at"] == datetime.fromtimestamp(T0, timezone.utc).isoformat(
        timespec="seconds")
