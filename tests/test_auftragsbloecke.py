"""Die Auftragsbloecke unter `auftraege/bloecke/` muessen alles nennen, was bei ihrem Adressaten liegt.

Warum es diese Proben gibt
--------------------------
Ein Prompt unter ``auftraege/bloecke/`` ist eine **Zustellform**, keine zweite Wahrheit:
Die Aufträge stehen in ``auftraege/offen/``. Genau daraus entsteht die Gefahr — wird ein
Auftrag angelegt, nachdem der Block geschrieben wurde, fehlt er dort, und **niemand
merkt es**. Das ist wortgleich der Fehler vom 03.09.2026 («abgelegt ist nicht
ausgeliefert»), nur eine Ebene höher.

Und es ist zum zweiten Mal derselbe Fehlertyp wie beim Stichtag des Zustellbelegs: Dort
stand ein Kommentar, der einen Menschen ans Nachziehen erinnerte, und er wurde übergangen.
*Was von Hand nachgezogen wird, wird irgendwann nicht mehr nachgezogen.*

Was hier ausdrücklich NICHT geprüft wird
----------------------------------------
**Ob die Fragen im Block noch stimmen.** Das ist Prosa und wäre eine Suche mit vielen
Fehlalarmen — der Punkt, an dem ein Werkzeug abgeschaltet wird. Geprüft wird nur, was
maschinell entscheidbar ist: dass **jede Kennung vorkommt**.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import auftrag as auf
from aiimaging import auftragspost

WURZEL = Path(__file__).resolve().parents[1]
BLOECKE = WURZEL / "auftraege" / "bloecke"


def _neuester_block(worker: str) -> Path | None:
    """Der jüngste Block für diesen Adressaten — ``JJJJ-MM-TT_<worker>.md``.

    Die Datumsvoranstellung macht die Sortierung nach Namen zur Sortierung nach Zeit.
    """
    treffer = sorted(BLOECKE.glob(f"*_{worker}.md"))
    return treffer[-1] if treffer else None


@pytest.mark.parametrize("worker", sorted(auftragspost.ZUSTELLUNG_NOETIG))
def test_der_neueste_block_nennt_jeden_offenen_auftrag(worker):
    """Jede offene Kennung dieses Adressaten steht im Block — sonst ist sie nicht zugestellt."""
    block = _neuester_block(worker)
    if block is None:
        pytest.skip(f"Fuer {worker!r} gibt es (noch) keinen Prompt-Block.")
    text = block.read_text(encoding="utf-8")
    offen = [a["auftrag_id"] for a in auf.unerledigt(WURZEL)
             if a.get("worker") == worker]
    # DIE KURZFORM ZAEHLT MIT: Im Fliesstext steht `auf-37`, nicht `auf-20260823-37` —
    # der lange Name macht einen Block unlesbar, und unlesbar heisst: wird nicht gelesen.
    fehlend = [k for k in offen
               if k not in text and f"auf-{k.rsplit('-', 1)[-1]}" not in text]
    assert not fehlend, (
        f"{block.name} nennt {len(fehlend)} offene Auftraege nicht: {', '.join(fehlend)}.\n"
        f"Ein Block, der einen Auftrag auslaesst, laesst ihn liegen — und es faellt "
        f"niemandem auf, weil in `auftraege/offen/` alles ordentlich aussieht.")


@pytest.mark.parametrize("worker", sorted(auftragspost.ZUSTELLUNG_NOETIG))
def test_der_block_sagt_wie_geantwortet_wird(worker):
    """*Ein Auftrag ohne Rückweg erzeugt eine Antwort, die niemand findet.*

    Dieselbe Regel wie in `auftragspost.block`, hier für den dritten Zustellweg.
    """
    block = _neuester_block(worker)
    if block is None:
        pytest.skip(f"Fuer {worker!r} gibt es (noch) keinen Prompt-Block.")
    text = block.read_text(encoding="utf-8")
    assert "Wie geantwortet wird" in text
    assert "auftraege/ergebnisse" in text or "Ergebnisdatei" in text


@pytest.mark.parametrize("worker", sorted(auftragspost.ZUSTELLUNG_NOETIG))
def test_der_block_traegt_die_regel_drei_auflage(worker):
    """Unser Repo ist öffentlich, und der Block geht an jemanden, der das nicht weiss."""
    block = _neuester_block(worker)
    if block is None:
        pytest.skip(f"Fuer {worker!r} gibt es (noch) keinen Prompt-Block.")
    text = block.read_text(encoding="utf-8")
    assert "öffentlich" in text
    assert "Benutzernamen" in text


def test_kein_block_traegt_einen_pfad_aus_dieser_umgebung():
    """Was hier durchrutscht, ist draussen — dieselbe Wache wie an `auftragspost.block`."""
    for block in sorted(BLOECKE.glob("*.md")):
        text = block.read_text(encoding="utf-8")
        _, ersetzt = auf.ohne_kennungen(text)
        assert ersetzt == 0, (
            f"{block.name} traegt {ersetzt} Pfad(e) mit Benutzernamen.")
