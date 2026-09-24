"""Der Knotenweg — die Brücken-Schnittstelle der Knotenansicht, geprüft an Bibliothek und Server.

E26 (24.09.2026): Die aus KosmoOrbit kopierte Knotenansicht bestellt Bilder über dieselbe
HTTP-Schnittstelle wie dort. ``aiimaging.knotenweg`` bedient sie in der Ablageform der
Brücke, damit der Abholer die Aufträge ohne zweite Übersetzung rechnet.

Was hier festgehalten wird, und warum es wichtig ist:

* **Jeder Auftrag beginnt wartend.** Die fremde Brücke setzt ihn sofort in die Reihe, mit
  einem Token, den sie sich selbst gibt. Hier gilt erst der Klick eines Menschen.
* **Die Freigabe-Marke wirkt nur, wo sie hingehört:** nach einem echten Übergang aus
  ``awaiting_approval``. Ein fremder Auftrag ohne Marke bleibt, was er war.
* **Der Weg führt nirgendwohin sonst:** keine fremde Kennung, kein ``../`` im Dateinamen.
"""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, bruecke, knotenweg

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
KENNUNG = "vis-1790000000-abc123"
#: Die Szene, wie die Knotenansicht sie am 24.09.2026 im Browser wirklich geschickt hat —
#: abgeschrieben aus dem Durchstich, nicht ausgedacht. Dazu ein fremdes `out`, das der
#: Server verwerfen muss.
SZENE = {"schema": "kosmovis.render-scene/v1", "cameras": "auto",
         "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
         "style": {"mode": "none", "prompt": "Wohnhaus im Abendlicht, Holzfassade"},
         "vis": {"skip": False, "backbone": "z-image-turbo", "upscale": False},
         "geometry": {"format": "glb"}, "out": "/etc/fremd"}


@pytest.fixture
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


def _glb(tmp_path, name="haus.glb") -> Path:
    pfad = WURZEL / "tools" / "make_test_glb.py"
    spec = importlib.util.spec_from_file_location("mk_glb", pfad)
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    ziel = tmp_path / name
    ziel.write_bytes(mk.baue_glb([("Haus", (0, 0, 0), (8, 3, 5))]))
    return ziel


def _auftrag(tmp_path, modell: bytes = b"glTF-bytes", **kw) -> dict:
    return knotenweg.lege_an(tmp_path / "ablage", dict(SZENE), modell, "model.glb",
                             kennung=kw.pop("kennung", KENNUNG), **kw)


# ---------------------------------------------------------------- 1 · Annehmen


