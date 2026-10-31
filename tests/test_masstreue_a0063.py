"""A0063 · Masstreue-Prüfung ehrlich (Demolauf 31.10.2026, Befunde 3, 4, 6, 7).

Owner 31.10.2026: «Immer vom Render.» Die Prüfung «jedes KI-Bild auf den Pässen» braucht
darum am Ergebnis ein Feld, das genau das sagt — und Messungen, die eine Stimmung nicht für
einen Fehler halten.

* **(4)** ``guidance_applied`` heisst *klassifikatorfreie Führung* (C35) — bei
  ``z-image-turbo`` immer ``false``, auch wenn ``bild_und_tiefe`` vom Render gerechnet wurde.
  Neu daneben: ``render_guided`` (vom Render-Bild gestartet) und ``render_guided_mode``.
* **(7)** Nach «Modell laden» in eine bestehende Mappe: Bauteile, Hüllbox und Standpunkte des
  NEUEN Modells — und ein Fingerabdruck der glb (``glb_bytes``), an dem die Mappe am Mac eine
  veraltete Auskunft erkennt.
* **(3)** «Fenster gehalten» an einem Morgenbild (dunkler, wärmer): kein Fehlalarm mehr.
* **(6)** Prompt nennt Sichtbeton, der Materialknoten Backstein: eine Warnung am Lauf.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, bildschreiben, kosmo_szene, render

WURZEL = Path(__file__).resolve().parents[1]


# ======================================================================================
# (4) Das Führungs-Feld sagt den gerechneten Weg
# ======================================================================================

def _lauf(tmp_path, *, bildeingang: float | None, gerechnet: str | None = None,
          status: str = render.STATUS_OK):
    """Ein Lauf durch ``render.rendere`` mit einer Attrappe — ohne Gewichte, ohne GPU.

    ``status`` (Runde 2, Mangel 4): Seit der Engstelle (A0065) endet ein Lauf ohne Beauty-Render
    oder mit einem anderen gerechneten Weg OHNE Bild; die Probe sagt, welcher Ausgang erwartet ist.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    tiefe = bildschreiben.schreibe_graustufen_png(tmp_path / "tiefe.png", [0.5] * 4, 2, 2)
    beauty = bildschreiben.schreibe_farb_png(tmp_path / "beauty.png", [(1, 2, 3)] * 4, 2, 2)

    def modell(parameter):
        ziel = parameter["ausgabe_png"]
        Path(ziel).write_bytes(Path(parameter["depth_png"]).read_bytes())
        return {"bild_png": ziel, "hinweise": (), "modus_bestellt": parameter["modus"],
                "modus_gerechnet": gerechnet or parameter["modus"]}

    kw = {"beauty_png": str(beauty), "bildeingang_staerke": bildeingang} \
        if bildeingang is not None else {}
    auftrag = render.RenderAuftrag(depth_png=str(tiefe), prompt="a house",
                                   ausgabe_png=str(tmp_path / "aus.png"), **kw)
    ergebnis = render.rendere(auftrag, modell=modell)
    assert ergebnis["status"] == status, ergebnis
    if status != render.STATUS_OK:
        assert ergebnis["bild_png"] is None, ergebnis
    return ergebnis, kosmo_szene.engine_felder(abholer._engine_aus(ergebnis))


def test_bild_und_tiefe_meldet_render_guided_true(tmp_path):
    """Der Demolauf 31.10.: bild_und_tiefe 0,7 gerechnet — das Ergebnis muss es sagen."""
    ergebnis, felder = _lauf(tmp_path, bildeingang=0.7)
    assert ergebnis["modus_gerechnet"] == render.MODUS_BILD_UND_TIEFE
    assert felder["render_guided"] is True
    assert felder["render_guided_mode"] == render.MODUS_BILD_UND_TIEFE


def test_ohne_render_als_start_meldet_render_guided_false(tmp_path):
    """Reines txt2img (nur die Tiefe steuert, Start aus Rauschen) ist NICHT «vom Render».

    Runde 2, Mangel 4: Seit A0065 weist die Engstelle diesen Lauf ab, bevor das Modell rechnet —
    kein Bild, und weil kein Weg gerechnet wurde, behauptet das Ergebnis auch keinen: kein
    ``render_guided: true``, das Feld fehlt (nie ``null``). Das Feld selbst sagt für einen
    gemeldeten Weg ``txt2img`` weiter ``false`` (unten, an der Naht ``engine_felder``)."""
    e, felder = _lauf(tmp_path, bildeingang=None, gerechnet=render.MODUS_TXT2IMG,
                      status=render.STATUS_ABGELEHNT)
    assert e["error"] == render.masstreue_satz_ohne_beauty()
    assert "render_guided" not in felder and "render_guided_mode" not in felder
    gemeldet = kosmo_szene.engine_felder(abholer._engine_aus({
        "backbone": "z-image-turbo", "modus_gerechnet": render.MODUS_TXT2IMG, "parameter": {}}))
    assert gemeldet["render_guided"] is False
    assert gemeldet["render_guided_mode"] == render.MODUS_TXT2IMG


