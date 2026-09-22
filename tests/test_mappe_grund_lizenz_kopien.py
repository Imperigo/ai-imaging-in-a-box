"""Grund, Lizenz und eigene Kopien — drei Auskünfte, die auf dem Weg in die Mappe
verlorengingen oder verklebten.

**Die Befunde (Durchsicht 22.09.2026)**, alle in :mod:`aiimaging.arbeitsgang`:

(a) **Der Grund des Urteils stand am Bild als ``None``.** ``_urteil_zu`` las
    ``ausgaben["grund"]``; die Geometrieprüfung (``tiefenschaetzer.qa_gegen_soll`` über
    ``kette.qa_ausfuehrer``) liefert ihren Satz aber unter ``begruendung``. Nachgestellt
    am **echten** Ausführer mit einer Attrappe als Schätzer: ``begruendung`` gesetzt,
    ``grund`` fehlt. Nur der Weg «von Hand bearbeitet» (``nicht_anwendbar``) schreibt
    ``grund``.

(b) **Lizenz und Mängel der Bildstufe fielen weg.** ``render._ergebnis`` liefert beide
    neben den sechs Messfeldern; in der Projektdatei kam keines an. Bei einem Projekt,
    dessen Regel 1 die Lizenz ist, ist das die Auskunft, die später niemand mehr
    rekonstruiert.

(c) **Geteilte Objekte.** ``projekt.vermerke_bild`` kopiert die Herkunft nur flach. Die
    Messung am Bild war darum **dasselbe Objekt** wie die Messung im Lauf, und die
    Hinweisliste zusätzlich dieselbe wie in ``modus_abweichungen``. Im Arbeitsspeicher
    änderte eine Berichtigung an einer Stelle still die andere — und wer danach
    speichert, schreibt beide Fassungen.

**Wie geprüft wird:** über den Produktweg :func:`aiimaging.arbeitsgang.rechne`, mit
Attrappen statt Blender, Gewichten und GPU — Render und Prüfung aber, wo es um ihre
Felder geht, als **echte Ausführer** der Kette (``kette.render_ausfuehrer``,
``kette.qa_ausfuehrer``) mit eingesetztem Modell. Eine Attrappe, die das Feld selbst
erfindet, bewiese nur, dass die Attrappe es kennt. Gelesen wird die Mappe **von der
Platte**.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, bildlesen, bildschreiben, kette, projekt
from aiimaging.kette import ART_GEOMETRIE, ART_MULTIPASS, ART_QA, ART_RENDER

FERN = 1e10
BREITE, HOEHE = 50, 20
#: Die Soll-Tiefenkarte: 600 Punkte Bauwerk, der Rest Hintergrund.
SOLL = [1.0 + i / 1000 if i < 600 else FERN for i in range(BREITE * HOEHE)]


# ------------------------------------------------------------------- die Attrappen

def _schreibe_png(pfad: Path) -> Path:
    """Ein **gültiges** Graustufen-PNG — ``bildlesen.pruefe_png`` liest Prüfsummen."""
    return bildschreiben.schreibe_graustufen_png(pfad, [0.5] * 4, 2, 2)


class Werkstatt:
    """Geometrie und Multipass als Attrappen, Render und Prüfung als echte Ausführer.

    ``mit_maske`` legt dem Multipass einen Material-ID-Pass bei. Ohne ihn setzt
    ``qa_gegen_soll`` ``bestanden`` auf ``None`` (Owner-Entscheid 26.08.2026: der
    Maskenweg ist ein zweites Tor) — das ist der zweite geprüfte Fall.
    """

    def __init__(self, *, mit_maske: bool = True, qa=None) -> None:
        self.mit_maske = mit_maske
        self.qa = qa

    def tabelle(self) -> dict:
        return {
            ART_GEOMETRIE: self.geometrie,
            ART_MULTIPASS: self.multipass,
            ART_RENDER: kette.render_ausfuehrer(modell=self.bildmodell),
            ART_QA: self.qa or kette.qa_ausfuehrer(
                modell=lambda parameter: [-wert for wert in SOLL]),
        }

    def geometrie(self, *, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        out_dir = Path(out_dir)
        ergebnis = {"status": "ok",
                    "depth_png": str(_schreibe_png(out_dir / "tiefe_norm.png")),
                    "beauty_png": str(_schreibe_png(out_dir / "beauty.png")),
                    "depth_exr": "t.exr"}
        if self.mit_maske:
            wand, boden = (165, 255, 38), (255, 38, 38)
            farben = [wand if i < 600 else (0, 0, 0) for i in range(BREITE * HOEHE)]
            for i in range(600, 650):
                farben[i] = boden
            ergebnis["material_id_png"] = str(bildschreiben.schreibe_farb_png(
                out_dir / "material_id.png", farben, BREITE, HOEHE))
            ergebnis["material_id_tabelle"] = [
                {"index": 0, "name": "Wand_Nord", "farbe_srgb_8bit": list(wand),
                 "quelle": "material"},
                {"index": 1, "name": "Boden_Platte", "farbe_srgb_8bit": list(boden),
                 "quelle": "material"}]
        return ergebnis

    @staticmethod
    def bildmodell(parameter: dict) -> dict:
        ziel = parameter["ausgabe_png"]
        _schreibe_png(Path(ziel))
        return {"bild_png": ziel, "hinweise": [], "schritte_gerechnet": None}


@pytest.fixture
def glb(tmp_path):
    """Ein gültiges glb — Weg «durchgereicht», also ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


