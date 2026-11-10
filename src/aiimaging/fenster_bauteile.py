"""Die Fensterprüfung je Bauteil (A0291, «Masstreue je Bauteil») — reine Bibliothek, kein Paket.

**Anlass.** ``varianten.fenster_gehalten`` urteilt über das ganze Bild und seit v5 je Fensterband
(ein Geschoss). Übermalt die KI EIN Fenster in einem Band von fünf, bleibt der Median des Bands
Glas und der Gesamtanteil bei vier Fünfteln: Beide Zahlen halten, und niemand sagt, welches
Fenster fehlt. Gemessen am synthetischen Eichsatz (``tests/fenster_paare.py``, 105 Paare): Die
Band-Prüfung merkt 3 von 45 einzeln übermalten Fenstern, ohne Ort.

**Was hier geprüft wird.** Jedes zusammenhängende Glasstück des Material-ID-Passes ist ein
Bauteil. Ein Fensterband ist im ID-Pass aber EIN Glasstück ohne Sprossen (so im Testhaus der
Eichdaten von A0158); breite Glasstücke werden darum in quadratische **Felder** geteilt, die sich
überlappen, und jedes Feld wird wie ein Bauteil geprüft. Nebeneinanderliegende übermalte Felder
werden zu EINEM Fund zusammengezogen.

Je Bauteil oder Feld wird das Glas mit der **Wand gleich daneben** verglichen (ein Ring aus
Fassade, wie in v5) — und zwar nachdem das KI-Bild an genau dieser Wand ins Licht des Grundbilds
gebracht ist. Darum stört weder eine Stimmung noch ein Schatten, der über Fenster und Wand
zugleich fällt. Drei Regeln, jede für eine Art der Übermalung:

1. **Wie die Wand daneben** — der Abstand Glas zu Wand ist im KI-Bild unter einem Viertel des
   Abstands im Grundbild (dieselbe Schwelle wie je Band, ``FENSTER_BAND_KONTRAST_ANTEIL``), und
   mindestens drei Viertel der Bildpunkte liegen näher an der Wand als der halbe Abstand im
   Grundbild. Der zweite Teil hält den Ort genau: Ein Feld, das nur zur Hälfte übermalt ist,
   zählt nicht mit.
2. **Warm** — mindestens drei Viertel der Bildpunkte sind klar rötlicher als die Wand daneben
   und nicht dunkel, obwohl das Glas im Grundbild bläulicher war als die Wand.
3. **Ohne den Glaston der Nachbarfenster** — mindestens drei Viertel der Bildpunkte sind klar
   weniger bläulich als die Geschwister (andere Bauteile mit gleichem Glas im Grundbild) und
   nicht dunkel. Das fängt ein grau übermaltes Fenster in einer farbigen Wand: Es hebt sich von
   der Wand ab und ist doch kein Glas mehr. Gemessen wird am Verhältnis Blau zu Rot, weil eine
   Stimmung dieses bei allen Scheiben gleich verschiebt, und an der Streuung der Geschwister,
   weil Scheiben eines Bilds verschieden spiegeln.

Im Band zählt ein Fund erst, wenn er auch auf doppelter Feldbreite trägt: Ein Vorhang deckt ein
Feld, ein Fenster ist breiter.

**Was es nicht ist.** Ein Hinweis, kein Urteil: ``fenster_gehalten`` hängt den Befund an, ändert
aber ``gehalten`` nicht. Die Schwellen sind am synthetischen Eichsatz gesetzt und an den echten
Ausschnitten von A0158 gegengeprüft; am echten KI-Bild sind sie noch nicht geeicht.

**Bekannte Grenzen.** Ein heller, undurchsichtiger Vorhang, der mehr als ein Feld deckt, sieht aus
wie eine Übermalung. Sind die Geschwister selbst fast neutral, fällt ein graues Fenster nicht auf.
Sind alle Fenster einer farbigen Wand grau übermalt, gibt es keine Geschwister zum Vergleich. Ein
übermaltes Fenster im Band, das schmaler ist als 1,2 Feldbreiten, wird nicht gemeldet. Der Ort
eines Funds im Band stimmt auf etwa ein halbes Feld.
"""
from __future__ import annotations

import math

from . import varianten as _v

