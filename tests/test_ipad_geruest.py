"""Das Gerüst der iPad-App — **die Stellen, an denen es still auseinanderläuft.**

Die App (``ipad/``) ist Swift und läuft nicht in diesem Lauf. Was sie mit dem Python-Teil
verbindet, sind Abschriften: die Wege des Servers, der Name, die Kennung, der Dienst. Eine
Abschrift veraltet, ohne dass es jemand merkt — *und am Gerät fällt es als 404 auf, oder
als App, die nach der Umbenennung an einer Stelle noch den alten Namen zeigt.*

Geprüft wird darum:

1. **Die Wege stimmen überein** — gelesen aus den Wegtafeln des Server-**Moduls**, nicht
   per Textsuche in ``server.py``, und zusätzlich an der Wirkung: Jeder Weg der App wird
   am Server angefragt und darf nicht «Unbekannter Weg» sagen. Die Swift-Datei wird als
   Text gelesen; sie ist die Gegenseite und läuft hier nicht.
2. **Name, Kennung und Dienst stehen an einer Stelle** (``Marke.swift``), und das
   Manifest, das sie wiederholen muss, stimmt mit ihr überein.
3. **Der Kern bleibt plattformneutral** — er importiert nur Foundation.
4. **Der Kern, der geprüft wird, ist der, der in die App geht** (ein Verweis, keine Kopie).
5. Und wenn ``swift`` da ist, fährt ``swift test`` im Kern wirklich.
6. **Die mitgelieferten Schriften** (seit dem 23.09.2026): Sie liegen im App-Paket, sind
   echte TrueType-Dateien, tragen je Familie ihre Lizenz daneben, stehen mit Prüfsumme im
   ``NOTICE``, und jeder Name, unter dem die App sie verlangt, steht in der Datei selbst.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import hashlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad"
APP = IPAD / "Visbox.swiftpm"
APP_KERN = APP / "Kern"
KERNPAKET = IPAD / "VisboxKern"
KERN_QUELLEN = KERNPAKET / "Sources" / "VisboxKern"
KERN_PROBEN = KERNPAKET / "Tests" / "VisboxKernTests"
MARKE = KERN_QUELLEN / "Marke.swift"
WEGE = KERN_QUELLEN / "Wege.swift"
APP_MANIFEST = APP / "Package.swift"
KERN_MANIFEST = KERNPAKET / "Package.swift"
ARBEITSABLAUF = WURZEL / ".github" / "workflows" / "ipad.yml"
FLAECHE = WURZEL / "oberflaeche"
SCHRIFTEN = APP / "Schriften"
ZEICHENBLATT = APP / "Leiste" / "Zeichenblatt.swift"
NOTICE = WURZEL / "NOTICE"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


# ------------------------------------------------------------------ Lesen der Swift-Seite

def _ohne_kommentarzeilen(text: str) -> str:
    """Der Quelltext ohne ganze Kommentarzeilen (``//``, ``///``).

    Nur ganze Zeilen: Ein ``//`` mitten in einer Zeile kann in einer Zeichenkette stehen
    (``"http://…"``), und dort abzuschneiden hiesse, die Zeichenkette zu verstümmeln.
    """
    return "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("//"))


def _zeichenketten(text: str) -> list[str]:
    """Alle einzeiligen Zeichenketten-Literale, auch die rohen (``#"…"#``)."""
    code = _ohne_kommentarzeilen(text)
    return (re.findall(r'#"(.*?)"#', code)
            + re.findall(r'(?<!#)"((?:[^"\\\n]|\\.)*)"(?!#)', code))


def _swift_wege() -> dict[str, tuple[str, str, bool]]:
    """``{name: (METHODE, pfad, ohne_anmeldung)}`` aus ``Wege.swift``."""
    text = _ohne_kommentarzeilen(WEGE.read_text(encoding="utf-8"))
    muster = re.compile(
        r'static let (\w+)\s*=\s*Weg\(\s*pfad:\s*"([^"]+)"\s*,\s*methode:\s*\.(get|post)'
        r'(\s*,\s*ohneAnmeldung:\s*(true|false))?\s*\)', re.S)
    wege = {}
    for name, pfad, methode, _, offen in muster.findall(text):
        wege[name] = (methode.upper(), pfad, offen == "true")
    return wege


def _swift_alle() -> list[str]:
    text = _ohne_kommentarzeilen(WEGE.read_text(encoding="utf-8"))
    treffer = re.search(r"static let alle:\s*\[Weg\]\s*=\s*\[(.*?)\]", text, re.S)
    assert treffer, "Wege.swift hat keine Liste `alle` mehr"
    return re.findall(r"\w+", treffer.group(1))


def _marke() -> dict[str, str]:
    text = _ohne_kommentarzeilen(MARKE.read_text(encoding="utf-8"))
    werte = dict(re.findall(r'static let (\w+)\s*=\s*"([^"]+)"', text))
    assert {"name", "kennung", "dienst"} <= set(werte), werte
    return werte


def _swift_dateien(ordner: Path) -> list[Path]:
    """Jede Swift-Datei einmal — der Kern ist über den Verweis doppelt erreichbar."""
    gesehen, dateien = set(), []
    for weg, _, namen in os.walk(ordner, followlinks=True):
        if ".build" in Path(weg).parts or ".swiftpm" in Path(weg).parts:
            continue
        for n in namen:
            p = Path(weg) / n
            if p.suffix == ".swift" and p.resolve() not in gesehen:
                gesehen.add(p.resolve())
                dateien.append(p)
    return sorted(dateien)


# ------------------------------------------------------------- eine Anfrage ohne Netz

class _Anfrage:
    """Eine ganze Anfrage an ``Flaeche`` — ``do_GET``/``do_POST`` laufen wirklich.

    Dieselbe Bauform wie in ``tests/test_oberflaeche.py``; sie steht hier ein zweites Mal,
    weil Probedateien einander nicht importieren.
    """

    def __init__(self, modul, *, befehl, weg, kennwort="geheim", angemeldet=True,
                 offen=None, rumpf=b"{}"):
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": None, "kopplung_offen": offen})
        kopf = None
        if angemeldet:
            kopf = "Basic " + base64.b64encode(
                f"{modul.BENUTZER}:{kennwort}".encode()).decode()
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": kopf, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda *a: None
        self.selbst.end_headers = lambda: None

    def stelle(self) -> "_Anfrage":
        (self.selbst.do_GET if self.selbst.command == "GET" else self.selbst.do_POST)()
        return self

    @property
    def text(self) -> str:
        return self.selbst.wfile.getvalue().decode("utf-8", "replace")


# ============================================================ 1 · Die Wege stimmen überein

def test_die_wege_der_app_sind_die_wege_des_servers(server):
    """Beide Richtungen, getrennt nach Methode.

    *Ein Weg, den nur die App kennt, ist ein 404 am Gerät. Ein Weg, den nur der Server
    kennt, ist eine Fähigkeit, die das iPad nicht erreicht* — und fällt niemandem auf,
    weil sie nichts kaputtmacht, sondern nur fehlt.
    """
    wege = _swift_wege()
    assert wege, "in Wege.swift wurde kein einziger Weg gefunden — hat sich die Form geändert?"

    app = {(m, p) for m, p, _ in wege.values()}
    bedient = ({("GET", w) for w in server.WEGTAFEL_LESEN}
               | {("POST", w) for w in server.WEGTAFEL})

    nur_app = sorted(app - bedient)
    nur_server = sorted(bedient - app)
    assert not nur_app, f"Die App kennt Wege, die der Server nicht bedient: {nur_app}"
    assert not nur_server, (
        f"Der Server bedient Wege, die die App nicht kennt: {nur_server}. In "
        f"`ipad/Visbox.swiftpm/Kern/Wege.swift` nachtragen (und in `alle`).")


def test_jeder_weg_steht_auch_in_der_liste_alle():
    """Ein Weg, der als Konstante steht und in ``alle`` fehlt, ist für jede Schleife
    über ``alle`` unsichtbar — also für genau die Stellen, die «alle Wege» meinen."""
    deklariert = set(_swift_wege())
    gelistet = _swift_alle()
    assert sorted(gelistet) == sorted(deklariert), (
        f"deklariert, aber nicht in `alle`: {sorted(deklariert - set(gelistet))}; "
        f"in `alle`, aber nicht deklariert: {sorted(set(gelistet) - deklariert)}; "
        f"doppelt: {sorted({n for n in gelistet if gelistet.count(n) > 1})}")


def test_jeder_weg_der_app_ist_am_server_erreichbar(server):
    """**An der Wirkung**, nicht an der Tafel: jeder Weg der App als echte Anfrage.

    Die Probe darüber vergleicht zwei Listen. Diese hier fragt an — und fängt damit auch
    den Fall, dass ein Weg in der Tafel steht und seine Methode ihn nicht bedient.
    """
    for name, (methode, pfad, _) in _swift_wege().items():
        weg = pfad + ("?name=bild.png" if pfad == server.WEG_BILD else "")
        a = _Anfrage(server, befehl=methode, weg=weg).stelle()
        assert len(a.codes) == 1, (name, a.codes)
        assert "Unbekannter Weg" not in a.text, f"{name}: {methode} {pfad} → {a.text}"


def test_ohne_anmeldung_geht_genau_der_weg_den_die_app_so_nennt(server):
    """``ohneAnmeldung`` in der App ist eine Behauptung über die Tür des Servers.

    Geprüft wird sie an der Tür selbst: mit offener Kopplung, **ohne** Anmeldung. Was die
    App als offen führt, darf nicht 401 geben; alles andere muss.
    """
    from aiimaging import kopplung

    for name, (methode, pfad, ohne) in _swift_wege().items():
        offen = kopplung.eroeffne(_pin="123456")
        a = _Anfrage(server, befehl=methode, weg=pfad, angemeldet=False, offen=offen,
                     rumpf=json.dumps({"pin": "000000"}).encode()).stelle()
        if ohne:
            assert a.codes != [401], f"{name} gilt in der App als offen, der Server sagt 401"
        else:
            assert a.codes == [401], (
                f"{name}: {methode} {pfad} kam ohne Anmeldung durch ({a.codes}) — oder die "
                f"App führt ihn fälschlich als angemeldet")


def test_der_vorgabe_anschluss_der_app_ist_der_des_servers(server):
    """Wer am iPad die Adresse **ohne** Anschluss eintippt, bekommt ``Suche.vorgabeAnschluss``.

    Das ist eine Abschrift von ``VORGABE_ANSCHLUSS`` — und bis zur Durchsicht vom
    22.09.2026 eine unbewachte. Läuft sie auseinander, sagt das iPad «nimmt keine
    Verbindung an», obwohl die HomeStation läuft, nur auf einem anderen Anschluss.

    Die Serverseite wird **am Modul** gelesen und an dem, was ``baue_server`` ohne Angabe
    wirklich nimmt — nicht per Textsuche in ``server.py``.
    """
    import inspect

    text = _ohne_kommentarzeilen((KERN_QUELLEN / "Suche.swift").read_text(encoding="utf-8"))
    funde = re.findall(r"\bstatic\s+let\s+vorgabeAnschluss\s*(?::\s*Int\s*)?=\s*(\d+)", text)
    assert len(funde) == 1, f"vorgabeAnschluss in Suche.swift nicht genau einmal gefunden: {funde}"
    app = int(funde[0])

    gebaut = inspect.signature(server.baue_server).parameters["anschluss"].default
    assert gebaut == server.VORGABE_ANSCHLUSS, (gebaut, server.VORGABE_ANSCHLUSS)
    assert app == server.VORGABE_ANSCHLUSS, (
        f"Die App tippt ohne Angabe Anschluss {app} ein, der Server hört ohne Angabe auf "
        f"{server.VORGABE_ANSCHLUSS}. `Suche.vorgabeAnschluss` nachziehen.")


# ================================================ 2 · Name, Kennung, Dienst: eine Stelle

def test_name_kennung_und_dienst_stehen_nur_in_der_marke():
    """Eine Abwesenheitsprüfung über **jede** Swift-Datei unter ``ipad/``.

    Ausgenommen sind nur die Marke selbst und die beiden Manifeste — die Manifeste werden
    in der nächsten Probe gegen die Marke geprüft, nicht übersehen.

    Kennung und Dienst dürfen nirgends stehen, auch nicht im Kommentar (sie sind
    unverwechselbar). Der Name darf in keiner **Zeichenkette** stehen: In einem
    Typnamen wie ``VisboxApp`` ist er Quelltext und wird nie angezeigt; in einer
    Zeichenkette erscheint er am Bildschirm und bliebe nach der Umbenennung stehen.
    """
    marke = _marke()
    ausnahmen = {MARKE.resolve(), APP_MANIFEST.resolve(), KERN_MANIFEST.resolve()}
    funde = []
    for datei in _swift_dateien(IPAD):
        if datei.resolve() in ausnahmen:
            continue
        text = datei.read_text(encoding="utf-8")
        for schluessel in ("kennung", "dienst"):
            if marke[schluessel] in text:
                funde.append(f"{datei.relative_to(WURZEL)}: {schluessel} {marke[schluessel]!r}")
        for kette in _zeichenketten(text):
            if marke["name"].lower() in kette.lower():
                funde.append(f"{datei.relative_to(WURZEL)}: Name in {kette!r}")
    assert not funde, "Ausserhalb von Marke.swift:\n  " + "\n  ".join(funde)


def test_das_app_manifest_wiederholt_die_marke_wortgleich():
    """Das Manifest kann ``Marke.swift`` nicht lesen und muss Kennung, Dienst und Namen
    darum wiederholen. *Eine Wiederholung ist nur dann harmlos, wenn sie bewacht ist.*
    Ebenso der Arbeitsablauf, der die App unter ihrem Namen übersetzt."""
    marke = _marke()
    manifest = _ohne_kommentarzeilen(APP_MANIFEST.read_text(encoding="utf-8"))

    kennung = re.findall(r'bundleIdentifier:\s*"([^"]+)"', manifest)
    assert kennung == [marke["kennung"]], kennung

    dienste = re.findall(r'bonjourServiceTypes:\s*\[([^\]]*)\]', manifest)
    assert len(dienste) == 1, dienste
    assert re.findall(r'"([^"]+)"', dienste[0]) == [marke["dienst"]], dienste[0]

    produkt = re.findall(r'\.iOSApplication\(\s*name:\s*"([^"]+)"', manifest)
    assert produkt == [marke["name"]], produkt

    ablauf = ARBEITSABLAUF.read_text(encoding="utf-8")
    schema = re.findall(r"-scheme\s+(\S+)", ablauf)
    assert schema == [marke["name"]], (
        f"ipad.yml übersetzt das Schema {schema}, die App heisst {marke['name']!r}")


# ======================================================= 3 · Der Kern bleibt neutral

def _importe(datei: Path) -> list[str]:
    text = _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))
    # `[ \t]` UND NICHT `\s`: `\s` laeuft ueber das Zeilenende, und dann las die Probe
    # «import» und «final» aus zwei verschiedenen Zeilen als einen Import (erster Lauf,
    # 22.09.2026). Die Art (`import struct X.Y`) ist freiwillig; gemeldet wird das Modul.
    return re.findall(r"^[ \t]*(?:@\w+[ \t]+)*import[ \t]+(?:(?:struct|class|enum|protocol"
                      r"|func|var|let|typealias)[ \t]+)?([\w.]+)", text, re.M)