@pytest.fixture
def mappe(tmp_path, glb, monkeypatch):
    # DIE SOLL-KARTE OHNE EXR: Die Tiefe liest `bildlesen.tiefen_aus_report` aus einer
    # EXR, und die gibt es ohne Blender nicht. Ersetzt wird nur das Lesen — geschätzt,
    # markiert und geurteilt wird echt.
    monkeypatch.setattr(bildlesen, "tiefen_aus_report",
                        lambda report, **kw: (SOLL, BREITE, HOEHE))
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Testhaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


def _von_der_platte(wurzel) -> dict:
    """Die Mappe **neu geöffnet**, nicht das Wörterbuch aus dem Arbeitsspeicher."""
    return projekt.oeffne(wurzel)["projekt"]


# ------------------------------------------------ (a) · der Grund steht am Bild

def test_der_satz_der_geometriepruefung_steht_am_bild(mappe):
    """Der Wächter für Befund (a): gemessen, bestanden — und der Grund steht da.

    Verglichen wird mit dem, was **der echte Ausführer** in diesem Lauf geliefert hat,
    nicht mit einem Text, den der Test sich ausdenkt.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt().tabelle())

    qa = ergebnis["lauf"]["knoten"][kette.KNOTEN_QA]["ausgaben"]
    assert qa["bestanden"] is True, qa.get("begruendung")
    assert qa.get("begruendung"), "die Prüfung selbst begründet ihr Urteil"

    bild = _von_der_platte(mappe)["bilder"][0]
    assert bild["geometrie_bestanden"] is True
    assert bild["herkunft"]["grund"] is not None, (
        "ein gemessenes Urteil ohne seinen Satz — genau der Befund vom 22.09.2026")
    assert bild["herkunft"]["grund"] == qa["begruendung"]


def test_ein_urteil_none_traegt_den_vorbehalt_vor_dem_score_satz(mappe):
    """Ohne Maskenweg setzt die Prüfung ``bestanden`` auf ``None`` — und begründet mit
    dem Score («… ≥ Schwelle»).

    Allein neben ein nicht gemessenes Bild gestellt, liest sich dieser Satz wie ein
    bestandenes Urteil. Am Bild muss darum **zuerst** stehen, dass es keines gibt.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt(mit_maske=False).tabelle())

    qa = ergebnis["lauf"]["knoten"][kette.KNOTEN_QA]["ausgaben"]
    assert qa["bestanden"] is None
    bild = _von_der_platte(mappe)["bilder"][0]
    grund = bild["herkunft"]["grund"]
    assert bild["geometrie_gemessen"] is False
    assert grund.startswith(f"Die Prüfung {kette.KNOTEN_QA} hat gerechnet, aber kein "
                            f"Urteil gefällt — NICHT GEMESSEN"), grund
    assert qa["begruendung"] in grund, "was die Prüfung meldet, bleibt lesbar"


def test_der_handeingriff_behaelt_seinen_eigenen_satz(mappe):
    """Der Weg «von Hand bearbeitet» schreibt ``grund`` und nicht ``begruendung``.

    Er sagt selbst, dass er nicht urteilt (NICHT ANWENDBAR) — ein vorangestelltes
    «kein Urteil» wäre dort eine zweite, schwächere Fassung desselben Satzes.
    """
    satz = "NICHT ANWENDBAR: An diesem Bild wurde von Hand gearbeitet."

    def qa_handeingriff(*, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": None, "nicht_anwendbar": True,
                "grund": satz, "error": None}

    arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt(qa=qa_handeingriff).tabelle())

    assert _von_der_platte(mappe)["bilder"][0]["herkunft"]["grund"] == satz


