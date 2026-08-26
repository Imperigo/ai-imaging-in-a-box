"""Der Sonnenstand einer Bestellung erreicht den Render — und zwar nachgerechnet.

**Der gefährlichste der stehengebliebenen Felder**, und er ist es genau darum, weil das
Ergebnis richtig **aussieht**: Der Runner setzte eine feste Sonne, und ein Auftrag mit
Abendstand wurde gerendert, als wäre er nicht gestellt worden. Ein sauberes, gut
belichtetes, falsches Bild. Gemeldet aus dem ersten vollständigen Kettenlauf
(`auf-vis-20260825-15`, Posten 5.3).

**Zur Bauart dieser Datei.** Die Winkel werden nicht geglaubt, sondern
**zurückgemessen**: :func:`_sonnenstand` dreht ``(0, 0, -1)`` mit den gelieferten
Eulerwinkeln und rechnet daraus Höhe und Azimut zurück. Ein Test, der nur prüft, dass
``blender_euler`` liefert, was ``blender_euler`` rechnet, prüft die Formel gegen sich
selbst — und genau so ist der Fehler entstanden, den diese Datei nebenbei gefunden hat.

**Der Fund.** Die feste Drehung stand als ``(radians(50), 0, radians(35))`` da, mit dem
Kommentar *«50° Höhe und 35° Azimut»*. **Beide Zahlen im Kommentar sind falsch:** Es sind
40 Grad über dem Horizont, und der Azimut ist −35 (östlich von Süden) und nicht +35. *Ein
Kommentar ist keine Rechnung.*
"""
from __future__ import annotations

import math

import pytest

from aiimaging import sonne


def _sonnenstand(euler) -> tuple[float, float]:
    """Aus ``(rx, ry, rz)`` zurück auf ``(Höhe, Azimut von Süden)`` in Grad.

    Blenders Euler XYZ heisst ``R = Rz · Ry · Rx``; eine SUN strahlt entlang ``−Z``. Die
    **Sonne** steht der Strahlrichtung entgegen. Süden ist ``−Y``, Westen ``−X``.
    """
    rx, _ry, rz = euler
    v = (0.0, 0.0, -1.0)
    cx, sx = math.cos(rx), math.sin(rx)
    v = (v[0], v[1] * cx - v[2] * sx, v[1] * sx + v[2] * cx)
    cz, sz = math.cos(rz), math.sin(rz)
    v = (v[0] * cz - v[1] * sz, v[0] * sz + v[1] * cz, v[2])

    s = (-v[0], -v[1], -v[2])                       # Position der Sonne
    hoehe = math.degrees(math.asin(max(-1.0, min(1.0, s[2]))))
    azimut = math.degrees(math.atan2(-s[0], -s[1]))  # 0 = Süden, positiv nach Westen
    return hoehe, azimut


# ======================================================================================
# Die Rechnung, zurueckgemessen
# ======================================================================================

@pytest.mark.parametrize("hoehe, azimut", [
    (40.0, -35.0), (40.0, 0.0), (30.0, 90.0), (60.0, -90.0), (10.0, 170.0),
    (90.0, 0.0), (0.0, 45.0), (-10.0, 0.0),
])
def test_die_gestellte_sonne_steht_wirklich_dort(hoehe, azimut):
    """Der eigentliche Test dieser Datei: Höhe und Azimut werden aus der Drehung
    **zurückgerechnet** und gegen die Bestellung gehalten."""
    ist_hoehe, ist_azimut = _sonnenstand(sonne.blender_euler(hoehe, azimut))

    assert ist_hoehe == pytest.approx(hoehe, abs=1e-9)
    assert ist_azimut == pytest.approx(azimut, abs=1e-9)


def test_null_grad_azimut_heisst_sueden():
    """Der Nullpunkt der Süd-Konvention. Wäre er verschoben, stünde jedes Bild dieses
    Projekts falsch — und zwar gleichmässig falsch, also unauffällig."""
    _hoehe, azimut = _sonnenstand(sonne.blender_euler(45.0, 0.0))

    assert azimut == pytest.approx(0.0, abs=1e-9)


