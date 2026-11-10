"""«Freie Sicht aufs Haus» (A0306): Heranziehen und Rahmen in einem Ablauf.

**Die Lage vorher.** ``kameras.ziehe_bis_frei`` rechnete seit Wochen die Schritte, mit
denen eine Kamera an einem Nachbarbau vorbei näher ans Haus rückt, und hatte keinen
Aufrufer (``docs/PLAN.md``: «Verdeckung wird auf dem Produktpfad nicht behandelt»). Die
Gegenrichtung, ``schiebe_bis_im_bild``, lief. Wer die zwei hintereinander schaltet, lässt
sie gegeneinander ziehen.

**Die Zielfunktion** (Auftrag A0306): Auf mindestens 40 erfundenen Szenen der Anteil der
lösbaren Fälle, in denen die fertige Kamera freie Sicht hat UND das Haus die Rahmungsregel
hält. Ziel 100 %, unlösbare Fälle gemeldet, Fälle ohne Verdeckung unverändert.

Satz, Erzeuger und Prüfmass stehen in ``tests/sichtszenen.py``. Das Prüfmass rechnet mit
einem eigenen Strahlentest, einer eigenen Projektion und einer eigenen, feineren Suche;
gemeinsam mit der Lösung hat es nur den Massstab, den der Auftrag nennt.
"""
from __future__ import annotations

import math
import random
import re
from pathlib import Path

import pytest

import sichtszenen as sz
from aiimaging import kameras, kosmo_szene, sichtstrahl

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")


def _satz_mit_sicht(fall):
    szene = fall["szene"]
    return kameras.kamerasatz(szene["haus"], kuerzel=[fall["kuerzel"]],
                              sicht_frei=sichtstrahl.pruefer(szene["nachbarn"]))


def _mit_sicht(fall):
    return _satz_mit_sicht(fall)["kameras"][0]


@pytest.fixture(scope="module")
def heute():
    """Der Stand vor A0306: ``kamerasatz`` ohne Sichtprüfung."""
    return sz.messe(None)


@pytest.fixture(scope="module")
def neu():
    """Der eine Ablauf: ``kamerasatz`` mit Sichtprüfung."""
    return sz.messe(_mit_sicht)


# --------------------------------------------------------------------------------------
# Fertig-Satz 1: der Satz, sein Erzeuger, der heutige Wert
# --------------------------------------------------------------------------------------

def test_der_satz_hat_mindestens_vierzig_szenen_aus_acht_richtungen():
    szenen = sz.szenen()
    assert len(szenen) >= 40
    assert len(sz.RICHTUNGEN) == 8 and set(sz.RICHTUNGEN) <= set(kameras.RICHTUNGSFOLGE)
    assert len(sz.faelle()) == len(szenen) * 8
    for szene in szenen:
        assert 1 <= len(szene["nachbarn"]) <= 5, szene["name"]
    # Wechselnder Abstand und wechselnde Höhe, nicht fünfmal derselbe Bau.
    hoehen = sorted(n["z"][1] - n["z"][0] for s in szenen for n in s["nachbarn"])
    assert hoehen[0] < 4.0 and hoehen[-1] > 18.0
    assert any(n["drehung_grad"] for s in szenen for n in s["nachbarn"])


def test_der_erzeuger_liefert_jedes_mal_denselben_satz():
    assert sz.szenen() == sz.szenen()


def test_kein_nachbarbau_steht_im_haus():
    """Sonst wäre «verdeckt» keine Frage der Sicht, sondern ein Fehler des Erzeugers."""
    for szene in sz.szenen():
        (x0, y0, z0), (x1, y1, z1) = szene["haus"]
        ecken = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0 + 0.1, z1)]
        mitte = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        for nachbar in szene["nachbarn"]:
            assert not any(sichtstrahl.punkt_im_koerper(p, nachbar)
                           for p in ecken + [mitte]), szene["name"]


def test_alle_drei_klassen_sind_im_satz(heute):
    """Lösbare, unlösbare und von Anfang an freie Fälle, wie der Auftrag sie verlangt."""
    zahl = heute["zahl"]
    assert zahl["loesbar"] >= 60, zahl
    assert zahl["unloesbar"] >= 30, zahl
    assert zahl["frei"] >= 100, zahl
    assert sum(zahl.values()) == heute["faelle"] == 384
    # Grenzfälle (ein Standpunkt nur auf der Messerschneide) zählen weder als lösbar noch
    # als unlösbar. Sie dürfen vorkommen, aber nicht das Ergebnis tragen.
    assert zahl["grenzfall"] <= 3, zahl


