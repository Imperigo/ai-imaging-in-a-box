"""A0831 «Getippter Pfad speichert nichts»: Die Seite handelt nur mit der Mappe, die sich
öffnen liess.

Befund des externen Audits (24.11.2026, Station 3): Wer Mappe A offen hatte und im Feld den
Pfad von B eintippte, ohne zu öffnen, schrieb mit «Einstellungen übernehmen», «Rechnen»,
«Benennen», einer Skizze und der «Knotenansicht» in B. Das Feld ist ein Entwurf zum Öffnen;
das Ziel ist die bestätigte Mappe. Erst ein gelungenes «Öffnen» wechselt sie, ein
gescheitertes lässt A und ihren Kopf stehen.

**Gefahren in node, wie die Testhülle des Audits:** das Skript der Seite mit einer kleinen
Attrappe von ``document`` und ``fetch``; jede Anfrage wird mit ihrem Ziel mitgeschrieben.
Node muss da sein, die Probe überspringt nicht. Regel 3: die Mappen heissen «Atelier-A» und
«Atelier-B», kein Plattenpfad.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
SEITE = WURZEL / "oberflaeche" / "seite.html"

A, B = "Atelier-A", "Atelier-B"

_HUELLE = r"""
const skript = require("fs").readFileSync(process.argv[2], "utf8");
class El {
  constructor(tag, text) { this.tag = tag || ""; this.children = []; this.style = {};
    this.dataset = {}; this.value = ""; this.textContent = text || ""; this.hidden = false;
    this.width = 0; this.height = 0; this.naturalWidth = 0; this.src = ""; this.lauscher = {};
    this.classList = {add(){}, remove(){}, toggle(){}, contains(){ return false; }}; }
  addEventListener(art, f) { (this.lauscher[art] = this.lauscher[art] || []).push(f); }
  // EINE AUSWAHL NIMMT DIE ERSTE OPTION, wie im Browser.
  append(...k) { this.children.push(...k);
    for (const o of k) if (o.tag === "option" && this.value === "") this.value = o.value; }
  prepend(...k) { this.children.unshift(...k); }
  replaceChildren(...k) {
    if (this.children.some((o) => o.tag === "option")) this.value = "";
    this.children = k; }
  insertBefore(k) { this.children.push(k); }
  replaceWith() {} remove() {} focus() {} setPointerCapture() {}
  querySelector() { return null; }
  getBoundingClientRect() { return {left: 0, top: 0, width: 10, height: 10}; }
  getContext() { return new Proxy({}, {get: () => () => {}, set: () => true}); }
  toDataURL() { return "data:image/png;base64,AAAA"; }
}
const ids = {};
const document = { hidden: false, getElementById: (id) => ids[id] || (ids[id] = new El("#" + id)),
  createElement: (tag) => new El(tag), createTextNode: (t) => new El("", t),
  querySelectorAll: () => [] };
const ort = { href: "/" };
const modus = { b: "fehlt" };
const anfragen = [];

function mappe(ordner, name) {
  return { ordner, name, stand_nr: 1, laeufe: [], einstellungen: {}, grundriss: {},
    knotenbaum: [], bedienfelder: [],
    modell: { pfad: "haus.glb", einlass: { format: "glb" }, stand: "unveraendert" },
    "import": { format: "glb", weg: "direkt", hochachse_steht_fest: true, hochachse: "Y",
                treue: 1, hinweise: [] },
    bilder: [{ bild: "bild-1.png", zeichen: "nicht-gemessen", satz: "Nicht geprüft.",
               vorhanden: true, schicht: "geometrielayer", titel: null, herkunft: {} }],
    skizzen: [{ skizze: "skizze-1.png", stand: "offen", ueber: "bild-1.png", bemerkung: "Dach" }] };
}

function antwort(status, d) { return { status, ok: status < 400, json: async () => d }; }

async function fetch(url, opt) {
  const u = new URL(url, "http://seite");
  let ziel;
  if (u.pathname === "/api/projekt") ziel = u.searchParams.get("ordner");
  else if (opt && opt.body) { const k = JSON.parse(opt.body); if ("ordner" in k) ziel = k.ordner; }
  if (ziel !== undefined) anfragen.push({ weg: u.pathname, ziel });
  if (u.pathname === "/api/projekt") {
    if (ziel === "" || ziel === "__A__") return antwort(200, mappe("__A__", "Mappe A"));
    if (ziel === "__B__" && modus.b === "da") return antwort(200, mappe("__B__", "Mappe B"));
    return antwort(404, { fehler: "Diese Mappe gibt es nicht." });
  }
  if (u.pathname === "/api/fortschritt") return antwort(200, { laeuft: false, fertige: [] });
  if (u.pathname === "/api/skizze") return antwort(200, { skizze: "skizze-2.png", hinweis: "abgelegt" });
  return antwort(200, { ok: true });
}