def test_rueckfall_auf_txt2img_meldet_false_auch_wenn_bild_und_tiefe_bestellt(tmp_path):
    """Bestellt bild_und_tiefe, gerechnet txt2img: zählt, was GERECHNET wurde."""
    # Runde 2, Mangel 4: die Engstelle (A0065) liefert kein Bild — und meldet den Lauf mit dem
    # gerechneten Weg als NICHT render-geführt.
    e, felder = _lauf(tmp_path, bildeingang=0.7, gerechnet=render.MODUS_TXT2IMG,
                      status=render.STATUS_FEHLER)
    assert e["error"] == render.masstreue_satz_engstelle(render.MODUS_BILD_UND_TIEFE,
                                                         render.MODUS_TXT2IMG)
    assert felder["render_guided"] is False
    assert felder["render_guided_mode"] == render.MODUS_TXT2IMG


def test_guidance_applied_bleibt_die_klassifikatorfreie_fuehrung():
    """Der Vertrag C35 bleibt unverändert: z-image-turbo ohne CFG sagt weiter ``false`` —
    neben ``render_guided: true``. Zwei Fragen, zwei Felder."""
    felder = kosmo_szene.engine_felder(abholer._engine_aus({
        "backbone": "z-image-turbo", "modus_gerechnet": render.MODUS_BILD_UND_TIEFE,
        "parameter": {"fuehrung_angewandt": False}}))
    assert felder["guidance_applied"] is False
    assert felder["render_guided"] is True


def test_unbekannter_weg_laesst_das_feld_weg_und_nie_null():
    """Meldet das Bildmodell keinen Weg, fehlt das Feld (wie guidance_applied: nie null)."""
    felder = kosmo_szene.engine_felder(abholer._engine_aus({
        "backbone": "z-image-turbo", "parameter": {}}))
    assert "render_guided" not in felder and "render_guided_mode" not in felder


def test_image_edit_zaehlt_als_vom_render():
    felder = kosmo_szene.engine_felder(abholer._engine_aus({
        "backbone": "qwen-image-edit-2511", "modus_gerechnet": render.MODUS_IMAGE_EDIT,
        "parameter": {}}))
    assert felder["render_guided"] is True


# ======================================================================================
# (7) «Modell laden» in eine bestehende Mappe: die Auskunft des NEUEN Modells
# ======================================================================================

def _werkzeug(datei: str, name: str):
    import importlib.util
    import sys
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


MK_GLB = _werkzeug("make_test_glb.py", "make_test_glb_fuer_a0063")

#: Die alte Fassung: drei Teile, 3,2 m hoch (glTF-Koordinaten, Y oben) — synthetisch.
ALT = (("Wand_Nord", (0, 0, 0), (8, 3, 0.3)), ("Wand_Sued", (0, 0, 5), (8, 3, 5.3)),
       ("Decke", (0, 3, 0), (8, 3.2, 5.3)))
#: Die neue Fassung («Variante A»): fünf Teile, First auf 9,1 m.
NEU = ALT + (("Dach_Ost", (0, 3.2, 0), (4, 9.1, 5.3)), ("Dach_West", (4, 3.2, 0), (8, 9.1, 5.3)))


@pytest.fixture
def zwilling(tmp_path):
    """Ein Zwilling am Heim-PC für die Mappe am Mac — angelegt wie über «Datei laden …»."""
    from aiimaging import arbeitsgang, modellladen
    quelle = tmp_path / "vorlagen" / "Startbau.glb"
    quelle.parent.mkdir()
    quelle.write_bytes(MK_GLB.baue_glb(list(ALT)))
    start = tmp_path / "mappen" / "Startbau"
    arbeitsgang.lege_an(start, quelle)
    erstes = modellladen.lade(start, "Haus.glb", MK_GLB.baue_glb(list(ALT)), ersetzbar=set())
    assert erstes["stand"] == "geladen", erstes
    return start, Path(erstes["mappe"])


def _hoehe(box) -> float:
    return round(box[1][2] - box[0][2], 2)