def test_ein_auftrag_liegt_in_der_form_der_bruecke_und_wartet(tmp_path):
    zettel = _auftrag(tmp_path)
    ordner = tmp_path / "ablage" / KENNUNG
    assert zettel["status"] == bruecke.STATUS_AWAITING
    assert zettel["approval_token"].startswith(bruecke.TOKEN_VORSATZ)
    assert (ordner / bruecke.DATEI_MODELL).read_bytes() == b"glTF-bytes"
    szene = json.loads((ordner / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
    # Pfad und Ausgabeort setzt der Server — das mitgeschickte `out` ist verworfen.
    assert szene["out"] == str(ordner / "out")
    assert szene["geometry"]["path"] == str(ordner / bruecke.DATEI_MODELL)
    assert bruecke.offene_auftraege(tmp_path / "ablage") == [], (
        "ein wartender Auftrag darf nicht in der Reihe des Abholers stehen")


def test_eine_ifc_liegt_unter_ihrem_eigenen_namen(tmp_path):
    szene = dict(SZENE, geometry={"format": "ifc"})
    knotenweg.lege_an(tmp_path, szene, b"ISO-10303-21;", "haus.ifc", kennung=KENNUNG)
    assert (tmp_path / KENNUNG / bruecke.DATEI_MODELL_IFC).is_file()


@pytest.mark.parametrize("szene, modell, name, satz", [
    (dict(SZENE, geometry={"format": "glb"}), b"x", "haus.ifc", "nicht umetikettiert"),
    (dict(SZENE, geometry={"format": "fbx"}), b"x", "haus.fbx", "nimmt dieser Weg nicht an"),
    (dict(SZENE, geometry={}), b"x", "blob", "nimmt dieser Weg nicht an"),
    (dict(SZENE), b"", "model.glb", "leer"),
    ([], b"x", "model.glb", "kein JSON-Objekt"),
])
def test_was_nicht_passt_wird_mit_satz_abgewiesen(tmp_path, szene, modell, name, satz):
    with pytest.raises(knotenweg.KnotenwegError, match=satz):
        knotenweg.lege_an(tmp_path, szene, modell, name, kennung=KENNUNG)
    assert not (tmp_path / KENNUNG).exists(), "ein abgewiesener Auftrag hinterlässt nichts"


# ---------------------------------------------------------------- 2 · Freigeben


def test_erst_der_klick_eines_menschen_gibt_frei(tmp_path):
    # EINE ECHTE glb: Der Sichtgang des Lesers weist Attrappen-Bytes als Mangel ab — so
    # soll es sein, und darum prüft diese Probe mit einem Modell, das er annimmt.
    zettel = _auftrag(tmp_path, modell=_glb(tmp_path).read_bytes())
    ordner = tmp_path / "ablage" / KENNUNG
    assert bruecke.lies_auftrag(ordner)["freigegeben"] is False

    with pytest.raises(knotenweg.KnotenwegError) as falsch:
        knotenweg.freigeben(tmp_path / "ablage", KENNUNG, "CONFIRMED_RENDER_00000000")
    assert falsch.value.code == 403
    assert bruecke.lies_auftrag(ordner)["status"] == bruecke.STATUS_AWAITING

    frei = knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    assert frei["status"] == bruecke.STATUS_QUEUED
    assert bruecke.FELD_MELDUNG not in frei, (
        "auf `queued` liest die Knotenansicht eine Meldung als «vom Abholer zurückgestellt»")
    gelesen = bruecke.lies_auftrag(ordner)
    assert gelesen["freigegeben"] is True
    assert "Knotenansicht" in gelesen["freigabe_grund"]
    assert gelesen["maengel"] == ()
    assert bruecke.offene_auftraege(tmp_path / "ablage") == [ordner]


def test_die_marke_wirkt_nicht_solange_der_auftrag_noch_wartet(tmp_path):
    """Eine von Hand in einen wartenden Laufzettel geschriebene Marke ist kein Klick."""
    _auftrag(tmp_path)
    pfad = tmp_path / "ablage" / KENNUNG / bruecke.DATEI_LAUFZETTEL
    zettel = json.loads(pfad.read_text(encoding="utf-8"))
    zettel[bruecke.FELD_FREIGABE_KNOTEN] = {"am": "2026-09-24T00:00:00+00:00"}
    pfad.write_text(json.dumps(zettel), encoding="utf-8")
    assert bruecke.lies_auftrag(pfad.parent)["freigegeben"] is False


def test_ein_auftrag_der_fremden_bruecke_bleibt_unfrei(tmp_path):
    """Die Gegenprobe: ohne Marke gilt, was vor dem Knotenweg galt."""
    _auftrag(tmp_path)
    pfad = tmp_path / "ablage" / KENNUNG / bruecke.DATEI_LAUFZETTEL
    zettel = json.loads(pfad.read_text(encoding="utf-8"))
    zettel["status"] = bruecke.STATUS_QUEUED          # so legt die fremde Brücke ihn an
    pfad.write_text(json.dumps(zettel), encoding="utf-8")
    gelesen = bruecke.lies_auftrag(pfad.parent)
    assert gelesen["freigegeben"] is False
    assert "Brücke SELBST" in gelesen["freigabe_grund"]


def test_zweimal_freigeben_aendert_nichts(tmp_path):
    zettel = _auftrag(tmp_path)
    erst = knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    noch = knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    assert noch == erst


# ---------------------------------------------------------------- 3 · Abbrechen, Lesen


def test_abbrechen_trifft_nur_was_noch_nicht_zu_ende_ist(tmp_path):
    _auftrag(tmp_path)
    assert knotenweg.abbrechen(tmp_path / "ablage", KENNUNG)["status"] == "cancelled"
    bruecke.setze_status(tmp_path / "ablage" / KENNUNG, bruecke.STATUS_DONE)
    assert knotenweg.abbrechen(tmp_path / "ablage", KENNUNG)["status"] == "done"


def test_das_ergebnis_kommt_mit_sobald_es_daliegt(tmp_path):
    _auftrag(tmp_path)
    ordner = tmp_path / "ablage" / KENNUNG
    assert "result" not in knotenweg.lies(tmp_path / "ablage", KENNUNG)
    (ordner / bruecke.DATEI_ERGEBNIS).write_text('{"images": ["a.png"]}', encoding="utf-8")
    assert knotenweg.lies(tmp_path / "ablage", KENNUNG)["result"] == {"images": ["a.png"]}


def test_die_liste_nennt_die_juengsten_zuerst(tmp_path):
    _auftrag(tmp_path, kennung="vis-1790000000-aaaaaa")
    _auftrag(tmp_path, kennung="vis-1790000009-bbbbbb")
    (tmp_path / "ablage" / "fremder-ordner").mkdir()
    assert [z["job_id"] for z in knotenweg.liste(tmp_path / "ablage")] == [
        "vis-1790000009-bbbbbb", "vis-1790000000-aaaaaa"]


@pytest.mark.parametrize("kennung, name", [
    ("../ablage", "job.json"),
    (KENNUNG, "../../geheim.txt"),
    (KENNUNG, ".versteckt"),
    (KENNUNG, "gibt-es-nicht.png"),
])
def test_artefakte_nur_aus_dem_eigenen_ordner(tmp_path, kennung, name):
    _auftrag(tmp_path)
    (tmp_path / "geheim.txt").write_text("nein", encoding="utf-8")
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.artefakt(tmp_path / "ablage", kennung, name)
    assert fehler.value.code == 404


def test_gesundheit_taeuscht_keinen_dienst_vor():
    antwort = knotenweg.gesundheit(None)
    assert antwort["ok"] is True
    assert not any(antwort["services"].values())


# ---------------------------------------------------------------- 4 · Die Mappe


def test_die_mappe_liefert_modell_und_huellbox(tmp_path):
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _glb(tmp_path), name="Testbau")
    antwort = knotenweg.mappe_fuer_knoten(mappe)
    assert antwort["name"] == "Testbau"
    assert Path(antwort["glb"]).is_file()
    (lo, hi) = antwort["huellbox_m"]
    assert hi[0] - lo[0] == pytest.approx(8) and hi[2] - lo[2] == pytest.approx(3)
    assert antwort["grund"] == ""


# ---------------------------------------------------------------- 5 · Der Server reicht durch


class _Anfrage:
    """Eine Anfrage ohne Netz — ``do_GET``/``do_POST`` laufen wirklich (wie in
    ``test_oberflaeche.py``)."""

    def __init__(self, modul, *, befehl, weg, rumpf=b"", typ=None, ordner=None, ablage=None):
        klasse = type("Pruefling", (modul.Flaeche,),
                      {"kennwort": "geheim", "ordner": ordner, "kopplung_offen": None,
                       "ablage": ablage})
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        kopf = "Basic " + base64.b64encode(b"visbox:geheim").decode()
        self.selbst.headers = {"Authorization": kopf, "Content-Length": str(len(rumpf)),
                               "Content-Type": typ or "application/json"}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda *a: None
        self.selbst.end_headers = lambda: None

    def stelle(self):
        (self.selbst.do_GET if self.selbst.command == "GET" else self.selbst.do_POST)()
        return self

    def json(self):
        return json.loads(self.selbst.wfile.getvalue())


def _formular(felder: dict) -> tuple[bytes, str]:
    grenze = "----visbox-grenze"
    teile = []
    for name, (dateiname, inhalt) in felder.items():
        kopf = f'Content-Disposition: form-data; name="{name}"'
        if dateiname:
            kopf += f'; filename="{dateiname}"\r\nContent-Type: application/octet-stream'
        teile.append(f"--{grenze}\r\n{kopf}\r\n\r\n".encode() + inhalt + b"\r\n")
    return b"".join(teile) + f"--{grenze}--\r\n".encode(), f"multipart/form-data; boundary={grenze}"


def test_der_ganze_weg_ueber_den_server(server, tmp_path):
    """Annehmen, Freigeben, Lesen, Bild holen — so, wie die Knotenansicht fragt."""
    ablage = tmp_path / "ablage"
    # Binäre Bytes mit Zeilenenden darin: Der Formularleser darf sie nicht anfassen.
    modell = b"glTF\x02\x00\r\n\x00\xff\r\n\r\nende"
    rumpf, typ = _formular({"scene": (None, json.dumps(SZENE).encode()),
                            "model": ("model.glb", modell)})
    a = _Anfrage(server, befehl="POST", weg="/bruecke/jobs", rumpf=rumpf, typ=typ,
                 ablage=ablage).stelle()
    assert a.codes == [200], a.selbst.wfile.getvalue()
    zettel = a.json()
    kennung = zettel["job_id"]
    assert (ablage / kennung / "model.glb").read_bytes() == modell

    frei = _Anfrage(server, befehl="POST", weg=f"/bruecke/jobs/{kennung}/approve",
                    rumpf=json.dumps({"approval_token": zettel["approval_token"]}).encode(),
                    ablage=ablage).stelle()
    assert frei.codes == [200] and frei.json()["status"] == "queued"

    (ablage / kennung / "bild.png").write_bytes(b"\x89PNG")
    bild = _Anfrage(server, befehl="GET", weg=f"/bruecke/jobs/{kennung}/artifacts/bild.png",
                    ablage=ablage).stelle()
    assert bild.codes == [200] and bild.selbst.wfile.getvalue() == b"\x89PNG"

    liste = _Anfrage(server, befehl="GET", weg="/bruecke/jobs", ablage=ablage).stelle()
    assert [z["job_id"] for z in liste.json()] == [kennung]


def test_ohne_ablage_sagt_der_server_warum(server):
    a = _Anfrage(server, befehl="GET", weg="/bruecke/jobs").stelle()
    assert a.codes == [503]
    assert "--auftragsablage" in a.json()["fehler"]
    gesund = _Anfrage(server, befehl="GET", weg="/bruecke/health").stelle()
    assert gesund.codes == [200] and gesund.json()["services"]["jobstore"] is False


@pytest.mark.parametrize("weg, satz", [
    ("/bruecke/jobs/blender-sim", "gibt es in Visbox nicht"),
    ("/bruecke/jobs/bake", "gibt es in Visbox nicht"),
    ("/bruecke/claude-code", "gibt es in Visbox nicht"),
])
def test_wege_der_bruecke_die_es_hier_nicht_gibt_sagen_es(server, tmp_path, weg, satz):
    a = _Anfrage(server, befehl="POST", weg=weg, ablage=tmp_path).stelle()
    assert a.codes == [404]
    assert satz in a.json()["fehler"]


def test_ein_auftrag_ohne_formular_wird_abgewiesen(server, tmp_path):
    a = _Anfrage(server, befehl="POST", weg="/bruecke/jobs", rumpf=b"{}",
                 ablage=tmp_path).stelle()
    assert a.codes == [400] and "Formular" in a.json()["fehler"]


def test_die_vorsilbe_hat_eine_grenze(server):
    assert server._ist_knotenweg("/knoten") and server._ist_knotenweg("/knoten/mappe")
    assert server._ist_knotenweg("/bruecke/jobs")
    assert not server._ist_knotenweg("/knotenwerk")
    assert not server._ist_knotenweg("/brueckenbau")


def test_die_mappe_geht_ohne_plattenpfad_an_die_seite(server, tmp_path):
    """Regel 3: Die Seite erfährt, OB es ein Modell gibt — nicht, wo es auf der Platte liegt."""
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _glb(tmp_path), name="Testbau")
    a = _Anfrage(server, befehl="GET", weg="/knoten/mappe", ordner=mappe).stelle()
    assert a.codes == [200]
    assert a.json()["glb"] is True
    assert str(tmp_path) not in a.selbst.wfile.getvalue().decode("utf-8")
    modell = _Anfrage(server, befehl="GET", weg="/knoten/modell.glb", ordner=mappe).stelle()
    assert modell.codes == [200]
    assert modell.selbst.wfile.getvalue()[:4] == b"glTF"


