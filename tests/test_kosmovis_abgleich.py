"""Der Abgleich der Kopie mit dem aktuellen KosmoOrbit — und der Abbruch im Bau (S5, 21.10.2026).

``--pruefen`` vergleicht die Kopie nur mit ihrem eigenen Abdruck; dass das Original inzwischen
weitergegangen ist, sieht er nie. ``tools/kosmovis_uebernahme.py --abgleich`` liest den Stand von
KosmoOrbit über ``git`` (ohne Checkout) und sagt, was abweicht, was dort fehlt und was hier fehlt.
``tools/knoten_bau.py`` ruft zuerst die Prüfung und dann — mit ``KOSMO_ORBIT`` — den Abgleich, und
baut bei einem Befund nicht.

Zwei Arten Proben:

* **Mit Checkout** (``KOSMO_ORBIT`` = Pfad zu ``kosmo-orbit/`` in einem Klon): die echte Kopie gegen
  den Integrator-Stand. Ohne den Pfad übersprungen.
* **Ohne Checkout:** ein kleines künstliches Git-Repo als Quelle. Es zeigt, dass eine Abweichung
  rot wird, dass ein eigener, noch nicht eingespielter Zweig es nicht wird, und dass der Bau abbricht.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]

VIS = "apps/kosmo-orbit/src/modules/vis"
SHELL = "apps/kosmo-orbit/src/shell"


def _lade(name: str, datei: str):
    spec = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _git(repo: Path, *args: str) -> str:
    umgebung = {**os.environ, "GIT_AUTHOR_NAME": "Probe", "GIT_AUTHOR_EMAIL": "probe@example.invalid",
                "GIT_COMMITTER_NAME": "Probe", "GIT_COMMITTER_EMAIL": "probe@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env=umgebung).stdout.strip()


def _schreibe(wurzel: Path, dateien: dict[str, str]) -> None:
    for rel, inhalt in dateien.items():
        (wurzel / rel).parent.mkdir(parents=True, exist_ok=True)
        (wurzel / rel).write_text(inhalt, encoding="utf-8")


def _commit(repo: Path, dateien: dict[str, str], text: str) -> str:
    _schreibe(repo / "kosmo-orbit", dateien)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", text)
    return _git(repo, "rev-parse", "HEAD")


INTEGRATOR = "refs/remotes/origin/claude/kosmo-orbit-v1-build-pzxkbj"
START = {f"{VIS}/a.ts": "export const a = 1;\n", f"{VIS}/b.ts": "export const b = 2;\n",
         f"{SHELL}/tastennamen.ts": "export const t = 3;\n",
         "apps/kosmo-orbit/src/App.tsx": "// nicht Vis\n"}
KOPIERT = (f"{VIS}/a.ts", f"{VIS}/b.ts", f"{SHELL}/tastennamen.ts")


@pytest.fixture
def quelle_und_kopie(tmp_path):
    """Ein Repo mit ``kosmo-orbit/`` als Unterordner, der Integrator-Zweig als Remote-Ref und eine
    Kopie mit HERKUNFT.json, die genau den Startstand trägt."""
    if not shutil.which("git"):
        pytest.skip("git fehlt")
    repo = tmp_path / "ko"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "start")
    start = _commit(repo, START, "Start")
    _git(repo, "update-ref", INTEGRATOR, start)
    kopie = tmp_path / "kopie"
    _schreibe(kopie, {rel: START[rel] for rel in KOPIERT})
    herkunft = {"quelle": {"commit": start},
                "woertlich": {rel: hashlib.sha256(START[rel].encode()).hexdigest() for rel in KOPIERT},
                "geaendert": {}, "stellvertreter": {}, "eigen": {}}
    (kopie / "HERKUNFT.json").write_text(json.dumps(herkunft), encoding="utf-8")
    return repo, kopie, start


def _integrator_weiter(repo: Path, dateien: dict[str, str], text: str) -> str:
    _git(repo, "checkout", "-q", "--detach", INTEGRATOR.removeprefix("refs/remotes/"))
    neu = _commit(repo, dateien, text)
    _git(repo, "update-ref", INTEGRATOR, neu)
    return neu


def test_gleich_ist_gruen(quelle_und_kopie):
    ue = _lade("ue_gleich", "kosmovis_uebernahme.py")
    repo, kopie, start = quelle_und_kopie
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["commit"] == start and b["gleich"] == 3
    assert ue.abgleich_befunde(b) == 0 and b["neu_dort"] == []


def test_eine_abweichung_wird_rot_auch_ueber_die_befehlszeile(quelle_und_kopie, monkeypatch, capsys):
    ue = _lade("ue_rot", "kosmovis_uebernahme.py")
    repo, kopie, _ = quelle_und_kopie
    _integrator_weiter(repo, {f"{VIS}/a.ts": "export const a = 10;\n",
                              f"{VIS}/c.ts": "export const c = 4;\n",
                              f"{SHELL}/neu-im-ordner.ts": "export {};\n"}, "Int 1 weiter")
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["abweichend"] == [(f"{VIS}/a.ts", "Inhalt anders")]
    assert b["fehlt_hier"] == [f"{VIS}/c.ts"]                   # Muster modules/vis/** trifft dort
    assert (f"{SHELL}/neu-im-ordner.ts", "neu in einem Ordner der Kopie") in b["neu_dort"]
    assert ue.abgleich_befunde(b) == 2
    monkeypatch.setattr(ue, "ZIEL", kopie)
    assert ue.main(["--abgleich", str(repo / "kosmo-orbit")]) == 1
    aus = capsys.readouterr().out
    assert f"abweichend: {VIS}/a.ts" in aus and f"fehlt hier: {VIS}/c.ts" in aus
    # Gegen den festen Start-Stand (--ref) ist dieselbe Kopie grün.
    assert ue.main(["--abgleich", str(repo / "kosmo-orbit"), "--ref", "start"]) == 0


def test_fehlt_dort_wird_rot(quelle_und_kopie):
    ue = _lade("ue_dort", "kosmovis_uebernahme.py")
    repo, kopie, _ = quelle_und_kopie
    _git(repo, "rm", "-q", f"kosmo-orbit/{VIS}/b.ts")
    _integrator_weiter(repo, {}, "b.ts entfernt")
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["fehlt_dort"] == [f"{VIS}/b.ts"] and ue.abgleich_befunde(b) == 1


def test_ein_eigener_noch_nicht_eingespielter_zweig_ist_kein_abweichen(quelle_und_kopie, monkeypatch):
    ue = _lade("ue_eigen", "kosmovis_uebernahme.py")
    repo, kopie, start = quelle_und_kopie
    _git(repo, "checkout", "-q", "-b", "kv", start)
    _commit(repo, {f"{VIS}/b.ts": "export const b = 20;\n"}, "eigener Zweig")
    _git(repo, "update-ref", "refs/remotes/origin/claude/kosmovis-probe", "kv")
    _schreibe(kopie, {f"{VIS}/b.ts": "export const b = 20;\n"})
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["eigen"] == [(f"{VIS}/b.ts", "origin/claude/kosmovis-probe")]
    assert ue.abgleich_befunde(b) == 0
    # Ohne die eigenen Zweige ist dieselbe Datei eine Abweichung — auch über die Befehlszeile.
    assert ue.abgleich_befunde(ue.abgleich(repo / "kosmo-orbit", eigene=False, ziel=kopie)) == 1
    monkeypatch.setattr(ue, "ZIEL", kopie)
    geholt = []
    monkeypatch.setattr(ue, "holen", lambda q: geholt.append(q))
    assert ue.main(["--abgleich", str(repo / "kosmo-orbit"), "--holen"]) == 0
    assert geholt == [repo / "kosmo-orbit"]
    assert ue.main(["--abgleich", str(repo / "kosmo-orbit"), "--ohne-eigene"]) == 1
    # Ändert Int 1 dieselbe Datei auch, ist es ein Zusammenstoss — rot.
    _integrator_weiter(repo, {f"{VIS}/b.ts": "export const b = 30;\n"}, "Int 1 auch")
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["abweichend"] == [(f"{VIS}/b.ts", "auf origin/claude/kosmovis-probe und dort geändert")]


def test_eine_vermerkte_aenderung_ist_kein_abweichen(quelle_und_kopie):
    ue = _lade("ue_vermerkt", "kosmovis_uebernahme.py")
    repo, kopie, _ = quelle_und_kopie
    h = json.loads((kopie / "HERKUNFT.json").read_text(encoding="utf-8"))
    h["geaendert"] = {f"{VIS}/a.ts": "Probe: mit Grund geändert"}
    (kopie / "HERKUNFT.json").write_text(json.dumps(h), encoding="utf-8")
    _schreibe(kopie, {f"{VIS}/a.ts": "export const a = 99;\n"})
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b["vermerkt"] == [f"{VIS}/a.ts"] and ue.abgleich_befunde(b) == 0


# ------------------------------------------------------------------ der Bau bricht ab

def _bau_mit(kopie: Path, monkeypatch):
    kb = _lade("kb_abgleich", "knoten_bau.py")
    ue = _lade("ue_bau", "kosmovis_uebernahme.py")
    monkeypatch.setattr(ue, "ZIEL", kopie)
    monkeypatch.setattr(ue, "HERKUNFT", kopie / "HERKUNFT.json")
    monkeypatch.setattr(kb, "_uebernahme", lambda: ue)
    return kb


def test_der_bau_bricht_bei_abweichung_ab_ausser_mit_festem_stand(quelle_und_kopie, monkeypatch):
    repo, kopie, start = quelle_und_kopie
    kb = _bau_mit(kopie, monkeypatch)
    assert kb.vor_dem_bau(kosmo_orbit=str(repo / "kosmo-orbit"))["ergebnis"] == "gleich"
    assert "nicht abgeglichen" in kb.vor_dem_bau(kosmo_orbit="")["ergebnis"]
    neu = _integrator_weiter(repo, {f"{VIS}/a.ts": "export const a = 10;\n"}, "Int 1 weiter")
    with pytest.raises(kb.BauAbbruch, match="1 Abweichungen"):
        kb.vor_dem_bau(kosmo_orbit=str(repo / "kosmo-orbit"))
    vermerk = kb.vor_dem_bau(fester_stand=True, kosmo_orbit=str(repo / "kosmo-orbit"))
    assert vermerk["ergebnis"] == "abweichend, bewusst gegen den festen Stand gebaut"
    assert vermerk["commit"] == neu and vermerk["fester_stand"] == start and vermerk["abweichungen"] == 1


def test_der_bau_bricht_bei_einem_befund_der_pruefung_immer_ab(quelle_und_kopie, monkeypatch):
    _, kopie, _ = quelle_und_kopie
    kb = _bau_mit(kopie, monkeypatch)
    _schreibe(kopie, {f"{VIS}/a.ts": "// still geändert\n"})
    with pytest.raises(kb.BauAbbruch, match="Abdruck"):
        kb.vor_dem_bau(fester_stand=True, kosmo_orbit="")


def test_der_bau_ruft_die_pruefung_vor_npm(monkeypatch):
    kb = _lade("kb_reihe", "knoten_bau.py")
    reihe = []
    monkeypatch.setattr(kb, "vor_dem_bau", lambda fest=False: reihe.append("pruefen") or {"ergebnis": "x"})
    monkeypatch.setattr(kb, "braucht_npm_ci", lambda: False)
    monkeypatch.setattr(kb.subprocess, "run", lambda *a, **k: reihe.append(a[0][:2]))
    monkeypatch.setattr(kb, "stempele", lambda vermerk=None: reihe.append(("stempel", vermerk)))
    assert kb.main([]) == 0
    assert reihe[0] == "pruefen" and reihe[-1] == ("stempel", {"ergebnis": "x"})
    reihe.clear()
    monkeypatch.setattr(kb, "vor_dem_bau", lambda fest=False: reihe.append(("pruefen", fest)) or {})
    assert kb.main(["--fester-stand"]) == 0
    assert reihe[0] == ("pruefen", True)


# ------------------------------------------------------------------ mit echtem Checkout

@pytest.mark.skipif(not os.environ.get("KOSMO_ORBIT"), reason="KosmoOrbit liegt nicht daneben (KOSMO_ORBIT)")
def test_die_kopie_stimmt_mit_dem_integrator_stand():
    ue = _lade("ue_echt", "kosmovis_uebernahme.py")
    try:
        b = ue.abgleich(Path(os.environ["KOSMO_ORBIT"]))
    except subprocess.CalledProcessError as fehler:
        pytest.skip(f"kein git-Klon mit dem Integrator-Zweig: {fehler.stderr}")
    befunde = [*b["abweichend"], *b["fehlt_dort"], *b["fehlt_hier"]]
    assert not befunde, f"Abweichungen gegen {b['ref']} ({b['commit'][:9]}): {befunde[:10]}"