def test_positiver_azimut_zieht_nach_westen():
    """Die Richtung ist die halbe Konvention. Ein Vorzeichenfehler vertauscht Vormittag
    und Nachmittag, und beide Bilder sehen für sich genommen richtig aus."""
    _h, west = _sonnenstand(sonne.blender_euler(30.0, 60.0))
    _h2, ost = _sonnenstand(sonne.blender_euler(30.0, -60.0))

    assert west == pytest.approx(60.0, abs=1e-9)
    assert ost == pytest.approx(-60.0, abs=1e-9)


@pytest.mark.parametrize("von_norden, von_sueden", [
    (180.0, 0.0),        # Norden-Konvention 180 = Süden
    (90.0, -90.0),       # Osten
    (270.0, 90.0),       # Westen
])
def test_die_beiden_konventionen_treffen_dieselbe_richtung(von_norden, von_sueden):
    """Nicht zwei Rechnungen, sondern eine Frage nach dem Nullpunkt. Wenn beide Wege
    verschieden landeten, wäre eine von beiden falsch — und niemand wüsste welche."""
    a = _sonnenstand(sonne.blender_euler(35.0, von_norden,
                                         konvention=sonne.AZIMUT_VON_NORDEN))
    b = _sonnenstand(sonne.blender_euler(35.0, von_sueden,
                                         konvention=sonne.AZIMUT_VON_SUEDEN))

    assert a[0] == pytest.approx(b[0], abs=1e-9)
    assert math.cos(math.radians(a[1] - b[1])) == pytest.approx(1.0, abs=1e-9)


def test_die_konventionen_unterscheiden_sich_wirklich():
    """**Die Gegenprobe zum Test darüber.** Wären sie gleich, wäre die ganze Frage
    gegenstandslos — und der Test darüber hielte trotzdem."""
    a = _sonnenstand(sonne.blender_euler(35.0, 40.0, konvention=sonne.AZIMUT_VON_NORDEN))
    b = _sonnenstand(sonne.blender_euler(35.0, 40.0, konvention=sonne.AZIMUT_VON_SUEDEN))

    assert abs(a[1] - b[1]) > 90.0, "dieselbe Zahl, zwei sehr verschiedene Tageszeiten"


# ======================================================================================
# Der Fund: der alte Kommentar stimmte nicht
# ======================================================================================

ALTE_FESTE_DREHUNG = (math.radians(50.0), 0.0, math.radians(35.0))


def test_die_vorgabe_stellt_genau_die_alte_feste_sonne():
    """**Die wichtigste Prüfung dieses Umbaus.** Ohne sie wäre jedes Bild dieses Projekts
    ab heute anders beleuchtet als alle Messungen davor — und der Vergleich über die
    Wochen wäre still kaputt."""
    ist = sonne.lage()["euler"]

    for a, b in zip(ist, ALTE_FESTE_DREHUNG):
        assert a == pytest.approx(b, abs=1e-12)


def test_der_alte_kommentar_nannte_beide_zahlen_falsch():
    """*«50° Höhe und 35° Azimut»* — es sind 40 Grad und −35. Ein Kommentar ist keine
    Rechnung, und dieser hier hat eine Woche lang beides behauptet."""
    hoehe, azimut = _sonnenstand(ALTE_FESTE_DREHUNG)

    assert hoehe == pytest.approx(40.0, abs=1e-9)
    assert azimut == pytest.approx(-35.0, abs=1e-9)
    assert sonne.VORGABE_HOEHE_GRAD == 40.0
    assert sonne.VORGABE_AZIMUT_GRAD == -35.0


# ======================================================================================
# Was bestellt war und was Vorgabe ist — der Unterschied gehoert in den Bericht
# ======================================================================================

def test_ohne_bestellung_steht_die_vorgabe_da_und_sagt_es():
    befund = sonne.lage()

    assert befund["bestellt"] == ()
    assert befund["hoehe_grad"] == sonne.VORGABE_HOEHE_GRAD


def test_eine_halbe_bestellung_wird_als_halbe_gemeldet():
    """Wer nur die Höhe bestellt, hat den Azimut nicht bestellt. Beides als «bestellt» zu
    führen hiesse, eine Vorgabe als Wunsch auszugeben."""
    befund = sonne.lage(8.0)

    assert befund["bestellt"] == ("hoehe",)
    assert befund["hoehe_grad"] == 8.0
    assert befund["azimut_grad"] == sonne.VORGABE_AZIMUT_GRAD


