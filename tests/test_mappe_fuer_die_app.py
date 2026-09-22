"""Was die App vom Kern braucht — sechs Fähigkeiten, **über den Produktweg** geprüft.

Einheit D-KERN, 22.09.2026. Die iPad-App zeigt, was in der Mappe steht; was die Mappe
nicht trägt, kann sie nicht zeigen. Geprüft wird darum jedes Mal über
``arbeitsgang.lege_an`` / ``rechne`` / ``rechne_skizze`` mit Attrappen, und gelesen wird
aus der **neu von der Platte geöffneten** Mappe — nicht aus dem Rückgabewert.

1. **Score je Bild** — die Zahl zum Urteil (Entscheid 16: Farbe, Wort und Zahl).
   Fehlt sie, bleibt sie ``None``, nie 0.
2. **Namen nachträglich** (Entscheid 19) — ``projekt.benenne``; die Datei bleibt.
3. **Abbrechen** (Entscheid 31) — ``kette.fuehre_aus(abbrechen=…)``; Fertiges bleibt.
4. **Entwurf** (Entscheid 30) — weniger Schritte, keine Prüfung, «Entwurf — nicht
   geprüft», nie «bestanden».
5. **Varianten** (Entscheid 32) — n Startwerte nach ``varianten.saatreihe``, eine Gruppe.
6. **Skizze rechnen** — Bildquelle + Nachrender; die Skizze wird «gerechnet», und der
   Hinweis «SKIZZE NICHT ANGEKOMMEN» kommt bis ans Bild.

Ohne GPU, ohne Blender, ohne Gewichte. Regel 3: Alle Dateien entstehen hier aus ein paar
Bytes; kein echtes Projekt, kein echter Name.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, kette, projekt, render
from aiimaging.graph import ArtefaktCache
from aiimaging.kette import (
    ART_BILDQUELLE,
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_NACHRENDER,
    ART_QA,
    ART_RENDER,
)


# ======================================================================================
# Werkzeug
# ======================================================================================

def _png(pfad, werte=(0, 64, 128, 255)) -> Path:
    """Ein gültiges 2x2-Graustufen-PNG — echt, weil ``bildlesen.pruefe_png`` es liest."""
    roh = b"".join(b"\x00" + bytes(werte[z * 2:(z + 1) * 2]) for z in range(2))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(roh))
                     + block(b"IEND", b""))
    return pfad


class Werkbank:
    """Attrappen für die vier Stufen der Standardkette — mit Zählern.

    Sie schreiben **echte** Dateien, sonst wäre jeder Lauf ein Fehltreffer im
    Zwischenspeicher. ``qa_antwort`` ist, was die Prüfung meldet; ``render_seeds`` und
    ``render_schritte`` halten fest, womit die Bildstufe wirklich gerufen wurde.
    """

    def __init__(self, *, qa_antwort=None, render_faellt: bool = False) -> None:
        self.qa_antwort = qa_antwort
        self.render_faellt = render_faellt
        self.aufrufe = {ART_GEOMETRIE: 0, ART_MULTIPASS: 0, ART_RENDER: 0, ART_QA: 0}
        self.render_seeds: list[int] = []
        self.render_schritte: list[int] = []

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_GEOMETRIE] += 1
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_MULTIPASS] += 1
        return {"status": "ok", "depth_png": str(_png(Path(out_dir) / "tiefe_norm.png")),
                "beauty_png": str(_png(Path(out_dir) / "beauty.png", (5, 5, 5, 5)))}

    def render(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_RENDER] += 1
        self.render_seeds.append(knoten.params["seed"])
        self.render_schritte.append(knoten.params["schritte"])
        if self.render_faellt:
            return {"status": "fehler", "error": "Die Karte ist voll."}
        seed = knoten.params["seed"] % 250
        bild = _png(Path(out_dir) / "bild.png", (seed, seed, 1, 2))
        return {"status": "ok", "bild_png": str(bild)}

    def qa(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_QA] += 1
        if self.qa_antwort is not None:
            return dict(self.qa_antwort)
        return {"status": "ok", "bestanden": True, "score": 0.8123,
                "schwelle": knoten.params["schwelle"], "begruendung": "Attrappe."}


@pytest.fixture
def glb(tmp_path):
    """Ein gültiges glb — es geht den Weg «durchgereicht», also ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


