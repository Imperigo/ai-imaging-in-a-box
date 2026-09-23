"""Der Rundruf — die HomeStation sagt im Heimnetz, wo sie ist (Entscheid 27).

**Was er tut.** Ein iPad fragt über die Bonjour-Suche seines Systems: «Wer bietet
``_visbox._tcp`` an?» Diese Datei beantwortet genau diese Frage, und nur sie: mit dem Namen
des Dienstes (PTR), dem Anschluss und dem Rechnernamen (SRV), der Protokollfassung (TXT) und
der Adresse im Heimnetz (A). Danach weiss das iPad, wohin es sich verbindet, ohne dass
jemand eine Adresse abtippt.

**Womit.** Nur mit der Standardbibliothek (``socket``, ``struct``) — kein Zeroconf-Paket
(Regel 1: jede Abhängigkeit will installiert, gepflegt und lizenzgeprüft sein). Das
Verfahren heisst mDNS/DNS-SD (RFC 6762/6763): gewöhnliche DNS-Pakete, aber an die
Rundruf-Adresse ``224.0.0.251``, Anschluss 5353.

**Was er ausdrücklich NICHT tut, und es steht hier, damit es niemand für getan hält:**

* **Er nimmt einem vorhandenen Dienst den Anschluss nicht weg — beim Binden.**
  Er setzt ``SO_REUSEADDR`` und, wo es ihn gibt, ``SO_REUSEPORT``; geprüft ist
  (``tests/test_rundruf.py``), dass er sich an **denselben Anschluss binden** lässt, an
  dem schon ein anderer Socket mit einer der beiden Optionen hört — **nachgestellt auf
  einem freien Anschluss an 127.0.0.1, nicht an 5353** und ohne Rundruf-Gruppe (Durchsicht
  der Welle 2, 22.09.2026: Hier stand «an 5353», geprüft war das nie). Ob es an 5353
  neben einem echten avahi genauso geht, ist **am Gerät unbestätigt**. Er beantwortet
  nur Fragen nach seinem eigenen Dienst; alles andere bleibt unbeantwortet — dafür ist
  der andere da.
  **Und er nimmt ihm direkte Pakete weg** (Befund der Durchsicht D-SERVER, 22.09.2026,
  nachgefahren und bewacht in ``tests/test_durchsicht_kern_server.py``, Linux, über
  127.0.0.1): Setzt der andere Dienst nur ``SO_REUSEADDR``, landet **jedes** direkt an
  den Anschluss geschickte Paket (Unicast) beim zuletzt gebundenen Socket — also beim
  Rundruf, wenn er nach dem anderen startet —, und der andere bekommt keines. Setzt der
  andere ``SO_REUSEPORT``, verteilt das System die direkten Pakete **nach Absender** auf
  beide. Der Rundruf beantwortet davon nur Fragen nach seinem Dienst und verwirft den
  Rest. **Nicht nachgestellt:** ob Pakete an die Rundruf-Gruppe (224.0.0.251) beide
  erreichen, und wie sehr ein avahi auf direkte Pakete angewiesen ist. Offener Posten.
* **Er prüft seinen Namen nicht vorab** (das «Probing» aus RFC 6762 §8). Zwei HomeStations
  im selben Netz melden sich darum unter verschiedenen Namen nur, weil der Rechnername im
  Namen steht. Ein Namensstreit wird nicht erkannt.
* **Die Adresse gilt ab dem Start.** Wechselt der Rechner danach das Netz, nennt der
  Rundruf die alte Adresse, bis er neu gestartet wird.
* **Ob ein echtes iPad ihn findet, ist am Gerät unbestätigt** (22.09.2026). Geprüft ist
  hier, dass eine selbstgebaute Anfrage über einen lokalen UDP-Socket die richtige Antwort
  bekommt — nicht, dass iOS sie genauso stellt.

Gestartet wird er von ``server.py`` und **nur mit** ``--im-heimnetz``: Hört die Fläche nur
auf ``127.0.0.1``, kann sie kein anderes Gerät erreichen, und ein Rundruf lüde zu einer
Verbindung ein, die nicht zustande kommt.
"""
from __future__ import annotations

import socket
import struct
import threading

# ======================================================================================
# Was angekündigt wird
# ======================================================================================

