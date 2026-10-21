"""STIL-PROBE — greifen die Stile der Knotenansicht im Bau? (21.10.2026)

**Anlass:** Befund des Owners am Mac (Fassung 0.3.15–0.3.17): Links unten in der Knotenansicht lag
die Insel-Oberfläche ohne Stil als Spalte — vier Werkzeugknöpfe untereinander, darunter «SONNE» mit
einem doppelten «Sonnenstunden», die Kugel des Assistenten als grosses Feld mit nacktem Text; Claudes
offene Karte war unsichtbar (unter dem Fensterrand), und ein einzelner Knopf «Senden» schwebte ohne
Feld. Die Ursache war **eine** fehlende schliessende Klammer in ``vis-visual.css`` (nach
``.vis-raster-gross-urteil {``), entstanden beim Zusammenführen auf dem Hilfszweig. Im Bau landen
alle Stile in einer Datei hintereinander — darum stand danach fast die Hälfte der Regeln (Inseln,
Kugel, Claude-Marke, Gesprächsfeld) verschachtelt unter dieser einen Regel und griff nirgends.

Weder ``tsc`` noch Vite noch die Vitest-Proben merken so etwas: Eine offene Klammer ist für sie
gültiges CSS (Verschachtelung). Darum hier zwei Wächter:

1. :func:`pruefe_css` — **ohne Browser**: Jede CSS-Datei der Kopie und der Bau selbst müssen
   geschlossen sein, und keine Regel darf in einer gewöhnlichen Stilregel stecken (dieses Projekt
   verschachtelt nirgends; eine verschachtelte Regel ist darum immer eine verlorene Klammer).
2. :func:`sichtprobe` — **mit Chromium/Chrome**, gegen den Bau: berechnete Stile und Lage der Inseln,
   der Kugel, der Claude-Marke mit offener Karte und des Gesprächsfelds. Das ist der Blick, den der
   Owner hatte, als Zahl.
3. Im selben Lauf die **Knoten Kamera, Stimmung und Varianten** (Optik-Befunde des UI-Workers,
   21.10.2026): kein Teil steht über den 184 px breiten Körper hinaus, jede Reiterleiste ist
   einzeilig, keine zwei Beschriftungen überlappen, und keine Beschriftung bricht zweizeilig um.

Gebrauch::

    python3 tools/stil_probe.py            # beide Wächter gegen den eingecheckten Bau
    python3 tools/stil_probe.py --nur-css  # ohne Browser
    python3 tools/stil_probe.py --dist <ordner> --chrome <pfad>
"""
from __future__ import annotations

import argparse
import functools
import glob
import html
import http.server
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KOSMOVIS = WURZEL / "kosmovis"
BAU = KOSMOVIS / "apps" / "visbox-knoten" / "dist"


# ── 1 · CSS geschlossen ─────────────────────────────────────────────────────────────────────

def css_befunde(text: str) -> list[str]:
    """Befunde einer CSS-Datei: offene/überzählige Klammern und Regeln in einer Stilregel.

    Kommentare und Zeichenketten werden übersprungen. Ein Block, dessen Kopf mit ``@`` beginnt
    (``@media``, ``@supports``, ``@keyframes`` …), darf Regeln enthalten; ein gewöhnlicher
    Stilblock nicht."""
    befunde: list[str] = []
    stapel: list[tuple[str, int]] = []  # (Kopf, Zeile)
    kopf_anfang = 0
    zeile = 1
    i, n = 0, len(text)
    while i < n:
        z = text[i]
        if z == "\n":
            zeile += 1
        if text.startswith("/*", i):
            ende = text.find("*/", i + 2)
            ende = n if ende < 0 else ende + 2
            zeile += text.count("\n", i, ende)
            i = ende
            continue
        if z in "\"'":
            j = i + 1
            while j < n and text[j] != z:
                j += 2 if text[j] == "\\" else 1
            zeile += text.count("\n", i, j)
            i = j + 1
            continue
        if z == "{":
            kopf = re.sub(r"/\*.*?\*/", "", text[kopf_anfang:i], flags=re.S).strip()
            if stapel and not stapel[-1][0].startswith("@"):
                befunde.append(f"Zeile {zeile}: «{kopf[:60]}» steht in der Regel «{stapel[-1][0][:60]}» "
                               f"(Zeile {stapel[-1][1]}) — dort fehlt vermutlich eine schliessende Klammer")
            stapel.append((kopf, zeile))
            kopf_anfang = i + 1
        elif z == "}":
            if not stapel:
                befunde.append(f"Zeile {zeile}: schliessende Klammer ohne offenen Block")
            else:
                stapel.pop()
            kopf_anfang = i + 1
        elif z == ";":
            kopf_anfang = i + 1
        i += 1
    for kopf, z0 in stapel:
        befunde.append(f"Zeile {z0}: «{kopf[:60]}» wird nie geschlossen")
    return befunde


