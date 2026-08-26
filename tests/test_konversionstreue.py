"""«Durchgelaufen» ist kein Qualitätsmerkmal — die Lücke, die beide Leser teilen.

**Der Anlass** (HomeStation, `BEFUND_2026-08-24_IFC-LESER.md`, 24.08.2026): Neun echte IFC
durch zwei Leser, 9 von 9 `ok`, null Geometriefehler. Und dazu der Satz, der die ganze
Messung einordnet: *«Belegt ist bisher nur, dass die Konversion durchläuft. Nicht, ob die
Geometrie stimmt.»*

Dieselbe Verwechslung stand am Anfang der Geometrie-QA: Ein Score über das ganze Bild lief
ebenfalls durch und beantwortete nicht, ob im Bild ein Bauwerk steht.

**Warum synthetisch und nicht an echten Dateien.** Bei einer echten IFC kennt niemand die
Wahrheit — man müsste sie mit demselben Werkzeug ausrechnen, das man prüfen will. Bei
`tools/make_test_ifc.py` kennen wir jede Kante, weil wir sie geschrieben haben. Regel 3
ist damit nicht bloss eingehalten, sondern die Voraussetzung.
"""
from __future__ import annotations

import pathlib

import pytest

from aiimaging import konversionstreue as kt
from aiimaging.konversionstreue import KonversionsError, TOLERANZ_M

# Das synthetische Testbauwerk: 8,0 × 5,0 m, Wandhöhe 3,0 m auf 0,25 m Bodenplatte.
BAU = (8.0, 5.0, 3.25)


def _bericht(spanne, **rest) -> dict:
    return {"status": "ok", "bbox": [[0.0, 0.0, 0.0], list(spanne)], **rest}


# --------------------------------------------------------------------------------------
# 1 · Die richtige Umwandlung besteht — und eine falsche nicht
# --------------------------------------------------------------------------------------

def test_die_richtige_umwandlung_besteht():
    e = kt.pruefe_konversion(_bericht(BAU, n_elements=5, n_triangles=60),
                             huellbox_m=BAU, n_bauteile=5, n_dreiecke=60)

    assert e["stimmt"] is True
    assert e["abweichungen"] == []
    assert e["diagnose"] is None


def test_eine_falsche_zahl_reicht():
    """Gegenprobe zum Test darüber — sonst hiesse er nur, dass alles besteht."""
    e = kt.pruefe_konversion(_bericht(BAU, n_elements=4), huellbox_m=BAU, n_bauteile=5)

    assert e["stimmt"] is False
    assert [a["achse"] for a in e["abweichungen"]] == ["Bauteile"]


def test_die_toleranz_ist_eng_und_deckt_nur_rundung():
    """Ein Quader aus einer IFC-Extrusion wird nicht angenähert — seine Ecken stehen da.

    Was ankommen darf, sind Gleitkommareste. Wer diese Zahl lockern muss, hat einen
    Befund und keine Toleranzfrage.
    """
    knapp = (BAU[0] + TOLERANZ_M / 2, BAU[1], BAU[2])
    zuviel = (BAU[0] + TOLERANZ_M * 10, BAU[1], BAU[2])

    assert kt.pruefe_konversion(_bericht(knapp), huellbox_m=BAU)["stimmt"] is True
    assert kt.pruefe_konversion(_bericht(zuviel), huellbox_m=BAU)["stimmt"] is False
    assert TOLERANZ_M < 1e-3, "ein Millimeter waere fuer exakte Quader schon viel"


# --------------------------------------------------------------------------------------
# 2 · Die Diagnose — der eigentliche Ertrag
# --------------------------------------------------------------------------------------
#
# Eine Liste von Abweichungen sagt DASS etwas nicht stimmt. Die beiden haeufigsten
# IFC-Fehler haben einen Namen, und wer den Namen liest, weiss, wo er nachsehen muss.