def test_die_knotenseite_liefert_nur_aus_ihrem_bau(server, tmp_path, monkeypatch):
    bau = tmp_path / "dist"
    (bau / "assets").mkdir(parents=True)
    (bau / "index.html").write_text("<!doctype html>", encoding="utf-8")
    (bau / "assets" / "a.js").write_text("1", encoding="utf-8")
    (tmp_path / "geheim.txt").write_text("nein", encoding="utf-8")
    monkeypatch.setattr(server, "KNOTEN_BAU", bau)
    assert _Anfrage(server, befehl="GET", weg="/knoten/").stelle().codes == [200]
    assert _Anfrage(server, befehl="GET", weg="/knoten/assets/a.js").stelle().codes == [200]
    assert _Anfrage(server, befehl="GET", weg="/knoten").stelle().codes == [301]
    assert _Anfrage(server, befehl="GET", weg="/knoten/../geheim.txt").stelle().codes == [404]


def test_ohne_bau_sagt_die_knotenseite_wie_man_ihn_macht(server, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "KNOTEN_BAU", tmp_path / "fehlt")
    a = _Anfrage(server, befehl="GET", weg="/knoten/").stelle()
    assert a.codes == [404] and "npm run build" in a.json()["fehler"]


# ---------------------------------------------------------------- 6 · Wohin die Aufträge kommen


def _gebaut(server, monkeypatch) -> list:
    """Der echte Serverbau, aber ``serve_forever`` endet sofort wie mit Strg-C."""
    echt, liste = server.baue_server, []

    def bau(**kw):
        srv = echt(**kw)

        def sofort_beendet():
            raise KeyboardInterrupt

        srv.serve_forever = sofort_beendet
        liste.append(srv)
        return srv

    monkeypatch.setattr(server, "baue_server", bau)
    return liste


def test_die_ablage_liegt_ohne_angabe_in_der_mappe(server, tmp_path, monkeypatch):
    liste = _gebaut(server, monkeypatch)
    server.main(["--ordner", str(tmp_path), "--anschluss", "0"])
    klasse = liste[0].RequestHandlerClass
    assert klasse.ablage == tmp_path / "knotenweg"
    liste[0].server_close()


def test_die_ablage_laesst_sich_ausdruecklich_setzen(server, tmp_path, monkeypatch):
    liste = _gebaut(server, monkeypatch)
    server.main(["--ordner", str(tmp_path), "--anschluss", "0",
                 "--auftragsablage", str(tmp_path / "anderswo")])
    assert liste[0].RequestHandlerClass.ablage == tmp_path / "anderswo"
    liste[0].server_close()
