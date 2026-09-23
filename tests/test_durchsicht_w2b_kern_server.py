"""Die Mängel der Durchsicht der Welle 2, Einheit Kern/Server (22./23.09.2026) — **an der
Wirkung** geprüft, jeder mit dem Befund, den er festhält.

1. **Eine Skizze, die während ihres Laufs verworfen wird**, drehte das Nachholen nach
   einer Kollision still auf «gerechnet» zurück (``markiere_skizze`` überschreibt).
   Nachgestellt mit einer Sonde im Bildmodell, mitten im Lauf.
2. **Die Rundung beim Mischen** (``_mische``, ``+127``) war unbewacht.
3. **Zwei Skizzen mit gleichem Stamm** aus verschiedenen Unterordnern schrieben in einer
   Ebenen-Reihe dasselbe Eingangsbild.
4. **Gestreckt, oder ohne Unterlage auf Grau** — stand nur in der Mappe, niemand zeigte
   es. Jetzt ein Hinweis-Satz in der Sicht (``GET /api/projekt``).
5. **Das Vorher** (Feld ``vorher``): der Name des Bildes, über das skizziert wurde — nur
   ein Bild dieser Mappe, sonst ``null``. Die Webseite nimmt es für den Wischregler.
6. **Der Schlüssel der Webseite**: ein Tipp ohne Strich gab der Zeichnung einen neuen,
   und eine neue Grösse der Tafel leerte sie, ohne dass die Seite es wusste.
7. **Der Name der App** stand im 401-Satz, im Bereich, im Kopf ``Server`` und in den
   Startzeilen noch fest.

Ohne GPU, ohne Blender. Regel 3: alles hier entsteht aus ein paar Bytes.
"""
from __future__ import annotations

import ast
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import urllib.parse
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, bildlesen, bildschreiben, kette, projekt
from aiimaging.kette import (ART_BILDQUELLE, ART_GEOMETRIE, ART_MULTIPASS, ART_NACHRENDER,
                             ART_QA, ART_RENDER)

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"
ROT, BLAU = (255, 0, 0), (0, 0, 255)


# ======================================================================================
# Werkzeug
# ======================================================================================

def _rgba_png(pfad, breite: int, hoehe: int, punkte: dict, grund=(0, 0, 0, 0)) -> Path:
    """Ein RGBA-PNG wie aus der App: durchsichtiger Grund, Striche aus ``punkte``."""
    roh = bytearray()
    for y in range(hoehe):
        roh.append(0)
        for x in range(breite):
            roh += bytes(punkte.get((x, y), grund))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(bytes(roh))) + block(b"IEND", b""))
    return pfad


def _einfarbig(pfad, breite: int, hoehe: int, farbe) -> Path:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    return bildschreiben.schreibe_farb_png(pfad, [farbe] * (breite * hoehe), breite, hoehe)


class _Modell:
    """Das Bildmodell des Nachrenders — es rechnet nichts, es **liest**, was ankommt.

    ``sonde`` läuft **mitten im Lauf**, an der Stelle, an der sonst die GPU rechnet."""

    def __init__(self, *, sonde=None):
        self.eingaenge: list = []
        self.sonde = sonde

    def __call__(self, parameter: dict) -> dict:
        self.eingaenge.append(bildlesen.lies_png_farben(parameter["beauty_png"]))
        if self.sonde is not None:
            self.sonde()
        _einfarbig(parameter["ausgabe_png"], 2, 2, (9, 9, 9))
        return {"bild_png": parameter["ausgabe_png"], "hinweise": [],
                "schritte_gerechnet": None}


def _tabelle(modell, *, unterlage=(4, 4, BLAU)) -> dict:
    """Geometrie, Multipass und Bildstufe als Attrappen; Bildquelle und Nachrender ECHT."""
    breite, hoehe, farbe = unterlage

    def geometrie(*, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [8, 5, 3]]}

    def multipass(*, knoten, eingaben, out_dir):
        tiefe = bildschreiben.schreibe_graustufen_png(Path(out_dir) / "tiefe_norm.png",
                                                      [0.5] * 4, 2, 2)
        return {"status": "ok", "depth_png": str(tiefe),
                "beauty_png": str(_einfarbig(Path(out_dir) / "beauty.png", 2, 2, (5, 5, 5)))}

    def render(*, knoten, eingaben, out_dir):
        return {"status": "ok",
                "bild_png": str(_einfarbig(Path(out_dir) / "bild.png", breite, hoehe, farbe))}

    return {ART_GEOMETRIE: geometrie, ART_MULTIPASS: multipass, ART_RENDER: render,
            ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell),
            ART_QA: kette.qa_ausfuehrer()}


@pytest.fixture
def mappe(tmp_path):
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y",
                                       "qa": False})
    return wurzel


def _neu(wurzel) -> dict:
    """Die Mappe, **frisch von der Platte** — nicht der Rückgabewert."""
    return projekt.oeffne(wurzel)["projekt"]


