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
24 Einzelhäuser             12                       12 (dieselben)
==========================  =======================  ======================

**Was über den Satz hinaus gemessen ist** (je 100 Startwerte je Art, nicht Teil dieser Proben,
Laufzeit rund zwei Minuten): von 300 aufgelösten Anlagen besteht keine, von 100 intakten schlägt
keine an. Der Anteil des Inneren unter der Schwelle (``formtreue.VERFLECKT_AB_ANTEIL``, ein
Drittel) lag bei 246 gehaltenen Baukörpern bei höchstens 0,14, bei 98 verfleckten Hauptbauten
bei mindestens 0,50. **Härteprobe** mit stärker abweichenden intakten Bildern (60 Startwerte):
bis 35 % der Öffnungen weg und 40 % dazu kein Fehlalarm; bei 10 bis 45 % weg und 10 bis 70 %
dazu einer von 60 (ein Baukörper mit Kanten-Deckung im Inneren 0,37, also nah an der Schwelle).
"""
from __future__ import annotations

import pytest

import anlagen_erzeuger as erz
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
    """Flecken und Platte fallen im Inneren unter die Schwelle; verfleckt fällt oft nur örtlich auf."""
    from aiimaging import formtreue
    for f, _, neu in _anlagen(urteile, erz.ART_FLECKEN, erz.ART_PLATTE):
        haupt = neu["baukoerper"][0]
        assert haupt["urteil"] == formtreue.AUFGELOEST, f["name"]
        assert haupt["innen"]["kanten_iou"] < 0.25, f["name"]
    for f, _, neu in _anlagen(urteile, erz.ART_VERFLECKT):
        haupt = neu["baukoerper"][0]
        assert haupt["urteil"] in (formtreue.AUFGELOEST, formtreue.VERFLECKT), f["name"]


def test_erst_der_ort_verraet_den_verfleckten_bau():
    """Drei verfleckte Hauptbauten, deren Zahl besteht, ganz und im Inneren (ohne den Umriss)."""
    from aiimaging import formtreue
    for startwert in erz.STARTWERTE_NUR_OERTLICH:
        f = erz.fall(startwert, erz.ART_VERFLECKT)
        neu = formtreue.formtreue(f["ki"], f["grund"], f["maske"], f["breite"], f["hoehe"])
        haupt = neu["baukoerper"][0]
        assert haupt["kanten_iou"] >= 0.25 and haupt["innen"]["kanten_iou"] >= 0.25, startwert
        assert haupt["urteil"] == formtreue.VERFLECKT and neu["verfleckt"] == [1], startwert
        assert haupt["innen"]["anteil"] >= 0.5 > formtreue.VERFLECKT_AB_ANTEIL
        assert neu["urteil"] == formtreue.FORM_WEICHT_AB and neu["aufgeloest"] == []
        assert "Verfleckt: In " in neu["saetze"][0] and "ab 33% verfleckt" in neu["saetze"][0]
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
    """Der Abstand zur Schwelle im Satz: innen mindestens 0,5, örtlich höchstens 0,15."""
    innen, oertlich = [], []
    for f, _, neu in _anlagen(urteile, erz.ART_INTAKT):
        for k in neu["baukoerper"]:
            if k.get("innen") and k["innen"]["kanten_iou"] is not None:
                innen.append(k["innen"]["kanten_iou"])
            if k.get("innen") and k["innen"]["anteil"] is not None:
                oertlich.append(k["innen"]["anteil"])
    assert len(innen) >= 60 and min(innen) >= 0.5
    assert len(oertlich) >= 30 and max(oertlich) <= 0.15


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
