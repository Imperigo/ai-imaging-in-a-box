"""Die Schlusspräsentation — geprüft als Quelle, nicht als Datei.

**Warum es diese Datei gibt.** `praesentation/vortrag.mjs` lag bis zum 09.09.2026 unter
`build/`, also im Ordner für erzeugte und ausdrücklich wegwerfbare Dinge — nicht
versioniert. Zwei Sitzungen Zuschnitt hingen damit an einem ephemeren Container.

Geprüft wird hier das, was ohne die Bilder prüfbar ist: dass die **Auswahl** vollständig
ist, dass sie auf Beweisbilder zeigt und nicht irgendwohin, und dass die Platzhalter
sagen, worauf sie warten.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
ORDNER = WURZEL / "praesentation"
QUELLE = (ORDNER / "vortrag.mjs").read_text(encoding="utf-8")
KARTE = json.loads((ORDNER / "bilder.json").read_text(encoding="utf-8"))

#: Jeder Dateiname, den der Vortrag anfordert — `einBild(s, "maske.png")` und
#: `zweiBilder(s, "a.png", "b.png", …)`.
VERLANGT = sorted(set(re.findall(r'"([a-z0-9_]+\.png)"', QUELLE)))


def test_der_vortrag_verlangt_ueberhaupt_bilder():
    """Ohne diese Zeile sagten die beiden Tests darunter nichts.

    **Zwanzig und nicht dreissig**, obwohl es dreissig Folien sind: Vier tragen einen
    Platzhalter, zwei zeigen zwei Bilder nebeneinander, und Titel und Schluss zeigen
    keines. Die erste Fassung dieses Tests stand auf dreissig und fiel sofort — *eine
    Zahl, die aus der Folienzahl geschlossen war statt gezählt.*
    """
    assert len(VERLANGT) >= 20, f"nur {len(VERLANGT)} Bilder gefunden — Muster kaputt?"


@pytest.mark.parametrize("datei", VERLANGT)
def test_jedes_verlangte_bild_steht_in_der_auswahl(datei):
    """Ein Bild ohne Eintrag wird nie geholt — und die Folie bleibt leer.

    Eine leere Folie sieht aus wie eine Gestaltungsentscheidung. *Genau die Sorte
    Fehlschlag, der wie ein Erfolg aussieht.*
    """
    assert datei in KARTE, (
        f"{datei} wird auf einer Folie verlangt und steht nicht in bilder.json. "
        f"`python praesentation/hole_bilder.py` holt es damit nie.")


def test_die_auswahl_traegt_nichts_ueberzaehliges():
    """Die Gegenrichtung: ein Eintrag, den niemand mehr braucht, wird trotzdem geholt."""
    ueberzaehlig = sorted(set(KARTE) - set(VERLANGT))

    assert not ueberzaehlig, (
        f"{ueberzaehlig} steht in bilder.json und wird auf keiner Folie verlangt.")


@pytest.mark.parametrize("ziel,quelle", sorted(KARTE.items()))
def test_jede_quelle_zeigt_in_den_beweisgang(ziel, quelle):
    """Regel 3 und die Nachbaubarkeit in einem: relativer Pfad, unter `build/beweis/`.

    Ein absoluter Pfad trüge fast immer einen Benutzernamen, und ein Pfad ausserhalb des
    Beweisgangs wäre ein Bild, das dieses Repo nicht selbst erzeugen kann.
    """
    assert not quelle.startswith("/"), f"{ziel} zeigt auf einen absoluten Pfad"
    assert quelle.startswith("build/beweis/"), f"{ziel} zeigt nach {quelle}"


def test_die_platzhalter_sagen_worauf_sie_warten():
    """Vier Folien tragen noch keinen Beweis — und sagen, bei wem er liegt.

    Ein Platzhalter ohne Auftragskennung ist eine Lücke, die niemand schliesst: Man sieht,
    dass etwas fehlt, aber nicht, ob jemand daran ist.
    """
    zeilen = [z for z in QUELLE.splitlines() if "platzhalter(s," in z]

    assert zeilen, "keine Platzhalter gefunden — Muster kaputt oder alle Bilder da"
    assert any("auf-2026" in z for z in zeilen), (
        "kein Platzhalter nennt den Auftrag, bei dem sein Bild liegt")


def test_hole_bilder_meldet_luecken_statt_sie_zu_uebergehen(tmp_path):
    """Der Wächter des Werkzeugs: Was fehlt, ergibt Rückgabewert 1."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("hole_bilder", ORDNER / "hole_bilder.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)

    karte = {"gibtsnicht.png": "build/beweis/99_niemals/xyz.png"}

    assert modul.fehlende(karte, tmp_path) == [
        ("gibtsnicht.png", "build/beweis/99_niemals/xyz.png")]
    assert modul.hole(karte, tmp_path / "ziel", tmp_path) == []
