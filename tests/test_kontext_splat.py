"""Der Splat als Umgebung (Owner-Entscheid 76, 08.10.2026) — sichtbar, aber nicht gemessen.

Was hier bewacht wird
---------------------
1. **Der Erzeuger** (``tools/make_test_splat.py``): reproduzierbar, in der Dateiform eines
   echten Splats, in der glTF-Welt (Regel 3: Testdaten im Repo erzeugbar).
2. **Die Lage** (``aiimaging.kontext``): 16 Zahlen zeilenweise in der glTF-Welt, in
   Blender ``[Z-up-Korrektur] · R_x(+90) · M`` — dieselbe Drehung wie das Modell.
3. **Unverändert ohne Splat:** Kommando, Knoten-Hash und Speicherschlüssel des Abholers
   sind Wort für Wort die von vor dem 08.10.2026 (die Zahlen unten sind am alten Stand
   gerechnet und eingefroren).
4. **Die Maske:** Ein Eintrag ``quelle: "kontext"`` geht vor jeder Regel hinaus.
5. **Die Naht nach aussen** (``kosmo_szene.kontext_aus_szene``, Abholer): ein
   unbrauchbarer Kontext ist ein Mangel, und kein Pfad geht nach aussen (Regel 3).
6. **Die echte Kette** mit Blender: Testbau + synthetischer Splat → Multipass.

Der Runner wird **gelesen, nie importiert** (Regel 2, ``tests/test_prozessgrenze.py``).
"""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, bildlesen, contracts, kette, kontext, kosmo_szene
from aiimaging import maske, seams
from aiimaging.graph import Knoten

WURZEL = Path(__file__).resolve().parents[1]
ERZEUGER = WURZEL / "tools" / "make_test_splat.py"
RUNNER_QUELLE = seams.BLENDER_RUNNER.read_text(encoding="utf-8")


