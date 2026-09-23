"""Der Lieferstatus — am Auftrag und je Kamera, über den Produktweg (Runde 9, 23.09.2026).

Der Befund
----------
KosmoOrbit hat in seinem Ergebnisvertrag seit dem 01.09.2026 ein Feld ``lieferstatus``
(``geliefert`` / ``uebersprungen`` / ``fehlgeschlagen``) mit ``lieferstatus_grund`` — am
AUFTRAG, mit der Vorgabe ``'geliefert'``. Niemand setzte es (Teilantwort auf
``auf-20260919-119``, V3/V4, übertragen am 23.09.2026). Jedes unserer Ergebnisse
behauptete damit drüben eine vollständige Lieferung, auch eines ohne Bild.

Gebraucht wird es JE KAMERA in ``qa_je_kamera[]``, mit ``bilder_soll`` und ``bilder_ist``
nebeneinander.

Was diese Datei bewacht
-----------------------
Die WIRKUNG in der Datei, die die fremde Warteschlange liest — ``bruecke.lies_auftrag``
→ ``abholer.hole_einen`` → ``abholer.verarbeiter`` mit Attrappen für Multipass und Render
(aus ``tests/test_kettenlauf_26august.py``) → ``bruecke.schreibe_ergebnis``:

1. ganz geliefert: drei Kameras, drei Bilder, alles ``geliefert``;
2. eine Kamera abgebrochen (über dem Dach): sie ``fehlgeschlagen``, der Auftrag auch;
3. alle abgebrochen (Rahmung): kein Bild, jede Kamera ``fehlgeschlagen`` mit dem Satz,
   den ``verdict.reason`` schon trägt;
4. Zwilling: ``uebersprungen``, 0 von 1 — ein Bild zählt nicht zweimal;
5. Blickfeld und Abbestellung;
6. die zweite Quelle (eigene Ablage) schreibt dieselben Felder.

Dazu die Regeln am Baustein ``kosmo_szene.als_ergebnis``: Was nicht stimmt, wird laut
abgewiesen; was nicht bekannt ist, steht als ``None`` da — nie als 0 und nie als
«geliefert».

Regel 3: alle Szenen, Kameras und Modelle sind synthetisch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, eigene_quelle, jobs, kosmo_szene, werkzeuge

import test_abholer
from test_kettenlauf_26august import _auftragsordner, _kamerablock, _kette, _lauf

GELIEFERT = kosmo_szene.LIEFERSTATUS_GELIEFERT
UEBERSPRUNGEN = kosmo_szene.LIEFERSTATUS_UEBERSPRUNGEN
FEHLGESCHLAGEN = kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN


def _vertrag(tmp_path, **kette) -> dict:
    """Ein Auftrag (``cameras: auto`` = s, sSE, nNW) durch den Produktweg; zurück kommt
    die GESCHRIEBENE Datei, nicht ein Rückgabewert."""
    skip = kette.pop("skip", False)
    ordner = _auftragsordner(tmp_path, skip=skip)
    _protokoll, attrappen = _kette(tmp_path, **kette)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def _je(vertrag) -> dict:
    return {e["kamera"]: e for e in vertrag.get("qa_je_kamera", ())}


def _summe_stimmt(vertrag) -> None:
    """Die Summe der Bilder je Kamera ist die Bildliste — sonst zählt etwas doppelt."""
    ist = [e["bilder_ist"] for e in vertrag["qa_je_kamera"]]
    assert sum(ist) == len(vertrag["images"]), (ist, vertrag["images"])


# ======================================================================================
# 1 · Über den Produktweg
# ======================================================================================

def test_ganz_geliefert_heisst_jede_kamera_ein_bild_von_einem(tmp_path):
    vertrag = _vertrag(tmp_path)

    assert len(vertrag["images"]) == 3, "Vorbedingung: drei Kameras, drei Bilder"
    assert vertrag["lieferstatus"] == GELIEFERT
    assert vertrag["lieferstatus_grund"] == ""
    for name, e in _je(vertrag).items():
        assert (e["lieferstatus"], e["bilder_soll"], e["bilder_ist"]) == (
            GELIEFERT, 1, 1), name
        assert e["lieferstatus_grund"] == ""
    _summe_stimmt(vertrag)


def test_eine_abgebrochene_kamera_macht_den_auftrag_nicht_geliefert(tmp_path):
    """Die Kamera ``sSE`` steht über dem Dach — abgebrochen VOR dem Render. Zwei Bilder
    kommen, eines nicht: Der Auftrag darf nicht «geliefert» heissen."""
    def hoch(kuerzel):
        block = _kamerablock(kuerzel)
        return dict(block, auge=[0.0, -30.0, 77.0]) if kuerzel == "sSE" else block

    vertrag = _vertrag(tmp_path, kamerablock=hoch)
    je = _je(vertrag)

    assert len(vertrag["images"]) == 2, "Vorbedingung: eine Kamera nicht gerendert"
    assert (je["sSE"]["lieferstatus"], je["sSE"]["bilder_soll"],
            je["sSE"]["bilder_ist"]) == (FEHLGESCHLAGEN, 1, 0)
    assert "ueber dem Dach" in je["sSE"]["lieferstatus_grund"]
    assert je["s"]["lieferstatus"] == je["nNW"]["lieferstatus"] == GELIEFERT
    assert vertrag["lieferstatus"] == FEHLGESCHLAGEN
    grund = vertrag["lieferstatus_grund"]
    assert grund.startswith("2 von 3 Kameras geliefert, 2 von 3 Bildern"), grund
    # Der Grund der Kamera steht auch am Auftrag — er kommt drüben heute schon an,
    # die Felder je Kamera erst, wenn sie gebaut sind.
    assert je["sSE"]["lieferstatus_grund"] in grund
    _summe_stimmt(vertrag)


def test_alle_abgebrochen_traegt_je_kamera_den_satz_aus_dem_vertragsgrund(tmp_path):
    """Rahmung zu weit bei allen drei Kameras: kein Bild. Der Grund je Kamera ist
    DERSELBE Satz, den ``verdict.reason`` für die Gruppe trägt — ein Wortlaut."""
    vertrag = _vertrag(tmp_path, bbox_bauwerk=[[0, 0, 0], [1.0, 1.0, 1.0]])

    assert vertrag["images"] == []
    assert vertrag["lieferstatus"] == FEHLGESCHLAGEN
    assert vertrag["lieferstatus_grund"].startswith("0 von 3 Kameras geliefert, 0 von 3")
    gruppe = next(t for t in vertrag["qa"]["verdict"]["reason"].split("; ")
                  if t.startswith("NICHT GERENDERT (Rahmung), s, sSE, nNW: "))
    for name, e in _je(vertrag).items():
        assert (e["lieferstatus"], e["bilder_soll"], e["bilder_ist"]) == (
            FEHLGESCHLAGEN, 1, 0), name
        kopf = f"NICHT GERENDERT (Rahmung), {name}: "
        assert e["lieferstatus_grund"].startswith(kopf), e["lieferstatus_grund"]
        assert e["lieferstatus_grund"][len(kopf):] == gruppe.split(": ", 1)[1]
    _summe_stimmt(vertrag)


def test_der_zwilling_ist_uebersprungen_und_zaehlt_kein_bild(tmp_path):
    """Drei gleiche Soll-Karten: ``s`` wird gerendert, ``sSE`` und ``nNW`` übernehmen
    Bild und Urteil (``doppelt_von``). Der Zwilling trägt das ``bild_png`` seines
    Vorbilds — als «geliefert» gezählt, stünden drei Bilder da, wo eines ist."""
    vertrag = _vertrag(tmp_path, karten=[[[1.0]]] * 5)
    je = _je(vertrag)

    assert vertrag["images"] == ["s.png"], "Vorbedingung: einmal gerendert"
    assert (je["s"]["lieferstatus"], je["s"]["bilder_ist"]) == (GELIEFERT, 1)
    for name in ("sSE", "nNW"):
        assert (je[name]["lieferstatus"], je[name]["bilder_soll"],
                je[name]["bilder_ist"]) == (UEBERSPRUNGEN, 1, 0), name
        assert "wie Kamera 's'" in je[name]["lieferstatus_grund"]
    # ENTSCHEID 23.09.2026: Bilder kamen, und die Ansicht der Zwillinge ist mit dem Bild
    # ihres Vorbilds geliefert — am Auftrag «geliefert», MIT Grund, der die Zwillinge nennt.
    # «uebersprungen» hiesse drueben «fand insgesamt nicht statt».
    assert vertrag["lieferstatus"] == GELIEFERT
    assert vertrag["lieferstatus_grund"].startswith("1 von 3 Kameras geliefert")
    _summe_stimmt(vertrag)


def test_eine_kamera_die_vorbeischaut_ist_fehlgeschlagen_und_nicht_gerahmt(tmp_path):
    """Blickfeld vor Rahmung: ``nNW`` schaut von der Szene weg."""
    def weg(kuerzel):
        block = _kamerablock(kuerzel)
        return dict(block, blick_auf=[0.0, -60.0, 1.70]) if kuerzel == "nNW" else block

    vertrag = _vertrag(tmp_path, kamerablock=weg)
    je = _je(vertrag)

    assert je["nNW"]["lieferstatus"] == FEHLGESCHLAGEN
    assert je["nNW"]["lieferstatus_grund"].startswith(
        "NICHT GERENDERT (Kamera schaut an der Szene vorbei), nNW")
    assert "Rahmung" not in je["nNW"]["lieferstatus_grund"]
    assert vertrag["lieferstatus"] == FEHLGESCHLAGEN
    _summe_stimmt(vertrag)


def test_ein_abbestellter_auftrag_ist_uebersprungen_und_nicht_geliefert(tmp_path):
    """Der Wert, für den ihr ``uebersprungen`` gebaut wurde (erg-20260917-37 F3)."""
    vertrag = _vertrag(tmp_path, skip=True)

    assert vertrag["images"] == []
    assert vertrag["lieferstatus"] == UEBERSPRUNGEN
    assert "skip: true" in vertrag["lieferstatus_grund"]
    assert "qa_je_kamera" not in vertrag, "abbestellt: keine Kamera gerechnet"


def test_die_eigene_ablage_schreibt_dieselben_felder(tmp_path, monkeypatch):
    """Der zweite Weg: ein über den MCP-Einlass bestellter Auftrag, geschrieben über
    ``eigene_quelle.schreibe_ergebnis``."""
    ablage = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ablage))
    glb = tmp_path / "modell.glb"
    glb.write_bytes(test_abholer._minimale_glb())
    bestellt = werkzeuge.enqueue_render({
        "glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
        "out_dir": str(tmp_path / "out"), "approval_token": jobs.TOKEN_PRAEFIX + "TEST"})
    assert bestellt["error"] is None, bestellt

    _, attrappen = test_abholer._kette()
    bericht = abholer.durchgang(
        ablage, quelle=eigene_quelle, darf_rechnen=lambda: (True, "frei"),
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]

    datei = ablage / bestellt["job_id"] / eigene_quelle.DATEI_ERGEBNIS
    vertrag = json.loads(datei.read_text(encoding="utf-8"))
    assert vertrag["lieferstatus"] == GELIEFERT
    assert vertrag["qa_je_kamera"], "Vorbedingung: Kameras im Ergebnis"
    for e in vertrag["qa_je_kamera"]:
        assert (e["lieferstatus"], e["bilder_soll"], e["bilder_ist"]) == (GELIEFERT, 1, 1)
    _summe_stimmt(vertrag)


# ======================================================================================
# 2 · Die Regeln am Baustein — was nicht stimmt, wird abgewiesen
# ======================================================================================

def _kamera(**felder) -> dict:
    return dict({"kamera": "k"}, **felder)


@pytest.mark.parametrize("felder, teil", [
    ({"lieferstatus": GELIEFERT, "lieferstatus_grund": "", "bilder_soll": 1,
      "bilder_ist": 0}, "'geliefert' bei"),
    ({"lieferstatus": GELIEFERT, "lieferstatus_grund": "", "bilder_soll": 0,
      "bilder_ist": 0}, "'geliefert' bei"),
    ({"lieferstatus": FEHLGESCHLAGEN, "lieferstatus_grund": "x", "bilder_soll": 1,
      "bilder_ist": 1}, "in der anderen Richtung"),
    ({"lieferstatus": FEHLGESCHLAGEN, "lieferstatus_grund": " ", "bilder_soll": 1,
      "bilder_ist": 0}, "ohne lieferstatus_grund"),
    ({"lieferstatus": "teilweise", "lieferstatus_grund": "x", "bilder_soll": 1,
      "bilder_ist": 0}, "keiner der drei Werte"),
    ({"lieferstatus": FEHLGESCHLAGEN, "lieferstatus_grund": "x", "bilder_soll": True,
      "bilder_ist": 0}, "ganze Zahl ab 0"),
    ({"lieferstatus": FEHLGESCHLAGEN, "lieferstatus_grund": "x", "bilder_soll": 1,
      "bilder_ist": 0.0}, "ganze Zahl ab 0"),
])
def test_eine_widerspruechliche_lieferung_wird_abgewiesen(felder, teil):
    with pytest.raises(kosmo_szene.SzenenError, match=teil):
        kosmo_szene.als_ergebnis("vis-1-abcdef", [], je_kamera=[_kamera(**felder)])


def test_eine_unbekannte_bilderzahl_bleibt_none_und_wird_keine_null():
    """Die dritte Antwort: ``bilder_soll: None`` heisst nicht gezählt."""
    erg = kosmo_szene.als_ergebnis("vis-1-abcdef", [], je_kamera=[_kamera(
        lieferstatus=FEHLGESCHLAGEN, lieferstatus_grund="kein Bild",
        bilder_soll=None, bilder_ist=0)])

    e = erg["qa_je_kamera"][0]
    assert e["bilder_soll"] is None and e["bilder_ist"] == 0
    assert erg["lieferstatus"] == FEHLGESCHLAGEN
    assert "0 von unbekannt Bildern" in erg["lieferstatus_grund"]


def test_ohne_meldung_je_kamera_ist_der_auftrag_nicht_festgestellt():
    """Kein Aufrufer, der nichts sagt, bekommt «geliefert» — sondern ``None``."""
    ohne = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"])
    assert ohne["lieferstatus"] is None
    assert ohne["lieferstatus_grund"].startswith("NICHT FESTGESTELLT")

    halb = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], je_kamera=[
        _kamera(kamera="a", lieferstatus=GELIEFERT, lieferstatus_grund="",
                bilder_soll=1, bilder_ist=1),
        {"kamera": "b"}])
    assert halb["lieferstatus"] is None, "eine Kamera ohne Meldung"
    assert "1 von 2 Kameras" in halb["lieferstatus_grund"]
    assert "lieferstatus" not in halb["qa_je_kamera"][1], (
        "ohne Meldung fehlen die Felder — keine erfundenen Werte")


def test_eine_bilderzahl_die_nicht_zur_bildliste_passt_ist_nicht_festgestellt():
    """Zwei Zahlen für dieselbe Lieferung: Die Kameras melden ein Bild, die Liste trägt
    zwei. «geliefert» wäre hier eine von beiden Zahlen geglaubt."""
    erg = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"], je_kamera=[
        _kamera(lieferstatus=GELIEFERT, lieferstatus_grund="", bilder_soll=1,
                bilder_ist=1)])

    assert erg["lieferstatus"] is None
    assert "Die Kameras melden 1 Bild(er), die Bildliste traegt 2" in (
        erg["lieferstatus_grund"])


def test_die_felder_ueberleben_die_strikte_fassung():
    """``nur_vertragsfelder`` streicht nur ``hinweise`` — der Lieferstatus ist ein Feld
    IHRES Vertrags und muss die Datei erreichen."""
    erg = kosmo_szene.nur_vertragsfelder(kosmo_szene.als_ergebnis(
        "vis-1-abcdef", ["a.png"], je_kamera=[_kamera(
            lieferstatus=GELIEFERT, lieferstatus_grund="", bilder_soll=1,
            bilder_ist=1)]))

    assert erg["lieferstatus"] == GELIEFERT
    assert set(kosmo_szene.FELDER_LIEFERUNG) <= set(erg["qa_je_kamera"][0])


def test_ein_kamerabild_ohne_benannten_grund_ist_fehlgeschlagen_nicht_geliefert():
    """Der Rückfall, den der Produktweg heute nicht erreicht: kein Bild, kein Zwilling,
    kein Abbruch. Er darf nicht still als geliefert durchgehen."""
    lieferung = abholer._lieferung_der_kamera(
        {"kamera": "x", "bild_png": None, "grund": "Etwas anderes."})

    assert lieferung["lieferstatus"] == FEHLGESCHLAGEN
    assert (lieferung["bilder_soll"], lieferung["bilder_ist"]) == (1, 0)
    assert "Etwas anderes." in lieferung["lieferstatus_grund"]


def test_ein_urteil_ohne_namen_bekommt_auch_keine_lieferung():
    """Dieselbe Auswahl wie ``_qa_je_kamera_eintraege``: kein Name, kein Eintrag."""
    assert abholer._je_kamera_mit_lieferung(
        [{"bild_png": Path("a.png").name}, "kaputt"]) == []


# ── Die Rangfolge am Auftrag (Durchsicht der Runde 9, 23.09.2026) ─────────────────────
#
# Die Durchsicht vertauschte die Rangfolge (uebersprungen vor fehlgeschlagen) und schaltete
# den Zweig «nicht festgestellt» ab — beide Male blieb alles gruen. Diese Proben halten die
# Regel an der Funktion, die den Auftrag einstuft; der Produktweg (Zwilling) steht oben.

def _lieferzeile(name, status, soll=1, ist=None, grund="Grund."):
    ist = (1 if status == GELIEFERT else 0) if ist is None else ist
    return {"kamera": name, "lieferstatus": status, "bilder_soll": soll, "bilder_ist": ist,
            "lieferstatus_grund": "" if status == GELIEFERT else grund}


def test_fehlgeschlagen_geht_vor_uebersprungen_am_auftrag():
    from aiimaging import kosmo_szene as ks
    saetze = [_lieferzeile("a", GELIEFERT), _lieferzeile("b", UEBERSPRUNGEN, grund="wie Kamera 'a'"),
              _lieferzeile("c", FEHLGESCHLAGEN, grund="ueber dem Dach")]
    status, grund = ks._lieferstatus_des_auftrags(saetze, uebersprungen=False,
                                                  anzahl_bilder=1)
    assert status == FEHLGESCHLAGEN, (status, grund)
    assert "ueber dem Dach" in grund


def test_nur_uebersprungen_ohne_bild_heisst_uebersprungen():
    from aiimaging import kosmo_szene as ks
    saetze = [_lieferzeile("a", UEBERSPRUNGEN), _lieferzeile("b", UEBERSPRUNGEN)]
    status, _ = ks._lieferstatus_des_auftrags(saetze, uebersprungen=False, anzahl_bilder=0)
    assert status == UEBERSPRUNGEN


def test_eine_nicht_festgestellte_kamera_macht_den_auftrag_nicht_festgestellt():
    from aiimaging import kosmo_szene as ks
    saetze = [_lieferzeile("a", GELIEFERT), dict(_lieferzeile("b", GELIEFERT), lieferstatus=None)]
    status, grund = ks._lieferstatus_des_auftrags(saetze, uebersprungen=False,
                                                  anzahl_bilder=1)
    assert status is None, (status, grund)
    assert grund.startswith("NICHT FESTGESTELLT") and "'b'" in grund

