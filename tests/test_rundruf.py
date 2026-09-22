"""Der Rundruf (Entscheid 27) — **an der Wirkung geprüft, nicht am Quelltext.**

Ein iPad fragt über die Bonjour-Suche seines Systems nach ``_visbox._tcp``;
``oberflaeche/rundruf.py`` antwortet. Geprüft wird hier:

1. **Name und Dienst stimmen mit der App überein** — gelesen aus ``Marke.swift``. Ein
   Buchstabe Unterschied, und das iPad sucht einen Dienst, den niemand anbietet.
2. **Eine selbstgebaute DNS-Frage bekommt die richtige Antwort** — Instanzname,
   Anschluss, Fassung, Adresse. Erst direkt über die Paketfunktionen, dann über einen
   lokalen UDP-Socket mit dem echten Hintergrundfaden (ohne Multicast).
3. **Fremde Fragen bleiben unbeantwortet** — sonst verdrängte der Rundruf einen
   vorhandenen Bonjour-Dienst, ohne ihn abzuschalten.
4. **Zwei Antworter teilen sich einen Anschluss** — ``SO_REUSEADDR``/``SO_REUSEPORT`` an
   der Wirkung: Das zweite Binden gelingt.
5. **Er startet nur mit** ``--im-heimnetz`` und wird beim Beenden der Fläche beendet.

Was hier NICHT geprüft wird und nicht geprüft werden kann: ob ein echtes iPad ihn findet
(am Gerät unbestätigt, 22.09.2026).
"""
from __future__ import annotations

import ast
import re
import socket
import struct
import sys
import time
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
RUNDRUF_PY = FLAECHE / "rundruf.py"
MARKE = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Marke.swift"


@pytest.fixture(scope="module")
def rundruf():
    sys.path.insert(0, str(FLAECHE))
    try:
        import rundruf as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture
def angabe(rundruf):
    # 192.0.2.x ist eine Dokumentationsadresse (RFC 5737) — sie gehoert niemandem.
    return rundruf.Dienstangabe(anschluss=8731, adresse="192.0.2.10", rechnername="Probe Rechner")


def _marke() -> dict:
    zeilen = [z for z in MARKE.read_text(encoding="utf-8").splitlines()
              if not z.lstrip().startswith("//")]
    return dict(re.findall(r'static let (\w+)\s*=\s*"([^"]+)"', "\n".join(zeilen)))


def _saetze(antwort: dict) -> list[dict]:
    return antwort["antworten"] + antwort["zusatz"]


def _nach_typ(antwort: dict, typ: int) -> list[dict]:
    return [s for s in _saetze(antwort) if s["typ"] == typ]


# ================================================= 1 · Name und Dienst wie in der App

def test_der_dienst_ist_der_den_die_app_sucht(rundruf):
    """iOS sucht nur, was im Manifest steht, und das Manifest nennt ``Marke.dienst``."""
    assert rundruf.DIENST == _marke()["dienst"]


def test_der_name_ist_der_der_app(rundruf):
    """Nach der Abgabe heisst die App anders (Entscheid 34). Ein Rundruf unter dem alten
    Namen wäre die Stelle, die beim Umbenennen niemand findet."""
    assert rundruf.NAME == _marke()["name"]


def test_der_rundruf_braucht_nur_die_standardbibliothek():
    """Regel 1: kein Zeroconf-Paket. Gelesen aus dem Syntaxbaum, gegen die Liste der
    Standardbibliothek selbst — nicht gegen eine Liste von Hand."""
    fremd = set()
    for k in ast.walk(ast.parse(RUNDRUF_PY.read_text(encoding="utf-8"))):
        if isinstance(k, ast.Import):
            fremd |= {n.name.split(".")[0] for n in k.names}
        elif isinstance(k, ast.ImportFrom) and k.module:
            fremd.add(k.module.split(".")[0])
    assert fremd <= set(sys.stdlib_module_names) | {"__future__"}, sorted(fremd)


# ============================================ 2 · die Antwort auf eine selbstgebaute Frage

