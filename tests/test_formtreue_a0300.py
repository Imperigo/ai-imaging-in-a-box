"""A0300 «Formtreue je Baukörper»: Ein aufgelöster Hauptbau in einer Anlage fällt auf.

**Der Fehler.** Die Deckung zählt die Kanten über die ganze Hausfläche. In einer Anlage halten
die Nebenbauten ihre Kanten und heben die Zahl über die Schwelle 0,25, während der Hauptbau in
grüne Flecken aufgelöst ist (Wettbewerbsmodell, 24.10.2026: 0,256, «deckungsgleich»).

**Der Satz.** ``anlagen_erzeuger.anlagen_satz()``: 24 intakte Anlagen, 24 aufgelöste (je 8
Flecken, Platte, verfleckt), Hausanteil 15 bis 60 %, zwei bis vier Nebenbauten; dazu 24
Einzelhäuser und die bestehenden Einzelhaus-Paare aus 346 und 347. Synthetisch, ohne GPU.

**Die Zahlen (gemessen 10.11.2026).**

==========================  =======================  ======================
Satz                        heute «deckungsgleich»   neu «deckungsgleich»
==========================  =======================  ======================
24 aufgelöste Anlagen       24                       0
24 intakte Anlagen          24                       24 (kein Fehlalarm)
24 Einzelhäuser             11                       11 (dieselben)
==========================  =======================  ======================

**Ein Satz, an dem alles trifft, belegt wenig.** Darum stehen hier ausserdem:

* **Reihen quer über jede Schwelle** in kleinen Schritten: der verlorene Teil eines Baus von
  0 bis 100 %, fehlende Öffnungen von 0 bis 100 %, dazugemalte von 0 bis 300 %, die Grösse
  eines Baus um 1 % der Bildfläche, die Menge seiner Zeichnung um 150 Kantenpunkte, und die
  eine Regel ``formtreue.verloren`` Punkt für Punkt.
* **Gemeine Fälle:** der aufgelöste Bau ist nicht der grösste; der Hauptbau ist im Grundbild
  glatt; die KI malt Zeichnung auf glatte Dächer; das KI-Bild ist um einen Punkt verschoben;
  alles ist weg.
* **Der Zufallsvergleich gegen heute** (``anlagen_vergleich``): die ersten 40 Fälle hier, 3200
  von Hand. Kein Fall milder als heute, kein klar guter beanstandet.

**Was die Reihen zeigen, und was nicht entscheidbar ist.** Die Prüfung kippt nicht an einer
scharfen Kante: Sind bis 30 % eines Baus verfleckt, schlägt sie nie an, ab 60 % immer,
dazwischen teils (ein Übergang, kein Fehler: der gemessene Anteil folgt dem wahren auf rund
ein Zehntel genau). Malt die KI nur dazu und lässt die Zeichnung des Grundbilds stehen, heisst
der Bau «dazugemalt»: gemeldet, aber ohne Warnung, weil Kanten allein Material nicht von
neuen Fenstern trennen. Ein Bau, der im Grundbild innen glatt ist, bekommt kein Urteil.
"""
from __future__ import annotations

import pytest

import anlagen_erzeuger as erz
import anlagen_vergleich
from aiimaging import bildschreiben, farbabgleich, kosmo_szene, varianten as v


def _alt(fall, ka, kb) -> dict:
    """Das heutige Urteil: die Deckung über das ganze Haus (``varianten.deckung``)."""
    return v.deckung(True, farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=fall["maske"]))


@pytest.fixture(scope="module")
def karten():
    """Die Kantenkarten des ganzen Satzes, einmal gerechnet (reines Python, rund 20 s)."""
    aus = []
    for fall in erz.anlagen_satz() + erz.einzelhaus_satz():
        ka, kb = farbabgleich.kantenkarten(fall["ki"], fall["grund"], fall["breite"],
                                           fall["hoehe"])
        aus.append((fall, ka, kb))
    return aus


@pytest.fixture(scope="module")
def urteile(karten):
    """Je Fall ``(fall, alt, neu)``: die Deckung von heute und die Prüfung je Baukörper."""
    from aiimaging import formtreue
    return [(fall, _alt(fall, ka, kb),
             formtreue.formtreue_aus_karten(ka, kb, fall["maske"], fall["breite"], fall["hoehe"]))
            for fall, ka, kb in karten]


def _anlagen(urteile, *arten):
    return [(f, a, n) for f, a, n in urteile
            if f["name"].startswith("anlage") and f["art"] in arten]


# ================================================================== der Satz und sein Erzeuger

def test_der_satz_haelt_die_grenzen_des_auftrags(karten):
    anlagen = [f for f, _, _ in karten if f["name"].startswith("anlage")]
    intakt = [f for f in anlagen if f["art"] == erz.ART_INTAKT]
    aufgeloest = [f for f in anlagen if f["art"] in erz.ARTEN_AUFGELOEST]
    assert len(intakt) >= 20 and len(aufgeloest) >= 20
    assert {f["art"] for f in aufgeloest} == set(erz.ARTEN_AUFGELOEST)
    for f in anlagen:
        assert erz.HAUSANTEIL_MIN <= f["hausanteil"] <= erz.HAUSANTEIL_MAX, f["name"]
        assert 2 <= len(f["neben"]) <= 4 and f["hof"] is not None, f["name"]
        assert len(f["grund"]) == len(f["ki"]) == len(f["maske"]) == f["breite"] * f["hoehe"]
    assert len({f["name"] for f in anlagen}) == len(anlagen)
    assert min(f["hausanteil"] for f in anlagen) < 0.25 < 0.50 < max(f["hausanteil"] for f in anlagen)


def test_der_erzeuger_haengt_nur_am_startwert():
    a, b = erz.fall(3, erz.ART_FLECKEN), erz.fall(3, erz.ART_FLECKEN)
    assert a["ki"] == b["ki"] and a["grund"] == b["grund"] and a["maske"] == b["maske"]
    intakt = erz.fall(3, erz.ART_INTAKT)
    # Dieselbe Anordnung, dasselbe Grundbild: nur das KI-Bild ist anders.
    assert intakt["grund"] == a["grund"] and intakt["maske"] == a["maske"] and intakt["ki"] != a["ki"]
    with pytest.raises(ValueError):
        erz.fall(1, "zerbroeselt")


