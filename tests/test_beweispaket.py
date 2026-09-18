"""Das Paket muss dieselbe Wahrheit tragen wie die Galerie — und nur die kuratierten Bilder.

**Warum es diese Proben gibt.** Das Paket wiederholt Titel und Sätze der Galerie. Täte es
das aus eigenen Konstanten, hätten wir zwei Wahrheiten, die beim nächsten Zusatz
auseinanderlaufen — und zwar unbemerkt, weil beide für sich richtig aussehen.
"""
from __future__ import annotations

import importlib.util
import struct
import zipfile
import zlib
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]


def _modul(name: str):
    spec = importlib.util.spec_from_file_location(name, WURZEL / "tools" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _winziges_png(pfad: Path) -> None:
    def block(art: bytes, roh: bytes) -> bytes:
        return (struct.pack(">I", len(roh)) + art + roh
                + struct.pack(">I", zlib.crc32(art + roh) & 0xFFFFFFFF))
    kopf = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n" + block(b"IHDR", kopf)
                     + block(b"IDAT", zlib.compress(b"\x00\x00"))
                     + block(b"IEND", b""))


@pytest.fixture
def paket(tmp_path, monkeypatch):
    """Ein Bilderbaum mit EINER echten Tafel — samt Arbeitsordner, der draussen bleiben muss."""
    galerie = _modul("beweisgalerie")
    name = sorted(galerie.TAFELN)[0]
    ordner = tmp_path / "beweis" / name
    ordner.mkdir(parents=True)
    _winziges_png(ordner / "01_erstes_wert-0.42.png")
    _winziges_png(ordner / "02_zweites_wert-0.99.png")
    # Ein Arbeitsordner, wie ihn Blender hinterlaesst.
    (ordner / "lauf").mkdir()
    _winziges_png(ordner / "lauf" / "rohausgabe.png")
    return _modul("beweispaket"), tmp_path, name


def test_nur_die_kuratierten_bilder_kommen_ins_paket(paket):
    """**Arbeitsordner sind keine Beweistafeln.**

    `lauf/` und `_arbeit/` tragen Rohausgaben von Blender — Dateinamen ohne Aussage und
    ohne Bildunterschrift. Sie mitzunehmen hiesse, einem Leser Bilder zu geben, zu denen
    kein Satz gehört. *Am 17.09.2026 hat mich eine rekursive Zählung genau darüber
    stolpern lassen: 239 gegen 212, scheinbar 27 verschwundene Bilder — es waren Rohdaten.*
    """
    modul, tmp_path, name = paket
    tafeln, bilder, _ = modul.packe(tmp_path / "aus", bilderwurzel=tmp_path / "beweis")

    assert (tafeln, bilder) == (1, 2), "zwei kuratierte, die Rohausgabe bleibt draussen"
    assert not (tmp_path / "aus" / name / "rohausgabe.png").exists()
    assert not (tmp_path / "aus" / name / "lauf").exists()
    assert sorted(p.name for p in (tmp_path / "aus" / name).glob("*.png")) == [
        "01_erstes_wert-0.42.png", "02_zweites_wert-0.99.png"]


def test_jede_tafel_bekommt_ihren_satz_und_er_stammt_aus_der_galerie(paket):
    """**Eine Quelle für den Text, nicht zwei.**

    Der Satz im Paket muss derselbe sein wie in der Galerie. Stünde er hier noch einmal
    geschrieben, wären es zwei Wahrheiten — und die zweite veraltet, ohne falsch
    auszusehen.
    """
    modul, tmp_path, name = paket
    galerie = _modul("beweisgalerie")
    titel, _marke, was, _vorbehalt = galerie.TAFELN[name]

    modul.packe(tmp_path / "aus", bilderwurzel=tmp_path / "beweis")
    text = (tmp_path / "aus" / name / "LIESMICH.md").read_text(encoding="utf-8")

    assert text.startswith(f"# {titel}")
    kern = was.replace("<code>", "`").replace("</code>", "`")
    assert kern in text, "der Satz der Galerie, wörtlich"
    for bild in ("01_erstes_wert-0.42.png", "02_zweites_wert-0.99.png"):
        assert bild in text, "die Dateinamen tragen die Messwerte — sie gehören hinein"


