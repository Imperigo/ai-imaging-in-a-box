"""Fortschrittswache — und der geerbte Wächter, der genau dort nicht feuert.

Der wichtigste Test dieser Datei ist
:func:`test_der_geerbte_wachhund_haette_hier_die_uhr_zurueckgestellt`. Er stellt den
Fall nach, für den jener Wächter gebaut wurde, und zeigt, dass er ihn durchlässt.
"""
from __future__ import annotations

import pytest

from aiimaging import fortschritt


class Uhr:
    """Eine Uhr, die man vorstellen kann. Ohne sie kostete ein Stillstandstest fünf
    Minuten Wartezeit — und ein Test, der nicht läuft, prüft nichts."""

    def __init__(self, t: float = 0.0) -> None:
        self.t = float(t)

    def __call__(self) -> float:
        return self.t

    def weiter(self, s: float) -> None:
        self.t += float(s)


# ======================================================================================
# Der Befund
# ======================================================================================

def test_der_geerbte_wachhund_haette_hier_die_uhr_zurueckgestellt():
    """Ein Backend, das ewig 'running' meldet und nichts tut.

    Der Altbestand stellt bei ``status in ("running", "queued")`` die Uhr zurück und
    wartet weiter — der Stillstand wird nie gemeldet. Unsere Wache meldet ihn, und zwar
    ehrlich abgestuft: bei einem blossen Statuswort als **Warnung**, weil sich langsam
    von hängend nicht trennen lässt.
    """
    uhr = Uhr()
    wache = fortschritt.wache_fuer_status(frist_s=300, _uhr=uhr)
    wache.melde(("running", 0))    # das erste Zeichen IST Fortschritt

    for _ in range(20):            # 20 × 5 Minuten = 100 Minuten dasselbe Wort
        uhr.weiter(300)
        befund = wache.melde(("running", 0))

    assert befund["befund"] == "stillstand"
    assert befund["schwere"] == fortschritt.SCHWERE_WARN
    assert befund["unterscheidbar"] is False
    assert "LANGSAM nicht von HÄNGEND" in befund["detail"]
    # Die Uhr wurde NICHT zurückgestellt — das ist der ganze Unterschied zum Altbestand,
    # der bei jedem dieser zwanzig Blicke `last_progress_t = time.time()` gesetzt hätte.
    assert befund["still_seit_s"] == pytest.approx(6000)
    assert befund["schritte"] == 1, "zwanzigmal gefragt, ein einziges Zeichen bekommen"


def test_derselbe_fall_mit_belegtem_zeichen_ist_ein_fehler():
    """Sobald etwas Unabhängiges beobachtet wird, heisst Stillstand wirklich Stillstand."""
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=300, art=fortschritt.BELEGT, _uhr=uhr)
    wache.melde((1024, 100))
    uhr.weiter(301)
    befund = wache.melde((1024, 100))
    assert befund["befund"] == "stillstand"
    assert befund["schwere"] == fortschritt.SCHWERE_FEHLER
    assert befund["unterscheidbar"] is True


def test_ein_belegtes_zeichen_das_sich_bewegt_haelt_die_wache_ruhig():
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=300, art=fortschritt.BELEGT, _uhr=uhr)
    for groesse in (1024, 2048, 4096, 8192):
        uhr.weiter(200)
        befund = wache.melde((groesse, 0))
        assert befund["befund"] is None
        assert befund["schwere"] == fortschritt.SCHWERE_OK
    assert befund["schritte"] == 4


# ======================================================================================
# Die Uhr läuft ab Beginn
# ======================================================================================

def test_das_erste_zeichen_ist_fortschritt_und_stellt_die_uhr():
    """Vor dem ersten Zeichen läuft die Uhr ab dem Aufsetzen — danach ab dem Zeichen."""
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=100, art=fortschritt.BELEGT, _uhr=uhr)
    uhr.weiter(90)
    assert wache.melde(("erstes",))["befund"] is None
    uhr.weiter(90)
    assert wache.melde(("erstes",))["befund"] is None, "erst 90 s seit dem Zeichen"
    uhr.weiter(20)
    assert wache.melde(("erstes",))["befund"] == "stillstand"


