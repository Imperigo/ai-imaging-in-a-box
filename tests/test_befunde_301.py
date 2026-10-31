"""Befunde aus auf-20261021-301 — was danach gebaut ist (Protokoll 74, C99).

* **A1:** Bei der Abweisung in der Vorprüfung steht der Satz jetzt auch in ``job.json/message``
  (bisher nur in ``error`` und im Ergebnis). Die Abweisung im Prozess tat das schon.
* **A2:** Die zweite Speicherprüfung im Prozess (``render.lade_modell``) schreibt ihre Zahlen —
  verfügbar, frei, eigen, verlangt — über ``tools/abholen.py`` ins Journal.
* **A3:** Der Satz der Vorprüfung steht als eigene, ungekürzte Zeile im Journal, auch nach dem
  Entladen des eigenen Sprachmodells.
* **A6:** Ausserhalb des Abholers findet der Tiefenschätzer die Modellwurzel aus derselben
  Einstellung wie der Abholer (seine Einheit) und lädt nie aus dem Netz.

Attrappen statt Karte und Gewichte, Pfade synthetisch unter ``tmp_path`` (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, render
from aiimaging import tiefenschaetzer as ts

WURZEL = Path(__file__).resolve().parents[1]

#: auf-20261021-300/301: frei vor dem Lauf (nvidia-smi), im Prozess (mem_get_info).
FREI_VORHER = 30868
FREI_IM_PROZESS = 30364


def _abholen(name):
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / "abholen.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _ordner(tmp_path, **vis):
    from test_kettenlauf_26august import _auftragsordner
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


# ====================================================================== A1 · message

def test_abweisung_der_vorpruefung_steht_in_message(tmp_path):
    """Wörtlich aus 301 2a: «job_json_message: leer (null)»."""
    from test_befunde_298 import _verarbeiter
    ordner = _ordner(tmp_path, bildeingang=0.55)
    protokoll, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        bildeingang_karte=lambda: {"frei_mib": 15000, "eigen_mib": 0,
                                   "fremde_modelle": ["qwen3:14b"]})
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert protokoll["render"] == []
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert zettel[bruecke.FELD_MELDUNG] == zettel["error"] == antwort["grund"]
    assert zettel[bruecke.FELD_MELDUNG].startswith(render.ABWEIS_BILDEINGANG)
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["lieferstatus_grund"] == zettel[bruecke.FELD_MELDUNG]


def test_auch_zu_wenig_speicher_in_der_vorpruefung_steht_in_message(tmp_path):
    from test_befunde_298 import _verarbeiter
    ordner = _ordner(tmp_path, bildeingang=0.8)
    _p, verarbeite = _verarbeiter(tmp_path)
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                       bildeingang_karte=lambda: {"frei_mib": 20000, "eigen_mib": 0,
                                                  "fremde_modelle": []})
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert "20000 frei" in zettel[bruecke.FELD_MELDUNG]


# ====================================================================== A2 · im Prozess

def _torch(frei_mib):
    cuda = types.SimpleNamespace(
        is_available=lambda: True, is_initialized=lambda: True,
        memory_reserved=lambda: 0, mem_get_info=lambda: (frei_mib * 2**20, 32607 * 2**20))
    return types.SimpleNamespace(bfloat16="bf16", cuda=cuda)


def _diffusers(monkeypatch):
    modul = types.ModuleType("diffusers")
    modul.__version__ = "0.41.0.dev0"
    for name in ("ZImageControlNetModel", "ZImageControlNetPipeline"):
        setattr(modul, name, type(name, (), {}))
    modul.DiffusionPipeline = type("DiffusionPipeline", (), {})
    monkeypatch.setitem(sys.modules, "diffusers", modul)


def _gewichte(tmp_path):
    wurzel = tmp_path / "z-image-turbo"
    for teil in ("transformer", "vae", "text_encoder", "tokenizer"):
        (wurzel / teil).mkdir(parents=True)
    (wurzel / "model_index.json").write_text("{}")
    return wurzel


class _Pipeline:
    def to(self, geraet):
        return self


def _geladen(tmp_path, monkeypatch, frei_mib):
    _diffusers(monkeypatch)
    monkeypatch.setitem(sys.modules, "torch", _torch(frei_mib))
    monkeypatch.setattr(render, "_prozesse_auf_der_karte", lambda: {})
    monkeypatch.setattr(render, "_lade_mit_controlnet", lambda *a, **k: (_Pipeline(), None))
    monkeypatch.setattr(render, "_pipeline_adapter",
                        lambda *a, **k: types.SimpleNamespace(__call__=None))
    return render.lade_modell("z-image-turbo", modell_wurzel=_gewichte(tmp_path),
                              bildeingang=True)


def test_lade_modell_traegt_die_zahlen_der_zweiten_pruefung(tmp_path, monkeypatch):
    """Der Fall aus 301: 30 364 frei im Prozess + 504 Kontext = 30 868 verfügbar."""
    modell = _geladen(tmp_path, monkeypatch, FREI_IM_PROZESS)
    satz = modell.bildeingang_pruefung
    assert f"{FREI_VORHER} MiB verfuegbar ({FREI_IM_PROZESS} frei + 504 eigene)" in satz
    verlangt = render.bildeingang_bedarf("z-image-turbo")["verlangt_frei_mib"]
    assert f"verlangt {verlangt} MiB" in satz


def test_ohne_bildeingang_kein_satz(tmp_path, monkeypatch):
    _diffusers(monkeypatch)
    monkeypatch.setitem(sys.modules, "torch", _torch(FREI_IM_PROZESS))
    monkeypatch.setattr(render, "_lade_mit_controlnet", lambda *a, **k: (_Pipeline(), None))
    monkeypatch.setattr(render, "_lege_auf_geraet", lambda *a, **k: ("cuda", None, None))
    monkeypatch.setattr(render, "_pipeline_adapter", lambda *a, **k: types.SimpleNamespace())
    modell = render.lade_modell("z-image-turbo", modell_wurzel=_gewichte(tmp_path))
    assert modell.bildeingang_pruefung is None


def test_einmal_geladen_schreibt_die_zweite_pruefung_ins_journal(capsys):
    modul = _abholen("abholen_b301_a2")

    def lader(name, wurzel, **kw):
        def modell(parameter):
            return "bild.png"
        modell.bildeingang_pruefung = ("Bildeingang: 30868 MiB verfuegbar (30364 frei + 504 "
                                       "eigene), verlangt 30587 MiB (30075 gemessen + 512 "
                                       "Reserve).")
        return modell

    modul.EinmalGeladen(lader, "backbone", "modell_wurzel")(
        {"backbone": "z-image-turbo", "bildeingang_staerke": 0.55})
    zeile = capsys.readouterr().out
    assert "Im Prozess Bildeingang: 30868 MiB verfuegbar (30364 frei + 504 eigene)" in zeile


def test_einmal_geladen_schreibt_die_abweisung_im_prozess_ins_journal(capsys):
    modul = _abholen("abholen_b301_a2b")
    satz = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=26000, eigen_mib=504)["satz"]

    def lader(name, wurzel, **kw):
        raise render.RenderError(satz)

    with pytest.raises(render.RenderError):
        modul.EinmalGeladen(lader, "backbone", "modell_wurzel")(
            {"backbone": "z-image-turbo", "bildeingang_staerke": 0.55})
    assert f"Im Prozess {satz}" in capsys.readouterr().out


# ====================================================================== A3 · nach dem Entladen

def test_nach_dem_entladen_steht_der_satz_der_vorpruefung(tmp_path, capsys):
    """Wörtlich aus 301 2b: die Karte-Zeile endete nach «Es wird gerechnet.» — gekürzt."""
    from test_befunde_298 import _verarbeiter
    ordner = _ordner(tmp_path, bildeingang=0.55)
    zettel = ordner / bruecke.DATEI_LAUFZETTEL
    daten = json.loads(zettel.read_text(encoding="utf-8"))
    daten["idle_window_only"] = True
    zettel.write_text(json.dumps(daten), encoding="utf-8")
    geladen = ["qwen3:14b"]
    lang = ("Danach: Auslastung 34 % (ueber 10 %), aber nur 1241 MiB belegt (Grenze 4096) — "
            "beschaeftigt, nicht belegt. Es wird gerechnet.")

    def karte():
        return (not geladen), (lang if not geladen else "17330 MiB belegt")

    def entladen():
        geladen.clear()
        return {"entladen": True, "satz": "Das Sprachmodell qwen3:14b ist entladen; die "
                                          "Grafikkarte gehört dem Bild."}

    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        darf_rechnen=abholer.karte_oder_eigenes_entladen(karte, entladen, _warte=lambda s: None),
        bildeingang_karte=lambda: {"frei_mib": FREI_VORHER, "eigen_mib": 0,
                                   "fremde_modelle": list(geladen)})
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert antwort["bildeingang"].startswith(f"Bildeingang: {FREI_VORHER} MiB verfuegbar")
    _abholen("abholen_b301_a3")._berichte({"ergebnisse": [antwort]})
    aus = capsys.readouterr().out
    zeilen = [z.strip() for z in aus.splitlines()]
    assert f"Vorpruefung {antwort['bildeingang']}" in zeilen
    karte_zeile = next(z for z in zeilen if z.startswith("Karte:"))
    assert "entladen" in karte_zeile and "Bildeingang:" not in karte_zeile


def test_ohne_bildeingang_keine_zeile(tmp_path, capsys):
    _abholen("abholen_b301_a3b")._berichte({"ergebnisse": [
        {"job_id": "vis-1-abcdef", "tat": "verarbeitet", "grund": "", "karte": "frei",
         "bildeingang": None}]})
    aus = capsys.readouterr().out
    assert "Karte: frei" in aus and "Vorpruefung" not in aus


# ====================================================================== A6 · Modellwurzel

def _einheit(tmp_path, zeile):
    pfad = tmp_path / "kosmo-abholer.service"
    pfad.write_text(f"[Service]\n# Environment={render.UMGEBUNG_MODELLE}=/kommentar\n{zeile}\n",
                    encoding="utf-8")
    return pfad


def test_die_einheit_nennt_die_wurzel(tmp_path):
    ablage = tmp_path / "ablage"
    pfad = _einheit(tmp_path, f"Environment={render.UMGEBUNG_MODELLE}={ablage}")
    assert render.modellwurzel_der_einheit(pfad) == ablage


def test_die_einheit_mit_anfuehrung_und_heim(tmp_path):
    pfad = _einheit(tmp_path, f'Environment="A=b c" "{render.UMGEBUNG_MODELLE}=%h/gewichte"')
    assert render.modellwurzel_der_einheit(pfad, heim=tmp_path) == tmp_path / "gewichte"


@pytest.mark.parametrize("zeile", ["Environment=PYTHONUNBUFFERED=1",
                                   "Environment=AIIMAGING_MODELLE=relativ/pfad", ""])
def test_ohne_absolute_wurzel_nichts(tmp_path, zeile):
    assert render.modellwurzel_der_einheit(_einheit(tmp_path, zeile)) is None
    assert render.modellwurzel_der_einheit(tmp_path / "fehlt.service") is None


def test_die_eingecheckte_einheit_setzt_eine_wurzel():
    """Die Einheit im Repo und die Lesung passen zusammen — sonst liefe die Stufe ins Leere."""
    wurzel = render.modellwurzel_der_einheit(WURZEL / "betrieb" / render.EINHEIT_ABHOLER)
    assert wurzel is not None and wurzel.is_absolute()


def test_stufe_1b_greift_nur_wenn_der_ordner_existiert(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "ALTWURZEL_HOMESTATION", "/gibt-es-hier-sicher-nicht")
    ablage = tmp_path / "ablage"
    pfad = _einheit(tmp_path, f"Environment={render.UMGEBUNG_MODELLE}={ablage}")
    leer = {"XDG_DATA_HOME": str(tmp_path / "xdg")}
    assert render.modellwurzel(umgebung=leer, einheit=pfad)[1] == \
        render.HERKUNFT_ANWENDUNGSDATEN
    ablage.mkdir()
    assert render.modellwurzel(umgebung=leer, einheit=pfad) == (ablage,
                                                                render.HERKUNFT_ABHOLER)
    # Die Umgebung gewinnt weiter.
    anders = tmp_path / "anders"
    assert render.modellwurzel(umgebung={render.UMGEBUNG_MODELLE: str(anders)},
                               einheit=pfad) == (anders, render.HERKUNFT_UMGEBUNG)
    # Mit eigener Umgebung und ohne `einheit=` wird keine Einheit gelesen.
    assert render.modellwurzel(umgebung=leer)[1] == render.HERKUNFT_ANWENDUNGSDATEN


def test_ohne_variable_liest_der_prozess_die_einheit_des_abholers(tmp_path, monkeypatch):
    """Der Fall aus 301 A6: der Tiefenschätzer ausserhalb des Abholers."""
    monkeypatch.delenv(render.UMGEBUNG_MODELLE, raising=False)
    monkeypatch.setattr(render, "ALTWURZEL_HOMESTATION", "/gibt-es-hier-sicher-nicht")
    ablage = tmp_path / "ablage"
    (ablage / ts.VORGABE_TIEFENSCHAETZER).mkdir(parents=True)
    pfad = _einheit(tmp_path, f"Environment={render.UMGEBUNG_MODELLE}={ablage}")
    monkeypatch.setattr(render, "abholer_einheit_pfad", lambda **_kw: pfad)
    assert render.modellwurzel() == (ablage, render.HERKUNFT_ABHOLER)
    assert ts.standard_modell_wurzel(ts.VORGABE_TIEFENSCHAETZER) == \
        ablage / ts.VORGABE_TIEFENSCHAETZER


def test_der_pfad_der_einheit_folgt_xdg(tmp_path):
    assert render.abholer_einheit_pfad(umgebung={"XDG_CONFIG_HOME": str(tmp_path)}) == \
        tmp_path / "systemd" / "user" / render.EINHEIT_ABHOLER
    assert render.abholer_einheit_pfad(umgebung={"XDG_CONFIG_HOME": "relativ"}, heim=tmp_path) \
        == tmp_path / ".config" / "systemd" / "user" / render.EINHEIT_ABHOLER


def test_die_proben_lesen_keine_installierte_einheit():
    """conftest lenkt XDG_CONFIG_HOME um — am Heim-PC nennte die Einheit sonst eine Wurzel."""
    assert not render.abholer_einheit_pfad().exists()


def test_der_tiefenschaetzer_laedt_nie_aus_dem_netz(tmp_path):
    """Ein Ordner, den es nicht gibt, endet mit Satz — vor jedem Import, ohne Hub."""
    with pytest.raises(ts.TiefenschaetzerError, match="nie aus dem Netz") as fehler:
        ts.lade_modell(ts.VORGABE_TIEFENSCHAETZER, tmp_path / "fehlt")
    assert "uebergeben" in str(fehler.value)
    assert "transformers" not in sys.modules or sys.modules["transformers"] is not None


# ====================================================================== der Pruefauftrag 302

def test_der_pruefauftrag_302_ist_gueltig_und_vollstaendig():
    from aiimaging import auftrag
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-302.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["params"]["folgt_auf"] == "auf-20261021-301"
    assert daten["auflagen"]["leistungsgrenze_w"] == 400
    text = daten["anweisung"]
    for stichwort in ("A1", "A2", "A3", "A6", "message", "Im Prozess Bildeingang",
                      "Vorpruefung Bildeingang", "abholer-einheit", "nie aus dem Netz",
                      "HF_HUB_OFFLINE", "WAS AM HEIM-PC JETZT ANDERS RECHNET", "EINBAU", "NICHT:",
                      "Apache-2.0", "FLUX", "400 W", "Download 0 GB"):
        assert stichwort in text, stichwort
