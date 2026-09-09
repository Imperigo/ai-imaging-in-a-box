"""Der **Codestand**, auf dem eine Messung steht — und der Wächter darüber.

Warum es dieses Modul gibt
--------------------------
Am 09.09.2026 hat eine Durchsicht sieben veröffentlichte Dokumente entwertet. Der Anlass
war eine einzige eigene Änderung: `kameras.py`, Commit ``e99caba`` vom 01.09.2026, hat
den Kameraabstand für schräge Richtungen um rund 24 % verkürzt. Jede Zahl, die vorher an
einer diagonalen Kamera gemessen wurde, ist seither **nicht falsch, aber nicht mehr
reproduzierbar** — und acht Tage lang ist das niemandem aufgefallen.

*Was gefehlt hat, war kein weiterer Vorbehalt, sondern eine Verbindung zwischen einer
Messung und dem Codestand, auf dem sie steht.* Die stellt dieses Modul her.

Es ist bewusst klein: eine Zeile Text unter der Datumszeile, und ein Wächter, der sie
verlangt. Wer eine Zahl veröffentlicht, sagt damit, gegen welchen Stand sie steht — und
wer sie später nicht reproduzieren kann, sieht sofort, ob er dieselbe Software fährt.

Der Stichtag
------------
:data:`STICHTAG` ist der Tag, ab dem die Regel gilt. Ältere Dokumente werden **nicht**
nachträglich gestempelt: Welcher Commit unter einer Messung vom 20.08. stand, lässt sich
heute nicht mehr feststellen, und eine nachgetragene Zahl wäre geraten. *Eine Regel
rückwirkend zu erfüllen, indem man sie mit Vermutungen füllt, ist schlimmer als sie erst
ab heute zu haben.*
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

#: Ab diesem Tag muss ein Messdokument seinen Codestand nennen.
STICHTAG = date(2026, 9, 9)

#: Wie die Zeile im Dokument aussieht. Der Wächter sucht genau diesen Anfang.
MARKE = "**Codestand:**"

#: Dateien unter ``docs/``, die trotz Datum im Namen keine Messung veröffentlichen.
#: Jede Ausnahme steht hier mit ihrem Grund — eine unbegründete Ausnahmeliste wächst.
AUSNAHMEN = {
    # Ein Plan sagt, was zu tun ist, und veröffentlicht keine Messwerte.
    "PLAN_2026-08-20.md",
}


class MessstandError(ValueError):
    """Der Codestand liess sich nicht feststellen."""


def codestand(repo_wurzel=None) -> dict:
    """Commit, Sauberkeit und Datum — der Stand, auf dem eine Messung von jetzt steht.

    Returns:
        ``{commit, kurz, sauber, datum}``. ``sauber`` ist ``False``, sobald irgendetwas
        im Arbeitsbaum verändert ist: Eine Messung auf einem verändertem Baum steht auf
        keinem benennbaren Stand, und das gehört dazugesagt.

    Raises:
        MessstandError: Kein git, kein Repo, kein Commit. **Kein Rückfall auf «unbekannt»**
            — eine Zeile, die «unbekannt» sagt, sieht aus wie eine Angabe und ist keine.
    """
    wurzel = Path(repo_wurzel) if repo_wurzel else Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.run(
            ["git", "-C", str(wurzel), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=20, check=False)
        zustand = subprocess.run(
            ["git", "-C", str(wurzel), "status", "--porcelain"],
            capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as fehler:
        raise MessstandError(f"git nicht aufrufbar: {fehler}") from fehler
    if commit.returncode != 0 or not commit.stdout.strip():
        raise MessstandError(
            f"Kein Commit unter {wurzel} feststellbar ({commit.stderr.strip() or 'leer'}). "
            f"Eine Messung ohne benennbaren Codestand ist nicht nachfahrbar — und eine "
            f"Zeile, die «unbekannt» sagt, sieht aus wie eine Angabe und ist keine.")
    voll = commit.stdout.strip()
    return {
        "commit": voll,
        "kurz": voll[:7],
        "sauber": not zustand.stdout.strip(),
        "datum": date.today().isoformat(),
    }


def zeile(stand: dict | None = None, repo_wurzel=None) -> str:
    """Die Zeile, die in ein Messdokument gehört — fertig zum Einsetzen."""
    s = stand or codestand(repo_wurzel)
    nachsatz = "" if s["sauber"] else " · **Arbeitsbaum verändert**, nicht nachfahrbar"
    return f"{MARKE} `{s['kurz']}`{nachsatz}"


def _datum_im_namen(name: str) -> date | None:
    treffer = re.search(r"(20\d\d)-(\d\d)-(\d\d)", name)
    if not treffer:
        return None
    try:
        return date(*(int(t) for t in treffer.groups()))
    except ValueError:
        return None


def ohne_codestand(docs_ordner) -> list[str]:
    """Messdokumente ab dem :data:`STICHTAG`, die ihren Codestand nicht nennen.

    Gesucht wird nur in Dateien, die ein **Datum im Namen** tragen — das ist in diesem
    Repo die Form, in der eine Messung veröffentlicht wird. Ein Dokument ohne Datum ist
    ein fortlaufendes (Plan, Lexikon, Einbau-Stand) und veröffentlicht keine Messreihe.
    """
    ordner = Path(docs_ordner)
    fehlend = []
    for p in sorted(ordner.glob("*.md")):
        if p.name in AUSNAHMEN:
            continue
        wann = _datum_im_namen(p.name)
        if wann is None or wann < STICHTAG:
            continue
        if MARKE not in p.read_text(encoding="utf-8", errors="ignore"):
            fehlend.append(p.name)
    return fehlend


__all__ = ["AUSNAHMEN", "MARKE", "STICHTAG", "MessstandError", "codestand",
           "ohne_codestand", "zeile"]