def _unterlage_rechnen(mappe, **wie) -> str:
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(_Modell(), **wie))
    (name,) = ergebnis["bilder"]
    return name


def _skizze_ablegen(mappe, name, punkte, *, ueber, breite=4, hoehe=4) -> str:
    """Wie die Fläche: Datei schreiben, in der Mappe vermerken, speichern."""
    _rgba_png(Path(mappe) / name, breite, hoehe, punkte)
    p = _neu(mappe)
    projekt.vermerke_skizze(p, skizze=name, ueber=ueber, bemerkung="ein Vordach")
    projekt.speichere(p, mappe)
    return name


def _skizze_der_mappe(mappe, name) -> list:
    return [s for s in (_neu(mappe).get("skizzen") or []) if s["skizze"] == name]


def _bild_aus(mappe, skizze) -> dict:
    treffer = [b for b in _neu(mappe)["bilder"] if b["herkunft"].get("skizze") == skizze]
    assert len(treffer) == 1, treffer
    return treffer[0]


def _node():
    return shutil.which("node")


# ======================================================================================
# 1 · Eine während des Laufs verworfene Skizze bleibt verworfen
# ======================================================================================

def test_eine_waehrend_des_laufs_verworfene_skizze_bleibt_verworfen(mappe):
    """**Die Sonde, nachgestellt:** Mitten im Lauf (im Bildmodell) verwirft jemand die
    Skizze. Der Lauf kollidiert beim Speichern, holt den frischen Stand nach — und drehte
    bis zum 22.09.2026 die Skizze dabei still auf «gerechnet». Jetzt bleibt sie verworfen;
    das Bild ist trotzdem entstanden, steht in der Mappe und an der Skizze als Ergebnis."""
    _skizze_ablegen(mappe, "skizze-v.png", {(0, 0): (*ROT, 255)}, ueber=None)

    def verwerfen():
        p = _neu(mappe)
        projekt.markiere_skizze(p, skizze="skizze-v.png", stand=projekt.SKIZZE_VERWORFEN)
        projekt.speichere(p, mappe)

    ergebnis = arbeitsgang.rechne_skizze(mappe, "skizze-v.png",
                                         ausfuehrer=_tabelle(_Modell(sonde=verwerfen)))

    (skizze,) = _skizze_der_mappe(mappe, "skizze-v.png")
    assert skizze["stand"] == projekt.SKIZZE_VERWORFEN, "der Entscheid bleibt"
    bild = _bild_aus(mappe, "skizze-v.png")
    assert skizze["ergebnis"] == bild["bild"], "was daraus wurde, steht trotzdem da"
    assert ergebnis["bilder"] == [bild["bild"]]
    assert _neu(mappe)["laeufe"][-1]["skizze"] == "skizze-v.png", "der Lauf steht da"


def test_ohne_eingriff_wird_die_skizze_gerechnet(mappe):
    """Die Gegenprobe: Niemand verwirft — dann heisst es «gerechnet», wie bisher."""
    _skizze_ablegen(mappe, "skizze-g.png", {(0, 0): (*ROT, 255)}, ueber=None)
    arbeitsgang.rechne_skizze(mappe, "skizze-g.png", ausfuehrer=_tabelle(_Modell()))
    (skizze,) = _skizze_der_mappe(mappe, "skizze-g.png")
    assert skizze["stand"] == projekt.SKIZZE_GERECHNET
    assert skizze["ergebnis"] == _bild_aus(mappe, "skizze-g.png")["bild"]


def test_eine_waehrend_des_laufs_entfernte_skizze_nimmt_die_vermerke_nicht_mit(mappe):
    """Steht die Skizze beim Nachholen nicht mehr in der Mappe, würfe ``markiere_skizze``
    — und die Ausnahme nähme alle Vermerke des Laufs mit. Jetzt: Das Bild steht da und
    nennt seine Skizze; an der Skizze wird nichts vermerkt, weil es sie nicht mehr gibt."""
    _skizze_ablegen(mappe, "skizze-w.png", {(0, 0): (*ROT, 255)}, ueber=None)

    def entfernen():
        p = _neu(mappe)
        p["skizzen"] = [s for s in p["skizzen"] if s["skizze"] != "skizze-w.png"]
        projekt.speichere(p, mappe)

    arbeitsgang.rechne_skizze(mappe, "skizze-w.png",
                              ausfuehrer=_tabelle(_Modell(sonde=entfernen)))

    assert _skizze_der_mappe(mappe, "skizze-w.png") == []
    assert _bild_aus(mappe, "skizze-w.png")["herkunft"]["skizze"] == "skizze-w.png"


# ======================================================================================
# 2 · Die Rundung beim Mischen
# ======================================================================================

