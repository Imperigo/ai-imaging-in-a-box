"""Das Lexikon ist Anhang der Vertiefungsarbeit — also wird es geprüft wie Code.

Anlass: Am 20.08.2026 fiel beim Nachschlagen auf, dass **Seed** zweimal darin stand, in
zwei Fassungen, in zwei Abschnitten. Beim Nachzählen waren es sieben Begriffe mit
Doppeleinträgen.

Ein Lexikon, das denselben Begriff zweimal erklärt, veraltet an einer der beiden Stellen —
und wer die falsche liest, liest die alte. Das ist dieselbe Fehlerart wie eine tote Kante:
Es sieht vollständig aus und trägt nicht.
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

import pytest

LEXIKON = Path(__file__).resolve().parents[1] / "docs" / "LEXIKON.md"

#: Begriffe, die **absichtlich** doppelt vorkommen, weil ein Wort zwei Sachverhalte
#: bezeichnet. Jeder Eintrag hier ist eine Entscheidung und keine Nachlässigkeit — und er
#: steht hier, damit die nächste echte Dublette nicht in ihnen untergeht.
GEWOLLTE_TRENNUNGEN = {
    "aggregation",   # Lizenzrecht / Messwerte
    "parameter",     # Aufrufargument / Modellgewichte
    "prädiktor",     # Kompression / Byte-Entflechtung
    "rauschboden",   # Streuung einer Saatreihe / Boden einer Metrik ohne Geometrie
    "validierung",   # eines Verfahrens / Daten gegen Schema
}


def _eintraege() -> list[str]:
    text = LEXIKON.read_text(encoding="utf-8")
    return re.findall(r"^\*\*(.+?)\*\*\s+—", text, re.M)


def _kern(titel: str) -> str:
    """Der Begriff ohne Klammerzusatz und ohne Synonyme — ``Seed (Startwert)`` → ``seed``."""
    ohne = re.sub(r"\s*\(.*?\)", "", titel)
    return ohne.split(" / ")[0].split(" gegen ")[0].strip().lower()


def test_kein_begriff_steht_zweimal_darin():
    """Ausser den ausgewiesenen Bedeutungstrennungen."""
    zaehler = collections.Counter(_kern(e) for e in _eintraege())
    doppelt = {k: v for k, v in zaehler.items() if v > 1}
    unerwartet = {k: v for k, v in doppelt.items() if k not in GEWOLLTE_TRENNUNGEN}
    assert not unerwartet, (
        f"Doppelte Einträge: {sorted(unerwartet)}. Entweder zusammenführen, oder — wenn "
        f"das Wort wirklich zwei Sachverhalte bezeichnet — beide Titel mit einem "
        f"Klammerzusatz unterscheidbar machen und hier eintragen."
    )


def test_jede_gewollte_trennung_ist_auch_wirklich_eine():
    """Wer hier etwas einträgt, muss es auch im Lexikon unterscheidbar machen.

    Sonst wäre diese Liste ein Freibrief: Man trägt einen Begriff ein, und die Prüfung
    schweigt für immer — auch dann, wenn die zweite Fassung längst eine schlechte Kopie
    der ersten ist.
    """
    nach_kern = collections.defaultdict(list)
    for titel in _eintraege():
        nach_kern[_kern(titel)].append(titel)

    for begriff in sorted(GEWOLLTE_TRENNUNGEN):
        titel = nach_kern.get(begriff, [])
        assert len(titel) > 1, (
            f"{begriff!r} steht als gewollte Trennung in der Liste, kommt im Lexikon aber "
            f"nur {len(titel)}× vor. Wenn die Dublette weg ist, gehört auch der Eintrag "
            f"hier weg.")
        assert len(set(titel)) == len(titel), (
            f"{begriff!r} kommt mehrfach unter **demselben** Titel vor: {titel}. Eine "
            f"Bedeutungstrennung, die man am Titel nicht sieht, ist keine — wer "
            f"nachschlägt, findet zwei gleich aussehende Einträge und liest den ersten.")


def test_die_liste_der_trennungen_ist_nicht_verwaist():
    """Kein Eintrag darf sich auf einen Begriff beziehen, den es nicht mehr gibt."""
    vorhanden = {_kern(e) for e in _eintraege()}
    verwaist = GEWOLLTE_TRENNUNGEN - vorhanden
    assert not verwaist, f"Diese Begriffe stehen nicht mehr im Lexikon: {sorted(verwaist)}"


def test_das_aenderungsverzeichnis_hat_eine_zeile_je_sitzung():
    """Die Regel aus CLAUDE.md ist: Fachbegriffe werden in DERSELBEN Sitzung nachgetragen.

    Geprüft wird das Schwächste, was sich prüfen lässt — dass es das Verzeichnis
    überhaupt gibt und dass es wächst. Ob ein bestimmter Begriff fehlt, kann kein Test
    wissen; das ist Sache dessen, der ihn benutzt hat.
    """
    text = LEXIKON.read_text(encoding="utf-8")
    assert "## Änderungsverzeichnis" in text
    zeilen = [z for z in text.splitlines() if re.match(r"^\| 2026-\d\d-\d\d \|", z)]
    assert len(zeilen) >= 20, f"nur {len(zeilen)} Einträge im Änderungsverzeichnis"


@pytest.mark.parametrize("begriff", [
    "Tote Kante", "Rauschboden (Streuung einer Saatreihe)", "Saatreihe",
    "Rauschboden (Boden einer Metrik ohne Geometrie)", "Belichtungsrahmen",
    "Waise (verwaister Auftrag)", "GIL (Global Interpreter Lock)", "Vakuumprobe",
    "Seed (Startwert)", "Lebenszeichen gegen Fortschrittszeichen",
])
def test_die_tragenden_begriffe_dieses_projekts_stehen_darin(begriff):
    """Eine kleine, handverlesene Liste: Begriffe, ohne die die Berichte nicht lesbar sind.

    Sie ist ausdrücklich **nicht** vollständig — Vollständigkeit lässt sich nicht prüfen,
    nur Fehlen. Was hier steht, ist das, dessen Verlust am meisten kosten würde.
    """
    assert f"**{begriff}**" in LEXIKON.read_text(encoding="utf-8")
