"""Die Fassung je Knotenart — der Zwischenspeicher lernt den Codestand kennen.

Der Befund, aus dem diese Tests stammen
---------------------------------------
Sitzung 70 (23.09.2026): Nach der Führungs-Reparatur des Bearbeitungsmodells kam ein alter
Knoten weiter **ohne** Führung aus dem Zwischenspeicher der Mappe. Der Schlüssel kannte
Art, Parameter, Vorgänger und Dateiinhalte, aber nicht den Code. Für ihn hatte sich
nichts geändert — also ein Treffer, und ein falscher.

Die Reparatur ist eine Zahl je Art (``kette.FASSUNGEN``), die in den Schlüssel eingeht,
sobald sie über der Anfangsfassung liegt. Zwei Zusagen stehen darin, und beide werden
hier gehalten:

1. **Wer nichts hochzählt, verliert nichts.** Jeder Schlüssel ist bei der Anfangsfassung
   bitgleich mit dem vor Einführung der Fassung. Belegt über **festgeschriebene** Hashes,
   die mit dem alten Code gerechnet wurden — ein Vergleich neu gegen neu bewiese nichts,
   denn er fiele auch dann gleich aus, wenn beide Seiten sich verschoben hätten.
2. **Wer hochzählt, trifft genau eine Art** — und über die Vorgänger-Hashes, was auf ihr
   aufbaut. Belegt am Lauf mit gezählten Attrappen, nicht an der Laufzeit.

Regel 3: Alle Daten sind synthetisch und entstehen hier.
"""
from __future__ import annotations

from collections import Counter

import pytest

from aiimaging import abholer, kette
from aiimaging.graph import (
    FASSUNG_ANFANG,
    ArtefaktCache,
    GraphError,
    Knoten,
    inhalts_hash,
)
from aiimaging.kette import (
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_QA,
    ART_RENDER,
    AUSFUEHRER,
    FASSUNGEN,
    KNOTEN_GEOMETRIE,
    KNOTEN_MULTIPASS,
    KNOTEN_QA,
    KNOTEN_RENDER,
    baue_kette,
    fassung_von,
    fuehre_aus,
)

#: Schlüssel, gerechnet mit dem Code **vor** Einführung der Fassung (Stand 92e398b).
#: Nicht nachrechnen und eintragen, wenn einer dieser Tests fällt: Ein anderer Wert hier
#: heisst, dass jeder bestehende Zwischenspeicher an der HomeStation verworfen wird.
ALTER_HASH_RENDER = "253988c7c6e0312f338c82f1b66c0d6b5f615c3eb6db0bf9ff53c245efb133fb"

ALTE_KNOTENHASHES = {
    "geometrie": "f9ba3e998f2814e71eb47bd10626325c26e09c764e3e2c9c587ad301e57ca537",
    "multipass": "97a16eef17eda7597d5a4543a8a0c69a56e0e665ca51048d9b2916613e42004a",
    "render": "18e1cc0546143b0763749a9f4715333c057e6f8a16e823ae325c6a3765b2838b",
    "qa": "e0b901a90be6a003799e1213455f6974fc5925805465c0af005eb8b02b14c2d1",
    "bildquelle": "9279b66c4c9941ad8470b02a5dd29fe3e3f189f739d0453f38e792a5cafd131a",
    "nachrender": "0a7d9a82fc954b629bd0d991b5d5d4b50457b830e169c128d3b14ce87b3b2e1d",
}

ALTER_MULTIPASS_SCHLUESSEL = "efc21642505e25812e8a285dc3a5813f84c4a1ae4328aaa4005f1ad91110a41b"


def render_knoten() -> Knoten:
    return Knoten("bild", "render", {"prompt": "Wohnhaus", "kamera": {"b": 2, "a": 1}})


def probeknoten(art: str) -> Knoten:
    return Knoten("x", art, {"modell": "attrappe", "seed": 7})


# ======================================================================================
# 1 · Der Kern: graph.inhalts_hash
# ======================================================================================

def test_ohne_fassung_bleibt_der_hash_bitgleich_mit_dem_alten():
    """Die Zusage an jeden bestehenden Zwischenspeicher: nichts verschiebt sich."""
    assert inhalts_hash(render_knoten(), ["aaa", "bbb"]) == ALTER_HASH_RENDER