def test_halb_deckend_wird_gerundet_und_nicht_abgeschnitten(tmp_path):
    """``Strich · α + Unterlage · (1 − α)``, **gerundet**. Zwei Werte, an denen Abrunden
    und Runden auseinanderfallen, und einer genau unter der Hälfte:

    * Rot 1 mit Deckung 128 über Schwarz: 128/255 = 0,502 → **1** (abgeschnitten: 0);
    * Grün 127 mit Deckung 1 über Schwarz: 127/255 = 0,498 → **0** (eine Rundung, die
      schon ab 0,498 aufrundet, gäbe 1)."""
    skizze = _rgba_png(tmp_path / "s.png", 2, 1, {(0, 0): (1, 0, 0, 128),
                                                  (1, 0): (0, 127, 0, 1)})
    unterlage = _einfarbig(tmp_path / "u.png", 2, 1, (0, 0, 0))

    ergebnis = arbeitsgang.setze_auf_unterlage(skizze, tmp_path / "e.png",
                                               unterlage=unterlage)

    farben, _, _ = bildlesen.lies_png_farben(ergebnis["bild"])
    assert farben == [(1, 0, 0), (0, 0, 0)]


# ======================================================================================
# 3 · Zwei Skizzen mit gleichem Stamm in einer Ebenen-Reihe
# ======================================================================================

def test_zwei_skizzen_mit_gleichem_stamm_bekommen_je_ihr_eingangsbild(mappe):
    """``a/skizze.png`` und ``b/skizze.png`` als Ebenen-Reihe über den Bibliotheksweg. Bis
    zum 22.09.2026 hiess beider Eingangsbild ``eingang/skizze.png``: Die zweite überschrieb
    die erste, bevor die erste gerechnet war, und **beide Ebenen rechneten auf der
    zweiten Zeichnung.** Geprüft wird, was das Bildmodell wirklich bekam."""
    _skizze_ablegen(mappe, "a/skizze.png", {(0, 0): (*ROT, 255)}, ueber=None)
    _skizze_ablegen(mappe, "b/skizze.png", {(3, 3): (*BLAU, 255)}, ueber=None)
    modell = _Modell()

    arbeitsgang.rechne_skizze(mappe, ["a/skizze.png", "b/skizze.png"],
                              ausfuehrer=_tabelle(modell))

    (farben_a, _, _), (farben_b, _, _) = modell.eingaenge
    assert farben_a[0] == ROT and farben_a[15] == arbeitsgang.NEUTRALER_GRUND
    assert farben_b[15] == BLAU and farben_b[0] == arbeitsgang.NEUTRALER_GRUND
    eingang_a = _bild_aus(mappe, "a/skizze.png")["herkunft"]["unterlage"]["eingangsbild"]
    eingang_b = _bild_aus(mappe, "b/skizze.png")["herkunft"]["unterlage"]["eingangsbild"]
    assert eingang_a != eingang_b
    assert (mappe / eingang_a).is_file() and (mappe / eingang_b).is_file()


def test_dieselbe_skizze_bekommt_bei_jedem_lauf_denselben_eingangsnamen(mappe):
    """Gleich bleibt gleich: Der Name hängt am Skizzennamen, nicht am Lauf — sonst änderte
    jeder Lauf den Pfad im Graphen und damit jeden Zwischenspeicher-Schlüssel dahinter."""
    _skizze_ablegen(mappe, "skizze-z.png", {(0, 0): (*ROT, 255)}, ueber=None)
    namen = []
    for _ in range(2):
        arbeitsgang.rechne_skizze(mappe, "skizze-z.png", ausfuehrer=_tabelle(_Modell()))
        namen.append(_neu(mappe)["bilder"][-1]["herkunft"]["unterlage"]["eingangsbild"])
    assert namen[0] == namen[1]
    assert namen[0].startswith(arbeitsgang.EINGANGSORDNER + "/skizze-z-")


# ======================================================================================
# 4 und 5 · Die Sicht: der Hinweis zur Unterlage, und das Vorher
# ======================================================================================

@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


class _Anfrage:
    """Eine ganze Anfrage an ``Flaeche`` — ``do_GET``/``do_POST`` laufen wirklich (dieselbe
    Bauform wie in ``tests/test_flaeche_fuer_die_app.py``; Probedateien importieren
    einander nicht). Die Köpfe der Antwort werden festgehalten."""

    def __init__(self, modul, *, befehl="GET", weg, kennwort=None, rumpf=None):
        rumpf = json.dumps(rumpf).encode("utf-8") if rumpf is not None else b""
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": None, "kopplung_offen": None})
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": None, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.koepfe: dict[str, str] = {}
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda name, wert: self.koepfe.__setitem__(name, wert)
        self.selbst.end_headers = lambda: None
        (self.selbst.do_GET if befehl == "GET" else self.selbst.do_POST)()

    @property
    def daten(self) -> dict:
        return json.loads(self.selbst.wfile.getvalue().decode("utf-8"))


def _sicht(server, wurzel) -> dict:
    a = _Anfrage(server, weg="/api/projekt?ordner=" + urllib.parse.quote(str(wurzel)))
    assert a.codes == [200], a.daten
    return a.daten


