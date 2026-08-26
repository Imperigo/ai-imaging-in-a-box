#!/usr/bin/env python3
"""TOTE KANTEN — Code, der gerechnet aussieht und nie gerufen wird.

Der Anlass
----------
**Diese Woche hat das Projekt sieben tote Kanten gefunden, jede einzeln und jede durch
Zufall.** `komposition.py` (1400 Zeilen Fachwissen, von nichts gerufen), `befund.json`
(geschrieben, nie gelesen), der Bauteilwächter, der Maskenanker, die Kompositionsprüfung
auf dem Produktivweg — und dann zwei **eigene**: `bbox_bauwerk` samt
`rahmungsverhaeltnis` und `geometrie_qa.erreichbarkeit`.

Am 25.08.2026 wurde von Hand gezählt: 256 öffentliche Funktionen, 67 vom Produktpfad nicht
gerufen, davon **vier** ohne jeden Ruf. Diese Zählung hätte die beiden eigenen **nicht**
gefunden — sie hatten Tests. Und genau das ist der gefährliche Fall.

Warum «hat Tests, hat keinen Aufrufer» die schlimmste Sorte ist
----------------------------------------------------------------
Eine Funktion ohne jeden Ruf sieht verdächtig aus. Eine Funktion mit gründlichen Tests
sieht **fertig** aus. Sie ist grün, sie hat einen ausführlichen Docstring, sie beantwortet
eine Frage, die jemand gestellt hat — und sie beantwortet sie **nie**, weil kein Lauf sie
je erreicht.

*Die Testsuite ist dann das einzige Programm, das sie benutzt.* Beide Funde von heute
waren von dieser Art, und beide sind von aussen gemeldet worden: Die HomeStation hat
gemessen, was die Kette tut, und dabei bemerkt, was sie nicht tut.

Was dieses Werkzeug tut — und was ausdrücklich nicht
------------------------------------------------------
Es **meldet**, es prüft nicht. Ein Test darauf wären dutzende Fehlalarme: Einstiegspunkte,
MCP-Werkzeuge über eine Registry, Studienläufe und Werkzeugskripte sind zu Recht ungerufen.
*Ein Werkzeug, das schwache Stellen sucht und selbst über-meldet, verliert seinen Zweck
beim ersten Fehlalarm* — dieselbe Regel wie bei der Vakuumprobe.

Gearbeitet wird auf dem **Syntaxbaum**, nicht mit Textsuche: Ein Name in einem Kommentar
oder Docstring zählt nicht als Aufruf.

Die Grenze, und sie ist die wichtige
------------------------------------
Aufgelöst wird über den **blossen Namen**, nicht über den Import. ``foo.bar()`` und
``baz.bar()`` sehen hier gleich aus. Das heisst:

* **Falsch-lebendig ist möglich** — trägt irgendwo sonst ein Objekt ein Attribut desselben
  Namens, gilt die Funktion als gerufen. Dieses Werkzeug meldet also eher **zu wenig**.
* **Falsch-tot ist unwahrscheinlich**, aber nicht ausgeschlossen: Ein Aufruf über
  ``getattr(modul, name)`` mit gebautem Namen ist hier unsichtbar.

Eine Meldung ist darum ein **Anfang einer Untersuchung** und kein Urteil. Wer eine prüft,
sucht den Aufrufer selbst — und trägt sie in :data:`ABSICHTLICH` ein, wenn es keinen geben
soll.

Aufruf
------
``python tools/tote_kanten.py`` — oder mit ``--alle``, um auch die absichtlich
ungerufenen zu sehen.
"""
from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
PRODUKT = WURZEL / "src" / "aiimaging"
TESTS = WURZEL / "tests"
WERKZEUGE = WURZEL / "tools"

#: Funktionen, die **mit Absicht** keinen Produktaufrufer haben — mit dem Grund.
#:
#: Die Liste ist kurz zu halten. Jeder Eintrag ist ein Versprechen, dass jemand
#: nachgesehen hat; eine wachsende Liste ist ein Zeichen dafür, dass hier weggeschaut
#: statt geprüft wird.
ABSICHTLICH: dict[str, str] = {
    "main": "Einstiegspunkt eines Werkzeugskripts",
    "haupt": "Einstiegspunkt eines Werkzeugskripts",
}

#: Dateien, die kein Produktpfad sind: Runner laufen jenseits der Prozessgrenze, und
#: `mcp_server` reicht seine Werkzeuge über eine Registry heraus.
KEIN_PRODUKTPFAD = ("runners/", "mcp_server.py", "mcp_schemas.py")