def test_die_anfangsfassung_ausdruecklich_genannt_ist_dasselbe_wie_keine():
    """Wer ``fassung=FASSUNG_ANFANG`` übergibt, darf keinen anderen Schlüssel bekommen als
    wer nichts übergibt — sonst hinge der Treffer daran, wie der Aufruf geschrieben ist."""
    assert (inhalts_hash(render_knoten(), ["aaa", "bbb"], fassung=FASSUNG_ANFANG)
            == ALTER_HASH_RENDER)


def test_eine_hoehere_fassung_aendert_den_hash():
    alt = inhalts_hash(render_knoten(), ["aaa", "bbb"])
    zwei = inhalts_hash(render_knoten(), ["aaa", "bbb"], fassung=FASSUNG_ANFANG + 1)
    drei = inhalts_hash(render_knoten(), ["aaa", "bbb"], fassung=FASSUNG_ANFANG + 2)
    assert len({alt, zwei, drei}) == 3, "jede Fassung braucht ihren eigenen Schlüssel"


def test_gleiche_fassung_gleicher_hash():
    """Hochgezählt ist nicht zufällig: Dieselbe Fassung trifft denselben Eintrag wieder."""
    assert (inhalts_hash(render_knoten(), [], fassung=2)
            == inhalts_hash(render_knoten(), [], fassung=2))


@pytest.mark.parametrize("fassung", [0, -1, True, False, 1.0, 2.5, "2", None])
def test_unbrauchbare_fassung_wird_abgelehnt(fassung):
    """Laut statt still umgedeutet. ``True`` ist in Python die Zahl 1 — als Fassung wäre
    es ein Tippfehler, der zufällig den alten Schlüssel ergäbe. ``0`` wäre ein
    Herunterzählen unter den Anfang."""
    with pytest.raises(GraphError, match="fassung"):
        inhalts_hash(render_knoten(), [], fassung=fassung)


# ======================================================================================
# 2 · Die Bildkette: kette.FASSUNGEN
# ======================================================================================

def test_jede_art_der_kette_hat_ihre_zeile_zum_hochzaehlen():
    """Der Ort zum Hochzählen soll nicht erst gesucht werden müssen. Eine neue Art in
    ``AUSFUEHRER`` ohne Zeile hier fiele sonst erst auf, wenn ihr Code sich ändert — und
    dann sucht jemand unter Zeitdruck."""
    assert set(FASSUNGEN) == set(AUSFUEHRER)


def test_heute_steht_jede_art_auf_der_anfangsfassung():
    """Gehört zu diesem Commit: Er führt den Mechanismus ein, er zählt nichts hoch. Wer
    eine Art hochzählt, passt diese Zeile an — bewusst, und mit Ansage an die HomeStation.
    """
    assert all(f == FASSUNG_ANFANG for f in FASSUNGEN.values()), FASSUNGEN


@pytest.mark.parametrize("art", sorted(ALTE_KNOTENHASHES))
def test_unveraenderte_art_behaelt_ihren_alten_knotenhash(art):
    """Je Art festgeschrieben: der Schlüssel, den der Zwischenspeicher der Mappe heute
    schon unter sich hat. Rechnet ``_knoten_hash`` bei der Anfangsfassung anders, wäre der
    ganze Speicher verworfen."""
    assert kette._knoten_hash(probeknoten(art), ["aaa"]) == ALTE_KNOTENHASHES[art]


def test_fremde_art_bekommt_die_anfangsfassung():
    """Eine Art ohne Zeile (ein Test, eine künftige Stufe) darf keinen Speicher verwerfen."""
    assert fassung_von("gibt-es-nicht") == FASSUNG_ANFANG


def test_hochgezaehlte_art_bekommt_einen_neuen_hash_die_anderen_nicht(monkeypatch):
    """Genau eine Art — nicht der ganze Speicher. Das ist der Unterschied zu einem
    geänderten ``HASH_SCHEMA_ID``."""
    monkeypatch.setitem(FASSUNGEN, kette.ART_NACHRENDER, FASSUNG_ANFANG + 1)

    for art, alt in ALTE_KNOTENHASHES.items():
        neu = kette._knoten_hash(probeknoten(art), ["aaa"])
        if art == kette.ART_NACHRENDER:
            assert neu != alt, "hochgezählt, und der Schlüssel blieb — der Fall aus Sitzung 70"
        else:
            assert neu == alt, f"{art} wurde nicht angefasst und verlor trotzdem den Schlüssel"


# ======================================================================================
# 3 · Am Lauf gezählt: was rechnet nach dem Hochzählen neu?
# ======================================================================================

