"""Die Startzeile der Fläche im Heimnetz — geprüft an der echten Kommandozeile.

Befund 22.09.2026, am Produktweg nachgeprüft (``main`` mit ``--anschluss 0``):

1. ``--im-heimnetz`` überschrieb eine ausdrücklich angegebene ``--adresse``
   stillschweigend — gebaut wurde auf ``0.0.0.0``, Rückgabe 0, kein Wort dazu.
2. Die gedruckte Zeile lautete ``http://0.0.0.0:…`` — eine Adresse, die man auf dem
   iPad nicht eintippen kann. Wer sie ablas, kam nicht an und wusste nicht warum.

Die Wächter hier laufen über ``server.main`` — den Weg, den das Produkt wirklich geht —
und prüfen die **Wirkung**: die gedruckte Zeile und den Rückgabewert. Kein echter
Server läuft lange: ``serve_forever`` ist eine Attrappe, die sofort Strg-C meldet.

Die Ermittlung der Adresse wird am Socket ersetzt, nicht an ``heimnetz_adresse`` selbst:
So läuft die echte Prüfung (Loopback ist kein Heimnetz, Fehler heisst nicht ermittelt)
mit, und nur das Betriebssystem ist Attrappe.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_FLAECHE = Path(__file__).resolve().parents[1] / "oberflaeche"


@pytest.fixture
def flaeche():
    _sys.path.insert(0, str(_FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        _sys.path.remove(str(_FLAECHE))


@pytest.fixture
def gebaut(flaeche, monkeypatch):
    """Der echte Serverbau, aber ``serve_forever`` endet sofort wie mit Strg-C.

    Zurück kommt die Liste der gebauten Server mit ihrer Adresse — leer heisst: es wurde
    gar nichts gebaut.
    """
    echt = flaeche.baue_server
    liste = []

    def bau(**kw):
        srv = echt(**kw)

        def sofort_beendet():
            raise KeyboardInterrupt

        srv.serve_forever = sofort_beendet
        liste.append(srv)
        return srv

    monkeypatch.setattr(flaeche, "baue_server", bau)
    return liste


def _betriebssystem(monkeypatch, flaeche, *, eigene=None, fehler=None):
    """Den Socket-Aufruf der Fläche ersetzen: ``eigene`` Adresse oder ``fehler``.

    Die Attrappe kennt kein ``send`` — sendete die Ermittlung doch etwas, fiele der Test.
    """
    class _Sock:
        def __init__(self, *_a):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def connect(self, _ziel):
            if fehler is not None:
                raise fehler

        def getsockname(self):
            return (eigene, 54321)

    monkeypatch.setattr(flaeche, "socket",
                        SimpleNamespace(AF_INET=2, SOCK_DGRAM=2, socket=_Sock))


def _heimnetz(flaeche, *mehr):
    return flaeche.main(["--im-heimnetz", "--kennwort", "geheim", "--anschluss", "0", *mehr])


def test_heimnetz_nennt_die_adresse_die_ein_anderes_geraet_erreicht(
        flaeche, gebaut, monkeypatch, capsys):
    _betriebssystem(monkeypatch, flaeche, eigene="192.168.1.20")
    assert _heimnetz(flaeche) == 0
    aus = capsys.readouterr().out
    assert gebaut and gebaut[0].server_address[0] == "0.0.0.0"   # gehört wird auf allen
    assert "http://192.168.1.20:" in aus                         # genannt wird die erreichbare
    assert "0.0.0.0" not in aus


def test_heimnetz_ohne_ermittlung_sagt_es_statt_0_0_0_0(flaeche, gebaut, monkeypatch, capsys):
    _betriebssystem(monkeypatch, flaeche, fehler=OSError("Netz ist nicht erreichbar"))
    assert _heimnetz(flaeche) == 0
    aus = capsys.readouterr().out
    assert "Adresse im Heimnetz nicht ermittelt — am Rechner nachsehen" in aus
    assert "http://" not in aus                                  # keine geratene Adresse
    assert "0.0.0.0" not in aus


def test_nur_die_eigene_maschine_gilt_nicht_als_heimnetz(flaeche, gebaut, monkeypatch, capsys):
    # Ohne Netzkarte liefert manches System 127.0.1.1 — ein iPad erreicht das nie.
    _betriebssystem(monkeypatch, flaeche, eigene="127.0.1.1")
    assert _heimnetz(flaeche) == 0
    aus = capsys.readouterr().out
    assert "Adresse im Heimnetz nicht ermittelt" in aus
    assert "127.0.1.1" not in aus


def test_adresse_und_heimnetz_zusammen_werden_abgewiesen(flaeche, gebaut, capsys):
    rc = _heimnetz(flaeche, "--adresse", "127.0.0.1")
    aus = capsys.readouterr().out
    assert rc != 0
    assert "widersprechen sich" in aus
    assert gebaut == []                                          # nichts gebaut, nichts offen


def test_adresse_und_heimnetz_mit_derselben_aussage_gehen_durch(
        flaeche, gebaut, monkeypatch, capsys):
    _betriebssystem(monkeypatch, flaeche, eigene="10.0.0.7")
    assert _heimnetz(flaeche, "--adresse", "0.0.0.0") == 0
    assert "http://10.0.0.7:" in capsys.readouterr().out


def test_ohne_schalter_bleibt_es_bei_der_eigenen_maschine(flaeche, gebaut, capsys):
    # Die Vorgabe wanderte aus dem Parser in main — sie muss dort wirklich ankommen.
    assert flaeche.main(["--anschluss", "0"]) == 0
    aus = capsys.readouterr().out
    assert gebaut[0].server_address[0] == "127.0.0.1"
    assert "http://127.0.0.1:" in aus
    assert "ACHTUNG" not in aus


def test_die_zeile_nennt_den_wirklichen_anschluss(flaeche, gebaut, capsys):
    assert flaeche.main(["--anschluss", "0"]) == 0
    wirklich = gebaut[0].server_address[1]
    assert wirklich != 0
    assert f"http://127.0.0.1:{wirklich} " in capsys.readouterr().out