def test_der_befund_traegt_konvention_und_weltsystem():
    """Beides sind **Setzungen** und keine Messungen. Ein Bild, dem man die Annahme nicht
    ansieht, unter der es entstand, ist später nicht mehr einzuordnen."""
    befund = sonne.lage(8.0, 250.0)

    assert befund["konvention"] == sonne.VORGABE_KONVENTION
    assert "Norden" in befund["weltsystem"]
    assert befund["methode"] == sonne.METHODE


def test_der_fremde_sonnenblock_wird_gelesen():
    befund = sonne.aus_bestellung({"elevation": 8, "azimuth": 250})

    assert befund["bestellt"] == ("hoehe", "azimut")
    assert befund["hoehe_grad"] == 8.0 and befund["azimut_grad"] == 250.0


def test_kein_sonnenblock_ist_die_vorgabe_und_keine_bestellung():
    assert sonne.aus_bestellung(None)["bestellt"] == ()
    assert sonne.aus_bestellung({})["bestellt"] == ()


# ======================================================================================
# Was abgelehnt wird — und was ausdruecklich nicht
# ======================================================================================

@pytest.mark.parametrize("hoehe", [91.0, 100.0, -91.0, 1000.0])
def test_eine_hoehe_jenseits_des_zenits_wird_abgelehnt(hoehe):
    """Grösser als 90 ist keine höhere Sonne, sondern eine, die hinter dem Zenit wieder
    herunterkommt — mit ziemlicher Sicherheit ein Vorzeichen- oder Einheitenfehler."""
    with pytest.raises(sonne.SonnenError, match=r"\[-90, 90\]"):
        sonne.blender_euler(hoehe, 0.0)


def test_eine_sonne_unter_dem_horizont_ist_zugelassen():
    """**Die Gegenprobe, und sie ist eine Entscheidung.** Nacht ist eine gültige
    Bestellung — nur eben eine, die ein dunkles Bild ergibt. Wer sie verböte, entschiede
    über die Gestaltung; wer sie stillschweigend auf null höbe, lieferte etwas anderes
    als bestellt."""
    hoehe, _azimut = _sonnenstand(sonne.blender_euler(-15.0, 0.0))

    assert hoehe == pytest.approx(-15.0, abs=1e-9)


def test_eine_unbekannte_konvention_wird_nicht_stillschweigend_ersetzt():
    with pytest.raises(sonne.SonnenError, match="Unbekannte Azimutkonvention"):
        sonne.blender_euler(40.0, 0.0, konvention="von_westen")


@pytest.mark.parametrize("kaputt", ["acht", None, True, float("nan"), float("inf")])
def test_unbrauchbare_zahlen_werden_benannt(kaputt):
    with pytest.raises(sonne.SonnenError):
        sonne.blender_euler(kaputt, 0.0)


# ======================================================================================
# Die Naht — der Sonnenstand erreicht wirklich das Kommando
# ======================================================================================

def test_der_bestellte_sonnenstand_steht_im_blender_kommando():
    """Ein Parameter, der im Kern einstellbar ist und an der Aussenkante nicht durchkommt,
    ist die Fehlerart, die dieses Projekt am 23.08.2026 zweimal an einem Tag hatte."""
    from aiimaging import seams

    kommando = seams.baue_kommando_multipass(
        "a.glb", "/out", up_axis="Z_UP", sonne={"elevation": 8, "azimuth": 250})

    assert "--sonne-hoehe=8.0" in kommando
    assert "--sonne-azimut=250.0" in kommando


def test_ohne_bestellung_steht_kein_sonnenschalter_im_kommando():
    """**Die Gegenprobe, und sie trägt eine Entscheidung.** Ein mitgeschickter
    Vorgabewert wäre im Bericht des Runners von einer Bestellung nicht mehr zu
    unterscheiden — und genau diesen Unterschied führt dort das Feld `bestellt`."""
    from aiimaging import seams

    kommando = seams.baue_kommando_multipass("a.glb", "/out", up_axis="Z_UP")

    assert not [teil for teil in kommando if "sonne" in teil]
