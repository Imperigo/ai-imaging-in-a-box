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

Vierte Fläche seit 27.10.2026: der 96 × 60-Daumen des Varianten-Knotens (``VariantenDaumen.tsx``), Befund
Geräteprobe R73 bei KosmoOrbit, dort behoben in 112f3b495 und wörtlich übernommen: «Grundlagenbild» brach mitten im
Wort. Die Modus-Marke steht dort in der Form, die die Kopie setzt (heute «symbol»: ein Zeichen, Wortlaut im
``aria-label``). Neu für alle Flächen: kein Wort auf zwei Zeilen (je Wort gemessen) und keine Marke überlappt eine
andere. Eine Marke, die den Zeiger nicht nimmt, steht unter ``zeiger`` (Hinweis, kein Fund).

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


def daumen_modus_form() -> str:
    """Die Form der Modus-Marke am Varianten-Daumen, wie die Kopie sie setzt (``VariantenDaumen.tsx``)."""
    t = re.search(r'<ModusMarke lauf=\{zelle\} testid="varianten-daumen-modus"(?: form="(\w+)")? />',
                  (VIS / "VariantenDaumen.tsx").read_text(encoding="utf-8"))
    return (t.group(1) or "bild") if t else "bild"


_SYMBOL = ("<svg viewBox='0 0 12 12' width='1em' height='1em' aria-hidden='true' focusable='false'>"
           "<rect x='1.5' y='2.5' width='9' height='7' rx='1' fill='none' stroke='currentColor' stroke-width='1.2'/>"
           "<line x1='1.5' y1='10.5' x2='10.5' y2='1.5' stroke='currentColor' stroke-width='1.2'/></svg>")


def _marken(form: str, modus_form: str | None = None, name: str | None = None) -> str:
    """Die drei Marken wie ``GueteMarke``/``ModusMarke``/``FreiesBildMarke`` sie in der Form ``form`` setzen.

    ``modus_form`` setzt die Modus-Marke abweichend, am Daumen in der Form «symbol» (ein Zeichen, der Wortlaut im
    ``aria-label``, KosmoOrbit 112f3b495)."""
    name = name or form
    modus_form = modus_form or form
    def huelle(art, text, testid, extra="", f=form):
        return (f"<span class='k-tooltip vis-{art}-marke-huelle vis-{art}-marke-huelle--{f}'>"
                f"<span tabindex='0' class='vis-{art}-marke' data-testid='{testid}' {extra}>{text}</span>"
                f"<span class='k-nur-sr'>Kurzhilfe</span></span>")
    if modus_form == "symbol":
        modus = huelle("modus", _SYMBOL, f"{name}-modus", "data-modus='ohne-grundlagenbild' role='img' "
                       "aria-label='Ohne Grundlagenbild' data-form='symbol'", "symbol").replace(
            "class='vis-modus-marke'", "class='vis-modus-marke vis-modus-marke--symbol'")
    else:
        modus = huelle("modus", "Ohne Grundlagenbild", f"{name}-modus", "data-modus='ohne-grundlagenbild'", modus_form)
    return (huelle("guete", "Vorschau", f"{name}-vorschau")
            + modus
            + "<span class='k-tooltip vis-guete-marke-huelle vis-guete-marke-huelle--" + form + "'>"
            + f"<span tabindex='0' class='vis-guete-marke' data-testid='{name}-freies-bild' data-freies-bild='ja'"
            + " data-form='" + form + "'>freies Bild</span><span class='k-nur-sr'>Kurzhilfe</span></span>")


def _freies_bild(form: str, name: str) -> str:
    """Nur die Marke «freies Bild» in der Form ``form`` (wie ``FreiesBildMarke``)."""
    return ("<span class='k-tooltip vis-guete-marke-huelle vis-guete-marke-huelle--" + form + "'>"
            + f"<span tabindex='0' class='vis-guete-marke' data-testid='{name}-freies-bild' data-freies-bild='ja'"
            + " data-form='" + form + "'>freies Bild</span><span class='k-nur-sr'>Kurzhilfe</span></span>")