def test_ein_backend_das_nie_etwas_meldet_ist_der_klarste_stillstand():
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=300, art=fortschritt.BELEGT, _uhr=uhr)
    uhr.weiter(400)
    befund = wache.melde(None)
    assert befund["befund"] == "stillstand"
    assert befund["schritte"] == 0


def test_none_gilt_nicht_als_fortschritt():
    """Sonst hielte ein Backend, das nur noch schweigt, die Wache am Leben."""
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=100, art=fortschritt.BELEGT, _uhr=uhr)
    wache.melde((1, 1))
    for _ in range(5):
        uhr.weiter(50)
        befund = wache.melde(None)
    assert befund["befund"] == "stillstand"
    assert befund["schritte"] == 1


def test_die_frist_wird_nicht_schon_beim_gleichstand_gerissen():
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=300, art=fortschritt.BELEGT, _uhr=uhr)
    wache.melde((1, 1))
    uhr.weiter(300)
    assert wache.melde((1, 1))["befund"] is None
    uhr.weiter(0.001)
    assert wache.melde((1, 1))["befund"] == "stillstand"


# ======================================================================================
# Die Wache bricht nichts ab
# ======================================================================================

def test_die_wache_wirft_nie_von_selbst():
    """Abgebrochen wird eine Stufe höher, wo man weiss, was ein Abbruch kostet."""
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=1, art=fortschritt.BELEGT, _uhr=uhr)
    wache.melde(("gleich",))
    uhr.weiter(10_000)
    befund = wache.melde(("gleich",))
    assert befund["schwere"] == fortschritt.SCHWERE_FEHLER  # gemeldet …
    assert wache.befund()["schwere"] == fortschritt.SCHWERE_FEHLER  # … und wiederholbar
    # Kein raise, kein sys.exit, kein Abbruch — nur ein Befund.


def test_befund_ist_ohne_melde_abrufbar():
    uhr = Uhr()
    wache = fortschritt.Wache(frist_s=10, art=fortschritt.BELEGT, _uhr=uhr)
    uhr.weiter(11)
    assert wache.befund()["befund"] == "stillstand"
    assert wache.laeuft_seit_s == pytest.approx(11)


# ======================================================================================
# Belegte Zeichen aus dem Dateisystem
# ======================================================================================

def test_datei_marke_faengt_das_wachsen(tmp_path):
    ziel = tmp_path / "bild.png"
    assert fortschritt.datei_marke(ziel) is None
    ziel.write_bytes(b"x" * 10)
    a = fortschritt.datei_marke(ziel)
    ziel.write_bytes(b"x" * 20)
    b = fortschritt.datei_marke(ziel)
    assert a != b and b[0] == 20


def test_verzeichnis_marke_faengt_neue_dateien(tmp_path):
    assert fortschritt.verzeichnis_marke(tmp_path) == (0, 0)
    (tmp_path / "a.png").write_bytes(b"1")
    a = fortschritt.verzeichnis_marke(tmp_path)
    (tmp_path / "b.png").write_bytes(b"22")
    b = fortschritt.verzeichnis_marke(tmp_path)
    assert a == (1, 1) and b == (2, 3)


def test_verzeichnis_marke_filtert_nach_endung(tmp_path):
    (tmp_path / "a.png").write_bytes(b"1")
    (tmp_path / "b.log").write_bytes(b"22")
    assert fortschritt.verzeichnis_marke(tmp_path, endung=".png") == (1, 1)


def test_verzeichnis_marke_zaehlt_nicht_rekursiv(tmp_path):
    (tmp_path / "a.png").write_bytes(b"1")
    tief = tmp_path / "unten"
    tief.mkdir()
    (tief / "b.png").write_bytes(b"2")
    assert fortschritt.verzeichnis_marke(tmp_path, endung=".png") == (1, 1)


