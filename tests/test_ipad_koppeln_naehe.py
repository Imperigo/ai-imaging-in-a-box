"""iPad koppeln ohne Abtippen — Nähe und QR-Code (Owner-Entscheide 99/99a/99b, 20.10.2026).

Der Mac bietet sich im Koppelfenster über MultipeerConnectivity an (A) und zeigt einen
QR-Code (B); beide tragen denselben Koppelschein: Adresse und Zahl, **nie** das Kennwort.
Das Eintippen bleibt als letzter Weg. Übersetzt wird Swift nur auf der Prüfstrecke am Mac,
die Entscheidungen prüft der Kern (`KopplungNaeheTests`). Bewacht wird hier, was der Kern
nicht sehen kann: Manifest und plist, die Verschlüsselung, dass beide Seiten bestätigen,
dass nur der Schein hinausgeht und dass das Anbieten mit dem Fenster endet.
"""
from __future__ import annotations

import plistlib
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad" / "Visbox.swiftpm"
KERN = IPAD / "Kern"
MAC = WURZEL / "ipad" / "VisboxMac"
MAC_START = MAC / "Sources" / "VisboxMac" / "Start"
NAEHESUCHER = IPAD / "Verbindung" / "Naehesucher.swift"
QRLESER = IPAD / "Verbindung" / "QRLeser.swift"
KOPPELBILDSCHIRM = IPAD / "Verbindung" / "Koppelbildschirm.swift"
NAEHEANBIETER = MAC_START / "Naeheanbieter.swift"
KOPPELFENSTER = MAC_START / "IpadKoppelfenster.swift"
NAEHEKERN = KERN / "Naehekopplung.swift"


def _code(datei: Path) -> str:
    """Quelltext ohne ganze Kommentarzeilen — ein Kommentar ist keine Wirkung."""
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def _marke() -> dict[str, str]:
    return dict(re.findall(r'static let (\w+)\s*=\s*"([^"]+)"', _code(KERN / "Marke.swift")))


def _funktion(code: str, kopf: str) -> str:
    """Der Rumpf einer Funktion, bis zur nächsten auf derselben Einrückung."""
    beginn = code.index(kopf)
    einzug = len(code[:beginn].rsplit("\n", 1)[-1])
    rest = code[beginn + len(kopf):]
    ende = re.search(r"\n {%d}(?:@MainActor\n {%d})?(?:private |public |static |override |nonisolated )*func " % (
        einzug, einzug), rest)
    return rest[:ende.start()] if ende else rest


# ------------------------------------------------------------------ Dienst und Manifest

def test_der_naehedienst_erfuellt_die_regeln_von_multipeer():
    """``serviceType``: 1–15 Zeichen, Kleinbuchstaben, Ziffern, Bindestrich; ein Buchstabe
    mindestens, kein Bindestrich am Rand und keine zwei nebeneinander. Ein ungültiger wirft
    erst am Gerät — und beim Umbenennen der Marke (``KosmoSketch``) fiele es sonst nicht auf."""
    art = _marke()["naehedienst"]
    assert 1 <= len(art) <= 15, art
    assert re.fullmatch(r"[a-z0-9](?:[a-z0-9]|-(?!-))*", art) and not art.endswith("-"), art
    assert re.search(r"[a-z]", art), art
    assert f"_{art}._tcp" != _marke()["dienst"], "ein eigener Dienst, nicht der der HomeStation"


def test_das_manifest_nennt_die_naehe_und_die_kamera():
    manifest = _code(IPAD / "Package.swift")
    art = _marke()["naehedienst"]
    typen = re.findall(r'"([^"]+)"', re.search(r"bonjourServiceTypes:\s*\[([^\]]*)\]",
                                               manifest).group(1))
    assert {f"_{art}._tcp", f"_{art}._udp", _marke()["dienst"]} == set(typen), typen
    kamera = re.findall(r'\.camera\(\s*purposeString:\s*"([^"]+)"\s*\)', manifest)
    assert len(kamera) == 1, "die Kamera braucht genau einen Satz, warum (99b)"
    assert "QR-Code" in kamera[0] and "Mac" in kamera[0], kamera[0]
    netz = re.findall(r'\.localNetwork\(\s*purposeString:\s*"([^"]+)"', manifest)[0]
    assert "Nähe" in netz and "koppelt" in netz, f"der Satz nennt das Koppeln nicht: {netz!r}"


