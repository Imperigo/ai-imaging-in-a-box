"""``tools/einbau.py`` — die Zeile «WARTEN AUF EINE ANTWORT, DIE DA IST».

Warum es diese Wächter gibt
---------------------------
Befund vom 22.09.2026. Die Kopfzeile dieses Abschnitts wurde aus

    max((w["seit_tagen"] or 0) for w in wartend)

gebildet. ``seit_tagen`` ist ``None``, wenn die Antwort kein Datum trägt —
:func:`aiimaging.einbau.wartet_auf_beantwortetes` setzt das mit Absicht, und
``tests/test_einbau.py`` hält den Grund fest: *«Null Tage hiesse heute beantwortet.
Unbekannt heisst unbekannt.»*

Das ``or 0`` machte daraus stillschweigend eine Null. Trugen **alle** wartenden Posten
kein Datum, meldete der Bericht an den Owner «aeltester seit 0 Tagen» — also «heute
beantwortet», an genau der Stelle, an der nichts gemessen ist. *Eine Zahl, die
Dringlichkeit kleinredet*, und sie sah aus wie eine Messung.

Geprüft wird hier die **ausgegebene Zeile**, nicht der Quelltext: Die Wächter fahren das
Werkzeug über seinen Produktweg — ``main(["--repo", …])`` — gegen einen synthetischen
Probeordner und lesen, was auf dem Bildschirm steht. Drei Lagen, drei Wächter: kein
Datum, teils Datum, überall Datum.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _werkzeug():
    """Das Werkzeug so laden, wie es auf der Platte liegt — es ist kein Paketmodul."""
    pfad = REPO / "tools" / "einbau.py"
    spez = importlib.util.spec_from_file_location("werkzeug_einbau_alter", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _posten(tmp_path, zeilen: list[str]) -> None:
    """Ein Einbau-Stand an der Stelle, an der das Werkzeug ihn ohne Zutun sucht."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    kopf = ["| # | Posten | Zustand | Seit | Beleg |", "|---|---|---|---|---|"]
    (docs / "EINBAU_STAND.md").write_text("\n".join(kopf + zeilen) + "\n",
                                          encoding="utf-8")


def _beantwortet(tmp_path, kennung: str, *, beendet: str) -> None:
    """Auftrag **und** Antwort — der abgeleitete Zustand braucht beide Seiten.

    ``beendet=""`` ist der Fall, um den es geht: eine Antwort ohne Datum. Sie ist da,
    aber wann sie kam, weiss niemand.
    """
    offen = tmp_path / "auftraege" / "offen"
    offen.mkdir(parents=True, exist_ok=True)
    (offen / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-auftrag/v1", "auftrag_id": kennung,
        "art": "qa", "worker": "local", "rang": 1, "params": {},
        "beschreibung": "Probe", "anweisung": "Probe",
    }, ensure_ascii=False), encoding="utf-8")
    ergebnisse = tmp_path / "auftraege" / "ergebnisse"
    ergebnisse.mkdir(parents=True, exist_ok=True)
    (ergebnisse / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-ergebnis/v1", "auftrag_id": kennung,
        "status": "ok", "beendet": beendet, "zusammenfassung": "gemessen",
    }, ensure_ascii=False), encoding="utf-8")


def _wartezeile(tmp_path, capsys) -> str:
    """Der Produktweg: das Werkzeug fahren und die Kopfzeile des Abschnitts lesen.

    Nicht ``_zeilen`` von Hand aufgerufen — *eine Naht, die nur der direkte Aufrufer
    erreicht, gibt es für den Weg nicht, den das Produkt wirklich geht.*
    """
    _werkzeug().main(["--repo", str(tmp_path)])
    ausgabe = capsys.readouterr().out
    treffer = [z for z in ausgabe.splitlines()
               if z.startswith("WARTEN AUF EINE ANTWORT, DIE DA IST")]
    assert len(treffer) == 1, f"keine oder mehrfache Wartezeile in:\n{ausgabe}"
    return treffer[0]


def _vor_tagen(n: int) -> str:
    """Ein Datum, das heute genau ``n`` Tage alt ist — gerechnet wie das Modul rechnet."""
    return (datetime.now(timezone.utc).date() - timedelta(days=n)).isoformat() + "T00:00:00Z"