#: Ein Glasstück, das mindestens so viel breiter als hoch ist, wird in Felder geteilt. Gesetzt:
#: zwei — ein gewöhnliches Fenster bleibt ein Bauteil, ein Band wird geteilt.
FELD_AB_SEITENVERHAELTNIS = 2.0
#: Ein Feld ist so breit, wie das Glasstück hoch ist, mindestens aber so viele Bildpunkte.
FELD_MIN_BREITE = 6
#: Felder überlappen: Der Schritt ist ein Viertel der Feldbreite. So liegt ein übermaltes Fenster,
#: das mindestens so breit ist wie ein Feld, in einem Feld zu mindestens drei Vierteln.
FELD_SCHRITT_ANTEIL = 0.25
#: Der Ring aus Wand um ein Bauteil reicht mindestens so weit wie in v5 (``FENSTER_RING``) und
#: sonst diesen Anteil der Höhe des Bauteils weit. Gesetzt: gut ein Drittel — bei einem Fünftel
#: lag der Ring im vierfachen Massstab noch zur Hälfte im Rahmen (13 Fehlalarme).
RING_ANTEIL_HOEHE = 0.35
#: Hebt sich das Glas im Grundbild von der Wand um weniger als dieses Vielfache der
#: Mindesttrennung ab, darf der nächste Stoff (der Ring von v5) als Massstab dienen, wenn er
#: klarer trennt. Gesetzt: anderthalb.
WAND_SCHWACH = 1.5
#: Ein Feld mit weniger als diesem Anteil der Bildpunkte eines vollen Felds wird weggelassen.
FELD_MIN_ANTEIL = 0.6
#: Weniger Glaspunkte, und das Bauteil ist «nicht messbar».
BAUTEIL_MIN_PUNKTE = 24
#: So viele Bildpunkte eines Bauteils müssen für Regel 2 und 3 betroffen sein. Gesetzt: drei
#: Viertel — ein Vorhang über die halbe Scheibe reicht nicht.
BAUTEIL_ANTEIL = 0.75
#: Im Band zählt ein Fund erst, wenn auf doppelter Feldbreite so viele Bildpunkte betroffen sind.
#: Gesetzt: sechs Zehntel — ein Fenster von 1,2 Feldbreiten reicht, ein Vorhang von einer nicht.
BESTAETIGUNG_ANTEIL = 0.6
#: Unter diesem Anteil der Helligkeit der Wand gilt ein Bildpunkt als dunkel (Spiegelung, Öffnung)
#: und zählt für Regel 2 nicht als warm.
BAUTEIL_DUNKEL = 0.6
#: Regel 3: So bläulich (Blau zu Rot als Logarithmus) muss das Glas im Grundbild mindestens sein,
#: damit ein verlorener Glaston auffallen kann. Gesetzt: 0,06 — das Glas der Eichdaten hat 0,18.
REIHE_TON_MIN = 0.06
#: Regel 3: Ein Bildpunkt ist entfärbt, wenn sein Glaston um mindestens diesen Anteil des Glastons
#: im Grundbild unter dem mittleren der Geschwister liegt. Gesetzt: vier Zehntel.
REIHE_TON_ANTEIL = 0.4
#: Regel 3: … und um mindestens das Anderthalbfache der Spanne, in der die Geschwister selbst
#: liegen (vom unteren zum oberen Zehntel). Gesetzt; ohne das meldete die erste Fassung in der
#: Gegenprobe mit anderen Saaten dunkel spiegelnde Scheiben neben hellen.
REIHE_STREUUNG_FAKTOR = 1.5
#: Regel 3 braucht mindestens so viele Geschwister.
REIHE_GESCHWISTER_MIN = 2
#: Höchstens so viele Bildpunkte je Bauteil gehen in die Rechnung (gleichmässig ausgedünnt).
BAUTEIL_STICHPROBE = 3000