def test_loesung_und_pruefmass_meinen_denselben_spielraum():
    """Die Lösung sagt zu: ein Wegstück ab zwei Feinschritten findet sie immer, eines unter
    einem Feinschritt nie. Das Prüfmass nennt genau diese Grenzen lösbar und unlösbar
    (je mit einem Zentimeter Zugabe für sein eigenes Raster)."""
    assert sz.LOESBAR_AB_M == pytest.approx(2 * kameras.ZIEH_FEINSCHRITT_M + sz.PRUEFSCHRITT_M)
    assert sz.UNLOESBAR_UNTER_M == pytest.approx(kameras.ZIEH_FEINSCHRITT_M - sz.PRUEFSCHRITT_M)
    assert sz.PRUEFSCHRITT_M < kameras.ZIEH_FEINSCHRITT_M


def test_heute_ist_kein_einziger_verdeckter_fall_frei(heute):
    """**Der gemessene Ausgangswert: 0 %.** Die Regel wurde nicht aufgerufen, also steht
    jede Kamera, vor der ein Nachbarbau steht, weiter hinter ihm."""
    assert heute["erreicht"]["loesbar"] == 0
    assert heute["anteil_loesbar"] == 0.0
    # Und wo nichts verdeckt, hält die heutige Kamera die Rahmungsregel: Der Satz misst
    # die Verdeckung, nicht eine schon vorher kaputte Rahmung.
    assert heute["erreicht"]["frei"] == heute["zahl"]["frei"]


def test_die_alte_schaltung_zieht_gegeneinander(heute):
    """Erst ``ziehe_bis_frei``, dann ``schiebe_bis_im_bild``, mit fester Brennweite:
    **gemessen** löst das weniger als die Hälfte, und in einem Teil der Fälle schiebt der
    Eckentest die eben frei gestellte Kamera wieder hinter den Nachbarbau."""
    geloest = zurueck_ins_verdeckte = 0
    verdeckte = [(f, u) for f, u in heute["einzeln"] if u["klasse"] == "loesbar"]
    for fall, _urteil in verdeckte:
        alt = sz.nacheinander(fall)
        haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
        frei = sz.sicht_ist_frei(alt["kamera"]["auge"], haus, nachbarn)
        geloest += frei and sz.rahmung_haelt(alt["kamera"], haus)
        zurueck_ins_verdeckte += alt["gezogen_frei"] and alt["zurueckgeschoben"] and not frei
    assert geloest < len(verdeckte) / 2, (geloest, len(verdeckte))
    assert zurueck_ins_verdeckte >= 1, "Das Gegeneinander ist im Satz nicht mehr zu sehen."


# --------------------------------------------------------------------------------------
# Fertig-Satz 3: der Zielwert
# --------------------------------------------------------------------------------------

def test_ZIEL_alle_loesbaren_faelle_sind_frei_und_richtig_gerahmt(neu):
    verfehlt = [(f["szene"]["name"], f["kuerzel"], u["frei"], u["gerahmt"])
                for f, u in neu["einzeln"] if u["klasse"] == "loesbar" and not u["erreicht"]]
    assert not verfehlt, verfehlt
    assert neu["anteil_loesbar"] == 1.0
    assert neu["anteil_mit_freien"] == 1.0


def test_unloesbare_faelle_tragen_einen_vermerk_statt_still_verdeckt_zu_sein(neu):
    unloesbare = [(f, u) for f, u in neu["einzeln"] if u["klasse"] == "unloesbar"]
    assert unloesbare
    for fall, urteil in unloesbare:
        kamera = urteil["kamera"]
        sicht = kamera["sicht"]
        wo = (fall["szene"]["name"], fall["kuerzel"])
        assert sicht["frei"] is False and sicht["bewegt"] is False, wo
        assert sicht["abbruch"] == "kein_freier_standpunkt", wo
        assert sicht["vermerk"].startswith("VERDECKT"), wo
        assert sicht["vermerk"] in kamera["warnungen"], wo
        # Die Kamera bleibt, wo sie gerechnet war: kein halb herangezogener Standpunkt.
        assert kamera["auge"] == urteil["basis"]["auge"], wo
        assert kamera["brennweite_mm"] == urteil["basis"]["brennweite_mm"], wo
    fall = unloesbare[0][0]
    satz = _satz_mit_sicht(fall)
    assert satz["verdeckt"] == [fall["kuerzel"]]
    assert any(w.startswith(f"{fall['kuerzel']}: VERDECKT") for w in satz["warnungen"])


