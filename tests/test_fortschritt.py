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