#: Der Name, den ein Mensch in der Liste der gefundenen Geräte sieht (vor dem Rechnernamen).
#:
#: **Er muss mit ``Marke.name`` in ``ipad/Visbox.swiftpm/Kern/Marke.swift`` übereinstimmen**
#: — nach der Abgabe heisst die App anders (Entscheid 34), und ein Rundruf unter dem alten
#: Namen wäre die zwanzigste Stelle, die niemand umbenennt. ``tests/test_rundruf.py`` hält
#: beide gegeneinander.
NAME = "Visbox"

#: Die Dienstart in Bonjour-Form. **Muss mit ``Marke.dienst`` übereinstimmen** — iOS sucht
#: nur, was die App im Manifest nennt, und das Manifest nennt, was in der Marke steht. Ein
#: Buchstabe Unterschied, und das iPad sucht einen Dienst, den niemand anbietet (Wächter:
#: ``tests/test_rundruf.py``).
DIENST = "_visbox._tcp"

#: Die Domäne des Heimnetzes. mDNS kennt nur diese eine.
DOMAENE = "local"

#: Welche Fassung des Protokolls (``docs/VISBOX_PROTOKOLL.md``) der Server spricht — im
#: TXT-Eintrag als ``fassung=1``. Eine App, die eine andere erwartet, kann das vor dem
#: ersten Weg sehen statt an einem Feld, das fehlt.
FASSUNG = 1

#: Die Rundruf-Adresse und der Anschluss von mDNS (RFC 6762 §3).
GRUPPE = "224.0.0.251"
MDNS_ANSCHLUSS = 5353

#: Wie lange ein Empfänger eine Antwort aufheben darf. Die Vorgaben aus RFC 6762 §10:
#: Einträge über den Rechner (SRV, A) kurz, der Rest lang.
TTL_RECHNER = 120
TTL_DIENST = 4500
#: Eine Antwort an einen einfachen Fragesteller (nicht über 5353) darf höchstens 10 s
#: gelten (RFC 6762 §6.7) — er hört keine späteren Berichtigungen.
TTL_EINFACH = 10

# Die Satzarten, die hier vorkommen (RFC 1035 / 2782).
TYP_A = 1
TYP_PTR = 12
TYP_TXT = 16
TYP_SRV = 33
TYP_ALLE = 255
KLASSE_IN = 1
#: Das oberste Bit der Klasse: in einer Frage «bitte direkt an mich antworten» (QU), in
#: einer Antwort «ersetzt, was du über diesen Namen weisst» (cache-flush).
OBERSTES_BIT = 0x8000
#: Kopf einer Antwort: «ist eine Antwort» und «weiss es aus erster Hand».
FLAGGEN_ANTWORT = 0x8400

#: Der Name, unter dem DNS-SD fragt, welche Dienstarten es überhaupt gibt (RFC 6763 §9).
DIENSTARTEN = "_services._dns-sd._udp.local"

#: Eine mDNS-Nachricht ist höchstens so gross (RFC 6762 §17). Grösseres wird nicht gelesen.
PAKET_HOECHSTENS = 9000


class RundrufError(Exception):
    """Der Rundruf lässt sich so nicht starten — mit einem Satz für einen Menschen."""


class PaketError(ValueError):
    """Ein Paket, das sich nicht als DNS-Nachricht lesen lässt."""


# ======================================================================================
# Pakete bauen und lesen — ohne Netz, damit eine Probe sie direkt rufen kann
# ======================================================================================

def _name_bytes(name: str) -> bytes:
    """Ein Name in DNS-Schreibweise: je Teil ein Längenbyte und der Teil, am Ende eine 0.

    **Ohne Kompression.** Sie ist erlaubt, nicht verlangt; eine Antwort ohne sie ist ein
    paar Byte länger und dafür von jedem Leser zu lesen.
    """
    teile = [t for t in name.rstrip(".").split(".") if t] if name else []
    roh = b""
    for teil in teile:
        b = teil.encode("utf-8")
        if len(b) > 63:
            raise PaketError(f"Ein Namensteil ist höchstens 63 Byte lang — {teil!r} ist länger.")
        roh += bytes([len(b)]) + b
    return roh + b"\x00"


