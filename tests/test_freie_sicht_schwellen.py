"""«Freie Sicht aufs Haus» (A0306): die Schwellen der Lösung, von beiden Seiten besetzt.

**Warum es diese Datei gibt.** Ein Satz, an dem die Lösung 100 % erreicht, belegt wenig,
wenn ihre Schwellen in einer leeren Lücke des Satzes liegen (Lehre aus dem ersten
Gegenlesen im Spezialauftrag, 10.11.2026). ``tests/test_freie_sicht.py`` misst die
Zielfunktion; hier steht, was daneben gehört:

* **Reihen in kleinen Schritten quer über jede Schwelle** der Lösung: der Spielraum des
  Standpunkts (5 und 10 cm), die kürzeste Brennweite (24 mm), die Kante, an der ein
  Nachbarbau den ersten Sichtpunkt verdeckt (seitlich und in der Höhe), die Grenzen des
  Heranziehens bei kleinen Bauten.
* **Mehrere tausend Zufallsfälle gegen die Basis:** Jede Abweichung von der heutigen Kamera
  ist eine belegte Verbesserung (vorher verdeckt, nachher frei und gerahmt). Kein Fall
  wird schlechter.
* **Nicht entscheidbar** bleibt nicht entscheidbar: Wo die Sichtprüfung nicht jeden Punkt
  messen kann, wird weder «frei» noch «verdeckt» geraten und die Kamera nicht bewegt.
* **Gemeine Fälle**, gebaut, bevor es das Gegenlesen tut.

Geurteilt wird überall mit dem Prüfmass aus ``tests/sichtszenen.py`` (eigener Strahlentest,
eigene Projektion, eigene Suche), nicht mit dem Code der Lösung.
"""
from __future__ import annotations

import math

import pytest

import sichtszenen as sz
from aiimaging import kameras, sichtstrahl

HAUS = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]


def _pruefe(haus, nachbarn, kuerzel="s", **vorgabe) -> dict:
    """Ein Fall durch Lösung und Prüfmass, mit allen Zusagen. Gibt das Urteil zurück."""
    fall = {"szene": {"name": "reihe", "haus": haus, "nachbarn": nachbarn}, "kuerzel": kuerzel}
    satz = kameras.kamerasatz(haus, kuerzel=[kuerzel],
                              sicht_frei=sichtstrahl.pruefer(nachbarn), **vorgabe)
    kamera = satz["kameras"][0]
    urteil = sz.beurteile(fall, kamera, vorgabe=vorgabe)
    basis, sicht = urteil["basis"], kamera["sicht"]
    ohne_sicht = {k: v for k, v in kamera.items() if k != "sicht"}
    if urteil["klasse"] == "frei":
        assert ohne_sicht == basis and sicht["frei"] is True and not sicht["bewegt"]
    elif urteil["klasse"] == "loesbar":
        assert sicht["bewegt"] and urteil["erreicht"], (urteil["wegstueck_m"], sicht)
    elif urteil["klasse"] == "unloesbar":
        assert sicht["frei"] is False and not sicht["bewegt"], (urteil["wegstueck_m"], sicht)
        assert ohne_sicht["auge"] == basis["auge"] and satz["verdeckt"] == [kuerzel]
        assert sicht["vermerk"].startswith("VERDECKT")
    # In JEDER Klasse, auch im Grenzfall: Eine bewegte Kamera ist frei und gerahmt, eine
    # unbewegte ist die der Basis. Nie schlechter als vorher, nie halb herangezogen.
    if sicht["bewegt"]:
        assert urteil["erreicht"] and sicht["frei"] is True
        assert kamera["brennweite_mm"] >= min(kameras.ZIEH_BRENNWEITE_MIN_MM,
                                              basis["brennweite_mm"]) - 1e-9
        assert kamera["brennweite_mm"] <= basis["brennweite_mm"] + 1e-9
        assert kamera["abstand_m"] >= kameras.MIN_ZIEH_ABSTAND_M
    else:
        assert ohne_sicht["auge"] == basis["auge"]
        assert ohne_sicht["brennweite_mm"] == basis["brennweite_mm"]
    return urteil


