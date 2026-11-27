"""A0838 «Abbruch trifft eigenen Lauf» — **ein Abbruch hält nur den Lauf an, den die Seite sah.**

Befund V6 des externen Audits (24.11.2026, Zeile «global cancel from Beta view»): Die Seite
schickte beim Abbruch ``{}``, und der Server hielt an, was gerade lief. Endete Lauf A und
begann Lauf B (vom iPad, aus einer anderen Mappe), traf ein verspäteter Druck auf «Lauf
abbrechen» den Lauf B — einen Lauf, den der Mensch am Knopf nie gesehen hatte.

Seither trägt jeder Lauf eine Kennung (``Laufstand``), ``/api/fortschritt`` nennt sie mit
der Mappe (nur der Name, kein Plattenpfad), die Seite schickt beide mit, und der Server
bricht nur ab, wenn die Kennung stimmt; sonst 409 mit einem Satz, der die Mappe nennt.

**Übergang:** ein Abbruch ohne Kennung (``{}``, heute das iPad) wirkt bis A0840 wie bisher,
und die Antwort sagt es.

Ohne GPU, ohne Blender, ohne Netz; die Seite wird mit ``node`` gefahren (Muster
``tests/test_durchsicht_kern_server.py``). Regel 3: nur erfundene Mappennamen.
"""
from __future__ import annotations

import base64
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture(autouse=True)
def eigener_laufstand(server, monkeypatch):
    """Jede Probe bekommt ihren eigenen Laufstand; ein Lauf aus einer anderen Probe machte
    den Befund zum Zufall."""
    monkeypatch.setattr(server, "LAUFSTAND", server.Laufstand())


class _Anfrage:
    """Eine ganze Anfrage an ``Flaeche`` — ``do_GET``/``do_POST`` laufen wirklich, angemeldet.

    Dieselbe Bauform wie in ``tests/test_flaeche_fuer_die_app.py``; sie steht hier ein
    weiteres Mal, weil Probedateien einander nicht importieren.
    """

    def __init__(self, modul, *, befehl, weg, rumpf=None, kennwort="geheim"):
        rumpf = json.dumps(rumpf).encode("utf-8") if rumpf is not None else b""
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": None, "kopplung_offen": None})
        kopf = "Basic " + base64.b64encode(f"{modul.BENUTZER}:{kennwort}".encode()).decode()
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": kopf, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda *a: None
        self.selbst.end_headers = lambda: None
        (self.selbst.do_GET if befehl == "GET" else self.selbst.do_POST)()

    @property
    def daten(self) -> dict:
        return json.loads(self.selbst.wfile.getvalue().decode("utf-8"))


def _fortschritt(server) -> dict:
    a = _Anfrage(server, befehl="GET", weg=server.WEG_FORTSCHRITT)
    assert a.codes == [200]
    return a.daten


def _abbrechen(server, rumpf) -> _Anfrage:
    return _Anfrage(server, befehl="POST", weg=server.WEG_ABBRECHEN, rumpf=rumpf)


def _lauf_a_endet_lauf_b_beginnt(server, tmp_path):
    """Lauf A beginnt, die Seite sieht ihn; A endet, B beginnt in einer anderen Mappe.
    Gibt zurück, was die Seite von A gesehen hat."""
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-a")
    gesehen = _fortschritt(server)
    server.LAUFSTAND.beende(ergebnis={"vermerkt": 1, "abgebrochen": False})
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-b")
    return gesehen


# ======================================================================================
# Satz 1: der verspätete Abbruch trifft den neuen Lauf nicht
# ======================================================================================

def test_ein_verspaeteter_abbruch_trifft_den_neuen_lauf_nicht(server, tmp_path):
    """Die Zeile «global cancel from Beta view», umgestellt: Lauf A endet, Lauf B beginnt,
    der Abbruch mit der Kennung von A kommt an — B läuft weiter, die Antwort ist 409 und
    nennt die Mappe von B."""
    gesehen = _lauf_a_endet_lauf_b_beginnt(server, tmp_path)

    a = _abbrechen(server, {"lauf": gesehen.get("lauf"), "mappe": gesehen.get("mappe")})

    stand = server.LAUFSTAND.sicht()
    assert stand["laeuft"] is True
    assert stand["abbruch_verlangt"] is False, "der Abbruch für A hat B getroffen"
    assert a.codes == [409], a.daten
    assert "mappe-b" in a.daten["fehler"]
    assert a.daten["abbruch_verlangt"] is False
    assert a.daten["mappe"] == "mappe-b"


