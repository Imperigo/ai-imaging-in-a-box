"""DIE EBENE ÜBER DER LEINWAND — die Trefferprobe am eingecheckten Bau der Knotenansicht.

Owner-Fehler und stehende Regel vom 24.10.2026 (Visbox 0.3.54): *«Beim Zoomen verschwindet die
Porttyp-Legende unten links hinter den Nodes.»* Gemessen, in Chromium und WebKit gleich: Die Legende
und das Beiblatt am Render-Knoten (es wandert mit dem Knoten) lagen im selben Stapel, das Beiblatt
eine Stufe höher. Trugen Zoomen und Verschieben es unter die Legende, lag es darüber.

Die Regel: **Feste Bedienflächen (Legende, Inseln, Leisten, Karten, Meldungen) geraten bei keinem
Zoom hinter Inhalte der Arbeitsfläche.** Diese Probe prüft sie so, wie ein Zeiger sie erlebt:

* Sie lädt den eingecheckten Bau (``kosmovis/apps/visbox-knoten/dist``) in Chromium, ohne
  Zusatzpaket — eine Prüfseite bettet die Knotenansicht ein und spricht sie über dieselben
  Rad-Ereignisse an wie Maus und Trackpad (Strg + Rad zoomt am Zeiger, Wischen schiebt).
* Für jede Zoomstufe 0,25 / 0,5 / 1 / 2 / höchste und jede feste Fläche schiebt sie einen Inhalt
  der Leinwand (Render-Knoten, Render-Beiblatt) unter die Mitte der Fläche und fragt mit
  ``document.elementFromPoint``, was dort getroffen wird. Es muss die Fläche sein.
* Das Beiblatt wird beim Verschieben in die freie Mitte geklemmt; es erreicht nicht jede Fläche,
  muss aber die Legende erreichen (dort lag der Fehler). Wo es nur einen Teil einer Fläche deckt,
  wird an diesem Teil geprüft. Liegt kein Inhalt darunter, ist die Probe ungültig — und rot.

Gebrauch::

    python tools/ueber_leinwand_probe.py            # prüft den eingecheckten Bau, Ende 1 bei Fund
    python tools/ueber_leinwand_probe.py --json     # das ganze Ergebnis

Läuft in der Prüfstrecke (``tests/test_ueber_leinwand.py``) und damit vor jedem Release.
"""
from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
BAU = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist"

#: Die festen Flächen der Knotenansicht, die geprüft werden. ``pflicht``: muss im Bau da sein.
FLAECHEN = (
    {"name": "Porttyp-Legende", "sel": '[data-testid="vis-island-legende"]', "pflicht": True},
    {"name": "Kuratier-Knopf", "sel": '[data-testid="vis-kuratier-toggle"]', "pflicht": True},
    {"name": "GRAPH-Insel", "sel": '[data-testid="island-graph-root"]'},
    {"name": "ANSICHT-Insel", "sel": '[data-testid="island-ansicht-root"]'},
    {"name": "STIMMUNG-Insel", "sel": '[data-testid="island-stimmung-root"]'},
    {"name": "AUSTAUSCH-Insel", "sel": '[data-testid="island-austausch-root"]'},
    {"name": "SONNE-Insel", "sel": '[data-testid="island-sonne-root"]'},
    {"name": "Einstellungs-Kreis", "sel": '[data-testid="island-einstellungen-kreis"]'},
    {"name": "Kopf-Zweitgruppe", "sel": '[data-testid="island-kopf-zweitgruppe"]'},
    {"name": "Lot (Assistent)", "sel": '[data-testid="kosmo-eck-orb-wurzel"]'},
    {"name": "Werkzeug-Knopf oben links", "sel": ".app-werkzeug-palette-lage"},
    {"name": "Speichern-Kreis", "sel": ".app-speichern-kreis-lage"},
    {"name": "Erzählzeile", "sel": '[data-testid="erzaehl-zeile"]'},
    {"name": "Karte des Assistenten", "sel": '[data-testid="claude-vorschlag"]'},
)

#: Inhalte der Arbeitsfläche. ``muss``: Flächen, die dieser Inhalt erreichen muss (sonst alle).
INHALTE = (
    {"name": "Render-Knoten", "sel": '[data-testid="vis-node-render"]'},
    {"name": "Render-Beiblatt", "sel": '[data-testid="render-beiblatt"]', "muss": ["Porttyp-Legende"]},
)

ZOOMSTUFEN = (0.25, 0.5, 1, 2, "max")