def test_verzeichnis_marke_auf_fehlendem_ordner_ist_none(tmp_path):
    assert fortschritt.verzeichnis_marke(tmp_path / "gibtsnicht") is None


def test_blick_holt_die_marke_selbst(tmp_path):
    """Der gebundene Pfad wird wirklich gelesen — kein toter Parameter."""
    uhr = Uhr()
    ziel = tmp_path / "wachsend.png"
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    ziel.write_bytes(b"x")
    uhr.weiter(50)
    assert wache.blick()["befund"] is None
    ziel.write_bytes(b"xxxx")
    uhr.weiter(50)
    assert wache.blick()["befund"] is None, "gewachsen — kein Stillstand"
    uhr.weiter(101)
    befund = wache.blick()
    assert befund["befund"] == "stillstand"
    assert befund["schwere"] == fortschritt.SCHWERE_FEHLER


def test_blick_auf_ordner(tmp_path):
    uhr = Uhr()
    wache = fortschritt.wache_fuer_verzeichnis(tmp_path, endung=".png", frist_s=100,
                                               _uhr=uhr)
    (tmp_path / "a.png").write_bytes(b"1")
    uhr.weiter(50)
    assert wache.blick()["befund"] is None
    uhr.weiter(101)
    assert wache.blick()["befund"] == "stillstand"


def test_blick_ohne_quelle_sagt_es_statt_stillschweigend_none_zu_melden():
    wache = fortschritt.wache_fuer_status(frist_s=10)
    with pytest.raises(fortschritt.FortschrittsError, match="keine eigene Zeichenquelle"):
        wache.blick()


def test_dateiwachen_sind_zwangslaeufig_belegt(tmp_path):
    assert fortschritt.wache_fuer_datei(tmp_path / "x").art == fortschritt.BELEGT
    assert fortschritt.wache_fuer_verzeichnis(tmp_path).art == fortschritt.BELEGT
    assert fortschritt.wache_fuer_status().art == fortschritt.BEHAUPTET


# ======================================================================================
# Aufsetzen
# ======================================================================================

@pytest.mark.parametrize("frist, muster", [
    (0, "positiv"),
    (-5, "positiv"),
    (float("inf"), "endlich"),
    ("lang", "keine Zahl"),
])
def test_unbrauchbare_frist_wird_abgewiesen(frist, muster):
    with pytest.raises(fortschritt.FortschrittsError, match=muster):
        fortschritt.Wache(frist_s=frist)


def test_geratene_art_wird_abgewiesen():
    with pytest.raises(fortschritt.FortschrittsError, match="erlaubt sind"):
        fortschritt.Wache(art="vielleicht")


def test_vorgabefrist_ist_die_des_altbestands():
    """Nicht weil sie gemessen wäre, sondern damit ein Vergleich möglich bleibt."""
    assert fortschritt.FRIST_S == 300.0
    assert fortschritt.Wache().frist_s == 300.0


def test_vorgabeart_ist_die_vorsichtige():
    """Wer nichts sagt, bekommt die Art, die nicht verurteilen darf."""
    assert fortschritt.Wache().art == fortschritt.BEHAUPTET


# ======================================================================================
# Angeschlossen: der überwachte Starter in seams.py
# ======================================================================================

class Prozessattrappe:
    """Ein Subprozess, der nach `laeuft_blicke` Blicken fertig ist — oder nie."""

    def __init__(self, *, laeuft_blicke: int | None = 2, code: int = 0):
        self._rest = laeuft_blicke
        self._code = code
        self.returncode = None
        self.getoetet = False

    def poll(self):
        if self._rest is None:
            return None
        if self._rest > 0:
            self._rest -= 1
            return None
        self.returncode = self._code
        return self._code

    def kill(self):
        self.getoetet = True
        self.returncode = -9

    def wait(self):
        return self.returncode


