"""Die gemeinsame Vokabel für die Herkunft einer Lizenzangabe.

Warum es diese Datei gibt: Bis zum 18.08.2026 führten drei Registries dieselbe Angabe in
drei Schreibweisen — ``backbone`` mit festen Vokabeln, ``einbetter`` und
``tiefenschaetzer`` mit freiem Text. Die Prüflogik in ``backbone`` verglich exakt auf ein
Schlagwort und meldete deshalb frisch belegte Einträge weiter als „NICHT geprüft"
(``docs/LIZENZPRUEFUNG_2026-08-18.md``, Abschnitt 5).

Zwei Sachen werden hier festgehalten:

1. Was ein Beleg ist — beide Formen, und die Fälle, die keiner sind.
2. Dass die drei Registries dieselbe Vokabel benutzen. Ohne diese Probe könnte die
   Aufräumarbeit lautlos wieder auseinanderlaufen, und zwar genau so, wie sie es beim
   ersten Mal getan hat: nicht durch einen Fehler, sondern durch ein zweites Feld mit
   demselben Namen und einem eigenen Wertevorrat.
"""
from __future__ import annotations

import dataclasses

import pytest

from aiimaging import backbone, einbetter, tiefenschaetzer
from aiimaging.lizenzquelle import (
    HERKUNFT_HINWEIS_PRAEFIX,
    QUELLE_GEPRUEFT_PRAEFIX,
    QUELLE_MODELLKARTE,
    QUELLE_SEKUNDAER,
    QUELLE_UNGEPRUEFT,
    hinweis_zur_herkunft,
    ist_belegt,
)

#: Die drei Registries, die das Feld ``lizenz_quelle`` führen — als (Modul, Klasse, Werte).
REGISTRIES = (
    (backbone, backbone.Backbone, backbone.BACKBONES),
    (einbetter, einbetter.Einbetter, einbetter.EINBETTER),
    (tiefenschaetzer, tiefenschaetzer.Tiefenschaetzer, tiefenschaetzer.TIEFENSCHAETZER),
)


def _ist_bekannte_form(quelle: str) -> bool:
    """Eine der drei Vokabeln oder ein Vermerk ``"geprueft <datum> (<url>)"``."""
    return (quelle in (QUELLE_MODELLKARTE, QUELLE_SEKUNDAER, QUELLE_UNGEPRUEFT)
            or quelle.startswith(QUELLE_GEPRUEFT_PRAEFIX))


# --------------------------------------------------------------------------------------
# 1 · Was ein Beleg ist
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("quelle", [
    QUELLE_MODELLKARTE,
    "geprueft 2026-08-18 (https://huggingface.co/org/modell)",
    "geprueft 2026-08-18 (github.com/org/projekt — README, Abschnitt LICENSE)",
])
def test_beide_formen_gelten_als_beleg(quelle):
    """Das Schlagwort sagt DASS geprüft wurde, der Vermerk sagt zusätzlich WOGEGEN."""
    assert ist_belegt(quelle) is True
    assert hinweis_zur_herkunft(quelle) is None


@pytest.mark.parametrize("quelle", [
    QUELLE_UNGEPRUEFT,
    QUELLE_SEKUNDAER,
    "",
    "geprueft",          # ohne Angabe, wogegen — die Vorsilbe verlangt den Nachsatz
    "ungeprueft 2026-08-18",
    "wird noch geprueft",
])
def test_was_kein_beleg_ist_gilt_auch_nicht_als_einer(quelle):
    """Die zurückhaltende Antwort ist hier die richtige: im Zweifel nicht belegt."""
    assert ist_belegt(quelle) is False
    assert hinweis_zur_herkunft(quelle).startswith(HERKUNFT_HINWEIS_PRAEFIX)


@pytest.mark.parametrize("quelle", [None, 42, ("geprueft 2026-08-18",)])
def test_eine_kaputte_angabe_ist_kein_beleg_und_kein_absturz(quelle):
    """Ein fehlendes Feld darf nicht in einen Traceback laufen — aber erst recht nicht
    als Beleg durchgehen."""
    assert ist_belegt(quelle) is False
    assert hinweis_zur_herkunft(quelle) is not None


