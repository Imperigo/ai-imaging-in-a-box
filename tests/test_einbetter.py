"""Die Einbetter-Registry — Regel 1 in ausführbarer Form.

Der wichtigste Test hier ist der, der DINOv3 aus der Auswahl hält. Er wäre wertlos, wenn
DINOv3 gar nicht in der Registry stünde — darum die Gegenprobe.
"""
from __future__ import annotations

import pytest

from aiimaging import einbetter as e
from aiimaging.lizenzquelle import QUELLE_SEKUNDAER, QUELLE_UNGEPRUEFT, ist_belegt


def test_dinov3_steht_in_der_registry():
    """Gegenprobe gegen einen vakuösen Test: Der Ausschluss muss etwas ausschliessen."""
    assert "dinov3" in e.EINBETTER


def test_dinov3_ist_nicht_zulaessig():
    """Sonderlizenz mit Auflagen ist genau das, was Regel 1 ausschliesst — auch wenn
    kommerzielle Nutzung erlaubt wäre."""
    assert e.EINBETTER["dinov3"].zulaessig is False


def test_waehle_gibt_dinov3_niemals_zurueck():
    """Regel 1 im ausführbaren Pfad, nicht nur in der Doku."""
    assert "dinov3" not in [x.name for x in e.waehle()]


def test_waehle_ohne_filter_zeigt_es_doch():
    """Damit die Registry vollständig einsehbar bleibt — der Ausschluss soll auffindbar sein."""
    assert "dinov3" in [x.name for x in e.waehle(nur_zulaessige=False)]


def test_fordere_zulaessigen_lehnt_dinov3_mit_begruendung_ab():
    """Nicht bloss 'geht nicht' — der Grund muss in der Meldung stehen."""
    with pytest.raises(e.EinbetterError, match="Regel 1"):
        e.fordere_zulaessigen("dinov3")


def test_die_begruendung_nennt_die_drei_auflagen():
    """Wer das später liest, soll die Entscheidung nachvollziehen können ohne zu recherchieren."""
    grund = e.EINBETTER["dinov3"].begruendung
    assert "gated" in grund.lower()
    assert "Built with DINOv3" in grund


@pytest.mark.parametrize("name", [n for n, x in e.EINBETTER.items() if x.zulaessig])
def test_jeder_zulaessige_traegt_eine_erlaubte_lizenz(name):
    """Zulässig und Lizenz dürfen nicht auseinanderlaufen."""
    assert e.EINBETTER[name].lizenz in e.ZUGELASSENE_LIZENZEN


def test_vorgabe_ist_zulaessig_und_nicht_gated():
    """Die Vorgabe muss ohne Antragsverfahren nutzbar sein — sonst ist das Repo nicht nachvollziehbar."""
    v = e.hole(e.VORGABE_EINBETTER)
    assert v.zulaessig and not v.gated and v.lizenz == "Apache-2.0"


def test_unbekannter_einbetter_wird_gemeldet():
    with pytest.raises(e.EinbetterError, match="Unbekannter Einbetter"):
        e.hole("gibt-es-nicht")


def test_lizenzquelle_ist_bei_allen_vermerkt():
    """Ehrlichkeit über den Prüfstand: sekundär belegt ist nicht dasselbe wie geprüft."""
    for x in e.EINBETTER.values():
        assert x.lizenz_quelle and x.lizenz_quelle != ""


def test_dinov3_lizenz_ist_geprueft_nicht_nur_sekundaer():
    """Ein Ausschluss muss besser belegt sein als eine Zulassung.

    Gefragt wird seit dem 18.08.2026 über ``ist_belegt`` statt über eine Textprobe auf
    „geprueft" — dieselbe Vokabel wie in ``backbone`` und ``tiefenschaetzer``, und
    dieselbe, die die Registry selbst benutzt.
    """
    assert ist_belegt(e.EINBETTER["dinov3"].lizenz_quelle)


def _probe(name, lizenz_quelle):
    """Ein synthetischer Eintrag, der nur die Herkunft der Lizenzangabe variiert."""
    return e.Einbetter(name=name, modell_id=f"org/{name}", lizenz="Apache-2.0",
                       zulaessig=True, begruendung="synthetisch", dimension=8,
                       lizenz_quelle=lizenz_quelle)


@pytest.mark.parametrize("quelle", [QUELLE_UNGEPRUEFT, QUELLE_SEKUNDAER])
def test_eine_unbelegte_angabe_wird_als_solche_gemeldet(monkeypatch, quelle):
    """Der Prüfstand gehört in die Antwort, nicht in eine Fussnote.

    Synthetisch statt an einem Namen aus dem Bestand: Ein Test, der eine Namensliste
    festhält, hält einen Schuldenstand fest und wird beim nächsten Beleg zum Hindernis —
    genau das ist in ``test_backbone.py`` passiert (Prüfbericht Abschnitt 5).
    """
    monkeypatch.setitem(e.EINBETTER, "probe", _probe("probe", quelle))

    urteil = e.pruefe_lizenz("probe")
    assert urteil["lizenz_belegt"] is False
    assert urteil["lizenz_hinweis"].startswith("Lizenzangabe")


def test_ein_belegter_vermerk_mit_url_gilt_als_beleg(monkeypatch):
    """Die Gegenprobe — ohne sie wäre die Zusicherung oben vakuös."""
    monkeypatch.setitem(e.EINBETTER, "probe",
                        _probe("probe", "geprueft 2026-08-18 (https://example.invalid/mk)"))

    urteil = e.pruefe_lizenz("probe")
    assert urteil["lizenz_belegt"] is True
    assert urteil["lizenz_hinweis"] is None


def test_die_belegfrage_ist_von_der_zulaessigkeit_getrennt():
    """Ein Ausschluss ist kein Prüfstand: DINOv3 ist belegt UND unzulässig.

    Beides in ein Feld zu ziehen wäre die verlockende Abkürzung — und würde die Frage
    „wie gut wissen wir das?" hinter der Frage „dürfen wir das?" verschwinden lassen.
    """
    urteil = e.pruefe_lizenz("dinov3")
    assert urteil["zulaessig"] is False
    assert urteil["lizenz_belegt"] is True
