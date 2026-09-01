"""Die Auswertung der Ersatzkalibrierung — ohne Blender.

Geprüft wird, was das Werkzeug **rechnet**: die Einteilung in frontal und diagonal, die
Dublettenprüfung und der Weg, auf dem der Vorbehalt in jede Kurve kommt. Der Renderteil
braucht Blender; seine Zahlen stehen in `docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`.

*Warum die Dublettenprüfung hier so viel Platz bekommt:* Sie hat am 01.09.2026 die vierte
Szene entlarvt — `raeume` lieferte in allen 44 Zeilen exakt die Zahlen von `quader`, weil
zwei `IfcSpace` im Wandinneren von aussen nicht zu sehen sind. Ohne sie hätte die Studie
mit vier Szenen geworben und mit drei gemessen, und **keine einzige Zahl wäre falsch
gerechnet gewesen.**
"""

import importlib.util
from pathlib import Path

import pytest

from aiimaging import paarschwellen


def _studie():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "studie_ersatzkalibrierung.py"
    spec = importlib.util.spec_from_file_location("werkzeug_studie_ersatz", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _zeile(szene, kamera, art, gut, rho, kante, gruppe=None):
    m = _studie()
    return {"fall_id": f"{szene}-{kamera}-{art}", "gut": gut, "szene": szene,
            "kamera": kamera, "gruppe": gruppe or m.gruppe(kamera), "art": art,
            "rho": rho, "kantenanteil": kante, "geometrieanteil": 0.11}


# ======================================================================================
# Der Aufbau — vier Szenen, vier Richtungen, zwei Gruppen
# ======================================================================================

def test_vier_szenen_und_die_vierte_ist_der_sicherheitsabstand():
    """`paarschwellen` verlangt drei. Die vierte darf ausfallen, ohne die Messung zu
    entwerten — genau das ist am 01.09.2026 eingetreten."""
    m = _studie()
    assert len(m.SZENEN) == 4
    assert len(m.SZENEN) > paarschwellen.MINDEST_SZENEN


def test_je_zwei_richtungen_frontal_und_diagonal():
    """Nicht vier frontale: Die Gruppe ist die Auswertungseinheit, und jede Gruppe muss
    für sich `MINDEST_KAMERAS` erfüllen."""
    m = _studie()
    assert len(m.FRONTAL) == 2 and len(m.DIAGONAL) == 2
    assert len(m.FRONTAL) >= paarschwellen.MINDEST_KAMERAS
    assert len(m.DIAGONAL) >= paarschwellen.MINDEST_KAMERAS
    assert not set(m.FRONTAL) & set(m.DIAGONAL), "eine Richtung in beiden Gruppen"


def test_die_gruppe_haengt_an_der_richtung():
    m = _studie()
    assert all(m.gruppe(k) == "frontal" for k in m.FRONTAL)
    assert all(m.gruppe(k) == "diagonal" for k in m.DIAGONAL)


def test_hochbau_und_raeume_stehen_in_getrennten_szenen():
    """`make_test_ifc` weist die Kombination zurück — die Studie darf sie nicht bauen."""
    m = _studie()
    for _, kw, _ in m.SZENEN:
        assert not (kw.get("hochbau") and kw.get("mit_raeumen"))


# ======================================================================================
# Die Dublettenprüfung
# ======================================================================================

def test_zwei_punktgleiche_zeilen_derselben_gruppe_sind_eine_dublette():
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("raeume", "s", "treu", True, 1.0, 1.0)]
    d = m.dubletten(zeilen)
    assert d["n_dubletten"] == 1
    assert d["ist_vertreter"] == [True, False], "der Erstling bleibt, nicht der Letzte"


def test_dieselbe_zahl_in_verschiedenen_gruppen_ist_keine_dublette():
    """Die Gruppe ist die Auswertungseinheit. Eine frontale und eine diagonale Zeile
    belegen verschiedene Aussagen, auch wenn ihre Zahl dieselbe ist."""
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("quader", "sSE", "treu", True, 1.0, 1.0)]
    assert m.dubletten(zeilen)["n_dubletten"] == 0


def test_dieselbe_zahl_in_verschiedenen_fallarten_ist_keine_dublette():
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("quader", "s", "skala", True, 1.0, 1.0)]
    assert m.dubletten(zeilen)["n_dubletten"] == 0


def test_verglichen_wird_auf_vier_stellen_und_nicht_auf_alle():
    """Was im Bericht nicht mehr zu unterscheiden ist, darf nicht als zwei Belege zählen."""
    m = _studie()
    assert m.DUBLETTE_STELLEN == 4
    zeilen = [_zeile("quader", "s", "treu", True, 0.123456, 0.5),
              _zeile("raeume", "s", "treu", True, 0.123499, 0.5)]
    assert m.dubletten(zeilen)["n_dubletten"] == 1


def test_ein_deutlicher_unterschied_bleibt_ein_eigener_beleg():
    """Die Gegenprobe zum Test darüber — die Rundung darf nicht alles verschmelzen."""
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 0.1234, 0.5),
              _zeile("raeume", "s", "treu", True, 0.1244, 0.5)]
    assert m.dubletten(zeilen)["n_dubletten"] == 0


def test_zwei_nicht_messbare_zeilen_sind_ebenfalls_eine_dublette():
    """`None` ist die dritte Antwort und keine Ausnahme von der Zählung: Zweimal
    «nicht messbar» ist ein Befund, nicht zwei."""
    m = _studie()
    zeilen = [_zeile("quader", "s", "flach", False, None, None),
              _zeile("hochbau", "s", "flach", False, None, None)]
    assert m.dubletten(zeilen)["n_dubletten"] == 1


