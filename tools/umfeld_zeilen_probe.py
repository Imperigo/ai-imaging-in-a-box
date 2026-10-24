"""KNOTEN «UMFELD»: NICHTS ABGESCHNITTEN, NICHTS VERDECKT — die Messprobe am eingecheckten Bau.

Befund von KosmoOrbit Int 1 (24.10.2026, Demo-Stand), gleich in der Kopie: Im Knoten «Umfeld» waren
die Zeilen der Modell-Liste abgeschnitten — bei Bäumen und Autos fehlte das «CC0» —, und der Satz zur
Lizenz lag über der Zeile «Lädt einmal am Heim-PC …». Ursache: Die Hülle der Kurzhilfe (inline-block)
wuchs mit dem Text über die Körperbreite, fünf Zeilen brauchten mehr als die 70 px der Liste, der
Ladesatz war auf zwei Zeilen gekappt und der Lizenzsatz auf eine (Protokoll 74 §288, Nachtrag).

Diese Probe misst, was der Architekt sieht — wie die KosmoOrbit-Probe
``e2e/kv-umfeld-zeilen-ganz.spec.ts`` (die dort mit Playwright läuft):

* Sie lädt den eingecheckten Bau (``kosmovis/apps/visbox-knoten/dist``) in Chromium, ohne Zusatzpaket,
  setzt über ``window.visboxKi`` einen Knoten «Umfeld» mit allen fünf Kategorien und zoomt mit
  Strg + Rad auf 1 und auf 0,5.
* Je Stufe, einmal mit den Namen aus dem Katalog und einmal mit langen Namen (in die Zeile geschrieben):
  keine Zeile läuft über (``scrollWidth``/``scrollHeight``), Quelle und «CC0» stehen ganz in ihrer Zeile
  und im Knoten, Ladesatz und Lizenzsatz laufen nicht über und ihre Kisten schneiden sich nicht.

Gebrauch::

    python tools/umfeld_zeilen_probe.py            # Ende 1 bei Fund
    python tools/umfeld_zeilen_probe.py --json     # das ganze Ergebnis

Läuft in der Prüfstrecke (``tests/test_umfeld_zeilen.py``).
"""
from __future__ import annotations

import argparse
import functools
import html
import http.server
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
BAU = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist"
KATEGORIEN = ("baeume", "buesche", "wiese", "strasse", "autos")
ZOOMSTUFEN = (1, 0.5)
LANGER_NAME = "Grosser, alter Laubbaum mit breiter Krone · Kleiner Laubbaum, licht und hoch gewachsen"