def test_die_kantenquote_greift_im_satz_nicht(karten):
    """Sonst fallen Fugen heraus, die gemalt sind (Startwert 48 am 10.11.2026, siehe Erzeuger)."""
    geprueft = 0
    for fall, ka, kb in karten:
        if fall["art"] != erz.ART_INTAKT:
            continue                      # Flecken sind selbst Kanten; dort darf die Quote greifen
        n = fall["breite"] * fall["hoehe"]
        assert sum(kb) / n < 0.15 and sum(ka) / n < 0.15, fall["name"]
        geprueft += 1
    assert geprueft == 30


# ================================================================== heute: die Fläche rettet

def test_heute_heissen_alle_aufgeloesten_anlagen_deckungsgleich(karten):
    """Der heutige Wert der Zielfunktion: 24 von 24. Nur ``varianten`` und ``farbabgleich``."""
    aufgeloest = [(f, _alt(f, ka, kb)) for f, ka, kb in karten
                  if f["name"].startswith("anlage") and f["art"] in erz.ARTEN_AUFGELOEST]
    bestehen = [f["name"] for f, a in aufgeloest if a["urteil"] == v.DECKUNGSGLEICH]
    assert len(aufgeloest) == 24 and len(bestehen) == 24
    # Nicht knapp: die Zahl über das ganze Haus liegt weit über der Schwelle.
    assert min(a["kanten_iou"] for _, a in aufgeloest) > 0.40


# ================================================================== neu: je Baukörper

def test_kein_aufgeloestes_bild_heisst_mehr_deckungsgleich(urteile):
    from aiimaging import formtreue
    aufgeloest = _anlagen(urteile, *erz.ARTEN_AUFGELOEST)
    bestehen = [f["name"] for f, _, n in aufgeloest if n["urteil"] == formtreue.DECKUNGSGLEICH]
    assert len(aufgeloest) == 24 and bestehen == []
    assert all(n["urteil"] == formtreue.FORM_WEICHT_AB and n["warnung"] for _, _, n in aufgeloest)


def test_kein_fehlalarm_bei_den_intakten(urteile):
    from aiimaging import formtreue
    intakt = _anlagen(urteile, erz.ART_INTAKT)
    assert len(intakt) == 24
    for f, alt, neu in intakt:
        assert neu["urteil"] == formtreue.DECKUNGSGLEICH == alt["urteil"], f["name"]
        assert neu["saetze"] == [] and neu["aufgeloest"] == [] and neu["verfleckt"] == []
        assert neu["anlage"] is True
        assert all(b["urteil"] in (formtreue.GEHALTEN, formtreue.UNGEMESSEN)
                   for b in neu["baukoerper"]), f["name"]


def test_das_urteil_nennt_den_hauptbau_mit_ort(urteile):
    """Welcher Bau: der grösste (Nummer 1), mit dem Kasten des Hauptbaus und einem Ortswort."""
    for f, _, neu in _anlagen(urteile, *erz.ARTEN_AUFGELOEST):
        betroffen = neu["aufgeloest"] + neu["verfleckt"]
        assert betroffen == [1], (f["name"], betroffen)          # die Nebenbauten halten
        haupt = neu["baukoerper"][0]
        assert haupt["nr"] == 1 and tuple(haupt["kasten"]) == tuple(f["haupt"]), f["name"]
        assert haupt["name"].startswith("Baukörper 1 (der grösste, ")
        assert len(neu["saetze"]) == 1
        satz = neu["saetze"][0]
        assert satz.startswith("BAUKÖRPER HÄLT DIE FORM NICHT: Baukörper 1 (der grösste, ")
        assert f"x {f['haupt'][0]} bis {f['haupt'][2]}" in satz and haupt["ort"] in satz
        assert "nicht geeicht" in satz


def test_aufgeloest_und_verfleckt_sind_zwei_urteile(urteile):
    """Flecken und Platte verlieren die Zeichnung im Ganzen; verfleckt fällt teils nur örtlich auf."""
    from aiimaging import formtreue
    for f, _, neu in _anlagen(urteile, erz.ART_FLECKEN, erz.ART_PLATTE):
        haupt = neu["baukoerper"][0]
        assert haupt["urteil"] == formtreue.AUFGELOEST, f["name"]
        assert haupt["innen"]["kanten_iou"] < 0.25 and haupt["innen"]["erhalten"] < 0.5, f["name"]
    for f, _, neu in _anlagen(urteile, erz.ART_VERFLECKT):
        haupt = neu["baukoerper"][0]
        assert f["fleck_gedeckt"] >= 0.6, f["name"]
        assert haupt["urteil"] in (formtreue.AUFGELOEST, formtreue.VERFLECKT), f["name"]


def test_erst_der_ort_verraet_den_verfleckten_bau():
    """Drei verfleckte Hauptbauten, die im Ganzen nicht als verloren gelten: Erst der Ort zeigt es."""
    from aiimaging import formtreue
    for startwert in erz.STARTWERTE_NUR_OERTLICH:
        f = erz.fall(startwert, erz.ART_VERFLECKT)
        neu = formtreue.formtreue(f["ki"], f["grund"], f["maske"], f["breite"], f["hoehe"])
        haupt = neu["baukoerper"][0]
        innen = haupt["innen"]
        assert innen["kanten_iou"] >= 0.25 or innen["erhalten"] >= formtreue.ERHALTEN_MIN, startwert
        assert haupt["urteil"] == formtreue.VERFLECKT and neu["verfleckt"] == [1], startwert
        assert innen["anteil"] >= formtreue.VERFLECKT_AB_ANTEIL
        assert neu["urteil"] == formtreue.FORM_WEICHT_AB and neu["aufgeloest"] == []
        assert "Verfleckt: " in neu["saetze"][0] and "ab 33% verfleckt" in neu["saetze"][0]
        # Dieselbe Anordnung intakt: kein Satz.
        g = erz.fall(startwert, erz.ART_INTAKT)
        assert formtreue.formtreue(g["ki"], g["grund"], g["maske"], g["breite"],
                                   g["hoehe"])["urteil"] == formtreue.DECKUNGSGLEICH


def test_der_umriss_allein_rettet_eine_platte_nicht_mehr(urteile):
    """Gemessen: Eine glatte Platte kommt über ihren gehaltenen Umriss auf 0,25 und mehr."""
    from aiimaging import formtreue
    gerettet = [(f["name"], n["baukoerper"][0]) for f, _, n in _anlagen(urteile, erz.ART_PLATTE)
                if n["baukoerper"][0]["kanten_iou"] >= 0.25]
    assert gerettet, "keine Platte im Satz, deren Umriss allein die Schwelle erreicht"
    for name, haupt in gerettet:
        assert haupt["innen"]["kanten_iou"] == 0.0 and haupt["urteil"] == formtreue.AUFGELOEST, name