def test_die_mac_plist_nennt_die_naehe():
    with (MAC / "App" / "Info.plist").open("rb") as f:
        plist = plistlib.load(f)
    art = _marke()["naehedienst"]
    assert {f"_{art}._tcp", f"_{art}._udp"} <= set(plist["NSBonjourServices"])
    assert "Nähe" in plist["NSLocalNetworkUsageDescription"]


def test_der_kern_leitet_dienst_und_schema_aus_der_marke_ab():
    kern = _code(NAEHEKERN)
    assert "Marke.naehedienst" in kern and "Marke.koppelschema" in kern
    assert 'public static let fenster: TimeInterval = 120' in kern, "Entscheid 99a: zwei Minuten"
    for datei in (NAEHESUCHER, NAEHEANBIETER):
        assert "serviceType: Naehekopplung.dienstart" in _code(datei), datei.name


# ------------------------------------------------------------------ verschlüsselt

def test_jede_sitzung_ist_verschluesselt():
    for datei in (NAEHESUCHER, NAEHEANBIETER):
        code = _code(datei)
        sitzungen = re.findall(r"MCSession\(([^)]*)\)", code)
        assert sitzungen, f"{datei.name}: keine Sitzung"
        for argumente in sitzungen:
            assert "encryptionPreference: .required" in argumente, (datei.name, argumente)
        assert ".optional" not in code and "encryptionPreference: .none" not in code, datei.name


# ------------------------------------------------------------------ beide bestätigen

def test_das_ipad_fragt_und_laedt_erst_nach_annehmen_ein():
    bild = _code(KOPPELBILDSCHIRM)
    for satz in ('"Mit diesem Mac koppeln?"', 'Button("Ablehnen")', 'Button("Annehmen")',
                 "naehe.nimmAn()", "naehe.lehneAb()"):
        assert satz in bild, satz
    sucher = _code(NAEHESUCHER)
    assert sucher.count(".invitePeer(") == 1
    annehmen = _funktion(sucher, "func nimmAn()")
    assert ".invitePeer(" in annehmen and "Naehekopplung.einladungsvermerk" in annehmen
    assert "case .gefunden" in annehmen, "eingeladen wird nur der gezeigte Mac"


def test_der_mac_fragt_und_nimmt_erst_nach_koppeln_an():
    fenster = _code(KOPPELFENSTER)
    for satz in ('"iPad möchte koppeln"', 'Button("Ablehnen")', 'Button("Koppeln")',
                 "naehe.koppeln()", "naehe.lehneAb()"):
        assert satz in fenster, satz
    anbieter = _code(NAEHEANBIETER)
    # DIE EINLADUNG WIRD NUR AN EINER STELLE ANGENOMMEN — in «Koppeln».
    angenommen = re.findall(r"\w+\(true, \w+\)", anbieter)
    assert angenommen == ["antworte(true, s)"], angenommen
    koppeln = _funktion(anbieter, "func koppeln()")
    assert "absprache.macSagtKoppeln()" in koppeln and "antworte(true, s)" in koppeln
    eingeladen = _funktion(anbieter, "private func eingeladen(")
    assert "einladung(vermerk: vermerk)" in eingeladen, "ohne Vermerk des iPad keine Frage"


# ------------------------------------------------------------------ nur der Schein

def test_ueber_die_naehe_geht_nur_der_schein_nie_das_kennwort():
    """Entscheid 99: Der Mac schickt Adresse und Zahl — **nicht** das Kennwort. Die Klasse,
    die sendet, kennt weder Anmeldung noch Schlüsselbund, und gesendet wird an genau einer
    Stelle genau der Schein, und erst wenn der Kern es erlaubt."""
    anbieter = _code(NAEHEANBIETER)
    for verboten in ("anmeldung", "kennwort", "Heimschluesselbund", "Anmeldung", "leitung"):
        assert verboten not in anbieter, verboten
    sendungen = re.findall(r"\.send\(([^,]+),", anbieter)
    assert sendungen == ["schein.daten"], sendungen
    verbunden = _funktion(anbieter, "private func verbunden(")
    assert verbunden.index("absprache.darfSenden(") < verbunden.index(".send(")
    assert "s.encryptionPreference == .required" in verbunden
    # Das iPad schickt dem Mac nichts.
    assert ".send(" not in _code(NAEHESUCHER)