def _lies_name(daten: bytes, stelle: int) -> tuple[str, int]:
    """Einen Namen lesen, **auch einen komprimierten** — ``(name, stelle_danach)``.

    Ein Fragesteller darf Verweise (``0xC0``) benutzen, und iOS tut es. Die Zahl der
    Sprünge ist begrenzt: Ein Verweis, der auf sich selbst zeigt, liesse sonst diesen Faden
    für immer kreisen — und der Rundruf gehört zu einer Fläche, die weiter antworten soll.
    """
    teile, danach, spruenge = [], None, 0
    while True:
        if stelle >= len(daten):
            raise PaketError("Der Name läuft über das Ende des Pakets hinaus.")
        laenge = daten[stelle]
        if laenge & 0xC0 == 0xC0:
            if stelle + 1 >= len(daten):
                raise PaketError("Ein Verweis im Namen ist abgeschnitten.")
            if danach is None:
                danach = stelle + 2
            spruenge += 1
            if spruenge > 32:
                raise PaketError("Zu viele Verweise im Namen — vermutlich ein Kreis.")
            stelle = ((laenge & 0x3F) << 8) | daten[stelle + 1]
            continue
        if laenge & 0xC0:
            raise PaketError("Unbekannte Form eines Namensteils.")
        stelle += 1
        if laenge == 0:
            break
        if stelle + laenge > len(daten):
            raise PaketError("Ein Namensteil läuft über das Ende des Pakets hinaus.")
        teile.append(daten[stelle:stelle + laenge].decode("utf-8", "replace"))
        stelle += laenge
    return ".".join(teile), (danach if danach is not None else stelle)


def baue_anfrage(name: str, typ: int = TYP_PTR, *, kennung: int = 0,
                 direkt: bool = False) -> bytes:
    """Eine Frage, wie ein Bonjour-Sucher sie stellt — **für Proben und zum Nachsehen.**

    Args:
        name: Wonach gefragt wird, z. B. ``"_visbox._tcp.local"``.
        typ: Die Satzart (:data:`TYP_PTR`, :data:`TYP_SRV` …).
        kennung: Die Nummer der Anfrage. mDNS über 5353 benutzt 0; ein einfacher
            Fragesteller seine eigene, und die Antwort muss sie wiederholen.
        direkt: Das QU-Bit — «bitte direkt an mich antworten, nicht an alle».
    """
    kopf = struct.pack("!HHHHHH", kennung & 0xFFFF, 0, 1, 0, 0, 0)
    klasse = KLASSE_IN | (OBERSTES_BIT if direkt else 0)
    return kopf + _name_bytes(name) + struct.pack("!HH", typ, klasse)


def _lies_satz(daten: bytes, stelle: int) -> tuple[dict, int]:
    name, stelle = _lies_name(daten, stelle)
    if stelle + 10 > len(daten):
        raise PaketError("Ein Eintrag ist abgeschnitten.")
    typ, klasse, ttl, laenge = struct.unpack("!HHIH", daten[stelle:stelle + 10])
    stelle += 10
    if stelle + laenge > len(daten):
        raise PaketError("Der Inhalt eines Eintrags läuft über das Paket hinaus.")
    roh = daten[stelle:stelle + laenge]
    satz = {"name": name, "typ": typ, "klasse": klasse & 0x7FFF,
            "cache_flush": bool(klasse & OBERSTES_BIT), "ttl": ttl}
    if typ == TYP_PTR:
        satz["ziel"] = _lies_name(daten, stelle)[0]
    elif typ == TYP_SRV:
        if laenge < 7:
            raise PaketError("Ein SRV-Eintrag ist zu kurz.")
        satz["prioritaet"], satz["gewicht"], satz["anschluss"] = struct.unpack(
            "!HHH", roh[:6])
        satz["ziel"] = _lies_name(daten, stelle + 6)[0]
    elif typ == TYP_TXT:
        texte, i = [], 0
        while i < len(roh):
            n = roh[i]
            texte.append(roh[i + 1:i + 1 + n].decode("utf-8", "replace"))
            i += 1 + n
        satz["texte"] = texte
    elif typ == TYP_A:
        if laenge != 4:
            raise PaketError("Ein A-Eintrag hat genau vier Byte.")
        satz["adresse"] = socket.inet_ntoa(roh)
    return satz, stelle + laenge