def _sicht_von(server, mappe, skizze) -> dict:
    treffer = [b for b in _sicht(server, mappe)["bilder"]
               if (b.get("herkunft") or {}).get("skizze") == skizze]
    assert len(treffer) == 1, treffer
    return treffer[0]


def test_gestreckt_steht_als_hinweis_am_bild(server, mappe):
    """Blatt 6x4 auf ein Bild 4x4: gestreckt. Der Satz der Bibliothek steht in
    ``hinweise`` (die Webseite und die App zeigen die Liste) und in ``unterlage_hinweis``."""
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-s.png", {}, ueber=unterlage, breite=6, hoehe=4)
    arbeitsgang.rechne_skizze(mappe, "skizze-s.png", ausfuehrer=_tabelle(_Modell()))

    b = _sicht_von(server, mappe, "skizze-s.png")
    assert b["unterlage_hinweis"] and "GESTRECKT" in b["unterlage_hinweis"]
    assert b["unterlage_hinweis"] in b["hinweise"]


def test_ohne_unterlage_steht_das_grau_als_hinweis_am_bild(server, mappe):
    _skizze_ablegen(mappe, "skizze-o.png", {(0, 0): (*ROT, 255)}, ueber=None)
    arbeitsgang.rechne_skizze(mappe, "skizze-o.png", ausfuehrer=_tabelle(_Modell()))

    b = _sicht_von(server, mappe, "skizze-o.png")
    assert b["unterlage_hinweis"] and "Grau" in b["unterlage_hinweis"]
    assert b["hinweise"][-1] == b["unterlage_hinweis"]


def test_blatt_auf_bild_ohne_streckung_braucht_keinen_hinweis(server, mappe):
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-p.png", {(0, 0): (*ROT, 255)}, ueber=unterlage)
    arbeitsgang.rechne_skizze(mappe, "skizze-p.png", ausfuehrer=_tabelle(_Modell()))

    b = _sicht_von(server, mappe, "skizze-p.png")
    assert b["unterlage_hinweis"] is None
    assert not any("Unterlage" in h or "GESTRECKT" in h for h in b["hinweise"])


def test_meldet_die_bildstufe_nichts_bleibt_hinweise_nicht_gemessen(server):
    """**Die dritte Antwort bleibt:** ``hinweise: null`` heisst «die Bildstufe hat nichts
    gemeldet». Der Satz zur Unterlage macht daraus keine Liste — er steht dann allein in
    ``unterlage_hinweis``.

    Am Eintrag und nicht über den Lauf: Über die Kette meldet der Nachrender immer eine
    Liste (nachgesehen am 23.09.2026 — ``kette`` stellt dort mindestens «SKIZZE NICHT
    ANGEKOMMEN» voran). Eine Mappe mit anderer Herkunft kann den Fall trotzdem tragen."""
    eintrag = {"bild": "b.png", "schicht": "ai-imaging-layer", "geometrie_bestanden": None,
               "herkunft": {"grund": "NICHT GEMESSEN.", "skizze": "s.png",
                            "messung": {"hinweise": None},
                            "unterlage": {"bild": None, "gestreckt": False,
                                          "grund": "Ohne Unterlage gezeichnet — Grau."}}}
    b = server._bild_fuer_die_flaeche(eintrag)
    assert b["hinweise"] is None
    assert b["unterlage_hinweis"] == "Ohne Unterlage gezeichnet — Grau."


def test_das_vorher_ist_der_name_der_unterlage(server, mappe):
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-x.png", {(0, 0): (*ROT, 255)}, ueber=unterlage)
    arbeitsgang.rechne_skizze(mappe, "skizze-x.png", ausfuehrer=_tabelle(_Modell()))

    sicht = _sicht(server, mappe)
    (b,) = [x for x in sicht["bilder"] if (x.get("herkunft") or {}).get("skizze")]
    assert b["vorher"] == unterlage
    assert b["vorher"] in [x["bild"] for x in sicht["bilder"]], "ein Bild dieser Mappe"
    assert not Path(b["vorher"]).is_absolute(), "ein Name, kein Pfad"
    (u,) = [x for x in sicht["bilder"] if x["bild"] == unterlage]
    assert u["vorher"] is None, "ein Bild aus dem Modell hat kein Vorher"


def test_ohne_unterlage_gibt_es_kein_vorher(server, mappe):
    _skizze_ablegen(mappe, "skizze-y.png", {(0, 0): (*ROT, 255)}, ueber=None)
    arbeitsgang.rechne_skizze(mappe, "skizze-y.png", ausfuehrer=_tabelle(_Modell()))
    assert _sicht_von(server, mappe, "skizze-y.png")["vorher"] is None