def test_der_schein_hat_genau_adresse_zahl_und_frist():
    kern = _code(NAEHEKERN)
    assert 'public static let felder = ["adresse", "zahl", "bis"]' in kern
    text = _funktion(kern, "public var text: String")
    assert "adresse=" in text and "&zahl=" in text and "&bis=" in text
    assert not re.search(r"kennwort|passwort|benutzer", text, re.I)


def test_das_ipad_koppelt_mit_dem_schein_wie_beim_abtippen():
    bild = _code(KOPPELBILDSCHIRM)
    mit = _funktion(bild, "private func koppeln(mit schein: Koppelschein)")
    assert "await koppeln(an: schein.adresse" in mit and "schein.zahl.ziffern" in mit
    an = _funktion(bild, "private func koppeln(an ziel: URL")
    assert "stand.koppele(adresse: ziel" in an
    # Nähe und QR gehen durch den Kern, nicht an ihm vorbei.
    assert "Koppelschein.lies(" in _code(NAEHESUCHER)
    assert "Koppelschein.lies(" in _code(QRLESER)


# ------------------------------------------------------------------ nach zwei Minuten aus

def test_das_anbieten_endet_mit_dem_fenster():
    anbieter = _code(NAEHEANBIETER)
    assert anbieter.count("startAdvertisingPeer()") == 1
    assert "startAdvertisingPeer()" in _funktion(anbieter, "func biete(")
    assert "stopAdvertisingPeer()" in _funktion(anbieter, "func halte()")
    fenster = _code(KOPPELFENSTER)
    takt = fenster[fenster.index(".onReceive(takt)"):fenster.index(".onDisappear")]
    assert "!offen" in takt and "schliesseFenster()" in takt
    assert "naehe.halte()" in _funktion(fenster, "private func schliesseFenster()")
    assert "naehe.halte()" in fenster[fenster.index(".onDisappear"):]
    assert "Koppelfenster(jetzt:" in fenster, "die Frist rechnet der Kern"


def test_der_qr_code_kommt_von_coreimage_und_traegt_den_schein():
    fenster = _code(KOPPELFENSTER)
    assert 'CIFilter(name: "CIQRCodeGenerator")' in fenster
    assert "qrBild(s.text)" in fenster


def test_der_qr_leser_liegt_in_der_app():
    leser = _code(QRLESER)
    assert "DataScannerViewController" in leser and ".barcode(symbologies: [.qr])" in leser
    assert "AVCaptureMetadataOutput" in leser and "metadataObjectTypes = [.qr]" in leser
    bild = _code(KOPPELBILDSCHIRM)
    assert 'Button("Mit QR-Code koppeln")' in bild and "QRLeser(" in bild


def test_die_zahl_bleibt_als_letzter_weg():
    bild = _code(KOPPELBILDSCHIRM)
    assert "Zahl eintippen" in bild and 'TextField("000000", text: $zahl)' in bild


def test_nur_apples_plattform_fuer_naehe_und_qr():
    """Regel 1: Für Nähe und QR-Code nur Apple-Frameworks (Plattform, im ``NOTICE`` vermerkt)."""
    def importe(datei: Path) -> set[str]:
        return set(re.findall(r"^import (\w+)", _code(datei), re.M))
    assert importe(NAEHESUCHER) <= {"Foundation", "MultipeerConnectivity", "UIKit"}
    assert importe(QRLESER) <= {"AVFoundation", "SwiftUI", "UIKit", "VisionKit"}
    assert importe(NAEHEANBIETER) <= {"Foundation", "MultipeerConnectivity", "VisboxKern"}
    assert importe(KOPPELFENSTER) <= {"Combine", "CoreImage", "SwiftUI", "VisboxKern"}
    notice = (WURZEL / "NOTICE").read_text(encoding="utf-8")
    for rahmen in ("MultipeerConnectivity", "CoreImage", "AVFoundation", "VisionKit"):
        assert rahmen in notice, f"{rahmen} fehlt im Vermerk der Plattform"
