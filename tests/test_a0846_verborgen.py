"""Was die Seite verbirgt, ist auch unsichtbar (A0846 «Verborgenes bleibt verborgen»).

**Befund des externen Audits vom 24.11.2026, Stationen 1 und 3:** Beim Öffnen einer Mappe
standen unter «Was gerechnet würde» alle Felder der vier Rechenschritte aufgeklappt (45 Felder,
gut 3 700 px bis zum Abschnitt «Bilder» bei 1280 px Breite), und «Gewählte als Ebenen
rechnen» stand auch ohne eine einzige wartende Skizze da. Das Skript hatte beides richtig
verborgen (``hidden``) — aber ``.felder { display: grid }`` und ``.knopfzeile { display: flex }``
stehen im Stil über der Regel des Browsers für ``[hidden]``. Ein Attribut, das im DOM stimmt und
auf dem Bildschirm nichts bewirkt, sieht keine Probe ohne Browser.

Darum misst diese Probe die **berechnete** Darstellung in Chromium ohne Fenster, gegen den
echten Dienst (``oberflaeche/server.py``) mit einer synthetischen Mappe: ein Modell ohne Namen,
null, eine oder zwei wartende Skizzen. Das Messskript wird nur in die ausgelieferte Seite
gehängt; die Seite selbst bleibt, wie sie ist.

In ``pruefung.yml`` ist ``AIIMAGING_STILPROBE_PFLICHT=1`` gesetzt; auch sonst ist ein fehlendes
Chrome hier ein Fehler und kein Überspringen: Ohne Browser gibt es diese Messung nicht.

Bildbelege (Satz 3 des Auftrags) schreibt ``test_bildbelege`` nur, wenn ein Zielordner mit
``-o a0846_bilder=<ordner>`` genannt ist; ohne ihn tut sie nichts.
"""
from __future__ import annotations

import glob
import html
import json
import re
import struct
import subprocess
import sys
import threading
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, projekt

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"

#: Die Regel, um die es geht. Die Gegenprobe nimmt genau sie wieder heraus.
REGEL = ".felder[hidden], .knopfzeile[hidden] { display: none; }"

#: Die Abschnitte der Seite in ihrer Reihenfolge — sie bleibt (Satz 2).
ABSCHNITTE = ["Modell", "Was gerechnet würde", "Warteschlange", "Standpunkt",
              "Skizze — Entwurfsmodus", "Bilder"]

#: Misst, sobald die Mappe geladen ist, und schreibt das Ergebnis als JSON in
#: ``<pre id="a0846-messung">``, das ``--dump-dom`` mitliefert.
MESSUNG = r"""
(function () {
  const $ = (id) => document.getElementById(id);
  function sichtbar(el) {
    if (!el) return false;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      if (getComputedStyle(e).display === 'none') return false;
    }
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function anzeige(el) { return { hidden: el.hidden, display: getComputedStyle(el).display, sichtbar: sichtbar(el) }; }
  function messe() {
    const aus = { breite: innerWidth, stand: $('stand').textContent };
    try {
      aus.verborgen = [...document.querySelectorAll('.felder[hidden], .knopfzeile[hidden]')].map((e) => ({
        klasse: e.className, id: e.id || null, display: getComputedStyle(e).display,
        hoehe: Math.round(e.getBoundingClientRect().height) }));
      aus.felder = document.querySelectorAll('.felder').length;
      aus.ebenenzeile = anzeige($('ebenenzeile'));
      aus.abschnitte = [...document.querySelectorAll('main > section > h2')].map((h) => h.firstChild.textContent.trim());
      const bilder = [...document.querySelectorAll('main > section > h2')].find((h) => h.textContent.trim() === 'Bilder');
      aus.bis_bilder = bilder ? Math.round(bilder.getBoundingClientRect().top + scrollY) : null;
      const zeile = [...document.querySelectorAll('.knoten > .zeile')].find((z) => z.parentElement.querySelector(':scope > .felder'));
      if (zeile) {
        const f = zeile.parentElement.querySelector(':scope > .felder');
        aus.vor_klick = anzeige(f);
        zeile.click();
        aus.aufgeklappt = Object.assign(anzeige(f), { eingaben: f.querySelectorAll('input').length });
        zeile.click();
        aus.zugeklappt = anzeige(f);
      }
      zeigeLauf({ laeuft: true, art_des_zeichens: 'unbelegt', fertige: [], knotenart: 'render',
                  nummer: 1, von: 4, seit_s: 1, knoten_seit_s: 1 });
      aus.lauf = { block: sichtbar($('lauf')), abbrechen: anzeige($('abbrechen')) };
    } catch (f) { aus.fehler = String(f); }
    const p = document.createElement('pre'); p.id = 'a0846-messung'; p.textContent = JSON.stringify(aus);
    document.body.appendChild(p);
  }
  let n = 0;
  function bereit() { const s = $('stand').textContent; return /Bilder, /.test(s) || /Projektordner/.test(s); }
  function warte() { if (bereit() || ++n > 80) messe(); else setTimeout(warte, 100); }
  addEventListener('load', () => setTimeout(warte, 100));
})();
"""