@pytest.mark.parametrize("fall", ["datei-weg", "nicht-mehr-in-der-mappe", "pfad-nach-draussen"])
def test_ein_vorher_das_es_nicht_gibt_ist_null(server, mappe, fall):
    """Nur ein Bild, das in der Mappe **steht und liegt**. Fehlt die Datei, führt die
    Mappe den Namen nicht mehr, oder nennt die Herkunft einen Pfad aus der Mappe heraus:
    ``null`` — nie ein Name, unter dem die App nichts laden kann, und nie ein Pfad."""
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-q.png", {(0, 0): (*ROT, 255)}, ueber=unterlage)
    arbeitsgang.rechne_skizze(mappe, "skizze-q.png", ausfuehrer=_tabelle(_Modell()))
    p = _neu(mappe)
    if fall == "datei-weg":
        (mappe / unterlage).unlink()
    elif fall == "nicht-mehr-in-der-mappe":
        p["bilder"] = [b for b in p["bilder"] if b["bild"] != unterlage]
        projekt.speichere(p, mappe)
    else:
        draussen = _einfarbig(mappe.parent / "draussen.png", 2, 2, ROT)
        (bild,) = [b for b in p["bilder"] if b["herkunft"].get("skizze")]
        bild["herkunft"]["unterlage"]["bild"] = str(draussen)
        p["bilder"].append({**bild, "bild": str(draussen), "herkunft": {}})
        projekt.speichere(p, mappe)

    assert _sicht_von(server, mappe, "skizze-q.png")["vorher"] is None


# ======================================================================================
# 6 · Die Seite, gefahren in node: Schlüssel, Tafelgrösse, Wischregler
# ======================================================================================

#: Die Elemente der DOM-Attrappe — so viel, wie das Skript der Seite hier anfasst. Die
#: Leinwand zählt, wie oft ihr eine Grösse gesetzt wurde (das leert sie im Browser), das
#: Bild, wie oft ihm eine Quelle gesetzt wurde (dann meldet es sich neu).
_EL = r"""class ClassList { constructor(e){this.e=e;} _s(){return new Set((this.e.className||"").split(/\s+/).filter(Boolean));}
  add(...c){const s=this._s();c.forEach(x=>s.add(x));this.e.className=[...s].join(" ");}
  remove(...c){const s=this._s();c.forEach(x=>s.delete(x));this.e.className=[...s].join(" ");}
  toggle(c,f){const s=this._s();const an=f===undefined?!s.has(c):f;an?s.add(c):s.delete(c);this.e.className=[...s].join(" ");return an;}
  contains(c){return this._s().has(c);} }
class El {
  constructor(tag){this.tagName=(tag||"div").toUpperCase();this.children=[];this.className="";this.hidden=false;this.style={};this.dataset={};
    this._text="";this.value="";this.classList=new ClassList(this);this.listeners={};this._w=0;this._h=0;this.naturalWidth=0;this.naturalHeight=0;
    this.geleert=0;this._src="";this.srcGesetzt=0;}
  // EINE LEINWAND, DER MAN DIE GROESSE SETZT, IST LEER — auch bei derselben Zahl. Gezaehlt.
  get width(){return this._w;} set width(v){this._w=v;this.geleert++;}
  get height(){return this._h;} set height(v){this._h=v;this.geleert++;}
  get src(){return this._src;} set src(v){this._src=v;this.srcGesetzt++;}
  get textContent(){return this._text+this.children.map(c=>c.textContent||"").join("");}
  set textContent(t){this._text=String(t);this.children=[];}
  append(...k){for(const x of k){if(x&&x.parentNode)x.remove();const n=(typeof x==="string")?Object.assign(new El("#text"),{_text:x}):x;n.parentNode=this;this.children.push(n);}}
  prepend(...k){this.append(...k);}
  replaceChildren(...k){this.children=[];this._text="";this.append(...k);}
  insertBefore(n,ref){if(n.parentNode)n.remove();n.parentNode=this;const i=this.children.indexOf(ref);if(i<0)this.children.push(n);else this.children.splice(i,0,n);}
  remove(){if(this.parentNode){const p=this.parentNode;p.children=p.children.filter(c=>c!==this);this.parentNode=null;}}
  replaceWith(n){const p=this.parentNode;if(!p)return;const i=p.children.indexOf(this);p.children[i]=n;n.parentNode=p;this.parentNode=null;}
  addEventListener(t,f){(this.listeners[t]=this.listeners[t]||[]).push(f);}
  klick(){for(const f of (this.listeners.click||[]))f({});}
  querySelector(sel){const cls=sel.replace(".","");const such=(e)=>{for(const c of e.children){if(c.classList&&c.classList.contains(cls))return c;const r=such(c);if(r)return r;}return null;};return such(this);}
  alle(pred,aus=[]){for(const c of this.children){if(pred(c))aus.push(c);c.alle&&c.alle(pred,aus);}return aus;}
  focus(){} setPointerCapture(){} getBoundingClientRect(){return {left:0,top:0,width:10,height:10};}
  getContext(){return new Proxy({}, {get:()=>()=>{}, set:()=>true});}
  toDataURL(){return "data:image/png;base64,AAAA";}
}
"""

