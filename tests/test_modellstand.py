"""Liegt das Modell hinter seinem Erzeuger zurück? — die Prüfung, die drei Läufen fehlte.

**Der gemessene Anlass.** Am 01./02.09.2026 sind drei Läufe hintereinander mit
``lauf16.glb`` gefahren. An der Datei nachgezählt: 4 Netze, 4 Primitive, **0 Materialien**,
``asset.generator = "pygltflib@v1.16.5"``. Der Export schreibt Materialien seit dem
01.09.2026; das Modell lag also hinter seinem eigenen Erzeuger zurück, und die ganze Kette
war grün. Die Fassung mit Materialien lag daneben (``lauf16-mit-material.glb``: 3
Materialien, 7 Primitive) — eine Datei weiter, nicht im Lauf.

**Regel 3:** Alle Geometrie hier ist synthetisch, mit ``tools/make_test_glb.py`` im Repo
erzeugt. Die Zahlen aus den echten Läufen stehen als Kommentar, die Dateien nicht.

Die Falle, gegen die die Hälfte dieser Datei antritt
-----------------------------------------------------
Eine Prüfung, die «alles gut» sagt, weil sie nichts kennt, ist schlimmer als keine — sie
erzeugt das grüne Abzeichen, das niemanden mehr nachsehen lässt. Am 02.09.2026 ist genau
das zweimal aufgetreten (eine Wache, die beim ersten Treffer grün gab; ein Füllgrad, der
immer 0.700 meldete). Darum prüft jeder Abschnitt hier **beide** Richtungen: dass der
Mangel gefunden wird UND dass der gesunde Fall nicht beanstandet wird.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, glbbox, modellstand

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"

#: Zwei Quader — ein Bauwerk auf einer Platte. Was drin steht, ist hier gleichgültig;
#: geprüft wird der Kopf der Datei, nicht ihre Geometrie.
SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)

#: Ein gültiger Vermerk, wie ``KosmoDraw/code/tools/glb_export_runner.py`` ihn schreibt.
#: Die Zahlen passen zu :data:`SZENE` mit zwei Materialien.
VERMERK = {
    "schema": modellstand.VERMERK_SCHEMA,
    "erzeuger": "KosmoDraw glb_export_runner",
    "stand": "2026-09-02",
    "merkmale": {"disziplin_layer": "2026-08-19", "materialien": "2026-09-01"},
    "quelle": {"art": "ifc", "name": "modell.ifc", "bytes": 1234, "sha256": "0" * 64},
    "traegt": {"ifc_klassen": {"IfcWall": 4905, "IfcWindow": 700, "IfcDoor": 1016,
                               "IfcBuildingStorey": 9},
               "n_materialien": 2, "n_primitive": 2, "n_primitive_mit_material": 2,
               "n_bauteile_mit_material": 2, "n_disziplin_layer": 2},
}


def _erzeuger():
    """``tools/make_test_glb.py`` über den Dateipfad laden — es ist kein Paketmodul."""
    spez = importlib.util.spec_from_file_location("make_test_glb_modellstand", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


def _glb(tmp_path, name, **kw):
    pfad = tmp_path / name
    pfad.write_bytes(_erzeuger().baue_glb(SZENE, **kw))
    return pfad


def _mit_klassen(**klassen):
    """Ein Vermerk wie :data:`VERMERK`, aber mit anderen Bauteilzahlen der Quelle."""
    v = {k: (dict(w) if isinstance(w, dict) else w) for k, w in VERMERK.items()}
    v["traegt"] = dict(VERMERK["traegt"], ifc_klassen=dict(klassen))
    return v


# ======================================================================================
# 1 · Der Materialblock — die eine Feststellung, die ohne Vermerk trägt
# ======================================================================================

def test_eine_glb_ohne_materialblock_liegt_zurueck(tmp_path):
    """Der Befund von ``lauf16.glb``, an einer synthetischen Datei nachgestellt."""
    befund = modellstand.pruefe(_glb(tmp_path, "grau.glb"))

    assert befund["urteil"] == modellstand.ZURUECK, befund
    assert befund["maengel"], befund
    assert "Materialblock" in befund["maengel"][0], befund["maengel"]
    assert not modellstand.bestanden(befund)


def test_dieselbe_szene_mit_materialien_wird_nicht_beanstandet(tmp_path):
    """Die Gegenprobe. Ohne sie beanstandete die Regel jede Datei und bewiese nichts.

    Entscheidend ist der Unterschied zum Test darüber: **dieselbe** Geometrie, **derselbe**
    Weg, nur der ``materials``-Block dazu — und der Mangel verschwindet.
    """
    befund = modellstand.pruefe(
        _glb(tmp_path, "bunt.glb", materialien=("Glas", "Aussenputz")))

    assert befund["maengel"] == [], befund["maengel"]
    assert befund["gemessen"]["n_materialien"] == 2, befund["gemessen"]


def test_derselbe_mangel_steht_nur_einmal_im_befund(tmp_path):
    """Ohne Materialblock UND mit einer Merkmalsliste, die Materialien führt.

    Zwei Wege zeigen auf dieselbe Tatsache: die Messung an der Datei (die keinen Vermerk
    braucht) und der Abgleich gegen die Merkmalsliste. Zwei Zeilen für eine Tatsache
    liessen einen Lauf schlimmer aussehen, als er ist — dieselbe Sorte Unehrlichkeit wie
    zu wenig zu melden.
    """
    befund = modellstand.pruefe(_glb(tmp_path, "grau_mit_vermerk.glb", vermerk=VERMERK))

    assert befund["urteil"] == modellstand.ZURUECK, befund
    assert len(befund["maengel"]) == 1, befund["maengel"]


def test_der_materialbefund_braucht_keinen_vermerk(tmp_path):
    """Er greift auch bei einer Datei, die gar nichts über sich sagt.

    Das ist der Riegel gegen die eigentliche Falle: Wäre der Materialbefund an den Vermerk
    gebunden, ginge ``lauf16.glb`` — die keinen hat — als «ungeprüft» durch, und genau
    dieses Modell ist dreimal gefahren.
    """
    befund = modellstand.pruefe(_glb(tmp_path, "namenlos.glb"))

    assert befund["vermerk"] is False, befund
    assert befund["urteil"] == modellstand.ZURUECK, befund
    # Der Mangel schlägt das Nichtwissen. Andersherum wäre «ich kenne den Erzeuger nicht»
    # eine Ausrede für einen gemessenen Rückstand.
    assert befund["offen"], befund


# ======================================================================================
# 2 · Der dritte Zustand — ungeprüft ist kein Bestehen
# ======================================================================================

def test_ohne_herkunftsvermerk_ist_das_urteil_ungeprueft(tmp_path):
    befund = modellstand.pruefe(
        _glb(tmp_path, "ohne_vermerk.glb", materialien=("Glas",)))

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert befund["erzeuger"] is None
    assert any("Herkunftsvermerk" in g for g in befund["offen"]), befund["offen"]


@pytest.mark.parametrize("urteil", [modellstand.UNGEPRUEFT, modellstand.ZURUECK])
def test_nur_traegt_gilt_als_bestanden(urteil):
    """`bestanden` darf ``ungeprueft`` nicht durchwinken — sonst gäbe es nur zwei Zustände."""
    assert not modellstand.bestanden({"urteil": urteil})
    assert modellstand.bestanden({"urteil": modellstand.TRAEGT})


def test_ein_vollstaendiger_vermerk_ergibt_traegt(tmp_path):
    """Und die Gegenprobe dazu: Ein gültiger Fall muss auch wirklich durchgehen."""
    befund = modellstand.pruefe(
        _glb(tmp_path, "gut.glb", materialien=("Glas", "Aussenputz"), vermerk=VERMERK,
             erzeuger="KosmoDraw glb_export_runner (pygltflib@v1.16.5)"))

    assert befund["urteil"] == modellstand.TRAEGT, befund
    assert modellstand.bestanden(befund)
    assert befund["erzeuger"] == "KosmoDraw glb_export_runner"
    assert befund["offen"] == [], befund["offen"]


def test_eine_fremde_vertragskennung_wird_nicht_geraten(tmp_path):
    """Unbekannte Fassung ⇒ ungeprüft, nicht «trägt».

    Ein Feldname, den man errät, erzeugt in diesem Ökosystem keine Fehlermeldung, sondern
    eine tote Kante (siehe :mod:`aiimaging.kosmo_naht`). Hier wäre die tote Kante ein
    grünes Abzeichen für eine Datei, die niemand gelesen hat.
    """
    fremd = dict(VERMERK, schema="kosmo.modellstand/v99")
    befund = modellstand.pruefe(
        _glb(tmp_path, "fremd.glb", materialien=("Glas",), vermerk=fremd))

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert any("v99" in g for g in befund["offen"]), befund["offen"]


def test_ein_merkmal_ohne_messvorschrift_gilt_nicht_als_geprueft(tmp_path):
    """Sonst wüchse die Zahl der «geprüften» Merkmale mit jeder Fassung des Erzeugers.

    Ein Merkmal, das wir nicht nachmessen können, als bestanden zu verbuchen, ist dieselbe
    Bauform wie eine Wache, die beim ersten Treffer grün gibt.
    """
    kuenftig = {k: (dict(w) if isinstance(w, dict) else w) for k, w in VERMERK.items()}
    kuenftig["merkmale"] = dict(VERMERK["merkmale"], schattenwurf="2027-01-01")
    befund = modellstand.pruefe(
        _glb(tmp_path, "kuenftig.glb", materialien=("Glas", "Putz"), vermerk=kuenftig))

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert any("schattenwurf" in g for g in befund["offen"]), befund["offen"]


def test_eine_glb_ohne_geometrie_besteht_nicht(tmp_path):
    """Nicht messen ist nicht bestehen — dieselbe Regel wie in `_massstab_gemeldet`."""
    # Ohne Körper gibt es kein Primitiv; die Materialfrage stellt sich gar nicht.
    leer = tmp_path / "gar_nichts.glb"
    leer.write_bytes(_erzeuger().baue_glb(()))
    befund = modellstand.pruefe(leer)

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert befund["maengel"] == [], befund["maengel"]
    assert any("Primitiv" in g for g in befund["offen"]), befund["offen"]


# ======================================================================================
# 3 · Türen — verdächtig ist nicht dasselbe wie falsch
# ======================================================================================

def test_null_tueren_ist_eine_warnung_und_kein_mangel(tmp_path):
    """Der zweite Befund von Lauf 16: 0 IfcDoor bei 700 IfcWindow und 9 Geschossen.

    Ein Plan ohne Türen ist denkbar — darum hält das nichts auf. Aber es steht im Befund,
    und das ist der ganze Unterschied zum Zustand, in dem drei Läufe gefahren sind.
    """
    ohne = _mit_klassen(IfcWall=4905, IfcWindow=700, IfcDoor=0, IfcBuildingStorey=9)
    befund = modellstand.pruefe(
        _glb(tmp_path, "tuerlos.glb", materialien=("Glas", "Putz"), vermerk=ohne))

    assert befund["urteil"] == modellstand.TRAEGT, befund
    assert befund["maengel"] == [], befund["maengel"]
    assert len(befund["warnungen"]) == 1, befund["warnungen"]
    assert "IfcDoor" in befund["warnungen"][0], befund["warnungen"]


def test_mit_tueren_bleibt_die_warnung_aus(tmp_path):
    """Die Gegenprobe — sonst stünde die Warnung bei jedem Auftrag und bedeutete nichts."""
    befund = modellstand.pruefe(
        _glb(tmp_path, "mit_tueren.glb", materialien=("Glas", "Putz"), vermerk=VERMERK))

    assert befund["warnungen"] == [], befund["warnungen"]


def test_ohne_klassenangabe_wird_die_tuerfrage_nicht_beantwortet(tmp_path):
    """Eine glb kennt Dreiecke, keine Türen. Fehlt die Angabe, bleibt die Frage offen.

    Sie wird ausdrücklich **nicht** stillschweigend mit «alles in Ordnung» beantwortet —
    genau das ist die Prüfung, die grün gibt, weil sie nichts kennt.
    """
    ohne = {k: w for k, w in VERMERK.items()}
    ohne["traegt"] = {k: w for k, w in VERMERK["traegt"].items() if k != "ifc_klassen"}
    befund = modellstand.pruefe(
        _glb(tmp_path, "klassenlos.glb", materialien=("Glas", "Putz"), vermerk=ohne))

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert befund["warnungen"] == [], befund["warnungen"]
    assert any("Bauteilklassen" in g for g in befund["offen"]), befund["offen"]


def test_ein_fehlender_schluessel_ist_keine_null(tmp_path):
    """Der feine Unterschied, an dem eine Zählung über das Vorhandene scheitert.

    Ein `collections.Counter` über die Bauteile eines türlosen Modells schweigt über
    `IfcDoor` — der Schlüssel fehlt einfach. Wer daraus «null Türen» liest, hat aus
    Schweigen einen Befund gemacht; wer daraus «alles in Ordnung» liest, erst recht.
    Der Erzeuger schreibt für diese Klassen darum eine ausdrückliche Null, und hier steht
    die Gegenprobe: Ohne sie gibt es keine Warnung, sondern eine offene Frage.
    """
    stumm = _mit_klassen(IfcWall=4905, IfcWindow=700, IfcBuildingStorey=9)   # kein IfcDoor
    befund = modellstand.pruefe(
        _glb(tmp_path, "stumm.glb", materialien=("Glas", "Putz"), vermerk=stumm))

    assert befund["warnungen"] == [], befund["warnungen"]
    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert any("zählt `IfcDoor` nicht mit" in g for g in befund["offen"]), befund["offen"]


# ======================================================================================
# 4 · Die Naht — der Befund muss auf dem Weg liegen, den ein echter Auftrag nimmt
# ======================================================================================
#
# Das ist die Hälfte des Anlasses. `torwaechter` war seit langem gebaut und lief bis zum
# 26.08.2026 auf diesem Weg nirgends; `prompts.bauteilwaechter` genauso. Ein Riegel, der
# nur seine eigenen Tests beurteilt, beurteilt nichts.

def test_der_abholer_meldet_den_modellstand(tmp_path):
    befund = abholer._modellstand_gemeldet(_glb(tmp_path, "grau.glb"))

    assert befund["urteil"] == modellstand.ZURUECK
    assert befund["geprueft"] is False
    assert befund["maengel"], befund


def test_der_abholer_verbucht_ungeprueft_nicht_als_geprueft(tmp_path):
    befund = abholer._modellstand_gemeldet(
        _glb(tmp_path, "ohne_vermerk.glb", materialien=("Glas",)))

    assert befund["urteil"] == modellstand.UNGEPRUEFT
    assert befund["geprueft"] is False, befund


def test_der_abholer_reicht_die_quelle_durch(tmp_path):
    """«Welches Modell fährt hier eigentlich» — die Frage, die bisher nirgends stand."""
    befund = abholer._modellstand_gemeldet(
        _glb(tmp_path, "gut.glb", materialien=("Glas", "Putz"), vermerk=VERMERK))

    assert befund["geprueft"] is True, befund
    assert befund["quelle"]["name"] == "modell.ifc"
    assert len(befund["quelle"]["sha256"]) == 64


def test_eine_unlesbare_datei_geht_nicht_als_bestanden_durch(tmp_path):
    kaputt = tmp_path / "kaputt.glb"
    kaputt.write_bytes(b"nicht glTF")
    befund = abholer._modellstand_gemeldet(kaputt)

    assert befund["geprueft"] is False
    assert befund["urteil"] == modellstand.UNGEPRUEFT
    assert "nicht lesbar" in befund["grund"]


def test_der_grund_traegt_keinen_verzeichnispfad(tmp_path):
    """REGEL 3 — der Befund landet im Auftragsverzeichnis der fremden Oberfläche.

    Die Meldung der glb-Leser nennt den vollen Pfad, und `_ohne_pfade` kürzt nur
    Zeichenketten, die MIT einem Schrägstrich beginnen. Ein Pfad mitten im Satz bliebe
    stehen — genau so ist er beim ersten Anlauf durch zwei Regel-3-Tests gefallen.
    """
    kaputt = tmp_path / "kaputt.glb"
    kaputt.write_bytes(b"nicht glTF")
    grund = abholer._modellstand_gemeldet(kaputt)["grund"]

    assert str(tmp_path) not in grund, grund
    assert "/tmp/" not in grund and "/home/" not in grund, grund
    assert "kaputt.glb" in grund, grund


def test_der_riegel_steht_in_der_registrierung():
    """Ein Riegel ohne Eintrag ist einer, von dem niemand weiss, auf welchem Weg er gilt."""
    eintrag = abholer.RIEGEL["_modellstand_gemeldet"]

    assert eintrag["ort"] == "verarbeiter"
    assert set(eintrag["wege"]) == set(abholer.WEGE)


def test_die_glb_leser_ausnahme_bleibt_eine_ausnahme(tmp_path):
    """`modellstand.pruefe` wirft bei einer kaputten Datei und urteilt nicht.

    Ein Befund «trägt / liegt zurück» über eine Datei, die gar keine glb ist, wäre eine
    Aussage über etwas, das nicht gemessen wurde.
    """
    kaputt = tmp_path / "kaputt.glb"
    kaputt.write_bytes(b"nicht glTF")

    with pytest.raises(glbbox.GlbError):
        modellstand.pruefe(kaputt)


# ======================================================================================
# 5 · Das Merkmal `transparenz` — «BLEND, wo Fenster sind»
# ======================================================================================
#
# DER GEMESSENE ANLASS (02.09.2026). Die ausgeführte glb eines Demolaufs trug 700
# IfcWindow in der Quelle, **3 Materialien** und **kein einziges** mit `alphaMode: BLEND`.
# Der Prüfer sagte damals `ungeprueft` — die Datei trug keinen Vermerk. Die naheliegende
# Reparatur («dann stempeln wir eben») wurde nachgestellt: dieselbe glasfreie Datei, nur
# gestempelt, kam als `traegt`/bestanden zurück, weil `materialien` nur «n_materialien > 0»
# verlangt und drei Materialien da waren.
#
# Diese Abschnitte prüfen darum BEIDE Richtungen und die Grenze dazwischen: rot am Fehler,
# grün am gesunden Fall, still bei einer Quelle ohne Fenster. Ohne die dritte Probe mässe
# die Regel «hat BLEND» statt «hat BLEND, wo Fenster sind», und jeder Rohbau fiele durch.


def _mit_transparenz(**klassen):
    """Ein Vermerk, der `transparenz` FÜHRT — mit den Bauteilzahlen der Quelle."""
    v = _mit_klassen(**klassen)
    v["merkmale"] = dict(VERMERK["merkmale"], transparenz="2026-09-02")
    return v


def test_quelle_mit_fenstern_ohne_blend_liegt_zurueck(tmp_path):
    """Der Fall, um den es geht: Fenster in der Quelle, keine Scheibe in der Datei."""
    befund = modellstand.pruefe(
        _glb(tmp_path, "deckend.glb",
             materialien=("Aussenputz", "Beton"),
             vermerk=_mit_transparenz(IfcWindow=700, IfcDoor=1016)))

    assert befund["urteil"] == modellstand.ZURUECK, befund
    assert not modellstand.bestanden(befund)
    assert befund["gemessen"]["n_materialien_blend"] == 0
    assert any("BLEND" in m for m in befund["maengel"]), befund["maengel"]
    # Der Mangel nennt die Zahl, an der er hängt — sonst ist er nicht nachprüfbar.
    assert any("IfcWindow` = 700" in m for m in befund["maengel"]), befund["maengel"]


def test_dieselbe_szene_mit_einer_scheibe_wird_nicht_beanstandet(tmp_path):
    """Die Gegenprobe zum Mangel: eine Regel, die nur den Fehlerfall kennt, ist blind."""
    befund = modellstand.pruefe(
        _glb(tmp_path, "mit_scheibe.glb",
             materialien=("Aussenputz", ("Glas", "BLEND")),
             vermerk=_mit_transparenz(IfcWindow=700, IfcDoor=1016)))

    assert befund["urteil"] == modellstand.TRAEGT, befund
    assert modellstand.bestanden(befund)
    assert befund["gemessen"]["n_materialien_blend"] == 1


def test_eine_quelle_ohne_fenster_braucht_kein_glas(tmp_path):
    """`IfcWindow` = 0 ist eine MESSUNG, kein Mangel — ein Rohbau ist ein Zwischenstand.

    Ohne diese Probe mässe die Regel «hat BLEND» statt «hat BLEND, wo Fenster sind».
    """
    befund = modellstand.pruefe(
        _glb(tmp_path, "rohbau.glb",
             materialien=("Aussenputz", "Beton"),
             vermerk=_mit_transparenz(IfcWindow=0, IfcDoor=1016)))

    assert befund["urteil"] == modellstand.TRAEGT, befund
    assert befund["maengel"] == []
    assert befund["gemessen"]["n_materialien_blend"] == 0


def test_zaehlt_die_quelle_die_fenster_nicht_bleibt_es_ungeprueft(tmp_path):
    """Ein fehlender Schlüssel und eine Null sind zweierlei — dieselbe Regel wie bei Türen.

    Ob dieses Modell keine Fenster hat oder der Erzeuger sie nur nicht zählt, steht nicht
    in der Datei. Das ist nicht entscheidbar, und nicht entscheidbar ist kein Bestehen.
    """
    ohne_fensterzahl = _mit_transparenz(IfcWall=4905, IfcDoor=1016)
    befund = modellstand.pruefe(
        _glb(tmp_path, "ungezaehlt.glb",
             materialien=("Aussenputz", "Beton"), vermerk=ohne_fensterzahl))

    assert befund["urteil"] == modellstand.UNGEPRUEFT, befund
    assert not modellstand.bestanden(befund)
    assert befund["maengel"] == []
    assert any("IfcWindow" in o for o in befund["offen"]), befund["offen"]


def test_wer_transparenz_nicht_fuehrt_wird_nicht_daran_gemessen(tmp_path):
    """Die Regel gilt nur für Erzeuger, die das Merkmal BEHAUPTEN.

    `VERMERK` (KosmoDraws Fassung) führt `materialien` und `disziplin_layer`, nicht
    `transparenz`. Eine seiner Dateien ohne Scheibe darf davon nicht rot werden —
    sonst würde ein Erzeuger an einer Zusage gemessen, die er nie gegeben hat. Das ist
    dieselbe Linie wie «ein Merkmal ohne Messvorschrift zählt nicht als bestanden»,
    nur von der anderen Seite.
    """
    befund = modellstand.pruefe(
        _glb(tmp_path, "fremder_erzeuger.glb",
             materialien=("Aussenputz", "Beton"),
             vermerk=_mit_klassen(IfcWindow=700, IfcDoor=1016)))

    assert befund["urteil"] == modellstand.TRAEGT, befund
    assert befund["maengel"] == []


def test_die_blend_zahl_wird_an_der_datei_gemessen_nicht_im_vermerk_gelesen(tmp_path):
    """Eine Prüfung, die die Behauptung gegen sich selbst hält, ist keine.

    Der Vermerk darf `n_materialien_blend` nennen — gezählt wird trotzdem der
    `materials`-Block. Hier behauptet er eine Scheibe, die Datei hat keine.
    """
    luegt = _mit_transparenz(IfcWindow=700, IfcDoor=1016)
    luegt["traegt"] = dict(luegt["traegt"], n_materialien_blend=1)
    befund = modellstand.pruefe(
        _glb(tmp_path, "behauptet.glb", materialien=("Aussenputz", "Beton"), vermerk=luegt))

    assert befund["urteil"] == modellstand.ZURUECK, befund
    assert befund["gemessen"]["n_materialien_blend"] == 0
