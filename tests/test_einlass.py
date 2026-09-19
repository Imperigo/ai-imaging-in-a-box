"""Der Einlass — **die Tür, an der eine Architektin zuerst steht.**

Diese Sammlung prüft nicht, ob eine Datei gelesen wird. Sie prüft, ob ein Mensch nach dem
Fehlschlag **weiss, was zu tun ist.** Das ist der Unterschied, um den es in diesem Modul
geht: Bis zum 19.09.2026 endete jede falsche Datei — beschädigte IFC, umbenannte JPG,
SketchUp-Datei — in demselben ``KeyError`` aus einer fremden Bibliothek.

Die Zielgruppe sind Architektinnen und Studierende. *Ein Stacktrace ist für sie keine
Antwort, sondern das Ende des Versuchs.*
"""
from __future__ import annotations

import json
import struct

import pytest

from aiimaging import einlass, herkunft


def _glb(generator: str = "Blender 4.2", *, abgeschnitten: bool = False) -> bytes:
    """Eine gültige minimale glb — Kennung, Fassung, Länge, JSON-Block.

    Von Hand gebaut und nicht aus einer Datei geladen: Regel 3 verlangt synthetische
    Testdaten, die im Repo erzeugbar sind, und ein echtes Modell im Repo wäre genau das,
    was die Regel verbietet.
    """
    js = json.dumps({"asset": {"version": "2.0", "generator": generator}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    roh = struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block
    return roh[:20] if abgeschnitten else roh


@pytest.fixture
def ifc(tmp_path):
    """Eine kleine, gültige IFC — nur der Kopf, mehr sieht der Einlass nicht an."""
    pfad = tmp_path / "haus.ifc"
    pfad.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION((''),'');\n"
        "FILE_NAME('haus.ifc','2026-09-19T00:00:00',(''),(''),'','Testfixture','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\n"
        "ENDSEC;\nEND-ISO-10303-21;\n", encoding="utf-8")
    return pfad


# ───────────────────────────────── Die Fälle, die vorher abstürzten ──────────────────

def test_eine_datei_die_es_nicht_gibt_ist_ein_befund_und_keine_ausnahme(tmp_path):
    """Der haeufigste Fall ueberhaupt — ein Tippfehler im Pfad — verdient einen Satz.

    Eine Ausnahme waere hier technisch richtig und praktisch nutzlos: Sie zwingt jeden
    Aufrufer zu einem `try`, und wer keines schreibt, bekommt einen Traceback statt einer
    Auskunft.
    """
    befund = einlass.sichte(tmp_path / "gibtsnicht.ifc")

    assert befund["brauchbar"] is False
    assert "keine Datei" in befund["grund"]
    assert "Tippfehler" in befund["naechster_schritt"]


def test_eine_leere_datei_sagt_dass_sie_leer_ist(tmp_path):
    """Null Byte ist ein Befund ueber die Datei, kein Raetsel."""
    (pfad := tmp_path / "leer.ifc").write_bytes(b"")
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is False
    assert befund["groesse_byte"] == 0, "die gemessene Null gehoert in den Befund"
    assert "leer" in befund["grund"]


def test_eine_umbenannte_jpg_wird_als_bild_erkannt_und_nicht_als_kaputte_ifc(tmp_path):
    """BEFUND 19.09.2026: Genau dieser Fall endete in einem `KeyError` aus ifcopenshell.

    Gemessen war: Eine JPG mit der Endung `.ifc` lief durch `seams.ifc_zu_glb` und
    lieferte

        Exception ignored in: <function file.__del__ …>
        KeyError: 404872384

    Der Einlass sieht den Dateianfang an und nennt das Ding beim Namen. **Die Endung wird
    dabei nicht gefragt** — sie ist eine Behauptung des Benennenden, der Dateianfang eine
    des Erzeugers.
    """
    (pfad := tmp_path / "haus.ifc").write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100)
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is False
    assert "JPEG" in befund["format"]
    assert "Bild" in befund["naechster_schritt"]
    assert "KeyError" not in befund["grund"], "kein fremder Stacktrace mehr"


