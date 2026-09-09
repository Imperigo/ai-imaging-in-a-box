"""Eine Messung ohne ihren Codestand ist nicht nachfahrbar.

Der Anlass ist eine Durchsicht vom 09.09.2026, die **sieben** veröffentlichte Dokumente
entwertet hat. Ursache war eine einzige eigene Änderung: `kameras.py`, Commit ``e99caba``
vom 01.09.2026, hat den Kameraabstand für schräge Richtungen um rund 24 % verkürzt. Jede
Zahl aus einer diagonalen Ansicht davor ist seither *nicht falsch, aber nicht mehr
reproduzierbar* — und acht Tage lang ist das niemandem aufgefallen.

*Was gefehlt hat, war kein weiterer Vorbehalt, sondern eine Verbindung zwischen einer
Messung und dem Codestand, auf dem sie steht.*
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from aiimaging import messstand

WURZEL = Path(__file__).resolve().parents[1]


# ── Der Wächter über die Dokumente ───────────────────────────────────────────────────

def test_jedes_messdokument_ab_dem_stichtag_nennt_seinen_codestand():
    """Der eigentliche Riegel, und er gilt für die Dokumente dieses Repos."""
    fehlend = messstand.ohne_codestand(WURZEL / "docs")
    assert not fehlend, (
        "Diese Messdokumente nennen ihren Codestand nicht:\n  " + "\n  ".join(fehlend)
        + f"\nZeile einsetzen: {messstand.MARKE} `<kurzer commit>`"
    )


def test_aeltere_dokumente_werden_nicht_nachtraeglich_gestempelt(tmp_path):
    """**Rückwirkend gilt die Regel nicht**, und das ist kein Nachlass.

    Welcher Commit unter einer Messung vom 20.08.2026 stand, lässt sich heute nicht mehr
    feststellen. Eine nachgetragene Zahl wäre geraten — und *eine Regel rückwirkend mit
    Vermutungen zu erfüllen ist schlimmer, als sie erst ab heute zu haben.*
    """
    (tmp_path / "ALT_2026-08-20.md").write_text("# Alt\n\nZahlen ohne Stempel.\n",
                                                encoding="utf-8")
    assert messstand.ohne_codestand(tmp_path) == []


def test_ein_dokument_ab_dem_stichtag_ohne_zeile_faellt_auf(tmp_path):
    """Die Gegenprobe: Ohne sie prüfte der Test darüber nur, dass die Liste leer bleibt."""
    (tmp_path / "NEU_2026-09-09.md").write_text("# Neu\n\nZahlen ohne Stempel.\n",
                                                encoding="utf-8")
    assert messstand.ohne_codestand(tmp_path) == ["NEU_2026-09-09.md"]


def test_dokumente_ohne_datum_im_namen_sind_nicht_gemeint(tmp_path):
    """PLAN, LEXIKON, EINBAU_STAND laufen fort — sie veröffentlichen keine Messreihe."""
    (tmp_path / "PLAN.md").write_text("# Plan\n\nkein Stempel.\n", encoding="utf-8")
    assert messstand.ohne_codestand(tmp_path) == []


def test_die_ausnahmeliste_traegt_ihren_grund():
    """Eine unbegründete Ausnahmeliste wächst, bis sie die Regel ersetzt."""
    quelle = (WURZEL / "src" / "aiimaging" / "messstand.py").read_text(encoding="utf-8")
    for name in messstand.AUSNAHMEN:
        assert name in quelle, f"{name} steht nicht mit seinem Grund im Quelltext"


# ── Der Stempel selbst ───────────────────────────────────────────────────────────────

def test_der_codestand_kommt_aus_git_und_nicht_aus_einer_annahme():
    stand = messstand.codestand(WURZEL)
    assert len(stand["commit"]) == 40
    assert stand["kurz"] == stand["commit"][:7]
    assert isinstance(stand["sauber"], bool)
    assert stand["datum"] == date.today().isoformat()


def test_ein_veraenderter_arbeitsbaum_steht_in_der_zeile():
    """Eine Messung auf einem veränderten Baum steht auf keinem benennbaren Stand.

    Das gehört in die Zeile und nicht in eine Fussnote — sonst liest sie sich wie ein
    sauberer Stand.
    """
    schmutzig = messstand.zeile({"kurz": "abc1234", "sauber": False})
    sauber = messstand.zeile({"kurz": "abc1234", "sauber": True})

    assert "Arbeitsbaum verändert" in schmutzig
    assert "nicht nachfahrbar" in schmutzig
    assert "Arbeitsbaum" not in sauber
    assert sauber.endswith("`abc1234`")


def test_ohne_git_wird_nicht_geraten(tmp_path):
    """Fail-closed: **kein Rückfall auf «unbekannt»**.

    Eine Zeile, die «unbekannt» sagt, sieht aus wie eine Angabe und ist keine — dieselbe
    Lesart, gegen die in diesem Projekt die dritte Antwort steht.
    """
    with pytest.raises(messstand.MessstandError):
        messstand.codestand(tmp_path)