def test_gehaltene_baukoerper_liegen_innen_und_oertlich_klar_auf_der_guten_seite(urteile):
    """Der Abstand zur Schwelle im Satz: innen mindestens 0,5, örtlich höchstens 0,10."""
    innen, oertlich = [], []
    for f, _, neu in _anlagen(urteile, erz.ART_INTAKT):
        for k in neu["baukoerper"]:
            if k.get("innen") and k["innen"]["kanten_iou"] is not None:
                innen.append(k["innen"]["kanten_iou"])
            if k.get("innen") and k["innen"]["anteil"] is not None:
                oertlich.append(k["innen"]["anteil"])
    assert len(innen) >= 60 and min(innen) >= 0.5
    assert len(oertlich) >= 30 and max(oertlich) <= 0.10


def test_die_zahl_ueber_das_ganze_haus_ist_die_der_deckung(urteile):
    for f, alt, neu in urteile:
        assert neu["kanten_iou_haus"] == alt["kanten_iou"], f["name"]
        assert neu["schwelle"] == v.DECKUNG_KANTEN_IOU_SCHWELLE


# ================================================================== das Einzelhaus bleibt

def test_am_einzelhaus_satz_bleibt_jedes_urteil(urteile):
    einzel = [(f, a, n) for f, a, n in urteile if f["name"].startswith("einzel")]
    assert len(einzel) == 24
    for f, alt, neu in einzel:
        assert neu["urteil"] == alt["urteil"], f["name"]
        assert neu["anlage"] is False and neu["saetze"] == []
        assert len(neu["baukoerper"]) == 1
        assert neu["baukoerper"][0]["kanten_iou"] == alt["kanten_iou"]
    # Beide Urteile kommen vor, sonst prüfte die Probe nichts.
    assert {a["urteil"] for _, a, _ in einzel} == {v.DECKUNGSGLEICH, v.FORM_WEICHT_AB}


def test_die_bestehenden_einzelhaus_paare_behalten_ihr_urteil(tmp_path):
    """Die Paare aus 347 (Haus und Baum) und 346 (übermaltes Fensterband), über die Dateien."""
    import test_deckung_haus_347 as p347
    import test_fenster_gehalten_346 as p346
    from aiimaging import formtreue

    def png(name, farben, b, h):
        return str(bildschreiben.schreibe_farb_png(tmp_path / name, farben, b, h))

    kennung = png("id347.png", p347._bild(p347._kennung), p347.B, p347.H)
    grund = png("g347.png", p347._bild(p347._grund), p347.B, p347.H)
    paare = [
        ("347 übermalt, nur Haus", png("k347.png", p347._bild(p347._ki_uebermalt), p347.B, p347.H),
         grund, p347.NUR_HAUS, {}),
        ("347 gehalten, nur Haus", grund, grund, p347.NUR_HAUS, {}),
        ("347 übermalt, Maske mit Baum, Tabelle nimmt ihn heraus",
         png("k347b.png", p347._bild(p347._ki_uebermalt), p347.B, p347.H), grund,
         p347.HAUS_UND_BAUM, {"material_id_png": kennung, "tabelle": p347.TABELLE}),
        ("346 übermaltes Band", png("k346.png", p346._bild(p346._ki_uebermalt), p346.B, p346.H),
         png("g346.png", p346._bild(p346._grundbild), p346.B, p346.H), p346.MASKE, {}),
    ]
    for name, ki, gr, maske, mehr in paare:
        alt = v.deckung_aus_bildern(ki, gr, True, maske=maske, **mehr)
        neu = formtreue.formtreue_aus_bildern(ki, gr, maske, **mehr)
        assert alt["bereich"] == v.DECKUNG_BEREICH_HAUS, name
        assert neu["urteil"] == alt["urteil"] and neu["anlage"] is False, name
        assert neu["kanten_iou_haus"] == alt["kanten_iou"], name
        nachgefuehrt = formtreue.deckung_mit_baukoerpern(alt, neu)
        assert nachgefuehrt["urteil"] == alt["urteil"] and nachgefuehrt["satz"] == alt["satz"]


def test_ohne_maske_oder_bild_gibt_es_kein_urteil_je_baukoerper(tmp_path):
    from aiimaging import formtreue
    farben = [(200, 200, 200)] * 64
    a = str(bildschreiben.schreibe_farb_png(tmp_path / "a.png", farben, 8, 8))
    klein = str(bildschreiben.schreibe_farb_png(tmp_path / "k.png", farben[:16], 4, 4))
    assert formtreue.formtreue_aus_bildern(a, a, None) is None
    assert formtreue.formtreue_aus_bildern(a, None, [True] * 64) is None
    assert formtreue.formtreue_aus_bildern(a, str(tmp_path / "fehlt.png"), [True] * 64) is None
    assert formtreue.formtreue_aus_bildern(a, klein, [True] * 64) is None
    assert formtreue.formtreue_aus_bildern(a, a, [True] * 7) is None


# ================================================================== die Bausteine

def _maske(b, h, *kaesten):
    return [any(k[0] <= x < k[2] and k[1] <= y < k[3] for k in kaesten)
            for y in range(h) for x in range(b)]


def test_baukoerper_sind_die_zusammenhaengenden_stuecke_das_groesste_zuerst():
    from aiimaging import formtreue
    maske = _maske(30, 20, (1, 1, 5, 5), (18, 0, 30, 6), (2, 14, 8, 19))
    stuecke = formtreue.baukoerper(maske, 30, 20)
    assert [s["nr"] for s in stuecke] == [1, 2, 3]
    assert [s["kasten"] for s in stuecke] == [(18, 0, 30, 6), (2, 14, 8, 19), (1, 1, 5, 5)]
    assert [s["n"] for s in stuecke] == [72, 30, 16]
    assert [s["ort"] for s in stuecke] == ["oben rechts", "unten links", "oben links"]
    assert sum(s["n"] for s in stuecke) == sum(maske)
    assert formtreue.baukoerper([False] * 12, 4, 3) == []
    with pytest.raises(formtreue.FormtreueError):
        formtreue.baukoerper([True] * 5, 4, 3)