def test_der_kern_importiert_nur_foundation():
    """Der Kern soll unter Linux bauen und später in einer anderen App weiterleben. Ein
    ``import UIKit`` darin bände ihn an das iPad — und fiele unter Linux erst beim
    Übersetzen auf, also nur dort, wo jemand übersetzt."""
    dateien = sorted(KERN_QUELLEN.glob("*.swift"))
    assert dateien, "keine Quellen im Kern gefunden"
    for datei in dateien:
        text = datei.read_text(encoding="utf-8")
        assert set(_importe(datei)) <= {"Foundation"}, (datei.name, _importe(datei))
        # AUCH NICHT DURCH DIE HINTERTUER. `#if canImport(UIKit)` baut unter Linux
        # still ohne den Teil und auf dem iPad mit — zwei verschiedene Kerne.
        assert "canImport" not in text, datei.name
        assert "@_exported" not in text, datei.name


def test_die_proben_des_kerns_importieren_nur_xctest_foundation_und_den_kern():
    dateien = sorted(KERN_PROBEN.glob("*.swift"))
    assert dateien, "keine Proben im Kern gefunden"
    for datei in dateien:
        assert set(_importe(datei)) <= {"XCTest", "Foundation", "VisboxKern"}, (
            datei.name, _importe(datei))


