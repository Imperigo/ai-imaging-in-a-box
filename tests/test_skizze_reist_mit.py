"""Die Skizze reist mit — «Bild aus Skizze» aus einer Mappe am Mac (Demobefund 25.10.2026).

Mac 0.3.66, iPad 0.3.66, Mappe am Mac «haus-am-hang»: Das iPad zeichnete auf das Grundbild sSW
(«Mappe» → «Darauf skizzieren»), die Skizze kam am Mac an (``ueber =
bilder/vis-…/sSW__schoenbild.png``). Bestellt kam vom Heim-PC: «liegt nur am Mac … reist beim
Bestellen noch nicht mit» (Befund F4, ``test_f4_skizze_nur_am_mac.py``) — in einer Mappe am Mac
ging «Bild aus Skizze» überhaupt nicht.

Seither schickt die Knotenansicht bei einer Mappe am Mac die Skizze im Formular mit
(``skizze_png``, ``unterlage_png``, ``skizze_info``); der Heim-PC prüft sie, legt sie in den
Auftrag, und der Abholer baut daraus eine Mappe im Auftrag und rechnet sie wie jede andere — vom
Standpunkt des Bildes unter der Skizze (Entscheid 96b), hier sSW.

Regel 3: synthetische Bilder aus ein paar Bytes; die Attrappen wie ``test_skizze_fuehrt``.
"""
from __future__ import annotations

import http.client
import json
import struct
from pathlib import Path

import pytest

from aiimaging import abholer, knotenweg, projekt

from test_heimfehler_20261020 import _formular
from test_mappenpaket import _mappe, flaeche  # noqa: F401 (Fixture)
from test_skizze_fuehrt import (BLAU, ROT, _Modell, _einfarbig, _ergebnis, _rgba_png, _szene,
                                _tabelle)

WURZEL = Path(__file__).resolve().parents[1]
KENNUNG = "vis-1792900000-abc123"
GRUNDBILD_AUFTRAG = "vis-1792842106-6e0b77"
UEBER = f"bilder/{GRUNDBILD_AUFTRAG}/sSW__schoenbild.png"
SKIZZE = "ipad/skizze-20261025-122953-50b5.png"


def _png(tmp_path, name, punkte=None, breite=4, hoehe=4) -> bytes:
    return _rgba_png(tmp_path / "bytes" / name, breite, hoehe, punkte or {}).read_bytes()


def _unterlage(tmp_path) -> bytes:
    return _einfarbig(tmp_path / "bytes" / "unterlage.png", 4, 4, BLAU).read_bytes()


def _anlage(tmp_path, **mehr) -> dict:
    return {"png": _png(tmp_path, "skizze.png", {(1, 1): (*ROT, 255)}),
            "unterlage": _unterlage(tmp_path), "ueber": UEBER, "bemerkung": "ein Vordach",
            **mehr}