def test_jeder_lauf_hat_seine_kennung_und_der_fortschritt_nennt_sie_mit_der_mappe(
        server, tmp_path):
    gesehen_a = _lauf_a_endet_lauf_b_beginnt(server, tmp_path)
    gesehen_b = _fortschritt(server)

    assert gesehen_a["lauf"] and gesehen_b["lauf"]
    assert gesehen_a["lauf"] != gesehen_b["lauf"], "zwei Läufe, eine Kennung"
    assert (gesehen_a["mappe"], gesehen_b["mappe"]) == ("mappe-a", "mappe-b")
    # NUR DER NAME, KEIN PLATTENPFAD (Visbox-Regel 3).
    assert str(tmp_path) not in gesehen_b["mappe"]


def test_der_satz_bei_fremdem_lauf_nennt_keinen_plattenpfad(server, tmp_path):
    gesehen = _lauf_a_endet_lauf_b_beginnt(server, tmp_path)
    a = _abbrechen(server, {"lauf": gesehen["lauf"], "mappe": gesehen["mappe"]})
    assert a.codes == [409]
    assert str(tmp_path) not in json.dumps(a.daten, ensure_ascii=False)


def test_eine_passende_kennung_mit_fremder_mappe_bricht_nicht_ab(server, tmp_path):
    """Kennung und bestätigte Mappe müssen beide stimmen."""
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-b")
    gesehen = _fortschritt(server)
    a = _abbrechen(server, {"lauf": gesehen["lauf"], "mappe": "mappe-a"})
    assert a.codes == [409], a.daten
    assert server.LAUFSTAND.sicht()["abbruch_verlangt"] is False


# ======================================================================================
# Satz 3: was bleibt
# ======================================================================================

def test_ein_abbruch_mit_passender_kennung_wirkt_wie_bisher(server, tmp_path):
    """Entscheid 31: verlangt, nicht gewirkt — der laufende Schritt rechnet zu Ende, und
    «Abbruch verlangt» steht, bis der Lauf endet."""
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-a")
    gesehen = _fortschritt(server)

    a = _abbrechen(server, {"lauf": gesehen["lauf"], "mappe": gesehen["mappe"]})

    assert a.codes == [200], a.daten
    assert a.daten["abbruch_verlangt"] is True
    assert "rechnet zu Ende" in a.daten["satz"]
    assert "ohne_kennung" not in a.daten
    for _ in range(3):
        assert _fortschritt(server)["abbruch_verlangt"] is True
    server.LAUFSTAND.beende(ergebnis={"vermerkt": 0, "abgebrochen": True})
    assert _fortschritt(server)["abbruch_verlangt"] is True, "nach dem Ende noch lesbar"


def test_ein_abbruch_ohne_kennung_wirkt_bis_a0840_wie_bisher_und_sagt_es(server, tmp_path):
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-b")

    a = _abbrechen(server, {})

    assert a.codes == [200], a.daten
    assert a.daten["abbruch_verlangt"] is True
    assert server.LAUFSTAND.sicht()["abbruch_verlangt"] is True
    assert a.daten["ohne_kennung"] is True
    assert "Kennung" in a.daten["hinweis"]


def test_ein_abbruch_mit_kennung_ohne_lauf_sagt_dass_nichts_laeuft(server, tmp_path):
    assert server.LAUFSTAND.beginne_wenn_frei(tmp_path / "mappe-a")
    gesehen = _fortschritt(server)
    server.LAUFSTAND.beende(ergebnis={"vermerkt": 1, "abgebrochen": False})
    a = _abbrechen(server, {"lauf": gesehen["lauf"], "mappe": gesehen["mappe"]})
    assert a.codes == [400]
    assert "kein Lauf" in a.daten["fehler"]


# ======================================================================================
# Satz 2: die Seite schickt Kennung und bestätigte Mappe (mit node gefahren)
# ======================================================================================

