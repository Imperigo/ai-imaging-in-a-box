"""Entscheid 143 (Owner über die Zentrale, 24.10.2026, A): **Varianten rechnen standardmässig voll.**

Die Knotenansicht bestellt seit 143 bei «Variante erzeugen» und am Varianten-Knoten ohne Wahl
``vis.guete: 'voll'`` — auf der Grundlage des Render-Knotens (``vis.grundlage``, ein Startwert).
Am Heim-PC ist dafür **keine Änderung** nötig: «voll» rechnet wie ein Auftrag ohne Feld, und für
Varianten gilt der Bildeingang 0,5 (Entscheid 138), seit Entscheid 149 0,7. Diese Probe hält das fest, damit eine spätere
Änderung am Kern die Zusage der Oberfläche («vom Grundbild aus, Bildeingang 0,5») nicht still bricht.
Eine ausdrücklich gewählte Vorschau startet seit A0051b (Owner-Entscheid 31.10.2026 «Immer vom
Render») ebenfalls vom Grundbild; bis dahin rechnete sie ohne Bildeingang (Entscheid 104).

Anlass: Messung auf-20261023-346 — die Vorschau (8 Schritte, ohne Grundbild) übermalte ein Fensterband,
voll mit 0,5 hielt es. Ohne GPU, nur ``lies_szene``; Regel 3: alles synthetisch.
"""
from __future__ import annotations

from aiimaging import kosmo_szene

from test_varianten_vorgabe_e126 import _szene, himmel  # noqa: F401 — Fixture

GL = "gl-0a1b2c3d4e5f6071"


def _lies(**vis):
    return kosmo_szene.lies_szene(_szene(**vis), streng=False)


def _ohne_bildeingang_mangel(s) -> bool:
    """Kein Mangel zum Bildeingang oder zur Güte (andere — etwa eine fehlende Textur am Rechner der
    Probe — gehören nicht zu dieser Frage)."""
    return not any("bildeingang" in m or "guete" in m for m in s["maengel"])


def test_variante_voll_auf_grundlage_rechnet_vom_grundbild_07(himmel):  # noqa: F811
    # Seit Entscheid 149 (24.10.2026): Varianten 0,7 statt 0,5.
    s = _lies(guete="voll", grundlage=GL, seed=7, skip=False)
    assert _ohne_bildeingang_mangel(s)
    assert s["bildeingang"] == 0.7
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}


def test_voll_und_ohne_feld_rechnen_gleich(himmel):  # noqa: F811
    voll, ohne = _lies(guete="voll", grundlage=GL, seed=7), _lies(grundlage=GL, seed=7)
    for feld in ("bildeingang", "umriss_halten", "himmel_sichtbar", "messschalter"):
        assert voll[feld] == ohne[feld], feld


def test_ausdrueckliche_vorschau_startet_vom_grundbild(himmel):  # noqa: F811
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): auch die ausdrueckliche Vorschau startet vom
    # Grundbild, mit der Staerke der Variante.
    s = _lies(guete="vorschau", grundlage=GL, seed=7)
    assert _ohne_bildeingang_mangel(s)
    assert s["bildeingang"] == kosmo_szene.BILDEINGANG_VORGABE_VARIANTE
    ms = s["messschalter"]["bildeingang"]
    assert ms["herkunft"] == "vorgabe"