class Werkbank:
    """Gezählte Attrappen, die winzige echte Dateien schreiben (sonst verwirft
    ``fuehre_aus`` jeden Treffer, weil die zugesagten Dateien fehlen). Dieselbe Bauform
    wie in ``test_kette.py``."""

    def __init__(self) -> None:
        self.aufrufe: Counter = Counter()

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_GEOMETRIE] += 1
        glb = out_dir / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_MULTIPASS] += 1
        tiefe, beauty = out_dir / "tiefe_norm.png", out_dir / "beauty.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        beauty.write_text("beauty", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe), "beauty_png": str(beauty)}

    def render(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_RENDER] += 1
        bild = out_dir / "bild.png"
        bild.write_text("bild", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild)}

    def qa(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_QA] += 1
        return {"status": "ok", "bestanden": True, "score": 0.9}


def test_hochgezaehlter_render_rechnet_render_und_qa_neu_der_rest_trifft(tmp_path,
                                                                        monkeypatch):
    """**Der Fall aus Sitzung 70, am Lauf.** Der Render-Code ändert sich, die Fassung wird
    hochgezählt: Der Render rechnet neu, die QA dahinter auch (ihr Eingang ist ein anderes
    Bild), Geometrie und Multipass kommen weiter aus dem Speicher. Gezählt, nicht gemessen.
    """
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCHE-GEOMETRIE", encoding="utf-8")
    graph = baue_kette(ifc_path=str(ifc), prompt="Morgenlicht")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")

    def lauf():
        return fuehre_aus(graph, cache=cache, ausfuehrer=werkbank.tabelle(),
                          out_dir=tmp_path / "out")

    lauf()
    zweiter = lauf()
    assert zweiter["cache_treffer"] == 4, "ohne Hochzählen bleibt alles ein Treffer"

    monkeypatch.setitem(FASSUNGEN, ART_RENDER, FASSUNG_ANFANG + 1)
    dritter = lauf()

    assert werkbank.aufrufe == Counter(
        {ART_GEOMETRIE: 1, ART_MULTIPASS: 1, ART_RENDER: 2, ART_QA: 2})
    assert dritter["knoten"][KNOTEN_GEOMETRIE]["aus_cache"] is True
    assert dritter["knoten"][KNOTEN_MULTIPASS]["aus_cache"] is True
    assert dritter["knoten"][KNOTEN_RENDER]["aus_cache"] is False
    assert dritter["knoten"][KNOTEN_QA]["aus_cache"] is False

    # Und die neue Fassung ist ihrerseits ein Treffer — hochzählen heisst einmal neu
    # rechnen, nicht jedes Mal.
    vierter = lauf()
    assert vierter["cache_treffer"] == 4
    assert werkbank.aufrufe[ART_RENDER] == 2


# ======================================================================================
# 4 · Der Multipass-Speicher des Abholers liest dieselbe Zeile
# ======================================================================================

@pytest.fixture
def einstellungen(tmp_path):
    glb = tmp_path / "modell.glb"
    glb.write_text("SYNTHETISCHE-GLB-A", encoding="utf-8")
    return dict(glb_path=str(glb), up_axis="Y", aufloesung=1600, hoehe=1000,
                samples=128, kamera="sSE", out_dir="/irgendwo")


def test_multipass_schluessel_des_abholers_bleibt_bitgleich(einstellungen):
    """Auch der zweite Speicher — der des Abholers — verliert bei der Anfangsfassung
    nichts. Der Pfad zählt nicht, nur der Inhalt; darum ist der Wert über ``tmp_path``
    hinweg fest."""
    assert (abholer.multipass_schluessel(einstellungen, blender="Blender 4.2.1 LTS")
            == ALTER_MULTIPASS_SCHLUESSEL)


def test_hochgezaehlter_multipass_verwirft_auch_den_speicher_des_abholers(einstellungen,
                                                                           monkeypatch):
    """Eine Zeile, zwei Speicher. Stünde die Fassung nur in der Mappe, rechnete der
    Abholer nach einer Multipass-Reparatur weiter aus dem alten Speicher."""
    monkeypatch.setitem(FASSUNGEN, ART_MULTIPASS, FASSUNG_ANFANG + 1)
    assert (abholer.multipass_schluessel(einstellungen, blender="Blender 4.2.1 LTS")
            != ALTER_MULTIPASS_SCHLUESSEL)