def test_gleiches_rho_bei_verschiedenem_kantenanteil_ist_keine_dublette():
    """Verglichen wird das PAAR. Der Fall ist real: `treu` liefert auf jeder Szene
    ρ = 1.0000, aber auf Gelände nur 0.6408 Kantenanteil statt 1.0000."""
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("gelaende", "s", "treu", True, 1.0, 0.6408)]
    assert m.dubletten(zeilen)["n_dubletten"] == 0


# ======================================================================================
# Der Vorbehalt — der Grund, warum diese Studie sich nicht selbst adeln kann
# ======================================================================================

def test_jede_kurve_traegt_den_vorbehalt_der_perfekten_karten():
    m = _studie()
    zeilen = ([_zeile("s%d" % (i % 3), "s", "a%d" % i, True, 0.9, 0.9) for i in range(20)]
              + [_zeile("s%d" % (i % 3), "w", "b%d" % i, False, 0.3, 0.3) for i in range(20)])
    ergebnis = m.kurven(zeilen)
    assert ergebnis["kurven"], "ohne Kurven sagt der Test nichts"
    for schluessel, kurve in ergebnis["kurven"].items():
        assert m.VORBEHALT_PERFEKTE_KARTEN in kurve["vorbehalte"], schluessel
        assert kurve["genuegt_als_kalibrierung"] is False, schluessel


def test_ohne_den_vorbehalt_waere_es_eine_kalibrierung():
    """Die Gegenprobe. Ohne sie wäre der Test darüber auch grün, wenn die Kurve aus
    einem ganz anderen Grund durchgefallen wäre — und die Studie hätte einen Wächter,
    der nichts bewacht."""
    m = _studie()
    faelle = [{"fall_id": f"g{i}", "gut": True, "wert": 0.9,
               "szene": f"s{i % 3}", "kamera": f"k{i % 2}"} for i in range(20)]
    faelle += [{"fall_id": f"b{i}", "gut": False, "wert": 0.3,
                "szene": f"s{i % 3}", "kamera": f"k{i % 2}"} for i in range(20)]
    assert paarschwellen.trennkurve(faelle)["genuegt_als_kalibrierung"] is True
    assert paarschwellen.trennkurve(
        faelle, zusatz_vorbehalte=(m.VORBEHALT_PERFEKTE_KARTEN,)
    )["genuegt_als_kalibrierung"] is False


def test_der_vorbehalt_nennt_den_auftrag_den_er_nicht_ersetzt():
    """Ein Vorbehalt, der nicht sagt, worauf man noch wartet, wird zum Rauschen."""
    m = _studie()
    assert "auf-20260827-61" in m.VORBEHALT_PERFEKTE_KARTEN


def test_je_gruppe_und_zustand_und_groesse_eine_eigene_kurve():
    """Acht Kurven: zwei Gruppen × roh und entdoppelt × ρ und Kantenanteil. Eine
    gemeinsame Tabelle über beide Gruppen wäre genau der Fehler, den die Studie
    vermeiden soll."""
    m = _studie()
    zeilen = []
    for i in range(20):
        for kamera in ("s", "sSE"):
            zeilen.append(_zeile(f"s{i % 3}", kamera, f"g{i}", True, 0.9 - i / 1000, 0.9))
            zeilen.append(_zeile(f"s{i % 3}", kamera, f"b{i}", False, 0.3 - i / 1000, 0.3))
    schluessel = set(m.kurven(zeilen)["kurven"])
    assert schluessel == {
        f"{g}/{z}/{w}" for g in ("frontal", "diagonal")
        for z in ("roh", "entdoppelt") for w in ("rho", "kantenanteil")}


def test_die_entdoppelte_kurve_rechnet_mit_weniger_faellen():
    """Sonst wäre die Entdopplung eine Zierde. Die Zeilen sind absichtlich alle gleich."""
    m = _studie()
    zeilen = []
    for i in range(20):
        zeilen.append(_zeile(f"s{i}", "s", "treu", True, 1.0, 1.0))
        zeilen.append(_zeile(f"s{i}", "s", "flach", False, 0.3, 0.3))
    ergebnis = m.kurven(zeilen)
    roh = ergebnis["kurven"]["frontal/roh/rho"]
    entdoppelt = ergebnis["kurven"]["frontal/entdoppelt/rho"]
    assert roh["n_gut"] == 20 and roh["n_schlecht"] == 20
    assert entdoppelt["n_gut"] == 1 and entdoppelt["n_schlecht"] == 1
    assert any("UMFANG" in v for v in entdoppelt["vorbehalte"]), (
        "eine entdoppelte Kurve unter dem Mindestmass muss das melden")


def test_eine_wiederholte_kennung_verfaelscht_die_entdopplung_nicht():
    """*Der Fehler, den diese Datei beim Schreiben gefunden hat.* Die Entdopplung filterte
    zuerst über ``fall_id``; bei zwei Zeilen mit derselben Kennung liess sie **beide**
    durch, weil die Kennung des Erstlings auf beide passte. Gezählt wird seither die
    Position."""
    m = _studie()
    zeilen = [_zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("quader", "s", "treu", True, 1.0, 1.0),
              _zeile("quader", "s", "treu", True, 1.0, 1.0)]
    assert len({z["fall_id"] for z in zeilen}) == 1, "die Kennungen sind absichtlich gleich"
    d = m.dubletten(zeilen)
    assert d["n_dubletten"] == 2
    assert d["ist_vertreter"] == [True, False, False]