@pytest.fixture
def mappe(tmp_path, glb):
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


def _neu(wurzel) -> dict:
    """Die Mappe, **frisch von der Platte** — nicht der Rückgabewert."""
    return projekt.oeffne(wurzel)["projekt"]


def _bild(wurzel, knoten: str = kette.KNOTEN_RENDER) -> dict:
    treffer = [b for b in _neu(wurzel)["bilder"] if b["herkunft"]["knoten"] == knoten]
    assert len(treffer) == 1, treffer
    return treffer[0]


# ======================================================================================
# 1 · Score je Bild
# ======================================================================================

def test_das_bild_traegt_score_und_schwelle_seiner_pruefung(mappe):
    """Entscheid 16: Farbe, Wort **und Zahl**. Die Zahl kommt aus der Prüfung, die das
    Urteil gefällt hat, und steht am Bild in der Mappe."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), qa_schwelle=0.7)

    bild = _bild(mappe)
    assert bild["geometrie_bestanden"] is True
    assert bild["score"] == pytest.approx(0.8123)
    assert bild["schwelle"] == pytest.approx(0.7)


def test_ohne_pruefung_steht_der_score_als_none_da_nie_als_null(mappe):
    """Das Feld steht da — und ``None`` heisst nicht gemessen. Eine 0 hiesse «gemessen
    und ganz schlecht»."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), qa=False)

    bild = _bild(mappe)
    assert "score" in bild and "schwelle" in bild
    assert bild["score"] is None
    assert bild["schwelle"] is None


@pytest.mark.parametrize("antwort", [
    {"status": "ok", "bestanden": False, "begruendung": "ohne Zahl"},
    {"status": "ok", "bestanden": False, "score": True, "schwelle": "hoch"},
    {"status": "ok", "bestanden": False, "score": float("nan"), "schwelle": None},
], ids=["fehlt", "wahrheitswert-und-text", "nan"])
def test_eine_pruefung_ohne_brauchbare_zahl_laesst_den_score_none(mappe, antwort):
    """Was keine endliche Zahl ist, wird ``None`` — nie 0, nie 1.0 aus einem ``True``."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank(qa_antwort=antwort).tabelle())

    bild = _bild(mappe)
    assert bild["geometrie_bestanden"] is False, "das Urteil selbst bleibt stehen"
    assert bild["score"] is None
    assert bild["schwelle"] is None


def test_vermerke_bild_nimmt_keinen_wahrheitswert_als_score():
    p = {"bilder": []}
    with pytest.raises(projekt.ProjektError, match="score"):
        projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", score=True)
    assert p["bilder"] == []


# ======================================================================================
# 2 · Namen nachträglich
# ======================================================================================

def _skizze_ablegen(wurzel, name="skizze-1.png", bemerkung="Balkon im Obergeschoss",
                    stand=projekt.SKIZZE_OFFEN) -> str:
    _png(Path(wurzel) / name, (200, 10, 10, 200))
    p = _neu(wurzel)
    projekt.vermerke_skizze(p, skizze=name, bemerkung=bemerkung, stand=stand)
    projekt.speichere(p, wurzel)
    return name


def test_ein_bild_bekommt_einen_namen_und_die_datei_bleibt(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    vorher = _bild(mappe)
    stand_vorher = _neu(mappe)["stand_nr"]

    projekt.benenne(mappe, bild=vorher["bild"], titel="  Südansicht, Abendlicht  ")

    nachher = _bild(mappe)
    assert nachher["titel"] == "Südansicht, Abendlicht"
    assert nachher["bild"] == vorher["bild"], "die Datei heisst weiter wie vorher"
    assert (mappe / nachher["bild"]).is_file()
    assert _neu(mappe)["stand_nr"] == stand_vorher + 1


def test_der_name_ueberlebt_das_neurechnen(mappe):
    """Wer ein Bild benannt hat und es neu vermerkt bekommt, hat es nicht umbenannt."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    projekt.benenne(mappe, bild=_bild(mappe)["bild"], titel="Favorit")

    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    assert _bild(mappe)["titel"] == "Favorit"