_SKRIPT = r"""
const KATEGORIEN = __KATEGORIEN__, ZOOMSTUFEN = __ZOOMSTUFEN__, LANG = __LANG__;
const warte = (ms) => new Promise((r) => setTimeout(r, ms));
async function bis(fn, ms) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await warte(50); } return null; }
function miss(W, k, lang, stufe) {
  const fehler = [], EPS = 1, vor = stufe + (lang ? ', lange Namen' : '') + ': ';
  const innen = (a, b) => a.left >= b.left - EPS && a.right <= b.right + EPS && a.top >= b.top - EPS && a.bottom <= b.bottom + EPS;
  const schneiden = (a, b) => a.left < b.right - EPS && b.left < a.right - EPS && a.top < b.bottom - EPS && b.top < a.bottom - EPS;
  const doc = k.ownerDocument;
  const kRect = k.querySelector('[data-testid="umfeld"]').getBoundingClientRect();
  const textRects = (el, wort) => {
    const gang = doc.createTreeWalker(el, 4);
    for (let n = gang.nextNode(); n; n = gang.nextNode()) {
      const i = (n.textContent || '').indexOf(wort);
      if (i < 0) continue;
      const r = doc.createRange(); r.setStart(n, i); r.setEnd(n, i + wort.length);
      return Array.from(r.getClientRects());
    }
    return [];
  };
  const sichtbar = (rect, el) => {
    for (let a = el; a && a !== k.parentElement; a = a.parentElement) {
      const s = W.getComputedStyle(a);
      if ((s.overflowX !== 'visible' || s.overflowY !== 'visible') && !innen(rect, a.getBoundingClientRect())) return false;
    }
    return true;
  };
  for (const kat of KATEGORIEN) {
    const zeile = k.querySelector('[data-testid="umfeld-liste-' + kat + '"]');
    if (!zeile) { fehler.push(vor + kat + ': Zeile fehlt'); continue; }
    if (lang) (zeile.querySelector('[data-umfeld="modelle"]') || zeile).textContent = LANG;
    const zRect = zeile.getBoundingClientRect();
    if (zeile.scrollWidth > zeile.clientWidth + EPS) fehler.push(vor + kat + ': läuft seitlich über');
    if (zeile.scrollHeight > zeile.clientHeight + EPS) fehler.push(vor + kat + ': läuft unten über');
    if (!innen(zRect, kRect)) fehler.push(vor + kat + ': Zeile ragt aus dem Knoten');
    const herkunft = zeile.querySelector('[data-umfeld="herkunft"]');
    if (!herkunft) { fehler.push(vor + kat + ': Quelle und Lizenz fehlen als eigenes Stück'); continue; }
    if (herkunft.scrollWidth > herkunft.clientWidth + EPS) fehler.push(vor + kat + ': Quelle/Lizenz abgeschnitten');
    const quelle = (herkunft.textContent || '').split(' · ')[0];
    for (const wort of [quelle, 'CC0']) {
      const rs = textRects(herkunft, wort);
      if (!rs.length) fehler.push(vor + kat + ': «' + wort + '» steht nicht in der Zeile');
      for (const r of rs) if (r.width <= 0 || !innen(r, zRect) || !innen(r, kRect) || !sichtbar(r, herkunft)) fehler.push(vor + kat + ': «' + wort + '» nicht ganz sichtbar');
    }
  }
  const laden = k.querySelector('[data-testid="umfeld-laden"]'), lizenz = k.querySelector('[data-testid="umfeld-lizenz"]');
  for (const [name, el] of [['Ladesatz', laden], ['Lizenzsatz', lizenz]]) {
    if (el.scrollHeight > el.clientHeight + EPS) fehler.push(vor + name + ': läuft unten über');
    if (el.scrollWidth > el.clientWidth + EPS) fehler.push(vor + name + ': läuft seitlich über');
    if (!innen(el.getBoundingClientRect(), kRect)) fehler.push(vor + name + ': ragt aus dem Knoten');
  }
  if (schneiden(laden.getBoundingClientRect(), lizenz.getBoundingClientRect())) fehler.push(vor + 'Ladesatz und Lizenzsatz überdecken sich');
  return fehler;
}
(async () => {
  const aus = { fehler: [], stufen: [], zeilen: 0 };
  try {
    const f = document.getElementById('f');
    const doc = await bis(() => f.contentDocument && f.contentDocument.querySelector('.vis-knoten') && f.contentDocument, 30000);
    if (!doc) throw new Error('Knotenansicht nicht geladen');
    await warte(1500);
    const W = f.contentWindow;
    const l = W.visboxKi.rufe({ kennung: 'UZ-0', werkzeug: 'graph_lesen', argumente: {} }, 'karte');
    const gid = JSON.parse(l.sofort.text).graphen[0].graphId;
    const a = W.visboxKi.rufe({ kennung: 'UZ-1', werkzeug: 'vis_umfeldSetzen', argumente: { graphId: gid, kategorien: KATEGORIEN } }, 'coop');
    if (a && a.karte) W.visboxKi.entscheide('UZ-1', true);
    const k = await bis(() => doc.querySelector('[data-testid="vis-node-umfeld"]'), 5000);
    if (!k) throw new Error('Knoten «Umfeld» nicht gesetzt (' + JSON.stringify(a).slice(0, 200) + ')');
    const svg = doc.querySelector('[data-testid="node-canvas"]');
    const zoom = () => Number(doc.querySelector('[data-knoten-zoom]').dataset.knotenZoom);
    async function zoomeAuf(ziel) {
      let schritt = 12, richtung = 0;
      for (let i = 0; i < 400; i++) {
        const z = zoom();
        if (Math.abs(z - ziel) / ziel < 0.04) break;
        const neu = z < ziel ? -1 : 1;
        if (richtung && neu !== richtung) schritt = Math.max(0.5, schritt / 2);
        richtung = neu;
        const r = k.getBoundingClientRect(), sr = svg.getBoundingClientRect();
        const x = Math.min(Math.max(r.left + 20, sr.left + 5), sr.right - 5), y = Math.min(Math.max(r.top + 10, sr.top + 5), sr.bottom - 5);
        svg.dispatchEvent(new W.WheelEvent('wheel', { bubbles: true, cancelable: true, deltaMode: 0, clientX: x, clientY: y, ctrlKey: true, deltaY: neu * schritt }));
        await warte(30);
      }
      return zoom();
    }
    // Erst die Namen aus dem Katalog bei jeder Stufe, dann die langen (sie bleiben in der Zeile stehen).
    for (const lang of [false, true]) {
      for (const ziel of ZOOMSTUFEN) {
        const z = await zoomeAuf(ziel);
        if (!lang) aus.stufen.push(z);
        if (Math.abs(z - ziel) / ziel >= 0.04) aus.fehler.push('Zoom ' + ziel + ' nicht erreicht (' + z + ')');
        await warte(200);
        aus.fehler.push(...miss(W, k, lang, 'Zoom ' + ziel));
        aus.zeilen += k.querySelectorAll('[data-testid^="umfeld-liste-"]').length;
      }
    }
  } catch (err) { aus.fehler.push('Probe brach ab: ' + err.message); }
  document.getElementById('ergebnis').textContent = JSON.stringify(aus);
})();
"""


