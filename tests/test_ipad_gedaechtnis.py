"""Die Kopplung bleibt gemerkt — auch nach Löschen und Neuaufspielen über Xcode (0.2.12).

Owner 20.10.2026: «Kopplung einmal machen, danach nie wieder.» Bis 0.2.11 lagen Adresse und
Name der HomeStation in den App-Einstellungen; die gehen beim Löschen der App verloren, der
Schlüsselbund nicht. Bewacht wird der Quelltext — übersetzt wird Swift nur auf der Prüfstrecke.
"""
from __future__ import annotations

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
GEDAECHTNIS = WURZEL / "ipad" / "Visbox.swiftpm" / "Verbindung" / "Verbindungsgedaechtnis.swift"
KOPPEL = WURZEL / "ipad" / "Visbox.swiftpm" / "Verbindung" / "Koppelbildschirm.swift"


def _code(datei: Path) -> str:
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def test_das_gedaechtnis_liegt_im_schluesselbund():
    code = _code(GEDAECHTNIS)
    assert "import Security" in code
    assert "SecItemAdd(" in code and "SecItemCopyMatching(" in code
    # Ein eigener Dienst, getrennt von der Anmeldung.
    assert '".verbindung"' in code
    # Gelesen und geschrieben wird nur noch über den Schlüsselbund ...
    for teil in ("static var adresse", "static var name", "static var ueberDenMac",
                 "static var ordner"):
        stueck = code[code.index(teil):code.index("}", code.index("set {", code.index(teil)))]
        assert "UserDefaults" not in stueck, teil


def test_alte_werte_werden_uebernommen():
    """... und was eine alte Fassung in den App-Einstellungen liess, wandert einmal hinüber."""
    code = _code(GEDAECHTNIS)
    lies = code[code.index("private static func lies("):code.index("private static func schreibe(")]
    assert "UserDefaults.standard.string(forKey: schluessel)" in lies
    assert "UserDefaults.standard.removeObject(forKey: schluessel)" in lies


def test_der_koppelbildschirm_sagt_zwei_minuten():
    text = KOPPEL.read_text(encoding="utf-8")
    assert "zehn Minuten" not in text
    assert "zwei Minuten lang" in text