# ── Werkzeug ────────────────────────────────────────────────────────────────────────────────

def _chrome() -> str:
    """Chromium/Chrome wie ``tools/stil_probe.py``, dazu der Ablageort von Playwright."""
    sys.path.insert(0, str(WURZEL / "tools"))
    try:
        import stil_probe
    finally:
        sys.path.remove(str(WURZEL / "tools"))
    chrome = stil_probe.finde_chrome()
    if chrome:
        return chrome
    ablage = Path.home() / ".cache" / "ms-playwright"
    # Die Hülle ohne Fenster zuerst: Das volle Chromium kam mit `--dump-dom` am Heim-PC
    # nicht zurück (27.11.2026, nach 60 s abgebrochen).
    for muster in ("chromium_headless_shell-*/chrome-*linux*/chrome-headless-shell",
                   "chromium_headless_shell-*/chrome-linux/headless_shell",
                   "chromium-*/chrome-linux*/chrome"):
        treffer = sorted(glob.glob(str(ablage / muster)))
        if treffer:
            return treffer[-1]
    pytest.fail("Kein Chromium/Chrome — ohne Browser gibt es die Messung von A0846 nicht")


def _png(breite: int = 8, hoehe: int = 6) -> bytes:
    def block(art: bytes, daten: bytes) -> bytes:
        return (struct.pack(">I", len(daten)) + art + daten
                + struct.pack(">I", zlib.crc32(art + daten) & 0xFFFFFFFF))
    zeilen = b"".join(b"\x00" + b"\x80\x80\x80" * breite for _ in range(hoehe))
    return (b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0))
            + block(b"IDAT", zlib.compress(zeilen)) + block(b"IEND", b""))


def _glb(ziel: Path) -> Path:
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    teil = struct.pack("<II", len(js), 0x4E4F534A) + js
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(teil)) + teil)
    return ziel


def _mappe(wurzel: Path, skizzen: int) -> Path:
    """Die synthetische Mappe: ein Modell ohne Namen, ``skizzen`` wartende Skizzen."""
    mappe = wurzel / "mappe"
    arbeitsgang.lege_an(mappe, _glb(wurzel / "quelle" / "modell.glb"), name="Probemappe",
                        einstellungen={"prompt": "Abendlicht", "up_axis": "Y"})
    p = projekt.oeffne(mappe)["projekt"]
    for i in range(skizzen):
        name = f"skizze-{i + 1}.png"
        (mappe / name).write_bytes(_png())
        projekt.vermerke_skizze(p, skizze=name, bemerkung=f"Probe {i + 1}")
    projekt.speichere(p, mappe)
    return mappe


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture(scope="module")
def mappen(tmp_path_factory):
    return {n: _mappe(tmp_path_factory.mktemp(f"a0846-{n}"), n) for n in (0, 1, 2)}


class _Dienst:
    """Der echte Dienst auf einem freien Anschluss, solange der ``with``-Block läuft."""

    def __init__(self, server, ordner):
        self.http = server.baue_server(ordner=ordner, anschluss=0)

    def __enter__(self):
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self.http.server_address[1]}/"

    def __exit__(self, *_a):
        self.http.shutdown()
        self.http.server_close()


def _chromium(chrome: str, url: str, profil: Path, breite: int, hoehe: int, *zusatz: str):
    return subprocess.run(
        [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         f"--user-data-dir={profil}", f"--window-size={breite},{hoehe}",
         "--virtual-time-budget=8000", *zusatz, url],
        capture_output=True, text=True, timeout=60)


def _miss(server, monkeypatch, tmp_path, ordner, *, seite: str | None = None,
          breite: int = 1280, hoehe: int = 900) -> dict:
    text = SEITE.read_text(encoding="utf-8") if seite is None else seite
    tmp_path.mkdir(parents=True, exist_ok=True)
    gemessen = tmp_path / "seite-mit-messung.html"
    gemessen.write_text(text.replace("</body>", f"<script>{MESSUNG}</script></body>", 1),
                        encoding="utf-8")
    monkeypatch.setattr(server, "SEITE", gemessen)
    with _Dienst(server, ordner) as url:
        lauf = _chromium(_chrome(), url, tmp_path / "profil", breite, hoehe, "--dump-dom")
    treffer = re.search(r'<pre id="a0846-messung">(.*?)</pre>', lauf.stdout, re.S)
    assert treffer, "Die Messung kam nicht zurück: " + (lauf.stderr or lauf.stdout)[-400:]
    messung = json.loads(html.unescape(treffer.group(1)))
    assert not messung.get("fehler"), messung["fehler"]
    return messung


# ── Satz 1 · was verborgen ist, ist unsichtbar ──────────────────────────────────────────────

