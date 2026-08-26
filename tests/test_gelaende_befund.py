"""Die dritte Antwort, angewandt auf die Geländeregel selbst.

Der Anlass
----------
Die HomeStation hat es am 26.08.2026 aufgeschrieben (`auf-47`), und der Einwand sitzt:

    *«Er verlangt, dass der Besteller VORHER weiss, dass kein Gelände in der Szene ist.
    Bei einer fremden glb weiss er das nicht.»*

Und ihr Vorschlag dazu:

    *«Die Geräteregel könnte ihren Nullbefund selbst belegen, indem sie meldet, WELCHE
    Baustoffe sie geprüft hat. Findet sie 11 Baustoffe und keiner heisst nach Gelände,
    ist das ein anderer Befund als 'keine Baustofftabelle gefunden'.»*

Bis dahin bedeutete ``gelaende_erkannt: False`` beides — geprüft und nichts gefunden,
oder gar nichts zu prüfen gehabt. Beides ergab ``None``, und ``None`` liest sich wie ein
Fehler statt wie eine Enthaltung. **Genau die Verwechslung, die dieses Projekt sonst
überall auseinanderhält.**

Was hier NICHT geprüft wird
---------------------------
Ob die Regel *richtig* urteilt — das steht in ``test_maske.py``. Hier geht es um die
Frage, ob sie sagt, **worauf** ihr Urteil sich stützt.
"""
from __future__ import annotations

import pytest

from aiimaging import maske as m

#: Die elf Baustoffe des zweiten Modells der HomeStation, wörtlich aus ihrem Bericht
#: zu `auf-47`. **Keine erfundenen Namen** — der Fall, um den es geht, ist gemessen.
HOMESTATION_ELF = ["Beton_Decke", "Beton_Kern", "Beton_Querwand", "Beton_Erdbebenwand",
                   "Beton_Treppe", "Holz_Stuetze", "Trennwand_Leichtbau",
                   "Terrassenbelag", "Metall_Fassade", "Metall_Bruestung",
                   "Glas_Fassade"]


# ── Die drei Lagen ───────────────────────────────────────────────────────────────────

def test_elf_benannte_baustoffe_ohne_gelaende_sind_ein_nullbefund():
    """Der gemessene Fall. Er war bis heute von «nichts gelesen» nicht zu unterscheiden."""
    lage = m.gelaende_befund([], HOMESTATION_ELF)
    assert lage["befund"] == m.BEFUND_KEIN_GELAENDE_BELEGT
    assert len(lage["geprueft"]) == 11
    assert "Terrassenbelag" in lage["geprueft"], (
        "Die geprüften Namen müssen mitwandern — ein Nullbefund ohne seine Liste ist "
        "eine Behauptung, mit ihr eine Auskunft."
    )


def test_ein_namenloser_eintrag_macht_den_befund_unentscheidbar():
    """Eine Geländeregel über namenlose Flächen ist keine Regel.

    Und **ein einziger** namenloser Eintrag genügt: Er könnte der Boden sein.
    """
    lage = m.gelaende_befund([], [*HOMESTATION_ELF, ""])
    assert lage["befund"] == m.BEFUND_NICHT_ENTSCHEIDBAR
    assert lage["namenlos"] == 1


def test_der_klumpen_ist_nicht_entscheidbar():
    """Ein einziger Eintrag — die 56-MB-Kontext-IFC mit 502 002 Dreiecken.

    Dort trennt die Maske noch den Himmel ab und sonst nichts. «Kein Gelände gefunden»
    wäre eine Aussage über eine Tabelle, die gar nichts unterscheidet.
    """
    lage = m.gelaende_befund([], ["Bestand_Kontext"])
    assert lage["befund"] == m.BEFUND_NICHT_ENTSCHEIDBAR
    assert str(m.MINDESTENS_BENANNT) in lage["begruendung"]


def test_ein_treffer_der_regel_ist_der_dritte_fall():
    lage = m.gelaende_befund(["Gelaende_Hang"], ["Wand", "Decke"])
    assert lage["befund"] == m.BEFUND_GELAENDE_GEFUNDEN
    assert "Gelaende_Hang" in lage["begruendung"]


def test_die_drei_lagen_schliessen_einander_aus():
    """Sonst wäre die dritte Antwort nur ein weiteres Wort für dieselbe zweite."""
    lagen = {
        m.gelaende_befund(["Gelaende"], ["Wand"])["befund"],
        m.gelaende_befund([], HOMESTATION_ELF)["befund"],
        m.gelaende_befund([], [""])["befund"],
    }
    assert lagen == {m.BEFUND_GELAENDE_GEFUNDEN, m.BEFUND_KEIN_GELAENDE_BELEGT,
                     m.BEFUND_NICHT_ENTSCHEIDBAR}


def test_die_regel_ist_ohne_bild_befragbar():
    """Wer eine glb vor sich hat, soll ohne Render wissen, ob ein Lauf Sinn ergibt."""
    import inspect

    assert "farben" not in inspect.signature(m.gelaende_befund).parameters, (
        "gelaende_befund braucht ein Bild — dann ist die Auskunft erst nach dem Lauf "
        "zu haben, und genau dafür ist sie nicht gedacht."
    )