def lies_paket(daten: bytes) -> dict:
    """Eine DNS-Nachricht lesen — Frage oder Antwort.

    Returns:
        ``{kennung, flaggen, antwort, fragen, antworten, zusatz}``; ``fragen`` je
        ``{name, typ, klasse, direkt}``, die Einträge je ``{name, typ, klasse,
        cache_flush, ttl}`` und ihr Inhalt (``ziel``, ``anschluss``, ``texte``,
        ``adresse``).

    Raises:
        PaketError: Das Paket lässt sich nicht lesen.
    """
    if len(daten) < 12:
        raise PaketError("Kürzer als der Kopf einer DNS-Nachricht.")
    kennung, flaggen, nq, na, nn, nz = struct.unpack("!HHHHHH", daten[:12])
    stelle = 12
    fragen = []
    for _ in range(nq):
        name, stelle = _lies_name(daten, stelle)
        if stelle + 4 > len(daten):
            raise PaketError("Eine Frage ist abgeschnitten.")
        typ, klasse = struct.unpack("!HH", daten[stelle:stelle + 4])
        stelle += 4
        fragen.append({"name": name, "typ": typ, "klasse": klasse & 0x7FFF,
                       "direkt": bool(klasse & OBERSTES_BIT)})
    abschnitte = []
    for zahl in (na, nn, nz):
        saetze = []
        for _ in range(zahl):
            satz, stelle = _lies_satz(daten, stelle)
            saetze.append(satz)
        abschnitte.append(saetze)
    return {"kennung": kennung, "flaggen": flaggen, "antwort": bool(flaggen & 0x8000),
            "fragen": fragen, "antworten": abschnitte[0], "zusatz": abschnitte[2]}


def _satz(name: str, typ: int, ttl: int, inhalt: bytes, *, eindeutig: bool) -> bytes:
    klasse = KLASSE_IN | (OBERSTES_BIT if eindeutig else 0)
    return _name_bytes(name) + struct.pack("!HHIH", typ, klasse, ttl, len(inhalt)) + inhalt


def _txt_inhalt(texte) -> bytes:
    roh = b""
    for t in texte:
        b = t.encode("utf-8")[:255]
        roh += bytes([len(b)]) + b
    return roh or b"\x00"


def _saeuberer_teil(text: str) -> str:
    """Ein Rechnername, der als DNS-Teil taugt: Kleinbuchstaben, Ziffern, Bindestrich."""
    teil = "".join(z if z.isascii() and z.isalnum() else "-" for z in text.lower())
    teil = "-".join(t for t in teil.split("-") if t)[:40]
    return teil or "homestation"


