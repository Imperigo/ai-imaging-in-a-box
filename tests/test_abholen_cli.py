"""``tools/abholen.py`` — der Betriebs-Einstieg, geprüft an seiner Verdrahtung.

Warum diese Datei existiert
---------------------------
``tools/abholen.py`` ist am 19.08.2026 entstanden, weil :mod:`aiimaging.abholer` alles
konnte und **niemand es rief**. Ein Modul, das nie läuft, ist von einem fehlenden Modul
nicht zu unterscheiden.

Genau dieselbe Fehlerart kann sich im Einstieg wiederholen, eine Ebene tiefer: ein
Schalter, den ``argparse`` kennt und den niemand weiterreicht. ``--stillstand-frist-s``
stünde dann in der Hilfe, und die Wache liefe trotzdem mit der Vorgabe — oder gar nicht.
Diese Datei prüft darum nicht, was der Abholer tut (das steht in ``test_abholer.py``),
sondern **dass die Angaben des Betriebs bei ihm ankommen**.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _abholen():
    """``tools/`` ist kein Paket — wie in ``test_testgeometrie.py``."""
    pfad = REPO / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_pruefling", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _lauf(monkeypatch, tmp_path, argv, ausgabe):
    """Den Einstieg fahren und festhalten, womit er ``durchgang`` gerufen hat."""
    modul = _abholen()
    gesehen: dict = {}

    def falscher_durchgang(store, **kw):
        gesehen.update(kw)
        gesehen["store"] = store
        return {"gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
                "gestanden": 0, "waisen": [], "ergebnisse": []}

    monkeypatch.setattr(modul.abholer, "durchgang", falscher_durchgang)
    monkeypatch.setattr(modul.abholer, "verarbeiter", lambda **kw: (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path), *argv])

    assert modul.main() == 0
    return gesehen


def test_die_frist_des_betriebs_kommt_bei_der_wache_an(monkeypatch, tmp_path):
    """Der Schalter darf nicht bloss in der Hilfe stehen.

    Geprüft an der **gebauten Wache**, nicht am gemerkten Argument: Ein Wert, der
    entgegengenommen und dann verworfen wird, sähe an einem Argument-Test gleich aus.
    """
    ausgabe = tmp_path / "job" / "out"
    gesehen = _lauf(monkeypatch, tmp_path, ["--stillstand-frist-s", "42"], ausgabe)

    wache = gesehen["wache_bauen"]({"ausgabe": ausgabe, "job_id": "vis-1-abcdef"})
    assert wache.frist_s == 42.0


def test_ohne_wache_wird_keine_gebaut(monkeypatch, tmp_path):
    """`None` heisst im Abholer „nicht beobachtet" — und genau das soll ankommen."""
    gesehen = _lauf(monkeypatch, tmp_path, ["--ohne-wache"], tmp_path / "out")

    assert gesehen["wache_bauen"] is None


def test_die_wache_haengt_am_ausgabeordner_und_legt_ihn_an(monkeypatch, tmp_path):
    """Sonst fände der erste Blick nichts vor.

    Die Uhr liefe dann ab Beginn statt ab dem ersten Zeichen, und ein Auftrag, dessen
    erstes Bild spät kommt, sähe aus wie einer, der steht.
    """
    ausgabe = tmp_path / "job" / "out"
    gesehen = _lauf(monkeypatch, tmp_path, [], ausgabe)
    assert not ausgabe.exists()

    wache = gesehen["wache_bauen"]({"ausgabe": ausgabe, "job_id": "vis-1-abcdef"})

    assert ausgabe.is_dir()
    assert wache.blick()["befund"] is None       # der Ordner ist da, also gibt es ein Zeichen


def test_die_wache_ist_belegt_und_nicht_behauptet(monkeypatch, tmp_path):
    """Eine neue Datei taucht auf, weil etwas fertig wurde — nicht, weil jemand es sagt.

    Der Unterschied entscheidet über `warn` gegen `error`: Nur bei belegtem Zeichen heisst
    Stillstand wirklich Stillstand.
    """
    from aiimaging import fortschritt

    gesehen = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    wache = gesehen["wache_bauen"]({"ausgabe": tmp_path / "out", "job_id": "vis-1-abcdef"})

    assert wache.art == fortschritt.BELEGT


