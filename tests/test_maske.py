"""Die Bauwerksmaske — und vor allem die Stelle, an der sie sich weigert.

Was hier geprüft wird, und was nicht
------------------------------------
Der leichte Teil ist das Sortieren von Farben. Der schwierige, und der eigentliche Grund
für dieses Modul, ist die **Geländeregel**: Sie ist eine Setzung, sie kann danebengreifen,
und wenn sie danebengreift, sieht das Ergebnis genauso aus wie ein Erfolg — eine Maske mit
vielen Punkten. Der Unterschied ist nur, dass der halbe Boden darin steckt.

Die Tests hier drehen sich deshalb um drei Zusicherungen:

1. Die Regel greift auf den gemessenen Fall (``Boden_Platte``) und schneidet den Boden
   heraus, nicht das Bauwerk.
2. Greift sie **nicht**, gibt es keine Maske — ``None``, nicht „alles ausser Hintergrund".
3. Der Aufrufer kann die Regel ersetzen und die Erwartung erklären, und beides wirkt.

Die Testdaten sind synthetisch und entstehen in den Tests selbst (Regel 3): kleine
Kunstbilder aus wenigen Kennfarben, geschrieben mit
``bildschreiben.schreibe_farb_png``, gelesen mit ``bildlesen.lies_png_farben``. Kein
Blender, keine GPU, keine echten Projektdaten. Die Zahlen aus
``docs/MASKE_2026-08-21.md`` (44 604 Bauwerkspunkte, 17,02 %) tauchen hier bewusst
**nicht** als Erwartungswerte auf — sie stammen aus einem Renderlauf, den dieser Test
nicht wiederholt, und sie hier hinzuschreiben ergäbe einen Test, der eine Messung
behauptet, die er nicht durchführt.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import maske as m
from aiimaging.bildlesen import BildError, lies_png_farben
from aiimaging.bildschreiben import schreibe_farb_png, schreibe_graustufen_png

# Die Palette des Runners für die ersten Indizes — hsv_to_rgb(i * 0.618…, 0.85, 1.00),
# auf 8 Bit gerundet. Dieselben Werte, die in `docs/MASKE_2026-08-21.md` in der
# gemessenen Tabelle stehen. Sie stehen hier als Konstanten und werden nicht nachgerechnet:
# Ein Test, der die Formel des Runners nachbaut, prüft die Formel gegen sich selbst.
BODEN = (255, 38, 38)
SLAB = (38, 101, 255)
WAND_A = (165, 255, 38)
WAND_B = (255, 38, 228)


def eintrag(index: int, name: str, farbe, quelle: str = "material") -> dict:
    """Ein Eintrag der ``material_id_tabelle``, wie ihn der Runner schreibt."""
    return {
        "index": index,
        "name": name,
        "quelle": quelle,
        "farbe_srgb": [k / 255.0 for k in farbe],
        "farbe_srgb_8bit": list(farbe),
    }


@pytest.fixture
def tabelle() -> list[dict]:
    """Ein Gelände plus drei Bauteile — die Gestalt der gemessenen Szene, klein."""
    return [
        eintrag(0, "Boden_Platte", BODEN),
        eintrag(1, "IfcSlab_2eYuY4S8", SLAB),
        eintrag(2, "IfcWall_0QOeb014", WAND_A),
        eintrag(3, "IfcWall_1FMjVFy0", WAND_B),
    ]


@pytest.fixture
def bild() -> list[tuple[int, int, int]]:
    """4×2 Bildpunkte: 2 Hintergrund, 3 Boden, 3 Bauwerk (Slab, Wand A, Wand B)."""
    schwarz = m.HINTERGRUND_FARBE
    return [
        schwarz, schwarz, SLAB,  WAND_A,
        BODEN,   BODEN,   BODEN, WAND_B,
    ]


# ======================================================================================
# Die Regel selbst
# ======================================================================================

def test_die_regel_trifft_den_gemessenen_geländenamen_und_nicht_die_bauteile():
    """Der einzige Fall, an dem der Weg belegt ist: `Boden_Platte` gegen `IfcWall_…`."""
    assert m.ist_gelaende("Boden_Platte") is True
    assert m.ist_gelaende("IfcWall_0QOeb014") is False
    assert m.ist_gelaende("IfcSlab_2eYuY4S8") is False


def test_die_regel_vergleicht_ohne_ruecksicht_auf_gross_und_kleinschreibung():
    """Ein Exporteur, der `BODEN_PLATTE` schreibt, ändert nichts an der Sache."""
    assert m.ist_gelaende("BODEN_PLATTE") is True
    assert m.ist_gelaende("  Boden_Platte  ") is True


def test_ifcsite_wird_mit_angehaengter_guid_erkannt_ein_bauteil_aber_nicht():
    """Der Stern in `ifcsite*` ist für die GUID da, die der Exportweg anhängt.

    Er darf deshalb hinten fangen — und nur dort. `MeinIfcSite` ist ein anderer Name.
    """
    assert m.ist_gelaende("IfcSite_1a2b3c4d") is True
    assert m.ist_gelaende("MeinIfcSite_1a2b") is False


def test_kein_teilstringvergleich_ein_geschossboden_ist_kein_gelaende():
    """`"boden" in "Bodenplatte 2.OG"` wäre wahr — und schnitte ein Geschoss heraus."""
    assert m.ist_gelaende("Bodenplatte 2.OG") is False
    assert m.ist_gelaende("Boden_Platte_Untergeschoss") is False


def test_die_regel_faengt_kein_gelaender():
    """Der Grund, aus dem `gelaende` in der Vorgabe ohne Stern steht.

    `gelaende*` fienge `Geländer` mit — ein Handlauf am Bauwerk, der damit zum Boden
    erklärt würde und lautlos aus der Maske verschwände.
    """
    assert m.ist_gelaende("Gelaende") is True
    assert m.ist_gelaende("Geländer") is False
    assert m.ist_gelaende("Gelaender_Attika") is False


def test_ein_eigenes_muster_ersetzt_die_vorgabe_vollstaendig():
    """Ersetzen heisst ersetzen: Die Vorgabe darf nicht heimlich danebenstehen bleiben."""
    eigenes = ("*_terrain",)
    assert m.ist_gelaende("nordhang_terrain", eigenes) is True
    assert m.ist_gelaende("Boden_Platte", eigenes) is False


def test_ohne_muster_ist_nichts_gelaende():
    """Eine leere Regel ist zulässig — sie erklärt nur nichts zum Gelände."""
    assert m.ist_gelaende("Boden_Platte", ()) is False


# ======================================================================================
# Die Maske aus Farben und Tabelle
# ======================================================================================

def test_der_boden_faellt_heraus_und_die_bauteile_bleiben_drin(bild, tabelle):
    """Der Kernfall — und geprüft wird die Maske Punkt für Punkt, nicht ihre Summe.

    Eine Summe von 3 wäre auch dann richtig, wenn die Maske drei **falsche** Punkte
    trüge — etwa die drei Bodenpunkte.
    """
    ergebnis = m.bauwerksmaske(bild, tabelle)
    assert ergebnis["maske"] == [
        False, False, True,  True,
        False, False, False, True,
    ]


def test_die_vier_sorten_werden_getrennt_gezaehlt(bild, tabelle):
    """Hintergrund, Gelände, Bauwerk, Unbekannt — und die Summe ist das ganze Bild."""
    ergebnis = m.bauwerksmaske(bild, tabelle)
    assert (ergebnis["n_hintergrund"], ergebnis["n_gelaende"],
            ergebnis["n_bauwerk"], ergebnis["n_unbekannt"]) == (2, 3, 3, 0)
    assert ergebnis["n_bildpunkte"] == 8
    assert ergebnis["anteil_bauwerk"] == pytest.approx(3 / 8)


def test_das_ergebnis_nennt_die_namen_die_es_wohin_sortiert_hat(bild, tabelle):
    """Ohne diese Listen wäre die Regel eine Blackbox — und Blackboxen prüft niemand."""
    ergebnis = m.bauwerksmaske(bild, tabelle)
    assert ergebnis["gelaende_namen"] == ["Boden_Platte"]
    assert ergebnis["bauwerk_namen"] == [
        "IfcSlab_2eYuY4S8", "IfcWall_0QOeb014", "IfcWall_1FMjVFy0",
    ]


def test_das_ergebnis_traegt_die_verwendete_regel_mit(bild, tabelle):
    """Eine Zahl ohne ihre Regel ist später nicht mehr einzuordnen."""
    ergebnis = m.bauwerksmaske(bild, tabelle, gelaende_muster=("boden_platte",))
    assert ergebnis["muster"] == ["boden_platte"]
    assert "material_id" in ergebnis["methode"].lower() \
        or "material-id" in ergebnis["methode"].lower()


def test_das_ergebnis_nennt_ob_ueber_material_oder_objektnamen_sortiert_wurde(bild):
    """`quelle=objekt` heisst: Das Modell brachte gar keine Materialien mit.

    Wer eine Objekt-Maske für eine Material-Maske hält, sucht den Fehler später an der
    falschen Stelle.
    """
    objekt_tabelle = [
        eintrag(0, "Boden_Platte", BODEN, quelle="objekt"),
        eintrag(1, "IfcSlab_2eYuY4S8", SLAB, quelle="objekt"),
        eintrag(2, "IfcWall_0QOeb014", WAND_A, quelle="objekt"),
        eintrag(3, "IfcWall_1FMjVFy0", WAND_B, quelle="objekt"),
    ]
    assert m.bauwerksmaske(bild, objekt_tabelle)["quelle"] == ["objekt"]


def test_ein_eigenes_muster_verschiebt_die_grenze_im_bild(bild, tabelle):
    """Die Regel ist nicht Zierde: Ein anderes Muster ergibt eine andere Maske.

    Hier gilt die Slab als Gelände — dann muss ihr Bildpunkt aus der Maske fallen und
    der Boden hineinkommen.
    """
    ergebnis = m.bauwerksmaske(bild, tabelle, gelaende_muster=("ifcslab*",))
    assert ergebnis["maske"] == [
        False, False, False, True,
        True,  True,  True,  True,
    ]
    assert ergebnis["gelaende_namen"] == ["IfcSlab_2eYuY4S8"]


def test_hintergrund_ist_exakt_schwarz_und_ein_dunkler_punkt_ist_es_nicht(tabelle):
    """(0,0,0) heisst „nichts getroffen". (1,1,1) heisst „unbekannte Farbe".

    Der Unterschied ist der Grund, aus dem der Runner das Dithering abschaltet: Mit
    Dithering sprang selbst der schwarze Grund zwischen 0 und 1, und aus 5 Farben wurden
    gemessene 19.
    """
    ergebnis = m.bauwerksmaske([(0, 0, 0), (1, 1, 1)], tabelle)
    assert (ergebnis["n_hintergrund"], ergebnis["n_unbekannt"]) == (1, 1)


def test_eine_unbekannte_farbe_zaehlt_nicht_zum_bauwerk_und_wird_gemeldet(tabelle):
    """Raten wäre die Alternative — und eine Kantenmischfarbe ist kein Bauteil."""
    ergebnis = m.bauwerksmaske([SLAB, (7, 200, 91)], tabelle)
    assert ergebnis["maske"] == [True, False]
    assert ergebnis["n_unbekannt"] == 1
    assert any("(7, 200, 91)" in w for w in ergebnis["warnungen"])


def test_ohne_unbekannte_farben_steht_darueber_auch_nichts_in_den_warnungen(bild, tabelle):
    """Gegenstück zum Test darüber — und die Gegenprobe steht **hier**, nicht dort.

    Die Vakuumprobe hat diese Zusicherung als schwach gemeldet: `not any(...)` über einer
    Sammlung, die auch leer sein könnte. Die Gegenprobe gab es, aber sie prüfte eine
    **andere** Zeichenfolge (die Farbe statt „Tabelle nicht"). Wäre der Warntext geändert
    worden, hätte dieser Test vakuum-wahr bestanden und der andere wäre gefallen — zwei
    Tests am selben Mechanismus, die einander nicht decken.

    Jetzt steht beides hier: dieselbe Zeichenfolge, einmal erwartet und einmal nicht.
    """
    ohne = m.bauwerksmaske([SLAB, SLAB], tabelle)
    mit = m.bauwerksmaske([SLAB, (7, 200, 91)], tabelle)

    assert ohne["n_unbekannt"] == 0
    assert not any("Tabelle nicht" in w for w in ohne["warnungen"])
    # Und der Beleg, dass diese Zeichenfolge überhaupt vorkommen KANN:
    assert mit["n_unbekannt"] == 1
    assert any("Tabelle nicht" in w for w in mit["warnungen"])

def test_greift_die_regel_nicht_gibt_es_keine_maske(bild):
    """Der Kern: Keine Maske ist besser als eine, in der heimlich der Boden steckt.

    Die Tabelle nennt den Boden `Bodenflaeche` — ein Name, den die Vorgabe nicht kennt.
    Ohne diese Weigerung stünden hier 6 statt 3 Bauwerkspunkte, doppelt so viele wie
    richtig, und niemand sähe es dem Ergebnis an.
    """
    fremde = [
        eintrag(0, "Bodenflaeche", BODEN),
        eintrag(1, "IfcSlab_2eYuY4S8", SLAB),
        eintrag(2, "IfcWall_0QOeb014", WAND_A),
        eintrag(3, "IfcWall_1FMjVFy0", WAND_B),
    ]
    ergebnis = m.bauwerksmaske(bild, fremde)
    assert ergebnis["maske"] is None
    assert ergebnis["gelaende_erkannt"] is False
    assert ergebnis["n_bauwerk"] == 6          # der Beleg, dass der Boden mitzählte
    assert any("gelaende_erwartet=False" in w for w in ergebnis["warnungen"])


def test_wer_die_geländefreie_szene_erklaert_bekommt_die_maske(bild):
    """`gelaende_erwartet=False` ist eine Erklärung des Aufrufers, kein Schalter.

    Sie ist der einzige Weg zu einer Maske ohne erkanntes Gelände — und dass es einen
    gibt, ist wichtig: Eine Szene ohne Boden ist ein zulässiger Fall.
    """
    ohne_boden = [
        eintrag(0, "IfcSlab_2eYuY4S8", SLAB),
        eintrag(1, "IfcWall_0QOeb014", WAND_A),
        eintrag(2, "IfcWall_1FMjVFy0", WAND_B),
    ]
    farben = [SLAB, WAND_A, WAND_B, m.HINTERGRUND_FARBE]
    ergebnis = m.bauwerksmaske(farben, ohne_boden, gelaende_erwartet=False)
    assert ergebnis["maske"] == [True, True, True, False]
    assert ergebnis["gelaende_erkannt"] is False
    assert any("gelaende_erwartet" in w for w in ergebnis["warnungen"])


def test_greift_die_regel_widerspricht_das_der_erklaerung_und_wird_gesagt(bild, tabelle):
    """Der Aufrufer sagt „kein Gelände", die Regel findet eines. Beides kann nicht stimmen.

    Die Maske entsteht trotzdem — die Regel gewinnt, weil Herausnehmen die vorsichtigere
    Handlung ist —, aber der Widerspruch bleibt nicht unerwähnt.
    """
    ergebnis = m.bauwerksmaske(bild, tabelle, gelaende_erwartet=False)
    assert ergebnis["maske"] is not None
    assert ergebnis["n_bauwerk"] == 3
    assert any("Boden_Platte" in w and "kein Gelände" in w
               for w in ergebnis["warnungen"])


def test_eine_leere_maske_ist_eine_maske_und_wird_gemeldet(tabelle):
    """Alles Boden, kein Bauwerk: gültig gemessen, und trotzdem eine Auffälligkeit.

    Hier ist `None` **falsch** — es wurde gemessen, das Ergebnis ist bloss leer.
    """
    ergebnis = m.bauwerksmaske([BODEN, BODEN, m.HINTERGRUND_FARBE], tabelle)
    assert ergebnis["maske"] == [False, False, False]
    assert ergebnis["n_bauwerk"] == 0
    assert any("Kein einziger Bildpunkt" in w for w in ergebnis["warnungen"])


def test_ohne_bildpunkte_gibt_es_einen_fehler_und_keine_leere_maske(tabelle):
    """Eine leere Liste sähe aus wie „kein Bauwerk gefunden" und wäre „nicht gemessen"."""
    with pytest.raises(m.MaskeError, match="nichts zu maskieren"):
        m.bauwerksmaske([], tabelle)


def test_ohne_tabelle_gibt_es_einen_fehler(bild):
    """Ohne Namen greift keine Regel — und ohne Regel gibt es keine Bauwerksmaske."""
    with pytest.raises(m.MaskeError, match="Leere material_id_tabelle"):
        m.bauwerksmaske(bild, [])


# ======================================================================================
# Kaputte Tabellen
# ======================================================================================

def test_ein_eintrag_ohne_farbe_wird_nicht_aus_dem_index_zurueckgerechnet(bild):
    """Die Farbe liesse sich aus dem Goldenen Winkel herleiten — und das wäre Raten.

    Die Palette ist eine Entscheidung des Runners und darf sich ändern, ohne dass dieses
    Modul davon erfährt. Die Tabelle ist der Schlüssel, nicht die Formel.
    """
    kaputt = [{"index": 0, "name": "Boden_Platte", "quelle": "material"}]
    with pytest.raises(m.MaskeError, match="farbe_srgb_8bit"):
        m.bauwerksmaske(bild, kaputt)


def test_eine_farbe_ausserhalb_von_0_bis_255_wird_abgewiesen(bild):
    with pytest.raises(m.MaskeError, match="0..255"):
        m.bauwerksmaske(bild, [eintrag(0, "Boden_Platte", (0, 300, 12))])


def test_ein_material_in_der_hintergrundfarbe_wird_abgewiesen(bild):
    """Sonst wäre nicht mehr unterscheidbar, ob ein schwarzer Punkt etwas zeigt oder nichts."""
    with pytest.raises(m.MaskeError, match="Hintergrundfarbe"):
        m.bauwerksmaske(bild, [eintrag(0, "IfcWall_0QOeb014", (0, 0, 0))])


def test_zwei_gleichfarbige_eintraege_diesseits_und_jenseits_der_regel_sind_ein_fehler(bild):
    """Der eine Kollisionsfall, der wirklich unlösbar ist.

    Zwei gleichfarbige Wände stören niemanden. Eine Wand und ein Boden in derselben
    Farbe lassen sich nicht mehr trennen — und eine Seite zu wählen hiesse zu raten.
    """
    kollision = [
        eintrag(0, "Boden_Platte", SLAB),
        eintrag(1, "IfcWall_0QOeb014", SLAB),
    ]
    with pytest.raises(m.MaskeError, match="Farbkollision"):
        m.bauwerksmaske(bild, kollision)


def test_zwei_gleichfarbige_bauteile_sind_nur_eine_warnung(tabelle):
    """Für die Maske folgenlos — beide sind Bauwerk. Für eine Auswertung je Material nicht."""
    kollision = [
        eintrag(0, "Boden_Platte", BODEN),
        eintrag(1, "IfcWall_0QOeb014", WAND_A),
        eintrag(2, "IfcWall_1FMjVFy0", WAND_A),
    ]
    ergebnis = m.bauwerksmaske([WAND_A, BODEN], kollision)
    assert ergebnis["maske"] == [True, False]
    assert any("dieselbe Kennfarbe" in w for w in ergebnis["warnungen"])


def test_ein_bildpunkt_ohne_drei_kanaele_wird_abgewiesen(tabelle):
    """Ein RGBA-Tupel durchzulassen hiesse, Alpha als Blau zu lesen."""
    with pytest.raises(m.MaskeError, match="statt 3 Werte"):
        m.bauwerksmaske([(38, 101, 255, 255)], tabelle)


# ======================================================================================
# Der Report
# ======================================================================================

def test_die_tabelle_kommt_aus_dem_report_auf_der_platte(tmp_path, tabelle):
    pfad = tmp_path / "blender-report.json"
    pfad.write_text(json.dumps({"status": "ok", "material_id_tabelle": tabelle}),
                    encoding="utf-8")
    assert m.tabelle_aus_report(pfad) == tabelle


def test_ein_lauf_ohne_material_id_pass_liefert_keine_tabelle(tmp_path):
    """`--ohne-material-id` schreibt eine leere Tabelle — das ist kein Bauwerk ohne Punkte."""
    pfad = tmp_path / "blender-report.json"
    pfad.write_text(json.dumps({"status": "ok", "material_id_tabelle": []}),
                    encoding="utf-8")
    with pytest.raises(m.MaskeError, match="ohne-material-id"):
        m.tabelle_aus_report(pfad)


def test_ein_report_ohne_das_feld_wird_nicht_als_leer_gedeutet(tmp_path):
    """Ein fehlendes Feld ist etwas anderes als ein leeres — und wird anders gemeldet."""
    pfad = tmp_path / "blender-report.json"
    pfad.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    with pytest.raises(m.MaskeError, match="kein Feld 'material_id_tabelle'"):
        m.tabelle_aus_report(pfad)


def test_kaputtes_json_wird_gemeldet_und_nicht_uebergangen(tmp_path):
    pfad = tmp_path / "blender-report.json"
    pfad.write_text("{das ist kein json", encoding="utf-8")
    with pytest.raises(m.MaskeError, match="kein gültiges JSON"):
        m.tabelle_aus_report(pfad)


def test_ein_fehlender_report_wird_gemeldet(tmp_path):
    with pytest.raises(m.MaskeError, match="lässt sich nicht lesen"):
        m.tabelle_aus_report(tmp_path / "gibtesnicht.json")


# ======================================================================================
# Der ganze Weg: PNG schreiben → lesen → maskieren
# ======================================================================================

def test_der_weg_von_der_datei_zur_maske_traegt(tmp_path, bild, tabelle):
    """Der Rundlauf über eine echte Datei — Schreiber, Leser und Maske zusammen.

    Geprüft wird die Maske Punkt für Punkt und nicht nur ihre Länge: Eine Maske, die um
    eine Zeile verschoben ist, hätte dieselbe Länge und wäre unbrauchbar.
    """
    png = schreibe_farb_png(tmp_path / "material_id.png", bild, 4, 2)
    report = tmp_path / "blender-report.json"
    report.write_text(json.dumps({"material_id_tabelle": tabelle}), encoding="utf-8")

    ergebnis = m.bauwerksmaske_aus_lauf(png, report)
    assert ergebnis["maske"] == [
        False, False, True,  True,
        False, False, False, True,
    ]
    assert (ergebnis["breite"], ergebnis["hoehe"]) == (4, 2)
    assert ergebnis["material_id_png"] == str(png)


def test_der_report_darf_auch_schon_geladen_sein(tmp_path, bild, tabelle):
    """Wer den Report ohnehin im Speicher hat, soll ihn nicht erst schreiben müssen."""
    png = schreibe_farb_png(tmp_path / "material_id.png", bild, 4, 2)
    ergebnis = m.bauwerksmaske_aus_lauf(png, {"material_id_tabelle": tabelle})
    assert ergebnis["n_bauwerk"] == 3


def test_der_dateiweg_reicht_die_geländeregel_durch(tmp_path, bild, tabelle):
    """Eine Regel, die nur den einen von zwei Einstiegen erreicht, ist keine Regel.

    Diese Zusicherung fehlte zuerst: In der Mutationsprobe liess sich die Weitergabe von
    `gelaende_muster` in `bauwerksmaske_aus_lauf` streichen, ohne dass ein Test rot wurde.
    """
    png = schreibe_farb_png(tmp_path / "material_id.png", bild, 4, 2)
    ergebnis = m.bauwerksmaske_aus_lauf(
        png, {"material_id_tabelle": tabelle}, gelaende_muster=("ifcslab*",))
    assert ergebnis["gelaende_namen"] == ["IfcSlab_2eYuY4S8"]
    assert ergebnis["maske"] == [
        False, False, False, True,
        True,  True,  True,  True,
    ]


def test_der_dateiweg_reicht_die_erklaerung_zur_geländefreien_szene_durch(tmp_path):
    """Dieselbe Lücke, andere Leitung — auch sie überlebte die erste Mutationsprobe.

    Ohne die Weitergabe stünde hier `None`, denn die Vorgabe erwartet Gelände und die
    Regel findet in dieser Szene keines.
    """
    ohne_boden = [
        eintrag(0, "IfcSlab_2eYuY4S8", SLAB),
        eintrag(1, "IfcWall_0QOeb014", WAND_A),
    ]
    png = schreibe_farb_png(tmp_path / "material_id.png",
                            [SLAB, WAND_A, m.HINTERGRUND_FARBE, m.HINTERGRUND_FARBE], 2, 2)
    ergebnis = m.bauwerksmaske_aus_lauf(
        png, {"material_id_tabelle": ohne_boden}, gelaende_erwartet=False)
    assert ergebnis["maske"] == [True, True, False, False]


def test_die_zeilenreihenfolge_ist_von_oben_nach_unten(tmp_path, tabelle):
    """Indexgleichheit mit der Tiefenkarte hängt daran — und ein Versatz fällt sonst nicht auf.

    Erste Zeile ganz Bauwerk, zweite ganz Boden. Wäre die Reihenfolge gekippt, käme die
    Maske gespiegelt zurück — bei gleicher Anzahl True.
    """
    farben = [WAND_A, WAND_A, BODEN, BODEN]
    png = schreibe_farb_png(tmp_path / "material_id.png", farben, 2, 2)
    ergebnis = m.bauwerksmaske_aus_lauf(png, {"material_id_tabelle": tabelle})
    assert ergebnis["maske"] == [True, True, False, False]


def test_ein_16_bit_bild_wird_abgewiesen_statt_heruntergerechnet(tmp_path, tabelle):
    """Aus 16 Bit auf 8 Bit zu runden hiesse zu raten, welche der 256 Stufen gemeint war."""
    png = schreibe_graustufen_png(tmp_path / "grau16.png", [0.0, 1.0], 2, 1, bittiefe=16)
    with pytest.raises(BildError, match="Bittiefe 16"):
        m.bauwerksmaske_aus_lauf(png, {"material_id_tabelle": tabelle})


# ======================================================================================
# Der Farbleser — er darf die Kanäle nicht zusammenrechnen
# ======================================================================================

def test_der_farbleser_gibt_die_bytes_zurueck_die_geschrieben_wurden(tmp_path):
    """Byte für Byte: Die Zuordnung zur Tabelle ist ein Gleichheitsvergleich, kein Näherung."""
    farben = [BODEN, SLAB, WAND_A, WAND_B, (0, 0, 0), (1, 2, 3)]
    png = schreibe_farb_png(tmp_path / "farben.png", farben, 3, 2)
    gelesen, breite, hoehe = lies_png_farben(png)
    assert gelesen == farben
    assert (breite, hoehe) == (3, 2)


def test_zwei_kennfarben_gleicher_luminanz_bleiben_unterscheidbar(tmp_path, tabelle):
    """Der Grund, aus dem es `lies_png_farben` neben `lies_png_luminanz` gibt.

    (255, 38, 228) und (38, 255, 219) haben nach Rec.709 fast dieselbe Helligkeit — über
    die Luminanz gelesen wären zwei Bauteile lautlos dasselbe. Hier ist das eine ein
    bekanntes Bauteil und das andere eine unbekannte Farbe.
    """
    unbekannt = (38, 255, 219)
    png = schreibe_farb_png(tmp_path / "farben.png", [WAND_B, unbekannt], 2, 1)
    gelesen, _, _ = lies_png_farben(png)
    assert gelesen == [WAND_B, unbekannt]

    ergebnis = m.bauwerksmaske(gelesen, tabelle)
    assert ergebnis["maske"] == [True, False]
    assert ergebnis["n_unbekannt"] == 1


def test_ein_graustufenbild_wird_verlustfrei_aufgefaltet(tmp_path):
    """Der Leser urteilt nicht — ob ein graues Bild als Material-ID taugt, ist nicht
    seine Frage, sondern die von `maske`."""
    png = schreibe_graustufen_png(tmp_path / "grau8.png", [0.0, 1.0], 2, 1, bittiefe=8)
    gelesen, _, _ = lies_png_farben(png)
    assert gelesen == [(0, 0, 0), (255, 255, 255)]


# ======================================================================================
# Der Farbschreiber
# ======================================================================================

def test_der_farbschreiber_weist_zuviele_und_zuwenige_werte_ab(tmp_path):
    """Ein Bild mit fehlenden Werten wäre stillschweigend verschoben."""
    from aiimaging.bildschreiben import SchreibError
    with pytest.raises(SchreibError, match="3 Farben für 2×2"):
        schreibe_farb_png(tmp_path / "x.png", [BODEN, SLAB, WAND_A], 2, 2)


def test_der_farbschreiber_beschneidet_nicht_sondern_meldet(tmp_path):
    """Aus 256 stillschweigend 255 zu machen erzeugte zwei Materialien mit einer Kennfarbe."""
    from aiimaging.bildschreiben import SchreibError
    with pytest.raises(SchreibError, match="0..255"):
        schreibe_farb_png(tmp_path / "x.png", [(0, 256, 0)], 1, 1)


def test_der_farbschreiber_nimmt_kein_rgba_tupel(tmp_path):
    """Vier Werte je Punkt in eine RGB-Datei zu schreiben verschiebt das ganze Bild.

    Es fiele nicht einmal auf: Die Datei bliebe lesbar, die Farben wären nur ab dem
    ersten Punkt um einen Kanal verrutscht. Diese Zusicherung fehlte zuerst — die
    Mutationsprobe hat die Prüfung ohne einen roten Test wegnehmen können.
    """
    from aiimaging.bildschreiben import SchreibError
    with pytest.raises(SchreibError, match="4 statt 3 Werte"):
        schreibe_farb_png(tmp_path / "x.png", [(38, 101, 255, 255)], 1, 1)


def test_der_farbschreiber_nimmt_keine_anteile_in_0_bis_1(tmp_path):
    """`(1.0, 0.15, 0.15)` sieht aus wie eine Farbe und ist keine Kennung.

    Ohne diese Prüfung landete 0.15 als 0 in der Datei, und zwei Kennfarben wären eine.
    """
    from aiimaging.bildschreiben import SchreibError
    with pytest.raises(SchreibError, match="ganze Zahlen"):
        schreibe_farb_png(tmp_path / "x.png", [(1.0, 0.15, 0.15)], 1, 1)


# ======================================================================================
# Prozessgrenze
# ======================================================================================

def test_das_modul_kommt_ohne_blender_und_ohne_oberflaeche_aus():
    """Regeln 2 und 4, geprüft am Quelltext statt am Vertrauen."""
    from pathlib import Path
    quelle = (Path(m.__file__)).read_text(encoding="utf-8")
    assert "import bpy" not in quelle
    for verboten in ("tkinter", "PyQt", "streamlit", "gradio"):
        assert f"import {verboten}" not in quelle


# ======================================================================================
# Warum der Maskenweg ausfiel — gemeldet von der HomeStation, 26.08.2026
# ======================================================================================
#
# Ihr Befund: In allen vier Laeufen des Tages standen `rho_maske`, `kante` und
# `paarurteil` auf None, obwohl `material_id.png` vorlag und der Maskenbefund einen
# Bauwerksanteil meldete. Folge: Die in `GEMESSENE_POLARITAET` hinterlegte Polaritaet
# wird nie angewandt (sie wird nur IM Maskenweg gelesen), und der Score faellt auf
# `abs(spearman)` zurueck — in dem Modus besteht ein Bild mit VERTAUSCHTER Tiefe das Tor.
#
# Hier nachgemessen: Die Maske wird sehr wohl BERECHNET und dann verworfen.

@pytest.fixture
def tabelle_ohne_gelaende() -> list[dict]:
    """Ein reines Gebaeude-IFC — der eine IfcSite darin traegt keine Geometrie."""
    return [
        eintrag(1, "IfcSlab_2eYuY4S8", SLAB),
        eintrag(2, "IfcWall_0QOeb014", WAND_A),
        eintrag(3, "IfcWall_1FMjVFy0", WAND_B),
    ]


def test_die_maske_wird_berechnet_und_dann_verworfen(bild, tabelle_ohne_gelaende):
    """**Der Kern des Befundes.** Nicht «konnte nicht», sondern «wurde nicht behalten».

    Ohne erkanntes Gelände und mit ``gelaende_erwartet=True`` gibt `bauwerksmaske` die
    Maske als ``None`` zurück — und meldet im selben Atemzug die gezählten
    Bauwerkspunkte. Das ist kein Widerspruch, sondern Absicht: Findet die Regel kein
    Gelände, ist nicht entscheidbar, ob keines da ist oder ob sie es verfehlt hat. Im
    zweiten Fall steckte der ganze Boden als Bauwerk in der Maske.

    *Die Zusicherung hält fest, dass die Zahlen trotzdem dastehen* — sonst sähe ein
    verworfener Lauf aus wie einer, der gar nichts messen konnte.
    """
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=True)

    assert befund["maske"] is None
    assert befund["n_bauwerk"] > 0, (
        "Die Bauwerkspunkte müssen im Befund stehen, auch wenn die Maske verworfen wird.")
    assert befund["gelaende_erkannt"] is False


def test_der_grund_nennt_die_folge_und_die_abhilfe(bild, tabelle_ohne_gelaende):
    """Ein Ausstieg, der nur sagt DASS, ist schwer zu finden.

    Die HomeStation hat es wörtlich verlangt: *«eine Zeile im Bericht — Maskenweg
    übersprungen, weil … — wäre schon die halbe Miete.»*
    """
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=True)
    grund = " ".join(befund.get("warnungen") or ()) + str(befund.get("grund") or "")

    assert "Maskenweg" in grund, "Die Folge gehört in denselben Satz wie die Ursache."
    assert "--kein-gelaende" in grund, (
        "Die Abhilfe gehört dazu — und zwar in der Form, die ein Betreiber wirklich tippt.")


def test_mit_der_erklaerung_des_aufrufers_bleibt_die_maske(bild, tabelle_ohne_gelaende):
    """Die Gegenprobe. Ohne sie prüfte der Test oben nur, dass irgendetwas None ist."""
    befund = m.bauwerksmaske(bild, tabelle_ohne_gelaende, gelaende_erwartet=False)

    assert befund["maske"] is not None
    assert sum(befund["maske"]) == befund["n_bauwerk"]


def test_mit_benanntem_gelaende_bleibt_die_maske_auch_ohne_erklaerung(bild, tabelle):
    """**Und das ist seit dem 26.08.2026 wieder der Normalfall.**

    Bis zu jenem Tag überlebte der IFC-Name den glb-Export nicht: Die Geländeplatte hiess
    drüben ``IfcSlab_<GlobalId>``, die Regel bekam nichts zu lesen, und die Maske wurde
    **auch bei Szenen mit Gelände** verworfen. Seit der Knotenname den Namen mitträgt,
    trifft die Regel wieder — und ein Treffer dieses Tests ist der Beleg dafür.
    """
    befund = m.bauwerksmaske(bild, tabelle, gelaende_erwartet=True)

    assert befund["gelaende_erkannt"] is True
    assert befund["maske"] is not None
    assert sum(befund["maske"]) == befund["n_bauwerk"]


def test_die_kehrseite_der_mitgetragenen_namen_ist_benannt():
    """**Was der Anschluss des IFC-Namens am 26.08.2026 zusätzlich einfängt.**

    Die Wortregel greift seither auf den Namen — das ist ihr Zweck, und ohne ihn wurde die
    Maske überall verworfen. Aber ``site`` ist eines der Wörter, und damit gilt eine Wand
    namens ``Site-A`` als Gelände.

    *Die sichere Richtung ist trotzdem diese:* Gelände **in** der Maske ist der schlimmere
    Fehler — auf einer Bodenszene erreichte weisses Rauschen dort 0,72. Dieser Test hält
    den Zustand fest, **damit er eine Entscheidung bleibt und keine Überraschung.**
    """
    assert m.ist_gelaende("IfcWall_Site-A_abc") is True
    assert m.ist_gelaende("IfcSlab_Site_Boundary_abc") is True

    # Und was die Wortgrenzen weiterhin NICHT fangen — die Gegenprobe:
    for harmlos in ("IfcWall_Sitzbank_abc", "IfcSlab_Terrasse_abc",
                    "IfcWall_Gelaendegleich_abc", "IfcWall_Nordfassade_abc"):
        assert m.ist_gelaende(harmlos) is False, harmlos


def test_die_namen_der_zweiten_szene_loesen_keinen_fehlalarm_aus():
    """**Gegen echte Namen geprüft, nicht gegen ausgedachte.**

    Die HomeStation hat am 26.08.2026 ihr Demohaus angeboten — 511 Bauteile, eigener
    Blender-Export, alle Knoten benannt. Ihre Namen laufen durch **diese** Regel, sobald
    die Szene unsere Kette benutzt.

    Der heikle Fall steht mitten drin: der Baustoff **`Terrassenbelag`**. Er enthält
    ``Terrass…`` und ist trotzdem kein Gelände — die Wortgrenzen halten. Ohne sie wäre die
    ganze Terrasse eines elfgeschossigen Hauses aus der Bauwerksmaske gefallen.

    *Diese Zusicherung ist der billigste Teil der Übernahme einer fremden Szene:* Sie
    kostet nichts und beantwortet vorab die Frage, die sonst erst an einem schiefen Bild
    auffiele.
    """
    namen = ("DECKE_01__t000", "STUETZE_HOLZ_G05_P07", "FASS_N_BRUEST_03",
             "Beton_Decke", "Beton_Kern", "Beton_Querwand", "Beton_Erdbebenwand",
             "Beton_Treppe", "Holz_Stuetze", "Trennwand_Leichtbau", "Terrassenbelag",
             "Metall_Fassade", "Metall_Bruestung", "Glas_Fassade")

    fehlalarme = [n for n in namen if m.ist_gelaende(n)]

    assert not fehlalarme, (
        f"Diese Bauteile der zweiten Szene gälten als Gelände und fielen aus der "
        f"Bauwerksmaske: {fehlalarme}")
