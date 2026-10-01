"""Die echte Vorführmappe der Mac-App — gerechnet am Heim-PC (`auf-20261001-218`).

Sie liegt neben den Platzhaltern (`ipad/VisboxMac/Beispielmappe/`, auf die die Proben des
Werkzeugs bauen), nicht an ihrer Stelle; die Prüfstrecke legt **diese** ins Bündel, wenn es sie
gibt. Weil sie nicht hier erzeugt wurde, sondern am Heim-PC, wacht diese Datei über das, was
das Werkzeug dort schon geprüft hat: dieselbe Form, keine Begleitdaten, nichts nach Regel 3.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
ECHT = WURZEL / "ipad" / "VisboxMac" / "Vorfuehrmappe"
ABLAUF = WURZEL / ".github" / "workflows" / "ipad.yml"


def _werkzeug():
    pfad = WURZEL / "tools" / "vorfuehrmappe.py"
    spec = importlib.util.spec_from_file_location("vorfuehrmappe", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _mappe() -> dict:
    return json.loads((ECHT / "vorfuehrmappe.json").read_text(encoding="utf-8"))


def test_die_echte_mappe_hat_die_form_und_jedes_bild_liegt_da():
    m = _mappe()
    assert m["schema"] == "visbox.vorfuehrmappe/v1"
    assert m["platzhalter"] is False
    assert m["bilder"], "leere Mappe"
    for b in m["bilder"]:
        assert "/" not in b["datei"] and "\\" not in b["datei"], b["datei"]
        assert (ECHT / b["datei"]).is_file(), b["datei"]
        assert b["gerechnet_am"] and b["satz"]


def test_die_echte_mappe_traegt_nichts_nach_regel_drei():
    werkzeug = _werkzeug()
    assert werkzeug.regel3_funde(_mappe()) == []


def test_die_bilder_tragen_keine_begleitdaten():
    werkzeug = _werkzeug()
    for png in sorted(ECHT.glob("*.png")):
        roh = png.read_bytes()
        assert werkzeug.ohne_begleitdaten(roh) == roh, f"{png.name} trägt Begleitdaten"


def test_die_pruefstrecke_legt_die_echte_mappe_ins_buendel():
    ablauf = ABLAUF.read_text(encoding="utf-8")
    assert "Vorfuehrmappe" in ablauf and "Beispielmappe" in ablauf