def test_ueber_eck_benachbart_ist_ein_baukoerper():
    """Eine schräge Wand treppt im Raster; sie zerfällt nicht in Stücke."""
    from aiimaging import formtreue
    treppe = [x == y for y in range(6) for x in range(6)]
    assert len(formtreue.baukoerper(treppe, 6, 6)) == 1
    getrennt = [(x, y) in ((0, 0), (2, 0)) for y in range(3) for x in range(3)]
    assert len(formtreue.baukoerper(getrennt, 3, 3)) == 2


def test_der_ort_in_worten():
    from aiimaging import formtreue
    assert formtreue._ort((40, 40, 60, 60), 100, 100) == "Bildmitte"
    assert formtreue._ort((0, 40, 10, 60), 100, 100) == "links, mittlere Höhe"
    assert formtreue._ort((40, 80, 60, 100), 100, 100) == "unten Mitte"
    assert formtreue._ort((80, 0, 100, 10), 100, 100) == "oben rechts"


B2, H2 = 120, 40
LINKS, RECHTS = (4, 4, 56, 36), (64, 4, 116, 36)
_BODEN, _WAND, _FUGE = (192, 196, 190), (200, 200, 200), (120, 120, 120)


def _zwei_bauten(aufgeloest: bool):
    """Zwei Bauten mit Fugen alle zehn Punkte; im KI-Bild ist der linke glatt, wenn ``aufgeloest``.

    Der Boden ist fast so hell wie die Wand: Der Umriss ist hier keine Kante, damit die Probe
    nur die Zeichnung zählt und die Kantenquote (15 % der Bildpunkte) nicht greift.
    """
    def farbe(x, y, glatt_links):
        for k in (LINKS, RECHTS):
            if k[0] <= x < k[2] and k[1] <= y < k[3]:
                if k is LINKS and glatt_links:
                    return _WAND
                return _FUGE if (x - k[0]) % 10 == 9 else _WAND
        return _BODEN
    grund = [farbe(x, y, False) for y in range(H2) for x in range(B2)]
    ki = [farbe(x, y, aufgeloest) for y in range(H2) for x in range(B2)]
    return ki, grund, _maske(B2, H2, LINKS, RECHTS), B2, H2


def test_ein_glatter_bau_neben_einem_gehaltenen_faellt_auf():
    from aiimaging import formtreue
    ki, grund, maske, b, h = _zwei_bauten(True)
    haus = farbabgleich.kanten_iou(ki, grund, b, h, bereich=maske)
    assert v.deckung(True, haus)["urteil"] == v.DECKUNGSGLEICH      # die Fläche rettet
    neu = formtreue.formtreue(ki, grund, maske, b, h)
    assert neu["urteil"] == formtreue.FORM_WEICHT_AB and neu["aufgeloest"] == [1]
    assert neu["baukoerper"][0]["ort"] == "links, mittlere Höhe"
    assert neu["baukoerper"][1]["urteil"] == formtreue.GEHALTEN
    assert neu["schwaechster"] == 1
    gehalten = formtreue.formtreue(*_zwei_bauten(False))
    assert gehalten["urteil"] == formtreue.DECKUNGSGLEICH and gehalten["saetze"] == []


def test_ein_winziger_bau_bekommt_kein_urteil_und_macht_keine_anlage():
    """Ein Haus und ein Schopf unter 1 % der Bildfläche: Es bleibt ein Einzelhaus."""
    from aiimaging import formtreue
    ki, grund, _, b, h = _zwei_bauten(True)
    maske = _maske(b, h, RECHTS, (4, 4, 8, 8))                      # rechts ganz, links 16 Punkte
    neu = formtreue.formtreue(ki, grund, maske, b, h)
    klein = neu["baukoerper"][1]
    assert klein["urteil"] == formtreue.UNGEMESSEN and "Bildfläche" in klein["grund"]
    assert neu["anlage"] is False and neu["urteil"] == formtreue.DECKUNGSGLEICH


def test_nebenbauten_mit_glattem_dach_machen_aus_dem_hauptbau_kein_einzelhaus():
    """Die Anlage zählt nach Grösse: Der aufgelöste Bau fällt auf, auch wenn der andere glatt ist."""
    from aiimaging import formtreue

    def farbe(x, y, ki):
        if LINKS[0] <= x < LINKS[2] and LINKS[1] <= y < LINKS[3]:
            return _WAND if ki else (_FUGE if (x - LINKS[0]) % 10 == 9 else _WAND)
        return _WAND if (RECHTS[0] <= x < RECHTS[2] and RECHTS[1] <= y < RECHTS[3]) else _BODEN
    grund = [farbe(x, y, False) for y in range(H2) for x in range(B2)]
    ki = [farbe(x, y, True) for y in range(H2) for x in range(B2)]
    neu = formtreue.formtreue(ki, grund, _maske(B2, H2, LINKS, RECHTS), B2, H2)
    je = {k["ort"]: k["urteil"] for k in neu["baukoerper"]}
    assert je == {"links, mittlere Höhe": formtreue.AUFGELOEST,
                  "rechts, mittlere Höhe": formtreue.UNGEMESSEN}
    assert neu["anlage"] is True and neu["urteil"] == formtreue.FORM_WEICHT_AB


def test_ein_bau_ohne_kanten_im_grundbild_bekommt_kein_urteil():
    from aiimaging import formtreue
    b, h = 60, 30
    glatt = [(200, 200, 200)] * (b * h)
    neu = formtreue.formtreue(glatt, glatt, _maske(b, h, (2, 2, 28, 28), (32, 2, 58, 28)), b, h)
    assert [k["urteil"] for k in neu["baukoerper"]] == [formtreue.UNGEMESSEN] * 2
    assert neu["urteil"] == formtreue.UNGEMESSEN and neu["kanten_iou_haus"] is None


def test_eine_eigene_zerlegung_trennt_bauten_die_sich_beruehren():
    from aiimaging import formtreue
    b, h = B2, H2
    links, rechts = (4, 4, 60, 36), (60, 4, 116, 36)                # Wand an Wand

    def farbe(x, y, glatt_links):
        if not (4 <= x < 116 and 4 <= y < 36):
            return _BODEN
        if x < 60 and glatt_links:
            return _WAND
        return _FUGE if x % 10 == 9 else _WAND
    grund = [farbe(x, y, False) for y in range(h) for x in range(b)]
    ki = [farbe(x, y, True) for y in range(h) for x in range(b)]
    maske = _maske(b, h, links, rechts)
    zusammen = formtreue.formtreue(ki, grund, maske, b, h)
    assert len(zusammen["baukoerper"]) == 1 and zusammen["anlage"] is False
    karte = [("halle" if x < 60 else "haus") if m else None
             for m, x in zip(maske, [x for _ in range(h) for x in range(b)])]
    getrennt = formtreue.formtreue(ki, grund, maske, b, h, koerper_karte=karte)
    assert {k["kennung"]: k["urteil"] for k in getrennt["baukoerper"]} == {
        "halle": formtreue.AUFGELOEST, "haus": formtreue.GEHALTEN}
    assert getrennt["urteil"] == formtreue.FORM_WEICHT_AB
    with pytest.raises(formtreue.FormtreueError):
        formtreue.formtreue(ki, grund, maske, b, h, koerper_karte=karte[:-1])


