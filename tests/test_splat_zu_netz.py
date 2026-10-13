"""Die Splat-Brücke: Splat → Netz (Owner-Entscheid 79, 13.10.2026).

Was hier bewacht wird
---------------------
1. **Die stdlib-Hälfte** (``aiimaging.kontext_netz``): PLY-Kopf, SH-Grad, Quaternion,
   «oben» und Massstab aus der Matrix, Blickwinkel (Anzahl, nach aussen und nach innen,
   Augenhöhe), Ansichtsmatrix und Intrinsik — und dass sie nur die Standardbibliothek
   importiert, denn der Runner lädt sie über den Dateipfad.
2. **Die Naht** (``seams.splat_zu_netz``) mit einer Starter-Attrappe: das richtige Kommando,
   die Frist, der Speicher nach Inhalt (Treffer bei gleichem Inhalt, keiner bei anderem).
3. **Der Rückfall** (``seams.kontext_vorbereiten``): ohne Brücke die Kugeln, mit Satz.
4. **Die Blender-Stufe** lädt ein Netz als Netz (nur mit Blender und ``.venv-ifc``).
5. **Der Abholer** gibt das Netz an den Multipass und vermerkt den Weg.
6. **Die echte Fusion** mit dem CPU-Ersatzrenderer — nur, wenn ``AIIMAGING_SPLAT_PYTHON``
   gesetzt ist (eine Umgebung mit torch, gsplat und open3d).

Der Runner wird **gelesen, nie importiert** (Regel 2/4, ``tests/test_prozessgrenze.py``).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import math
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, bildlesen, contracts, kette, kontext, kontext_netz as kn
from aiimaging import kosmo_szene, maske, seams
from aiimaging.graph import Knoten
from conftest import MINI_PNG

WURZEL = Path(__file__).resolve().parents[1]
ERZEUGER = WURZEL / "tools" / "make_test_splat.py"
RUNNER_QUELLE = seams.SPLAT_RUNNER.read_text(encoding="utf-8")


def _erzeuger():
    spez = importlib.util.spec_from_file_location("make_test_splat_netzprobe", ERZEUGER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _kleines_netz(pfad: Path, versatz=(0.0, 0.0, 0.0)) -> dict:
    """Ein Quadrat aus zwei Dreiecken, rot — der kleinste Netz-Fall."""
    x, y, z = versatz
    return kn.schreibe_netz_ply(
        pfad, [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)],
        [(200, 40, 30)] * 4, [(0, 1, 2), (0, 2, 3)])


# ======================================================================================
# 1 · Die stdlib-Hälfte
# ======================================================================================

def test_kontext_netz_importiert_nur_die_standardbibliothek():
    """Der Runner lädt die Datei über ihren Pfad. Ein Import aus ``aiimaging`` oder von
    numpy bräche ihn — im ``.venv-splat`` gibt es das Paket nicht."""
    baum = ast.parse(Path(kn.__file__).read_text(encoding="utf-8"))
    module = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            assert knoten.level == 0, "relativer Import — ueber den Pfad nicht ladbar"
            module.add(knoten.module.split(".")[0])
    assert module - {"__future__"} <= set(sys.stdlib_module_names), module


def test_der_runner_laedt_kontext_netz_ueber_den_pfad_und_nicht_aiimaging():
    importe = set()
    for knoten in ast.walk(ast.parse(RUNNER_QUELLE)):
        if isinstance(knoten, ast.Import):
            importe.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.module:
            importe.add(knoten.module.split(".")[0])
    assert "aiimaging" not in importe
    assert {"gsplat", "open3d", "torch"} <= importe
    assert 'parents[1] / "kontext_netz.py"' in RUNNER_QUELLE
    assert 'render_mode="RGB+ED"' in RUNNER_QUELLE


def test_ply_kopf_splat_netz_und_punktwolke(tmp_path):
    _erzeuger().erzeuge_splat(tmp_path / "s.ply", punkte=200, mit_f_rest=True)
    kopf = kn.lies_ply_kopf(tmp_path / "s.ply")
    assert kopf["format"] == "binary_little_endian"
    ecken = kopf["elemente"][0]
    assert ecken["name"] == "vertex" and ecken["anzahl"] == 200
    assert ecken["eigenschaften"][0] == {"name": "x", "typ": "float"}
    assert not kn.ist_netz(kopf) and kn.art_der_datei(tmp_path / "s.ply") == "splat"
    assert kn.sh_grad_aus_kopf(kopf) == 3

    _kleines_netz(tmp_path / "n.ply")
    kopf = kn.lies_ply_kopf(tmp_path / "n.ply")
    assert kn.ist_netz(kopf) and kn.art_der_datei(tmp_path / "n.ply") == "netz"
    flaeche = kopf["elemente"][1]
    assert flaeche["anzahl"] == 2 and flaeche["eigenschaften"][0]["typ"] == "list"
    z = kn.netz_kennzahlen(tmp_path / "n.ply")
    assert (z["ecken"], z["dreiecke"], z["datei"]) == (4, 2, "n.ply")
    assert str(tmp_path) not in json.dumps(z)

    (tmp_path / "p.ply").write_bytes(b"ply\nformat ascii 1.0\nelement vertex 1\n"
                                     b"property float x\nend_header\n1\n")
    assert kn.art_der_datei(tmp_path / "p.ply") == "punkte"


@pytest.mark.parametrize("inhalt", [b"PK\x03\x04", b"ply\nformat ascii 1.0\n",
                                    b"ply\nformat dxf 1.0\nend_header\n",
                                    b"ply\nformat ascii 1.0\nelement vertex 1\n"
                                    b"property quad x\nend_header\n"])
def test_ply_kopf_weist_unlesbares_ab(tmp_path, inhalt):
    (tmp_path / "x.ply").write_bytes(inhalt)
    with pytest.raises(kn.KontextNetzError):
        kn.lies_ply_kopf(tmp_path / "x.ply")


def test_netz_kennzahlen_weist_einen_splat_ab(tmp_path):
    _erzeuger().erzeuge_splat(tmp_path / "s.ply", punkte=100)
    with pytest.raises(kn.KontextNetzError, match="keine Flächen"):
        kn.netz_kennzahlen(tmp_path / "s.ply")
    with pytest.raises(kn.KontextNetzError):
        kn.schreibe_netz_ply(tmp_path / "f.ply", [(0, 0, 0)], [(1, 2, 3)], [(0, 1, 2)])


@pytest.mark.parametrize("n_rest, grad", [(0, 0), (9, 1), (24, 2), (45, 3)])
def test_sh_grad_aus_der_zahl_der_f_rest(n_rest, grad):
    assert kn.sh_grad(n_rest) == grad


@pytest.mark.parametrize("n_rest", [1, 10, 44, 46])
def test_sh_grad_raet_nicht(n_rest):
    with pytest.raises(kn.KontextNetzError):
        kn.sh_grad(n_rest)


def _mal(m, v):
    return tuple(sum(m[z][k] * v[k] for k in range(3)) for z in range(3))


def test_quaternion_zu_matrix():
    einheit = kn.quaternion_zu_matrix(1, 0, 0, 0)
    assert einheit == ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    # 90° um z: x wird y. Unnormiert gespeichert (Faktor 3) gibt dieselbe Drehung.
    c = math.cos(math.radians(45.0))
    for f in (1.0, 3.0):
        r = kn.quaternion_zu_matrix(f * c, 0, 0, f * c)
        assert _mal(r, (1, 0, 0)) == pytest.approx((0, 1, 0), abs=1e-12)
        assert _mal(r, (0, 0, 1)) == pytest.approx((0, 0, 1), abs=1e-12)
    # Beliebig: orthonormal mit Determinante 1.
    r = kn.quaternion_zu_matrix(0.3, -0.5, 0.7, 0.2)
    for i in range(3):
        for j in range(3):
            assert sum(r[i][k] * r[j][k] for k in range(3)) == pytest.approx(
                1.0 if i == j else 0.0, abs=1e-12)
    det = (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
           - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
           + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))
    assert det == pytest.approx(1.0)
    with pytest.raises(kn.KontextNetzError):
        kn.quaternion_zu_matrix(0, 0, 0, 0)


def test_oben_und_massstab_aus_der_matrix():
    assert kn.oben_und_massstab(None) == ((0.0, 1.0, 0.0), 1.0)
    # Ein Splat mit Z oben: R_x(−90) bildet z auf y ab — oben im Splat ist also z.
    r_x_minus_90 = [1, 0, 0, 5, 0, 0, 1, 0, 0, -1, 0, 2, 0, 0, 0, 1]
    oben, massstab = kn.oben_und_massstab(r_x_minus_90)
    assert oben == pytest.approx((0.0, 0.0, 1.0)) and massstab == pytest.approx(1.0)
    # Doppelt so gross: ein Meter der Welt sind eine halbe Einheit des Splats.
    doppelt = [2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1]
    assert kn.oben_und_massstab(doppelt) == ((0.0, 1.0, 0.0), pytest.approx(2.0))
    # Mit dem Produkt gerechnet: die Matrix bildet `oben` wirklich auf +Y ab.
    m = kontext.pruefe_matrix([0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
                               0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    oben, _ = kn.oben_und_massstab(m)
    bild = [sum(m[4 * z + k] * oben[k] for k in range(3)) for z in range(3)]
    assert bild == pytest.approx([0.0, 1.0, 0.0])
    with pytest.raises(kn.KontextNetzError):
        kn.oben_und_massstab([0.0] * 16)


def _bereich(oben=(0.0, 1.0, 0.0)):
    # Ein Quadrat 20 × 20 m auf der Ebene senkrecht zu `oben`, Boden bei 0.
    u1, u2 = kn._basis(oben)
    punkte = [tuple(a * u1[i] + b * u2[i] for i in range(3))
              for a in range(-10, 11, 2) for b in range(-10, 11, 2)]
    return kn.dichter_bereich(punkte, oben=oben)


@pytest.mark.parametrize("oben", [(0.0, 1.0, 0.0), (0.0, 0.0, 1.0)])
def test_blickwinkel_ring_nach_aussen_und_umlauf_nach_innen(oben):
    bereich = _bereich(oben)
    assert bereich["boden"] == pytest.approx(0.0, abs=1e-9)
    ansichten = kn.blickwinkel(bereich, oben=oben, massstab=1.0, je_kreis=8)
    ring = [a for a in ansichten if a["art"] == "ring"]
    umlauf = [a for a in ansichten if a["art"] == "umlauf"]
    assert len(ring) == 8 * len(kn.RING_NEIGUNGEN_GRAD) and len(umlauf) == 8
    # Der Ring steht EIN Punkt, auf Augenhöhe über dem Boden, in der waagrechten Mitte.
    auge = ring[0]["auge"]
    assert all(a["auge"] == auge for a in ring)
    assert kn._punkt(auge, oben) == pytest.approx(kn.AUGENHOEHE_M)
    richtungen = []
    for a in ring:
        d = [a["ziel"][i] - auge[i] for i in range(3)]
        # Die Neigung stimmt …
        assert math.degrees(math.asin(kn._punkt(d, oben))) == pytest.approx(a["neigung_grad"])
        richtungen.append(d)
    # … und waagrecht zeigen sie in alle Richtungen nach aussen: Ihr Mittel ist null.
    mittel = [sum(d[i] for d in richtungen) / len(richtungen) for i in range(3)]
    waagrecht = [mittel[i] - kn._punkt(mittel, oben) * oben[i] for i in range(3)]
    assert max(abs(w) for w in waagrecht) < 1e-9
    # Der Umlauf blickt von aussen auf den Ring, erhöht.
    abstand = kn.UMLAUF_ABSTAND_FAKTOR * bereich["halbmesser"]
    for a in umlauf:
        assert a["ziel"] == auge
        d = [a["auge"][i] - auge[i] for i in range(3)]
        assert math.sqrt(kn._punkt(d, d)) == pytest.approx(abstand)
        assert kn._punkt(d, oben) > 0.5 * abstand * math.sin(
            math.radians(kn.UMLAUF_ERHEBUNG_GRAD))


def test_augenhoehe_gilt_in_metern_der_welt():
    halb = kn.blickwinkel(_bereich(), massstab=2.0, je_kreis=1)
    assert halb[0]["auge"][1] == pytest.approx(kn.AUGENHOEHE_M / 2.0)
    with pytest.raises(kn.KontextNetzError):
        kn.blickwinkel(_bereich(), je_kreis=0)
    with pytest.raises(kn.KontextNetzError):
        kn.dichter_bereich([(0, 0, 0)])


def test_ansichtsmatrix_wie_opencv():
    v = kn.ansicht_matrix((1.0, 2.0, 3.0), (1.0, 2.0, -7.0), (0.0, 1.0, 0.0))

    def abbilden(p):
        return tuple(v[4 * z] * p[0] + v[4 * z + 1] * p[1] + v[4 * z + 2] * p[2]
                     + v[4 * z + 3] for z in range(3))

    assert abbilden((1.0, 2.0, 3.0)) == pytest.approx((0, 0, 0))
    assert abbilden((1.0, 2.0, -7.0)) == pytest.approx((0, 0, 10))   # Blick = +z
    assert abbilden((1.0, 3.0, 3.0)) == pytest.approx((0, -1, 0))    # oben = −y
    assert abbilden((2.0, 2.0, 3.0)) == pytest.approx((1, 0, 0))     # rechts = +x
    assert v[12:] == (0.0, 0.0, 0.0, 1.0)
    with pytest.raises(kn.KontextNetzError):
        kn.ansicht_matrix((0, 0, 0), (0, 5, 0), (0, 1, 0))


def test_intrinsik():
    ki = kn.intrinsik(640, 480, 90.0)
    assert ki["fx"] == pytest.approx(320.0) and ki["fy"] == ki["fx"]
    assert (ki["cx"], ki["cy"]) == (320.0, 240.0)
    assert ki["K"] == pytest.approx((320.0, 0, 320.0, 0, 320.0, 240.0, 0, 0, 1))
    assert kn.intrinsik(100, 50, 60.0)["fx"] == pytest.approx(50.0 / math.tan(math.radians(30)))
    assert kn.bildhoehe(640) == 480 and kn.bildhoehe(160) == 120
    for falsch in ((0, 10, 90.0), (10, 10, 0.0), (10, 10, 180.0)):
        with pytest.raises(kn.KontextNetzError):
            kn.intrinsik(*falsch)


def test_netz_parameter_tragen_fassung_und_gesetzte_zahlen():
    p = kn.netz_parameter()
    assert p["fassung"] == kn.FASSUNG and p["voxel_m"] == kn.VOXEL_M
    assert p["gesetzt"]["augenhoehe_m"] == kn.AUGENHOEHE_M
    assert kn.netz_parameter(voxel_m=0.1) != p
    for falsch in ({"voxel_m": 0.0}, {"aufloesung": 4}, {"je_kreis": 0}):
        with pytest.raises(kn.KontextNetzError):
            kn.netz_parameter(**falsch)


# ======================================================================================
# 2 · Die Naht mit einer Starter-Attrappe
# ======================================================================================

class _Lauf:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class _Starter:
    """Schreibt, was der Runner schreiben würde — und merkt sich jeden Aufruf."""

    def __init__(self, *, netz=True, status="ok", code=0):
        self.aufrufe, self.netz, self.status, self.code = [], netz, status, code

    def __call__(self, cmd, timeout):
        self.aufrufe.append((list(cmd), timeout))
        ziel = Path(cmd[3])
        bericht = Path(cmd[cmd.index("--report") + 1])
        if self.netz:
            _kleines_netz(ziel)
        bericht.write_text(json.dumps({
            "status": self.status, "error": None if self.status == "ok" else "kaputt",
            "renderer": "gsplat", "geraet": "cuda",
            "netz": {"datei": ziel.name, "ecken": 4, "dreiecke": 2},
            "blickwinkel": {"gesamt": 48}, "zeiten_s": {"gesamt_s": 1.5}}),
            encoding="utf-8")
        return _Lauf(self.code, "", "")


@pytest.fixture
def splat_python(tmp_path, monkeypatch):
    python = tmp_path / "venv-splat-python"
    python.write_text("#!/bin/sh\n")
    monkeypatch.setenv(seams.SPLAT_PYTHON_ENV, str(python))
    monkeypatch.delenv(seams.ZEITFAKTOR_ENV, raising=False)
    return python


def test_finde_splat_python(tmp_path, monkeypatch, splat_python):
    assert seams.finde_splat_python() == str(splat_python)
    monkeypatch.setenv(seams.SPLAT_PYTHON_ENV, str(tmp_path / "gibt-es-nicht"))
    with pytest.raises(seams.SeamError, match="nicht eingerichtet"):
        seams.finde_splat_python()


def test_naht_startet_den_runner_mit_frist_und_parametern(tmp_path, splat_python):
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    starter = _Starter()
    m = [1, 0, 0, 5, 0, 0, 1, 0, 0, -1, 0, 2, 0, 0, 0, 1]     # Splat mit Z oben
    bericht = seams.splat_zu_netz(splat, matrix=m, speicher=tmp_path / "speicher",
                                  voxel_m=0.1, _starte=starter)
    (cmd, frist), = starter.aufrufe
    assert cmd[:3] == [str(splat_python), str(seams.SPLAT_RUNNER), str(splat)]
    assert frist == seams.GESAMTFRIST_SPLAT_S
    werte = {cmd[i]: cmd[i + 1] for i in range(4, len(cmd) - 1) if cmd[i].startswith("--")}
    assert werte["--voxel-m"] == "0.1" and werte["--renderer"] == "gsplat"
    assert "--oben=0.0,0.0,1.0" in cmd and werte["--massstab"] == "1.0"
    assert werte["--aufloesung"] == str(kn.AUFLOESUNG_PX)
    assert werte["--blickwinkel"] == str(kn.BLICKWINKEL_JE_KREIS)
    assert bericht["zwischenspeicher"]["treffer"] is False
    assert Path(bericht["netz_ply"]).is_file()
    assert bericht["netz"]["sha256"] == kn.netz_kennzahlen(bericht["netz_ply"])["sha256"]
    assert bericht["splat"]["sha256"] == kontext.fingerabdruck(splat)["sha256"]


def test_naht_speichert_nach_inhalt(tmp_path, splat_python):
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100, startwert=1)
    starter = _Starter()
    speicher = tmp_path / "speicher"
    erst = seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)
    # Gleicher Inhalt — auch unter anderem Namen — ist ein Treffer, ohne Lauf.
    kopie = tmp_path / "anderswo" / "kopie.ply"
    kopie.parent.mkdir()
    shutil.copyfile(splat, kopie)
    zweit = seams.splat_zu_netz(kopie, speicher=speicher, ziel=tmp_path / "n.ply",
                                _starte=starter)
    assert len(starter.aufrufe) == 1 and zweit["zwischenspeicher"]["treffer"] is True
    assert zweit["zwischenspeicher"]["schluessel"] == erst["zwischenspeicher"]["schluessel"]
    assert Path(zweit["netz_ply"]) == tmp_path / "n.ply" and (tmp_path / "n.ply").is_file()
    # Anderer Inhalt unter demselben Namen: kein Treffer.
    _erzeuger().erzeuge_splat(splat, punkte=100, startwert=2)
    seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)
    assert len(starter.aufrufe) == 2
    # Andere Parameter: kein Treffer.
    seams.splat_zu_netz(splat, speicher=speicher, voxel_m=0.2, _starte=starter)
    assert len(starter.aufrufe) == 3
    # Ein verdorbenes Netz im Speicher ist kein Treffer, sondern wird neu gerechnet.
    netz = Path(seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)["netz_ply"])
    netz.write_bytes(b"ply\nkaputt")
    seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)
    assert len(starter.aufrufe) == 4


@pytest.mark.parametrize("starter, stichwort", [
    (_Starter(code=1, status="error"), "fehlgeschlagen"),
    (_Starter(netz=False), "meldete Erfolg"),
    (_Starter(status="error"), "keinen Erfolg"),
])
def test_naht_glaubt_keinem_erfolg_ohne_netz(tmp_path, splat_python, starter, stichwort):
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    with pytest.raises(seams.SeamError, match=stichwort):
        seams.splat_zu_netz(splat, speicher=tmp_path / "sp", _starte=starter)
    # Gescheitertes wird nicht abgelegt.
    assert not list((tmp_path / "sp").rglob("netz.ply"))


def test_naht_verlangt_eine_frist(tmp_path, splat_python):
    with pytest.raises(seams.SeamError, match="timeout=None"):
        seams.splat_zu_netz(tmp_path / "s.ply", timeout=None, _starte=_Starter())


# ======================================================================================
# 3 · Der Rückfall auf die Kugeln
# ======================================================================================

def test_ohne_bruecke_bleiben_die_kugeln_mit_satz(tmp_path, monkeypatch):
    monkeypatch.setenv(seams.SPLAT_PYTHON_ENV, str(tmp_path / "fehlt" / "python"))
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    v = seams.kontext_vorbereiten(splat)
    assert v["weg"] == "kugeln" and v["ply"] == str(splat) and v["netz"] is None
    assert v["hinweis"] == kn.SATZ_KUGELN_NICHT_EINGERICHTET
    assert "Konfetti" in v["hinweis"] and str(tmp_path) not in v["grund"]


def test_eine_gescheiterte_bruecke_sagt_es_anders(tmp_path):
    def scheitert(ply, **kw):
        raise seams.SeamError(f"Splat→Netz fehlgeschlagen: {tmp_path}/geheim/x.ply kaputt")

    v = seams.kontext_vorbereiten(tmp_path / "s.ply", _splat_zu_netz=scheitert)
    assert v["weg"] == "kugeln" and v["hinweis"] == kn.SATZ_KUGELN_GESCHEITERT
    assert "x.ply kaputt" in v["grund"] and str(tmp_path) not in v["grund"]


def test_ein_geliefertes_netz_geht_ohne_bruecke_durch(tmp_path):
    _kleines_netz(tmp_path / "n.ply")

    def nie(*a, **k):
        raise AssertionError("die Bruecke darf fuer ein Netz nicht laufen")

    v = seams.kontext_vorbereiten(tmp_path / "n.ply", _splat_zu_netz=nie)
    assert v["weg"] == "netz" and v["netz"]["dreiecke"] == 2 and v["hinweis"] is None


def test_mit_bruecke_das_netz_samt_kennzahlen(tmp_path, splat_python):
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    v = seams.kontext_vorbereiten(
        splat, _splat_zu_netz=lambda ply, **kw: seams.splat_zu_netz(
            ply, speicher=tmp_path / "sp", _starte=_Starter(), **kw))
    assert v["weg"] == "netz" and kn.art_der_datei(v["ply"]) == "netz"
    assert v["netz"]["dreiecke"] == 2 and v["netz"]["blickwinkel"] == 48
    assert v["netz"]["zwischenspeicher_treffer"] is False
    assert str(tmp_path) not in json.dumps(v["netz"])


def test_die_kugel_notloesung_ist_kein_speichertreffer():
    """Sonst lieferte ein alter Eintrag weiter das Konfetti, sobald die Brücke da ist."""
    kugeln = {"depth_png": None, "kontext": {"quelle": kn.QUELLE_SPLAT}}
    netz = {"depth_png": None, "kontext": {"quelle": kn.QUELLE_NETZ}}
    m_kugeln = kette._cache_maengel(kette.ART_MULTIPASS, kugeln, {})
    assert any("Notloesung" in m for m in m_kugeln)
    assert kette._cache_maengel(kette.ART_MULTIPASS, netz, {}) == []
    assert kette._cache_maengel(kette.ART_MULTIPASS, {"depth_png": None}, {}) == []


def test_der_kettenknoten_bereitet_den_kontext_vor(tmp_path, monkeypatch):
    gesehen = {}

    def attrappe(glb, out, **kw):
        gesehen.update(kw)
        return {"status": "ok", "kontext": {"quelle": kn.QUELLE_NETZ}}

    _kleines_netz(tmp_path / "netz.ply")
    monkeypatch.setattr(seams, "glb_zu_multipass", attrappe)
    monkeypatch.setattr(seams, "kontext_vorbereiten", lambda ply, matrix=None: {
        "ply": str(tmp_path / "netz.ply"), "weg": "netz", "netz": {"dreiecke": 2},
        "grund": None, "hinweis": None})
    knoten = Knoten(id="multipass", art=kette.ART_MULTIPASS,
                    params={"aufloesung": 32, "samples": 1, "beauty": True,
                            "material_id": True, "kontext_ply": "u.ply"})
    bericht = kette._fuehre_multipass(knoten=knoten, eingaben=[{"glb_path": "m.glb",
                                                                "up_axis": "Y"}],
                                      out_dir=tmp_path)
    assert gesehen["kontext_ply"] == str(tmp_path / "netz.ply")
    assert bericht["kontext_weg"]["weg"] == "netz"


# ======================================================================================
# 4 · Glätten nur auf dem Kugel-Weg
# ======================================================================================

def test_geglaettet_wird_nur_der_kugel_weg():
    assert kontext.wird_geglaettet({"kontext": {"quelle": kn.QUELLE_SPLAT}})
    assert kontext.wird_geglaettet({})
    assert kontext.wird_geglaettet(None)
    assert not kontext.wird_geglaettet({"kontext": {"quelle": kn.QUELLE_NETZ}})


def test_tiefe_mit_netz_wird_nicht_gemittelt(tmp_path):
    from aiimaging import bildschreiben

    b, h = 6, 1
    werte = [10.0, 10.0, 1e10, 30.0, 1e10, 1e10]
    umgebung = [False, False, True, True, True, False]
    mit = bildschreiben.tiefe_exr_zu_png("x.exr", tmp_path / "a.png", umgebung=umgebung,
                                         _leser=lambda p: (list(werte), b, h))
    ohne = bildschreiben.tiefe_exr_zu_png("x.exr", tmp_path / "b.png", umgebung=umgebung,
                                          glaetten=False, _leser=lambda p: (list(werte), b, h))
    assert mit["umgebung"]["glaettung"]["n_gefuellt"] >= 1
    assert ohne["umgebung"]["glaettung"]["angewandt"] is False


# ======================================================================================
# 5 · Der Abholer
# ======================================================================================

def _glb(tmp_path) -> Path:
    werkzeug = WURZEL / "tools" / "make_test_glb.py"
    spez = importlib.util.spec_from_file_location("make_test_glb_netzprobe", werkzeug)
    erzeuger = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(erzeuger)
    glb = tmp_path / "m.glb"
    glb.write_bytes(erzeuger.baue_glb([("Haus", (-4.0, 0.0, -3.0), (4.0, 6.0, 3.0))]))
    return glb


def _durchlauf(tmp_path, **naht):
    gesehen = []

    def multipass(glb, aus, **kw):
        gesehen.append(kw)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False, _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1), **naht)
    splat = Path(tmp_path) / "home" / "nutzer" / "umgebung.ply"
    splat.parent.mkdir(parents=True)
    _erzeuger().erzeuge_splat(splat, punkte=100)
    kontext_ = kosmo_szene.kontext_aus_szene({"kind": "splat", "ply": str(splat),
                                              "fit": "passpunkte"})
    szene = {"kameras": [{"kuerzel": "s", "richtung": "s"}], "aufloesung": 64, "hoehe": 64,
             "samples": 1, "prompt": "a house", "kontext": kontext_}
    ergebnis = verarbeite({"modell": _glb(tmp_path), "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path, "szene": szene})
    return ergebnis, gesehen, splat, szene


def _hinweise(ergebnis) -> list[str]:
    vertrag = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"score": 0.9, "bestanden": True},
        je_kamera=ergebnis["kameras"])
    return vertrag["qa"]["verdict"].get("hinweise") or []


def test_abholer_ohne_bruecke_kugeln_mit_hinweis(tmp_path, monkeypatch):
    monkeypatch.setenv(seams.SPLAT_PYTHON_ENV, str(tmp_path / "fehlt" / "python"))
    ergebnis, gesehen, splat, szene = _durchlauf(tmp_path)
    assert gesehen[0]["kontext_ply"] == str(splat)
    vermerk = ergebnis["kameras"][0][kosmo_szene.URTEIL_KONTEXT]
    assert vermerk["weg"] == "kugeln" and vermerk["netz"] is None
    assert kn.SATZ_KUGELN_NICHT_EINGERICHTET in _hinweise(ergebnis)
    assert szene["kontext"]["weg"] == "kugeln"          # auch der Befund des Auftrags
    assert "nutzer" not in json.dumps(vermerk)


def test_abholer_mit_netz_attrappe_gibt_das_netz_weiter(tmp_path):
    netz = tmp_path / "netz.ply"
    _kleines_netz(netz)
    aufrufe = []

    def vorbereiten(ply, matrix=None):
        aufrufe.append(ply)
        return {"ply": str(netz), "weg": "netz", "grund": None, "hinweis": None,
                "netz": {"ecken": 4, "dreiecke": 2, "sha256": "ab" * 32,
                         "quelle": "splat-bruecke", "blickwinkel": 48}}

    ergebnis, gesehen, splat, _ = _durchlauf(tmp_path, _kontext_vorbereiten=vorbereiten)
    assert aufrufe == [str(splat)]                       # einmal je Auftrag
    assert gesehen[0]["kontext_ply"] == str(netz)
    vermerk = ergebnis["kameras"][0][kosmo_szene.URTEIL_KONTEXT]
    assert vermerk["weg"] == "netz" and vermerk["netz"]["dreiecke"] == 2
    hinweise = _hinweise(ergebnis)
    assert not any("NOTLOESUNG" in h for h in hinweise)
    assert any(h.startswith("UMGEBUNG: Splat 'umgebung.ply'") for h in hinweise)


def test_vermerk_liest_den_weg_auch_aus_dem_bericht():
    k = {"art": "splat", "datei": "u.ply", "hinweise": []}
    assert kosmo_szene.kontext_vermerk(k, {"kontext": {"quelle": kn.QUELLE_NETZ}})["weg"] == "netz"
    assert kosmo_szene.kontext_vermerk(k, {"kontext": {"quelle": kn.QUELLE_SPLAT}})["weg"] == "kugeln"
    assert kosmo_szene.kontext_vermerk(k)["weg"] is None


# ======================================================================================
# 6 · Die Blender-Stufe lädt ein Netz als Netz
# ======================================================================================

def _blender_fehlt() -> bool:
    return not shutil.which("blender") and not Path("/opt/blender/blender").exists()


def _ifc_fehlt() -> bool:
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


ohne_kette = pytest.mark.skipif(_blender_fehlt() or _ifc_fehlt(),
                                reason="Blender oder .venv-ifc fehlt")

#: Wie in tests/test_kontext_splat.py: Mitte des Testbaus, Boden 0,6 m unter der Platte.
VERSATZ = (4.0, -0.6, -2.5)
LAUF = dict(up_axis="Y", kamera="s", aufloesung=160, hoehe=120, samples=4)
WAND_FARBE = (200, 60, 50)
BODEN_FARBE = (60, 140, 60)


def _umgebungsnetz(pfad: Path) -> dict:
    """Ein farbiges Netz in der glTF-Welt (Y oben): Boden 30 × 30 m, Wand dahinter.

    Dieselbe Lage wie der synthetische Splat (``tools/make_test_splat.py``): Wand bei
    z = −12, 18 m breit, 8 m hoch.
    """
    ecken, farben, dreiecke = [], [], []

    def viereck(a, b, c, d, farbe):
        i = len(ecken)
        ecken.extend([a, b, c, d])
        farben.extend([farbe] * 4)
        dreiecke.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])

    for gx in range(-3, 3):                              # Boden in 5-m-Feldern
        for gz in range(-3, 3):
            x0, z0 = 5.0 * gx, 5.0 * gz
            viereck((x0, 0, z0), (x0, 0, z0 + 5), (x0 + 5, 0, z0 + 5), (x0 + 5, 0, z0),
                    BODEN_FARBE)
    viereck((-9, 0, -12), (9, 0, -12), (9, 8, -12), (-9, 8, -12), WAND_FARBE)
    kn.schreibe_netz_ply(pfad, ecken, farben, dreiecke)
    return {"ecken": len(ecken), "dreiecke": len(dreiecke),
            "huellbox": [[-15.0, 0.0, -15.0], [15.0, 8.0, 15.0]]}


@pytest.fixture(scope="module")
def netzlaeufe(tmp_path_factory):
    if _blender_fehlt() or _ifc_fehlt():
        pytest.skip("Blender oder .venv-ifc fehlt")
    tmp = tmp_path_factory.mktemp("kontext_netz")
    ifc = tmp / "bau.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc)], check=True,
                   capture_output=True, cwd=WURZEL)
    glb = tmp / "bau.glb"
    assert seams.ifc_zu_glb(ifc, glb)["status"] == "ok"
    netz = tmp / "umgebung_netz.ply"
    erzeugt = _umgebungsnetz(netz)
    matrix = [1.0, 0.0, 0.0, VERSATZ[0], 0.0, 1.0, 0.0, VERSATZ[1],
              0.0, 0.0, 1.0, VERSATZ[2], 0.0, 0.0, 0.0, 1.0]
    ohne = seams.glb_zu_multipass(glb, tmp / "ohne", **LAUF)
    mit = seams.glb_zu_multipass(glb, tmp / "mit", kontext_ply=netz, kontext_matrix=matrix,
                                 **LAUF)
    return {"ohne": ohne, "mit": mit, "erzeugt": erzeugt, "netz": netz}


def _tiefe_geometrie(bericht) -> int:
    werte, _, _ = bildlesen.lies_exr_tiefe_stdlib(bericht["depth_exr"])
    return sum(1 for w in werte if math.isfinite(w) and w < 1.0e7)


@ohne_kette
def test_netz_wird_als_netz_geladen_und_ist_in_der_tiefe(netzlaeufe):
    mit = netzlaeufe["mit"]
    assert mit["status"] == "ok", mit.get("error")
    k = mit["kontext"]
    assert k["quelle"] == kn.QUELLE_NETZ and k["datei"] == "umgebung_netz.ply"
    assert (k["ecken"], k["dreiecke"]) == (netzlaeufe["erzeugt"]["ecken"],
                                          netzlaeufe["erzeugt"]["dreiecke"])
    assert k["punkte_gerendert"] is None and "Eckpunktfarbe" in k["farbe"]
    assert _tiefe_geometrie(mit) > 1.5 * _tiefe_geometrie(netzlaeufe["ohne"])


@ohne_kette
def test_netz_bauwerksmaske_gleich_und_kontext_in_der_tabelle(netzlaeufe):
    ohne = maske.maske_aus_bericht(netzlaeufe["ohne"])
    mit = maske.maske_aus_bericht(netzlaeufe["mit"])
    assert ohne["gemessen"] and mit["gemessen"], mit.get("grund")
    assert mit["maske"] == ohne["maske"]
    assert mit["n_kontext"] > 0
    # Nicht geschlossen — das Netz hat echte Lücken (kontext.wird_geglaettet).
    assert sum(mit["kontext_pixel"]) == mit["n_kontext"]
    tabelle = netzlaeufe["mit"]["material_id_tabelle"]
    assert tabelle[-1]["quelle"] == "kontext" and tabelle[-1]["name"] == "Kontext_Netz"
    assert tabelle[:-1] == netzlaeufe["ohne"]["material_id_tabelle"]
    assert netzlaeufe["mit"]["kontext"]["verdeckung"]["anteil"] == 0.0


@ohne_kette
def test_netz_huellbox_kamera_und_zaehlung_unveraendert(netzlaeufe):
    for feld in ("bbox", "bbox_bauwerk", "bbox_bauwerk_note", "kamera", "n_meshes",
                 "n_materialien", "sonne"):
        assert netzlaeufe["mit"][feld] == netzlaeufe["ohne"][feld], feld
    k = netzlaeufe["mit"]["kontext"]
    lo, hi = netzlaeufe["erzeugt"]["huellbox"]
    ecken = [contracts.blender_gltf_import_dreht(tuple(c + v for c, v in zip(p, VERSATZ)))
             for p in (lo, hi)]
    assert k["huellbox"][0] == pytest.approx(
        [min(ecken[0][i], ecken[1][i]) for i in range(3)], abs=1e-3)
    assert k["huellbox"][1] == pytest.approx(
        [max(ecken[0][i], ecken[1][i]) for i in range(3)], abs=1e-3)
    assert k["zaehlt_zur_bauwerksbox"] is False and k["zaehlt_zur_rahmung"] is False
    assert "/" not in json.dumps({n: w for n, w in k.items()
                                  if n not in ("matrix_bedeutung", "farbe")})


@ohne_kette
def test_netz_ist_im_bild_in_seiner_farbe(netzlaeufe):
    mit = netzlaeufe["mit"]
    umgebung = maske.umgebung_je_bildpunkt(mit)
    farben, _, _ = bildlesen.lies_png_farben(mit["beauty_png"])
    punkte = [f[:3] for f, u in zip(farben, umgebung) if u]
    assert len(punkte) > 100
    # Jeder Umgebungspunkt trägt eine der beiden Farben des Netzes (Emission, kein Licht).
    def nah(f, soll):
        return max(abs(int(a) - b) for a, b in zip(f, soll)) <= 25
    anteil = sum(1 for f in punkte if nah(f, WAND_FARBE) or nah(f, BODEN_FARBE)) / len(punkte)
    assert anteil > 0.9, anteil
    # Die Tiefe wird nach dem Modell normiert, aber nicht gemittelt.
    u = mit["depth_normalisierung"]["umgebung"]
    assert u["nach_modell"] is True and u["glaettung"]["angewandt"] is False


# ======================================================================================
# 7 · Die echte Fusion — mit dem CPU-Ersatzrenderer
# ======================================================================================

ohne_splat_python = pytest.mark.skipif(
    not os.environ.get(seams.SPLAT_PYTHON_ENV),
    reason=f"{seams.SPLAT_PYTHON_ENV} nicht gesetzt (Umgebung mit torch, gsplat, open3d)")


def _netz_lesen(pfad: Path):
    """Ecken und Farben eines Open3D-Netzes, mit der Standardbibliothek."""
    kopf = kn.lies_ply_kopf(pfad)
    ecken = kopf["elemente"][0]
    form = "<" + "".join(kn.PLY_TYPEN[e["typ"]][0] for e in ecken["eigenschaften"])
    groesse = struct.calcsize(form)
    namen = [e["name"] for e in ecken["eigenschaften"]]
    daten = pfad.read_bytes()[kopf["kopf_bytes"]:]
    zeilen = [dict(zip(namen, struct.unpack_from(form, daten, i * groesse)))
              for i in range(ecken["anzahl"])]
    return zeilen


@ohne_splat_python
def test_fusion_mit_dem_ersatzrenderer(tmp_path):
    m = _erzeuger()
    splat = tmp_path / "s.ply"
    erzeugt = m.erzeuge_splat(splat, punkte=12000, startwert=7)
    bericht = seams.splat_zu_netz(splat, renderer="cpu-probe", aufloesung=160,
                                  blickwinkel=8, voxel_m=0.15, speicher=tmp_path / "sp")
    print(json.dumps({k: bericht[k] for k in ("blickwinkel", "netz", "zeiten_s", "splat")},
                     ensure_ascii=False))
    assert bericht["renderer"] == "cpu-probe" and bericht["nur_probe"] is True
    assert bericht["splat"]["dicht"] == erzeugt["dicht"]
    assert bericht["blickwinkel"]["gesamt"] == 8 * (len(kn.RING_NEIGUNGEN_GRAD) + 1)
    z = kn.netz_kennzahlen(bericht["netz_ply"])
    assert z["dreiecke"] > 1000 and z["dreiecke"] == bericht["netz"]["dreiecke"]
    # Hüllbox des Netzes ≈ Hüllbox der dichten Punkte (Fussabdruck und Voxel als Rand).
    lo, hi = erzeugt["huellbox_dicht"]
    n_lo, n_hi = bericht["netz"]["huellbox"]
    for i in range(3):
        assert n_lo[i] == pytest.approx(lo[i], abs=1.0), ("lo", i, n_lo, lo)
        assert n_hi[i] == pytest.approx(hi[i], abs=1.0), ("hi", i, n_hi, hi)
    # Farben aus dem Splat: fast jede Ecke trägt eine der drei Farben des Erzeugers.
    zeilen = _netz_lesen(Path(bericht["netz_ply"]))
    soll = [tuple(round(255 * k) for k in f)
            for f in (m.FARBE_BODEN, m.FARBE_WAND, m.FARBE_QUADER)]
    treffer = sum(1 for e in zeilen
                  if any(max(abs(e["red"] - s[0]), abs(e["green"] - s[1]),
                             abs(e["blue"] - s[2])) <= 30 for s in soll))
    assert treffer / len(zeilen) > 0.9, treffer / len(zeilen)
    # Zweiter Lauf: aus dem Speicher.
    wieder = seams.splat_zu_netz(splat, renderer="cpu-probe", aufloesung=160,
                                 blickwinkel=8, voxel_m=0.15, speicher=tmp_path / "sp")
    assert wieder["zwischenspeicher"]["treffer"] is True


def test_eine_hochachse_mit_minus_kommt_beim_runner_an(tmp_path, splat_python):
    """``auf-20261013-275`` Fehler 1: Am echten Splat ist die Hochachse z. B. (-0.033, …). Als
    eigener Wert nach ``--oben`` hielt argparse ihn für einen Schalter und brach ab."""
    import importlib.util
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    starter = _Starter()
    m = [1, 0, 0, 0, 0, -0.03, -1, 0, 0, 1, -0.03, 0, 0, 0, 0, 1]
    seams.splat_zu_netz(splat, matrix=m, speicher=tmp_path / "sp", _starte=starter)
    (cmd, _frist), = starter.aufrufe
    oben = [a for a in cmd if a.startswith("--oben")]
    assert len(oben) == 1 and oben[0].startswith("--oben=")
    spez = importlib.util.spec_from_file_location("runner_oben", seams.SPLAT_RUNNER)
    runner = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(runner)
    args = runner._parser().parse_args([str(splat), str(tmp_path / "n.ply"), oben[0]])
    assert min(args.oben) < 0                                 # der Wert kam an


def test_die_voxelgroesse_haelt_open3d_am_echten_splat_aus():
    """``auf-20261013-275`` Fehler 2: 5 cm stürzte Open3D ab, 7 cm lief."""
    assert kn.VOXEL_M == 0.07


# ======================================================================================
# 8 · Blickwinkel aus der Aufnahme (13.10.2026, nach auf-20261013-275)
# ======================================================================================
#
# Die Aufnahme ist synthetisch (``tools/make_test_colmap.py``, Regel 3) und wird in jeder
# Probe neu geschrieben — keine Binärdatei im Repo. Das Format ist an pycolmap 4.2.1
# nachgeprüft (Protokoll); pycolmap selbst ist hier nicht im Spiel (GPL-Teile im Rad).

COLMAP_ERZEUGER = WURZEL / "tools" / "make_test_colmap.py"


def _colmap():
    spez = importlib.util.spec_from_file_location("make_test_colmap_probe", COLMAP_ERZEUGER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _ansicht_mal(v, p):
    return tuple(v[4 * z] * p[0] + v[4 * z + 1] * p[1] + v[4 * z + 2] * p[2] + v[4 * z + 3]
                 for z in range(3))


@pytest.mark.parametrize("auge, ziel, oben", [
    ((1.0, 2.0, 3.0), (1.0, 2.0, -7.0), (0.0, 1.0, 0.0)),
    ((-4.0, 1.6, 9.0), (3.0, 0.2, -2.0), (0.0, 1.0, 0.0)),
    ((0.5, -2.0, 0.3), (2.0, 7.0, 1.0), (0.0, 0.0, 1.0)),
])
def test_colmap_pose_ist_die_ansichtsmatrix(auge, ziel, oben):
    """COLMAP ``cam_from_world`` und :func:`ansicht_matrix` folgen derselben Konvention
    (OpenCV): Die Pose geht ohne Umklappen als Ansichtsmatrix an gsplat und Open3D."""
    v = kn.ansicht_matrix(auge, ziel, oben)
    r = [list(v[0:3]), list(v[4:7]), list(v[8:11])]
    q = _colmap().quaternion_aus_matrix(r)
    pose = kn.pose_zu_ansicht(q, (v[3], v[7], v[11]))
    assert pose == pytest.approx(v, abs=1e-12)
    assert kn.kamerazentrum(q, (v[3], v[7], v[11])) == pytest.approx(auge, abs=1e-12)
    # Und dieselbe Bedeutung: Das Ziel liegt vor der Kamera auf der Achse, oben ist −y.
    vorn = _ansicht_mal(pose, ziel)
    assert vorn[0] == pytest.approx(0.0, abs=1e-9) and vorn[1] == pytest.approx(0.0, abs=1e-9)
    assert vorn[2] > 0
    hoch = tuple(a + o for a, o in zip(auge, oben))
    assert _ansicht_mal(pose, hoch)[1] < 0


@pytest.mark.parametrize("text", [False, True])
def test_colmap_aufnahme_mit_rig_wird_gelesen(tmp_path, text):
    befund = _colmap().schreibe_aufnahme(tmp_path / "sparse" / "0", augenblicke=6, punkte=50,
                                         text=text)
    a = kn.lies_aufnahme(tmp_path / "sparse" / "0")
    assert a["format"] == ("txt" if text else "bin") and a["rig"] is True
    assert len(a["bilder"]) == 24 and len(a["augenblicke"]) == 6
    # Je Augenblick die vier Rig-Kameras, nach Kamera geordnet.
    assert [[a["bilder"][i]["kamera"] for i in ab] for ab in a["augenblicke"]] == [[1, 2, 3, 4]] * 6
    k = a["kameras"][1]
    assert (k["modell"], k["breite"], k["hoehe"], k["perspektivisch"]) == ("PINHOLE", 1086,
                                                                           1086, True)
    assert k["fx"] == pytest.approx(543.0) and k["cx"] == pytest.approx(543.0)
    # Die vier Kameras eines Augenblicks stehen am selben Ort, auf dem Weg.
    for nr, ab in enumerate(a["augenblicke"]):
        zentren = [kn.kamerazentrum(a["bilder"][i]["q"], a["bilder"][i]["t"]) for i in ab]
        for z in zentren:
            assert z == pytest.approx(befund["zentren"][nr], abs=1e-9)
    # Die Punkte samt Spuren: alle, und als Stichprobe jeder zweite.
    assert len(kn.lies_punkte3d(tmp_path / "sparse" / "0")) == 50
    assert len(kn.lies_punkte3d(tmp_path / "sparse" / "0", hoechstens=25)) == 25


def test_colmap_ohne_frames_ist_jedes_bild_ein_augenblick(tmp_path):
    _colmap().schreibe_aufnahme(tmp_path, augenblicke=3, punkte=10, mit_frames=False)
    a = kn.lies_aufnahme(tmp_path)
    assert a["rig"] is False and len(a["augenblicke"]) == 12
    assert all(len(ab) == 1 for ab in a["augenblicke"])
    namen = [a["bilder"][ab[0]]["name"] for ab in a["augenblicke"]]
    assert namen == sorted(namen)


def test_colmap_unlesbares_wird_abgewiesen(tmp_path):
    with pytest.raises(kn.KontextNetzError, match="Keine COLMAP-Aufnahme"):
        kn.lies_aufnahme(tmp_path)
    _colmap().schreibe_aufnahme(tmp_path, augenblicke=2, punkte=5)
    roh = (tmp_path / "images.bin").read_bytes()
    (tmp_path / "images.bin").write_bytes(roh[:len(roh) // 2])
    with pytest.raises(kn.KontextNetzError, match="endet"):
        kn.lies_aufnahme(tmp_path)
    (tmp_path / "images.bin").write_bytes(roh)
    roh = (tmp_path / "cameras.bin").read_bytes()
    (tmp_path / "cameras.bin").write_bytes(roh[:12] + struct.pack("<i", 99) + roh[16:])
    with pytest.raises(kn.KontextNetzError, match="Modell 99"):
        kn.lies_aufnahme(tmp_path)


@pytest.mark.parametrize("n, k, erwartet", [
    (240, 60, None), (10, 4, [0, 3, 6, 9]), (5, 9, [0, 1, 2, 3, 4]), (7, 1, [3]),
    (0, 5, []), (5, 0, []),
])
def test_augenblicke_gleichmaessig_mit_erstem_und_letztem(n, k, erwartet):
    gewaehlt = kn.waehle_augenblicke(n, k)
    if erwartet is not None:
        assert gewaehlt == erwartet
    else:
        assert len(gewaehlt) == 60 and len(set(gewaehlt)) == 60
        assert gewaehlt[0] == 0 and gewaehlt[-1] == 239
        schritte = {b - a for a, b in zip(gewaehlt, gewaehlt[1:])}
        assert schritte <= {4, 5}                  # 239 / 59 ≈ 4,05


def test_aufnahme_blickwinkel_alle_rig_kameras_je_augenblick(tmp_path):
    """Am echten Splat: 4 Kameras × 240 Augenblicke, höchstens 240 Bilder → 60 Augenblicke
    mit je allen vier Kameras, auf die Renderbreite skaliert, quadratisch."""
    _colmap().schreibe_aufnahme(tmp_path, augenblicke=240, punkte=10)
    a = kn.lies_aufnahme(tmp_path)
    ansichten, auswahl = kn.aufnahme_blickwinkel(a, breite=640, hoechstens=240)
    assert len(ansichten) == 240 and auswahl["augenblicke_gewaehlt"] == 60
    assert auswahl["kameras_je_augenblick"] == 4 and auswahl["bilder_gesamt"] == 960
    je = {}
    for v in ansichten:
        je.setdefault(v["augenblick"], []).append(v["kamera"])
    assert all(sorted(k) == [1, 2, 3, 4] for k in je.values())
    ki = ansichten[0]["ki"]
    assert (ki["breite"], ki["hoehe"]) == (640, 640)
    assert ki["fx"] == pytest.approx(543.0 * 640 / 1086) and ki["cx"] == pytest.approx(320.0)
    assert ansichten[0]["ansicht"] == kn.pose_zu_ansicht(a["bilder"][ansichten[0]["bild"]]["q"],
                                                         a["bilder"][ansichten[0]["bild"]]["t"])
    # Ein Fischauge wird ausgelassen und gezählt, nicht als Lochkamera missdeutet.
    a["kameras"][2] = dict(a["kameras"][2], modell="OPENCV_FISHEYE", perspektivisch=False)
    ansichten, auswahl = kn.aufnahme_blickwinkel(a, breite=640, hoechstens=240)
    assert len(ansichten) == 180 and auswahl["ausgelassen_nicht_perspektivisch"] == 60
    for k in a["kameras"].values():
        k["perspektivisch"] = False
    with pytest.raises(kn.KontextNetzError, match="kein Blickwinkel"):
        kn.aufnahme_blickwinkel(a)


def test_intrinsik_skaliert_haelt_das_seitenverhaeltnis():
    k = {"modell": "PINHOLE", "perspektivisch": True, "breite": 1600, "hoehe": 1200,
         "fx": 1000.0, "fy": 1010.0, "cx": 801.0, "cy": 598.0}
    ki = kn.intrinsik_skaliert(k, 640)
    assert (ki["breite"], ki["hoehe"]) == (640, 480)
    assert ki["K"] == pytest.approx((400.0, 0, 320.4, 0, 404.0, 239.2, 0, 0, 1))
    with pytest.raises(kn.KontextNetzError, match="keine Lochkamera"):
        kn.intrinsik_skaliert(dict(k, perspektivisch=False), 640)


def test_gleichheit_echte_zahlen_gehen_durch_verschoben_nicht():
    """Die Zahlen der HomeStation am echten Splat (13.10.2026): Median 0,0274, P90 0,0877
    Einheiten bei einer dichten Ausdehnung von 4,43 × 1,04 × 10,23 Einheiten, 89 % der
    Kameras in der unerweiterten Box. Das muss klar durchgehen."""
    diag = math.sqrt(4.43 ** 2 + 1.04 ** 2 + 10.23 ** 2)
    echt = kn.gleichheit_befund(median=0.0274, p90=0.0877, diagonale=diag, kameras_innen=0.89,
                                n_punkte=20000, n_kameras=960)
    assert echt["gleich"] is True and echt["grund"] is None
    assert echt["median_rel"] < kn.GLEICH_MEDIAN_MAX / 3          # mit Luft
    assert echt["p90_rel"] < kn.GLEICH_P90_MAX / 4
    # 10 m verschoben — am echten Splat 1 Einheit ≈ 6,22 m, also 1,6 Einheiten.
    weg = kn.gleichheit_befund(median=1.6, p90=1.7, diagonale=diag, kameras_innen=0.89,
                               n_punkte=20000, n_kameras=960)
    assert weg["gleich"] is False and "nicht im selben System" in weg["grund"]
    assert "Median" in weg["grund"] and "P90" in weg["grund"]
    draussen = kn.gleichheit_befund(median=0.0274, p90=0.0877, diagonale=diag,
                                    kameras_innen=0.2, n_punkte=20000, n_kameras=960)
    assert draussen["gleich"] is False and "Kamerazentren" in draussen["grund"]
    ohne = kn.gleichheit_befund(median=None, p90=None, diagonale=diag, kameras_innen=1.0,
                                n_punkte=0, n_kameras=960)
    assert ohne["gleich"] is False and "nicht pruefbar" in ohne["grund"]


def test_huelle_und_anteil_innen():
    lo, hi = kn.huelle_erweitert((0, 0, 0), (4, 2, 10), 0.25)
    assert lo == (-1.0, -0.5, -2.5) and hi == (5.0, 2.5, 12.5)
    assert kn.anteil_innen([(0, 0, 0), (5, 2.5, 12.5), (6, 0, 0), (0, 0, -3)], lo, hi) == 0.5
    assert kn.anteil_innen([], lo, hi) == 0.0


def test_blockwache_vergroessert_den_voxel_genug():
    """auf-20261013-275: 435 000 Blöcke bei 5 cm stürzten ab. Der neue Voxel muss darunter."""
    assert kn.voxel_fuer_bloecke(0.05, 200_000) == 0.05
    neu = kn.voxel_fuer_bloecke(0.05, 435_000)
    assert 435_000 * (0.05 / neu) ** 2 < kn.BLOECKE_MAX
    assert kn.voxel_fuer_bloecke(0.05, 260_000) == pytest.approx(0.05 * 1.25)


def test_neue_gesetzte_zahlen_im_speicherschluessel():
    g = kn.netz_parameter()["gesetzt"]
    assert g["aufnahme_blicke_max"] == kn.AUFNAHME_BLICKE_MAX == 240
    assert g["bloecke_max"] == kn.BLOECKE_MAX and g["gleich_median_max"] == kn.GLEICH_MEDIAN_MAX
    assert kn.FASSUNG == 3          # 3 seit auf-20261013-276: Tiefenfilter, Masken, Ordnung


# --- die Konvention: woher der Ordner kommt -------------------------------------------

def test_aufnahme_kandidaten_neben_dem_splat(tmp_path):
    ply = tmp_path / "projekt" / "exports" / "umgebung.ply"
    assert kn.aufnahme_kandidaten(ply) == [
        tmp_path / "projekt" / "exports" / "sparse" / "0",
        tmp_path / "projekt" / "sparse" / "0",
        tmp_path / "projekt" / "exports" / "umgebung.colmap"]


@pytest.mark.parametrize("ort", ["daneben", "hoeher", "stamm"])
def test_finde_aufnahme_neben_dem_splat(tmp_path, monkeypatch, ort):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    ply = tmp_path / "p" / "exports" / "umgebung.ply"
    ordner = {"daneben": ply.parent / "sparse" / "0", "hoeher": ply.parent.parent / "sparse" / "0",
              "stamm": ply.parent / "umgebung.colmap"}[ort]
    _colmap().schreibe_aufnahme(ordner, augenblicke=2, punkte=5, text=(ort == "stamm"))
    assert seams.finde_aufnahme(ply) == (ordner, "neben dem splat", None)


def test_finde_aufnahme_reihenfolge(tmp_path, monkeypatch):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    ply = tmp_path / "s.ply"
    assert seams.finde_aufnahme(ply) == (None, "keine", None)
    # Ein Ordner ohne images ist keine Aufnahme.
    (tmp_path / "sparse" / "0").mkdir(parents=True)
    (tmp_path / "sparse" / "0" / "cameras.bin").write_bytes(b"\0" * 8)
    assert seams.finde_aufnahme(ply)[1] == "keine"
    neben = tmp_path / "s.colmap"
    _colmap().schreibe_aufnahme(neben, augenblicke=2, punkte=5)
    env = tmp_path / "dienst" / "sparse"
    _colmap().schreibe_aufnahme(env, augenblicke=2, punkte=5)
    param = tmp_path / "ausdruecklich"
    _colmap().schreibe_aufnahme(param, augenblicke=2, punkte=5)
    assert seams.finde_aufnahme(ply) == (neben, "neben dem splat", None)
    monkeypatch.setenv(seams.SPLAT_AUFNAHME_ENV, str(env))
    assert seams.finde_aufnahme(ply) == (env, "umgebung", None)
    assert seams.finde_aufnahme(ply, param) == (param, "parameter", None)
    # Die Variable zeigt ins Leere: weitersuchen, Grund vermerken — ohne Pfad.
    monkeypatch.setenv(seams.SPLAT_AUFNAHME_ENV, str(tmp_path / "geheim" / "fehlt"))
    ordner, art, grund = seams.finde_aufnahme(ply)
    assert (ordner, art) == (neben, "neben dem splat")
    assert seams.SPLAT_AUFNAHME_ENV in grund and str(tmp_path) not in grund
    # Ausdrücklich genannt, aber keine Aufnahme: ein Fehler, kein stiller Ring.
    with pytest.raises(seams.SeamError, match="kein COLMAP-Ordner"):
        seams.finde_aufnahme(ply, tmp_path / "geheim")


def test_naht_reicht_die_aufnahme_weiter_und_schluesselt_ihren_inhalt(tmp_path, splat_python,
                                                                    monkeypatch):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    speicher = tmp_path / "sp"
    starter = _Starter()
    ohne = seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)
    assert not any(a.startswith("--aufnahme") for a in starter.aufrufe[-1][0])
    assert ohne["aufnahme"]["quelle"] == "keine" and ohne["aufnahme"]["sha256"] is None
    # Neben dem Splat abgelegt: gefunden, weitergereicht (mit `=`), anderer Schlüssel.
    ordner = tmp_path / "sparse" / "0"
    _colmap().schreibe_aufnahme(ordner, augenblicke=3, punkte=5)
    mit = seams.splat_zu_netz(splat, speicher=speicher, _starte=starter)
    cmd = starter.aufrufe[-1][0]
    assert f"--aufnahme={ordner}" in cmd
    args = _runner_parser().parse_args([str(splat), "n.ply", f"--aufnahme={ordner}"])
    assert args.aufnahme == str(ordner)
    assert mit["zwischenspeicher"]["schluessel"] != ohne["zwischenspeicher"]["schluessel"]
    assert mit["aufnahme"]["quelle"] == "neben dem splat"
    assert mit["aufnahme"]["sha256"] == kn.aufnahme_fingerabdruck(ordner)["sha256"]
    assert str(tmp_path) not in json.dumps(mit["aufnahme"])
    # Gleicher Inhalt an anderem Ort: Treffer. Andere Kameras: neues Netz.
    kopie = tmp_path / "anders"
    shutil.copytree(ordner, kopie)
    n = len(starter.aufrufe)
    wieder = seams.splat_zu_netz(splat, speicher=speicher, aufnahme=kopie, _starte=starter)
    assert len(starter.aufrufe) == n and wieder["zwischenspeicher"]["treffer"] is True
    _colmap().schreibe_aufnahme(kopie, augenblicke=4, punkte=5)
    seams.splat_zu_netz(splat, speicher=speicher, aufnahme=kopie, _starte=starter)
    assert len(starter.aufrufe) == n + 1


def test_vermerk_sagt_woher_die_blickwinkel_kamen(tmp_path, splat_python, monkeypatch):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)

    class _Rueckfall(_Starter):
        def __call__(self, cmd, timeout):
            lauf = super().__call__(cmd, timeout)
            bericht = Path(cmd[cmd.index("--report") + 1])
            b = json.loads(bericht.read_text(encoding="utf-8"))
            b.update(blickwinkel_quelle="ring", deckung={"anteil": 0.42},
                     aufnahme={"verwendet": False, "grund": f"Aufnahme und Splat liegen nicht "
                               f"im selben System ({tmp_path}/geheim/x)"})
            bericht.write_text(json.dumps(b), encoding="utf-8")
            return lauf

    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    _colmap().schreibe_aufnahme(tmp_path / "sparse" / "0", augenblicke=2, punkte=5)
    v = seams.kontext_vorbereiten(
        splat, _splat_zu_netz=lambda ply, **kw: seams.splat_zu_netz(
            ply, speicher=tmp_path / "sp", _starte=_Rueckfall(), **kw))
    assert v["weg"] == "netz"
    n = v["netz"]
    assert (n["blickwinkel_quelle"], n["aufnahme"], n["deckung"]) == ("ring", "neben dem splat",
                                                                     0.42)
    assert "nicht im selben System" in n["aufnahme_grund"]
    assert str(tmp_path) not in json.dumps(n)


def _runner_parser():
    spez = importlib.util.spec_from_file_location("runner_aufnahme", seams.SPLAT_RUNNER)
    runner = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(runner)
    return runner._parser()


def test_der_runner_liest_colmap_ohne_pycolmap():
    """pycolmap (PyPI-Rad 4.2.1) bindet GPL-2.0+-Teile von SuiteSparse statisch ein; gelesen
    wird darum mit der Standardbibliothek (``kontext_netz.lies_aufnahme``)."""
    importe = set()
    for knoten in ast.walk(ast.parse(RUNNER_QUELLE)):
        if isinstance(knoten, ast.Import):
            importe.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.module:
            importe.add(knoten.module.split(".")[0])
    assert "pycolmap" not in importe
    assert "kn.lies_aufnahme(" in RUNNER_QUELLE and "kn.gleichheit_befund(" in RUNNER_QUELLE
    einrichtung = (WURZEL / "betrieb" / "splat-umgebung.sh").read_text(encoding="utf-8")
    assert "pycolmap" not in einrichtung.replace("KEIN pycolmap", "")


# --- die echte Fusion mit Aufnahme (nur mit AIIMAGING_SPLAT_PYTHON) -------------------

def _fusion(tmp_path, *, aufnahme=None, **kw):
    return seams.splat_zu_netz(tmp_path / "s.ply", renderer="cpu-probe", aufloesung=160,
                               blickwinkel=8, voxel_m=0.15, speicher=tmp_path / "sp",
                               aufnahme=aufnahme, **kw)


@pytest.fixture
def strasse(tmp_path, monkeypatch):
    """Der synthetische Strassenraum (``make_test_splat.py --form strasse``) mit seiner
    Aufnahme entlang der Mittellinie — die Lage, an der der Ring am echten Splat scheiterte."""
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    _erzeuger().erzeuge_splat(tmp_path / "s.ply", punkte=12000, startwert=7, form="strasse")
    _colmap().schreibe_aufnahme(tmp_path / "auf", augenblicke=80, form="strasse")
    return tmp_path


@ohne_splat_python
def test_aufnahme_deckt_den_strassenraum_besser_als_der_ring(strasse):
    ring = _fusion(strasse)
    auf = _fusion(strasse, aufnahme=strasse / "auf")
    print(json.dumps({n: {"quelle": b["blickwinkel_quelle"], "deckung": b["deckung"],
                          "dreiecke": b["netz"]["dreiecke"], "inseln": b["netz"]["inseln"],
                          "blickwinkel": b["blickwinkel"]["gesamt"],
                          "gleichheit": (b["aufnahme"].get("gleichheit") or {}).get("median_rel"),
                          "zeit_s": b["zeiten_s"]["gesamt_s"]}
                      for n, b in (("ring", ring), ("aufnahme", auf))}, ensure_ascii=False))
    assert ring["blickwinkel_quelle"] == "ring" and ring["aufnahme"]["quelle"] == "keine"
    assert auf["blickwinkel_quelle"] == "aufnahme" and auf["aufnahme"]["verwendet"] is True
    assert auf["aufnahme"]["quelle"] == "parameter"
    assert auf["blickwinkel"]["aufnahme"] == kn.AUFNAHME_BLICKE_MAX
    assert auf["aufnahme"]["gleichheit"]["gleich"] is True
    assert auf["deckung"]["anteil"] > ring["deckung"]["anteil"] + 0.1
    assert auf["deckung"]["anteil"] > 0.9
    # Weniger Fetzen: Die Aufnahme sieht die Wände von vorn, der Ring streifend.
    assert auf["netz"]["inseln"]["komponenten"] < ring["netz"]["inseln"]["komponenten"]
    # Das Netz bleibt im Splat (kein Wachstum über den Rand bei streifendem Blick).
    lo, hi = auf["splat"]["huellbox_dicht"]
    n_lo, n_hi = auf["netz"]["huellbox"]
    for i in range(3):
        assert n_lo[i] > lo[i] - 1.0 and n_hi[i] < hi[i] + 1.0
    assert str(strasse) not in json.dumps({k: v for k, v in auf.items() if k != "netz_ply"})


@ohne_splat_python
def test_verschobene_aufnahme_faellt_auf_den_ring_mit_grund(strasse):
    d = 10.0 / math.sqrt(3.0)                       # 10 m, schräg
    _colmap().schreibe_aufnahme(strasse / "weg", augenblicke=80, form="strasse",
                                versatz=(d, d, d))
    b = _fusion(strasse, aufnahme=strasse / "weg")
    g = b["aufnahme"]["gleichheit"]
    print(json.dumps(g, ensure_ascii=False))
    assert b["blickwinkel_quelle"] == "ring" and b["aufnahme"]["verwendet"] is False
    assert g["gleich"] is False and g["median_rel"] > kn.GLEICH_MEDIAN_MAX
    assert "nicht im selben System" in b["aufnahme"]["grund"]
    assert b["blickwinkel"]["ring"] > 0 and b["blickwinkel"]["aufnahme"] == 0


@ohne_splat_python
def test_blockwache_vergroessert_den_voxel_statt_abzustuerzen(strasse):
    runner = seams.SPLAT_RUNNER
    bericht = strasse / "b.json"
    lauf = subprocess.run(
        [os.environ[seams.SPLAT_PYTHON_ENV], str(runner), str(strasse / "s.ply"),
         str(strasse / "n.ply"), "--report", str(bericht), "--renderer", "cpu-probe",
         "--aufloesung", "160", "--blickwinkel", "8", "--voxel-m", "0.15",
         "--bloecke-max", "1500"], capture_output=True, text=True, timeout=600)
    b = json.loads(bericht.read_text(encoding="utf-8"))
    assert lauf.returncode == 0, b.get("error")
    v = b["voxel"]
    print(json.dumps(v))
    assert v["vergroessert"] is True and v["versuche"][0]["abgebrochen"] is True
    assert v["benutzt_splat_einheiten"] > v["angefragt_splat_einheiten"]
    assert v["versuche"][-1]["bloecke"] <= 1500 and "Open3D" in v["grund"]
    # auf-20261013-276 Fehler 2: Der abgebrochene Versuch steht mit seiner Zeit da, und die
    # Teilzeiten erklären die Gesamtzeit (vorher fehlten am echten Splat 34 s).
    z = b["zeiten_s"]
    print(json.dumps(z))
    assert all(x["dauer_s"] > 0 for x in v["versuche"])
    assert z["blockwache_verworfen_s"] == pytest.approx(
        sum(x["dauer_s"] for x in v["versuche"] if x.get("abgebrochen")), abs=0.01)
    assert z["blockwache_verworfen_s"] > 0 and "bibliotheken_s" in z
    assert abs(z["ungezaehlt_s"]) < 0.05 * z["gesamt_s"] + 0.5


def test_die_schalter_der_erzeuger_wirken(tmp_path):
    """Schalterprobe: ``make_test_colmap.py`` und ``make_test_splat.py --form`` von der
    Befehlszeile — dieselbe Aufnahme wie aus Python, und die Strasse ist lang und schmal."""
    m = _colmap()
    assert m.main([str(tmp_path / "a"), "--augenblicke", "3", "--radius", "5",
                   "--versatz", "1,2,3", "--text", "--form", "platz"]) == 0
    a = kn.lies_aufnahme(tmp_path / "a")
    assert a["format"] == "txt" and len(a["augenblicke"]) == 3
    zentrum = kn.kamerazentrum(a["bilder"][1]["q"], a["bilder"][1]["t"])
    assert zentrum == pytest.approx((5.0 + 1.0, 1.6 + 2.0, 0.0 + 3.0), abs=1e-9)
    assert m.main([str(tmp_path / "b"), "--form", "strasse", "--augenblicke", "2"]) == 0
    assert kn.lies_aufnahme(tmp_path / "b")["format"] == "bin"
    assert _erzeuger().main([str(tmp_path / "s.ply"), "--punkte", "400",
                             "--form", "strasse"]) == 0
    kopf = kn.lies_ply_kopf(tmp_path / "s.ply")
    assert kopf["elemente"][0]["anzahl"] == 400


# ======================================================================================
# 9 · Nach auf-20261013-276: Tiefenfilter, Masken der Aufnahme, vier Fehler
# ======================================================================================
#
# Am echten Splat: gesprenkelte erwartete Tiefe, die gefilmte Person als Wolke nah vor den
# Kameras, 497 497 Netzstücke. Dazu vier Fehler (Symlink, Zeiten der Blockwache, sha256 nicht
# reproduzierbar, Deckung nur über eine Teilmenge). Die stdlib-Proben laufen immer, die
# Fusion nur mit AIIMAGING_SPLAT_PYTHON.

def _png_lesen(pfad: Path) -> tuple[int, int, bytes]:
    """Ein 8-Bit-Graustufen-PNG ohne Filter (wie ``make_test_colmap`` es schreibt) lesen."""
    import zlib

    daten = pfad.read_bytes()
    assert daten[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, breite, hoehe = 8, b"", 0, 0
    while pos < len(daten):
        (laenge,) = struct.unpack(">I", daten[pos:pos + 4])
        art, inhalt = daten[pos + 4:pos + 8], daten[pos + 8:pos + 8 + laenge]
        if art == b"IHDR":
            breite, hoehe = struct.unpack(">II", inhalt[:8])
            assert inhalt[8:10] == bytes([8, 0])            # 8 Bit, Graustufen
        elif art == b"IDAT":
            idat += inhalt
        pos += 12 + laenge
    roh = zlib.decompress(idat)
    zeilen = b"".join(roh[y * (breite + 1) + 1:(y + 1) * (breite + 1)] for y in range(hoehe))
    return breite, hoehe, zeilen


# --- die gesetzten Zahlen und ihre Lesart -------------------------------------------

def test_tiefenfilter_gesetzt_und_im_speicherschluessel():
    g = kn.netz_parameter()["gesetzt"]
    assert g["deckkraft_tiefe"] == kn.DECKKRAFT_TIEFE > kn.DECKKRAFT_LEER
    assert g["tiefe_sprung_rel"] == kn.TIEFE_SPRUNG_REL and g["nah_min_m"] == kn.NAH_MIN_M
    assert g["deckung_stichprobe"] == kn.DECKUNG_STICHPROBE
    # Vorgabe seit auf-20261013-277: KEIN Filter (Streuung verwarf am echten Splat 99,99 %).
    assert kn.VORGABE_TIEFENFILTER == ()
    assert kn.netz_parameter()["tiefenfilter"] == []
    assert kn.netz_parameter(tiefenfilter="alle")["tiefenfilter"] == sorted(kn.TIEFENFILTER)
    # Mit Filtern ist es ein anderes Netz — also ein anderer Schlüssel; «keine» ist die Vorgabe.
    ohne = kn.netz_parameter(tiefenfilter="keine")
    assert ohne["tiefenfilter"] == []
    assert (seams.splat_schluessel("a" * 64, ohne)
            == seams.splat_schluessel("a" * 64, kn.netz_parameter()))
    assert (seams.splat_schluessel("a" * 64, kn.netz_parameter(tiefenfilter="alle"))
            != seams.splat_schluessel("a" * 64, ohne))


def test_tiefenfilter_lesen():
    assert kn.tiefenfilter_lesen(None) == []
    assert kn.tiefenfilter_lesen("alle") == sorted(kn.TIEFENFILTER)
    assert kn.tiefenfilter_lesen("keine") == kn.tiefenfilter_lesen(()) == []
    assert kn.tiefenfilter_lesen("nah, deckkraft") == ["deckkraft", "nah"]
    with pytest.raises(kn.KontextNetzError, match="unbekannt"):
        kn.tiefenfilter_lesen("nha")                       # ein Tippfehler schaltet nicht ab


def test_nahbereich_in_metern_der_welt():
    """1,5 m der Welt — am echten Splat ist eine Einheit ≈ 6,22 m (massstab ≈ 0,16)."""
    assert kn.nah_min_splat(1.0) == pytest.approx(kn.NAH_MIN_M)
    assert kn.nah_min_splat(1 / 6.22) == pytest.approx(kn.NAH_MIN_M * 6.22)
    with pytest.raises(kn.KontextNetzError):
        kn.nah_min_splat(0.0)


# --- Fehler 4: die Deckung zählt eine Stichprobe über ALLE dichten Punkte ------------

def test_stichprobe_gleichmaessig_ueber_alle_und_wiederholbar():
    """``auf-20261013-276`` Fehler 4: ~20 000 Punkte als Schritt durch die Datei. Jetzt eine
    Zufallsstichprobe über alle — unabhängig von der Reihenfolge, in der der Trainer schreibt."""
    n, k = 1_000_000, kn.DECKUNG_STICHPROBE
    a = kn.stichprobe_indizes(n, k)
    assert a == kn.stichprobe_indizes(n, k)                # fester Startwert
    assert len(a) == len(set(a)) == k and a == sorted(a)
    assert a[0] < n // 1000 and a[-1] > n - n // 1000      # von vorn bis hinten
    # Je Zehntel der Datei ein Zehntel der Stichprobe (± 3 %).
    zehntel = [0] * 10
    for i in a:
        zehntel[i * 10 // n] += 1
    assert all(abs(z / k - 0.1) < 0.003 for z in zehntel), zehntel
    assert kn.stichprobe_indizes(50, k) == list(range(50))  # weniger Punkte: alle
    assert kn.stichprobe_indizes(0) == []


def test_der_runner_zaehlt_die_deckung_ueber_die_ganze_stichprobe():
    assert "kn.stichprobe_indizes(len(lage_dicht))" in RUNNER_QUELLE
    assert "_deckung(netz, deckung_punkte," in RUNNER_QUELLE


# --- Fehler 1: die Aufnahme hinter einem Verweis (Symlink) ---------------------------

def test_aufnahme_wird_hinter_einem_symlink_gefunden(tmp_path, monkeypatch):
    """``auf-20261013-276`` Fehler 1: Die App lädt ``context.ply`` als Verweis in ihrem
    Projektordner; die Aufnahme liegt neben dem Ziel."""
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    lauf = tmp_path / "lauf"
    _erzeuger().erzeuge_splat(lauf / "splat.ply", punkte=100)
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=2, punkte=5)
    app = tmp_path / "app" / "projekt"
    app.mkdir(parents=True)
    (app / "context.ply").symlink_to(lauf / "splat.ply")
    ordner, art, grund = seams.finde_aufnahme(app / "context.ply")
    assert art == "neben dem splat" and grund is None
    assert ordner.resolve() == (lauf / "sparse" / "0").resolve()
    # Der Pfad, wie er kommt, bleibt vorn: Eine Aufnahme neben dem Verweis gilt zuerst.
    _colmap().schreibe_aufnahme(app / "sparse" / "0", augenblicke=2, punkte=5)
    assert seams.finde_aufnahme(app / "context.ply")[0] == app / "sparse" / "0"
    # Ohne Verweis keine zweiten Kandidaten (ein relativer Pfad wird nicht doppelt).
    assert len(kn.aufnahme_kandidaten(Path("x") / "s.ply")) == 3


def test_masken_werden_neben_einer_verlinkten_aufnahme_gefunden(tmp_path):
    lauf = tmp_path / "lauf"
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=2, punkte=5,
                                person=4, masken=lauf / "masks", ansichtsordner=True)
    (tmp_path / "verweis").symlink_to(lauf / "sparse" / "0")
    namen = [b["name"] for b in kn.lies_aufnahme(tmp_path / "verweis")["bilder"].values()]
    fund = kn.finde_masken(tmp_path / "verweis", namen)
    assert fund["gefunden"] and fund["art"] == "../../masks" and len(fund["dateien"]) == 8


# --- die Masken der Aufnahme ---------------------------------------------------------

def test_masken_lage_und_drei_namensformen(tmp_path):
    a = tmp_path / "lauf" / "sparse" / "0"
    assert [k for k, _ in kn.masken_kandidaten(a)] == ["../../masks", "../masks", "masks"]
    assert [o for _, o in kn.masken_kandidaten(a)] == [
        tmp_path / "lauf" / "masks", tmp_path / "lauf" / "sparse" / "masks", a / "masks"]
    m = tmp_path / "m"
    (m / "back").mkdir(parents=True)
    (m / "back" / "0031.jpg.png").write_bytes(b"x")            # voller Name + .png
    (m / "front").mkdir()
    (m / "front" / "0001.png").write_bytes(b"x")               # Stamm + .png
    (m / "left").mkdir()
    (m / "left" / "0002.jpg").write_bytes(b"x")                # derselbe Name
    assert kn.maske_zum_bild(m, "back/0031.jpg") == m / "back" / "0031.jpg.png"
    assert kn.maske_zum_bild(m, "front/0001.jpg") == m / "front" / "0001.png"
    assert kn.maske_zum_bild(m, "left/0002.jpg") == m / "left" / "0002.jpg"
    assert kn.maske_zum_bild(m, "right/0003.jpg") is None


def test_masken_nur_neben_dieser_aufnahme(tmp_path):
    """Auskunft der HomeStation (13.10.2026): Masken eines anderen Laufs derselben Aufnahme
    passen nur dem Namen nach. Gesucht wird nur relativ zu DIESER Aufnahme."""
    anderer = tmp_path / "anderer_lauf"
    _colmap().schreibe_aufnahme(anderer / "sparse" / "0", augenblicke=2, punkte=5, person=4,
                                masken=anderer / "masks", ansichtsordner=True)
    dieser = tmp_path / "abnahme" / "sparse" / "0"
    _colmap().schreibe_aufnahme(dieser, augenblicke=2, punkte=5, ansichtsordner=True)
    namen = [b["name"] for b in kn.lies_aufnahme(dieser)["bilder"].values()]
    assert kn.finde_masken(dieser, namen)["gefunden"] is False
    # Ausdrücklich genannt, gilt der Ordner.
    assert kn.finde_masken(dieser, namen, anderer / "masks")["art"] == "parameter"


def test_synthetische_masken_schneiden_die_person_aus(tmp_path):
    lauf = tmp_path / "lauf"
    befund = _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=3, punkte=5,
                                         person=12, masken=lauf / "masks",
                                         ansichtsordner=True, breite=200, hoehe=200)
    assert befund["masken"]["anzahl"] == 12
    assert 0.0 < befund["masken"]["ausgeschnitten"] < 0.5   # die Person, nicht das Bild
    schwarz = []
    for p in sorted((lauf / "masks").rglob("*.png")):
        b, h, pixel = _png_lesen(p)
        assert (b, h) == (200, 200) and set(pixel) <= {0, 255}
        schwarz.append(pixel.count(0) / len(pixel))
    assert len(schwarz) == 12 and max(schwarz) > 0.05       # nah vor einer Kamera: gross
    daten = json.loads((lauf / "masks" / "maske.json").read_text(encoding="utf-8"))
    assert daten["schema"].startswith("kosmoprepare.splat-maske/")
    assert kn.polaritaet_aus_json(daten) is True


def test_maskenfingerabdruck_folgt_dem_inhalt(tmp_path):
    lauf = tmp_path / "lauf"
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=2, punkte=5, person=6,
                                masken=lauf / "masks", breite=64, hoehe=64)
    namen = [b["name"] for b in kn.lies_aufnahme(lauf / "sparse" / "0")["bilder"].values()]
    a = kn.masken_fingerabdruck(kn.finde_masken(lauf / "sparse" / "0", namen))
    kopie = tmp_path / "kopie"
    shutil.copytree(lauf, kopie)
    b = kn.masken_fingerabdruck(kn.finde_masken(kopie / "sparse" / "0", namen))
    assert a == b                                           # Inhalt, nicht Pfad
    ziel = next((kopie / "masks").glob("*.png"))
    ziel.write_bytes(ziel.read_bytes() + b"\0")
    assert kn.masken_fingerabdruck(kn.finde_masken(kopie / "sparse" / "0", namen)) != a
    assert kn.masken_fingerabdruck({"gefunden": False}) is None


@pytest.mark.parametrize("daten, erwartet", [
    ({"schema": "kosmoprepare.splat-maske/0.2", "verfahren": "person"}, True),
    ({"polaritaet": "weiss=behalten"}, True),
    ({"polarity": "white = keep"}, True),
    ({"polaritaet": "schwarz=behalten"}, False),
    ({"polaritaet": 0}, False),
    ({"polaritaet": 255}, True),
    ({"schema": "etwas/1"}, None),
    ([1, 2], None),
])
def test_polaritaet_aus_maske_json(daten, erwartet):
    assert kn.polaritaet_aus_json(daten) is erwartet


def test_polaritaet_vorgabe_mehrheit_und_json():
    v = kn.masken_polaritaet(0.9)
    assert (v["weiss_behalten"], v["quelle"], v["warnung"]) == (True, "vorgabe", None)
    m = kn.masken_polaritaet(0.1)                            # fast alles schwarz
    assert (m["weiss_behalten"], m["quelle"]) == (False, "mehrheitsregel") and m["warnung"]
    j = kn.masken_polaritaet(0.1, aus_json=True)             # die Datei gilt, mit Warnung
    assert (j["weiss_behalten"], j["quelle"]) == (True, "maske.json") and j["warnung"]
    assert kn.masken_polaritaet(0.9, aus_json=True)["warnung"] is None


def test_naht_reicht_masken_weiter_und_schluesselt_ihren_inhalt(tmp_path, splat_python,
                                                               monkeypatch):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    monkeypatch.delenv(seams.SPLAT_MASKEN_ENV, raising=False)
    lauf = tmp_path / "lauf"
    splat = lauf / "splat.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=2, punkte=5,
                                ansichtsordner=True)
    starter = _Starter()
    ohne = seams.splat_zu_netz(splat, speicher=tmp_path / "sp", _starte=starter)
    assert "--masken=keine" in starter.aufrufe[-1][0]
    assert ohne["masken"]["gefunden"] is False and ohne["masken"]["sha256"] is None
    assert any(a == "--tiefenfilter=keine"
               for a in starter.aufrufe[-1][0])
    # Masken dazu: weitergereicht, anderer Schlüssel, Vermerk ohne Pfad.
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=2, punkte=5, person=6,
                                masken=lauf / "masks", ansichtsordner=True, breite=64,
                                hoehe=64)
    mit = seams.splat_zu_netz(splat, speicher=tmp_path / "sp", _starte=starter)
    assert f"--masken={lauf / 'masks'}" in starter.aufrufe[-1][0]
    assert mit["zwischenspeicher"]["schluessel"] != ohne["zwischenspeicher"]["schluessel"]
    assert mit["masken"]["gefunden"] is True and mit["masken"]["anzahl"] == 8
    assert mit["masken"]["lage"] == "../../masks" and mit["masken"]["maske_json"] is True
    assert str(tmp_path) not in json.dumps(mit["masken"])
    # Andere Masken: neues Netz.
    n = len(starter.aufrufe)
    m = next((lauf / "masks").rglob("*.png"))
    m.write_bytes(m.read_bytes() + b"\0")
    seams.splat_zu_netz(splat, speicher=tmp_path / "sp", _starte=starter)
    assert len(starter.aufrufe) == n + 1
    # Ausdrücklich genannt, aber ohne passende Maske: ein Fehler, kein stilles Weglassen.
    with pytest.raises(seams.SeamError, match="keine Maske"):
        seams.splat_zu_netz(splat, speicher=tmp_path / "sp", masken=tmp_path,
                            _starte=starter)
    # Ohne Aufnahme keine Masken — auch wenn ein Ordner daliegt.
    allein = tmp_path / "allein"
    _erzeuger().erzeuge_splat(allein / "s.ply", punkte=100)
    (allein / "masks").mkdir()
    b = seams.splat_zu_netz(allein / "s.ply", speicher=tmp_path / "sp", _starte=starter)
    assert b["masken"]["quelle"] == "keine aufnahme"
    assert not any(a.startswith("--masken") for a in starter.aufrufe[-1][0])


def test_naht_reicht_die_tiefenfilter_weiter(tmp_path, splat_python, monkeypatch):
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=100)
    starter = _Starter()
    a = seams.splat_zu_netz(splat, speicher=tmp_path / "sp", tiefenfilter="keine",
                            _starte=starter)
    assert "--tiefenfilter=keine" in starter.aufrufe[-1][0]
    b = seams.splat_zu_netz(splat, speicher=tmp_path / "sp", tiefenfilter=["nah"],
                            _starte=starter)
    assert "--tiefenfilter=nah" in starter.aufrufe[-1][0]
    assert a["zwischenspeicher"]["schluessel"] != b["zwischenspeicher"]["schluessel"]
    args = _runner_parser().parse_args([str(splat), "n.ply", "--tiefenfilter=keine",
                                        "--masken=keine"])
    assert (args.tiefenfilter, args.masken) == ("keine", "keine")
    with pytest.raises(seams.SeamError, match="unbekannt"):
        seams.splat_zu_netz(splat, speicher=tmp_path / "sp", tiefenfilter="nha",
                            _starte=starter)


def test_die_person_im_splat_und_in_der_aufnahme_am_selben_ort(tmp_path):
    """Die Person des Splats und die der Masken sind dieselbe (``make_test_colmap.rig_weg``
    und ``person_wolke``), und sie ändert ihren Ort mit jedem Augenblick."""
    c = _colmap()
    erzeugt = _erzeuger().erzeuge_splat(tmp_path / "s.ply", punkte=400, form="strasse",
                                        person=10, person_augenblicke=20)
    assert erzeugt["person"] == 200 and erzeugt["dicht"] == 400 - erzeugt["schwebe"] + 200
    weg = c.rig_weg(20, form="strasse")
    lagen = []
    for a, (auge, vorn) in enumerate(weg):
        wolke = c.person_wolke(a, auge, vorn, 10)
        mx = sum(p[0] for p in wolke) / len(wolke) - auge[0]
        mz = sum(p[2] for p in wolke) / len(wolke) - auge[2]
        d = math.hypot(mx, mz)
        assert 0.3 < d < 1.0, d                          # nah am Rig
        lagen.append(math.atan2(mz, mx))
    assert len({round(w, 1) for w in lagen}) > 15        # jedes Mal woanders


def test_der_ersatzrenderer_liefert_eine_akkumulierte_deckkraft():
    """Der Tiefenfilter braucht alpha; bis 276 gab der Ersatz nur Farbe und Tiefe."""
    baum = ast.parse(RUNNER_QUELLE)
    probe = next(k for k in ast.walk(baum)
                 if isinstance(k, ast.FunctionDef) and k.name == "_probe_ansichten")
    quelle = ast.get_source_segment(RUNNER_QUELLE, probe)
    assert "np.bincount(idx, weights=" in quelle and "alpha.reshape(h, b)" in quelle
    assert "render_mode=\"RGB+ED\"" in RUNNER_QUELLE


@ohne_splat_python
def test_das_netz_ist_bei_gleichem_schluessel_bitgleich(strasse):
    """``auf-20261013-276`` Fehler 3: Gleicher Schlüssel, andere sha256. Ursache Open3D (die
    Hashtabelle der TSDF füllt sich parallel, die Dreiecke kommen in wechselnder Reihenfolge);
    der Runner ordnet das Netz jetzt nach Lage. Vorher hier: drei Läufe, drei sha256."""
    summen = []
    for i in range(3):
        lauf = subprocess.run(
            [os.environ[seams.SPLAT_PYTHON_ENV], str(seams.SPLAT_RUNNER),
             str(strasse / "s.ply"), str(strasse / f"n{i}.ply"), "--report",
             str(strasse / f"b{i}.json"), "--renderer", "cpu-probe", "--aufloesung", "160",
             "--blickwinkel", "8", "--voxel-m", "0.15"],
            capture_output=True, text=True, timeout=600)
        b = json.loads((strasse / f"b{i}.json").read_text(encoding="utf-8"))
        assert lauf.returncode == 0, b.get("error")
        summen.append(kn.netz_kennzahlen(strasse / f"n{i}.ply")["sha256"])
    assert len(set(summen)) == 1, summen
    # Fehler 4: Die Deckung zählt eine Stichprobe über alle dichten Punkte.
    d = b["deckung"]
    assert d["dicht_gesamt"] == b["splat"]["dicht"]
    assert d["punkte"] == min(b["splat"]["dicht"], kn.DECKUNG_STICHPROBE)


# --- C · die Person im synthetischen Strassenraum (nur mit AIIMAGING_SPLAT_PYTHON) ------

@pytest.fixture
def strasse_mit_person(tmp_path, monkeypatch):
    """Der Strassenraum mit der gefilmten Person (``--person 30``) und den Masken dazu, so
    abgelegt wie bei der HomeStation: ``lauf/sparse/0``, ``lauf/masks/<ansicht>/…png``."""
    monkeypatch.delenv(seams.SPLAT_AUFNAHME_ENV, raising=False)
    monkeypatch.delenv(seams.SPLAT_MASKEN_ENV, raising=False)
    lauf = tmp_path / "lauf"
    _erzeuger().erzeuge_splat(lauf / "splat.ply", punkte=12000, startwert=7, form="strasse",
                              person=30)
    _colmap().schreibe_aufnahme(lauf / "sparse" / "0", augenblicke=80, form="strasse",
                                person=30, masken=lauf / "masks", ansichtsordner=True,
                                breite=543, hoehe=543)
    return lauf


@ohne_splat_python
def test_die_person_zerfetzt_das_netz_und_der_tiefenfilter_heilt_es(strasse_mit_person):
    """``auf-20261013-276``: Die Person als Wolke vor der Kamera zerlegt das Netz in Fetzen.

    Am synthetischen Strassenraum mit dem Ersatzrenderer (erwartete Tiefe wie gsplat), Voxel
    7 cm wie am echten Splat: ohne Filter viele Stücke und ein grosser Inselanteil; mit den
    Filtern ein Bruchteil davon. Getragen wird das vor allem von der **Streuung entlang des
    Strahls** — Nahbereich und Masken allein halfen hier kaum (Messblatt
    ``docs/SPLAT_TIEFENFILTER_2026-10-13.md``).
    """
    lauf = strasse_mit_person

    def fusion(filter_):
        return seams.splat_zu_netz(lauf / "splat.ply", renderer="cpu-probe", aufloesung=160,
                                   voxel_m=0.07, speicher=lauf / "sp", tiefenfilter=filter_)

    ohne, mit = fusion("keine"), fusion("alle")   # «alle» ausdruecklich: Vorgabe ist keiner
    zahlen = {n: {"deckung": b["deckung"]["anteil"],
                  "stuecke": b["netz"]["inseln"]["komponenten"],
                  "inselanteil": b["netz"]["inseln"]["entfernt_dreiecke_anteil"],
                  "verworfen": b["tiefenfilter"]["je_filter"], "masken": b["masken"]}
              for n, b in (("ohne", ohne), ("mit", mit))}
    print(json.dumps(zahlen, ensure_ascii=False))
    assert ohne["blickwinkel_quelle"] == mit["blickwinkel_quelle"] == "aufnahme"
    # Die Masken: gefunden neben der Aufnahme, Polarität aus maske.json, alle 240 benutzt.
    m = mit["masken"]
    assert m["gefunden"] is True and m["lage"] == "../../masks" and m["benutzt"] == 240
    assert (m["polaritaet"], m["polaritaet_quelle"]) == ("weiss = behalten", "maske.json")
    assert m["angewandt"] is True and ohne["masken"]["angewandt"] is False
    assert ohne["tiefenfilter"]["verworfen_anteil"] == 0.0
    je = mit["tiefenfilter"]["je_filter"]
    assert all(je[k] > 0 for k in kn.TIEFENFILTER), je        # jeder Filter greift
    assert mit["tiefenfilter"]["weg_aktiv"] is True
    assert mit["tiefenfilter"]["streuung_bilder"] == 240
    # Die Fetzen: ein Bruchteil der Stücke, ein Bruchteil des Inselanteils.
    assert (mit["netz"]["inseln"]["komponenten"] * 4
            < ohne["netz"]["inseln"]["komponenten"])
    assert (mit["netz"]["inseln"]["entfernt_dreiecke_anteil"] * 3
            < ohne["netz"]["inseln"]["entfernt_dreiecke_anteil"])
    # Die Deckung zählt die Person mit (18 % der dichten Punkte) — mit Filter fällt sie weg.
    assert mit["deckung"]["anteil"] > 0.65


def test_die_schalter_fuer_person_und_masken_wirken(tmp_path):
    """Schalterprobe: ``--person``, ``--masken``, ``--ansichtsordner`` (``make_test_colmap``)
    und ``--person``, ``--person-augenblicke`` (``make_test_splat``) von der Befehlszeile."""
    assert _colmap().main([str(tmp_path / "lauf" / "sparse" / "0"), "--augenblicke", "2",
                           "--form", "strasse", "--person", "5", "--ansichtsordner",
                           "--masken", str(tmp_path / "lauf" / "masks")]) == 0
    namen = sorted(b["name"] for b in kn.lies_aufnahme(
        tmp_path / "lauf" / "sparse" / "0")["bilder"].values())
    assert namen[0] == "back/0000.jpg" and len(namen) == 8
    assert (tmp_path / "lauf" / "masks" / "back" / "0000.jpg.png").is_file()
    assert _erzeuger().main([str(tmp_path / "s.ply"), "--punkte", "400", "--form", "strasse",
                             "--person", "5", "--person-augenblicke", "4"]) == 0
    assert kn.lies_ply_kopf(tmp_path / "s.ply")["elemente"][0]["anzahl"] == 420



@ohne_splat_python
def test_leere_bilder_nach_dem_sieben_kosten_den_lauf_nicht(tmp_path):
    """``auf-20261013-277`` Fehler 2: Ein nach dem Sieben leeres Tiefenbild liess Open3D
    abbrechen («No block is touched»). Seither werden leere und gescheiterte Bilder
    übersprungen und gezählt."""
    splat = tmp_path / "s.ply"
    _erzeuger().erzeuge_splat(splat, punkte=4000)
    b = seams.splat_zu_netz(splat, renderer="cpu-probe", aufloesung=96, voxel_m=0.2,
                            speicher=tmp_path / "sp", tiefenfilter="alle")
    assert "uebersprungen" in b["blickwinkel"], b["blickwinkel"]