const crypto = require("crypto").webcrypto;
const api = new Function("document", "fetch", "crypto", "setInterval", "location",
  skript + ";\nreturn {einstellungenSchicken, rechnen, skizzeRechnen, skizzeAblegen, nachsehen," +
  " zeichenStart, zeichenZug, zeichenEnde};")(document, fetch, crypto, () => 1, ort);

const ruhe = async () => { for (let i = 0; i < 30; i++) await new Promise((r) => setTimeout(r, 0)); };
const text = (e) => [e.textContent || "", ...e.children.map(text)].join(" ");
function finde(e, wort) {
  if (e.tag === "button" && e.textContent === wort) return e;
  for (const k of e.children) { const t = finde(k, wort); if (t) return t; }
  return null;
}
const fehlend = [];
async function ausloesen(e, art, ereignis, wort) {
  if (!e) { fehlend.push(wort || art); return; }
  for (const f of (e.lauscher[art] || [])) await f(Object.assign({ preventDefault() {} }, ereignis || {}));
  await ruhe();
}
function strich(x) {
  const e = { pointerId: 1, pointerType: "pen", pressure: 0.5, clientX: x, clientY: x,
              preventDefault() {} };
  api.zeichenStart(e); api.zeichenZug(Object.assign({}, e, { clientX: x + 1 })); api.zeichenEnde(e);
}
const lage = () => ({ feld: ids.ordner.value, kopf: text(ids.modell),
  hinweis: (ids.ordnerhinweis ? ids.ordnerhinweis.textContent : null), stand: ids.stand.textContent });

async function handeln() {
  anfragen.length = 0;
  await api.einstellungenSchicken({ seed: 3 }); await ruhe();
  await api.rechnen(); await ruhe();
  await ausloesen(finde(ids.bilder, "Benennen"), "click", null, "Benennen");
  await ausloesen(finde(ids.bilder, "Speichern"), "click", null, "Speichern");
  strich(1);
  await api.skizzeAblegen(); await ruhe();
  await api.skizzeRechnen("skizze-1.png", null, false); await ruhe();
  await api.nachsehen(); await ruhe();
  ort.href = "/knoten/";
  await ausloesen(ids.knoten, "click");
  return { anfragen: anfragen.slice(), knoten: ort.href, unterlage: ids.unterlagenbild.src,
           fehlend: fehlend.splice(0) };
}