def test_falsche_eingaben_werden_abgewiesen():
    from aiimaging import formtreue
    ki, grund, maske, b, h = _zwei_bauten(False)
    with pytest.raises(formtreue.FormtreueError):
        formtreue.formtreue(ki[:-1], grund, maske, b, h)
    with pytest.raises(formtreue.FormtreueError):
        formtreue.formtreue(ki, grund, maske[:-1], b, h)
    with pytest.raises(formtreue.FormtreueError):
        formtreue.formtreue(ki, grund, maske, b, h, schwelle=1.5)


def test_das_deckungsurteil_wird_nur_strenger_nie_milder():
    from aiimaging import formtreue
    befund = formtreue.formtreue(*_zwei_bauten(True))
    aus = formtreue.deckung_mit_baukoerpern(v.deckung(True, 0.43), befund)
    assert aus["urteil"] == v.FORM_WEICHT_AB and aus["warnung"] is True
    assert aus["kanten_iou"] == 0.43 and "Baukörper 1" in aus["satz"]
    assert aus["baukoerper_befund"] is befund
    # Was schon «weicht ab» oder «nicht gemessen» heisst, bleibt; ein gehaltener Befund ändert nichts.
    for alt in (v.deckung(True, 0.1), v.deckung(True, None), v.deckung(False, 0.9)):
        assert formtreue.deckung_mit_baukoerpern(alt, befund)["urteil"] == alt["urteil"]
    gehalten = formtreue.formtreue(*_zwei_bauten(False))
    assert formtreue.deckung_mit_baukoerpern(v.deckung(True, 0.43), gehalten)["urteil"] == v.DECKUNGSGLEICH
    assert formtreue.deckung_mit_baukoerpern(None, befund) is None


# ================================================================== der Satz zur Form im Urteil

def test_der_satz_zur_form_nennt_den_baukoerper_je_kamera():
    from aiimaging import formtreue
    befund = formtreue.formtreue(*_zwei_bauten(True))
    hinweise: list = []
    kosmo_szene._deckung_eintragen(
        None, [{"kamera": "sSE", "deckung": 0.43, "formtreue": befund},
               {"kamera": "sNW", "deckung": 0.43,
                "formtreue": formtreue.formtreue(*_zwei_bauten(False))},
               {"kamera": "sN", "deckung": 0.43}], hinweise)
    assert len(hinweise) == 1
    satz = hinweise[0]
    assert satz.startswith(f"{kosmo_szene.SATZ_FORM_WEICHT_AB}, Kamera 'sSE': "
                           f"{formtreue.SATZ_BAUKOERPER}: Baukörper 1 (der grösste, links, ")
    assert "Bildpunkte x 4 bis 56, y 4 bis 36" in satz
    # Zweimal eingetragen steht er einmal; unter der Schwelle stehen beide Sätze.
    kosmo_szene._deckung_eintragen(
        None, [{"kamera": "sSE", "deckung": 0.43, "formtreue": befund}], hinweise)
    assert len(hinweise) == 1
    beide: list = []
    kosmo_szene._deckung_eintragen(
        None, [{"kamera": "sSE", "deckung": 0.1, "formtreue": befund}], beide)
    assert len(beide) == 2 and all(s.startswith(kosmo_szene.SATZ_FORM_WEICHT_AB) for s in beide)


# ================================================================== die eine Regel, Punkt für Punkt

def test_verloren_ist_deckung_unter_der_schwelle_und_weniger_als_die_haelfte_erhalten():
    """Beide Grenzen in Einerschritten: 100 Kantenpunkte im Grundbild, 0 bis 100 gemeinsam."""
    from aiimaging import formtreue
    for gemeinsam in range(0, 101):
        for dazu in (0, 50, 100, 200, 300, 400):                 # Kantenpunkte nur im KI-Bild
            eines = 100 + dazu
            soll = gemeinsam / eines < 0.25 and gemeinsam < 50
            assert formtreue.verloren(gemeinsam, 100, eines, 0.25) is soll, (gemeinsam, dazu)
    # Genau auf der Grenze ist nicht verloren (wie bei der Deckung: «>= Schwelle» besteht).
    assert formtreue.verloren(25, 100, 100, 0.25) is False
    assert formtreue.verloren(24, 100, 100, 0.25) is True
    assert formtreue.verloren(50, 100, 400, 0.25) is False         # Deckung 0,125, die Hälfte steht
    assert formtreue.verloren(49, 100, 400, 0.25) is True
    # Ohne Kanten im Grundbild gibt es nichts zu verlieren.
    assert formtreue.verloren(0, 0, 80, 0.25) is False and formtreue.verloren(0, 0, 0, 0.25) is False


# ================================================================== Reihen an gebauten Kantenkarten
#
# Zwei Bauten nebeneinander, 200 x 60. Die Kanten sind hier direkt gesetzt (senkrechte Linien),
# ohne Kantenfindung: So liegt jeder Schritt der Reihe genau dort, wo er liegen soll.

B3, H3 = 200, 60
BAU_A, BAU_B = (4, 4, 96, 56), (104, 4, 196, 56)


def _linien(kasten, schritt=6, bis=None, ab=None):
    """Kantenpunkte auf senkrechten Linien im Kasten; ``ab``/``bis`` begrenzen in x."""
    return {y * B3 + x for y in range(kasten[1], kasten[3])
            for x in range(kasten[0] + 3, kasten[2] - 2, schritt)
            if (ab is None or x >= ab) and (bis is None or x < bis)}


def _karte(*mengen):
    punkte = set().union(*mengen)
    return [i in punkte for i in range(B3 * H3)]


