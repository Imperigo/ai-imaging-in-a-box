"""A0848 «Leerer Start zeigt Weg»: Ohne Mappe sagt die Seite, wie es weitergeht.

Befund des externen Audits (24.11.2026, Station 1, ohne Mappe beginnen): Wer die Visbox-Seite
ohne Mappe öffnete, las im Kopf den Satz des Dienstes mit Programmtext (``--ordner``), viermal
«Noch kein Projekt geöffnet» in den Abschnitten, und «Rechnen» war bedienbar, obwohl es nichts
zu rechnen gab. Jetzt nennt **ein** Satz am Kopf die zwei Wege (Mappe öffnen oder in der
Knotenansicht ein Modell laden, Entscheid 91), und «Rechnen» ist gesperrt, mit seinem Grund.

**Gefahren in Chromium ohne Fenster, gegen den echten Dienst** (``server.baue_server``, nur
``127.0.0.1``). Damit «sichtbar» gemessen und nicht aus Attributen geraten wird, liefert ein
kleiner Vermittler die echte Seite mit einem Messskript am Ende aus und reicht jede andere
Anfrage unverändert an den Dienst weiter. Chromium muss da sein, die Probe überspringt nicht.
Regel 3: die Mappe heisst «Atelier», die Probe nennt keinen Plattenpfad.
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from aiimaging import arbeitsgang

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
WERKZEUGE = WURZEL / "tools"
SEITE = FLAECHE / "seite.html"

#: Die zwei Fenster des Design Systems: das kleinste und das gewöhnliche.
FENSTER = [(1024, 640), (1440, 900)]

#: Die Abschnitte der Seite in ihrer Reihenfolge — sie bleiben stehen, auch ohne Mappe.
ABSCHNITTE = ["Modell", "Was gerechnet würde", "Warteschlange", "Standpunkt",
              "Skizze — Entwurfsmodus", "Bilder"]

LEERSATZ = "Noch kein Projekt geöffnet"

#: Ans Ende der Seite gesetzt: misst nach dem ersten Laden und schreibt das Ergebnis als JSON
#: in ``<pre id="a0848">``, das ``--dump-dom`` mitliefert.
MESSUNG = r"""
<script>
setTimeout(function () {
  function gerendert(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const c = getComputedStyle(e);
      if (c.visibility === "hidden" || c.display === "none" || parseFloat(c.opacity) === 0) return false;
    }
    return true;
  }
  function imFenster(el) {
    if (!gerendert(el)) return false;
    const r = el.getBoundingClientRect();
    return r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth;
  }
  const aus = { breite: innerWidth, hoehe: innerHeight };
  try {
    const knopf = document.getElementById("rechnen");
    const grundIds = (knopf.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
    const gruende = grundIds.map((id) => document.getElementById(id)).filter(Boolean);
    aus.rechnen = {
      gesperrt: knopf.disabled,
      sichtbar: imFenster(knopf),
      grund: gruende.filter(gerendert).map((e) => e.innerText.trim()).filter(Boolean),
      grund_im_fenster: gruende.some(imFenster),
    };
    aus.kopf = document.querySelector("header").innerText;
    aus.modell_laden = [...document.querySelectorAll("a")]
      .filter((a) => a.textContent.trim() === "Modell laden")
      .map((a) => ({ href: a.getAttribute("href"), sicht: gerendert(a), im_fenster: imFenster(a) }));
    aus.leersatz = (document.body.innerText.match(/Noch kein Projekt geöffnet/g) || []).length;
    aus.abschnitte = [...document.querySelectorAll("main > section > h2")]
      .map((h) => (h.firstChild ? h.firstChild.textContent : "").trim());
    aus.stand = document.getElementById("stand").innerText;
  } catch (f) { aus.fehler = String(f); }
  const p = document.createElement("pre"); p.id = "a0848"; p.textContent = JSON.stringify(aus);
  document.body.appendChild(p);
}, 1500);
</script>
"""


def finde_chrome() -> str | None:
    """Chromium wie die Stilprobe (``tools/stil_probe.py``), sonst das der Playwright-Ablage
    (``PLAYWRIGHT_BROWSERS_PATH`` oder ihr gewöhnlicher Ort im Benutzerordner)."""
    sys.path.insert(0, str(WERKZEUGE))
    try:
        import stil_probe
        gefunden = stil_probe.finde_chrome()
    finally:
        sys.path.remove(str(WERKZEUGE))
    if gefunden:
        return gefunden
    ablage = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / ".cache" / "ms-playwright")
    for muster in ("chromium_headless_shell-*/*/chrome-headless-shell", "chromium-*/chrome-linux*/chrome"):
        treffer = sorted(glob.glob(str(ablage / muster)))
        if treffer:
            return treffer[-1]
    return None


@pytest.fixture(scope="module")
def chrome() -> str:
    pfad = finde_chrome()
    assert pfad, "Kein Chromium: diese Probe fährt die Seite im Browser und überspringt nicht"
    return pfad


@pytest.fixture(scope="module")
def server_modul():
    sys.path[:0] = [str(FLAECHE), str(WERKZEUGE)]
    try:
        import make_test_glb
        import server
        return server, make_test_glb
    finally:
        for weg in (str(FLAECHE), str(WERKZEUGE)):
            sys.path.remove(weg)


def _vermittler(ziel: str) -> ThreadingHTTPServer:
    """Liefert ``/`` als echte Seite mit Messskript, alles andere holt er beim Dienst."""
    seite = SEITE.read_text(encoding="utf-8").replace("</body>", MESSUNG + "</body>", 1).encode()

    class Vermittler(BaseHTTPRequestHandler):
        def log_message(self, *_a):
            pass

        def _antworte(self, code: int, art: str, rumpf: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", art)
            self.send_header("Content-Length", str(len(rumpf)))
            self.end_headers()
            self.wfile.write(rumpf)

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                self._antworte(200, "text/html; charset=utf-8", seite)
                return
            try:
                with urllib.request.urlopen(ziel + self.path, timeout=30) as a:
                    self._antworte(a.status, a.headers.get("Content-Type", ""), a.read())
            except urllib.error.HTTPError as f:
                self._antworte(f.code, f.headers.get("Content-Type", ""), f.read())

    return ThreadingHTTPServer(("127.0.0.1", 0), Vermittler)


def _miss(server, chrome: str, ordner=None) -> dict:
    """Die Seite in jedem der zwei Fenster messen — ``{breite: messung}``."""
    dienst = server.baue_server(ordner=ordner, anschluss=0)
    threading.Thread(target=dienst.serve_forever, daemon=True).start()
    vermittler = _vermittler(f"http://127.0.0.1:{dienst.server_address[1]}")
    threading.Thread(target=vermittler.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{vermittler.server_address[1]}/"
        aus = {}
        for breite, hoehe in FENSTER:
            lauf = subprocess.run(
                [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                 f"--window-size={breite},{hoehe}", "--virtual-time-budget=6000", "--dump-dom", url],
                capture_output=True, text=True, timeout=180)
            treffer = re.search(r'<pre id="a0848">(.*?)</pre>', lauf.stdout, re.S)
            assert treffer, "Die Messung kam nicht zurück: " + (lauf.stderr or lauf.stdout)[-400:]
            m = json.loads(html.unescape(treffer.group(1)))
            assert "fehler" not in m, m
            aus[breite] = m
        return aus
    finally:
        vermittler.shutdown()
        dienst.shutdown()


@pytest.fixture(scope="module")
def leer(server_modul, chrome) -> dict:
    """Der Dienst ohne Mappe (kein ``--ordner``, nichts zuletzt geöffnet)."""
    return _miss(server_modul[0], chrome)


@pytest.fixture(scope="module")
def mit_mappe(server_modul, chrome, tmp_path_factory) -> dict:
    """Der Dienst mit einer Mappe über dem synthetischen Situationsmodell."""
    server, make_test_glb = server_modul
    ordner = tmp_path_factory.mktemp("a0848")
    haus = ordner / "situation.glb"
    haus.write_bytes(make_test_glb.baue_glb(make_test_glb.situationsszene()))
    mappe = ordner / "Atelier"
    arbeitsgang.lege_an(mappe, haus, name="Atelier", einstellungen={"up_axis": "Y"})
    return _miss(server, chrome, ordner=mappe)


#: Was in einem Satz für Menschen nach Plattenpfad aussieht.
PFAD = re.compile(r"(?:[A-Za-z]:\\|(?:^|\s)~?/\S|\S/\S+/)")


# ======================================================================================
# Satz 1 · Ohne Mappe: Rechnen gesperrt mit Grund, ein Satz am Kopf, der Weg zum Modell
# ======================================================================================

@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_ohne_mappe_ist_rechnen_gesperrt_und_sagt_warum(leer, breite):
    r = leer[breite]["rechnen"]
    assert r["gesperrt"], "ohne Mappe gibt es nichts zu rechnen"
    assert r["grund"], "der Grund steht sichtbar beim Knopf (aria-describedby)"
    assert r["grund_im_fenster"], "der Grund liegt im Fenster, ohne Rollen"


@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_der_kopf_hat_keinen_programmtext_und_keinen_pfad(leer, breite):
    kopf = leer[breite]["kopf"]
    assert "--" not in kopf, kopf
    assert not PFAD.search(kopf), kopf


@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_modell_laden_fuehrt_auf_die_knotenansicht(leer, breite):
    links = leer[breite]["modell_laden"]
    assert links, "ein Link «Modell laden» steht da"
    assert all(l["href"] == "/knoten/" for l in links), links
    assert any(l["im_fenster"] for l in links), "er ist ohne Rollen zu sehen"


@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_der_leersatz_steht_hoechstens_einmal(leer, breite):
    assert leer[breite]["leersatz"] <= 1, leer[breite]["leersatz"]


@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_ohne_mappe_bleiben_die_abschnitte_stehen(leer, breite):
    assert leer[breite]["abschnitte"] == ABSCHNITTE


# ======================================================================================
# Satz 2 · Bleibt: mit Mappe ist Rechnen bedienbar, die Abschnitte stehen wie heute
# ======================================================================================

@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_mit_mappe_ist_rechnen_bedienbar(mit_mappe, breite):
    m = mit_mappe[breite]
    assert not m["rechnen"]["gesperrt"]
    assert m["rechnen"]["sichtbar"]
    assert m["rechnen"]["grund"] == [], "kein Grund, wenn nichts gesperrt ist"
    assert m["leersatz"] == 0
    assert m["modell_laden"] == [] or not any(l["sicht"] for l in m["modell_laden"])


@pytest.mark.parametrize("breite", [b for b, _ in FENSTER])
def test_mit_mappe_stehen_die_abschnitte_in_derselben_reihenfolge(mit_mappe, breite):
    assert mit_mappe[breite]["abschnitte"] == ABSCHNITTE
