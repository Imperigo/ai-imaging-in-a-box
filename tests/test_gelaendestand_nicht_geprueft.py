"""Ein von Hand gesetzter Geländestand ist eine Angabe — auf BEIDEN Kamerawegen.

**Owner-Entscheid 22.09.2026:** Ein von Hand gesetzter Geländestand (``gelaende_z``,
Schalter ``--gelaende-z``) ist eine ANGABE und gilt als NICHT GEPRÜFT — an jeder Stelle,
nicht als verlässlicher Bezug.

**Der Befund davor** (Durchsicht 22.09.2026, mit einem Lauf bestätigt): Dieselbe Eingabe
ergab zwei verschiedene Aussagen. Der vorgegebene Kameraweg
(``kameras.berichtsfelder_aus_stellung``) meldete ``gesetzt`` und «Geländeangabe … NICHT
GEPRÜFT»; der gerechnete (``kameras.kamerasatz``) meldete ``terrain_an_kamera``, also
``verlaesslich: True`` und keine Warnung. Welche Aussage der Betreiber bekam, hing davon
ab, ob die Kamera gerechnet oder mitgeschickt war — nicht von der Zahl.

Geprüft wird über den **Produktweg**: den Kamerablock, wie ihn der Runner meldet, durch
``abholer._komposition_vor_dem_render``. Eine Naht, die nur der direkte Aufrufer
erreicht, gibt es für das Produkt nicht.
"""
import pytest

from aiimaging import abholer, kameras, komposition

#: Synthetisch: ein Quader mit zwei Untergeschossen (Fuss 6 m unter dem Gelände).
BBOX = [[0.0, 0.0, -6.0], [40.0, 26.0, 15.0]]


def _block_gerechnet(gelaende_z):
    """Der Kamerablock des GERECHNETEN Wegs — dieselben Felder, die
    ``runners/blender_depth_stage.py`` aus ``kamerasatz`` in ``herkunft`` schreibt."""
    satz = kameras.kamerasatz(BBOX, kuerzel=("sSE",), gelaende_z=gelaende_z,
                              seitenverhaeltnis=1.0)
    k = satz["kameras"][0]
    return {
        "weg": "abgeleitet", "kuerzel": k["kuerzel"],
        "modus": k["modus"], "neigung_grad": k["neigung_grad"],
        "shift_mm": k["shift_mm"], "abstand_m": k["abstand_m"],
        "seitenverhaeltnis": k["seitenverhaeltnis"],
        "gelaende_z": satz["gelaende_z"],
        "gelaende_bezug": satz["gelaende_bezug"],
        "gebaeudehoehe_m": round(
            satz["mitte"][2] + satz["masse_m"][2] / 2.0 - satz["gelaende_z"], 4),
        "brennweite_mm": k["brennweite_mm"],
        "auge": list(k["auge"]), "blick_auf": list(k["blick_auf"]),
    }


def _block_vorgegeben(gelaende_z):
    """Der Kamerablock des VORGEGEBENEN Wegs — Stellung von aussen, die Berichtsfelder
    so ergänzt, wie der Runner es mit ``berichtsfelder_aus_stellung`` tut."""
    gerechnet = _block_gerechnet(gelaende_z)
    auge, ziel = gerechnet["auge"], gerechnet["blick_auf"]
    felder = kameras.berichtsfelder_aus_stellung(
        auge, ziel, BBOX, brennweite_mm=gerechnet["brennweite_mm"],
        gelaende_z=gelaende_z)
    return {"weg": "vorgegeben", "kuerzel": "vorgabe", "auge": auge,
            "blick_auf": ziel, **felder}


WEGE = {"gerechnet": _block_gerechnet, "vorgegeben": _block_vorgegeben}


def _urteil(weg, gelaende_z):
    return abholer._komposition_vor_dem_render({"kamera": WEGE[weg](gelaende_z)})


def _gelaendeangaben(urteil):
    return [w for w in urteil["warnungen"] if w.startswith("Geländeangabe")]


@pytest.mark.parametrize("gelaende_z", [0.0, 3.0])
@pytest.mark.parametrize("weg", sorted(WEGE))
def test_ein_gesetzter_gelaendestand_heisst_nicht_geprueft(weg, gelaende_z):
    """Auf jedem Weg: beurteilt, aber der Bezug ist NICHT GEPRÜFT — weder verlässlich
    noch schiefgegangen, und das steht als Warnung am Urteil."""
    urteil = _urteil(weg, gelaende_z)

    assert urteil["beurteilt"] is True, urteil["grund"]
    hoehe = urteil["kamerahoehe"]
    assert hoehe["bezugspunkt"] == "gesetzt", hoehe
    assert hoehe["verlaesslich"] is None, (
        "ein gesetzter Geländestand ist eine Angabe — verlässlich (True) wäre eine "
        "Prüfung, die niemand gemacht hat"
    )
    angaben = _gelaendeangaben(urteil)
    assert len(angaben) == 1, urteil["warnungen"]
    assert "NICHT GEPRÜFT" in angaben[0]


@pytest.mark.parametrize("gelaende_z", [0.0, 3.0])
def test_beide_wege_sagen_dasselbe_ueber_dieselbe_eingabe(gelaende_z):
    """Der eigentliche Befund: Welche Aussage der Betreiber bekommt, darf nicht davon
    abhängen, ob die Kamera gerechnet oder mitgeschickt wurde."""
    gerechnet = _urteil("gerechnet", gelaende_z)
    vorgegeben = _urteil("vorgegeben", gelaende_z)

    for feld in ("bezugspunkt", "verlaesslich", "warnungen"):
        assert gerechnet["kamerahoehe"][feld] == vorgegeben["kamerahoehe"][feld], feld
    assert _gelaendeangaben(gerechnet) == _gelaendeangaben(vorgegeben)


@pytest.mark.parametrize("weg", sorted(WEGE))
def test_ohne_angabe_bleibt_es_die_huellbox_unterkante(weg):
    """Die Gegenprobe: Ohne ``gelaende_z`` ist es kein ungeprüfter, sondern ein
    schiefgegangener Bezug — ``verlaesslich: False``, und keine «Geländeangabe»."""
    urteil = _urteil(weg, None)
    assert urteil["kamerahoehe"]["bezugspunkt"] == "huellbox_unterkante"
    assert urteil["kamerahoehe"]["verlaesslich"] is False
    assert _gelaendeangaben(urteil) == []


def test_der_verlaessliche_bezug_bleibt_bestehen():
    """``terrain_an_kamera`` wird nicht abgeschafft — er ist für ein GEMESSENES Gelände
    da. Nur eine Angabe des Betreibers darf ihn nicht mehr tragen."""
    eintrag = komposition.BEZUGSPUNKTE["terrain_an_kamera"]
    assert eintrag["verlaesslich"] is True
    assert komposition.kamerahoehe(1.70, bezugspunkt="terrain_an_kamera")["warnungen"] == []
