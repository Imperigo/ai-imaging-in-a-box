"""Der Rueckstau ueber ZWEI Ablagen — und die Nummernfalle, die ihn verfaelscht hat.

**Der Anlass, und er ist ein eigener Fehler vom 19.09.2026.** Ein Auftrag galt hier als
unbeantwortet, weil in diesem Baum keine Antwort lag. Sie lag im anderen Repo. Daraus
wurde ein Vorwurf, und der Vorwurf war falsch.

**Owner-Entscheid 19.09.2026:** Es bleiben zwei Ablagen — ein Umzug braeche, was laeuft.
Stattdessen zaehlt ein Werkzeug sie zusammen.

**Die zweite Lehre desselben Tages steht in `test_eine_nummer_ist_keine_kennung`:** Eine
erste Zuordnung ueber die blosse laufende Nummer meldete 15 Treffer statt 7. Acht davon
waren Dateien einer ganz anderen Nummernreihe.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import rueckstau as R  # noqa: E402


def _auftrag(wurzel: Path, kennung: str, worker: str = "local") -> None:
    verz = wurzel / "auftraege" / "offen"
    verz.mkdir(parents=True, exist_ok=True)
    (verz / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-auftrag/v1",
        "auftrag_id": kennung, "art": "frage", "worker": worker,
        "erstellt": "2026-09-01T00:00:00Z", "beschreibung": "Pruefauftrag",
        "geometrie": {"synthetisch": True}, "auflagen": {},
        "rueckgabe": ["R1"],
    }), encoding="utf-8")


def _fremde_antwort(fremd: Path, dateiname: str, inhalt: dict | str) -> None:
    verz = fremd / "auftraege" / "ergebnisse"
    verz.mkdir(parents=True, exist_ok=True)
    p = verz / dateiname
    p.write_text(json.dumps(inhalt) if isinstance(inhalt, dict) else inhalt, encoding="utf-8")


def test_eine_antwort_im_anderen_baum_zaehlt(tmp_path):
    """Der Kern. Ohne ihn ist jede Zahl dieses Repos eine halbe Auskunft."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260901-11")
    _fremde_antwort(fremd, "auf-20260901-11.json", {"auftrag": "auf-20260901-11", "antworten": {}})

    b = R.rueckstau(hier, fremd)

    assert b["anderswo_beantwortet"] == ["auf-20260901-11"]
    assert b["wirklich_offen"] == []


def test_ohne_treffer_bleibt_der_auftrag_offen(tmp_path):
    """Die Gegenprobe. Ohne sie waere der Test darueber auch gruen, wenn ALLES als
    anderswo beantwortet gaelte — und dann waere nie ein Auftrag offen."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260901-11")
    _fremde_antwort(fremd, "auf-20260901-99.json", {"auftrag": "auf-20260901-99"})

    b = R.rueckstau(hier, fremd)

    assert b["anderswo_beantwortet"] == []
    assert b["wirklich_offen"] == ["auf-20260901-11"]


def test_eine_nummer_ist_keine_kennung(tmp_path):
    """**Der Fehler vom 19.09.2026, als Pruefung.** `erg-20260906-51-…` beantwortet B48,
    nicht `auf-20260826-51` — die 51 ist dieselbe Ziffer aus einer anderen Reihe.
    Wer ueber die Nummer zuordnet, meldet Antworten, die es nicht gibt."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260826-51")
    _fremde_antwort(fremd, "erg-20260906-51-anderes-thema.md", "# Antwort auf B48\nNichts hiermit zu tun.")

    b = R.rueckstau(hier, fremd)

    assert b["anderswo_beantwortet"] == []
    assert b["wirklich_offen"] == ["auf-20260826-51"]


