"""Folgebau zu «Skizze führt das Bild»: Auflage A1, Entscheide 96a und 96b (15.10.2026).

* **A1 (Auflage des Integrators):** Der Name einer Skizze ist ein RELATIVER Pfad in der Mappe.
  Drüben weist der Vertrag ab (``skizzenNameMangel``); hier wird **unabhängig nochmals** geprüft —
  beim Lesen der Szene, beim Annehmen (``knotenweg.lege_an``) und vor dem Rechnen
  (``abholer.skizzenlauf``: dazu muss der Name in der Mappe als Skizze stehen).
* **96a:** Hängt eine Skizze am Render-Knoten, ist ihre Bemerkung die Anweisung. Die Liste der
  Mappe meldet sie darum mit (``bemerkung``, ``None`` ohne), damit der Knoten VOR dem Senden sagen
  kann, dass ohne Bemerkung nichts geht. Die Bibliothek nimmt sie wie bisher, wenn keine
  ``anweisung`` kommt, und weist ohne Bemerkung ab.
* **96b:** Das Bild entsteht vom Standpunkt des Bildes, AUF DAS gezeichnet wurde. Jedes gerechnete
  Bild trägt dafür seit heute ``herkunft.standpunkt``; ``rechne_skizze`` nimmt genau diesen.
  Ohne Unterlage oder ohne bekannten Standpunkt bleibt es beim Standpunkt der Mappe — und das
  steht am Bild und am Ergebnis.

Regel 3: alles synthetisch, Geometrie/Multipass/Bildmodell sind Attrappen (Muster
``test_skizze_fuehrt``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from aiimaging import abholer, arbeitsgang, bruecke, kette, knotenweg, kosmo_szene, projekt  # noqa: E402
from aiimaging.kette import ART_MULTIPASS  # noqa: E402
from test_skizze_fuehrt import (KENNUNG, ROT, _abholen, _bestellen_und_freigeben, _ergebnis,  # noqa: E402
                                _glb, _Modell, _rgba_png, _szene, _tabelle, mappe)  # noqa: F401

AUGE = [3.0, 1.6, 12.0]
ZIEL = [3.0, 1.6, 0.0]


def _mit_mitschrift(modell, mitschrift: list) -> dict:
    """Die Tabelle aus ``test_skizze_fuehrt``, deren Multipass mitschreibt, mit welchem Standpunkt
    er gerufen wurde."""
    tabelle = _tabelle(modell)
    echt = tabelle[ART_MULTIPASS]

    def multipass(*, knoten, eingaben, out_dir):
        # `rahmung` steht immer im Knoten (Vorgabe «bauwerk», wirkt nur mit `kamera`) — hier zaehlt,
        # welcher Standpunkt bestellt ist.
        mitschrift.append({k: knoten.params.get(k) for k in projekt.STANDPUNKT_FELDER_BILD
                           if knoten.params.get(k) is not None and k != "rahmung"})
        return echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir)

    return {**tabelle, ART_MULTIPASS: multipass}


def _skizze_auf(mappe, name, ueber, bemerkung="ein Vordach") -> None:
    _rgba_png(mappe / name, 4, 4, {(1, 1): (*ROT, 255)})
    p = projekt.oeffne(mappe)["projekt"]
    projekt.vermerke_skizze(p, skizze=name, ueber=ueber, bemerkung=bemerkung)
    projekt.speichere(p, mappe)


def _bild_von_hand(mappe, **standpunkt) -> str:
    """Ein Bild aus einem Lauf mit bestelltem Standpunkt (``auge``/``blick_auf``)."""
    aus = arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(_Modell()), qa=False,
                             **standpunkt)
    return aus["bilder"][-1]


# ======================================================================================
# A1 · der Name ist ein relativer Pfad in der Mappe
# ======================================================================================

@pytest.mark.parametrize("name", ["skizze-a.png", "skizzen/fassade-sued.png", "a..b.png",
                                  ".versteckt.png", "a" * kosmo_szene.SKIZZENNAME_HOECHSTENS])
def test_a1_gueltige_namen(name):
    assert kosmo_szene.skizzenname_mangel(name) is None


@pytest.mark.parametrize("fall,name,satz", [
    ("Segment ..", "../../etc/passwd", "«.» oder «..»"),
    ("Segment .. in der Mitte", "skizzen/../../x.png", "«.» oder «..»"),
    ("Segment .", "./skizze.png", "«.» oder «..»"),
    ("fuehrender /", "/etc/passwd", "beginnt mit «/»"),
    ("fuehrender Backslash", "\\\\server\\freigabe\\x.png", "Backslash"),
    ("Backslash ueberhaupt", "skizzen\\x.png", "Backslash"),
    ("Laufwerk", "C:/Windows/x.png", "Laufwerk"),
    ("Laufwerk ohne Schraegstrich", "c:x.png", "Laufwerk"),
    ("Steuerzeichen", "skizze\n.png", "Steuerzeichen"),
    ("Nullzeichen", "skizze\x00.png", "Steuerzeichen"),
    ("Loeschzeichen", "skizze\x7f.png", "Steuerzeichen"),
    ("zu lang", "a" * (kosmo_szene.SKIZZENNAME_HOECHSTENS + 1), "hoechstens 255"),
    ("kein Text", 7, "kein Text"),
])
def test_a1_abgewiesen_je_regel(fall, name, satz):
    assert satz in (kosmo_szene.skizzenname_mangel(name) or ""), fall


def test_a1_die_szene_traegt_den_mangel_und_keinen_namen():
    gelesen = kosmo_szene.skizze_aus_szene({"quelle": "mappe", "name": "../x.png"})
    assert gelesen["name"] is None
    assert any("'skizze.name'" in m and "«..»" in m for m in gelesen["maengel"])


@pytest.mark.parametrize("name", ["../skizze-a.png", "/tmp/skizze-a.png", "C:skizze-a.png",
                                  "skizze\\a.png"])
def test_a1_beim_annehmen_abgewiesen_bevor_die_mappe_gelesen_wird(tmp_path, mappe, name):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path / "ablage", _szene(name=name), _glb(mappe), "model.glb",
                          kennung=KENNUNG, mappe=mappe.name, mappe_pfad=mappe)
    assert "abgewiesen" in str(fehler.value)
    assert not (tmp_path / "ablage" / KENNUNG).exists()


def test_a1_der_abholer_prueft_nochmals_auch_einen_auftrag_von_hand(tmp_path, mappe):
    """Ein Auftrag, der am Server vorbei in die Ablage kam: Der Abholer rechnet ihn nicht."""
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-a.png"))
    szene = json.loads((ordner / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
    for name, satz in [("../skizze-a.png", "«.» oder «..»"),
                       ("skizze-nie.png", "steht nicht als Skizze in der Mappe")]:
        rechne_gerufen = []
        auftrag = {"szene": {**szene, "skizze": {"quelle": "mappe", "name": name}},
                   "verzeichnis": ordner}
        with pytest.raises(abholer.AbholerError) as fehler:
            abholer.skizzenlauf(auftrag, rechne=lambda *a, **k: rechne_gerufen.append(1))
        assert satz in str(fehler.value)
        assert rechne_gerufen == []


# ======================================================================================
# 96a · die Bemerkung ist die Anweisung
# ======================================================================================

def test_96a_die_liste_der_mappe_meldet_die_bemerkung(mappe):
    _skizze_auf(mappe, "skizze-leer.png", None, bemerkung="  ")
    liste = {s["name"]: s for s in knotenweg.skizzen_der_mappe(projekt.oeffne(mappe)["projekt"])}
    assert liste["skizze-a.png"]["bemerkung"] == "ein Vordach"
    assert liste["skizze-leer.png"]["bemerkung"] is None


def test_96a_ohne_anweisung_rechnet_die_bibliothek_mit_der_bemerkung(tmp_path, mappe):
    modell = _Modell()
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-a.png"))
    _abholen(ordner, modell)
    assert modell.auftraege[-1]["prompt"].startswith("ein Vordach")
    vermerk = _ergebnis(ordner)["qa"]["verdict"]
    assert "Anweisung aus der Bemerkung der Skizze" in json.dumps(vermerk, ensure_ascii=False)


def test_96a_ohne_bemerkung_weist_die_bibliothek_mit_satz_ab(mappe):
    _skizze_auf(mappe, "skizze-leer.png", None, bemerkung="")
    with pytest.raises(arbeitsgang.ArbeitsgangError, match="fehlt die Anweisung"):
        arbeitsgang.rechne_skizze(mappe, "skizze-leer.png", ausfuehrer=_tabelle(_Modell()))


# ======================================================================================
# 96b · vom Standpunkt des Bildes unter der Skizze
# ======================================================================================

def test_96b_jedes_gerechnete_bild_traegt_seinen_standpunkt(mappe):
    p = projekt.oeffne(mappe)["projekt"]
    (unterlage,) = [b for b in p["bilder"]]
    # Die Mappe bestellt keinen Standpunkt — gerechnet wurde von Sueden, und das steht da.
    assert unterlage["herkunft"]["standpunkt"] == {"kamera": arbeitsgang.STANDPUNKT_VORGABE}
    von_hand = _bild_von_hand(mappe, auge=AUGE, blick_auf=ZIEL)
    assert projekt.standpunkt_des_bildes(projekt.oeffne(mappe)["projekt"], von_hand) == {
        "auge": AUGE, "blick_auf": ZIEL}


def test_96b_die_skizze_nimmt_die_kamera_ihres_bildes_nicht_die_der_mappe(mappe):
    # Die Mappe steht inzwischen auf «von Norden» — die Skizze wurde aber auf ein Bild
    # gezeichnet, das von Hand (Auge/Ziel) gerechnet wurde.
    unterlage = _bild_von_hand(mappe, auge=AUGE, blick_auf=ZIEL)
    p = projekt.oeffne(mappe)["projekt"]
    p.setdefault("einstellungen", {})["kamera"] = "n"
    projekt.speichere(p, mappe)
    _skizze_auf(mappe, "skizze-b.png", unterlage)

    mitschrift: list = []
    aus = arbeitsgang.rechne_skizze(mappe, "skizze-b.png",
                                    ausfuehrer=_mit_mitschrift(_Modell(), mitschrift),
                                    cache=None)
    assert mitschrift[-1] == {"auge": AUGE, "blick_auf": ZIEL}     # kein «kamera: n»
    assert aus["standpunkt_skizze"]["von"] == projekt.STANDPUNKT_VOM_BILD
    assert aus["standpunkt_skizze"]["bild"] == unterlage
    assert aus["standpunkt_vorgabe"] is None
    bild = next(b for b in aus["projekt"]["bilder"] if b["bild"] == aus["bilder"][-1])
    assert bild["herkunft"]["standpunkt_skizze"]["zeile"] == projekt.STANDPUNKT_ZEILE_BILD
    # Und das neue Bild traegt denselben Standpunkt — eine Skizze darauf entsteht wieder von dort.
    assert bild["herkunft"]["standpunkt"] == {"auge": AUGE, "blick_auf": ZIEL}


def test_96b_ohne_unterlage_bleibt_der_standpunkt_der_mappe_und_es_wird_gesagt(mappe):
    p = projekt.oeffne(mappe)["projekt"]
    p.setdefault("einstellungen", {})["kamera"] = "n"
    projekt.speichere(p, mappe)
    _skizze_auf(mappe, "skizze-frei.png", None)
    mitschrift: list = []
    aus = arbeitsgang.rechne_skizze(mappe, "skizze-frei.png",
                                    ausfuehrer=_mit_mitschrift(_Modell(), mitschrift),
                                    cache=None)
    assert mitschrift[-1] == {"kamera": "n"}
    assert aus["standpunkt_skizze"]["von"] == projekt.STANDPUNKT_DER_MAPPE
    assert aus["standpunkt_skizze"]["zeile"] == (
        "Standpunkt der Mappe, weil die Skizze auf kein Bild gezeichnet wurde.")


def test_96b_unterlage_ohne_bekannten_standpunkt_standpunkt_der_mappe_mit_grund(mappe):
    """Ein Bild von vor dem 15.10.2026 (ohne ``herkunft.standpunkt``, mit bestelltem Standpunkt):
    geraten wird nicht."""
    p = projekt.oeffne(mappe)["projekt"]
    (eintrag,) = p["bilder"]
    del eintrag["herkunft"]["standpunkt"]
    eintrag["herkunft"]["standpunkt_vorgabe"] = None
    projekt.speichere(p, mappe)
    assert projekt.standpunkt_des_bildes(projekt.oeffne(mappe)["projekt"], eintrag["bild"]) is None

    mitschrift: list = []
    aus = arbeitsgang.rechne_skizze(mappe, "skizze-a.png",
                                    ausfuehrer=_mit_mitschrift(_Modell(), mitschrift),
                                    cache=None)
    assert mitschrift[-1] == {"kamera": arbeitsgang.STANDPUNKT_VORGABE}
    assert aus["standpunkt_skizze"]["von"] == projekt.STANDPUNKT_DER_MAPPE
    assert aus["standpunkt_skizze"]["zeile"] == projekt.STANDPUNKT_ZEILE_UNBEKANNT


def test_96b_ein_aelteres_bild_ohne_bestellten_standpunkt_ist_bekannt_von_sueden(mappe):
    p = projekt.oeffne(mappe)["projekt"]
    (eintrag,) = p["bilder"]
    del eintrag["herkunft"]["standpunkt"]
    assert eintrag["herkunft"]["standpunkt_vorgabe"]["kamera"] == "s"
    assert projekt.standpunkt_des_bildes(p, eintrag["bild"]) == {"kamera": "s"}


def test_96b_der_knotenweg_geht_denselben_weg_und_sagt_es_am_ergebnis(tmp_path, mappe):
    unterlage = _bild_von_hand(mappe, auge=AUGE, blick_auf=ZIEL)
    _skizze_auf(mappe, "skizze-b.png", unterlage)
    liste = {s["name"]: s for s in knotenweg.skizzen_der_mappe(projekt.oeffne(mappe)["projekt"])}
    assert liste["skizze-b.png"]["standpunkt"] == "bild"
    _skizze_auf(mappe, "skizze-frei.png", None)
    liste = {s["name"]: s for s in knotenweg.skizzen_der_mappe(projekt.oeffne(mappe)["projekt"])}
    assert liste["skizze-frei.png"]["standpunkt"] == "mappe"

    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-b.png"))
    _abholen(ordner, _Modell())
    text = json.dumps(_ergebnis(ordner), ensure_ascii=False)
    assert projekt.STANDPUNKT_ZEILE_BILD in text


def test_96b_die_seite_sagt_den_standpunkt_der_mappe_neben_dem_skizzenbild(mappe):
    sys.path.insert(0, str(Path(__file__).parent.parent / "oberflaeche"))
    import server  # noqa: E402

    herkunft = {"skizze": "s.png", "messung": {"hinweise": []},
                "standpunkt_skizze": {"von": "mappe", "zeile": projekt.STANDPUNKT_ZEILE_OHNE_BILD}}
    h = server._hinweise_zum_bild({"herkunft": herkunft})
    assert projekt.STANDPUNKT_ZEILE_OHNE_BILD in h["hinweise"]
    vom_bild = dict(herkunft, standpunkt_skizze={"von": "bild",
                                                 "zeile": projekt.STANDPUNKT_ZEILE_BILD})
    # Vom Bild darunter ist der gemeinte Fall — dazu steht nichts.
    assert server._hinweise_zum_bild({"herkunft": vom_bild})["hinweise"] == []