def test_die_voreingestellte_frist_ist_die_uebernommene_und_keine_eigene(monkeypatch, tmp_path):
    """Sie ist aus dem Altbestand und **nicht gemessen** — das steht so in der Hilfe.

    Der Test hält sie an die Modulkonstante gebunden, damit sie nicht still zu einer
    zweiten, abweichenden Zahl auseinanderläuft.
    """
    from aiimaging import fortschritt

    gesehen = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    wache = gesehen["wache_bauen"]({"ausgabe": tmp_path / "out", "job_id": "vis-1-abcdef"})

    assert wache.frist_s == fortschritt.FRIST_S


def test_der_betreiber_entscheid_zur_fremden_freigabe_bleibt_voreingestellt_aus(
        monkeypatch, tmp_path):
    """Die Regel, wegen der es diesen Einstieg überhaupt gibt — hier gegen ein Versehen."""
    ohne = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    mit = _lauf(monkeypatch, tmp_path, ["--fremde-freigabe"], tmp_path / "out")

    assert ohne["fremde_freigabe_gilt"] is False
    assert mit["fremde_freigabe_gilt"] is True


# ======================================================================================
# Der Befund erreicht den Menschen davor
# ======================================================================================

def _lauf_mit_ergebnissen(monkeypatch, tmp_path, capsys, ergebnisse):
    """Den Einstieg mit vorgegebenen Auftragsantworten fahren und die Ausgabe fangen."""
    modul = _abholen()

    monkeypatch.setattr(modul.abholer, "durchgang", lambda store, **kw: {
        "gesehen": len(ergebnisse), "verarbeitet": len(ergebnisse), "fehler": 0,
        "liegengelassen": 0, "gestanden": 0, "waisen": [], "ergebnisse": ergebnisse})
    monkeypatch.setattr(modul.abholer, "verarbeiter", lambda **kw: (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path)])

    assert modul.main() == 0
    return capsys.readouterr().out


def _befund_ablegen(ordner, inhalt):
    import json

    from aiimaging import abholer

    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / abholer.DATEI_BEFUND).write_text(json.dumps(inhalt, ensure_ascii=False),
                                               encoding="utf-8")
    return ordner


def test_der_befund_erscheint_in_der_ausgabe(monkeypatch, tmp_path, capsys):
    """Der eigentliche Zweck: Was der Lauf gemessen hat, soll den Betreiber erreichen,
    ohne dass er eine Datei suchen muss.

    Bis zum 23.08.2026 sah er „3 Bild(er) geschrieben" und die Wache — von der
    Übersetzung, der Kameraspanne und der Kompositionsprüfung nichts.
    """
    ordner = _befund_ablegen(tmp_path / "vis-1-abcdef", {
        "prompt": "overcast sky", "prompt_sprache": {
            "noetig": True, "verfahren": "glossar", "original": "bedeckter Himmel",
            "vollstaendig": True},
        "geometrie_urteil": {"kameraspanne": {
            "n_gemessen": 3, "schlechtester": 0.66, "bester": 0.81}},
        "kameras": [{"kamera": "s", "komposition": {"beurteilt": True,
                                                    "warnungen": ["Neigung 2.5°"]}}],
    })
    ausgabe = _lauf_mit_ergebnissen(monkeypatch, tmp_path, capsys, [
        {"job_id": "vis-1-abcdef", "status": "verarbeitet", "grund": "3 Bild(er).",
         "verzeichnis": ordner, "wache": None, "warnungen": ()}])

    assert "Prompt uebersetzt" in ausgabe
    assert "bedeckter Himmel" in ausgabe
    assert "schlechteste von 3 Kameras" in ausgabe
    assert "Komposition, alle 1 Kameras: Neigung" in ausgabe


def test_ohne_befund_bleibt_die_ausgabe_wie_vorher(monkeypatch, tmp_path, capsys):
    """Gegenprobe. Ein Auftrag ohne Befund darf keine leeren Zeilen erzeugen — und der
    Einstieg darf daran nicht scheitern."""
    ausgabe = _lauf_mit_ergebnissen(monkeypatch, tmp_path, capsys, [
        {"job_id": "vis-1-abcdef", "status": "liegengelassen", "grund": "Kein Token.",
         "verzeichnis": tmp_path / "leer", "wache": None, "warnungen": ()}])

    assert "vis-1-abcdef" in ausgabe
    assert "Prompt uebersetzt" not in ausgabe
    assert "Geometrie:" not in ausgabe