def test_die_app_importiert_den_kern_nicht_als_modul():
    """Der Kern wird in der App **mitübersetzt** (derselbe Zielbereich, siehe
    ``ipad/LIESMICH.md``). Ein ``import VisboxKern`` in der App fände dort kein Modul und
    bräche die Übersetzung — aber erst auf dem Mac, also nicht in diesem Lauf."""
    for datei in _swift_dateien(APP):
        assert "VisboxKern" not in _importe(datei), datei.relative_to(WURZEL)


# ====================================== 4 · Der geprüfte Kern ist der eingebaute Kern

def test_der_kern_des_pakets_ist_ein_verweis_auf_den_kern_der_app():
    """**Die tragende Behauptung der Ablage.** Geprüft wird im Kernpaket, übersetzt wird
    im App-Paket. Wären es zwei Kopien, prüfte ``swift test`` eine, und in die App ginge
    die andere — und die beiden liefen auseinander, ohne dass eine Probe es sähe."""
    assert KERN_QUELLEN.is_symlink(), f"{KERN_QUELLEN.relative_to(WURZEL)} ist kein Verweis"
    ziel = os.readlink(KERN_QUELLEN)
    assert not os.path.isabs(ziel), f"absoluter Verweis {ziel!r} — bricht in jedem anderen Klon"
    assert KERN_QUELLEN.resolve() == APP_KERN.resolve()
    # UND KEIN VERWEIS IM APP-PAKET. Swift Playgrounds sieht nur, was im `.swiftpm` liegt;
    # ein Verweis nach draussen laege dort ins Leere.
    for weg, ordner, namen in os.walk(APP):
        for n in ordner + namen:
            p = Path(weg) / n
            assert not p.is_symlink(), f"Verweis im App-Paket: {p.relative_to(WURZEL)}"