def test_ein_leerer_name_nimmt_ihn_zurueck(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    name = _bild(mappe)["bild"]
    projekt.benenne(mappe, bild=name, titel="Favorit")

    projekt.benenne(mappe, bild=name, titel="   ")

    assert _bild(mappe)["titel"] is None


def test_eine_skizze_bekommt_einen_namen(mappe):
    name = _skizze_ablegen(mappe)

    projekt.benenne(mappe, skizze=name, titel="Erste Idee")

    (eintrag,) = _neu(mappe)["skizzen"]
    assert eintrag["titel"] == "Erste Idee"
    assert eintrag["skizze"] == name


def test_benennen_von_einem_alten_stand_wird_abgelehnt(mappe):
    """Wie ``speichere``: Wer von einem älteren Stand kommt, überschreibt nicht."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    alt = _neu(mappe)["stand_nr"]
    name = _bild(mappe)["bild"]
    projekt.benenne(mappe, bild=name, titel="Von drüben")      # jemand anderes schreibt

    with pytest.raises(projekt.ProjektKollision):
        projekt.benenne(mappe, bild=name, titel="Von hier", von_stand=alt)

    assert _bild(mappe)["titel"] == "Von drüben"


@pytest.mark.parametrize("wie", [
    dict(bild="gibt-es-nicht.png", titel="x"),
    dict(bild="a.png", skizze="b.png", titel="x"),
    dict(titel="x"),
    dict(bild="__BILD__", titel="zwei\nZeilen"),
    dict(bild="__BILD__", titel="x" * (projekt.TITEL_HOECHSTENS + 1)),
], ids=["unbekannt", "beides", "keines", "zeilenumbruch", "zu-lang"])
def test_unbrauchbares_benennen_wird_abgewiesen_und_nichts_geschrieben(mappe, wie):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    wie = {k: (_bild(mappe)["bild"] if v == "__BILD__" else v) for k, v in wie.items()}
    stand = _neu(mappe)["stand_nr"]

    with pytest.raises(projekt.ProjektError):
        projekt.benenne(mappe, **wie)

    assert _neu(mappe)["stand_nr"] == stand
    assert _bild(mappe)["titel"] is None


# ======================================================================================
# 3 · Abbrechen
# ======================================================================================

def _graph(tmp_path):
    (tmp_path / "m.glb").write_text("glb", encoding="utf-8")
    return kette.baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Y",
                            prompt="ein Haus")


def test_nach_dem_abbruch_laeuft_kein_knoten_mehr(tmp_path):
    """Die Frage steht VOR jedem Knoten. Einmal «ja», und der Rest steht als
    «abgebrochen» da; gerechnet hat nur, was davor lag."""
    werk = Werkbank()
    fragen = []

    def abbrechen():
        fragen.append(1)
        return len(fragen) >= 2          # vor dem zweiten Knoten anhalten

    lauf = kette.fuehre_aus(_graph(tmp_path), ausfuehrer=werk.tabelle(),
                            out_dir=tmp_path / "out", abbrechen=abbrechen)

    assert lauf["status"] == kette.STATUS_ABGEBROCHEN
    assert werk.aufrufe == {ART_GEOMETRIE: 1, ART_MULTIPASS: 0, ART_RENDER: 0, ART_QA: 0}
    assert lauf["abgebrochen"] == [kette.KNOTEN_MULTIPASS, kette.KNOTEN_RENDER,
                                   kette.KNOTEN_QA]
    for kid in lauf["abgebrochen"]:
        assert lauf["knoten"][kid]["status"] == kette.STATUS_ABGEBROCHEN
    assert lauf["knoten"][kette.KNOTEN_GEOMETRIE]["status"] == kette.STATUS_OK
    assert lauf["gerechnet"] == 1, "abgebrochene Knoten zählen nicht als gerechnet"
    assert len(fragen) == 2, "nach dem «ja» wird nicht erneut gefragt"


def test_ohne_abbruch_wird_vor_jedem_knoten_gefragt(tmp_path):
    fragen = []
    lauf = kette.fuehre_aus(_graph(tmp_path), ausfuehrer=Werkbank().tabelle(),
                            out_dir=tmp_path / "out",
                            abbrechen=lambda: fragen.append(1) or False)
    assert lauf["status"] == kette.STATUS_OK
    assert lauf["abgebrochen"] == []
    assert len(fragen) == 4


def test_fertiges_bleibt_im_zwischenspeicher(tmp_path):
    """Entscheid 14: Fertiges wird nach einem Abbruch nicht neu gerechnet."""
    werk = Werkbank()
    speicher = ArtefaktCache(tmp_path / "speicher")
    fragen = []
    kette.fuehre_aus(_graph(tmp_path), ausfuehrer=werk.tabelle(), cache=speicher,
                     out_dir=tmp_path / "out",
                     abbrechen=lambda: fragen.append(1) or len(fragen) >= 3)
    assert werk.aufrufe[ART_MULTIPASS] == 1

    zweiter = kette.fuehre_aus(_graph(tmp_path), ausfuehrer=werk.tabelle(),
                               cache=speicher, out_dir=tmp_path / "out")

    assert zweiter["status"] == kette.STATUS_OK
    assert werk.aufrufe[ART_GEOMETRIE] == 1 and werk.aufrufe[ART_MULTIPASS] == 1
    assert zweiter["cache_treffer"] == 2


def test_eine_scheiternde_abbruchfrage_haelt_nichts_an_und_steht_im_ergebnis(tmp_path):
    def kaputt():
        raise RuntimeError("Leitung weg")

    lauf = kette.fuehre_aus(_graph(tmp_path), ausfuehrer=Werkbank().tabelle(),
                            out_dir=tmp_path / "out", abbrechen=kaputt)
    assert lauf["status"] == kette.STATUS_OK
    assert "Leitung weg" in lauf["abbruchfrage_fehler"]


def test_ein_abgebrochener_knoten_meldet_sein_ende_aber_keinen_beginn(tmp_path):
    ereignisse = []
    kette.fuehre_aus(_graph(tmp_path), ausfuehrer=Werkbank().tabelle(),
                     out_dir=tmp_path / "out", melder=ereignisse.append,
                     abbrechen=lambda: True)
    beginn = [e for e in ereignisse if e["art"] == "knoten_beginnt"]
    ende = [e for e in ereignisse if e["art"] == "knoten_fertig"]
    assert beginn == []
    assert {e["status"] for e in ende} == {kette.STATUS_ABGEBROCHEN}
    assert len(ende) == 4


def test_rechne_vermerkt_das_fertige_bild_und_den_abgebrochenen_lauf(mappe):
    """Angehalten vor der Prüfung: Das Bild ist fertig und steht in der Mappe — ohne
    Urteil, mit dem Grund, dass angehalten wurde. Ein zweiter Lauf rechnet es nicht neu."""
    werk = Werkbank()
    reihe = iter([False, False, False, True])       # vor der Prüfung anhalten
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle(),
                                  abbrechen=lambda: next(reihe))
    assert ergebnis["abgebrochen"] is True

    bild = _bild(mappe)
    assert bild["geometrie_bestanden"] is None
    assert bild["score"] is None
    assert "angehalten" in bild["herkunft"]["grund"]
    (lauf,) = _neu(mappe)["laeufe"]
    assert lauf["abgebrochen"] is True
    assert lauf["status"] == kette.STATUS_ABGEBROCHEN
    assert lauf["abgebrochene_knoten"] == [kette.KNOTEN_QA]
    assert lauf["bilder_vermerkt"] == 1

    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())
    assert werk.aufrufe[ART_RENDER] == 1, "das fertige Bild wurde neu gerechnet"
    assert _bild(mappe)["geometrie_bestanden"] is True


def test_nach_einem_abbruch_ist_die_mappe_wieder_frei(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), abbrechen=lambda: True)
    assert not (mappe / arbeitsgang.SPERRDATEI).exists()


# ======================================================================================
# 4 · Entwurf
# ======================================================================================

def test_ein_entwurf_rechnet_weniger_schritte_und_prueft_nicht(mappe):
    werk = Werkbank()
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle(), entwurf=True)

    assert werk.aufrufe[ART_QA] == 0, "ein Entwurf wird nicht geprüft"
    assert werk.render_schritte == [arbeitsgang.ENTWURF_SCHRITTE]
    assert arbeitsgang.ENTWURF_SCHRITTE < 20
    assert ergebnis["vermerkt"] == 1

    bild = _bild(mappe)
    assert bild["entwurf"] is True
    assert bild["geometrie_bestanden"] is None
    assert bild["geometrie_gemessen"] is False
    assert bild["score"] is None
    assert bild["herkunft"]["grund"].startswith(arbeitsgang.ENTWURF_VERMERK)
    assert arbeitsgang.ENTWURF_VERMERK == "Entwurf — nicht geprüft"
    assert _neu(mappe)["laeufe"][-1]["entwurf"] is True


def test_ein_entwurf_ueberstimmt_die_pruefung_der_mappe_und_behaelt_wenige_schritte(
        tmp_path, glb):
    wurzel = tmp_path / "p"
    arbeitsgang.lege_an(wurzel, glb, einstellungen={
        "prompt": "Abendlicht", "up_axis": "Y", "qa": True, "schritte": 4})
    werk = Werkbank()

    arbeitsgang.rechne(wurzel, ausfuehrer=werk.tabelle(), entwurf=True)

    assert werk.aufrufe[ART_QA] == 0
    assert werk.render_schritte == [4], "weniger heisst höchstens, nicht genau"
    assert _bild(wurzel)["geometrie_bestanden"] is None


def test_ein_gewoehnlicher_lauf_ist_kein_entwurf(mappe):
    werk = Werkbank()
    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())
    assert _bild(mappe)["entwurf"] is False
    assert werk.render_schritte == [20]


def test_entwurf_mit_pruefung_im_selben_aufruf_wird_abgewiesen(mappe):
    with pytest.raises(arbeitsgang.ArbeitsgangError, match="Entwurf"):
        arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), entwurf=True, qa=True)
    assert _neu(mappe).get("laeufe", []) == []


def test_ein_entwurf_mit_urteil_kommt_nicht_in_die_mappe():
    p = {"bilder": []}
    with pytest.raises(projekt.ProjektError, match="Entwurf"):
        projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", urteil=True,
                              entwurf=True)


# ======================================================================================
# 5 · Varianten
# ======================================================================================

def test_drei_startwerte_ergeben_drei_bilder_in_einer_gruppe(mappe):
    werk = Werkbank()
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle(), varianten=3)

    assert werk.render_seeds == [7, 8, 9], "die Vorschrift der Saatreihe: seed, seed+1 …"
    assert ergebnis["vermerkt"] == 3
    bilder = _neu(mappe)["bilder"]
    assert len(bilder) == 3
    gruppen = [b["variantengruppe"] for b in bilder]
    assert len({g["id"] for g in gruppen}) == 1
    assert ergebnis["variantengruppe"] == gruppen[0]["id"]
    assert [g["nummer"] for g in gruppen] == [1, 2, 3]
    assert {g["von"] for g in gruppen} == {3}
    assert {g["art"] for g in gruppen} == {arbeitsgang.VARIANTEN_STARTWERTE}
    assert [b["herkunft"]["seed"] for b in bilder] == [7, 8, 9]
    assert len(_neu(mappe)["laeufe"]) == 3
    assert werk.aufrufe[ART_GEOMETRIE] == 1, "die Geometrie kommt ab Lauf zwei aus dem Speicher"


def test_ein_einzelner_lauf_hat_keine_gruppe(mappe):
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    assert ergebnis["variantengruppe"] is None
    assert _bild(mappe)["variantengruppe"] is None


def test_ein_abbruch_in_der_reihe_startet_keine_weitere_variante(mappe):
    werk = Werkbank()
    fragen = []
    # Vier Knoten je Variante: Variante 1 ganz, Variante 2 bis vor die Prüfung.
    ergebnis = arbeitsgang.rechne(
        mappe, ausfuehrer=werk.tabelle(), varianten=3,
        abbrechen=lambda: fragen.append(1) or len(fragen) >= 8)

    assert ergebnis["abgebrochen"] is True
    assert ergebnis["varianten_nicht_begonnen"] == 1
    assert werk.render_seeds == [7, 8]
    laeufe = _neu(mappe)["laeufe"]
    assert [l["abgebrochen"] for l in laeufe] == [False, True]
    assert len(_neu(mappe)["bilder"]) == 2, "Fertiges bleibt — auch das ungeprüfte"


@pytest.mark.parametrize("wie", [
    dict(varianten=1), dict(varianten=arbeitsgang.VARIANTEN_HOECHSTENS + 1),
    dict(varianten=True), dict(varianten=3, art="ebenen"), dict(varianten=3, art="farben"),
    dict(varianten=3, seed=render.MAX_SEED),
], ids=["eine", "zu-viele", "wahrheitswert", "ebenen-hier", "unbekannte-art",
        "startwert-am-rand"])
def test_unbestellbare_reihen_werden_vor_dem_ersten_lauf_abgewiesen(mappe, wie):
    werk = Werkbank()
    with pytest.raises(arbeitsgang.ArbeitsgangError):
        arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle(), **wie)
    assert sum(werk.aufrufe.values()) == 0
    assert _neu(mappe).get("laeufe", []) == []


# ======================================================================================
# 6 · Skizze rechnen lassen
# ======================================================================================

class _Modell:
    """Ein Bildmodell, das nichts rechnet — es hält nur fest, welcher Prompt ankam."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, parameter: dict) -> dict:
        self.prompts.append(parameter["prompt"])
        ziel = parameter["ausgabe_png"]
        _png(ziel, werte=(10, 20, 30, 40))
        return {"bild_png": ziel, "hinweise": [], "schritte_gerechnet": None}


def _skizzentabelle(werk: Werkbank, modell) -> dict:
    """Geometrie und Multipass als Attrappen; Bildquelle, Nachrender und Prüfung ECHT.

    Die echte Prüfung rechnet auf einer Skizze nicht — sie urteilt «nicht anwendbar»,
    ohne ein Modell zu laden. Die Bildstufe des Modells darf nicht laufen."""
    def render_verboten(**_):
        raise AssertionError("ein Skizzenlauf rechnet das Bild aus dem Modell nicht")

    return {**werk.tabelle(), ART_RENDER: render_verboten,
            ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell),
            ART_QA: kette.qa_ausfuehrer()}


