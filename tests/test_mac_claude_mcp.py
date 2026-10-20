"""Claude über MCP in der Mac-App — nur auf diesem Rechner, ohne fremdes Paket, ohne Geheimnis.

Plan KI-Bedienung (``docs/PLAN_KI_BEDIENUNG_2026-10-20.md``), Stufe 2; Entscheide 106, 106e und
108 B. Die Logik (JSON-RPC, Wartefrist, Host- und Origin-Prüfung, Weg über stdio) prüft
``swift test`` im Kern (``McpkernTests``, ``McpleitungTests``). Die Mac-App übersetzt nur die
Prüfstrecke am Mac; bewacht wird hier darum die **Verdrahtung**: dass der Hörer nur Loopback
bindet, auf 8631, ab Werk an, dass ``--mcp-stdio`` vor dem Fenster greift, dass kein fremdes
Paket hereinkommt und kein Geheimnis im Anschluss steht.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad"
KERN = IPAD / "Visbox.swiftpm" / "Kern"
MAC = IPAD / "VisboxMac"
QUELLEN = MAC / "Sources" / "VisboxMac"
CLAUDE = QUELLEN / "Claude"
PROBEN = IPAD / "VisboxKern" / "Tests" / "VisboxKernTests"


def _code(pfad: Path) -> str:
    """Der Quelltext ohne Zeilenkommentare — bewacht wird, was übersetzt wird."""
    return "\n".join(z for z in pfad.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith("//"))


def _importe(pfad: Path) -> set[str]:
    return set(re.findall(r"^[ \t]*import[ \t]+(\w+)", pfad.read_text(encoding="utf-8"), re.M))


def _claude_dateien() -> list[Path]:
    dateien = sorted(CLAUDE.glob("*.swift"))
    assert dateien, "keine Dateien unter VisboxMac/…/Claude"
    return dateien


# ------------------------------------------------------------------- nur dieser Rechner

def test_der_hoerer_bindet_nur_loopback():
    code = _code(CLAUDE / "Claudeanschluss.swift")
    assert "requiredLocalEndpoint = NWEndpoint.hostPort(host: .ipv4(.loopback), port: anschluss)" in code
    assert "requiredInterfaceType = .loopback" in code
    assert "includePeerToPeer = false" in code
    assert "NWListener(using: parameter)" in code, "ohne `on:` — die Adresse kommt aus den Parametern"
    # KEIN ANGEBOT IM NETZ: kein Bonjour, keine geteilte Adresse.
    assert ".service" not in code
    assert "allowLocalEndpointReuse" not in code
    for datei in _claude_dateien():
        text = _code(datei)
        assert "0.0.0.0" not in text and not re.search(r"\.any\b", text), datei.name
        assert "NWListener(using: parameter, on:" not in text, datei.name


def test_jede_verbindung_wird_auf_die_gegenstelle_geprueft():
    code = _code(CLAUDE / "Claudeanschluss.swift")
    assert "Mcpzugang.gegenstelleIstLokal(" in code
    assert re.search(r"guard Claudeanschluss\.istLokal\(verbindung\), zaehler\.nimm\(\) else \{\s*"
                     r"verbindung\.cancel\(\)", code), "fremde Verbindung zu, bevor gelesen wird"


def test_der_anschluss_ist_8631_und_der_pfad_mcp():
    kern = _code(KERN / "Mcpkern.swift")
    assert "public static let anschluss = 8631" in kern
    assert 'public static let pfad = "/mcp"' in kern
    assert "public static let servername = Marke.name.lowercased()" in kern
    # DER PLAN NENNT DENSELBEN WEG, den Claude Code einträgt.
    plan = (WURZEL / "docs" / "PLAN_KI_BEDIENUNG_2026-10-20.md").read_text(encoding="utf-8")
    assert "claude mcp add --transport http visbox http://127.0.0.1:8631/mcp" in plan
    # DER HOERER NIMMT DIE ZAHL AUS DEM KERN, nicht ein zweites Mal.
    anschluss = _code(CLAUDE / "Claudeanschluss.swift")
    assert "NWEndpoint.Port(rawValue: UInt16(Mcp.anschluss))" in anschluss
    assert "8631" not in anschluss
    # NICHT DER ANSCHLUSS VON KOSMOORBIT (8630) UND NICHT DER DER VERMITTLUNG (8731).
    assert "8630" not in kern and "8731" not in kern


def test_host_und_origin_werden_im_kern_geprueft():
    leitung = _code(KERN / "Mcpleitung.swift")
    assert 'h == "127.0.0.1:\\(anschluss)" || h == "localhost:\\(anschluss)"' in leitung
    assert "Mcpzugang.ursprungErlaubt(origin)" in leitung
    assert "!Mcpzugang.kamUeberVermittler(kopf.koepfe)" in leitung, "106e: vorerst nur lokal"
    proben = (PROBEN / "McpleitungTests.swift").read_text(encoding="utf-8")
    assert "boese.example:8631" in proben, "DNS-Rebinding ist geprüft"


# ------------------------------------------------------------------- ab Werk an, stdio

def test_ab_werk_an_und_beim_start_gestartet():
    anschluss = _code(CLAUDE / "Claudeanschluss.swift")
    assert 'static let einstellung = "claudeMcp.an"' in anschluss
    assert "UserDefaults.standard.object(forKey: einstellung) as? Bool ?? true" in anschluss, (
        "108 B: fehlt der Eintrag, ist es an")
    app = _code(QUELLEN / "VisboxMacApp.swift")
    assert "Claudeanschluss.gemeinsam.starteWennAn()" in app


def test_mcp_stdio_greift_vor_dem_fenster_und_vor_dem_einzelstart():
    app = _code(QUELLEN / "VisboxMacApp.swift")
    stdio = app.find("Claudestdio.pruefe()")
    einzel = app.find("Einzelstart.pruefe()")
    assert 0 <= stdio < einzel, "sonst holte der Einzelstart die laufende Visbox nach vorn"
    code = _code(CLAUDE / "Claudestdio.swift")
    assert 'static let schalter = "--mcp-stdio"' in code
    assert "exit(fuehreAus())" in code
    # STDOUT GEHOERT DEM PROTOKOLL: keine Ausgabe mit print, Hinweise nach stderr.
    for datei in _claude_dateien():
        assert not re.search(r"\bprint\s*\(", _code(datei)), datei.name
    assert "FileHandle.standardError" in code
    # OHNE LAUFENDE APP DER PLATZHALTER «ohne App», nie ein Werkzeug, das etwas tut.
    assert "Mcpplatzhalter(ort: .ohneApp)" in code


def test_seit_stufe_3_traegt_die_knotenansicht_und_ohne_app_der_platzhalter():
    """Bis Stufe 2 stand hier der Platzhalter «kommt mit Stufe 3». Seit Stufe 3 reicht der
    Kern in der App an die Knotenansicht und die Mac-Werkzeuge (`Knotentraeger`); nur der Weg
    über stdio ohne laufende App behält den Platzhalter «ohne App»."""
    anschluss = _code(CLAUDE / "Claudeanschluss.swift")
    assert "Mcpkern(traeger: Knotentraeger(zentrale: Kizentrale.gemeinsam), fassung: fassung)" in anschluss
    assert "Mcpplatzhalter" not in anschluss
    assert "struct Knotentraeger: Werkzeugtraeger" in _code(CLAUDE / "Kizentrale.swift")


def test_die_wartefrist_ist_45_sekunden_und_die_leitung_haelt_laenger():
    kern = _code(KERN / "Mcpkern.swift")
    assert "public static let wartefrist: TimeInterval = 45" in kern
    leitung = _code(CLAUDE / "Claudeleitung.swift")
    assert "static let lebensfrist: TimeInterval = Mcp.wartefrist + 75" in leitung


# ------------------------------------------------------------------- Regel 1 und Regel 3

def test_kein_fremdes_paket_im_manifest():
    manifest = (MAC / "Package.swift").read_text(encoding="utf-8")
    pakete = re.findall(r"\.package\(([^)]*)\)", manifest)
    assert pakete == ['path: "../VisboxKern"'], pakete
    assert "url:" not in manifest


def test_der_claude_teil_benutzt_nur_plattform_und_kern():
    for datei in _claude_dateien():
        assert _importe(datei) <= {"Foundation", "Network", "VisboxKern"}, (datei.name, _importe(datei))
    for datei in (KERN / "Mcpkern.swift", KERN / "Mcpleitung.swift"):
        assert _importe(datei) == {"Foundation"}, datei.name


def test_kein_geheimnis_im_anschluss():
    """Regel 3 und Entscheid 106: kein Schlüssel, kein Kennwort, kein Token — weder im
    Anschluss noch im Kern noch in seinen Proben."""
    verboten = re.compile(r"authorization|bearer|token|kennwort|passw|api[_-]?key|secret|"
                          r"schluesselbund|keychain|sk-ant", re.I)
    dateien = _claude_dateien() + [KERN / "Mcpkern.swift", KERN / "Mcpleitung.swift",
                                   PROBEN / "McpkernTests.swift", PROBEN / "McpleitungTests.swift"]
    for datei in dateien:
        treffer = verboten.findall(_code(datei))
        assert not treffer, f"{datei.name}: {sorted(set(treffer))}"


def test_der_kern_hat_seine_proben():
    for name in ("McpkernTests.swift", "McpleitungTests.swift"):
        assert (PROBEN / name).is_file(), name
    proben = (PROBEN / "McpkernTests.swift").read_text(encoding="utf-8")
    for methode in ("initialize", "tools/list", "tools/call", "ping", "notifications/initialized"):
        assert methode in proben, methode
