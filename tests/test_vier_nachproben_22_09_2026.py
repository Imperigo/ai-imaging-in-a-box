"""Vier kleine Befunde derselben Durchsicht (22.09.2026) — je einer mit seinem Waechter.

Alle vier haben dieselbe Wurzel: **eine Auskunft, die still ihre Bedeutung wechselt.**

(a) Eine unlesbare ``auftraege/zustellung.json`` galt beim VERMERKEN als leer. Der
    naechste Vermerk mit einer neuen Kennung ersetzte darauf die ganze Datei — alle
    alten Zustellzeiten waren weg, und niemand hat es gesehen.
(b) ``tools/einbau.py`` sortierte die Posten, die auf eine vorhandene Antwort warten,
    mit ``-(seit_tagen or 0)``. Ein Posten ohne Antwortdatum stand ganz unten, als waere
    er der juengste — dabei kann er der aelteste sein.
(c) ``kosmo_szene._andere_kameras_einrechnen`` zaehlte die Zwillingsansicht einer
    ANDEREN Kamera als zweiten Befund: ein Bild, zwei Kameranamen im Grund.
(d) Die Schemakennung ``kosmovis.render-scene/v1`` stand zweimal im Kern, in
    ``kosmo_naht`` und in ``kosmo_szene``, und keine las die andere.

Jeder Waechter prueft die WIRKUNG — bei (b) und (c) ueber den Weg, den das Produkt
wirklich geht (``tools/einbau.py main``, ``abholer.hole_einen`` bis in die geschriebene
Datei). Nur (d) sieht in den Quelltext, und dort nach der ABWESENHEIT einer Zutat.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from aiimaging import abholer, auftragspost, bruecke, kosmo_naht, kosmo_szene

from test_abholer import _auftrag, _kette
from test_vertrag_jede_kamera_spricht import SAUBER, WIDERSPRUCH

WURZEL = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------------------
# (a) Eine unlesbare Zustellablage wird nicht still ueberschrieben
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("inhalt", [
    '{"auf-20260901-01": "2026-09-01T00:00:00Z",\n',     # abgerissen mitten im Schreiben
    '["auf-20260901-01"]\n',                              # lesbar, aber kein Woerterbuch
])
def test_eine_kaputte_zustellablage_laesst_den_vermerk_laut_scheitern(tmp_path, inhalt):
    """Bis zum 22.09.2026 wurde die kaputte Datei als leer gelesen und beim ersten neuen
    Vermerk durch ``{"auf-neu": …}`` ersetzt. Der alte Zustellzeitpunkt stand danach
    nirgends mehr — und «die erste Zustellung zaehlt» galt fuer niemanden mehr."""
    ziel = tmp_path / auftragspost.ZUSTELLUNG_DATEI
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(inhalt, encoding="utf-8")
    vorher = ziel.read_bytes()

    with pytest.raises(auftragspost.PostError, match="nicht lesbar|kein Woerterbuch"):
        auftragspost.vermerke_zustellung(tmp_path, ["auf-20260922-01"])

    assert ziel.read_bytes() == vorher, "die unlesbare Ablage wurde trotzdem ueberschrieben"
    # Und kein halbfertiger Zwischenstand bleibt neben ihr liegen.
    assert sorted(p.name for p in ziel.parent.iterdir()) == [ziel.name]


def test_eine_lesbare_zustellablage_wird_weiter_ergaenzt(tmp_path):
    """Die Gegenprobe: Das laute Scheitern gilt der KAPUTTEN Datei, nicht jeder."""
    ziel = tmp_path / auftragspost.ZUSTELLUNG_DATEI
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps({"auf-20260901-01": "2026-09-01T00:00:00Z"}),
                    encoding="utf-8")

    assert auftragspost.vermerke_zustellung(
        tmp_path, ["auf-20260922-01"], wann="2026-09-22T00:00:00Z") == 1

    assert json.loads(ziel.read_text(encoding="utf-8")) == {
        "auf-20260901-01": "2026-09-01T00:00:00Z",
        "auf-20260922-01": "2026-09-22T00:00:00Z"}
    # DAS FORMAT BLEIBT ZEICHEN FUER ZEICHEN (Durchsicht 22.09.2026): Der Kommentar in
    # `vermerke_zustellung` sagt es zu, bis dahin verglich diese Probe nur den Inhalt.
    # Jede Formatverschiebung erschiene sonst als Aenderung an jeder alten Zeile der
    # eingecheckten Datei — und der Verlauf, um den es geht, waere im Diff nicht lesbar.
    text = ziel.read_text(encoding="utf-8")
    assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------------------
# (b) Ein Posten unbekannten Alters steht nicht als juengster da
# --------------------------------------------------------------------------------------

def _einbau_cli():
    pfad = WURZEL / "tools" / "einbau.py"
    spec = importlib.util.spec_from_file_location("werkzeug_einbau_nachprobe", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _auftrag_mit_antwort(wurzel: Path, kennung: str, beendet: str) -> None:
    offen = wurzel / "auftraege" / "offen"
    offen.mkdir(parents=True, exist_ok=True)
    (offen / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-auftrag/v1", "auftrag_id": kennung,
        "art": "qa", "worker": "local", "rang": 1, "params": {},
        "beschreibung": "Probe", "anweisung": "Probe",
    }, ensure_ascii=False), encoding="utf-8")
    ergebnisse = wurzel / "auftraege" / "ergebnisse"
    ergebnisse.mkdir(parents=True, exist_ok=True)
    (ergebnisse / f"{kennung}.json").write_text(json.dumps({
        "schema": "aiimaging.homeworker-ergebnis/v1", "auftrag_id": kennung,
        "status": "ok", "beendet": beendet, "zusammenfassung": "gemessen",
    }, ensure_ascii=False), encoding="utf-8")


def test_ein_posten_ohne_antwortdatum_steht_nicht_als_juengster(tmp_path, capsys):
    """Ueber ``tools/einbau.py main`` an einem synthetischen Probeordner.

    Drei Posten warten auf eine Antwort, die da ist: einer alt (Anfang August), einer
    frisch (gestern bis vor kurzem), einer ohne Datum. Der undatierte steht in der Tafel
    ZULETZT — mit dem alten Schluessel ``-(seit_tagen or 0)`` landete er darum als
    «0 Tage» ganz unten, unter dem juengsten.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "EINBAU_STAND.md").write_text("\n".join([
        "| # | Posten | Zustand | Seit | Beleg |",
        "|---|---|---|---|---|",
        "| C3 | Alt | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-01 | `auf-20260801-57` (local) |",
        "| C5 | Frisch | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-01 | `auf-20260801-58` (local) |",
        "| C4 | Undatiert | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-01 | `auf-20260801-59` (local) |",
    ]) + "\n", encoding="utf-8")
    _auftrag_mit_antwort(tmp_path, "auf-20260801-57", "2026-08-02T00:00:00Z")
    _auftrag_mit_antwort(tmp_path, "auf-20260801-58", "2026-09-21T00:00:00Z")
    _auftrag_mit_antwort(tmp_path, "auf-20260801-59", "")

    _einbau_cli().main(["--repo", str(tmp_path)])
    ausgabe = capsys.readouterr().out

    abschnitt = ausgabe.split("WARTEN AUF EINE ANTWORT, DIE DA IST", 1)
    assert len(abschnitt) == 2, ausgabe
    # Nur dieser Abschnitt — der Einbau-Stand darunter nennt dieselben Kennungen noch
    # einmal, in der Reihenfolge der Tafel.
    abschnitt = abschnitt[1].split("Jeder dieser Posten nennt NUR", 1)[0]
    zeilen = [z for z in abschnitt.splitlines() if re.match(r"\s+C[345]\s", z)]
    reihe = [z.split()[0] for z in zeilen]
    assert sorted(reihe) == ["C3", "C4", "C5"], ausgabe
    # Die bekannten stehen weiter aeltester zuerst — die Reparatur dreht nichts um.
    assert reihe.index("C3") < reihe.index("C5"), reihe
    # Und der undatierte steht NICHT unter dem juengsten.
    assert reihe.index("C4") < reihe.index("C5"), (
        "Ein Posten unbekannten Alters steht als juengster da: " + " / ".join(zeilen))


