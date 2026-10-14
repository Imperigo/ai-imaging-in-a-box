"""«In Programme verschieben» (Owner-Entscheid 89, 14.10.2026, Blatt 18 Feld 4).

Am Mac des Owners scheiterte das Aktualisieren, weil macOS die App vom versteckten Ersatzort
(App Translocation) startete. Bewacht wird, dass die Mac-App das beim Start erkennt, den Umzug
anbietet und ihn so ausführt, dass nichts verloren geht. Swift übersetzt nur die Prüfstrecke.
"""
from __future__ import annotations

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"


def _code(datei: Path) -> str:
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def test_der_umzug_legt_nach_programme_ohne_etwas_zu_verlieren():
    code = _code(MAC / "Aktualisieren" / "Umzug.swift")
    assert "Aktualisierung.programmeZiel" in code
    # Eine aeltere Visbox in «Programme» geht in den Papierkorb, nicht ins Nichts.
    assert "trashItem(at: ziel" in code and "removeItem" not in code
    assert code.index("trashItem(at: ziel") < code.index("copyItem(at: quelle, to: ziel)")
    # Ohne das Entfernen der Quarantaene legte macOS auch die Kopie wieder an den versteckten Ort.
    assert '"com.apple.quarantine"' in code and "removexattr(" in code
    assert code.index("copyItem(") < code.index("entferneQuarantaene(ziel)") < code.index(
        "openApplication(at: ziel")
    assert "NSApp.terminate(nil)" in code


def test_angeboten_wird_beim_start_und_im_aktualisieren_blatt():
    fenster = _code(MAC / "Start" / "Hauptfenster.swift")
    assert "umzugOffen = Umzug.istVersteckt" in fenster
    assert "Button(Aktualisierung.umzugKnopf)" in fenster
    blatt = _code(MAC / "Aktualisieren" / "Aktualisierenblatt.swift")
    assert "if Umzug.istVersteckt" in blatt and "Button(Aktualisierung.umzugKnopf)" in blatt
