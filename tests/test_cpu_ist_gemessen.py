"""Warum der Blender-Lauf auf der CPU rechnet — und warum das im Quelltext stehen muss.

Der Anlass, und er kam von der anderen Maschine
-----------------------------------------------
Neben ``szene.cycles.device = "CPU"`` stand bis zum 06.09.2026 der Kommentar
``# in dieser Umgebung gibt es keine GPU``.

Das ist ein Satz über die **Umgebung**, und er ist nur im Entwicklungscontainer wahr. Auf
der HomeStation steht eine RTX 5090. Dort las ihn jemand, sah eine ungenutzte Karte, und
alles an diesem Kommentar legte nahe umzustellen.

*Ein Kommentar, der eine falsche Tatsache behauptet, lädt zu genau der Änderung ein, die
er verhindern sollte.*

Gemessen wurde dann statt umgestellt, und das Ergebnis widerspricht der Erwartung: OptiX
ist bei den real genutzten 8–128 Samples auf 512 px **langsamer** (fester Anlaufaufwand),
und es verschiebt Kantenpixel der Material-ID-Maske. Ein Wechsel wäre also nicht nur
teurer, er würde auch Zahlen verändern.

Warum die Probe den Quelltext liest und nicht das Verhalten
-----------------------------------------------------------
``bpy`` gibt es im Produkt-venv nicht und darf es nach Regel 2 nicht geben — das Modul
läuft **jenseits der Prozessgrenze**, in Blenders eigenem Interpreter. Von hier aus ist
die Zeile darum nur als Text erreichbar.

Das ist eine echte Einschränkung und keine Bequemlichkeit: Die Probe hält fest, **was
dasteht**, nicht was geschieht. Für einen Kommentar ist das genau richtig — ein Kommentar
*ist* Text. Für das Verhalten daneben ist es das Beste, was diese Seite der Grenze
hergibt.
"""
from __future__ import annotations

import re
from pathlib import Path

QUELLE = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")
TEXT = QUELLE.read_text(encoding="utf-8")

#: Die Zeile selbst — ohne angehängte Begründung. Die Begründung steht darüber, weil sie
#: sechs Zeilen braucht und eine Zeile mit sechs Zeilen Kommentar niemand mehr liest.
ZEILE = re.compile(r'^\s*szene\.cycles\.device = "CPU"\s*(#.*)?$', re.M)


def _begruendung() -> str:
    """Der Kommentarblock unmittelbar über der Zeile."""
    zeilen = TEXT.splitlines()
    for i, z in enumerate(zeilen):
        if ZEILE.match(z):
            block = []
            for vorher in reversed(zeilen[:i]):
                if not vorher.strip().startswith("#"):
                    break
                block.append(vorher)
            return "\n".join(reversed(block))
    return ""


def test_der_lauf_rechnet_weiter_auf_der_cpu():
    """**Das Verhalten bleibt, und das ist der Befund** — nicht die Nebensache dazu.

    Gemessen am 06.09.2026: GPU ist in allen drei Konfigurationen langsamer. Wer hier auf
    ``GPU`` stellt, macht die Kette langsamer *und* verschiebt Zahlen.
    """
    treffer = ZEILE.findall(TEXT)
    assert len(treffer) == 1, (
        f"{len(treffer)} Stellen setzen `cycles.device`. Genau eine soll es sein — zwei "
        f"waeren eine doppelte Vorgabe, und die stille Haelfte gewinnt.")


def test_die_begruendung_ist_eine_messung_und_keine_behauptung_ueber_die_umgebung():
    """**Der eigentliche Wächter.** Er hält nicht die Zeile, sondern ihren Grund.

    Ein Grund, der auf einer Maschine falsch ist, wird auf dieser Maschine widerlegt —
    und dann fällt die richtige Entscheidung mit ihm.
    """
    grund = _begruendung()
    assert grund, "Die Zeile steht ohne jede Begruendung da."
    klein = grund.lower()
    for anker in ("gemessen", "06.09.2026", "langsamer", "material-id"):
        assert anker in klein, (
            f"Der Begruendung fehlt {anker!r}. Sie muss sagen, dass CPU GEMESSEN ist — "
            f"wann, wie viel langsamer die Karte war, und dass ein Wechsel Zahlen "
            f"verschiebt. Ohne diese vier liest der naechste sie als Meinung.")


def test_die_alte_behauptung_steht_nur_noch_als_zitat_da():
    """Sie darf vorkommen — aber als **berichtigter Satz**, nicht als geltender Grund.

    *Einen falschen Satz spurlos zu loeschen, nimmt dem naechsten die Warnung:* Er wuerde
    dieselbe Frage neu stellen und dieselbe Umstellung erwaegen, die hier gemessen und
    verworfen wurde.
    """
    grund = _begruendung()
    if "keine GPU" not in grund:
        return
    assert "Hier stand" in grund or "stand:" in grund, (
        "«keine GPU» darf nur als zitierter, ausdruecklich berichtigter Satz vorkommen — "
        "sonst ist die falsche Behauptung wieder der geltende Grund.")


def test_die_zeile_traegt_keine_kurzbegruendung_mehr_am_zeilenende():
    """Ein Halbsatz am Zeilenende hat genau den Fehler ermöglicht: Er hatte Platz für eine
    Behauptung und keinen für eine Messung."""
    for zeile in TEXT.splitlines():
        treffer = ZEILE.match(zeile)
        if treffer and treffer.group(1):
            raise AssertionError(
                f"Die Zeile traegt wieder einen angehaengten Kommentar: "
                f"{treffer.group(1)!r}. In eine Zeile passt keine Messung, nur eine "
                f"Meinung — und genau so ist der Fehler entstanden.")
