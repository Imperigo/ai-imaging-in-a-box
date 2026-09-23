"""Die Abschrift der App gegen den Server: **«gestreckt» entscheidet auf beiden Seiten gleich.**

Die App zeigt die Unterlage unter dem Blatt so, wie die HomeStation die Skizze darauf setzt
— Blatt auf Bild, bei anderem Seitenverhältnis gestreckt. Ob gestreckt wird, rechnet sie
selbst nach: ``Blattunterlage.gestreckt`` in ``ipad/Visbox.swiftpm/Kern/Blattunterlage.swift``
ist **abgeschrieben** aus :func:`aiimaging.arbeitsgang.setze_auf_unterlage` (Welle 2b,
23.09.2026). Die Kernprobe der App (``BlattunterlageTests.testGestrecktFaelltWieBeimServer``)
prüft die Abschrift nur gegen Zahlen, die in ihr selbst stehen. Bis zum 23.09.2026 hielt
**kein** Wächter die Abschrift gegen den Server (Durchsicht der Welle 2b): Änderte eine Seite
die Schwelle, zeigte die App «nicht gestreckt», während der Server streckte — gezeichnet
würde dann nicht, wo gerechnet wird.

**Wie geprüft wird.** Die Server-Seite **läuft**: ``setze_auf_unterlage`` wird mit einer
Skizze in der Grösse des App-Blattes und einer Reihe von Unterlagen aufgerufen, und
gelesen wird ihr ``gestreckt``. Die Swift-Seite wird **aus der Quelle gelesen** — hier gibt
es keinen Swift-Übersetzer, auf den sich eine Python-Probe verlassen dürfte. Gelesen werden
die Zeilen des Rumpfs von ``gestreckt`` (die Zuweisungen und das ``return``) und die
Blattgrösse aus ``Kern/Ebenen.swift``; ausgewertet werden sie mit einem kleinen Auswerter,
der nur Ganzzahlen, Kommazahlen, ``abs``, ``Double(…)``, die vier Rechenarten und
Vergleiche kennt. Das ist eine Abschrift-Probe, wie ``PruefzeichenTests`` ``kette.py`` liest:
Sie hält den **Text** der Abschrift gegen die **Wirkung** des Originals.

Die Unterlagen sind klein (wenige Dutzend bis Hunderte Bildpunkte), weil die Regel nur
die Grössen sieht, nicht die Bildpunkte; das Blatt hat seine volle Grösse, damit beide
Seiten mit **denselben** Zahlen rechnen. Unter den Fällen liegen zwei genau auf der Grenze
(Abweichung gleich einem Prozent — nicht gestreckt) und mehrere zwischen einem und zwei
Prozent: Eine Schwelle, die sich auf einer Seite verschiebt, trennt dort die beiden Seiten.

Ohne GPU, ohne Swift. Regel 3: alles hier entsteht aus ein paar Bytes.
"""
from __future__ import annotations

import ast
import re
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, bildschreiben

WURZEL = Path(__file__).resolve().parents[1]
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"
BLATTUNTERLAGE = KERN / "Blattunterlage.swift"
EBENEN = KERN / "Ebenen.swift"

#: Die Unterlagen (Breite, Höhe). Beim Blatt 1536 × 1024 (3 : 2, Stand 23.09.2026):
#: ``(100, 66)`` und ``(300, 202)`` liegen **genau** auf der Grenze (Abweichung = 1 %),
#: ``(148, 100)``, ``(152, 100)``, ``(98, 66)``, ``(300, 203)`` zwischen 1 und 2 %,
#: ``(149, 100)``, ``(151, 100)`` knapp darunter. Welche Seite «gestreckt» sagt, legt die
#: Probe **nicht** fest — sie verlangt nur, dass beide dasselbe sagen, und dass beide
#: Antworten vorkommen.
UNTERLAGEN = [(150, 100), (3, 2), (96, 64), (149, 100), (148, 100), (151, 100), (152, 100),
              (100, 66), (100, 67), (100, 68), (98, 66), (99, 66), (300, 202), (300, 203),
              (300, 198), (100, 100), (192, 108), (64, 96), (1, 1)]