def test_millimeter_als_meter_wird_beim_namen_genannt():
    """**Der häufigste Fehler beim IFC-Lesen, und `make_test_ifc.py` schreibt ihn eigens.**

    `IfcSIUnit` trägt den Vorsatz `MILLI`; wer `IfcUnitAssignment` überspringt, bekommt
    ein Haus von acht Kilometern Länge. In einer reinen Zahlenabweichung sieht das aus wie
    irgendein Fehler — mit Namen ist es eine Adresse.
    """
    e = kt.pruefe_konversion(_bericht([w * 1000.0 for w in BAU]), huellbox_m=BAU)

    assert e["stimmt"] is False
    assert "MASSSTAB" in e["diagnose"]
    assert "Millimeter" in e["diagnose"]


@pytest.mark.parametrize("faktor,wort", [(100.0, "Zentimeter"), (10.0, "Dezimeter"),
                                         (0.3048, "Fuss"), (0.001, "Millimeter")])
def test_die_uebrigen_einheitenfehler_ebenfalls(faktor, wort):
    e = kt.pruefe_konversion(_bericht([w * faktor for w in BAU]), huellbox_m=BAU)

    assert wort in e["diagnose"]


def test_ein_unbekannter_faktor_wird_NICHT_geraten():
    """**Eine Diagnose zu raten wäre schlimmer als keine.**

    Der Faktor stimmt über alle drei Achsen — das ist ein Massstabsfehler. Welcher, sagt
    dieses Modul nicht, weil es 7,3 nicht kennt.
    """
    e = kt.pruefe_konversion(_bericht([w * 7.3 for w in BAU]), huellbox_m=BAU)

    assert "MASSSTAB" in e["diagnose"]
    assert "NICHT geraten" in e["diagnose"]
    assert not any(wort in e["diagnose"]
                   for wort in ("Millimeter", "Zentimeter", "Fuss"))


def test_vertauschte_achsen_sind_kein_groessenfehler():
    """Das Bauwerk ist nicht falsch **gross**, sondern falsch **gedreht**.

    Dieselben drei Kantenlängen in anderer Reihenfolge — der übersehene
    Z-oben/Y-oben-Wechsel. Wer das als «zwei Achsen daneben» liest, sucht am falschen Ort.
    """
    e = kt.pruefe_konversion(_bericht((BAU[0], BAU[2], BAU[1])), huellbox_m=BAU)

    assert "ACHSEN VERTAUSCHT" in e["diagnose"]
    assert "gedreht" in e["diagnose"]


def test_eine_wirklich_andere_geometrie_wird_auch_so_genannt():
    """Weder Einheiten noch Drehung — und dann sagt es das, statt eine Ursache zu erfinden."""
    e = kt.pruefe_konversion(_bericht((BAU[0], BAU[1], 9.9)), huellbox_m=BAU)

    assert "weder ein Einheiten- noch ein Drehfehler" in e["diagnose"]


# --------------------------------------------------------------------------------------
# 3 · Nicht geprüft ist nicht falsch
# --------------------------------------------------------------------------------------

def test_eine_fehlgeschlagene_umwandlung_ist_NICHT_GEPRUEFT():
    """**Der Unterschied schickt jemanden auf eine andere Suche.**

    «Falsch umgewandelt» heisst: die Geometrie ansehen. «Nicht gelaufen» heisst: den
    Fehler des Runners ansehen. Beides `False` zu melden verwechselt die beiden.
    """
    e = kt.pruefe_konversion({"status": "error", "error": "keine Geometrie im IFC"},
                             huellbox_m=BAU)

    assert e["stimmt"] is None
    assert e["gemessen"] is False
    assert any("NICHT GEPRUEFT" in w for w in e["warnungen"])


def test_ein_bericht_ohne_huellbox_ebenso():
    e = kt.pruefe_konversion({"status": "ok", "bbox": None}, huellbox_m=BAU)

    assert e["stimmt"] is None
    assert any("nichts zu vergleichen" in w for w in e["warnungen"])


def test_eine_fehlende_anzahl_wird_gemeldet_und_nicht_uebergangen():
    e = kt.pruefe_konversion(_bericht(BAU), huellbox_m=BAU, n_bauteile=5)

    assert any("NICHT GEPRUEFT" in w for w in e["warnungen"])
    assert e["stimmt"] is True, "die Huellbox stimmt — die Anzahl ist ungeprueft, nicht falsch"


