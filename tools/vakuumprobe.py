#!/usr/bin/env python3
"""VAKUUMPROBE — findet grüne Tests, die nichts geprüft haben.

Der Anlass
----------
Am 20.08.2026 hat die HomeStation einen eigenen Fehler gemeldet: Sie hatte einen Wächter
als *grün* geführt, er habe eine bestimmte Auflösung geprüft. Das Fundartefakt aus ihrem
eigenen Lauf trug ``{"geprueft": 0}``. **Er hatte nichts gemessen.** Sie hatte aus „Test
bestanden" auf „Wächter hat geprüft" geschlossen, ohne nachzusehen.

> **Ein bestandener Test ist kein Beleg dafür, dass er etwas geprüft hat.**

Das ist die Testsuiten-Fassung des Satzes, den dieses Projekt schon dreimal bezahlt hat.
Diese Probe stellt die Frage an die **eigene** Suite.

Was gesucht wird
----------------
Die Gestalt, die vakuum-wahr ist: eine Zusicherung über **alle** Elemente einer Sammlung,
die auch dann hält, wenn die Sammlung **leer** ist.

* ``all(...)`` über nichts ist ``True``.
* ``not any(...)`` über nichts ist ``True``.

Ein Test, der so gebaut ist, besteht auch dann, wenn der Mechanismus, der die Sammlung
füllen soll, **vollständig kaputt** ist.

Wie gemessen wird — und warum nicht statisch
--------------------------------------------
Statisch lässt sich nicht sagen, ob eine Sammlung zur Laufzeit leer ist. Also wird
**umgeschrieben und ausgeführt**: Auf einer *Kopie* der Suite werden genau diese Aufrufe
durch eine Fassung ersetzt, die bei leerer Sammlung **fehlschlägt**. Was danach rot ist,
war vorher grün und leer.

Das Repo wird dabei **nicht angefasst** — gearbeitet wird in einem temporären Verzeichnis.

Was ein Treffer bedeutet — und was nicht
-----------------------------------------
Ein Treffer ist **kein Fehler**, sondern eine **schwache Stelle**. Eine Zusicherung über
eine Abwesenheit („keine Warnung enthält X") ist inhaltlich richtig, auch wenn gar keine
Warnung da ist. Sie ist nur *für sich allein* wertlos.

Was sie tragfähig macht, ist eine **Gegenprobe**: ein Test, der am selben Mechanismus
zeigt, dass die Sammlung sich im umgekehrten Fall **füllt**. Wer einen Treffer prüft,
sucht danach — und schreibt eine, wenn keine da ist.

*Erste Messung am 20.08.2026: 40 umgeschriebene Stellen, **6 Treffer**, und für jeden
Treffer lag eine Gegenprobe in derselben Datei. Kein einziger falsch-grüner Test.*

Aufruf
------
``python tools/vakuumprobe.py`` — oder mit ``--zeige-kopie``, um das Arbeitsverzeichnis
zu behalten und hineinzusehen.
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

#: Der Helfer, der jeder umgeschriebenen Testdatei angehängt wird.
HELFER = '''

# ── von tools/vakuumprobe.py angehängt ────────────────────────────────────────────────
def _vakuumwache(it, _art):
    werte = list(it)
    assert werte, (
        f"VAKUUM: {_art}() lief über eine LEERE Sammlung. Dieser Test hält auch dann, "
        f"wenn der Mechanismus, der sie füllen soll, vollständig kaputt ist. Er braucht "
        f"eine Gegenprobe: einen Test, der am selben Mechanismus zeigt, dass sich die "
        f"Sammlung im umgekehrten Fall füllt."
    )
    return werte


def _all(it):
    return all(_vakuumwache(it, "all"))


def _any(it):
    return any(_vakuumwache(it, "any"))
'''


def stellen(quelle: str) -> list[tuple[int, int, str]]:
    """Die vakuum-wahren Aufrufe einer Testdatei: ``(Zeile, Spalte, 'all'|'any')``.

    Gefunden wird nur, was **direkt** in einem ``assert`` steht. Ein ``all(...)`` mitten
    in einer Hilfsfunktion sagt nichts über den Ausgang eines Tests, und jeder Treffer,
    den ein Mensch als irrelevant abtut, macht die nächste Meldung eine Spur unglaubwürdiger.
    """
    gefunden: list[tuple[int, int, str]] = []
    for knoten in ast.walk(ast.parse(quelle)):
        if not isinstance(knoten, ast.Assert):
            continue
        pruefung = knoten.test

        def ist(n, name: str) -> bool:
            return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == name)

        if ist(pruefung, "all"):
            gefunden.append((pruefung.func.lineno, pruefung.func.col_offset, "all"))
        elif (isinstance(pruefung, ast.UnaryOp) and isinstance(pruefung.op, ast.Not)
              and ist(pruefung.operand, "any")):
            gefunden.append((pruefung.operand.func.lineno,
                             pruefung.operand.func.col_offset, "any"))
    return gefunden


def schreibe_um(datei: Path) -> int:
    """Eine Testdatei an Ort und Stelle umschreiben. Gibt die Zahl der Stellen zurück.

    Ersetzt wird **von hinten nach vorn**, damit frühere Zeilennummern gültig bleiben.
    """
    quelle = datei.read_text(encoding="utf-8")
    treffer = stellen(quelle)
    if not treffer:
        return 0
    zeilen = quelle.splitlines(keepends=True)
    for zeile, spalte, name in sorted(treffer, reverse=True):
        z = zeilen[zeile - 1]
        if z[spalte:spalte + len(name)] != name:
            # Die Quelle passt nicht zur Auswertung — lieber gar nicht anfassen als
            # falsch. Ein stiller Fehlgriff hier erzeugte einen Treffer, den es nicht gibt.
            return 0
        zeilen[zeile - 1] = z[:spalte] + "_" + name + z[spalte + len(name):]
    datei.write_text("".join(zeilen) + HELFER, encoding="utf-8")
    return len(treffer)


#: Was in die Arbeitskopie mitmuss, damit die Suite dort überhaupt läuft.
#:
#: ``docs`` steht hier, seit `tests/test_lexikon.py` das Lexikon liest. Ohne es scheitern
#: dreizehn Tests aus einem Grund, der mit Vakuum nichts zu tun hat — und die erste
#: Fassung dieses Werkzeugs meldete sie prompt als Treffer.
#:
#: **Am 26.08.2026 ist dieselbe Lücke ein zweites Mal aufgegangen**, und diesmal in die
#: gefährlichere Richtung: Drei neue Wächter lesen Dateien im Repo — ``README.md``,
#: ``NOTICE`` und ``auftraege/offen/``. Keine davon stand hier. In der Arbeitskopie
#: scheiterte darum schon das **Einsammeln**, und das Werkzeug meldete nicht etwa einen
#: Fehler, sondern **null Treffer** — von zwölf am Vormittag auf keinen, ohne dass sich an
#: der Suite etwas geändert hätte. Siehe :func:`_rote`.
#: Was in die Arbeitskopie mitmuss.
#:
#: **Die Liste ist gewachsen, und jedes Mal aus demselben Grund:** Ein Verzeichnis, das
#: ein Test liest und das hier fehlt, macht diesen Test in der Kopie rot — **vor** jedem
#: Umschreiben. Er zaehlt dann nicht mehr als Treffer, und die Probe ist an dieser Stelle
#: blind, ohne es zu sagen.
#:
#: `betrieb` und `integrations` kamen am 26.08.2026 dazu: `docs/EINBAU_STAND.md` beruft
#: sich auf `betrieb/kosmo-abholer.service`, und der Waechter darueber prueft, dass es die
#: Datei gibt. In der Kopie gab es sie nicht.
MITKOPIEREN = ("tests", "src", "tools", "docs", "auftraege", "betrieb", "integrations",
               "pyproject.toml", "README.md", "NOTICE", "CLAUDE.md", "LICENSE")


def _kopiere(wurzel: Path, ziel: Path) -> None:
    for teil in MITKOPIEREN:
        quelle = wurzel / teil
        if not quelle.exists():
            continue
        if quelle.is_dir():
            shutil.copytree(quelle, ziel / teil,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(quelle, ziel / teil)


class ProbeError(RuntimeError):
    """Die Probe konnte nicht gemessen werden. **Nicht** dasselbe wie: nichts gefunden."""


def _rote(ziel: Path) -> tuple[set[str], str, int]:
    """Die Suite laufen lassen und die Namen der roten Tests einsammeln.

    Returns:
        ``(namen, ausgabe, gesammelt)`` — die roten Tests, das Protokoll, und wie viele
        Tests überhaupt gelaufen sind.

    Die dritte Zahl ist am 26.08.2026 dazugekommen, und der Anlass ist ein Fehler dieses
    Werkzeugs an sich selbst: Drei neue Testdateien lasen Dateien, die nicht in
    :data:`MITKOPIEREN` standen. In der Arbeitskopie scheiterte das **Einsammeln** — und
    ein Sammelfehler erzeugt keine ``FAILED``-Zeile. Beide Läufe hatten also null rote
    Tests, ihre Differenz war leer, und die Meldung lautete *«Treffer: keine — jede
    geprüfte Sammlung war gefüllt.»*

    **Von zwölf Treffern auf keinen, ohne dass sich an der Suite etwas geändert hätte, und
    das Werkzeug gab Entwarnung.** Das ist genau der Fehler, gegen den es gebaut ist, nur
    eine Ebene höher: aus *nicht gemessen* wurde *in Ordnung*. Gezählt wird darum jetzt
    mit, wie viele Tests wirklich gelaufen sind — und :func:`probe` bricht ab, wenn es zu
    wenige sind.
    """
    lauf = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "--no-header"],
        cwd=ziel, capture_output=True, text=True, check=False)
    ausgabe = lauf.stdout + lauf.stderr
    namen = {z.split(" ")[1] for z in ausgabe.splitlines()
             if z.startswith("FAILED ") and len(z.split(" ")) > 1}
    return namen, ausgabe, _sammelfehler(ausgabe, lauf.returncode)


def _sammelfehler(ausgabe: str, rueckgabe: int) -> str:
    """Der Grund, warum dieser Lauf nichts aussagt — oder ``""``, wenn er etwas aussagt.

    **Warum das Symptom und keine Mindestzahl.** Der erste Entwurf verlangte, dass in der
    Arbeitskopie mindestens 900 Tests laufen. Das war eine gesetzte Zahl, und sie hat
    prompt die **eigenen Tests dieses Werkzeugs** gefällt: Die bauen absichtlich winzige
    Suiten aus zwei, drei Tests. Eine Schranke, die den Normalfall trifft, ist keine.

    Gefragt ist stattdessen genau das, was wirklich passiert ist: Ein **Sammelfehler**.
    Er ist an pytest exakt ablesbar — Rückgabewert 2 heisst abgebrochen, und
    ``ERROR``-Zeilen nennen die Datei. Beides ist von einem gewöhnlichen roten Test
    unterscheidbar, und beides ist unabhängig von der Grösse der Suite.
    """
    if any(z.startswith("ERROR ") for z in ausgabe.splitlines()):
        return "pytest meldet ERROR-Zeilen (Sammelfehler, kein roter Test)"
    if rueckgabe == 2:
        return "pytest wurde abgebrochen (Rückgabewert 2)"
    if not re.search(r"\d+ (?:passed|failed|skipped)", ausgabe):
        return "kein einziger Test ist gelaufen"
    return ''


def probe(wurzel: Path, ziel: Path) -> dict:
    """Zweimal laufen lassen: einmal unverändert, einmal umgeschrieben.

    **Die Nullprobe ist der Punkt.** Ein Test, der schon vorher rot war, ist kein
    Vakuumtreffer — er ist einfach rot. Die erste Fassung dieses Werkzeugs zählte jeden
    roten Test mit, sobald irgendwo im Protokoll das Wort ``VAKUUM`` auftauchte, und
    meldete am 20.08.2026 **19 Treffer statt 6**: dreizehn davon waren Lexikon-Tests, die
    nur scheiterten, weil ``docs/`` nicht mitkopiert wurde.

    Ein Werkzeug, das schwache Tests sucht und selbst über-meldet, verliert seinen Zweck
    beim ersten Fehlalarm. Gezählt wird darum nur, was **erst durch das Umschreiben** rot
    wird.
    """
    _kopiere(wurzel, ziel / "vorher")
    vorher, protokoll_vorher, grund = _rote(ziel / "vorher")
    if grund:
        raise ProbeError(
            f"Die Arbeitskopie liess sich nicht messen: {grund}. Das ist mit ziemlicher "
            f"Sicherheit eine Datei, die ein Test liest und die nicht in MITKOPIEREN "
            f"steht — dann gehoert sie dorthin. **Es ist ausdruecklich KEIN Ergebnis "
            f"'null Treffer':** Eine Probe, die nicht laufen konnte, hat nichts "
            f"geprueft.\n\nLetzte Zeilen des Protokolls:\n"
            + "\n".join(protokoll_vorher.splitlines()[-25:]))

    _kopiere(wurzel, ziel / "nachher")
    umgeschrieben = sum(schreibe_um(d)
                        for d in sorted((ziel / "nachher" / "tests").glob("test_*.py")))
    nachher, ausgabe, _ = _rote(ziel / "nachher")

    return {
        "umgeschrieben": umgeschrieben,
        "treffer": sorted(nachher - vorher),
        "schon_vorher_rot": sorted(vorher),
        "ausgabe": ausgabe,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--wurzel", default=".", help="Projektwurzel (Vorgabe: hier)")
    p.add_argument("--zeige-kopie", action="store_true",
                   help="Arbeitsverzeichnis behalten statt aufräumen")
    a = p.parse_args(argv)

    wurzel = Path(a.wurzel).resolve()
    ordner = Path(tempfile.mkdtemp(prefix="vakuumprobe-"))
    try:
        try:
            befund = probe(wurzel, ordner)
        except ProbeError as fehler:
            # Rueckgabewert 2 und nicht 1: Ein Treffer (1) ist ein BEFUND, eine
            # nicht durchgefuehrte Probe (2) ist gar keiner. Wer beides gleich
            # behandelt, hat wieder den Fall, der dieses Werkzeug ueberhaupt
            # noetig gemacht hat.
            print("PROBE NICHT DURCHGEFUEHRT — das ist weder bestanden noch "
                  "durchgefallen.\n")
            print(fehler)
            return 2
        print(f"Umgeschriebene Stellen: {befund['umgeschrieben']}")
        if befund["schon_vorher_rot"]:
            print(f"Schon vor dem Umschreiben rot (NICHT gezählt): "
                  f"{len(befund['schon_vorher_rot'])}")
            for t in befund["schon_vorher_rot"]:
                print(f"  · {t}")
        if not befund["treffer"]:
            print("Treffer: keine — jede geprüfte Sammlung war gefüllt.")
            return 0
        print(f"Treffer: {len(befund['treffer'])}\n")
        for t in befund["treffer"]:
            print(f"  {t}")
        print("\nEin Treffer ist KEIN Fehler, sondern eine schwache Stelle. Prüfe, ob es")
        print("eine Gegenprobe gibt — einen Test, der am selben Mechanismus zeigt, dass")
        print("sich die Sammlung im umgekehrten Fall füllt. Wenn nicht: schreib eine.")
        return 1
    finally:
        if a.zeige_kopie:
            print(f"\nArbeitsverzeichnis behalten: {ordner}")
        else:
            shutil.rmtree(ordner, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