class Dienstangabe:
    """Was angekündigt wird — ein Dienst, ein Rechner, eine Adresse, ein Anschluss.

    Args:
        anschluss: Der Anschluss, auf dem die Fläche **wirklich** hört (nach dem Binden,
            nicht der verlangte — bei ``--anschluss 0`` wählt ihn das Betriebssystem).
        adresse: Die Adresse im Heimnetz (IPv4, als Text). ``None`` wird abgewiesen: Ohne
            Adresse gäbe es nur einen Namen anzukündigen, unter dem niemand ankommt — die
            dritte Antwort ist hier «nicht ankündigen», nie eine geratene Adresse.
        rechnername: Woraus der Rechnername im Heimnetz entsteht. Vorgabe: der Name dieses
            Rechners, auf Buchstaben, Ziffern und Bindestriche gebracht.
    """

    def __init__(self, *, anschluss: int, adresse, rechnername: str | None = None):
        if adresse is None:
            raise RundrufError(
                "Adresse im Heimnetz nicht ermittelt — ohne sie gibt es nichts anzukündigen. "
                "Die Adresse am Rechner nachsehen und am iPad eintippen.")
        try:
            self.adresse_roh = socket.inet_aton(str(adresse))
        except OSError:
            raise RundrufError(f"{adresse!r} ist keine IPv4-Adresse.") from None
        if isinstance(anschluss, bool) or not isinstance(anschluss, int) \
                or not 0 < anschluss < 65536:
            raise RundrufError(f"Der Anschluss ist eine Zahl von 1 bis 65535 — war {anschluss!r}.")
        self.adresse = str(adresse)
        self.anschluss = anschluss
        kurz = _saeuberer_teil(rechnername if rechnername is not None else socket.gethostname())
        self.dienst = f"{DIENST}.{DOMAENE}"
        # DER RECHNERNAME STEHT IM NAMEN, damit zwei HomeStations im selben Netz nicht
        # denselben tragen. Er ist nicht der Name, unter dem ein vorhandener avahi-Dienst
        # den Rechner fuehrt: Der gehoert ihm, und ein zweiter Antworter mit womoeglich
        # anderer Adresse darunter waere ein Streit um einen fremden Namen.
        self.instanz = f"{NAME} auf {kurz}.{self.dienst}"
        self.rechner = f"{NAME.lower()}-{kurz}.{DOMAENE}"
        self.texte = (f"fassung={FASSUNG}",)

    # Die vier Eintraege — `einfach` heisst: Antwort an einen einfachen Fragesteller,
    # dann ohne cache-flush und mit kurzer Gueltigkeit (RFC 6762 §6.7).
    def ptr(self, einfach=False) -> bytes:
        return _satz(self.dienst, TYP_PTR, TTL_EINFACH if einfach else TTL_DIENST,
                     _name_bytes(self.instanz), eindeutig=False)

    def srv(self, einfach=False) -> bytes:
        return _satz(self.instanz, TYP_SRV, TTL_EINFACH if einfach else TTL_RECHNER,
                     struct.pack("!HHH", 0, 0, self.anschluss) + _name_bytes(self.rechner),
                     eindeutig=not einfach)

    def txt(self, einfach=False) -> bytes:
        return _satz(self.instanz, TYP_TXT, TTL_EINFACH if einfach else TTL_DIENST,
                     _txt_inhalt(self.texte), eindeutig=not einfach)

    def a(self, einfach=False) -> bytes:
        return _satz(self.rechner, TYP_A, TTL_EINFACH if einfach else TTL_RECHNER,
                     self.adresse_roh, eindeutig=not einfach)

    def arten(self, einfach=False) -> bytes:
        return _satz(DIENSTARTEN, TYP_PTR, TTL_EINFACH if einfach else TTL_DIENST,
                     _name_bytes(self.dienst), eindeutig=False)