def _erzeuger():
    spez = importlib.util.spec_from_file_location("make_test_splat_pruefling", ERZEUGER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _kopf(pfad: Path) -> tuple[int, list[str], int]:
    daten = pfad.read_bytes()
    ende = daten.index(b"end_header\n") + len(b"end_header\n")
    zeilen = daten[:ende].decode("ascii").splitlines()
    n = int(next(z for z in zeilen if z.startswith("element vertex")).split()[-1])
    namen = [z.split()[-1] for z in zeilen if z.startswith("property")]
    return n, namen, ende


# ======================================================================================
# 1 · Der Erzeuger
# ======================================================================================

def test_erzeuger_schreibt_die_dateiform_eines_3dgs_splats(tmp_path):
    befund = _erzeuger().erzeuge_splat(tmp_path / "s.ply", punkte=400)
    n, namen, ende = _kopf(tmp_path / "s.ply")
    assert n == 400 == befund["punkte"]
    assert namen[:9] == ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2"]
    assert namen[-8:] == ["opacity", "scale_0", "scale_1", "scale_2",
                          "rot_0", "rot_1", "rot_2", "rot_3"]
    assert (tmp_path / "s.ply").stat().st_size == ende + 400 * 4 * len(namen)
    assert befund["dicht"] + befund["schwebe"] == 400


def test_erzeuger_ist_reproduzierbar_und_der_startwert_wirkt(tmp_path):
    m = _erzeuger()
    m.erzeuge_splat(tmp_path / "a.ply", punkte=300, startwert=3)
    m.erzeuge_splat(tmp_path / "b.ply", punkte=300, startwert=3)
    m.erzeuge_splat(tmp_path / "c.ply", punkte=300, startwert=4)
    assert (tmp_path / "a.ply").read_bytes() == (tmp_path / "b.ply").read_bytes()
    assert (tmp_path / "a.ply").read_bytes() != (tmp_path / "c.ply").read_bytes()


def test_erzeuger_f_rest_und_ursprung(tmp_path):
    m = _erzeuger()
    befund = m.erzeuge_splat(tmp_path / "r.ply", punkte=4000, mit_f_rest=True,
                             ursprung=(10.0, -1.0, 2.0), groesse=20.0)
    _, namen, _ = _kopf(tmp_path / "r.ply")
    assert sum(1 for n in namen if n.startswith("f_rest_")) == 45
    lo, hi = befund["huellbox_dicht"]
    # Boden y = 0 relativ zum Ursprung, Wand bis 8 m hoch — in der glTF-Welt ist Y oben.
    assert lo[1] == pytest.approx(-1.0) and hi[1] == pytest.approx(-1.0 + m.WAND_HOEHE, abs=0.05)
    assert lo[0] == pytest.approx(0.0, abs=0.2) and hi[0] == pytest.approx(20.0, abs=0.2)


def test_erzeuger_schwebeteile_liegen_unter_der_schwelle_des_runners(tmp_path):
    """Die Probe für das Verwerfen taugt nur, wenn die Schwebeteile wirklich darunter
    liegen und die dichten Punkte darüber."""
    m = _erzeuger()
    sig = lambda x: 1.0 / (1.0 + math.exp(-x))           # noqa: E731
    assert sig(m.OPAZITAET_SCHWEBE) < kontext.DECKKRAFT_MIN < sig(m.OPAZITAET_DICHT)


def test_erzeuger_als_kommando_und_mit_zu_wenig_punkten(tmp_path):
    lauf = subprocess.run([sys.executable, str(ERZEUGER), str(tmp_path / "k.ply"),
                           "--punkte", "100", "--ursprung=1,-2,3"],
                          capture_output=True, text=True, cwd=WURZEL)
    assert lauf.returncode == 0, lauf.stderr
    assert _kopf(tmp_path / "k.ply")[0] == 100
    # Jeder Schalter einmal gedrückt (tests/test_schalterprobe.py).
    m = _erzeuger()
    assert m.main([str(tmp_path / "s.ply"), "--punkte", "120", "--startwert", "5",
                   "--ursprung", "1,2,3", "--groesse", "12", "--mit-f-rest"]) == 0
    n, namen, _ = _kopf(tmp_path / "s.ply")
    assert n == 120 and "f_rest_44" in namen
    assert m.main([str(tmp_path / "z.ply"), "--punkte", "12"]) == 2
    with pytest.raises(ValueError):
        _erzeuger().erzeuge_splat(tmp_path / "x.ply", punkte=10)


# ======================================================================================
# 2 · Die Lage
# ======================================================================================

def _ry(grad: float, t=(0.0, 0.0, 0.0)) -> list[float]:
    """Drehung um die glTF-Hochachse Y, dann Verschiebung — zeilenweise."""
    c, s = math.cos(math.radians(grad)), math.sin(math.radians(grad))
    return [c, 0.0, s, t[0], 0.0, 1.0, 0.0, t[1], -s, 0.0, c, t[2], 0.0, 0.0, 0.0, 1.0]


def _anwenden(m, p):
    return tuple(m[4 * z] * p[0] + m[4 * z + 1] * p[1] + m[4 * z + 2] * p[2] + m[4 * z + 3]
                 for z in range(3))


def test_matrix_wird_zeilenweise_gelesen_und_streng_geprueft():
    assert kontext.pruefe_matrix(kontext.MATRIX_EINHEIT) == kontext.MATRIX_EINHEIT
    spaltenweise = list(kontext.MATRIX_EINHEIT)
    spaltenweise[12:15] = [4.0, 0.0, -2.0]               # Verschiebung in der letzten Zeile
    for falsch in (list(range(15)), spaltenweise, [float("nan")] + [0.0] * 15,
                   [True] + [0.0] * 15, [0.0] * 15 + [1.0], "1,0,0", None):
        with pytest.raises(kontext.KontextError):
            kontext.pruefe_matrix(falsch)


def test_ohne_matrix_gilt_die_einheit_in_der_gltf_welt():
    """Der Splat bekommt dieselbe Drehung wie das Modell: Blenders glTF-Import, R_x(+90)."""
    m = kontext.matrix_nach_blender(None)
    for p in ((1.0, 2.0, 3.0), (-4.0, 0.5, -7.0)):
        assert _anwenden(m, p) == pytest.approx(contracts.blender_gltf_import_dreht(p))


def test_verschiebung_und_drehung_um_die_hochachse():
    """Die Probe, die der Integrator verlangt hat: M = T · R_y(90°) in der glTF-Welt."""
    m_gltf = _ry(90.0, t=(4.0, -0.6, -2.5))
    m = kontext.matrix_nach_blender(m_gltf)
    for p in ((0.0, 0.0, -12.0), (3.0, 8.0, 0.0), (0.0, 0.0, 0.0)):
        erwartet = contracts.blender_gltf_import_dreht(_anwenden(m_gltf, p))
        assert _anwenden(m, p) == pytest.approx(erwartet, abs=1e-9)
    # Die Hochachse bleibt Hochachse: Ein Punkt 8 m über dem Boden liegt in Blender bei z+8.
    assert _anwenden(m, (0.0, 8.0, 0.0))[2] - _anwenden(m, (0.0, 0.0, 0.0))[2] == pytest.approx(8.0)


def test_eine_z_up_glb_nimmt_den_splat_mit():
    """Bei ``--rotiere-z-up`` wird das Modell zurückgedreht — der Splat genauso."""
    m = kontext.matrix_nach_blender(None, z_up_quelle=True)
    for p in ((1.0, 2.0, 3.0), (5.0, -1.0, 0.25)):
        modell = contracts.z_up_korrektur(contracts.blender_gltf_import_dreht(p))
        assert _anwenden(m, p) == pytest.approx(modell)


def test_massstab_der_matrix():
    m = [2.0, 0, 0, 1, 0, 2.0, 0, 0, 0, 0, 2.0, 0, 0, 0, 0, 1]
    assert kontext.matrix_massstab(m) == pytest.approx(2.0)
    assert kontext.matrix_massstab(kontext.matrix_nach_blender(m)) == pytest.approx(2.0)


def test_fingerabdruck_nennt_keinen_pfad(tmp_path):
    datei = tmp_path / "geheim" / "umgebung.ply"
    datei.parent.mkdir()
    datei.write_bytes(b"ply\n")
    f = kontext.fingerabdruck(datei)
    assert f["datei"] == "umgebung.ply" and f["bytes"] == 4 and len(f["sha256"]) == 64
    assert "geheim" not in json.dumps(f)
    with pytest.raises(kontext.KontextError):
        kontext.fingerabdruck(tmp_path / "fehlt.ply")


# ======================================================================================
# 3 · Unverändert ohne Splat — Kommando, Hash, Speicherschlüssel
# ======================================================================================

#: Am Stand VOR dem 08.10.2026 gerechnet (Commit ba047a4) und hier eingefroren.
HASH_MULTIPASS_OHNE_SPLAT = "22a91c8db9fbf1728031ffa26e8016e14b95e274323913e94615d3571f92ba9d"
SCHLUESSEL_ABHOLER_OHNE_SPLAT = "eab3cf796944e2347a70f4180b23dd619e47c1b7fe1b58272873eb4d27bddceb"


def test_kommando_ohne_splat_ist_das_bisherige():
    cmd = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", kamera="s",
                                        aufloesung=160, hoehe=120, samples=4)
    assert cmd[cmd.index("--") + 1:] == [
        "--glb", "m.glb", "--out", "aus", "--aufloesung", "160", "--samples", "4",
        "--kamera", "s", "--hoehe", "120", "--herzschlag-s", "2.0"]
    assert not any("kontext" in teil for teil in cmd)