def test_die_kennung_im_text_zaehlt_auch(tmp_path):
    """Eine Antwort traegt die Kennung nicht immer im Dateinamen. Nennt sie sie im Text,
    ist sie trotzdem eine Antwort — genau so lagen die Antworten, die ich uebersah."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260826-51")
    _fremde_antwort(fremd, "erg-20260906-77-sammelblatt.md",
                    "# Sammelantwort\nBeantwortet auf-20260826-51 mit Beleg.")

    b = R.rueckstau(hier, fremd)

    assert b["anderswo_beantwortet"] == ["auf-20260826-51"]


def test_ein_fehlender_fremdbaum_wird_benannt_statt_verschwiegen(tmp_path):
    """**Die wichtigste Eigenschaft.** Der Cloud-Worker hat den anderen Baum nicht. Ein
    Werkzeug, das dann stillschweigend «alles offen» meldet, erzeugt genau den Vorwurf,
    gegen den es gebaut wurde. *Was es nicht sehen kann, nennt es beim Namen.*"""
    hier = tmp_path / "hier"
    _auftrag(hier, "auf-20260901-11")

    b = R.rueckstau(hier, tmp_path / "gibt-es-nicht")

    assert b["fremdbaum_gesehen"] is False
    assert "auf-20260901-11" in b["wirklich_offen"]
    assert "nicht gesehen" in b["vorbehalt"].lower()


def test_mit_fremdbaum_gibt_es_keinen_vorbehalt(tmp_path):
    """Gegenprobe: sonst stuende der Vorbehalt unter jedem Lauf und waere Tapete."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260901-11")
    (fremd / "auftraege" / "ergebnisse").mkdir(parents=True)

    b = R.rueckstau(hier, fremd)

    assert b["fremdbaum_gesehen"] is True
    assert b["vorbehalt"] == ""


def test_erwaehnt_in_einem_AUFTRAG_ist_keine_antwort(tmp_path):
    """**Fehlbefund vom 19.09.2026, gefunden beim Lauf am echten Bestand.** Die erste
    Fassung las auch die Auftragsordner des Fremdbaums und meldete `auf-20260827-61` als
    beantwortet — die Kennung stand dort in `auf-20260827-62.md`, einem Auftrag, der auf
    sie verweist. *Erwaehnt zu werden ist keine Antwort.*"""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260827-61")
    auftragsordner = fremd / "auftraege" / "von-kosmovis"
    auftragsordner.mkdir(parents=True)
    (auftragsordner / "auf-20260827-62.md").write_text(
        "AUFTRAG auf-20260827-62\nBezieht sich auf auf-20260827-61.", encoding="utf-8")
    (fremd / "auftraege" / "ergebnisse").mkdir(parents=True)

    b = R.rueckstau(hier, fremd)

    assert b["anderswo_beantwortet"] == []
    assert b["wirklich_offen"] == ["auf-20260827-61"]


# ======================================================================================
# Das Werkzeug — und seine Schalter, weil ein ungedrueckter Schalter still nichts tun kann
# ======================================================================================

def _werkzeug():
    import importlib.util
    pfad = Path(__file__).resolve().parents[1] / "tools" / "rueckstau.py"
    spec = importlib.util.spec_from_file_location("werkzeug_rueckstau", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_das_werkzeug_drueckt_seine_schalter(tmp_path, capsys):
    """`--fremd`, `--wurzel` und `--json` in einem Lauf. **Die Schalterprobe hat genau
    diesen Test verlangt** — sie meldete `rueckstau.py: ['--fremd']` als nie gedrueckt,
    und ein Schalter, den keine Probe drueckt, kann still nichts tun."""
    hier, fremd = tmp_path / "hier", tmp_path / "fremd"
    _auftrag(hier, "auf-20260901-11")
    _fremde_antwort(fremd, "auf-20260901-11.json", {"auftrag": "auf-20260901-11"})

    rc = _werkzeug().main(["--wurzel", str(hier), "--fremd", str(fremd), "--json"])

    assert rc == 0
    bericht = json.loads(capsys.readouterr().out)
    assert bericht["anderswo_beantwortet"] == ["auf-20260901-11"]
    assert bericht["fremdbaum_gesehen"] is True


def test_das_werkzeug_bleibt_gruen_auch_mit_rueckstand(tmp_path, capsys):
    """*Ein Rueckstand ist kein Fehler, sondern ein verteilter Auftrag.* Waere das hier
    rot, stuende es unter jedem Lauf rot — und dann sieht niemand mehr hin."""
    hier = tmp_path / "hier"
    _auftrag(hier, "auf-20260901-11")

    rc = _werkzeug().main(["--wurzel", str(hier), "--fremd", str(tmp_path / "nichts")])

    assert rc == 0
    assert "NICHT gesehen" in capsys.readouterr().out