def test_eine_skizze_wird_gerechnet_und_steht_danach_als_gerechnet_da(mappe):
    name = _skizze_ablegen(mappe)
    modell = _Modell()

    ergebnis = arbeitsgang.rechne_skizze(
        mappe, name, ausfuehrer=_skizzentabelle(Werkbank(), modell))

    assert ergebnis["vermerkt"] == 1
    assert modell.prompts == ["Balkon im Obergeschoss"], (
        "ohne eigene Anweisung gilt die Bemerkung der Skizze")
    (skizze,) = _neu(mappe)["skizzen"]
    assert skizze["stand"] == projekt.SKIZZE_GERECHNET
    bild = _bild(mappe, knoten=f"{arbeitsgang.SKIZZEN_VORSATZ}-{kette.KNOTEN_NACHRENDER}")
    assert skizze["ergebnis"] == bild["bild"]
    assert bild["herkunft"]["skizze"] == name
    assert bild["schicht"] == kette.SCHICHT_AI_IMAGING
    assert bild["geometrie_bestanden"] is None
    assert "NICHT ANWENDBAR" in bild["herkunft"]["grund"]
    assert [b["herkunft"]["knoten"] for b in _neu(mappe)["bilder"]] == [
        f"{arbeitsgang.SKIZZEN_VORSATZ}-{kette.KNOTEN_NACHRENDER}"], (
        "die Skizze selbst ist kein erzeugtes Bild")