# ======================================================================================
# Die Swift-Seite, aus der Quelle gelesen
# ======================================================================================

def _rumpf_von_gestreckt() -> str:
    """Der Rumpf von ``public var gestreckt: Bool? { … }`` — bis zur schliessenden Klammer
    auf derselben Einrückung."""
    text = BLATTUNTERLAGE.read_text(encoding="utf-8")
    kopf = re.search(r"^(?P<einzug>[ \t]*)public var gestreckt: Bool\? \{\n", text, re.M)
    assert kopf, "Blattunterlage.gestreckt nicht gefunden — die Abschrift ist umgezogen"
    ende = text.index("\n" + kopf.group("einzug") + "}", kopf.end())
    return text[kopf.end():ende]


def _blattgroesse() -> dict[str, int]:
    """``Ebenenstapel.blattBreite`` und ``blattHoehe`` aus ``Kern/Ebenen.swift``."""
    text = EBENEN.read_text(encoding="utf-8")
    werte = {}
    for name in ("blattBreite", "blattHoehe"):
        treffer = re.findall(rf"static let {name}\s*=\s*(\d+)\s*$", text, re.M)
        assert len(treffer) == 1, f"{name}: {treffer}"
        werte[f"Ebenenstapel.{name}"] = int(treffer[0])
    return werte


_ERLAUBT = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Call, ast.Name,
            ast.Constant, ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub,
            ast.Gt, ast.GtE, ast.Lt, ast.LtE)


def _werte_aus(ausdruck: str, namen: dict):
    """Ein Swift-Ausdruck aus der Abschrift, ausgewertet — **nur** Rechnen und Vergleichen.

    ``Double(x)`` wird zu ``float(x)`` (Swift rechnet dort in doppelter Genauigkeit wie
    Python), ``Ebenenstapel.blattBreite`` zu einem Namen. Alles andere als die erlaubten
    Knoten bricht ab: Die Probe liest Quelltext, sie führt keinen aus."""
    py = ausdruck.replace("Ebenenstapel.", "Ebenenstapel_").replace("Double(", "float(")
    baum = ast.parse(py.strip(), mode="eval")
    for knoten in ast.walk(baum):
        assert isinstance(knoten, _ERLAUBT), f"unerwartet in der Abschrift: {ast.dump(knoten)}"
        if isinstance(knoten, ast.Call):
            assert isinstance(knoten.func, ast.Name) and knoten.func.id in ("abs", "float")
        if isinstance(knoten, ast.Constant):
            assert type(knoten.value) in (int, float), knoten.value
    umgebung = {k.replace("Ebenenstapel.", "Ebenenstapel_"): v for k, v in namen.items()}
    umgebung.update(abs=abs, float=float)
    return eval(compile(baum, str(BLATTUNTERLAGE), "eval"), {"__builtins__": {}}, umgebung)


def swift_gestreckt(breite: int, hoehe: int) -> bool:
    """Was die App bei einer Unterlage ``breite × hoehe`` sagt — **aus ihrer Quelle**.

    Gelesen werden, in ihrer Reihenfolge: ``guard let a = breite, let b = hoehe``, jede
    Zeile ``let x = …`` und ``return …``. Andere Zeilen (Kommentare, Leerzeilen) zählen
    nicht; eine unbekannte Anweisung bricht ab, statt still übergangen zu werden."""
    namen: dict = {"breite": breite, "hoehe": hoehe, **_blattgroesse()}
    for zeile in _rumpf_von_gestreckt().splitlines():
        zeile = zeile.split("//")[0].strip()
        if not zeile:
            continue
        waechter = re.fullmatch(r"guard (.+) else \{ return nil \}", zeile)
        if waechter:
            for teil in waechter.group(1).split(","):
                ziel, quelle = re.fullmatch(r"\s*let (\w+) = (\w+)\s*", teil).groups()
                namen[ziel] = namen[quelle]
            continue
        zuweisung = re.fullmatch(r"let (\w+) = (.+)", zeile)
        if zuweisung:
            namen[zuweisung.group(1)] = _werte_aus(zuweisung.group(2), namen)
            continue
        rueckgabe = re.fullmatch(r"return (.+)", zeile)
        assert rueckgabe, f"unbekannte Zeile in gestreckt: {zeile!r}"
        ergebnis = _werte_aus(rueckgabe.group(1), namen)
        assert isinstance(ergebnis, bool), ergebnis
        return ergebnis
    raise AssertionError("gestreckt ohne return")


