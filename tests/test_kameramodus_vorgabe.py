"""Der Runner hatte eine **eigene** Kameravorgabe — fünf Tage lang die falsche.

**Der Befund kommt vom Owner** (28.08.2026): *«wenn der local worker nun einen demolauf
macht ist die kamera vom endbild … nicht auf augenhöhe mensch … wieso?»*

Nachgemessen an zwei Blender-Berichten: `modus: gekippt`, `shift_y: 0.0` — obwohl
`kameras.kamerasatz` seit dem **23.08.2026** auf `MODUS_SHIFT` steht. Der Owner hatte den
Wechsel an diesem Tag entschieden, unter der Bedingung, dass `auf-33` das Verhalten am
Gerät bestätigt; es hat, in fünf Fällen.

**Der Commit, der die Vorgabe wechselte, hat den Runner nicht angefasst.** Dort stand seit
dem 21.08. — und da zu Recht — ein `or kameras.MODUS_GEKIPPT`. Aus einer richtigen Zeile
wurde durch einen Entscheid an anderer Stelle eine falsche, und nichts hat es gemeldet.

*Eine Vorgabe, die an zwei Stellen steht, geht beim nächsten Entscheid wieder auseinander —
und es fällt niemandem auf, weil beide Stellen für sich schlüssig aussehen.*
"""
from __future__ import annotations

import re
from pathlib import Path

from aiimaging import kameras

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")


def test_die_bibliothek_traegt_den_entscheid_vom_23_august():
    """Die eine Stelle, an der die Vorgabe stehen darf."""
    import inspect
    unterschrift = inspect.signature(kameras.kamerasatz)
    assert unterschrift.parameters["modus"].default == kameras.MODUS_SHIFT


def test_der_runner_traegt_KEINE_eigene_kameravorgabe():
    """**Der Wächter, der am 23.08.2026 gefehlt hat.**

    Geprüft wird die Quelle und nicht das Verhalten: Der Runner läuft nur in Blender, und
    ein Test, der ihn ausführt, gäbe es hier nicht. Die Fehlerart ist aber im Quelltext
    sichtbar — ein Rückfall auf einen der beiden Modi, der die Bibliothek überstimmt.
    """
    quelle = RUNNER.read_text(encoding="utf-8")
    # Kommentare heraus: Der Befund selbst steht als Begründung im Quelltext und darf
    # die Namen nennen, ohne den Wächter auszulösen.
    ohne_kommentar = "\n".join(z.split("#")[0] for z in quelle.splitlines())

    treffer = re.findall(r"or\s+kameras\.MODUS_[A-Z]+", ohne_kommentar)
    assert not treffer, (
        f"Der Runner faellt auf eine eigene Kameravorgabe zurueck: {treffer}. "
        f"Die Vorgabe gehoert in 'kameras.kamerasatz' und NUR dorthin — sonst geht sie "
        f"beim naechsten Entscheid wieder auseinander."
    )


def test_der_runner_reicht_den_modus_nur_durch_wenn_einer_gesetzt_ist():
    """Ohne ``--kamera-modus`` darf der Schlüssel gar nicht erst übergeben werden —
    dann gilt die Vorgabe der Bibliothek, und zwar automatisch."""
    quelle = RUNNER.read_text(encoding="utf-8")
    assert '**({"modus": a.kamera_modus}' in quelle, (
        "Der Modus muss WEGGELASSEN werden, wenn niemand ihn setzt. Ein `modus=None` "
        "waere ebenfalls falsch: `kamerasatz` erwartet dort einen der beiden Namen."
    )


def test_der_gewaehlte_modus_stellt_die_kamera_waagrecht():
    """Was der Entscheid inhaltlich bedeutet — und warum der Owner es im Bild sieht.

    Gemessen am Hochbau (28.08.2026, 192 px): Vorher stand das Blickziel auf **4,50 m**
    bei einem Auge auf 1,45 m — die Kamera schaute steil nach oben, und die senkrechten
    Kanten liefen zusammen. Nachher liegt das Blickziel auf **derselben Höhe wie das
    Auge**, und der Versatz übernimmt (`shift_y` 0,0812 statt 0,0).
    """
    bbox = [[0.0, 0.0, -0.25], [12.0, 9.5, 15.0]]
    geshiftet = kameras.kamerasatz(bbox, kuerzel=["sSE"])["kameras"][0]
    gekippt = kameras.kamerasatz(bbox, kuerzel=["sSE"],
                                 modus=kameras.MODUS_GEKIPPT)["kameras"][0]

    assert geshiftet["modus"] == kameras.MODUS_SHIFT
    assert geshiftet["auge"][2] == geshiftet["blick_auf"][2], (
        "waagrecht heisst: Auge und Blickziel auf derselben Hoehe")
    assert geshiftet["shift_y"] != 0.0, "der Versatz uebernimmt, was die Neigung tat"

    assert gekippt["blick_auf"][2] > gekippt["auge"][2], (
        "die alte Vorgabe schaute nach oben — genau das sieht man im Bild")
    assert gekippt["shift_y"] == 0.0