def antworte(paket: bytes, angabe: Dienstangabe, *,
             absender_anschluss: int = MDNS_ANSCHLUSS) -> tuple[bytes, bool] | None:
    """Die Antwort auf ein empfangenes Paket — oder ``None``, wenn es uns nicht betrifft.

    **Nur Fragen nach dem eigenen Dienst werden beantwortet.** Auf demselben Anschluss
    hört womöglich ein anderer Bonjour-Dienst; was ihm gehört, beantwortet er. *Wer auf
    fremde Fragen antwortet, verdrängt ihn, ohne ihn abzuschalten.*

    Args:
        paket: Was ankam.
        angabe: Was angekündigt wird.
        absender_anschluss: Von welchem Anschluss die Frage kam. Nicht 5353 heisst: ein
            **einfacher Fragesteller** (RFC 6762 §6.7) — er bekommt die Antwort direkt,
            mit seiner Kennung und seiner Frage darin.

    Returns:
        ``(antwort, direkt)``: ``direkt`` heisst an den Absender, sonst an die Gruppe.
        ``None`` bei einer Antwort (nicht Frage), einem unlesbaren Paket oder einer Frage,
        die uns nicht betrifft.
    """
    try:
        gelesen = lies_paket(paket)
    except PaketError:
        return None
    if gelesen["antwort"] or (gelesen["flaggen"] >> 11) & 0xF:
        # EINE ANTWORT (auch unsere eigene Ankuendigung, die zurueckkommt) oder keine
        # gewoehnliche Frage: nichts zu tun.
        return None

    einfach = absender_anschluss != MDNS_ANSCHLUSS
    antworten, zusatz, beantwortet = [], [], []

    def dazu(liste, eintrag):
        if eintrag not in antworten and eintrag not in liste:
            liste.append(eintrag)

    for frage in gelesen["fragen"]:
        if frage["klasse"] not in (KLASSE_IN, TYP_ALLE):
            continue
        name, typ = frage["name"].lower().rstrip("."), frage["typ"]
        treffer = False
        if name == DIENSTARTEN and typ in (TYP_PTR, TYP_ALLE):
            dazu(antworten, angabe.arten(einfach))
            treffer = True
        if name == angabe.dienst.lower() and typ in (TYP_PTR, TYP_ALLE):
            dazu(antworten, angabe.ptr(einfach))
            for extra in (angabe.srv(einfach), angabe.txt(einfach), angabe.a(einfach)):
                dazu(zusatz, extra)
            treffer = True
        if name == angabe.instanz.lower():
            if typ in (TYP_SRV, TYP_ALLE):
                dazu(antworten, angabe.srv(einfach))
                dazu(zusatz, angabe.a(einfach))
                treffer = True
            if typ in (TYP_TXT, TYP_ALLE):
                dazu(antworten, angabe.txt(einfach))
                treffer = True
        if name == angabe.rechner.lower() and typ in (TYP_A, TYP_ALLE):
            dazu(antworten, angabe.a(einfach))
            treffer = True
        if treffer:
            beantwortet.append(frage)

    if not antworten:
        return None
    zusatz = [z for z in zusatz if z not in antworten]

    fragen_roh = b""
    if einfach:
        # EIN EINFACHER FRAGESTELLER ERKENNT SEINE ANTWORT an Kennung und Frage; ohne
        # beides verwirft er sie (RFC 6762 §6.7).
        for f in beantwortet:
            fragen_roh += _name_bytes(f["name"]) + struct.pack("!HH", f["typ"], KLASSE_IN)
    kopf = struct.pack("!HHHHHH", gelesen["kennung"] if einfach else 0, FLAGGEN_ANTWORT,
                       len(beantwortet) if einfach else 0, len(antworten), 0, len(zusatz))
    direkt = einfach or any(f["direkt"] for f in gelesen["fragen"])
    return kopf + fragen_roh + b"".join(antworten) + b"".join(zusatz), direkt


def ankuendigung(angabe: Dienstangabe, *, abschied: bool = False) -> bytes:
    """Eine Antwort ohne Frage — beim Start (RFC 6762 §8.3) und, mit ``abschied``, beim
    Beenden mit Gültigkeit 0 (§10.1): Dann vergessen die Geräte den Eintrag sofort, statt
    eine Stunde lang auf eine HomeStation zu zeigen, die nicht mehr antwortet."""
    saetze = [angabe.ptr(), angabe.srv(), angabe.txt(), angabe.a()]
    if abschied:
        # DIE GUELTIGKEIT STEHT AN FESTER STELLE: direkt hinter Name, Typ und Klasse.
        neu = []
        for s in saetze:
            _, nach_name = _lies_name(s, 0)
            neu.append(s[:nach_name + 4] + b"\x00\x00\x00\x00" + s[nach_name + 8:])
        saetze = neu
    kopf = struct.pack("!HHHHHH", 0, FLAGGEN_ANTWORT, 0, len(saetze), 0, 0)
    return kopf + b"".join(saetze)


# ======================================================================================
# Der Antworter im Hintergrund
# ======================================================================================

