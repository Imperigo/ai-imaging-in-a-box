"""Die Mängel der Durchsichten D-KERN und D-SERVER (Welle 1, 22.09.2026) — **an der
Wirkung** geprüft, jeder mit dem Befund, den er festhält.

1. **Ein Name während eines Laufs** (und eine Skizze während eines Laufs): Der Lauf
   speicherte am Ende auf seinem alten Stand, ``speichere`` warf ``ProjektKollision``,
   und **alle Vermerke des Laufs fehlten**. Nachgestellt mit einer Sonde, die mitten im
   Lauf benennt. Jetzt holt der Lauf den fremden Stand nach.
2. **Score ohne Urteil**: ``bestanden=None`` mit Score stand am Bild wie eine Messung.
3. **Unicode-Zeilentrenner** im Namen (U+2028, U+2029, U+0085) kamen durch.
4. **Abbruch während des letzten Knotens einer Variante**: Die nächste begann trotzdem.
5. **Die Fläche rief private Funktionen** des Arbeitsgangs.
6. **Die Zahl im Prüfzeichen** der Webseite: bis sechs Nachkommastellen — 0.7999999 gegen
   0.8 zeigte Gleichstand. **Der Schlüssel der Skizze** galt bis zum Leeren der Tafel.
7. **Die Koppelseite**: ein Satz, der im Browser nicht stimmt, und der Name der App fest
   eingeschrieben.

Ohne GPU, ohne Blender. Regel 3: alles hier entsteht aus ein paar Bytes.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import socket
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, kopplung, projekt
from aiimaging.kette import ART_GEOMETRIE, ART_MULTIPASS, ART_QA, ART_RENDER, KNOTEN_RENDER

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"
MARKE = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Marke.swift"


# ======================================================================================
# Werkzeug
# ======================================================================================

def _png(pfad, werte=(0, 64, 128, 255)) -> Path:
    roh = b"".join(b"\x00" + bytes(werte[z * 2:(z + 1) * 2]) for z in range(2))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(roh)) + block(b"IEND", b""))
    return pfad


class Werkbank:
    """Attrappen für die vier Stufen. ``waehrend_render``/``waehrend_qa`` sind Sonden:
    Sie laufen **mitten im Lauf**, an der Stelle, an der sonst die GPU rechnet."""

    def __init__(self, *, qa_antwort=None, waehrend_render=None, waehrend_qa=None):
        self.qa_antwort = qa_antwort
        self.waehrend_render = waehrend_render
        self.waehrend_qa = waehrend_qa
        self.render_seeds: list[int] = []

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [8, 5, 3]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": str(_png(Path(out_dir) / "tiefe_norm.png")),
                "beauty_png": str(_png(Path(out_dir) / "beauty.png", (5, 5, 5, 5)))}

    def render(self, *, knoten, eingaben, out_dir):
        self.render_seeds.append(knoten.params["seed"])
        if self.waehrend_render is not None:
            self.waehrend_render()
        s = knoten.params["seed"] % 250
        return {"status": "ok", "bild_png": str(_png(Path(out_dir) / "bild.png", (s, s, 1, 2)))}

    def qa(self, *, knoten, eingaben, out_dir):
        if self.waehrend_qa is not None:
            self.waehrend_qa()
        if self.qa_antwort is not None:
            return dict(self.qa_antwort)
        return {"status": "ok", "bestanden": True, "score": 0.8123,
                "schwelle": knoten.params["schwelle"], "begruendung": "Attrappe."}


@pytest.fixture
def mappe(tmp_path):
    """Eine Mappe mit durchgereichter glb — ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


def _neu(wurzel) -> dict:
    """Die Mappe, **frisch von der Platte** — nicht der Rückgabewert."""
    return projekt.oeffne(wurzel)["projekt"]


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


def _node():
    return shutil.which("node")


# ======================================================================================
# 1 · Wer während eines Laufs schreibt, nimmt dem Lauf nichts weg
# ======================================================================================