# =================================================================== 5 · swift test

def _swift():
    gefunden = shutil.which("swift")
    if gefunden:
        return gefunden
    kandidat = Path("/opt/swift/usr/bin/swift")
    return str(kandidat) if kandidat.is_file() else None


def test_swift_test_im_kern():
    """Die Proben des Kerns, **wirklich gefahren** — wenn eine Swift-Kette da ist.

    Ohne Kette wird übersprungen, und zwar mit Grund. *Ein Überspringen ohne Grund sieht
    in der Zusammenfassung aus wie ein Bestehen.*
    """
    swift = _swift()
    if swift is None:
        pytest.skip("keine Swift-Kette (weder im PATH noch unter /opt/swift) — "
                    "Anleitung in ipad/LIESMICH.md")
    lauf = subprocess.run([swift, "test"], cwd=KERNPAKET, capture_output=True, text=True,
                          timeout=900)
    ausgabe = (lauf.stdout + lauf.stderr)[-4000:]
    assert lauf.returncode == 0, ausgabe
    # GEFAHREN, NICHT NUR GEBAUT. Ein Lauf mit null Proben ist ebenfalls «returncode 0».
    gefahren = re.findall(r"Executed (\d+) tests?, with 0 failures", ausgabe)
    assert gefahren and int(gefahren[-1]) > 0, ausgabe