# ======================================================================================
# Die Server-Seite, gefahren
# ======================================================================================

def _leere_skizze(pfad: Path, breite: int, hoehe: int) -> Path:
    """Ein durchsichtiges RGBA-PNG in der Grösse des Blattes — wie ein leeres Blatt der App."""
    zeile = b"\x00" + b"\x00" * (4 * breite)

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(zeile * hoehe)) + block(b"IEND", b""))
    return pfad


@pytest.fixture(scope="module")
def server_gestreckt(tmp_path_factory):
    """``gestreckt`` aus :func:`arbeitsgang.setze_auf_unterlage`, je Unterlage — mit einer
    Skizze in der Grösse des App-Blattes (aus ``Ebenen.swift``, nicht hier eingeschrieben)."""
    ordner = tmp_path_factory.mktemp("abschrift")
    blatt = _blattgroesse()
    skizze = _leere_skizze(ordner / "blatt.png", blatt["Ebenenstapel.blattBreite"],
                           blatt["Ebenenstapel.blattHoehe"])
    antworten = {}
    for breite, hoehe in UNTERLAGEN:
        unterlage = bildschreiben.schreibe_farb_png(
            ordner / f"u-{breite}x{hoehe}.png", [(90, 120, 150)] * (breite * hoehe),
            breite, hoehe)
        ergebnis = arbeitsgang.setze_auf_unterlage(skizze, ordner / "e.png",
                                                   unterlage=unterlage)
        assert (ergebnis["breite"], ergebnis["hoehe"]) == (breite, hoehe)
        antworten[(breite, hoehe)] = ergebnis["gestreckt"]
    return antworten


# ======================================================================================
# Die Proben
# ======================================================================================

@pytest.mark.parametrize("breite,hoehe", UNTERLAGEN)
def test_app_und_server_entscheiden_gestreckt_gleich(server_gestreckt, breite, hoehe):
    """Je Unterlage: Was der Server tut, sagt die App voraus."""
    assert swift_gestreckt(breite, hoehe) == server_gestreckt[(breite, hoehe)]


def test_die_reihe_trennt_wirklich(server_gestreckt):
    """Die Probe selbst: Beide Antworten kommen vor, und die Grenzfälle liegen dort, wo die
    Reihe sie behauptet — sonst hiesse «gleich» nur, dass nichts gefragt wurde.

    Genau auf der Grenze (Abweichung gleich einem Prozent) heisst es **nicht** gestreckt
    (``>``, nicht ``>=``); zwischen einem und zwei Prozent gestreckt."""
    antworten = set(server_gestreckt.values())
    assert antworten == {True, False}
    assert server_gestreckt[(100, 66)] is False and server_gestreckt[(300, 202)] is False
    assert all(server_gestreckt[f] is True for f in [(148, 100), (152, 100), (98, 66)])
    assert server_gestreckt[(150, 100)] is False and server_gestreckt[(100, 100)] is True


def test_der_leser_liest_die_abschrift_und_nicht_nichts():
    """Der Leser der Swift-Seite: Er findet die Blattgrösse und im Rumpf ein ``return`` mit
    der Schwelle — und ohne Grösse (``nil``) gibt es kein Urteil (die dritte Antwort ist in
    der App ``nil`` und wird hier nicht gelesen, nur ihr Wächter ``guard … else { return
    nil }``)."""
    blatt = _blattgroesse()
    assert blatt["Ebenenstapel.blattBreite"] > 0 and blatt["Ebenenstapel.blattHoehe"] > 0
    rumpf = _rumpf_von_gestreckt()
    assert re.search(r"guard let \w+ = breite, let \w+ = hoehe else \{ return nil \}", rumpf)
    assert re.search(r"^\s*return .*\d", rumpf, re.M)