def test_ein_name_waehrend_des_laufs_und_die_vermerke_des_laufs_bleiben_beide(mappe):
    """**Die Sonde der Durchsicht, nachgestellt:** Ein Bild liegt in der Mappe; ein
    zweiter Lauf rechnet; mitten darin benennt das iPad das Bild. Bis zum 22.09.2026
    warf der Lauf am Ende ``ProjektKollision``, und sein Lauf- und Bildvermerk fehlten."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    (bild,) = _neu(mappe)["bilder"]

    def benennen():
        projekt.benenne(mappe, bild=bild["bild"], titel="Südansicht")

    ergebnis = arbeitsgang.rechne(
        mappe, ausfuehrer=Werkbank(waehrend_render=benennen).tabelle(), cache=None)

    p = _neu(mappe)
    assert len(p["laeufe"]) == 2, "der Lauf steht in der Mappe"
    assert ergebnis["vermerkt"] == 1
    (eintrag,) = [b for b in p["bilder"] if b["bild"] == bild["bild"]]
    assert eintrag["titel"] == "Südansicht", "der Name des anderen bleibt"
    assert eintrag["zuletzt_vermerkt"] >= bild["zuletzt_vermerkt"]
    assert ergebnis["projekt"]["stand_nr"] == p["stand_nr"], \
        "zurück kommt der gespeicherte Stand, nicht der überholte"


def test_eine_skizze_waehrend_des_laufs_und_die_vermerke_des_laufs_bleiben_beide(mappe):
    """Derselbe Fehler auf dem häufigeren Weg: Wer wartet, zeichnet. Die Fläche legt die
    Skizze ab (öffnen, vermerken, speichern), während der Lauf rechnet."""
    def ablegen():
        _png(mappe / "skizze-waehrenddessen.png")
        p = _neu(mappe)
        projekt.vermerke_skizze(p, skizze="skizze-waehrenddessen.png", bemerkung="Vordach")
        projekt.speichere(p, mappe)

    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank(waehrend_qa=ablegen).tabelle())

    p = _neu(mappe)
    assert [s["skizze"] for s in p["skizzen"]] == ["skizze-waehrenddessen.png"]
    assert len(p["laeufe"]) == 1 and len(p["bilder"]) == 1


def test_wer_dauernd_dazwischen_schreibt_bekommt_die_kollision(mappe, monkeypatch):
    """Nachgeholt wird höchstens ``NACHHOLEN_HOECHSTENS``-mal. Ein Schreiber, der jedes Mal
    zwischen Öffnen und Speichern trifft, bekommt die Kollision gemeldet — keine
    Endlosschleife."""
    echt = projekt.speichere
    versuche = []

    def dazwischen(p, wurzel):
        if p.get("laeufe"):                        # nur die Speicherungen des Laufs
            versuche.append(1)
            fremd = projekt.oeffne(wurzel)["projekt"]
            echt(fremd, wurzel)                    # jemand anderes war schneller
        return echt(p, wurzel)

    monkeypatch.setattr(projekt, "speichere", dazwischen)
    with pytest.raises(projekt.ProjektKollision):
        arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    assert len(versuche) == arbeitsgang.NACHHOLEN_HOECHSTENS


# ======================================================================================
# 2 · Eine Zahl ohne Urteil steht nicht am Bild
# ======================================================================================

def test_ein_score_ohne_urteil_steht_in_der_herkunft_und_nicht_am_bild(mappe):
    """Fehlt der Maskenweg, rechnet die Prüfung und urteilt nicht (``bestanden=None``),
    meldet aber ihren Score. Am Bild stand er bis zum 22.09.2026 unter ``score`` — neben
    «nicht gemessen» eine Zahl, die sich wie eine Messung liest."""
    antwort = {"status": "ok", "bestanden": None, "score": 0.91, "schwelle": 0.65,
               "begruendung": "Score 0.910 ≥ Schwelle 0.65, ohne Maske."}
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank(qa_antwort=antwort).tabelle())

    (bild,) = _neu(mappe)["bilder"]
    assert bild["geometrie_bestanden"] is None
    assert bild["score"] is None and bild["schwelle"] is None
    assert bild["herkunft"]["messung"]["score"] == pytest.approx(0.91)
    assert bild["herkunft"]["messung"]["schwelle"] == pytest.approx(0.65)
    lauf = _neu(mappe)["laeufe"][-1]
    assert "score" not in lauf["messungen"][KNOTEN_RENDER], \
        "im Lauf steht, was die Bildstufe gemessen hat — nicht die Prüfung"


def test_mit_urteil_steht_die_zahl_am_bild_und_in_der_herkunft(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), qa_schwelle=0.7)
    (bild,) = _neu(mappe)["bilder"]
    assert bild["geometrie_bestanden"] is True
    assert bild["score"] == pytest.approx(0.8123)
    assert bild["herkunft"]["messung"]["score"] == pytest.approx(0.8123)


def test_vermerke_bild_weist_eine_zahl_ohne_urteil_ab():
    p = {"bilder": []}
    with pytest.raises(projekt.ProjektError, match="ohne Urteil"):
        projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", urteil=None,
                              score=0.9, schwelle=0.65)
    assert p["bilder"] == []


def test_die_sicht_zeigt_keine_zahl_ohne_urteil_auch_aus_einer_alten_mappe(server):
    """Eine Mappe aus der Zeit vor der Regel kann die Zahl noch tragen."""
    alt = {"bild": "a.png", "schicht": "geometrielayer", "geometrie_bestanden": None,
           "score": 0.91, "schwelle": 0.65, "herkunft": {"grund": "NICHT GEMESSEN."}}
    sicht = server._bild_fuer_die_flaeche(alt)
    assert sicht["zeichen"] == "nicht-gemessen"
    assert sicht["score"] is None and sicht["schwelle"] is None
    mit = server._bild_fuer_die_flaeche(dict(alt, geometrie_bestanden=False))
    assert mit["score"] == pytest.approx(0.91)


# ======================================================================================
# 3 · Ein Name steht auf einer Zeile — auch nach Unicode
# ======================================================================================

@pytest.mark.parametrize("trenner", [" ", " ", "\u0085", "\u009b"],
                         ids=["zeilentrenner", "absatztrenner", "zeilenende-c1",
                              "steuerzeichen-c1"])
def test_ein_unicode_zeilentrenner_im_namen_wird_abgewiesen(mappe, trenner):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    (bild,) = _neu(mappe)["bilder"]
    stand = _neu(mappe)["stand_nr"]

    with pytest.raises(projekt.ProjektError, match="Zeilen- oder Absatztrenner"):
        projekt.benenne(mappe, bild=bild["bild"], titel=f"Süd{trenner}ansicht")

    assert _neu(mappe)["stand_nr"] == stand, "abgewiesen heisst: nichts geschrieben"
    assert _neu(mappe)["bilder"][0]["titel"] is None


def test_ein_gewoehnlicher_name_mit_umlauten_und_zeichen_geht_durch(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    (bild,) = _neu(mappe)["bilder"]
    projekt.benenne(mappe, bild=bild["bild"], titel="Süd · Abend — «Variante 2»")
    assert _neu(mappe)["bilder"][0]["titel"] == "Süd · Abend — «Variante 2»"


# ======================================================================================
# 4 · Ein Klick während des letzten Knotens hält auch die Reihe an
# ======================================================================================

def test_ein_klick_waehrend_des_letzten_knotens_beginnt_keine_neue_variante(mappe):
    """Die Prüfung ist der letzte Knoten jeder Variante. Kommt der Klick, während sie
    rechnet, läuft Variante 1 regulär zu Ende — und bis zum 22.09.2026 begann Variante 2
    trotzdem, angehalten erst vor ihrem ersten Knoten, mit einem leeren Lauf."""
    angehalten = {"ja": False}
    werk = Werkbank(waehrend_qa=lambda: angehalten.update(ja=True))
    ereignisse = []

    ergebnis = arbeitsgang.rechne(
        mappe, ausfuehrer=werk.tabelle(), varianten=3, cache=None,
        abbrechen=lambda: angehalten["ja"], melder=ereignisse.append)

    assert werk.render_seeds == [7], "keine weitere Variante"
    assert ergebnis["abgebrochen"] is True
    assert ergebnis["varianten_nicht_begonnen"] == 2
    assert [e["nummer"] for e in ereignisse if e.get("art") == "variante_beginnt"] == [1]
    (lauf,) = _neu(mappe)["laeufe"]
    assert lauf["abgebrochen"] is False, "die Variante selbst lief zu Ende"
    assert lauf["varianten_nicht_begonnen"] == 2, "die Mappe sagt, dass die Reihe endete"
    assert len(_neu(mappe)["bilder"]) == 1


def test_ohne_abbruch_laeuft_die_reihe_ganz_und_zaehlt_null(mappe):
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), varianten=2,
                                  abbrechen=lambda: False)
    assert ergebnis["abgebrochen"] is False
    assert [l["varianten_nicht_begonnen"] for l in _neu(mappe)["laeufe"]] == [0, 0]


def test_ein_einzelner_lauf_fuehrt_keine_variantenzahl(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())
    assert _neu(mappe)["laeufe"][-1]["varianten_nicht_begonnen"] is None


# ======================================================================================
# 5 · Was die Fläche vom Arbeitsgang ruft, ist öffentlich
# ======================================================================================

def test_was_die_flaeche_ruft_steht_in_der_oeffentlichen_liste():
    for name in ("pruefe_varianten", "entwurfsargumente", "VARIANTEN_ARTEN",
                 "SKIZZEN_VORSATZ"):
        assert name in arbeitsgang.__all__, name
        assert hasattr(arbeitsgang, name), name


def test_die_flaeche_ruft_keine_private_funktion_des_arbeitsgangs():
    """Eine Abwesenheit — darum am Text. Ein Aufruf unter privatem Namen bricht still,
    sobald der Arbeitsgang umgebaut wird."""
    quelle = (FLAECHE / "server.py").read_text(encoding="utf-8")
    assert re.findall(r"arbeitsgang\._\w+", quelle) == []


def test_eine_falsche_reihe_wird_ueber_die_oeffentliche_pruefung_abgewiesen():
    with pytest.raises(arbeitsgang.ArbeitsgangError):
        arbeitsgang.pruefe_varianten(arbeitsgang.VARIANTEN_HOECHSTENS + 1,
                                     arbeitsgang.VARIANTEN_STARTWERTE)
    args = arbeitsgang.entwurfsargumente({"schritte": 30}, {})
    assert args["qa"] is False and args["schritte"] == arbeitsgang.ENTWURF_SCHRITTE


# ======================================================================================
# 6 · Die Seite: nie Gleichstand, und ein neuer Strich ist eine neue Zeichnung
# ======================================================================================

def _zahltext(paare) -> list:
    node = _node()
    if node is None:
        pytest.skip("kein node im PATH — die Funktion der Seite lässt sich hier nicht fahren")
    funktion = re.search(r"\nfunction zahlText\(.*?\n}\n", SEITE.read_text(encoding="utf-8"),
                         re.S)
    assert funktion, "zahlText steht nicht mehr in der Seite"
    skript = (funktion.group(0) + "\nconst paare = " + json.dumps(paare) + ";\n"
              "console.log(JSON.stringify(paare.map(([a, b]) => zahlText(a, b))));\n")
    lauf = subprocess.run([node, "-e", skript], capture_output=True, text=True, timeout=30)
    assert lauf.returncode == 0, lauf.stderr
    return json.loads(lauf.stdout)


@pytest.mark.parametrize("score,schwelle,erwartet", [
    (0.7999999, 0.8, ("0.7999999", "0.8000000")),
    (0.7999999999999999, 0.8, ("0.7999999999999999", "0.8000000000000000")),
    (0.8000001, 0.8, ("0.8000001", "0.8000000")),
])
def test_bis_siebzehn_stellen_zeigt_die_seite_nie_gleichstand(score, schwelle, erwartet):
    (r,) = _zahltext([[score, schwelle]])
    assert (r["score"], r["schwelle"]) == erwartet


def test_zwei_verschiedene_zahlen_sehen_nie_gleich_aus():
    """Nachbarn im Gleitkommaraster um typische Schwellen — die engsten Fälle, die es
    gibt. Verschieden bleibt verschieden, und gleich bleibt gleich."""
    import math
    paare = []
    for schwelle in (0.5, 0.65, 0.7, 0.8, 0.95, 1.0):
        for score in (math.nextafter(schwelle, 0), math.nextafter(schwelle, 2),
                      schwelle - 1e-9, schwelle + 1e-12):
            paare.append([score, schwelle])
        paare.append([schwelle, schwelle])
    for (score, schwelle), r in zip(paare, _zahltext(paare)):
        if score == schwelle:
            assert r["score"] == r["schwelle"]
        else:
            assert r["score"] != r["schwelle"], (score, schwelle, r)
            assert (float(r["score"]) < float(r["schwelle"])) == (score < schwelle), \
                "die Reihenfolge kehrt sich nie um"


_TAFEL = r"""
const skript = require("fs").readFileSync(process.argv[2], "utf8");
class El { constructor(){ this.children=[]; this.style={}; this.dataset={}; this.value="";
  this.textContent=""; this.hidden=false; this.width=0; this.height=0; this.naturalWidth=0;
  this.classList={add(){},remove(){},toggle(){},contains(){return false;}}; }
  addEventListener(){} append(){} replaceChildren(){} setPointerCapture(){}
  getBoundingClientRect(){ return {left:0, top:0, width:10, height:10}; }
  getContext(){ return new Proxy({}, {get:()=>()=>{}, set:()=>true}); }
  toDataURL(){ return "data:image/png;base64,AAAA"; } }