def test_die_frage_nach_dem_dienst_bringt_name_anschluss_fassung_und_adresse(rundruf, angabe):
    """**Der ganze Zweck in einem Paket:** PTR auf die Instanz, SRV mit Anschluss und
    Rechner, TXT mit der Fassung, A mit der Adresse — alles in der einen Antwort, damit
    das iPad nicht viermal fragen muss."""
    frage = rundruf.baue_anfrage("_visbox._tcp.local", rundruf.TYP_PTR)
    roh, direkt = rundruf.antworte(frage, angabe)
    a = rundruf.lies_paket(roh)

    assert a["antwort"] is True
    (ptr,) = _nach_typ(a, rundruf.TYP_PTR)
    assert ptr["name"] == "_visbox._tcp.local"
    assert ptr["ziel"] == angabe.instanz
    assert ptr["ziel"].startswith(rundruf.NAME + " ")

    (srv,) = _nach_typ(a, rundruf.TYP_SRV)
    assert srv["name"] == angabe.instanz
    assert srv["anschluss"] == 8731
    (txt,) = _nach_typ(a, rundruf.TYP_TXT)
    assert "fassung=1" in txt["texte"]
    (adr,) = _nach_typ(a, rundruf.TYP_A)
    assert adr["name"] == srv["ziel"], "die Adresse gehört zum Rechner, auf den SRV zeigt"
    assert adr["adresse"] == "192.0.2.10"
    assert direkt is False, "über 5353 gefragt, ohne QU-Bit: an die Gruppe antworten"


def test_die_fassung_liest_die_app_so_wie_sie_hier_steht(rundruf, angabe):
    """Die Leitungsform des TXT-Eintrags (RFC 6763 §6): je Eintrag ein Längenbyte und
    ``schluessel=wert``. So liest sie ``Suche.txtEintraege`` in der App."""
    roh, _ = rundruf.antworte(rundruf.baue_anfrage(angabe.instanz, rundruf.TYP_TXT), angabe)
    (txt,) = _nach_typ(rundruf.lies_paket(roh), rundruf.TYP_TXT)
    schluessel, _, wert = txt["texte"][0].partition("=")
    assert (schluessel, wert) == ("fassung", str(rundruf.FASSUNG))


def test_ein_einfacher_fragesteller_bekommt_seine_kennung_und_seine_frage_zurueck(rundruf, angabe):
    """RFC 6762 §6.7: Wer nicht von 5353 fragt, erkennt seine Antwort an Kennung und Frage.
    Er bekommt sie **direkt**, ohne cache-flush und mit höchstens 10 s Gültigkeit."""
    frage = rundruf.baue_anfrage("_visbox._tcp.local", rundruf.TYP_PTR, kennung=4711)
    roh, direkt = rundruf.antworte(frage, angabe, absender_anschluss=50000)
    a = rundruf.lies_paket(roh)

    assert direkt is True
    assert a["kennung"] == 4711
    assert [f["name"] for f in a["fragen"]] == ["_visbox._tcp.local"]
    assert all(not s["cache_flush"] for s in _saetze(a))
    assert all(s["ttl"] <= rundruf.TTL_EINFACH for s in _saetze(a))


def test_ueber_5353_gilt_die_kennung_null_und_cache_flush_nur_fuer_eindeutige(rundruf, angabe):
    a = rundruf.lies_paket(rundruf.antworte(
        rundruf.baue_anfrage("_visbox._tcp.local", kennung=99), angabe)[0])
    assert a["kennung"] == 0 and a["fragen"] == []
    assert all(s["cache_flush"] is (s["typ"] != rundruf.TYP_PTR) for s in _saetze(a)), (
        "PTR ist geteilt (kein cache-flush), SRV/TXT/A gehören nur diesem Rechner")


def test_das_qu_bit_bringt_die_antwort_direkt(rundruf, angabe):
    frage = rundruf.baue_anfrage("_visbox._tcp.local", direkt=True)
    assert rundruf.antworte(frage, angabe)[1] is True


def test_die_frage_nach_den_dienstarten_nennt_den_dienst(rundruf, angabe):
    """DNS-SD-Aufzählung (RFC 6763 §9) — manche Sucher fragen erst, was es gibt."""
    roh, _ = rundruf.antworte(rundruf.baue_anfrage(rundruf.DIENSTARTEN), angabe)
    (ptr,) = _nach_typ(rundruf.lies_paket(roh), rundruf.TYP_PTR)
    assert ptr["ziel"] == "_visbox._tcp.local"