_SKRIPT = r"""
const FLAECHEN = __FLAECHEN__, INHALTE = __INHALTE__, ZOOMSTUFEN = __ZOOMSTUFEN__;
const warte = (ms) => new Promise((r) => setTimeout(r, ms));
async function bis(fn, ms) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await warte(50); } return null; }
(async () => {
  const aus = { fehler: [], geprueft: 0, stufen: [], flaechen: [], ausgelassen: [] };
  try {
    const f = document.getElementById('f');
    const doc = await bis(() => f.contentDocument && f.contentDocument.querySelector('.vis-knoten') && f.contentDocument, 30000);
    if (!doc) throw new Error('Knotenansicht nicht geladen');
    await warte(1500);
    const W = f.contentWindow;
    const svg = doc.querySelector('[data-testid="node-canvas"]');
    const zoom = () => Number(doc.querySelector('[data-knoten-zoom]').dataset.knotenZoom);
    const sr = svg.getBoundingClientRect();
    const mitte = { x: sr.left + sr.width / 2, y: sr.top + sr.height / 2 };
    const rad = (init) => svg.dispatchEvent(new W.WheelEvent('wheel', Object.assign({ bubbles: true, cancelable: true, deltaMode: 0, clientX: mitte.x, clientY: mitte.y }, init)));
    const knopf = doc.querySelector('[data-testid="vis-node-render"] [data-testid="node-expand"]');
    if (!knopf) throw new Error('Render-Knoten ohne Aufklapp-Knopf');
    knopf.click();
    if (!(await bis(() => doc.querySelector('[data-testid="render-beiblatt"]'), 5000))) throw new Error('Beiblatt geht nicht auf');
    // Claudes Karte und die Erzaehlzeile: verbunden melden und einen Vorschlag als Karte stellen
    // (dieselbe Bruecke, die der Mac benutzt), damit auch sie unter der Leinwand-Probe stehen.
    if (W.visboxKi && W.visboxWirt && W.visboxWirt.lage) {
      W.visboxWirt.lage({ claude: { verbunden: true } });
      const l = await W.visboxKi.rufe({ kennung: 'UL-1', werkzeug: 'graph_lesen', argumente: {} }, 'karte');
      const g = JSON.parse(l.sofort.text).graphen[0];
      const prompt = g.knoten.find((k) => k.typ === 'prompt');
      if (prompt) await W.visboxKi.rufe({ kennung: 'UL-2', werkzeug: 'vis_nodeParametrieren', argumente: { graphId: g.graphId, nodeId: prompt.nodeId, params: { text: 'Probe' } } }, 'karte');
      await bis(() => doc.querySelector('[data-testid="claude-vorschlag"]'), 3000);
    }
    const sichtbar = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && W.getComputedStyle(e).visibility !== 'hidden'; };
    for (const fl of FLAECHEN) {
      const da = sichtbar(doc.querySelector(fl.sel));
      if (fl.pflicht && !da) aus.fehler.push(fl.name + ' fehlt');
      if (da) aus.flaechen.push(fl.name);
    }
    async function zoomeAuf(ziel) {
      let schritt = 12, richtung = 0;
      for (let i = 0; i < 400; i++) {
        const z = zoom();
        if (ziel !== 'max' && Math.abs(z - ziel) / ziel < 0.04) break;
        const neu = ziel === 'max' || z < ziel ? -1 : 1;
        if (richtung && neu !== richtung) schritt = Math.max(0.5, schritt / 2);
        richtung = neu;
        rad({ ctrlKey: true, deltaY: neu * schritt });
        await warte(30);
        if (ziel === 'max' && Math.abs(zoom() - z) < 1e-9) break;
      }
      return zoom();
    }
    function lage(inh, fl) {
      const F = doc.querySelector(fl.sel), I = doc.querySelector(inh.sel);
      const f2 = F.getBoundingClientRect(), r = I.getBoundingClientRect();
      let x = f2.left + f2.width / 2, y = f2.top + f2.height / 2;
      const inMitte = r.left < x && r.right > x && r.top < y && r.bottom > y;
      const ix = [Math.max(f2.left, r.left), Math.min(f2.right, r.right)], iy = [Math.max(f2.top, r.top), Math.min(f2.bottom, r.bottom)];
      const deckt = ix[1] - ix[0] > 2 && iy[1] - iy[0] > 2;
      if (!inMitte && deckt) { x = (ix[0] + ix[1]) / 2; y = (iy[0] + iy[1]) / 2; }
      return { F, r, x, y, inMitte, darunter: inMitte || deckt, s: { x: f2.left + f2.width / 2, y: f2.top + f2.height / 2 } };
    }
    for (const ziel of ZOOMSTUFEN) {
      const z = await zoomeAuf(ziel);
      aus.stufen.push(z);
      if (ziel !== 'max' && Math.abs(z - ziel) / ziel >= 0.04) aus.fehler.push('Zoom ' + ziel + ' nicht erreicht (' + z + ')');
      for (const fl of FLAECHEN) {
        if (!aus.flaechen.includes(fl.name)) continue;
        for (const inh of INHALTE) {
          let l = lage(inh, fl);
          // Schieben in bis zu vier Zuegen: das Beiblatt klemmt sich an die freie Mitte, und
          // nach jedem Zug steht es neu.
          // Steht es nach einem Zug still (geklemmt, weil sein Knoten weit ausserhalb liegt), wird
          // der naechste Zug verdoppelt.
          let hebel = 1;
          for (let zug = 0; zug < 12 && !l.inMitte; zug++) {
            const rand = Math.min(20, l.r.width / 3, l.r.height / 3);
            const p = { x: Math.min(Math.max(l.s.x, l.r.left + rand), l.r.right - rand), y: Math.min(Math.max(l.s.y, l.r.top + rand), l.r.bottom - rand) };
            const d = { x: l.s.x - p.x, y: l.s.y - p.y };
            if (Math.hypot(d.x, d.y) <= 0.5) break;
            const vorher = l.r;
            rad({ deltaX: -d.x * hebel || 0.01, deltaY: -d.y * hebel });
            await warte(80);
            l = lage(inh, fl);
            hebel = Math.abs(l.r.left - vorher.left) + Math.abs(l.r.top - vorher.top) < 1 ? hebel * 2 : 1;
          }
          const muss = !inh.muss || inh.muss.includes(fl.name);
          if (!l.darunter) { if (muss) aus.fehler.push('Zoom ' + ziel + ': ' + inh.name + ' liess sich nicht unter ' + fl.name + ' schieben (ungueltige Probe; Inhalt ' + [l.r.left, l.r.top, l.r.right, l.r.bottom].map(Math.round).join(',') + ', Ziel ' + Math.round(l.s.x) + ',' + Math.round(l.s.y) + ')'); else aus.ausgelassen.push(ziel + '/' + fl.name + '/' + inh.name); continue; }
          const e = doc.elementFromPoint(l.x, l.y);
          if (e && l.F.contains(e)) { aus.geprueft++; continue; }
          const wer = !e ? 'nichts' : e.tagName.toLowerCase() + '.' + String((e.className && e.className.baseVal !== undefined) ? e.className.baseVal : e.className).split(' ')[0];
          aus.fehler.push('Zoom ' + ziel + ': an ' + (l.inMitte ? 'der Mitte' : 'einem gedeckten Punkt') + ' von ' + fl.name + ' (' + Math.round(l.x) + ',' + Math.round(l.y) + ') trifft der Zeiger ' + wer + ' statt der Flaeche (' + inh.name + ' darunter)');
        }
      }
    }
  } catch (err) { aus.fehler.push('Probe brach ab: ' + err.message); }
  document.getElementById('ergebnis').textContent = JSON.stringify(aus);
})();
"""


