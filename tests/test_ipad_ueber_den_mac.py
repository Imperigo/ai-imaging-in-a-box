"""Das iPad arbeitet über den Mac, verschlüsselt (Owner-Entscheid 118, 21.10.2026; «Visbox
eigenständig», Schritt 4).

Die Regeln prüft der Swift-Kern (``MacanbindungTests``, ``MacmappensichtTests``,
``MaczertifikatTests``). Bewacht wird hier, was der Kern nicht sehen kann: dass seine
Abschriften die Werte des Heim-PC tragen (Grösse und Schlüssel der Skizze, die Felder der
Sicht gegen eine **echte Antwort des Servers**), und dass die Apps die Regeln wirklich benutzen
— TLS am Mac, kein unverschlüsselter Hörer, der Lotse am iPad, das Koppelfenster mit dem Mac.
Übersetzt wird Swift nur auf der Prüfstrecke am Mac.
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
IPAD = WURZEL / "ipad" / "Visbox.swiftpm"
KERN = IPAD / "Kern"
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
SICHT_KERN = KERN / "Macmappensicht.swift"
DIENST = MAC / "Vermittlung" / "Vermittlungsdienst.swift"
QUELLE = MAC / "Vermittlung" / "Ipadmappenquelle.swift"
IDENTITAET = MAC / "Start" / "Macidentitaet.swift"
FENSTER = MAC / "Start" / "IpadKoppelfenster.swift"
LOTSE = IPAD / "Verbindung" / "Maclotse.swift"
SENDER = IPAD / "Verbindung" / "Sender.swift"
STAND = IPAD / "Verbindung" / "Verbindungsstand.swift"


def _code(datei: Path) -> str:
    """Quelltext ohne ganze Kommentarzeilen — ein Kommentar ist keine Wirkung."""
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def _liste(datei: Path, name: str) -> list[str]:
    treffer = re.search(rf"static let {name}\s*=\s*\[([^\]]*)\]", _code(datei), re.S)
    assert treffer, f"{name} fehlt in {datei.name}"
    return re.findall(r'"([^"]+)"', treffer.group(1))


def _importe(datei: Path) -> set[str]:
    return set(re.findall(r"^import (\w+)", _code(datei), re.M))


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture
def mappe(tmp_path):
    """Eine Mappe mit durchgereichter glb und einer Skizze — ohne Subprozess."""
    from aiimaging import arbeitsgang, projekt
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus", einstellungen={"prompt": "Abendlicht"})
    p = projekt.oeffne(wurzel)["projekt"]
    projekt.vermerke_skizze(p, skizze="skizze-1.png", bemerkung="Dach")
    projekt.speichere(p, wurzel)
    return wurzel


# ------------------------------------------------------------------ Abschriften des Heim-PC

def test_die_sicht_am_mac_erfindet_kein_feld_des_servers(server, mappe):
    """Die Felder, die der Mac dem iPad als Sicht schickt, sind die des Servers — gegen eine
    echte Antwort von ``server.sicht``, nicht gegen eine Abschrift."""
    sicht = server.sicht(mappe)
    assert set(_liste(SICHT_KERN, "felderDerSicht")) <= set(sicht), (
        set(_liste(SICHT_KERN, "felderDerSicht")) - set(sicht))
    assert '"am_mac"' in _code(SICHT_KERN), "das eigene Feld des Mac ist benannt"
    assert "am_mac" not in sicht, "das eigene Feld darf am Heim-PC nichts anderes heissen"
    skizze = sicht["skizzen"][0]
    assert set(_liste(SICHT_KERN, "felderDerSkizze")) <= set(skizze), skizze
    bild = server._bild_fuer_die_flaeche({"bild": "x.png", "erzeugt": "2026-10-21T00:00:00Z"})
    assert set(_liste(SICHT_KERN, "felderDesBildes")) <= set(bild), bild


def test_die_skizze_am_mac_hat_die_grenzen_des_heim_pc(server):
    code = _code(SICHT_KERN)
    assert "public static let hoechstensBytes = 2 * 1024 * 1024" in code
    assert server.SKIZZE_GROESSENRIEGEL == 2 * 1024 * 1024
    assert server.SCHLUESSEL_FORM.pattern == r"[A-Za-z0-9._-]{8,128}"
    assert "(8...128).contains(s.count)" in code
    assert server.PNG_KENNUNG == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    assert "[0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]" in code


# ------------------------------------------------------------------ der Mac

def test_der_mac_hoert_dem_ipad_nur_verschluesselt_zu():
    dienst = _code(DIENST)
    assert "NWParameters(tls: tls" in dienst
    assert "NWParameters.tcp" not in dienst, "kein unverschlüsselter Hörer mehr (Entscheid 118)"
    assert "sec_protocol_options_set_local_identity(" in dienst
    assert "sec_protocol_options_set_min_tls_protocol_version(" in dienst and ".TLSv12" in dienst
    # OHNE ZERTIFIKAT KEIN ANBIETEN — kein Rueckfall.
    starte = dienst[dienst.index("func starte("):dienst.index("func halte()")]
    assert "guard identitaet != nil" in starte


def test_der_mac_kuendigt_tls_an_und_nennt_sein_zertifikat():
    vermittlung = _code(KERN / "Vermittlung.swift")
    assert '("tls", "1")' in vermittlung
    assert '"zertifikat_sha256"' in vermittlung


def test_das_zertifikat_liegt_im_schluesselbund_und_der_schluessel_verlaesst_ihn_nicht():
    code = _code(IDENTITAET)
    assert "SecKeyCreateRandomKey(" in code and "kSecAttrIsPermanent as String: true" in code
    assert "SecKeyCreateSignature(" in code and ".ecdsaSignatureMessageX962SHA256" in code
    assert "Maczertifikat.tbs(" in code and "Maczertifikat.zertifikat(" in code
    assert "SecKeyCopyExternalRepresentation(privat" not in code, "nie den privaten Schlüssel"
    assert "kSecUseDataProtectionKeychain" not in code, "Behelfs-Unterschrift (wie Heimschluesselbund)"
    assert _importe(IDENTITAET) <= {"CryptoKit", "Foundation", "Security", "VisboxKern"}


def test_das_koppelfenster_koppelt_mit_dem_mac():
    fenster = _code(FENSTER)
    assert "vermittlung.dienstZumKoppeln()" in fenster
    assert "abdruck: abdruck" in fenster and "dienst.zahlFuersKoppelfenster()" in fenster
    assert "leitung.koppleIPad()" not in fenster, "nicht mehr die Zahl des Heim-PC (Entscheid 118)"
    assert "Fingerabdruck.zeichen(schein.abdruck)" in fenster


def test_die_mappe_am_mac_beantwortet_der_mac_nur_hinter_der_tuer():
    dienst = _code(DIENST)
    bearbeite = dienst[dienst.index("func bearbeite("):dienst.index("private func aktualisiere()")]
    # ERST DIE TUER UND DIE POSITIVLISTE (`stand.beantworte`), DANN DIE MAPPE AM MAC.
    assert bearbeite.index("stand.beantworte(") < bearbeite.index("Ipadmappenquelle.antwort(")
    assert "case .weiterreichen" in bearbeite[:bearbeite.index("Ipadmappenquelle.antwort(")]
    quelle = _code(QUELLE)
    assert "Macmappensicht.bildweg(" in quelle and "resolvingSymlinksInPath()" in quelle
    assert ".withoutOverwriting" in quelle
    assert _importe(QUELLE) <= {"Foundation", "VisboxKern"}


# ------------------------------------------------------------------ das iPad

def test_das_ipad_heftet_das_zertifikat_des_mac_an():
    assert "delegate: Maclotse.gemeinsam" in _code(SENDER)
    lotse = _code(LOTSE)
    assert "Fingerabdruck.pruefe(" in lotse and ".cancelAuthenticationChallenge" in lotse
    assert _importe(LOTSE) <= {"CryptoKit", "Foundation", "Security"}
    stand = _code(STAND)
    assert "Macanbindung.pruefeKopplung(" in stand
    assert "guard anbindung.darfSprechen" in stand, "nie unverschlüsselt über den Mac"
    assert "Macanbindung.wiedergefunden(" in stand, "kein Rückfall beim Wiederfinden"


def test_der_vermerk_der_plattform_nennt_die_leitung():
    notice = (WURZEL / "NOTICE").read_text(encoding="utf-8")
    assert "Entscheid 118" in notice and "Maczertifikat.swift" in notice


# ------------------------------------------------- Entscheid 118a: die Folgen

def _swift_text(datei: Path, name: str) -> str:
    """Der Wert einer ``static let name = "…" + "…"`` — zusammengesetzt, wie Swift ihn liest."""
    code = _code(datei)
    treffer = re.search(rf"static let {name}\s*=\s*((?:\"[^\"]*\"\s*\+?\s*)+)", code)
    assert treffer, f"{name} fehlt in {datei.name}"
    return "".join(re.findall(r'"([^"]*)"', treffer.group(1)))


def test_der_satz_zum_beendeten_direkten_weg_ist_auf_beiden_seiten_derselbe():
    """Eine 410 ohne lesbaren Satz (eine Weiterleitung verschluckt den Rumpf) zeigt am iPad
    denselben Satz wie der Heim-PC."""
    sys.path.insert(0, str(WURZEL / "src"))
    from aiimaging import geraetebuch
    assert _swift_text(KERN / "Macanbindung.swift", "satzDirektBeendet") \
        == geraetebuch.SATZ_DIREKT_BEENDET


def test_der_mac_reicht_mit_dem_wegkopf_weiter():
    """Ohne ``X-Geraet-Weg: mac`` wiese der Heim-PC das iPad seit 118a ab — die Vermittlung
    setzt ihn an jede Weiterreichung, die über die ``Heimstrecke`` geht."""
    vermittlung = _code(KERN / "Vermittlung.swift")
    assert "Kopfzeile(Geraeteart.wegkopf, \"mac\")" in vermittlung
    assert "w.koepfe(mit: anmeldung)" in _code(MAC / "Vermittlung" / "Heimstrecke.swift")


def test_die_vermittlung_entsteht_auch_ohne_heim_pc():
    anschluss = _code(MAC / "Start" / "Vermittlungsanschluss.swift")
    richte = anschluss[anschluss.index("func richteAus("):anschluss.index("func schalteAnbieten(")]
    assert "dienst = nil" not in richte, "ohne Heim-PC kein Abbau mehr (118a)"
    assert "Vermittlungsdienst(heim: ziel.map" in richte
    dienst = _code(DIENST)
    assert "private let heim: Heimstrecke?" in dienst
    bearbeite = dienst[dienst.index("func bearbeite("):dienst.index("private func aktualisiere()")]
    # ERST DIE MAPPE AM MAC, DANN «KEIN RECHNER»:
    assert (bearbeite.index("Ipadmappenquelle.antwort(")
            < bearbeite.index("guard let heim else { return Ipadmappenwege.ohneRechner(ziel) }")
            < bearbeite.index("heim.reiche("))
    # DAS MENUE «IPAD» haengt nicht mehr an der Adresse des Heim-PC:
    haupt = _code(MAC / "Start" / "Hauptfenster.swift")
    davor = [z for z in haupt[:haupt.index('Menu("iPad")')].splitlines() if z.strip()][-1]
    assert "leitung.adresse" not in davor, davor