class Strom:
    """Ein Ausgabestrom, der eine feste Bytefolge liefert und dann endet."""

    def __init__(self, inhalt: bytes = b""):
        self._rest = bytearray(inhalt)
        self.zu = False

    def read(self, n: int = 1) -> bytes:
        if not self._rest:
            return b""
        heraus = bytes(self._rest[:n])
        del self._rest[:n]
        return heraus

    def close(self):
        self.zu = True


def _popen_attrappe(prozess, *, ausgabe: bytes = b"blender sagt etwas\n"):
    """Ein Popen-Ersatz. Seit dem 20.08. laufen die Ströme über PIPE und einen Faden,
    der sie laufend in eine Datei giesst — siehe `seams._giesse`."""
    def oeffne(cmd, stdout=None, stderr=None):
        prozess.stdout = Strom(ausgabe)
        prozess.stderr = Strom(b"")
        return prozess
    return oeffne


def test_ueberwachter_starter_gibt_einen_completedprocess_zurueck(tmp_path):
    from aiimaging import seams
    uhr = Uhr()
    ziel = tmp_path / "wachsend.exr"
    ziel.write_bytes(b"x")
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    starte = seams.starter_mit_wache(wache, takt_s=1, _schlaf=lambda s: uhr.weiter(s),
                                     _popen=_popen_attrappe(Prozessattrappe()), _uhr=uhr)
    ergebnis = starte(["blender"], 900)
    assert ergebnis.returncode == 0
    assert "blender sagt etwas" in ergebnis.stdout
    assert ergebnis.stderr == ""


def test_ueberwachter_starter_bricht_bei_belegtem_stillstand_ab(tmp_path):
    """Der Fall, für den das ganze Modul da ist: Der Prozess lebt, die Datei wächst nicht."""
    from aiimaging import seams
    uhr = Uhr()
    ziel = tmp_path / "steht.exr"
    ziel.write_bytes(b"x")
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    prozess = Prozessattrappe(laeuft_blicke=None)          # wird nie fertig
    starte = seams.starter_mit_wache(wache, takt_s=30, _schlaf=lambda s: uhr.weiter(s),
                                     _popen=_popen_attrappe(prozess), _uhr=uhr)
    with pytest.raises(seams.SeamError, match="Stillstand"):
        starte(["blender"], 1800)
    assert prozess.getoetet, "ein hängender Prozess muss auch wirklich beendet werden"


def test_der_abbruch_sagt_wieviel_frueher_er_kam_als_der_gesamt_timeout(tmp_path):
    from aiimaging import seams
    uhr = Uhr()
    ziel = tmp_path / "steht.exr"
    ziel.write_bytes(b"x")
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    starte = seams.starter_mit_wache(
        wache, takt_s=30, _schlaf=lambda s: uhr.weiter(s),
        _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=None)), _uhr=uhr)
    with pytest.raises(seams.SeamError) as fehler:
        starte(["blender"], 1800)
    assert "Gesamt-Timeout (1800 s)" in str(fehler.value)


def test_eine_wachsende_datei_haelt_den_lauf_am_leben(tmp_path):
    """Ein langsamer, aber gesunder Lauf darf nicht abgebrochen werden."""
    from aiimaging import seams
    uhr = Uhr()
    ziel = tmp_path / "waechst.exr"
    ziel.write_bytes(b"x")
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    groesse = [1]

    def schlaf(s):
        uhr.weiter(s)
        groesse[0] += 1
        ziel.write_bytes(b"x" * groesse[0])

    starte = seams.starter_mit_wache(
        wache, takt_s=60, _schlaf=schlaf,
        _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=20)), _uhr=uhr)
    ergebnis = starte(["blender"], 1800)
    assert ergebnis.returncode == 0
    assert uhr.t >= 1200, "der Lauf lief über 20 Minuten — und wurde nicht abgebrochen"