# --------------------------------------------------------------------------------------
# Schwelle 1: der Spielraum des Standpunkts (unter 5 cm nie, ab 10 cm immer)
# --------------------------------------------------------------------------------------

def _rahmungsgrenze(haus, basis) -> float:
    """Der kleinste Abstand, an dem die Rahmung noch hält, auf 1 mm (ohne Nachbarbau)."""
    stueck = sz.freies_wegstueck(haus, [], basis, schritt_m=0.001, genug_m=1e9)
    d0 = math.hypot(basis["auge"][0] - basis["blick_auf"][0],
                    basis["auge"][1] - basis["blick_auf"][1])
    return d0 - 0.001 - stueck


def test_reihe_ueber_den_spielraum_in_zentimeterschritten():
    """Ein breiter Riegel quer vor der Kamera, in Schritten von 1 cm verschoben. Hinter ihm
    ist die Sicht verdeckt, vor ihm frei; das freie Wegstück reicht von seiner Vorderkante
    bis zur Rahmungsgrenze und wächst je Schritt um einen Zentimeter, von «gibt es nicht»
    bis 25 cm. Zugesagt: unter 5 cm nie gelöst, ab 10 cm immer, dazwischen beides erlaubt,
    aber nie eine Kamera, die nicht frei und gerahmt wäre."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    d_min = _rahmungsgrenze(HAUS, basis)
    d0 = basis["abstand_m"]
    uy = (basis["auge"][1] - basis["blick_auf"][1]) / d0
    geloest = {"unter_5": 0, "zwischen": 0, "ab_10": 0}
    gezaehlt = dict(geloest)
    for schritt in range(-10, 26):
        breite_stueck = schritt / 100.0 + 0.005          # nie genau auf der Schwelle
        # Vorderkante des Riegels (zum Haus hin) im Abstand d_min + Stück vom Blickziel.
        kante_y = basis["blick_auf"][1] + uy * (d_min + breite_stueck)
        riegel = sichtstrahl.quader((7.0, kante_y - 1.0), 60.0, 2.0, 14.0, name="riegel")
        urteil = _pruefe(HAUS, [riegel])
        gruppe = ("unter_5" if breite_stueck < 0.05 else
                  "ab_10" if breite_stueck >= 0.10 else "zwischen")
        gezaehlt[gruppe] += 1
        geloest[gruppe] += urteil["kamera"]["sicht"]["bewegt"]
        # Das Prüfmass misst dasselbe Wegstück wie die Bauart der Reihe (auf 2 cm).
        assert urteil["wegstueck_m"] <= max(breite_stueck, 0.0) + 0.02
    assert geloest["unter_5"] == 0, geloest
    assert geloest["ab_10"] == gezaehlt["ab_10"] == 16, (geloest, gezaehlt)
    assert gezaehlt["unter_5"] == 15 and gezaehlt["zwischen"] == 5


# --------------------------------------------------------------------------------------
# Schwelle 2: die kürzeste Brennweite
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("brennweite", [24.0 + i * 0.25 for i in range(13)] + [28.0, 31.5, 35.0, 50.0])
def test_reihe_ueber_die_bestellte_brennweite(brennweite):
    """Von 24 mm aufwärts in Viertelmillimetern: Mit 24 mm bestellt gibt es kein weiteres
    Objektiv, knapp darüber ein wenig. Je Brennweite drei Riegel in verschiedener Lage
    zwischen Kamera und Haus; nie fällt die Brennweite unter 24 mm."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=brennweite)["kameras"][0]
    klassen = set()
    for anteil in (0.97, 0.9, 0.8):
        y = basis["blick_auf"][1] + (basis["auge"][1] - basis["blick_auf"][1]) * anteil
        riegel = sichtstrahl.quader((7.0, y), 60.0, 1.0, 14.0)
        klassen.add(_pruefe(HAUS, [riegel], brennweite_mm=brennweite)["klasse"])
    assert "frei" not in klassen
    if brennweite >= 28.0:
        assert "loesbar" in klassen, "Mit Luft bis 24 mm muss der Riegel dicht vor der Kamera lösbar sein."


