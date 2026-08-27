"""``betrieb/*.service`` — die eingecheckte Fassung gegen die eingebaute gehalten.

Der Befund, der diese Datei nötig gemacht hat (27.08.2026)
----------------------------------------------------------
``betrieb/kosmo-abholer.service`` trug seit dem 26.08. den Schalter ``--eigener-store``,
und ``docs/EINBAU_STAND.md`` führte Posten **B8** seither als erledigt. Die wirklich
eingebaute Nutzereinheit stammte vom **20.08.** und kannte den Schalter nicht. Ein über
den MCP-Einlass bestellter Render blieb also weiter liegen — nur stand jetzt in der
Buchführung, es sei behoben.

*Das ist die unangenehmste Sorte Fehler:* Nicht «kaputt und gemeldet», sondern «kaputt
und als heil verbucht». Wer nachsieht, liest die Buchführung und hört auf zu suchen.

Warum die vorhandenen Wächter das nicht sahen
----------------------------------------------
``test_einbau_stand.py`` prüft, ob ein als erledigt geführter Posten einen **Beleg
nennt, den es gibt**. Den gab es: ``betrieb/kosmo-abholer.service`` lag da und trug den
Schalter. Der Wächter sieht ins **Repo** — und die Einheit, die läuft, steht woanders.

    Eine Datei im Repo belegt, was jemand geschrieben hat.
    Sie belegt nicht, was auf dem Gerät läuft.

Die Ursache war der Platzhalter
--------------------------------
Die eingecheckte Fassung trug dreimal ``/home/<nutzer>/`` mit der Anweisung, das vor dem
Installieren von Hand zu ersetzen — eingeführt am 26.08., um Regel 3 zu genügen. Damit
war jede installierte Einheit eine **von Hand abgeschriebene Kopie**, und ab dem
Abschreiben eine andere Datei. Sie holt sich keine Änderung mehr ab.

Behoben ist das an der Wurzel: ``%h`` ist systemds eigener Platzhalter für das
Heimatverzeichnis und wird beim Laden aufgelöst. Kein Name im Repo, und nichts, was von
Hand zu ersetzen wäre — also auch nichts, was auseinanderlaufen kann.

Was hier geprüft wird
---------------------
* **Kein Platzhalter in einer Direktive.** In Kommentaren darf über ``<nutzer>`` geredet
  werden (dieser Absatz tut es auch); in einer wirksamen Zeile ist er ein Bauteil, das
  Handarbeit verlangt.
* **Eingebaut deckt sich mit eingecheckt** — für jede Einheit, die auf diesem Gerät
  wirklich installiert ist. Nicht installierte werden übersprungen: Ein Wächter, der auf
  einem fremden Rechner rot wird, wird abgeschaltet statt gelesen.
* **Jede Hilfe eines Schalters ist eine gültige Formatzeichenkette.** Der Grund steht bei
  :func:`test_jede_argparse_hilfe_ist_formatierbar`.

Regel 3: Diese Datei schreibt **keinen** Pfad in ihre Meldungen. Verglichen wird an
absoluten Pfaden — gesagt wird nur der Dateiname.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
BETRIEB = REPO / "betrieb"

#: Wo systemd die Einheiten des Benutzers sucht. ``XDG_CONFIG_HOME`` zuerst, weil ein
#: Gerät es setzen darf; sonst die Vorgabe.
EINHEITEN = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd" / "user"

#: Eine wirksame Zeile: nicht leer, kein Kommentar, kein Abschnittskopf.
_UNWIRKSAM = re.compile(r"^\s*(#|;|\[|$)")

#: Ein von Hand zu ersetzender Platzhalter — spitze Klammern um ein Wort.
#: Bewusst allgemein: ``<nutzer>`` war der erste, aber nicht zwingend der letzte.
PLATZHALTER = re.compile(r"<[a-zA-Z][a-zA-Z0-9_-]*>")


def _einheiten() -> list[Path]:
    return sorted(BETRIEB.glob("*.service")) + sorted(BETRIEB.glob("*.timer"))


def _wirksame_zeilen(text: str) -> list[tuple[int, str]]:
    return [(i, z) for i, z in enumerate(text.splitlines(), 1) if not _UNWIRKSAM.match(z)]


def test_es_gibt_ueberhaupt_einheiten_zu_pruefen():
    """Gegenprobe: Ohne sie wären alle folgenden Tests vakuos grün.

    Ein ``glob``, der nichts findet, macht jede ``for``-Schleife darunter zur leeren
    Zusicherung — dieselbe Falle wie bei Gruppe C in ``test_testgeometrie.py``.
    """
    assert _einheiten(), "betrieb/ enthaelt keine .service/.timer — der Waechter waere leer."


@pytest.mark.parametrize("einheit", _einheiten(), ids=lambda p: p.name)
def test_keine_direktive_verlangt_handarbeit(einheit: Path):
    """Ein Platzhalter in einer Direktive macht jede Installation zur Handkopie."""
    treffer = [(nr, z.strip()) for nr, z in _wirksame_zeilen(einheit.read_text(encoding="utf-8"))
               if PLATZHALTER.search(z)]
    assert not treffer, (
        f"{einheit.name}: {len(treffer)} wirksame Zeile(n) tragen einen Platzhalter, der "
        f"vor dem Installieren von Hand zu ersetzen waere — Zeile(n) "
        f"{', '.join(str(nr) for nr, _ in treffer)}. Genau daran ist die Einheit am "
        f"26.08.2026 auseinandergelaufen. Fuer das Heimatverzeichnis nimmt systemd `%h`; "
        f"das loest es selbst auf und laesst nichts zum Abschreiben uebrig."
    )


@pytest.mark.parametrize("einheit", _einheiten(), ids=lambda p: p.name)
def test_eingebaut_deckt_sich_mit_eingecheckt(einheit: Path):
    """Die eigentliche Naht: Was laeuft, ist was hier steht.

    Uebersprungen, wenn die Einheit auf diesem Geraet nicht installiert ist — auf einem
    Rechner ohne die Dienste ist ihre Abwesenheit kein Fehler.
    """
    eingebaut = EINHEITEN / einheit.name
    if not eingebaut.is_file():
        pytest.skip(f"{einheit.name} ist auf diesem Geraet nicht installiert.")
    if eingebaut.read_text(encoding="utf-8") != einheit.read_text(encoding="utf-8"):
        pytest.fail(
            f"{einheit.name}: die eingebaute Einheit weicht von der eingecheckten ab. "
            f"Die Buchfuehrung in docs/EINBAU_STAND.md belegt sich an der EINGECHECKTEN "
            f"Fassung — solange die beiden auseinanderliegen, belegt sie nichts ueber das "
            f"Geraet. Neu einspielen und `systemctl --user daemon-reload`."
        )


def _hilfetexte(pfad: Path):
    """(Zeile, Hilfetext) jedes ``add_argument(help=...)`` mit auswertbarem Literal."""
    try:
        baum = ast.parse(pfad.read_text(encoding="utf-8"))
    except SyntaxError:
        return
    for knoten in ast.walk(baum):
        if not (isinstance(knoten, ast.Call) and getattr(knoten.func, "attr", "") == "add_argument"):
            continue
        for kw in knoten.keywords:
            if kw.arg != "help":
                continue
            try:
                yield knoten.lineno, ast.literal_eval(kw.value)
            except (ValueError, SyntaxError):
                continue


@pytest.mark.parametrize("skript", sorted((REPO / "tools").glob("*.py")), ids=lambda p: p.name)
def test_jede_argparse_hilfe_ist_formatierbar(skript: Path):
    """Ein nacktes ``%`` in einer Hilfe legt das ganze Werkzeug still.

    **Gemessen am 27.08.2026, und der Fund war teuer.** ``tools/abholen.py`` trug in der
    Hilfe zu ``--zeitdeckel-s`` den Text *«flach innerhalb 1 %, waehrend»*. ``argparse``
    formatiert jede Hilfe mit ``help % params``; ``%,`` ist dort kein gueltiger
    Platzhalter. **Python 3.14 prueft das schon in ``add_argument``**, nicht erst beim
    Anzeigen der Hilfe — das Werkzeug stirbt also beim Start und nicht bei ``--help``.

    Der Dienst lief daraufhin 85-mal in Folge in denselben Absturz, alle 30 Sekunden
    einer, und nahm dabei **keinen einzigen Auftrag** an. Von aussen sah das aus wie ein
    Dienst, den es gibt.

    *Warum ein eigener Test und nicht bloss ``test_abholen_cli.py``:* Der dortige greift
    nur, weil er zufaellig ``main()`` ruft, und er deckt genau ein Skript ab. Dieser hier
    nimmt jedes Werkzeug und nennt die Fundstelle.
    """
    schlecht = []
    for zeile, text in _hilfetexte(skript):
        try:
            text % {}
        except (ValueError, TypeError):
            schlecht.append(zeile)
        except KeyError:
            pass  # `%(default)s` und Verwandte sind gewollt und loesen KeyError aus.
    assert not schlecht, (
        f"{skript.name}: Hilfetext in Zeile {', '.join(str(z) for z in schlecht)} ist "
        f"keine gueltige Formatzeichenkette. Ein wortwoertliches Prozentzeichen wird in "
        f"argparse als `%%` geschrieben. Unter Python 3.14 wirft schon `add_argument` — "
        f"das Werkzeug startet dann ueberhaupt nicht mehr."
    )