def test_der_gesamt_timeout_bleibt_daneben_bestehen(tmp_path):
    """Er fängt den Fall, den keine Wache fängt: stetiger Fortschritt, trotzdem zu lang."""
    from aiimaging import seams
    import subprocess as sp
    uhr = Uhr()
    ziel = tmp_path / "waechst.exr"
    ziel.write_bytes(b"x")
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=100, _uhr=uhr)
    groesse = [1]

    def schlaf(s):
        uhr.weiter(s)
        groesse[0] += 1
        ziel.write_bytes(b"x" * groesse[0])

    prozess = Prozessattrappe(laeuft_blicke=None)
    starte = seams.starter_mit_wache(wache, takt_s=60, _schlaf=schlaf,
                                     _popen=_popen_attrappe(prozess), _uhr=uhr)
    with pytest.raises(sp.TimeoutExpired):
        starte(["blender"], 300)
    assert prozess.getoetet


def test_eine_statuswache_taugt_hier_nicht_und_sagt_es(tmp_path):
    """Ein Subprozess sagt uns von sich aus nichts — ein erfundenes Statuswort wäre
    genau der Selbstbetrug, gegen den dieses Modul gebaut ist."""
    from aiimaging import seams
    starte = seams.starter_mit_wache(
        fortschritt.wache_fuer_status(frist_s=10), takt_s=1,
        _schlaf=lambda s: None,
        _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=None)))
    with pytest.raises(fortschritt.FortschrittsError, match="keine eigene Zeichenquelle"):
        starte(["blender"], 60)


def test_ein_fertiger_prozess_wird_gar_nicht_erst_ueberwacht(tmp_path):
    """Wer sofort fertig ist, soll nicht an einer Wache scheitern, die nie greifen kann."""
    from aiimaging import seams
    uhr = Uhr()
    ziel = tmp_path / "fehlt.exr"          # gibt es nie → Marke ist immer None
    wache = fortschritt.wache_fuer_datei(ziel, frist_s=1, _uhr=uhr)
    uhr.weiter(10_000)                     # die Frist ist längst gerissen
    starte = seams.starter_mit_wache(wache, takt_s=1, _schlaf=lambda s: uhr.weiter(s),
                                     _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=0)),
                                     _uhr=uhr)
    assert starte(["blender"], 900).returncode == 0


def test_starter_wacht_ueber_seine_eigene_ausgabe_wenn_nur_eine_frist_kommt():
    """Henne-Ei: Die Ausgabedatei entsteht erst beim Start — eine von aussen gebaute
    Wache könnte ihren Pfad gar nicht kennen."""
    from aiimaging import seams
    prozess = Prozessattrappe(laeuft_blicke=3)
    starte = seams.starter_mit_wache(frist_s=100, takt_s=1, _schlaf=lambda s: None,
                                     _popen=_popen_attrappe(prozess))
    ergebnis = starte(["blender"], 900)
    assert ergebnis.returncode == 0
    assert "blender sagt etwas" in ergebnis.stdout


def test_stille_standardausgabe_gilt_als_stillstand():
    """Ein Prozess, der nichts mehr schreibt, ist der Fall, um den es geht."""
    from aiimaging import seams
    uhr = Uhr()

    def stumm(cmd, stdout=None, stderr=None):
        p = Prozessattrappe(laeuft_blicke=None)      # schreibt nie etwas
        p.stdout = Strom(b"")
        p.stderr = Strom(b"")
        return p

    starte = seams.starter_mit_wache(frist_s=100, takt_s=30,
                                     _schlaf=lambda s: uhr.weiter(s),
                                     _popen=stumm, _uhr=uhr)
    with pytest.raises(seams.SeamError, match="Stillstand"):
        starte(["blender"], 1800)