def test_kommando_mit_splat_haengt_hinten_an():
    m = _ry(90.0, t=(4.0, -0.6, -2.5))
    cmd = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", kamera="s",
                                        kontext_ply="u.ply", kontext_matrix=m)
    hinten = cmd[-3:]
    assert hinten[:2] == ["--kontext-ply", "u.ply"]
    assert hinten[2].startswith("--kontext-matrix=")
    assert [float(w) for w in hinten[2].split("=", 1)[1].split(",")] == pytest.approx(m)


def test_kommando_weist_matrix_ohne_splat_und_falsche_matrix_ab():
    with pytest.raises(seams.SeamError):
        seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", kontext_matrix=_ry(0))
    with pytest.raises(seams.SeamError):
        seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", kontext_ply="u.ply",
                                      kontext_matrix=[1.0] * 16)


def test_fehlender_splat_haelt_vor_dem_blender_start_an(tmp_path):
    gestartet = []
    with pytest.raises(seams.SeamError, match="gibt es nicht"):
        seams.glb_zu_multipass(tmp_path / "m.glb", tmp_path / "aus", up_axis="Y",
                               kontext_ply=tmp_path / "fehlt.ply",
                               _starte=lambda cmd, frist: gestartet.append(cmd))
    assert gestartet == []


def _multipass_hash(**zusatz) -> str:
    g = kette.baue_kette(glb_path="/x/m.glb", up_axis="Y", prompt="haus", kamera="s", **zusatz)
    k = g.knoten["multipass"]
    return kette._knoten_hash(k, ["a" * 64])


