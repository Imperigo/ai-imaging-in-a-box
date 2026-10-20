"""Fehler am Heim-PC und an der Mac-App vom 20.10.2026 — je Befund eine Probe.

* **A** — «Der Heim-PC ist nicht erreicht: Er hat nicht rechtzeitig geantwortet.» bei jeder
  Variante: Der Server las und zerlegte das hochgeladene Modell unter der Reihe; eine
  Variante (``vis.grundlage``) braucht gar keins.
* **B1–B6** — die Befunde der HomeStation aus ``auf-20261020-290``.

Regel 3: alles synthetisch, keine Projektdaten.
"""
from __future__ import annotations

import importlib.util
import io
import json
import threading
import time
from pathlib import Path

import pytest

from aiimaging import abholer, bildschreiben, bruecke, geometrie_qa, glbbox, knotenweg

from conftest import MINI_PNG
from test_abholer import _auftrag, _erfolg

WURZEL = Path(__file__).resolve().parents[1]


def _make_test_glb():
    spec = importlib.util.spec_from_file_location("make_test_glb",
                                                  WURZEL / "tools" / "make_test_glb.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ======================================================================================
# A · Das Formular gestreamt, und eine Variante ohne Modell
# ======================================================================================

def _formular(felder: dict, grenze: str = "----visbox-grenze-0123") -> tuple[bytes, str]:
    teile = []
    for name, (dateiname, inhalt) in felder.items():
        kopf = f'Content-Disposition: form-data; name="{name}"'
        if dateiname:
            kopf += f'; filename="{dateiname}"'
        teile.append(f"--{grenze}\r\n{kopf}\r\n\r\n".encode() + inhalt + b"\r\n")
    rumpf = b"".join(teile) + f"--{grenze}--\r\n".encode()
    return rumpf, f'multipart/form-data; boundary="{grenze}"'


class _Tropfen(io.BytesIO):
    """Ein Strom, der höchstens wenige Bytes je ``read`` hergibt — wie eine langsame Leitung."""

    def read(self, n=-1):
        return super().read(min(n if n >= 0 else 7, 7))


def test_der_teiler_schreibt_die_datei_unmittelbar_auf_die_platte(tmp_path):
    # Ein Inhalt, der der Grenzmarke zum Verwechseln ähnlich sieht, über viele Stücke.
    modell = (b"glTF" + b"\r\n----visbox-grenze-012" + bytes(range(256)) * 50)
    rumpf, typ = _formular({"scene": (None, b'{"a": 1}'), "model": ("m.glb", modell)})
    felder = knotenweg.teile_formular(_Tropfen(rumpf), len(rumpf), typ, ordner=tmp_path,
                                      datei_felder=("model",))
    assert felder["scene"] == (None, b'{"a": 1}')
    dateiname, pfad = felder["model"]
    assert dateiname == "m.glb" and isinstance(pfad, Path)
    assert pfad.read_bytes() == modell
    assert pfad.parent == tmp_path and pfad.name.startswith(".")      # nie ausgeliefert
    knotenweg.raeume_formular(felder)
    assert not pfad.exists()


def test_der_teiler_haelt_die_grenze_und_raeumt_auf(tmp_path):
    rumpf, typ = _formular({"model": ("m.glb", b"x" * 5000)})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.teile_formular(io.BytesIO(rumpf), len(rumpf), typ, ordner=tmp_path,
                                 datei_felder=("model",), hoechstens_datei=1000)
    assert fehler.value.code == 413
    assert list(tmp_path.iterdir()) == []


def test_ein_abgeschnittenes_formular_wird_mit_satz_abgewiesen(tmp_path):
    rumpf, typ = _formular({"model": ("m.glb", b"x" * 500)})
    with pytest.raises(knotenweg.KnotenwegError, match="unvollständig"):
        knotenweg.teile_formular(io.BytesIO(rumpf[:300]), 300, typ, ordner=tmp_path,
                                 datei_felder=("model",))
    assert list(tmp_path.iterdir()) == []


def test_lies_formular_spricht_weiter_dieselbe_form():
    import sys
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    import server
    rumpf, typ = _formular({"scene": (None, b"{}"), "datei": ("haus.ifc", b"ISO-10303")})
    assert server.lies_formular(typ, rumpf) == {"scene": (None, b"{}"),
                                                "datei": ("haus.ifc", b"ISO-10303")}
    with pytest.raises(knotenweg.KnotenwegError):
        server.lies_formular("application/json", b"{}")


def _grundlage_auftrag(ablage: Path, kennung: str) -> Path:
    """Ein früherer Lauf, der die Grundlage ``kennung`` gelegt hat — mit Modell und Ergebnis."""
    erster = knotenweg.lege_an(ablage, {"geometry": {"format": "glb"}, "vis": {"skip": True}},
                               b"glTF-erstes-modell", "m.glb", kennung="vis-1792500000-aaaaaa")
    (ablage / erster["job_id"] / bruecke.DATEI_ERGEBNIS).write_text(
        json.dumps({"grundlage": {"id": kennung, "wiederverwendet": False}}), encoding="utf-8")
    return ablage / erster["job_id"]


def test_eine_variante_ohne_modell_nimmt_das_modell_der_grundlage(tmp_path):
    kennung = "gl-0123456789abcdef"
    erster = _grundlage_auftrag(tmp_path, kennung)
    zettel = knotenweg.lege_an(tmp_path, {"vis": {"grundlage": kennung, "guete": "vorschau"}},
                               None, kennung="vis-1792500100-bbbbbb")
    neu = tmp_path / zettel["job_id"]
    assert (neu / bruecke.DATEI_MODELL).read_bytes() == b"glTF-erstes-modell"
    # Die Datei des ersten Laufs bleibt, wo sie ist.
    assert (erster / bruecke.DATEI_MODELL).read_bytes() == b"glTF-erstes-modell"
    szene = json.loads((neu / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
    assert szene["geometry"] == {"path": str(neu / bruecke.DATEI_MODELL), "format": "glb"}
    assert zettel["status"] == bruecke.STATUS_AWAITING


def test_fehlt_die_grundlage_am_rechner_kommt_ein_satz_statt_warten(tmp_path):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, {"vis": {"grundlage": "gl-ffffffffffffffff"}}, None)
    assert fehler.value.code == 409
    assert "Grundlage rendern" in str(fehler.value)
    # Ohne Grundlage braucht es weiter ein Modell.
    with pytest.raises(knotenweg.KnotenwegError, match="«model»"):
        knotenweg.lege_an(tmp_path, {"vis": {}}, None)
    assert [p for p in tmp_path.iterdir() if p.is_dir()] == []


@pytest.fixture
def flaeche(tmp_path, monkeypatch):
    """Ein echter Server auf einem freien Anschluss, Ablage im tmp-Ordner."""
    import sys
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    import server
    monkeypatch.setattr(server.Flaeche, "ablage", tmp_path / "ablage")
    monkeypatch.setattr(server.Flaeche, "kennwort", None)
    monkeypatch.setattr(server.Flaeche, "ordner", None)
    monkeypatch.setattr(server.Flaeche, "zuletzt_geoeffnet", None)
    (tmp_path / "ablage").mkdir()
    dienst = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Flaeche)
    faden = threading.Thread(target=dienst.serve_forever, daemon=True)
    faden.start()
    yield server, dienst.server_address[1], tmp_path / "ablage"
    dienst.shutdown()
    dienst.server_close()


def _post(anschluss, weg, rumpf, typ):
    import http.client
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("POST", weg, body=rumpf, headers={"Content-Type": typ})
    antwort = leitung.getresponse()
    return antwort.status, json.loads(antwort.read() or b"{}")


def test_der_server_nimmt_eine_variante_ohne_modell_an(flaeche):
    server, anschluss, ablage = flaeche
    kennung = "gl-00112233445566aa"
    _grundlage_auftrag(ablage, kennung)
    rumpf, typ = _formular({"scene": (None, json.dumps(
        {"vis": {"grundlage": kennung}}).encode())})
    code, antwort = _post(anschluss, "/bruecke/jobs", rumpf, typ)
    assert code == 200, antwort
    assert (ablage / antwort["job_id"] / bruecke.DATEI_MODELL).is_file()
    # Und ohne Grundlage am Rechner: 409 mit Satz.
    rumpf, typ = _formular({"scene": (None, b'{"vis": {"grundlage": "gl-9999999999999999"}}')})
    code, antwort = _post(anschluss, "/bruecke/jobs", rumpf, typ)
    assert code == 409 and "Grundlage" in antwort["fehler"]


def test_der_server_liest_den_rumpf_ausserhalb_der_reihe(flaeche):
    """Während ein grosser Auftrag noch über die Leitung kommt, antwortet der Server auf
    andere Wege — bis zum 20.10.2026 hielt das Lesen unter der Reihe alles an."""
    import socket
    server, anschluss, ablage = flaeche
    modell = b"glTF" + b"\0" * 200_000
    rumpf, typ = _formular({"scene": (None, b'{"geometry": {"format": "glb"}}'),
                            "model": ("m.glb", modell)})
    leitung = socket.create_connection(("127.0.0.1", anschluss), timeout=10)
    leitung.sendall((f"POST /bruecke/jobs HTTP/1.1\r\nHost: x\r\nContent-Type: {typ}\r\n"
                     f"Content-Length: {len(rumpf)}\r\n\r\n").encode() + rumpf[:1000])
    time.sleep(0.2)
    # Der Auftrag haengt mitten im Rumpf — ein anderer Weg muss trotzdem antworten.
    import http.client
    zweite = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=3)
    zweite.request("GET", "/bruecke/health")
    assert zweite.getresponse().status == 200
    leitung.sendall(rumpf[1000:])
    antwort = leitung.recv(65536).decode("utf-8", "replace")
    leitung.close()
    assert " 200 " in antwort.split("\r\n", 1)[0], antwort[:200]
    auftraege = [p for p in ablage.iterdir() if p.is_dir()]
    assert len(auftraege) == 1
    assert (auftraege[0] / bruecke.DATEI_MODELL).read_bytes() == modell
    assert not [p for p in ablage.iterdir() if p.name.startswith(".eingang-")]


