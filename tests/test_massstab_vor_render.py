"""Der Massstabs-Riegel meldet dort, wo Bilder entstehen — seit dem 26.08.2026.

**Der Riegel war seit langem gebaut und lief auf diesem Weg nirgends.**
`aiimaging.torwaechter` nennt in seinem eigenen Docstring den Anlass:

  *«Eine Konversion kann sauber `ok` melden und die Geometrie trotzdem um Faktor 1000
  danebenliegen. Der Runner war zufrieden, das Modell 30 km gross, und der Fehler fiel
  erst am fertigen Bild auf.»*

Nachgezählt am 26.08.2026: `torwaechter` kommt in `abholer.py`, `bruecke.py` und
`tools/abholen.py` **nullmal** vor. Die fünfte Stelle desselben Owner-Einwands dieser
Woche — und die einzige, an der ein fertiger Riegel danebenstand.

**Er meldet und bricht nichts ab, und das ist eine Korrektur.** Der erste Entwurf brach
ab, sobald `pruefe_massstab` einen `verdacht_faktor` nannte, mit der Begründung, das sei
eine *benannte* Bedingung wie bei `_kamera_ueber_dach`. Eine Gegenprüfung hat gezeigt,
dass das nicht stimmt — nachgerechnet an der Funktion selbst:

* **0,003 m bis 1,0 m** ergibt `faktor = 0.001`. Das ist **jeder Bauteil-Render** — eine
  Tür, ein Fensterdetail, eine Demoszene.
* **3000 m bis 10⁶ m** ergibt `faktor = 1000`. Das trifft auch **ein einziges verirrtes
  Mesh** 4 km neben dem Bau, etwa einen mitexportierten Vermessungspunkt.

Ein `verdacht_faktor` ist **kein Beleg für einen Einheitenfehler**; er sagt nur, dass eine
Division ein plausibles Ergebnis liefert. Und die Zahl, die den Abbruch tragen müsste — wie
oft der Torwächter auf dem echten Bestand anschlägt —, hat niemand, weil er nie lief.
*Ein Riegel, der scharfgestellt wird, bevor seine Fehlalarmrate bekannt ist, lehnt Aufträge
ab, und niemand weiss welche.*
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, torwaechter
from conftest import MINI_PNG

#: Ein gewöhnliches Bauwerk: 8 × 5 × 11 m.
BAUWERK = [[0.0, 0.0, 0.0], [8.0, 5.0, 11.0]]
#: Millimeter als Meter gelesen — der Fall aus dem Vorläufer, 30 km statt 30 m.
FAKTOR_1000 = [[0.0, 0.0, 0.0], [8000.0, 5000.0, 11000.0]]
#: Gelände samt Umgebung. Gemessen an 40 echten Dateien: 1002 m und 1127 m, Einheit in
#: Ordnung. **Kein** Einheitenfehler.
KONTEXTMODELL = [[0.0, 0.0, 0.0], [1002.0, 800.0, 40.0]]


# ======================================================================================
# Die Rechnung — und die Fenster, in denen sie sich irren wuerde
# ======================================================================================

def test_der_faktor_tausend_wird_erkannt_und_benannt():
    """**Der Fall aus dem Vorläufer.** 8 m werden zu 8 km, weil jemand Millimeter für
    Meter gehalten hat. Gemeldet — nicht abgebrochen."""
    lage = abholer._massstab_gemeldet({"bbox_bauwerk": FAKTOR_1000})

    assert lage["beanstandet"] is True
    assert lage["verdacht_faktor"] == 1000
    assert lage["quelle"] == "bbox_bauwerk"
    assert lage["geprueft"] is True


def test_ein_gewoehnliches_bauwerk_wird_nicht_beanstandet():
    """Die Gegenprobe. Eine Meldung bei jedem Bauwerk wäre die nächste Dauerzeile."""
    lage = abholer._massstab_gemeldet({"bbox_bauwerk": BAUWERK})

    assert lage["beanstandet"] is False
    assert lage["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN


def test_ein_kontextmodell_traegt_keinen_faktor():
    """An 40 echten Dateien fielen zwei Modelle mit 1002 m und 1127 m durch — Gelände
    samt Umgebung, Einheit völlig in Ordnung. Der fehlende Faktor ist genau der
    Unterschied zum Einheitenfehler."""
    lage = abholer._massstab_gemeldet({"bbox_bauwerk": KONTEXTMODELL})

    assert lage["beanstandet"] is True
    assert lage["verdacht_faktor"] is None


@pytest.mark.parametrize("kante, faktor", [
    (0.003, 0.001), (0.5, 0.001), (0.9, 0.001),
    (3000.0, 1000.0), (4000.0, 1000.0), (30000.0, 1000.0),
])
def test_das_fenster_des_verdachts_ist_breiter_als_es_aussieht(kante, faktor):
    """**Der Grund, warum hier nichts abbricht** — nachgerechnet an der Funktion selbst.

    Zwischen 3 mm und 1 m liegt *jeder Bauteil-Render*: eine Tür, ein Fensterdetail, eine
    Demoszene. Und ab 3 km liegt auch *ein einziges verirrtes Mesh* — ein mitexportierter
    Vermessungspunkt 4 km neben dem Bau. Beide bekämen die Diagnose «Einheitenfehler»,
    und beide Male wäre sie falsch.
    """
    lage = abholer._massstab_gemeldet(
        {"bbox_bauwerk": [[0.0, 0.0, 0.0], [kante, kante / 2, kante / 3]]})

    assert lage["verdacht_faktor"] == faktor
    assert lage["beanstandet"] is True


def test_genau_ein_meter_gilt_noch_als_bauwerk():
    """Die Schranke ist ``MIN <= kante``, nicht ``<``. Ein Integrationstest dieses
    Projekts steht bei exakt 1,0 m — wer die Vergleichsrichtung anfasst, macht ihn rot,
    und der Fehler sähe aus wie ein Rahmungsfehler."""
    lage = abholer._massstab_gemeldet({"bbox_bauwerk": [[0, 0, 0], [1.0, 1.0, 1.0]]})

    assert lage["beanstandet"] is False


def test_ein_fehlender_bericht_ist_nicht_geprueft():
    """Jeder Lauf von vor dem 25.08.2026 trägt keine Hüllbox. *Nicht messen ist nicht
    bestehen* — und es ist auch kein Mangel."""
    lage = abholer._massstab_gemeldet({})

    assert lage["geprueft"] is False
    assert lage["beanstandet"] is False
    assert lage["quelle"] is None


def test_ohne_bauwerksbox_wird_die_szenenbox_genommen_und_es_steht_da():
    """Ein Rückfall, den niemand sieht, ist von einer Messung nicht zu unterscheiden."""
    lage = abholer._massstab_gemeldet({"bbox": FAKTOR_1000})

    assert lage["quelle"] == "bbox"
    assert lage["beanstandet"] is True


def test_die_bauwerksbox_hat_vorrang_vor_der_szenenbox():
    """**Der Grund, warum die Wahl der Box eine Frage ist.** Ein 8-m-Bauwerk auf einer
    1002-m-Geländeplatte ist in Ordnung; auf der Szenenbox gemessen wäre es beanstandet."""
    lage = abholer._massstab_gemeldet(
        {"bbox": KONTEXTMODELL, "bbox_bauwerk": BAUWERK})

    assert lage["quelle"] == "bbox_bauwerk"
    assert lage["beanstandet"] is False


def test_die_note_zur_huellbox_wandert_mit():
    """`bbox_bauwerk` ist `None`, sobald `aiimaging.maske` aus Blender nicht erreichbar
    war — dann misst man am Ende doch die Geländeplatte, und das darf nicht unsichtbar
    sein."""
    lage = abholer._massstab_gemeldet(
        {"bbox": BAUWERK, "bbox_bauwerk_note": "maske nicht erreichbar"})

    assert lage["quelle"] == "bbox"
    assert "nicht erreichbar" in lage["note"]


@pytest.mark.parametrize("kaputt", [None, "gross", [1, 2], [[0, 0], [1, 1]], [[0, 0, 0]]])
def test_eine_unbrauchbare_box_stuerzt_nicht_ab(kaputt):
    """«Der Torwächter soll ablehnen, nicht abstürzen» — der Bericht kommt aus einem
    fremden Prozess jenseits der Prozessgrenze."""
    lage = abholer._massstab_gemeldet({"bbox_bauwerk": kaputt})

    assert lage["beanstandet"] is False
    assert lage["geprueft"] is False


def test_der_bericht_wird_gebaut_und_nicht_durchgereicht():
    """``status`` heisst im Multipass-Bericht «die Ausgabedateien sind frisch», in einem
    `ifc_to_glb`-Report «die Konversion ist gelungen». Ein fremdes `status` hier zu lesen
    trüge eine Bedeutung mit, die nicht gemeint ist — und der Zweig ist auf diesem Weg
    ohnehin unerreichbar, weil `seams` bei einem Fehlschlag wirft."""
    lage = abholer._massstab_gemeldet(
        {"status": "error", "error": "Blender abgestuerzt", "bbox_bauwerk": BAUWERK})

    assert lage["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN, (
        "das fremde 'status' wird bewusst NICHT gelesen")


# ======================================================================================
# Die Naht — an der ganzen Kette und nicht am Baustein
# ======================================================================================

def _lauf(tmp_path, bericht_zusatz):
    zaehler = {"render": 0}

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"},
                **bericht_zusatz}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild = Path(tmp_path) / f"b{zaehler['render']}.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "s", "richtung": "s"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house"}})
    return ergebnis, zaehler["render"]


def test_ein_dreissig_kilometer_modell_wird_gemeldet_und_gerendert(tmp_path):
    """**Der Kern der Korrektur.** Der erste Entwurf brach hier ab. Er tut es nicht mehr,
    solange die Fehlalarmrate am echten Bestand ungemessen ist — gefragt in einem eigenen
    Auftrag."""
    ergebnis, n_render = _lauf(tmp_path, {"bbox_bauwerk": FAKTOR_1000})

    assert n_render == 1, "gerendert wird, und der Befund sagt warum das fragwuerdig ist"
    lage = ergebnis["kameras"][0]["massstab"]
    assert lage["beanstandet"] is True
    assert lage["verdacht_faktor"] == 1000


def test_ein_gewoehnlicher_auftrag_wird_nicht_beanstandet(tmp_path):
    """Die Gegenprobe an der Naht."""
    ergebnis, n_render = _lauf(tmp_path, {"bbox_bauwerk": BAUWERK})

    assert n_render == 1
    assert ergebnis["kameras"][0]["massstab"]["beanstandet"] is False


def test_ein_bericht_ohne_huellbox_laeuft_durch_wie_bisher(tmp_path):
    """`bbox` kommt in elf Attrappen dieser Testsammlung nullmal vor — und in jedem Lauf
    von vor dem 25.08.2026 auch nicht."""
    ergebnis, n_render = _lauf(tmp_path, {})

    assert n_render == 1
    assert ergebnis["kameras"][0]["massstab"]["geprueft"] is False


def test_der_massstab_steht_nicht_in_der_abbruchschleife(tmp_path):
    """**Der zweite Teil der Korrektur.** Rahmung und Kamerahöhe sind Eigenschaften der
    KAMERA — eine andere Blickrichtung kann sie heilen, darum überspringt die Schleife
    dort je Kamera. Der Massstab ist eine Eigenschaft der GEOMETRIE und bei jeder Kamera
    derselbe; ihn dort einzuhängen hiesse, dreimal denselben Blender-Lauf zu bezahlen
    (gemessen ~97 s je Kamera), um ein Urteil zu fällen, das nach dem ersten feststand."""
    quelle = Path(abholer.__file__).read_text(encoding="utf-8")

    assert "for lage in (rahmung, komposition):" in quelle
    assert "for lage in (massstab, rahmung, komposition):" not in quelle


# ======================================================================================
# Was ein Mensch am Terminal davon sieht
# ======================================================================================

def test_der_kurzbefund_nennt_den_faktor_und_seine_grenze():
    """Er nennt den Faktor — **und im selben Satz, dass derselbe Verdacht jeden
    Bauteil-Render unter 1 m trifft.** Eine Diagnose ohne ihre Fehlalarmbreite schickt
    jemanden auf eine Fehlersuche, die es vielleicht gar nicht gibt."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "s", "massstab": {"beanstandet": True, "verdacht_faktor": 1000,
                                     "groesste_kante_m": 8000.0,
                                     "quelle": "bbox_bauwerk", "note": ""}}]})

    treffer = [z for z in zeilen if "MASSSTAB UNPLAUSIBEL" in z]
    assert len(treffer) == 1
    assert "1000" in treffer[0]
    assert "Gerendert wurde TROTZDEM" in treffer[0]
    assert "unter 1 m" in treffer[0], "die Fehlalarmbreite gehoert in dieselbe Zeile"


def test_der_kurzbefund_unterscheidet_das_kontextmodell_vom_einheitenfehler():
    """Zwei verschiedene Sätze, weil es zwei Befunde sind — und der eine legt eine
    Korrektur an der Quelle nahe, der andere gar nichts."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "s", "massstab": {"beanstandet": True, "verdacht_faktor": None,
                                     "groesste_kante_m": 1002.0,
                                     "quelle": "bbox", "note": ""}}]})

    treffer = [z for z in zeilen if "MASSSTAB UNPLAUSIBEL" in z]
    assert len(treffer) == 1
    assert "Kontextmodell" in treffer[0] and "1002" in treffer[0]
    assert "unter 1 m" not in treffer[0]


def test_bei_plausiblem_massstab_steht_keine_zeile_da():
    """Eine Zeile, die bei jedem Auftrag erscheint, ist nach dem dritten Mal keine."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "s", "massstab": {"beanstandet": False}}]})

    assert not [z for z in zeilen if "Massstab" in z or "MASSSTAB" in z]


def test_ein_alter_befund_ohne_das_feld_wird_nicht_rot():
    assert not [z for z in abholer.befund_kurz({"kameras": [{"kamera": "s"}]})
                if "MASSSTAB" in z]
