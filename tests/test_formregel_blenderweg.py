"""A0289 Runde 3, M4: Der Blender-Lauf fragt die Form mit derselben Regel wie ``glbbox``.

``blender_depth_stage._form_zweitmeinung`` fragte bis zum 10.11.2026 nur die Hüllboxen und trennte
damit Körper ab, die der Weg ohne Blender stehen liess. Jetzt holt sie die Dreiecke aus dem
Blender-Objekt und verlangt denselben Beweis an der Oberseite. Diese Proben laufen **ohne Blender**:
Der Runner wird als Datei geladen, ``bpy`` ist eine Attrappe (wie in
``tests/test_rahmung_vor_render.py``, von dort kommen die Helfer).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from test_rahmung_vor_render import _Einheit, _mesh, _runner_mit_objekten


class _Welt:
    """Eine Weltmatrix, die rechnet: ``@`` für die Hüllbox, Zeilen für die Dreiecke."""

    def __init__(self, zeilen):
        self.zeilen = zeilen

    def __matmul__(self, v):
        return [sum(z[i] * v[i] for i in range(3)) + z[3] for z in self.zeilen[:3]]

    def __iter__(self):
        return iter(self.zeilen)


def _netzobjekt(name, hoehe, spiegel=False, x=(-30, 30), y=(-25, 25), nx=12, ny=10):
    """Ein Blender-Objekt als Attrappe: eine offene Fläche ``z = hoehe(x, y)`` mit echtem Netz."""
    import math as _m
    ecken = [(x[0] + (x[1] - x[0]) * i / nx, y[0] + (y[1] - y[0]) * j / ny) for j in range(ny + 1) for i in range(nx + 1)]
    ecken = [(ex, ey, hoehe(ex, ey)) for ex, ey in ecken]
    dreiecke = []
    for j in range(ny):
        for i in range(nx):
            a, b = j * (nx + 1) + i, j * (nx + 1) + i + 1
            c, d = b + nx + 1, a + nx + 1
            dreiecke += [(a, b, c), (a, c, d)]
    z = [e[2] for e in ecken]
    box = [(bx, by, bz) for bx in x for by in y for bz in (min(z), max(z))]
    s = -1.0 if spiegel else 1.0
    welt = _Welt([[s, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    netz = SimpleNamespace(vertices=[SimpleNamespace(co=e) for e in ecken],
                           loop_triangles=[SimpleNamespace(vertices=d) for d in dreiecke],
                           calc_loop_triangles=lambda: None)
    del _m
    return SimpleNamespace(name=name, type="MESH", bound_box=box, matrix_world=welt, data=netz)


def _hang_z(x, y):
    import math as _m
    return 0.1 * y + 0.3 * (_m.sin(x / 7.0) + _m.cos(y / 9.0) + 0.5 * _m.sin((x + y) / 5.0))


@pytest.mark.parametrize("spiegel", [False, True])
def test_die_form_trennt_im_blender_lauf_den_bewiesenen_hang(monkeypatch, spiegel):
    """A0289 Runde 3, M4, ohne Blender: Ein offener, unebener Hang mit Haus darauf wird auch hier
    abgetrennt, mit derselben Regel wie in ``glbbox``; die Dreiecke kommen aus dem Objekt. Am
    gespiegelten Objekt dreht der Umlaufsinn, die Oberseite bleibt oben."""
    modul = _runner_mit_objekten(monkeypatch, [
        _netzobjekt("Mesh.001", _hang_z, spiegel=spiegel),
        _mesh("Mesh.002", (-6, -5, -0.5), (6, 5, 12)),
    ])
    lo, hi, note, schrumpfung, form = modul._bbox_bauwerk()
    assert form == {"entschieden_durch": "form", "gelaende_namen": ("Mesh.001",)}
    assert lo == [-6, -5, -0.5] and hi == [6, 5, 12]
    assert schrumpfung > 0.5 and "die FORM hat entschieden" in note


def test_die_form_trennt_im_blender_lauf_keine_kuppel_mit_aufbau(monkeypatch):
    """Die Klasse, an der Runde 2 scheiterte, auf diesem Weg: eine gewölbte Fläche bis an den Boden,
    darauf etwas Höheres. Kein Hang: nichts wird abgetrennt, das Bauwerk bleibt ganz."""
    import math as _m
    kuppel = lambda x, y: 8.0 * _m.cos(_m.pi * x / 60.0) * _m.cos(_m.pi * y / 50.0)     # noqa: E731
    modul = _runner_mit_objekten(monkeypatch, [
        _netzobjekt("Mesh.001", kuppel),
        _mesh("Mesh.002", (-2, -2, 7.5), (2, 2, 14)),
    ])
    lo, hi, _note, _schrumpfung, form = modul._bbox_bauwerk()
    assert form["entschieden_durch"] == "keine" and form["gelaende_namen"] == ()
    assert lo[:2] == [-30, -25] and hi[:2] == [30, 25]


def test_die_form_trennt_im_blender_lauf_nichts_was_sie_nicht_lesen_kann(monkeypatch):
    """Derselbe Hang, aber das Netz ist nicht lesbar (hier: die Attrappe ohne Netz): nicht geraten."""
    hang = _netzobjekt("Mesh.001", _hang_z)
    ohne = SimpleNamespace(name="Mesh.001", type="MESH", bound_box=hang.bound_box, matrix_world=_Einheit())
    modul = _runner_mit_objekten(monkeypatch, [ohne, _mesh("Mesh.002", (-6, -5, -0.5), (6, 5, 12))])
    _lo, _hi, _note, _schrumpfung, form = modul._bbox_bauwerk()
    assert form["entschieden_durch"] == "keine"


def test_die_form_ergaenzt_im_blender_lauf_die_namensregel_nicht(monkeypatch):
    """Hat die Namensregel etwas gefunden, bleibt sie zuständig, wie in ``glbbox``."""
    modul = _runner_mit_objekten(monkeypatch, [
        _netzobjekt("Mesh.001", _hang_z),
        _mesh("Gelaende_Randstein", (-30.5, -25, 0.0), (-30, 25, 0.2)),
        _mesh("Mesh.002", (-6, -5, -0.5), (6, 5, 12)),
    ])
    _lo, _hi, _note, _schrumpfung, form = modul._bbox_bauwerk()
    assert form["entschieden_durch"] == "name" and form["gelaende_namen"] == ("Gelaende_Randstein",)
