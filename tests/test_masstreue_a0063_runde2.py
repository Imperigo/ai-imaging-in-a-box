"""A0063 Runde 2 · Mängel aus dem Gegenlesen (31.10.2026) und der neu gefasste Satz 7.

* **Satz 7 (neu):** Nach «Modell laden» zeigt die Visbox nie veraltete Bauteilzahl, Hüllbox
  oder Standpunkte. Die Veraltung wird am **Inhalts-Abdruck** der glb erkannt
  (:func:`aiimaging.projekt.glb_abdruck`, SHA-256 über Inhalt und Grösse), nicht nur an der
  Dateigrösse (``glb_bytes``) — zwei Modelle gleicher Grösse sind nicht dasselbe Modell. Alte
  Mappen ohne Abdruck bekommen keine Zahlen, sondern den Hinweis «Modell neu holen».
* **Mangel 3:** alte Mac-Mappen ohne Fingerabdruck zeigten weiter 30 Teile / 7,1 m.
* **Mangel 7:** ``_engine_des_auftrags`` nahm den Weg nur von Kamera 1.
* **Mangel 10:** bei veralteter Auskunft blieben Hochachse, Box-Vermerk und ``glb_stand`` des
  alten Modells stehen; ``Knotenquelle.swift`` rechnete die Antwort ein zweites Mal selbst.
* **Mangel 11:** ``RENDER_GEFUEHRTE_WEGE`` als feste Texte, mit falschem Kommentar.
* **Mangel 6:** ``render_guided`` fehlte in der Vertrags-Kopie unter ``kosmovis/``.

Swift läuft hier nicht (kein Übersetzer in der Cloud): Die Mac-Regel ist an der Quelle
bewacht, die XCTest-Proben laufen am Mac (Liste Heim-PC).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging import abholer, kosmo_szene, projekt, render

WURZEL = Path(__file__).resolve().parents[1]
MACMAPPE = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Macmappe.swift"
MACPROBE = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests" / "MacmappeTests.swift"
KNOTENQUELLE = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" / "Knotenquelle.swift"
KIZENTRALE = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Claude" / "Kizentrale.swift"
GLBABDRUCK_MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" / "Glbabdruck.swift"
VERTRAG = WURZEL / "kosmovis" / "packages" / "kosmo-contracts" / "src" / "render-result.ts"


# ======================================================================================
# Mangel 7: der Weg des AUFTRAGS, nicht der von Kamera 1
# ======================================================================================

def _urteil(weg):
    return {"engine": {"name": "z-image-turbo", "lizenz": "Apache-2.0", "fuehrung": False,
                       "weg": weg, "lizenz_offen": False}}


def _felder(*wege):
    return kosmo_szene.engine_felder(abholer._engine_des_auftrags([_urteil(w) for w in wege]))


def test_alle_kameras_vom_render_heisst_render_guided_true():
    f = _felder("bild_und_tiefe", "bild_und_tiefe")
    assert f["render_guided"] is True and f["render_guided_mode"] == "bild_und_tiefe"


@pytest.mark.parametrize("wege", [("bild_und_tiefe", "txt2img"), ("txt2img", "bild_und_tiefe")])
def test_eine_kamera_nicht_vom_render_macht_den_auftrag_nicht_render_gefuehrt(wege):
    """Gegenlesen Mangel 7: Kamera 1 vom Render, Kamera 2 nicht — der Auftrag sagte «true»."""
    f = _felder(*wege)
    assert f["render_guided"] is False
    # Ein einziger Weg für den Auftrag wäre für eine der Kameras falsch: das Feld fehlt.
    assert "render_guided_mode" not in f


def test_ein_unbekannter_weg_neben_render_sagt_nicht_true():
    """Meldet eine Kamera keinen Weg, ist «alle vom Render» nicht belegt — kein ``true``,
    aber auch kein erfundenes ``false``: das Feld fehlt (nie ``null``, wie ``guidance_applied``)."""
    f = _felder("bild_und_tiefe", None)
    assert "render_guided" not in f and "render_guided_mode" not in f


def test_verschiedene_wege_vom_render_sind_render_gefuehrt_ohne_einen_modus():
    f = _felder("bild_und_tiefe", "image_edit")
    assert f["render_guided"] is True and "render_guided_mode" not in f


# ======================================================================================
# Mangel 11: die Wege kommen aus der Engstelle, nicht aus festen Texten
# ======================================================================================

def test_render_gefuehrte_wege_sind_die_der_engstelle():
    assert kosmo_szene.RENDER_GEFUEHRTE_WEGE == frozenset(render.MODI_VOM_RENDER)


def test_kein_falscher_kommentar_zu_ki_img2img():
    quelle = (WURZEL / "src" / "aiimaging" / "kosmo_szene.py").read_text(encoding="utf-8")
    assert "dieselben wie ``abholer.KI_IMG2IMG``" not in quelle
    assert 'RENDER_GEFUEHRTE_WEGE = frozenset({"bild_und_tiefe", "image_edit"})' not in quelle


# ======================================================================================
# Satz 7 (Python): die Auskunft trägt den INHALTS-Abdruck ihrer glb
# ======================================================================================

def _werkzeug(datei: str, name: str):
    import importlib.util
    import sys
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


MK_GLB = _werkzeug("make_test_glb.py", "make_test_glb_fuer_a0063_r2")
ALT = (("Wand_Nord", (0, 0, 0), (8, 3, 0.3)), ("Wand_Sued", (0, 0, 5), (8, 3, 5.3)),
       ("Decke", (0, 3, 0), (8, 3.2, 5.3)))
NEU = ALT + (("Dach_Ost", (0, 3.2, 0), (4, 9.1, 5.3)), ("Dach_West", (4, 3.2, 0), (8, 9.1, 5.3)))


@pytest.fixture
def zwilling(tmp_path):
    from aiimaging import arbeitsgang, modellladen
    quelle = tmp_path / "vorlagen" / "Startbau.glb"
    quelle.parent.mkdir()
    quelle.write_bytes(MK_GLB.baue_glb(list(ALT)))
    start = tmp_path / "mappen" / "Startbau"
    arbeitsgang.lege_an(start, quelle)
    erstes = modellladen.lade(start, "Haus.glb", MK_GLB.baue_glb(list(ALT)), ersetzbar=set())
    assert erstes["stand"] == "geladen", erstes
    return start, Path(erstes["mappe"])


def test_die_auskunft_traegt_den_inhalts_abdruck_ihrer_glb(zwilling):
    from aiimaging import knotenweg
    _start, mappe = zwilling
    knoten = knotenweg.mappe_fuer_knoten(mappe)
    glb = knotenweg.glb_der_mappe(mappe)
    ab = projekt.glb_abdruck(glb)
    assert knoten["glb_abdruck"] == {"art": ab["art"], "groesse_byte": ab["groesse_byte"],
                                     "summe": ab["summe"]}
    # Nur, was auf jedem Rechner gleich ist: keine Änderungszeit, kein Zeitpunkt des Vermerks.
    assert "geaendert_ns" not in knoten["glb_abdruck"] and "vermerkt" not in knoten["glb_abdruck"]


def test_nach_modell_laden_ein_anderer_abdruck_der_zum_ausgelieferten_modell_passt(zwilling):
    from aiimaging import knotenweg, mappenpaket, modellladen
    start, mappe = zwilling
    alt = mappenpaket.paket(mappe)["knoten"]["glb_abdruck"]
    modellladen.lade(start, "Haus.glb", MK_GLB.baue_glb(list(NEU)), ersetzbar={mappe})
    neu = mappenpaket.paket(mappe)["knoten"]["glb_abdruck"]
    assert neu["summe"] != alt["summe"]
    # Genau die Datei, die das Paket als `modell.glb` an den Mac ausliefert.
    assert neu["summe"] == projekt.fingerabdruck(knotenweg.glb_der_mappe(mappe))["summe"]


def test_gleiche_groesse_anderer_inhalt_anderer_abdruck(zwilling):
    """Der Kern von Satz 7: ``glb_bytes`` (nur Grösse) bliebe gleich — der Abdruck nicht."""
    from aiimaging import knotenweg
    _start, mappe = zwilling
    glb = knotenweg.glb_der_mappe(mappe)
    vorher = knotenweg.mappe_fuer_knoten(mappe)
    daten = bytearray(glb.read_bytes())
    daten[-1] ^= 0x01  # ein Bit im Binärteil, dieselbe Länge
    glb.write_bytes(bytes(daten))
    nachher = knotenweg.mappe_fuer_knoten(mappe)
    assert nachher["glb_bytes"] == vorher["glb_bytes"]
    assert nachher["glb_abdruck"]["summe"] != vorher["glb_abdruck"]["summe"]


def test_ohne_modell_kein_abdruck(zwilling):
    from aiimaging import knotenweg
    _start, mappe = zwilling
    knotenweg.glb_der_mappe(mappe).unlink()
    assert knotenweg.mappe_fuer_knoten(mappe)["glb_abdruck"] is None


# ======================================================================================
# Satz 7 und Mängel 3, 10 (Swift, an der Quelle bewacht; XCTest am Mac)
# ======================================================================================

def _veraltet_zweig(quelle: str) -> str:
    """Der Teil von ``knotenAntwort``, der eine veraltete Auskunft behandelt."""
    start = quelle.index("let veraltet = auskunftVeraltet(")
    return quelle[start:start + 1500]


def test_die_mappe_am_mac_prueft_den_inhalts_abdruck_nicht_die_groesse():
    quelle = MACMAPPE.read_text(encoding="utf-8")
    assert "glb_abdruck" in quelle and "glbAbdruck" in quelle
    # Die Entscheidung fällt nicht mehr an der Grösse.
    assert 'felder["glb_bytes"]?.alsGanz' not in quelle


def test_der_hinweis_sagt_modell_neu_holen():
    quelle = MACMAPPE.read_text(encoding="utf-8")
    satz = re.search(r"func satzAuskunftVeraltet\(.*?\n    }\n", quelle, re.S)
    assert satz and "Modell neu holen" in satz.group(0)


def test_alte_mappe_ohne_abdruck_ist_nicht_belegt():
    """Mangel 3: Ohne Abdruck in der Auskunft gilt sie NICHT als die des Modells."""
    quelle = MACMAPPE.read_text(encoding="utf-8")
    regel = re.search(r"static func auskunftVeraltet\(.*?\n    }\n", quelle, re.S)
    assert regel, "die Regel steht als eigene Funktion im Kern"
    text = regel.group(0)
    assert "ohne_abdruck" in text and "abdruck_anders" in text and "nicht_lesbar" in text


def test_bei_veraltung_kein_feld_des_alten_modells():
    """Mangel 10: Hochachse, Box-Vermerk und glb_stand gehören zum alten Modell wie die Zahlen."""
    zweig = _veraltet_zweig(MACMAPPE.read_text(encoding="utf-8"))
    for feld in ("bauteile", "huellbox_m", "standpunkte", "hochachse", "glb_stand"):
        assert f'felder["{feld}"] = .null' in zweig, feld
    assert 'felder["huellbox_vermerk"] = .text("")' in zweig


def test_knotenquelle_und_kizentrale_nutzen_dieselbe_antwort():
    """Mangel 10: eine Quelle für zwei Leser — keine zweite Rechnung in ``Knotenquelle``."""
    for datei in (KNOTENQUELLE, KIZENTRALE):
        quelle = datei.read_text(encoding="utf-8")
        assert "Mappenkern.knotenAntwort(mappe, liegt:" in quelle, datei.name
        assert "abdruck: { Glbabdruck.summe(in: ordner) }" in quelle, datei.name
        assert "glbBytes" not in quelle and "attributesOfItem" not in quelle, datei.name


def test_der_mac_rechnet_den_abdruck_wie_der_heim_pc():
    """Dieselben Grenzen wie :func:`projekt.fingerabdruck`: ganz bis 64 MiB, sonst Anfang und
    Ende je 64 KiB, die Grösse als Text dahinter."""
    kern = MACMAPPE.read_text(encoding="utf-8")
    assert projekt.VOLLE_PRUEFUNG_BIS_BYTE == 64 * 1024 * 1024
    assert projekt.FENSTER_BYTE == 64 * 1024
    assert "abdruckVollBis = 64 * 1024 * 1024" in kern
    assert "abdruckFenster = 64 * 1024" in kern
    mac = GLBABDRUCK_MAC.read_text(encoding="utf-8")
    assert "import CryptoKit" in mac and "SHA256()" in mac
    assert "Mappenkern.abdruckBereiche" in mac and "Mappenkern.abdruckSchluss" in mac


def test_xctest_proben_fuer_den_mac_liegen():
    probe = MACPROBE.read_text(encoding="utf-8")
    for name in ("testVeralteteAuskunftNachNeuemModell", "testAlteMappeOhneAbdruckZeigtKeineZahlen",
                 "testAbdruckBereicheWieAmHeimPC"):
        assert f"func {name}(" in probe, name


# ======================================================================================
# Mangel 6: die Vertrags-Kopie kennt render_guided
# ======================================================================================

def test_die_vertragskopie_kennt_render_guided():
    quelle = VERTRAG.read_text(encoding="utf-8")
    assert re.search(r"^\s*render_guided: z\.boolean\(\)\.optional\(\),", quelle, re.M)
    assert re.search(r"^\s*render_guided_mode: z\.string\(\)\.optional\(\),", quelle, re.M)


def test_die_abweichung_steht_in_herkunft():
    import json
    herkunft = json.loads((WURZEL / "kosmovis" / "HERKUNFT.json").read_text(encoding="utf-8"))
    grund = herkunft["geaendert"]["packages/kosmo-contracts/src/render-result.ts"]
    assert "render_guided" in grund and "A0063" in grund
