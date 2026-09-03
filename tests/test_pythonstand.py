"""Läuft dieses Repo auf der Fassung, die es zusagt?

*Der Anlass ist der 02.09.2026, und er war teuer.* `src/aiimaging/abholer.py` trug einen
**mehrzeiligen Ausdruck innerhalb eines f-Strings**. Den gibt es erst ab Python 3.12
(PEP 701); `pyproject.toml` sagt `>=3.11` zu, und in dieser Umgebung läuft 3.11.

Die Folge war nicht ein roter Test, sondern **fünfundzwanzig Sammelabbrüche**: pytest kam
gar nicht bis zur ersten Probe. Wer das sieht, liest drei Tracebacks, bevor er den einen
Satz findet, um den es geht — und der stand in keinem davon.

**Auf der Maschine, auf der die Zeile entstand, war alles grün.** Sie läuft Python 3.14.4.
Zwischen den beiden Ständen liegen drei Nebenversionen, und die Testzahl im README sagte
auf der einen Seite «alles grün», während die andere nicht einmal importieren konnte.

Was diese Datei kann — und was nicht
------------------------------------
Sie prüft gegen den **laufenden** Auslegeprozess. Hier fängt sie den Fall; auf 3.14 fängt
sie ihn **nicht**, denn dort ist die Zeile gültig. `ast.parse(..., feature_version=…)`
hilft nicht: Es deckt Sprachmerkmale ab, nicht den Tokenizer, und PEP 701 hat den
Tokenizer geändert.

*Ein Wächter, der seine blinde Stelle verschweigt, ist gefährlicher als keiner.* Die
andere Hälfte der Antwort ist darum keine Probe, sondern eine **Ansage** — sie steht in
`auf-20260826-59`.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]


def _mindestfassung() -> tuple[int, int]:
    """Die zugesagte Mindestfassung — **aus `pyproject.toml`**, nicht noch einmal hier.

    Eine zweite Stelle mit derselben Zahl wäre die doppelte Vorgabe, an der dieses Projekt
    am 23.08. fünf Tage lang eine gekippte Kamera hatte.
    """
    roh = tomllib.loads((WURZEL / "pyproject.toml").read_text(encoding="utf-8"))
    text = str(roh["project"]["requires-python"]).strip()
    ziffern = text.lstrip(">=~^ ").split(".")
    return int(ziffern[0]), int(ziffern[1])


def _versionierte_dateien() -> list[Path]:
    """Jede von git geführte `.py` — **nicht** ein Ordnerdurchlauf.

    Ein Durchlauf über das Dateisystem läse `build/`, `.venv` und die Reste abgebrochener
    Läufe mit; was dort nicht parst, geht niemanden etwas an.
    """
    roh = subprocess.run(["git", "-C", str(WURZEL), "ls-files", "*.py"],
                         capture_output=True, text=True, check=True).stdout
    return [WURZEL / z for z in roh.split() if z]


def test_der_laufende_python_stand_haelt_die_zusage():
    """Wer unter der Mindestfassung fährt, soll es als **einen Satz** erfahren."""
    mindest = _mindestfassung()
    laeuft = sys.version_info[:2]
    assert laeuft >= mindest, (
        f"Python {laeuft[0]}.{laeuft[1]} laeuft, zugesagt ist mindestens "
        f"{mindest[0]}.{mindest[1]} (pyproject.toml). Alles Weitere in dieser Sammlung "
        f"sagt darueber nichts.")


@pytest.mark.parametrize("pfad", _versionierte_dateien(), ids=lambda p: p.name)
def test_jede_versionierte_datei_laesst_sich_einlesen(pfad):
    """**Der Wächter, und sein Zweck ist die Lesbarkeit des Fehlschlags.**

    Ohne ihn meldet pytest fünfundzwanzig Sammelabbrüche und keinen Grund. Mit ihm steht
    **eine** rote Zeile da, mit Datei und Zeilennummer — und zwar auch dann, wenn die
    kaputte Datei von niemandem importiert wird.
    """
    quelle = pfad.read_text(encoding="utf-8")
    try:
        ast.parse(quelle, filename=str(pfad))
    except SyntaxError as fehler:
        mindest = _mindestfassung()
        pytest.fail(
            f"{pfad.relative_to(WURZEL)} laesst sich auf Python "
            f"{sys.version_info.major}.{sys.version_info.minor} nicht einlesen: "
            f"Zeile {fehler.lineno}, {fehler.msg}.\n"
            f"Zugesagt ist mindestens {mindest[0]}.{mindest[1]} — was auf einer neueren "
            f"Fassung gueltig ist, muss es hier nicht sein. Am 02.09.2026 war es ein "
            f"mehrzeiliger Ausdruck IN einem f-String (PEP 701, ab 3.12).")


def test_der_waechter_wuerde_eine_kaputte_datei_wirklich_melden(tmp_path):
    """Die Gegenprobe: Ohne sie wäre der Wächter darüber auch grün, wenn er gar nichts
    einliese. *Ein Wächter, der nicht fällt, bewacht nichts.*"""
    kaputt = tmp_path / "kaputt.py"
    kaputt.write_text("def f(:\n    pass\n", encoding="utf-8")
    with pytest.raises(SyntaxError):
        ast.parse(kaputt.read_text(encoding="utf-8"))


def test_die_liste_kommt_aus_git_und_nicht_aus_dem_dateisystem():
    """`build/` und Reste abgebrochener Läufe gehören nicht dazu — und ohne diese Probe
    fiele es erst auf, wenn dort etwas Kaputtes liegt und niemand versteht, warum."""
    dateien = _versionierte_dateien()
    assert dateien, "ohne Dateien sagt der Waechter nichts"
    assert not [p for p in dateien if "build" in p.parts or ".venv" in p.parts]