def test_eine_komprimierte_frage_wird_gelesen(rundruf, angabe):
    """iOS darf Namen mit Verweisen schicken: Hier zeigt die zweite Frage (SRV auf die
    Instanz) mit einem Verweis auf den Dienstnamen der ersten."""
    kopf = struct.pack("!HHHHHH", 0, 0, 2, 0, 0, 0)
    dienst = rundruf._name_bytes("_visbox._tcp.local")
    erste = dienst + struct.pack("!HH", rundruf.TYP_PTR, 1)
    teil = angabe.instanz.split("._visbox")[0].encode()
    zweite = bytes([len(teil)]) + teil + struct.pack("!H", 0xC000 | 12) \
        + struct.pack("!HH", rundruf.TYP_SRV, 1)
    roh, _ = rundruf.antworte(kopf + erste + zweite, angabe)
    a = rundruf.lies_paket(roh)
    assert [s["typ"] for s in a["antworten"]] == [rundruf.TYP_PTR, rundruf.TYP_SRV]


def test_ein_kreisender_verweis_haelt_den_faden_nicht_fest(rundruf, angabe):
    kopf = struct.pack("!HHHHHH", 0, 0, 1, 0, 0, 0)
    kreis = struct.pack("!H", 0xC000 | 12) + struct.pack("!HH", 12, 1)   # zeigt auf sich
    assert rundruf.antworte(kopf + kreis, angabe) is None


# ================================================ 3 · fremde Fragen bleiben unbeantwortet

@pytest.mark.parametrize("name,typ", [
    ("_andere._tcp.local", 12),            # ein fremder Dienst
    ("_visbox._udp.local", 12),            # fast derselbe
    ("irgendwer.local", 1),                # die Adresse eines anderen Rechners
])
def test_eine_fremde_frage_bekommt_keine_antwort(rundruf, angabe, name, typ):
    """**Die Probe, die das Nebeneinander trägt.** Wer auf fremde Fragen antwortet,
    verdrängt den anderen Dienst, ohne ihn abzuschalten."""
    assert rundruf.antworte(rundruf.baue_anfrage(name, typ), angabe) is None


def test_eine_antwort_wird_nicht_beantwortet(rundruf, angabe):
    """Die eigene Ankündigung kommt über die Gruppe zurück — sie ist keine Frage."""
    assert rundruf.antworte(rundruf.ankuendigung(angabe), angabe) is None


