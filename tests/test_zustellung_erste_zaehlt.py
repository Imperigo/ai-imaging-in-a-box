"""Die erste Zustellung zählt — ein zweiter Vermerk datiert sie nicht um.

**Befund 22.09.2026, beim Verschicken selbst passiert.** ``tools/auftragspost.py ui
--vermerken`` setzte den Zeitpunkt ALLER offenen ui-Aufträge in
``auftraege/zustellung.json`` auf «jetzt» — auch den eines Auftrags, der seit dem
Vortag draussen war. Ein Auftrag, der jünger aussieht, als er ist, verdeckt Rückstand,
und zwar in der gefährlichen Richtung. Und die Ausgabe meldete «5 Kennung(en)
nachgezogen», obwohl nur eine neu war.

Beim Blickvermerk galt die Regel «der erste zählt» schon; für die Zustellung fehlte sie.

Alle Proben laufen an einem synthetischen Probeordner unter ``tmp_path`` (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from aiimaging import auftrag as auf
from aiimaging import auftragspost

ALT = "2026-09-21T13:55:15Z"


def _cli():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "auftragspost.py"
    spec = importlib.util.spec_from_file_location("werkzeug_auftragspost_erste", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _vermerk(wurzel: Path) -> dict:
    return json.loads((wurzel / auftragspost.ZUSTELLUNG_DATEI).read_text(encoding="utf-8"))


def _probeordner(tmp_path: Path) -> Path:
    """Zwei offene ui-Aufträge; der ältere ist schon zugestellt, der jüngere nicht."""
    wurzel = tmp_path / "repo"
    for kennung in ("auf-20260909-01", "auf-20260922-02"):
        auf.schreibe_auftrag(
            auf.baue_auftrag(auftrag_id=kennung, art="frage", beschreibung="x",
                             worker=auf.WORKER_UI), wurzel)
    ziel = wurzel / auftragspost.ZUSTELLUNG_DATEI
    ziel.write_text(json.dumps({"auf-20260909-01": ALT}) + "\n", encoding="utf-8")
    return wurzel


def test_ein_zweiter_vermerk_ueberschreibt_die_erste_zustellung_nicht(tmp_path):
    """Die Bibliothek selbst: Bestehendes bleibt, Neues entsteht, gezählt wird nur Neues."""
    wurzel = tmp_path
    assert auftragspost.vermerke_zustellung(wurzel, ["auf-a"], wann=ALT) == 1

    neu = auftragspost.vermerke_zustellung(wurzel, ["auf-a", "auf-b"],
                                           wann="2026-09-22T18:47:24Z")

    assert neu == 1, "nur «auf-b» war neu"
    assert _vermerk(wurzel) == {"auf-a": ALT, "auf-b": "2026-09-22T18:47:24Z"}, (
        "Der erste Zeitpunkt von «auf-a» ist umdatiert worden — der Auftrag sähe jünger "
        "aus, als er ist.")


def test_vermerken_im_werkzeug_behaelt_den_alten_zeitpunkt_und_zaehlt_getrennt(
        tmp_path, capsys):
    """Der Produktweg: genau der Aufruf, bei dem es am 22.09.2026 passiert ist."""
    wurzel = _probeordner(tmp_path)

    assert _cli().main(["ui", "--repo", str(wurzel), "--vermerken"]) == 0

    vermerk = _vermerk(wurzel)
    assert vermerk["auf-20260909-01"] == ALT, (
        "--vermerken hat eine bestehende Zustellung umdatiert (Befund 22.09.2026).")
    assert "auf-20260922-02" in vermerk, "der neue Auftrag ist nicht vermerkt worden"
    assert vermerk["auf-20260922-02"] != ALT

    ausgabe = capsys.readouterr().out
    assert "1 Kennung(en) NEU vermerkt, 1 schon vermerkt" in ausgabe, ausgabe


def test_ein_zweiter_lauf_meldet_null_neu_und_laesst_alles_stehen(tmp_path, capsys):
    """Die Wiederholung: nichts Neues, nichts umdatiert — und das wird gesagt."""
    wurzel = _probeordner(tmp_path)
    werkzeug = _cli()
    werkzeug.main(["ui", "--repo", str(wurzel), "--vermerken"])
    nach_erstem = _vermerk(wurzel)
    capsys.readouterr()

    assert werkzeug.main(["ui", "--repo", str(wurzel), "--vermerken"]) == 0

    assert _vermerk(wurzel) == nach_erstem
    ausgabe = capsys.readouterr().out
    assert "0 Kennung(en) NEU vermerkt, 2 schon vermerkt" in ausgabe, ausgabe