@pytest.mark.parametrize("kennung,erwartet_im_namen,erwartet_im_rat", [
    (b"SketchUp Model\x00", "SketchUp", "IFC"),
    (b"3D Geometry File Format 3.0", "Rhino", "glTF"),
    (b"AC1027\x00\x00", "AutoCAD", "IFC"),
    (b"Kaydara FBX Binary  \x00", "FBX", "glTF"),
    (b"BLENDER-v302", "Blender", "glTF"),
])
def test_fremde_architekturformate_werden_beim_namen_genannt(
        tmp_path, kennung, erwartet_im_namen, erwartet_im_rat):
    """*Wer «SketchUp kann ich nicht» liest, weiss in einer Sekunde, woran er ist.*

    Vorher liefen alle diese Formate als kaputte IFC ins Leere. Der Rat daneben ist kein
    Beiwerk: **Eine Absage ohne Ausweg ist eine halbe Auskunft** — und der Ausweg ist
    hier immer derselbe, naemlich ein Export, den das Ausgangsprogramm schon kann.
    """
    (pfad := tmp_path / "modell.bin").write_bytes(kennung + b"\x00" * 64)
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is False
    assert erwartet_im_namen in befund["format"]
    assert erwartet_im_rat in befund["naechster_schritt"], \
        "die Absage muss sagen, wie man weiterkommt"


def test_ein_unbekanntes_format_ist_NICHT_ENTSCHEIDBAR_und_nicht_unbrauchbar(tmp_path):
    """Die dritte Antwort, angewandt auf den Einlass — und sie ist hier keine Feinheit.

    Was wir nicht erkennen, ist eine Aussage ueber **unsere Kennungen**, nicht ueber die
    Datei. Sie als unbrauchbar zu melden hiesse, aus einem Nichtwissen einen Vorwurf zu
    machen.
    """
    (pfad := tmp_path / "raetsel.ifc").write_bytes(b"irgendetwas voellig anderes" * 4)
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is None, "weder ja noch nein"
    assert befund["format"] is None
    assert "nicht erkennen" in befund["grund"]


def test_eine_abgeschnittene_gltf_ist_ein_befund_ueber_die_datei(tmp_path):
    """Das Format stimmt, der Kopf ist kaputt — das ist ein Urteil ueber die Datei.

    Darum `False` und nicht `None`: Wir haben genug gesehen, um zu wissen, dass es nicht
    geht.
    """
    (pfad := tmp_path / "halb.glb").write_bytes(_glb(abgeschnitten=True))
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is False
    assert befund["format"] == "glTF", "die Familie steht fest, die enge Angabe nicht"
    assert "abgebrochen" in befund["naechster_schritt"] \
        or "unvollstaendig" in befund["naechster_schritt"] \
        or "unvollständig" in befund["naechster_schritt"]


# ───────────────────────────────── Was durchgehen muss ───────────────────────────────

def test_eine_gueltige_ifc_geht_durch_und_sagt_was_drinsteht(ifc):
    """Die Gegenprobe. *Ein Waechter, der alles abweist, bewacht nichts.*"""
    befund = einlass.sichte(ifc)

    assert befund["brauchbar"] is True
    assert befund["format"] == "IFC"
    assert "IFC4" in befund["grund"]
    assert "METRE" in befund["grund"], "die Einheit gehoert in den Satz"
    assert befund["naechster_schritt"] == "Der Lauf kann beginnen."


def test_eine_gueltige_glb_geht_durch(tmp_path):
    """Dieselbe Gegenprobe fuer das zweite Format, das wir wirklich koennen."""
    (pfad := tmp_path / "modell.glb").write_bytes(_glb())
    befund = einlass.sichte(pfad)

    assert befund["brauchbar"] is True
    assert "Blender" in befund["grund"]


def test_die_endung_entscheidet_nicht_aber_sie_wird_gemeldet(ifc, tmp_path):
    """Eine umbenannte, INHALTLICH RICHTIGE Datei ist brauchbar — und einen Hinweis wert.

    Der Hinweis verhindert nichts. Er steht da, weil andere Werkzeuge der Endung glauben
    und es dort dann auffaellt, wo niemand mehr weiss, woher es kommt.
    """
    (falsch := tmp_path / "modell.glb").write_bytes(ifc.read_bytes())
    befund = einlass.sichte(falsch)

    assert befund["brauchbar"] is True, "der Inhalt stimmt, also geht es"
    assert befund["endung_passt"] is False
    assert any(".glb" in h and "IFC" in h for h in befund["hinweise"])