def test_knoten_hash_ohne_splat_ist_der_bisherige():
    assert _multipass_hash() == HASH_MULTIPASS_OHNE_SPLAT


def test_knoten_hash_folgt_dem_inhalt_des_splats_nicht_seinem_pfad(tmp_path):
    a, b = tmp_path / "a.ply", tmp_path / "anderswo.ply"
    a.write_bytes(b"splat-1")
    b.write_bytes(b"splat-1")
    h_a, h_b = _multipass_hash(kontext_ply=a), _multipass_hash(kontext_ply=b)
    assert h_a == h_b != HASH_MULTIPASS_OHNE_SPLAT
    b.write_bytes(b"splat-2")
    assert _multipass_hash(kontext_ply=b) != h_a, "neuer Splat unter altem Namen ist kein Treffer"
    assert _multipass_hash(kontext_ply=a, kontext_matrix=_ry(90.0)) != h_a


def test_kette_prueft_den_kontext_beim_bau():
    with pytest.raises(kette.KettenError):
        kette.baue_kette(glb_path="m.glb", up_axis="Y", prompt="x", kontext_matrix=_ry(0))
    with pytest.raises(kette.KettenError):
        kette.baue_kette(glb_path="m.glb", up_axis="Y", prompt="x", kontext_ply="u.ply",
                         kontext_matrix=[0.0] * 16)


def test_der_multipass_knoten_reicht_den_kontext_weiter(tmp_path, monkeypatch):
    gesehen = {}

    def attrappe(glb, out, **kw):
        gesehen.update(kw)
        return {"status": "ok", "error": "Attrappe"}

    monkeypatch.setattr(seams, "glb_zu_multipass", attrappe)
    knoten = Knoten(id="multipass", art=kette.ART_MULTIPASS,
                    params={"aufloesung": 32, "samples": 1, "beauty": True,
                            "material_id": True, "kontext_ply": "u.ply",
                            "kontext_matrix": _ry(90.0)})
    kette._fuehre_multipass(knoten=knoten, eingaben=[{"glb_path": "m.glb", "up_axis": "Y"}],
                            out_dir=tmp_path)
    assert gesehen["kontext_ply"] == "u.ply"
    assert gesehen["kontext_matrix"] == _ry(90.0)


def test_speicherschluessel_des_abholers_ohne_splat_ist_der_bisherige(tmp_path):
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glbinhalt")
    e = dict(glb_path=str(glb), up_axis="Y", kamera="s", aufloesung=512, samples=128,
             timeout=900.0)
    assert abholer.multipass_schluessel(e, blender="4.2.1") == SCHLUESSEL_ABHOLER_OHNE_SPLAT
    splat = tmp_path / "u.ply"
    splat.write_bytes(b"s1")
    mit = abholer.multipass_schluessel(dict(e, kontext_ply=str(splat)), blender="4.2.1")
    splat.write_bytes(b"s2")
    assert abholer.multipass_schluessel(dict(e, kontext_ply=str(splat)), blender="4.2.1") != mit
    assert mit != SCHLUESSEL_ABHOLER_OHNE_SPLAT


# ======================================================================================
# 4 · Die Maske
# ======================================================================================