def test_kaputte_pakete_sind_keine_antwort_und_kein_absturz(rundruf, angabe):
    for roh in (b"", b"\x00" * 5, b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x3fabc"):
        assert rundruf.antworte(roh, angabe) is None


def test_der_abschied_setzt_die_gueltigkeit_auf_null(rundruf, angabe):
    """Beim Beenden vergessen die Geräte den Eintrag sofort, statt eine Stunde lang auf
    eine HomeStation zu zeigen, die nicht mehr antwortet."""
    a = rundruf.lies_paket(rundruf.ankuendigung(angabe, abschied=True))
    assert {s["ttl"] for s in a["antworten"]} == {0}
    assert {s["typ"] for s in a["antworten"]} == {12, 33, 16, 1}


# ======================================================= die dritte Antwort: keine Adresse

def test_ohne_adresse_wird_nichts_angekuendigt(rundruf):
    """Nicht ermittelt ist weder 0.0.0.0 noch 127.0.0.1 — und ein Rundruf ohne Adresse
    kündigte einen Namen an, unter dem niemand ankommt."""
    with pytest.raises(rundruf.RundrufError, match="nicht ermittelt"):
        rundruf.Dienstangabe(anschluss=8731, adresse=None)


@pytest.mark.parametrize("anschluss", [0, 70000, True, "8731"])
def test_ein_unbrauchbarer_anschluss_wird_abgewiesen(rundruf, anschluss):
    with pytest.raises(rundruf.RundrufError):
        rundruf.Dienstangabe(anschluss=anschluss, adresse="192.0.2.10")


# ====================================== über einen lokalen UDP-Socket, mit dem echten Faden

def _frage_ueber_udp(rundruf, ziel, name, typ=12):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        s.sendto(rundruf.baue_anfrage(name, typ, kennung=321), ziel)
        daten, _ = s.recvfrom(9000)
    return rundruf.lies_paket(daten)


def test_der_faden_antwortet_ueber_einen_echten_socket(rundruf, angabe):
    """Der Weg, den ein Paket wirklich geht: Socket → Faden → ``antworte`` → Socket.
    Ohne Multicast, über ``127.0.0.1`` — die Antwort kommt direkt zurück."""
    r = rundruf.Rundruf(angabe, bindung=("127.0.0.1", 0), gruppe=False).starte()
    try:
        a = _frage_ueber_udp(rundruf, r.gebunden, "_visbox._tcp.local")
        (srv,) = _nach_typ(a, rundruf.TYP_SRV)
        (txt,) = _nach_typ(a, rundruf.TYP_TXT)
        assert a["kennung"] == 321
        assert srv["anschluss"] == 8731
        assert "fassung=1" in txt["texte"]
        assert _nach_typ(a, rundruf.TYP_PTR)[0]["ziel"] == angabe.instanz
        assert r.beantwortet == 1
    finally:
        r.beende()


def test_eine_fremde_frage_ueber_den_socket_bleibt_still(rundruf, angabe):
    r = rundruf.Rundruf(angabe, bindung=("127.0.0.1", 0), gruppe=False).starte()
    try:
        with pytest.raises(socket.timeout):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.6)
                s.sendto(rundruf.baue_anfrage("_andere._tcp.local"), r.gebunden)
                s.recvfrom(9000)
        # UND ER LEBT DANACH NOCH: Die naechste eigene Frage wird beantwortet.
        assert _frage_ueber_udp(rundruf, r.gebunden, "_visbox._tcp.local")["antworten"]
    finally:
        r.beende()


def test_zwei_antworter_teilen_sich_einen_anschluss(rundruf, angabe):
    """**Die Wirkung von SO_REUSEADDR/SO_REUSEPORT:** Ein zweiter Antworter bindet an
    denselben Anschluss, ohne den ersten zu verdrängen — so wie dieser Rundruf neben
    einem vorhandenen avahi auf 5353 steht. Ohne die beiden Optionen schlüge das zweite
    Binden mit «Address already in use» fehl."""
    erster = rundruf.Rundruf(angabe, bindung=("127.0.0.1", 0), gruppe=False).starte()
    try:
        zweiter = rundruf.Rundruf(angabe, bindung=erster.gebunden, gruppe=False).starte()
        try:
            assert zweiter.gebunden == erster.gebunden
            assert erster.laeuft and zweiter.laeuft
        finally:
            zweiter.beende()
    finally:
        erster.beende()


@pytest.mark.parametrize("option", ["SO_REUSEADDR", "SO_REUSEPORT"])
def test_neben_einem_fremden_dienst_der_nur_eine_option_setzt(rundruf, angabe, option):
    """**Jede der beiden Optionen an ihrer eigenen Wirkung.** Ein fremder Dienst hält den
    Anschluss und setzt nur **eine** der beiden. Welche ein vorhandener Dienst wirklich
    setzt (avahi, andere mDNS-Stapel), ist hier nicht nachgesehen — darum beide Fälle.
    Linux lässt ein zweites Binden nur zu, wenn beide Seiten **dieselbe** Option gesetzt
    haben; der Rundruf muss darum beide setzen.

    Die Probe mit zwei eigenen Antwortern darüber fällt nicht, wenn nur eine der beiden
    Zeilen fehlt (Mutationsprobe 22.09.2026): Beide Antworter setzen dieselbe übrige.
    Erst ein fremder Dienst mit genau der anderen trennt die beiden Fälle."""
    if not hasattr(socket, option):
        pytest.skip(f"{option} gibt es auf diesem System nicht")
    fremd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        fremd.setsockopt(socket.SOL_SOCKET, getattr(socket, option), 1)
        fremd.bind(("127.0.0.1", 0))
        r = rundruf.Rundruf(angabe, bindung=fremd.getsockname(), gruppe=False).starte()
        try:
            assert r.gebunden == fremd.getsockname()
        finally:
            r.beende()
    finally:
        fremd.close()


