"""Die Drehung des Himmelsbilds liegt immer in [0, 360) — auch an den Rändern des Rundens.

Anlass: Beim Erzeugen der Vertrags-Fixtures (21.10.2026) ergab ``drehung_zur_kamera`` für einen
Wert knapp unter 360 genau 360.0, und ``drehung_aus_bericht`` reichte −5 oder 725 ungeprüft weiter.
"""
import pytest

from aiimaging import abholer, stimmung


@pytest.mark.parametrize("eps", [1e-9, 4e-7])
def test_drehung_zur_kamera_rundet_nicht_auf_360(eps):
    wert = stimmung.drehung_zur_kamera(80 - eps, 0, seitlich_grad=80, seite="rechts")
    assert 0.0 <= wert < 360.0


def _bericht(grad):
    return {"umgebung": {"drehung": {"weg": "zur_kamera", "drehung_grad": grad}}}


@pytest.mark.parametrize("roh,soll", [(359.9996, 0.0), (359.99999, 0.0), (-5.0, 355.0),
                                      (725.0, 5.0), (84.8241, 84.824)])
def test_drehung_aus_bericht_liegt_im_kreis(roh, soll):
    wert = abholer.drehung_aus_bericht(_bericht(roh))
    assert 0.0 <= wert < 360.0
    assert wert == pytest.approx(soll)