GEHALTEN, UEBERMALT, NICHT_MESSBAR = "gehalten", "uebermalt", "nicht messbar"
ART_WAND, ART_WARM, ART_REIHE = "wie die Wand daneben", "warm uebermalt", "ohne den Glaston der Nachbarfenster"
SATZ_BAUTEIL_UEBERMALT = "FENSTER EINZELN UEBERMALT"
METHODE_BAUTEILE = (
    "Je zusammenhaengendem Glasstueck des Material-ID-Passes (breite Stuecke in ueberlappende "
    "quadratische Felder geteilt): Glas gegen die Wand gleich daneben, nachdem das KI-Bild an "
    "dieser Wand ins Licht des Grundbilds gebracht ist. Uebermalt, wenn der Abstand zur Wand unter "
    "einem Viertel des Abstands im Grundbild liegt, wenn drei Viertel der Bildpunkte klar "
    "roetlicher als die Wand und nicht dunkel sind, oder wenn drei Viertel klar weniger blaeulich "
    "sind als die anderen Fenster des Bilds (Blau zu Rot, gemessen an deren Streuung). Im Band "
    "muss ein Fund auf doppelter Feldbreite tragen. Hinweis, kein Urteil (A0291)")


def _ton(p) -> float:
    """Der Glaston eines Bildpunkts: Blau zu Rot als Logarithmus (0 ist neutral, darüber bläulich)."""
    return math.log((float(p[2]) + 1.0) / (float(p[0]) + 1.0))


def _helligkeit(p) -> float:
    return (float(p[0]) + float(p[1]) + float(p[2])) / 3.0


def _bits_zu_x(bits: int) -> list:
    aus = []
    while bits:
        tief = bits & -bits
        aus.append(tief.bit_length() - 1)
        bits ^= tief
    return aus


def glasstuecke(glas_zeilen: dict) -> list:
    """Die zusammenhängenden Glasstücke (vier Nachbarn) als ``{zeile: bits}`` je Stück."""
    eltern: list = []

    def wurzel(a: int) -> int:
        while eltern[a] != a:
            eltern[a] = eltern[eltern[a]]
            a = eltern[a]
        return a

    laeufe = []                                   # (zeile, bits des Laufs)
    davor: list = []                              # Läufe der Zeile darüber: (nummer, bits)
    letzte = None
    for y in sorted(glas_zeilen):
        if letzte is None or y != letzte + 1:
            davor = []
        jetzt = []
        bits = glas_zeilen[y]
        while bits:
            tief = bits & -bits
            lauf = bits & ~(bits + tief)          # die zusammenhängenden Einsen ab dem tiefsten Bit
            bits ^= lauf
            nummer = len(laeufe)
            laeufe.append((y, lauf))
            eltern.append(nummer)
            for andere, andere_bits in davor:
                if andere_bits & lauf:
                    eltern[wurzel(andere)] = wurzel(nummer)
            jetzt.append((nummer, lauf))
        davor, letzte = jetzt, y
    stuecke: dict = {}
    for nummer, (y, lauf) in enumerate(laeufe):
        zeilen = stuecke.setdefault(wurzel(nummer), {})
        zeilen[y] = zeilen.get(y, 0) | lauf
    return sorted(stuecke.values(), key=lambda z: (min(z), min((b & -b).bit_length() for b in z.values())))


def _kern(zeilen: dict) -> dict:
    """Das Stück ohne seinen Rand (ein Bildpunkt): Dort verfehlt ein leicht versetztes KI-Bild nichts."""
    aus = {}
    for y, b in zeilen.items():
        innen = b & (b << 1) & (b >> 1) & zeilen.get(y - 1, 0) & zeilen.get(y + 1, 0)
        if innen:
            aus[y] = innen
    return aus


def _ausschnitt(zeilen: dict, x0: int, x1: int) -> dict:
    maske = ((1 << (x1 - x0 + 1)) - 1) << x0
    return {y: b & maske for y, b in zeilen.items() if b & maske}


def _punkte(zeilen: dict, breite: int) -> list:
    return [y * breite + x for y, b in sorted(zeilen.items()) for x in _bits_zu_x(b)]


def _ort(zeilen: dict) -> dict:
    alle = 0
    for b in zeilen.values():
        alle |= b
    return {"x0": (alle & -alle).bit_length() - 1, "y0": min(zeilen),
            "x1": alle.bit_length() - 1, "y1": max(zeilen)}


