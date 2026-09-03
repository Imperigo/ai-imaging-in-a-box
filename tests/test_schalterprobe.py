"""Die Schalterprobe — und die Schalter, die sie gefunden hat.

*Der Anlass sind drei Fehler eines Tages, alle derselben Sorte:* Ein
Kommandozeilenschalter, den nie eine Probe gedrückt hat, kann still nichts tun. Am
01.09.2026 kamen **9 von 33** Schaltern in keiner einzigen Probe vor, und zwei davon
waren kaputt — `auftragspost --auftrag X --nach Y` druckte statt abzulegen, und
`einbau --worker kern` wurde mit «invalid choice» abgewiesen, weil die Liste der
Adressaten ein zweites Mal im Skript stand.

Diese Datei prüft das Werkzeug **und drückt die gefundenen Schalter**.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from aiimaging import auftrag

WURZEL = Path(__file__).resolve().parents[1]


def _werkzeug(name: str):
    pfad = WURZEL / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"werkzeug_{name}", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ======================================================================================
# Das Werkzeug selbst
# ======================================================================================

def test_es_findet_die_angemeldeten_schalter(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tools" / "beispiel.py").write_text(
        'ap.add_argument("--gedrueckt")\nap.add_argument("--nie")\n', encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text('main(["--gedrueckt"])\n',
                                                  encoding="utf-8")

    befund = _werkzeug("schalterprobe").ungedrueckt(tmp_path)

    assert befund["n_gesamt"] == 2
    assert befund["je_werkzeug"] == {"beispiel.py": ["--nie"]}


def test_ein_schalter_in_einfachen_anfuehrungszeichen_gilt_als_gedrueckt(tmp_path):
    """Proben schreiben mal `"--x"` und mal `'--x'`. Wer nur eine Form sucht, meldet
    Schalter als ungedrückt, die längst geprüft sind — und eine Liste mit falschen
    Einträgen wird nicht gelesen."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tools" / "beispiel.py").write_text('ap.add_argument("--x")\n',
                                                    encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text("main(['--x'])\n", encoding="utf-8")

    assert _werkzeug("schalterprobe").ungedrueckt(tmp_path)["je_werkzeug"] == {}


def test_absichtlich_ungedrueckte_schalter_stehen_mit_begruendung_da():
    """*Eine wachsende Liste dort ist ein Zeichen dafür, dass weggesehen statt geprüft
    wird* — deshalb trägt jeder Eintrag einen Grund und nicht bloss einen Namen."""
    absichtlich = _werkzeug("schalterprobe").ABSICHTLICH
    assert absichtlich, "leer wäre verdächtig: --help meldet argparse immer"
    for schalter, grund in absichtlich.items():
        assert schalter.startswith("--")
        assert len(grund) > 15, (schalter, grund)


def test_der_einstieg_laeuft_und_kennt_beide_formen(capsys):
    """`--json` und `--wurzel` sind selbst zwei der Schalter, die dieses Werkzeug zählt.
    *Ein Zähler, der seine eigenen Schalter nicht drückt, ist ein schlechter Zeuge.*"""
    schalterprobe = _werkzeug("schalterprobe")
    assert schalterprobe.main(["--wurzel", str(WURZEL), "--json"]) == 0
    befund = json.loads(capsys.readouterr().out)
    assert befund["n_gesamt"] > 20
    assert schalterprobe.main(["--wurzel", str(WURZEL)]) == 0
    assert "keiner Probe" in capsys.readouterr().out


# ======================================================================================
# Die gefundenen Schalter, jetzt gedrückt
# ======================================================================================

def test_einbau_worker_kennt_JEDEN_adressaten(capsys):
    """**Der Fehler, den die Schalterprobe gefunden hat.**

    Die Auswahlliste stand ein zweites Mal im Skript und war seit dem 28.08.2026
    veraltet: `--worker kern` wurde mit «invalid choice» abgewiesen. Sie kommt jetzt aus
    `auftrag.WORKER` — die Liste steht an einer Stelle, und diese Probe fährt **jeden**
    Wert daraus, nicht einen ausgesuchten.
    """
    einbau = _werkzeug("einbau")
    for name in auftrag.WORKER:
        assert einbau.main(["--repo", str(WURZEL), "--worker", name]) in (0, 1), name
        assert name in capsys.readouterr().out, name


def test_einbau_json_ist_lesbar(capsys):
    einbau = _werkzeug("einbau")
    assert einbau.main(["--repo", str(WURZEL), "--json"]) in (0, 1)
    satz = json.loads(capsys.readouterr().out)
    assert "rueckstand" in satz and "antwortverhalten" in satz


def test_auftragspost_neueste_gibt_genau_einen_block(capsys):
    post = _werkzeug("auftragspost")
    assert post.main(["--repo", str(WURZEL), "ui", "--neueste"]) == 0
    ausgabe = capsys.readouterr().out
    assert ausgabe.count("AUFTRAG auf-") == 1, "«neueste» heisst einer, nicht alle"


def test_vakuumprobe_wurzel_zeigt_auf_ein_fremdes_verzeichnis(tmp_path, capsys):
    """`--wurzel` ohne Probe war die Frage: Läuft das Werkzeug überhaupt woanders?

    Der Baum hier ist winzig, aber vollständig: eine Quelle, eine Probe, die sie benutzt.
    **Ein leeres Verzeichnis wäre der falsche Versuch** — dann meldet das Werkzeug «keine
    Tests» und man hätte geprüft, dass es mit nichts nichts anfängt.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "winzig.py").write_text(
        "def zaehle(x):\n    return [w for w in x if w > 0]\n", encoding="utf-8")
    (tmp_path / "tests" / "test_winzig.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(tmp_path / 'src')!r})\n"
        "from winzig import zaehle\n\n"
        "def test_alle_positiv():\n"
        "    assert all(w > 0 for w in zaehle([1, 2]))\n", encoding="utf-8")

    vakuum = _werkzeug("vakuumprobe")
    assert vakuum.main(["--wurzel", str(tmp_path)]) in (0, 1)
    assert "Treffer" in capsys.readouterr().out


def test_die_drei_abholer_schalter_erreichen_den_wirklichen_aufruf(monkeypatch, tmp_path):
    """**Am Aufrufer geprüft, nicht an der Zerlegung der Kommandozeile.**

    Dass `argparse` `--stil` in `a.stil` legt, ist keine Auskunft — die Frage ist, ob der
    Wert bei `abholer.verarbeiter` ankommt. Dieselbe Lehre wie am 28.08. bei
    `_schalter_aus` und am 01.09. bei `darf_starten`: *Ein Wächter, der den Aufruf selbst
    nachbaut, bewacht seine eigene Nachbildung.*
    """
    abholen = _werkzeug("abholen")
    gesehen = {}

    def _falle(**kwargs):
        gesehen.update(kwargs)
        raise SystemExit(0)                 # nach dem Aufruf ist die Frage beantwortet

    monkeypatch.setattr(abholen.abholer, "verarbeiter", _falle)
    with pytest.raises(SystemExit):
        abholen.main(["--store", str(tmp_path), "--stil", "kosmo_standard",
                      "--seeds", "11,22,33", "--ohne-nullprobe"])

    assert gesehen["stil"] == "kosmo_standard"
    assert gesehen["seeds"] == (11, 22, 33), "mehrere Seeds heisst: alle rendern"
    assert gesehen["nullprobe"] is False, "--ohne-nullprobe laesst die Kontrollanker weg"


def test_ohne_die_schalter_gelten_die_vorgaben(monkeypatch, tmp_path):
    """Die Gegenprobe. Ohne sie wäre der Test darüber auch grün, wenn die Werte fest
    verdrahtet wären — und `--ohne-nullprobe` ist der gefährliche von den dreien:
    *«Nicht empfohlen — siehe auf-21.»*"""
    abholen = _werkzeug("abholen")
    gesehen = {}

    def _falle(**kwargs):
        gesehen.update(kwargs)
        raise SystemExit(0)

    monkeypatch.setattr(abholen.abholer, "verarbeiter", _falle)
    with pytest.raises(SystemExit):
        abholen.main(["--store", str(tmp_path)])

    assert gesehen["stil"] is None
    assert gesehen["nullprobe"] is True, "die Kontrollanker sind die Vorgabe"
    assert gesehen["seeds"] == abholen.abholer.VORGABE_SEEDS


def test_vakuumprobe_zeige_kopie_behaelt_das_arbeitsverzeichnis(tmp_path, capsys):
    """Der Schalter verspricht, den Ordner **nicht** aufzuräumen. Geprüft wird, dass der
    genannte Pfad hinterher wirklich noch da ist — ein gedruckter Pfad ist keine Datei."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "winzig.py").write_text(
        "def zaehle(x):\n    return [w for w in x if w > 0]\n", encoding="utf-8")
    (tmp_path / "tests" / "test_winzig.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(tmp_path / 'src')!r})\n"
        "from winzig import zaehle\n\n"
        "def test_alle_positiv():\n"
        "    assert all(w > 0 for w in zaehle([1, 2]))\n", encoding="utf-8")

    vakuum = _werkzeug("vakuumprobe")
    assert vakuum.main(["--wurzel", str(tmp_path), "--zeige-kopie"]) in (0, 1)
    ausgabe = capsys.readouterr().out

    assert "behalten" in ausgabe
    pfad = Path(ausgabe.split("behalten:")[1].strip().splitlines()[0])
    assert pfad.is_dir(), f"der genannte Ordner {pfad} gibt es nicht"