_DOM = r"""// Eine kleine DOM-Attrappe: so viel Element, wie das Skript der Seite hier anfasst.
const fs = require("fs");
const skript = fs.readFileSync(process.argv[2], "utf8");
const sicht = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
""" + _EL + r"""const ids = {};
const document = { hidden:false, getElementById:(id)=>ids[id]||(ids[id]=new El("div")), createElement:(t)=>new El(t),
  createTextNode:(t)=>Object.assign(new El("#text"),{_text:t}), querySelectorAll:()=>[] };
const gesendet = [];
async function fetch(url, opt) {
  if (url === "/api/skizze") gesendet.push(JSON.parse(opt.body).schluessel);
  // DIE ANTWORT AUF EINE SKIZZE GEHT VERLOREN: kein Erfolg, die Tafel bleibt stehen.
  const d = url === "/api/skizze" ? {fehler: "Die Antwort kam nicht an."}
          : url.startsWith("/api/fortschritt") ? {laeuft:false, fertige:[]}
          : url.startsWith("/api/projekt") ? sicht : {};
  return {json: async () => d};
}
const crypto = require("crypto").webcrypto;
const ctx = {document, fetch, crypto, setInterval:()=>1, clearInterval:()=>{}, console};
const api = new Function(...Object.keys(ctx), skript +
  ";\nreturn {zeichenStart, zeichenZug, zeichenEnde, skizzeAblegen, tafelGroesse, laden, tafel};")(
  ...Object.values(ctx));
const e = (x) => ({pointerId: 1, pointerType: "pen", pressure: 0.5, clientX: x, clientY: x,
                   preventDefault(){}});
const strich = (x) => { api.zeichenStart(e(x)); api.zeichenZug(e(x + 1)); api.zeichenEnde(e(x)); };
const tipp = (x) => { api.zeichenStart(e(x)); api.zeichenEnde(e(x)); };
// Das Bild unter der Tafel meldet sich (wie der Browser mit `load`).
const bildLaedt = (b, h) => { ids.unterlagenbild.naturalWidth = b; ids.unterlagenbild.naturalHeight = h;
                              api.tafelGroesse(); };
const aus = {};
(async () => {
  await new Promise(r => setTimeout(r, 30));          // das erste `laden` der Seite
  // WIE IM BROWSER: Eine Auswahlliste steht auf ihrer ersten Wahl (die Attrappe kennt
  // keine Optionen) — gewaehlt wird das erste Bild, und es meldet sich.
  const waehle = (name) => { ids.unterlage.value = name;
                             for (const f of ids.unterlage.listeners.change) f({}); };
  const [erstes, zweites] = sicht.bilder.map(b => b.bild);
  aus.start = ids.stand.textContent;                  // das erste `laden` kam durch
  waehle(erstes);
  bildLaedt(4, 4);
  // A · Ein Tipp ohne Strich aendert die Zeichnung nicht, und nicht ihren Schluessel.
  strich(1);
  await api.skizzeAblegen();                          // Antwort verloren
  tipp(3);
  await api.skizzeAblegen();                          // dieselbe Zeichnung noch einmal
  strich(5);
  await api.skizzeAblegen();                          // eine ergaenzte Zeichnung
  aus.a = gesendet.splice(0);
  // B · Die Mappe wird neu geladen (wie nach jedem Lauf): Die Zeichnung bleibt.
  const srcVorher = ids.unterlagenbild.srcGesetzt, geleertVorher = ids.tafel.geleert;
  await api.laden();
  aus.laden = ids.stand.textContent;
  bildLaedt(4, 4);                                    // meldet sich das Bild trotzdem
  aus.b = {src: ids.unterlagenbild.srcGesetzt - srcVorher, geleert: ids.tafel.geleert - geleertVorher,
           gezeichnet: api.tafel.gezeichnet, schluessel: api.tafel.schluessel};
  // C · Eine andere Groesse leert die Tafel — und die Seite weiss es.
  const schluesselVorher = api.tafel.schluessel;
  bildLaedt(8, 6);
  aus.c = {gezeichnet: api.tafel.gezeichnet, schluessel: api.tafel.schluessel, vorher: schluesselVorher,
           stiftlage: ids.stiftlage.textContent};
  await api.skizzeAblegen();                          // eine leere Tafel geht nicht hinaus
  aus.c.gesendet = gesendet.splice(0);
  aus.c.stand = ids.stand.textContent;
  // D · Eine andere Unterlage (gleiche Groesse) leert die Tafel ebenfalls.
  strich(2);
  const vorWechsel = api.tafel.gezeichnet;
  waehle(zweites);
  aus.d = {vorher: vorWechsel, gezeichnet: api.tafel.gezeichnet, schluessel: api.tafel.schluessel,
           src: ids.unterlagenbild.src};
  console.log(JSON.stringify(aus));
})().catch((f) => { console.log("AUSNAHME " + f.stack); });
"""


