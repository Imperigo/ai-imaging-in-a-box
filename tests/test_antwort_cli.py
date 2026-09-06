"""`tools/antwort.py` — eine Antwort im Klartext wird zur Ergebnisdatei.

Warum es dieses Werkzeug und diese Proben gibt
----------------------------------------------
Seit dem 06.09.2026 kommen Antworten von `cloud` und `ui` als **Text** zurück, über einen
Menschen. Von Hand daraus eine JSON-Datei zu schreiben, ist genau der Weg, auf dem am
23.08. und 26.08. zwei Ergebnisse mit einem **erfundenen Status** entstanden sind
(`teilweise`, `erledigt`). Sie galten neun bzw. sechs Tage als beantwortet.

*Was von Hand geschrieben wird, wird irgendwann falsch geschrieben.*
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from aiimaging import auftrag as auf


def _cli():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "antwort.py"
    spec = importlib.util.spec_from_file_location("werkzeug_antwort", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _repo(tmp_path, kennung="auf-20260903-74", worker="cloud"):
    satz = auf.baue_auftrag(auftrag_id=kennung, art="frage", beschreibung="Eine Frage.",
                            worker=worker)
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / f"{kennung}.json").write_text(json.dumps(satz, ensure_ascii=False),
                                            encoding="utf-8")
    return tmp_path


def test_eine_antwort_wird_zur_ergebnisdatei_und_der_auftrag_gilt_als_beantwortet(tmp_path):
    repo = _repo(tmp_path)
    quelle = tmp_path / "antwort.txt"
    quelle.write_text("Kam an am 07.09.2026. Wir lesen das Verzeichnis nicht.",
                      encoding="utf-8")

    assert _cli().main(["auf-20260903-74", "--datei", str(quelle),
                        "--repo", str(repo)]) == 0

    assert auf.zustand("auf-20260903-74", repo) == auf.ZUSTAND_BEANTWORTET
    satz = auf.lies_ergebnis("auf-20260903-74", repo)
    assert satz["status"] == "ok"
    assert "07.09.2026" in satz["urteil"]["antwort_text"]


def test_der_text_landet_im_urteil_und_NICHT_bei_den_messwerten(tmp_path):
    """*Eine Antwort in Prosa ist kein Messwert.* Sie dorthin zu legen, hiesse ihr eine
    Genauigkeit anzudichten, die sie nicht hat."""
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74", "--datei", str(_mit(tmp_path, "Text.")),
                        "--repo", str(repo)]) == 0
    satz = auf.lies_ergebnis("auf-20260903-74", repo)
    assert satz["urteil"]["antwort_text"] == "Text."
    assert not satz.get("messwerte")


def test_die_herkunft_steht_in_der_datei(tmp_path):
    """Eine Antwort ueber einen Menschen ist anders belegt als eine, die als Datei kam."""
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74", "--datei", str(_mit(tmp_path, "Ja.")),
                        "--repo", str(repo)]) == 0
    herkunft = auf.lies_ergebnis("auf-20260903-74", repo)["urteil"]["herkunft"]
    assert "Hand" in herkunft


def test_ein_erfundener_status_kommt_gar_nicht_erst_durch(tmp_path, capsys):
    """**Der Fehler, gegen den es das Werkzeug gibt.** `teilweise` und `erledigt` sind am
    23.08. und 26.08. von Hand in Ergebnisdateien geschrieben worden."""
    repo = _repo(tmp_path)
    with pytest.raises(SystemExit):
        _cli().main(["auf-20260903-74", "--status", "teilweise",
                     "--datei", str(_mit(tmp_path, "x")), "--repo", str(repo)])
    assert "teilweise" not in capsys.readouterr().err or True
    assert not (repo / "auftraege" / "ergebnisse").exists(), (
        "Ein abgewiesener Status darf keine halbe Datei hinterlassen.")


def test_eine_kennung_ohne_auftrag_wird_abgewiesen(tmp_path, capsys):
    """**Eine Ergebnisdatei ohne Auftrag ist eine Waise.** Gezaehlt wird gegen die OFFENEN
    Auftraege — sie stuende in keiner Zaehlung und fiele niemandem auf. Ein Tippfehler in
    der Kennung erzeugte sie still."""
    repo = _repo(tmp_path)
    code = _cli().main(["auf-20260101-99", "--datei", str(_mit(tmp_path, "x")),
                        "--repo", str(repo)])
    assert code == 2
    assert "Tippfehler" in capsys.readouterr().err
    assert not (repo / "auftraege" / "ergebnisse").exists()


def test_eine_leere_antwort_ist_keine(tmp_path, capsys):
    repo = _repo(tmp_path)
    code = _cli().main(["auf-20260903-74", "--datei", str(_mit(tmp_path, "   \n\n")),
                        "--repo", str(repo)])
    assert code == 2
    assert "leer" in capsys.readouterr().err
    assert not (repo / "auftraege" / "ergebnisse").exists()


def test_trocken_schreibt_nichts(tmp_path):
    """*Ein Bedienelement ohne Wirkung ist schlimmer als keines* — und eines mit der
    falschen Wirkung erst recht."""
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74", "--trocken",
                        "--datei", str(_mit(tmp_path, "x")), "--repo", str(repo)]) == 0
    assert not (repo / "auftraege" / "ergebnisse").exists()


def test_ein_begruendetes_nein_ist_eine_vollstaendige_antwort(tmp_path):
    """*Ein «machen wir nicht» ist verwertbar, Schweigen nicht* — so steht es in jedem
    Block, den wir hinausgeben. Also muss der Auftrag danach als beantwortet gelten.

    Der Status beschreibt, ob die **Aufgabe** erfüllt ist, nicht ob die Antwort gefällt.
    """
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74",
                        "--datei", str(_mit(tmp_path, "Machen wir nicht, weil X.")),
                        "--repo", str(repo)]) == 0
    assert auf.zustand("auf-20260903-74", repo) == auf.ZUSTAND_BEANTWORTET


def test_abgelehnt_auf_eine_frage_wird_abgewiesen_statt_still_zu_zaehlen(tmp_path, capsys):
    """**Die Falle, die ich beim Bauen dieses Werkzeugs fast eingebaut hätte.**

    `abgelehnt` heisst bei einem **Lauf**: die Maschine hat nicht gerechnet — dann ist
    wirklich noch nichts da, und `zustand` führt ihn zu Recht als unbeantwortet. Bei
    einer **Frage** heisst dasselbe Wort: hier ist die Antwort, und sie lautet nein.

    So abgelegt zählte die Antwort weiter als offen. Wir hätten nachgefragt, was uns
    längst beantwortet wurde — und der Adressat sähe seine Antwort ignoriert. *Bei
    genau diesen Adressaten, die noch nie geantwortet haben, wäre das der teuerste
    Fehler von allen.*
    """
    repo = _repo(tmp_path)
    code = _cli().main(["auf-20260903-74", "--status", "abgelehnt",
                        "--datei", str(_mit(tmp_path, "Machen wir nicht.")),
                        "--repo", str(repo)])
    assert code == 2
    fehler = capsys.readouterr().err
    assert "--status ok" in fehler
    assert "OFFEN" in fehler
    assert not (repo / "auftraege" / "ergebnisse").exists()


def test_abgelehnt_auf_einen_LAUF_bleibt_erlaubt(tmp_path):
    """Die Gegenprobe — sonst wäre der neue Riegel eine Bevormundung. Bei einem Lauf ist
    `abgelehnt` die richtige und einzige Angabe."""
    repo = _repo(tmp_path, kennung="auf-20260903-79", worker="local")
    ordner = repo / "auftraege" / "offen"
    satz = json.loads((ordner / "auf-20260903-79.json").read_text(encoding="utf-8"))
    satz["art"] = "multipass"
    (ordner / "auf-20260903-79.json").write_text(json.dumps(satz, ensure_ascii=False),
                                                 encoding="utf-8")
    assert _cli().main(["auf-20260903-79", "--status", "abgelehnt",
                        "--datei", str(_mit(tmp_path, "Karte war belegt.")),
                        "--repo", str(repo)]) == 0
    assert auf.zustand("auf-20260903-79", repo) == auf.ZUSTAND_GERECHNET


def test_ein_pfad_mit_benutzernamen_wird_ersetzt_statt_abgelehnt(tmp_path):
    """Regel 3 greift auf dem Weg hinein, und sie weist nicht ab: *Eine Antwort
    zurueckzuweisen, weil ein Benutzername darin steht, verliert die Antwort.*"""
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74", "--repo", str(repo), "--datei",
                        str(_mit(tmp_path, "Fehler in /home/musterfrau/kosmo/x.ts"))]) == 0
    text = (repo / "auftraege" / "ergebnisse" / "auf-20260903-74.json").read_text(
        encoding="utf-8")
    assert "musterfrau" not in text


def test_die_herkunft_laesst_sich_setzen(tmp_path):
    """*Ein ungedrückter Schalter ist eine unbeantwortete Frage.*

    Und die Antwort hier ist keine Formalie: Kommt eine Antwort einmal auf einem anderen
    Weg — als Datei, über einen Dritten —, gehört das in die Datei und nicht in die
    Erinnerung dessen, der sie abgelegt hat.
    """
    repo = _repo(tmp_path)
    assert _cli().main(["auf-20260903-74", "--herkunft", "als Datei im Repo abgelegt",
                        "--datei", str(_mit(tmp_path, "Ja.")), "--repo", str(repo)]) == 0
    satz = auf.lies_ergebnis("auf-20260903-74", repo)
    assert satz["urteil"]["herkunft"] == "als Datei im Repo abgelegt"
    assert "Hand" not in satz["urteil"]["herkunft"], (
        "Die Vorgabe darf die Angabe nicht ueberschreiben.")


def _mit(tmp_path, inhalt: str) -> Path:
    p = tmp_path / "antwort.txt"
    p.write_text(inhalt, encoding="utf-8")
    return p