# ============================================================ 6 · Die Schriften (23.09.2026)
#
# Entscheide 20 und 25: IBM Plex Sans, IBM Plex Mono und Instrument Serif, SIL OFL 1.1,
# MITGELIEFERT und nicht geladen. Was hier still auseinanderlaufen kann: ein Name in der App,
# den keine Datei traegt (am Geraet: die Systemschrift, ohne dass es jemand merkt), eine
# Datei ohne Lizenz daneben, eine Datei, die nicht die im `NOTICE` ist, und ein Manifest,
# das die Dateien nicht in die App legt.
#
# Die Schriftdateien werden SELBST gelesen (Tabellenverzeichnis, `name`, `fvar`, `OS/2` nach
# der OpenType-Beschreibung), nur mit der Standardbibliothek — keine neue Abhaengigkeit.

def _sfnt_tabellen(daten: bytes) -> dict[str, bytes]:
    """Die Tabellen einer TrueType-Datei, je Kennung ihr Inhalt."""
    anzahl = struct.unpack(">H", daten[4:6])[0]
    tabellen = {}
    for i in range(anzahl):
        kennung, _, anfang, laenge = struct.unpack(">4sIII", daten[12 + 16 * i:28 + 16 * i])
        assert anfang + laenge <= len(daten), f"Tabelle {kennung!r} reicht über das Dateiende"
        tabellen[kennung.decode("latin-1")] = daten[anfang:anfang + laenge]
    return tabellen