def _seite_fahren(tmp_path, dom: str, sicht: dict) -> str:
    node = _node()
    if node is None:
        pytest.skip("kein node im PATH — das Skript der Seite lässt sich hier nicht fahren")
    skript = re.search(r"<script>(.*)</script>", SEITE.read_text(encoding="utf-8"), re.S)
    (tmp_path / "seite.js").write_text(skript.group(1), encoding="utf-8")
    (tmp_path / "sicht.json").write_text(json.dumps(sicht), encoding="utf-8")
    (tmp_path / "dom.js").write_text(dom, encoding="utf-8")
    lauf = subprocess.run([node, str(tmp_path / "dom.js"), str(tmp_path / "seite.js"),
                           str(tmp_path / "sicht.json")],
                          capture_output=True, text=True, timeout=60)
    assert lauf.returncode == 0, lauf.stderr
    assert not lauf.stdout.startswith("AUSNAHME"), lauf.stdout
    return lauf.stdout


@pytest.fixture(scope="module")
def tafellauf(server, tmp_path_factory):
    """Die Seite gegen eine **echte** Sicht mit zwei Bildern gleicher Grösse — sonst kommt
    ``laden`` nicht bis zur Tafel (eine unvollständige Sicht wirft vorher, und die Probe
    prüfte das Neuladen gar nicht)."""
    wurzel = tmp_path_factory.mktemp("tafel")
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = wurzel / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    mappe = wurzel / "projekt"
    arbeitsgang.lege_an(mappe, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y",
                                       "qa": False})
    for startwert in (7, 8):                           # zwei Läufe, zwei Bilder
        arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(_Modell()), seed=startwert)
    sicht = _sicht(server, mappe)
    assert len(sicht["bilder"]) == 2
    (wurzel / "seite").mkdir()
    aus = json.loads(_seite_fahren(wurzel / "seite", _DOM, sicht))
    aus["namen"] = [b["bild"] for b in sicht["bilder"]]
    return aus


def test_die_tafelprobe_kommt_durch_das_laden(tafellauf):
    """Die Probe selbst: Beide Male lief ``laden`` bis zum Ende (sonst stünde dort ein
    Fehlersatz, und «nichts geleert» hiesse nur «nichts versucht»)."""
    assert re.fullmatch(r"2 Bilder, \d+ Läufe", tafellauf["start"]), tafellauf["start"]
    assert re.fullmatch(r"2 Bilder, \d+ Läufe", tafellauf["laden"]), tafellauf["laden"]


def test_ein_tipp_ohne_strich_gibt_keinen_neuen_schluessel(tafellauf):
    """Bis zum 22.09.2026 verwarf schon das Aufsetzen den Schlüssel: Ein Tipp ohne Strich
    liess dieselbe Zeichnung als neue hinausgehen — mit einer zweiten Datei drüben."""
    erster, nach_tipp, ergaenzt = tafellauf["a"]
    assert erster and nach_tipp == erster, "ein Tipp ist kein Strich"
    assert ergaenzt and ergaenzt != erster, "ein Strich ist eine neue Zeichnung"


def test_ein_neues_laden_der_mappe_loescht_die_zeichnung_nicht(tafellauf):
    """Nach jedem Lauf lädt die Seite die Mappe neu. Das setzte das Bild unter der Tafel
    neu, das meldete sich, und die Leinwand bekam ihre (gleiche) Grösse neu gesetzt —
    und war leer, ohne dass die Seite es wusste."""
    b = tafellauf["b"]
    assert b["src"] == 0, "dasselbe Bild wird nicht neu gesetzt"
    assert b["geleert"] == 0, "dieselbe Grösse leert die Tafel nicht"
    assert b["gezeichnet"] is True and b["schluessel"]


def test_eine_neue_groesse_leert_die_tafel_und_die_seite_weiss_es(tafellauf):
    """Die alte Lücke: ``tafelGroesse`` leerte die Leinwand, liess aber ``gezeichnet`` und
    den Schlüssel stehen — «In die Mappe legen» schickte dann eine leere Tafel unter dem
    Schlüssel der verlorenen Zeichnung."""
    c = tafellauf["c"]
    assert c["vorher"], "vor dem Wechsel gab es einen Schlüssel"
    assert c["gezeichnet"] is False and c["schluessel"] is None
    assert c["stiftlage"] == "Noch kein Strich gezeichnet."
    assert c["gesendet"] == [], "eine leere Tafel geht nicht hinaus"
    assert c["stand"] == "Es ist nichts gezeichnet."


def test_eine_andere_unterlage_gleicher_groesse_leert_die_tafel(tafellauf):
    """Eine Zeichnung gehört zu dem Bild, auf das sie gezeichnet wurde. Bei gleicher
    Grösse leert keine neue Grösse mehr die Tafel — also tut es der Wechsel selbst."""
    d = tafellauf["d"]
    assert d["vorher"] is True, "vor dem Wechsel war gezeichnet"
    assert (d["gezeichnet"], d["schluessel"]) == (False, None)
    assert d["src"].endswith("name=" + urllib.parse.quote(tafellauf["namen"][1], safe="")), \
        "und die neue Unterlage liegt darunter"