def test_ohne_endung_ist_endung_passt_NICHT_falsch_sondern_None(ifc, tmp_path):
    """`None` heisst NICHT GEMESSEN. Eine Datei ohne Endung hat keine falsche Endung.

    Ohne diese Probe waere `False` der bequeme Rueckfall — und `False` ist hier eine
    Behauptung ueber etwas, das gar nicht dasteht.
    """
    (ohne := tmp_path / "modell").write_bytes(ifc.read_bytes())

    assert einlass.sichte(ohne)["endung_passt"] is None


# ───────────────────────────────── Die Hochachse ─────────────────────────────────────

def test_bei_einer_ifc_steht_die_hochachse_fest(ifc):
    """IFC ist nach ISO 16739 Z-up. Das folgt aus dem **Format**, nicht aus dem Erzeuger."""
    befund = einlass.sichte(ifc)

    assert befund["hochachse_steht_fest"] is True
    assert befund["hochachse"] == "Z_UP"


def test_bei_einer_glb_steht_sie_NICHT_fest_und_der_hinweis_sagt_was_das_kostet(tmp_path):
    """glTF 2.0 kennt kein Up-Achsen-Feld — und das ist die teuerste Stelle der Kette.

    Wird die Achse falsch angegeben, liegt das Gebaeude auf der Seite. Tiefenkarte,
    Kamera und Geometrie-QA sind dann **gemeinsam** verdreht und darum in sich stimmig:
    *Der Fehlschlag sieht wie ein Erfolg aus.* Der Hinweis muss das sagen, nicht bloss
    «Achse unbekannt».
    """
    (pfad := tmp_path / "modell.glb").write_bytes(_glb())
    befund = einlass.sichte(pfad)

    assert befund["hochachse_steht_fest"] is False
    assert befund["hochachse"] is None, "keine geratene Achse im Befund"
    assert "angegeben" in befund["naechster_schritt"]
    assert any("auf der Seite" in h for h in befund["hinweise"]), \
        "der Hinweis muss die Folge nennen, nicht nur die Luecke"


# ───────────────────────────────── Die Gestalt des Befunds ───────────────────────────

@pytest.mark.parametrize("bauen", [
    lambda p: None,                                            # existiert nicht
    lambda p: p.write_bytes(b""),                              # leer
    lambda p: p.write_bytes(b"\x89PNG\r\n\x1a\n"),             # fremdes Format
    lambda p: p.write_bytes(b"voellig unbekannt" * 8),         # unerkannt
    lambda p: p.write_bytes(_glb()),                           # gueltig
])
def test_jeder_befund_hat_dieselbe_gestalt(tmp_path, bauen):
    """Ein Aufrufer darf nicht wissen muessen, welchen Weg die Pruefung genommen hat.

    Ein fehlender Schluessel waere ein `KeyError` mitten in einer Fehlerbehandlung — also
    genau dort, wo am wenigsten jemand damit rechnet.
    """
    pfad = tmp_path / "modell.dat"
    bauen(pfad)
    befund = einlass.sichte(pfad)

    for feld in ("brauchbar", "grund", "format", "endung_passt", "groesse_byte",
                 "hochachse", "hochachse_steht_fest", "kopf", "hinweise",
                 "naechster_schritt"):
        assert feld in befund, f"{feld!r} fehlt — der Befund hat zwei Gestalten"
    assert isinstance(befund["hinweise"], list)
    assert isinstance(befund["grund"], str) and befund["grund"].strip()
    assert isinstance(befund["naechster_schritt"], str) and befund["naechster_schritt"].strip()


def test_brauchbar_ist_dreiwertig_und_nie_etwas_anderes(tmp_path):
    """`True`, `False`, `None` — und nichts sonst. Kein `0`, kein `""`, kein `"ja"`."""
    faelle = [b"", b"\x89PNG\r\n\x1a\n", b"unbekannt" * 8, _glb()]
    pfad = tmp_path / "m.glb"
    for inhalt in faelle:
        pfad.write_bytes(inhalt)
        assert einlass.sichte(pfad)["brauchbar"] in (True, False, None)


def test_ein_ordner_ist_keine_datei(tmp_path):
    """Ohne diese Probe liefe der Sichtgang in einen `IsADirectoryError` beim Lesen."""
    (ordner := tmp_path / "modelle").mkdir()
    befund = einlass.sichte(ordner)

    assert befund["brauchbar"] is False
    assert "Ordner" in befund["grund"]