def _sfnt_namen(tabellen: dict[str, bytes]) -> dict[int, set[str]]:
    """Die Namentabelle: je Namensnummer die Einträge (6 = PostScript-Name)."""
    name = tabellen["name"]
    _, anzahl, ablage = struct.unpack(">HHH", name[:6])
    namen: dict[int, set[str]] = {}
    for i in range(anzahl):
        plattform, _, _, nummer, laenge, stelle = struct.unpack(
            ">HHHHHH", name[6 + 12 * i:18 + 12 * i])
        roh = name[ablage + stelle:ablage + stelle + laenge]
        text = roh.decode("utf-16-be") if plattform in (0, 3) else roh.decode("latin-1")
        namen.setdefault(nummer, set()).add(text)
    return namen


def _sfnt_postscript_namen(tabellen: dict[str, bytes]) -> set[str]:
    """Jeder PostScript-Name der Datei: der eigene (Nr. 6) und, bei einer variablen Datei,
    die ihrer benannten Schnitte (Tabelle ``fvar``)."""
    namen = _sfnt_namen(tabellen)
    gefunden = set(namen.get(6, set()))
    fvar = tabellen.get("fvar")
    if fvar:
        _, _, achsen_ab, _, achsen, achsgroesse, schnitte, schnittgroesse = struct.unpack(
            ">HHHHHHHH", fvar[:16])
        ab = achsen_ab + achsen * achsgroesse
        for i in range(schnitte):
            eintrag = fvar[ab + i * schnittgroesse:ab + (i + 1) * schnittgroesse]
            if schnittgroesse >= 6 + 4 * achsen:
                nummer = struct.unpack(">H", eintrag[4 + 4 * achsen:6 + 4 * achsen])[0]
                gefunden |= namen.get(nummer, set())
    return gefunden


def _sfnt_familie(tabellen: dict[str, bytes]) -> str:
    """Der Familienname, wie ihn ein Mensch liest (Nr. 16, sonst Nr. 1)."""
    namen = _sfnt_namen(tabellen)
    return sorted(namen.get(16) or namen[1])[0]


def _schriftdateien() -> list[Path]:
    dateien = sorted(SCHRIFTEN.rglob("*.ttf"))
    assert dateien, f"keine Schriftdatei unter {SCHRIFTEN.relative_to(WURZEL)}"
    return dateien


def _schnitte() -> list[dict]:
    """Die Einträge von ``Schrift.schnitte`` in ``Leiste/Zeichenblatt.swift``."""
    text = _ohne_kommentarzeilen(ZEICHENBLATT.read_text(encoding="utf-8"))
    muster = re.compile(
        r'Schriftschnitt\(\s*familie:\s*\.(\w+)\s*,\s*postScript:\s*"([^"]+)"\s*,'
        r'\s*datei:\s*"([^"]+)"\s*,\s*staerke:\s*(\d+)\s*\)')
    schnitte = [dict(familie=f, postscript=p, datei=d, staerke=int(s))
                for f, p, d, s in muster.findall(text)]
    # NICHT VAKUUM: Ohne diese Zeile wäre jede Probe über die Schnitte bei einem
    # umformatierten Eintrag grün, weil sie über eine leere Liste liefe.
    assert len(schnitte) == text.count("Schriftschnitt(familie:"), (
        "Ein Eintrag in `Schrift.schnitte` hat nicht die erwartete Form "
        "(familie, postScript, datei, staerke)")
    familien = set(re.findall(r"^\s*case\s+(\w+)\s*$",
                              re.search(r"enum Schriftfamilie[^{]*\{(.*?)\n\}", text,
                                        re.S).group(1), re.M))
    assert familien and {s["familie"] for s in schnitte} == familien, (
        f"Familien {sorted(familien)}, Schnitte für {sorted({s['familie'] for s in schnitte})}"
        " — eine Familie ohne Schnitt fiele am Gerät still auf die Systemschrift.")
    return schnitte