@pytest.mark.parametrize("methode, weg, draussen", [
    ("POST", "/bruecke/jobs", True), ("POST", "/knoten/modell-laden", True),
    ("GET", "/knoten/modell.glb", True), ("GET", "/knoten/mappe", True),
    ("GET", "/bild", True), ("GET", "/knoten/skizze", True),
    ("GET", "/bruecke/jobs/vis-1-abcdef/artifacts/s.png", True),
    ("POST", "/bruecke/jobs/vis-1-abcdef/approve", False),
    ("POST", "/knoten/graph", False), ("GET", "/bruecke/jobs", False),
    ("GET", "/api/fortschritt", False), ("POST", "/api/rechne", False),
])
def test_welche_wege_ausserhalb_der_reihe_gehen(methode, weg, draussen):
    import sys
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    import server
    assert server.ausserhalb_der_reihe(methode, weg) is draussen


def test_die_mac_app_wartet_auf_die_zwei_wege_mit_modell_laenger():
    """Kern-Regel in Swift, hier gegen die Wege des Servers abgeglichen."""
    import sys
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    import server
    kern = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Knotenwege.swift").read_text(
        encoding="utf-8")
    assert (f'public static let wegeMitModell: Set<String> = ["{server.WEG_BRUECKE}/jobs", '
            f'"{server.WEG_KNOTEN_MODELL_LADEN}"]') in kern
    assert "public static let wartezeitLang: TimeInterval = 300" in kern
    quelle = (WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" /
              "Knotenquelle.swift").read_text(encoding="utf-8")
    assert "Knotenwege.wartezeit(methode:" in quelle and "langeSitzung" in quelle