# ── Lage 1: kein einziges Alter gemessen ─────────────────────────────────────────────

def test_ohne_ein_einziges_datum_steht_keine_zahl_da(tmp_path, capsys):
    """Der Befund selbst. Vorher: «aeltester seit 0 Tagen» — heute beantwortet.

    Null ist hier die gefährlichste aller Antworten: Sie ist die harmloseste Lage, und
    sie steht an der Stelle, an der nichts gemessen wurde.
    """
    _posten(tmp_path, [
        "| C3 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-11` |",
        "| C4 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-12` |"])
    _beantwortet(tmp_path, "auf-20260901-11", beendet="")
    _beantwortet(tmp_path, "auf-20260901-12", beendet="")

    zeile = _wartezeile(tmp_path, capsys)

    assert "2 Posten" in zeile
    assert "unbekannt" in zeile.lower(), zeile
    assert "0 Tagen" not in zeile, "eine Null hiesse «heute beantwortet»"
    assert "Tagen" not in zeile, f"keine gemessene Zahl, also auch keine Angabe: {zeile}"


# ── Lage 2: einige gemessen, einige nicht ────────────────────────────────────────────

def test_neben_einem_bekannten_aeltesten_werden_die_undatierten_genannt(tmp_path, capsys):
    """Sonst liest sich das älteste BEKANNTE als das älteste überhaupt.

    Der undatierte Posten kann jeden von ihnen überholen — das weiss nur niemand.
    """
    _posten(tmp_path, [
        "| C3 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-11` |",
        "| C4 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-12` |",
        "| C5 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-13` |"])
    _beantwortet(tmp_path, "auf-20260901-11", beendet=_vor_tagen(6))
    _beantwortet(tmp_path, "auf-20260901-12", beendet=_vor_tagen(2))
    _beantwortet(tmp_path, "auf-20260901-13", beendet="")

    zeile = _wartezeile(tmp_path, capsys)

    assert "3 Posten" in zeile
    assert "6 Tagen" in zeile, f"das älteste BEKANNTE Alter fehlt: {zeile}"
    assert "1 ohne Datum" in zeile, f"die undatierten bleiben ungenannt: {zeile}"


# ── Lage 3: alles gemessen ───────────────────────────────────────────────────────────

def test_wo_jedes_alter_gemessen_ist_steht_die_zahl_ohne_vorbehalt(tmp_path, capsys):
    """Die Gegenprobe. Ohne sie hätte ein Wächter, der einfach nie eine Zahl zeigt, ihn
    bestanden — und die Zeile wäre für den häufigsten Fall nutzlos geworden."""
    _posten(tmp_path, [
        "| C3 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-11` |",
        "| C4 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-12` |"])
    _beantwortet(tmp_path, "auf-20260901-11", beendet=_vor_tagen(9))
    _beantwortet(tmp_path, "auf-20260901-12", beendet=_vor_tagen(4))

    zeile = _wartezeile(tmp_path, capsys)

    assert "2 Posten" in zeile
    assert "aeltester seit 9 Tagen" in zeile, zeile
    assert "unbekannt" not in zeile.lower()
    assert "ohne Datum" not in zeile


# ── Die Einzelzeilen darunter waren nie falsch — und bleiben es ──────────────────────

def test_die_einzelzeile_ohne_datum_zeigt_weiterhin_ein_fragezeichen(tmp_path, capsys):
    """Sie war schon richtig, als die Kopfzeile log. Genau darum fiel es keinem auf:
    Wer bis zur Einzelzeile las, sah «?»; wer nur die Kopfzeile las, sah «0 Tage»."""
    _posten(tmp_path, [
        "| C3 | Etwas | 🟩 **halb** | 2026-09-01 | `auf-20260901-11` |"])
    _beantwortet(tmp_path, "auf-20260901-11", beendet="")

    _werkzeug().main(["--repo", str(tmp_path)])
    zeilen = capsys.readouterr().out.splitlines()

    einzel = [z for z in zeilen if "auf-20260901-11" in z and z.startswith("      C3")]
    assert einzel and "?" in einzel[0], zeilen