def _ifc_tabelle():
    farben = [(255, 38, 38), (38, 101, 255), (165, 255, 38)]
    return [{"index": i, "name": f"IfcWall_Wand-{i}_x", "quelle": "objekt",
             "farbe_srgb_8bit": list(f)} for i, f in enumerate(farben)]


KONTEXT_FARBE = (255, 156, 38)


def test_kontext_geht_vor_jeder_regel_hinaus():
    tabelle = _ifc_tabelle()
    bild_ohne = [(0, 0, 0), (255, 38, 38), (38, 101, 255), (0, 0, 0), (165, 255, 38)]
    # Mit Splat: wo vorher Himmel war, steht jetzt die Umgebung — das Bauwerk bleibt.
    bild_mit = [KONTEXT_FARBE, (255, 38, 38), (38, 101, 255), KONTEXT_FARBE, (165, 255, 38)]
    mit_tabelle = tabelle + [{"index": 3, "name": "Kontext_Splat", "quelle": "kontext",
                              "farbe_srgb_8bit": list(KONTEXT_FARBE)}]
    ohne = maske.bauwerksmaske(bild_ohne, tabelle)
    mit = maske.bauwerksmaske(bild_mit, mit_tabelle)
    assert ohne["maske"] is not None and ohne["ifc_katalog"] is True
    assert mit["maske"] == ohne["maske"]
    assert mit["ifc_katalog"] is True and mit["gelaende_befund"] == ohne["gelaende_befund"]
    assert mit["bauwerk_namen"] == ohne["bauwerk_namen"]
    assert (mit["n_kontext"], ohne["n_kontext"]) == (2, 0)
    assert mit["kontext_namen"] == ["Kontext_Splat"] and ohne["kontext_namen"] == []
    assert mit["n_unbekannt"] == 0


def test_rot_ohne_herausnahme_braeche_der_katalog():
    """Warum der Kontext eine eigene Quelle braucht: Als gewöhnlicher Eintrag hätte er den
    Katalog-Nullbefund gekippt (am Testbau so gemessen, 08.10.2026) — die Maske fiele aus,
    obwohl sich am Modell nichts änderte."""
    tabelle = _ifc_tabelle() + [{"index": 3, "name": "Kontext_Splat", "quelle": "objekt",
                                 "farbe_srgb_8bit": list(KONTEXT_FARBE)}]
    bild = [KONTEXT_FARBE, (255, 38, 38)]
    assert maske.bauwerksmaske(bild, tabelle)["maske"] is None


def test_kontext_kollision_und_nur_kontext_werden_abgewiesen():
    t = _ifc_tabelle()
    with pytest.raises(maske.MaskeError, match="Farbkollision"):
        maske.bauwerksmaske([(0, 0, 0)], t + [dict(t[0], quelle="kontext", name="K")])
    with pytest.raises(maske.MaskeError, match="nur Kontext"):
        maske.bauwerksmaske([(0, 0, 0)], [{"name": "K", "quelle": "kontext",
                                           "farbe_srgb_8bit": list(KONTEXT_FARBE)}])


def test_runner_schreibt_dieselbe_quelle_und_schliesst_den_kontext_aus():
    assert f'eintragen(obj.name, "{maske.QUELLE_KONTEXT}")' in RUNNER_QUELLE
    assert RUNNER_QUELLE.count('obj.type != "MESH" or _ist_kontext(obj)') == 2, (
        "beide Hüllboxen (Szene und Bauwerk) lassen den Kontext aus")
    assert 'o.type == "MESH" and not _ist_kontext(o)' in RUNNER_QUELLE
    # Kein Pfad im Bericht: Die Quelle ist der Fingerabdruck.
    assert 'befund = {"quelle": "splat-ply", **kx.fingerabdruck(pfad)}' in RUNNER_QUELLE
    # Geladen wird nach der Kamera — Rahmung und Sicht sind dann schon gerechnet.
    assert (RUNNER_QUELLE.index("kamera_herkunft = _kamera_setzen(")
            < RUNNER_QUELLE.index("_kontext_laden(a)\n        kontext = "))