class Rundruf:
    """Der Antworter als Hintergrundfaden — **sauber beendbar.**

    Args:
        angabe: Was angekündigt wird.
        bindung: Wo gehört wird. Vorgabe: alle Adressen, Anschluss 5353.
        gruppe: ``True`` tritt der Rundruf-Gruppe bei und kündigt an. ``False`` hört nur
            auf ``bindung`` — **für Proben über einen lokalen UDP-Socket**, ohne echtes
            Multicast.
    """

    #: Wie oft der Faden nachsieht, ob er aufhören soll. Kurz genug, dass ein Strg-C nicht
    #: merklich wartet; lang genug, dass er zwischendurch nicht rechnet.
    TAKT_S = 0.25

    def __init__(self, angabe: Dienstangabe, *, bindung=("", MDNS_ANSCHLUSS),
                 gruppe: bool = True):
        self.angabe = angabe
        self.bindung = bindung
        self.gruppe = gruppe
        self._sock = None
        self._faden = None
        self._halt = threading.Event()
        #: Wie viele Antworten hinausgingen — damit eine Probe sieht, dass wirklich
        #: geantwortet wurde, und ein Mensch, ob überhaupt jemand fragt.
        self.beantwortet = 0

    @property
    def gebunden(self):
        """Wo der Antworter wirklich hört (``(adresse, anschluss)``), oder ``None``."""
        return self._sock.getsockname() if self._sock is not None else None

    def _oeffne(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            # NEBENEINANDER, NICHT STATT. Ohne diese beiden scheitert das Binden, sobald
            # ein avahi-Dienst auf 5353 hoert — oder, schlimmer, er scheitert beim naechsten
            # Start, weil wir ihm den Anschluss weggenommen haben. Geprueft ist das
            # BINDEN neben einem anderen Socket, nicht, dass der andere danach jede Frage
            # bekommt (siehe Modulkopf).
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except OSError:
                    pass                    # manche Systeme kennen den Namen, nicht die Sache
            s.bind(self.bindung)
            if self.gruppe:
                schnitt = self.angabe.adresse_roh
                s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                             struct.pack("4s4s", socket.inet_aton(GRUPPE), schnitt))
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, schnitt)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
            s.settimeout(self.TAKT_S)
        except OSError:
            s.close()
            raise
        return s

    def starte(self) -> "Rundruf":
        """Binden, beitreten, ankündigen, und den Faden starten.

        Raises:
            RundrufError: Binden oder Beitreten scheitert — mit dem Satz des Systems.
        """
        if self._faden is not None:
            raise RundrufError("Dieser Rundruf läuft schon.")
        try:
            self._sock = self._oeffne()
        except OSError as fehler:
            raise RundrufError(f"Der Rundruf liess sich nicht öffnen: {fehler}") from None
        self._halt.clear()
        if self.gruppe:
            self._sende_gruppe(ankuendigung(self.angabe))
        self._faden = threading.Thread(target=self._horche, name="rundruf", daemon=True)
        self._faden.start()
        return self

    def _sende_gruppe(self, roh: bytes) -> None:
        try:
            self._sock.sendto(roh, (GRUPPE, MDNS_ANSCHLUSS))
        except OSError:
            pass                            # eine verlorene Ankuendigung ist kein Absturz

    def _horche(self) -> None:
        """Der Faden. **Er fängt alles**: Ein Fehler in einem Paket beendet nicht das
        Finden für alle anderen Geräte."""
        while not self._halt.is_set():
            try:
                daten, absender = self._sock.recvfrom(PAKET_HOECHSTENS)
            except socket.timeout:
                continue
            except OSError:
                if self._halt.is_set():
                    break
                continue
            try:
                ergebnis = antworte(daten, self.angabe, absender_anschluss=absender[1])
                if ergebnis is None:
                    continue
                roh, direkt = ergebnis
                ziel = absender if (direkt or not self.gruppe) else (GRUPPE, MDNS_ANSCHLUSS)
                self._sock.sendto(roh, ziel)
                self.beantwortet += 1
            except Exception:              # noqa: BLE001 — siehe Docstring
                continue

    def beende(self, *, warte_s: float = 2.0) -> None:
        """Abschied senden, Faden anhalten, Socket schliessen. Mehrfach rufbar."""
        if self._sock is None:
            return
        if self.gruppe:
            self._sende_gruppe(ankuendigung(self.angabe, abschied=True))
        self._halt.set()
        if self._faden is not None:
            self._faden.join(timeout=warte_s)
        try:
            self._sock.close()
        finally:
            self._sock = None
            self._faden = None

    @property
    def laeuft(self) -> bool:
        return self._faden is not None and self._faden.is_alive()


def starte(*, anschluss: int, adresse, rechnername: str | None = None) -> Rundruf:
    """Den Rundruf für die Fläche starten — **der Weg, den** ``server.main`` **geht.**

    Raises:
        RundrufError: Keine Adresse, kein gültiger Anschluss, oder das System lässt den
            Anschluss 5353 bzw. den Beitritt zur Gruppe nicht zu.
    """
    angabe = Dienstangabe(anschluss=anschluss, adresse=adresse, rechnername=rechnername)
    return Rundruf(angabe).starte()
