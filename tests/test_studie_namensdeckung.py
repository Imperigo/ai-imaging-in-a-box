"""Sehen Boxseite und Bildseite dieselben Namen? — die Studie, die den Bau geändert hat.

Warum es diese Proben gibt
--------------------------
Die Studie beantwortet **nicht** eine Nebenfrage: Von ihrem Ergebnis hing ab, ob die
Brücke von der Boxseite zur Bildseite überhaupt gebaut wird — und in welcher Form.

Sie hat den Bau zweimal geändert:

1. **Der erste Anlauf mass in die falsche Richtung.** Gezählt wurde, wie viele der von der
   Form erkannten *Namen* in der Tabelle vorkommen. Beim geteilten Gelände ergab das
   100 % — und war falsch: Die Maske arbeitet über *Tabelleneinträge*, und dort standen
   vier, von denen die Namensliste nur einen traf.
2. **Blenders Dublettensuffix** kam erst dadurch ans Licht. Es zwang die Suffixregel in
   `maske.deckt_uebertragenen_namen`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _studie():
    spec = importlib.util.spec_from_file_location(
        "studie_namensdeckung", WURZEL / "tools" / "studie_namensdeckung.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_materialnamen_und_knotennamen_treffen_sich_nie(tmp_path):
    """**Der Befund, der die Grenze zieht.** Die Boxseite kann das Gelände finden und die
    Bildseite nicht — nicht weil etwas fehlt, sondern weil die beiden über verschiedene
    Namen reden."""
    s = _studie()
    aus = s.messen(tmp_path / "a.glb")
    fall = aus["faelle"]["material"]
    assert fall["deckung"] == 0.0
    assert fall["n_gelaende_eintraege"] == 1, (
        "Das Gelaende verschwindet nicht, weil die Tabelle Materialnamen traegt — seine "
        "Bildpunkte stehen unter dem Material, mit dem es gerendert wurde. Ohne diesen "
        "Eintrag laese sich 0/0 wie «hier gibt es nichts zu finden».")


def test_objektnamen_decken_sich_vollstaendig(tmp_path):
    """Der Normalfall unserer eigenen Kette: `ifc_to_glb_runner` überträgt keine
    Materialien, also vergibt Blender objektweise IDs — und dann passen die Namen."""
    s = _studie()
    assert s.messen(tmp_path / "b.glb")["faelle"]["objekt"]["deckung"] == 1.0


def test_ein_geteiltes_gelaende_bricht_die_deckung_auf_ein_viertel(tmp_path):
    """**Der Fall, der am echten Bestand vorliegt** — dort sind es zwanzig Knoten
    desselben Namens, hier vier.

    Blender vergibt Objektnamen eindeutig und hängt `.001` an. Ein Vergleich auf
    Gleichheit trifft nur den ersten Eintrag.
    """
    s = _studie()
    aus = s.messen(tmp_path / "c.glb", s.KOERPER_GETEILTES_GELAENDE)
    fall = aus["faelle"]["objekt_mit_dubletten"]
    assert fall["deckung"] == 0.25
    assert len(fall["verfehlt"]) == 3
    assert all(n.endswith((".001", ".002", ".003")) for n in fall["verfehlt"])


def test_die_suffixregel_der_maske_schliesst_genau_diese_luecke(tmp_path):
    """Die Verbindung zwischen Messung und Bau: Was die Studie als Lücke misst, schliesst
    `maske.deckt_uebertragenen_namen` — und nur das."""
    from aiimaging import maske as m

    s = _studie()
    aus = s.messen(tmp_path / "d.glb", s.KOERPER_GETEILTES_GELAENDE)
    verfehlt = aus["faelle"]["objekt_mit_dubletten"]["verfehlt"]
    zusatz = aus["form_gelaende"]
    assert verfehlt, "sonst misst diese Probe nichts"
    assert all(m.deckt_uebertragenen_namen(n, zusatz) for n in verfehlt)


def test_die_studie_laeuft_ueber_die_befehlszeile(tmp_path, capsys):
    """*Ein ungedrückter Schalter ist eine unbeantwortete Frage* — auch `--ziel`."""
    s = _studie()
    assert s.main(["--ziel", str(tmp_path / "e.glb")]) == 0
    ausgabe = capsys.readouterr().out
    assert "BEFUND" in ausgabe
    assert "traegt NICHT" in ausgabe
    assert (tmp_path / "e.glb").is_file()


def test_die_studie_gibt_auch_json(tmp_path, capsys):
    import json as _json
    s = _studie()
    assert s.main(["--json", "--ziel", str(tmp_path / "f.glb")]) == 0
    satz = _json.loads(capsys.readouterr().out)
    assert set(satz) == {"ein Gelaendekoerper", "geteiltes Gelaende (4 Knoten)"}