def test_eine_pruefung_ohne_satz_wird_nicht_zu_none(mappe):
    """Liefert eine Prüfung gar keinen Satz, steht das da — nicht ``None``."""
    def qa_stumm(*, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": False, "begruendung": "", "error": None}

    arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt(qa=qa_stumm).tabelle())

    grund = _von_der_platte(mappe)["bilder"][0]["herkunft"]["grund"]
    assert grund == (f"Die Prüfung {kette.KNOTEN_QA} hat zu ihrem Urteil keine "
                     f"Begründung mitgeliefert.")


# ------------------------------------------------ (b) · die Lizenz kommt an

def test_die_lizenz_des_gewichts_steht_am_bild_und_im_lauf(mappe):
    """Der Wächter für Befund (b), mit dem **echten** Render-Ausführer.

    Die Lizenz, die ``render.rendere`` aus ``backbone.pruefe_lizenz`` holt, muss nach
    Schreiben und Öffnen am Bild und im Lauf stehen — und zwar dieselbe.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt().tabelle())

    geliefert = ergebnis["lauf"]["knoten"][kette.KNOTEN_RENDER]["ausgaben"]["lizenz"]
    assert geliefert and geliefert["lizenz"], "die Renderstufe liefert eine Lizenz"

    p = _von_der_platte(mappe)
    herkunft = p["bilder"][0]["herkunft"]
    assert herkunft["lizenz"] is not None, "die Lizenz fiel auf dem Weg in die Mappe weg"
    assert herkunft["lizenz"]["name"] == geliefert["name"]
    assert herkunft["lizenz"]["lizenz"] == geliefert["lizenz"]
    assert herkunft["lizenz"]["zulaessig"] is geliefert["zulaessig"]
    assert herkunft["maengel"] == [], "geprüft und nichts gefunden bleibt eine leere Liste"

    angaben = p["laeufe"][-1]["angaben"][kette.KNOTEN_RENDER]
    assert angaben["lizenz"] == herkunft["lizenz"]
    assert angaben["maengel"] == []


def test_ein_abgelehnter_auftrag_behaelt_lizenz_und_maengel_im_lauf(mappe):
    """Ohne Bild kein Bildeintrag — aber gerade hier sind die Mängel die Auskunft.

    Ein Non-Commercial-Gewicht wird unter Regel 1 abgelehnt. Das steht in ``maengel``,
    und das muss im Lauf ankommen, auch wenn kein Bild entstand.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkstatt().tabelle(),
                                  backbone="flux1-dev")

    assert ergebnis["vermerkt"] == 0
    angaben = _von_der_platte(mappe)["laeufe"][-1]["angaben"][kette.KNOTEN_RENDER]
    assert angaben["maengel"], "die Ablehnung steht nicht in der Mappe"
    assert angaben["lizenz"] is not None
    assert angaben["lizenz"]["zulaessig"] is False


def test_ohne_angabe_bleibt_none_und_wird_nicht_leer(mappe):
    """Eine Stufe, die weder Lizenz noch Mängel meldet: ``None``, nicht ``{}`` / ``[]``.

    Aus «nicht angegeben» darf kein «geprüft und leer» werden.
    """
    def render_stumm(*, knoten, eingaben, out_dir):
        bild = _schreibe_png(Path(out_dir) / "bild.png")
        return {"status": "ok", "bild_png": str(bild)}

    tabelle = Werkstatt().tabelle()
    tabelle[ART_RENDER] = render_stumm
    arbeitsgang.rechne(mappe, ausfuehrer=tabelle)

    p = _von_der_platte(mappe)
    herkunft = p["bilder"][0]["herkunft"]
    assert herkunft["lizenz"] is None and herkunft["maengel"] is None
    angaben = p["laeufe"][-1]["angaben"][kette.KNOTEN_RENDER]
    assert angaben == {"lizenz": None, "maengel": None}


# ------------------------------------------------ (c) · keine geteilten Objekte

