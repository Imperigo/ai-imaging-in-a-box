"""Zwei Befunde aus ``auf-20261020-291`` (HomeStation, 20.10.2026): Sätze, die verloren gingen.

1. Der Abholer entlud das eigene Sprachmodell, um rechnen zu dürfen — und warf den Satz
   «… entladen: qwen3:14b …» weg (``_karte_frei``: ``return True, ""``). Das Protokoll zeigte
   nur das «NICHT frei» von vor dem Entladen.
2. «Anwenden» verwarf das Ergebnis des Entladens; am Mac kam «Nicht entladen: …» nie an.
"""
from __future__ import annotations

from aiimaging import abholer, assistent

from test_kettenlauf_26august import _auftragsordner, _kette


def test_der_satz_des_entladens_geht_bis_in_die_antwort(tmp_path):
    ordner = _auftragsordner(tmp_path)
    laufzettel = ordner / "job.json"
    import json
    satz = json.loads(laufzettel.read_text(encoding="utf-8"))
    satz["idle_window_only"] = True
    laufzettel.write_text(json.dumps(satz), encoding="utf-8")
    zustand = {"belegt": True}

    def darf():
        return (not zustand["belegt"], "Auslastung 3 %" if not zustand["belegt"]
                else "Auslastung 12 %, 9 GB belegt")

    def entlade():
        zustand["belegt"] = False
        return {"entladen": True, "satz": "Sprachmodell entladen: qwen3:14b."}

    auskunft = abholer.karte_oder_eigenes_entladen(darf, entlade, _warte=lambda s: None)
    _, attrappen = _kette(tmp_path)
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False, **attrappen)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                                 darf_rechnen=auskunft)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert "entladen: qwen3:14b" in antwort["karte"]
    assert "Danach: Auslastung 3 %" in antwort["karte"]


def test_ohne_auflage_sagt_die_karte_nichts(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _, attrappen = _kette(tmp_path)
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False, **attrappen)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)
    assert antwort["karte"] is None


def test_abholen_druckt_die_karte_je_auftrag(capsys):
    import importlib.util
    from pathlib import Path
    werkzeug = Path(__file__).resolve().parents[1] / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_auf291", werkzeug)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    modul._berichte({"ergebnisse": [{"job_id": "vis-1-abcdef", "tat": "verarbeitet",
                                     "grund": "3 Bild(er)", "wache": None,
                                     "karte": "Sprachmodell entladen: qwen3:14b."}]})
    assert "Karte: Sprachmodell entladen: qwen3:14b." in capsys.readouterr().out


def test_anwenden_reicht_den_satz_des_entladens_weiter():
    from test_assistent import BLATT14, Ersatz, _blatt14_botschaften
    v = assistent.frage(BLATT14, sprachmodell=Ersatz(_blatt14_botschaften()))["vorschlag"]
    nutzlast, code = assistent.anwenden(
        v, starte=lambda e, n: ({"laeuft": True}, 202),
        entlade=lambda: {"entladen": False, "satz": "Nicht entladen: qwen3:30b gehoert KosmoOrbit."})
    assert code == 202
    assert nutzlast["entladen"] == {"entladen": False,
                                    "satz": "Nicht entladen: qwen3:30b gehoert KosmoOrbit."}
    # Ohne Satz bleibt das Ergebnis, wie es war.
    assert assistent.anwenden(v, starte=lambda e, n: {"x": 1}, entlade=lambda: None) == {"x": 1}
