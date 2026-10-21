"""Die Huellbox einer glb mit ``EXT_mesh_gpu_instancing`` — Anfrage 21.10.2026 (Steine als Instanzen).

Ein Stein steht einmal als Mesh im Kopf, seine Lagen als Accessors der Erweiterung. Die Box
muss alle Lagen umfassen und darf nie kleiner sein als die wahre; fehlt ``min``/``max`` an der
Verschiebung, gibt es keine Box (wie bei einem Mesh ohne Grenzen). Regel 3: synthetisch.
"""
from __future__ import annotations

import math

from aiimaging import glbbox

STEIN = {"min": [-0.1, 0.0, -0.05], "max": [0.1, 0.06, 0.05]}


def _gltf(instanzen=None, *, knoten_extra=None):
    accessors = [dict(STEIN, count=24, type="VEC3", componentType=5126)]
    ext = None
    if instanzen is not None:
        attribute = {}
        for name, spanne in instanzen.items():
            attribute[name] = len(accessors)
            accessors.append(dict(spanne or {}, count=3, componentType=5126,
                                  type="VEC4" if name == "ROTATION" else "VEC3"))
        ext = {glbbox.EXT_INSTANZEN: {"attributes": attribute}}
    knoten = {"name": "Mauerwerk", "mesh": 0, **(knoten_extra or {})}
    if ext:
        knoten["extensions"] = ext
    return {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [knoten], "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
            "accessors": accessors, "extensionsUsed": [glbbox.EXT_INSTANZEN]}


def _box(js):
    befund = glbbox.knotenboxen(js)
    return befund, (befund["knoten"][0][1:] if befund["knoten"] else None)


def test_ohne_erweiterung_bleibt_die_box_die_des_meshes():
    _, (lo, hi) = _box(_gltf())
    assert lo == STEIN["min"] and hi == STEIN["max"]


def test_reine_verschiebungen_umfassen_alle_lagen():
    _, (lo, hi) = _box(_gltf({"TRANSLATION": {"min": [0.0, 0.0, 0.0], "max": [12.0, 6.0, 0.0]}}))
    assert [round(v, 6) for v in lo] == [-0.1, 0.0, -0.05]
    assert [round(v, 6) for v in hi] == [12.1, 6.06, 0.05]


def test_mit_drehung_ist_die_box_nie_kleiner_als_die_wahre():
    _, (lo, hi) = _box(_gltf({"TRANSLATION": {"min": [0, 0, 0], "max": [10, 0, 0]},
                              "ROTATION": {"min": [0, 0, 0, 0.7], "max": [0, 0.71, 0, 1]},
                              "SCALE": {"min": [1, 1, 1], "max": [2, 2, 2]}}))
    r = math.sqrt(0.1 ** 2 + 0.06 ** 2 + 0.05 ** 2) * 2
    assert lo[0] <= -0.2 and hi[0] >= 10.2        # ein um 90 Grad gedrehter Stein, doppelt gross
    assert math.isclose(hi[1], r) and math.isclose(lo[1], -r)


def test_die_knotenmatrix_gilt_auch_fuer_die_instanzen():
    _, (lo, hi) = _box(_gltf({"TRANSLATION": {"min": [0, 0, 0], "max": [4, 0, 0]}},
                             knoten_extra={"translation": [100.0, 0.0, 0.0]}))
    assert round(lo[0], 6) == 99.9 and round(hi[0], 6) == 104.1


def test_ohne_min_max_an_der_verschiebung_gibt_es_keine_box():
    befund, box = _box(_gltf({"TRANSLATION": None}))
    assert box is None
    assert befund["ohne_grenzen"] == ["Mauerwerk"]