# --------------------------------------------------------------------------------------
# (c) Die Zwillingsansicht einer ANDEREN Kamera ist kein zweiter Befund
# --------------------------------------------------------------------------------------

def _szene_drei_kameras():
    return {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [
            {"name": "Eingang", "position": [0, -20, 1.3], "target": [0, 0, 1.3],
             "fov": 60, "up_axis": "z"},
            {"name": "Uebersicht", "position": [0, -60, 38], "target": [0, 0, 5],
             "fov": 50, "up_axis": "z"},
            {"name": "Gegenueber", "position": [0, 60, 38], "target": [0, 0, 5],
             "fov": 50, "up_axis": "z"},
        ],
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus"},
        "vis": {"backbone": "qwen"},
    }


def test_der_zwilling_einer_anderen_kamera_wird_nur_einmal_genannt(tmp_path):
    """Produktweg wie in ``test_vertrag_jede_kamera_spricht``: ``abholer.hole_einen`` bis
    in die Datei, die die fremde Warteschlange liest.

    ``Eingang`` ist die schlechteste Kamera und besteht; ``Uebersicht`` faellt GEMESSEN
    an Tor A durch. ``Gegenueber`` hat dieselbe Soll-Karte wie ``Uebersicht`` und wird
    darum nicht gerendert, sondern uebernimmt deren Bild und Urteil (``doppelt_von``).
    Vor dem 22.09.2026 stand dann «'Uebersicht', 'Gegenueber'» im Grund — ein Bild als
    zwei Befunde.
    """
    gemessen: list = []

    def soll(bericht):
        # Zwei gleiche Karten fuer die zweite und dritte Kamera, eine eigene fuer die
        # erste. Die Kamera steht im Ordner, in den die Attrappe ihren Tiefenpass legt.
        ordner = str(Path(bericht["depth_png"]).parent)
        if "Eingang" in ordner:
            return [[0.0, 1.0], [2.0, 3.0]], 2, 2
        return [[5.0, 6.0], [7.0, 8.0]], 2, 2

    def qa(bild, soll_werte, **kw):
        if Path(bild).name.startswith("nullprobe_"):
            return {"status": "ok", "score": 0.30, "bestanden": False}
        gemessen.append(Path(bild).parent.name)
        return dict(SAUBER if "Eingang" in str(bild) else WIDERSPRUCH)

    ordner = _auftrag(tmp_path, szene=_szene_drei_kameras())
    _, attrappen = _kette()
    attrappen["_qa"] = qa
    attrappen["_soll"] = soll
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    erg = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))

    # Vorbedingung: Es gab wirklich einen Zwilling der ANDEREN Kamera.
    assert sorted(set(gemessen)) == ["Eingang", "Uebersicht"], gemessen
    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang"
    assert tore["passed"] is False and tore["released"] is False

    befunde = [g for g in tore["fail_reasons"] if g.startswith("kamera_nicht_bestanden:")]
    assert befunde == ["kamera_nicht_bestanden:Uebersicht"], tore["fail_reasons"]
    assert tore["reason"].startswith("NICHT BESTANDEN wegen Kamera 'Uebersicht'. "), (
        tore["reason"])
    text = " ".join([tore["reason"], *tore.get("warnings", ())])
    assert "Gegenueber" not in text, text


# --------------------------------------------------------------------------------------
# (d) Eine Schemakennung, eine Stelle
# --------------------------------------------------------------------------------------

def test_die_szenenkennung_steht_nur_in_kosmo_szene():
    """Die Naht liest die Kennung aus ``kosmo_szene`` — dasselbe Objekt, keine Kopie.

    Geprueft wird zweierlei: dass es DASSELBE Objekt ist (eine gleichlautende Kopie
    bestuende einen Gleichheitstest, aber nicht diesen), und dass im Kern keine zweite
    Zeichenkette dieser Kennung als Wert steht. Erwaehnungen in Kommentaren und
    Docstrings zaehlen nicht — sie stehen in Backticks, nicht in Anfuehrungszeichen.
    """
    assert kosmo_naht.SCHEMA_RENDER_SCENE is kosmo_szene.SCHEMA_SZENE

    wert = re.compile(r"""(["'])kosmovis\.render-scene/v1\1""")
    fundorte = [pfad.name for pfad in sorted((WURZEL / "src" / "aiimaging").rglob("*.py"))
                if wert.search(pfad.read_text(encoding="utf-8"))]
    assert fundorte == ["kosmo_szene.py"], fundorte