def test_kein_unloesbarer_fall_wird_als_frei_ausgegeben(neu):
    """Die Gegenrichtung: Die Lösung darf nichts «lösen», was das Prüfmass für unlösbar
    hält. Sonst hätte sie einen Standpunkt ausserhalb der Regeln gefunden."""
    assert neu["erreicht"]["unloesbar"] == 0


# --------------------------------------------------------------------------------------
# Fertig-Satz 2: ein Ablauf, und ohne Verdeckung dieselbe Kamera
# --------------------------------------------------------------------------------------

def test_ohne_verdeckung_bleibt_die_kamera_zahl_fuer_zahl_dieselbe(neu):
    freie = [(f, u) for f, u in neu["einzeln"] if u["klasse"] == "frei"]
    assert freie
    for fall, urteil in freie:
        kamera = dict(urteil["kamera"])
        sicht = kamera.pop("sicht")
        assert kamera == urteil["basis"], (fall["szene"]["name"], fall["kuerzel"])
        assert sicht["frei"] is True and sicht["bewegt"] is False
        assert sicht["abbruch"] == "sicht_frei" and sicht["vermerk"] == ""


def test_ohne_sichtpruefung_ist_der_satz_schluessel_fuer_schluessel_der_alte():
    """Wer ``sicht_frei`` nicht hereinreicht, bekommt weder ``verdeckt`` noch ``sicht``:
    Kein bestehender Leser des Kamerasatzes sieht etwas Neues."""
    satz = kameras.kamerasatz(sz.szenen()[0]["haus"])
    assert "verdeckt" not in satz
    assert all("sicht" not in k for k in satz["kameras"])


def test_die_herangezogene_kamera_bleibt_auf_ihrem_weg(neu):
    """Näher, weiteres Objektiv, sonst nichts: gleiche Augenhöhe, gleiche Blickrichtung,
    gleiches Blickziel, Brennweite zwischen 24 mm und der bestellten."""
    gezogene = [(f, u) for f, u in neu["einzeln"] if u["klasse"] == "loesbar"]
    for fall, urteil in gezogene:
        kamera, basis = urteil["kamera"], urteil["basis"]
        wo = (fall["szene"]["name"], fall["kuerzel"])
        assert kamera["sicht"]["bewegt"] and kamera["sicht"]["abbruch"] == "herangezogen", wo
        assert kamera["auge"][2] == basis["auge"][2], wo
        assert kamera["blick_auf"][:2] == basis["blick_auf"][:2], wo
        assert kamera["abstand_m"] < basis["abstand_m"], wo
        assert kameras.ZIEH_BRENNWEITE_MIN_MM <= kamera["brennweite_mm"] <= basis["brennweite_mm"], wo
        vorher = [basis["auge"][i] - basis["blick_auf"][i] for i in range(2)]
        nachher = [kamera["auge"][i] - kamera["blick_auf"][i] for i in range(2)]
        kreuz = vorher[0] * nachher[1] - vorher[1] * nachher[0]
        assert abs(kreuz) < 1e-6 * basis["abstand_m"] ** 2, wo
        assert kamera["vollstaendig"] and kamera["fuellgrad"] >= kameras.BILDBREITE_ABBRUCH, wo
        # Der Bildausschnitt geht nicht verloren: nie kleiner als der Riegel, und solange
        # die Brennweite nicht an ihrer Grenze steht, so gross wie vorher.
        if kamera["brennweite_mm"] > kameras.ZIEH_BRENNWEITE_MIN_MM + 1e-6 \
                and kamera["fuellgrad"] < basis["fuellgrad"] - 1e-6:
            # Kleiner als vorher nur, wenn der Eckentest die Brennweite begrenzt hat.
            enger = kameras.rahmung_am_standpunkt(
                kamera["auge"], sz._ziel(fall["szene"]["haus"], kamera), fall["szene"]["haus"],
                azimut_grad=kamera["azimut_grad"],
                brennweite_mm=kamera["brennweite_mm"] * 1.01)
            assert not enger["ecken_passt"], wo
        assert kamera["begruendung"].startswith("HERANGEZOGEN"), wo
        assert kamera["sicht"]["vorher"]["verdeckte_punkte"] >= 1, wo