def test_jedes_verborgene_feld_und_jede_verborgene_knopfzeile_ist_unsichtbar(
        server, mappen, monkeypatch, tmp_path):
    m = _miss(server, monkeypatch, tmp_path, mappen[1])
    assert "Bilder, " in m["stand"], f"die Mappe wurde nicht geladen: {m['stand']}"
    gruppen = [v for v in m["verborgen"] if "felder" in v["klasse"].split()]
    assert len(gruppen) >= 3, f"zu wenig zugeklappte Gruppen, um etwas zu messen: {m['verborgen']}"
    sichtbar = [v for v in m["verborgen"] if v["display"] != "none"]
    assert sichtbar == [], f"verborgen und doch dargestellt: {sichtbar}"


@pytest.mark.parametrize("skizzen,sichtbar", [(0, False), (1, False), (2, True)])
def test_ebenen_rechnen_erst_ab_zwei_wartenden_skizzen(
        server, mappen, monkeypatch, tmp_path, skizzen, sichtbar):
    m = _miss(server, monkeypatch, tmp_path, mappen[skizzen])
    assert "Bilder, " in m["stand"], f"die Mappe wurde nicht geladen: {m['stand']}"
    assert m["ebenenzeile"]["hidden"] is (not sichtbar), m["ebenenzeile"]
    assert m["ebenenzeile"]["sichtbar"] is sichtbar, (
        f"«Gewählte als Ebenen rechnen» bei {skizzen} wartenden Skizzen: {m['ebenenzeile']}")


def test_ohne_die_regel_ist_die_messung_rot(server, mappen, monkeypatch, tmp_path):
    """Gegenprobe (Prüfsystematik Punkt 10): ohne die Regel misst dieselbe Probe den Befund
    des Audits — ``grid`` an den zugeklappten Gruppen, ``flex`` an der Ebenenzeile."""
    text = SEITE.read_text(encoding="utf-8")
    assert REGEL in text, "die Regel für [hidden] fehlt in der Seite"
    m = _miss(server, monkeypatch, tmp_path, mappen[1], seite=text.replace(REGEL, "", 1))
    anzeigen = {v["display"] for v in m["verborgen"]}
    assert {"grid", "flex"} <= anzeigen, m["verborgen"]
    assert m["ebenenzeile"]["sichtbar"] is True


# ── Satz 2 · was bleibt ─────────────────────────────────────────────────────────────────────

def test_aufgeklappte_gruppen_zeigen_ihre_felder(server, mappen, monkeypatch, tmp_path):
    m = _miss(server, monkeypatch, tmp_path, mappen[2])
    assert m["vor_klick"]["hidden"] is True and m["vor_klick"]["sichtbar"] is False
    assert m["aufgeklappt"]["hidden"] is False
    assert m["aufgeklappt"]["display"] == "grid", m["aufgeklappt"]
    assert m["aufgeklappt"]["sichtbar"] is True and m["aufgeklappt"]["eingaben"] > 0
    assert m["zugeklappt"]["sichtbar"] is False


def test_lauf_abbrechen_steht_waehrend_eines_laufs(server, mappen, monkeypatch, tmp_path):
    m = _miss(server, monkeypatch, tmp_path, mappen[2])
    assert m["lauf"]["block"] is True
    assert m["lauf"]["abbrechen"]["sichtbar"] is True, m["lauf"]


def test_die_abschnitte_bleiben_in_ihrer_reihenfolge(server, mappen, monkeypatch, tmp_path):
    m = _miss(server, monkeypatch, tmp_path, mappen[2])
    assert m["abschnitte"] == ABSCHNITTE


# ── Satz 3 · Bildbelege ─────────────────────────────────────────────────────────────────────

def _bildordner(request) -> Path | None:
    for eintrag in request.config.getoption("override_ini") or []:
        schluessel, _, wert = eintrag.partition("=")
        if schluessel.strip() == "a0846_bilder" and wert.strip():
            return Path(wert.strip())
    return None


def test_bildbelege(server, mappen, monkeypatch, tmp_path, request):
    """Leerer Start und Prüfmappe in 1024 x 640 und 1440 x 900, dazu die ganze Länge bei
    1280 px und je Zelle die Messung (``messung.json``). Nur mit ``-o a0846_bilder=<ordner>``."""
    ziel = _bildordner(request)
    if ziel is None:
        return
    ziel.mkdir(parents=True, exist_ok=True)
    chrome = _chrome()
    messungen = {}
    for zustand, ordner in (("leer", None), ("pruefmappe", mappen[1])):
        for breite, hoehe in ((1024, 640), (1440, 900), (1280, 900)):
            m = _miss(server, monkeypatch, tmp_path / f"{zustand}-{breite}", ordner,
                      breite=breite, hoehe=hoehe)
            messungen[f"{zustand}-{breite}x{hoehe}"] = m
            if breite == 1280:
                hoehe = max(900, (m.get("bis_bilder") or 0) + 500)
                name = f"{zustand}-1280-ganz.png"
            else:
                name = f"{zustand}-{breite}x{hoehe}.png"
            monkeypatch.setattr(server, "SEITE", SEITE)
            with _Dienst(server, ordner) as url:
                _chromium(chrome, url, tmp_path / f"profil-{zustand}-{breite}", breite, hoehe,
                          f"--screenshot={ziel / name}")
            assert (ziel / name).is_file(), name
    (ziel / "messung.json").write_text(json.dumps(messungen, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
