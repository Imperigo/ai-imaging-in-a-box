"""A0833 «Gesicherter Graph bleibt heil» (Audit 24.11.2026, Befund V2, Heim-PC).

Die Audit-Probe ``visbox-speicherprobe.py`` sicherte in eine Mappe mit Graph «original» einen
zweiten Graph «starter» ohne ``stand`` und las danach «graph on disk starter»: Ohne Stand wurde
ersetzt. Eine Seite, die den gesicherten Graph nicht lesen konnte, legt einen Anfang und sichert
ihn; der gesicherte Graph war dann weg. Seither gilt: ohne Stand nur in eine Mappe ohne Graph,
und eine unlesbare Datei wird erst ersetzt, wenn eine Kopie daneben liegt.
"""
from __future__ import annotations

import hashlib
import json
import threading

import pytest

from aiimaging import knotenweg

from test_modell_laden import _Server, server, start  # noqa: F401 (Probe-Wirt und Fixtures)

ORIGINAL = {"id": "original", "kind": "visgraph", "nodes": [], "edges": []}
STARTER = {**ORIGINAL, "id": "starter"}


def _sha(pfad) -> str:
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def _kopien(ordner) -> list:
    return sorted(p for p in ordner.iterdir()
                  if p.name != knotenweg.GRAPH_DATEI and p.name.startswith("knotengraph"))


# ------------------------------------------------------------------ Satz 1: graph on disk original

def test_graph_on_disk_bleibt_original(tmp_path):
    """Die Zeile «graph on disk» der Audit-Probe, umgestellt: 409, die Datei bytegleich."""
    knotenweg.schreibe_graph(tmp_path, [ORIGINAL])
    datei = tmp_path / knotenweg.GRAPH_DATEI
    vorher = _sha(datei)
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.schreibe_graph(tmp_path, [STARTER], stand=None)
    assert fehler.value.code == 409
    assert _sha(datei) == vorher
    assert knotenweg.lies_graph(tmp_path)["graphen"][0]["id"] == "original"
    print("graph on disk", knotenweg.lies_graph(tmp_path)["graphen"][0]["id"])


def test_der_satz_spricht_mit_dem_menschen(tmp_path):
    knotenweg.schreibe_graph(tmp_path, [ORIGINAL])
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.schreibe_graph(tmp_path, [STARTER])
    satz = str(fehler.value)
    assert "neu laden" in satz and "nicht überschrieben" in satz
    assert " du " in f" {satz.lower()} "
    assert str(tmp_path) not in satz and tmp_path.name not in satz, "kein Plattenpfad (Regel 3)"


def test_am_server_ohne_stand_409_und_die_datei_bleibt(server, start):  # noqa: F811
    s = _Server(server, start)
    kopf = {"Content-Type": "application/json"}
    code, _ = s._frage("POST", server.WEG_KNOTEN_GRAPH,
                       json.dumps({"graphen": [ORIGINAL]}).encode(), kopf)
    assert code == 200
    vorher = _sha(start / knotenweg.GRAPH_DATEI)
    code, antwort = s._frage("POST", server.WEG_KNOTEN_GRAPH,
                             json.dumps({"graphen": [STARTER]}).encode(), kopf)
    assert code == 409 and "neu laden" in json.dumps(antwort, ensure_ascii=False)
    assert _sha(start / knotenweg.GRAPH_DATEI) == vorher
    assert s.get(server.WEG_KNOTEN_GRAPH)[1]["graphen"] == [ORIGINAL]


# ------------------------------------------------------------------ Satz 2: eine unlesbare Datei

UNLESBAR = {
    "abgebrochenes_json": b'{"format": "visbox.knotengraph/v1", "graphen": [{"id": "orig',
    "unbekanntes_format": json.dumps({"format": "visbox.knotengraph/v9",
                                      "graphen": [ORIGINAL]}).encode(),
}


@pytest.mark.parametrize("art", sorted(UNLESBAR))
def test_unlesbar_ohne_stand_wird_nicht_ersetzt(tmp_path, art):
    datei = tmp_path / knotenweg.GRAPH_DATEI
    datei.write_bytes(UNLESBAR[art])
    assert knotenweg.lies_graph(tmp_path)["satz"], "die Probe braucht eine unlesbare Datei"
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.schreibe_graph(tmp_path, [STARTER])
    assert fehler.value.code == 409
    assert datei.read_bytes() == UNLESBAR[art]
    assert _kopien(tmp_path) == []


@pytest.mark.parametrize("art", sorted(UNLESBAR))
def test_unlesbar_mit_stand_wird_ersetzt_und_die_kopie_liegt_daneben(tmp_path, art):
    datei = tmp_path / knotenweg.GRAPH_DATEI
    datei.write_bytes(UNLESBAR[art])
    sicht = knotenweg.lies_graph_mit_stand(tmp_path)
    assert sicht["graphen"] == [] and sicht["satz"]
    erg = knotenweg.schreibe_graph(tmp_path, [STARTER], stand=sicht["stand"])
    assert erg["gesichert"] == 1
    assert knotenweg.lies_graph(tmp_path)["graphen"] == [STARTER]
    kopien = _kopien(tmp_path)
    assert len(kopien) == 1 and kopien[0].read_bytes() == UNLESBAR[art]
    assert any(z.isdigit() for z in kopien[0].name), "der Name trägt einen Zeitstempel"


