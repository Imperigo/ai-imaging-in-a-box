"""Die Vakuumprobe — geprüft an einer Suite, deren Antwort wir vorher kennen.

Ein Werkzeug, das schwache Tests findet und selbst ungeprüft ist, wäre die Pointe des
eigenen Anlasses. Geprüft wird darum an einer winzigen, eigens gebauten Testsuite mit
genau einem vakuum-wahren und einem gefüllten Fall.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vakuumprobe  # noqa: E402


# ======================================================================================
# Was als vakuum-wahr erkannt wird
# ======================================================================================

@pytest.mark.parametrize("quelle, erwartet", [
    ("def t():\n    assert all(x for x in y)\n", 1),
    ("def t():\n    assert not any(x for x in y)\n", 1),
    ("def t():\n    assert any(x for x in y)\n", 0),          # any() über nichts ist False
    ("def t():\n    assert not all(x for x in y)\n", 0),      # dito
    ("def t():\n    assert len(y) == 3\n", 0),
])
def test_nur_die_vakuum_wahren_gestalten_werden_gefunden(quelle, erwartet):
    assert len(vakuumprobe.stellen(quelle)) == erwartet


def test_ein_all_ausserhalb_eines_assert_zaehlt_nicht():
    """Ein `all(...)` in einer Hilfsfunktion sagt nichts über den Ausgang eines Tests.

    Jeder Treffer, den ein Mensch als irrelevant abtut, macht die nächste Meldung eine
    Spur unglaubwürdiger.
    """
    assert vakuumprobe.stellen("def hilf(y):\n    return all(x for x in y)\n") == []


def test_die_zeilen_und_spalten_zeigen_auf_den_aufruf():
    treffer = vakuumprobe.stellen("def t():\n    assert all(x for x in y)\n")
    zeile, spalte, name = treffer[0]
    assert (zeile, name) == (2, "all")
    assert "    assert all(x for x in y)"[spalte:spalte + 3] == "all"


# ======================================================================================
# Das Umschreiben
# ======================================================================================

def test_umschreiben_ersetzt_nur_den_aufruf(tmp_path):
    datei = tmp_path / "test_x.py"
    datei.write_text("def t():\n    y = [1]\n    assert all(v for v in y)\n",
                     encoding="utf-8")
    assert vakuumprobe.schreibe_um(datei) == 1
    neu = datei.read_text(encoding="utf-8")
    assert "assert _all(v for v in y)" in neu
    assert "def _all(" in neu, "der Helfer muss mitkommen"


def test_eine_datei_ohne_treffer_bleibt_unangetastet(tmp_path):
    datei = tmp_path / "test_x.py"
    vorher = "def t():\n    assert 1 == 1\n"
    datei.write_text(vorher, encoding="utf-8")
    assert vakuumprobe.schreibe_um(datei) == 0
    assert datei.read_text(encoding="utf-8") == vorher


def test_mehrere_treffer_in_einer_datei_verschieben_sich_nicht(tmp_path):
    """Ersetzt wird von hinten nach vorn — sonst stimmen die späteren Zeilen nicht mehr."""
    datei = tmp_path / "test_x.py"
    datei.write_text(
        "def a():\n    assert all(v for v in y)\n\n"
        "def b():\n    assert not any(v for v in z)\n", encoding="utf-8")
    assert vakuumprobe.schreibe_um(datei) == 2
    neu = datei.read_text(encoding="utf-8")
    assert "assert _all(v for v in y)" in neu
    assert "assert not _any(v for v in z)" in neu


# ======================================================================================
# Der ganze Durchlauf, an einer Suite mit bekannter Antwort
# ======================================================================================

def _minisuite(basis: Path):
    (basis / "tests").mkdir(parents=True)
    (basis / "tests" / "test_mini.py").write_text(
        "def test_leer_und_damit_wertlos():\n"
        "    warnungen = []\n"
        "    assert not any('x' in w for w in warnungen)\n"
        "\n"
        "def test_gefuellt_und_damit_tragend():\n"
        "    warnungen = ['a', 'b']\n"
        "    assert all(isinstance(w, str) for w in warnungen)\n",
        encoding="utf-8")
    return basis


def test_der_durchlauf_findet_den_leeren_und_nicht_den_gefuellten(tmp_path):
    quelle = _minisuite(tmp_path / "quelle")
    befund = vakuumprobe.probe(quelle, tmp_path / "ziel")
    assert befund["umgeschrieben"] == 2, "beide Gestalten werden umgeschrieben"
    assert befund["treffer"] == ["tests/test_mini.py::test_leer_und_damit_wertlos"]


def test_eine_suite_ohne_vakuum_meldet_nichts(tmp_path):
    quelle = tmp_path / "quelle"
    (quelle / "tests").mkdir(parents=True)
    (quelle / "tests" / "test_mini.py").write_text(
        "def test_gefuellt():\n"
        "    assert all(w for w in [1, 2])\n", encoding="utf-8")
    befund = vakuumprobe.probe(quelle, tmp_path / "ziel")
    assert befund["umgeschrieben"] == 1
    assert befund["treffer"] == []


def test_das_repo_wird_nicht_angefasst(tmp_path):
    """Gearbeitet wird auf einer Kopie. Ein Werkzeug, das die Suite verändert, die es
    prüft, wäre unbrauchbar."""
    quelle = _minisuite(tmp_path / "quelle")
    vorher = (quelle / "tests" / "test_mini.py").read_text(encoding="utf-8")
    vakuumprobe.probe(quelle, tmp_path / "ziel")
    assert (quelle / "tests" / "test_mini.py").read_text(encoding="utf-8") == vorher


# ======================================================================================
# Die Nullprobe — ohne sie meldet das Werkzeug Fehlalarme
# ======================================================================================

def test_ein_schon_vorher_roter_test_ist_kein_treffer(tmp_path):
    """Der Fehler, den dieses Werkzeug am 20.08.2026 selbst gemacht hat.

    Die erste Fassung zählte jeden roten Test mit, sobald irgendwo im Protokoll das Wort
    ``VAKUUM`` auftauchte, und meldete **19 Treffer statt 6** — dreizehn davon waren
    Lexikon-Tests, die nur scheiterten, weil ``docs/`` nicht mitkopiert wurde.

    Ein Werkzeug, das schwache Tests sucht und selbst über-meldet, verliert seinen Zweck
    beim ersten Fehlalarm.
    """
    quelle = tmp_path / "quelle"
    (quelle / "tests").mkdir(parents=True)
    (quelle / "tests" / "test_mini.py").write_text(
        "def test_schon_immer_rot():\n"
        "    assert False, 'mit Vakuum hat das nichts zu tun'\n"
        "\n"
        "def test_leer_und_damit_wertlos():\n"
        "    assert not any('x' in w for w in [])\n",
        encoding="utf-8")

    befund = vakuumprobe.probe(quelle, tmp_path / "ziel")
    assert befund["treffer"] == ["tests/test_mini.py::test_leer_und_damit_wertlos"]
    assert befund["schon_vorher_rot"] == ["tests/test_mini.py::test_schon_immer_rot"]


def test_die_arbeitskopie_traegt_die_dokumente_mit(tmp_path):
    """`tests/test_lexikon.py` liest `docs/LEXIKON.md`. Fehlt der Ordner in der Kopie,
    scheitern dreizehn Tests aus einem Grund, der mit Vakuum nichts zu tun hat."""
    assert "docs" in vakuumprobe.MITKOPIEREN

    quelle = tmp_path / "quelle"
    (quelle / "tests").mkdir(parents=True)
    (quelle / "docs").mkdir()
    (quelle / "docs" / "etwas.md").write_text("da", encoding="utf-8")
    (quelle / "tests" / "test_mini.py").write_text(
        "from pathlib import Path\n"
        "def test_liest_ein_dokument():\n"
        "    assert (Path(__file__).parents[1] / 'docs' / 'etwas.md').is_file()\n",
        encoding="utf-8")

    befund = vakuumprobe.probe(quelle, tmp_path / "ziel")
    assert befund["schon_vorher_rot"] == [], "das Dokument muss in der Kopie liegen"
    assert befund["treffer"] == []
