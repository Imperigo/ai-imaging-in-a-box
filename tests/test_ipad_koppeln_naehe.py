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
    assert sucher.count(".invitePeer(") == 1, "eine Stelle, an der eingeladen wird"
    annehmen = _funktion(sucher, "func nimmAn()")
    assert "lade(mac)" in annehmen
    assert "case .gefunden" in annehmen, "eingeladen wird nur der gezeigte Mac"
    lade = _funktion(sucher, "private func lade(")
    assert ".invitePeer(" in lade and "Naehekopplung.einladungsvermerk" in lade
    # Wer «lade» ruft: «Annehmen» und das Neu-Einladen nach einem Versuch, der nicht trug.
    assert set(re.findall(r"(?<!func )\blade\(\w+\)", sucher)) <= {"lade(mac)"}


def test_der_mac_nimmt_nur_mit_vermerk_an_und_schickt_erst_nach_koppeln():
    """Seit dem Demolauf vom 24.10.2026 nimmt der Mac eine Einladung **mit Vermerk sofort**
    an — vorher erst nach dem Klick, und MultipeerConnectivity wartete darauf nicht. Was
    Entscheid 99 schützt, bleibt: Der Schein geht erst nach «Koppeln» hinaus."""
    fenster = _code(KOPPELFENSTER)
    for satz in ('"iPad möchte koppeln"', 'Button("Ablehnen")', 'Button("Koppeln")',
                 "naehe.koppeln()", "naehe.lehneAb()"):
        assert satz in fenster, satz
    anbieter = _code(NAEHEANBIETER)
    # DIE EINLADUNG WIRD NUR AN EINER STELLE ANGENOMMEN — nach der Pruefung des Vermerks.
    angenommen = re.findall(r"\w+\(true, \w+\)", anbieter)
    assert angenommen == ["antworte(true, s)"], angenommen
    eingeladen = _funktion(anbieter, "private func eingeladen(")
    assert eingeladen.index("einladung(vermerk: vermerk)") < eingeladen.index("antworte(true, s)")
    assert ".ipadFragt" not in eingeladen, "gefragt wird erst, wenn die Sitzung steht"
    assert ".ipadFragt" in _funktion(anbieter, "private func verbunden(")
    koppeln = _funktion(anbieter, "func koppeln()")
    assert koppeln.index("absprache.macSagtKoppeln()") < koppeln.index("sendeSchein(")
    assert "antworte" not in koppeln
    # «Ablehnen» schliesst die Sitzung ohne Schein — das ist die Absage, die das iPad liest.
    ablehnen = _funktion(anbieter, "func lehneAb()")
    assert ".disconnect()" in ablehnen and ".send(" not in ablehnen


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
    senden = _funktion(anbieter, "private func sendeSchein(")
    assert senden.index("absprache.darfSenden(") < senden.index(".send(")
    assert "s.encryptionPreference == .required" in senden
    assert "sendeSchein(" not in _funktion(anbieter, "private func verbunden("), \
        "die stehende Sitzung allein schickt nichts"
    # Das iPad schickt dem Mac nichts.
    assert ".send(" not in _code(NAEHESUCHER)


def test_der_schein_hat_genau_adresse_zahl_frist_und_abdruck():
    """Seit Entscheid 118 (21.10.2026) dazu der Fingerabdruck des Zertifikats des Mac — das,
    was das iPad anheftet. Nie Kennwort oder Benutzer."""
    kern = _code(NAEHEKERN)
    assert 'public static let felder = ["adresse", "zahl", "bis", "abdruck"]' in kern
    text = _funktion(kern, "public var text: String")
    assert "adresse=" in text and "&zahl=" in text and "&bis=" in text and "&abdruck=" in text
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


# ------------------------------------------------------------------ Demolauf 24.10.2026

def test_ein_nicht_verbunden_vor_der_sitzung_ist_keine_absage():
    """FEHLER 1 des Demolaufs (Visbox 0.3.54): Das erste «nicht verbunden» galt als Absage des
    Mac — es kam nach rund drei Sekunden, während am Mac die Frage noch stand. Was es heisst,
    entscheidet seither der Kern (`Naeheeinladung`): vor der stehenden Sitzung neu einladen,
    danach aufgeben, dazu zwei Fristen."""
    sucher = _code(NAEHESUCHER)
    getrennt = _funktion(sucher, "private func getrennt(")
    assert "e.getrennt(jetzt:" in getrennt and "s === sitzung" in getrennt
    assert "satzMacAbgelehnt" not in sucher, "den Satz waehlt der Kern, nicht die Klasse"
    assert "e.uhr(jetzt:" in _funktion(sucher, "private func pruefeFrist(")
    assert "case .connected: self?.verbunden(peerID, in: session)" in sucher
    assert "einladung?.sitzungSteht()" in _funktion(sucher, "private func verbunden(")
    befolge = _funktion(sucher, "private func befolge(")
    assert "case .neuEinladen" in befolge and "self.lade(mac)" in befolge
    assert "Naeheeinladung.neuEinladenNach" in befolge
    lade = _funktion(sucher, "private func lade(")
    assert lade.index("sitzung?.disconnect()") < lade.index("MCSession("), \
        "eine alte Sitzung, die nicht trug, geht vor der neuen weg"
    assert "timeout: Naeheeinladung.verbindenHoechstens" in lade
    kern = _code(NAEHEKERN)
    assert "public struct Naeheeinladung" in kern
    assert "public static let hoechstensVersuche = 3" in kern
    # Der Mac laesst ein iPad, das neu einlaedt, wieder herein, und meldet einen Versuch, der
    # nie stand, nicht rot.
    anbieter = _code(NAEHEANBIETER)
    eingeladen = _funktion(anbieter, "private func eingeladen(")
    assert "alt == peer, !absprache.verbunden" in eingeladen
    assert "guard hatteSitzung else" in _funktion(anbieter, "private func getrennt(")


def test_das_adressfeld_belegt_nichts_veraltetes_vor():
    """FEHLER 2 des Demolaufs: Im Adressfeld stand «https://192.168.1.24:8731» — der
    Platzhalter, eine echt aussehende Adresse, die es im Netz nicht gab. Dazu zwei stille Wege
    für veraltete Adressen: die gemerkte eines Mac, der nicht antwortet, und eine Auflösung aus
    einer früheren Suche."""
    bild = _code(KOPPELBILDSCHIRM)
    platzhalter = re.findall(r'TextField\("([^"]*)"', bild)
    for p in platzhalter:
        assert not re.search(r"\d+\.\d+\.\d+\.\d+|https?://\w", p), p
    assert "TextField(Suche.adressplatzhalter, text: $adresseText)" in bild
    erscheinen = bild[bild.index(".onAppear"):bild.index(".onDisappear")]
    assert "Suche.vorbelegung(gemerkt: stand.adresse, erreichbar: !koppelwege)" in erscheinen
    assert "adresseText = a.absoluteString" in erscheinen
    assert "Suche.satzZuletzt(" in bild
    kern = _code(KERN / "Suche.swift")
    assert re.search(r'adressplatzhalter = "[^"0-9]*"', kern), "keine Ziffern im Platzhalter"
    sucher = _code(IPAD / "Verbindung" / "Sucher.swift")
    assert "self?.bekannt = [:]" in _funktion(sucher, "func beende()")
    stand = _code(IPAD / "Verbindung" / "Verbindungsstand.swift")
    frei = _funktion(stand, "private func gibFrei(")
    assert "gefunden = []" in frei