# ───────────────────────────────── Die Regeln des Projekts ───────────────────────────

def test_der_sichtgang_startet_keinen_prozess(ifc, monkeypatch):
    """**Regel 4 und der ganze Zweck dieses Moduls:** Ein Sichtgang, der eine halbe Stunde
    dauert, ist kein Sichtgang.

    Kein Subprozess heisst: kein Blender, kein `.venv-ifc`, keine GPU, kein Netz. Bei
    einer 500-MB-IFC dasselbe wie bei einer 5-KB-IFC.
    """
    import subprocess

    def verweigern(*a, **k):
        raise AssertionError("Der Einlass hat einen Prozess gestartet — das darf er nicht.")

    monkeypatch.setattr(subprocess, "run", verweigern)
    monkeypatch.setattr(subprocess, "Popen", verweigern)
    monkeypatch.setattr(subprocess, "check_output", verweigern)

    assert einlass.sichte(ifc)["brauchbar"] is True


def test_eine_unlesbare_datei_wirft_denn_das_ist_ein_fehler_des_werkzeugs(tmp_path, monkeypatch):
    """Der Unterschied, der die ganze Sorgfalt dieses Moduls ausmacht.

    Eine **unbrauchbare** Datei ist ein Befund und kommt zurueck. Ein **nicht
    stattgefundener** Sichtgang ist ein Fehler des Werkzeugs und fliegt. Wer beides
    zusammenwirft, kann spaeter nicht mehr unterscheiden, ob die Datei schlecht war oder
    die Pruefung.
    """
    (pfad := tmp_path / "gesperrt.ifc").write_bytes(b"ISO-10303-21;\n" + b"x" * 100)

    def sperren(*a, **k):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("pathlib.Path.open", sperren)

    with pytest.raises(einlass.EinlassError, match="nicht lesen"):
        einlass.sichte(pfad)


def test_die_meldungen_sind_deutsch_und_ohne_eszett():
    """Schweizer Schreibung, und keine englische Fehlermeldung im Durchgereichten."""
    from pathlib import Path as _P

    quelle = (_P(einlass.__file__)).read_text(encoding="utf-8")
    assert "ß" not in quelle, "Schweizer Schreibung: 'ss', nie das Eszett"


def test_die_fremden_kennungen_koennen_unsere_eigenen_formate_nicht_abweisen(tmp_path, ifc):
    """Der Schadensdeckel fuer eine falsche Kennung — und er ist der Grund, warum die
    Liste ueberhaupt GESETZT sein darf.

    Die Kennungen in `FREMDE_FORMATE` stammen aus veroeffentlichten Formatbeschreibungen
    und sind **nicht** an echten Dateien dieses Projekts gemessen. Waere eine davon
    falsch, duerfte sie hoechstens einen falschen Namen in eine Absage schreiben — sie
    darf **kein brauchbares Modell abweisen.**

    Geprueft wird das an der Sache und nicht an der Annahme: Jede unserer beiden
    Formatgestalten geht durch, gleichgueltig was in der Liste steht.
    """
    assert einlass.sichte(ifc)["brauchbar"] is True

    (glb := tmp_path / "m.glb").write_bytes(_glb())
    assert einlass.sichte(glb)["brauchbar"] is True

    for kennung, versatz, name, _rat in einlass.FREMDE_FORMATE:
        assert not ifc.read_bytes()[versatz:versatz + len(kennung)] == kennung, \
            f"die Kennung {name!r} trifft auf eine gueltige IFC — sie wuerde sie abweisen"
        assert not _glb()[versatz:versatz + len(kennung)] == kennung, \
            f"die Kennung {name!r} trifft auf eine gueltige glb"


def test_jedes_fremde_format_nennt_einen_ausweg():
    """*Eine Absage ohne Ausweg ist eine halbe Auskunft.*

    Diese Probe haelt die Regel fuer jeden kuenftigen Eintrag fest — sonst waere sie eine
    Gewohnheit, und Gewohnheiten enden beim ersten Eintrag unter Zeitdruck.
    """
    for kennung, _versatz, name, rat in einlass.FREMDE_FORMATE:
        assert rat and rat.strip(), f"{name!r} sagt nicht, wie man weiterkommt"
        assert len(rat) > 30, f"der Rat zu {name!r} ist zu kurz, um zu helfen: {rat!r}"