def _dateien(ordner: Path) -> list[Path]:
    return sorted(p for p in ordner.rglob("*.py") if "__pycache__" not in p.parts)


def _ist_produktpfad(datei: str) -> bool:
    return not any(teil in datei for teil in KEIN_PRODUKTPFAD)


def _namen_in(knoten) -> set[str]:
    """Jeder Name, der unter ``knoten`` **gelesen** wird.

    ``Name``-Knoten und die Attributnamen von ``Attribute``-Knoten. Kommentare und
    Docstrings kennt der Syntaxbaum nicht als Namen — genau darum wird er benutzt und
    keine Textsuche.
    """
    gefunden: set[str] = set()
    for k in ast.walk(knoten):
        if isinstance(k, ast.Name):
            gefunden.add(k.id)
        elif isinstance(k, ast.Attribute):
            gefunden.add(k.attr)
    return gefunden


def _funktionen(datei: Path) -> tuple[dict, set[str]]:
    """``({name: (zeile, gerufene_namen)}, namen_auf_modulebene)`` einer Datei.

    **Auch die privaten** (``_name``): Sie sind keine toten Kanten, aber sie tragen den
    Weg. Wer nur die öffentlichen verfolgt, verliert die Kette bei jedem Helfer — und
    meldet dann alles dahinter als tot.
    """
    try:
        baum = ast.parse(datei.read_text(encoding="utf-8"))
    except SyntaxError:
        return {}, set()

    funktionen, modulebene = {}, set()
    for knoten in baum.body:
        if isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funktionen[knoten.name] = (knoten.lineno, _namen_in(knoten))
            for schmuck in knoten.decorator_list:
                modulebene |= _namen_in(schmuck)
        elif isinstance(knoten, ast.ClassDef):
            # Methoden werden ueber eine Instanz gerufen; ihr Name allein traegt zu
            # wenig. Was sie RUFEN, zaehlt trotzdem — sonst reisst die Kette an jeder
            # Klasse ab.
            modulebene |= _namen_in(knoten)
        else:
            modulebene |= _namen_in(knoten)
    return funktionen, modulebene


def erhebung() -> dict:
    """Die ganze Zählung in einem Wörterbuch — ohne Ausgabe, damit sie prüfbar ist.

    **Gefragt ist die Erreichbarkeit von einem Einstiegspunkt aus**, nicht «wird der Name
    irgendwo genannt». Der Unterschied ist der ganze Nutzen: Ein Helfer, den nur eine
    ebenfalls tote Funktion ruft, ist selbst tot — und eine Funktion, die ihr eigenes
    Modul von innen benutzt, kann sehr wohl auf dem Produktpfad liegen.

    Einstiegspunkte sind alles, was von **aussen** hereinruft: die Werkzeugskripte unter
    ``tools/``, die Runner jenseits der Prozessgrenze, und die über eine Registry
    herausgereichten MCP-Werkzeuge.
    """
    produktdateien = _dateien(PRODUKT)

    definiert: dict[str, list[tuple[str, int]]] = defaultdict(list)
    ruft: dict[str, set[str]] = defaultdict(set)
    wurzeln: set[str] = set()

    for datei in produktdateien:
        kurz = str(datei.relative_to(WURZEL))
        funktionen, modulebene = _funktionen(datei)
        aussenkante = not _ist_produktpfad(kurz)
        for name, (zeile, gerufen) in funktionen.items():
            definiert[name].append((kurz, zeile))
            ruft[name] |= gerufen
            if aussenkante:
                # Runner und MCP-Werkzeuge werden von aussen gerufen — von Blender, von
                # einer Registry. Sie sind Einstiegspunkte und keine toten Kanten.
                wurzeln.add(name)
        # Was auf Modulebene steht, wird beim Import ausgefuehrt: Tabellen, Schmuck,
        # Klassenkoerper. Das sind Wurzeln.
        wurzeln |= modulebene

    # Was die Werkzeugskripte rufen, ist der Produktpfad schlechthin: `tools/abholen.py`
    # IST die Kette, wie ein Mensch sie startet.
    for datei in _dateien(WERKZEUGE):
        baum_namen = _namen_in(ast.parse(datei.read_text(encoding="utf-8")))
        wurzeln |= baum_namen

    # Erreichbarkeit — Breitensuche ueber die Namen.
    erreicht: set[str] = set()
    rand = [n for n in wurzeln if n in definiert]
    while rand:
        name = rand.pop()
        if name in erreicht:
            continue
        erreicht.add(name)
        rand.extend(k for k in ruft.get(name, ()) if k in definiert and k not in erreicht)

    in_tests = set()
    for datei in _dateien(TESTS):
        in_tests |= _namen_in(ast.parse(datei.read_text(encoding="utf-8")))

    oeffentlich = {n: orte for n, orte in definiert.items() if not n.startswith("_")}
    nur_tests, nirgends, absichtlich = [], [], []
    for name, orte in sorted(oeffentlich.items()):
        if name in erreicht:
            continue
        eintrag = {"name": name, "orte": orte, "getestet": name in in_tests}
        if name in ABSICHTLICH:
            eintrag["grund"] = ABSICHTLICH[name]
            absichtlich.append(eintrag)
        elif name in in_tests:
            nur_tests.append(eintrag)
        else:
            nirgends.append(eintrag)

    return {"n_definitionen": len(oeffentlich), "n_erreicht": len(erreicht),
            "nur_tests": nur_tests, "nirgends": nirgends, "absichtlich": absichtlich}


