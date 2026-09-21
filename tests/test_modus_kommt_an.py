"""Was bestellt war und was gerechnet wurde — und dass beides den Leser erreicht.

**Am 21.09.2026 von der HomeStation gemessen** (`auf-20260921-134`): Drei Läufe mit
`qwen-image-edit-2511`, jeder mit einem Ausgangsbild bestellt, alle drei mit derselben
sha256 — das Bild kam nicht an. Und in allen drei Ergebnissen stand `modus_bestellt` und
`modus_gerechnet` auf ``None``.

Die beiden Felder gab es. Der Adapter baute sie, ein langer Kommentar begründete sie
(«ein Hinweis wird gelesen oder nicht; ein Feld lässt sich vergleichen») — und
:func:`aiimaging.render.rendere` las sie nie aus der Antwort. Sie endeten eine Funktion
vor dem Leser.

> *Eine Auskunft, die eine Funktion früher wegwirft, als der Leser sie braucht, gibt es
> für den Leser nicht.*

Dazu der zweite Befund derselben Station (`auf-20260921-130`): Die entscheidende Zeile
stand in `auf-20260919-123` wörtlich da — **als Hinweis unter vier anderen**. Wer Hinweise
überfliegt, sieht ausgerechnet den nicht, der den Lauf entwertet. Darum steht die
Abweichung jetzt **vorne**.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging.render import (
    MODUS_IMAGE_EDIT,
    MODUS_TXT2IMG,
    STATUS_OK,
    RenderAuftrag,
    rendere,
)

PNG_PLATZHALTER = b"\x89PNG\r\n\x1a\n"

ABWEICHUNG = (
    "BESTELLT WAR 'image_edit', GERECHNET WURDE 'txt2img': Das Ausgangsbild ist bei "
    "dieser Pipeline nicht angekommen."
)


@pytest.fixture
def tiefe(tmp_path) -> str:
    pfad = tmp_path / "tiefe_norm.png"
    pfad.write_bytes(PNG_PLATZHALTER)
    return str(pfad)


@pytest.fixture
def anker(tmp_path) -> str:
    pfad = tmp_path / "beauty.png"
    pfad.write_bytes(PNG_PLATZHALTER)
    return str(pfad)


def _auftrag(tiefe, ziel, **kw) -> RenderAuftrag:
    felder = {"depth_png": tiefe, "prompt": "Wohnhaus, Beton und Holz",
              "ausgabe_png": str(ziel)}
    felder.update(kw)
    return RenderAuftrag(**felder)


class Naht:
    """Ein Modell, das antwortet wie der echte Adapter — mit den zwei Modus-Feldern."""

    def __init__(self, **zusatz):
        self.zusatz = zusatz

    def __call__(self, parameter: dict):
        ziel = parameter["ausgabe_png"]
        Path(ziel).write_bytes(PNG_PLATZHALTER)
        return {"bild_png": ziel, "schritte_gerechnet": 8, **self.zusatz}


# --------------------------------------------------------------------------------------
# 1 · Die Felder erreichen das Ergebnis
# --------------------------------------------------------------------------------------

def test_eine_abweichung_steht_im_ergebnis_und_nicht_nur_im_adapter(tiefe, anker, tmp_path):
    """Der Wächter für den gemeldeten Befund: beide Felder kommen an, nicht ``None``."""
    naht = Naht(modus_bestellt=MODUS_IMAGE_EDIT, modus_gerechnet=MODUS_TXT2IMG,
                hinweise=[ABWEICHUNG])

    ergebnis = rendere(_auftrag(tiefe, tmp_path / "bild.png", beauty_png=anker),
                       modell=naht)

    assert ergebnis["status"] == STATUS_OK
    assert ergebnis["modus_bestellt"] == MODUS_IMAGE_EDIT
    assert ergebnis["modus_gerechnet"] == MODUS_TXT2IMG
    assert ergebnis["modus_abweichung"] is True


def test_die_abweichung_steht_vorne_und_nicht_unter_fuenfzehn(tiefe, anker, tmp_path):
    """Ein Hinweis an Position sechzehn ist für den, der überfliegt, keiner."""
    naht = Naht(modus_bestellt=MODUS_IMAGE_EDIT, modus_gerechnet=MODUS_TXT2IMG,
                hinweise=["etwas anderes", ABWEICHUNG, "noch etwas"])

    ergebnis = rendere(_auftrag(tiefe, tmp_path / "bild.png", beauty_png=anker),
                       modell=naht)

    assert ergebnis["hinweise"][0] == ABWEICHUNG
    assert "etwas anderes" in ergebnis["hinweise"], (
        "die uebrigen Hinweise duerfen dabei nicht verlorengehen")
    assert "noch etwas" in ergebnis["hinweise"]


def test_ohne_abweichung_sind_beide_felder_gleich(tiefe, tmp_path):
    naht = Naht(modus_bestellt=MODUS_TXT2IMG, modus_gerechnet=MODUS_TXT2IMG)

    ergebnis = rendere(_auftrag(tiefe, tmp_path / "bild.png"), modell=naht)

    assert ergebnis["modus_bestellt"] == MODUS_TXT2IMG
    assert ergebnis["modus_gerechnet"] == MODUS_TXT2IMG
    assert ergebnis["modus_abweichung"] is False


# --------------------------------------------------------------------------------------
# 2 · Die dritte Antwort: schweigt die Naht, heisst das nicht «war gleich»
# --------------------------------------------------------------------------------------

def test_eine_schweigende_naht_heisst_nicht_gemessen(tiefe, anker, tmp_path):
    """``None`` bei ``modus_gerechnet`` ist **nicht gemessen**, nicht «hat gepasst».

    Der bestellte Modus steht trotzdem da — er kommt aus dem Auftrag und ist immer
    bekannt. Alles andere wäre eine verlorene Auskunft aus reiner Symmetrie.
    """
    naht = Naht()

    ergebnis = rendere(_auftrag(tiefe, tmp_path / "bild.png", beauty_png=anker),
                       modell=naht)

    assert ergebnis["modus_bestellt"] == MODUS_IMAGE_EDIT, (
        "was bestellt war, steht im Auftrag und braucht keine Naht")
    assert ergebnis["modus_gerechnet"] is None
    assert ergebnis["modus_abweichung"] is None, (
        "aus «nicht gemessen» darf kein «keine Abweichung» werden")


def test_auch_ein_blosser_pfad_als_antwort_laesst_den_bestellten_modus_stehen(
        tiefe, anker, tmp_path):
    """Die schmalste Naht: das Modell gibt nur einen Pfad zurück."""
    ziel = tmp_path / "bild.png"

    def schmal(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(PNG_PLATZHALTER)
        return parameter["ausgabe_png"]

    ergebnis = rendere(_auftrag(tiefe, ziel, beauty_png=anker), modell=schmal)

    assert ergebnis["modus_bestellt"] == MODUS_IMAGE_EDIT
    assert ergebnis["modus_gerechnet"] is None
    assert ergebnis["modus_abweichung"] is None