def flaechen() -> str:
    """Die sechs Flächen, aufgebaut wie in der Kopie (der Daumen 96 × 60 px wie ``VariantenDaumen.tsx``).

    Seit Generalprobe 373 (S12, 27.10.2026) dazu: das Raster im Bildvergleich (Körper 184 × 180 px, die Marke über dem
    Gitter in ``vis-raster-oben``, ``VariantenRaster.tsx``) und die grosse Ansicht (Marken in ``vis-gross-marken-oben``
    VOR dem Bild, das bis an die Höhe der Ansicht reicht — darunter lag die Marke vorher hinter der Fusszeile)."""
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
        f"<div class='vis-marken-leiste'>{_marken('bild')}</div></div>"
        "<div style='margin-top:24px'><button type='button' class='vis-vdaumen-bild vis-vdaumen-bild--fertig' "
        "data-flaeche='daumen'><div style='position:absolute;inset:0;background:#c45f3a'></div>"
        f"<div class='vis-marken-leiste'>{_marken('bild', daumen_modus_form(), 'daumen')}</div></button></div>"
        "<div class='vis-node-koerper' data-flaeche='raster' style='position:relative;width:184px;height:180px;"
        "margin-top:24px'><div class='vis-raster' data-testid='varianten-raster'><div class='vis-raster-oben'>"
        + _freies_bild("abzeichen", "raster") + "</div><div class='vis-raster-gitter' style='grid-template-columns:"
        "minmax(0,0.8fr) minmax(0,1fr);grid-template-rows:auto minmax(0,1fr)'><span></span>"
        "<span class='vis-raster-kopf'>Abendstimmung</span><span class='vis-raster-zeilenkopf'>Eingang</span>"
        "<span class='vis-raster-zelle' style='background:#c45f3a'></span></div></div></div>"
        "<div data-flaeche='gross' style='position:relative;width:600px;height:320px;overflow:hidden;margin-top:24px;"
        "display:flex;flex-direction:column'><div style='flex:1;min-height:0;overflow:hidden'>"
        f"<div class='vis-gross-marken-oben'>{_marken('zeile', 'zeile', 'gross')}</div>"
        "<span class='vis-gross-bild-hoch vis-gross-bild-block'><span style='display:block;height:320px;"
        "background:#c45f3a'></span></span></div><div style='height:48px;background:#20242b'>Fusszeile</div></div>")


