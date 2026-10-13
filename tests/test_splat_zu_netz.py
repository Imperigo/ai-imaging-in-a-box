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