def test_unter_24_mm_bestellt_wird_nie_verlaengert_und_nie_weiter_verkuerzt():
    """Wer 20 mm bestellt, steht schon unter der Grenze. Die Lösung verkürzt dann nicht
    weiter und verlängert nicht auf 24: Es bleibt bei der bestellten Brennweite."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=20.0)["kameras"][0]
    for versatz in (1.5, 3.0, 6.0):
        schuppen = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + versatz), 30.0, 1.0, 12.0)
        kamera = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=20.0,
                                    sicht_frei=sichtstrahl.pruefer([schuppen]))["kameras"][0]
        assert kamera["brennweite_mm"] == 20.0
        if kamera["sicht"]["bewegt"]:
            assert sz.sicht_ist_frei(kamera["auge"], HAUS, [schuppen]) and sz.rahmung_haelt(kamera, HAUS)


# --------------------------------------------------------------------------------------
# Schwelle 3: die Kante, an der ein Nachbarbau den ersten Sichtpunkt verdeckt
# --------------------------------------------------------------------------------------

def test_reihe_seitlich_ueber_die_sichtkante_in_zwei_zentimeter_schritten():
    """Ein Turm vor der Kamera wandert von der Seite in das Blickfeld, 2 cm je Schritt. An
    der Stelle, an der er den ersten Sichtpunkt verdeckt, kippt der Fall von «frei» auf
    «verdeckt». Auf jeder Seite der Kante gelten die Zusagen, und das Urteil der Lösung
    über «frei» stimmt in jedem Schritt mit dem des Prüfmasses überein."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    y = basis["auge"][1] + 6.0
    # Die Kante suchen: grob, wo der Turm (4 m breit) zum ersten Mal verdeckt.
    kante = next(x / 10.0 for x in range(300, -1, -1)
                 if not sz.sicht_ist_frei(basis["auge"], HAUS,
                                          [sichtstrahl.quader((x / 10.0, y), 4.0, 4.0, 12.0)]))
    klassen = []
    for schritt in range(-20, 21):
        turm = sichtstrahl.quader((kante + 0.05 + schritt * 0.02, y), 4.0, 4.0, 12.0, name="turm")
        urteil = _pruefe(HAUS, [turm])
        klassen.append(urteil["klasse"])
        hier = kameras.sichtbefund(basis["auge"], HAUS, sichtstrahl.pruefer([turm]))["frei"]
        assert hier == (urteil["klasse"] == "frei"), schritt
    assert klassen[0] != "frei" and klassen[-1] == "frei"
    assert klassen.count("frei") >= 10 and len(klassen) - klassen.count("frei") >= 10
    # Die Kante ist eine Kante: einmal frei, dann frei.
    erste_freie = klassen.index("frei")
    assert all(k == "frei" for k in klassen[erste_freie:])