def test_jeder_lauf_bekommt_eine_frische_wache():
    """Eine wiederverwendete trüge die Stillstandsuhr des vorigen Laufs mit."""
    from aiimaging import seams
    uhr = Uhr()
    starte = seams.starter_mit_wache(frist_s=100, takt_s=1,
                                     _schlaf=lambda s: uhr.weiter(s), _uhr=uhr,
                                     _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=1)))
    assert starte(["a"], 900).returncode == 0
    uhr.weiter(10_000)                      # zwischen den Läufen vergeht viel Zeit
    assert starte(["b"], 900).returncode == 0, "der zweite Lauf darf davon nichts wissen"


def test_genau_eines_von_wache_und_frist():
    from aiimaging import seams
    with pytest.raises(seams.SeamError, match="GENAU EINES"):
        seams.starter_mit_wache()
    with pytest.raises(seams.SeamError, match="GENAU EINES"):
        seams.starter_mit_wache(fortschritt.wache_fuer_status(), frist_s=100)


def test_multipass_baut_fuer_blender_gar_keine_wache_mehr(monkeypatch, tmp_path):
    """Vorgabe war AUS; seit der GPU-Messung ist es eine Abweisung.

    Der Test hiess bis zum 20.08. „schaltet die Wache nur auf ausdrückliche Ansage" und
    prüfte, dass `stillstand_frist_s=120` einen Starter baut. Genau das wäre auf der
    HomeStation der Abbruch jedes Laufs über 122 Sekunden gewesen.
    """
    from aiimaging import seams
    gesehen = {}

    def merke(cmd, timeout):
        gesehen["cmd"] = cmd
        raise seams.SeamError("hier endet der Test — der Starter war die Frage")

    monkeypatch.setattr(seams, "_default_starte", merke)
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")
    gebaut = []
    monkeypatch.setattr(seams, "starter_mit_wache",
                        lambda *a, **k: gebaut.append(k) or merke)

    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP")
    assert gebaut == [], "ohne Ansage darf keine Wache gebaut werden"

    with pytest.raises(seams.SeamError, match="KEINEN zulässigen Wert"):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP", stillstand_frist_s=120)
    assert gebaut == [], ("seit der GPU-Messung wird die Wache für Blender gar nicht "
                          "mehr gebaut — es gibt keine tragende Frist")


def test_ein_eigener_starter_schlaegt_die_wache(monkeypatch, tmp_path):
    """Die Tests dieses Projekts reichen `_starte` herein — das muss weiter gelten."""
    from aiimaging import seams
    gebaut = []
    monkeypatch.setattr(seams, "starter_mit_wache", lambda *a, **k: gebaut.append(k))
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")

    def eigener(cmd, timeout):
        raise seams.SeamError("eigener Starter")

    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError, match="eigener Starter"):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP", stillstand_frist_s=120,
                               _starte=eigener)
    assert gebaut == []


# ======================================================================================
# Gemessen: Blenders Ausgabe hat einen Takt von 32 Sekunden
# ======================================================================================

@pytest.mark.parametrize("frist", [10, 96, 300, 100_000])
def test_fuer_blender_gibt_es_KEINE_zulaessige_frist(tmp_path, monkeypatch, frist):
    """Auf der GPU schweigt die Ausgabe 175 s am Stück (auf-20260820-18).

    Damit bricht jede Frist, die kürzer ist als der ganze Lauf, einen gesunden Lauf ab —
    und wie lange ein Lauf dauert, weiss man vorher nicht. Auch eine sehr grosse Frist
    ist keine Lösung: Sie wäre keine Wache, sondern ein zweiter Gesamt-Timeout.
    """
    from aiimaging import seams
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError, match="KEINEN zulässigen Wert"):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP", stillstand_frist_s=frist)


def test_die_abweisung_nennt_die_messung_und_nicht_nur_die_regel(tmp_path, monkeypatch):
    from aiimaging import seams
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError) as fehler:
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP", stillstand_frist_s=30)
    text = str(fehler.value)
    assert "1,0 s" in text and "175 Sekunden Stille" in text
    assert "kein langsamer Takt, sondern keiner" in text
    assert "ANDERE Quelle" in text, "die Meldung muss einen Ausweg nennen"