def test_kein_schalter_bleibt_ungedrueckt():
    """**Der Wächter, und er ist der Zweck dieser Datei.**

    Am 01.09.2026 kamen 9 von 33 Schaltern in keiner Probe vor. Zwei davon waren kaputt,
    und drei weitere konnten gar nicht geprüft werden, weil `abholen.main()` kein `argv`
    entgegennahm — *ein Einstieg, den keine Probe aufrufen kann, hat keine ungeprüften
    Schalter, er ist selbst einer.*

    Die Zahl steht hier auf **null** und nicht auf einer Obergrenze: Eine Obergrenze wäre
    ein Vorrat, den man aufbraucht. Wer einen Schalter baut, schreibt die Probe dazu —
    oder trägt ihn mit Begründung in `ABSICHTLICH` ein, wo ihn jeder sieht.
    """
    befund = _werkzeug("schalterprobe").ungedrueckt(WURZEL)
    assert befund["n_ungedrueckt"] == 0, befund["je_werkzeug"]
    assert befund["n_gesamt"] >= 30, "ohne Schalter sagt dieser Test nichts"


def test_der_waechter_faellt_bei_einem_neuen_ungedrueckten_schalter(tmp_path):
    """Die Gegenprobe zum Wächter darüber: Er meldet wirklich, statt immer null zu sagen."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tools" / "neu.py").write_text('ap.add_argument("--frisch")\n',
                                               encoding="utf-8")
    (tmp_path / "tests" / "test_leer.py").write_text("pass\n", encoding="utf-8")

    assert _werkzeug("schalterprobe").ungedrueckt(tmp_path)["n_ungedrueckt"] == 1


# ======================================================================================
# Und ein falscher Alarm des Nachbarwerkzeugs
# ======================================================================================

def test_tote_kanten_sieht_einen_aufruf_ueber_getattr(tmp_path):
    """**Der falsche Alarm vom 02.09.2026.**

    `tools/tote_kanten.py` meldete `jobs.vermerke_meldung` als «von keinem Einstiegspunkt
    erreichbar», obwohl der Weg dorthin lebt: Er läuft über
    `getattr(quelle, "vermerke_grund", None)`, und ein solcher Aufruf ist im Syntaxbaum
    keine Attributzugriff, sondern eine Zeichenkette.

    *Ein Werkzeug, das falsche Alarme gibt, wird nicht schärfer gelesen, sondern gar
    nicht mehr.* Es meldet mit Absicht lieber zu wenig als zu viel — dieser Fall gehörte
    auf die andere Seite.
    """
    import ast
    tote = _werkzeug("tote_kanten")
    baum = ast.parse('def f(x):\n    return getattr(x, "gesucht", None)\n')

    assert "gesucht" in tote._namen_in(baum)


def test_eine_gewoehnliche_zeichenkette_gilt_NICHT_als_name():
    """Die Gegenprobe, und sie ist die wichtigere: Zählte jede Zeichenkette als Name,
    hielte ein Wort in irgendeiner Fehlermeldung jede tote Kante am Leben."""
    import ast
    tote = _werkzeug("tote_kanten")
    baum = ast.parse('def f():\n    return "gesucht"\n')

    assert "gesucht" not in tote._namen_in(baum)