@pytest.fixture
def glb() -> bytes:
    """Eine kleinste gültige glb — das Modell, das die Knotenansicht aus der Mappe am Mac schickt."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    return struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block


def _lege_an(tmp_path, glb, anlage, *, szene=None, am_mac="haus-am-hang", mappe_pfad=None,
             **mehr):
    return knotenweg.lege_an(tmp_path / "ablage", szene or _szene(name=SKIZZE), glb, "model.glb",
                             kennung=KENNUNG, mappe=am_mac, mappe_pfad=mappe_pfad,
                             am_mac=am_mac, skizze_anlage=anlage, **mehr)


# ============================================================ 1 · Annehmen

def test_die_skizze_aus_der_mappe_am_mac_wird_angenommen_und_liegt_im_auftrag(tmp_path, glb):
    zettel = _lege_an(tmp_path, glb, _anlage(tmp_path))
    ordner = tmp_path / "ablage" / KENNUNG
    anlage = ordner / knotenweg.ORDNER_SKIZZE_AM_MAC
    assert (anlage / knotenweg.DATEI_ANLAGE_SKIZZE).is_file()
    assert (anlage / knotenweg.DATEI_ANLAGE_UNTERLAGE).is_file()
    angaben = knotenweg.anlage_des_auftrags(ordner)
    assert angaben["name"] == SKIZZE and angaben["ueber"] == UEBER
    # STANDPUNKT VOM BILD UNTER DER SKIZZE (Entscheid 96b), nicht «mappe».
    assert angaben["standpunkt"] == {"kamera": "sSW"}
    mit = zettel["skizze_mitgereist"]
    assert mit["standpunkt"] == "Standpunkt vom Bild unter der Skizze (sSW)"
    assert mit["unterlage_von"] == "mitgeschickt"
    # Kein Mappenpfad am Auftrag, keiner im Laufzettel (Regel 3); nichts davon abrufbar.
    assert knotenweg.mappe_des_auftrags(ordner) is None
    assert str(tmp_path) not in json.dumps({k: v for k, v in zettel.items() if k != "scene"})
    with pytest.raises(knotenweg.KnotenwegError):
        knotenweg.artefakt(tmp_path / "ablage", KENNUNG, knotenweg.ORDNER_SKIZZE_AM_MAC)


def test_ohne_anlage_bleibt_der_satz_nur_am_mac(tmp_path, glb):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, None)
    assert "liegt nur am Mac" in str(fehler.value)
    assert "reist beim Bestellen noch nicht mit" not in str(fehler.value)


def test_ohne_mappe_am_mac_zaehlt_eine_anlage_nicht(tmp_path, glb):
    """Nur eine Mappe am Mac schickt mit; sonst gilt der Weg wie bisher (Mappe am Heim-PC)."""
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path), am_mac=None)
    assert "nur aus einer offenen Mappe" in str(fehler.value)


def test_die_unterlage_kommt_vom_heim_pc_wenn_sie_nicht_mitkam(tmp_path, glb):
    """Der Heim-PC hat das Grundbild gerechnet — es liegt in seinem Auftrag."""
    grund = tmp_path / "ablage" / GRUNDBILD_AUFTRAG
    grund.mkdir(parents=True)
    (grund / "job.json").write_text("{}", encoding="utf-8")
    (grund / "sSW__schoenbild.png").write_bytes(_unterlage(tmp_path))
    zettel = _lege_an(tmp_path, glb, _anlage(tmp_path, unterlage=None))
    assert zettel["skizze_mitgereist"]["unterlage_von"] == "heim-pc"
    assert (tmp_path / "ablage" / KENNUNG / knotenweg.ORDNER_SKIZZE_AM_MAC
            / knotenweg.DATEI_ANLAGE_UNTERLAGE).read_bytes() == _unterlage(tmp_path)


def test_fehlt_die_unterlage_ueberall_wird_mit_satz_abgewiesen(tmp_path, glb):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, unterlage=None))
    assert "kam nicht mit und liegt auf dem Heim-PC nicht" in str(fehler.value)
    assert not (tmp_path / "ablage" / KENNUNG).exists()


@pytest.mark.parametrize("name", ["../skizze.png", "/etc/skizze.png", "ipad/../../x.png",
                                  "C:/skizze.png", "ipad\\skizze.png"])
def test_ein_name_der_die_mappe_verlaesst_wird_abgewiesen(tmp_path, glb, name):
    """A1: relativer Name, kein ``..`` — für die Skizze UND ihre Unterlage."""
    with pytest.raises(knotenweg.KnotenwegError):
        _lege_an(tmp_path, glb, _anlage(tmp_path), szene=_szene(name=name))
    with pytest.raises(knotenweg.KnotenwegError):
        _lege_an(tmp_path, glb, _anlage(tmp_path, ueber=name if name.endswith(".png")
                                        else name + ".png"))
    assert not (tmp_path / "ablage" / KENNUNG).exists()


def test_kein_png_und_zu_gross_werden_abgewiesen(tmp_path, glb):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, png=b"GIF89a" + b"\0" * 64))
    assert "kein PNG" in str(fehler.value)
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, unterlage=b"nicht png" * 10))
    assert "kein PNG" in str(fehler.value)
    gross = _png(tmp_path, "gross.png") + b"\0" * (knotenweg.SKIZZE_ANLAGE_HOECHSTENS + 1)
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, png=gross))
    assert fehler.value.code == 413
    riese = bytearray(_png(tmp_path, "r.png"))
    riese[16:24] = (99999).to_bytes(4, "big") + (4).to_bytes(4, "big")
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, png=bytes(riese)))
    assert "Bildpunkte" in str(fehler.value)


def test_ohne_anweisung_bemerkung_und_prompt_wird_abgewiesen(tmp_path, glb):
    szene = _szene(name=SKIZZE)
    szene["style"]["prompt"] = ""
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, _anlage(tmp_path, bemerkung="gewünschter Name: Variante A"),
                 szene=szene)
    assert str(fehler.value) == knotenweg.SATZ_SKIZZE_OHNE_ANWEISUNG


@pytest.mark.parametrize("ueber,erwartet", [
    (UEBER, {"kamera": "sSW"}),
    (f"bilder/{GRUNDBILD_AUFTRAG}/nNO__schoenbild.png", {"kamera": "nNE"}),
    (f"bilder/{GRUNDBILD_AUFTRAG}/ansicht-1__schoenbild.png", None),
    ("heim/bild-1.png", None),
    (None, None),
])
def test_standpunkt_der_unterlage(ueber, erwartet):
    assert knotenweg.standpunkt_der_unterlage(ueber) == erwartet


# ============================================================ 2 · Rechnen

def test_der_heim_pc_rechnet_die_mitgereiste_skizze_vom_standpunkt_ssw(tmp_path, glb):
    zettel = _lege_an(tmp_path, glb, _anlage(tmp_path))
    knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    ordner = tmp_path / "ablage" / KENNUNG
    modell = _Modell()
    antwort = abholer.hole_einen(
        ordner, verarbeite=abholer.verarbeiter(_skizzen_ausfuehrer=_tabelle(modell)),
        darf_rechnen=lambda: (True, "frei"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    # Die Skizze AUF IHRER UNTERLAGE ging ins Modell — blau mit dem roten Strich.
    (farben, breite, hoehe) = modell.eingaenge[-1]
    assert (breite, hoehe) == (4, 4) and farben[1 * 4 + 1] == ROT and farben[0] == BLAU
    assert modell.auftraege[-1]["prompt"] == "a canopy"  # die Bemerkung, übersetzt (Ergebnis 352 S3)
    ergebnis = _ergebnis(ordner)
    skizze = ergebnis["qa"]["verdict"]
    assert len(ergebnis["images"]) == 1
    befund = abholer.lies_befund(ordner)
    assert befund["skizze"]["standpunkt_von"] == "bild"
    assert "vom Bild unter der Skizze (sSW)" in befund["skizze"]["standpunkt"]
    assert befund["skizze"]["anweisung_aus"] == "bemerkung"
    assert skizze["passed"] is False  # «nicht anwendbar», wie jede Skizze
    # Gerechnet in der Mappe IM AUFTRAG, die Skizze dort «gerechnet».
    gebaut = ordner / knotenweg.ORDNER_SKIZZENMAPPE
    p = projekt.oeffne(gebaut)["projekt"]
    assert [e for e in p["skizzen"] if e["skizze"] == SKIZZE][-1]["stand"] == \
        projekt.SKIZZE_GERECHNET
    assert projekt.standpunkt_des_bildes(p, UEBER) == {"kamera": "sSW"}
    assert str(tmp_path) not in json.dumps(befund)


def test_mappe_aus_anlage_bleibt_in_der_mappe(tmp_path, glb):
    """A1 auf der Bildseite: Auch eine von Hand veränderte Anlage verlässt die Mappe nicht."""
    _lege_an(tmp_path, glb, _anlage(tmp_path))
    ordner = tmp_path / "ablage" / KENNUNG
    datei = ordner / knotenweg.ORDNER_SKIZZE_AM_MAC / knotenweg.DATEI_ANLAGE
    angaben = json.loads(datei.read_text(encoding="utf-8"))
    datei.write_text(json.dumps(dict(angaben, name="../../aussen.png")), encoding="utf-8")
    with pytest.raises(knotenweg.KnotenwegError):
        knotenweg.mappe_aus_anlage(ordner)
    assert not (tmp_path / "ablage" / "aussen.png").exists()


# ============================================================ 3 · Über den Server

def test_ueber_den_server_wie_die_mac_app_bestellt(flaeche):  # noqa: F811
    _, anschluss, tmp = flaeche
    szene = json.dumps(_szene(name=SKIZZE)).encode()
    rumpf, typ = _formular({
        "scene": (None, szene),
        "model": ("m.glb", b"glTF" + b"\0" * 64),
        knotenweg.FELD_SKIZZE_PNG: ("skizze.png", _png(tmp, "s.png", {(1, 1): (*ROT, 255)})),
        knotenweg.FELD_UNTERLAGE_PNG: ("unterlage.png", _unterlage(tmp)),
        knotenweg.FELD_SKIZZE_INFO: (None, json.dumps({"ueber": UEBER,
                                                       "bemerkung": "ein Vordach"}).encode()),
    })
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("POST", "/bruecke/jobs", body=rumpf,
                    headers={"Content-Type": typ, "X-Mappe-Am-Mac": "haus-am-hang",
                             "X-Mappe-Heim": "Hof"})
    antwort = leitung.getresponse()
    zettel = json.loads(antwort.read())
    assert antwort.status == 200, zettel
    assert zettel["mappe"] == "haus-am-hang"
    assert zettel["skizze_mitgereist"]["standpunkt"].endswith("(sSW)")
    ordner = tmp / "ablage" / zettel["job_id"]
    assert knotenweg.anlage_des_auftrags(ordner)["name"] == SKIZZE


def test_der_server_reicht_die_anlage_nur_mit_mappe_am_mac():
    quelle = (WURZEL / "oberflaeche" / "server.py").read_text(encoding="utf-8")
    assert "anlage = knotenweg.lies_skizzen_anlage(felder)" in quelle
    assert "skizze_anlage=anlage if am_mac else None" in quelle


# ============================================================ 4 · Mac-App (Swift, gebaut in der iPad-Prüfstrecke)

def test_die_mac_app_nennt_den_standpunkt_vom_bild_wie_der_heim_pc():
    """Bis 0.3.66 stand in ``Mappenkern.knotenAntwort`` fest «mappe» (Demobefund 25.10.2026)."""
    from aiimaging import kameras
    import re
    quelle = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Macmappe.swift").read_text(
        encoding="utf-8")
    assert '"standpunkt": .text(standpunktDerSkizze(ueber: s.ueber))' in quelle
    assert '"standpunkt": .text("mappe")' not in quelle
    liste = re.search(r"static let richtungen: Set<String> = \[([^\]]*)\]", quelle).group(1)
    assert set(re.findall(r'"([^"]+)"', liste)) == (set(kameras.RICHTUNGEN)
                                                     | set(kameras.GLEICHWORTE_DEUTSCH))
    proben = (WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests"
              / "MacmappeTests.swift").read_text(encoding="utf-8")
    assert "testStandpunktVomBildUnterDerSkizze" in proben
