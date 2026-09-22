"""Das erste Verbinden — eine kurze Zahl für einen Augenblick.

**Warum es das gibt:** Die HomeStation schützt ihre Oberfläche mit 32 zufälligen Zeichen.
Das ist für ein Kennwort richtig und für das erste Verbinden unbrauchbar — *was nur über
das Eintippen erreichbar ist, wird nicht benutzt.*

Die Wächter hier prüfen nicht, dass eine Zahl herauskommt, sondern **wovon sie lebt und
woran sie stirbt**: an der Frist, an den Versuchen, und am ersten gelungenen Verbinden.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from aiimaging import kopplung

QUELLE = Path(kopplung.__file__)


# --------------------------------------------------------------------------------------
# 1 · Die Zahl selbst
# --------------------------------------------------------------------------------------

def test_die_zahl_hat_immer_sechs_stellen():
    """Auch eine kleine Zahl wird auf sechs Stellen aufgefüllt.

    Ohne führende Nullen verriete die **Länge** die Grössenordnung — «4711» sagte einem
    Ratenden, dass die oberen zwei Stellen null sind. *Eine Zahl, deren Länge etwas
    verrät, ist kürzer als sie aussieht.*
    """
    for _ in range(200):
        p = kopplung.eroeffne()
        assert len(p.pin) == kopplung.PIN_STELLEN
        assert p.pin.isdigit()


def test_zwei_zahlen_sind_nicht_dieselbe():
    zahlen = {kopplung.eroeffne().pin for _ in range(200)}
    assert len(zahlen) > 190, "eine Quelle, die sich wiederholt, ist keine Zufallsquelle"


def test_die_zahl_kommt_aus_secrets_und_nicht_aus_random():
    """Geprüft an der Quelle, nicht an der Verteilung.

    Eine Verteilungsprüfung bestünde auch `random` — und `random` ist aus wenigen Werten
    fortrechenbar. *Ein Zufall, der sich fortrechnen lässt, ist keiner.*
    """
    quelle = QUELLE.read_text(encoding="utf-8")
    assert "secrets.randbelow" in quelle
    assert not re.search(r"^import random|\brandom\.(random|randint|choice)\b",
                         quelle, re.MULTILINE)


# --------------------------------------------------------------------------------------
# 2 · Woran sie stirbt
# --------------------------------------------------------------------------------------

def test_nach_der_frist_gilt_sie_nicht_mehr():
    p = kopplung.eroeffne(jetzt=0.0, frist_s=600.0)

    assert kopplung.stand(p, jetzt=599.0) == kopplung.STAND_OFFEN
    assert kopplung.stand(p, jetzt=600.0) == kopplung.STAND_ABGELAUFEN
    assert kopplung.pruefe(p, p.pin, jetzt=601.0)["angenommen"] is False


def test_eine_zurueckgestellte_uhr_bricht_die_frist_nicht_auf():
    """**Die Probe auf den Entscheid, keine Wanduhr zu benutzen.**

    Die Frist läuft auf einer stetigen Uhr. Diese Probe stellt die Uhr zurück — auf einer
    Wanduhr wäre die Zahl damit wieder gültig.

    *Eine Sperre, die eine falsch gehende Uhr aufbricht, ist keine Sperre. Sie ist eine
    Verzögerung.*
    """
    quelle = QUELLE.read_text(encoding="utf-8")
    assert "time.monotonic" in quelle
    assert "time.time()" not in quelle, (
        "die Frist darf auf keiner Uhr rechnen, die sich stellen laesst")


def test_fuenf_fehlversuche_toeten_die_zahl():
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")

    for i in range(kopplung.VERSUCHE):
        antwort = kopplung.pruefe(p, "000000", jetzt=1.0)
        assert antwort["angenommen"] is False
        assert antwort["versuche_uebrig"] == kopplung.VERSUCHE - 1 - i

    assert kopplung.stand(p, jetzt=1.0) == kopplung.STAND_AUFGEBRAUCHT
    assert kopplung.pruefe(p, "123456", jetzt=1.0)["angenommen"] is False, (
        "auch die richtige Zahl hilft danach nicht mehr — sonst waere der Zaehler keine "
        "Schranke, sondern eine Verzoegerung")


def test_auch_ueber_eine_abgelaufene_zahl_wird_nicht_beliebig_oft_geraten():
    """Der Zähler ist die einzige Schranke, die **nicht** von der Uhr abhängt.

    Bewegte er sich nach Ablauf der Frist nicht mehr, liesse sich über eine tote Zahl
    beliebig oft raten — und wer die Uhr stellen kann, hätte damit alles.
    """
    p = kopplung.eroeffne(jetzt=0.0, frist_s=10.0, _pin="123456")

    vorher = p.versuche_uebrig
    kopplung.pruefe(p, "000000", jetzt=99.0)

    assert p.versuche_uebrig == vorher, (
        "abgelaufen heisst abgelehnt, bevor geraten wird — der Zaehler bleibt fuer den "
        "Fall stehen, in dem die Frist noch laeuft")
    # Aber innerhalb der Frist zaehlt jeder Versuch, auch mit richtiger Zahl:
    q = kopplung.eroeffne(jetzt=0.0, frist_s=10.0, _pin="123456")
    kopplung.pruefe(q, "123456", jetzt=1.0)
    assert q.versuche_uebrig == kopplung.VERSUCHE - 1


def test_eine_zahl_verbindet_genau_ein_geraet():
    """Sonst verbindet sich, wer über die Schulter gesehen hat, als Zweiter mit."""
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")

    assert kopplung.pruefe(p, "123456", jetzt=1.0)["angenommen"] is True
    zweites = kopplung.pruefe(p, "123456", jetzt=2.0)

    assert zweites["angenommen"] is False
    assert zweites["stand"] == kopplung.STAND_VERBRAUCHT


def test_von_hand_schliessen_geht_sofort():
    """*Eine Sperre, die man nur durch Abwarten wieder los wird, wartet niemand ab.*"""
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")
    kopplung.schliesse(p)

    assert kopplung.pruefe(p, "123456", jetzt=1.0)["angenommen"] is False


# --------------------------------------------------------------------------------------
# 3 · Zwei Sätze, und warum sie verschieden sind
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("bauen, eingabe, zeitpunkt", [
    (lambda: kopplung.eroeffne(jetzt=0.0, frist_s=10.0, _pin="123456"), "000000", 1.0),
    (lambda: kopplung.eroeffne(jetzt=0.0, frist_s=10.0, _pin="123456"), "123456", 99.0),
    (lambda: kopplung.eroeffne(jetzt=0.0, frist_s=10.0, versuche=1, _pin="123456"),
     "000000", 1.0),
])
def test_das_geraet_hoert_immer_denselben_satz(bauen, eingabe, zeitpunkt):
    """**Drei verschiedene Gründe, ein Satz.**

    Wer eine Zahl rät, soll nicht erfahren, ob er an der Zahl oder an der Frist
    gescheitert ist — das halbierte sonst seine Arbeit.

    *Wer beim Raten erfährt, warum er daneben lag, rät beim nächsten Mal besser.*
    """
    antwort = kopplung.pruefe(bauen(), eingabe, jetzt=zeitpunkt)

    assert antwort["angenommen"] is False
    assert antwort["satz_fuer_das_geraet"] == kopplung.SATZ_FUER_DAS_GERAET


def test_der_mensch_an_der_homestation_hoert_den_genauen_grund():
    """Er steht vor dem Gerät und muss wissen, was zu tun ist."""
    abgelaufen = kopplung.eroeffne(jetzt=0.0, frist_s=10.0, _pin="123456")
    falsch = kopplung.eroeffne(jetzt=0.0, _pin="123456")
    verbraucht = kopplung.eroeffne(jetzt=0.0, _pin="123456")
    kopplung.pruefe(verbraucht, "123456", jetzt=1.0)

    assert kopplung.pruefe(abgelaufen, "123456", jetzt=99.0)["grund"] == (
        kopplung.GRUND_ABGELAUFEN)
    assert kopplung.pruefe(falsch, "000000", jetzt=1.0)["grund"] == kopplung.GRUND_FALSCH
    assert kopplung.pruefe(verbraucht, "123456", jetzt=2.0)["grund"] == (
        kopplung.GRUND_VERBRAUCHT)
    assert len({kopplung.GRUND_ABGELAUFEN, kopplung.GRUND_FALSCH,
                kopplung.GRUND_VERBRAUCHT}) == 3


# --------------------------------------------------------------------------------------
# 4 · Kleinigkeiten, die im Betrieb gross werden
# --------------------------------------------------------------------------------------

def test_ein_angehaengtes_leerzeichen_scheitert_nicht():
    """Ein Tablet hängt beim Einfügen gern eines an. Daran soll niemand scheitern."""
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")

    assert kopplung.pruefe(p, " 123456\n", jetzt=1.0)["angenommen"] is True


def test_leerzeichen_INNEN_werden_nicht_weggerechnet():
    """Sonst wären «123456» und «1 2 3 4 5 6» dieselbe Eingabe — und der Vorrat kleiner."""
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")

    assert kopplung.pruefe(p, "1 2 3 4 5 6", jetzt=1.0)["angenommen"] is False


def test_etwas_das_keine_zeichenkette_ist_stuerzt_nicht_ab():
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")

    assert kopplung.pruefe(p, None, jetzt=1.0)["angenommen"] is False
    assert kopplung.pruefe(p, 123456, jetzt=1.0)["angenommen"] is False


def test_der_vergleich_laeuft_ueber_compare_digest():
    """Ein gewöhnlicher Vergleich bricht bei der ersten abweichenden Stelle ab.

    *Eine Vorsichtsmassnahme, die nur dort greift, wo man sie für nötig hält, greift
    irgendwann nicht mehr.*
    """
    # BIS ZUM 22.09.2026 stand hier ein Blick in den Quelltext: «kommt compare_digest
    # vor?». Er blieb gruen, wenn der Aufruf dastand und das Ergebnis danach ein `==`
    # entschied. Gezaehlt wird jetzt, ob der gleichzeitige Vergleich WIRKLICH laeuft —
    # und ob er die eingetippte Zahl gegen die echte haelt.
    import hmac

    echt = hmac.compare_digest
    gesehen = []

    def zaehlend(a, b):
        gesehen.append((a, b))
        return echt(a, b)

    k = kopplung.eroeffne(jetzt=0.0, _pin="123456")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(hmac, "compare_digest", zaehlend)
        falsch = kopplung.pruefe(k, "123450", jetzt=1.0)
        richtig = kopplung.pruefe(k, "123456", jetzt=2.0)

    assert falsch["angenommen"] is False and richtig["angenommen"] is True
    assert len(gesehen) == 2, (
        f"compare_digest lief {len(gesehen)}-mal statt je Versuch einmal — entschieden "
        f"hat dann ein gewoehnlicher Vergleich, der bei der ersten falschen Ziffer abbricht")
    for a, b in gesehen:
        assert {str(a if isinstance(a, str) else a.decode()),
                str(b if isinstance(b, str) else b.decode())} & {"123456"}, (
            "verglichen wurde nicht gegen die echte Zahl")


def test_eine_kopplung_ohne_versuche_wird_abgelehnt():
    """Sie sähe im Betrieb aus wie eine falsch abgetippte Zahl und wäre keine."""
    with pytest.raises(kopplung.KopplungError):
        kopplung.eroeffne(versuche=0)
    with pytest.raises(kopplung.KopplungError):
        kopplung.eroeffne(frist_s=0)


def test_die_zahl_steht_in_keiner_meldung():
    """**Ein Geheimnis, das in einem Protokoll landet, ist keines mehr.**

    Geprüft wird an allem, was dieses Modul nach aussen gibt: Keine Antwort und keine
    Fehlermeldung darf die Zahl enthalten.
    """
    p = kopplung.eroeffne(jetzt=0.0, _pin="123456")
    ausgaben = [
        str(kopplung.pruefe(p, "000000", jetzt=1.0)),
        str(kopplung.pruefe(p, "123456", jetzt=2.0)),
        str(kopplung.pruefe(p, "123456", jetzt=3.0)),
        kopplung.SATZ_FUER_DAS_GERAET, kopplung.GRUND_FALSCH,
        kopplung.GRUND_ABGELAUFEN, kopplung.GRUND_AUFGEBRAUCHT, kopplung.GRUND_VERBRAUCHT,
    ]
    for text in ausgaben:
        assert "123456" not in text, f"die Zahl steht in einer Ausgabe: {text!r}"


def test_der_kern_bleibt_ohne_oberflaeche_benutzbar():
    """Regel 4 — dieses Modul kennt kein Netz, keine Oberfläche, keine Datei."""
    quelle = QUELLE.read_text(encoding="utf-8")
    for verboten in ("import http", "socket", "open(", "Path(", "requests"):
        assert verboten not in quelle, f"{verboten!r} hat hier nichts zu suchen"


# --------------------------------------------------------------------------------------
# 5 · Erreichbar über den Weg, den das Produkt geht
# --------------------------------------------------------------------------------------
#
# **Sonst gäbe es das alles nicht.** Dieses Projekt hat dreimal erlebt, dass eine
# Fähigkeit gebaut war und über den Weg, den ein Mensch wirklich geht, nicht erreichbar:
# der Schrittzähler, der Zwischenspeicher, die zwei Modus-Felder.
#
#     *Eine Naht, die nur der direkte Aufrufer erreicht, gibt es für den Weg nicht, den
#     das Produkt wirklich geht.*

import io as _io
import sys as _sys
from pathlib import Path as _Path

_FLAECHE = _Path(__file__).resolve().parents[1] / "oberflaeche"


@pytest.fixture
def flaechenmodul():
    _sys.path.insert(0, str(_FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        _sys.path.remove(str(_FLAECHE))


class _Tuer:
    """Eine Anfrage ohne Netz — gerade genug, dass ``_darf_herein`` laufen kann."""

    def __init__(self, modul, *, command, path, kennwort, offen, authorization=None):
        self.klasse = type("FlaechePruefling", (modul.Flaeche,),
                           {"kennwort": kennwort, "kopplung_offen": offen})
        self.selbst = self.klasse.__new__(self.klasse)
        self.selbst.command = command
        self.selbst.path = path
        self.selbst.headers = {"Authorization": authorization}
        self.selbst.wfile = _io.BytesIO()
        self.selbst.send_response = lambda *a, **k: None
        self.selbst.send_header = lambda *a, **k: None
        self.selbst.end_headers = lambda: None

    def darf_herein(self) -> bool:
        return self.selbst._darf_herein()


def test_ohne_kennwort_gibt_es_kein_verbinden(flaechenmodul):
    """*Wer ``--kopplung`` schreibt, erwartet, dass es wirkt* — es gäbe nichts zu tauschen."""
    with pytest.raises(flaechenmodul.FlaechenError):
        flaechenmodul.baue_server(adresse="127.0.0.1", anschluss=0, kennwort=None,
                                  kopplung_offen=kopplung.eroeffne())


def test_die_tuer_laesst_genau_diesen_einen_weg_durch(flaechenmodul):
    offen = kopplung.eroeffne()

    durch = _Tuer(flaechenmodul, command="POST", path=flaechenmodul.WEG_VERBINDEN,
                  kennwort="geheim", offen=offen)
    assert durch.darf_herein() is True, "ohne diesen Weg gaebe es kein erstes Verbinden"

    for befehl, weg in (("GET", "/"), ("GET", flaechenmodul.WEG_VERBINDEN),
                        ("POST", "/api/rechne"), ("POST", "/api/skizze")):
        zu = _Tuer(flaechenmodul, command=befehl, path=weg,
                   kennwort="geheim", offen=offen)
        assert zu.darf_herein() is False, f"{befehl} {weg} darf nicht unangemeldet durch"


def test_ohne_offene_kopplung_ist_auch_dieser_weg_zu(flaechenmodul):
    """Ohne ``--kopplung`` gibt es die Öffnung überhaupt nicht.

    *Eine Tür, die immer offensteht, weil sie einmal gebraucht wurde, ist keine Tür.*
    """
    zu = _Tuer(flaechenmodul, command="POST", path=flaechenmodul.WEG_VERBINDEN,
               kennwort="geheim", offen=None)

    assert zu.darf_herein() is False


def _flaeche_mit_kopplung(modul, offen, kennwort="das-lange-kennwort"):
    class Antwort:
        def __init__(self): self.daten = None
        def __call__(self, nutzlast, code=200): self.daten = (nutzlast, code)

    klasse = type("FlaecheVerbinden", (modul.Flaeche,),
                  {"kennwort": kennwort, "kopplung_offen": offen})
    f = klasse.__new__(klasse)
    antwort = Antwort()
    f._sende = antwort
    f._fehler = lambda satz, code=400: antwort({"fehler": satz}, code)
    return f, antwort


def test_die_richtige_zahl_bringt_das_kennwort(flaechenmodul, capsys):
    offen = kopplung.eroeffne(_pin="123456")
    f, antwort = _flaeche_mit_kopplung(flaechenmodul, offen)

    f._verbinden({"pin": "123456"})

    nutzlast, code = antwort.daten
    assert code == 200
    assert nutzlast["verbunden"] is True
    assert nutzlast["kennwort"] == "das-lange-kennwort"
    assert nutzlast["benutzer"] == flaechenmodul.BENUTZER


def test_eine_falsche_zahl_bringt_kein_kennwort_und_keinen_grund(flaechenmodul, capsys):
    """**Beides zusammen ist der Punkt:** kein Geheimnis, und keine Auskunft zum Raten."""
    offen = kopplung.eroeffne(_pin="123456")
    f, antwort = _flaeche_mit_kopplung(flaechenmodul, offen)

    f._verbinden({"pin": "000000"})

    nutzlast, code = antwort.daten
    assert code == 403
    assert nutzlast["verbunden"] is False
    assert "kennwort" not in nutzlast
    assert nutzlast["satz"] == kopplung.SATZ_FUER_DAS_GERAET
    assert kopplung.GRUND_FALSCH not in str(nutzlast)

    # Der genaue Grund geht an die HomeStation, also in das Fenster, in dem sie laeuft.
    assert kopplung.GRUND_FALSCH in capsys.readouterr().out


def test_das_kennwort_geht_genau_einmal_ueber_diesen_weg(flaechenmodul):
    """*Ein Weg, über den ein Geheimnis zweimal herauskommt, ist eine Ausgabestelle.*"""
    offen = kopplung.eroeffne(_pin="123456")
    f, antwort = _flaeche_mit_kopplung(flaechenmodul, offen)

    f._verbinden({"pin": "123456"})
    assert antwort.daten[0]["verbunden"] is True

    f._verbinden({"pin": "123456"})
    nutzlast, code = antwort.daten
    assert nutzlast["verbunden"] is False
    assert "kennwort" not in nutzlast


def test_fuenf_fehlversuche_wirken_auch_ueber_die_flaeche(flaechenmodul):
    """Der Zähler ist nur dann eine Schranke, wenn ihn alle Anfragen teilen."""
    offen = kopplung.eroeffne(_pin="123456")
    f, antwort = _flaeche_mit_kopplung(flaechenmodul, offen)

    for _ in range(kopplung.VERSUCHE):
        f._verbinden({"pin": "000000"})

    f._verbinden({"pin": "123456"})
    assert antwort.daten[0]["verbunden"] is False, (
        "nach dem Aufbrauchen hilft auch die richtige Zahl nicht mehr")


class _Anfrage(_Tuer):
    """Wie `_Tuer`, aber die ganze Anfrage: `do_POST` läuft hier **wirklich**.

    `_Tuer` reicht bis zur Türschwelle — sie ruft `_darf_herein`. Für die Frage, ob ein
    Weg in der Wegtafel hängt, genügt das nicht: Die Tafel liegt hinter der Schwelle.
    """

    def __init__(self, modul, *, command, path, kennwort, offen, rumpf=b"",
                 authorization=None):
        super().__init__(modul, command=command, path=path, kennwort=kennwort,
                         offen=offen, authorization=authorization)
        self.selbst.headers = dict(self.selbst.headers,
                                   **{"Content-Length": str(len(rumpf))})
        self.selbst.rfile = _io.BytesIO(rumpf)
        self.codes = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)

    def stelle(self):
        self.selbst.do_POST()
        return self

    def nutzlast(self):
        return json.loads(self.selbst.wfile.getvalue().decode("utf-8"))


def test_der_weg_haengt_wirklich_in_der_wegtafel(flaechenmodul, capsys):
    """Der Wächter gegen genau den Fehler, den dieses Projekt dreimal gemacht hat.

    Eine Methode, die gebaut ist und in keiner Verzweigung steht, gibt es für den, der
    über HTTP kommt, nicht.

    **Was dieser Wächter bis zum 22.09.2026 nicht geprüft hat:** Er sah nach, ob zwei
    Zeilen im Quelltext von ``oberflaeche/server.py`` **stehen**. Ob sie beim Anklopfen
    auch **erreicht werden**, stand nirgends. Wer ``do_POST`` umbaut und die alte Kette
    als unbenutzte Methode stehenlässt, liess ihn grün — und das erste Verbinden
    antwortete in Wahrheit 404.

        *Ein Wächter, der die Stellung einer Zeile prüft statt ihrer Wirkung, prüft den
        Text und nicht das Programm.*

    Angeklopft wird jetzt auf dem Weg, den das Gerät wirklich geht: ein POST auf
    ``WEG_VERBINDEN`` mit der richtigen Zahl — und zurück muss das Kennwort kommen, nicht
    ein «Unbekannter Weg».
    """
    offen = kopplung.eroeffne(_pin="123456")
    a = _Anfrage(flaechenmodul, command="POST", path=flaechenmodul.WEG_VERBINDEN,
                 kennwort="das-lange-kennwort", offen=offen,
                 rumpf=json.dumps({"pin": "123456"}).encode("utf-8")).stelle()

    assert a.codes == [200], (
        f"POST {flaechenmodul.WEG_VERBINDEN} kam mit {a.codes} zurück — 404 hiesse, der "
        f"Weg hängt in keiner Verzweigung.")
    nutzlast = a.nutzlast()
    assert nutzlast["verbunden"] is True
    assert nutzlast["kennwort"] == "das-lange-kennwort"