def _leinwand_probe():
    spec = importlib.util.spec_from_file_location("ueber_leinwand_probe", WURZEL / "tools" / "ueber_leinwand_probe.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def chromium() -> str:
    """Derselbe Browser wie die Trefferprobe über der Leinwand."""
    return _leinwand_probe().chromium()


def pruefseite() -> str:
    skript = (_SKRIPT.replace("__KATEGORIEN__", json.dumps(KATEGORIEN))
              .replace("__ZOOMSTUFEN__", json.dumps(ZOOMSTUFEN))
              .replace("__LANG__", json.dumps(LANGER_NAME, ensure_ascii=False)))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:#000}"
            "iframe{border:0;width:1440px;height:900px;display:block}</style></head><body>"
            "<iframe id='f' src='dist/index.html'></iframe><pre id='ergebnis'>laeuft</pre>"
            f"<script>{skript}</script></body></html>")


class _Leise(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D401 - kein Zugriffsprotokoll im Testlauf
        pass


def pruefe(bau: Path = BAU, browser: str | None = None) -> dict:
    """Fährt die Probe am Bau ``bau`` und liefert ``{fehler, stufen, zeilen}``."""
    browser = browser or chromium()
    with tempfile.TemporaryDirectory() as tmp:
        wurzel = Path(tmp)
        (wurzel / "dist").symlink_to(bau.resolve(), target_is_directory=True)
        (wurzel / "probe.html").write_text(pruefseite(), encoding="utf-8")
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(_Leise, directory=str(wurzel)))
        faden = threading.Thread(target=server.serve_forever, daemon=True)
        faden.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/probe.html"
            lauf = subprocess.run(
                [browser, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                 "--window-size=1440,1000", "--force-device-scale-factor=1",
                 "--virtual-time-budget=120000", "--dump-dom", url],
                capture_output=True, text=True, timeout=300)
        finally:
            server.shutdown()
            server.server_close()
    treffer = re.search(r'<pre id="ergebnis">(.*?)</pre>', lauf.stdout, re.S)
    if not treffer or treffer.group(1) == "laeuft":
        return {"fehler": ["Probe lieferte kein Ergebnis (Browser: " + lauf.stderr[-300:] + ")"],
                "stufen": [], "zeilen": 0}
    return json.loads(html.unescape(treffer.group(1)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="das ganze Ergebnis ausgeben")
    ap.add_argument("--bau", type=Path, default=BAU, help="Ordner des Baus (Vorgabe: der eingecheckte)")
    args = ap.parse_args(argv)
    ergebnis = pruefe(args.bau)
    if args.json:
        print(json.dumps(ergebnis, ensure_ascii=False, indent=1))
    else:
        print(f"Stufen: {[round(s, 3) for s in ergebnis['stufen']]}, Zeilen geprüft: {ergebnis['zeilen']}, "
              f"Funde: {len(ergebnis['fehler'])}")
        for f in ergebnis["fehler"]:
            print("  ROT  " + f)
    return 1 if ergebnis["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