def test_neue_fassung_im_zwilling_liefert_bauteile_und_huellbox_des_neuen_modells(zwilling):
    """Befund 7: vorher 30 Bauteile / 7,1 m, nachher sollte es 38 / 9,1 m sein. Hier 3 → 5."""
    from aiimaging import mappenpaket, modellladen
    start, mappe = zwilling
    vorher = mappenpaket.paket(mappe)["knoten"]
    assert vorher["bauteile"] == 3 and _hoehe(vorher["huellbox_m"]) == 3.2

    zweites = modellladen.lade(start, "Haus.glb", MK_GLB.baue_glb(list(NEU)), ersetzbar={mappe})
    assert zweites["stand"] == "geladen" and zweites["ersetzt"] is True, zweites
    assert Path(zweites["mappe"]) == mappe

    nachher = mappenpaket.paket(mappe)["knoten"]
    assert nachher["bauteile"] == 5
    assert _hoehe(nachher["huellbox_m"]) == 9.1
    # Die Standpunkte rechnen mit der neuen Hüllbox — dieselben wie frisch aus der neuen glb.
    assert nachher["standpunkte"] is not None and vorher["standpunkte"] is not None
    assert nachher["standpunkte"] != vorher["standpunkte"]


def test_die_auskunft_traegt_den_fingerabdruck_ihrer_glb(zwilling):
    """Woran die Mappe am Mac erkennt, dass ihre Auskunft zu einem anderen Modell gehört:
    ``glb_bytes`` ist die Grösse genau der Datei, aus der Bauteile und Hüllbox gelesen sind —
    dieselbe, die das Paket als ``modell.glb`` ausliefert."""
    from aiimaging import knotenweg, mappenpaket, modellladen
    start, mappe = zwilling
    alt = mappenpaket.paket(mappe)
    modellladen.lade(start, "Haus.glb", MK_GLB.baue_glb(list(NEU)), ersetzbar={mappe})
    neu = mappenpaket.paket(mappe)
    modell = [d for d in neu["dateien"] if d["art"] == "modell"][0]
    assert neu["knoten"]["glb_bytes"] == modell["bytes"]
    assert neu["knoten"]["glb_bytes"] == knotenweg.glb_der_mappe(mappe).stat().st_size
    assert alt["knoten"]["glb_bytes"] != neu["knoten"]["glb_bytes"]


def test_ohne_modell_kein_fingerabdruck(zwilling):
    from aiimaging import knotenweg
    _start, mappe = zwilling
    knotenweg.glb_der_mappe(mappe).unlink()
    assert knotenweg.mappe_fuer_knoten(mappe)["glb_bytes"] is None


MACMAPPE = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Macmappe.swift"
MACPROBE = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests" / "MacmappeTests.swift"


def test_die_mappe_am_mac_prueft_den_fingerabdruck():
    """Am Mac liest ``mappe_lesen`` (und die Knotenansicht) die Auskunft aus ``mappe.json``.
    Passt ``glb_bytes`` nicht zur ``modell.glb`` daneben, ist sie veraltet: Bauteile, Hüllbox
    und Standpunkte werden nicht als die des Modells ausgegeben (Swift, ohne Übersetzer hier —
    die Regel ist bewacht, die XCTest-Probe läuft am Mac)."""
    quelle = MACMAPPE.read_text(encoding="utf-8")
    # Runde 2 (Satz 7 neu gefasst): entschieden wird am Inhalts-Abdruck, nicht an der Grösse.
    assert "glb_abdruck" in quelle and "satzAuskunftVeraltet" in quelle
    assert "glbAbdruck" in quelle
    probe = MACPROBE.read_text(encoding="utf-8")
    assert "testVeralteteAuskunftNachNeuemModell" in probe


# ======================================================================================
# (3) Die Glasflächen-QA hält eine Stimmung nicht für übermaltes Glas
# ======================================================================================
#
# Demolauf 31.10.2026: «Morgen» (dunkel, wolkig) meldete nur 13 % Glas erhalten, die Fenster
# waren aber sichtbar. Die Ursache: Die Regel verglich das KI-Bild mit dem Grundbild in
# absoluten Farben. Dunkelt die Stimmung das ganze Bild ab, liegt ein gehaltener Glaspunkt näher
# an der (ebenso abgedunkelten) KI-Fassade als am hellen Glas des Grundbilds.

from aiimaging import varianten  # noqa: E402

