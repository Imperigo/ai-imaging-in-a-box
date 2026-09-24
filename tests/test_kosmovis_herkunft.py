"""Die KosmoVis-Kopie bleibt rückführbar — geprüft, nicht versprochen.

Owner-Entscheid E26 (24.09.2026): Das Vis-Werkzeug von KosmoOrbit kommt als **Kopie**
nach ``kosmovis/``, wird bis Februar hier weiterbearbeitet und geht dann nahtlos zurück.
*Nahtlos* heisst: Für jede Datei ist bekannt, ob sie das Original ist, ein Stellvertreter
oder Visbox-eigen. ``tools/kosmovis_uebernahme.py`` hält das in ``kosmovis/HERKUNFT.json``
fest; diese Proben halten es fest, wenn niemand hinschaut.

Die Proben brauchen weder Node noch ``npm install`` — sie lesen nur Dateien.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
KOPIE = WURZEL / "kosmovis"


def _werkzeug():
    pfad = WURZEL / "tools" / "kosmovis_uebernahme.py"
    spec = importlib.util.spec_from_file_location("kosmovis_uebernahme", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _herkunft() -> dict:
    return json.loads((KOPIE / "HERKUNFT.json").read_text(encoding="utf-8"))


def test_jede_kopie_stimmt_und_keine_datei_ist_ohne_herkunft(capsys):
    """Der Kern der Sache: ``--pruefen`` endet mit 0. Eine still geänderte Kopie oder eine
    unverbuchte Datei liesse ihn mit 1 enden."""
    assert _werkzeug().main(["--pruefen"]) == 0
    assert "Alle Kopien stimmen." in capsys.readouterr().out


def test_die_herkunft_nennt_quelle_commit_und_entscheid():
    h = _herkunft()
    assert h["quelle"]["repo"] == "Imperigo/Architektur-Cosmos"
    assert re.fullmatch(r"[0-9a-f]{40}", h["quelle"]["commit"])
    assert h["entscheid"].startswith("E26")
    assert len(h["woertlich"]) >= 150, "der Schnitt ist geschrumpft — gewollt?"


def test_jeder_stellvertreter_sagt_im_kopf_dass_er_einer_ist():
    """Wer im Februar zurückführt, liest die Datei, nicht ``HERKUNFT.json``. Ein
    Stellvertreter, der nicht sagt, was er ist, sieht dort aus wie das Original."""
    for rel in _herkunft()["stellvertreter"]:
        kopf = (KOPIE / rel).read_text(encoding="utf-8")[:600]
        assert "STELLVERTRETER" in kopf, rel


def test_keine_heimrechner_adresse_in_der_kopie():
    """Regel 3. Das Original von ``state/home-server.ts`` trägt die feste Tailnet-Adresse
    des Heimrechners (Bereich 100.64.0.0/10). Der Stellvertreter lässt sie weg — und
    diese Probe sorgt dafür, dass sie auch mit keiner anderen Datei hereinkommt."""
    tailnet = re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
    funde = []
    for datei in KOPIE.rglob("*"):
        if "node_modules" in datei.parts or "dist" in datei.parts or not datei.is_file():
            continue
        if datei.suffix in {".ts", ".tsx", ".css", ".json", ".html", ".md"}:
            if tailnet.search(datei.read_text(encoding="utf-8", errors="replace")):
                funde.append(datei.relative_to(KOPIE).as_posix())
    assert not funde


def test_eine_still_geaenderte_kopie_faellt_auf(tmp_path, monkeypatch):
    """Die Gegenprobe: ein Byte in einer wörtlichen Kopie geändert — ``--pruefen`` muss
    rot werden. Sonst prüft die erste Probe nichts."""
    w = _werkzeug()
    ziel = tmp_path / "kosmovis"
    shutil.copytree(KOPIE, ziel, ignore=shutil.ignore_patterns("node_modules", "dist"))
    monkeypatch.setattr(w, "ZIEL", ziel)
    monkeypatch.setattr(w, "HERKUNFT", ziel / "HERKUNFT.json")
    assert w.pruefe() == []

    opfer = ziel / "apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx"
    opfer.write_text(opfer.read_text(encoding="utf-8") + "\n// still\n", encoding="utf-8")
    (ziel / "apps/kosmo-orbit/src/unverbucht.ts").write_text("export {};\n", encoding="utf-8")

    befunde = w.pruefe()
    assert any("NodeCanvas.tsx: weicht vom Original ab" in b for b in befunde)
    assert any("unverbucht.ts: ohne Herkunft" in b for b in befunde)


def test_die_uebernahme_kopiert_woertlich_und_haelt_den_abdruck_fest(tmp_path, monkeypatch,
                                                                      capsys):
    """Der Kopierweg selbst, an einer erfundenen Quelle: Er kopiert, was das Muster
    trifft, lässt aus, was ausgeschlossen ist, und behält Stellvertreter und Eigenes."""
    w = _werkzeug()
    quelle = tmp_path / "quelle"
    (quelle / "a/b").mkdir(parents=True)
    (quelle / "a/b/x.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (quelle / "a/b/node_modules").mkdir()
    (quelle / "a/b/node_modules/y.js").write_text("fremd\n", encoding="utf-8")
    ziel = tmp_path / "ziel"
    ziel.mkdir()
    (ziel / "HERKUNFT.json").write_text(json.dumps(
        {"stellvertreter": {"s.ts": "Grund"}, "eigen": {"e/**": "Grund"}}), encoding="utf-8")
    monkeypatch.setattr(w, "ZIEL", ziel)
    monkeypatch.setattr(w, "HERKUNFT", ziel / "HERKUNFT.json")
    monkeypatch.setattr(w, "WOERTLICH", ("a/**",))
    monkeypatch.setattr(w, "PROBEN", ())

    assert w.main([str(quelle), "--commit", "0" * 40]) == 0
    assert "1 Dateien wörtlich kopiert" in capsys.readouterr().out
    h = json.loads((ziel / "HERKUNFT.json").read_text(encoding="utf-8"))
    assert list(h["woertlich"]) == ["a/b/x.ts"]
    assert h["stellvertreter"] == {"s.ts": "Grund"}
    assert h["eigen"] == {"e/**": "Grund"}
    assert not (ziel / "a/b/node_modules").exists()


def test_fehlt_ein_muster_in_der_quelle_bricht_die_uebernahme_ab(tmp_path, monkeypatch):
    """Ein umbenanntes Original darf nicht still aus der Kopie fallen."""
    w = _werkzeug()
    (tmp_path / "quelle").mkdir()
    monkeypatch.setattr(w, "ZIEL", tmp_path / "ziel")
    monkeypatch.setattr(w, "HERKUNFT", tmp_path / "ziel/HERKUNFT.json")
    monkeypatch.setattr(w, "WOERTLICH", ("gibt/es/nicht.ts",))
    monkeypatch.setattr(w, "PROBEN", ())
    with pytest.raises(SystemExit, match="Nicht gefunden"):
        w.main([str(tmp_path / "quelle"), "--commit", "0" * 40])