_WISCH = r"""
const skript = require("fs").readFileSync(process.argv[2], "utf8");
const sicht = JSON.parse(require("fs").readFileSync(process.argv[3], "utf8"));
""" + _EL + r"""
const ids = {};
const document = { hidden:false, getElementById:(id)=>ids[id]||(ids[id]=new El("div")), createElement:(t)=>new El(t),
  createTextNode:(t)=>Object.assign(new El("#text"),{_text:t}), querySelectorAll:()=>[] };
async function fetch(url) {
  const d = url.startsWith("/api/projekt") ? sicht : {laeuft:false, fertige:[]};
  return {json: async () => d};
}
const crypto = require("crypto").webcrypto;
const ctx = {document, fetch, crypto, setInterval:()=>1, clearInterval:()=>{}, console};
new Function(...Object.keys(ctx), skript)(...Object.values(ctx));
(async () => {
  await new Promise(r => setTimeout(r, 30));
  const bilder = ids["bilder"];
  const knoepfe = bilder.alle(c => c.tagName === "BUTTON" && c.textContent === "Wischregler");
  knoepfe[0].klick();
  const deck = bilder.alle(c => c.classList && c.classList.contains("deck"))[0];
  const satz = bilder.alle(c => c.classList && c.classList.contains("satz"))
                     .map(c => c.textContent).filter(t => t.startsWith("Links dieses Bild"));
  const titel = bilder.alle(c => c.classList && c.classList.contains("titel")).map(c => c.textContent);
  console.log(JSON.stringify({knoepfe: knoepfe.length, oben: deck ? deck.children[0].src : null,
                              satz, text: bilder.textContent}));
})().catch((f) => { console.log("AUSNAHME " + f.stack); });
"""


def test_der_wischregler_der_seite_nimmt_das_vorher(server, mappe, tmp_path):
    """Über eine **echte** Sicht (Server aus einer Mappe): Das Skizzenbild zeigt im
    Wischregler das Bild, über das skizziert wurde — nicht mehr die Zeichnung allein. Und
    der Satz zur Streckung steht in der Karte."""
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-r.png", {}, ueber=unterlage, breite=6, hoehe=4)
    arbeitsgang.rechne_skizze(mappe, "skizze-r.png", ausfuehrer=_tabelle(_Modell()))
    sicht = _sicht(server, mappe)
    (b,) = [x for x in sicht["bilder"] if (x.get("herkunft") or {}).get("skizze")]
    assert b["vorher"] == unterlage

    aus = json.loads(_seite_fahren(tmp_path, _WISCH, sicht))

    assert aus["knoepfe"] == 1, "nur das Skizzenbild hat ein Vorher"
    assert aus["oben"] and "name=" + urllib.parse.quote(unterlage, safe="") in aus["oben"]
    assert "skizze-r.png" not in aus["oben"]
    assert aus["satz"] and "das Bild, auf das skizziert wurde" in aus["satz"][0]
    assert "GESTRECKT" in aus["text"]


# ======================================================================================
# 7 · Der Name der App, überall aus der Konstante
# ======================================================================================

def test_die_abweisung_nennt_den_namen_aus_der_konstante(server, monkeypatch):
    """**An der Wirkung:** Heisst die App anders, heissen Satz, Bereich und Kopf ``Server``
    der Abweisung mit — und nichts vom alten Namen bleibt stehen."""
    alt = server.NAME
    monkeypatch.setattr(server, "NAME", 'Probe "Name"')
    a = _Anfrage(server, weg="/api/projekt", kennwort="geheim")
    assert a.codes == [401]
    assert "in dem Probe \"Name\" gestartet wurde" in a.daten["fehler"]
    assert a.koepfe["WWW-Authenticate"] == 'Basic realm="Probe \\"Name\\"", charset="UTF-8"'
    assert a.selbst.version_string().startswith('Probe "Name"')
    assert alt not in a.daten["fehler"] + a.koepfe["WWW-Authenticate"]


@pytest.mark.parametrize("adresse", ["127.0.0.1", "0.0.0.0"])
def test_die_startzeile_nennt_den_namen_aus_der_konstante(server, monkeypatch, adresse):
    alt = server.NAME
    monkeypatch.setattr(server, "NAME", "Probename")
    zeile = server.startzeile(adresse, 8731)
    assert zeile.startswith("Probename läuft auf")
    assert alt not in zeile


def test_kein_satz_des_servers_nennt_den_namen_fest(server):
    """**Eine Abwesenheit — darum am Text.** Keine Zeichenkette in ``server.py`` enthält den
    Namen der App (ausser als Teil eines Pfads zum App-Paket). So fallen auch die Sätze,
    die nur beim Start gedruckt werden, und die hier keine Probe fährt."""
    name = server.NAME
    baum = ast.parse((FLAECHE / "server.py").read_text(encoding="utf-8"))
    funde = [k.value for k in ast.walk(baum)
             if isinstance(k, ast.Constant) and isinstance(k.value, str)
             and name in k.value.replace(f"{name}.swiftpm", "").replace(f"{name}Kern", "")]
    assert funde == []