def test_ohne_frist_laeuft_der_multipass_unveraendert(tmp_path, monkeypatch):
    """Die Abweisung darf nur den einen Parameter treffen."""
    from aiimaging import seams
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")
    monkeypatch.setattr(seams, "_default_starte",
                        lambda cmd, timeout: (_ for _ in ()).throw(
                            seams.SeamError("normaler Weg")))
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError, match="normaler Weg"):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP")


def test_beide_messungen_stehen_als_zahl_im_code():
    """Damit niemand sie aus der Erinnerung neu erfindet — und damit sichtbar bleibt,
    dass die CPU-Zahl ein Artefakt war."""
    from aiimaging import seams
    assert seams.BLENDER_TAKT_S == 32.0, "CPU, Blender 4.2 — nicht übertragbar"
    assert seams.BLENDER_GPU_STILLE_S == 175.0, "GPU, Blender 5.2 LTS, OptiX"
    assert seams.BLENDER_GPU_STILLE_S > 5 * seams.BLENDER_TAKT_S


# ======================================================================================
# Echte Prozesse: die Blockade, gegen die der Faden gebaut ist
# ======================================================================================

def test_ein_sehr_gespraechiges_kind_blockiert_nicht(tmp_path):
    """Der Test, der die Bauform rechtfertigt.

    Ein Kind, das mehr schreibt, als in einen Pipe-Puffer passt (üblich 64 KB), bliebe
    stehen, wenn niemand liest — und zwar durch genau die Wache, die den Stillstand
    verhindern soll. Hier laufen 2 MB durch.
    """
    import sys as _sys
    from aiimaging import seams
    # Echte Uhr und echter Schlaf: Hier wird ein echter Prozess gemessen, und eine
    # gefälschte Uhr würde den Gesamt-Timeout sofort reissen.
    starte = seams.starter_mit_wache(frist_s=1000, takt_s=0.01)
    ergebnis = starte(
        [_sys.executable, "-c",
         "import sys\nfor i in range(20000): sys.stdout.write('x'*100 + '\\n')"],
        60)
    assert ergebnis.returncode == 0
    assert len(ergebnis.stdout) > 2_000_000


def test_die_ausgabe_eines_echten_prozesses_kommt_vollstaendig_an(tmp_path):
    import sys as _sys
    from aiimaging import seams
    starte = seams.starter_mit_wache(frist_s=1000, takt_s=0.01)
    ergebnis = starte(
        [_sys.executable, "-c",
         "import sys; sys.stdout.write('hallo'); sys.stderr.write('achtung')"], 60)
    assert ergebnis.stdout == "hallo"
    assert ergebnis.stderr == "achtung"


def test_ein_rueckgabewert_ungleich_null_kommt_durch():
    import sys as _sys
    from aiimaging import seams
    starte = seams.starter_mit_wache(frist_s=1000, takt_s=0.01)
    assert starte([_sys.executable, "-c", "raise SystemExit(3)"], 60).returncode == 3


# ======================================================================================
# Der Herzschlag — die einzige Quelle, die gemessen trägt
# ======================================================================================

def test_der_dateiname_ist_auf_beiden_seiten_derselbe():
    """Ein Dateiname, den zwei Seiten einer Prozessgrenze unabhängig raten, ist eine tote
    Kante mit Ansage."""
    from pathlib import Path as P
    from aiimaging import seams
    quelle = (P(seams.__file__).parent / "runners" / "blender_depth_stage.py").read_text(
        encoding="utf-8")
    assert f'HERZSCHLAG_DATEI = "{seams.HERZSCHLAG_DATEI}"' in quelle