def test_unlesbar_ohne_kopie_kein_ersetzen(tmp_path, monkeypatch):
    """Geht die Kopie nicht, bleibt die alte Datei: erst die Kopie, dann das Ersetzen."""
    datei = tmp_path / knotenweg.GRAPH_DATEI
    datei.write_bytes(UNLESBAR["abgebrochenes_json"])
    stand = knotenweg.lies_graph_mit_stand(tmp_path)["stand"]

    def kaputt(*_a, **_k):
        raise OSError("Platte voll")

    monkeypatch.setattr(knotenweg.shutil, "copy2", kaputt)
    with pytest.raises((knotenweg.KnotenwegError, OSError)):
        knotenweg.schreibe_graph(tmp_path, [STARTER], stand=stand)
    assert datei.read_bytes() == UNLESBAR["abgebrochenes_json"]


def test_zwei_kopien_ueberschreiben_sich_nie(tmp_path):
    """Zweimal unlesbar in derselben Sekunde: zwei Kopien, keine verloren (E7)."""
    datei = tmp_path / knotenweg.GRAPH_DATEI
    for inhalt in (b"{eins", b"{zwei"):
        datei.write_bytes(inhalt)
        knotenweg.schreibe_graph(tmp_path, [STARTER],
                                 stand=knotenweg.lies_graph_mit_stand(tmp_path)["stand"])
    assert sorted(p.read_bytes() for p in _kopien(tmp_path)) == [b"{eins", b"{zwei"]


def test_unlesbar_mit_fremdem_stand_409(tmp_path):
    datei = tmp_path / knotenweg.GRAPH_DATEI
    datei.write_bytes(b"{kaputt")
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.schreibe_graph(tmp_path, [STARTER], stand="0123456789abcdef")
    assert fehler.value.code == 409
    assert datei.read_bytes() == b"{kaputt" and _kopien(tmp_path) == []


# ------------------------------------------------------------------ Satz 3: was bleibt

def test_eine_leere_mappe_nimmt_den_ersten_ohne_stand(tmp_path):
    assert knotenweg.schreibe_graph(tmp_path, [ORIGINAL])["gesichert"] == 1
    assert knotenweg.lies_graph(tmp_path)["graphen"] == [ORIGINAL]


def test_gleicher_stand_ersetzt_fremder_stand_409(tmp_path):
    stand = knotenweg.schreibe_graph(tmp_path, [ORIGINAL])["stand"]
    neu = knotenweg.schreibe_graph(tmp_path, [STARTER], stand=stand)["stand"]
    assert knotenweg.lies_graph(tmp_path)["graphen"] == [STARTER]
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.schreibe_graph(tmp_path, [ORIGINAL], stand=stand)
    assert fehler.value.code == 409 and "anderes Gerät" in str(fehler.value)
    assert knotenweg.graph_stand(tmp_path) == neu
    assert _kopien(tmp_path) == [], "ein lesbarer Graph braucht keine Kopie"


@pytest.mark.parametrize("stand", [None, knotenweg.GRAPH_STAND_LEER])
def test_zwei_erste_sicherungen_zugleich_genau_eine(tmp_path, monkeypatch, stand):
    """Prüfen und Ersetzen unter einer Sperre: zwei erste Sicherungen, genau eine gewinnt."""
    echt = knotenweg.graph_stand
    beide_geprueft = threading.Barrier(2, timeout=0.5)

    def langsam(ordner):
        wert = echt(ordner)
        try:
            beide_geprueft.wait()           # ohne Sperre prüfen beide, bevor einer schreibt
        except threading.BrokenBarrierError:
            pass
        return wert

    monkeypatch.setattr(knotenweg, "graph_stand", langsam)
    ergebnisse: list = []

    def sichere(graph):
        try:
            knotenweg.schreibe_graph(tmp_path, [graph], stand=stand)
            ergebnisse.append(("ok", graph["id"]))
        except knotenweg.KnotenwegError as fehler:
            ergebnisse.append((fehler.code, graph["id"]))

    faeden = [threading.Thread(target=sichere, args=(g,)) for g in (ORIGINAL, STARTER)]
    for f in faeden:
        f.start()
    for f in faeden:
        f.join(5)
    assert sorted(e[0] for e in ergebnisse if e[0] != "ok") == [409]
    sieger = [e[1] for e in ergebnisse if e[0] == "ok"]
    assert len(sieger) == 1
    assert knotenweg.lies_graph(tmp_path)["graphen"][0]["id"] == sieger[0]