def test_die_warnungen_des_auftrags_erscheinen_ebenfalls(monkeypatch, tmp_path, capsys):
    """Sie kommen aus `lies_auftrag` und wurden bis zum 22.08.2026 gar nicht
    weitergereicht — eine tote Kante auf dem Weg der Warnung selbst."""
    ausgabe = _lauf_mit_ergebnissen(monkeypatch, tmp_path, capsys, [
        {"job_id": "vis-1-abcdef", "status": "verarbeitet", "grund": "1 Bild.",
         "verzeichnis": tmp_path / "leer", "wache": None,
         "warnungen": ("Keine Sonnenangabe.",)}])

    assert "! Keine Sonnenangabe." in ausgabe


def test_der_gelaendestand_des_betriebs_kommt_an(monkeypatch, tmp_path):
    """Die Warnung war da, der Handgriff fehlte.

    Die Kompositionsprüfung meldet bei jedem Auftrag den unzuverlässigen Bezugspunkt —
    zu Recht, denn aus einer glb ist der Geländestand nicht zu erfahren. Nur konnte ihn
    ein Betreiber bis zum 23.08.2026 auch nicht **setzen**: `verarbeiter` nahm ihn nicht
    entgegen, obwohl die Naht und der Runner ihn seit langem kennen. Eine Dauerwarnung
    ohne Handgriff ist keine Warnung mehr, sondern Möblierung.

    Dieselbe Lücke wie bei der Brennweite: im Modul längst einstellbar, auf dem Weg, den
    ein Auftrag nimmt, nicht.
    """
    modul = _abholen()
    gesehen: dict = {}

    monkeypatch.setattr(modul.abholer, "durchgang", lambda store, **kw: {
        "gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
        "gestanden": 0, "waisen": [], "ergebnisse": []})
    monkeypatch.setattr(modul.abholer, "verarbeiter",
                        lambda **kw: gesehen.update(kw) or (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv",
                        ["abholen.py", "--store", str(tmp_path), "--gelaende-z", "412.5"])

    assert modul.main() == 0
    assert gesehen["gelaende_z"] == 412.5


def test_ohne_angabe_bleibt_der_gelaendestand_offen(monkeypatch, tmp_path):
    """`None` heisst „nicht gesagt", nicht „null" — und null wäre bei einem Bauwerk auf
    412 m über Meer die schlimmste aller Antworten."""
    modul = _abholen()
    gesehen: dict = {}

    monkeypatch.setattr(modul.abholer, "durchgang", lambda store, **kw: {
        "gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
        "gestanden": 0, "waisen": [], "ergebnisse": []})
    monkeypatch.setattr(modul.abholer, "verarbeiter",
                        lambda **kw: gesehen.update(kw) or (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path)])

    assert modul.main() == 0
    assert gesehen["gelaende_z"] is None


# ======================================================================================
# Die zweite Ablage — der Weg, den ein Knoten in KosmoOrbit nimmt
# ======================================================================================
#
# Bis zum 26.08.2026 las diesen Weg niemand: `werkzeuge.enqueue_render` legte den Auftrag
# ab, er ging mit Freigabe auf `queued`, und dort blieb er. Der Anschluss liegt in
# `abholer` und `eigene_quelle` — aber gefahren wird er von HIER, und diese Datei ist
# die einzige Stelle, an der das geprüft werden kann.
#
# Die Mutationsprobe hat es belegt: Wird die Zeile, die die zweite Ablage anhängt, wieder
# entfernt, blieb ohne diese Tests **alles grün**.

def _alle_durchgaenge(monkeypatch, tmp_path, argv):
    """Wie ``_lauf``, sammelt aber **jeden** Durchgang statt nur den letzten.

    Mit zwei Ablagen ist «der letzte Aufruf» keine Auskunft mehr über den ersten.
    """
    modul = _abholen()
    laeufe: list = []

    def falscher_durchgang(store, **kw):
        laeufe.append({"store": store, **kw})
        return {"gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
                "gestanden": 0, "waisen": [], "ergebnisse": []}

    monkeypatch.setattr(modul.abholer, "durchgang", falscher_durchgang)
    monkeypatch.setattr(modul.abholer, "verarbeiter", lambda **kw: (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path), *argv])
    assert modul.main() == 0
    return modul, laeufe


def test_ohne_schalter_bleibt_es_bei_der_bruecke(monkeypatch, tmp_path):
    """Der ältere Weg ist die Vorgabe — jeder bestehende Betrieb muss unverändert laufen."""
    modul, laeufe = _alle_durchgaenge(monkeypatch, tmp_path, [])
    assert len(laeufe) == 1
    assert laeufe[0]["quelle"] is modul.bruecke


