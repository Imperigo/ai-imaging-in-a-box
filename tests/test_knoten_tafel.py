"""Die Erklärkarten der Knoten für die Tafel (`tools/knoten_tafel.py`).

Owner-Auftrag 23.10.2026: «pro node eine tafel zur aufklärung der einzelnen funktionen». Die Karten
zeichnen jeden Knoten mit seinen Ein- und Ausgängen und erklären jedes Feld in einem Satz. *Eine Karte, die einen
Anschluss zeigt, den der Knoten nicht hat, ist schlimmer als keine Karte* — darum wird hier
gegen den Knotenkatalog der Kopie (`kosmovis/…/derive/visgraph.ts`) gezählt, nicht gegen das
Gedächtnis. Und jeder Schalter des Werkzeugs wird einmal gedrückt (`test_schalterprobe.py`).
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KATALOG = WURZEL / "kosmovis" / "packages" / "kosmo-kernel" / "src" / "derive" / "visgraph.ts"


def _werkzeug():
    pfad = WURZEL / "tools" / "knoten_tafel.py"
    spec = importlib.util.spec_from_file_location("werkzeug_knoten_tafel", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _konstanten() -> dict[str, str]:
    """`export const NAME = 'wert'` aus dem Kern — für Katalog-Schlüssel wie `[KAMERA_AUS_3D_TYP]`."""
    werte = {}
    for datei in KATALOG.parent.glob("*.ts"):
        werte.update(re.findall(r"export const (\w+) = '(\w+)'", datei.read_text(encoding="utf-8")))
    return werte


def _katalog() -> dict[str, dict]:
    """typ → {label, kategorie, inputs [(label, typ)], outputs [(label, typ)]} aus dem TS-Katalog.

    Auch Einträge mit berechnetem Schlüssel (`[KAMERA_AUS_3D_TYP]: {`) zählen: Der Leser übersah
    sie bis zum 14.10.2026 und meldete «zwölf», als es dreizehn waren (Protokoll 74 §123)."""
    text = KATALOG.read_text(encoding="utf-8")
    teil = text[text.index("export const VIS_NODE_KATALOG"):text.index("export function visPort")]
    konst = _konstanten()
    aus = {}
    for block in re.split(r"\n  (?=(?:\w+|\[\w+\]): \{\n)", teil)[1:]:
        roh = re.search(r"typ: (?:'(\w+)'|(\w+))", block)
        typ = roh.group(1) or konst[roh.group(2)]
        # Seit dem 21.10.2026 auch Anschlüsse mit `nurVon` (Skizze am Render, die Eingänge der Oberfläche).
        port = r"\{ name: '\w+', typ: '(\w+)', label: '([^']+)'(?:, nurVon: \[[^\]]*\])? \}"

        def ports(feld):
            # Eine Ebene Klammern darf drin sein (`nurVon: ['…']`), sonst endete die Liste dort.
            m = re.search(feld + r": \[((?:[^\[\]]|\[[^\]]*\])*)\]", block, re.S)
            return [(label, t) for t, label in re.findall(port, m.group(1))] if m else []

        aus[typ] = {"label": re.search(r"label: '([^']+)'", block).group(1),
                    "kategorie": re.search(r"kategorie: '(\w+)'", block).group(1),
                    "inputs": ports("inputs"), "outputs": ports("outputs")}
    return aus


def test_der_katalog_wird_gelesen():
    """Die Gegenprobe zum Leser: siebzehn Knotenarten (seit 21.10.2026), wie der Kommentar im Katalog sagt."""
    katalog = _katalog()
    assert len(katalog) == 17
    assert "Katalog der 17 Node-Typen" in KATALOG.read_text(encoding="utf-8")
    assert katalog["render"]["inputs"][0] == ("Szene", "szene")


def test_jede_knotenart_hat_genau_eine_karte():
    kt = _werkzeug()
    assert sorted(k["typ"] for k in kt.KNOTEN) == sorted(_katalog())


def test_karten_zeigen_die_anschluesse_des_katalogs():
    """Name, Reihenfolge und Sorte jedes Anschlusses, Titel und Gruppe — wie im Katalog."""
    kt = _werkzeug()
    katalog = _katalog()
    for k in kt.KNOTEN:
        soll = katalog[k["typ"]]
        assert k["titel"] == soll["label"], k["typ"]
        assert k["gruppe"] == soll["kategorie"], k["typ"]
        assert k["ein"] == soll["inputs"], k["typ"]
        assert k["aus"] == soll["outputs"], k["typ"]


def test_jede_karte_hat_eine_notiz_von_ein_bis_zwei_saetzen():
    """Die Notiz neben dem Bild ist eine Laien-Zusammenfassung — ein bis zwei Sätze."""
    kt = _werkzeug()
    for kurz, _titel, notiz, _html in kt.karten():
        saetze = [s for s in re.split(r"(?<=[.!?»])\s+(?=[A-ZÄÖÜ«])", notiz) if s]
        assert 1 <= len(saetze) <= 2, (kurz, saetze)


def test_jede_karte_erklaert_die_sechs_teile():
    """Wozu, jedes Feld in einem Satz, Fluss, Auslöser, Verbindung, ehrliche Grenze — nichts leer."""
    kt = _werkzeug()
    for k in kt.KNOTEN:
        assert k["hilfe"] and k["loest"] and k["verbunden"] and k["grenze"], k["typ"]
        assert k["felder"], k["typ"]
        for feld, satz in k["felder"]:
            assert feld and satz.endswith((".", "»", ")")), (k["typ"], feld)
        assert k["fluss"], k["typ"]
        for art, sorte, text in k["fluss"]:
            assert art in ("ein", "aus") and sorte.lower() in kt.PORT and text, (k["typ"], sorte)
        assert k["visbox"][0] in kt.VISBOX_TON, k["typ"]


def test_stellvertreter_sind_gekennzeichnet():
    """Knoten, die in Visbox nichts bewirken, sagen es — statt verschwiegen zu werden."""
    kt = _werkzeug()
    stellvertreter = sorted(k["typ"] for k in kt.KNOTEN if k["visbox"][0] == "stellvertreter")
    assert stellvertreter == ["aufnahme", "blatt", "kameraAus3d"]
    for k in kt.KNOTEN:
        if k["visbox"][0] == "stellvertreter":
            assert "Stellvertreter" in kt.NOTIZEN[k["kurz"]], k["typ"]


def _sichtbarer_text(inhalt: str) -> str:
    """Was auf der Karte zu lesen ist: ohne Stilblock (Schriftpfade) und ohne Tags."""
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", inhalt, flags=re.S))


def test_regel_100_kein_partnername_auf_karten_und_im_blatt(tmp_path):
    """Entscheid 100/100a: Was Leser sehen, nennt das Partnerprogramm und die anderen Worker nicht."""
    kt = _werkzeug()
    assert kt.main(["--ausgabe", str(tmp_path), "--nur-html"]) == 0
    texte = {p.name: _sichtbarer_text(p.read_text(encoding="utf-8")) for p in tmp_path.glob("*.html")}
    texte.update({p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("*.json")})
    texte["KNOTEN_ERKLAERT.md"] = (WURZEL / "docs" / "KNOTEN_ERKLAERT.md").read_text(encoding="utf-8")
    for name, text in texte.items():
        klein = text.lower()
        for wort in ("kosmoorbit", "kosmovis", "integrator", "zentrale"):
            assert wort not in klein, (name, wort)
    assert set(kt.VERBOTEN) >= {"kosmoorbit", "kosmovis", "integrator", "zentrale"}


def test_das_blatt_erklaert_jede_knotenart():
    """Jede Knotenart der Registrierung hat im Blatt einen eigenen Abschnitt mit ihrem Namen."""
    blatt = (WURZEL / "docs" / "KNOTEN_ERKLAERT.md").read_text(encoding="utf-8")
    kopfe = re.findall(r"^### \d+ · (.+)$", blatt, re.M)
    namen = {re.split(r" — ", k)[0] for k in kopfe}
    assert {v["label"] for v in _katalog().values()} == namen


def test_nur_html_schreibt_html_und_json_ohne_chromium(tmp_path, capsys):
    kt = _werkzeug()
    assert kt.main(["--ausgabe", str(tmp_path), "--nur-html", "--karte", "render"]) == 0
    namen = sorted(p.name for p in tmp_path.iterdir())
    assert namen == ["20261023-knoten-14-render.html", "20261023-knoten-14-render.json"]
    tafel = json.loads((tmp_path / "20261023-knoten-14-render.json").read_text(encoding="utf-8"))
    assert tafel["gruppe"] == "Visbox · Was die Knoten tun"
    assert tafel["titel"] == "Knoten 14: Render"
    assert set(tafel) == {"titel", "gruppe", "notiz"}


def test_alle_karten_ohne_heimpfad_in_der_tafelnotiz(tmp_path):
    """Regel 3 und `tafel/LIESMICH.md`: Was auf die Tafel geht, nennt keine Heimpfade."""
    kt = _werkzeug()
    assert kt.main(["--ausgabe", str(tmp_path), "--nur-html"]) == 0
    jsons = sorted(tmp_path.glob("*.json"))
    assert len(jsons) == 18  # Übersicht und siebzehn Knoten
    for p in jsons:
        assert "/home/" not in p.read_text(encoding="utf-8"), p.name


def test_unbekannte_karte_und_fehlendes_chromium_sagen_es(tmp_path, capsys):
    kt = _werkzeug()
    assert kt.main(["--ausgabe", str(tmp_path), "--karte", "gibt-es-nicht", "--nur-html"]) == 2
    assert kt.main(["--ausgabe", str(tmp_path), "--karte", "render",
                    "--chrome", str(tmp_path / "kein-chrome")]) == 3
    assert "Kein Chromium" in capsys.readouterr().err


def test_zuschneiden_entfernt_den_schwarzen_streifen(tmp_path):
    from PIL import Image

    kt = _werkzeug()
    bild = Image.new("RGB", (200, 300), (0, 0, 0))
    bild.paste((18, 21, 28), (0, 0, 200, 120))
    pfad = tmp_path / "karte.png"
    bild.save(pfad)
    assert kt.zuschneiden(pfad) == (200, 120)