def test_das_gesamtverzeichnis_nennt_auch_was_nicht_gefahren_wurde(paket):
    """**Die dritte Antwort, wie in der Galerie.**

    Ein Verzeichnis, aus dem das Fehlende verschwindet, sieht vollständig aus. Wer die
    Tafeln zählt, glaubt dann, das sei alles.
    """
    modul, tmp_path, name = paket
    galerie = _modul("beweisgalerie")
    modul.packe(tmp_path / "aus", bilderwurzel=tmp_path / "beweis")
    text = (tmp_path / "aus" / "LIESMICH.md").read_text(encoding="utf-8")

    assert f"1 von {len(galerie.TAFELN)} Tafeln" in text
    assert "NICHT GEFAHREN in diesem Lauf" in text
    fehlend = [k for k in galerie.TAFELN if k != name]
    for k in fehlend:
        assert f"`{k}`" in text, f"{k} fehlt im Verzeichnis und verschwindet damit"


def test_ein_ordner_ohne_text_haelt_den_lauf_an(paket):
    """Dieselbe Regel wie in der Galerie: **kein Bild ohne den Satz daneben.**"""
    modul, tmp_path, _ = paket
    (tmp_path / "beweis" / "99_gibt_es_nicht").mkdir()
    _winziges_png(tmp_path / "beweis" / "99_gibt_es_nicht" / "01_irgendwas.png")

    with pytest.raises(SystemExit, match="Ohne Text keine Tafel"):
        modul.packe(tmp_path / "aus", bilderwurzel=tmp_path / "beweis")


def test_das_zip_packt_mit_relativen_pfaden_aus(paket):
    """Ein Archiv mit absoluten Pfaden packt beim Empfänger irgendwohin aus — oder nirgends."""
    modul, tmp_path, name = paket
    modul.packe(tmp_path / "aus", bilderwurzel=tmp_path / "beweis")
    ziel = modul.zippe(tmp_path / "aus", tmp_path / "aus.zip")

    with zipfile.ZipFile(ziel) as z:
        namen = z.namelist()
    assert namen, "ein leeres Archiv ist kein Archiv"
    assert all(not n.startswith("/") and ".." not in n for n in namen), (
        f"nur relative Pfade, ohne Ausbruch: {namen[:3]}")
    assert all(n.startswith("aus/") for n in namen), "alles in EINEM Ordner, nicht verstreut"
    assert f"aus/{name}/LIESMICH.md" in namen


def test_der_schalter_zip_legt_wirklich_ein_archiv_daneben(paket, capsys):
    """**Der Schalter wird gedrückt, nicht die Funktion gerufen.**

    Ein Kommandozeilenschalter, den nie eine Probe drückt, kann still nichts tun — am
    01.09.2026 waren in diesem Repo zwei von neun ungedrückten Schaltern kaputt. Diese
    Probe ruft darum `main(["--zip", …])` und nicht `zippe()`: *Geprüft ist der Weg, den
    ein Mensch geht, nicht der, den der Test kennt.*
    """
    modul, tmp_path, name = paket
    ziel = tmp_path / "aus"

    rc = modul.main(["--nach", str(ziel), "--bilder", str(tmp_path / "beweis"), "--zip"])

    assert rc == 0
    archiv = ziel.with_suffix(".zip")
    assert archiv.is_file() and archiv.stat().st_size > 0, (
        "--zip muss ein Archiv hinterlassen, nicht nur eine Zeile drucken")
    with zipfile.ZipFile(archiv) as z:
        assert f"aus/{name}/LIESMICH.md" in z.namelist()

    gedruckt = capsys.readouterr().out
    assert "Tafeln" in gedruckt and ".zip" in gedruckt, (
        f"und er sagt, was er getan hat: {gedruckt!r}")


def test_ohne_den_schalter_entsteht_kein_archiv(paket):
    """**GEGENPROBE.** Sonst prüfte die Probe darüber nur, dass überhaupt gezippt wird."""
    modul, tmp_path, _ = paket
    ziel = tmp_path / "aus"

    modul.main(["--nach", str(ziel), "--bilder", str(tmp_path / "beweis")])

    assert not ziel.with_suffix(".zip").exists(), "ohne --zip kein Archiv"
    assert (ziel / "LIESMICH.md").is_file(), "der Ordner entsteht trotzdem"
