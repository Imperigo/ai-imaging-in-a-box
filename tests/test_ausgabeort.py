"""Der Ausgabeort wird an EINER Stelle entschieden — Schreiber und Waechter fragen dieselbe.

WARUM ES DIESE PROBE GIBT (01.09.2026): am 28.08. lief die Bildkette zum ersten Mal ganz
durch und schrieb drei Bilder nach `/tmp/kosmo-jobs/<job>/out`. Der naechste Neustart nahm
sie mit — zehn Laeufe bis zum ersten Bild, und es ueberlebte den Tag nicht.

Der Umlenker `out_wurzel` war da und breit getestet, nur ohne CLI-Zeile. Beim Verkabeln lag
eine Falle bereit: die Fortschrittswache in `tools/abholen.py` rechnete den Ordner ein
ZWEITES Mal aus und las dabei immer `auftrag["ausgabe"]`. Solange `out_wurzel` fehlte, waren
beide gleich und nichts fiel auf. Mit gesetztem `out_wurzel` haette die Wache einen leeren
Ordner bewacht und Stillstand gemeldet, waehrend die Bilder daneben entstehen.
"""
from pathlib import Path
import ast, re
from aiimaging import abholer


def test_ausgabeort_biegt_um_und_behaelt_den_namen(tmp_path):
    auftrag = {"verzeichnis": tmp_path / "vis-4711", "ausgabe": tmp_path / "vis-4711" / "out"}
    ohne = abholer.ausgabeort(auftrag, None)
    mit = abholer.ausgabeort(auftrag, tmp_path / "dauerhaft")
    assert ohne == tmp_path / "vis-4711" / "out"
    assert mit == tmp_path / "dauerhaft" / "vis-4711", "Der Auftragsname muss erhalten bleiben"


def test_die_wache_rechnet_den_ort_nicht_selbst_aus():
    """Die Falle beim Verkabeln — sie faellt an der Fassung vom 28.08. durch.

    Dort stand in `wache_bauen` woertlich `ziel = Path(auftrag["ausgabe"])`. Diese Probe
    liest den Quelltext, weil der Fehler nur bei gesetztem `--out-wurzel` sichtbar wuerde
    und ein Lauf dafuer eine echte GPU braucht.
    """
    quelle = Path(abholer.__file__).parent.parent.parent / "tools" / "abholen.py"
    baum = ast.parse(quelle.read_text(encoding="utf-8"))
    wache = next(n for n in ast.walk(baum)
                 if isinstance(n, ast.FunctionDef) and n.name == "wache_bauen")
    text = ast.unparse(wache)
    assert 'auftrag["ausgabe"]' not in text and "auftrag['ausgabe']" not in text, (
        "wache_bauen rechnet den Ausgabeort selbst aus. Mit --out-wurzel bewacht sie dann "
        "einen leeren Ordner und meldet Stillstand, waehrend nebenan geschrieben wird.")
    assert "ausgabeort" in text, "Sie muss abholer.ausgabeort fragen — die eine Stelle."


def test_die_cli_reicht_die_wurzel_wirklich_durch():
    quelle = Path(abholer.__file__).parent.parent.parent / "tools" / "abholen.py"
    t = quelle.read_text(encoding="utf-8")
    assert '"--out-wurzel"' in t, "Der Schalter fehlt — der Umlenker bleibt unbedienbar."
    assert re.search(r"verarbeiter\(\s*out_wurzel=a\.out_wurzel", t), (
        "Der Schalter wird angenommen, aber nicht an den verarbeiter uebergeben.")
