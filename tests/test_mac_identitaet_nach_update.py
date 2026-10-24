"""Das Zertifikat des Mac nach einem Update (Befund Demolauf 0.3.54, 24.10.2026).

Befund: Jedes Update der Mac-App trennte alle iPads («Der Mac zeigt ein anderes Zertifikat als
beim Koppeln»), und im Schlüsselbund lagen acht Einträge «Visbox Mac …». ``Macidentitaet`` fand
das alte Zertifikat nicht (Suche über das Etikett; die neu ad hoc unterschriebene App darf den
alten Schlüssel nicht ohne Weiteres benutzen) und legte **still** ein neues an.

Die Regel steht im Swift-Kern (``Macidentitaetsregel``, Proben ``MacidentitaetsregelTests``).
Bewacht wird hier, was der Kern nicht sehen kann: dass der Mac-Teil sie benutzt, das Zertifikat
über den gemerkten Fingerabdruck findet, «lesbar» mit einer Probe-Unterschrift prüft, nur
löscht, was er lesen konnte, und den Schlüssel nicht aus dem Schlüsselbund holt (Option «Datei»
ist bewertet, aber nicht gebaut). Übersetzt wird Swift nur auf der Prüfstrecke am Mac.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"
PROBEN = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests"
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
REGEL = KERN / "Macidentitaetsregel.swift"
REGELPROBEN = PROBEN / "MacidentitaetsregelTests.swift"
IDENTITAET = MAC / "Start" / "Macidentitaet.swift"
DIENST = MAC / "Vermittlung" / "Vermittlungsdienst.swift"
BLATT = WURZEL / "docs" / "MAC_UNTERSCHRIFT_EINRICHTEN.md"


def _code(datei: Path) -> str:
    """Quelltext ohne ganze Kommentarzeilen — ein Kommentar ist keine Wirkung."""
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//") and not z.strip().startswith("///"))


def _funktion(code: str, name: str) -> str:
    """Der Rumpf einer Funktion bis zur nächsten auf derselben Einrückung."""
    anfang = code.index(f"func {name}(")
    rest = code[anfang + 1:]
    naechste = re.search(r"\n    (?:private |public )?(?:static )?func ", rest)
    return code[anfang:anfang + 1 + (naechste.start() if naechste else len(rest))]


# ------------------------------------------------------------------ die Regel im Kern

def test_die_regel_steht_im_kern_mit_proben():
    regel = _code(REGEL)
    for fall in ("case lesbar", "case keines", "case nichtLesbar",
                 "case behalten", "case erneuern", "case erstesMal",
                 "case ersetzenNachVerlust", "case anhalten"):
        assert fall in regel, fall
    assert set(re.findall(r"^import (\w+)", regel, re.M)) <= {"Foundation"}
    proben = REGELPROBEN.read_text(encoding="utf-8")
    assert "func testNichtBeiJedemStartErneut()" in proben
    assert "func testNichtLesbarErsetztEinmal()" in proben


# ------------------------------------------------------------------ der Mac-Teil

def test_der_mac_fragt_die_regel_bevor_er_ein_neues_anlegt():
    code = _code(IDENTITAET)
    rumpf = _funktion(code, "liesOderErzeuge")
    assert "Macidentitaetsregel.schritt(" in rumpf
    # VOR DER REGEL wird nichts angelegt und nichts geloescht.
    vor_der_regel = rumpf[:rumpf.index("Macidentitaetsregel.schritt(")]
    assert "erzeuge(" not in vor_der_regel.replace("liesOderErzeuge(", "")
    assert "loesche(" not in vor_der_regel
    # NACH EINEM VERLUST: einmal je Fassung, und die iPads hoeren davon.
    verlust = rumpf[rumpf.index("case .ersetzenNachVerlust"):rumpf.index("case .anhalten")]
    assert "ersetztEintrag" in verlust and "neuKoppelnEintrag" in verlust
    anhalten = rumpf[rumpf.index("case .anhalten"):]
    assert "erzeuge(" not in anhalten.split("}")[0], "angehalten heisst: kein neues"


def test_gefunden_wird_ueber_den_fingerabdruck_und_lesbar_heisst_unterschreiben():
    code = _code(IDENTITAET)
    suche = _funktion(code, "suche")
    assert "abdruck($0) == gemerkt" in suche
    zertifikate = _funktion(code, "eigeneZertifikate")
    assert "kSecMatchLimitAll" in zertifikate and "SecCertificateCopySubjectSummary(" in zertifikate
    assert "Maczertifikat.name(zusatz: \"\")" in zertifikate
    pruefe = _funktion(code, "pruefe")
    assert "SecKeyCreateSignature(" in pruefe, "die Probe-Unterschrift"
    erzeuge = _funktion(code, "erzeuge")
    assert "forKey: abdruckEintrag" in erzeuge, "ein neues wird gemerkt"


def test_geloescht_wird_nur_was_die_app_lesen_konnte():
    """Bis 0.3.54 löschte die App alle Schlüssel mit dem Kennzeichen — fremd gewordene hätten je
    einmal nach dem Kennwort gefragt. Jetzt nur genau das gelesene Paar."""
    code = _code(IDENTITAET)
    loesche = _funktion(code, "loesche")
    assert "func loesche(_ geladen: Geladen)" in loesche
    assert "kSecValueRef as String: zertifikat" in loesche
    assert "kSecValueRef as String: schluessel" in loesche
    for zeile in code.splitlines():
        if "SecItemDelete(" in zeile:
            assert "kSecAttrApplicationTag" not in zeile and "kSecAttrLabel" not in zeile, zeile


def test_der_schluessel_bleibt_im_schluesselbund():
    """Option «Schlüssel als Datei» ist bewertet, aber nicht gebaut (Owner-Frage) — die Wache
    hält, dass es nicht still doch geschieht."""
    code = _code(IDENTITAET)
    assert "SecKeyCopyExternalRepresentation(privat" not in code
    for verboten in ("FileManager", "Application Support", ".p12", "SecPKCS12", "SecAccessCreate",
                     "kSecAttrAccess "):
        assert verboten not in code, verboten
    # GEMERKT WIRD NUR, WAS KEIN GEHEIMNIS IST.
    eintraege = set(re.findall(r'"(vermittlung\.[A-Za-z]+)"', code))
    assert eintraege == {"vermittlung.zertifikatBis", "vermittlung.zertifikatAbdruck",
                         "vermittlung.zertifikatErsetztIn", "vermittlung.ipadsNeuKoppeln"}


def test_die_zeile_ipad_sagt_neu_koppeln_bis_eines_gekoppelt_hat():
    dienst = _code(DIENST)
    aktualisiere = dienst[dienst.index("private func aktualisiere()"):dienst.index("private func biete()")]
    assert "Macidentitaetsregel.zeilenhinweis(" in aktualisiere
    assert "fehler: fehler ?? verlust" in aktualisiere
    bearbeite = dienst[dienst.index("func bearbeite("):dienst.index("private func aktualisiere()")]
    gekoppelt = bearbeite[bearbeite.index("stand.erfolgreicheKopplungen > vorher"):]
    assert "Macidentitaet.ipadNeuGekoppelt()" in gekoppelt.split("}")[0]


def test_das_blatt_sagt_wie_man_alte_eintraege_loescht():
    blatt = BLATT.read_text(encoding="utf-8")
    assert "Schlüsselbundverwaltung" in blatt
    assert "Visbox Mac" in blatt and "Visbox · iPad-Leitung" in blatt