def test_reihe_ueber_die_hoehe_des_nachbarbaus_in_fuenf_zentimeter_schritten():
    """Ein Bau vor der Kamera wächst von 0,3 m auf 4,3 m. Unter Augenhöhe verdeckt er
    nichts (die unterste Punktreihe liegt bei 15 % der Haushöhe), darüber zuerst die
    unterste Reihe. Beide Seiten der Schwelle sind besetzt."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    klassen = []
    for i in range(81):
        hoehe = 0.3 + i * 0.05
        bau = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 4.0), 20.0, 3.0, hoehe)
        klassen.append(_pruefe(HAUS, [bau])["klasse"])
    assert klassen[0] == "frei" and klassen[-1] != "frei"
    wechsel = sum(1 for a, b in zip(klassen, klassen[1:]) if (a == "frei") != (b == "frei"))
    assert wechsel == 1, "Zwischen «verdeckt nichts» und «verdeckt» liegt genau eine Höhe."
    assert 15 <= klassen.count("frei") <= 66


# --------------------------------------------------------------------------------------
# Schwelle 4: kleine Bauten und die Grenzen des Heranziehens
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("kante", [2.0 + i * 0.5 for i in range(17)])
def test_reihe_ueber_die_hausgroesse(kante):
    """Vom Kiosk (2 m) bis zum Haus (10 m): Bei kleinen Bauten setzt der Mindestabstand den
    Standort, der Riegel 65 % und die Untergrenze von 6 m zum Blickziel kommen ins Spiel.
    Die Zusagen gelten auch dort, aus zwei Richtungen und mit zwei Lagen des Hindernisses."""
    haus = [[0.0, 0.0, 0.0], [kante, kante * 0.8, max(2.5, kante * 0.7)]]
    for kuerzel in ("s", "eES"):
        basis = kameras.kamerasatz(haus, kuerzel=[kuerzel])["kameras"][0]
        for anteil in (0.95, 0.75):
            ort = [basis["blick_auf"][i] + (basis["auge"][i] - basis["blick_auf"][i]) * anteil
                   for i in range(2)]
            schuppen = sichtstrahl.quader(ort, 3.0, 0.6, 6.0, drehung_grad=basis["azimut_grad"])
            urteil = _pruefe(haus, [schuppen], kuerzel)
            kamera = urteil["kamera"]
            # Nie in den Puffer um die Hüllbox.
            p = kameras.HUELLBOX_PUFFER_M
            assert not (haus[0][0] - p <= kamera["auge"][0] <= haus[1][0] + p
                        and haus[0][1] - p <= kamera["auge"][1] <= haus[1][1] + p)


# --------------------------------------------------------------------------------------
# Mehrere tausend Zufallsfälle gegen die Basis: nie schlechter
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("saat", [101, 102, 103, 104, 105, 106])
def test_zufallsfaelle_gegen_die_basis_keiner_wird_schlechter(saat, monkeypatch):
    """Sechs weitere Sätze aus anderer Saat, je 384 Fälle (2304 zusammen). Verglichen wird
    mit der heutigen Kamera: Entweder ist die neue Zahl für Zahl dieselbe (verdeckt sie,
    trägt sie zusätzlich die Warnung VERDECKT), oder die alte war verdeckt und die neue ist
    frei und regelgerecht gerahmt. Etwas Drittes gibt es nicht. (Ohne die teure Suche des Prüfmasses; die läuft im Hauptsatz.)"""
    monkeypatch.setattr(sz, "SAAT", saat)
    bewegt = verdeckt = 0
    for fall in sz.faelle():
        haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
        basis = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]])["kameras"][0]
        kamera = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]],
                                    sicht_frei=sichtstrahl.pruefer(nachbarn))["kameras"][0]
        sicht = kamera.pop("sicht")
        wo = (saat, fall["szene"]["name"], fall["kuerzel"])
        basis_frei = sz.sicht_ist_frei(basis["auge"], haus, nachbarn)
        assert sicht["frei"] is not None, wo
        if sicht["bewegt"]:
            bewegt += 1
            assert not basis_frei, wo
            assert sz.sicht_ist_frei(kamera["auge"], haus, nachbarn), wo
            assert sz.rahmung_haelt(kamera, haus), wo
        else:
            assert sicht["frei"] is basis_frei, wo
            verdeckt += not basis_frei
            if not basis_frei:
                # Der einzige Unterschied zur Basis: Die verdeckte Kamera sagt es.
                assert kamera.pop("warnungen") == (sicht["vermerk"],), wo
                assert basis.pop("warnungen") == (), wo
            assert kamera == basis, wo
    assert bewegt >= 30 and verdeckt >= 20, (bewegt, verdeckt)


# --------------------------------------------------------------------------------------
# Nicht entscheidbar: nicht raten, wie die Basis handeln
# --------------------------------------------------------------------------------------

def _teils_ungemessen(nachbarn, jeder: int):
    """Eine Sichtprüfung, die jeden ``jeder``-ten Strahl nicht messen kann."""
    zaehler = {"n": 0}

    def _pruefe_teils(auge, punkt):
        zaehler["n"] += 1
        if zaehler["n"] % jeder == 0:
            return {"frei": None, "grund": "NICHT GEMESSEN"}
        return sichtstrahl.sicht_frei(auge, punkt, nachbarn)

    return _pruefe_teils


@pytest.mark.parametrize("jeder", [1, 2, 3, 7, 15])
def test_teils_ungemessen_und_nichts_verdeckt_ist_nicht_entscheidbar(jeder):
    """Kein Punkt verdeckt, aber nicht jeder gemessen: Das ist nicht «frei». Die Kamera
    bleibt die der Basis, und das Ergebnis sagt «nicht prüfbar»."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    satz = kameras.kamerasatz(HAUS, kuerzel=["s"], sicht_frei=_teils_ungemessen([], jeder))
    kamera = satz["kameras"][0]
    sicht = kamera.pop("sicht")
    assert kamera == basis
    assert sicht["frei"] is None and sicht["abbruch"] == "nicht_pruefbar"
    assert "NICHT GEPRÜFT" in sicht["vermerk"]
    assert satz["verdeckt"] == []