def _nach_modul(eintraege) -> dict:
    """Nach Modul gruppiert. Eine Liste von achtzig Namen liest niemand; eine Karte schon.

    Und die Gruppierung ist selbst eine Auskunft: Häufen sich die Meldungen in **einem**
    Modul, ist es ein ungenutztes Modul und keine Sammlung von Einzelfällen. Genau so sah
    `komposition.py` aus, bevor es am 23.08.2026 auffiel — 1400 Zeilen, von nichts
    gerufen.
    """
    karte = defaultdict(list)
    for eintrag in eintraege:
        karte[eintrag["orte"][0][0]].append(eintrag)
    return dict(sorted(karte.items(), key=lambda kv: (-len(kv[1]), kv[0])))


def _gruppe(titel: str, erklaerung: list[str], eintraege) -> None:
    print(f"{titel} ({len(eintraege)}):")
    for zeile in erklaerung:
        print(f"  {zeile}")
    if not eintraege:
        print("  (keine)")
        return
    for datei, gruppe in _nach_modul(eintraege).items():
        markierung = "  ← ganzes Modul?" if len(gruppe) >= 8 else ""
        print(f"\n  {datei}  ({len(gruppe)}){markierung}")
        for eintrag in gruppe:
            print(f"      {eintrag['name']}:{eintrag['orte'][0][1]}")
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--alle", action="store_true",
                    help="auch die absichtlich ungerufenen zeigen")
    a = ap.parse_args(argv)

    ergebnis = erhebung()
    print(f"Oeffentliche Funktionen auf Modulebene: {ergebnis['n_definitionen']}")
    print(f"Von einem Einstiegspunkt aus erreichbar: {ergebnis['n_erreicht']} "
          f"(oeffentliche und private zusammen)")
    print()

    _gruppe(
        "NUR UEBER TESTS ERREICHBAR — die gefaehrliche Sorte",
        ["Gruen, gruendlich geprueft, mit ausfuehrlichem Docstring — und kein Lauf",
         "erreicht sie je. Die Testsuite ist das einzige Programm, das sie benutzt.",
         "Studien- und Analysemodule stehen zu Recht hier; ein Modul des Produktpfads",
         "nicht."],
        ergebnis["nur_tests"])

    _gruppe(
        "VON KEINEM EINSTIEGSPUNKT ERREICHBAR UND UNGETESTET",
        ["Auch kein Test nennt sie. Ungeprueft ist schlimmer als ungerufen — wer sie",
         "behaelt, gibt ihr wenigstens eine Pruefung."],
        ergebnis["nirgends"])

    if a.alle and ergebnis["absichtlich"]:
        print(f"ABSICHTLICH OHNE AUFRUFER ({len(ergebnis['absichtlich'])}):")
        for eintrag in ergebnis["absichtlich"]:
            datei, zeile = eintrag["orte"][0]
            print(f"  {eintrag['name']}  ({datei}:{zeile})  — {eintrag['grund']}")
        print()

    print("Eine Meldung ist der ANFANG einer Untersuchung und kein Urteil. Aufgeloest")
    print("wird ueber den blossen NAMEN und nicht ueber den Import: `foo.bar()` und")
    print("`baz.bar()` sehen hier gleich aus. Dieses Werkzeug meldet darum eher zu WENIG")
    print("als zu viel — was es meldet, ist umso ernster zu nehmen.")
    print()
    print("Wer eine Meldung prueft, sucht den Aufrufer selbst. Gibt es keinen und soll es")
    print("keinen geben, kommt sie mit BEGRUENDUNG in ABSICHTLICH. Eine wachsende Liste")
    print("dort ist ein Zeichen dafuer, dass weggesehen statt geprueft wird.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
