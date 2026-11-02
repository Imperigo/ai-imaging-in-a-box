"""Bild aus Skizze auf einer FRISCHEN Blender-Grundlage (A0094, Vertrag A0050 drüben).

Owner-Entscheid «Immer vom Render» (31.10.2026): kein KI-Bild ohne Blender-Grundlage. KosmoOrbit
v0.1.12 bestellt ein «Bild aus Skizze» darum mit ``skizze.grundlage: "frisch"`` und genau EINER
Kamera (dem Standpunkt der Skizze). Bis A0094 blieb jeder solche Auftrag hier mit «Unbekannte
Felder in der Bestellung: skizze.grundlage» liegen.

Geprüft wird ohne GPU und ohne Blender, über den Produktweg Annehmen → Freigeben → Abholen:

(a) Die Bestellung mit ``grundlage: "frisch"`` und einer Kamera wird angenommen.
(b) Der Lauf rechnet ZUERST eine frische Grundlage von dieser Kamera, und das Startbild des
    Bildmodells ist deren Beauty-Render — die Skizze liegt als Führung darauf, ihre Anweisung
    ist der Prompt. Der Visbox-eigene Skizzenweg (Skizze auf ihrer alten Unterlage) wird NICHT
    genommen.
(c) Mehr als eine Kamera, keine Kamera, oder eine alte ``vis.grundlage`` wird mit dem Satz aus
    KosmoOrbit (``render-scene.ts``) abgewiesen.
(d) Ohne das Feld bleibt alles wie bisher.

Regel 3: Alles entsteht aus ein paar Bytes; Multipass, Bildmodell, Soll-Karte und Prüfung sind
Attrappen.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, bildlesen, bildschreiben, bruecke, knotenweg
from aiimaging import kosmo_szene, projekt

KENNUNG = "vis-1793600000-a00940"
ROT, BLAU, GRUEN = (255, 0, 0), (0, 0, 255), (0, 200, 0)
KAMERA = {"position": [3, 1.6, 12], "target": [0, 1.5, 0], "up_axis": "y"}

#: Wörtlich aus KosmoOrbit `render-scene.ts` (A0050), superRefine an `skizze`.
SATZ_KO_ALTE_GRUNDLAGE = ('Eine Skizze rechnet auf einer frischen Blender-Grundlage vom '
                          'Standpunkt der Skizze (skizze.grundlage "frisch") — eine alte '
                          'vis.grundlage geht dazu nicht.')
SATZ_KO_KAMERALISTE = ('Mit einer Skizze entsteht EIN Bild vom Standpunkt des Bildes unter der '
                       'Skizze (sonst dem der Mappe) — eine Kameraliste geht dazu nicht (cameras '
                       'weglassen oder "auto").')


def _rgba_png(pfad, breite, hoehe, punkte, grund=(0, 0, 0, 0)) -> Path:
    roh = bytearray()
    for y in range(hoehe):
        roh.append(0)
        for x in range(breite):
            roh += bytes(punkte.get((x, y), grund))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(bytes(roh)))
                     + block(b"IEND", b""))
    return pfad


def _einfarbig(pfad, breite, hoehe, farbe) -> Path:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    return bildschreiben.schreibe_farb_png(pfad, [farbe] * (breite * hoehe), breite, hoehe)


def _glb_bytes() -> bytes:
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    return struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block


@pytest.fixture
def mappe(tmp_path):
    """Eine Mappe mit einem (blauen) Bild und einer Skizze darauf: ein roter Strich bei (1, 1).

    Die Unterlage ist BLAU — die frische Grundlage im Lauf ist GRÜN. So zeigt das Startbild,
    worauf die Skizze gesetzt wurde.
    """
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(_glb_bytes())
    wurzel = tmp_path / "Probemappe"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    unterlage = _einfarbig(wurzel / "bilder" / "alt.png", 4, 4, BLAU)
    p = projekt.oeffne(wurzel)["projekt"]
    p.setdefault("bilder", []).append({"bild": projekt.pfad_fuer_die_mappe(unterlage, wurzel)})
    _rgba_png(wurzel / "skizze-a.png", 4, 4, {(1, 1): (*ROT, 255)})
    projekt.vermerke_skizze(p, skizze="skizze-a.png",
                            ueber=projekt.pfad_fuer_die_mappe(unterlage, wurzel),
                            bemerkung="ein Vordach")
    projekt.speichere(p, wurzel)
    return wurzel


def _szene(*, grundlage="frisch", kameras=None, vis=None, **skizze) -> dict:
    s = {"schema": "kosmovis.render-scene/v1",
         "cameras": [dict(KAMERA)] if kameras is None else kameras,
         "render": {"resolution": [4, 4], "samples": 16, "faithful": 0.8},
         "style": {"mode": "none", "prompt": "Wohnhaus im Abendlicht"},
         "vis": {"skip": False, "backbone": "z-image-turbo", "upscale": False, **(vis or {})},
         "geometry": {"format": "glb"}, "out": ""}
    s["skizze"] = {"quelle": "mappe", "name": "skizze-a.png", **skizze}
    if grundlage is not None:
        s["skizze"]["grundlage"] = grundlage
    return s


def _gelesen(szene) -> dict:
    return kosmo_szene.lies_szene(szene | {"geometry": {"path": "m.glb", "format": "glb"}})


# ======================================================================================
# (a) Angenommen
# ======================================================================================

def test_a_frisch_mit_einer_kamera_wird_gelesen_und_nicht_als_unbekannt_abgewiesen():
    g = _gelesen(_szene(anweisung="a wooden canopy"))
    assert g["maengel"] == (), g["maengel"]
    assert g["skizze"]["grundlage"] == kosmo_szene.SKIZZE_GRUNDLAGE_FRISCH == "frisch"
    assert "skizze.grundlage" not in kosmo_szene.unbekannte_felder(_szene())


def test_a_frisch_wird_auf_dem_produktweg_angenommen(tmp_path, mappe):
    # Heute blieb der Auftrag beim Abholen mit «Unbekannte Felder in der Bestellung:
    # skizze.grundlage» liegen — der Fehler aus KosmoOrbit v0.1.12.
    antwort, _, ergebnis = _bestellen_abholen(tmp_path, mappe, _szene(anweisung="a canopy"))
    assert "Unbekannte Felder" not in json.dumps(antwort, ensure_ascii=False, default=str)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort.get("grund")
    assert knotenweg.mappe_des_auftrags(tmp_path / "ablage" / KENNUNG) == mappe.resolve()


# ======================================================================================
# (b) Gerechnet: erst die frische Grundlage, dann das Bild von ihrem Beauty-Render
# ======================================================================================

def _attrappen():
    protokoll = {"multipass": [], "render": [], "eingang": [], "skizzenweg": 0}

    def multipass(glb, out, **kw):
        protokoll["multipass"].append(kw)
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        tiefe = bildschreiben.schreibe_graustufen_png(out / "tiefe.png", [0.5] * 16, 4, 4)
        beauty = _einfarbig(out / "beauty.png", 4, 4, GRUEN)
        return {"depth_png": str(tiefe), "beauty_png": str(beauty),
                "depth_exr": None}

    def rendere(a, **kw):
        protokoll["render"].append(a)
        protokoll["eingang"].append(bildlesen.lies_png_farben(a.beauty_png)[0])
        _einfarbig(a.ausgabe_png, 4, 4, (9, 9, 9))
        return {"status": "ok", "bild_png": a.ausgabe_png}

    def soll(bericht):
        return [0.0, 1.0, 2.0, 3.0] * 4, 4, 4

    def qa(bild, soll_werte, **kw):
        return {"status": "ok", "score": 0.9, "bestanden": True, "schwelle": kw.get("schwelle")}

    def rechne_skizze(*a, **kw):
        protokoll["skizzenweg"] += 1
        raise AssertionError("Mit grundlage 'frisch' darf der Visbox-Skizzenweg nicht rechnen.")

    return protokoll, dict(_multipass=multipass, _rendere=rendere, _soll=soll, _qa=qa,
                           _rechne_skizze=rechne_skizze, nullprobe=False)


def _bestellen_abholen(tmp_path, mappe, szene):
    ablage = tmp_path / "ablage"
    zettel = knotenweg.lege_an(ablage, szene, _glb_bytes(), "model.glb", kennung=KENNUNG,
                               mappe=mappe.name, mappe_pfad=mappe)
    knotenweg.freigeben(ablage, KENNUNG, zettel["approval_token"])
    protokoll, naehte = _attrappen()
    antwort = abholer.hole_einen(ablage / KENNUNG, verarbeite=abholer.verarbeiter(**naehte),
                                 darf_rechnen=lambda: (True, "frei"))
    datei = ablage / KENNUNG / bruecke.DATEI_ERGEBNIS
    ergebnis = json.loads(datei.read_text("utf-8")) if datei.is_file() else {}
    return antwort, protokoll, ergebnis


def test_b_erst_frische_grundlage_dann_startbild_ihr_beauty_mit_der_skizze(tmp_path, mappe):
    antwort, protokoll, ergebnis = _bestellen_abholen(
        tmp_path, mappe, _szene(anweisung="a wooden canopy"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort.get("grund")

    # Der Visbox-eigene Skizzenweg (Skizze auf ihrer alten Unterlage) rechnete NICHT.
    assert protokoll["skizzenweg"] == 0
    # ZUERST eine frische Grundlage, genau eine, vom Standpunkt der Bestellung.
    assert len(protokoll["multipass"]) == 1
    kw = protokoll["multipass"][0]
    # (Die Kamera kommt Y-up und geht Z-up an Blender: [x, -z, y].)
    assert list(kw["auge"]) == [3, -12, 1.6] and list(kw["blick_auf"]) == [0, 0, 1.5]
    # DANN das Bild: Startbild ist das Beauty der frischen Grundlage (GRÜN, nicht die alte
    # blaue Unterlage), die Skizze liegt darauf (ROT bei (1, 1)) und führt.
    assert len(protokoll["render"]) >= 1
    eingang = protokoll["eingang"][0]
    assert eingang[1 * 4 + 1] == ROT
    uebrige = [f for i, f in enumerate(eingang) if i != 1 * 4 + 1]
    assert set(uebrige) == {GRUEN}, set(uebrige)
    # Die Anweisung der Skizze ist der Prompt — was sich am Bild ändern soll.
    assert "wooden canopy" in protokoll["render"][0].prompt
    # Das Ergebnis sagt, woraus es entstand — auf der frischen Grundlage.
    assert len(ergebnis["images"]) == 1 and len(ergebnis["qa_je_kamera"]) == 1
    hinweise = " ".join(ergebnis["qa"]["verdict"]["hinweise"])
    assert "AUS SKIZZE GERECHNET" in hinweise and "frischen Blender-Grundlage" in hinweise


def test_b_ohne_anweisung_gilt_die_bemerkung_der_skizze(tmp_path, mappe):
    antwort, protokoll, _ = _bestellen_abholen(tmp_path, mappe, _szene())
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort.get("grund")
    assert "Vordach" in protokoll["render"][0].prompt or "canopy" in \
        protokoll["render"][0].prompt.lower()


# ======================================================================================
# (c) Abgewiesen mit dem Satz aus KosmoOrbit
# ======================================================================================

def test_c_frisch_mit_zwei_kameras_wird_mit_dem_satz_aus_kosmoorbit_abgewiesen():
    zwei = [dict(KAMERA), dict(KAMERA, position=[-3, 1.6, 12])]
    g = _gelesen(_szene(kameras=zwei))
    assert SATZ_KO_KAMERALISTE in g["maengel"], g["maengel"]
    assert SATZ_KO_KAMERALISTE in g["maengel_endgueltig"]


def test_c_frisch_mit_alter_grundlage_wird_mit_dem_satz_aus_kosmoorbit_abgewiesen():
    g = _gelesen(_szene(vis={"grundlage": "gl-0123456789abcdef"}))
    assert SATZ_KO_ALTE_GRUNDLAGE in g["maengel"], g["maengel"]
    assert SATZ_KO_ALTE_GRUNDLAGE in g["maengel_endgueltig"]
    # Nicht zusätzlich der alte Satz des Visbox-Skizzenwegs.
    assert not any("fuehrt ihr Bild selbst" in m for m in g["maengel"])


def test_c_die_saetze_stehen_woertlich_in_der_kopie_des_vertrags():
    ts = (Path(__file__).resolve().parents[1] / "kosmovis" / "packages" / "kosmo-contracts"
          / "src" / "render-scene.ts").read_text("utf-8")
    assert kosmo_szene.SATZ_SKIZZE_FRISCH_ALTE_GRUNDLAGE == SATZ_KO_ALTE_GRUNDLAGE
    assert kosmo_szene.SATZ_SKIZZE_KAMERALISTE == SATZ_KO_KAMERALISTE
    assert SATZ_KO_ALTE_GRUNDLAGE in ts and SATZ_KO_KAMERALISTE in ts
    assert "grundlage: z.literal('frisch').optional()" in ts


@pytest.mark.parametrize("kameras", ["auto", "saved"])
def test_c_frisch_ohne_die_eine_kamera_wird_mit_satz_abgewiesen(kameras):
    g = _gelesen(_szene(kameras=kameras))
    assert any("frisch" in m and "EINE Kamera" in m for m in g["maengel"]), g["maengel"]


def test_c_ein_anderer_wert_als_frisch_ist_ein_mangel():
    g = _gelesen(_szene(grundlage="alt"))
    assert any("'skizze.grundlage'" in m for m in g["maengel"]), g["maengel"]


# ======================================================================================
# (d) Ohne das Feld: wie bisher
# ======================================================================================

def test_d_ohne_feld_bleibt_die_kameraliste_ein_mangel_wie_bisher():
    g = _gelesen(_szene(grundlage=None))
    assert any("'cameras' ist eine Liste" in m for m in g["maengel"]), g["maengel"]
    assert "grundlage" not in g["skizze"]


def test_d_ohne_feld_bleibt_die_alte_grundlage_der_alte_satz():
    g = _gelesen(_szene(grundlage=None, kameras="auto",
                        vis={"grundlage": "gl-0123456789abcdef"}))
    assert any("'vis.grundlage' und 'skizze' zugleich" in m for m in g["maengel"])
    assert SATZ_KO_ALTE_GRUNDLAGE not in g["maengel"]


def test_d_ohne_feld_rechnet_weiter_der_visbox_skizzenweg(tmp_path, mappe):
    ablage = tmp_path / "ablage"
    zettel = knotenweg.lege_an(ablage, _szene(grundlage=None, kameras="auto"), _glb_bytes(),
                               "model.glb", kennung=KENNUNG, mappe=mappe.name, mappe_pfad=mappe)
    knotenweg.freigeben(ablage, KENNUNG, zettel["approval_token"])
    protokoll, naehte = _attrappen()
    antwort = abholer.hole_einen(ablage / KENNUNG, verarbeite=abholer.verarbeiter(**naehte),
                                 darf_rechnen=lambda: (True, "frei"))
    # Der alte Weg wurde genommen (die Attrappe des Skizzenwegs schlägt an), kein Multipass.
    assert protokoll["skizzenweg"] == 1
    assert protokoll["multipass"] == []
    assert antwort["tat"] != abholer.TAT_VERARBEITET


def test_b_maske_deckung_und_pruefung_lesen_das_reine_beauty_ohne_skizze(tmp_path, mappe,
                                                                          monkeypatch):
    """Auflage G-A0094: Die Skizze gehört nur ins Startbild des Bildmodells.

    Bauwerksmaske, Deckung (Kanten gegen das Grundbild) und die Geometrie-Prüfung (Soll-Karte
    aus dem Bericht) lesen das Beauty der frischen Grundlage SELBST — ohne den roten Strich der
    Skizze. Läse eine davon das Startbild, mässe die Prüfung die Skizze statt des Modells.
    """
    gelesen = {"maske": [], "deckung": [], "soll": []}

    def farben(pfad):
        return set(bildlesen.lies_png_farben(pfad)[0]) if pfad else None

    echte_maske = abholer._maske_bauen

    def maske(bericht, **kw):
        gelesen["maske"].append(farben(bericht.get("beauty_png")))
        return echte_maske(bericht, **kw)

    echte_deckung = abholer.deckung_der_kamera

    def deckung(ki_png, grundbild_png, maske=None, bericht=None):
        gelesen["deckung"].append(farben(grundbild_png))
        gelesen["soll"].append(farben((bericht or {}).get("beauty_png")))
        return echte_deckung(ki_png, grundbild_png, maske, bericht)

    monkeypatch.setattr(abholer, "_maske_bauen", maske)
    monkeypatch.setattr(abholer, "deckung_der_kamera", deckung)
    antwort, protokoll, _ = _bestellen_abholen(
        tmp_path, mappe, _szene(anweisung="a wooden canopy"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort.get("grund")
    # Gegenprobe: das Startbild des Bildmodells TRUG die Skizze (sonst prüfte diese Probe nichts).
    assert ROT in set(protokoll["eingang"][0])
    # Maske, Deckung und der Bericht, aus dem die Prüfung ihre Soll-Karte liest: reines Grün.
    for wo in ("maske", "deckung", "soll"):
        assert gelesen[wo], f"{wo}: nicht aufgerufen"
        assert all(f == {GRUEN} for f in gelesen[wo]), (wo, gelesen[wo])