# ======================================================================================
# 5 · Die Naht nach aussen
# ======================================================================================

def _context(tmp_path, **anders):
    splat = tmp_path / "home" / "nutzer" / "umgebung.ply"
    splat.parent.mkdir(parents=True, exist_ok=True)
    splat.write_bytes(b"ply")
    return dict({"kind": "splat", "ply": str(splat),
                 "verortung": str(tmp_path / "umgebung.verortung.json"),
                 "transform": _ry(90.0, t=(1.0, 0.0, 2.0)), "fit": "behelf",
                 "crs_note": "Lokales System des Modells."}, **anders)


def test_kontext_aus_szene_liest_den_block(tmp_path):
    k = kosmo_szene.kontext_aus_szene(_context(tmp_path))
    assert k["maengel"] == []
    assert k["datei"] == "umgebung.ply" and k["verortung"] == "umgebung.verortung.json"
    assert k["matrix"] == pytest.approx(_ry(90.0, t=(1.0, 0.0, 2.0)))
    assert kosmo_szene.SATZ_KONTEXT_BEHELF in k["hinweise"]
    assert any("Lokales System" in h for h in k["hinweise"])
    assert kosmo_szene.kontext_aus_szene(None) is None


@pytest.mark.parametrize("anders, stichwort", [
    ({"kind": "mesh"}, "context.kind"),
    ({"ply": "/gibt/es/nicht.ply"}, "liegt auf diesem"),
    ({"ply": None}, "context.ply"),
    ({"transform": [1, 2, 3]}, "context.transform"),
    ({"fit": "geschaetzt"}, "context.fit"),
])
def test_ein_unbrauchbarer_kontext_ist_ein_mangel(tmp_path, anders, stichwort):
    k = kosmo_szene.kontext_aus_szene(_context(tmp_path, **anders))
    assert any(stichwort in m for m in k["maengel"]), k["maengel"]


def test_lies_szene_kennt_context_und_haelt_bei_mangel_an(tmp_path):
    grund = {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
             "style": {"prompt": "house"}, "render": {}, "vis": {}}
    gut = kosmo_szene.lies_szene(dict(grund, context=_context(tmp_path)))
    assert not any("context" in m for m in gut["maengel"]), gut["maengel"]
    assert gut["kontext"]["datei"] == "umgebung.ply"
    assert kosmo_szene.lies_szene(grund)["kontext"] is None
    schlecht = kosmo_szene.lies_szene(dict(grund, context=_context(tmp_path, kind="hdri")))
    assert any("context.kind" in m for m in schlecht["maengel"])
    assert "kontext" in kosmo_szene.DURCHGEREICHT


def test_der_vermerk_nach_aussen_traegt_keinen_pfad(tmp_path):
    k = kosmo_szene.kontext_aus_szene(_context(tmp_path))
    bericht = {"kontext": {"sha256": "ab" * 32, "punkte_gerendert": 10,
                           "verworfen_deckkraft": 2, "verdeckung": {"anteil": 0.0}}}
    v = kosmo_szene.kontext_vermerk(k, bericht)
    assert "nutzer" not in json.dumps(v) and str(tmp_path) not in json.dumps(v)
    assert v["sha256"] == "ab" * 32 and v["verdeckt_anteil"] == 0.0
    ergebnis = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"score": 0.9, "bestanden": True},
        je_kamera=[{"kamera": "s", kosmo_szene.URTEIL_KONTEXT: v}])
    hinweise = ergebnis["qa"]["verdict"].get("hinweise") or []
    assert any(h.startswith("UMGEBUNG: Splat 'umgebung.ply'") for h in hinweise)
    assert kosmo_szene.SATZ_KONTEXT_BEHELF in hinweise
    assert "nutzer" not in json.dumps(ergebnis, default=str)


def test_abholer_fuehrt_kontext_in_seinen_tabellen():
    assert {"kontext_ply", "kontext_matrix"} <= set(abholer.MULTIPASS_DURCHGEREICHT)