def test_der_hinweis_skizze_nicht_angekommen_reist_bis_ans_bild(mappe):
    """Owner-Entscheid 22.09.2026: auf dem Vorgabemodell weiter rechnen — mit Hinweis.
    Er muss am Bild IN DER MAPPE stehen, sonst sieht ein reiner Text-zu-Bild-Lauf aus wie
    eine Bearbeitung der Skizze."""
    name = _skizze_ablegen(mappe)

    arbeitsgang.rechne_skizze(mappe, name, anweisung="ein Vordach",
                              ausfuehrer=_skizzentabelle(Werkbank(), _Modell()))

    bild = _bild(mappe, knoten=f"{arbeitsgang.SKIZZEN_VORSATZ}-{kette.KNOTEN_NACHRENDER}")
    hinweise = bild["herkunft"]["messung"]["hinweise"]
    anfang = kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.split(":")[0]
    assert hinweise and hinweise[0].startswith(anfang), hinweise
    assert render.VORGABE_BACKBONE in hinweise[0]


def test_eine_gescheiterte_skizze_bleibt_offen(mappe):
    name = _skizze_ablegen(mappe)

    def faellt(**_):
        return {"status": "fehler", "error": "Die Karte ist voll."}

    tabelle = {**_skizzentabelle(Werkbank(), _Modell()), ART_NACHRENDER: faellt}
    ergebnis = arbeitsgang.rechne_skizze(mappe, name, ausfuehrer=tabelle)

    assert ergebnis["vermerkt"] == 0
    (skizze,) = _neu(mappe)["skizzen"]
    assert skizze["stand"] == projekt.SKIZZE_OFFEN
    assert skizze["ergebnis"] is None
    assert _neu(mappe)["laeufe"][-1]["skizze"] == name