(async () => {
  ids.tafel = new El("canvas"); ids.tafel.width = 10; ids.tafel.height = 10;
  const aus = {};
  await ruhe();
  aus.start = Object.assign(lage(), { anfragen: anfragen.slice() });

  ids.ordner.value = "__B__";
  await ausloesen(ids.ordner, "input");
  aus.getippt = Object.assign(lage(), { handeln: await handeln() });
  aus.getippt.danach = lage();

  anfragen.length = 0;
  await ausloesen(ids.laden, "click");
  aus.fehlschlag = Object.assign(lage(), { oeffnen: anfragen.slice() });
  aus.fehlschlag.handeln = await handeln();

  modus.b = "da";
  anfragen.length = 0;
  await ausloesen(ids.ordner, "keydown", { key: "Enter" });
  aus.erfolg = Object.assign(lage(), { oeffnen: anfragen.slice() });
  aus.erfolg.handeln = await handeln();
  aus.erfolg.danach = lage();
  console.log(JSON.stringify(aus));
})().catch((f) => { console.log("AUSNAHME " + f.stack); });
""".replace("__A__", A).replace("__B__", B)

#: Was jede Handlung schickt (Weg der Anfrage). `/api/projekt` kommt vom Nachsehen und vom
#: Neuladen der Mappe nach einer Änderung.
WEGE = {"/api/einstellungen", "/api/rechne", "/api/benennen", "/api/skizze",
        "/api/rechne-skizze", "/api/projekt"}


@pytest.fixture(scope="module")
def lauf(tmp_path_factory):
    node = shutil.which("node")
    assert node, "node fehlt im PATH: diese Probe fährt die Seite und überspringt nicht"
    ordner = tmp_path_factory.mktemp("a0831")
    skript = re.search(r"<script>(.*)</script>", SEITE.read_text(encoding="utf-8"), re.S)
    assert skript, "das Skript der Seite ist nicht zu finden"
    (ordner / "seite.js").write_text(skript.group(1), encoding="utf-8")
    (ordner / "huelle.js").write_text(_HUELLE, encoding="utf-8")
    ergebnis = subprocess.run([node, str(ordner / "huelle.js"), str(ordner / "seite.js")],
                              capture_output=True, text=True, timeout=60)
    assert ergebnis.returncode == 0, ergebnis.stderr
    assert not ergebnis.stdout.startswith("AUSNAHME"), ergebnis.stdout
    return json.loads(ergebnis.stdout)


def _ziele(handeln) -> tuple[set, set]:
    assert handeln["fehlend"] == [], "diese Knöpfe fehlten auf der Seite"
    return {a["weg"] for a in handeln["anfragen"]}, {a["ziel"] for a in handeln["anfragen"]}


# ======================================================================================
# Satz 1 · Getippt und nicht geöffnet: alles geht weiter an A
# ======================================================================================

def test_getippt_und_nicht_geoeffnet_nennen_alle_anfragen_a(lauf):
    h = lauf["getippt"]["handeln"]
    wege, ziele = _ziele(h)
    assert wege == WEGE, "jede Handlung hat geschickt"
    assert ziele == {A}, h["anfragen"]


def test_getippt_und_nicht_geoeffnet_oeffnet_die_knotenansicht_a(lauf):
    assert lauf["getippt"]["handeln"]["knoten"] == "/knoten/?ordner=" + A


def test_getippt_und_nicht_geoeffnet_bleibt_die_unterlage_aus_a(lauf):
    assert "ordner=" + A + "&" in lauf["getippt"]["handeln"]["unterlage"]


def test_das_feld_bleibt_der_entwurf(lauf):
    """Neu laden nach einer Änderung schreibt das Feld nicht zurück: Was getippt ist, bleibt."""
    assert lauf["getippt"]["danach"]["feld"] == B
    assert "Mappe A" in lauf["getippt"]["danach"]["kopf"]


# ======================================================================================
# Der eine Satz, solange Feld und offene Mappe auseinanderliegen
# ======================================================================================

def test_der_satz_nennt_die_offene_und_die_getippte_mappe(lauf):
    satz = lauf["getippt"]["hinweis"]
    assert satz == f"Offen ist «{A}». Mit «Öffnen» wechselst du zu «{B}».", satz


def test_ohne_abweichung_steht_kein_satz(lauf):
    assert lauf["start"]["hinweis"] == ""
    assert lauf["erfolg"]["danach"]["hinweis"] == ""


def test_der_satz_wird_angesagt():
    """Der Screenreader sagt ihn an, ohne dass der Fokus hinspringt (`aria-live`)."""
    html = SEITE.read_text(encoding="utf-8")
    marke = re.search(r'<[^>]*\bid="ordnerhinweis"[^>]*>', html)
    assert marke, "das Element für den Satz fehlt"
    assert 'aria-live="polite"' in marke.group(0)


# ======================================================================================
# Satz 2 · Öffnen: gescheitert bleibt A, gelungen wird B
# ======================================================================================

def test_ein_gescheitertes_oeffnen_laesst_a_und_den_kopf_stehen(lauf):
    f = lauf["fehlschlag"]
    assert [a["ziel"] for a in f["oeffnen"]] == [B], "versucht wurde B"
    assert "Mappe A" in f["kopf"] and "Mappe B" not in f["kopf"]
    assert f["stand"] == "Diese Mappe gibt es nicht."
    assert f["hinweis"].startswith(f"Offen ist «{A}».")
    wege, ziele = _ziele(f["handeln"])
    assert wege == WEGE
    assert ziele == {A}, f["handeln"]["anfragen"]
    assert f["handeln"]["knoten"] == "/knoten/?ordner=" + A


def test_ein_gelungenes_oeffnen_macht_b_zum_ziel_aller_anfragen(lauf):
    e = lauf["erfolg"]
    assert [a["ziel"] for a in e["oeffnen"]] == [B]
    assert "Mappe B" in e["kopf"]
    wege, ziele = _ziele(e["handeln"])
    assert wege == WEGE
    assert ziele == {B}, e["handeln"]["anfragen"]
    assert e["handeln"]["knoten"] == "/knoten/?ordner=" + B
    assert "ordner=" + B + "&" in e["handeln"]["unterlage"]


# ======================================================================================
# Satz 3 · Bleibt: die zuletzt geöffnete Mappe kommt beim Start ins Feld (Entscheid 90)
# ======================================================================================

def test_beim_start_kommt_die_zuletzt_geoeffnete_mappe_ins_feld(lauf):
    s = lauf["start"]
    assert [a["ziel"] for a in s["anfragen"]] == [""], "der Start fragt ohne Eintrag"
    assert s["feld"] == A
    assert "Mappe A" in s["kopf"]
