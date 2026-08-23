"""Der Bauteilwächter auf dem Weg, den ein echter Auftrag nimmt.

**Der Befund, der diese Datei ausgelöst hat.** `prompts.bauteilwaechter` ist die direkte
Antwort auf den teuersten Fehler dieses Projekts: Am 18.08.2026 stand „clean flat roof" im
Prompt für einen oben offenen Quader, und das Bildmodell lieferte ein Dach. Es hat nichts
falsch gemacht — es tat, was dastand.

Seither steht der Wächter in `prompts.py`, geprüft, begründet — und lief bis zum
23.08.2026 auf **keinem einzigen echten Auftrag**. Gerufen wurde er nur von `komponiere`,
und `komponiere` liegt nicht auf dem Weg, den ein Auftrag der Oberfläche nimmt: Der bringt
seinen Prompt roh mit.

Dieselbe Fehlerart wie bei `komposition.py` am selben Tag, und hier ist sie teurer: Es ist
der Wächter gegen genau die Sorte Fehler, die das Projekt begründet hat.
"""
import pytest

from aiimaging import kosmo_szene


def _gelesen(prompt):
    return kosmo_szene.lies_szene({
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "style": {"prompt": prompt},
    })


# ======================================================================================
# Er läuft überhaupt
# ======================================================================================

def test_ein_bauteil_im_prompt_wird_gemeldet():
    gelesen = _gelesen("a house with a large balcony")
    assert "balcony" in gelesen["prompt_bauteile"]
    assert any("Bauteile" in w for w in gelesen["warnungen"])


def test_ein_prompt_ohne_bauteile_erzeugt_keine_warnung():
    """Gegenprobe — sonst stünde die Warnung bei jedem Auftrag und bedeutete nichts.

    Anders als beim Geländestand ist das hier der Normalfall: Ein Stimmungsprompt nennt
    keine Bauteile, und dann soll nichts dastehen.
    """
    gelesen = _gelesen("overcast sky, no people, soft light")
    assert gelesen["prompt_bauteile"] == ()
    assert not any("Bauteile" in w for w in gelesen["warnungen"])


def test_der_hinweis_nennt_den_fall_aus_dem_er_stammt():
    """Ein Hinweis, der nur „Vorsicht" sagt, hilft niemandem beim Abwägen."""
    hinweis = [w for w in _gelesen("with a flat roof")["warnungen"] if "Bauteile" in w][0]
    assert "Halluzination" in hinweis
    assert "18.08.2026" in hinweis, "der gemessene Fall gehört in die Meldung"


# ======================================================================================
# Beide Fassungen — und warum das nicht bloss Gründlichkeit ist
# ======================================================================================

def test_die_uebersetzung_rettet_den_fund_bei_einem_kompositum():
    """Der Fall, der zeigt, warum BEIDE Fassungen geprüft werden.

    Der Wächter kennt „dach" als ganzes Wort. ``Flachdach`` ist ein Kompositum und
    entgeht ihm — die Wortgrenzen sind Absicht, sonst schlüge „Betonung" bei „Beton" an.
    Die Übersetzung macht daraus ``flat roof``, und **dort** greift er.

    Wer nur das Original prüfte, übersähe also genau die Wörter, die der deutschen
    Sprache eigen sind. Wer nur die Übersetzung prüfte, übersähe alles, was gar nicht
    übersetzt wurde.
    """
    from aiimaging import prompts

    assert prompts.bauteilwaechter("Flachdach")["gefunden"] is False
    gelesen = _gelesen("ein Wohnhaus mit Flachdach")
    assert gelesen["prompt"] == "a residential building with flat roof"
    assert "roof" in gelesen["prompt_bauteile"]


def test_ein_deutsches_bauteil_ohne_uebersetzung_wird_trotzdem_gefunden():
    """Die Gegenrichtung — und sie braucht ein Wort, das das Glossar NICHT kennt.

    Der erste Anlauf prüfte „Geländer". Das steht im Glossar, wird zu ``railing``, und
    der Wächter fände es auch in der Übersetzung — der Test überlebte die Mutation
    „prüfe nur die Übersetzung" und zeigte damit gar nichts.

    Der zweite Anlauf prüfte ``Turm`` — nicht im Glossar, bleibt also stehen. Auch das
    zeigte nichts: Ein **unübersetztes** Wort steht anschliessend in beiden Fassungen,
    und die Übersetzung fängt es genauso.

    Gebraucht wird ein Wort, dessen **Übersetzung** der Wächter nicht kennt. Davon gibt
    es genau zwei: ``laibung`` → ``reveal`` und ``dächer`` → ``roofs``. Nur das Original
    fängt sie — und genau dafür werden beide Fassungen geprüft.
    """
    from aiimaging import sprache

    assert sprache.GLOSSAR["laibung"] == "reveal"
    assert "reveal" not in prompts_bauteilwoerter(), "sonst prüft dieser Test nichts"

    gelesen = _gelesen("die Laibung bei bedecktem Himmel")
    assert "reveal" in gelesen["prompt"], "übersetzt — das ist die Voraussetzung"
    assert "laibung" in gelesen["prompt_bauteile"]


def prompts_bauteilwoerter():
    from aiimaging import prompts

    return prompts.BAUTEILWOERTER


def test_jedes_bauteil_steht_nur_einmal_da():
    """Original und Übersetzung nennen dasselbe Wort — die Meldung soll es nicht
    verdoppeln."""
    gelesen = _gelesen("a roof and another roof")
    assert list(gelesen["prompt_bauteile"]).count("roof") == 1


# ======================================================================================
# Bis auf das Terminal des Betreibers
# ======================================================================================

def test_die_bauteile_erreichen_die_kurzfassung():
    """Ein Fund, den niemand sieht, ist kein Fund."""
    from aiimaging import abholer

    zeilen = abholer.befund_kurz({"prompt_bauteile": ["roof", "balcony"]})
    assert len(zeilen) == 1
    assert "roof" in zeilen[0] and "balcony" in zeilen[0]
    assert "Geometrie" in zeilen[0], "die Frage gehört dazu, nicht nur die Wörter"


def test_ohne_bauteile_steht_dazu_nichts_in_der_kurzfassung():
    from aiimaging import abholer

    assert abholer.befund_kurz({"prompt_bauteile": []}) == ()
