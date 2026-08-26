"""Einstellbar ist ein Versprechen, das man an der NAHT prüft — jetzt auch an dieser.

**Der Anlass ist derselbe wie an der Nachbarnaht** (`tests/test_naht_durchreichung.py`):
Am 23.08.2026 hat dieses Projekt zweimal an einem Tag denselben Fehler gemacht, beide Male
an einer Naht. Die Brennweite war im Kern längst einstellbar und kam an der Aussenkante
trotzdem nicht durch — zwei fest verdrahtete `28.0` standen im Weg. Der Geländestand
ebenso. Beide Male hiess es «einstellbar», und beide Male stimmte das im Modul und nicht
im Betrieb.

Für `kosmo_szene.lies_szene` gibt es die Tabelle seit dem 23.08. **Für `verarbeiter` gab
es sie nicht** — und das ist die Naht, an der die GPU-Zeit anfällt. Gezählt am 26.08.2026:
`glb_zu_multipass` hat 18 echte Einstellungen, durchgereicht werden 12; `RenderAuftrag`
hat 12 Felder, gesetzt werden 7.

*Nirgends stand, welche der zehn Absicht sind und welche Lücken.* Genau diese dritte
Möglichkeit — «steht nirgends» — ist die bequemste, und gegen sie ist die Tabelle gebaut.

**Ein Schritt mehr als an der Nachbarnaht.** Dort ist die gelesene Menge ein
Rückgabewörterbuch; hier ist sie die **Signatur einer fremden Funktion**. Der Test hält
die Tabelle darum gegen `inspect.signature` — **samt der Vorgabewerte**. Wer `beauty` auf
`False` oder `timeout` auf 300 setzt, bekommt es rot. Eine Tabelle, die von Hand gepflegt
werden muss, veraltet; an diesem einen Tag ist das schon zweimal nachgewiesen worden.
"""
from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from aiimaging import abholer, render, seams
from conftest import MINI_PNG


def _multipass_einstellungen() -> set[str]:
    return {name for name in inspect.signature(seams.glb_zu_multipass).parameters
            if name not in abholer.MULTIPASS_KEINE_EINSTELLUNG}


# ======================================================================================
# 1 · Die Tabelle ist vollständig — der eigentliche Wächter
# ======================================================================================

def test_jede_multipass_einstellung_steht_in_genau_einer_der_beiden_listen():
    """**Der Test, um dessentwillen es die Tabelle gibt.** Wer `glb_zu_multipass` um einen
    Parameter erweitert, muss hier Farbe bekennen: Kommt er an, oder bleibt er stehen?"""
    gelesen = _multipass_einstellungen()
    erklaert = set(abholer.MULTIPASS_DURCHGEREICHT) | set(abholer.MULTIPASS_STEHENGEBLIEBEN)

    assert gelesen - erklaert == set(), (
        "Diese Einstellungen gibt es, und niemand sagt, ob sie ankommen")
    assert erklaert - gelesen == set(), (
        "Diese stehen in der Tabelle und gibt es nicht mehr — eine Tabelle, die "
        "Parameter behauptet, die es nicht gibt, macht die Luecke unauffindbar")


def test_jedes_renderfeld_steht_in_genau_einer_der_beiden_listen():
    gelesen = {f.name for f in dataclasses.fields(render.RenderAuftrag)}
    erklaert = set(abholer.RENDER_DURCHGEREICHT) | set(abholer.RENDER_STEHENGEBLIEBEN)

    assert gelesen - erklaert == set()
    assert erklaert - gelesen == set()


@pytest.mark.parametrize("tabellen", [
    (abholer.MULTIPASS_DURCHGEREICHT, abholer.MULTIPASS_STEHENGEBLIEBEN),
    (abholer.RENDER_DURCHGEREICHT, abholer.RENDER_STEHENGEBLIEBEN),
])
def test_kein_parameter_steht_in_beiden_listen(tabellen):
    """«Kommt an» und «bleibt stehen» zugleich ist keine Auskunft, sondern zwei."""
    a, b = tabellen
    assert set(a) & set(b) == set()


def test_die_zaehlung_stimmt_mit_der_gemeldeten():
    """Die Zahlen stehen im Protokoll, im PLAN und im Commit. Stimmen sie nicht mit dem
    Code überein, ist eine davon eine Erinnerung und keine Messung.

    *Sechs, nicht fünf* — `shift_y` fehlte in der ersten Zählung und ist bei der
    Gegenprüfung aufgefallen."""
    assert len(_multipass_einstellungen()) == 18
    assert len(abholer.MULTIPASS_DURCHGEREICHT) == 12
    assert len(abholer.MULTIPASS_STEHENGEBLIEBEN) == 6
    assert len(abholer.RENDER_DURCHGEREICHT) == 7
    assert len(abholer.RENDER_STEHENGEBLIEBEN) == 5


# ======================================================================================
# 2 · Ein Eintrag, der nichts sagt, ist keiner
# ======================================================================================

@pytest.mark.parametrize("name", sorted(abholer.MULTIPASS_STEHENGEBLIEBEN))
def test_jeder_stehengebliebene_multipass_eintrag_sagt_auch_was_fehlt(name):
    """Ein «wird nicht gesetzt» ohne den nächsten Schritt ist eine Sackgasse. Mit ihm ist
    es eine Aufgabe — dieselbe Schranke wie an der Nachbarnaht."""
    eintrag = abholer.MULTIPASS_STEHENGEBLIEBEN[name]

    assert set(eintrag) == {"vorgabe", "absicht", "grund", "noetig"}
    assert isinstance(eintrag["absicht"], bool)
    assert len(eintrag["grund"]) > 40, "ein Halbsatz erklaert nichts"
    assert len(eintrag["noetig"]) > 8, "was fehlt, gehoert benannt"