B, H = 40, 30
GLAS_ID, WAND_ID = (10, 200, 30), (200, 10, 10)
#: Sichtbeton und spiegelndes, hellblaues Glas (wie das Grundbild in auf-20261023-346).
BETON = (160, 158, 155)
GLAS = (158, 178, 190)
HIMMEL = (150, 190, 230)
TABELLE = [{"index": 0, "name": "Sichtbeton", "farbe_srgb_8bit": list(WAND_ID)},
           {"index": 1, "name": "Glas", "farbe_srgb_8bit": list(GLAS_ID)}]
#: «Morgen, wolkig»: alles auf knapp die Hälfte abgedunkelt, eine Spur kühler.
MORGEN = (0.45, 0.46, 0.48)


def _haus(x, y):
    return 5 <= x < 35 and 5 <= y < 28


def _fenster(x, y):
    """Fünf Einzelfenster im OG und EG."""
    return (y in range(9, 14) or y in range(18, 23)) and (x - 7) % 6 in (0, 1, 2) and 7 <= x < 34


def _bild(farbe_von):
    return [farbe_von(x, y) for y in range(H) for x in range(B)]


def _grundbild(x, y):
    if not _haus(x, y):
        return HIMMEL
    return GLAS if _fenster(x, y) else BETON


def _dunkel(farbe, faktor=MORGEN):
    return tuple(round(k * f) for k, f in zip(farbe, faktor))


def _ki_morgen(x, y):
    """Dasselbe Haus im Morgenlicht — die Fenster sind sichtbar und gehalten."""
    return _dunkel(_grundbild(x, y))


def _ki_morgen_uebermalt(x, y):
    """Im Morgenlicht, aber die KI hat die Fenster mit Beton zugemalt."""
    return _dunkel(HIMMEL if not _haus(x, y) else BETON)


def _kennung(x, y):
    if not _haus(x, y):
        return (0, 0, 0)
    return GLAS_ID if _fenster(x, y) else WAND_ID


def _messe(ki):
    return varianten.fenster_gehalten(ki, _bild(_grundbild), _bild(_kennung),
                                      varianten.glasfarben(TABELLE), maske=_bild(_haus))


def test_morgenbild_mit_sichtbaren_fenstern_ohne_fehlalarm():
    befund = _messe(_bild(_ki_morgen))
    assert befund["n_glas"] > 0 and befund["trennung"] >= varianten.FENSTER_TRENNUNG_MIN
    assert befund["anteil"] >= 0.95, befund
    assert befund["gehalten"] is True


def test_morgenbild_mit_uebermalten_fenstern_faellt_weiter_auf():
    """Der Ausgleich der Stimmung darf das, wofür die Prüfung da ist, nicht verdecken."""
    befund = _messe(_bild(_ki_morgen_uebermalt))
    assert befund["gehalten"] is False and befund["anteil"] <= 0.05, befund


def test_ohne_stimmung_misst_die_regel_wie_bisher():
    befund = _messe(_bild(_grundbild))
    assert befund["anteil"] == 1.0 and befund["gehalten"] is True


def test_der_ausgleich_steht_im_befund():
    """Was ausgeglichen wurde, steht da (je Kanal) — nachprüfbar am Gerät."""
    befund = _messe(_bild(_ki_morgen))
    ausgleich = befund["ton_ausgleich"]
    assert len(ausgleich) == 3 and all(2.0 <= k <= 2.3 for k in ausgleich), ausgleich


# ======================================================================================
# (6) Prompt und Materialknoten widersprechen sich: eine Warnung am Lauf
# ======================================================================================
#
# Demolauf 31.10.2026: Prompt «Sichtbeton, Fichte, Holzschalung», der Graph aber Fassade =
# Backstein, Dach unverbunden. Kein Fehler im Graph — aber das Bild zeigte Backstein, und
# niemand sagte, dass der Prompt etwas anderes wollte. Ohne Variante gilt der Materialknoten
# (Befund 337, `test_sonst_bleibt_die_materialwahl`); das bleibt so. Neu kommt der Satz.

from aiimaging import stimmung  # noqa: E402

BACKSTEIN = {"fassade": {"id": "backstein"}}


@pytest.fixture
def stoffdateien(tmp_path, monkeypatch):
    from test_knoten_material import _texturen
    ordner = tmp_path / "himmel"
    ordner.mkdir(exist_ok=True)
    for p, e in stimmung.STIMMUNGEN.items():
        for a in ("2k", "4k"):
            (ordner / stimmung.dateiname(p, e["hdri"], a)).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))
    _texturen(tmp_path, monkeypatch)