def test_die_feinsuche_findet_was_die_groben_schritte_ueberspringen(neu):
    """Die groben Schritte (12 % der Reststrecke) überspringen bei 40 m fast fünf Meter.
    Im Satz gibt es Fälle, die erst die Feinsuche löst; ohne sie stünden sie als verdeckt da."""
    fein = [u for _f, u in neu["einzeln"]
            if u["klasse"] == "loesbar" and u["kamera"]["sicht"]["feinsuche"]]
    assert fein, "Kein Fall im Satz braucht die Feinsuche; der Satz prüft sie nicht mehr."
    assert all(u["erreicht"] for u in fein)


def test_fester_abstand_wird_gemeldet_aber_nie_bewegt():
    """Ein bestellter Abstand gilt. Steht ein Nachbarbau davor, steht das im Ergebnis."""
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    mauer = sichtstrahl.quader((7.0, 30.0), 30.0, 4.0, 12.0, name="riegel")
    ohne = kameras.kamerasatz(haus, kuerzel=["n"], abstand_fest_m=45.0)["kameras"][0]
    mit = kameras.kamerasatz(haus, kuerzel=["n"], abstand_fest_m=45.0,
                             sicht_frei=sichtstrahl.pruefer([mauer]))
    kamera = mit["kameras"][0]
    assert kamera["auge"] == ohne["auge"] and kamera["brennweite_mm"] == ohne["brennweite_mm"]
    assert kamera["sicht"]["frei"] is False and kamera["sicht"]["bewegt"] is False
    assert kamera["sicht"]["abbruch"] == "nicht_nachgefuehrt"
    assert "Abstand ist bestellt" in kamera["sicht"]["vermerk"]
    assert kamera["sicht"]["vorher"]["verdeckt_durch"] == "riegel"
    assert mit["verdeckt"] == ["n"]


def test_ein_einzelfall_zum_nachrechnen():
    """Ein Haus, ein Nachbarbau kurz vor der Kamera: von Hand nachvollziehbar."""
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    basis = kameras.kamerasatz(haus, kuerzel=["s"])["kameras"][0]
    # Ein Bau 3 m vor der Kamera, auf ihrem Weg zum Haus.
    vor_der_kamera = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0),
                                        6.0, 4.0, 8.0, name="schuppen")
    satz = kameras.kamerasatz(haus, kuerzel=["s"],
                              sicht_frei=sichtstrahl.pruefer([vor_der_kamera]))
    kamera = satz["kameras"][0]
    assert satz["verdeckt"] == []
    assert kamera["sicht"]["frei"] is True and kamera["sicht"]["bewegt"] is True
    assert kamera["sicht"]["vorher"]["verdeckt_durch"] == "schuppen"
    # Die Kamera steht jetzt zwischen Schuppen und Haus, also mehr als 7 m näher.
    assert kamera["auge"][1] > basis["auge"][1] + 7.0
    assert kamera["brennweite_mm"] < basis["brennweite_mm"]
    assert abs(kamera["fuellgrad"] - basis["fuellgrad"]) < 1e-6
    assert sz.rahmung_haelt(kamera, haus)
    assert sz.sicht_ist_frei(kamera["auge"], haus, [vor_der_kamera])


def test_bestellt_mit_24_mm_gibt_es_kein_weiteres_objektiv():
    """Mit dem weitesten Objektiv bestellt bleibt nur der Spielraum bis zum Bildrand.
    Reicht er nicht, wird gemeldet; die Brennweite fällt nie unter die Grenze."""
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    basis = kameras.kamerasatz(haus, kuerzel=["s"], brennweite_mm=24.0)["kameras"][0]
    weit_vorn = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 10.0),
                                   8.0, 4.0, 8.0)
    kamera = kameras.kamerasatz(haus, kuerzel=["s"], brennweite_mm=24.0,
                                sicht_frei=sichtstrahl.pruefer([weit_vorn]))["kameras"][0]
    assert kamera["brennweite_mm"] == 24.0
    assert kamera["sicht"]["frei"] is False
    assert kamera["sicht"]["abbruch"] == "kein_freier_standpunkt"


@pytest.mark.parametrize("vorgabe", [{"modus": kameras.MODUS_GEKIPPT},
                                     {"brennweite_mm": 50.0, "seitenverhaeltnis": 1.0}],
                         ids=["gekippt", "50mm-quadratisch"])