def test_die_schriftdateien_liegen_im_paket_und_sind_truetype():
    """Echte TrueType-Dateien, keine Fehlerseite des Proxys, kein Git-LFS-Zeiger.

    Eine abgebrochene oder umgeleitete Abfrage liefert HTML oder Text mit der Endung
    ``.ttf`` — beim Übersetzen fällt das nicht auf, am Gerät scheitert die Registrierung.
    """
    for datei in _schriftdateien():
        daten = datei.read_bytes()
        assert daten[:4] == b"\x00\x01\x00\x00", (
            f"{datei.relative_to(WURZEL)} beginnt mit {daten[:4]!r}, nicht wie TrueType")
        tabellen = _sfnt_tabellen(daten)
        fehlend = {"cmap", "glyf", "head", "name", "OS/2"} - set(tabellen)
        assert not fehlend, f"{datei.name}: ohne Tabelle(n) {sorted(fehlend)}"


def test_je_familie_liegt_ihre_lizenz_daneben():
    """Die OFL verlangt, dass der Lizenztext mit der Schrift geht (Bedingung 2).

    Der Ordner einer Familie trägt genau einen Lizenztext ``<Ordner>-OFL.txt`` — der
    Wortlaut aus der Verteilung, nur umbenannt, weil ``.process`` flach ablegt (siehe
    ``test_kein_dateiname_kommt_unter_schriften_doppelt_vor``).
    """
    ordner = sorted({d.parent for d in _schriftdateien()})
    for o in ordner:
        lizenzen = sorted(o.glob("*OFL*"))
        assert [p.name for p in lizenzen] == [f"{o.name}-OFL.txt"], (
            f"{o.relative_to(WURZEL)}: Lizenztexte {[p.name for p in lizenzen]}")
        text = lizenzen[0].read_text(encoding="utf-8")
        assert "This Font Software is licensed under the SIL Open Font License, Version 1.1." \
            in text, lizenzen[0].name
        assert "SIL OPEN FONT LICENSE Version 1.1" in text, lizenzen[0].name


def test_kein_dateiname_kommt_unter_schriften_doppelt_vor():
    """``resources: [.process(...)]`` legt alle Dateien FLACH in die App.

    Zwei gleichnamige Dateien, auch in verschiedenen Unterordnern, bricht SwiftPM ab:
    «multiple resources named 'OFL.txt' in target 'AppModule'» — nachgefahren am
    23.09.2026 mit Swift 6.4 unter Linux, an einer Kopie dieses Aufbaus mit dreimal
    ``OFL.txt`` aus der Verteilung.
    """
    namen = [p.name for p in SCHRIFTEN.rglob("*") if p.is_file()]
    doppelt = sorted({n for n in namen if namen.count(n) > 1})
    assert not doppelt, f"doppelt unter Schriften/: {doppelt}"


def test_das_manifest_legt_die_schriften_in_die_app():
    """Ohne Angabe wären die Dateien im Ziel «unbehandelt»: SwiftPM warnt, die Prüfstrecke
    verlangt null Warnungen, und in der App fehlten die Schriften (nachgefahren wie oben).
    Die Form ist die, die Swift Playgrounds selbst schreibt."""
    manifest = _ohne_kommentarzeilen(APP_MANIFEST.read_text(encoding="utf-8"))
    ziel = re.search(r"\.executableTarget\((.*?)\n\s*\)", manifest, re.S)
    assert ziel, "kein executableTarget im Manifest"
    ressourcen = re.findall(r"resources:\s*\[(.*?)\]", ziel.group(1), re.S)
    assert len(ressourcen) == 1, ressourcen
    eintraege = re.findall(r'\.(\w+)\("([^"]+)"\)', ressourcen[0])
    assert ("process", SCHRIFTEN.name) in eintraege, eintraege
    assert SCHRIFTEN.is_dir()