def _lies(prompt, materialien=BACKSTEIN, **vis):
    render_ = {"samples": 8, "environment": {"preset": "morgen"}}
    if materialien is not None:
        render_["materialien"] = materialien
    szene = {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
             "render": render_, "style": {"prompt": prompt}, "vis": vis}
    return kosmo_szene.lies_szene(szene, streng=False)


def _widerspruch(s):
    return [w for w in s["warnungen"] if w.startswith(kosmo_szene.SATZ_MATERIAL_WIDERSPRUCH)]


def test_prompt_sichtbeton_gegen_knoten_backstein_warnt(stoffdateien):
    s = _lies("Ein Haus am Hang, Fassade aus Sichtbeton")
    assert not s["maengel"], s["maengel"]
    assert s["materialien"]["fassade"]["id"] == "backstein", "die Wahl bleibt"
    saetze = _widerspruch(s)
    assert len(saetze) == 1, s["warnungen"]
    assert "Backstein" in saetze[0] and "concrete" in saetze[0]
    w = s["material_widerspruch"]
    assert w["fassade"] == "backstein" and w["familien_prompt"] == ["beton"]


def test_der_demolauf_mehrere_stoffe_gegen_backstein_warnt(stoffdateien):
    """Der Wortlaut aus dem Demolauf: drei Stoffe, keiner ist Backstein.

    «Fichte» und «Holzschalung» stehen nicht im Glossar und bleiben deutsch (die Übersetzung
    sagt es selbst) — erkannt wird darum nur der Beton. Das genügt für den Widerspruch; die
    Lücke im Glossar ist als eigener Befund gemeldet (A0063), hier nicht gebaut."""
    s = _lies("Ein Haus am Hang, Fassade aus Sichtbeton und Fichte, Holzschalung")
    saetze = _widerspruch(s)
    assert len(saetze) == 1, s["warnungen"]
    assert s["material_widerspruch"]["familien_prompt"] == ["beton"]
    assert any("fichte" in w.lower() for w in s["warnungen"]), "die Glossarluecke ist sichtbar"


@pytest.mark.parametrize("prompt, materialien", [
    ("Ein Haus am Hang, Backsteinfassade", BACKSTEIN),            # derselbe Stoff
    ("Ein Haus am Hang, Fassade aus Klinker", BACKSTEIN),          # dieselbe Familie
    ("Ein Haus am Hang", BACKSTEIN),                               # kein Stoff im Prompt
    ("Ein Haus am Hang, Fassade aus Sichtbeton", None),            # kein Materialknoten
    ("Ein Haus am Hang, Fassade aus Sichtbeton und Backstein", BACKSTEIN),  # einer passt
])
def test_kein_widerspruch_kein_satz(stoffdateien, prompt, materialien):
    s = _lies(prompt, materialien)
    assert _widerspruch(s) == [], s["warnungen"]
    assert s.get("material_widerspruch") is None


def test_nur_grundlage_rechnet_kein_ki_bild_und_warnt_nicht(stoffdateien):
    s = _lies("Ein Haus am Hang, Fassade aus Sichtbeton", skip=True)
    assert _widerspruch(s) == []


def test_der_satz_kommt_ins_ergebnis():
    """Am Lauf heisst: im Ergebnis, unter den Hinweisen (wie der Satz der Stoff-Variante)."""
    satz = f"{kosmo_szene.SATZ_MATERIAL_WIDERSPRUCH}: Probe."
    saetze = kosmo_szene.ergebnis_saetze_der_szene({"material_widerspruch": {"satz": satz}})
    assert saetze == [satz]
    assert "material_widerspruch" in kosmo_szene.DURCHGEREICHT


def test_am_lauf_steht_die_warnung_im_ergebnis(tmp_path, monkeypatch, stoffdateien):
    """Der ganze Weg mit Attrappen: Auftrag → Lauf → Ergebnis (angewandt und Hinweise)."""
    from test_grundlage_varianten import _mit_schoenbild
    from test_kettenlauf_26august import _kette, _lauf
    from test_material_der_variante_337 import _in_ablage
    _protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    ordner = _in_ablage(tmp_path, "vis-1-aaaaaa", prompt="Ein Haus am Hang, Fassade aus Sichtbeton",
                        materialien=BACKSTEIN)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = antwort["ergebnis"]
    assert ergebnis["angewandt"]["material_widerspruch"]["fassade"] == "backstein"
    saetze = [h for h in ergebnis["qa"]["verdict"].get("hinweise") or ()
              if str(h).startswith(kosmo_szene.SATZ_MATERIAL_WIDERSPRUCH)]
    assert len(saetze) == 1, ergebnis["qa"]["verdict"].get("hinweise")