# ======================================================================================
# B1 · Güte mit «nur Grundlage»: Endzustand statt alle 30 s neu gelesen
# ======================================================================================

def _szene(**vis):
    return {"schema": bruecke.kosmo_szene.SCHEMA_SZENE,
            "geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"resolution": [512, 512], "samples": 64},
            "style": {"prompt": "ein Haus", "mode": "none"}, "vis": vis}


def test_guete_mit_skip_endet_auf_error_mit_satz(tmp_path):
    ordner = _auftrag(tmp_path, szene=_szene(skip=True, guete="vorschau"))
    antwort = abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_FEHLER
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert "'vis.guete'" in zettel["error"] and "'vis.skip'" in zettel["error"]
    assert "'vis.guete'" in zettel[bruecke.FELD_MELDUNG]
    # Der nächste Durchgang sieht ihn nicht mehr — kein Neulesen alle 30 s.
    assert ordner not in [Path(p) for p in bruecke.offene_auftraege(tmp_path)]


def test_ein_gewoehnlicher_mangel_bleibt_liegengelassen(tmp_path):
    """Die Gegenprobe: Nur Widersprüche sind endgültig (Vertrag E79: liegen mit Grund)."""
    ordner = _auftrag(tmp_path, szene=_szene(guete="schnell"))
    antwort = abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_QUEUED