def test_sekundaerquelle_und_gar_nichts_werden_unterschieden():
    """Der Unterschied zählt: sekundär gehört ist schlechter als die Modellkarte und
    besser als gar nichts. Ein gemeinsamer Text unterschlüge die Hälfte."""
    assert hinweis_zur_herkunft(QUELLE_SEKUNDAER) != hinweis_zur_herkunft(QUELLE_UNGEPRUEFT)
    assert "Sekundärquelle" in hinweis_zur_herkunft(QUELLE_SEKUNDAER)
    assert "NICHT geprüft" in hinweis_zur_herkunft(QUELLE_UNGEPRUEFT)


def test_der_hinweis_ist_von_einer_lizenzauflage_unterscheidbar():
    """Warum die gemeinsame Vorsilbe existiert: Auf das Wort „geprüft" zu suchen trifft
    auch Auflagen, die mit der Herkunft nichts zu tun haben — daran ist ein Test
    hängengeblieben, der etwas anderes zu prüfen glaubte (Prüfbericht Abschnitt 5)."""
    fremde_auflage = "Modellkarte, geprüft 2026-08-18: Einsatz hinter paid API untersagt."
    assert "geprüft" in fremde_auflage
    assert not fremde_auflage.startswith(HERKUNFT_HINWEIS_PRAEFIX)


# --------------------------------------------------------------------------------------
# 2 · Eine Vokabel für alle drei Registries
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("modul,klasse,werte", REGISTRIES,
                         ids=[m.__name__.rsplit(".", 1)[-1] for m, _, _ in REGISTRIES])
def test_jede_registry_faellt_auf_dieselbe_vorgabe_zurueck(modul, klasse, werte):
    """Wer das Feld weglässt, bekommt überall dieselbe zurückhaltendste Annahme.

    Vorher stand in zwei der drei Registries der freie Text ``"ungeprueft"`` — zufällig
    derselbe Wert wie die Vokabel, aber ohne Verbindung zu ihr. Zufällige Gleichheit hält
    keine Umbenennung aus.
    """
    vorgabe = {f.name: f.default for f in dataclasses.fields(klasse)}["lizenz_quelle"]
    assert vorgabe == QUELLE_UNGEPRUEFT
    assert not ist_belegt(vorgabe)


@pytest.mark.parametrize("modul,klasse,werte", REGISTRIES,
                         ids=[m.__name__.rsplit(".", 1)[-1] for m, _, _ in REGISTRIES])
def test_jeder_eintrag_traegt_eine_bekannte_form(modul, klasse, werte):
    """Ein Tippfehler im Vermerk („geprüft" statt „geprueft") würde einen Beleg lautlos
    entwerten. Hier fällt er auf."""
    for eintrag in werte.values():
        assert _ist_bekannte_form(eintrag.lizenz_quelle), (
            f"{modul.__name__}/{eintrag.name}: {eintrag.lizenz_quelle!r} ist keine der "
            f"bekannten Formen"
        )


@pytest.mark.parametrize("modul,klasse,werte", REGISTRIES,
                         ids=[m.__name__.rsplit(".", 1)[-1] for m, _, _ in REGISTRIES])
def test_jede_registry_beantwortet_die_belegfrage_als_datum(modul, klasse, werte):
    """``pruefe_lizenz`` sagt überall, ob die Angabe belegt ist — als Feld, nicht als
    Textprobe, die jeder Aufrufer selbst erfinden müsste."""
    for name, eintrag in werte.items():
        urteil = modul.pruefe_lizenz(name)
        assert urteil["lizenz_belegt"] is ist_belegt(eintrag.lizenz_quelle)
        assert urteil["lizenz_hinweis"] == hinweis_zur_herkunft(eintrag.lizenz_quelle)


def test_belegte_eintraege_kommen_im_bestand_wirklich_vor():
    """Gegenprobe gegen eine vakuöse Schleife: Es gibt belegte Einträge, und sie werden
    als belegt erkannt.

    Bewusst NUR diese Richtung. „Es muss auch unbelegte geben" wäre wieder ein
    festgeschriebener Schuldenstand — der Test bräche dann ausgerechnet an dem Tag, an
    dem alles belegt ist. Die unbelegte Seite prüfen ``tests/test_backbone.py``,
    ``tests/test_einbetter.py`` und ``tests/test_tiefenschaetzer.py`` an synthetischen
    Einträgen, die keinem Prüfstand hinterherlaufen.
    """
    quellen = [e.lizenz_quelle for _, _, werte in REGISTRIES for e in werte.values()]
    assert any(ist_belegt(q) for q in quellen)