def _mit_abweichung(tabelle: dict) -> dict:
    """Die Renderstufe meldet eine Abweichung — dann gibt es alle drei Stellen."""
    echt = tabelle[ART_RENDER]

    def render_abweichend(*, knoten, eingaben, out_dir):
        return dict(echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir),
                    modus_bestellt="image_edit", modus_gerechnet="txt2img",
                    modus_abweichung=True, hinweise=("BESTELLT WAR 'image_edit'.",))

    return dict(tabelle, **{ART_RENDER: render_abweichend})


def test_eine_berichtigung_am_bild_aendert_den_lauf_nicht(mappe):
    """Der Wächter für Befund (c), vom Bild aus.

    Die Messung am Bild wird geändert und gespeichert. Im Lauf — im Arbeitsspeicher
    **und** in der neu geöffneten Mappe — darf davon nichts ankommen.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_mit_abweichung(Werkstatt().tabelle()))
    p = ergebnis["projekt"]

    messung_am_bild = p["bilder"][0]["herkunft"]["messung"]
    messung_am_bild["hinweise"].append("NACHTRAG AM BILD")
    messung_am_bild["modus_bestellt"] = "berichtigt"
    p["bilder"][0]["herkunft"]["lizenz"]["name"] = "berichtigt"
    projekt.speichere(p, mappe)

    for lauf in (p["laeufe"][-1], _von_der_platte(mappe)["laeufe"][-1]):
        im_lauf = lauf["messungen"][kette.KNOTEN_RENDER]
        assert "NACHTRAG AM BILD" not in im_lauf["hinweise"], (
            "die Hinweisliste am Bild ist dieselbe wie im Lauf")
        assert im_lauf["modus_bestellt"] == "image_edit"
        assert "NACHTRAG AM BILD" not in lauf["modus_abweichungen"][0]["hinweise"]
        assert lauf["angaben"][kette.KNOTEN_RENDER]["lizenz"]["name"] != "berichtigt"


def test_eine_aenderung_im_lauf_aendert_die_abweichungsliste_nicht(mappe):
    """Derselbe Wächter von der anderen Seite: die Liste in ``modus_abweichungen``.

    Sie war zusätzlich mit der Messung im Lauf geteilt — also mit einer **dritten**
    Stelle, die niemand daneben vermutet.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_mit_abweichung(Werkstatt().tabelle()))
    p = ergebnis["projekt"]

    p["laeufe"][-1]["messungen"][kette.KNOTEN_RENDER]["hinweise"].append("NACHTRAG IM LAUF")
    projekt.speichere(p, mappe)

    for q in (p, _von_der_platte(mappe)):
        assert "NACHTRAG IM LAUF" not in q["laeufe"][-1]["modus_abweichungen"][0]["hinweise"]
        assert "NACHTRAG IM LAUF" not in q["bilder"][0]["herkunft"]["messung"]["hinweise"]


def test_das_knotenergebnis_und_die_messung_in_der_mappe_sind_getrennt(mappe):
    """Die dritte Kopie, bis zur Durchsicht vom 22.09.2026 ohne Wächter.

    ``rechne`` gibt das Knotenergebnis als ``lauf`` an den Aufrufer zurück, und
    ``geraeteweg`` ist darin ein Wörterbuch. Ohne die Kopie in ``_messung_zu`` wäre die
    Messung in der Mappe dasselbe Objekt: Wer das zurückgegebene Ergebnis bearbeitet,
    schriebe still die Mappe um.
    """
    tabelle = Werkstatt().tabelle()
    echt = tabelle[ART_RENDER]

    def render_mit_geraet(*, knoten, eingaben, out_dir):
        return dict(echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir),
                    geraeteweg={"geraet": "cpu", "grund": "Probe"})

    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=dict(tabelle,
                                                         **{ART_RENDER: render_mit_geraet}))
    zurueck = ergebnis["lauf"]["knoten"][kette.KNOTEN_RENDER]["ausgaben"]["geraeteweg"]
    zurueck["geraet"] = "vom Aufrufer berichtigt"

    im_lauf = ergebnis["projekt"]["laeufe"][-1]["messungen"][kette.KNOTEN_RENDER]
    assert im_lauf["geraeteweg"]["geraet"] == "cpu", (
        "das zurückgegebene Knotenergebnis und die Messung in der Mappe sind dasselbe Objekt")
    assert ergebnis["projekt"]["bilder"][0]["herkunft"]["messung"]["geraeteweg"]["geraet"] == "cpu"