def test_die_widersprueche_stehen_als_endgueltig_in_der_szene():
    szene = bruecke.kosmo_szene.lies_szene(_szene(skip=True, guete="voll"))
    assert szene["maengel_endgueltig"] and set(szene["maengel_endgueltig"]) <= set(
        szene["maengel"])
    assert bruecke.kosmo_szene.lies_szene(_szene(guete="voll"))["maengel_endgueltig"] == ()


# ======================================================================================
# B2 · Der Abbruchsatz steht am Laufzettel, der Status bleibt «cancelled»
# ======================================================================================

def test_der_abbruchsatz_steht_in_message(tmp_path):
    ordner = _auftrag(tmp_path)

    def verarbeite(auftrag):
        knotenweg.abbrechen(tmp_path, ordner.name)            # der Nutzer bricht ab
        raise abholer.AuftragAbgebrochen(
            "Abgebrochen bei Kamera 2 von 2, vor dem Bildmodell.")

    antwort = abholer.hole_einen(ordner, verarbeite=verarbeite, fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_CANCELLED
    assert zettel[bruecke.FELD_MELDUNG] == (
        "Vom Nutzer abgebrochen. Abgebrochen bei Kamera 2 von 2, vor dem Bildmodell. "
        "Kein Ergebnis geschrieben.")
    assert antwort["grund_vermerkt"] is True


# ======================================================================================
# B3 · Der Zwilling am Quader trotz drei Randpunkten (genau der Fall aus auf-290)
# ======================================================================================

B, H = 1600, 992
HINTERGRUND = 1e10          # so schreibt Cycles «nichts getroffen» — endlich


def _quaderkarte():
    karte = [HINTERGRUND] * (B * H)
    for y in range(300, 700):
        zeile = y * B
        for x in range(500, 1100):
            karte[zeile + x] = 9.3 + (x - 500) * 0.005 + (y - 300) * 0.003
    return karte


def test_drei_randpunkte_verhindern_den_zwilling_nicht():
    a = _quaderkarte()
    b = list(a)
    # Wie gemessen: 1 587 197 von 1 587 200 gleich, 3 Punkte an der Unterkante kippen.
    for x in (600, 601, 900):
        a[699 * B + x] = 12.6          # in der einen Ansicht Geometrie …
        b[699 * B + x] = HINTERGRUND   # … in der anderen Hintergrund
    b[400 * B + 700] += 6e-6           # Rechenrauschen der EXR
    assert sum(1 for x, y in zip(a, b) if x != y) == 4
    assert abholer._gleiche_ansicht(a, b, breite=B, hoehe=H)
    # Und _finde_zwilling greift damit im Betrieb.
    vorbild = {"soll": a, "breite": B, "hoehe": H, "kamera": "sSE", "urteil": {}}
    assert abholer._finde_zwilling([vorbild], b, B, H) is vorbild


def test_eine_abweichung_mitten_im_bauwerk_bleibt_eine_andere_ansicht():
    """Die Gegenprobe: Ausserhalb der Kante zählt schon ein Punkt — und viele Punkte an der
    Kante sind eine andere Silhouette."""
    a = _quaderkarte()
    b = list(a)
    b[500 * B + 800] = HINTERGRUND                     # ein Loch mitten in der Fassade
    assert not abholer._gleiche_ansicht(a, b, breite=B, hoehe=H)
    c = list(a)
    for x in range(500, 1100):                         # eine ganze Kante: 600 Punkte
        c[699 * B + x] = HINTERGRUND
    assert not abholer._gleiche_ansicht(a, c, breite=B, hoehe=H)


def test_der_hintergrund_1e10_ist_hintergrund_und_keine_tiefe():
    """1e10 neben 9,3 m war bis zum 20.10.2026 «Tiefenunterschied», nicht Maske."""
    assert abholer._ist_hintergrund(1e10) and abholer._ist_hintergrund(float("inf"))
    assert not abholer._ist_hintergrund(9.3)
    assert abholer._gleiche_ansicht([1e10, 5.0], [float("inf"), 5.0])
    # Ohne Bildmasse bleibt die strenge Regel: jeder Punkt gleich.
    assert not abholer._gleiche_ansicht([1e10, 5.0], [5.0, 5.0])


# ======================================================================================
# B4 · Rahmung am Bauwerk, nicht an der Geländeplatte (Platte 40 × 30 m + Haus)
# ======================================================================================

PLATTE = [[-14.0, -18.0, -0.5], [26.0, 12.0, 15.0]]      # Szene: Platte 40 × 30 m
HAUS = [[0.0, -9.0, 0.0], [12.0, 0.0, 15.0]]            # Bauwerk 12 × 9 m


def _bericht(fuellgrad=0.70):
    return {"kamera": {"weg": "abgeleitet", "fuellgrad": fuellgrad},
            "deckungsgrad": 0.70, "bbox": PLATTE, "bbox_bauwerk": HAUS}


def test_gerahmt_nach_dem_bauwerk_wird_am_bauwerk_gemessen():
    lage = abholer._rahmung_vor_dem_render(_bericht(), gerahmte_box=HAUS)
    assert lage["abbruch"] is False
    assert lage["wirksame_bildbreite"] == pytest.approx(0.70, abs=0.01)
    assert lage["gerahmt_nach"] == "kamerabox"


def test_ohne_gerahmte_box_bleibt_die_rechnung_nach_der_szene():
    """So rechnete der Riegel bis zum 20.10.2026 auch für eine nach dem Bauwerk gerahmte
    Kamera — 0,70 × 12/40 = 21 %, der Befund der HomeStation."""
    lage = abholer._rahmung_vor_dem_render(_bericht())
    assert lage["abbruch"] is True
    assert lage["wirksame_bildbreite"] == pytest.approx(0.21, abs=0.01)


def test_der_verarbeiter_misst_an_der_box_die_er_gerahmt_hat(tmp_path):
    """Durch den Verarbeiter: echte glb (Platte 40 × 30 m + Haus aus make_test_glb), die
    Auto-Kamera rahmt nach dem Bauwerk — und der Riegel lässt sie rechnen."""
    glb = tmp_path / "platte_haus.glb"
    glb.write_bytes(_make_test_glb().baue_glb(_make_test_glb().VORGABE_SZENE))
    box = glbbox.rahmungsbox(glb)["box"]
    assert box is not None
    gesehen = {}
    zaehler = {"render": 0}
    bild = tmp_path / "b.png"

    def multipass(glb_pfad, aus, **kw):
        gesehen.setdefault("kamera_huellbox", kw.get("kamera_huellbox"))
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "abgeleitet", "fuellgrad": 0.70},
                "deckungsgrad": 0.70, "bbox": PLATTE, "bbox_bauwerk": HAUS}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False, _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))
    ergebnis = verarbeite({"modell": glb, "job_id": "vis-1-aaaaaa", "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "sSE", "richtung": "sSE"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house", "gelaende_erwartet": True}})
    assert gesehen["kamera_huellbox"] == box
    assert ergebnis["kameras"][0]["rahmung"]["abbruch"] is False
    assert zaehler["render"] == 1


