"""Die Erklärkarten der iPad-App für die Tafel (`tools/ipad_tafel.py`), Abteil «Visbox · iPad».

Owner-Auftrag 24.10.2026: ein eigenes Abteil fürs iPad «mit der ui, funktionen etc die auf dem ipad sind». *Eine
Karte, die einen Knopf zeigt, den die App nicht hat, ist schlimmer als keine Karte* — darum sucht diese Probe jede
Bildschirm-Beschriftung, die eine Karte nennt, wortgleich in den Swift-Quellen der App, und sie hält Geplantes
(Entscheide 135, 141, 145) vom Gebauten getrennt: Was geplant ist, steht nur im Feld `geplant`, mit seinem
Entscheid, und steht **nicht** im Code.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
QUELLEN = WURZEL / "ipad" / "Visbox.swiftpm"
BLATT = WURZEL / "docs" / "IPAD_ERKLAERT.en.md"
ENTSCHEIDE = WURZEL / "docs" / "ENTSCHEIDE_IPAD_2026-09-21.md"


def _werkzeug():
    pfad = WURZEL / "tools" / "ipad_tafel.py"
    spec = importlib.util.spec_from_file_location("werkzeug_ipad_tafel", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _swift() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(QUELLEN.rglob("*.swift")))


def _sichtbarer_text(inhalt: str) -> str:
    """Was auf der Karte zu lesen ist: ohne Stilblock (Schriftpfade) und ohne Tags."""
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", inhalt, flags=re.S))


def _gebaut(k: dict) -> list[str]:
    """Die Texte einer Karte, die Gebautes beschreiben (alles ausser `geplant`)."""
    return [k["hilfe"], k["geschieht"], k["grenze"]] + [t[3] for t in k["teile"]]


def test_elf_karten_in_fester_folge_mit_titel_und_teilen():
    it = _werkzeug()
    kurz = [k["kurz"] for k in it.KARTEN]
    assert len(kurz) == 11
    assert [s[:2] for s in kurz] == [f"{i:02d}" for i in range(11)]
    for k in it.KARTEN:
        assert k["titel"].strip() and k["hilfe"].strip(), k["kurz"]
        assert k["teile"], k["kurz"]
        for nr, en, ui, satz in k["teile"]:
            assert en.strip() and satz.strip(), (k["kurz"], en)
        nummern = [t[0] for t in k["teile"] if t[0] is not None]
        assert nummern == list(range(1, len(nummern) + 1)), k["kurz"]
        assert k["geschieht"].strip() and k["grenze"].strip() and k["quelle"].strip()


def test_jede_nummer_der_liste_steht_im_schema():
    """Die Zeilen rechts verweisen auf Nummern im gezeichneten Bildschirm — jede muss es dort geben."""
    it = _werkzeug()
    for k in it.KARTEN:
        svg = k["bild"]()
        assert svg.startswith("<svg"), k["kurz"]
        gezeichnet = {int(n) for n in re.findall(r'font-weight="700" text-anchor="middle" '
                                                 r'font-family="Plex, sans-serif">(\d+)</text>', svg)}
        for nr, *_ in k["teile"]:
            if nr is not None:
                assert nr in gezeichnet, (k["kurz"], nr)


def test_jede_bildschirm_beschriftung_steht_im_code():
    """Nur was im Code ist: jede Beschriftung in Klammern und jedes «Zitat» aus gebauten Teilen."""
    it = _werkzeug()
    code = _swift()
    for k in it.KARTEN:
        for nr, en, ui, satz in k["teile"]:
            if ui:
                assert ui in code, (k["kurz"], ui)
        for text in _gebaut(k):
            for zitat in re.findall(r"«([^»]+)»", text):
                if "…" in zitat:
                    continue
                assert zitat in code, (k["kurz"], zitat)


def test_geplantes_steht_getrennt_mit_entscheid_und_nicht_im_code():
    """Entscheide 141 und 145 (und 135): geplant ist nicht gebaut — und die Karte sagt es nur dort."""
    it = _werkzeug()
    code = _swift()
    entscheide = ENTSCHEIDE.read_text(encoding="utf-8")
    alle = [(k, t, e) for k in it.KARTEN for t, e in k["geplant"]]
    assert {e for _, _, e in alle} == {"135", "141", "145"}
    for k, t, e in alle:
        assert re.search(rf"^\| {e} \|", entscheide, re.M), e
        for zitat in re.findall(r"«([^»]+)»", t):
            assert zitat not in code, (k["kurz"], zitat)
    for k in it.KARTEN:
        for text in [k["geschieht"]] + [t[3] for t in k["teile"]]:
            assert not re.search(r"\b(planned|geplant)\b", text, re.I), (k["kurz"], text)
        html = it.karte_html(k, 0)
        if k["geplant"]:
            assert html.count('class="geplant"') == 1
            assert "Planned — decided, not built" in html
        else:
            assert 'class="geplant"' not in html
    grenzen = next(k for k in it.KARTEN if k["kurz"] == "10-limits-planned")
    assert len(grenzen["geplant"]) >= 3


def test_regel_100_kein_partnername(tmp_path):
    it = _werkzeug()
    assert it.main(["--ausgabe", str(tmp_path), "--nur-html"]) == 0
    texte = {p.name: _sichtbarer_text(p.read_text(encoding="utf-8")) for p in tmp_path.glob("*.html")}
    texte.update({p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("*.json")})
    texte["IPAD_ERKLAERT.en.md"] = BLATT.read_text(encoding="utf-8")
    assert len(texte) == 23
    for name, text in texte.items():
        klein = text.lower()
        for wort in it.VERBOTEN:
            assert wort not in klein, (name, wort)
        assert "/home/" not in (text if name.endswith((".json", ".md")) else "")
        assert "tailscale" not in klein, name


def test_tafeldateien_heissen_und_gruppieren_wie_verlangt(tmp_path):
    it = _werkzeug()
    assert it.main(["--ausgabe", str(tmp_path), "--nur-html", "--karte", "03"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["20261024-ipad-03-drawing.html",
                                                          "20261024-ipad-03-drawing.json"]
    tafel = json.loads((tmp_path / "20261024-ipad-03-drawing.json").read_text(encoding="utf-8"))
    assert set(tafel) == {"titel", "gruppe", "notiz"}
    assert tafel["gruppe"] == "Visbox · iPad"
    assert tafel["titel"] == "Drawing sheet (Zeichenfläche)"
    assert 20 <= len(tafel["notiz"]) <= 240
    html = (tmp_path / "20261024-ipad-03-drawing.html").read_text(encoding="utf-8")
    assert "Drawn schematic — not a screenshot" in html


def test_das_blatt_ist_aus_den_karten_geschrieben(tmp_path):
    """`docs/IPAD_ERKLAERT.en.md` wird nicht von Hand geführt — es ist, was `--markdown` schreibt."""
    it = _werkzeug()
    ziel = tmp_path / "blatt.md"
    assert it.main(["--markdown", str(ziel)]) == 0
    assert ziel.read_text(encoding="utf-8") == BLATT.read_text(encoding="utf-8")
    kopfe = re.findall(r"^## (\d\d) · (.+)$", BLATT.read_text(encoding="utf-8"), re.M)
    assert [t for _, t in kopfe] == [k["titel"] for k in it.KARTEN]


def test_unbekannte_karte_und_fehlendes_chromium_sagen_es(tmp_path, capsys):
    it = _werkzeug()
    assert it.main(["--ausgabe", str(tmp_path), "--karte", "gibt-es-nicht", "--nur-html"]) == 2
    assert it.main(["--ausgabe", str(tmp_path), "--karte", "03", "--chrome", str(tmp_path / "kein")]) == 3
    assert "Kein Chromium" in capsys.readouterr().err


def test_keine_tafelbilder_im_repo():
    """Die PNG gehören auf die Tafel, nicht ins Repo."""
    assert not list(WURZEL.glob("**/20261024-ipad-*.png"))
