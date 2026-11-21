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


def _integrator_weiter_roh(repo: Path, dateien: dict[str, bytes], text: str) -> str:
    """Wie ``_integrator_weiter``, aber mit Bytes: Proben, die kein UTF-8-Text sein müssen."""
    _git(repo, "checkout", "-q", "--detach", INTEGRATOR.removeprefix("refs/remotes/"))
    for rel, inhalt in dateien.items():
        (repo / "kosmo-orbit" / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / "kosmo-orbit" / rel).write_bytes(inhalt)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", text)
    neu = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", INTEGRATOR, neu)
    return neu


# Ausserhalb von modules/vis/**, wie die echten Proben: unter modules/vis/ träfe das Muster sie als
# «fehlt hier», und sie würden nie gelesen.
PROBEN_ORDNER = "apps/kosmo-orbit/test"
WORT = "modules/vis"
NENNT = f"// {WORT}\n"                  # nennt das Suchwort
NENNT_NICHT = "// etwas anderes\n"     # nennt es nicht

#: Name → (Inhalt, gilt als binär, steht unter «neu dort»). Die Fälle, die das Gegenlesen R1 fand
#: (Nullbytes, UTF-16 ohne BOM, UTF-16 mit BOM) und die Grenzen daneben.
FAELLE = {
    "utf8-text-nennt.ts":          (NENNT.encode(), False, True),
    "utf8-text-nennt-nicht.ts":    (NENNT_NICHT.encode(), False, False),
    "utf8-mit-bom-nennt.ts":       (b"\xef\xbb\xbf" + NENNT.encode(), False, True),
    "leer.ts":                     (b"", False, False),
    "ungueltig-utf8-nennt.bin":    (b"\xf0(\x8c\xbc " + WORT.encode() + b" \xff", True, True),
    "ungueltig-utf8-nennt-nicht.bin": (b"\x89PNG\xf0(\x8c\xbc", True, False),
    "nullbytes.ts":                (b"\x00" * 64, True, False),
    "nullbyte-im-text-nennt.ts":   (b"\x00" + NENNT.encode(), True, True),
    "utf16-le-ohne-bom-nennt.ts":  (NENNT.encode("utf-16-le"), True, True),
    "utf16-be-ohne-bom-nennt.ts":  (NENNT.encode("utf-16-be"), True, True),
    "utf16-le-ohne-bom-nennt-nicht.ts": (NENNT_NICHT.encode("utf-16-le"), True, False),
    "utf16-mit-bom-nennt.ts":      (NENNT.encode("utf-16"), True, True),
    "utf16-mit-bom-nennt-nicht.ts": (NENNT_NICHT.encode("utf-16"), True, False),
    "utf32-mit-bom-nennt.ts":      (NENNT.encode("utf-32"), True, True),
    "utf32-mit-bom-nennt-nicht.ts": (NENNT_NICHT.encode("utf-32"), True, False),
    "utf32-be-ohne-bom-nennt.ts":  (NENNT.encode("utf-32-be"), True, True),
    # Um ein Byte versetzt: UTF-32 LE ist dann in keiner Kodierung auf der Zeichenbreite
    # ausgerichtet; ein Fund in der Bytefolge von UTF-16 BE oder UTF-32 BE wäre Zufall.
    "utf32-le-versetzt-nennt-nicht.ts": (b"x" + NENNT.encode("utf-32-le"), True, False),
    # Erst ein versetzter Treffer, dann ein ausgerichteter: der zweite zählt (die Suche hört nicht
    # beim ersten unausgerichteten auf).
    "utf32-le-erst-versetzt-dann-ausgerichtet.ts": (
        b"x" + WORT.encode("utf-32-le") + b"abc" + WORT.encode("utf-32-le"), True, True),
    # Dagegen ist ein um ein Byte versetzter UTF-16-LE-Text gültiges UTF-16 BE (führende Nullbytes).
    "utf16-le-versetzt-ist-utf16-be.ts": (b"x" + NENNT.encode("utf-16-le"), True, True),
    "utf16-le-nennt-am-anfang.ts": ("modules/vis".encode("utf-16-le"), True, True),
    "utf32-le-ohne-bom-nennt.ts":  (NENNT.encode("utf-32-le"), True, True),
}


