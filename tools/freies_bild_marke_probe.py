"""MARKE «FREIES BILD»: GANZ SICHTBAR — die Messprobe am eingecheckten Bau (Befund Int 1, Geräteprobe R70).

Befund von KosmoOrbit Int 1 (Geräteprobe R70, 24.10.2026), gleich in der Kopie: Die Marke «freies Bild»
(Entscheid 149) war abgeschnitten. Gemessen in KosmoOrbit (E2E ``kv-freies-bild-marke-ganz``): am Knoten «Aufs
Blatt» ragte sie hinter Knopf, «Vorschau» und Modus-Marke aus dem 38-px-Körper, auf der Kuratier-Karte lag sie
ganz ausserhalb und wurde von der Karte beschnitten, im Vergleich lagen die drei Marken übereinander. Knotenbild,
Grossansicht und Daumen waren ganz (Protokoll 74 §292).

Diese Probe misst denselben engsten Fall — alle drei Marken zugleich («Vorschau», «Ohne Grundlagenbild», «freies
Bild») — am **eingecheckten Stil** des Baus (``kosmovis/apps/visbox-knoten/dist``), ohne Brücke: Die drei
Flächen werden mit dem Aufbau der Kopie (``NodeCanvas.tsx`` Fall ``blatt``, ``KuratierFlaeche.tsx``) und deren
Massen gesetzt (Knotenkörper 184 px breit, ``38 + BLATT_MARKEN_H`` hoch; Karte 216 × 162 px; Vergleichskarte
330 × 200 px), in normaler und in grosser Schrift. Je Marke: läuft nicht über, ihr Text liegt ganz in der
Marke, in jedem beschneidenden Vorfahren, und die Mitte jeder Textzeile trifft die Marke selbst.

Gebrauch::

    python tools/freies_bild_marke_probe.py            # Ende 1 bei Fund
    python tools/freies_bild_marke_probe.py --json

Läuft in der Prüfstrecke (``tests/test_freies_bild_marke.py``).
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
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


def blatt_marken_h() -> int:
    """``BLATT_MARKEN_H`` aus der Kopie — die Höhe, die der Knoten der Markenzeile gibt."""
    t = re.search(r"export const BLATT_MARKEN_H = (\d+);", (VIS / "NodeCanvas.tsx").read_text(encoding="utf-8"))
    return int(t.group(1)) if t else 0


def _marken(form: str) -> str:
    """Die drei Marken wie ``GueteMarke``/``ModusMarke``/``FreiesBildMarke`` sie in der Form ``form`` setzen."""
    def huelle(art, text, testid, extra=""):
        return (f"<span class='k-tooltip vis-{art}-marke-huelle vis-{art}-marke-huelle--{form}'>"
                f"<span tabindex='0' class='vis-{art}-marke' data-testid='{testid}' {extra}>{text}</span>"
                f"<span class='k-nur-sr'>Kurzhilfe</span></span>")
    return (huelle("guete", "Vorschau", f"{form}-vorschau")
            + huelle("modus", "Ohne Grundlagenbild", f"{form}-modus", "data-modus='ohne-grundlagenbild'")
            + "<span class='k-tooltip vis-guete-marke-huelle vis-guete-marke-huelle--" + form + "'>"
            + f"<span tabindex='0' class='vis-guete-marke' data-testid='{form}-freies-bild' data-freies-bild='ja'"
            + " data-form='" + form + "'>freies Bild</span><span class='k-nur-sr'>Kurzhilfe</span></span>")


def flaechen() -> str:
    """Die drei Flächen, aufgebaut wie in der Kopie."""
    hoehe = 38 + blatt_marken_h()
    return (
        "<div class='vis-node-koerper' data-flaeche='blatt' style='position:relative;width:184px;"
        f"height:{hoehe}px'>"
        "<div class='vis-node-blatt'><div class='vis-node-blatt-zeile'>"
        "<button class='k-button k-button--sm'>Aufs Blatt</button></div>"
        f"<div class='vis-node-blatt-marken' data-testid='blatt-marken'>{_marken('abzeichen')}</div></div></div>"
        "<div style='display:grid;grid-template-columns:216px;margin-top:24px'>"
        "<div class='vis-raster-karte' data-flaeche='karte' style='width:216px;height:162px'>"
        "<div style='position:absolute;inset:0;background:#c45f3a'></div>"
        "<div class='vis-raster-karte-embleme'><span class='vis-raster-karte-id'>V-01</span>"
        f"<span class='vis-raster-karte-embleme-rechts'>{_marken('abzeichen')}</span></div>"
        "<div class='vis-raster-karte-fuss'><span class='vis-raster-karte-meta'>V-01</span></div></div></div>"
        "<div class='vis-vergleich-karte' data-flaeche='vergleich' style='position:relative;width:330px;"
        "height:200px;margin-top:24px'><div style='position:absolute;inset:0;background:#c45f3a'></div>"
        f"<div class='vis-marken-leiste'>{_marken('bild')}</div></div>")


_SKRIPT = r"""
function miss(wo) {
  const fehler = [], gesehen = [], EPS = 1;
  const innen = (a, b) => a.left >= b.left - EPS && a.right <= b.right + EPS && a.top >= b.top - EPS && a.bottom <= b.bottom + EPS;
  for (const flaeche of document.querySelectorAll('[data-flaeche]')) {
    const name = wo + ' · ' + flaeche.dataset.flaeche;
    const marken = Array.from(flaeche.querySelectorAll('.vis-guete-marke, .vis-modus-marke'));
    for (const el of marken) {
      const id = el.dataset.testid;
      if (el.dataset.freiesBild === 'ja') gesehen.push(flaeche.dataset.flaeche);
      if (el.scrollWidth > el.clientWidth + EPS) fehler.push(name + ' ' + id + ': läuft seitlich über');
      if (el.scrollHeight > el.clientHeight + EPS) fehler.push(name + ' ' + id + ': läuft unten über');
      const r = document.createRange(); r.selectNodeContents(el);
      const zeilen = Array.from(r.getClientRects()).filter((q) => q.width > 0);
      if (!zeilen.length) fehler.push(name + ' ' + id + ': kein Text');
      for (const q of zeilen) {
        if (!innen(q, el.getBoundingClientRect())) fehler.push(name + ' ' + id + ': Text ragt aus der Marke');
        for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          const s = getComputedStyle(a);
          if ((s.overflowX !== 'visible' || s.overflowY !== 'visible') && !innen(q, a.getBoundingClientRect())) {
            fehler.push(name + ' ' + id + ': Text abgeschnitten von ' + (a.className || a.tagName)); break;
          }
        }
        const oben = document.elementFromPoint((q.left + q.right) / 2, (q.top + q.bottom) / 2);
        if (oben && !el.contains(oben) && !oben.contains(el)) fehler.push(name + ' ' + id + ': Text verdeckt von ' + (oben.className || oben.tagName));
      }
    }
  }
  return { fehler, gesehen };
}
(async () => {
  const aus = { fehler: [], gesehen: [], stil: !!document.querySelector('link[rel=stylesheet]') };
  try {
    await new Promise((r) => setTimeout(r, 300));
    for (const [wo, gross] of [['normal', false], ['grosse Schrift', true]]) {
      if (gross) document.documentElement.setAttribute('data-schrift', 'gross');
      await new Promise((r) => setTimeout(r, 100));
      const m = miss(wo);
      aus.fehler.push(...m.fehler); aus.gesehen.push(...m.gesehen.map((g) => wo + ' · ' + g));
    }
  } catch (err) { aus.fehler.push('Probe brach ab: ' + err.message); }
  document.getElementById('ergebnis').textContent = JSON.stringify(aus);
})();
"""


def _zeilen_probe():
    spec = importlib.util.spec_from_file_location("umfeld_zeilen_probe", WURZEL / "tools" / "umfeld_zeilen_probe.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def chromium() -> str:
    """Derselbe Browser wie die übrigen Proben am Bau."""
    return _zeilen_probe().chromium()


def stil_des_baus(bau: Path = BAU) -> list[str]:
    """Die Stilblätter, die ``dist/index.html`` einbindet (relativ zu ``dist``)."""
    text = (bau / "index.html").read_text(encoding="utf-8")
    return re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="\.?/?([^"]+)"', text)


def pruefseite(bau: Path = BAU) -> str:
    links = "".join(f"<link rel='stylesheet' href='dist/{h}'>" for h in stil_des_baus(bau))
    return ("<!doctype html><html><head><meta charset='utf-8'>" + links
            + "<style>body{margin:24px;background:#0d0f12}</style></head><body>" + flaechen()
            + "<pre id='ergebnis'>laeuft</pre><script>" + _SKRIPT + "</script></body></html>")


class _Leise(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D401 - kein Zugriffsprotokoll im Testlauf
        pass


def pruefe(bau: Path = BAU, browser: str | None = None) -> dict:
    """Fährt die Probe am Bau ``bau`` und liefert ``{fehler, gesehen, stil}``."""
    browser = browser or chromium()
    with tempfile.TemporaryDirectory() as tmp:
        wurzel = Path(tmp)
        (wurzel / "dist").symlink_to(bau.resolve(), target_is_directory=True)
        (wurzel / "probe.html").write_text(pruefseite(bau), encoding="utf-8")
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(_Leise, directory=str(wurzel)))
        faden = threading.Thread(target=server.serve_forever, daemon=True)
        faden.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/probe.html"
            lauf = subprocess.run(
                [browser, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                 "--window-size=900,900", "--force-device-scale-factor=1",
                 "--virtual-time-budget=20000", "--dump-dom", url],
                capture_output=True, text=True, timeout=180)
        finally:
            server.shutdown()
            server.server_close()
    treffer = re.search(r'<pre id="ergebnis">(.*?)</pre>', lauf.stdout, re.S)
    if not treffer or treffer.group(1) == "laeuft":
        return {"fehler": ["Probe lieferte kein Ergebnis (Browser: " + lauf.stderr[-300:] + ")"],
                "gesehen": [], "stil": False}
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
        print(f"Flächen gemessen: {ergebnis['gesehen']}, Funde: {len(ergebnis['fehler'])}")
        for f in ergebnis["fehler"]:
            print("  ROT  " + f)
    return 1 if ergebnis["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
