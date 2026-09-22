"""Die Innenansicht über die Projektmappe — bestellbar **und** lieferbar. Befund 22.09.2026.

Was nachgefahren wurde
----------------------
Über die Oberfläche war die Innenansicht seit dem 22.09.2026 bestellbar, über die Mappe
aber nicht lieferbar. Räume entstehen nur aus der IFC; ``arbeitsgang.rechne`` warf
``ifc_path`` weg und baute immer aus der umgewandelten glb, wo ``raeume`` ``None`` ist.
Nachgefahren über ``lege_an`` (IFC) und ``rechne`` mit ``innenraum``: Der Raumleser wurde
nie gerufen, der Multipass endete im Fehlerknoten «Innenansicht verlangt, aber kein
Standpunkt», und am Runner kam kein Auge an.

Seither liest ``lege_an`` die Räume beim Anlegen einmal und legt sie in der Mappe ab;
``rechne`` setzt sie bei einer Innenbestellung mit ``kette.mit_raeumen`` an den
Geometrie-Knoten.

    *Eine Naht, die nur der direkte Aufrufer erreicht, gibt es für das Produkt nicht.*

Warum diese Proben
------------------
1. **Die Bestellung kommt über den Produktweg am Runner an** — ``lege_an`` mit einer
   IFC, ``rechne`` mit ``innenraum``, Geometrie und Multipass mit ihren echten
   Ausführern. Geprüft wird der Standpunkt, den der Runner bekommt, nicht ein Eintrag.
2. **Ohne Bestellung ändert sich nichts** — der Geometrie-Knoten, den der Lauf wirklich
   rechnet, trägt dieselben Parameter wie vor der Änderung. Sonst rechnete jeder alte
   Lauf einer IFC-Mappe neu.
3. **Eine glb-Mappe scheitert weiter laut**, mit dem Grund «über eine glb eingestiegen».
4. **Eine alte Mappe** (angelegt vor dieser Änderung, ohne Raumeintrag) bricht nicht:
   Aussen rechnet sie wie bisher, innen wird mit einem Satz abgewiesen, der sagt, was zu
   tun ist.
5. **Gelesen und nichts gefunden ist nicht dasselbe wie nicht gelesen.** Scheitert der
   Raumleser beim Anlegen, steht eine leere Raumliste mit Grund in der Mappe — und der
   Grund kommt im Fehler des Laufs an.
6. **Die Räume stehen im Hash** — zwei Raumlisten, zwei Geometrie-Hashes.

Ohne Blender, ohne ``.venv-ifc``, ohne GPU: Umwandlung, Raumleser und Runner werden per
monkeypatch ersetzt. Die IFC kommt aus ``tools/make_test_ifc.py``, die glb aus
``tools/make_test_glb.py`` — beide synthetisch (Regel 3).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, graph, kette, projekt, raumkamera
from aiimaging.kette import KNOTEN_GEOMETRIE, KNOTEN_MULTIPASS

WURZEL = Path(__file__).resolve().parents[1]

#: Der Raum, wie ihn der Raumleser für ``tools/make_test_ifc.py --raeume`` meldet —
#: synthetisch, kein echtes Projekt (Regel 3).
RAUM_SUED = {"name": "Raum-Sued", "z_unten_m": 0.1, "hoehe_m": 2.4,
             "grundriss_m": [[7.7, 0.3], [7.7, 2.5], [5.0, 2.5], [5.0, 0.3]]}

#: Bauwerk 12 × 9 × 15 m auf einer Geländeplatte — synthetisch, in glTF-Koordinaten.
SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


def _werkzeug(datei: str, name: str):
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def werkzeuge():
    return (_werkzeug("make_test_glb.py", "make_test_glb_fuer_innenmappe"),
            _werkzeug("make_test_ifc.py", "make_test_ifc_fuer_innenmappe"))


class Werkstatt:
    """Die Attrappen an den Prozessgrenzen — und was dort ankam.

    Ersetzt werden nur die Stellen, die einen Subprozess starten: die Umwandlung
    (``seams.ifc_zu_glb``), der Raumleser (``seams.ifc_raeume``) und der Runner
    (``seams.glb_zu_multipass``). Alles dazwischen läuft echt.
    """

    def __init__(self, monkeypatch, glb_bytes: bytes, *, raumleser_faellt: bool = False):
        self.glb_bytes = glb_bytes
        self.raumleser_faellt = raumleser_faellt
        self.raumleser_gerufen: list[str] = []
        self.runner_gerufen: list[dict] = []
        monkeypatch.setattr(kette.seams, "ifc_zu_glb", self.umwandlung)
        monkeypatch.setattr(kette.seams, "ifc_raeume", self.raumleser)
        monkeypatch.setattr(kette.seams, "glb_zu_multipass", self.runner)

    def umwandlung(self, quelle, ziel, **kw):
        ziel = Path(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_bytes(self.glb_bytes)
        return {"status": "ok", "glb_path": str(ziel), "up_axis": "Y"}

    def raumleser(self, ifc_path, **kw):
        self.raumleser_gerufen.append(str(ifc_path))
        if self.raumleser_faellt:
            raise RuntimeError("venv-ifc fehlt (Attrappe)")
        return {"status": "ok", "raeume": [dict(RAUM_SUED)]}

    def runner(self, glb, out_dir, **kw):
        self.runner_gerufen.append(kw)
        tiefe = Path(out_dir) / "tiefe.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe)}


def _bild(*, knoten, eingaben, out_dir):
    bild = Path(out_dir) / "bild.png"
    bild.write_text("bild", encoding="utf-8")
    return {"status": "ok", "bild_png": str(bild)}


def _pruefung(*, knoten, eingaben, out_dir):
    return {"status": "ok", "bestanden": None, "begruendung": "Attrappe"}


def _tabelle(geometrie=None) -> dict:
    """Geometrie und Multipass echt, Bild und Prüfung als Attrappe."""
    tabelle = {**kette.AUSFUEHRER, kette.ART_RENDER: _bild, kette.ART_QA: _pruefung}
    if geometrie is not None:
        tabelle[kette.ART_GEOMETRIE] = geometrie
    return tabelle


@pytest.fixture
def ifc(tmp_path, werkzeuge):
    return werkzeuge[1].erzeuge_ifc(tmp_path / "quelle" / "haus.ifc", mit_raeumen=True)


@pytest.fixture
def szene(werkzeuge) -> bytes:
    return werkzeuge[0].baue_glb(SZENE)


def _multipass_fehler(ergebnis) -> str:
    mp = ergebnis["lauf"]["knoten"][KNOTEN_MULTIPASS]
    assert mp["status"] == kette.STATUS_FEHLER, mp
    return mp["error"] or (mp.get("ausgaben") or {}).get("error") or ""


# ------------------------------------------------------ 1 · Über die Mappe geliefert

def test_eine_ueber_die_mappe_bestellte_innenansicht_erreicht_den_standpunkt(
        tmp_path, monkeypatch, ifc, szene):
    """**Angelegt über** ``lege_an``, **bestellt über** ``rechne``, **angekommen am Runner**.

    Auf halber Raumhöhe (0,1 m + 2,4 m / 2 = 1,3 m), waagrecht, mit der gemessenen
    24-mm-Brennweite statt des 50-mm-Rückfalls des Runners. Der Raumleser läuft genau
    einmal — beim Anlegen, nicht bei jedem Lauf.
    """
    werkstatt = Werkstatt(monkeypatch, szene)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, ifc, einstellungen={"prompt": "Abendlicht"})

    eintrag = projekt.oeffne(wurzel)["projekt"]["import"]["raeume"]
    assert eintrag["status"] == "ok"
    assert [r["raum"]["name"] for r in eintrag["raeume"]] == ["Raum-Sued"]

    ergebnis = arbeitsgang.rechne(
        wurzel, ausfuehrer=_tabelle(),
        innenraum={"raum": "Raum-Sued", "art": raumkamera.ART_FRONTAL})

    assert werkstatt.raumleser_gerufen == [str(ifc)], "einmal gelesen, beim Anlegen"
    mp = ergebnis["lauf"]["knoten"][KNOTEN_MULTIPASS]
    assert mp["status"] == kette.STATUS_OK, mp.get("error")
    assert len(werkstatt.runner_gerufen) == 1
    gesehen = werkstatt.runner_gerufen[0]
    assert gesehen.get("auge") is not None, (
        "die über die Mappe bestellte Innenansicht kommt am Runner nicht an")
    assert gesehen["auge"][2] == pytest.approx(1.3), "halbe Raumhöhe ab z_unten"
    assert gesehen["auge"][2] == pytest.approx(gesehen["blick_auf"][2]), "Kamera waagrecht"
    assert gesehen.get("brennweite") == pytest.approx(raumkamera.BRENNWEITE_INNEN_MM), (
        "ohne die gemessene Brennweite gilt drüben der 50-mm-Rückfall (09.09.2026)")


# ---------------------------------------------------- 2 · Ohne Bestellung wie bisher

def test_ohne_innenraum_rechnet_die_ifc_mappe_den_bisherigen_graphen(
        tmp_path, monkeypatch, ifc, szene):
    """Die Räume stehen in der Mappe — im Lauf ohne Innenbestellung dürfen sie nicht
    auftauchen. Verglichen wird, was der Geometrie-Ausführer **wirklich bekommt**, mit dem
    Knoten, den ``baue_kette`` ohne Räume baut — und damit auch sein Hash."""
    Werkstatt(monkeypatch, szene)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, ifc, einstellungen={"prompt": "Abendlicht"})

    bekommen = []

    def geometrie(*, knoten, eingaben, out_dir):
        bekommen.append(knoten)
        return kette.AUSFUEHRER[kette.ART_GEOMETRIE](
            knoten=knoten, eingaben=eingaben, out_dir=out_dir)

    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle(geometrie))
    assert ergebnis["lauf"]["knoten"][KNOTEN_MULTIPASS]["status"] == kette.STATUS_OK

    glb = projekt.loese_pfad(projekt.oeffne(wurzel)["projekt"]["import"]["glb"], wurzel)
    bisher = kette.baue_kette(glb_path=str(glb), up_axis="Y", prompt="Abendlicht")
    assert len(bekommen) == 1
    assert "raeume" not in bekommen[0].params
    assert bekommen[0].params == bisher.knoten[KNOTEN_GEOMETRIE].params
    assert (graph.inhalts_hash(bekommen[0], [])
            == graph.inhalts_hash(bisher.knoten[KNOTEN_GEOMETRIE], [])), \
        "ohne Innenbestellung muss jeder alte Lauf seinen Zwischenspeicher behalten"


# ------------------------------------------------------ 3 · glb-Mappe: laut, ehrlich

def test_eine_glb_mappe_scheitert_innen_laut_mit_ehrlichem_grund(
        tmp_path, monkeypatch, szene):
    """Aus einer glb gibt es keinen Raumbegriff — ``raeume`` bleibt ``None``, und der
    Grund sagt das. Gerendert wird nicht, der Raumleser wird gar nicht erst gefragt."""
    werkstatt = Werkstatt(monkeypatch, szene)
    quelle = tmp_path / "quelle" / "haus.glb"
    quelle.parent.mkdir(parents=True)
    quelle.write_bytes(szene)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, quelle,
                        einstellungen={"prompt": "Abendlicht", "up_axis": "Y"})

    einfuhr = projekt.oeffne(wurzel)["projekt"]["import"]
    assert "raeume" in einfuhr and einfuhr["raeume"] is None, "nicht gelesen, nicht leer"

    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle(),
                                  innenraum={"raum": "Raum-Sued"})
    fehler = _multipass_fehler(ergebnis)
    assert "Innenansicht verlangt" in fehler and "glb" in fehler, fehler
    assert werkstatt.runner_gerufen == [], "wer innen bestellt, bekommt nicht aussen"
    assert werkstatt.raumleser_gerufen == []


# ------------------------------------------------------ 4 · Alte Mappe bricht nicht

def _als_alte_mappe(wurzel: Path) -> None:
    """Den Raumeintrag entfernen — so sah eine IFC-Mappe vor dem 22.09.2026 aus."""
    p = projekt.oeffne(wurzel)["projekt"]
    del p["import"]["raeume"]
    projekt.speichere(p, wurzel)


def test_eine_alte_ifc_mappe_weist_die_innenansicht_mit_einem_satz_ab(
        tmp_path, monkeypatch, ifc, szene):
    werkstatt = Werkstatt(monkeypatch, szene)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, ifc, einstellungen={"prompt": "Abendlicht"})
    _als_alte_mappe(wurzel)

    with pytest.raises(arbeitsgang.ArbeitsgangError) as fehler:
        arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle(), innenraum={"raum": "Raum-Sued"})
    satz = str(fehler.value)
    assert "neu angelegt" in satz, satz
    assert "NICHT, dass das Modell keine hat" in satz, satz
    assert werkstatt.runner_gerufen == []


def test_eine_alte_ifc_mappe_rechnet_aussen_wie_bisher(tmp_path, monkeypatch, ifc, szene):
    werkstatt = Werkstatt(monkeypatch, szene)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, ifc, einstellungen={"prompt": "Abendlicht"})
    _als_alte_mappe(wurzel)

    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle())
    assert ergebnis["lauf"]["knoten"][KNOTEN_MULTIPASS]["status"] == kette.STATUS_OK
    assert werkstatt.runner_gerufen[0].get("auge") is None, "aussen, wie bisher"


# ---------------------------------------- 5 · Gelesen-und-leer ist nicht nicht-gelesen

def test_ein_gescheiterter_raumleser_steht_als_befund_und_kommt_im_fehler_an(
        tmp_path, monkeypatch, ifc, szene):
    """Das Anlegen hält nicht an; in der Mappe steht eine **leere** Liste mit Grund —
    nicht ``None`` —, und der Grund erreicht den Fehler des Laufs."""
    werkstatt = Werkstatt(monkeypatch, szene, raumleser_faellt=True)
    wurzel = tmp_path / "mappe"
    arbeitsgang.lege_an(wurzel, ifc, einstellungen={"prompt": "Abendlicht"})

    eintrag = projekt.oeffne(wurzel)["projekt"]["import"]["raeume"]
    assert eintrag is not None and eintrag["raeume"] == []
    assert eintrag["status"] == "fehler" and "venv-ifc fehlt" in eintrag["grund"]

    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle(),
                                  innenraum={"raum": "Raum-Sued"})
    fehler = _multipass_fehler(ergebnis)
    assert "Der Raumleser meldete" in fehler and "venv-ifc fehlt" in fehler, fehler
    assert werkstatt.runner_gerufen == []


# ----------------------------------------------------------- 6 · Räume im Hash

def test_die_raeume_stehen_im_hash_und_none_laesst_den_graphen_stehen():
    grund = kette.baue_kette(glb_path="haus.glb", up_axis="Y", prompt="Abendlicht",
                             innenraum={"raum": "Raum-Sued"})
    sued = {"status": "ok",
            "raeume": [{"raum": RAUM_SUED, "kamera": raumkamera.standpunkte(RAUM_SUED)}]}
    leer = {"status": "ok", "raeume": []}

    assert kette.mit_raeumen(grund, None) == grund, "nicht gelesen heisst nicht angefasst"
    mit_sued = kette.mit_raeumen(grund, sued).knoten[KNOTEN_GEOMETRIE]
    mit_leer = kette.mit_raeumen(grund, leer).knoten[KNOTEN_GEOMETRIE]
    assert graph.inhalts_hash(mit_sued, []) != graph.inhalts_hash(mit_leer, []), \
        "zwei Raumlisten, zwei Hashes — sonst wäre der alte Grundriss ein Treffer"

    ueber_ifc = kette.baue_kette(ifc_path="haus.ifc", prompt="Abendlicht",
                                 innenraum={"raum": "Raum-Sued"})
    with pytest.raises(kette.KettenError, match="zwei Quellen"):
        kette.mit_raeumen(ueber_ifc, sued)
