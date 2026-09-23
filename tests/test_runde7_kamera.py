"""Kameraangaben wirken nur auf dem Weg, auf dem sie gerechnet werden — Befund 23.09.2026.

Was nachgelesen wurde
---------------------
(A) ``augenhoehe``, ``bias_grad`` und ``kamera_modus`` gehen im Runner nur in
    ``kameras.kamerasatz`` — und das wird nur auf dem Kameraweg ``abgeleitet`` gerechnet
    (Kamera aus dem Richtungskürzel). Angenommen wurden sie auf jedem Weg: von der Kette,
    von ``seams`` und vom Homeworker. Der Blender-Bericht sagte dazu nichts. Dieselbe
    Fehlerart wie beim Deckungsgrad am 22.09.2026
    (``tests/test_deckungsgrad_wirkt_nur_abgeleitet.py``).
(C) ``kamera`` zusammen mit ``auge``: ``seams`` liess das Kürzel still fallen. Die Kette
    weist die Kombination seit dem 22.09.2026 ab, ``seams`` nicht — und der Homeworker
    setzte ``kamera`` IMMER (``VORGABE_KAMERA``), auch neben einem Standpunkt von Hand.

Was hier bewacht ist, jeweils an der WIRKUNG
--------------------------------------------
1. Runner (``main`` mit einer Attrappe von ``bpy``, die Kamera läuft echt): Auf
   ``abgeleitet`` stehen die benutzten Werte im Bericht, und zwei Werte ergeben zwei
   Kameras. Sonst ``None`` und, **nur wenn bestellt**, ``<name>_wirkungslos`` mit Grund.
   Der Rückfall ohne erreichbare Bibliothek stürzt nicht ab.
2. Kette (``baue_kette`` und der echte Multipass-Ausführer): Die drei Angaben ohne
   ``kamera`` werden abgewiesen, Blender wird nicht gerufen.
3. ``seams``: ``kamera`` und ``auge`` zugleich → ``SeamError``, bevor aufgeräumt oder
   gestartet wird. Die drei heutigen Aufgabenformen des Abholers (auto, innen,
   mitgesandt) laufen über den Produktweg bis in die ECHTE Kommandobildung und fallen
   nicht.
4. Homeworker (``fuehre_aus``, dahinter der ECHTE ``seams.glb_zu_multipass`` bis zum
   Blender-Start, der eine Attrappe ist): Mit ``auge``/``blick_auf`` wird kein Kürzel
   gesetzt, die vier nur-mit-Kürzel-Angaben gehen nicht an Blender, und das Ergebnis
   nennt sie als wirkungslos.

Regel 2: Der Runner wird als Datei geladen, nicht als Modul importiert. Regel 3: Szene,
Standpunkte und Aufträge sind synthetisch.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import abholer, kameras, kette, seams
from aiimaging.kette import ART_MULTIPASS, KNOTEN_MULTIPASS
from aiimaging.seams import SeamError

from test_homeworker import GLB_BERICHT, hw
from test_interior_bestellung import _lauf, _szene, ifc_naht  # noqa: F401 (Fixture)

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")

SZENE = ([0.0, 0.0, 0.0], [20.0, 16.0, 9.0])
BBOX = [list(SZENE[0]), list(SZENE[1])]
AUGE = ["--auge=40,-30,1.7", "--blick-auf=10,8,4.5"]
AUGE_L = [40.0, -30.0, 1.7]
BLICK_L = [10.0, 8.0, 4.5]

#: Berichtsname → (Schalter des Runners mit Wert, Wert, Feld in der Herkunft)
BESTELLUNGEN = {
    "augenhoehe": ("--augenhoehe=1.3", 1.3, "augenhoehe_m"),
    "bias_grad": ("--bias=20", 20.0, "bias_grad"),
    "kamera_modus": ("--kamera-modus=gekippt", "gekippt", "modus"),
}


# ======================================================================================
# Die Attrappe — gerade so viel Blender, wie `main` bis zum Bericht anfasst
# ======================================================================================

class _Vektor(list):
    def __add__(self, anderer):
        return _Vektor(a + b for a, b in zip(self, anderer))

    def __sub__(self, anderer):
        return _Vektor(a - b for a, b in zip(self, anderer))

    def __mul__(self, zahl):
        return _Vektor(a * zahl for a in self)

    def to_track_quat(self, *_):
        return (1.0, 0.0, 0.0, 0.0)


class _Objekte(list):
    def new(self, name, daten):
        return SimpleNamespace(name=name, data=daten, type="CAMERA")


def _runner(monkeypatch, *, ohne_bibliothek: bool = False):
    bpy = mock.MagicMock()
    bpy.app.version_string = "attrappe"
    bpy.data.objects = _Objekte()
    bpy.data.materials = []
    bpy.data.cameras.new = lambda name: SimpleNamespace(
        lens=50.0, shift_y=0.0, sensor_fit="AUTO", sensor_width=36.0)
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "mathutils", SimpleNamespace(Vector=_Vektor))

    spez = importlib.util.spec_from_file_location("blender_pruefling_runde7", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    monkeypatch.setattr(modul, "_bbox_aller_meshes", lambda: (list(SZENE[0]), list(SZENE[1])))
    monkeypatch.setattr(modul, "_bbox_bauwerk", lambda: (
        list(SZENE[0]), list(SZENE[1]), "", None,
        {"entschieden_durch": "keine", "gelaende_namen": []}))
    monkeypatch.setattr(modul, "_sonne_setzen", lambda *a, **k: (None, {"attrappe": True}))
    monkeypatch.setattr(modul, "_compositor_auf_tiefe", lambda out: "attrappe")
    monkeypatch.setattr(modul, "_welt_setzen", lambda *a, **k: None)
    if ohne_bibliothek:
        monkeypatch.setattr(modul, "_kameras_modul", lambda: None)
    return modul


def _bericht(monkeypatch, tmp_path, *schalter, ohne_bibliothek=False) -> dict:
    modul = _runner(monkeypatch, ohne_bibliothek=ohne_bibliothek)
    aus = tmp_path / f"lauf_{sum(1 for _ in tmp_path.iterdir())}"
    monkeypatch.setattr(sys, "argv", ["blender", "--background", "--python", "x.py", "--",
                                      "--glb", "m.glb", "--out", str(aus),
                                      "--ohne-material-id", *schalter])
    modul.main()
    return json.loads((aus / "blender-report.json").read_text(encoding="utf-8"))


def _stellung(bericht) -> tuple:
    k = bericht["kamera"]
    return (tuple(k["auge"]), tuple(k["blick_auf"]), k["shift_y"])


# ======================================================================================
# 1 · Am Runner
# ======================================================================================

@pytest.mark.parametrize("name", sorted(BESTELLUNGEN))
def test_abgeleitet_meldet_den_benutzten_wert_und_er_wirkt(monkeypatch, tmp_path, name):
    """Der einzige Weg, auf dem gerechnet wird. Die Gegenprobe (Vorgabe gegen
    Bestellung) belegt, dass die Angabe dort WIRKT — sonst prüfte der Test nur eine Zahl."""
    schalter, wert, feld = BESTELLUNGEN[name]
    bestellt = _bericht(monkeypatch, tmp_path, "--kamera", "sSE", schalter)
    vorgabe = _bericht(monkeypatch, tmp_path, "--kamera", "sSE")

    assert bestellt["kamera"]["weg"] == "abgeleitet"
    assert bestellt[name] == (wert if isinstance(wert, str) else pytest.approx(wert))
    assert bestellt["kamera"][feld] == bestellt[name], (
        "Bericht und Herkunft muessen denselben, WIRKLICH benutzten Wert tragen.")
    assert bestellt[f"{name}_wirkungslos"] is None
    assert _stellung(bestellt) != _stellung(vorgabe), (
        f"Auf dem abgeleiteten Weg muss {name} die Kamera veraendern.")


def test_abgeleitet_ohne_bestellung_meldet_die_vorgaben_der_bibliothek(monkeypatch, tmp_path):
    """Nicht bestellt heisst nicht «nicht gerechnet»: Auf ``abgeleitet`` steht der Wert,
    mit dem die Kamera gestellt wurde — die Vorgabe der Bibliothek, nicht eine eigene."""
    bericht = _bericht(monkeypatch, tmp_path, "--kamera", "sSE")
    assert bericht["augenhoehe"] == pytest.approx(kameras.AUGENHOEHE_M)
    assert bericht["bias_grad"] == pytest.approx(kameras.BIAS_GRAD)
    assert bericht["kamera_modus"] == kameras.MODUS_SHIFT
    assert all(bericht[f"{n}_wirkungslos"] is None for n in BESTELLUNGEN)


@pytest.mark.parametrize("weg, grundschalter", [("vorgegeben", AUGE), ("rueckfall", [])])
@pytest.mark.parametrize("name", sorted(BESTELLUNGEN))
def test_ohne_abgeleitete_kamera_ist_die_bestellung_wirkungslos_und_gemeldet(
        monkeypatch, tmp_path, weg, grundschalter, name):
    """**Der Kern von (A).** Mit und ohne Bestellung dieselbe Kamera — also darf im
    Bericht kein Wert stehen, und die übergangene Bestellung muss mit Grund dastehen."""
    schalter, wert, _ = BESTELLUNGEN[name]
    bestellt = _bericht(monkeypatch, tmp_path, *grundschalter, schalter)
    ohne = _bericht(monkeypatch, tmp_path, *grundschalter)

    assert bestellt["kamera"]["weg"] == weg
    assert _stellung(bestellt) == _stellung(ohne), (
        "Voraussetzung des Befunds: Auf diesem Weg wirkt die Angabe nicht.")
    assert bestellt[name] is None, "None heisst NICHT GESTELLT — eine Zahl behauptete es."
    grund = bestellt[f"{name}_wirkungslos"]
    assert isinstance(grund, str) and weg in grund and repr(wert) in grund, grund


def test_ohne_bestellung_ist_nichts_wirkungslos(monkeypatch, tmp_path):
    """Entscheid 23.09.2026: Eine Vorgabe, die niemand bestellt hat, ist nicht
    «wirkungslos bestellt». Die Werte bleiben trotzdem ``None`` — gestellt wurden sie
    auf diesem Weg nicht."""
    bericht = _bericht(monkeypatch, tmp_path, *AUGE)
    for name in BESTELLUNGEN:
        assert bericht[name] is None
        assert bericht[f"{name}_wirkungslos"] is None


def test_rueckfall_ohne_bibliothek_stuerzt_nicht_ab_und_meldet_alle_drei(
        monkeypatch, tmp_path):
    """Der Nebenfund von Runde 6 auf dem Rückfall ohne Bibliothek, für die neuen Felder."""
    bericht = _bericht(monkeypatch, tmp_path, "--kamera", "sSE",
                       *(s for s, _, _ in BESTELLUNGEN.values()), ohne_bibliothek=True)
    assert bericht["kamera"]["weg"] == "rueckfall"
    for name in BESTELLUNGEN:
        assert bericht[name] is None
        assert "rueckfall" in bericht[f"{name}_wirkungslos"]


# ======================================================================================
# 2 · An der Kette
# ======================================================================================

@pytest.fixture
def naht(monkeypatch):
    aufrufe: list[dict] = []

    def glb_zu_multipass(glb_path, out_dir, **kw):
        aufrufe.append(kw)
        tiefe = Path(out_dir) / "tiefe_norm.png"
        tiefe.write_text("t", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe)}

    monkeypatch.setattr(seams, "glb_zu_multipass", glb_zu_multipass)
    return aufrufe


def _multipass(tmp_path, **bestellung) -> dict:
    graph = kette.baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Z",
                             prompt="Haus", bbox=BBOX, **bestellung)
    return kette.AUSFUEHRER[ART_MULTIPASS](
        knoten=graph.knoten[KNOTEN_MULTIPASS],
        eingaben=[{"glb_path": str(tmp_path / "m.glb"), "up_axis": "Z"}],
        out_dir=tmp_path)


KETTENWERTE = {"augenhoehe": 1.3, "bias_grad": 20.0, "kamera_modus": "gekippt"}


@pytest.mark.parametrize("ohne_kamera", [
    {},                                                   # Rückfall
    {"auge": AUGE_L, "blick_auf": BLICK_L},               # vorgegeben
])
@pytest.mark.parametrize("name", sorted(KETTENWERTE))
def test_kette_weist_die_angabe_ohne_kamera_ab(tmp_path, naht, ohne_kamera, name):
    aus = _multipass(tmp_path, **{name: KETTENWERTE[name]}, **ohne_kamera)
    assert aus["status"] == kette.STATUS_FEHLER
    assert "kein Kameraweg" in aus["error"] and f"`{name}`" in aus["error"], aus["error"]
    assert naht == [], "Abgewiesen heisst: Blender wird gar nicht erst gerufen."


def test_kette_gegenprobe_mit_kamera_kommt_alles_an(tmp_path, naht):
    aus = _multipass(tmp_path, kamera="sSE", **KETTENWERTE)
    assert aus["status"] == kette.STATUS_OK
    assert {n: naht[0][n] for n in KETTENWERTE} == KETTENWERTE


# ======================================================================================
# 3 · An der Naht `seams`
# ======================================================================================

def _verweigerer(cmd, timeout):
    raise AssertionError(f"gestartet, obwohl abgewiesen: {cmd}")


def test_seams_weist_kamera_und_auge_ab_bevor_aufgeraeumt_oder_gestartet_wird(tmp_path):
    aus = tmp_path / "aus"
    aus.mkdir()
    vorlauf = aus / "blender-report.json"
    vorlauf.write_text("{}", encoding="utf-8")

    with pytest.raises(SeamError, match="Standpunkt zweimal bestellt"):
        seams.glb_zu_multipass("m.glb", aus, up_axis="Y", kamera="sSE",
                               auge=AUGE_L, blick_auf=BLICK_L, _starte=_verweigerer)
    assert vorlauf.exists(), "Eine Bestellung, die nie laufen konnte, loescht nichts."

    with pytest.raises(SeamError, match="Standpunkt zweimal bestellt"):
        seams.baue_kommando_multipass("m.glb", aus, up_axis="Y", kamera="sSE",
                                      auge=AUGE_L, blick_auf=BLICK_L)


def test_seams_gegenproben_je_eine_quelle():
    mit_kamera = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", kamera="sSE")
    von_hand = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y",
                                             auge=AUGE_L, blick_auf=BLICK_L)
    assert "--kamera" in mit_kamera and not any(a.startswith("--auge") for a in mit_kamera)
    assert "--kamera" not in von_hand and any(a.startswith("--auge") for a in von_hand)


def _durch_die_echte_kommandobildung(kw: dict) -> list[str]:
    """Was der Abholer an den Multipass schickt, durch ``seams.baue_kommando_multipass``.

    Dieselbe gemeinsame Stelle (``_multipass_argumente``), die auch der echte Lauf nimmt.
    Weggelassen werden nur die beiden Fristen, die das Kommando nicht betreffen."""
    kw = dict(kw)
    kw.pop("timeout", None)
    kw.pop("stillstand_frist_s", None)
    return seams.baue_kommando_multipass("m.glb", "aus", **kw)


def test_abholer_auto_richtungen_fallen_nicht(tmp_path):
    szene = _szene(geometry={"path": "model.glb", "format": "glb"})
    del szene["interior"]
    antwort, protokoll, _ = _lauf(tmp_path, szene)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"]
    for kw in protokoll["multipass"]:
        kommando = _durch_die_echte_kommandobildung(kw)
        assert "--kamera" in kommando


def test_abholer_innenansicht_faellt_nicht(tmp_path, ifc_naht):
    antwort, protokoll, _ = _lauf(tmp_path, _szene())
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    (kw,) = protokoll["multipass"]
    kommando = _durch_die_echte_kommandobildung(kw)
    assert "--kamera" not in kommando and any(a.startswith("--auge=") for a in kommando)


def test_abholer_mitgesandte_kameras_fallen_nicht(tmp_path, ifc_naht):
    mitgesandt = [{"name": "Innen-1", "position": [6.0, 1.0, 1.6],
                   "target": [6.0, 2.4, 1.6], "fov": 70, "up_axis": "z"}]
    antwort, protokoll, _ = _lauf(tmp_path, _szene(cameras=mitgesandt))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    (kw,) = protokoll["multipass"]
    kommando = _durch_die_echte_kommandobildung(kw)
    assert "--kamera" not in kommando and any(a.startswith("--auge=") for a in kommando)


# ======================================================================================
# 4 · Am Homeworker — bis in den echten `seams.glb_zu_multipass`
# ======================================================================================

@pytest.fixture
def blender_start(monkeypatch, tmp_path):
    """Nur der Blender-Start und die EXR-Normalisierung sind Attrappen.

    ``fuehre_aus`` ruft ``seams.glb_zu_tiefenkarte``; dahinter läuft der ECHTE
    ``glb_zu_multipass`` samt Abweisung und Kommandobildung. Zurück kommt die Liste der
    Kommandos, die an Blender gegangen wären."""
    echt = seams.glb_zu_multipass
    kommandos: list[list[str]] = []

    def starte(cmd, timeout):
        kommandos.append(list(cmd))
        aus = Path(cmd[cmd.index("--out") + 1])
        (aus / "blender-report.json").write_text(
            json.dumps({"status": "ok", "kamera": {"weg": "attrappe"}}), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def nachbearbeiten(report, out_dir, **_kw):
        ziel = Path(out_dir) / "tiefe_norm.png"
        ziel.write_bytes(b"\x89PNG\r\n\x1a\n")
        report["depth_png"] = str(ziel)
        return report

    monkeypatch.setenv("AIIMAGING_BLENDER", "blender")
    monkeypatch.setattr(seams, "_tiefe_nachbearbeiten", nachbearbeiten)
    monkeypatch.setattr(seams, "ifc_zu_glb", lambda ifc, glb, **kw: dict(GLB_BERICHT))
    monkeypatch.setattr(seams, "glb_zu_tiefenkarte",
                        lambda glb, aus, **kw: echt(glb, aus, _starte=starte, **kw))
    return kommandos


def _hw_satz(tmp_path, art="multipass", **params) -> dict:
    ifc = tmp_path / "bau.ifc"
    ifc.write_text("ISO-10303-21;\n", encoding="utf-8")
    return {"auftrag_id": "auf-20260923-97", "art": art,
            "geometrie": {"synthetisch": False, "pfad": str(ifc)},
            "params": {"out_dir": str(tmp_path / "aus"), **params}}


NUR_MIT_KAMERA = {"augenhoehe": 1.3, "bias_grad": 20.0, "kamera_modus": "gekippt",
                  "deckungsgrad": 0.55}
SCHALTER = ("--augenhoehe", "--bias", "--kamera-modus", "--deckungsgrad")


def test_homeworker_standpunkt_von_hand_kommt_ohne_kuerzel_bei_blender_an(
        tmp_path, blender_start):
    """**Der Wächter von Punkt 4.** Bis zum 23.09.2026 setzte der Homeworker immer
    ``kamera``; mit der Abweisung in ``seams`` fiele JEDER Auftrag mit Standpunkt von
    Hand — und vorher fiel das Kürzel still weg."""
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, auge=AUGE_L, blick_auf=BLICK_L,
                                      brennweite=24.0, **NUR_MIT_KAMERA), tmp_path)

    assert ergebnis["status"] == "ok", ergebnis["fehler"]
    (kommando,) = blender_start
    assert "--kamera" not in kommando
    assert "--auge=40.0,-30.0,1.7" in kommando
    assert "--brennweite=24.0" in kommando, "was auf jedem Weg wirkt, geht weiter mit"
    assert not [a for a in kommando if a.startswith(SCHALTER)], kommando

    befund = ergebnis["messwerte"]["kamerabestellung"]
    # Seit der Runde 7b (23.09.2026) "von_hand" statt None — None hiesse «unbekannt».
    assert befund["kamera"] is None and befund["kamera_quelle"] == "von_hand"
    assert sorted(befund["wirkungslos"]) == sorted(NUR_MIT_KAMERA), (
        "Nicht still verworfen: Jede nicht weitergereichte Angabe steht mit Grund da.")
    assert all(repr(NUR_MIT_KAMERA[n]) in s for n, s in befund["wirkungslos"].items())


def test_homeworker_kamera_und_auge_ausdruecklich_wird_nicht_geordnet(
        tmp_path, blender_start, monkeypatch):
    umgewandelt = []
    monkeypatch.setattr(seams, "ifc_zu_glb",
                        lambda ifc, glb, **kw: umgewandelt.append(ifc) or dict(GLB_BERICHT))
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, kamera="nNW", auge=AUGE_L,
                                      blick_auf=BLICK_L), tmp_path)
    assert ergebnis["status"] == "fehler"
    assert ergebnis["urteil"] == {"auftrag": "standpunkt zweimal bestellt"}
    assert "Standpunkt zweimal bestellt" in ergebnis["fehler"]
    assert blender_start == [] and umgewandelt == [], "weder umgewandelt noch gestartet"


def test_homeworker_gegenprobe_ohne_auge_bleibt_alles_wie_bisher(tmp_path, blender_start):
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, **NUR_MIT_KAMERA), tmp_path)
    assert ergebnis["status"] == "ok", ergebnis["fehler"]
    (kommando,) = blender_start
    assert kommando[kommando.index("--kamera") + 1] == hw.VORGABE_KAMERA
    assert "--augenhoehe=1.3" in kommando and "--deckungsgrad=0.55" in kommando
    assert "--bias=20.0" in kommando and "--kamera-modus=gekippt" in kommando
    befund = ergebnis["messwerte"]["kamerabestellung"]
    assert befund == {"kamera": hw.VORGABE_KAMERA, "kamera_quelle": "vorgabe",
                      "wirkungslos": {}}


def test_homeworker_render_weg_traegt_den_befund_auch(tmp_path, blender_start):
    """Auch der ``render``-Zweig — hier an seinem ersten Ausgang (Regel 1 vor dem
    Render), der ohne GPU erreichbar ist."""
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, art="render", prompt="Haus",
                                      schaetzer="depth-anything-v2-large",
                                      auge=AUGE_L, blick_auf=BLICK_L, augenhoehe=1.3),
                             tmp_path)
    assert ergebnis["urteil"].get("regel_1") == "abgelehnt"
    assert list(ergebnis["messwerte"]["kamerabestellung"]["wirkungslos"]) == ["augenhoehe"]