def test_drei_ebenen_ergeben_drei_laeufe_in_einer_gruppe(mappe):
    namen = [_skizze_ablegen(mappe, f"skizze-{i}.png", f"Ebene {i}") for i in (1, 2, 3)]
    modell = _Modell()

    ergebnis = arbeitsgang.rechne_skizze(
        mappe, namen, ausfuehrer=_skizzentabelle(Werkbank(), modell))

    assert modell.prompts == ["Ebene 1", "Ebene 2", "Ebene 3"]
    assert ergebnis["vermerkt"] == 3
    bilder = _neu(mappe)["bilder"]
    gruppen = [b["variantengruppe"] for b in bilder]
    assert len({g["id"] for g in gruppen}) == 1
    assert {g["art"] for g in gruppen} == {arbeitsgang.VARIANTEN_EBENEN}
    assert [g["skizze"] for g in gruppen] == namen
    assert [b["herkunft"]["skizze"] for b in bilder] == namen
    assert {s["stand"] for s in _neu(mappe)["skizzen"]} == {projekt.SKIZZE_GERECHNET}
    assert len(_neu(mappe)["laeufe"]) == 3


@pytest.mark.parametrize("fall", ["unbekannt", "verworfen", "datei-fehlt",
                                  "ohne-anweisung", "doppelt"])
def test_eine_unrechenbare_skizze_wird_abgewiesen(mappe, fall):
    if fall == "unbekannt":
        ziel = "skizze-gibt-es-nicht.png"
    elif fall == "verworfen":
        ziel = _skizze_ablegen(mappe, stand=projekt.SKIZZE_VERWORFEN)
    elif fall == "datei-fehlt":
        ziel = _skizze_ablegen(mappe)
        (mappe / ziel).unlink()
    elif fall == "ohne-anweisung":
        ziel = _skizze_ablegen(mappe, bemerkung="")
    else:
        ziel = [_skizze_ablegen(mappe)] * 2
    werk = Werkbank()

    with pytest.raises(arbeitsgang.ArbeitsgangError):
        arbeitsgang.rechne_skizze(mappe, ziel, ausfuehrer=_skizzentabelle(werk, _Modell()))

    assert sum(werk.aufrufe.values()) == 0
    assert _neu(mappe).get("laeufe", []) == []
