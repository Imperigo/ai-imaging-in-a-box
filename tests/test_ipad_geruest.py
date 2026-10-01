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
7. **Die Mac-App** (seit dem 01.10.2026, v0.1.7): Ihre ``Info.plist`` wiederholt die Marke,
   ihr Manifest bindet nur den Kern ein, sie importiert nur Apples Plattform und den Kern,
   das Kennwort liegt in keiner Datei mit ``UserDefaults`` und in keinem Protokoll, und die
   Prüfstrecke setzt das Bündel aus genau diesen Angaben zusammen.
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
MAC = IPAD / "VisboxMac"
MAC_MANIFEST = MAC / "Package.swift"
MAC_PLIST = MAC / "App" / "Info.plist"
MAC_QUELLEN = MAC / "Sources" / "VisboxMac"


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

    **Eine Ausnahme, und sie ist eng** (01.10.2026, Vorführmappe): die Kennung eines
    Dateiformats, ``<name>.<wort>/v<n>`` (``visbox.vorfuehrmappe/v1``, wie
    ``visbox.projekt/v1`` auf der Python-Seite). Sie ist kein Text am Bildschirm, sondern
    der Name eines Formats — und der soll eine Umbenennung **überleben**: Eine Mappe, die vor
    der Umbenennung geschrieben wurde, muss danach noch lesbar sein. Alles andere in
    derselben Zeichenkette bleibt geprüft.
    """
    marke = _marke()
    # DAS MANIFEST DER MAC-APP nennt Paket- und Zielnamen («VisboxMac», «../VisboxKern»):
    # Quelltext, der nie angezeigt wird. Dass dort NUR solche stehen, prüft
    # `test_das_mac_manifest_bindet_nur_den_kern_ein` — die Ausnahme ist bewacht, nicht offen.
    ausnahmen = {MARKE.resolve(), APP_MANIFEST.resolve(), KERN_MANIFEST.resolve(),
                 MAC_MANIFEST.resolve()}
    formatkennung = re.compile(re.escape(marke["name"].lower()) + r"\.[a-z]+/v\d+")
    funde = []
    for datei in _swift_dateien(IPAD):
        if datei.resolve() in ausnahmen:
            continue
        text = datei.read_text(encoding="utf-8")
        for schluessel in ("kennung", "dienst"):
            if marke[schluessel] in text:
                funde.append(f"{datei.relative_to(WURZEL)}: {schluessel} {marke[schluessel]!r}")
        for kette in _zeichenketten(text):
            if marke["name"].lower() in formatkennung.sub("", kette.lower()):
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


def test_die_app_sucht_ihre_schriften_nicht_in_bundle_module():
    """**Mac-CI, 23.09.2026.** Xcode legt für ein App-Paket (`.iOSApplication`) kein
    `Bundle.module` an — das Übersetzen brach daran ab, unter Linux fiel es nicht auf.
    Die Schriften werden darum im Bundle der App gesucht. Abwesenheit, weil der Fehler
    hier nicht übersetzt werden kann."""
    fundstellen = [
        f"{pfad.relative_to(APP)}:{nr}"
        for pfad in sorted(APP.rglob("*.swift"))
        for nr, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1)
        if "Bundle.module" in zeile and not zeile.lstrip().startswith("///")
        and not zeile.lstrip().startswith("//")
    ]
    assert not fundstellen, f"Bundle.module im App-Paket: {fundstellen}"


# ============================================================ 7 · Die Mac-App (01.10.2026)
#
# v0.1.7, Strom A: eine eigene App für den Mac, die den Kern mitbenutzt (Entscheid 44). Sie
# wird nur in der Prüfstrecke übersetzt — was hier steht, ist das, was ohne Übersetzer
# auseinanderlaufen kann: die Abschrift der Marke in der plist, die Angaben, aus denen die
# Prüfstrecke das Bündel zusammensetzt, und die Regel, dass das Kennwort nur im Schlüsselbund
# liegt.

def _plist() -> dict:
    import plistlib
    with MAC_PLIST.open("rb") as f:
        return plistlib.load(f)


def _mac_ziel() -> str:
    """Der Name des ausführbaren Ziels im Manifest der Mac-App."""
    manifest = _ohne_kommentarzeilen(MAC_MANIFEST.read_text(encoding="utf-8"))
    ziele = re.findall(r'\.executableTarget\(\s*name:\s*"([^"]+)"', manifest)
    assert len(ziele) == 1, ziele
    return ziele[0]


def _mac_code(datei: Path) -> str:
    """Der Quelltext ohne ganze Kommentarzeilen — ein Kommentar darf erklären, warum etwas
    NICHT in ``UserDefaults`` liegt."""
    return _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))


def test_die_mac_plist_wiederholt_die_marke():
    """Name und Dienst wortgleich, die Kennung als die des iPad **mit eigener Endung** — zwei
    Apps unter einer Kennung verwechselt macOS (Schlüsselbund, Einstellungen, Erlaubnisse)."""
    marke = _marke()
    plist = _plist()
    assert plist["CFBundleName"] == marke["name"], plist["CFBundleName"]
    assert plist["CFBundleDisplayName"] == marke["name"], plist["CFBundleDisplayName"]
    assert re.fullmatch(re.escape(marke["kennung"]) + r"\.[a-z0-9-]+",
                        plist["CFBundleIdentifier"]), (
        f"{plist['CFBundleIdentifier']!r} ist nicht {marke['kennung']!r} mit einer Endung")
    assert plist["NSBonjourServices"] == [marke["dienst"]], plist["NSBonjourServices"]
    satz = plist["NSLocalNetworkUsageDescription"]
    assert "iPad" in satz and "WLAN" in satz and "Heim-PC" in satz, satz
    assert plist["CFBundlePackageType"] == "APPL"


def test_die_mac_plist_und_das_manifest_sagen_dasselbe():
    """Das Programm, das ``swift build`` erzeugt, ist das, das die plist startet — und die
    Mindestfassung von macOS steht an beiden Stellen gleich."""
    plist = _plist()
    assert plist["CFBundleExecutable"] == _mac_ziel(), (plist["CFBundleExecutable"], _mac_ziel())
    manifest = _ohne_kommentarzeilen(MAC_MANIFEST.read_text(encoding="utf-8"))
    fassung = re.findall(r"\.macOS\(\.v(\d+)\)", manifest)
    assert fassung == ["14"], fassung
    assert plist["LSMinimumSystemVersion"] == "14.0", plist["LSMinimumSystemVersion"]


def test_das_mac_manifest_bindet_nur_den_kern_ein():
    """**Keine neue Abhängigkeit** (Regel 1): genau eine, der Kern per Pfad — und keine
    Adresse, von der SwiftPM etwas herunterlädt. Und weil das Manifest aus der Namensprobe
    ausgenommen ist: Es nennt nur Paket-, Ziel- und Pfadnamen, nichts, was angezeigt würde."""
    manifest = _ohne_kommentarzeilen(MAC_MANIFEST.read_text(encoding="utf-8"))
    assert ".package(url:" not in manifest
    assert re.findall(r'\.package\(\s*path:\s*"([^"]+)"\s*\)', manifest) == ["../VisboxKern"]
    assert (MAC / "../VisboxKern").resolve() == KERNPAKET.resolve()
    ziel = _mac_ziel()
    erlaubt = {"VisboxMac", ziel, "../VisboxKern", "VisboxKern", f"Sources/{ziel}"}
    fremd = sorted(set(_zeichenketten(manifest)) - erlaubt)
    assert not fremd, f"im Manifest der Mac-App: {fremd}"
    assert MAC_QUELLEN.is_dir()


def test_die_mac_app_importiert_nur_apples_plattform_und_den_kern():
    """Regel 1 an der Stelle, an der eine Abhängigkeit hereinkäme: an den Importen. Erlaubt
    sind Apples Bausteine (sie gehören zur Plattform, ``NOTICE``) und der Kern."""
    erlaubt = {"Foundation", "SwiftUI", "AppKit", "WebKit", "Network", "Security", "CoreText",
               "Combine", "Dispatch", "OSLog", "VisboxKern"}
    dateien = _swift_dateien(MAC_QUELLEN)
    assert dateien, "keine Quellen der Mac-App gefunden"
    for datei in dateien:
        fremd = set(_importe(datei)) - erlaubt
        assert not fremd, f"{datei.relative_to(WURZEL)} importiert {sorted(fremd)}"


def test_keine_datei_der_mac_app_mit_userdefaults_nennt_das_kennwort():
    """**Die Lehre aus dem früheren Mac-Client**, der das Kennwort in ``UserDefaults`` ablegte
    (22.09.2026) — für die neue Mac-App dieselbe Abwesenheitsprobe wie für die Verbindung des
    iPad (``AnfragenTests.testKeineDateiMitUserDefaultsNenntDasKennwort``), über **alle**
    Ordner der Mac-App."""
    mit = 0
    for datei in _swift_dateien(MAC_QUELLEN):
        code = _mac_code(datei)
        if "UserDefaults" not in code:
            continue
        mit += 1
        for verboten in ("kennwort", "anmeldung", "passw"):
            assert verboten not in code.lower(), (
                f"{datei.relative_to(WURZEL)} benutzt UserDefaults und nennt «{verboten}»")
    assert mit > 0, "keine Datei der Mac-App benutzt UserDefaults — hat sich der Ort geändert?"


def test_die_mac_app_schreibt_das_kennwort_in_kein_protokoll():
    """Nie in ``print``/Protokoll: Keine Zeile, die etwas ausgibt, nennt Kennwort oder
    Anmeldung. (Die ``Anmeldung`` des Kerns verdeckt ihr Kennwort zudem in jeder
    Beschreibung.)"""
    ausgabe = re.compile(r"\b(print|debugPrint|dump|NSLog|os_log)\s*\(|\b(logger|Logger)\b")
    funde = []
    for datei in _swift_dateien(MAC_QUELLEN):
        for nr, zeile in enumerate(_mac_code(datei).splitlines(), 1):
            if ausgabe.search(zeile) and re.search(r"kennwort|anmeldung|passw", zeile, re.I):
                funde.append(f"{datei.relative_to(WURZEL)}:{nr}: {zeile.strip()}")
    assert not funde, "Ausgabe mit Kennwort:\n  " + "\n  ".join(funde)


def test_der_vorgeschlagene_benutzer_ist_der_des_servers(server):
    """Beim Einrichten schlägt die Mac-App einen Benutzer vor — aus der Marke, nicht fest
    (Protokoll §2). Der Vorschlag stimmt nur, solange der Server ihn ebenso nennt."""
    text = _ohne_kommentarzeilen((KERN_QUELLEN / "Heimadresse.swift").read_text(encoding="utf-8"))
    assert re.search(r"static var vorgabeBenutzer: String \{ Marke\.name\.lowercased\(\) \}", text)
    assert server.BENUTZER == _marke()["name"].lower(), (server.BENUTZER, _marke()["name"])


def test_die_mac_schriftfamilien_stehen_in_den_dateien():
    """Die Mac-App fragt nach **Familien**, nicht nach Schnitten (``Start/Macschriften.swift``).
    Eine Familie, die keine Datei trägt, gäbe am Gerät still die Systemschrift."""
    text = _mac_code(MAC_QUELLEN / "Start" / "Macschriften.swift")
    familien = set(re.findall(r'\.(?:text|zahl|titel):\s*"([^"]+)"', text))
    assert len(familien) == 3, familien
    in_dateien = {_sfnt_familie(_sfnt_tabellen(d.read_bytes())) for d in _schriftdateien()}
    assert familien <= in_dateien, (
        f"{sorted(familien - in_dateien)} — in den Dateien: {sorted(in_dateien)}")
    # UND DORT, WO DIE PRUEFSTRECKE SIE HINLEGT: `Contents/Resources/Schriften`.
    assert 'appendingPathComponent("Schriften"' in text


def test_die_pruefstrecke_baut_die_mac_app_aus_diesen_angaben():
    """Der Job ``mac`` in ``ipad.yml``: übersetzt für Apple-Chip, nimmt Programm und Namen aus
    der plist, legt die Schriften unverändert dorthin, wo die App sie sucht, unterschreibt
    behelfsweise, packt mit ``ditto`` und legt das ZIP 14 Tage ab."""
    import yaml

    ablauf = yaml.safe_load(ARBEITSABLAUF.read_text(encoding="utf-8"))
    job = ablauf["jobs"]["mac"]
    assert job["runs-on"] == "macos-15"
    assert job["timeout-minutes"] == 30
    schritte = job["steps"]
    befehle = "\n".join(s.get("run", "") for s in schritte)
    orte = {s.get("working-directory") for s in schritte if "run" in s} - {None}
    assert orte == {"ipad/VisboxMac"}, orte
    assert (WURZEL / "ipad" / "VisboxMac").resolve() == MAC.resolve()

    assert "swift build -c release --arch arm64" in befehle
    assert "Print :CFBundleExecutable' App/Info.plist" in befehle
    assert "Print :CFBundleName' App/Info.plist" in befehle
    assert 'cp App/Info.plist "$BUENDEL/Contents/Info.plist"' in befehle
    # DIE SCHRIFTEN: der ganze Ordner des iPad-Pakets, samt Lizenztexten, an den Ort, den
    # `Macschriften` liest.
    kopie = re.search(r'ditto (\S+) "\$BUENDEL/Contents/Resources/Schriften"', befehle)
    assert kopie, befehle
    assert (MAC / kopie.group(1)).resolve() == SCHRIFTEN.resolve(), kopie.group(1)
    assert re.search(r'codesign --force --deep --sign - "\$BUENDEL"', befehle)
    assert re.search(r'ditto -c -k --keepParent "\$BUENDEL" "\$NAME-mac\.zip"', befehle)

    ablage = [s for s in schritte if str(s.get("uses", "")).startswith("actions/upload-artifact")]
    assert len(ablage) == 1, ablage
    assert ablage[0]["uses"] == "actions/upload-artifact@v4"
    mit = ablage[0]["with"]
    assert mit["name"] == f"{_plist()['CFBundleName']}-mac", mit["name"]
    assert mit["retention-days"] == 14
    assert mit["path"].endswith("-mac.zip"), mit["path"]


# ================================================= 8 · Der Mac als Vermittler (01.10.2026)
#
# Unterwegs gibt sich der Mac dem iPad gegenueber als Server aus und reicht an den Heim-PC
# weiter (Entscheide 42/47, Protokoll §8b). Die Regeln stehen im Kern (`Kern/Leitung.swift`,
# `Kern/Vermittlung.swift`, `Kern/Vermittlerkopplung.swift`) und sind dort mit Proben
# bewacht. Was hier bewacht wird, sind wieder die ABSCHRIFTEN: Der Mac laesst kein Python
# laufen und muss Fassung, Kopplungsregeln, Saetze und die Groesse einer Skizze kennen.

VERMITTLUNG = KERN_QUELLEN / "Vermittlung.swift"
VERMITTLERKOPPLUNG = KERN_QUELLEN / "Vermittlerkopplung.swift"
LEITUNG = KERN_QUELLEN / "Leitung.swift"
INFOZUSATZ = APP / "InfoZusatz.plist"
MAC_VERMITTLUNG = IPAD / "VisboxMac" / "Sources" / "VisboxMac" / "Vermittlung"


def _swift_konstante(datei: Path, name: str) -> str:
    """Der Wert hinter ``static let <name> … = `` bis zum Zeilenende."""
    text = _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))
    treffer = re.search(rf"static let {name}(?:\s*:\s*[\w.]+)?\s*=\s*(.+)", text)
    assert treffer, f"{name} fehlt in {datei.name}"
    return treffer.group(1).strip()


def _swift_text(datei: Path, name: str) -> str:
    """Eine Zeichenkette hinter ``static let <name> =`` — auch über ``+``-Zeilen gefügt."""
    text = _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))
    treffer = re.search(rf'static let {name}\s*=\s*((?:\s*\+?\s*"(?:[^"\\\n]|\\.)*")+)', text)
    assert treffer, f"{name} fehlt in {datei.name}"
    return "".join(re.findall(r'"((?:[^"\\\n]|\\.)*)"', treffer.group(1)))


def test_der_mac_bietet_die_fassung_des_rundrufs_an():
    sys.path.insert(0, str(FLAECHE))
    try:
        import rundruf
    finally:
        sys.path.remove(str(FLAECHE))
    assert _swift_konstante(VERMITTLUNG, "fassung") == f'"{rundruf.FASSUNG}"'


def test_die_kopplung_am_mac_hat_die_regeln_der_homestation(server):
    """Frist, Versuche, Stellen und der Satz bei Erfolg — eine Abschrift von
    ``aiimaging.kopplung`` und ``server.py``. Läuft eine Seite weg, gälten am Mac andere
    Regeln als zuhause, und niemand sähe es."""
    from aiimaging import kopplung

    assert float(_swift_konstante(VERMITTLERKOPPLUNG, "frist")) == kopplung.FRIST_S
    assert int(_swift_konstante(VERMITTLERKOPPLUNG, "versuche")) == kopplung.VERSUCHE
    assert int(_swift_konstante(VERMITTLERKOPPLUNG, "stellen")) == kopplung.PIN_STELLEN
    assert int(_swift_konstante(VERMITTLERKOPPLUNG, "laenge")) == server.KENNWORTLAENGE
    assert _swift_text(VERMITTLERKOPPLUNG, "grundFalsch") == kopplung.GRUND_FALSCH
    assert _swift_text(VERMITTLERKOPPLUNG, "grundVerbraucht") == kopplung.GRUND_VERBRAUCHT
    assert _swift_text(VERMITTLUNG, "satzVerbunden") == server.SATZ_VERBUNDEN
    # Der Benutzername kommt aus der Marke (klein) — derselbe wie beim Server.
    assert _marke()["name"].lower() == server.BENUTZER


def test_die_tuer_des_mac_spricht_den_satz_des_servers(server):
    """Die 401 des Mac hat denselben Satz wie die des Servers, mit dem Namen aus der Marke.
    Gelesen an der Tür des Servers selbst, nicht aus seinem Quelltext."""
    a = _Anfrage(server, befehl="GET", weg="/api/fortschritt", angemeldet=False).stelle()
    assert a.codes == [401]
    satz = json.loads(a.text)["fehler"].replace(server.NAME, r"\(Marke.name)")
    text = _ohne_kommentarzeilen(VERMITTLUNG.read_text(encoding="utf-8"))
    block = re.search(r"public static var tuer: Leitungsantwort \{(.*?)\n    \}", text, re.S)
    assert block, "die Tür des Mac fehlt in Vermittlung.swift"
    assert satz in "".join(re.findall(r'"((?:[^"\\\n]|\\.)*)"', block.group(1)))


def test_die_grenze_des_mac_fasst_die_groesste_skizze_des_servers(server):
    """Der Mac weist einen Rumpf über ``rumpfGrenze`` ab, bevor er ihn liest. Die grösste
    Anfrage der App ist eine Skizze bis ``SKIZZE_GROESSENRIEGEL`` — als Base64 im JSON um
    ein Drittel grösser. Wächst der Riegel des Servers, muss die Grenze des Mac mitwachsen."""
    ausdruck = _swift_konstante(LEITUNG, "rumpfGrenze")
    assert re.fullmatch(r"[\d\s*]+", ausdruck), ausdruck
    grenze = eval(ausdruck)  # nur Ziffern und «*», geprüft in der Zeile darüber
    base64 = (server.SKIZZE_GROESSENRIEGEL + 2) // 3 * 4
    assert grenze >= base64 + 64 * 1024, (grenze, base64)


def test_die_app_bittet_um_das_lokale_netzwerk_mit_einem_satz():
    """Die Erlaubnis «Lokales Netzwerk» steht **einmal**, im Manifest (`.localNetwork`), mit
    einem Satz, warum — und er nennt seit dem 01.10.2026 auch den Mac, weil die App ihn
    unterwegs im WLAN sucht. ``InfoZusatz.plist`` wiederholt sie nicht: Zwei Quellen für
    denselben Schlüssel hiessen, dass eine die andere still überschreibt."""
    manifest = _ohne_kommentarzeilen(APP_MANIFEST.read_text(encoding="utf-8"))
    saetze = re.findall(r'\.localNetwork\(\s*purposeString:\s*"([^"]+)"', manifest)
    assert len(saetze) == 1, saetze
    satz = saetze[0]
    assert satz.endswith(".") and ". " not in satz, f"ein Satz, nicht mehrere: {satz!r}"
    assert "Mac" in satz and "HomeStation" in satz, satz
    zusatz = INFOZUSATZ.read_text(encoding="utf-8")
    for schluessel in ("NSLocalNetworkUsageDescription", "NSBonjourServices"):
        assert schluessel not in zusatz, f"{schluessel} steht doppelt (Manifest und InfoZusatz)"


def test_der_mac_teil_bleibt_duenn_und_bei_der_plattform():
    """Regel 1 und 4: Der Mac-Teil der Vermittlung benutzt nur Apple-Plattform und den Kern
    — keine neue Abhängigkeit, keine Oberfläche (die Zeile «iPad» zeichnet die Mac-App)."""
    dateien = sorted(MAC_VERMITTLUNG.glob("*.swift"))
    assert dateien, "keine Dateien unter VisboxMac/…/Vermittlung"
    for datei in dateien:
        assert set(_importe(datei)) <= {"Foundation", "Network", "Security", "VisboxKern"}, (
            datei.name, _importe(datei))


# ======================================================= 9 · Der Assistent am Mac (01.10.2026)
#
# Die Leiste des Assistenten prueft eine Nachricht, bevor sie hinausgeht, und kuerzt lange
# Beitraege im Verlauf (Durchsicht 01.10.2026, M2) — gegen die Grenzen, die der Server
# setzt. Sie sind ABSCHRIFTEN: Wird drueben eine Grenze enger, wiese der Server ab, was der
# Mac fuer zulaessig haelt, und jede weitere Frage scheiterte am selben Verlaufsbeitrag.

ASSISTENT_KERN = KERN_QUELLEN / "Assistent.swift"


def test_die_grenzen_des_assistenten_am_mac_sind_die_des_servers():
    from aiimaging import assistent

    assert int(_swift_konstante(ASSISTENT_KERN, "nachrichtHoechstens")) == (
        assistent.NACHRICHT_HOECHSTENS)
    assert int(_swift_konstante(ASSISTENT_KERN, "verlaufHoechstens")) == (
        assistent.VERLAUF_HOECHSTENS)
    assert int(_swift_konstante(ASSISTENT_KERN, "verlaufTextHoechstens")) == (
        assistent.VERLAUF_TEXT_HOECHSTENS)
    # GEZAEHLT WIE PYTHON: `len(str)` zaehlt Unicode-Zeichen, Swift `count` zusammengesetzte.
    text = _ohne_kommentarzeilen(ASSISTENT_KERN.read_text(encoding="utf-8"))
    assert re.search(r"func laenge\(_ text: String\) -> Int \{ text\.unicodeScalars\.count \}",
                     text), "Assistentengespraech.laenge zählt nicht mehr wie Python"


# ------------------------------------- 8b · Sicherheitsdurchsicht des Vermittlers (01.10.2026)
#
# Der Mac laeuft unterwegs in fremden WLANs. Die Durchsicht vom 01.10.2026 fand dort, was
# zwei Leser verschieden lesen (`;` im Pfad), was ein Fremder billig belegen kann, und
# Abschriften, die niemand bewachte. Bewacht wird hier, was der Kern unter Linux nicht
# sehen kann: die Gegenseite in Python und der Mac-Teil als Text.

SENDER = APP / "Verbindung" / "Sender.swift"
HEIMSTRECKE = MAC_VERMITTLUNG / "Heimstrecke.swift"
VERMITTLUNGSANSCHLUSS = MAC_QUELLEN / "Start" / "Vermittlungsanschluss.swift"


def _swift_wegliste(datei: Path, name: str) -> list[str]:
    """Die Namen in ``static let <name>: [Weg] = [Wege.a, Wege.b, …]``."""
    text = _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))
    treffer = re.search(rf"static let {name}:\s*\[Weg\]\s*=\s*\[(.*?)\]", text, re.S)
    assert treffer, f"{name} fehlt in {datei.name}"
    return re.findall(r"Wege\.(\w+)", treffer.group(1))


def test_die_positivliste_des_mac_ist_eine_teilmenge_der_serverwege(server):
    """**Nur, was die App ruft, geht über den Mac** — und es sind Wege, die der Server
    wirklich bedient, mit derselben Art. ``verbinden`` und ``koppeln`` stehen nie darin:
    Ginge `POST /api/verbinden` weiter, gäbe der Heim-PC bei offener Kopplung **sein**
    Kennwort heraus (Befund `;` im Pfad, 01.10.2026)."""
    wege = _swift_wege()
    liste = _swift_wegliste(VERMITTLUNG, "weiterreichbar")
    assert liste, "die Positivliste ist leer"
    for name in liste:
        assert name in wege, f"Wege.{name} gibt es nicht"
        methode, pfad, ohne_anmeldung = wege[name]
        tafel = server.WEGTAFEL if methode == "POST" else server.WEGTAFEL_LESEN
        assert pfad in tafel, f"{methode} {pfad} bedient der Server nicht"
        assert not ohne_anmeldung, f"{pfad}: ein Weg ohne Anmeldung geht nie weiter"
        assert pfad not in (server.WEG_VERBINDEN, server.WEG_KOPPELN), pfad
        assert ";" not in pfad and "%" not in pfad and "//" not in pfad, pfad
    assert "verbinden" not in liste and "koppeln" not in liste


def test_die_koppelsaetze_des_mac_sind_die_der_homestation():
    """Die Sätze der Kopplung am Mac sind die von ``aiimaging.kopplung`` — nur steht «am Mac»,
    wo dort «an der HomeStation» steht: Der Satz sagt, **wo** es eine neue Zahl gibt."""
    from aiimaging import kopplung

    def am_mac(satz: str) -> str:
        return satz.replace("An der HomeStation", "Am Mac").replace("an der HomeStation",
                                                                    "am Mac")

    assert _swift_text(VERMITTLERKOPPLUNG, "grundAbgelaufen") == am_mac(kopplung.GRUND_ABGELAUFEN)
    assert _swift_text(VERMITTLERKOPPLUNG, "grundAufgebraucht") == am_mac(
        kopplung.GRUND_AUFGEBRAUCHT)
    assert _swift_text(VERMITTLERKOPPLUNG, "satzFuerDasGeraet") == am_mac(
        kopplung.SATZ_FUER_DAS_GERAET)
    # UND ES IST WIRKLICH ETWAS ERSETZT WORDEN — sonst prüfte die Zeile darüber nichts.
    assert "HomeStation" in kopplung.SATZ_FUER_DAS_GERAET


def test_der_mac_gibt_auf_bevor_das_ipad_aufgibt():
    """``Heimstrecke.wartezeit`` < Frist des ``Sender`` der App: So sagt der Mac «nicht
    erreicht», bevor das iPad selbst aufgibt und nur «keine Antwort» weiss (Protokoll §8b)."""
    mac = float(_swift_konstante(HEIMSTRECKE, "wartezeit"))
    text = _ohne_kommentarzeilen(SENDER.read_text(encoding="utf-8"))
    treffer = re.findall(r"timeoutIntervalForRequest\s*=\s*([\d.]+)", text)
    assert len(treffer) == 1, treffer
    assert mac < float(treffer[0]), (mac, treffer[0])


def test_die_uhr_der_kopplung_zaehlt_den_ruhezustand():
    """``systemUptime`` steht im Ruhezustand still — eine Zahl gälte nach zugeklapptem Deckel
    weiter. Der Kern liest keine Uhr (sie wird hineingereicht), der Mac-Teil reicht eine, die
    den Schlaf mitzählt (``ContinuousClock``)."""
    for datei in (VERMITTLUNG, VERMITTLERKOPPLUNG, LEITUNG, *MAC_VERMITTLUNG.glob("*.swift")):
        code = _ohne_kommentarzeilen(datei.read_text(encoding="utf-8"))
        assert "systemUptime" not in code, datei.name
        assert "SuspendingClock" not in code, datei.name
    uhr = _ohne_kommentarzeilen((MAC_VERMITTLUNG / "Vermittlungsuhr.swift")
                                .read_text(encoding="utf-8"))
    assert "ContinuousClock" in uhr
    dienst = _ohne_kommentarzeilen((MAC_VERMITTLUNG / "Vermittlungsdienst.swift")
                                   .read_text(encoding="utf-8"))
    assert "jetzt: Vermittlungsuhr.jetzt" in dienst


def test_die_leitung_nach_hause_nimmt_keinen_proxy_des_systems():
    """Ein fremdes WLAN kann per automatischer Konfiguration einen Proxy setzen. Die Leitung
    zum Heim-PC geht direkt durch Tailscale: ``connectionProxyDictionary = [:]``."""
    code = _ohne_kommentarzeilen(HEIMSTRECKE.read_text(encoding="utf-8"))
    assert re.search(r"connectionProxyDictionary\s*=\s*\[:\]", code)


def test_der_mac_bietet_sich_nur_an_wenn_eingeschaltet():
    """**Vorgabe aus** (Owner-Entscheid 01.10.2026): ``Vermittlungsanschluss`` startet den
    Dienst nur hinter dem Merker, und der Merker ist ``false``, solange niemand ihn setzt
    (``UserDefaults.bool`` ohne Eintrag)."""
    code = _ohne_kommentarzeilen(VERMITTLUNGSANSCHLUSS.read_text(encoding="utf-8"))
    aufrufe = [z.strip() for z in code.splitlines() if ".starte()" in z]
    assert aufrufe, "der Dienst wird nirgends gestartet"
    for zeile in aufrufe:
        assert zeile.startswith(("if angeboten", "if an ")), zeile
    assert "angeboten = Vermittlergedaechtnis.angeboten" in code
    gedaechtnis = _ohne_kommentarzeilen((MAC_VERMITTLUNG / "Vermittlergedaechtnis.swift")
                                        .read_text(encoding="utf-8"))
    assert re.search(r"static var angeboten: Bool \{\s*get \{ UserDefaults\.standard\.bool\(",
                     gedaechtnis)