def test_der_faden_endet_sauber_und_gibt_den_socket_frei(rundruf, angabe):
    r = rundruf.Rundruf(angabe, bindung=("127.0.0.1", 0), gruppe=False).starte()
    ziel = r.gebunden
    faden = r._faden
    t0 = time.monotonic()
    r.beende()
    assert not faden.is_alive(), "der Faden läuft nach dem Beenden weiter"
    assert time.monotonic() - t0 < 2.0
    assert r.gebunden is None and not r.laeuft
    r.beende()                                    # ein zweites Mal schadet nicht
    # UND DER ANSCHLUSS IST WIEDER FREI — auch ohne SO_REUSEADDR bindbar.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(ziel)


# ============================================== 5 · nur mit --im-heimnetz, und beendet

class _Gebaut:
    """Der echte Serverbau, aber ``serve_forever`` endet sofort wie mit Strg-C."""

    def __init__(self, server, monkeypatch):
        echt = server.baue_server
        self.liste = []

        def bau(**kw):
            srv = echt(**kw)

            def sofort():
                raise KeyboardInterrupt

            srv.serve_forever = sofort
            self.liste.append(srv)
            return srv

        monkeypatch.setattr(server, "baue_server", bau)


class _Attrappe:
    def __init__(self):
        self.beendet = 0

    def beende(self):
        self.beendet += 1


def test_ohne_heimnetz_startet_kein_rundruf(server, monkeypatch, capsys):
    """Auf 127.0.0.1 kann kein anderes Gerät herein — ein Rundruf lüde zu einer
    Verbindung ein, die nicht zustande kommt."""
    _Gebaut(server, monkeypatch)
    gerufen = []
    monkeypatch.setattr(server, "starte_rundruf",
                        lambda anschluss: gerufen.append(anschluss) or (_Attrappe(), ""))
    assert server.main(["--anschluss", "0"]) == 0
    assert gerufen == []
    assert "Finden" not in capsys.readouterr().out


def test_mit_heimnetz_startet_er_auf_dem_wirklichen_anschluss_und_endet_mit(
        server, monkeypatch, capsys):
    gebaut = _Gebaut(server, monkeypatch)
    gerufen, attrappe = [], _Attrappe()
    monkeypatch.setattr(server, "starte_rundruf",
                        lambda anschluss: gerufen.append(anschluss) or (attrappe, "  Finden: x"))
    assert server.main(["--im-heimnetz", "--kennwort", "geheim", "--anschluss", "0"]) == 0
    assert gerufen == [gebaut.liste[0].server_address[1]], (
        "angekündigt wird der Anschluss, auf dem die Fläche WIRKLICH hört")
    assert attrappe.beendet == 1, "beim Beenden der Fläche endet auch der Rundruf"
    assert "Finden: x" in capsys.readouterr().out


def test_ohne_ermittelte_adresse_laeuft_die_flaeche_trotzdem_und_sagt_warum(
        server, monkeypatch, capsys):
    """Der Rundruf ist eine Bequemlichkeit. Scheitert er, bleibt die Fläche erreichbar —
    und der Satz sagt, dass die Adresse einzutippen ist."""
    _Gebaut(server, monkeypatch)
    monkeypatch.setattr(server, "heimnetz_adresse", lambda: None)
    assert server.main(["--im-heimnetz", "--kennwort", "geheim", "--anschluss", "0"]) == 0
    aus = capsys.readouterr().out
    assert "kein Rundruf" in aus and "nicht ermittelt" in aus
    assert "0.0.0.0" not in aus


def test_der_echte_start_nimmt_die_heimnetzadresse_der_flaeche(server, monkeypatch):
    """``starte_rundruf`` übergibt, was ``heimnetz_adresse`` sagt — hier eine Adresse,
    die dieser Rechner nicht hat. Das Beitreten scheitert dann, und das wird ein Satz,
    kein Absturz."""
    monkeypatch.setattr(server, "heimnetz_adresse", lambda: "192.0.2.77")
    r, satz = server.starte_rundruf(8731)
    try:
        if r is None:
            assert "kein Rundruf" in satz
        else:                                   # ein System, das den Beitritt doch zulaesst
            assert r.angabe.adresse == "192.0.2.77"
    finally:
        if r is not None:
            r.beende()
