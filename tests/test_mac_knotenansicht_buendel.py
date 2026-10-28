"""Die Mac-App lädt die Knotenansicht aus ihrem eigenen Bündel («Visbox eigenständig», Schritt 1,
20.10.2026; Plan ``docs/PLAN_VISBOX_EIGENSTAENDIG_2026-10-20.md`` §3, §7).

Bis dahin öffnete die Mac-App ``https://<heim-pc>/knoten/`` — ohne Heim-PC keine Oberfläche.
Seither liegt der Bau im Bündel (``Contents/Resources/Knoten``), die App bedient ihn über ein
eigenes Adressschema (``visbox://app/knoten/``) und reicht nur die Datenwege an den Heim-PC
weiter.

Swift lässt sich hier nicht übersetzen (das tut die Prüfstrecke am Mac); die Regel selbst steht
im Kern und hat dort Proben (``KnotenwegeTests``). Bewacht wird hier, was der Kern nicht sehen
kann: die **Abschriften** gegen den Server (Datenwege, Typen, Bereiche), die **Prüfstrecke**
(der Bau kommt ins Bündel) und die **Verdrahtung** (die App lädt die Knoten nicht mehr vom
Heim-PC, die Seite den Ursprung nicht aus ``location.origin``).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"
WEGE = KERN / "Knotenwege.swift"
WAHL = KERN / "Flaechenwahl.swift"
MAC = WURZEL / "ipad" / "VisboxMac"
START = MAC / "Sources" / "VisboxMac" / "Start"
ARBEIT = START / "Arbeitsansicht.swift"
QUELLE = START / "Knotenquelle.swift"
ABLAUF = WURZEL / ".github" / "workflows" / "ipad.yml"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten"


@pytest.fixture
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


def _code(datei: Path) -> str:
    """Ohne ganze Kommentarzeilen — ein Kommentar darf erklären, was NICHT mehr geschieht."""
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith("//"))


def _swift_text(name: str) -> str:
    treffer = re.search(rf'static let {name}\s*=\s*"([^"]*)"', _code(WEGE))
    assert treffer, f"{name} fehlt in Knotenwege.swift"
    return treffer.group(1)


# ------------------------------------------------------------- Abschriften gegen den Server

def test_die_datenwege_der_app_sind_die_des_servers(server):
    block = re.search(r"static let datenwege: Set<String> = \[(.*?)\]", _code(WEGE), re.S)
    assert block, "Knotenwege.datenwege hat seine Form geändert"
    app = set(re.findall(r'"([^"]+)"', block.group(1)))
    serverwege = {wert for name, wert in vars(server).items()
                  if name.startswith("WEG_KNOTEN_") and isinstance(wert, str)}
    assert app == serverwege, (sorted(app ^ serverwege), "fehlt auf einer Seite")


def test_die_bereiche_sind_die_des_servers(server):
    assert _swift_text("bereich") == server.WEG_KNOTEN
    assert _swift_text("bruecke") == server.WEG_BRUECKE
    assert _swift_text("ordnerImBuendel") == "Knoten"


def test_die_typen_der_app_sind_die_des_servers(server):
    block = re.search(r"static let typen: \[String: String\] = \[(.*?)\]", _code(WEGE), re.S)
    assert block, "Knotenwege.typen hat seine Form geändert"
    app = dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', block.group(1)))
    assert app == server.KNOTEN_TYPEN


def test_das_schema_der_app_ist_das_der_seite():
    """``EIGENES_SCHEMA`` in ``mappe.ts`` ist ``Knotenwege.schema`` mit Doppelpunkt — sonst
    schickte die Seite in der App Formulare ungepackt."""
    mappe = (WIRT / "src" / "mappe.ts").read_text(encoding="utf-8")
    seite = re.search(r"export const EIGENES_SCHEMA = '([a-z]+):'", mappe)
    assert "static let schema = Marke.name.lowercased()" in _code(WEGE)
    marke = re.search(r'static let name = "([^"]+)"', _code(KERN / "Marke.swift")).group(1)
    assert seite and seite.group(1) == marke.lower()
    assert _swift_text("rechner") == "app"


# ------------------------------------------------------------- der Bau kommt ins Bündel

def test_die_pruefstrecke_legt_den_bau_ins_buendel(server):
    import yaml

    ablauf = yaml.safe_load(ABLAUF.read_text(encoding="utf-8"))
    schritte = ablauf["jobs"]["mac"]["steps"]
    befehle = "\n".join(s.get("run", "") for s in schritte)
    kopie = re.search(r'ditto (\S+) "\$BUENDEL/Contents/Resources/Knoten"', befehle)
    assert kopie, "der Bau der Knotenansicht kommt nicht ins Mac-Bündel"
    # Vom Arbeitsort des Jobs aus genau der Bau, den auch der Server ausliefert.
    assert (MAC / kopie.group(1)).resolve() == server.KNOTEN_BAU.resolve()
    assert f"test -f {kopie.group(1)}/index.html" in befehle      # das Tor vor der Kopie
    # Kopiert wird VOR der Unterschrift — danach braeche jede neue Datei das Siegel.
    namen = [s.get("name", "") for s in schritte]
    zusammen = next(i for i, s in enumerate(schritte) if kopie.group(0) in s.get("run", ""))
    # Seit Entscheid 128 heisst der Schritt «Unterschrift (festes Eigenzertifikat, sonst Behelf)».
    unterschrift = next(i for i, n in enumerate(namen) if n.startswith("Unterschrift"))
    assert zusammen < unterschrift
    auskunft = [s for s in schritte if "Knotenansicht im Buendel" in s.get("name", "")]
    # Seit A0012 (28.10.2026) ein Tor: kein `continue-on-error`, scheitert hart.
    assert len(auskunft) == 1 and not auskunft[0].get("continue-on-error")
    assert "index.html" in auskunft[0]["run"]
    # Ein neuer Bau startet den Mac-Lauf.
    for art in ("push", "pull_request"):
        wege = ablauf[True][art]["paths"] if True in ablauf else ablauf["on"][art]["paths"]
        assert "kosmovis/apps/visbox-knoten/dist/**" in wege, art


def test_der_eingecheckte_bau_ist_verschiebbar():
    """Der Bau lädt seine Teile relativ (``./assets/…``) — sonst suchte WebKit sie im eigenen
    Schema unter ``visbox://app/assets/…``, ausserhalb des Bereichs."""
    index = (WIRT / "dist" / "index.html").read_text(encoding="utf-8")
    verweise = re.findall(r'(?:src|href)="([^"]+)"', index)
    assert verweise and all(v.startswith("./") for v in verweise), verweise
    for v in verweise:
        assert (WIRT / "dist" / v).is_file(), v
    css = "".join(p.read_text(encoding="utf-8") for p in (WIRT / "dist" / "assets").glob("*.css"))
    absolut = [u for u in re.findall(r"url\(([^)]+)\)", css)
               if u.strip("'\"").startswith("/")]
    assert not absolut, absolut


