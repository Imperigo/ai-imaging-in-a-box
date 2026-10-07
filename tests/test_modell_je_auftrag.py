"""Ein Bildmodell je Auftrag — **einmal laden für die ganze Reihe, danach freigeben.**

**Der Befund** (HomeStation, ``auftraege/ergebnisse/auf-20261001-221.json``): Drei
Varianten über «Anwenden» an der Fläche, im Dienstprotokoll dreimal «Loading pipeline
components», je rund 1–2 s. ``render.rendere`` lädt sein Modell, wenn ihm keines übergeben
wird — und auf dem Weg über die Mappe (``arbeitsgang.rechne``) übergibt ihm niemand eines.
Also lud es je Variante.

**Was jetzt gilt:** Innerhalb eines Auftrags (``render.ein_modell_je_auftrag``) bleibt ein
geladenes Bildmodell liegen, solange Backbone, Gewichtsort, Lader und Schrittzähler gleich
bleiben. Am Ende des Auftrags wird es losgelassen und ``gib_grafikspeicher_frei`` gerufen —
auch nach einem Fehler oder Abbruch. **Ausserhalb** eines Auftrags lädt ``rendere`` wie
bisher bei jedem Aufruf.

Gerechnet wird mit Attrappen: ein zählender ``_lader``, kein ``torch``, keine Gewichte.
"""
from __future__ import annotations

import gc
import weakref
from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, kette, render
from aiimaging.kette import ART_RENDER
from conftest import MINI_PNG
from test_arbeitsgang import Werkbank

Z = "z-image-turbo"
Z_UNION = "z-image-turbo-union21"


class Bildmodell:
    """Eine Modellattrappe, die ein Bild schreibt. Eine Klasse, damit eine schwache
    Referenz auf sie zeigen kann — so lässt sich prüfen, dass niemand sie mehr hält."""

    def __init__(self, name: str, *, faellt_beim: int | None = None) -> None:
        self.name = name
        self.aufrufe = 0
        self.faellt_beim = faellt_beim

    def __call__(self, parameter: dict) -> str:
        self.aufrufe += 1
        if self.faellt_beim is not None and self.aufrufe == self.faellt_beim:
            raise RuntimeError("Die Attrappe scheitert absichtlich.")
        Path(parameter["ausgabe_png"]).write_bytes(MINI_PNG)
        return parameter["ausgabe_png"]


class ZaehlenderLader:
    """Ersatz für ``render.lade_modell`` mit der Signatur der Naht ``_lader``."""

    def __init__(self, **modellart) -> None:
        self.geladen: list[str] = []
        self.modelle: list[weakref.ref] = []
        self._modellart = modellart

    def __call__(self, backbone_name, modell_wurzel=None):
        self.geladen.append(backbone_name)
        modell = Bildmodell(backbone_name, **self._modellart)
        self.modelle.append(weakref.ref(modell))
        return modell

    @property
    def ladungen(self) -> int:
        return len(self.geladen)

    def noch_gehalten(self) -> int:
        gc.collect()
        return sum(1 for r in self.modelle if r() is not None)


@pytest.fixture
def freigaben(monkeypatch):
    """Zählt die Rufe des Freigabe-Pfads, ohne torch zu berühren."""
    rufe = []

    def frei():
        rufe.append(1)
        return {"belegt_mib": 0, "haelt_bildmodell": False, "satz": "frei (Attrappe)"}

    monkeypatch.setattr(render, "gib_grafikspeicher_frei", frei)
    return rufe


def _auftrag(tmp_path, backbone=Z, *, nummer=0) -> render.RenderAuftrag:
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(MINI_PNG)
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house", backbone=backbone,
                                seed=nummer, ausgabe_png=str(tmp_path / f"bild{nummer}.png"))


def _tabelle(lader) -> dict:
    """Die Werkbank aus ``test_arbeitsgang`` — nur die Bildstufe ist die ECHTE
    ``kette.render_ausfuehrer`` mit zählendem Lader, also ``render.rendere`` selbst."""
    return {**Werkbank().tabelle(), ART_RENDER: kette.render_ausfuehrer(_lader=lader)}


@pytest.fixture
def mappe(tmp_path, glb):
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


@pytest.fixture
def glb(tmp_path):
    import json
    import struct
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


# ======================================================================================
# 1 · Der Befund: drei Varianten, ein Ladevorgang
# ======================================================================================

def test_drei_varianten_laden_das_bildmodell_einmal(mappe, freigaben):
    """**Der Kern des Auftrags.** Vor dem 07.10.2026 stand hier 3 — je Variante einmal
    «Loading pipeline components» (auf-20261001-221)."""
    lader = ZaehlenderLader()
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(lader), varianten=3, cache=None)

    assert ergebnis["vermerkt"] == 3
    assert [lauf.get("status") for lauf in ergebnis["laeufe"]] == ["ok"] * 3
    assert lader.ladungen == 1, f"geladen {lader.ladungen}x statt einmal: {lader.geladen}"