@pytest.fixture
def bericht_mit_faellen(quelle_und_kopie):
    ue = _lade("ue_faelle", "kosmovis_uebernahme.py")
    repo, kopie, _ = quelle_und_kopie
    _integrator_weiter_roh(repo, {f"{PROBEN_ORDNER}/{n}": inhalt for n, (inhalt, _, _) in FAELLE.items()},
                           "Int 1: Proben in allen Spielarten")
    return ue, ue.abgleich(repo / "kosmo-orbit", ziel=kopie)


@pytest.mark.parametrize("name", sorted(FAELLE))
def test_jede_probe_steht_dort_wo_sie_hingehoert(bericht_mit_faellen, name):
    """A0499 R2: Der Abgleich bricht bei keiner Spielart ab (R1: UnicodeDecodeError bei ungültigem
    UTF-8), eine binäre Probe steht mit Namen unter «binaer» (auch Nullbytes mit Text-Endung und
    UTF-16 ohne BOM: R1 liess sie unsichtbar), und das Suchwort wird in ihr gefunden, wenn sie es
    nennt (R1: UTF-16 mit BOM nannte es und stand nicht unter «neu dort»)."""
    _, b = bericht_mit_faellen
    _, binaer, nennt = FAELLE[name]
    rel = f"{PROBEN_ORDNER}/{name}"
    assert (rel in b["binaer"]) is binaer
    assert (rel in [r for r, _ in b["neu_dort"]]) is nennt


def test_der_bericht_hat_genau_die_erwarteten_binaerdateien_und_zaehlt_sonst_nichts(bericht_mit_faellen):
    ue, b = bericht_mit_faellen
    assert b["binaer"] == sorted(f"{PROBEN_ORDNER}/{n}" for n, (_, bin_, _) in FAELLE.items() if bin_)
    assert b["gleich"] == 3 and b["abweichend"] == [] and b["fehlt_dort"] == [] and b["fehlt_hier"] == []
    assert ue.abgleich_befunde(b) == 0      # Binärdateien sind ein Hinweis, kein Befund


def test_die_berichtszeile_sagt_ehrlich_was_gesucht_wurde(bericht_mit_faellen, capsys):
    """Die Zeile darf nicht nach «geprüft, kein Treffer» klingen, wo nur ASCII gesucht wurde."""
    ue, b = bericht_mit_faellen
    ue.drucke_abgleich(b)
    zeilen = [z for z in capsys.readouterr().out.splitlines() if z.startswith("binär: ")]
    assert len(zeilen) == len(b["binaer"]) == sum(1 for _, bin_, _ in FAELLE.values() if bin_)
    for z in zeilen:
        assert "ASCII, UTF-16 und UTF-32" in z and "modules/vis" in z
    assert all(f"binär: {rel} — " in "\n".join(zeilen) for rel in b["binaer"])


def test_ueber_die_befehlszeile_steht_jede_binaerdatei_im_bericht(bericht_mit_faellen, quelle_und_kopie,
                                                                 monkeypatch, capsys):
    ue, b = bericht_mit_faellen
    repo, kopie, _ = quelle_und_kopie
    monkeypatch.setattr(ue, "ZIEL", kopie)
    assert ue.main(["--abgleich", str(repo / "kosmo-orbit")]) == 0
    aus = capsys.readouterr().out
    for rel in b["binaer"]:
        assert f"binär: {rel} — " in aus
    assert f"binär: {PROBEN_ORDNER}/utf8-mit-bom-nennt.ts" not in aus and "leer.ts" not in aus


def test_nur_text_proben_gaben_vor_und_nach_dem_fix_dasselbe(quelle_und_kopie, capsys):
    """Leitplanke: Text bleibt Text. Diese Probe ist auf der Basis grün und muss es bleiben."""
    ue = _lade("ue_nur_text", "kosmovis_uebernahme.py")
    repo, kopie, _ = quelle_und_kopie
    _integrator_weiter(repo, {f"{PROBEN_ORDNER}/text-probe.ts": NENNT}, "nur Text")
    b = ue.abgleich(repo / "kosmo-orbit", ziel=kopie)
    assert b.get("binaer", []) == []
    assert b["neu_dort"] == [(f"{PROBEN_ORDNER}/text-probe.ts", "neue Probe, nennt modules/vis")]
    ue.drucke_abgleich(b)
    assert "binär:" not in capsys.readouterr().out


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