@pytest.mark.parametrize("jeder", [2, 3, 7])
def test_auf_einen_standpunkt_mit_ungemessener_sicht_wird_nicht_gezogen(jeder):
    """Am Standort sicher verdeckt (ein gemessener Punkt genügt dafür), aber unterwegs ist
    nie jeder Punkt messbar: Die Kamera wird nicht auf Verdacht herangezogen."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    schuppen = [sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 30.0, 2.0, 14.0)]
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                sicht_frei=_teils_ungemessen(schuppen, jeder))["kameras"][0]
    assert kamera["sicht"]["frei"] is False and not kamera["sicht"]["bewegt"]
    assert kamera["auge"] == basis["auge"]
    # Mit einer Prüfung, die alles misst, ist derselbe Fall lösbar: Der Unterschied ist
    # allein das Nichtwissen.
    assert kameras.kamerasatz(HAUS, kuerzel=["s"], sicht_frei=sichtstrahl.pruefer(schuppen)
                              )["kameras"][0]["sicht"]["bewegt"]


def test_unbrauchbare_huellbox_wird_wie_bisher_abgewiesen():
    with pytest.raises(ValueError):
        kameras.kamerasatz([[0, 0, 0], [1, 1, float("nan")]], sicht_frei=lambda a, p: True)


# --------------------------------------------------------------------------------------
# Gemeine Fälle
# --------------------------------------------------------------------------------------

def _basis(kuerzel="s", haus=HAUS):
    return kameras.kamerasatz(haus, kuerzel=[kuerzel])["kameras"][0]


def test_gemein_die_kamera_steht_im_nachbarbau():
    """Der gerechnete Standort liegt IN einem Bau. Das ist verdeckt (wer im Bau steht,
    sieht nichts), und frei wird die Kamera erst ausserhalb."""
    b = _basis()
    um_die_kamera = sichtstrahl.quader((b["auge"][0], b["auge"][1]), 6.0, 6.0, 10.0, name="um")
    urteil = _pruefe(HAUS, [um_die_kamera])
    assert urteil["klasse"] == "loesbar"
    assert not sichtstrahl.punkt_im_koerper(urteil["kamera"]["auge"], um_die_kamera)


def test_gemein_der_nachbarbau_klebt_an_der_fassade():
    """Wand an Wand: Kein Standpunkt der Welt macht diese Fassade frei."""
    anbau = sichtstrahl.quader((7.0, -3.0), 14.0, 6.0, 9.0)
    assert _pruefe(HAUS, [anbau])["klasse"] == "unloesbar"
    # Von der anderen Seite stört er nicht.
    assert _pruefe(HAUS, [anbau], "n")["klasse"] == "frei"


def test_gemein_bauten_hinter_haus_und_hinter_kamera_stoeren_nicht():
    b = _basis()
    hinter_haus = sichtstrahl.quader((7.0, 30.0), 40.0, 10.0, 30.0)
    hinter_kamera = sichtstrahl.quader((b["auge"][0], b["auge"][1] - 6.0), 40.0, 10.0, 30.0)
    assert _pruefe(HAUS, [hinter_haus, hinter_kamera])["klasse"] == "frei"


def test_gemein_ein_schwebender_bau_verdeckt_nur_oben():
    """Eine Brücke über dem Weg, Unterkante über Augenhöhe: Die Kamera schaut darunter
    durch zum Fuss, aber die oberen Sichtpunkte sind verdeckt. Das zählt als verdeckt."""
    b = _basis()
    bruecke = sichtstrahl.quader((7.0, b["auge"][1] + 8.0), 40.0, 3.0, 20.0, fuss_z=3.0)
    urteil = _pruefe(HAUS, [bruecke])
    assert urteil["klasse"] != "frei"
    assert urteil["basis"]["auge"][2] < 3.0


def test_gemein_eine_gasse_zwischen_zwei_bauten():
    """Zwei Bauten lassen eine Gasse, durch die die Kamera schaut. Zu eng: verdeckt. Breit
    genug: frei. Die Breite wächst in 25-cm-Schritten über die Schwelle."""
    b = _basis()
    y = b["auge"][1] + 10.0
    klassen = []
    for i in range(40):
        halbe = 0.5 + i * 0.25
        links = sichtstrahl.quader((b["auge"][0] - halbe - 5.0, y), 10.0, 4.0, 14.0)
        rechts = sichtstrahl.quader((b["auge"][0] + halbe + 5.0, y), 10.0, 4.0, 14.0)
        klassen.append(_pruefe(HAUS, [links, rechts])["klasse"])
    assert klassen[0] != "frei" and klassen[-1] == "frei"
    assert klassen.count("frei") >= 5 and klassen.count("frei") <= 35


def test_gemein_hochformat_gekippt_und_gelaende_gesetzt():
    """Andere Kamera, anderes Format, gesetzter Geländestand, Haus weit weg vom Ursprung
    und auf 412 m Höhe: dieselben Zusagen."""
    haus = [[2600000.0, 1200000.0, 412.5], [2600016.0, 1200011.0, 424.0]]
    for vorgabe in ({"seitenverhaeltnis": 0.8}, {"modus": kameras.MODUS_GEKIPPT},
                    {"gelaende_z": 413.0}, {"deckungsgrad": 0.8}):
        for kuerzel in ("s", "wWN", "e"):
            b = kameras.kamerasatz(haus, kuerzel=[kuerzel], **vorgabe)["kameras"][0]
            ort = [b["blick_auf"][i] + (b["auge"][i] - b["blick_auf"][i]) * 0.93 for i in range(2)]
            schuppen = sichtstrahl.quader(ort, 5.0, 1.0, 9.0, fuss_z=412.5,
                                          drehung_grad=37.0, name="schuppen")
            _pruefe(haus, [schuppen], kuerzel, **vorgabe)


def test_gemein_ausschnitt_kamera_wird_gemeldet_nie_bewegt():
    """Eine lange, flache Halle als Ausschnitt (Entscheid 75): gewollt nah. Steht etwas
    davor, steht es im Ergebnis; bewegt wird die Kamera nicht."""
    halle = [[0.0, 0.0, 0.0], [66.0, 12.0, 3.45]]
    ohne = kameras.kamerasatz(halle, kuerzel=["s"], ausschnitt=True)["kameras"][0]
    assert ohne["ausschnitt"]
    wand = sichtstrahl.quader((33.0, (ohne["auge"][1] + 0.0) / 2.0), 80.0, 0.5, 6.0)
    kamera = kameras.kamerasatz(halle, kuerzel=["s"], ausschnitt=True,
                                sicht_frei=sichtstrahl.pruefer([wand]))["kameras"][0]
    sicht = kamera.pop("sicht")
    assert sicht["frei"] is False and not sicht["bewegt"]
    assert sicht["abbruch"] == "nicht_nachgefuehrt" and "Ausschnitt" in sicht["vermerk"]
    assert kamera["auge"] == ohne["auge"] and kamera["brennweite_mm"] == ohne["brennweite_mm"]


def test_gemein_die_sichtpruefung_wird_nur_mit_auge_und_punkt_gefragt():
    """Die Prüfung der Szene bekommt genau zwei Dreiergruppen, nie etwas anderes: Das ist
    die Form, die der Strahlenschuss des Runners annimmt."""
    gefragt = []

    def _merke(auge, punkt):
        gefragt.append((auge, punkt))
        return True

    kameras.kamerasatz(HAUS, kuerzel=["s", "nNE"], sicht_frei=_merke)
    assert len(gefragt) == 15 + 30
    assert all(len(a) == 3 and len(p) == 3 for a, p in gefragt)