def test_mappe_haelt_den_splat_relativ_und_findet_ihn_wieder(tmp_path):
    mappe = tmp_path / "mappe"
    (mappe / "umgebung").mkdir(parents=True)
    splat = mappe / "umgebung" / "ort.ply"
    splat.write_bytes(b"ply")
    gespeichert = arbeitsgang._kontext_fuer_die_mappe({"kontext_ply": str(splat)}, mappe)
    assert gespeichert["kontext_ply"] == "umgebung/ort.ply"
    args = arbeitsgang._kontext_aus_der_mappe(dict(gespeichert, prompt="x"), mappe)
    assert Path(args["kontext_ply"]) == splat
    assert arbeitsgang._kontext_fuer_die_mappe({"prompt": "x"}, mappe) == {"prompt": "x"}
    splat.unlink()
    with pytest.raises(arbeitsgang.ArbeitsgangError, match="ort.ply"):
        arbeitsgang._kontext_aus_der_mappe(gespeichert, mappe)


# ======================================================================================
# 6 · Die echte Kette — Testbau + synthetischer Splat → Multipass
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

#: Wohin der Splat gelegt wird — glTF-Welt: Mitte des Testbaus (x 4, Blender-y 2,5 = glTF
#: z −2,5), der Boden 0,6 m unter der Unterkante der Bodenplatte. So steht er nirgends
#: VOR dem Bauwerk (Probe b), nur darunter, daneben und dahinter.
VERSATZ = (4.0, -0.6, -2.5)
LAUF = dict(up_axis="Y", kamera="s", aufloesung=160, hoehe=120, samples=4)


@pytest.fixture(scope="module")
def laeufe(tmp_path_factory):
    if _blender_fehlt() or _ifc_fehlt():
        pytest.skip("Blender oder .venv-ifc fehlt")
    tmp = tmp_path_factory.mktemp("kontext")
    ifc = tmp / "bau.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc)], check=True,
                   capture_output=True, cwd=WURZEL)
    glb = tmp / "bau.glb"
    assert seams.ifc_zu_glb(ifc, glb)["status"] == "ok"
    splat = tmp / "umgebung.ply"
    erzeugt = _erzeuger().erzeuge_splat(splat, punkte=20000, startwert=7)
    matrix = _ry(0.0, t=VERSATZ)
    ohne = seams.glb_zu_multipass(glb, tmp / "ohne", **LAUF)
    mit = seams.glb_zu_multipass(glb, tmp / "mit", kontext_ply=splat, kontext_matrix=matrix,
                                 **LAUF)
    return {"ohne": ohne, "mit": mit, "erzeugt": erzeugt, "matrix": matrix,
            "glb": glb, "splat": splat, "tmp": tmp}


def _tiefe_geometrie(bericht) -> int:
    werte, _, _ = bildlesen.lies_exr_tiefe_stdlib(bericht["depth_exr"])
    return sum(1 for w in werte if math.isfinite(w) and w < 1.0e7)


@ohne_kette
def test_a_die_tiefe_zeigt_den_splat(laeufe):
    assert laeufe["mit"]["status"] == "ok", laeufe["mit"].get("error")
    ohne, mit = _tiefe_geometrie(laeufe["ohne"]), _tiefe_geometrie(laeufe["mit"])
    assert mit > ohne * 1.5, (ohne, mit)


@ohne_kette
def test_b_bauwerksmaske_ohne_und_mit_splat_gleich(laeufe):
    ohne = maske.maske_aus_bericht(laeufe["ohne"])
    mit = maske.maske_aus_bericht(laeufe["mit"])
    assert ohne["gemessen"] and mit["gemessen"], mit.get("grund")
    assert mit["maske"] == ohne["maske"]
    assert mit["n_kontext"] > 0 and ohne["n_kontext"] == 0


@ohne_kette
def test_c_huellbox_und_kamera_unveraendert(laeufe):
    for feld in ("bbox", "bbox_bauwerk", "bbox_bauwerk_note", "kamera", "n_meshes",
                 "n_materialien", "sonne"):
        assert laeufe["mit"][feld] == laeufe["ohne"][feld], feld