def test_die_regel_haelt_auch_mit_anderer_kamera(vorgabe):
    """Der Satz ist mit der Vorgabe-Kamera gebaut (Shift, 35 mm, 16:9). Eine Stichprobe
    mit gekippter Kamera und mit 50 mm im Quadrat: dieselben drei Zusagen."""
    geprueft = 0
    for fall in sz.faelle()[::5]:
        haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
        basis = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]], **vorgabe)["kameras"][0]
        kamera = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]],
                                    sicht_frei=sichtstrahl.pruefer(nachbarn),
                                    **vorgabe)["kameras"][0]
        wo = (fall["szene"]["name"], fall["kuerzel"])
        if sz.sicht_ist_frei(basis["auge"], haus, nachbarn):
            assert kamera["auge"] == basis["auge"] and not kamera["sicht"]["bewegt"], wo
            continue
        stueck = sz.freies_wegstueck(haus, nachbarn, basis)
        if stueck >= sz.LOESBAR_AB_M:
            geprueft += 1
            assert sz.sicht_ist_frei(kamera["auge"], haus, nachbarn), wo
            assert sz.rahmung_haelt(kamera, haus), wo
        elif stueck < sz.UNLOESBAR_UNTER_M:
            assert kamera["sicht"]["frei"] is False and kamera["auge"] == basis["auge"], wo
    assert geprueft >= 5, "Die Stichprobe enthält kaum noch lösbare Fälle."


# --------------------------------------------------------------------------------------
# Die Sichtprüfung ist austauschbar
# --------------------------------------------------------------------------------------

def test_die_sichtpruefung_darf_wahrheitswert_oder_runnerantwort_liefern():
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    basis = kameras.kamerasatz(haus, kuerzel=["s"])["kameras"][0]
    schuppen = [sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 6.0, 4.0, 8.0)]
    als_antwort = kameras.kamerasatz(haus, kuerzel=["s"],
                                     sicht_frei=sichtstrahl.pruefer(schuppen))["kameras"][0]
    als_bool = kameras.kamerasatz(
        haus, kuerzel=["s"],
        sicht_frei=lambda a, p: sichtstrahl.sicht_frei(a, p, schuppen)["frei"])["kameras"][0]
    assert als_bool["auge"] == als_antwort["auge"]
    assert als_bool["brennweite_mm"] == als_antwort["brennweite_mm"]


def test_nicht_gemessen_ist_nicht_frei_und_nicht_verdeckt():
    """Antwortet die Prüfung überall «nicht gemessen» (``frei: None``), wird nichts bewegt
    und nichts behauptet: Die dritte Antwort bleibt die dritte."""
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    kamera = kameras.kamerasatz(haus, kuerzel=["s"],
                                sicht_frei=lambda a, p: {"frei": None})["kameras"][0]
    assert kamera["sicht"]["frei"] is None
    assert kamera["sicht"]["abbruch"] == "nicht_pruefbar"
    assert kamera["sicht"]["bewegt"] is False
    assert "NICHT GEPRÜFT" in kamera["sicht"]["vermerk"]


def test_sichtpunkte_liegen_auf_den_zugewandten_fassaden():
    haus = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]
    frontal = kameras.sichtpunkte(haus, (7.0, -30.0, 1.7))
    assert len(frontal) == 15 and all(p[1] == 0.0 for p in frontal)
    ueber_eck = kameras.sichtpunkte(haus, (40.0, -30.0, 1.7))
    assert len(ueber_eck) == 30
    assert all(p[0] == 14.0 or p[1] == 0.0 for p in ueber_eck)
    assert all(0.0 < p[2] < 9.0 for p in ueber_eck)
    assert kameras.sichtpunkte(haus, (7.0, 5.0, 20.0)) == []


# --------------------------------------------------------------------------------------
# Worauf die Rechnung baut
# --------------------------------------------------------------------------------------

def test_die_kuerzeste_brennweite_ist_die_des_kameraknotens():
    assert kameras.ZIEH_BRENNWEITE_MIN_MM == min(kosmo_szene.KAMERAS_AUTO_BRENNWEITEN)


