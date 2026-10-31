"""A0051 · Masstreue (Owner-Entscheid 30.10.2026): **kein KI-Bild ohne Blender-Grundlage.**

Wortlaut des Owners: «weg ist immer gleich, jedes bild muss basierend auf blender render und
multipasses laufen, kein ai imaging entsteht ohne sonst verlieren wir die masstreue». Damit ist der
Visbox-Entscheid 149 («Freies Bild», ``vis.freies_bild: true``, 24.10.2026) aufgehoben.

Geprüft wird hier die Sperre, an allen Türen, durch die ein KI-Bild-Auftrag in die Visbox kommt:

* an der Brücke (Knotenansicht am Mac, Claude am Mac und am iPad gehen alle über ``knotenweg.lege_an``):
  ``vis.freies_bild: true`` wird mit 400 abgewiesen, kein Auftragsordner;
* im Abholer (ein Auftrag, der von Hand in die Ablage gelegt wurde): abgewiesen, **kein Blender-Lauf,
  kein Bildmodell gerufen**;
* in der Bildstufe selbst: ohne Tiefenkarte aus dem Multipass wird kein Modell geladen;
* ohne Modell und ohne Grundlage gibt es keinen Lauf.

Alte Ergebnisse mit ``freies_bild: true`` bleiben lesbar (Satz und Kennzeichen im Ergebnis).

Ohne GPU, ohne Blender, alles synthetisch (Regel 3).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene, render

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_voll_ohne_klick import SZENE as _SZENE

WURZEL = Path(__file__).resolve().parents[1]


def _mit_vis(ordner: Path, **vis) -> None:
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")


# ================================================================ der Satz

def test_der_satz_nennt_den_entscheid_und_die_aufhebung():
    assert kosmo_szene.SATZ_MASSTREUE.startswith("MASSTREUE")
    satz = kosmo_szene.masstreue_satz_freies_bild()
    assert satz.startswith(kosmo_szene.SATZ_MASSTREUE)
    assert "30.10.2026" in satz and "149" in satz and "aufgehoben" in satz
    assert "Blender" in satz


# ================================================================ in der Bestellung

def test_freies_bild_ist_ein_endgueltiger_mangel():
    szene = dict(_SZENE, vis={**_SZENE["vis"], "freies_bild": True},
                 geometry={"path": "modell.glb", "format": "glb"})
    s = kosmo_szene.lies_szene(szene, streng=False)
    assert s["freies_bild"] is False
    assert any(m.startswith(kosmo_szene.SATZ_MASSTREUE) for m in s["maengel_endgueltig"])
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == [
        kosmo_szene.masstreue_satz_freies_bild()]


@pytest.mark.parametrize("wert", [False, None])
def test_freies_bild_false_oder_null_bleibt_ohne_wirkung(wert):
    """Eine ältere Bestellung, die das Feld mit ``false`` mitschickt, läuft weiter."""
    szene = dict(_SZENE, vis={**_SZENE["vis"], "freies_bild": wert})
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == []


# ================================================================ an der Brücke (Mac und iPad)

def test_freies_bild_wird_an_der_bruecke_abgewiesen(tmp_path):
    szene = dict(_SZENE, vis={**_SZENE["vis"], "freies_bild": True})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, szene, b"glTF-bytes", "model.glb",
                          kennung="vis-1790000000-00a051")
    assert fehler.value.code == 400
    assert kosmo_szene.SATZ_MASSTREUE in str(fehler.value)
    assert not (tmp_path / "vis-1790000000-00a051").exists()


def test_ohne_modell_und_ohne_grundlage_nimmt_die_bruecke_nichts_an(tmp_path):
    with pytest.raises(knotenweg.KnotenwegError):
        knotenweg.lege_an(tmp_path, dict(_SZENE), None, "model.glb",
                          kennung="vis-1790000000-00a052")
    assert not (tmp_path / "vis-1790000000-00a052").exists()


# ================================================================ im Abholer: nichts gerechnet

def test_freies_bild_im_abholer_kein_blender_kein_bildmodell(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    _mit_vis(ordner, freies_bild=True)
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert kosmo_szene.SATZ_MASSTREUE in str(antwort.get("grund"))
    assert protokoll["render"] == [], "kein Bildmodell gerufen"
    assert protokoll["multipass"] == [], "abgewiesen vor dem Blender-Lauf"


def test_ohne_modell_und_ohne_grundlage_rechnet_der_abholer_nichts(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene.pop("geometry")
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert protokoll["render"] == [] and protokoll["multipass"] == []


# ================================================================ in der Bildstufe

class _Lader:
    def __init__(self):
        self.gerufen = []

    def __call__(self, *args, **kwargs):
        self.gerufen.append(args)
        raise AssertionError("ohne Grundlage darf kein Modell geladen werden")


@pytest.mark.parametrize("tiefe", ["", "gibt/es/nicht.png"])
def test_ohne_tiefe_aus_dem_multipass_wird_kein_modell_geladen(tiefe):
    lader = _Lader()
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, prompt="Haus im Abendlicht"),
                         _lader=lader)
    assert erg["status"] == render.STATUS_ABGELEHNT
    assert lader.gerufen == []


# ================================================================ alte Ergebnisse bleiben lesbar

def test_ein_altes_freies_bild_bleibt_lesbar():
    angewandt = {"freies_bild": {"satz": kosmo_szene.freies_bild_satz(), "herkunft": "freies_bild"}}
    saetze = kosmo_szene.ergebnis_saetze_der_szene(angewandt)
    assert saetze and saetze[-1].startswith(kosmo_szene.SATZ_FREIES_BILD)
    ergebnis = kosmo_szene.als_ergebnis("vis-1792000000-abcdef", [], angewandt=angewandt)
    assert ergebnis["freies_bild"] is True


# ================================================================ die Spielregel am iPad

def test_die_spielregel_am_ipad_bietet_kein_freies_bild_mehr_an():
    kern = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Mcpkern.swift").read_text(encoding="utf-8")
    assert "freies_bild: true" not in kern
    assert "Masstreue" in kern and "Blender-Grundlage" in kern


# ================================================================ Runde 2 (Gegenlesen G-A0051)
# Mangel 1: «Bildeingang aus» war das aufgehobene freie Bild unter anderem Namen — ohne Grundbild als
# Start, nur aus Text und Tiefe (Messreihe T in 353; lies_szene nannte es selbst «frei»). Seit der
# Masstreue wird auch das abgewiesen, an Brücke und Abholer, bevor Blender oder ein Bildmodell rechnet.

@pytest.mark.parametrize("umriss", [None, False])
def test_bildeingang_aus_ist_ein_endgueltiger_mangel(umriss):
    vis = {**_SZENE["vis"], "bildeingang": False}
    if umriss is not None:
        vis["umriss_halten"] = umriss
    szene = dict(_SZENE, vis=vis, geometry={"path": "modell.glb", "format": "glb"})
    s = kosmo_szene.lies_szene(szene, streng=False)
    assert s["freies_bild"] is False
    assert kosmo_szene.masstreue_satz_bildeingang_aus() in s["maengel_endgueltig"]
    assert not any(w.startswith(kosmo_szene.SATZ_FREIES_BILD) for w in s["warnungen"]), \
        "kein Bild trägt mehr die Marke des aufgehobenen Entscheids 149"
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == [
        kosmo_szene.masstreue_satz_bildeingang_aus()]


def test_bildeingang_aus_wird_an_der_bruecke_abgewiesen(tmp_path):
    szene = dict(_SZENE, vis={**_SZENE["vis"], "bildeingang": False, "umriss_halten": False})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, szene, b"glTF-bytes", "model.glb",
                          kennung="vis-1790000000-00a053")
    assert fehler.value.code == 400
    assert kosmo_szene.masstreue_satz_bildeingang_aus() in str(fehler.value)
    assert not (tmp_path / "vis-1790000000-00a053").exists()


def test_bildeingang_aus_im_abholer_kein_blender_kein_bildmodell(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    _mit_vis(ordner, bildeingang=False)
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert kosmo_szene.SATZ_MASSTREUE in str(antwort.get("grund"))
    assert protokoll["render"] == [], "kein Bildmodell gerufen"
    assert protokoll["multipass"] == [], "abgewiesen vor dem Blender-Lauf"


def test_bildeingang_mit_staerke_bleibt_erlaubt():
    """Gegenprobe: der Bildeingang selbst (Start vom Grundbild) ist der Weg der Masstreue."""
    szene = dict(_SZENE, vis={**_SZENE["vis"], "bildeingang": 0.5})
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == []


def test_bildeingang_aus_bei_nur_grundlage_ist_kein_masstreue_mangel():
    """«Nur Grundlage» rechnet kein KI-Bild — dort gibt es nichts zu sperren."""
    szene = dict(_SZENE, vis={**_SZENE["vis"], "bildeingang": False, "skip": True})
    assert kosmo_szene.widersprueche_beim_annehmen(szene) == []


# Mangel 3: die Tür «ohne Modell und ohne Grundlage» mit Code und Satz bewacht, nicht mit irgendeinem
# Fehler — und im Abholer mit dem Grund.

def test_ohne_modell_und_ohne_grundlage_400_mit_satz(tmp_path):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, dict(_SZENE), None, "model.glb",
                          kennung="vis-1790000000-00a054")
    assert fehler.value.code == 400
    assert str(fehler.value) == knotenweg.SATZ_OHNE_MODELL_UND_GRUNDLAGE
    assert not (tmp_path / "vis-1790000000-00a054").exists()


def test_ohne_modell_und_ohne_grundlage_nennt_der_abholer_den_grund(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene.pop("geometry")
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "geometry" in str(antwort.get("grund"))
    assert protokoll["render"] == [] and protokoll["multipass"] == []