def test_das_notice_nennt_jede_schriftdatei_mit_ihrer_pruefsumme():
    """Regel 1, Präzisierung Schriften: *unverändert und mit ihrer Lizenz im NOTICE*.

    Geprüft wird an der Datei: Ihr Familienname (aus der Namentabelle) steht als Kopf eines
    Blocks mit ``OFL-1.1``, und in diesem Block steht ihr Dateiname samt der SHA-256 der
    Datei, wie sie im Repo liegt. Ändert jemand die Datei, stimmt die Prüfsumme nicht mehr.
    """
    bloecke = [b.strip() for b in re.split(r"^-{80}$", NOTICE.read_text(encoding="utf-8"),
                                           flags=re.M) if b.strip()]
    for datei in _schriftdateien():
        familie = _sfnt_familie(_sfnt_tabellen(datei.read_bytes()))
        passend = [b for b in bloecke if b.splitlines()[0].startswith(familie + " ")]
        assert len(passend) == 1, f"NOTICE: {len(passend)} Blöcke für {familie!r}"
        block = passend[0]
        assert re.search(r"\bOFL-1\.1\b", block.splitlines()[0]), block.splitlines()[0]
        assert datei.name in block, f"NOTICE, Block {familie!r}: {datei.name} fehlt"
        pruefsumme = hashlib.sha256(datei.read_bytes()).hexdigest()
        assert re.search(re.escape(datei.name) + r"[^\n]*\n\s*SHA-256 " + pruefsumme, block), (
            f"NOTICE, Block {familie!r}: {datei.name} steht nicht mit SHA-256 {pruefsumme}")


def test_jeder_postscript_name_steht_in_seiner_datei():
    """Der Name, unter dem die App eine Schrift verlangt, muss die Datei selbst tragen.

    Sonst liefert das System am Gerät unter diesem Namen eine Ersatzschrift — die App fällt
    dann zwar auf die Systemschrift zurück (``Schriftregister``), aber still. Gelesen wird
    die Namentabelle der Datei (Nr. 6) und bei einer variablen Datei die Namen ihrer
    benannten Schnitte; die Stärke wird gegen ``OS/2`` geprüft (``usWeightClass``).
    """
    dateien = {d.stem: d for d in _schriftdateien()}
    for schnitt in _schnitte():
        datei = dateien.get(schnitt["datei"])
        assert datei, f"{schnitt['datei']}.ttf liegt nicht unter Schriften/"
        tabellen = _sfnt_tabellen(datei.read_bytes())
        namen = _sfnt_postscript_namen(tabellen)
        assert schnitt["postscript"] in namen, (
            f"{schnitt['postscript']!r} steht nicht in {datei.name} (dort: {sorted(namen)})")
        staerke = struct.unpack(">H", tabellen["OS/2"][4:6])[0]
        assert staerke == schnitt["staerke"], (
            f"{schnitt['postscript']}: in der App {schnitt['staerke']}, in der Datei {staerke}")


def test_jede_mitgelieferte_schriftdatei_wird_benutzt():
    """Eine Datei, die keiner verlangt, geht trotzdem in die App — und ins NOTICE."""
    benutzt = {s["datei"] for s in _schnitte()}
    unbenutzt = sorted(d.name for d in _schriftdateien() if d.stem not in benutzt)
    assert not unbenutzt, f"mitgeliefert, aber in `Schrift.schnitte` nicht genannt: {unbenutzt}"


def test_die_schriftnamen_stehen_nur_im_zeichenblatt():
    """Eine Abwesenheitsprüfung: Kein PostScript- oder Dateiname einer Schrift und kein
    ``.custom("…")`` mit festem Namen ausserhalb von ``Zeichenblatt.swift``. Wer an einer
    zweiten Stelle eine Schrift beim Namen nennt, umgeht den Rückfall auf die
    Systemschrift, wenn die Registrierung scheitert."""
    namen = {s["postscript"] for s in _schnitte()} | {s["datei"] for s in _schnitte()}
    funde = []
    for datei in _swift_dateien(APP):
        if datei.resolve() == ZEICHENBLATT.resolve():
            continue
        text = datei.read_text(encoding="utf-8")
        funde += [f"{datei.relative_to(WURZEL)}: {n}" for n in sorted(namen) if n in text]
        if re.search(r'\.custom\(\s*"', _ohne_kommentarzeilen(text)):
            funde.append(f"{datei.relative_to(WURZEL)}: .custom mit festem Namen")
    assert not funde, "Schriftnamen ausserhalb des Zeichenblatts:\n  " + "\n  ".join(funde)
