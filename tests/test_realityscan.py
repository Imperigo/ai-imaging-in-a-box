"""Die RealityScan-Brücke: Fotos → Netz (Owner-Entscheid 81, 13.10.2026).

Was hier bewacht wird — **ohne RealityScan**, das es hier nicht gibt
---------------------------------------------------------------------
1. **Einschalten nur ausdrücklich** (Auflage 2): ohne :data:`realityscan.REALITYSCAN_ENV` aus,
   ohne Export-Parameterdatei ein Grund ohne Pfad, keine Suche nach einer Installation.
2. **Die stdlib-Hälfte**: ``wine_pfad``, die Aufnahme als COLMAP-Text (Rundreise mit dem
   eigenen Leser, auch beim Rig), ``finde_bilder``, die Befehlsfolge (``-headless`` zuerst,
   ``Z:``-Pfade, eine Liste ohne Shell).
3. **Der Lauf** mit einer Attrappe für ``realityscan-cli`` (ein Python-Skript in
   ``tmp_path``, das aus den COLMAP-Punkten ein farbiges Netz schreibt): Speicher nach Inhalt,
   Export ohne Farbe, Lageprüfung, Bericht ohne Pfade.
4. **Die Einbindung** in ``seams.kontext_vorbereiten``, den Abholer und die Kette: Vermerk
   ``weg``, Hinweis-Satz, Reihenfolge der Rückfälle, Treffer des Multipass-Speichers.
5. **Bis zur Blender-Stufe** (nur mit Blender): Das Netz aus der Attrappe wird als Netz geladen.

Alle Daten sind synthetisch (``tools/make_test_colmap.py``, ``tools/make_test_splat.py``,
Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, kette, kosmo_szene, kontext_netz as kn, realityscan as rs, seams
from conftest import MINI_PNG

WURZEL = Path(__file__).resolve().parents[1]


def _werkzeug(name: str):
    spez = importlib.util.spec_from_file_location(f"{name}_rs_probe",
                                                  WURZEL / "tools" / f"{name}.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _aufnahme(lauf: Path, *, text: bool = False, augenblicke: int = 6, punkte: int = 600,
              bilder: bool = True) -> Path:
    """``<lauf>/sparse/0`` (COLMAP 4 mit Rig, Ansichtsordner) und ``<lauf>/images/…``."""
    sparse = lauf / "sparse" / "0"
    _werkzeug("make_test_colmap").schreibe_aufnahme(
        sparse, augenblicke=augenblicke, punkte=punkte, text=text, ansichtsordner=True)
    if bilder:
        for b in kn.lies_aufnahme(sparse)["bilder"].values():
            p = lauf / "images" / b["name"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\xff\xd8 synthetisch " + b["name"].encode())
    return sparse


#: Die Attrappe für den Starter: liest die Befehlsfolge, nimmt die COLMAP-Punkte aus der
#: ``points3D.txt`` neben der ``images.txt`` und schreibt um jeden ein kleines farbiges
#: Dreieck — ein Netz, das dort liegt, wo die Aufnahme liegt. **Wie RealityScan 2.2 am
#: Heim-PC** (``auf-20261013-278``): Bildnamen werden gegen den Ordner der ``images.txt``
#: aufgelöst, und fehlt eines, «hängt» sie (Code 9, statt bis zur Frist zu warten); eine leere
#: ``points3D.txt`` ebenso; die Farben kommen als ``float`` 0..1, und ein **Deckel** aus einem
#: Riesendreieck liegt über allem; die Fassung steht nur mit ``-stdConsole`` in der Ausgabe.
#: Umgebungsvariablen steuern Versatz, fehlende Farbe, keinen Export und den Rückgabewert.
ATTRAPPE = r'''#!{python}
import json, os, struct, sys
args = sys.argv[1:]
if os.environ.get("RS_ATTRAPPE_PROTOKOLL"):
    with open(os.environ["RS_ATTRAPPE_PROTOKOLL"], "a") as d:
        d.write(json.dumps(args) + "\n")
def linux(w):
    assert w.startswith("Z:"), w
    return w[2:].replace("\\", "/")
txt = linux(args[args.index("-loadColmap") + 1])
k = args.index("-exportSelectedModel")
ziel = linux(args[k + 1])
for z in open(txt).read().splitlines()[4::2]:
    name = z.split()[9]
    if not os.path.isfile(os.path.join(os.path.dirname(txt), name)):
        print("Dialog: Bild fehlt " + name, file=sys.stderr)
        sys.exit(9)
v = [float(w) for w in os.environ.get("RS_ATTRAPPE_VERSATZ", "0,0,0").split(",")]
farbe = os.environ.get("RS_ATTRAPPE_OHNE_FARBE") != "1"
punkte = []
with open(os.path.join(os.path.dirname(txt), "points3D.txt")) as d:
    for z in d:
        if z.startswith("#") or not z.strip():
            continue
        t = z.split()
        punkte.append(tuple(float(t[i + 1]) + v[i] for i in range(3)))
if not punkte:
    print("COLMAP missing 3D points", file=sys.stderr)
    sys.exit(9)
ecken, dreiecke = [], []
for x, y, z in punkte:
    i0 = len(ecken)
    ecken += [(x, y, z), (x + 0.05, y, z), (x, y, z + 0.05)]
    dreiecke.append((i0, i0 + 1, i0 + 2))
i0 = len(ecken)                                   # der Deckel: ein Riesendreieck
ecken += [(-40.0, 9.0, -40.0), (40.0, 9.0, -40.0), (0.0, 9.0, 40.0)]
dreiecke.append((i0, i0 + 1, i0 + 2))
if "-stdConsole" in args:
    print("RealityScan 2.2.0.12345 (Attrappe)")
print("Export nach " + args[k + 1] + " aus " + os.path.dirname(txt))
if os.environ.get("RS_ATTRAPPE_KEIN_EXPORT") != "1":
    kopf = ("ply\nformat binary_little_endian 1.0\nelement vertex %d\nproperty float x\n"
            "property float y\nproperty float z\n" % len(ecken))
    if farbe:
        kopf += "property float red\nproperty float green\nproperty float blue\n"
    kopf += "element face %d\nproperty list uchar int vertex_indices\nend_header\n" % len(dreiecke)
    with open(ziel, "wb") as d:
        d.write(kopf.encode("ascii"))
        for e in ecken:
            d.write(struct.pack("<fff", *e) + (struct.pack("<fff", 0.6, 0.48, 0.36) if farbe else b""))
        for a, b, c in dreiecke:
            d.write(struct.pack("<Biii", 3, a, b, c))
code = int(os.environ.get("RS_ATTRAPPE_CODE", "0"))
if code:
    print("Fehler in " + txt, file=sys.stderr)
sys.exit(code)
'''


@pytest.fixture
def eingerichtet(tmp_path, monkeypatch):
    """RealityScan «installiert»: Attrappe als Starter (am Heim-PC das wine des Pakets), eine
    leere exe (mit Leerzeichen im Pfad), ein XML."""
    wo = tmp_path / "opt" / "realityscan"
    cli = wo / "bin" / "wine"
    cli.parent.mkdir(parents=True)
    cli.write_text(ATTRAPPE.replace("{python}", sys.executable), encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    exe = wo / "drive_c" / "Program Files" / "Epic Games" / "RealityScan.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"MZ")
    xml = tmp_path / "einstellungen" / "export ply.xml"
    xml.parent.mkdir(parents=True)
    xml.write_text("<ModelExport synthetisch='ja'/>", encoding="utf-8")
    monkeypatch.setenv(rs.REALITYSCAN_ENV, str(cli))
    monkeypatch.setenv(rs.REALITYSCAN_EXE_ENV, str(exe))
    monkeypatch.setenv(rs.REALITYSCAN_EXPORT_XML_ENV, str(xml))
    monkeypatch.setenv(rs.REALITYSCAN_SPEICHER_ENV, str(tmp_path / "speicher"))
    protokoll = tmp_path / "aufrufe.jsonl"
    monkeypatch.setenv("RS_ATTRAPPE_PROTOKOLL", str(protokoll))
    return {"cli": cli, "exe": exe, "xml": xml, "protokoll": protokoll,
            "speicher": tmp_path / "speicher"}


def _aufrufe(eingerichtet) -> list[list[str]]:
    p = eingerichtet["protokoll"]
    if not p.is_file():
        return []
    return [json.loads(z) for z in p.read_text(encoding="utf-8").splitlines() if z]


# ======================================================================================
# 1 · Einschalten nur ausdrücklich
# ======================================================================================

def test_ohne_variable_ist_realityscan_aus():
    assert rs.eingeschaltet() is False
    e = rs.einrichtung()
    assert e["bereit"] is False and e["ursache"] == rs.URSACHE_AUS
    assert rs.REALITYSCAN_ENV in e["grund"]


def test_fehlendes_export_xml_gibt_einen_grund_ohne_pfad(eingerichtet, monkeypatch, tmp_path):
    monkeypatch.delenv(rs.REALITYSCAN_EXPORT_XML_ENV)
    e = rs.einrichtung()
    assert e["eingeschaltet"] and not e["bereit"] and e["ursache"] == rs.URSACHE_EINRICHTUNG
    assert rs.REALITYSCAN_EXPORT_XML_ENV in e["grund"] and str(tmp_path) not in e["grund"]
    monkeypatch.setenv(rs.REALITYSCAN_EXPORT_XML_ENV, str(tmp_path / "fehlt.xml"))
    assert "zeigt auf keine Datei" in rs.einrichtung()["grund"]


def test_fehlende_cli_oder_exe_gibt_einen_grund(eingerichtet, monkeypatch, tmp_path):
    monkeypatch.setenv(rs.REALITYSCAN_ENV, str(tmp_path / "nirgends" / "realityscan-cli"))
    monkeypatch.setenv(rs.REALITYSCAN_EXE_ENV, str(tmp_path / "nirgends.exe"))
    e = rs.einrichtung()
    assert not e["bereit"] and "Starter" in e["grund"] and "wine" in e["grund"]
    assert "RealityScan.exe" in e["grund"] and str(tmp_path) not in e["grund"]
    assert e["cli"] is None and e["exe"] is None


def test_eingerichtet_ist_bereit(eingerichtet):
    e = rs.einrichtung()
    assert e["bereit"] and e["grund"] is None
    assert e["cli"] == str(eingerichtet["cli"]) and e["exe"] == str(eingerichtet["exe"])


def test_keine_automatische_suche_nach_einer_installation():
    """Auflage 2: Eine Suche fände RealityScan auch dort, wo es ein anderer für sich
    installiert hat. Nur die gesetzte Variable schaltet ein."""
    quelle = Path(rs.__file__).read_text(encoding="utf-8")
    assert "which(" not in quelle and "glob(" not in quelle and "rglob" not in quelle
    assert "/opt/realityscan" in rs.EXE_VORGABE          # nur als Vorgabe, nie als Suche


def test_realityscan_importiert_nur_die_standardbibliothek():
    import ast
    baum = ast.parse(Path(rs.__file__).read_text(encoding="utf-8"))
    namen = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            namen |= {a.name.split(".")[0] for a in knoten.names}
        elif isinstance(knoten, ast.ImportFrom) and knoten.module:
            namen.add(knoten.module.split(".")[0])
    assert namen - set(sys.stdlib_module_names) <= {"aiimaging", "__future__"}


# ======================================================================================
# 2 · Pfade, COLMAP-Text, Bilder, Befehlsfolge
# ======================================================================================

@pytest.mark.parametrize("linux, wine", [
    ("/", "Z:\\"),
    ("/mnt/daten/lauf/images", "Z:\\mnt\\daten\\lauf\\images"),
    ("/a//b/../c/", "Z:\\a\\c"),
    ("/opt/Program Files/x.exe", "Z:\\opt\\Program Files\\x.exe"),
])
def test_wine_pfad(linux, wine):
    assert rs.wine_pfad(linux) == wine
    assert rs.wine_pfad(Path(linux)) == wine


@pytest.mark.parametrize("schlecht", ["relativ/pfad", "", "/a\\b", '/a"b'])
def test_wine_pfad_weist_ab(schlecht):
    with pytest.raises(rs.RealityScanError):
        rs.wine_pfad(schlecht)


@pytest.mark.parametrize("text", [False, True])
def test_colmap_text_rundreise_posen_identisch_auch_beim_rig(tmp_path, text):
    sparse = _aufnahme(tmp_path / "lauf", text=text, bilder=False)
    vorher = kn.lies_aufnahme(sparse)
    assert vorher["rig"] is True
    befund = rs.colmap_als_text(sparse, tmp_path / "txt")
    nachher = kn.lies_aufnahme(tmp_path / "txt")
    assert nachher["format"] == "txt" and nachher["rig"] is False   # COLMAP 3 kennt kein Rig
    assert befund["bilder"] == len(vorher["bilder"]) == len(nachher["bilder"]) == 24
    for nr, b in vorher["bilder"].items():
        n = nachher["bilder"][nr]
        assert (n["name"], n["kamera"], n["q"], n["t"]) == (b["name"], b["kamera"], b["q"], b["t"])
        assert "/" in n["name"]                                       # z. B. front/0003.jpg
    for nr, k in vorher["kameras"].items():
        assert nachher["kameras"][nr] == k
    # Die Punkte samt Spuren, und die 2D-Punkte je Bild.
    assert kn.lies_punkte3d(tmp_path / "txt", 10 ** 6) == kn.lies_punkte3d(sparse, 10 ** 6)
    assert list(rs._bilder_2d(tmp_path / "txt")) == list(rs._bilder_2d(sparse))
    assert list(rs._punkte_3d(tmp_path / "txt")) == list(rs._punkte_3d(sparse))
    assert befund["punkte3d"] == 600 and befund["beobachtungen"] == 1200


def test_colmap_text_form_nach_der_dokumentation(tmp_path):
    sparse = _aufnahme(tmp_path / "lauf", bilder=False)
    rs.colmap_als_text(sparse, tmp_path / "txt")
    bilder = (tmp_path / "txt" / "images.txt").read_text(encoding="utf-8").splitlines()
    kopf = [z for z in bilder if z.startswith("#")]
    daten = [z for z in bilder if not z.startswith("#")]
    assert "IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME" in kopf[1]
    assert "Number of images: 24" in kopf[3]
    assert len(daten) == 2 * 24                                   # zwei Zeilen je Bild
    erste = daten[0].split()
    assert len(erste) == 10 and erste[9].endswith(".jpg")
    zweite = daten[1].split()
    assert len(zweite) % 3 == 0 and all(int(w) >= -1 for w in zweite[2::3])
    kameras = [z for z in (tmp_path / "txt" / "cameras.txt").read_text().splitlines()
               if not z.startswith("#")]
    assert len(kameras) == 4 and kameras[0].split()[1:4] == ["PINHOLE", "1086", "1086"]
    punkte = [z.split() for z in (tmp_path / "txt" / "points3D.txt").read_text().splitlines()
              if not z.startswith("#")]
    assert len(punkte) == 600 and all(len(t) >= 8 and (len(t) - 8) % 2 == 0 for t in punkte)


def test_colmap_text_ohne_punkte(tmp_path):
    sparse = _aufnahme(tmp_path / "lauf", bilder=False)
    befund = rs.colmap_als_text(sparse, tmp_path / "txt", mit_punkten=False)
    assert befund["punkte3d"] == 0
    assert kn.lies_punkte3d(tmp_path / "txt") == []
    assert len(kn.lies_aufnahme(tmp_path / "txt")["bilder"]) == 24
    assert all(not punkte for _, punkte in rs._bilder_2d(tmp_path / "txt"))


def test_colmap_text_weist_bildnamen_mit_leerzeichen_ab(tmp_path):
    sparse = _aufnahme(tmp_path / "lauf", text=True, bilder=False)
    p = sparse / "images.txt"
    p.write_text(p.read_text().replace("front/0000.jpg", "front/0 000.jpg"), encoding="utf-8")
    with pytest.raises(rs.RealityScanError, match="Leerzeichen"):
        rs.colmap_als_text(sparse, tmp_path / "txt")


def test_finde_bilder_nach_der_konvention(tmp_path):
    sparse = _aufnahme(tmp_path / "lauf")
    fund = rs.finde_bilder(sparse)
    assert fund["gefunden"] and fund["ordner"] == tmp_path / "lauf" / "images"
    assert fund["anzahl"] == 24 and fund["grund"] is None and len(fund["sha256"]) == 64
    # Eine andere Grösse ist ein anderer Inhalt — der Schlüssel ändert sich.
    p = tmp_path / "lauf" / "images" / "back" / "0002.jpg"
    p.write_bytes(p.read_bytes() + b"mehr")
    assert rs.finde_bilder(sparse)["sha256"] != fund["sha256"]
    # Ein fehlendes Bild: nicht gefunden, mit Zahl und Name, ohne Pfad.
    p.unlink()
    fehlt = rs.finde_bilder(sparse)
    assert not fehlt["gefunden"] and fehlt["fehlend"] == 1
    assert "back/0002.jpg" in fehlt["grund"] and str(tmp_path) not in fehlt["grund"]


def test_finde_bilder_hinter_einem_verweis_und_ausdruecklich(tmp_path):
    sparse = _aufnahme(tmp_path / "lauf")
    verweis = tmp_path / "anderswo" / "sparse" / "0"
    verweis.parent.mkdir(parents=True)
    verweis.symlink_to(sparse)
    assert rs.finde_bilder(verweis)["gefunden"]               # über das Ziel des Verweises
    assert not rs.finde_bilder(sparse, tmp_path / "leer")["gefunden"]
    assert rs.finde_bilder(verweis, tmp_path / "lauf" / "images")["gefunden"]
    shutil.rmtree(tmp_path / "lauf" / "images")
    assert "nicht gefunden" in rs.finde_bilder(sparse)["grund"]


def _cmd(**kw):
    return rs.kommando(cli="/opt/realityscan/bin/wine",
                       exe="/opt/rs/drive_c/Program Files/Epic Games/RealityScan.exe",
                       images_txt="/tmp/arbeit/colmap/images.txt",
                       netz_ply="/tmp/arbeit/export.ply", export_xml="/home/x/export ply.xml",
                       **kw)


def test_kommando_wie_am_heim_pc_gemessen():
    """Die Befehlsfolge aus ``auf-20261013-278``: ``-stdConsole`` für die Fassung (F8),
    ``-loadColmap`` ohne ``-addFolder`` (doppelte Bilder, F3) und ohne ``-align`` (eigene
    Komponenten, F5), ``-exportSelectedModel`` statt ``"Model 1"`` (unvereinfacht, F6)."""
    cmd = _cmd()
    assert cmd[0].endswith("wine") and cmd[1].endswith("RealityScan.exe")
    befehle = [w for w in cmd[2:] if w.startswith("-")]
    assert befehle == ["-headless", "-stdConsole", "-newScene", "-loadColmap",
                       "-selectMaximalComponent", "-setReconstructionRegionAuto",
                       "-calculateNormalModel", "-simplify", "-calculateVertexColors",
                       "-exportSelectedModel", "-quit"]
    assert cmd[2] == "-headless"                               # nur als erster Befehl erlaubt
    for weg in ("-addFolder", "-align", "-importColmap", "-exportModel", "Model 1"):
        assert weg not in cmd
    assert cmd[cmd.index("-loadColmap") + 1] == "Z:\\tmp\\arbeit\\colmap\\images.txt"
    assert cmd[cmd.index("-simplify") + 1] == str(rs.ZIEL_DREIECKE)
    k = cmd.index("-exportSelectedModel")
    assert cmd[k + 1:k + 3] == ["Z:\\tmp\\arbeit\\export.ply", "Z:\\home\\x\\export ply.xml"]
    assert cmd[-1] == "-quit"
    # Eine Liste ohne Shell: kein Element trägt Anführungszeichen, Leerzeichen bleiben
    # in EINEM Element.
    assert not any('"' in w or "'" in w for w in cmd)
    assert sum(1 for w in cmd if "Program Files" in w) == 1


def test_kommando_zahlen():
    assert _cmd(ziel_dreiecke=1234)[_cmd().index("-simplify") + 1] == "1234"
    with pytest.raises(rs.RealityScanError):
        _cmd(ziel_dreiecke=0)


def test_colmap_text_bildnamen_relativ_zum_textordner(tmp_path):
    """278 F3: ``-loadColmap`` löst die Namen gegen den Ordner der ``images.txt`` auf; fehlt
    ein Bild, wartet RealityScan auf einen Dialog. Jeder Name zeigt darum von dort aufs Foto —
    relativ, weil absolute Namen an den Ordner angehängt werden."""
    sparse = _aufnahme(tmp_path / "lauf")
    txt = tmp_path / "speicher" / "schluessel" / "lauf-x" / "colmap"
    rs.colmap_als_text(sparse, txt, bilder=tmp_path / "lauf" / "images")
    a = kn.lies_aufnahme(txt)
    vorher = kn.lies_aufnahme(sparse)
    for nr, b in a["bilder"].items():
        assert not b["name"].startswith("/") and b["name"].startswith("../")
        assert (txt / b["name"]).resolve() == (tmp_path / "lauf" / "images"
                                               / vorher["bilder"][nr]["name"]).resolve()
        assert (b["q"], b["t"]) == (vorher["bilder"][nr]["q"], vorher["bilder"][nr]["t"])
    # Ein Leerzeichen auf dem Weg wäre im Text nicht darstellbar — Grund statt Hänger.
    leer = tmp_path / "mit leer" / "images"
    shutil.copytree(tmp_path / "lauf" / "images", leer)
    with pytest.raises(rs.RealityScanError, match="Leerzeichen") as fehler:
        rs.colmap_als_text(sparse, tmp_path / "t2", bilder=leer)
    assert fehler.value.ursache == rs.URSACHE_BILDER


def test_der_starter_gibt_eine_liste_ohne_shell_in_eigener_gruppe_weiter(monkeypatch):
    gesehen = {}

    class Prozess:
        pid, returncode = 4711, 0

        def __init__(self, cmd, **kw):
            gesehen.update(cmd=cmd, **kw)

        def communicate(self, timeout=None):
            gesehen["frist"] = timeout
            return "", ""

    monkeypatch.setattr(rs.subprocess, "Popen", Prozess)
    cmd = _cmd()
    ergebnis = rs._starte_gruppe(cmd, 10)
    assert gesehen["cmd"] is cmd and isinstance(gesehen["cmd"], list)
    assert not gesehen.get("shell") and gesehen["start_new_session"] is True
    assert gesehen["frist"] == 10 and ergebnis.returncode == 0


@pytest.mark.skipif(not hasattr(os, "killpg"), reason="nur POSIX")
def test_die_frist_beendet_die_ganze_gruppe_auch_das_enkelkind(tmp_path, monkeypatch):
    """278 F9: Nach der Frist blieb ``RealityScan.exe`` als Waise stehen, weil nur ``wine``
    beendet wurde. Hier startet der «Starter» ein Kind, das weiterliefe — es muss mit weg."""
    monkeypatch.setattr(rs, "NACHFRIST_S", 2.0)
    pid_datei = tmp_path / "kind.pid"
    skript = ("import subprocess, sys, time\n"
              "k = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
              f"open({str(pid_datei)!r}, 'w').write(str(k.pid))\n"
              "time.sleep(60)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        rs._starte_gruppe([sys.executable, "-c", skript], 3)
    kind = int(pid_datei.read_text())
    import time
    for _ in range(50):                                         # höchstens 5 s
        try:
            os.kill(kind, 0)
        except ProcessLookupError:
            break
        # Ein Zombie (schon beendet, nur nicht abgeholt) zählt als beendet.
        try:
            if Path(f"/proc/{kind}/stat").read_text().split()[2] == "Z":
                break
        except OSError:
            break
        time.sleep(0.1)
    else:
        os.kill(kind, 9)
        raise AssertionError("das Enkelkind lebt nach der Frist weiter")


def test_ohne_pfade_nimmt_linux_und_windows_pfade():
    text = ("Fehler in /home/nutzer/geheim/lauf/netz.ply und Z:\\home\\nutzer\\x\\export.xml, "
            "Ordner /home/nutzer; siehe https://example.org/a/b")
    aus = rs.ohne_pfade(text)
    assert "nutzer" not in aus and "geheim" not in aus
    assert "<pfad>/netz.ply" in aus and "<pfad>/export.xml" in aus
    assert "https://example.org/a/b" in aus
    assert rs.ohne_pfade("in /a/b/c", {"/a/b": "<arbeit>"}) == "in <arbeit>/c"
    assert rs.ohne_pfade("in Z:\\a\\b\\c", {"/a/b": "<arbeit>"}) == "in <arbeit>\\c"


def test_ohne_pfade_auch_doppelt_maskiert_und_mit_schraegstrich():
    """278: Wine schreibt Pfade in manchen Meldungen doppelt maskiert — so stand am Heim-PC
    ein Benutzerverzeichnis im Fehlertext (Regel 3)."""
    for text in ("Fehler: Z:\\\\home\\\\nutzer\\\\geheim\\\\export.ply fehlt",
                 "Fehler: z:\\\\home\\\\nutzer\\\\ordner fehlt",
                 "Fehler: Z:/home/nutzer/geheim/export.ply fehlt",
                 "Fehler: C:\\users\\nutzer\\AppData\\Local\\Temp\\RealityScan.log"):
        aus = rs.ohne_pfade(text)
        assert "nutzer" not in aus and "geheim" not in aus, aus
        assert aus.startswith("Fehler: <pfad>")
    assert rs.ohne_pfade("Z:\\\\a\\\\b\\\\c", {"/a/b": "<arbeit>"}).startswith("<arbeit>")
    assert rs.ohne_pfade("Z:/a/b/c", {"/a/b": "<arbeit>"}) == "<arbeit>/c"
    assert rs.ohne_pfade("siehe https://example.org/a/b") == "siehe https://example.org/a/b"


# ======================================================================================
# 3 · Der Lauf mit der Attrappe
# ======================================================================================

def test_lauf_schreibt_ein_netz_und_einen_bericht_ohne_pfade(tmp_path, eingerichtet):
    sparse = _aufnahme(tmp_path / "home" / "nutzer" / "lauf")
    b = rs.realityscan_zu_netz(sparse)
    assert b["status"] == "ok" and b["zwischenspeicher"]["treffer"] is False
    assert kn.art_der_datei(b["netz_ply"]) == "netz"
    assert b["netz"]["dreiecke"] == 600 and b["netz"]["ecken"] == 1800   # ohne Deckel
    assert b["netz"]["vereinfacht"] is True and b["netz"]["format"] == "binary_little_endian"
    assert b["bereinigung"]["farben"] == "float→uchar"
    assert b["bereinigung"]["deckel_dreiecke"] == 1 and b["bereinigung"]["ecken_entfernt"] == 3
    assert b["programm"]["fassung"] == "2.2.0.12345"
    assert b["lage"]["passt"] and b["lage"]["nah_colmap"] > 0.95
    assert b["aufnahme"]["rig"] is True and b["bilder"]["anzahl"] == 24
    ohne = {k: v for k, v in b.items() if k != "netz_ply"}
    text = json.dumps(ohne, ensure_ascii=False)
    assert str(tmp_path) not in text and "nutzer" not in text and "Z:\\" not in text
    assert "<arbeit>" in b["ausgabe"]["stdout"]                 # der Arbeitsordner, ersetzt
    # Die Attrappe fand jedes Bild relativ zur images.txt (sonst Code 9), ohne -addFolder.
    (aufruf,) = _aufrufe(eingerichtet)
    assert "-addFolder" not in aufruf and "-loadColmap" in aufruf
    # Farben als uchar, wie Blender sie liest.
    kopf = kn.lies_ply_kopf(b["netz_ply"])
    typen = {e["name"]: e["typ"] for e in kopf["elemente"][0]["eigenschaften"]}
    assert (typen["red"], typen["green"], typen["blue"]) == ("uchar",) * 3
    assert rs.lies_ecken(b["netz_ply"])["farbe"]


def test_aufnahme_ohne_punkte_startet_nicht(tmp_path, eingerichtet):
    """278 F4: An einer leeren points3D.txt hängt RealityScan — darum ein Grund vorher."""
    sparse = _aufnahme(tmp_path / "lauf", punkte=0)

    def nie(cmd, timeout):
        raise AssertionError("ohne 3D-Punkte darf nichts starten")

    with pytest.raises(rs.RealityScanError, match="3D-Punkte") as fehler:
        rs.realityscan_zu_netz(sparse, _starte=nie)
    assert fehler.value.ursache == rs.URSACHE_AUFNAHME


def _ply(pfad, ecken, flaechen, *, farbe="float", form="binary_little_endian"):
    kopf = ["ply", f"format {form} 1.0", f"element vertex {len(ecken)}",
            "property float x", "property float y", "property float z",
            f"property {farbe} red", f"property {farbe} green", f"property {farbe} blue",
            f"element face {len(flaechen)}", "property list uchar int vertex_indices",
            "end_header"]
    import struct
    with open(pfad, "wb") as d:
        d.write(("\n".join(kopf) + "\n").encode())
        for e in ecken:
            if form == "ascii":
                d.write((" ".join(str(w) for w in e) + "\n").encode())
            else:
                f = "<fff" + ("fff" if farbe == "float" else "BBB")
                d.write(struct.pack(f, *e))
        for fl in flaechen:
            if form == "ascii":
                d.write((" ".join(str(w) for w in (len(fl), *fl)) + "\n").encode())
            else:
                d.write(struct.pack(f"<B{len(fl)}i", len(fl), *fl))
    return pfad


@pytest.mark.parametrize("form", ["binary_little_endian", "ascii"])
def test_bereinige_export_farben_und_deckel(tmp_path, form):
    """278 F7 und der Deckel: float-Farben werden uchar, das Riesendreieck fällt weg, seine
    Ecken mit ihm; ein Viereck (Fächer) bleibt, wenn es klein ist."""
    N = 80                         # 2.5 % der Diagonale sind dann ≈ 2.7, eine Kante ≤ 1.42
    ecken, flaechen = [], []
    for i in range(N):
        for j in range(N):
            ecken.append((float(i), 0.0, float(j), 0.5, 1.0, 0.0))
    for i in range(N - 1):
        for j in range(N - 1):
            a = i * N + j
            flaechen.append((a, a + 1, a + N + 1))
    flaechen.append((0, 1, N + 1, N))                              # ein Viereck
    d0 = len(ecken)
    ecken += [(-500.0, 5.0, -500.0, 1, 1, 1), (500.0, 5.0, -500.0, 1, 1, 1),
              (0.0, 5.0, 500.0, 1, 1, 1)]
    flaechen.append((d0, d0 + 1, d0 + 2))
    q = _ply(tmp_path / "roh.ply", ecken, flaechen, form=form)
    b = rs.bereinige_export(q, tmp_path / "netz.ply")
    assert b["farben"] == "float→uchar" and b["deckel_dreiecke"] == 1
    # Die drei Deckelecken und die Ecke (N-1, 0), die im Gitter keine Fläche trägt.
    assert b["ecken_entfernt"] == 4
    assert b["deckel_flaeche_anteil"] > 0.99
    kopf = kn.lies_ply_kopf(tmp_path / "netz.ply")
    assert kopf["format"] == "binary_little_endian"
    assert kn.netz_kennzahlen(tmp_path / "netz.ply")["dreiecke"] >= (N - 1) ** 2
    _, _, ecken2, flaechen2 = rs._lies_netz(tmp_path / "netz.ply", kopf)
    assert len(ecken2) == N * N - 1 and len(flaechen2) == (N - 1) ** 2 + 1
    assert {e[3:] for e in ecken2} == {(128, 255, 0)}
    assert max(i for f in flaechen2 for i in f) == N * N - 2


def test_bereinige_export_laesst_uchar_und_ohne_deckel_gleich(tmp_path):
    n = 80
    ecken = [(float(i), 0.0, float(j), 10, 20, 30) for i in range(n) for j in range(n)]
    flaechen = []
    for i in range(n - 1):
        for j in range(n - 1):
            a = i * n + j
            flaechen += [(a, a + 1, a + n), (a + 1, a + n + 1, a + n)]
    q = _ply(tmp_path / "roh.ply", ecken, flaechen, farbe="uchar")
    b = rs.bereinige_export(q, tmp_path / "netz.ply")
    assert (b["farben"], b["deckel_dreiecke"], b["ecken_entfernt"]) == ("uchar", 0, 0)
    _, _, e2, f2 = rs._lies_netz(tmp_path / "netz.ply", kn.lies_ply_kopf(tmp_path / "netz.ply"))
    assert {tuple(e[3:]) for e in e2} == {(10, 20, 30)} and len(e2) == n * n
    def lage(ek, fl):                                   # Flächen als Koordinaten, ohne Nummern
        return sorted(tuple(sorted(tuple(ek[i][:3]) for i in f)) for f in fl)
    assert lage(e2, f2) == lage(ecken, flaechen)


def test_bereinige_export_ohne_farbe_ist_ein_exportfehler(tmp_path):
    p = tmp_path / "roh.ply"
    p.write_bytes(b"ply\nformat ascii 1.0\nelement vertex 3\nproperty float x\n"
                  b"property float y\nproperty float z\nelement face 1\n"
                  b"property list uchar int vertex_indices\nend_header\n0 0 0\n1 0 0\n0 0 1\n"
                  b"3 0 1 2\n")
    with pytest.raises(rs.RealityScanError) as fehler:
        rs.bereinige_export(p, tmp_path / "netz.ply")
    assert fehler.value.ursache == rs.URSACHE_EXPORT


def test_speicher_nach_inhalt(tmp_path, eingerichtet):
    sparse = _aufnahme(tmp_path / "lauf")
    erst = rs.realityscan_zu_netz(sparse)
    zweit = rs.realityscan_zu_netz(sparse)
    assert zweit["zwischenspeicher"] == {"treffer": True,
                                         "schluessel": erst["zwischenspeicher"]["schluessel"]}
    assert zweit["netz"]["sha256"] == erst["netz"]["sha256"] and zweit["lage"]["passt"]
    assert len(_aufrufe(eingerichtet)) == 1
    # Ein anderer Inhalt der Exportdatei ist ein anderes Netz.
    eingerichtet["xml"].write_text("<ModelExport anders='ja'/>", encoding="utf-8")
    dritt = rs.realityscan_zu_netz(sparse)
    assert dritt["zwischenspeicher"]["treffer"] is False and len(_aufrufe(eingerichtet)) == 2
    # Ein anderes Foto (Grösse) ebenso.
    p = tmp_path / "lauf" / "images" / "front" / "0001.jpg"
    p.write_bytes(p.read_bytes() * 2)
    assert rs.realityscan_zu_netz(sparse)["zwischenspeicher"]["treffer"] is False


def test_schluessel_haengt_an_jedem_teil():
    grund = dict(aufnahme_sha="a" * 64, bilder_sha="b" * 64, export_xml_sha="c" * 64,
                 parameter={"fassung": 1, "ziel_dreiecke": 5})
    s = rs.realityscan_schluessel(**grund)
    for feld, wert in (("aufnahme_sha", "d" * 64), ("bilder_sha", "e" * 64),
                       ("export_xml_sha", "f" * 64),
                       ("parameter", {"fassung": 1, "ziel_dreiecke": 6})):
        assert rs.realityscan_schluessel(**dict(grund, **{feld: wert})) != s
    assert rs.realityscan_schluessel(**grund) == s


def test_export_ohne_farbe_ist_ein_fehler_und_wird_gespeichert(tmp_path, eingerichtet,
                                                               monkeypatch):
    sparse = _aufnahme(tmp_path / "lauf")
    monkeypatch.setenv("RS_ATTRAPPE_OHNE_FARBE", "1")
    with pytest.raises(rs.RealityScanError) as fehler:
        rs.realityscan_zu_netz(sparse)
    assert fehler.value.ursache == rs.URSACHE_EXPORT and "red/green/blue" in fehler.value.grund
    # Kein zweiter Lauf von Stunden: Derselbe Export brächte dasselbe.
    with pytest.raises(rs.RealityScanError, match="aus dem Speicher"):
        rs.realityscan_zu_netz(sparse)
    assert len(_aufrufe(eingerichtet)) == 1


def test_ohne_export_und_mit_fehlercode_wird_nicht_gespeichert(tmp_path, eingerichtet,
                                                               monkeypatch):
    sparse = _aufnahme(tmp_path / "lauf")
    monkeypatch.setenv("RS_ATTRAPPE_KEIN_EXPORT", "1")
    for _ in range(2):
        with pytest.raises(rs.RealityScanError) as fehler:
            rs.realityscan_zu_netz(sparse)
        assert fehler.value.ursache == rs.URSACHE_LAUF and "kein Netz" in fehler.value.grund
    assert len(_aufrufe(eingerichtet)) == 2                     # beide Male neu versucht
    monkeypatch.delenv("RS_ATTRAPPE_KEIN_EXPORT")
    monkeypatch.setenv("RS_ATTRAPPE_CODE", "3")
    with pytest.raises(rs.RealityScanError) as fehler:
        rs.realityscan_zu_netz(sparse)
    assert fehler.value.ursache == rs.URSACHE_LAUF and "Code 3" in fehler.value.grund
    assert str(tmp_path) not in fehler.value.grund
    # Kein leerer Schlüssel-Ordner bleibt zurück.
    assert not any(eingerichtet["speicher"].glob("*/netz.ply"))


def test_die_frist_kommt_beim_starter_an(tmp_path, eingerichtet, monkeypatch):
    sparse = _aufnahme(tmp_path / "lauf")
    gesehen = {}

    def starte(cmd, timeout):
        gesehen["frist"] = timeout
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setenv("AIIMAGING_ZEITFAKTOR", "2")
    with pytest.raises(rs.RealityScanError, match="Frist") as fehler:
        rs.realityscan_zu_netz(sparse, _starte=starte)
    assert fehler.value.ursache == rs.URSACHE_LAUF
    assert gesehen["frist"] == pytest.approx(2 * rs.GESAMTFRIST_REALITYSCAN_S)


def test_nicht_eingerichtet_startet_nichts(tmp_path, monkeypatch):
    sparse = _aufnahme(tmp_path / "lauf")

    def nie(cmd, timeout):
        raise AssertionError("ohne Einrichtung darf nichts starten")

    with pytest.raises(rs.RealityScanError) as fehler:
        rs.realityscan_zu_netz(sparse, _starte=nie)
    assert fehler.value.ursache == rs.URSACHE_AUS


# ----------------------------------------------------------------------------------------
# Die Lage
# ----------------------------------------------------------------------------------------

def _gitter(n=12, kante=10.0):
    return [(kante * i / n, 0.0, kante * j / n) for i in range(n) for j in range(n)] + \
           [(kante * i / n, kante * j / n, 0.0) for i in range(n) for j in range(n)]


def test_nah_anteil():
    a = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
    assert rs.nah_anteil(a, [(0.05, 0.0, 0.0)], 0.1) == 0.5
    assert rs.nah_anteil(a, [], 0.1) == 0.0 and rs.nah_anteil([], a, 0.1) == 0.0


def test_lage_passend_verschoben_skaliert_und_ohne_punkte():
    punkte = _gitter()
    passt = rs.lage_befund(ecken=punkte, punkte=punkte)
    assert passt["passt"] and passt["nah_colmap"] == 1.0 and passt["massstab"] == 1.0
    verschoben = rs.lage_befund(ecken=[(x + 3, y + 2, z + 3) for x, y, z in punkte],
                                punkte=punkte)
    assert not verschoben["passt"] and "neu gelagert" in verschoben["grund"]
    skaliert = rs.lage_befund(ecken=[(3 * x, 3 * y, 3 * z) for x, y, z in punkte],
                              punkte=punkte)
    assert not skaliert["passt"] and skaliert["massstab"] == pytest.approx(3.0, rel=0.01)
    leer = rs.lage_befund(ecken=punkte, punkte=[])
    assert not leer["passt"] and "nicht pruefbar" in leer["grund"]
    splat_daneben = rs.lage_befund(ecken=punkte, punkte=punkte,
                                   splat_punkte=[(x, y + 5, z) for x, y, z in punkte])
    assert not splat_daneben["passt"] and "beim Splat" in splat_daneben["grund"]


def test_verschobener_export_wird_wegen_der_lage_nicht_benutzt(tmp_path, eingerichtet,
                                                                monkeypatch):
    sparse = _aufnahme(tmp_path / "lauf")
    monkeypatch.setenv("RS_ATTRAPPE_VERSATZ", "5,3,5")
    with pytest.raises(rs.RealityScanError) as fehler:
        rs.realityscan_zu_netz(sparse)
    assert fehler.value.ursache == rs.URSACHE_LAGE
    assert fehler.value.bericht["lage"]["nah_colmap"] < rs.LAGE_NAH_MIN
    # Das Netz bleibt im Speicher — die Prüfung ist billig, der Lauf nicht.
    with pytest.raises(rs.RealityScanError):
        rs.realityscan_zu_netz(sparse)
    assert len(_aufrufe(eingerichtet)) == 1


def test_lage_auch_gegen_den_splat(tmp_path, eingerichtet):
    lauf = tmp_path / "lauf"
    sparse = _aufnahme(lauf, punkte=1500)
    splat = lauf / "umgebung.ply"
    _werkzeug("make_test_splat").erzeuge_splat(splat, punkte=20000)
    b = rs.realityscan_zu_netz(sparse, splat=splat)
    assert b["lage"]["passt"], b["lage"]
    assert b["lage"]["nah_splat"] >= rs.LAGE_NAH_MIN and b["lage"]["n_splat"] > 1000


# ======================================================================================
# 4 · Die Einbindung
# ======================================================================================

def _splat_neben_aufnahme(tmp_path, **kw) -> Path:
    lauf = tmp_path / "home" / "nutzer" / "lauf"
    _aufnahme(lauf, punkte=1500, **kw)
    splat = lauf / "umgebung.ply"
    _werkzeug("make_test_splat").erzeuge_splat(splat, punkte=20000)
    return splat


def _offener_weg(tmp_path, aufrufe):
    netz = tmp_path / "offen.ply"
    kn.schreibe_netz_ply(netz, [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(9, 9, 9)] * 3, [(0, 1, 2)])

    def bruecke(ply, **kw):
        aufrufe.append(ply)
        return {"netz_ply": str(netz), "netz": {"ecken": 3, "dreiecke": 1, "sha256": "ab"}}
    return bruecke


def test_einbindung_realityscan_zuerst_mit_satz(tmp_path, eingerichtet):
    splat = _splat_neben_aufnahme(tmp_path)
    offen = []
    v = seams.kontext_vorbereiten(splat, _splat_zu_netz=_offener_weg(tmp_path, offen))
    assert v["weg"] == rs.WEG and offen == []                 # der offene Weg lief nicht
    assert v["hinweis"] == rs.SATZ_REALITYSCAN and "nicht im Produkt" in v["hinweis"]
    assert v["realityscan_grund"] is None and kn.art_der_datei(v["ply"]) == "netz"
    assert v["netz"]["quelle"] == rs.WEG and v["netz"]["dreiecke"] == 1500
    assert v["netz"]["aufnahme"] == seams.AUFNAHME_NEBEN_SPLAT
    assert v["netz"]["programm_fassung"] == "2.2.0.12345" and v["netz"]["lage"]["nah_splat"]
    assert str(tmp_path) not in json.dumps(v["netz"]) and "nutzer" not in json.dumps(v["netz"])


def test_einbindung_ohne_variable_der_offene_weg(tmp_path):
    splat = _splat_neben_aufnahme(tmp_path)
    offen = []
    v = seams.kontext_vorbereiten(splat, _splat_zu_netz=_offener_weg(tmp_path, offen))
    assert v["weg"] == "netz" and offen == [splat] and v["hinweis"] is None
    assert v["realityscan_ursache"] == rs.URSACHE_AUS
    assert "nicht eingeschaltet" in v["realityscan_grund"]


@pytest.mark.parametrize("fall, ursache", [
    ("lage", rs.URSACHE_LAGE), ("bilder", rs.URSACHE_BILDER), ("aufnahme", rs.URSACHE_AUFNAHME),
    ("xml", rs.URSACHE_EINRICHTUNG), ("lauf", rs.URSACHE_LAUF), ("export", rs.URSACHE_EXPORT),
])
def test_einbindung_rueckfall_mit_grund(tmp_path, eingerichtet, monkeypatch, fall, ursache):
    splat = _splat_neben_aufnahme(tmp_path)
    lauf = splat.parent
    if fall == "lage":
        monkeypatch.setenv("RS_ATTRAPPE_VERSATZ", "5,3,5")
    elif fall == "bilder":
        shutil.rmtree(lauf / "images")
    elif fall == "aufnahme":
        shutil.rmtree(lauf / "sparse")
    elif fall == "xml":
        monkeypatch.delenv(rs.REALITYSCAN_EXPORT_XML_ENV)
    elif fall == "lauf":
        monkeypatch.setenv("RS_ATTRAPPE_CODE", "1")
    elif fall == "export":
        monkeypatch.setenv("RS_ATTRAPPE_OHNE_FARBE", "1")
    offen = []
    v = seams.kontext_vorbereiten(splat, _splat_zu_netz=_offener_weg(tmp_path, offen))
    assert v["weg"] == "netz" and offen == [splat]
    assert v["realityscan_ursache"] == ursache and v["realityscan_grund"]
    assert str(tmp_path) not in v["realityscan_grund"] and "nutzer" not in v["realityscan_grund"]
    assert v["hinweis"] is None


def test_einbindung_alles_scheitert_dann_kugeln(tmp_path, eingerichtet, monkeypatch):
    splat = _splat_neben_aufnahme(tmp_path)
    monkeypatch.setenv("RS_ATTRAPPE_CODE", "1")
    monkeypatch.setenv(seams.SPLAT_PYTHON_ENV, str(tmp_path / "fehlt" / "python"))
    v = seams.kontext_vorbereiten(splat)
    assert v["weg"] == "kugeln" and v["hinweis"] == kn.SATZ_KUGELN_NICHT_EINGERICHTET
    assert v["realityscan_ursache"] == rs.URSACHE_LAUF


def test_ein_geliefertes_netz_braucht_kein_realityscan(tmp_path, eingerichtet):
    netz = tmp_path / "n.ply"
    kn.schreibe_netz_ply(netz, [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(9, 9, 9)] * 3, [(0, 1, 2)])

    def nie(*a, **k):
        raise AssertionError("fuer ein geliefertes Netz laeuft nichts")

    v = seams.kontext_vorbereiten(netz, _splat_zu_netz=nie, _realityscan=nie)
    assert v["weg"] == "netz" and v["realityscan_ursache"] == rs.URSACHE_GELIEFERT


def test_abholer_und_vermerk_mit_realityscan(tmp_path, eingerichtet):
    splat = _splat_neben_aufnahme(tmp_path)
    gesehen = []

    def multipass(glb, aus, **kw):
        gesehen.append(kw)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"},
                "kontext": {"quelle": kn.QUELLE_NETZ}}

    def rendere(auftrag, **kw):
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path / "aus", nullprobe=False, _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))
    glb = tmp_path / "m.glb"
    glb.write_bytes(_werkzeug("make_test_glb").baue_glb(
        [("Haus", (-4.0, 0.0, -3.0), (4.0, 6.0, 3.0))]))
    kontext_ = kosmo_szene.kontext_aus_szene({"kind": "splat", "ply": str(splat),
                                              "fit": "passpunkte"})
    szene = {"kameras": [{"kuerzel": "s", "richtung": "s"}], "aufloesung": 64, "hoehe": 64,
             "samples": 1, "prompt": "a house", "kontext": kontext_}
    ergebnis = verarbeite({"modell": glb, "job_id": "vis-1-aaaaaa", "verzeichnis": tmp_path,
                           "szene": szene})
    assert kn.art_der_datei(gesehen[0]["kontext_ply"]) == "netz"
    assert gesehen[0]["kontext_ply"].startswith(str(eingerichtet["speicher"]))
    vermerk = ergebnis["kameras"][0][kosmo_szene.URTEIL_KONTEXT]
    assert vermerk["weg"] == rs.WEG and vermerk["netz"]["quelle"] == rs.WEG
    assert vermerk["realityscan_grund"] is None
    hinweise = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"score": 0.9, "bestanden": True},
        je_kamera=ergebnis["kameras"])["qa"]["verdict"].get("hinweise") or []
    assert rs.SATZ_REALITYSCAN in hinweise
    assert "nutzer" not in json.dumps(vermerk) and str(tmp_path) not in json.dumps(vermerk)


def test_vermerk_traegt_den_grund_ohne_realityscan():
    k = {"art": "splat", "datei": "u.ply", "weg": "netz", "hinweise": [],
         "realityscan_grund": "RealityScan nicht eingeschaltet."}
    assert kosmo_szene.kontext_vermerk(k)["realityscan_grund"] == "RealityScan nicht eingeschaltet."


# ----------------------------------------------------------------------------------------
# Der Speicher des Multipass unterscheidet den Weg
# ----------------------------------------------------------------------------------------

def _eintrag(weg=None, ursache=None, mit_weg=True):
    e = {"depth_png": None, "kontext": {"quelle": kn.QUELLE_NETZ}}
    if mit_weg:
        e["kontext_weg"] = {"weg": weg, "realityscan_ursache": ursache}
    return e


def _treffer(eintrag) -> bool:
    return kette._cache_maengel(kette.ART_MULTIPASS, eintrag, {}) == []


def test_multipass_treffer_ohne_realityscan_bleiben_wie_sie_waren():
    assert _treffer(_eintrag("netz", rs.URSACHE_AUS))
    assert _treffer(_eintrag(mit_weg=False))                    # von vor dieser Regel
    assert not _treffer(_eintrag(rs.WEG))                       # ausgeschaltet heisst aus


def test_multipass_treffer_nach_dem_einschalten(monkeypatch):
    monkeypatch.setenv(rs.REALITYSCAN_ENV, "/irgendwo/realityscan-cli")
    assert _treffer(_eintrag(rs.WEG))
    for ursache in (None, rs.URSACHE_AUS, rs.URSACHE_EINRICHTUNG, rs.URSACHE_LAUF):
        assert not _treffer(_eintrag("netz", ursache)), ursache
    assert not _treffer(_eintrag(mit_weg=False))
    for ursache in (rs.URSACHE_LAGE, rs.URSACHE_BILDER, rs.URSACHE_AUFNAHME,
                    rs.URSACHE_EXPORT, rs.URSACHE_GELIEFERT):
        assert _treffer(_eintrag("netz", ursache)), ursache
    # Die Kugel-Regel bleibt daneben bestehen.
    kugeln = {"depth_png": None, "kontext": {"quelle": kn.QUELLE_SPLAT}}
    assert not _treffer(kugeln)


def test_der_kettenknoten_traegt_den_realityscan_vermerk(tmp_path, monkeypatch):
    from aiimaging.graph import Knoten

    monkeypatch.setattr(seams, "glb_zu_multipass", lambda glb, out, **kw: {
        "status": "ok", "kontext": {"quelle": kn.QUELLE_NETZ}})
    monkeypatch.setattr(seams, "kontext_vorbereiten", lambda ply, matrix=None: {
        "ply": "netz.ply", "weg": rs.WEG, "netz": {"dreiecke": 2}, "grund": None,
        "hinweis": rs.SATZ_REALITYSCAN, "realityscan_grund": None,
        "realityscan_ursache": None})
    knoten = Knoten(id="multipass", art=kette.ART_MULTIPASS,
                    params={"aufloesung": 32, "samples": 1, "beauty": True,
                            "material_id": True, "kontext_ply": "u.ply"})
    bericht = kette._fuehre_multipass(knoten=knoten, eingaben=[{"glb_path": "m.glb",
                                                                "up_axis": "Y"}],
                                      out_dir=tmp_path)
    assert bericht["kontext_weg"]["weg"] == rs.WEG
    assert bericht["kontext_weg"]["hinweis"] == rs.SATZ_REALITYSCAN
    assert "realityscan_ursache" in bericht["kontext_weg"]


# ======================================================================================
# 5 · Bis zur Blender-Stufe
# ======================================================================================

def _blender_fehlt() -> bool:
    return not shutil.which("blender") and not Path("/opt/blender/blender").exists()


@pytest.mark.skipif(_blender_fehlt(), reason="Blender fehlt")
def test_der_ganze_weg_bis_blender(tmp_path, eingerichtet):
    splat = _splat_neben_aufnahme(tmp_path)
    v = seams.kontext_vorbereiten(splat)
    assert v["weg"] == rs.WEG, v.get("realityscan_grund")
    glb = tmp_path / "m.glb"
    glb.write_bytes(_werkzeug("make_test_glb").baue_glb(
        [("Haus", (-4.0, 0.0, -3.0), (4.0, 6.0, 3.0))]))
    bericht = seams.glb_zu_multipass(glb, tmp_path / "mp", up_axis="Y", kamera="s",
                                     aufloesung=96, hoehe=72, samples=1, kontext_ply=v["ply"])
    assert bericht["status"] == "ok", bericht.get("error")
    k = bericht["kontext"]
    assert k["quelle"] == kn.QUELLE_NETZ
    assert (k["ecken"], k["dreiecke"]) == (v["netz"]["ecken"], v["netz"]["dreiecke"])
    assert os.path.basename(v["ply"]) == k["datei"]