# ======================================================================================
# B5 · Die Nullanker einmal je Soll-Karte
# ======================================================================================

def test_die_nullanker_werden_nach_inhalt_gemerkt(tmp_path):
    gerechnet = []

    def rechne():
        gerechnet.append(1)
        return {"grau": 0.1, "rauschen": 0.05}, {"grau": {"rho": -0.5, "kante": 0.1}}

    soll = [5.0, 6.0, float("inf"), 7.0]
    erst = abholer._nullprobe_gemerkt(tmp_path, rechne, soll=soll, breite=2, hoehe=2,
                                      maske=[True, True, False, True], grenze=0.65)
    zweit = abholer._nullprobe_gemerkt(tmp_path, rechne, soll=list(soll), breite=2, hoehe=2,
                                       maske=[True, True, False, True], grenze=0.65)
    assert erst == zweit and len(gerechnet) == 1
    # Eine andere Soll-Karte, eine andere Maske: neu gerechnet.
    abholer._nullprobe_gemerkt(tmp_path, rechne, soll=[5.0, 6.0, 8.0, 7.0], breite=2,
                               hoehe=2, maske=[True, True, False, True], grenze=0.65)
    abholer._nullprobe_gemerkt(tmp_path, rechne, soll=soll, breite=2, hoehe=2,
                               maske=[True, True, True, True], grenze=0.65)
    assert len(gerechnet) == 3
    # Ohne Ablage wird immer gerechnet, wie bisher.
    abholer._nullprobe_gemerkt(None, rechne, soll=soll, breite=2, hoehe=2)
    assert len(gerechnet) == 4