def css_dateien(wurzel: Path = WURZEL) -> list[Path]:
    """Alle CSS-Dateien der Kopie (Quelle und Bau), ohne ``node_modules``."""
    return sorted(p for p in (wurzel / "kosmovis").rglob("*.css") if "node_modules" not in p.parts)


def pruefe_css(wurzel: Path = WURZEL) -> dict[str, list[str]]:
    """``{datei: befunde}`` — leer, wenn alles geschlossen ist."""
    aus: dict[str, list[str]] = {}
    for p in css_dateien(wurzel):
        b = css_befunde(p.read_text(encoding="utf-8"))
        if b:
            aus[str(p.relative_to(wurzel))] = b
    return aus


# ── 2 · Sichtprobe im Browser ───────────────────────────────────────────────────────────────

#: Vor dem Bau eingespielt: die Boten der Mac-App als leere Attrappen — so steht die Seite, wie
#: sie am Mac steht (Gesprächsfeld mit Eingabe statt dem Satz «nur in der App»).
APP_ATTRAPPE = ("window.webkit={messageHandlers:{visboxKi:{postMessage(){}},"
                "visboxWirt:{postMessage(){}}}};")

#: Nach dem Bau eingespielt: misst in drei Schritten und schreibt das Ergebnis als JSON in
#: ``<pre id="stil-probe">``, das ``--dump-dom`` mitliefert.
MESSUNG = r"""
(function () {
  // Einblend-Bewegungen zu Ende führen: Ohne Fenster laufen sie nicht immer weiter.
  function beende() { try { document.getAnimations().forEach((a) => { try { a.finish(); } catch (_) {} }); } catch (_) {} }
  function gerendert(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const c = getComputedStyle(e);
      if (c.visibility === 'hidden' || c.display === 'none' || parseFloat(c.opacity) === 0) return false;
      if (/inset\(50%\)/.test(c.clipPath) || c.clip === 'rect(0px, 0px, 0px, 0px)') return false;
    }
    return true;
  }
  function sicht(el) {
    if (!gerendert(el)) return false;
    const r = el.getBoundingClientRect(), x = r.x + r.width / 2, y = r.y + r.height / 2;
    if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return false;
    const t = document.elementFromPoint(x, y);
    return !!t && (t === el || el.contains(t) || t.contains(el));
  }
  function box(el) { if (!el) return null; const r = el.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); }
  const q = (s) => document.querySelector(s);
  const knopf = (t) => [...document.querySelectorAll('button')].find((b) => t.test(b.textContent.trim()));
  const blatt = (t) => [...document.querySelectorAll('body *')].find((e) => e.children.length === 0 && e.textContent.trim() === t);
  const aus = { breite: innerWidth, hoehe: innerHeight };
  // Was ein Vorfahr mit overflow abschneidet, ist nicht zu sehen (z. B. die dritte Zeile der Wahl).
  function sichtRect(e) {
    const r = e.getBoundingClientRect(); let l = r.left, o = r.top, re = r.right, u = r.bottom;
    for (let x = e.parentElement; x && x.nodeType === 1; x = x.parentElement) {
      if (getComputedStyle(x).overflow !== 'visible') { const p = x.getBoundingClientRect(); l = Math.max(l, p.left); o = Math.max(o, p.top); re = Math.min(re, p.right); u = Math.min(u, p.bottom); }
      if (x.hasAttribute('data-knoten-koerper')) break;
    }
    return re - l > 0.5 && u - o > 0.5 ? { left: l, top: o, right: re, bottom: u } : null;
  }
  // Optik-Befunde 1–3 (UI-Worker, 21.10.2026): Überstand über den Körper, Reiterleisten,
  // überlappende und zweizeilige Beschriftungen — in Körper-Pixeln (der Zoom ist herausgerechnet).
  function knotenMessung() {
    const m = {};
    for (const art of ['kamera', 'stimmung', 'varianten']) {
      const w = q('[data-knoten-koerper] [data-testid="' + art + '"]');
      if (!w) { m[art] = null; continue; }
      const k = w.closest('[data-knoten-koerper]'), kb = k.getBoundingClientRect();
      const s = kb.width / k.offsetWidth || 1;
      const zu = (e) => { for (let x = e; x && x !== k; x = x.parentElement) { const c = getComputedStyle(x); if (c.display === 'none' || c.visibility === 'hidden' || parseFloat(c.opacity) === 0 || x.getAttribute('role') === 'tooltip') return true; } return false; };
      let rechts = 0, unten = 0, wer = '';
      for (const e of w.querySelectorAll('*')) {
        if (e.children.length > 0 && !/^(BUTTON|INPUT|LABEL|SELECT)$/.test(e.tagName)) continue;
        const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1 || zu(e)) continue;
        const dr = (r.right - kb.right) / s, du = (r.bottom - kb.bottom) / s;
        if (Math.max(dr, du) > Math.max(rechts, unten)) wer = (e.textContent || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 30);
        rechts = Math.max(rechts, dr); unten = Math.max(unten, du);
      }
      const leisten = [...w.querySelectorAll('.k-tabs')].filter((e) => !zu(e)).map((e) => Math.round(e.getBoundingClientRect().height / s * 10) / 10);
      const namen = [...w.querySelectorAll('.k-checkbox-label, .k-switch-label')].filter((e) => !zu(e));
      const ueber = [];
      for (let i = 0; i < namen.length; i++) for (let j = i + 1; j < namen.length; j++) {
        const a = sichtRect(namen[i]), b = sichtRect(namen[j]); if (!a || !b) continue;
        if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5) ueber.push(namen[i].textContent.trim() + ' / ' + namen[j].textContent.trim());
      }
      const zweizeilig = namen.filter((e) => sichtRect(e) && e.getBoundingClientRect().height / s > 24).map((e) => e.textContent.trim());
      m[art] = { rechts: Math.round(rechts * 10) / 10, unten: Math.round(unten * 10) / 10, wer, leisten, ueberlappt: ueber, zweizeilig };
    }
    return m;
  }
  function schreibe() { const p = document.createElement('pre'); p.id = 'stil-probe'; p.textContent = JSON.stringify(aus); document.body.appendChild(p); }
  setTimeout(function () {
    beende();
    try {
      aus.wurzel = !!q('.app-wurzel[data-station="vis"]');
      aus.thema = document.documentElement.dataset.theme || null;
      aus.inseln = {};
      for (const n of ['graph', 'ansicht', 'stimmung', 'austausch', 'sonne']) {
        const e = q('[data-testid="island-' + n + '-root"]');
        aus.inseln[n] = e ? { pos: getComputedStyle(e).position, box: box(e.querySelector('button') || e) } : null;
      }
      aus.knoten = knotenMessung();
      const orb = q('[data-testid="kosmo-orb-wurzel"] button');
      aus.kugel = orb ? { pos: getComputedStyle(orb.parentElement).position, box: box(orb), sicht: sicht(orb) } : null;
      // Die Sonne aufklappen: Der Titel der Pille ist in der Leiste nur für Vorleser da.
      const sonne = q('[data-testid="island-sonne-root"] button'); if (sonne) sonne.click();
    } catch (e) { aus.fehler = String(e); }
    setTimeout(function () {
      beende();
      try {
        aus.titel_sichtbar = [...document.querySelectorAll('.isl-leiste .isl-werkzeug-titel')].filter(gerendert).map((e) => e.textContent.trim());
        // Claude verbunden, eine offene Karte (wie K-3 im Demolauf am Mac).
        window.visboxWirt.lage({ claude: { verbunden: true }, assistent: { beitraege: [], wartet: false, stand: 'bereit' } });
        const g = JSON.stringify(window.visboxKi.rufe({ kennung: 'P-0', werkzeug: 'graph_lesen' }, 'karte'));
        const gid = (g.match(/"graphId":"([^"]+)"/) || [])[1], nid = (g.match(/"nodeId":"([^"]+)"/) || [])[1];
        window.visboxKi.rufe({ kennung: 'P-1', werkzeug: 'vis_nodeSchieben', argumente: { graphId: gid, nodeId: nid, x: 40, y: 40 } }, 'karte');
      } catch (e) { aus.fehler = String(e); }
      setTimeout(function () {
        beende();
        try {
          aus.claude = { marke: sicht(q('[data-testid="claude-verbunden"]')), offen: sicht(knopf(/^\d+ offen$/)),
                         karte: sicht(blatt('Vorschlag von Claude')), box: box(q('[data-testid="claude-verbunden"]')) };
          const k = q('[data-testid="kosmo-orb-wurzel"] button'); if (k) k.click();
        } catch (e) { aus.fehler = String(e); }
        setTimeout(function () {
            beende();
          try {
            const feld = q('[data-testid="kosmo-input"]'), senden = q('[data-testid="kosmo-send"]');
            const panel = feld && feld.closest('aside');
            aus.gespraech = { feld: sicht(feld), senden: sicht(senden), feld_box: box(feld), senden_box: box(senden),
                              panel_pos: panel ? getComputedStyle(panel).position : null };
          } catch (e) { aus.fehler = String(e); }
          schreibe();
        }, 900);
      }, 700);
    }, 700);
  }, 2500);
})();
"""