@ohne_kette
def test_d_der_bericht_kontext_stimmt(laeufe):
    k = laeufe["mit"]["kontext"]
    e = laeufe["erzeugt"]
    assert k["datei"] == "umgebung.ply" and k["bytes"] == laeufe["splat"].stat().st_size
    assert (k["punkte_gelesen"], k["punkte_gerendert"], k["verworfen_deckkraft"]) == (
        e["punkte"], e["dicht"], e["schwebe"])
    assert k["matrix_angewandt"] is True
    assert k["zaehlt_zur_bauwerksbox"] is False and k["zaehlt_zur_rahmung"] is False
    # Hüllbox: glTF-Hüllbox der dichten Punkte, verschoben und in Blender gedreht.
    lo, hi = e["huellbox_dicht"]
    ecken = [contracts.blender_gltf_import_dreht(tuple(c + v for c, v in zip(punkt, VERSATZ)))
             for punkt in (lo, hi)]
    erwartet_lo = [min(ecken[0][i], ecken[1][i]) for i in range(3)]
    erwartet_hi = [max(ecken[0][i], ecken[1][i]) for i in range(3)]
    assert k["huellbox"][0] == pytest.approx(erwartet_lo, abs=1e-3)
    assert k["huellbox"][1] == pytest.approx(erwartet_hi, abs=1e-3)
    # Die Wand steht HINTER dem Bauwerk (Blender +y) und aufrecht (z bis ~ 7,4 m).
    assert k["huellbox"][1][1] > laeufe["mit"]["bbox"][1][1] + 5.0
    assert k["huellbox"][1][2] == pytest.approx(VERSATZ[1] + 8.0, abs=0.05)
    tabelle = laeufe["mit"]["material_id_tabelle"]
    assert tabelle[-1]["quelle"] == "kontext" and k["material_id"]["index"] == len(tabelle) - 1
    assert k["verdeckung"]["anteil"] == 0.0
    assert k["radius_m"]["untergrenze"] == kontext.RADIUS_MIN_M
    # Kein Pfad im Block — Regel 3.
    assert "/" not in json.dumps({n: w for n, w in k.items()
                                  if n not in ("matrix_bedeutung", "farbe", "radius_m")})


@ohne_kette
def test_e_ohne_splat_bitgleich(laeufe):
    ohne, mit = laeufe["ohne"], laeufe["mit"]
    assert "kontext" not in ohne
    assert not (Path(ohne["material_id_png"]).parent / "material_id_ohne_kontext.png").exists()
    # Die Material-ID ohne Kontext im Splat-Lauf ist Punkt für Punkt die des Laufs ohne.
    ohne_kontext = Path(mit["material_id_png"]).parent / mit["kontext"]["material_id_ohne_kontext_png"]
    assert (bildlesen.lies_png_farben(ohne_kontext)[0]
            == bildlesen.lies_png_farben(ohne["material_id_png"])[0])
    # Die Tabelle des Modells ist dieselbe; der Kontext steht nur hinten dran.
    assert mit["material_id_tabelle"][:-1] == ohne["material_id_tabelle"]


@ohne_kette
def test_drehung_um_die_hochachse_am_echten_lauf(laeufe):
    """Die Integrator-Probe am Bild: M = T · R_y(90°) — die Hüllbox im Bericht folgt."""
    m = _ry(90.0, t=VERSATZ)
    bericht = seams.glb_zu_multipass(laeufe["glb"], laeufe["tmp"] / "dreh", up_axis="Y",
                                     aufloesung=32, samples=1, material_id=False,
                                     kontext_ply=laeufe["splat"], kontext_matrix=m)
    lo, hi = laeufe["erzeugt"]["huellbox_dicht"]
    ecken = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    welt = [contracts.blender_gltf_import_dreht(_anwenden(m, p)) for p in ecken]
    k = bericht["kontext"]
    assert k["huellbox"][0] == pytest.approx([min(w[i] for w in welt) for i in range(3)], abs=1e-3)
    assert k["huellbox"][1] == pytest.approx([max(w[i] for w in welt) for i in range(3)], abs=1e-3)
    assert k["verdeckung"]["anteil"] is None