def _urteil_a(ki_a, grund_a=None, bau_b=BAU_B, grund_b=None):
    from aiimaging import formtreue
    grund_a = _linien(BAU_A) if grund_a is None else grund_a
    grund_b = _linien(bau_b) if grund_b is None else grund_b
    neu = formtreue.formtreue_aus_karten(_karte(ki_a, grund_b), _karte(grund_a, grund_b),
                                         _maske(B3, H3, BAU_A, bau_b), B3, H3)
    return neu, next(k for k in neu["baukoerper"] if tuple(k["kasten"]) == BAU_A)


def test_reihe_verlorener_teil_von_null_bis_ganz():
    """Bau A verliert seine Linien von links her, in Schritten von 5 % seiner Breite."""
    from aiimaging import formtreue
    breite = BAU_A[2] - BAU_A[0]
    reihe = []
    for schritt in range(0, 21):
        teil = schritt / 20
        neu, a = _urteil_a(_linien(BAU_A, ab=BAU_A[0] + teil * breite))
        reihe.append((teil, a["urteil"], a["innen"]["anteil"], a["innen"]["erhalten"]))
        assert a["innen"]["anteil"] is not None
        # Der Ort misst, was fehlt, und nie mehr: Ein Streifen schmaler als das Prüffenster
        # (hier 31 Punkte, ein Drittel des Baus) füllt noch kein Fenster.
        assert teil - 0.25 <= a["innen"]["anteil"] <= teil + 0.05, reihe[-1]
        assert abs(a["innen"]["erhalten"] - (1 - teil)) <= 0.07, reihe[-1]
        assert neu["warnung"] is (a["urteil"] != formtreue.GEHALTEN)
    je = {teil: urteil for teil, urteil, _, _ in reihe}
    # Bis 35 % nie, ab 40 % immer: Bei 40 % stehen genau 28 von 84 Fenstern unter der Schwelle,
    # ein Drittel. (Vor dem 10.11.2026 abends verglich die Prüfung die gerundete Zahl 0,3333
    # mit 1/3 und liess genau diesen Fall durch; die Reihe hat es gefunden.)
    assert all(je[t / 20] == formtreue.GEHALTEN for t in range(0, 8))
    assert all(je[t / 20] != formtreue.GEHALTEN for t in range(8, 21))
    bei_40 = next(a for t, _, a, _ in reihe if t == 0.4)
    assert bei_40 == 0.3333
    # Einmal gekippt, bleibt es gekippt; «aufgelöst» löst «verfleckt» ab, wenn fast alles fehlt.
    urteile = [u for _, u, _, _ in reihe]
    assert urteile == sorted(urteile, key=[formtreue.GEHALTEN, formtreue.VERFLECKT,
                                           formtreue.AUFGELOEST].index)
    assert je[0.5] == formtreue.VERFLECKT and je[1.0] == formtreue.AUFGELOEST
    erste_aufgeloest = [teil for teil, u, _, _ in reihe if u == formtreue.AUFGELOEST][0]
    assert erste_aufgeloest == 0.8                                   # erhalten 0,20, unter 0,25


def test_reihe_dazugemalt_warnt_nie_und_wird_gemeldet():
    """Bau A behält alle Linien, die KI malt 0 bis 5 neue je alte dazu."""
    from aiimaging import formtreue
    alt = _linien(BAU_A, schritt=12)
    gemeldet = []
    for je_alte in range(0, 6):
        neue = set()
        for versatz in range(1, je_alte + 1):
            neue |= {i + 2 * versatz for i in alt}
        neu, a = _urteil_a(alt | neue, grund_a=alt)
        assert neu["warnung"] is False and a["innen"]["erhalten"] == 1.0, je_alte
        deckung = a["innen"]["kanten_iou"]
        assert abs(deckung - 1 / (1 + je_alte)) < 0.03          # am Saum fällt eine neue Linie weg
        if deckung < 0.25:
            assert a["urteil"] == formtreue.DAZUGEMALT and neu["nicht_entscheidbar"] == [a["nr"]]
            gemeldet.append(je_alte)
        else:
            assert a["urteil"] == formtreue.GEHALTEN and neu["nicht_entscheidbar"] == []
    assert gemeldet and min(gemeldet) >= 3 and 5 in gemeldet   # um 1/4 herum kippt die Meldung


def test_reihe_fehlt_und_dazugemalt_zusammen():
    """Das Gitter: 0 bis 100 % der Linien fehlen (gleichmässig verteilt), 0 bis 3 neue je alte."""
    from aiimaging import formtreue
    alt = sorted({i % B3 for i in _linien(BAU_A, schritt=4)})        # die x-Lagen, 23 Linien
    for fehlen in range(0, len(alt) + 1, 2):
        # gleichmässig verteilt weglassen, damit kein Fleck entsteht
        weg = {alt[int(j * len(alt) / fehlen)] for j in range(fehlen)} if fehlen else set()
        bleibt = {i for i in _linien(BAU_A, schritt=4) if i % B3 not in weg}
        for je_alte in (0, 1, 3):
            neue = {i + v for i in _linien(BAU_A, schritt=4) for v in (1, 2, 3)[:je_alte]}
            neu, a = _urteil_a(bleibt | neue, grund_a=_linien(BAU_A, schritt=4))
            erhalten = a["innen"]["erhalten"]
            soll_verloren = formtreue.verloren(round(erhalten * a["innen"]["kanten_grundbild"]),
                                               a["innen"]["kanten_grundbild"],
                                               round(erhalten * a["innen"]["kanten_grundbild"]
                                                     / max(a["innen"]["kanten_iou"], 1e-9)), 0.25)
            assert abs(erhalten - (1 - fehlen / len(alt))) < 0.02
            if erhalten >= 0.5:
                assert neu["warnung"] is False, (fehlen, je_alte, a["urteil"])
            if soll_verloren:
                assert a["urteil"] == formtreue.AUFGELOEST, (fehlen, je_alte)


def test_reihe_groesse_eines_baus_um_ein_prozent_der_bildflaeche():
    """Bau B schrumpft: Unter 1 % der Bildfläche ist das Bild keine Anlage mehr."""
    from aiimaging import formtreue
    ki_a = _linien(BAU_A, ab=BAU_A[0] + 60)                          # A ist zu zwei Dritteln leer
    for breite in range(3, 11):
        bau_b = (104, 4, 104 + breite, 24)                           # 20 hoch
        neu, a = _urteil_a(ki_a, bau_b=bau_b, grund_b=set())
        gross = breite * 20 >= 0.01 * B3 * H3
        assert gross is (breite >= 6)
        assert neu["anlage"] is gross, breite
        assert a["urteil"] == formtreue.VERFLECKT                    # der Bau selbst wird gemessen
        assert neu["warnung"] is gross, breite                       # aber nur in der Anlage gewarnt
        if not gross:
            assert neu["urteil"] == formtreue.DECKUNGSGLEICH and neu["saetze"] == []