def test_nach_dem_auftrag_ist_das_modell_losgelassen_und_freigegeben(mappe, freigaben):
    lader = ZaehlenderLader()
    arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(lader), varianten=3, cache=None)

    assert lader.noch_gehalten() == 0, "niemand darf das Modell nach dem Auftrag halten"
    assert len(freigaben) == 1, "der Freigabe-Pfad läuft am Ende des Auftrags genau einmal"


def test_ein_zweiter_auftrag_laedt_neu(mappe, freigaben):
    """Zwischen Aufträgen bleibt alles wie vorher: Freigeben, dann neu laden."""
    lader = ZaehlenderLader()
    arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(lader), varianten=3, cache=None)
    arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(lader), varianten=2, cache=None)

    assert lader.ladungen == 2
    assert len(freigaben) == 2


def test_scheitert_eine_variante_wird_trotzdem_freigegeben(mappe, freigaben):
    """Die zweite Variante wirft im Modell. ``rendere`` fängt das (``status='fehler'``),
    das gescheiterte Modell wird **verworfen** — die nächste Variante bekommt ein frisches,
    wie vor dem 07.10.2026 jede Variante — und am Ende ist alles freigegeben."""
    lader = ZaehlenderLader(faellt_beim=2)
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(lader), varianten=3, cache=None)

    assert len(ergebnis["laeufe"]) == 3, "die Reihe läuft nach dem Fehler weiter"
    assert ergebnis["vermerkt"] == 2, "die gescheiterte Variante hat kein Bild"
    assert lader.ladungen == 2, "nach dem Fehler neu geladen, sonst nicht"
    assert lader.noch_gehalten() == 0
    # Einmal vor dem Neuladen (das verworfene Modell soll die Stufenwahl des neuen nicht
    # verdrängen), einmal am Ende des Auftrags.
    assert len(freigaben) == 2


class Abbruch(BaseException):
    """Etwas, das weder ``rendere`` noch die Kette fängt — wie ein Abbruch von aussen."""


def test_ein_abbruch_mitten_im_auftrag_gibt_trotzdem_frei(mappe, freigaben):
    lader = ZaehlenderLader()
    tabelle = _tabelle(lader)
    werk_qa = tabelle[kette.ART_QA]
    rufe = []

    def qa(**kw):
        rufe.append(1)
        if len(rufe) == 2:
            raise Abbruch()
        return werk_qa(**kw)

    tabelle[kette.ART_QA] = qa
    with pytest.raises(Abbruch):
        arbeitsgang.rechne(mappe, ausfuehrer=tabelle, varianten=3, cache=None)

    assert lader.ladungen == 1
    assert lader.noch_gehalten() == 0
    assert len(freigaben) == 1


# ======================================================================================
# 2 · Wechsel des Backbones heisst neu laden — und das alte vorher loslassen
# ======================================================================================

def test_backbone_wechsel_laedt_neu_und_laesst_das_alte_vorher_los(tmp_path, freigaben):
    lader = ZaehlenderLader()
    with render.ein_modell_je_auftrag() as vorrat:
        for nummer, name in enumerate((Z, Z, Z_UNION, Z_UNION, Z)):
            erg = render.rendere(_auftrag(tmp_path, name, nummer=nummer), _lader=lader)
            assert erg["status"] == "ok", erg["error"]
            # Nie zwei Modelle zugleich: Das alte hielte sonst die Karte, und der neue
            # Ladevorgang entschiede sich für die Auslagerung (Befund 01.09.2026,
            # `tools/abholen.py` EinmalGeladen).
            assert lader.noch_gehalten() == 1
        assert vorrat.ladungen == 3

    assert lader.geladen == [Z, Z_UNION, Z]
    # Zweimal beim Wechsel, einmal am Ende.
    assert len(freigaben) == 3
    assert lader.noch_gehalten() == 0


def test_anderer_gewichtsort_laedt_neu(tmp_path, freigaben):
    lader = ZaehlenderLader()
    with render.ein_modell_je_auftrag():
        a = _auftrag(tmp_path, nummer=1)
        render.rendere(a, _lader=lader)
        b = render.RenderAuftrag(**{**a.__dict__, "modell_wurzel": str(tmp_path / "anderswo"),
                                    "ausgabe_png": str(tmp_path / "b.png")})
        render.rendere(b, _lader=lader)
        render.rendere(b, _lader=lader)
    assert lader.ladungen == 2


def test_ein_anderer_schrittzaehler_laedt_neu(tmp_path, freigaben, monkeypatch):
    """Der Zähler wird beim Laden in das Modell gebunden (``_pipeline_adapter``). Ein
    Modell mit dem Zähler eines anderen Laufs meldete dessen Schritte. Der Zähler geht nur
    an den ECHTEN Lader — darum ist hier ``lade_modell`` ersetzt, nicht ``_lader``."""
    geladen = []

    def lade(name, wurzel=None, *, schrittzaehler=None):
        geladen.append(schrittzaehler)
        return Bildmodell(name)

    monkeypatch.setattr(render, "lade_modell", lade)
    eins, zwei = (lambda n: None), (lambda n: None)
    with render.ein_modell_je_auftrag():
        for nummer, zaehler in enumerate((eins, eins, zwei)):
            # Mit Gewichtsort, damit die Ablage nicht nachgeschlagen wird (die gibt es hier
            # nicht) — geprüft wird der Vorrat, nicht die Ablage.
            a = render.RenderAuftrag(**{**_auftrag(tmp_path, nummer=nummer).__dict__,
                                        "modell_wurzel": str(tmp_path)})
            erg = render.rendere(a, schrittzaehler=zaehler)
            assert erg["status"] == "ok", erg["error"]
    assert geladen == [eins, zwei]