_SKRIPT = r"""
function miss(wo) {
  const fehler = [], gesehen = [], zeiger = [], EPS = 1;
  const innen = (a, b) => a.left >= b.left - EPS && a.right <= b.right + EPS && a.top >= b.top - EPS && a.bottom <= b.bottom + EPS;
  for (const flaeche of document.querySelectorAll('[data-flaeche]')) {
    const name = wo + ' · ' + flaeche.dataset.flaeche;
    const marken = Array.from(flaeche.querySelectorAll('.vis-guete-marke, .vis-modus-marke'));
    const kisten = marken.map((el) => [el.dataset.testid, el.getBoundingClientRect()]);
    for (let i = 0; i < kisten.length; i++)
      for (let j = i + 1; j < kisten.length; j++) {
        const a = kisten[i][1], b = kisten[j][1];
        if (a.left < b.right - EPS && b.left < a.right - EPS && a.top < b.bottom - EPS && b.top < a.bottom - EPS)
          fehler.push(name + ': ' + kisten[i][0] + ' überlappt ' + kisten[j][0]);
      }
    for (const el of marken) {
      const id = el.dataset.testid;
      if (el.dataset.freiesBild === 'ja') gesehen.push(flaeche.dataset.flaeche);
      if (el.scrollWidth > el.clientWidth + EPS) fehler.push(name + ' ' + id + ': läuft seitlich über');
      if (el.scrollHeight > el.clientHeight + EPS) fehler.push(name + ' ' + id + ': läuft unten über');
      // UI-Regel 2: kein Wort auf zwei Zeilen (je Wort gemessen, wie KosmoOrbit daumen-marke-umbruch).
      for (const t of Array.from(el.childNodes).filter((n) => n.nodeType === 3)) {
        for (const m of t.data.matchAll(/\S+/g)) {
          const w = document.createRange(); w.setStart(t, m.index); w.setEnd(t, m.index + m[0].length);
          const z = new Set(Array.from(w.getClientRects()).filter((q) => q.width > 0).map((q) => Math.round(q.top)));
          if (z.size > 1) fehler.push(name + ' ' + id + ': Wort «' + m[0] + '» ist zerbrochen');
        }
      }
      // Regel 3: ein Symbol trägt den vollen Wortlaut im aria-label; gemessen wird dann das Zeichen.
      const symbol = el.getAttribute('role') === 'img';
      if (symbol && !(el.getAttribute('aria-label') || '').trim()) fehler.push(name + ' ' + id + ': Symbol ohne Namen');
      const r = document.createRange(); r.selectNodeContents(el);
      const zeilen = symbol ? [el.querySelector('svg').getBoundingClientRect()]
        : Array.from(r.getClientRects()).filter((q) => q.width > 0);
      if (!zeilen.length) fehler.push(name + ' ' + id + ': kein Text');
      for (const q of zeilen) {
        if (!innen(q, el.getBoundingClientRect())) fehler.push(name + ' ' + id + ': Text ragt aus der Marke');
        for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          const s = getComputedStyle(a);
          if ((s.overflowX !== 'visible' || s.overflowY !== 'visible') && !innen(q, a.getBoundingClientRect())) {
            fehler.push(name + ' ' + id + ': Text abgeschnitten von ' + (a.className || a.tagName)); break;
          }
        }
        const mx = (q.left + q.right) / 2, my = (q.top + q.bottom) / 2;
        const oben = document.elementFromPoint(mx, my);
        if (oben && !el.contains(oben) && !oben.contains(el)) {
          // Nimmt die Marke den Zeiger gar nicht (pointer-events: none), ist sie nicht verdeckt, sondern für die Maus
          // durchlässig: eigens gemeldet, und mit Zeiger noch einmal auf Verdecken geprüft.
          if (getComputedStyle(el).pointerEvents === 'none') {
            zeiger.push(name + ' ' + id + ': nimmt den Zeiger nicht (Kurzhilfe mit der Maus nicht erreichbar)');
            const alt = el.style.pointerEvents; el.style.pointerEvents = 'auto';
            const nochmal = document.elementFromPoint(mx, my);
            el.style.pointerEvents = alt;
            if (nochmal && !el.contains(nochmal) && !nochmal.contains(el)) fehler.push(name + ' ' + id + ': Text verdeckt von ' + (nochmal.className || nochmal.tagName));
          } else fehler.push(name + ' ' + id + ': Text verdeckt von ' + (oben.className || oben.tagName));
        }
      }
    }
  }
  return { fehler, gesehen, zeiger };
}
(async () => {
  const aus = { fehler: [], gesehen: [], zeiger: [], stil: !!document.querySelector('link[rel=stylesheet]') };
  try {
    await new Promise((r) => setTimeout(r, 300));
    for (const [wo, gross] of [['normal', false], ['grosse Schrift', true]]) {
      if (gross) document.documentElement.setAttribute('data-schrift', 'gross');
      await new Promise((r) => setTimeout(r, 100));
      const m = miss(wo);
      aus.fehler.push(...m.fehler); aus.zeiger.push(...m.zeiger); aus.gesehen.push(...m.gesehen.map((g) => wo + ' · ' + g));
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
                "gesehen": [], "zeiger": [], "stil": False}
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
        for f in ergebnis.get("zeiger", []):
            print("  HINWEIS  " + f)
    return 1 if ergebnis["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