const ids = {};
const document = { hidden:false, getElementById:(id)=>ids[id]||(ids[id]=new El()),
  createElement:()=>new El(), createTextNode:()=>new El(), querySelectorAll:()=>[] };
ids.tafel = new El(); ids.tafel.width = 10; ids.tafel.height = 10;
const gesendet = [];
async function fetch(url, opt) {
  if (url === "/api/skizze") gesendet.push(JSON.parse(opt.body).schluessel);
  // DIE ANTWORT GEHT VERLOREN: kein Erfolg, die Tafel bleibt stehen.
  const d = url === "/api/skizze" ? {fehler: "Die Antwort kam nicht an."}
          : url.startsWith("/api/fortschritt") ? {laeuft:false, fertige:[]}
          : {fehler: "keine Mappe"};
  return {json: async () => d};
}
const crypto = require("crypto").webcrypto;
const api = new Function("document", "fetch", "crypto", "setInterval",
  skript + ";\nreturn {zeichenStart, zeichenZug, zeichenEnde, skizzeAblegen};")(
  document, fetch, crypto, () => 1);
const strich = (x) => {
  const e = {pointerId: 1, pointerType: "pen", pressure: 0.5, clientX: x, clientY: x,
             preventDefault(){}};
  api.zeichenStart(e); api.zeichenZug(Object.assign({}, e, {clientX: x + 1}));
  api.zeichenEnde(e);
};
(async () => {
  strich(1);
  await api.skizzeAblegen();          // Antwort verloren
  await api.skizzeAblegen();          // derselbe Klick noch einmal, ohne neuen Strich
  strich(5);                          // weitergezeichnet
  await api.skizzeAblegen();
  console.log(JSON.stringify(gesendet));
})().catch((f) => { console.log("AUSNAHME " + f.stack); });
"""


def test_ein_neuer_strich_bekommt_einen_neuen_schluessel(tmp_path):
    """**Die Wirkung, gefahren in node:** Dieselbe Zeichnung zweimal geschickt trägt
    denselben Schlüssel (kein zweites Bild), eine ergänzte Zeichnung einen neuen. Bis zum
    22.09.2026 trug auch die ergänzte den alten — und der Server wies sie als «andere
    Zeichnung mit demselben Schlüssel» ab."""
    node = _node()
    if node is None:
        pytest.skip("kein node im PATH — das Skript der Seite lässt sich hier nicht fahren")
    skript = re.search(r"<script>(.*)</script>", SEITE.read_text(encoding="utf-8"), re.S)
    (tmp_path / "seite.js").write_text(skript.group(1), encoding="utf-8")
    (tmp_path / "tafel.js").write_text(_TAFEL, encoding="utf-8")
    lauf = subprocess.run([node, str(tmp_path / "tafel.js"), str(tmp_path / "seite.js")],
                          capture_output=True, text=True, timeout=60)
    assert lauf.returncode == 0, lauf.stderr
    assert not lauf.stdout.startswith("AUSNAHME"), lauf.stdout
    erster, wiederholt, ergaenzt = json.loads(lauf.stdout)
    assert erster and erster == wiederholt, "ohne neuen Strich bleibt der Schlüssel"
    assert ergaenzt and ergaenzt != erster, "ein neuer Strich ist eine neue Zeichnung"


# ======================================================================================
# 7 · Die Koppelseite: der Name aus der Marke, und nur Sätze, die im Browser stimmen
# ======================================================================================

class _Anfrage:
    """Eine ganze Anfrage an ``Flaeche`` — ``do_GET``/``do_POST`` laufen wirklich (dieselbe
    Bauform wie in ``tests/test_flaeche_fuer_die_app.py``; Probedateien importieren
    einander nicht)."""

    def __init__(self, modul, *, befehl, weg, offen, rumpf=None, kennwort="geheim"):
        rumpf = json.dumps(rumpf).encode("utf-8") if rumpf is not None else b""
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": None, "kopplung_offen": offen})
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": None, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda *a: None
        self.selbst.end_headers = lambda: None
        (self.selbst.do_GET if befehl == "GET" else self.selbst.do_POST)()

    @property
    def text(self) -> str:
        return self.selbst.wfile.getvalue().decode("utf-8")


def _marke_name() -> str:
    zeilen = [z for z in MARKE.read_text(encoding="utf-8").splitlines()
              if not z.lstrip().startswith("//")]
    return re.search(r'static let name\s*=\s*"([^"]+)"', "\n".join(zeilen)).group(1)


def test_der_name_der_flaeche_ist_der_der_app(server):
    assert server.NAME == _marke_name()


def test_die_koppelseite_nennt_den_namen_aus_der_konstante(server, monkeypatch):
    """**An der Wirkung:** Heisst die App anders, heisst die Koppelseite mit — und nichts
    vom alten Namen bleibt stehen."""
    monkeypatch.setattr(server, "NAME", "Probename <&>")
    seite = _Anfrage(server, befehl="GET", weg=server.WEG_KOPPELN,
                     offen=kopplung.eroeffne(_pin="123456")).text
    assert "<title>Probename &lt;&amp;&gt; — Gerät verbinden</title>" in seite
    assert "in dem Probename &lt;&amp;&gt; auf dem Rechner" in seite
    assert _marke_name() not in seite
    assert "__NAME__" not in seite


def test_die_koppelseite_sagt_nicht_dass_sich_das_geraet_etwas_merkt(server):
    """Im Browser stimmte «Dieses Gerät merkt sich die Anmeldung» nicht: Der Browser
    merkt sich nichts, was ihm niemand zu merken gibt. Weder die Seite noch der Satz, den
    sie nach dem Verbinden zeigt, behaupten es."""
    offen = kopplung.eroeffne(_pin="654321")
    seite = _Anfrage(server, befehl="GET", weg=server.WEG_KOPPELN, offen=offen).text
    antwort = _Anfrage(server, befehl="POST", weg=server.WEG_VERBINDEN, offen=offen,
                       rumpf={"pin": "654321"})
    assert antwort.codes == [200]
    satz = json.loads(antwort.text)["satz"]
    for text in (seite, satz):
        assert "merkt sich die Anmeldung" not in text
    assert "nur dieses eine Mal" in satz
    assert "nur dieses eine Mal" in seite


# ======================================================================================
# 8 · Der Rundruf neben einem fremden Dienst: was geprüft ist, und was er ihm wegnimmt
# ======================================================================================

@pytest.fixture(scope="module")
def rundruf():
    sys.path.insert(0, str(FLAECHE))
    try:
        import rundruf as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


#: Wie viele verschiedene Absender je Probe fragen. Unter SO_REUSEPORT verteilt Linux
#: direkte Pakete nach Absender; mit zwanzig ist «alle beim selben» ausgeschlossen
#: (Wahrscheinlichkeit 2 hoch -19).
ABSENDER = 20


def _direkt_fragen(rundruf, option) -> tuple[int, int]:
    """Ein fremder Dienst bindet zuerst (mit ``option``), der Rundruf danach an denselben
    Anschluss. Zwanzig Absender fragen direkt. ``(beim_rundruf, beim_fremden)``."""
    import time
    angabe = rundruf.Dienstangabe(anschluss=8731, adresse="192.0.2.10",
                                  rechnername="Probe Rechner")
    fremd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    absender = []
    try:
        fremd.setsockopt(socket.SOL_SOCKET, getattr(socket, option), 1)
        fremd.bind(("127.0.0.1", 0))
        fremd.settimeout(0.3)
        r = rundruf.Rundruf(angabe, bindung=fremd.getsockname(), gruppe=False).starte()
        try:
            for _ in range(ABSENDER):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                absender.append(s)
                s.sendto(rundruf.baue_anfrage("_visbox._tcp.local", 12, kennung=7),
                         r.gebunden)
            beim_fremden = 0
            try:
                while True:
                    fremd.recvfrom(9000)
                    beim_fremden += 1
            except socket.timeout:
                pass
            ende = time.monotonic() + 3
            while r.beantwortet + beim_fremden < ABSENDER and time.monotonic() < ende:
                time.sleep(0.02)
            return r.beantwortet, beim_fremden
        finally:
            r.beende()
    finally:
        for s in absender:
            s.close()
        fremd.close()


def test_setzt_der_fremde_nur_reuseaddr_bekommt_er_kein_direktes_paket(rundruf):
    """**Hält den Befund der Durchsicht D-SERVER fest** (22.09.2026, hier nachgefahren),
    auf den sich der Modulkopf von ``rundruf.py`` und das Protokoll §8 stützen: Setzt
    der fremde Dienst nur ``SO_REUSEADDR``, landet **jedes** direkt an den Anschluss
    geschickte Paket beim zuletzt gebundenen Socket — dem Rundruf. Ändert das
    Betriebssystem das, fällt diese Probe, und die Sätze dort sind nachzuziehen. Über
    Pakete an die Rundruf-Gruppe sagt sie nichts."""
    beim_rundruf, beim_fremden = _direkt_fragen(rundruf, "SO_REUSEADDR")
    assert (beim_rundruf, beim_fremden) == (ABSENDER, 0)


def test_setzt_der_fremde_reuseport_teilen_sich_beide_die_direkten_pakete(rundruf):
    """Mit ``SO_REUSEPORT`` auf beiden Seiten verteilt Linux direkte Pakete **nach
    Absender** auf die beiden Sockets: Der fremde Dienst bekommt einen Teil, nicht alle.
    (Die Sonde der Durchsicht fragte von einem einzigen Absender und sah darum 20 von 20
    beim Rundruf — nachgefahren mit zwanzig Absendern, 22.09.2026.)"""
    if not hasattr(socket, "SO_REUSEPORT"):
        pytest.skip("SO_REUSEPORT gibt es auf diesem System nicht")
    beim_rundruf, beim_fremden = _direkt_fragen(rundruf, "SO_REUSEPORT")
    assert beim_rundruf + beim_fremden == ABSENDER
    assert 0 < beim_fremden < ABSENDER, "der fremde Dienst bekommt einen Teil, nicht alle"