def _felder(zeilen: dict) -> list:
    """Ein breites Glasstück in überlappende Felder teilen; sonst das Stück selbst.

    Returns: ``[(x0, x1, zeilen des Felds)]`` — bei einem ungeteilten Stück genau ein Eintrag.
    """
    ort = _ort(zeilen)
    weite = ort["x1"] - ort["x0"] + 1
    n = sum(bin(b).count("1") for b in zeilen.values())
    hoehe = n / weite                              # die mittlere Höhe einer Spalte
    feld = max(FELD_MIN_BREITE, round(hoehe))
    if weite < FELD_AB_SEITENVERHAELTNIS * hoehe or weite < 2 * feld:
        return [(ort["x0"], ort["x1"], zeilen)]
    schritt = max(1, round(feld * FELD_SCHRITT_ANTEIL))
    anfaenge = list(range(ort["x0"], ort["x1"] - feld + 2, schritt))
    if anfaenge[-1] != ort["x1"] - feld + 1:
        anfaenge.append(ort["x1"] - feld + 1)
    teile = [(a, a + feld - 1, _ausschnitt(zeilen, a, a + feld - 1)) for a in anfaenge]
    # Ein schräg angeschnittenes Feld am Ende des Bands besteht fast nur aus Rand: weglassen.
    voll = sorted(sum(bin(b).count("1") for b in t[2].values()) for t in teile)[len(teile) // 2]
    return [t for t in teile if sum(bin(b).count("1") for b in t[2].values()) >= FELD_MIN_ANTEIL * voll]


def _lage_in_worten(ort: dict, breite: int, hoehe: int) -> str:
    mx, my = (ort["x0"] + ort["x1"]) / 2.0 / max(1, breite), (ort["y0"] + ort["y1"]) / 2.0 / max(1, hoehe)
    senkrecht = "oben" if my < 1 / 3 else ("unten" if my > 2 / 3 else "Mitte")
    waagrecht = "links" if mx < 1 / 3 else ("rechts" if mx > 2 / 3 else "Mitte")
    return "Bildmitte" if senkrecht == waagrecht == "Mitte" else f"{senkrecht} {waagrecht}".replace(
        "Mitte ", "mittig ").replace(" Mitte", " mittig")


def _haeufigster_stoff(kennung, aussen: dict, innen: dict, fassade_zeilen: dict, breite: int) -> list:
    """Die Fassadenpunkte des häufigsten Stoffs zwischen zwei gewachsenen Flächen.

    Nur der häufigste: Ein Rahmen, ein Stück Dach oder ein Sturz neben dem Fenster ist nicht die
    Wand, mit der das Glas verglichen werden soll.
    """
    stoffe: dict = {}
    for y, b in aussen.items():
        frei = b & ~innen.get(y, 0) & fassade_zeilen.get(y, 0)
        for x in _bits_zu_x(frei):
            i = y * breite + x
            stoffe.setdefault(tuple(kennung[i][:3]), []).append(i)
    return max(stoffe.values(), key=len) if stoffe else []


def _miss(ki, grund, kennung, zeilen: dict, kern: dict, fassade_zeilen: dict, breite: int) -> dict:
    """Ein Bauteil oder Feld gegen die Wand daneben: Kennzahlen und, wo es reicht, Regel 1 und 2."""
    voll = (1 << breite) - 1
    alle_i = _punkte(zeilen, breite)
    aus = {"n_glas": len(alle_i), "urteil": NICHT_MESSBAR, "art": None, "kontrast": None,
           "abstand_grund": None}
    if len(alle_i) < BAUTEIL_MIN_PUNKTE:
        return dict(aus, grund=f"Zu klein ({len(alle_i)} Bildpunkte, unter {BAUTEIL_MIN_PUNKTE}).")
    # NUR DER KERN ZÄHLT: Das KI-Bild sitzt oft einen Bildpunkt daneben, und am Rand eines
    # Fensters stünde dann Wand. Bleibt ohne Rand zu wenig übrig, wird nicht gemessen.
    glas_i = _punkte(kern, breite)
    if len(glas_i) < BAUTEIL_MIN_PUNKTE:
        return dict(aus, grund=f"Zu schmal (ohne Rand {len(glas_i)} Bildpunkte, unter "
                               f"{BAUTEIL_MIN_PUNKTE}).")
    glas_i = glas_i[::max(1, len(glas_i) // BAUTEIL_STICHPROBE)]
    median = _v._median_je_kanal                                       # noqa: SLF001
    glas_g = median([grund[i] for i in glas_i])
    # DIE WAND DANEBEN: der häufigste Stoff in einem Ring um das Bauteil. Der Ring reicht so weit
    # wie in v5 (sieben Bildpunkte) und bei grossen Bauteilen gut ein Drittel ihrer Höhe weit —
    # bei 1600 Bildpunkten Bildbreite ist ein Rahmen breiter als sieben Bildpunkte, und der Ring
    # läge sonst ganz im Rahmen (im achtfachen Massstab gemessen: jedes Fenster ein Fehlalarm).
    innen = _v._zeilen_wachsen(zeilen, _v.FENSTER_RING[0], voll)      # noqa: SLF001
    nah = _v._zeilen_wachsen(zeilen, _v.FENSTER_RING[1], voll)        # noqa: SLF001
    weite = round(RING_ANTEIL_HOEHE * len(zeilen))
    fern = _v._zeilen_wachsen(zeilen, weite, voll) if weite > _v.FENSTER_RING[1] else nah  # noqa: SLF001
    ring_i = _haeufigster_stoff(kennung, fern, innen, fassade_zeilen, breite)
    if len(ring_i) < _v.FENSTER_RING_MIN:
        return dict(aus, grund=f"Zu wenig Wand daneben ({len(ring_i)} Bildpunkte).")
    ring_i = ring_i[::max(1, len(ring_i) // BAUTEIL_STICHPROBE)]
    wand_g = median([grund[i] for i in ring_i])
    abstand_grund = _v._abstand(glas_g, wand_g)                        # noqa: SLF001
    if fern is not nah and abstand_grund < WAND_SCHWACH * _v.FENSTER_TRENNUNG_MIN:
        # HEBT SICH DAS GLAS VON DIESER WAND KAUM AB (helles Glas neben heller Wand, so im
        # Obergeschoss des Testhauses), dient der nächste Stoff als Massstab, wenn er klarer trennt.
        naechster_i = _haeufigster_stoff(kennung, nah, innen, fassade_zeilen, breite)
        naechster_i = naechster_i[::max(1, len(naechster_i) // BAUTEIL_STICHPROBE)]
        if len(naechster_i) >= _v.FENSTER_RING_MIN:
            naechster_g = median([grund[i] for i in naechster_i])
            if _v._abstand(glas_g, naechster_g) > abstand_grund:       # noqa: SLF001
                ring_i, wand_g = naechster_i, naechster_g
                abstand_grund = _v._abstand(glas_g, wand_g)            # noqa: SLF001
    aus["abstand_grund"] = round(abstand_grund, 1)
    if abstand_grund < _v.FENSTER_TRENNUNG_MIN:
        return dict(aus, grund=f"Im Grundbild sieht das Glas aus wie die Wand daneben (Abstand "
                               f"{abstand_grund:.1f} unter {_v.FENSTER_TRENNUNG_MIN:.0f}).")
    wand_roh = median([ki[i] for i in ring_i])
    unten, oben = _v.FENSTER_AUSGLEICH_GRENZE
    ausgleich = tuple(min(oben, max(unten, (wand_g[k] + 1.0) / (wand_roh[k] + 1.0))) for k in range(3))
    wand_k = tuple(wand_roh[k] * ausgleich[k] for k in range(3))
    punkte = [tuple(float(ki[i][k]) * ausgleich[k] for k in range(3)) for i in glas_i]
    glas_k = median(punkte)
    kontrast = _v._abstand(glas_k, wand_k) / abstand_grund             # noqa: SLF001
    blau_wand = _v._blau(wand_k)                                       # noqa: SLF001
    vorsprung_grund = _v._blau(glas_g) - _v._blau(wand_g)              # noqa: SLF001
    hell_wand = _helligkeit(wand_k)
    warm = sum(1 for p in punkte if _v._blau(p) - blau_wand <= -_v.FENSTER_FARBTON_TRENNUNG_MIN  # noqa: SLF001
               and _helligkeit(p) >= BAUTEIL_DUNKEL * hell_wand) / len(punkte)
    naehe = _v.FENSTER_ABHEBUNG_ANTEIL * abstand_grund
    wie_wand = sum(1 for p in punkte if _v._abstand(p, wand_k) <= naehe) / len(punkte)   # noqa: SLF001
    aus.update(urteil=GEHALTEN, kontrast=round(kontrast, 3), warm_anteil=round(warm, 3),
               wand_anteil=round(wie_wand, 3),
               _glas_g=glas_g, _roh=[ki[i] for i in glas_i], _wand_roh=wand_roh,
               _ton=_ton(median([ki[i] for i in glas_i])))
    if kontrast < _v.FENSTER_BAND_KONTRAST_ANTEIL and wie_wand >= BAUTEIL_ANTEIL:
        aus.update(urteil=UEBERMALT, art=ART_WAND)
    elif vorsprung_grund >= _v.FENSTER_FARBTON_TRENNUNG_MIN and warm >= BAUTEIL_ANTEIL:
        aus.update(urteil=UEBERMALT, art=ART_WARM)
    return aus


def _aus_der_reihe(felder: list) -> None:
    """Regel 3 über alle gehaltenen Felder: den Glaston verloren, den die Geschwister noch haben.

    Der Glaston ist das Verhältnis Blau zu Rot (als Logarithmus). Eine Stimmung verschiebt es bei
    allen Scheiben eines Bilds um denselben Betrag; der UNTERSCHIED zu den Geschwistern bleibt.
    Darum wird hier am rohen KI-Bild gemessen, ohne Ausgleich an der Wand.
    """
    abstand = _v._abstand                                              # noqa: SLF001
    kandidaten = [f for f in felder if f["urteil"] == GEHALTEN]
    funde = []
    for f in kandidaten:
        ton_grund = _ton(f["_glas_g"])
        if ton_grund < REIHE_TON_MIN:
            continue                               # das Glas hat im Grundbild selbst keinen Glaston
        geschwister = [
            g for g in kandidaten if g is not f
            and not (g["_stueck"] == f["_stueck"] and g["_x0"] <= f["_x1"] and f["_x0"] <= g["_x1"])
            and abstand(g["_glas_g"], f["_glas_g"]) < _v.FENSTER_TRENNUNG_MIN]
        if len(geschwister) < REIHE_GESCHWISTER_MIN:
            continue
        # KLAR UNTER DER REIHE, GEMESSEN AN IHRER EIGENEN STREUUNG: Scheiben eines Bilds spiegeln
        # verschieden (dunkel, Himmel, wie im Grundbild), und ihr Glaston streut entsprechend. Je
        # weiter die Geschwister auseinanderliegen, desto tiefer muss ein Feld darunter fallen.
        toene = sorted(g["_ton"] for g in geschwister)
        streuung = toene[(9 * (len(toene) - 1) + 5) // 10] - toene[(len(toene) - 1) // 10]
        grenze = toene[len(toene) // 2] - max(REIHE_TON_ANTEIL * ton_grund,
                                               REIHE_STREUUNG_FAKTOR * streuung)
        hell = BAUTEIL_DUNKEL * _helligkeit(f["_wand_roh"])
        entfaerbt = sum(1 for p in f["_roh"] if _ton(p) <= grenze and _helligkeit(p) >= hell) / len(f["_roh"])
        f["reihe_anteil"], f["_grenze"] = round(entfaerbt, 3), grenze
        if entfaerbt >= BAUTEIL_ANTEIL:
            funde.append(f)
    for f in funde:                                # erst am Ende: Ein Fund ändert die Geschwister nicht
        f.update(urteil=UEBERMALT, art=ART_REIHE)


def _bestaetigt(gruppe: list, ki, grund, kennung, zeilen: dict, kern: dict, fassade_zeilen: dict,
                breite: int) -> bool:
    """Trägt ein Fund im Band auch auf doppelter Feldbreite?

    Ein Feld ist so breit, wie das Band hoch ist; ein Vorhang kann es ganz decken. Ein Fenster ist
    breiter. Darum zählt ein Fund im Band erst, wenn auch auf doppelter Breite um seine Mitte
    mindestens :data:`BESTAETIGUNG_ANTEIL` der Bildpunkte betroffen sind.
    """
    feld = gruppe[0]["_x1"] - gruppe[0]["_x0"] + 1
    ort = _ort(zeilen)
    mitte = (min(f["_x0"] for f in gruppe) + max(f["_x1"] for f in gruppe) + 1) // 2
    x0 = max(ort["x0"], min(mitte - feld, ort["x1"] - 2 * feld + 1))
    x1 = min(ort["x1"], x0 + 2 * feld - 1)
    doppelt = _miss(ki, grund, kennung, _ausschnitt(zeilen, x0, x1), _ausschnitt(kern, x0, x1),
                    fassade_zeilen, breite)
    if doppelt["urteil"] == NICHT_MESSBAR:
        return False
    for f in gruppe:
        if f["art"] == ART_WAND and doppelt["wand_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        if f["art"] == ART_WARM and doppelt["warm_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        if f["art"] == ART_REIHE:
            hell = BAUTEIL_DUNKEL * _helligkeit(doppelt["_wand_roh"])
            roh = doppelt["_roh"]
            if sum(1 for p in roh if _ton(p) <= f["_grenze"] and _helligkeit(p) >= hell) \
                    >= BESTAETIGUNG_ANTEIL * len(roh):
                return True
    return False


def pruefe_indizes(ki, grund, kennung, glas_i, fassade_i, breite: int) -> dict:
    """Wie :func:`pruefe_bauteile`, aber mit den schon gesuchten Glas- und Fassadenpunkten."""
    hoehe = len(kennung) // breite if breite else 0
    fassade_zeilen = _v._zeilen_bits(fassade_i, breite)                # noqa: SLF001
    felder = []
    stuecke = glasstuecke(_v._zeilen_bits(glas_i, breite))             # noqa: SLF001
    for nr, zeilen in enumerate(stuecke):
        kern = _kern(zeilen)
        teile = _felder(zeilen)
        for x0, x1, feld_zeilen in teile:
            if not feld_zeilen:
                continue
            feld = _miss(ki, grund, kennung, feld_zeilen, _ausschnitt(kern, x0, x1) if len(teile) > 1
                         else kern, fassade_zeilen, breite)
            feld.update(_stueck=nr, _x0=x0, _x1=x1, _zeilen=feld_zeilen, _geteilt=len(teile) > 1)
            felder.append(feld)
    _aus_der_reihe(felder)
    bauteile = []
    for nr, zeilen in enumerate(stuecke):
        eigene = [f for f in felder if f["_stueck"] == nr]
        geteilt = bool(eigene) and eigene[0]["_geteilt"]
        # Nebeneinanderliegende übermalte Felder zu EINEM Fund zusammenziehen.
        gruppen: list = []
        for f in sorted((f for f in eigene if f["urteil"] == UEBERMALT), key=lambda f: f["_x0"]):
            if gruppen and f["_x0"] <= gruppen[-1][-1]["_x1"] + 1:
                gruppen[-1].append(f)
            else:
                gruppen.append([f])
        if geteilt:
            for gruppe in gruppen:
                if not _bestaetigt(gruppe, ki, grund, kennung, zeilen, _kern(zeilen), fassade_zeilen,
                                   breite):
                    for f in gruppe:               # zu schmal für ein Fenster: kein Fund
                        f.update(urteil=GEHALTEN, art=None, schmal=True)
            gruppen = [g for g in gruppen if g[0]["urteil"] == UEBERMALT]
        for gruppe in gruppen:
            flaeche: dict = {}
            for f in gruppe:
                for y, b in f["_zeilen"].items():
                    flaeche[y] = flaeche.get(y, 0) | b
            schlimmstes = min(gruppe, key=lambda f: f["kontrast"])
            bauteile.append({"urteil": UEBERMALT, "art": schlimmstes["art"], "ort": _ort(flaeche),
                             "n_glas": sum(bin(b).count("1") for b in flaeche.values()),
                             "kontrast": schlimmstes["kontrast"], "feld": geteilt, "glasstueck": nr})
        messbar = [f for f in eigene if f["urteil"] != NICHT_MESSBAR]
        if gruppen and not geteilt:
            continue                               # ein ungeteiltes Stück ist sein eigener Fund
        rest = {"urteil": GEHALTEN if messbar else NICHT_MESSBAR, "art": None, "ort": _ort(zeilen),
                "n_glas": sum(bin(b).count("1") for b in zeilen.values()),
                "kontrast": None,
                "feld": False, "glasstueck": nr}
        if geteilt:
            rest.update(felder=len(eigene), felder_uebermalt=sum(len(g) for g in gruppen))
            if gruppen:
                rest["urteil"] = GEHALTEN if len(messbar) > rest["felder_uebermalt"] else UEBERMALT
                if rest["urteil"] == UEBERMALT:
                    continue                       # das ganze Band ist übermalt: Der Fund steht schon da
        heil = sorted(f["kontrast"] for f in messbar if f["urteil"] == GEHALTEN)
        if heil:
            rest["kontrast"] = heil[len(heil) // 2]
        if not messbar:
            rest["grund"] = next((f.get("grund") for f in eigene if f.get("grund")), "Nicht messbar.")
        bauteile.append(rest)
    bauteile.sort(key=lambda b: (b["ort"]["y0"], b["ort"]["x0"], b["urteil"] != UEBERMALT))
    for nr, b in enumerate(bauteile):
        b["nr"] = nr
        b["lage"] = _lage_in_worten(b["ort"], breite, hoehe)
    uebermalt = [b["nr"] for b in bauteile if b["urteil"] == UEBERMALT]
    return {"bauteile": bauteile, "uebermalt": uebermalt, "hinweis": _hinweis(bauteile),
            "methode": METHODE_BAUTEILE}


def _hinweis(bauteile: list) -> str | None:
    """Der Satz für den Bericht der Kamera — ``None``, wenn kein Bauteil übermalt ist."""
    funde = [b for b in bauteile if b["urteil"] == UEBERMALT]
    if not funde:
        return None
    gemessen = sum(1 for b in bauteile if b["urteil"] != NICHT_MESSBAR)
    orte = "; ".join(
        f"Bauteil {b['nr']} ({b['lage']}, Bildpunkte x {b['ort']['x0']} bis {b['ort']['x1']}, "
        f"y {b['ort']['y0']} bis {b['ort']['y1']}: {b['art']})" for b in funde[:6])
    mehr = f" und {len(funde) - 6} weitere" if len(funde) > 6 else ""
    return (f"{SATZ_BAUTEIL_UEBERMALT} (Hinweis, kein Urteil): {len(funde)} von {gemessen} gemessenen "
            f"Glasbauteilen sehen im KI-Bild nicht mehr aus wie Glas — {orte}{mehr}. Am Bild pruefen.")


def pruefe_bauteile(ki, grund, kennung, glas: set, *, breite: int, maske=None, ausser=()) -> dict:
    """Je Glasbauteil des ID-Passes: «gehalten», «uebermalt» oder «nicht messbar», mit Ort.

    Args:
        ki, grund, kennung: Farben je Bildpunkt (gleich lang) — KI-Bild, Grundbild und
            Material-ID-Pass.
        glas: die Kennfarben des Glases (``varianten.glasfarben``).
        breite: Bildbreite in Bildpunkten; ohne sie gibt es keinen Ort.
        maske: die Bauwerksmaske; ohne sie zählt jeder Punkt, der im ID-Pass nicht schwarz ist.
        ausser: Kennfarben, die nicht zur Fassade zählen (Umfeld, Gelände).

    Returns:
        ``{bauteile, uebermalt, hinweis, methode}`` — ``bauteile`` ist eine Liste von
        ``{nr, urteil, art, ort: {x0, y0, x1, y1}, lage, n_glas, kontrast, feld, glasstueck,
        grund?}``, von oben links nach unten rechts. ``feld`` sagt, ob der Fund ein Teil eines
        breiten Glasstücks ist (ein Fenster im Band). ``uebermalt`` nennt die Nummern,
        ``hinweis`` ist der Satz für den Bericht oder ``None``.
    """
    n = len(kennung)
    if not breite or breite <= 0 or n % breite:
        raise ValueError(f"Die Breite {breite!r} passt nicht zu {n} Bildpunkten.")
    if len(ki) != n or len(grund) != n or (maske is not None and len(maske) != n):
        raise ValueError(f"Ungleiche Laengen: KI {len(ki)}, Grundbild {len(grund)}, ID-Pass {n}, "
                         f"Maske {None if maske is None else len(maske)}.")
    ausser = {tuple(int(k) for k in f[:3]) for f in ausser or ()}
    glas_i, fassade_i = [], []
    for i, k in enumerate(kennung):
        k = tuple(k[:3])
        if not (maske[i] if maske is not None else k != (0, 0, 0)):
            continue
        if k in glas:
            glas_i.append(i)
        elif k not in ausser:
            fassade_i.append(i)
    return pruefe_indizes(ki, grund, kennung, glas_i, fassade_i, breite)