def test_mit_eigenem_store_werden_beide_ablagen_abgegangen(monkeypatch, tmp_path):
    """Und jede mit **ihrer** Quelle — sonst läse der Abholer das falsche Format."""
    eigen = tmp_path / "aiimaging-jobs"
    eigen.mkdir()
    modul, laeufe = _alle_durchgaenge(monkeypatch, tmp_path,
                                      ["--eigener-store", str(eigen)])
    assert len(laeufe) == 2, (
        "Die zweite Ablage wird nicht abgegangen. Ein über KosmoOrbit bestellter Render "
        "bliebe wieder liegen — genau der Zustand vom 26.08.2026."
    )
    zuordnung = {str(lauf["store"]): lauf["quelle"] for lauf in laeufe}
    assert zuordnung[str(tmp_path)] is modul.bruecke
    assert zuordnung[str(eigen)] is modul.eigene_quelle


def test_eine_fehlende_zweite_ablage_haelt_die_erste_nicht_auf(monkeypatch, tmp_path):
    """Wer den MCP-Einlass nie benutzt hat, hat den Ordner nie angelegt.

    Ein Abbruch daran hiesse: Ein Schalter, der beide Wege bedienen soll, legt den
    bewährten lahm.
    """
    modul, laeufe = _alle_durchgaenge(monkeypatch, tmp_path,
                                      ["--eigener-store", str(tmp_path / "gibt-es-nicht")])
    assert len(laeufe) == 1
    assert laeufe[0]["quelle"] is modul.bruecke


def test_die_probe_zaehlt_beide_ablagen_getrennt(monkeypatch, tmp_path, capsys):
    """Ein Auftrag, der auf dem einen Weg liegt, ist sonst von einem auf dem anderen
    nicht zu unterscheiden."""
    eigen = tmp_path / "aiimaging-jobs"
    eigen.mkdir()
    modul = _abholen()
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path),
                                      "--eigener-store", str(eigen), "--probe"])
    assert modul.main() == 0
    ausgabe = capsys.readouterr().out
    assert "[Bruecke]" in ausgabe
    assert "MCP-Einlass" in ausgabe


# ======================================================================================
# Der Multipass-Zwischenspeicher
# ======================================================================================

def test_ohne_schalter_bleibt_der_speicher_aus(monkeypatch, tmp_path):
    """Ein Gedächtnis, das niemand bestellt hat, ist die unangenehmste Art Überraschung."""
    modul = _abholen()
    gesehen: dict = {}
    monkeypatch.setattr(modul.abholer, "verarbeiter",
                        lambda **kw: (gesehen.update(kw), lambda a: {})[1])
    monkeypatch.setattr(modul.abholer, "durchgang", lambda store, **kw: {
        "gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
        "gestanden": 0, "waisen": [], "ergebnisse": []})
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path)])
    assert modul.main() == 0
    assert gesehen["zwischenspeicher"] is None


def test_mit_schalter_kommt_ein_speicher_beim_verarbeiter_an(monkeypatch, tmp_path):
    """Der Schalter darf nicht bloss in der Hilfe stehen."""
    from aiimaging import graph

    modul = _abholen()
    gesehen: dict = {}
    monkeypatch.setattr(modul.abholer, "verarbeiter",
                        lambda **kw: (gesehen.update(kw), lambda a: {})[1])
    monkeypatch.setattr(modul.abholer, "durchgang", lambda store, **kw: {
        "gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
        "gestanden": 0, "waisen": [], "ergebnisse": []})
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path),
                                      "--zwischenspeicher", str(tmp_path / "cache")])
    assert modul.main() == 0
    assert isinstance(gesehen["zwischenspeicher"], graph.ArtefaktCache)


def test_ein_zwischenspeicher_im_repo_wird_abgewiesen(monkeypatch, tmp_path, capsys):
    """**Regel 3.** Die Einträge tragen absolute Pfade — im Repo landeten sie im Commit.

    Der Wächter `tests/test_regel3_kennungen.py` fände sie, aber erst danach. Hier fällt
    es vorher auf, und zwar **auch bei `--probe`**: Wer nur nachsehen will, soll den
    falschen Ort trotzdem genannt bekommen.
    """
    modul = _abholen()
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path),
                                      "--zwischenspeicher", str(REPO / "build"),
                                      "--probe"])
    assert modul.main() == 2
    assert "nicht im Repo" in capsys.readouterr().out