def finde_chrome(vorgabe: str | None = None) -> str | None:
    if vorgabe:
        return vorgabe if Path(vorgabe).is_file() else None
    treffer = sorted(glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome"))
    if treffer:
        return treffer[-1]
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        pfad = shutil.which(name)
        if pfad:
            return pfad
    return None


def miss(bau: Path, chrome: str, breite: int = 1440, hoehe: int = 900) -> dict:
    """Öffnet den Bau in Chrome (ohne Fenster) und gibt die Messung zurück."""
    seite = (bau / "index.html").read_text(encoding="utf-8")
    seite = seite.replace("<head>", f"<head><script>{APP_ATTRAPPE}</script>", 1)
    seite = seite.replace("</body>", f"<script>{MESSUNG}</script></body>", 1)
    rumpf = seite.encode("utf-8")

    class Diener(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_a):
            pass

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(rumpf)))
                self.end_headers()
                self.wfile.write(rumpf)
                return
            super().do_GET()

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Diener, directory=str(bau)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
        lauf = subprocess.run(
            [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={breite},{hoehe}", "--virtual-time-budget=10000", "--dump-dom", url],
            capture_output=True, text=True, timeout=180)
    finally:
        server.shutdown()
    treffer = re.search(r'<pre id="stil-probe">(.*?)</pre>', lauf.stdout, re.S)
    if not treffer:
        raise RuntimeError("Die Messung kam nicht zurück: " + (lauf.stderr or lauf.stdout)[-400:])
    return json.loads(html.unescape(treffer.group(1)))


def befunde_der_messung(m: dict) -> list[str]:
    """Was an der Messung nicht stimmt — leer, wenn die Stile greifen."""
    b: list[str] = []
    if m.get("fehler"):
        b.append(f"Fehler in der Seite: {m['fehler']}")
    w, h = m.get("breite", 0), m.get("hoehe", 0)
    if not m.get("wurzel"):
        b.append("Keine Wurzel .app-wurzel[data-station='vis']")
    if m.get("thema") not in ("orbit", "paper"):
        b.append(f"Kein Thema an <html> (data-theme = {m.get('thema')!r})")
    inseln = m.get("inseln") or {}
    #: Wo der erste Knopf jeder Insel sitzt — am Rand, nicht in einer Spalte links unten.
    lagen = {"graph": lambda x, y: x < 60 and 80 < y < h - 80,
             "ansicht": lambda x, y: y < 60 and 60 < x < w - 60,
             "stimmung": lambda x, y: x > w - 80 and 80 < y < h - 80,
             "austausch": lambda x, y: y > h - 80 and 60 < x < w - 60,
             "sonne": lambda x, y: x < 60 and y > h / 2}
    for name, passt in lagen.items():
        i = inseln.get(name)
        if not i:
            b.append(f"Insel «{name}» fehlt")
            continue
        if i["pos"] not in ("fixed", "absolute"):
            b.append(f"Insel «{name}» ist nicht positioniert (position: {i['pos']})")
        x, y, bw, bh = i["box"]
        if not passt(x + bw / 2, y + bh / 2):
            b.append(f"Insel «{name}» sitzt nicht an ihrem Rand ({i['box']})")
    k = m.get("kugel")
    if not k:
        b.append("Kugel des Assistenten fehlt")
    else:
        x, y, bw, bh = k["box"]
        if not (24 <= bw <= 80 and 24 <= bh <= 80) or x < w - 140 or y < h - 140 or not k["sicht"]:
            b.append(f"Kugel nicht als kleiner Knopf rechts unten ({k['box']}, sichtbar {k['sicht']})")
    if m.get("titel_sichtbar"):
        b.append(f"Pillentitel in der Leiste sichtbar (doppelt): {m['titel_sichtbar']}")
    c = m.get("claude") or {}
    for teil, satz in (("marke", "Marke «Claude verbunden»"), ("offen", "Zähler «1 offen»"), ("karte", "Karte «Vorschlag von Claude»")):
        if not c.get(teil):
            b.append(f"{satz} bei offener Karte nicht im Fenster ({c.get('box')})")
    b.extend(befunde_der_knoten(m.get("knoten")))
    g = m.get("gespraech") or {}
    if not (g.get("feld") and g.get("senden")):
        b.append(f"Gesprächsfeld nicht ganz zu sehen (Feld {g.get('feld_box')}, Senden {g.get('senden_box')})")
    elif g.get("panel_pos") == "static":
        b.append("Gesprächsfeld nicht positioniert (position: static)")
    return b


#: Eine Reiterleiste ist einzeilig, solange sie unter dieser Höhe bleibt (Körper-Pixel): einzeilig
#: misst sie 22–29 (je nach Zoom, die Ränder halten ihre Bildschirmbreite), zweizeilig über 50.
LEISTE_EINZEILIG = 36
#: So viel darf ein Teil wegen Rundung über die Körperkante ragen (Körper-Pixel).
UEBERSTAND_DULDUNG = 0.5


def befunde_der_knoten(k: dict | None) -> list[str]:
    """Optik-Befunde 1–3 (UI-Worker, 21.10.2026) an der Messung der drei Knoten — leer, wenn
    nichts übersteht, jede Leiste einzeilig ist und keine Beschriftung überlappt oder umbricht."""
    if not k:
        return ["Knoten Kamera, Stimmung, Varianten nicht gemessen"]
    b: list[str] = []
    for art in ("kamera", "stimmung", "varianten"):
        x = k.get(art)
        if not x:
            b.append(f"Knoten «{art}» fehlt im Startgraphen")
            continue
        if x["rechts"] > UEBERSTAND_DULDUNG or x["unten"] > UEBERSTAND_DULDUNG:
            b.append(f"Knoten «{art}»: «{x['wer']}» steht über den Körper "
                     f"(rechts {x['rechts']} px, unten {x['unten']} px)")
        hohe = [h for h in x["leisten"] if h > LEISTE_EINZEILIG]
        if hohe:
            b.append(f"Knoten «{art}»: Reiterleiste bricht um (Höhe {hohe})")
        if x["ueberlappt"]:
            b.append(f"Knoten «{art}»: Beschriftungen überlappen ({', '.join(x['ueberlappt'][:4])})")
        if x["zweizeilig"]:
            b.append(f"Knoten «{art}»: Beschriftung bricht zweizeilig um ({', '.join(x['zweizeilig'])})")
    return b


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dist", default=str(BAU), help="Ordner des Baus (Vorgabe: der eingecheckte).")
    ap.add_argument("--chrome", default=None, help="Pfad zu Chromium/Chrome, sonst gesucht.")
    ap.add_argument("--nur-css", action="store_true", help="Nur die Klammern, ohne Browser.")
    a = ap.parse_args(argv)
    rot = False
    css = pruefe_css()
    for datei, bs in css.items():
        rot = True
        for x in bs:
            print(f"CSS {datei}: {x}")
    if not css:
        print(f"CSS: {len(css_dateien())} Dateien geschlossen.")
    if not a.nur_css:
        chrome = finde_chrome(a.chrome)
        if not chrome:
            print("Kein Chromium/Chrome gefunden — Sichtprobe nicht gefahren.")
            return 2
        m = miss(Path(a.dist), chrome)
        bs = befunde_der_messung(m)
        for x in bs:
            print(f"SICHT: {x}")
        if not bs:
            print("Sicht: Inseln am Rand, Kugel klein, Claude-Karte und Gesprächsfeld zu sehen; "
                  "Kamera, Stimmung und Varianten ohne Überstand und Überlappung.")
        rot = rot or bool(bs)
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