def pruefseite() -> str:
    skript = (_SKRIPT.replace("__FLAECHEN__", json.dumps(FLAECHEN, ensure_ascii=False))
              .replace("__INHALTE__", json.dumps(INHALTE, ensure_ascii=False))
              .replace("__ZOOMSTUFEN__", json.dumps(ZOOMSTUFEN)))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:#000}"
            "iframe{border:0;width:1440px;height:900px;display:block}</style></head><body>"
            "<iframe id='f' src='dist/index.html'></iframe><pre id='ergebnis'>laeuft</pre>"
            f"<script>{skript}</script></body></html>")


def chromium() -> str:
    for p in ("/opt/pw-browsers/chromium/chrome-linux/chrome", "/opt/pw-browsers/chromium"):
        if Path(p).is_file():
            return p
    kandidaten = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    if kandidaten:
        return str(kandidaten[-1])
    gefunden = shutil.which("chromium") or shutil.which("chromium-browser")
    if not gefunden:
        raise SystemExit("Chromium nicht gefunden — die Trefferprobe braucht einen Browser.")
    return gefunden


class _Leise(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D401 - kein Zugriffsprotokoll im Testlauf
        pass


def pruefe(bau: Path = BAU, browser: str | None = None) -> dict:
    """Fährt die Probe am Bau ``bau`` und liefert ``{fehler, geprueft, stufen, flaechen, ausgelassen}``."""
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
                 "--virtual-time-budget=240000", "--dump-dom", url],
                capture_output=True, text=True, timeout=300)
        finally:
            server.shutdown()
            server.server_close()
    treffer = re.search(r'<pre id="ergebnis">(.*?)</pre>', lauf.stdout, re.S)
    if not treffer or treffer.group(1) == "laeuft":
        return {"fehler": ["Probe lieferte kein Ergebnis (Browser: " + lauf.stderr[-300:] + ")"],
                "geprueft": 0, "stufen": [], "flaechen": [], "ausgelassen": []}
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
        print(f"Flächen: {len(ergebnis['flaechen'])}, Stufen: {[round(s, 3) for s in ergebnis['stufen']]}, "
              f"geprüft: {ergebnis['geprueft']}, Funde: {len(ergebnis['fehler'])}")
        for f in ergebnis["fehler"]:
            print("  ROT  " + f)
    return 1 if ergebnis["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