# ======================================================================================
# B6 · Die verkleinerten Steuerbilder verschieben die Silhouette nicht
# ======================================================================================

def test_hin_und_zurueck_skaliert_bleibt_die_silhouette_deckungsgleich(tmp_path):
    """Befund zu «Geometrie nicht gemessen» bei der Vorschau: Das KI-Bild entsteht klein
    (1024 × 640) und wird auf die Grösse der Grundlage zurückgebracht. Ginge dabei die Lage
    verloren, fiele die Silhouette neben die Bauwerksmaske. Sie tut es nicht — die Null
    kommt aus dem Bild selbst (Innenraum statt Haus), nicht aus der Skalierung."""
    pytest.importorskip("PIL")
    b, h = 400, 248                                  # das Seitenverhältnis von 1600 × 992
    werte = [0.0] * (b * h)
    for y in range(80, 200):
        for x in range(120, 300):
            werte[y * b + x] = 0.8
    gross = tmp_path / "gross.png"
    bildschreiben.schreibe_graustufen_png(gross, werte, b, h, bittiefe=16)
    klein = tmp_path / "klein.png"
    kb, kh = 256, 160                                # wie 1024 × 640 zu 1600 × 992
    bildschreiben.skaliere_png(gross, klein, kb, kh)
    zurueck = tmp_path / "zurueck.png"
    bildschreiben.skaliere_png(klein, zurueck, b, h)
    from aiimaging import bildlesen
    roh, rb, rh, _ = bildlesen._png_lesen(zurueck)
    assert (rb, rh) == (b, h)
    soll = [w > 0.4 for w in werte]
    ist = [w > 0.4 for w in roh]
    assert geometrie_qa.iou(soll, ist) > 0.95