@pytest.mark.parametrize("name", sorted(abholer.RENDER_STEHENGEBLIEBEN))
def test_jeder_stehengebliebene_renderfeld_eintrag_sagt_auch_was_fehlt(name):
    eintrag = abholer.RENDER_STEHENGEBLIEBEN[name]

    assert set(eintrag) == {"vorgabe", "absicht", "grund", "noetig"}
    assert len(eintrag["grund"]) > 40
    assert len(eintrag["noetig"]) > 8


def test_es_sind_absichten_und_luecken_und_beides_kommt_vor():
    """**Die Gegenprobe zur Tabelle selbst.** Wäre alles «Absicht», hätte jemand die
    Frage weggeschrieben statt sie zu beantworten; wäre alles «Lücke», sagte die Spalte
    nichts."""
    alle = list(abholer.MULTIPASS_STEHENGEBLIEBEN.values()) + \
        list(abholer.RENDER_STEHENGEBLIEBEN.values())
    absichten = [e for e in alle if e["absicht"]]
    luecken = [e for e in alle if not e["absicht"]]

    assert len(absichten) == 7
    assert len(luecken) == 4, "timeout, kamera_huellbox, schritte, denoise"
    assert {n for n, e in
            {**abholer.MULTIPASS_STEHENGEBLIEBEN,
             **abholer.RENDER_STEHENGEBLIEBEN}.items() if not e["absicht"]} == {
        "timeout", "kamera_huellbox", "schritte", "denoise"}


# ======================================================================================
# 3 · Der Vorgabewert wird gegen den Code geprüft, nicht behauptet
# ======================================================================================

@pytest.mark.parametrize("name", sorted(abholer.MULTIPASS_STEHENGEBLIEBEN))
def test_die_multipass_vorgabe_stimmt_mit_der_signatur(name):
    """**Der Schritt, den die Nachbarnaht nicht haben konnte.** Die Behauptung «der
    Vorgabewert ist der richtige» wird hier gegen die wirkliche Signatur gehalten. Ändert
    jemand `beauty` auf `False` oder `timeout` auf 300, wird dieser Test rot — und genau
    diese stille Änderung soll die Tabelle abfangen."""
    echt = inspect.signature(seams.glb_zu_multipass).parameters[name].default

    assert abholer.MULTIPASS_STEHENGEBLIEBEN[name]["vorgabe"] == echt


@pytest.mark.parametrize("name", sorted(abholer.RENDER_STEHENGEBLIEBEN))
def test_die_renderfeld_vorgabe_stimmt_mit_der_dataclass(name):
    felder = {f.name: f for f in dataclasses.fields(render.RenderAuftrag)}

    assert abholer.RENDER_STEHENGEBLIEBEN[name]["vorgabe"] == felder[name].default


# ======================================================================================
# 4 · Und es stimmt auch im Betrieb — nicht nur in der Tabelle
# ======================================================================================
#
# Ohne diesen Abschnitt prueft die Tabelle nur sich selbst. Das ist genau der Fehler,
# gegen den `test_naht_durchreichung.py` seinen dritten Abschnitt hat.

def _lauf(tmp_path):
    """Ein Durchgang mit Attrappen, der mitschreibt, WAS wirklich uebergeben wurde."""
    protokoll = {"multipass": [], "render": []}

    def multipass(glb, aus, **kw):
        protokoll["multipass"].append(kw)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(MINI_PNG)
        beauty = Path(aus) / "beauty.png"
        beauty.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "beauty_png": str(beauty),
                "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        protokoll["render"].append(auftrag)
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                "verzeichnis": tmp_path,
                "szene": {"kameras": [{"kuerzel": "s", "richtung": "s"}],
                          "aufloesung": 64, "hoehe": 64, "samples": 1,
                          "prompt": "a house"}})
    return protokoll


def test_der_multipass_bekommt_genau_die_durchgereichten(tmp_path):
    """**Die Probe, die zählt.** Eine Tabelle, die nur sich selbst prüft, ist eine
    Behauptung mit Testabdeckung."""
    protokoll = _lauf(tmp_path)

    assert set(protokoll["multipass"][0]) == set(abholer.MULTIPASS_DURCHGEREICHT)


def test_der_renderauftrag_traegt_die_stehengebliebenen_auf_ihrer_vorgabe(tmp_path):
    """Und die Gegenrichtung: Was nicht gesetzt wird, steht danach auf genau dem Wert,
    den die Tabelle als `vorgabe` behauptet."""
    protokoll = _lauf(tmp_path)
    auftrag = protokoll["render"][0]

    for name, eintrag in abholer.RENDER_STEHENGEBLIEBEN.items():
        assert getattr(auftrag, name) == eintrag["vorgabe"], name


def test_die_beiden_bekannten_luecken_stehen_mit_ihrem_auftrag_da():
    """`kamera_huellbox` wartet auf `auf-41`, `schritte` und `denoise` auf `auf-44`. Ein
    offener Punkt ohne Adresse ist einer, den niemand schliesst."""
    assert "auf-41" in abholer.MULTIPASS_STEHENGEBLIEBEN["kamera_huellbox"]["noetig"]
    assert "auf-44" in abholer.RENDER_STEHENGEBLIEBEN["schritte"]["noetig"]
    assert "auf-44" in abholer.RENDER_STEHENGEBLIEBEN["denoise"]["noetig"]
    assert "auf-38" in abholer.RENDER_STEHENGEBLIEBEN["negativ_prompt"]["noetig"]