def test_ohne_erwartete_anzahlen_wird_nur_die_huellbox_geprueft():
    e = kt.pruefe_konversion(_bericht(BAU, n_elements=99), huellbox_m=BAU)

    assert e["stimmt"] is True
    assert e["warnungen"] == []


# --------------------------------------------------------------------------------------
# 4 · Unsinnige Eingaben
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("bbox", [None, [[0, 0, 0]], [[0, 0], [1, 1]], "acht",
                                  [[0, 0, 0], ["a", "b", "c"]]])
def test_eine_unlesbare_huellbox_wird_abgewiesen(bbox):
    with pytest.raises(KonversionsError):
        kt.spanne_aus_bbox(bbox)


def test_eine_unvollstaendige_erwartung_wird_abgewiesen():
    with pytest.raises(KonversionsError, match="drei Kantenlängen"):
        kt.pruefe_konversion(_bericht(BAU), huellbox_m=(8.0, 5.0))


def test_eine_negative_toleranz_wird_abgewiesen():
    with pytest.raises(KonversionsError, match="negativ"):
        kt.pruefe_konversion(_bericht(BAU), huellbox_m=BAU, toleranz_m=-1.0)


def test_das_modul_zieht_keinen_runner_mit():
    """Regel 2 in ausführbarer Form: Es liest ein Wörterbuch, mehr nicht.

    Ein Prüfmodul, das den Runner importierte, um an dessen Konstanten zu kommen, wäre der
    Anfang genau des Weges, den `tests/test_prozessgrenze.py` verbietet — und dieser Fehler
    ist mir am selben Tag schon einmal unterlaufen.
    """
    import ast

    baum = ast.parse(pathlib.Path(kt.__file__).read_text(encoding="utf-8"))
    namen = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            namen.update(a.name for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            namen.add(knoten.module or "")

    assert not [n for n in namen if "runner" in n or "ifcopenshell" in n or "bpy" in n], (
        f"dieses Modul importiert {sorted(namen)} — davon gehoert nichts hierher")
    assert namen <= {"__future__", "collections.abc"}, (
        f"unerwartete Abhaengigkeit: {sorted(namen - {'__future__', 'collections.abc'})}")


# ======================================================================================
# Über die WIRKLICHE Kette — die vier Posten aus `auf-20260824-39`, hier gerechnet
# ======================================================================================
#
# Der Auftrag ging am 24.08.2026 an die HomeStation. Am 26.08. fiel auf, dass er dort nie
# hingehoert haette: Alle vier Posten brauchen nur synthetische Geometrie und den
# IFC-Runner — keine GPU und keine echten Dateien. `.venv-ifc` liegt in diesem Container.
#
# Was oben in dieser Datei steht, prueft die Funktion an Woerterbuechern. Was hier steht,
# faehrt sie ueber eine wirklich erzeugte IFC. *Eine Attrappe, die den Fehler nicht kennt,
# kann ihn nicht finden* — der Satz hat an diesem Tag schon einmal Geld gekostet.

import copy
import importlib.util
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


def _generator():
    """Die Sollmasse **aus dem Generator gelesen**, nicht abgeschrieben.

    Der Auftrag verlangt es wörtlich: *«von dort lesen, nicht abschreiben»*. Eine Zahl,
    die an zwei Stellen steht, ist an einer davon bereits falsch.
    """
    spez = importlib.util.spec_from_file_location("mk", WURZEL / "tools" / "make_test_ifc.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _konvertiere(tmp_path, name, *schalter):
    from aiimaging.seams import ifc_zu_glb
    ifc = tmp_path / name
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc), *schalter],
                   check=True, capture_output=True, cwd=WURZEL)
    bericht = ifc_zu_glb(ifc, ifc.with_suffix(".glb"))
    assert bericht["status"] == "ok", bericht.get("error")
    return bericht


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_g1_der_gerade_fall_stimmt(tmp_path):
    """8,0 × 5,0 × 3,25 m — und zwar auf unter einen Mikrometer."""
    mk = _generator()
    soll = (mk.LAENGE_X, mk.BREITE_Y, mk.HOEHE_Z + mk.PLATTENDICKE)

    bericht = _konvertiere(tmp_path, "t.ifc")
    befund = kt.pruefe_konversion(bericht, huellbox_m=soll)

    assert befund["stimmt"] is True, befund
    assert befund["abweichungen"] == []
    assert bericht["n_elements"] == 5


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_g2_millimeter_ergeben_dieselben_meter(tmp_path):
    """**Der Test des Tests.** Dieselbe Geometrie in Millimetern, mit IfcSIUnit-Vorsatz.

    Bestätigt eine Annahme, die dieses Projekt schon einmal teuer korrigiert hat:
    *ArchiCAD über IFC4 braucht keine Einheitenumrechnung — IfcOpenShell rechnet selbst
    um.* Wer hier von Hand mal 1000 nähme, träfe genau daneben.
    """
    mk = _generator()
    soll = (mk.LAENGE_X, mk.BREITE_Y, mk.HOEHE_Z + mk.PLATTENDICKE)

    bericht = _konvertiere(tmp_path, "t_mm.ifc", "IFC4", "MILLI")
    befund = kt.pruefe_konversion(bericht, huellbox_m=soll)

    assert befund["stimmt"] is True, (
        f"Der Millimeterfall ergibt {befund['spanne']} statt {soll} — dann übergeht "
        f"jemand den IfcSIUnit-Vorsatz.")


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_g3_das_werkzeug_faengt_die_drei_faelschungen(tmp_path):
    """Die Gegenprobe am Werkzeug selbst. **Ein Prüfer, der nie anschlägt, prüft nichts.**"""
    mk = _generator()
    soll = (mk.LAENGE_X, mk.BREITE_Y, mk.HOEHE_Z + mk.PLATTENDICKE)
    echt = _konvertiere(tmp_path, "t.ifc")

    gross = copy.deepcopy(echt)
    gross["bbox"] = [[v * 1000 for v in gross["bbox"][0]],
                     [v * 1000 for v in gross["bbox"][1]]]
    a = kt.pruefe_konversion(gross, huellbox_m=soll)
    assert a["stimmt"] is False and "MASSSTAB" in (a["diagnose"] or "")
    assert "1000" in (a["diagnose"] or ""), "der Faktor gehört benannt"

    gedreht = copy.deepcopy(echt)
    for ecke in gedreht["bbox"]:
        ecke[1], ecke[2] = ecke[2], ecke[1]
    b = kt.pruefe_konversion(gedreht, huellbox_m=soll)
    assert b["stimmt"] is False and "ACHSEN" in (b["diagnose"] or "")

    weniger = copy.deepcopy(echt)
    weniger["n_elements"] -= 1
    c = kt.pruefe_konversion(weniger, huellbox_m=soll,
                                           n_bauteile=echt["n_elements"])
    assert c["stimmt"] is False, "ein fehlendes Bauteil ist eine Abweichung"


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_g4_raeume_aendern_die_huellbox_nicht(tmp_path):
    """Räume liegen **innerhalb** der Wände — und ein IfcSpace ist keine gebaute Substanz.

    Ein `IfcSpace` als Mesh ist ein massiver Quader. Käme er mit, wäre das Bauwerk innen
    voll und die Tiefenkarte falsch.
    """
    mk = _generator()
    soll = (mk.LAENGE_X, mk.BREITE_Y, mk.HOEHE_Z + mk.PLATTENDICKE)

    bericht = _konvertiere(tmp_path, "t_r.ifc", "--raeume")
    befund = kt.pruefe_konversion(bericht, huellbox_m=soll)

    assert befund["stimmt"] is True, befund
    assert bericht["uebersprungen"].get("IfcSpace") == 2, (
        f"Erwartet zwei übersprungene Räume, gemeldet {bericht.get('uebersprungen')}")