def test_reihe_menge_der_zeichnung_um_die_mindestzahl():
    """Bau A trägt eine bis sechs Linien; unter 150 Kantenpunkten im Inneren gibt es kein Urteil."""
    from aiimaging import formtreue
    for linien in range(1, 7):
        lagen = [BAU_A[0] + 10 + 14 * j for j in range(linien)]
        grund = {y * B3 + x for y in range(BAU_A[1], BAU_A[3]) for x in lagen}
        neu, a = _urteil_a(set(), grund_a=grund)                     # im KI-Bild ist A leer
        punkte = a["innen"]["kanten_grundbild"]
        assert punkte == linien * 48
        if punkte < formtreue.KOERPER_MIN_KANTEN:
            assert a["urteil"] == formtreue.UNGEMESSEN and "keine Zeichnung" in a["grund"]
            assert neu["warnung"] is False
        else:
            assert a["urteil"] == formtreue.AUFGELOEST and neu["warnung"] is True
    assert 3 * 48 < formtreue.KOERPER_MIN_KANTEN <= 4 * 48           # die Grenze liegt in der Reihe


# ================================================================== Reihen am Erzeuger (mit Kantenfindung)

def _lauf(startwert, art, **regler):
    from aiimaging import formtreue
    f = erz.fall(startwert, art, **regler)
    ka, kb = farbabgleich.kantenkarten(f["ki"], f["grund"], f["breite"], f["hoehe"])
    return f, _alt(f, ka, kb), formtreue.formtreue_aus_karten(ka, kb, f["maske"], f["breite"],
                                                              f["hoehe"])


def test_reihe_fleckanteil_am_erzeuger():
    """Der Hauptbau wird von 0 bis 100 % verfleckt; gezählt wird nach dem wirklich gedeckten Teil.

    Gemessen (24 Startwerte je Stufe, 504 Bilder): bis 35 % gedeckt nie beanstandet (143
    Bilder), 35 bis 45 % 16 von 53, 45 bis 60 % 66 von 71, ab 60 % 237 von 237.
    """
    from aiimaging import formtreue
    faelle = [_lauf(s, erz.ART_VERFLECKT, fleck_anteil=stufe / 10)
              for stufe in range(0, 11) for s in (1, 2, 3)]
    wenig = [(f, n) for f, _, n in faelle if f["fleck_gedeckt"] <= 0.30]
    viel = [(f, n) for f, _, n in faelle if f["fleck_gedeckt"] >= 0.60]
    dazwischen = [(f, n) for f, _, n in faelle if 0.30 < f["fleck_gedeckt"] < 0.60]
    assert len(wenig) >= 5 and len(viel) >= 10 and len(dazwischen) >= 3
    for f, neu in wenig:
        assert neu["urteil"] == formtreue.DECKUNGSGLEICH, (f["name"], f["fleck_gedeckt"])
    for f, neu in viel:
        assert neu["urteil"] == formtreue.FORM_WEICHT_AB and 1 in neu["aufgeloest"] + neu["verfleckt"]
    # Der gemessene Anteil folgt dem wahren (wo ein örtliches Urteil möglich ist).
    for f, _, neu in faelle:
        anteil = neu["baukoerper"][0]["innen"]["anteil"]
        if anteil is not None:
            assert abs(anteil - f["fleck_gedeckt"]) <= 0.25, (f["name"], anteil, f["fleck_gedeckt"])
    # Heute sieht die Deckung keinen dieser Fälle.
    assert all(a["urteil"] == v.DECKUNGSGLEICH for _, a, _ in faelle)


def test_reihe_fehlende_oeffnungen_am_erzeuger():
    """In JEDEM Bau fehlen 0 bis 100 % der Öffnungen, zufällig verteilt (auch nebeneinander).

    Gemessen (12 Startwerte je Stufe): bis 30 % nie beanstandet, ab 70 % immer; dazwischen
    1 bis 9 von 12. Die Deckung von heute beanstandet auch «alles fehlt» nicht: Die Umrisse
    halten die Zahl über das Haus über der Schwelle.
    """
    from aiimaging import formtreue
    for stufe in range(0, 11):
        for s in (1, 2):
            f, alt, neu = _lauf(s, erz.ART_INTAKT, weg=stufe / 10, dazu=0.0)
            assert alt["urteil"] == v.DECKUNGSGLEICH, (stufe, s)
            if stufe <= 2:
                assert neu["urteil"] == formtreue.DECKUNGSGLEICH, (stufe, s)
            if stufe >= 8:
                assert neu["urteil"] == formtreue.FORM_WEICHT_AB, (stufe, s)
            for bau, k in zip(sorted(f["bauten"], key=lambda b: b["kasten"]),
                              sorted(neu["baukoerper"], key=lambda k: tuple(k["kasten"]))):
                if k["urteil"] != formtreue.UNGEMESSEN and bau["oeffnungen"]:
                    wahr = bau["erhalten"] / bau["oeffnungen"]
                    assert abs(k["innen"]["erhalten"] - wahr) <= 0.15, (stufe, s, k["nr"])


def test_reihe_dazugemalte_oeffnungen_am_erzeuger():
    """Nichts fehlt, die KI malt 0 bis 300 % dazu: nie eine Warnung, ab 250 % «dazugemalt»."""
    from aiimaging import formtreue
    gemeldet = 0
    for stufe in range(0, 7):
        for s in (1, 2):
            _, alt, neu = _lauf(s, erz.ART_INTAKT, weg=0.0, dazu=stufe / 2)
            assert neu["urteil"] == formtreue.DECKUNGSGLEICH == alt["urteil"], (stufe, s)
            assert neu["aufgeloest"] == [] and neu["verfleckt"] == []
            gemeldet += bool(neu["nicht_entscheidbar"])
            if stufe <= 3:
                assert neu["nicht_entscheidbar"] == [], (stufe, s)
    assert gemeldet >= 1


# ================================================================== gemeine Fälle