_SEITE_FAHREN = r"""
const skript = require("fs").readFileSync(process.argv[2], "utf8");
const fall = JSON.parse(require("fs").readFileSync(process.argv[3], "utf8"));
class El { constructor(){ this.children=[]; this.style={}; this.dataset={}; this.value="";
  this.textContent=""; this.hidden=false; this.disabled=false; this.width=0; this.height=0;
  this.naturalWidth=0;
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
let fortschritt = fall.vorher;
async function fetch(url, opt) {
  let d = {fehler: "keine Mappe"}, status = 200;
  if (url.startsWith("/api/fortschritt")) d = fortschritt;
  else if (url === "/api/abbrechen") {
    gesendet.push(opt.body);
    d = fall.antwort; status = fall.status; fortschritt = fall.nachher;
  }
  return {status, ok: status < 400, json: async () => d};
}
const crypto = require("crypto").webcrypto;
(async () => {
  try {
    const api = new Function("document", "fetch", "crypto", "setInterval",
      skript + ";\nreturn {fortschrittHolen, abbrechen};")(document, fetch, crypto, () => 1);
    await api.fortschrittHolen();
    await api.abbrechen();
    await new Promise((r) => setTimeout(r, 50));
    console.log(JSON.stringify({gesendet, satz: ids.abbruchsatz.textContent,
                                gesperrt: ids.abbrechen.disabled}));
  } catch (e) { console.log("AUSNAHME " + (e && e.stack)); }
})();
"""


def _seite_fahren(tmp_path, fall) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("kein node im PATH — die Seite lässt sich hier nicht fahren")
    skript = re.search(r"<script>(.*)</script>", SEITE.read_text(encoding="utf-8"), re.S)
    assert skript, "kein Skript in der Seite"
    (tmp_path / "seite.js").write_text(skript.group(1), encoding="utf-8")
    (tmp_path / "fahren.js").write_text(_SEITE_FAHREN, encoding="utf-8")
    (tmp_path / "fall.json").write_text(json.dumps(fall), encoding="utf-8")
    lauf = subprocess.run([node, str(tmp_path / "fahren.js"), str(tmp_path / "seite.js"),
                           str(tmp_path / "fall.json")],
                          capture_output=True, text=True, timeout=60)
    assert lauf.returncode == 0, lauf.stderr
    assert not lauf.stdout.startswith("AUSNAHME"), lauf.stdout
    return json.loads(lauf.stdout.strip().splitlines()[-1])


def _lauf(kennung, mappe, abbruch=False) -> dict:
    return {"laeuft": True, "lauf": kennung, "mappe": mappe, "fertige": [],
            "abbruch_verlangt": abbruch, "art_des_zeichens": "unbelegt"}


def test_die_seite_schickt_kennung_und_bestaetigte_mappe(tmp_path):
    ergebnis = _seite_fahren(tmp_path, {
        "vorher": _lauf("kennung-a", "mappe-a"),
        "status": 200,
        "antwort": {"abbruch_verlangt": True, "satz": "Abbruch verlangt."},
        "nachher": _lauf("kennung-a", "mappe-a", abbruch=True),
    })
    assert len(ergebnis["gesendet"]) == 1
    rumpf = json.loads(ergebnis["gesendet"][0])
    assert rumpf != {}, "die Seite schickt den Abbruch ohne Kennung"
    assert rumpf == {"lauf": "kennung-a", "mappe": "mappe-a"}


def test_die_seite_zeigt_den_satz_zum_fremden_lauf_und_gibt_den_knopf_frei(tmp_path):
    """Die 409 kommt an: der Satz mit der Mappe von B bleibt stehen, auch wenn der
    Fortschritt danach neu gelesen wird, und der Knopf ist wieder frei — für B, wenn du
    ihn willst."""
    satz = "Jetzt rechnet die Mappe «mappe-b»."
    ergebnis = _seite_fahren(tmp_path, {
        "vorher": _lauf("kennung-a", "mappe-a"),
        "status": 409,
        "antwort": {"fehler": satz, "abbruch_verlangt": False,
                    "lauf": "kennung-b", "mappe": "mappe-b"},
        "nachher": _lauf("kennung-b", "mappe-b"),
    })
    assert ergebnis["satz"] == satz
    assert ergebnis["gesperrt"] is False