# ------------------------------------------------------------- die Verdrahtung in der App

def test_die_app_laedt_die_knoten_nicht_mehr_vom_heim_pc():
    wahl = _code(WAHL)
    assert "if ausDemBuendel { return Knotenwege.einstieg }" in wahl
    assert re.search(r"case \.knoten: return true\s*\n\s*case \.seite: return false", wahl)
    arbeit = _code(ARBEIT)
    assert "setURLSchemeHandler(context.coordinator.quelle, forURLScheme: Knotenwege.schema)" in arbeit
    # Die Knoten auch ohne Heim-PC: die Fläche verlangt ihn nur noch für die Seite.
    assert "if wahl.ausDemBuendel || (leitung.adresse != nil && leitung.anmeldung != nil)" in arbeit
    assert '"/knoten/"' not in arbeit and '"/knoten"' not in arbeit


def test_die_quelle_reicht_mit_den_regeln_der_app_weiter():
    """Dieselben Regeln wie jede Anfrage der App: angeheftetes Zertifikat, kein Proxy, kein
    Zwischenspeicher — und die Köpfe aus dem Kern (Anmeldung der App, ``X-Geraet: mac``)."""
    quelle = _code(QUELLE)
    assert "final class Knotenquelle: NSObject, WKURLSchemeHandler" in quelle
    assert "delegate: Heimvertrauenslotse.gemeinsam" in quelle
    assert "art.connectionProxyDictionary = [:]" in quelle
    assert "art.urlCache = nil" in quelle and "art.httpCookieStorage = nil" in quelle
    assert "Knotenwege.ziel(adresse: adresse)" in quelle
    assert "Knotenwege.koepfeFuerHeim(seite: vonDerSeite, anmeldung: anmeldung)" in quelle
    assert "Knotenwege.koepfeFuerSeite(heim: koepfe)" in quelle
    assert "Knotenwege.satzOhneHeim" in quelle
    # Nach `stop` meldet sie nichts mehr (WebKit bricht sonst das Programm ab).
    assert "func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask)" in quelle
    assert "self.laufend[kennung] != nil" in quelle
    # Und kein eigenes Kennwort-Handwerk: die Anmeldung kommt herein, nicht aus einem Speicher.
    assert "UserDefaults" not in quelle and "SecItem" not in quelle


def test_die_seite_baut_die_bruecke_nicht_aus_dem_ursprung():
    mappe = (WIRT / "src" / "mappe.ts").read_text(encoding="utf-8")
    code = "\n".join(z for z in mappe.splitlines() if not z.lstrip().startswith(("*", "//", "/*")))
    assert "location.origin" not in code
    assert "localStorage.setItem('kosmo.bridge', brueckenAdresse())" in code
    main = (WIRT / "src" / "main.tsx").read_text(encoding="utf-8")
    # Seit Schritt 2 (20.10.2026) liegt um den Umschlag noch `brueckeSagtDenSatz` (ohne Rechner ein
    # Satz am Render-Knoten, `tests/test_mac_ohne_rechner.py`); die Bytes macht weiter dieser.
    assert "koerperAlsBytes(window.fetch.bind(window))" in main
    # Der Umschlag vor allem, was die Seite sonst holt.
    assert main.index("koerperAlsBytes(window.fetch") < main.index("brueckeAufDiesenServer();")