def test_fuellgrad_waechst_gleichmaessig_und_der_eckentest_kippt_nur_einmal():
    """Zwei Eigenschaften, auf die Lösung UND Prüfmass bauen, hier an Zufallsstellungen
    nachgemessen: Der Füllgrad ist der Brennweite verhältnisgleich, und der Eckentest
    geht mit kürzerer Brennweite nie verloren."""
    r = random.Random(306)
    for _ in range(200):
        haus = [[0.0, 0.0, 0.0], [r.uniform(8, 24), r.uniform(8, 18), r.uniform(6, 18)]]
        kuerzel = r.choice(sz.RICHTUNGEN)
        basis = kameras.kamerasatz(haus, kuerzel=[kuerzel])["kameras"][0]
        ziel = sz._ziel(haus, basis)
        anteil = r.uniform(0.45, 1.0)
        ort = tuple(ziel[i] + (basis["auge"][i] - ziel[i]) * anteil for i in range(2)) \
            + (basis["auge"][2],)
        lagen = [kameras.rahmung_am_standpunkt(ort, ziel, haus, brennweite_mm=f,
                                               azimut_grad=basis["azimut_grad"])
                 for f in (24.0, 28.0, 32.0, 35.0)]
        for lage, f in zip(lagen, (24.0, 28.0, 32.0, 35.0)):
            assert math.isclose(lage["fuellgrad"] / f, lagen[0]["fuellgrad"] / 24.0,
                                rel_tol=1e-9)
        passt = [lage["ecken_passt"] for lage in lagen]
        assert passt == sorted(passt, reverse=True), passt


def test_die_rahmung_am_gerechneten_standort_ist_die_des_kamerasatzes():
    """``rahmung_am_standpunkt`` misst denselben Füllgrad wie ``kamerasatz``: eine
    Rechnung, nicht zwei."""
    for szene in sz.szenen()[:12]:
        for kamera in kameras.kamerasatz(szene["haus"], kuerzel=list(sz.RICHTUNGEN))["kameras"]:
            if kamera["durchlaeufe"]:
                continue                 # zurückgeschoben: der Shift ist dort der alte
            lage = kameras.rahmung_am_standpunkt(
                kamera["auge"], sz._ziel(szene["haus"], kamera), szene["haus"],
                azimut_grad=kamera["azimut_grad"])
            assert math.isclose(lage["fuellgrad"], kamera["fuellgrad"], rel_tol=1e-9)
            assert lage["haelt"]


# --------------------------------------------------------------------------------------
# Die Aufrufstelle im Runner (läuft nur in Blender; geprüft wird die Quelle)
# --------------------------------------------------------------------------------------

def _runner_ohne_kommentare() -> str:
    return "\n".join(z.split("#")[0] for z in RUNNER.read_text(encoding="utf-8").splitlines())


def test_der_runner_reicht_den_strahlenschuss_nur_mit_schalter_herein():
    """Ohne ``AIIMAGING_FREIE_SICHT=1`` ändert sich an keinem Lauf etwas: Die Regel ist an
    erfundenen Szenen gemessen, am echten Bestand noch nicht."""
    quelle = _runner_ohne_kommentare()
    treffer = re.findall(r'\*\*\(\{"sicht_frei": _sicht_frei\}\s+'
                         r'if os\.environ\.get\("AIIMAGING_FREIE_SICHT"\) == "1" else \{\}\)',
                         quelle)
    assert len(treffer) == 1
    assert quelle.count("sicht_frei=") == 0, "Die Sichtprüfung darf nur über den Schalter kommen."


def test_der_runner_stellt_die_brennweite_der_herangezogenen_kamera():
    """Sonst stünde die Kamera näher, aber mit dem bestellten Objektiv, und das Haus
    liefe über den Bildrand: genau das Gegeneinander, das A0306 auflöst."""
    quelle = _runner_ohne_kommentare()
    assert re.search(r'if \(k\.get\("sicht"\) or \{\}\)\.get\("bewegt"\):\s+'
                     r'brennweite = k\["brennweite_mm"\]', quelle)
    assert '"sicht": k.get("sicht"),' in quelle


def test_die_antwort_des_runners_und_des_strahlentests_haben_dieselben_felder():
    """Austauschbar heisst: dieselbe Antwortform. Die Felder des Runners stehen in seiner
    Quelle, die des Strahlentests kommen aus einem Aufruf."""
    quelle = RUNNER.read_text(encoding="utf-8")
    anfang = quelle.index("def _sicht_frei(")
    rumpf = quelle[anfang:quelle.index("\ndef ", anfang + 10)]
    antwort = sichtstrahl.sicht_frei((0, 0, 0), (10, 0, 0), [])
    for feld in antwort:
        assert f'"{feld}"' in rumpf, feld
