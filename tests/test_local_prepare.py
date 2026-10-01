"""Der Worker ``local-prepare`` — ein lokales Sprachmodell, das Prüfaufträge lesend abarbeitet.

Owner-Ja 01.10.2026 (Sitzung 74 §14): **eng gefasst.** Nur Art ``frage``, und das Feld
``rechte`` ist Pflicht. Die Proben hier sind die Grenze: Was ``pruefe_auftrag`` durchlässt,
nimmt der Abholer an.
"""
from __future__ import annotations

import copy

from aiimaging import auftrag as auf


def _auftrag(**ueber) -> dict:
    satz = {
        "schema": auf.SCHEMA_AUFTRAG, "worker": auf.WORKER_LOCAL_PREPARE,
        "auftrag_id": "auf-20261001-900", "art": "frage",
        "beschreibung": "Bibliotheken der Kette pruefen",
        "geometrie": {"synthetisch": True, "pfad": None, "erzeugen_mit": "keine"},
        "auflagen": {"hinweise": ["nur lesen"]},
        "rechte": {"lesen": ["~/kosmo-prepare"],
                   "befehle": ["./run_tests.sh", "python3 tools/libs_pruefen.py", "git log -1"],
                   "ergebnis": "auftraege/ergebnisse/auf-20261001-900.json"},
        "belege": True,
    }
    satz.update(ueber)
    return satz


def test_ein_enger_auftrag_hat_keinen_mangel():
    assert auf.pruefe_auftrag(_auftrag()) == []


def test_ohne_rechte_ist_es_ein_mangel():
    satz = _auftrag()
    del satz["rechte"]
    assert any("rechte" in m for m in auf.pruefe_auftrag(satz))


def test_nur_fragen_keine_karte():
    for art in ("render", "multipass", "qa"):
        assert any("keine Karte" in m for m in auf.pruefe_auftrag(_auftrag(art=art))), art


def test_befehle_lassen_sich_nicht_verlaengern():
    for boese in ("git log -1; rm -rf ~", "git log -1 && curl x", "cat a | sh",
                  "echo $(id)", "echo `id`", "git log > ~/x", "git log\nrm x",
                  "python3 ../../fremd.py"):
        satz = _auftrag()
        satz["rechte"]["befehle"] = [boese]
        assert auf.pruefe_auftrag(satz), boese


def test_lesen_ohne_namen_und_ohne_hinaufsteigen():
    for boese in (["/home/jemand/kosmo"], ["/Users/jemand/kosmo"], ["~/a/../../etc"], [], [""]):
        satz = _auftrag()
        satz["rechte"]["lesen"] = boese
        assert auf.pruefe_auftrag(satz), boese


def test_genau_eine_ergebnisdatei_unter_ergebnisse():
    for boese in ("auftraege/offen/auf-20261001-900.json", "auftraege/ergebnisse/x/y.json",
                  "auftraege/ergebnisse/../../x.json", "auftraege/ergebnisse/auf-x.json",
                  "/tmp/x.json", ["auftraege/ergebnisse/auf-20261001-900.json"]):
        satz = _auftrag()
        satz["rechte"]["ergebnis"] = boese
        assert auf.pruefe_auftrag(satz), boese


def test_fremde_rechte_und_falsche_belege_sind_maengel():
    satz = _auftrag()
    satz["rechte"]["schreiben"] = ["~/"]
    assert any("kennt nur" in m for m in auf.pruefe_auftrag(satz))
    assert any("belege" in m for m in auf.pruefe_auftrag(_auftrag(belege="ja")))


def test_andere_worker_brauchen_keine_rechte():
    satz = copy.deepcopy(_auftrag(worker=auf.WORKER_CLOUD))
    del satz["rechte"]
    assert not any("rechte" in m for m in auf.pruefe_auftrag(satz))