def test_der_aufgeloeste_bau_ist_nicht_der_groesste():
    """Ein Nebenbau ist aufgelöst: Das Urteil nennt IHN, mit seiner Nummer und seinem Kasten."""
    from aiimaging import formtreue
    gefunden = 0
    for s in (1, 2, 3, 4):
        for art in (erz.ART_FLECKEN, erz.ART_PLATTE):
            f, alt, neu = _lauf(s, art, fleck_auf=1)
            ziel = next(k for k in neu["baukoerper"] if tuple(k["kasten"]) == tuple(f["fleck_bau"]))
            assert ziel["nr"] != 1 and alt["urteil"] == v.DECKUNGSGLEICH
            if ziel["urteil"] == formtreue.UNGEMESSEN:
                assert neu["urteil"] == formtreue.DECKUNGSGLEICH     # zu wenig Zeichnung: wie heute
                continue
            gefunden += 1
            assert neu["aufgeloest"] + neu["verfleckt"] == [ziel["nr"]], (s, art)
            assert f"Baukörper {ziel['nr']} ({ziel['ort']})" in neu["saetze"][0]
            assert neu["baukoerper"][0]["urteil"] == formtreue.GEHALTEN   # der Hauptbau hält
    assert gefunden >= 4


def test_ein_im_grundbild_glatter_hauptbau_ist_nicht_entscheidbar():
    """Der Hauptbau trägt im Grundbild keine Zeichnung und wird zu Flecken: kein Urteil, wie heute.

    Kanten allein trennen hier Flecken nicht von gemaltem Material. Das ist eine Grenze der
    Prüfung, keine Lösung; sie steht im Urteil (``grund``).
    """
    from aiimaging import formtreue
    for s in (1, 2, 3):
        _, alt, neu = _lauf(s, erz.ART_FLECKEN, glatt=(0,))
        haupt = neu["baukoerper"][0]
        assert haupt["urteil"] == formtreue.UNGEMESSEN and "keine Zeichnung" in haupt["grund"]
        assert neu["urteil"] == alt["urteil"] and neu["saetze"] == []


def test_die_ki_malt_zeichnung_auf_glatte_daecher_ohne_warnung():
    """Zwei Bauten sind im Grundbild glatt, die KI malt Öffnungen darauf: kein Fehlalarm."""
    from aiimaging import formtreue
    for s in (1, 2, 3):
        for menge in (0.3, 1.0):
            _, alt, neu = _lauf(s, erz.ART_INTAKT, glatt=(0, 1), ki_malt_auf_glatt=menge)
            assert neu["urteil"] == formtreue.DECKUNGSGLEICH == alt["urteil"], (s, menge)
            assert neu["baukoerper"][0]["urteil"] == formtreue.UNGEMESSEN


def test_ein_verschobenes_bild_wird_nie_milder_beurteilt():
    """Das KI-Bild ist um 1 bis 6 Punkte verschoben: Wo heute «weicht ab» steht, bleibt es."""
    from aiimaging import formtreue
    f = erz.fall(2, erz.ART_INTAKT)
    b, h = f["breite"], f["hoehe"]
    beanstandet = 0
    for versatz in range(1, 7):
        verschoben = [f["ki"][y * b + max(0, x - versatz)] for y in range(h) for x in range(b)]
        ka, kb = farbabgleich.kantenkarten(verschoben, f["grund"], b, h)
        alt = _alt(f, ka, kb)
        neu = formtreue.formtreue_aus_karten(ka, kb, f["maske"], b, h)
        assert neu["kanten_iou_haus"] == alt["kanten_iou"]
        if alt["urteil"] == v.FORM_WEICHT_AB:
            beanstandet += 1
            assert neu["urteil"] == formtreue.FORM_WEICHT_AB, versatz
    assert beanstandet >= 1


def test_alles_weg_bleibt_beanstandet_und_nennt_jeden_bau():
    """Das KI-Bild ist eine graue Fläche: Heute «weicht ab», neu ebenso, mit allen Bauten."""
    from aiimaging import formtreue
    f = erz.fall(3, erz.ART_INTAKT)
    grau = [(128, 128, 128)] * len(f["ki"])
    ka, kb = farbabgleich.kantenkarten(grau, f["grund"], f["breite"], f["hoehe"])
    alt = _alt(f, ka, kb)
    neu = formtreue.formtreue_aus_karten(ka, kb, f["maske"], f["breite"], f["hoehe"])
    assert alt["urteil"] == v.FORM_WEICHT_AB == neu["urteil"]
    gemessen = [k for k in neu["baukoerper"] if k["urteil"] != formtreue.UNGEMESSEN]
    assert gemessen and all(k["urteil"] == formtreue.AUFGELOEST for k in gemessen)
    assert len(neu["saetze"]) == len(gemessen)


def test_ein_bau_am_bildrand_wird_gemessen():
    from aiimaging import formtreue
    rand = (0, 0, 92, 60)                                            # bis an drei Bildränder
    grund_a = {y * B3 + x for y in range(0, 60) for x in range(3, 90, 6)}
    neu = formtreue.formtreue_aus_karten(_karte(_linien(BAU_B)), _karte(grund_a, _linien(BAU_B)),
                                         _maske(B3, H3, rand, BAU_B), B3, H3)
    a = next(k for k in neu["baukoerper"] if tuple(k["kasten"]) == rand)
    assert a["urteil"] == formtreue.AUFGELOEST and a["ort"] == "links, mittlere Höhe"


# ================================================================== der Zufallsvergleich gegen heute

def test_zufallsvergleich_gegen_heute_die_ersten_vierzig():
    """Vierzig gewürfelte Fälle quer durch alle Regler (3200 von Hand, siehe ``anlagen_vergleich``)."""
    zaehlung = anlagen_vergleich.befund([anlagen_vergleich.vergleiche_einen(n) for n in range(40)])
    assert zaehlung["faelle"] == 40
    assert zaehlung["milder"] == []                   # nie milder als die Deckung von heute
    assert zaehlung["zahl_ungleich"] == []            # dieselbe Zahl über das ganze Haus
    assert zaehlung["ungleich_ohne_anlage"] == []     # Einzelhaus: dasselbe Urteil
    assert zaehlung["gut_beanstandet"] == []          # kein klar guter Fall beanstandet
    assert zaehlung["schlecht_besteht"] == []         # jeder klar schlechte fällt auf
    klassen = {k[0] for k in zaehlung["klassen"]}
    assert {"einzelhaus", "klar_gut", "klar_schlecht", "uebergang"} <= klassen
    # Heute sieht die Deckung keinen der klar schlechten Fälle in einer Anlage.
    assert all(alt == v.DECKUNGSGLEICH for (klasse, alt, _), _ in zaehlung["klassen"].items()
               if klasse == "klar_schlecht")