# ======================================================================================
# 3 · Ausserhalb eines Auftrags: wie bisher
# ======================================================================================

def test_ohne_auftrag_laedt_rendere_wie_bisher_je_aufruf(tmp_path, freigaben):
    """**Die Gegenprobe.** Wer ``rendere`` direkt ruft (Homeworker, Messwerkzeuge), sieht
    keine Änderung: je Aufruf geladen, nichts behalten, kein zusätzliches Freigeben."""
    lader = ZaehlenderLader()
    for nummer in range(3):
        render.rendere(_auftrag(tmp_path, nummer=nummer), _lader=lader)

    assert lader.ladungen == 3
    assert lader.noch_gehalten() == 0
    assert freigaben == []


def test_ein_uebergebenes_modell_bleibt_unberuehrt_und_nichts_wird_freigegeben(
        tmp_path, freigaben):
    """``tools/abholen.py`` übergibt sein ``EinmalGeladen`` als ``modell=``. Daran ändert
    der Auftrag nichts: kein Vorrat, kein Freigeben — der Betriebsweg des Abholers bleibt
    Wort für Wort, wie er war."""
    eigenes = Bildmodell("eigen")
    with render.ein_modell_je_auftrag() as vorrat:
        for nummer in range(3):
            render.rendere(_auftrag(tmp_path, nummer=nummer), modell=eigenes)
    assert eigenes.aufrufe == 3
    assert vorrat.ladungen == 0
    assert freigaben == []


def test_verschachtelt_gibt_erst_der_aeussere_frei(tmp_path, freigaben):
    lader = ZaehlenderLader()
    with render.ein_modell_je_auftrag() as aussen:
        with render.ein_modell_je_auftrag() as innen:
            assert innen is aussen
            render.rendere(_auftrag(tmp_path, nummer=1), _lader=lader)
        assert freigaben == []
        render.rendere(_auftrag(tmp_path, nummer=2), _lader=lader)
    assert lader.ladungen == 1
    assert len(freigaben) == 1


def test_ein_abgelehnter_auftrag_laedt_nichts(tmp_path, freigaben):
    lader = ZaehlenderLader()
    with render.ein_modell_je_auftrag() as vorrat:
        erg = render.rendere(_auftrag(tmp_path, "flux1-dev"), _lader=lader)
    assert erg["status"] == render.STATUS_ABGELEHNT
    assert vorrat.ladungen == 0 and lader.ladungen == 0
    assert freigaben == []


# ======================================================================================
# 4 · Der Abholer: je Auftrag ein Vorrat, auch über Kameras und Startwerte
# ======================================================================================

def test_der_abholer_laedt_je_auftrag_einmal_ueber_alle_kameras(tmp_path, freigaben):
    lader = ZaehlenderLader()

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        # Die ECHTE Bildstufe, nur mit zählendem Lader — so wie der Abholer sie ohne
        # `_render_modell` ruft.
        return render.rendere(auftrag, _lader=lader, **kw)

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        # Je Kamera eine ANDERE Soll-Karte — sonst hielte der Abholer die Kameras für
        # Zwillinge (`_finde_zwilling`) und rechnete nur die erste.
        _soll=lambda *a, **k: ([[float(next(karten))]], 1, 1))
    karten = iter(range(1000))

    def auftrag(job):
        return {"modell": tmp_path / "m.glb", "job_id": job, "verzeichnis": tmp_path / job,
                "szene": {"kameras": [{"kuerzel": "sSE", "richtung": "sSE"},
                                      {"kuerzel": "nNW", "richtung": "nNW"},
                                      {"kuerzel": "e", "richtung": "e"}],
                          "aufloesung": 64, "hoehe": 64, "samples": 1,
                          "prompt": "a house"}}

    verarbeite(auftrag("vis-1-aaaaaa"))
    assert len(set(lader.geladen)) == 1
    gerechnet = sum(1 for _ in tmp_path.rglob("*.png") if "tiefe" not in _.name)
    assert gerechnet >= 3, f"drei Kameras sollten rechnen, Bilder: {gerechnet}"
    nach_dem_ersten = lader.ladungen
    verarbeite(auftrag("vis-2-bbbbbb"))

    assert nach_dem_ersten == 1, f"drei Kameras, {nach_dem_ersten} Ladevorgänge"
    assert lader.ladungen == 2, "der zweite Auftrag lädt neu"
    assert lader.noch_gehalten() == 0
    assert len(freigaben) == 2