# ── Und dass die Maske es weitersagt ────────────────────────────────────────────────

@pytest.fixture()
def tabelle_ohne_gelaende():
    """Elf Baustoffe, keiner nach Gelände — mit unterscheidbaren Kennfarben."""
    return [{"name": n, "farbe_srgb_8bit": [10 + 7 * i, 40 + 3 * i, 200 - 5 * i], "quelle": "material"}
            for i, n in enumerate(HOMESTATION_ELF)]


@pytest.fixture()
def bild(tabelle_ohne_gelaende):
    """Ein winziges Bild: die ersten drei Farben plus Hintergrund."""
    farben = [tuple(e["farbe_srgb_8bit"]) for e in tabelle_ohne_gelaende[:3]]
    return [*farben, m.HINTERGRUND_FARBE]


def test_der_befund_der_maske_traegt_die_lage_und_die_namen(bild, tabelle_ohne_gelaende):
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=True)
    assert befund["gelaende_befund"] == m.BEFUND_KEIN_GELAENDE_BELEGT
    assert len(befund["gelaende_geprueft"]) == 11
    assert befund["maske"] is None, (
        "Die Maske fällt weiterhin aus. Ein Nullbefund belegt, dass die REGEL nicht "
        "anschlug — nicht, dass es kein Gelände gibt. Beides fällt nur zusammen, wenn "
        "die Regel vollständig ist, und das ist an einem Lauf nicht messbar."
    )


def test_die_warnung_nennt_die_namen_und_die_abhilfe(bild, tabelle_ohne_gelaende):
    """Sie sagt die ANTWORT statt der Frage — das ist der ganze Unterschied."""
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=True)
    text = " ".join(befund["warnungen"])
    assert "KEIN GELAENDE BELEGT" in text
    assert "Terrassenbelag" in text, "Ohne die Namen bleibt es eine Behauptung."
    assert "--kein-gelaende" in text, "Die Abhilfe in der Form, die ein Betreiber tippt."
    assert "Maskenweg" in text, "Die Folge gehört in denselben Satz wie die Ursache."


def test_bei_unlesbarer_tabelle_steht_der_alte_satz_und_nicht_der_neue():
    """Sonst wäre der Nullbefund nur ein neuer Name für dieselbe Ratlosigkeit."""
    tabelle = [{"name": "", "farbe_srgb_8bit": [10, 20, 30], "quelle": "objekt"},
               {"name": "Wand", "farbe_srgb_8bit": [40, 50, 60], "quelle": "material"}]
    befund = m.bauwerksmaske([(10, 20, 30), m.HINTERGRUND_FARBE], tabelle,
                             gelaende_erwartet=True)
    text = " ".join(befund["warnungen"])
    assert befund["gelaende_befund"] == m.BEFUND_NICHT_ENTSCHEIDBAR
    assert "KEIN GELAENDE BELEGT" not in text
    assert "nicht entscheidbar" in text


def test_mit_der_erklaerung_des_aufrufers_schweigt_die_neue_zeile(bild, tabelle_ohne_gelaende):
    """Selbstlöschend. Eine Zeile, die immer dasteht, verdeckt die echten."""
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=False)
    assert befund["maske"] is not None
    assert "KEIN GELAENDE BELEGT" not in " ".join(befund["warnungen"])
    # Die Lage steht trotzdem im Befund — sie ist eine Messung und keine Meldung.
    assert befund["gelaende_befund"] == m.BEFUND_KEIN_GELAENDE_BELEGT


def test_die_kurzform_nennt_die_geprueften_baustoffe():
    """Der Betreiber sieht die Namen am Terminal, nicht erst in einer Datei."""
    from aiimaging import abholer

    zeilen = abholer.befund_kurz({"kameras": [{
        "kamera": "s", "bild_png": "s.png",
        "maskenbefund": {"maske": None, "grund": "kein Gelaende belegt",
                         "gelaende_befund": m.BEFUND_KEIN_GELAENDE_BELEGT,
                         "gelaende_geprueft": HOMESTATION_ELF},
    }]})
    text = " ".join(zeilen)
    assert "MASKENWEG NICHT GEFAHREN" in text
    assert "11 benannte Baustoffe" in text
    assert "Terrassenbelag" in text


def test_die_kurzform_schweigt_bei_unentscheidbarer_lage():
    """Sonst stünde die Namensliste auch dort, wo es gar keine gibt."""
    from aiimaging import abholer

    zeilen = abholer.befund_kurz({"kameras": [{
        "kamera": "s", "bild_png": "s.png",
        "maskenbefund": {"maske": None, "grund": "nichts gelesen",
                         "gelaende_befund": m.BEFUND_NICHT_ENTSCHEIDBAR,
                         "gelaende_geprueft": []},
    }]})
    text = " ".join(zeilen)
    assert "MASKENWEG NICHT GEFAHREN" in text, "Die Hauptzeile bleibt."
    assert "benannte Baustoffe" not in text