def test_der_takt_kommt_beim_runner_an():
    """Ohne das Argument schriebe niemand den Herzschlag, auf den die Wache wartet —
    und die Wache bräche jeden Lauf ab."""
    from aiimaging import seams
    argumente = seams._multipass_argumente(
        "m.glb", "/tmp/aus", drehen=False, aufloesung=512, samples=16,
        beauty=True, material_id=True, herzschlag_takt_s=2.0)
    assert "--herzschlag-s" in argumente
    assert argumente[argumente.index("--herzschlag-s") + 1] == "2.0"


def test_ohne_takt_kein_argument():
    from aiimaging import seams
    argumente = seams._multipass_argumente(
        "m.glb", "/tmp/aus", drehen=False, aufloesung=512, samples=16,
        beauty=True, material_id=True)
    assert "--herzschlag-s" not in argumente


def test_die_frist_ist_ein_vielfaches_des_takts(tmp_path, monkeypatch):
    """Fünf ausgefallene Schläge, nicht einer: Ein Faden kann ins Hintertreffen geraten,
    ohne dass etwas kaputt ist."""
    from aiimaging import seams
    monkeypatch.setattr(seams, "finde_blender", lambda: "/bin/true")
    gebaut = {}

    def merke(wache=None, **kw):
        gebaut["frist"] = wache.frist_s
        gebaut["art"] = wache.art
        raise seams.SeamError("Wache gebaut")

    monkeypatch.setattr(seams, "starter_mit_wache", merke)
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(seams.SeamError, match="Wache gebaut"):
        seams.glb_zu_multipass(glb, tmp_path, up_axis="Y_UP", herzschlag_takt_s=2.0)
    assert gebaut["frist"] == 10.0 == seams.HERZSCHLAG_AUSFAELLE * 2.0
    assert gebaut["art"] == fortschritt.BELEGT


def test_die_frist_ist_neunzigmal_kuerzer_als_der_gesamt_timeout():
    from aiimaging import seams
    frist = seams.HERZSCHLAG_AUSFAELLE * seams.HERZSCHLAG_TAKT_S
    assert 900 / frist == 90.0


def test_ein_ausbleibender_herzschlag_bricht_ab(tmp_path):
    """Der Fall, für den das Ganze gebaut ist: Der Prozess lebt und schreibt nichts mehr."""
    from aiimaging import seams
    uhr = Uhr()
    schlag = tmp_path / seams.HERZSCHLAG_DATEI
    schlag.write_text("1 0.0\n", encoding="utf-8")
    wache = fortschritt.wache_fuer_datei(schlag, frist_s=10.0, _uhr=uhr)
    prozess = Prozessattrappe(laeuft_blicke=None)
    starte = seams.starter_mit_wache(wache, takt_s=2, _schlaf=lambda s: uhr.weiter(s),
                                     _popen=_popen_attrappe(prozess), _uhr=uhr)
    with pytest.raises(seams.SeamError, match="Stillstand"):
        starte(["blender"], 900)
    assert prozess.getoetet


def test_ein_schlagender_herzschlag_haelt_den_lauf_am_leben(tmp_path):
    from aiimaging import seams
    uhr = Uhr()
    schlag = tmp_path / seams.HERZSCHLAG_DATEI
    schlag.write_text("1 0.0\n", encoding="utf-8")
    wache = fortschritt.wache_fuer_datei(schlag, frist_s=10.0, _uhr=uhr)
    nummer = [1]

    def schlagen(s):
        uhr.weiter(s)
        nummer[0] += 1
        with open(schlag, "a", encoding="utf-8") as f:
            f.write(f"{nummer[0]} {uhr.t:.1f}\n")

    starte = seams.starter_mit_wache(
        wache, takt_s=2, _schlaf=schlagen, _uhr=uhr,
        _popen=_popen_attrappe(Prozessattrappe(laeuft_blicke=200)))
    assert starte(["blender"], 900).returncode == 0
    assert uhr.t >= 400, "der Lauf lief über sechs Minuten und wurde nicht abgebrochen"
