"""Die Naht «Aufs Blatt» — und die Zahl, die in der Meldung falsch steht.

**Der Anlass.** Demolauf 15 und 17 blieben an derselben Stelle stehen: Der Knopf «Aufs
Blatt» wies das Regelergebnis der eigenen Kette ab («mit 1.2 MB zu gross … hier passen
bis 1.0 MB»). Abgelehnt wurde ``Eingang.png`` mit 1 241 264 Byte.

**Was am 03.09.2026 gemessen wurde.** Der Deckel der Gegenstelle vergleicht **Base64-
Zeichen**, nicht Bytes: ``BILD_DECKEL_BASE64_ZEICHEN = 1_048_576``. Drei Bytes werden zu
vier Zeichen, der wirkliche Deckel liegt also bei **786 432 Byte (0.75 MiB)**. Die
Meldung rechnet die gemessene Groesse in Rohbytes um, die Grenze aber nicht — sie nennt
«1.0 MB» und ist damit um den Faktor 4/3 zu hoch. Wer ihr folgt, wird ein zweites Mal
abgewiesen. Genau dieser Fall steht unten als Test.

Von den 66 Nutzbildern, die die Kette bis heute erzeugt hat, liegen 60 (90.9 %) ueber dem
Deckel; der Median liegt bei 1 277 231 Byte. Die Ablehnung war der Normalfall.

Alle Bilder hier sind synthetisch und werden im Test erzeugt (Regel 3).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import bildlesen, bildschreiben  # noqa: E402


def _rauschbild(ziel, breite: int, hoehe: int, seed: int = 11):
    """Rauschen laesst sich kaum komprimieren — so entsteht eine verlaesslich grosse Datei."""
    wuerfel = random.Random(seed)
    farben = [(wuerfel.randrange(256), wuerfel.randrange(256), wuerfel.randrange(256))
              for _ in range(breite * hoehe)]
    return bildschreiben.schreibe_farb_png(ziel, farben, breite, hoehe)


def _flaeche(ziel, breite: int, hoehe: int):
    """Eine einfarbige Flaeche komprimiert sehr gut — verlaesslich klein."""
    return bildschreiben.schreibe_farb_png(ziel, [(30, 60, 90)] * (breite * hoehe),
                                           breite, hoehe)


# ── Die Rechnung, an der die Meldung scheitert ────────────────────────────────────────

def test_drei_bytes_werden_vier_zeichen():
    assert bildschreiben.base64_zeichen(3) == 4
    assert bildschreiben.base64_zeichen(1) == 4      # aufgefuellt
    assert bildschreiben.base64_zeichen(1_241_264) == 1_655_020


def test_der_deckel_in_bytes_ist_drei_viertel_der_zeichenzahl():
    """**Die Zahl, um die es geht.** Nicht 1 000 000 und nicht 1 048 576."""
    assert bildschreiben.BLATT_DECKEL_BASE64_ZEICHEN == 1_048_576
    assert bildschreiben.BLATT_DECKEL_BYTE == 786_432
    assert bildschreiben.BLATT_DECKEL_BYTE * 4 == bildschreiben.BLATT_DECKEL_BASE64_ZEICHEN * 3


def test_wer_der_meldung_folgt_und_auf_1_MB_verkleinert_wird_erneut_abgewiesen(tmp_path):
    """**Der Kern des Befunds, als Probe.**

    Die Meldung sagt «hier passen bis 1.0 MB». Eine Datei knapp unter 1.0 MB passt aber
    nicht: 1 000 000 Byte ergeben 1 333 336 Base64-Zeichen und reissen den Deckel um 27 %.

    Gemessen wird die **Datei**, nicht die Punktzahl — denn base64-kodiert wird die Datei.
    """
    datei = tmp_path / "knapp_unter_1MB.png"
    datei.write_bytes(b"\x00" * 1_000_000)
    befund = bildschreiben.passt_aufs_blatt(datei)
    assert befund["passt"] is False
    assert befund["zeichen"] == 1_333_336
    assert "1.0 MB" in befund["grund"], "der Grund muss die irrefuehrende Zahl benennen"


# ── Die Probe muss widersprechen koennen ──────────────────────────────────────────────

def test_ein_bild_UEBER_der_grenze_wird_weiterhin_abgewiesen(tmp_path):
    """Solange der Deckel steht, muss er auch halten. Eine Pruefung, die alles durchlaesst,
    ist keine."""
    gross = _rauschbild(tmp_path / "gross.png", 700, 500)
    assert gross.stat().st_size > bildschreiben.BLATT_DECKEL_BYTE
    assert bildschreiben.passt_aufs_blatt(gross)["passt"] is False


def test_ein_bild_UNTER_der_grenze_wird_angenommen(tmp_path):
    klein = _flaeche(tmp_path / "klein.png", 400, 300)
    assert klein.stat().st_size < bildschreiben.BLATT_DECKEL_BYTE
    assert bildschreiben.passt_aufs_blatt(klein)["passt"] is True


# ── Die Fassung ───────────────────────────────────────────────────────────────────────

def test_die_fassung_passt_und_die_gegenprobe_bestaetigt_es(tmp_path):
    quelle = _rauschbild(tmp_path / "quelle.png", 700, 500)
    ergebnis = bildschreiben.blattfassung(quelle, tmp_path / "blatt.png")

    assert ergebnis["passt"] is True
    assert ergebnis["verkleinert"] is True
    assert ergebnis["quelle_bytes"] > bildschreiben.BLATT_DECKEL_BYTE
    # Nicht dem Rueckgabewert glauben, sondern die Datei messen:
    assert bildschreiben.passt_aufs_blatt(tmp_path / "blatt.png")["passt"] is True
    _farben, b, h = bildlesen.lies_png_farben(tmp_path / "blatt.png")
    assert (b, h) == (ergebnis["breite"], ergebnis["hoehe"])
    assert b < 700 and h < 500


def test_was_schon_passt_wird_nicht_verkleinert(tmp_path):
    """Eine Fassung, die vorsichtshalber Aufloesung wegwirft, waere schlechter als keine."""
    quelle = _flaeche(tmp_path / "quelle.png", 400, 300)
    ergebnis = bildschreiben.blattfassung(quelle, tmp_path / "blatt.png")
    assert ergebnis["passt"] is True
    assert ergebnis["verkleinert"] is False
    assert ergebnis["versuche"] == 0
    assert (tmp_path / "blatt.png").read_bytes() == quelle.read_bytes()


def test_die_fassung_schummelt_sich_NICHT_unter_den_deckel(tmp_path):
    """**Die zweite Probe, die widersprechen kann.**

    Ein unerreichbarer Deckel muss zu ``passt=False`` fuehren, nicht zu einem Briefmarken-
    bild, das die Frage nicht mehr beantwortet. Wer hier durchwinkt, meldet Erfolg fuer
    ein Bild, das niemand mehr lesen kann.
    """
    quelle = _rauschbild(tmp_path / "quelle.png", 700, 500)
    ergebnis = bildschreiben.blattfassung(
        quelle, tmp_path / "blatt.png", deckel_zeichen=4_000, min_kante=400)
    assert ergebnis["passt"] is False
    assert ergebnis["warnungen"], "ein Fehlschlag ohne Begruendung ist keine Meldung"
    assert "400" in " ".join(ergebnis["warnungen"])


def test_der_eigene_deckel_gilt_auch_wenn_er_kleiner_gesetzt_wird(tmp_path):
    """Der Deckel ist ein Parameter und keine feste Zahl — die Gegenstelle kann ihn
    aendern, ohne dass hier jemand eine Konstante nachzieht."""
    quelle = _rauschbild(tmp_path / "quelle.png", 500, 400)
    ergebnis = bildschreiben.blattfassung(
        quelle, tmp_path / "blatt.png", deckel_zeichen=200_000, min_kante=50)
    assert ergebnis["passt"] is True
    assert (tmp_path / "blatt.png").stat().st_size <= 200_000 // 4 * 3


def test_kastenmittel_mittelt_und_nimmt_nicht_den_naechsten_nachbarn():
    """Ein Render traegt duenne Linien; der naechste Nachbar laesst sie verschwinden."""
    farben = [(0, 0, 0), (100, 100, 100),
              (200, 200, 200), (255, 255, 255)]        # 2x2
    klein = bildschreiben._kastenmittel(farben, 2, 2, 1, 1)
    assert klein == [((0 + 100 + 200 + 255) // 4,) * 3]
    assert klein != [(0, 0, 0)], "das waere der naechste Nachbar"


def test_eine_fehlende_datei_ist_ein_fehler_und_kein_false(tmp_path):
    """`passt=False` hiesse «gemessen und zu gross». Es gab aber nichts zu messen."""
    with pytest.raises(bildschreiben.SchreibError, match="keine Datei"):
        bildschreiben.passt_aufs_blatt(tmp_path / "gibtsnicht.png")


# ── Und die Naht selbst: legt der Abholer die Fassung wirklich ab? ─────────────────────

def test_der_abholer_legt_die_blattfassung_neben_das_bild(tmp_path):
    """Eine Bibliotheksfunktion, die niemand aufruft, repariert die Naht nicht. Der Fall
    vom 03.09.2026 fiel genau deshalb auf: Die Kette wusste von der Grenze nichts."""
    from aiimaging import abholer

    bild = _rauschbild(tmp_path / "Eingang.png", 700, 500)
    abholer._blatt_ablegen(tmp_path, "Eingang", bild)

    import json
    bericht = json.loads((tmp_path / "Eingang_blatt.json").read_text(encoding="utf-8"))
    assert bericht["passt"] is True
    assert bericht["verkleinert"] is True
    assert bericht["blatt_png"] is not None
    assert bildschreiben.passt_aufs_blatt(bericht["blatt_png"])["passt"] is True


def test_passt_das_bild_schon_wird_keine_zweite_datei_angelegt(tmp_path):
    """Zwei Dateien mit demselben Inhalt stiften nur Zweifel, welche gilt."""
    from aiimaging import abholer

    bild = _flaeche(tmp_path / "Eingang.png", 400, 300)
    abholer._blatt_ablegen(tmp_path, "Eingang", bild)

    import json
    bericht = json.loads((tmp_path / "Eingang_blatt.json").read_text(encoding="utf-8"))
    assert bericht["passt"] is True
    assert bericht["verkleinert"] is False
    assert bericht["blatt_png"] is None
    assert not (tmp_path / "Eingang_blatt.png").exists()


def test_ein_fehlschlag_der_blattfassung_kostet_den_lauf_nicht(tmp_path):
    """Das Bild ist da; die Blattfassung ist eine Auskunft ueber die naechste Stufe."""
    from aiimaging import abholer

    abholer._blatt_ablegen(tmp_path, "Eingang", tmp_path / "gibtsnicht.png")  # wirft nicht
    assert not (tmp_path / "Eingang_blatt.json").exists()
