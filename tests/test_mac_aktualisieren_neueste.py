"""Der Knopf «● 0.x.y verfügbar» lädt immer die neueste Freigabe (Owner-Befund 20.10.2026).

Owner, wörtlich: «wenn schon zwei neue updates da sind und ich zwei versionen hinterherhinke,
dann muss ich zuerst die zweitneuste herunterladen und dann die neuste ... bitte updateknopf
immer direkt zur neusten verfügbaren».

Die Regeln stehen im Kern (`Angebotsstand`, geprüft mit `swift test` in `ipad/VisboxKern`);
hier wird bewacht, dass die Mac-App sie benutzt — übersetzt wird Swift nur auf der
Prüfstrecke am Mac.
"""
from __future__ import annotations

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
WAECHTER = (WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Aktualisieren"
            / "Fassungswaechter.swift")
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Aktualisierung.swift"
KERNPROBEN = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests" / "AktualisierungTests.swift"


def _code(datei: Path) -> str:
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def test_der_klick_fragt_vor_dem_laden_noch_einmal():
    code = _code(WAECHTER)
    teil = code[code.index("func ladeUndErsetze()"):code.index("private func melde(")]
    assert "await self.hole(" in teil
    assert "self.stand.beginne(frisch: frisch)" in teil
    # Geladen wird das Ziel aus dem Kern, nicht das angezeigte Angebot.
    assert "Ersetzer.ersetze(ziel," in teil and "Ersetzer.ersetze(angebot" not in teil
    assert teil.index("self.hole(") < teil.index("beginne(frisch:") < teil.index("Ersetzer.ersetze(")


def test_jede_antwort_geht_durch_den_kern():
    code = _code(WAECHTER)
    frage = code[code.index("private func frage()"):code.index("func ladeUndErsetze()")]
    assert "stand.nimm(antwort)" in frage
    # Die App entscheidet nicht selbst, ob ein Angebot ersetzt wird.
    assert "bietetAn(" not in code
    assert "var angebot: Freigabe? { stand.angebot }" in code
    assert "stand.beende(ersetzt:" in code


def test_nach_einem_fehler_und_nach_dem_aufwachen_bald_wieder():
    code = _code(WAECHTER)
    start = code[code.index("func starte()"):code.index("func halte()")]
    # Beim Start (auch nach «Neu starten») sofort, vor dem ersten Warten.
    assert start.index("await self?.frage()") < start.index("Task.sleep")
    assert "gelungen: self.letzteGelungen" in start
    assert "Aktualisierung.blickAbstand" in start
    assert "NSWorkspace.didWakeNotification" in start
    kern = _code(KERN)
    assert "public static let abstandNachFehler: TimeInterval = 5 * 60" in kern
    assert "public static let blickAbstand: TimeInterval = 60" in kern


def test_der_kern_haelt_die_vier_faelle_des_owners():
    proben = KERNPROBEN.read_text(encoding="utf-8")
    for name in ("testEinKlickLaedtDieNeuesteAuchUeberZweiFassungenHinweg",
                 "testEineNeueAntwortErsetztDasAngebot",
                 "testScheitertDieFrageBleibtDasAngezeigteAngebot",
                 "testEinLaufendesLadenWirdNichtUnterbrochen"):
        assert f"func {name}()" in proben, name
    kern = _code(KERN)
    assert "public struct Angebotsstand" in kern
    assert "public mutating func nimm(_ antwort: Freigabe?) -> Bool" in kern
    assert "public mutating func beginne(frisch: Freigabe?) -> Freigabe?" in kern
