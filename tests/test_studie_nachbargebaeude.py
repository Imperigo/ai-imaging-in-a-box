"""Die Nachbargebäude-Studie — ohne Blender geprüft.

*Der Anlass ist ein Vorbehalt, der uns nicht gehörte.* Seit dem 01.09.2026 trug die
Bauwerksmaske einen Satz aus `auf-20260823-37` — einer Messung der HomeStation. Einen
fremden Vorbehalt weiterzutragen ist bequem und wird mit jeder Weitergabe unschärfer.

Nachgemessen hat er hier **nicht** reproduziert, und das ist kein Widerspruch, sondern
eine Eingrenzung: Er ist eine Aussage über den **Schätzer**, nicht über die **Szene**.
"""

import importlib.util
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _studie():
    pfad = WURZEL / "tools" / "studie_nachbargebaeude.py"
    spec = importlib.util.spec_from_file_location("werkzeug_studie_nachbar", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_der_nachbar_traegt_die_klasse_die_das_umfeld_kennt():
    """Er muss `IfcCivilElement` heissen — sonst zählt die Maske ihn als **Bauwerk**, und
    die Studie misst einen Zielbau mit angewachsenem Nachbarn."""
    m = _studie()
    name, _lo, _hi = m._nachbar(1.0)
    assert name.lower().startswith("ifccivilelement")

    from aiimaging import maske
    assert maske.ist_umfeld(name) is True


def test_der_nachbar_steht_hinter_dem_ziel_und_nicht_daneben():
    """Sonst verdeckt er nichts und der ganze Aufbau misst zwei Bauwerke nebeneinander."""
    m = _studie()
    _n, lo, hi = m._nachbar(1.0)
    _z, ziel_lo, ziel_hi = m.ZIEL
    assert hi[2] < ziel_lo[2], "der Nachbar liegt in der Tiefe hinter dem Ziel"
    assert lo[0] < ziel_lo[0] and hi[0] > ziel_hi[0], "und er ist breiter als das Ziel"


def test_der_nachbar_ist_gross_genug_um_den_hintergrund_zu_fuellen():
    """**Der erste verfehlte Anlauf, als Probe festgehalten.**

    Mit 28 × 16 m deckte er 9,8 % des Hintergrunds, und der Kantenanteil trennte weiter
    mühelos — das war kein Gegenbeweis, sondern eine Szene, die die Bedingung gar nicht
    herstellte. *Die häufigste Art, eine Messung zu verfehlen.*
    """
    m = _studie()
    _n, lo, hi = m._nachbar(1.0)
    breite = hi[0] - lo[0]
    hoehe = hi[1] - lo[1]
    _z, ziel_lo, ziel_hi = m.ZIEL
    assert breite >= 5 * (ziel_hi[0] - ziel_lo[0])
    assert hoehe >= 3 * (ziel_hi[1] - ziel_lo[1])


def test_die_kamera_rahmt_das_ZIEL_und_nicht_die_ganze_szene():
    """**Der zweite verfehlte Anlauf.** Ohne ausdrückliche Hüllbox rahmt der Runner die
    ganze Szene — die ist hier 120 m breit, das Ziel wurde winzig, und 86 % des
    Hintergrunds waren wieder Himmel."""
    m = _studie()
    _z, ziel_lo, ziel_hi = m.ZIEL
    lo, hi = m.ZIEL_HUELLBOX
    # glTF (x, y, z) -> Welt (x, -z, y): die Huellbox beschreibt DAS ZIEL, gedreht.
    assert (hi[0] - lo[0]) == (ziel_hi[0] - ziel_lo[0])
    assert (hi[2] - lo[2]) == (ziel_hi[1] - ziel_lo[1])
    assert (hi[1] - lo[1]) == (ziel_hi[2] - ziel_lo[2])


def test_die_glaettung_mittelt_wirklich_und_laesst_den_rand_stehen():
    """Der Ersatz für die Unschärfe eines Schätzers — und er ist einer, kein Nachbau."""
    m = _studie()
    karte = [0.0] * 9
    karte[4] = 9.0
    aus = m._geglaettet(karte, 3, 3)
    assert aus[4] == 1.0, "die Mitte ist das Mittel der neun"
    assert aus[0] == 0.0, "der Rand bleibt unangetastet — er hat kein volles Fenster"


def test_die_szene_traegt_keine_echten_namen():
    """Regel 3: Der Zielbau heisst nach seiner IFC-Klasse, nicht nach einem Projekt."""
    m = _studie()
    for name in (m.ZIEL[0], m._nachbar(1.0)[0]):
        assert name.lower().startswith("ifc")
