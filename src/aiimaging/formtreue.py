"""Formtreue je Baukörper: hält JEDER Bau einer Anlage seine Form (A0300)?

**Anlass (Wettbewerbsmodell, 24.10.2026, Zelle B2C3):** Die KI löste das Hauptgebäude mit Hof in
grüne Flecken auf und die Halle in eine glatte Platte, und das Ergebnis hiess «deckungsgleich»:
Kanten-Deckung am Haus 0,256 gegen die Schwelle 0,25. Die Deckung (``varianten.deckung``) zählt
die Kanten über die GANZE Hausfläche in einen Topf. In einer Anlage halten die Nebenbauten ihre
Kanten und heben die Zahl über die Schwelle; der aufgelöste Bau geht darin unter.

**Die Regel.** Die Hausfläche (Bauwerksmaske ohne Umfeld und Gelände, wie die Deckung sie
nimmt) wird in ihre zusammenhängenden Stücke zerlegt, das sind die **Baukörper**. Je
Baukörper wird gemessen, wie viel der Zeichnung des Grundbilds in seinem **Inneren** im
KI-Bild **erhalten** ist (:func:`inneres`):

* ohne einen Saum von 2 Bildpunkten: Der Umriss gegen den Grund deckt sich fast immer und hob
  am synthetischen Satz eine glatte Platte allein auf bis zu 0,40;
* am besten Versatz samt Dehnung (ein KI-Bild liegt selten bildpunktgenau), mit bis zu zwei
  Bildpunkten Toleranz;
* ohne Zufallstreffer: Dichte Kanten (Laub, Flecken) treffen die alten auch dann, wenn vom Bau
  nichts mehr da ist; dieser Anteil ist messbar und wird abgezogen.

Ist weniger als die bestehende Schwelle erhalten (``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``),
ist die Zeichnung **verloren** (:func:`verloren`):

* Gilt das für das ganze Innere, heisst der Baukörper **«aufgelöst»**.
* Gilt es in mindestens einem Drittel der Prüffenster, die das Innere decken, heisst er
  **«verfleckt»**, auch wenn sein Mittel besteht.
* Steht die Zeichnung, liegt aber die Kanten-Deckung unter der Schwelle, heisst er
  **«dazugemalt»**: gemeldet, ohne Warnung. Ob die KI Material gemalt hat oder neue Fenster,
  entscheiden Kanten allein nicht (dieselben Daten, zwei Wahrheiten).

Hält ein Baukörper nicht, weicht die Form ab, und das Urteil sagt, WELCHER: Nummer (1 = der
grösste), Ort im Bild, Kasten in Bildpunkten.

**Nie milder als heute, am Einzelhaus gleich.** Je Baukörper wird nur in einer **Anlage**
geurteilt: Neben dem grössten Baukörper decken die übrigen mindestens :data:`ANLAGE_AB_REST`
der Hausfläche. Für ein einzelnes Haus bleibt die Deckung über das ganze Haus das Urteil; sie
ist dort am Gerät gesetzt. Was die Deckung «Form weicht ab» nennt, bleibt es in jedem Fall.

**Nie still.** Wo nicht geurteilt werden kann, steht es mit Grund im Ergebnis (``hinweise``,
Satzanfang :data:`SATZ_NICHT_GEMESSEN`): keine Anlage; ein Baukörper, dessen Inneres im
Grundbild weniger als :data:`KOERPER_MIN_KANTEN` Kantenpunkte trägt (keine Zeichnung, die
verloren gehen könnte); ein KI-Bild, das dort so dicht an Kanten ist, dass Treffer Zufall
wären; eine erreichte Kantenquote; eine Zeichnung, die für ein knappes Urteil zu fein ist.

**Bekannte Grenzen (gemessen am Satz des Gegenlesens, 313 Paare, 10.11.2026).**

* Unschärfe auf sehr feinem Fensterraster bei erreichter Kantenquote: 4 Fehlalarme auf 194
  intakte Bilder. Mit :data:`FEIN_STRENG` wären es 0, dafür hiessen 31 statt 12 von 104
  aufgelösten «nicht gemessen».
* Ein um seine halbe Breite verschobener Nebenbau geht durch, wenn sein Fensterraster sich
  nach wenigen Bildpunkten wieder mit sich selbst deckt: Die Suche nach dem Versatz folgt ihm.
* Eine neue Kante zwei Bildpunkte neben einer verlorenen zählt als die alte (Toleranz).
* Ein im Grundbild glatter Bau, der zu Flecken wird, bleibt «nicht gemessen».
* Baukörper, die sich im Bild berühren oder überdecken (Schrägsicht), sind EIN Stück. Wer sie
  trennen kann (ein Kennpass je Bau), übergibt die Zerlegung selbst (``koerper_karte``).
* «Verfleckt» kippt nicht an einer scharfen Kante, sondern in einem Übergang.
* Alles je Baukörper ist **gesetzt, nicht geeicht**; die Eichung am echten Bild (wie gross ist
  der Versatz im Betrieb wirklich?) ist ein Messauftrag für das Gerät.
* Die Kantenfindung lässt höchstens die stärksten 15 % der Bildpunkte als Kante gelten
  (``umriss.KANTEN_QUANTIL``); ist das erreicht, steht es als Hinweis im Ergebnis.

Reine stdlib, ohne Oberfläche aufrufbar (Regel 4): :func:`formtreue` aus Bilddaten,
:func:`formtreue_aus_bildern` aus zwei Dateien, :func:`deckung_und_formtreue_aus_bildern` für
die Stelle, die das Deckungsurteil bildet (``abholer.deckung_der_kamera``).
"""
from __future__ import annotations

from collections.abc import Sequence

#: Eine ANLAGE: Neben dem grössten Baukörper decken die übrigen zusammen mindestens diesen
#: Teil der Hausfläche. Gesetzt: 10 %. Darunter ist das Bild ein Einzelhaus (auch mit einem
#: Schopf), und es gilt allein die Deckung über das ganze Haus, wie am Gerät gesetzt.
#: (Bis zur Runde 2 zählte «zwei Baukörper von je 1 % der Bildfläche»; bei 5 % Hausanteil
#: trugen dann Nebenbauten von je 0,7 % die Hauszahl, und der aufgelöste Hauptbau blieb still.)
ANLAGE_AB_REST = 0.10
#: Ab dieser Grösse wird ein Baukörper im Ergebnis genannt, auch wenn er kein Urteil bekommt.
KOERPER_MIN_ANTEIL = 0.01
#: So viele Kantenpunkte muss das Grundbild im Inneren eines Baukörpers haben, damit er ein
#: Urteil bekommt. Gesetzt: 150, so viel, wie ein Prüffenster im Mittel trägt
#: (:data:`FENSTER_KANTEN`). Gemessen am 10.11.2026 mit 24: Ein Nebenbau mit fünf Öffnungen
#: verlor bei 24 % zufälligem Verlust vier davon und hiess «aufgelöst»; an so wenig Zeichnung
#: ist das Urteil Zufall.
KOERPER_MIN_KANTEN = 150
#: Der Saum am Rand eines Baukörpers, der nicht zählt: 2 Bildpunkte, dieselbe Zahl wie
#: ``umriss.TOLERANZ_PX``. Der Umriss gegen den Grund deckt sich fast immer (mit «Umriss
#: halten» sicher) und sagt nichts darüber, ob das Innere noch der Bau ist.
SAUM_PX = 2
#: So weit darf das KI-Bild je Baukörper gegen das Grundbild versetzt liegen: Der beste Versatz
#: wird in diesem Umkreis gesucht (Bildpunkte, waagrecht und senkrecht). Gesetzt: 6, für einen
#: Versatz bis 4 Bildpunkte plus den Rest einer Skalierung um 3 %. **Anlass (Gegenlesen
#: 10.11.2026):** Ohne Suche hiessen 32 von 52 intakten, um 2 bis 5 Bildpunkte versetzten oder
#: um 2 bis 3 % skalierten Anlagen «Form weicht ab».
SUCHE_PX = 6
#: Die Dehnungen, die die Suche je Baukörper zusätzlich probiert (KI-Bild um so viel grösser
#: oder kleiner als das Grundbild, um die Mitte des Baukörpers). Die erste gewinnt bei
#: Gleichstand. Gesetzt: bis 3 %, in Schritten von 1 %. **Anlass (Runde 2):** Ein Versatz
#: allein fängt eine Skalierung nicht, der Bau verzieht sich in sich; um 2 bis 3 % skalierte
#: intakte Anlagen hiessen sonst in 37 von 52 Fällen «verfleckt».
SKALEN = (0.0, -0.01, 0.01, -0.02, 0.02, -0.03, 0.03)
#: Reserve am Rand der gepolsterten Karte (Bildpunkte).
FEIN_PX = 2
#: Ist die Karte des KI-Bilds im Inneren eines Baukörpers so dicht, dass sie an diesem Teil
#: aller Punkte trifft, sagen Treffer nichts mehr: Der Baukörper heisst «nicht gemessen».
ZUFALL_MAX = 0.75
#: Die Grösse des Prüffensters: so gross, dass es im Mittel so viele Kantenpunkte des
#: Grundbilds aus dem Inneren des Baukörpers trägt. Gesetzt: 150. Dichte Zeichnung, kleines
#: Fenster.
FENSTER_KANTEN = 150
#: So viele Kantenpunkte des Grundbilds muss ein Fenster tragen, damit es zählt. Gesetzt: 30.
FENSTER_MIN_KANTEN = 30
#: So viele zählende Fenster braucht ein Baukörper für ein örtliches Urteil.
FENSTER_MIN_ANZAHL = 12
#: So oft muss das Fenster in das Innere des Baukörpers passen (nach Fläche). Gesetzt: 2.
FENSTER_MIN_FLAECHEN = 2
#: Ab diesem Anteil der Fenster, in denen die Zeichnung verloren ist, heisst ein Baukörper
#: «verfleckt». **Gesetzt: ein Drittel, am synthetischen Satz geprüft, nicht geeicht.** Ein
#: Mass («ein Drittel des Baus»), keine Kante, die zwei Lager trennt.
VERFLECKT_AB_ANTEIL = 1.0 / 3.0
#: Ab diesem Anteil der Bildpunkte gilt die Kantenquote als erreicht (``umriss.KANTEN_QUANTIL``
#: lässt höchstens 15 % zu). Dann können schwächere Kanten eines gehaltenen Baus fehlen.
KANTENQUOTE_AB = 0.148
#: Liegt der Anteil sogar darüber, haben mehr Bildpunkte dieselbe Kantenstärke, als die Quote
#: zulässt (Gleichstand): Die Auswahl ist dann zufällig, je Baukörper wird nicht geurteilt.
KANTENQUOTE_GLEICHSTAND = 0.16
#: Soll bei feiner Zeichnung und erreichter Quote des Grundbilds auch «aufgelöst» als nicht
#: entscheidbar gelten? Gemessen am Gegenlese-Satz (10.11.2026, 313 Paare): ohne 4 Fehlalarme
#: auf 194 intakte und 12 von 104 aufgelösten «nicht gemessen»; mit 0 Fehlalarme, aber 31 von
#: 104 «nicht gemessen». Gesetzt: aus. Die vier Fehlalarme (Unschärfe auf sehr feinem
#: Fensterraster) stehen als bekannte Grenze in den Proben.
FEIN_STRENG = False

GEHALTEN = "gehalten"
AUFGELOEST = "aufgeloest"
VERFLECKT = "verfleckt"
#: Die Zeichnung des Grundbilds ist erhalten, aber die KI hat so viel dazugemalt, dass die
#: Kanten-Deckung im Inneren unter der Schwelle liegt. Nicht entscheidbar (Material oder neue
#: Fenster?): gemeldet, aber ohne Warnung, das Urteil bleibt das der Deckung über das Haus.
DAZUGEMALT = "dazugemalt"
UNGEMESSEN = "ungemessen"

#: Das Urteil über alle Baukörper. Die Wörter sind die der Deckung, damit beide Urteile
#: nebeneinander lesbar sind (``varianten.DECKUNGSGLEICH`` usw.).
DECKUNGSGLEICH = "deckungsgleich"
FORM_WEICHT_AB = "form_weicht_ab"

HERKUNFT = ("Schwelle der Deckung (gesetzt aus auf-20261022-337 und -339), je Baukörper auf "
            "den erhaltenen Teil der Zeichnung angewandt (bester Versatz, Zufallstreffer "
            "abgezogen); gesetzt am synthetischen Satz, am echten Bild nicht geeicht (A0300)")

#: Der Anfang des Satzes je Baukörper, der seine Form nicht hält.
SATZ_BAUKOERPER = "BAUKÖRPER HÄLT DIE FORM NICHT"
#: Der Anfang eines Hinweises, wo je Baukörper nicht geurteilt werden konnte.
SATZ_NICHT_GEMESSEN = "FORM JE BAUKÖRPER NICHT GEMESSEN"


class FormtreueError(ValueError):
    """Die Eingaben passen nicht zusammen (ungleiche Masse)."""


def _ort(kasten, breite: int, hoehe: int) -> str:
    """Wo der Baukörper im Bild liegt, in Worten: Drittel des Bilds nach seinem Mittelpunkt."""
    mx, my = (kasten[0] + kasten[2]) / 2.0, (kasten[1] + kasten[3]) / 2.0
    waag = "links" if mx < breite / 3.0 else ("rechts" if mx >= 2.0 * breite / 3.0 else "Mitte")
    senk = "oben" if my < hoehe / 3.0 else ("unten" if my >= 2.0 * hoehe / 3.0 else "Mitte")
    if waag == "Mitte" and senk == "Mitte":
        return "Bildmitte"
    if senk == "Mitte":
        return f"{waag}, mittlere Höhe" if waag != "Mitte" else "Bildmitte"
    return f"{senk} {waag}" if waag != "Mitte" else f"{senk} Mitte"


def baukoerper(bereich: Sequence[bool], breite: int, hoehe: int) -> list[dict]:
    """Die zusammenhängenden Stücke des Hausbereichs, das grösste zuerst.

    Zusammenhängend heisst: über Kante oder Ecke benachbart (acht Nachbarn), damit eine
    schräge Wand, die im Raster treppt, nicht in Stücke zerfällt.

    Returns:
        Je Stück ``{nr, n, anteil_bild, kasten, ort, punkte}``; ``nr`` zählt ab 1 nach Grösse
        (bei gleicher Grösse nach Lage von oben links), ``kasten`` ist ``(x0, y0, x1, y1)``
        mit ausschliessendem Ende, ``punkte`` die Bildpunkt-Nummern (Zeile mal Breite plus Spalte).
    """
    n = breite * hoehe
    if len(bereich) != n:
        raise FormtreueError(f"Bereich hat {len(bereich)} Punkte, erwartet {breite}x{hoehe}={n}.")
    gesehen = bytearray(n)
    stuecke = []
    for start in range(n):
        if not bereich[start] or gesehen[start]:
            continue
        gesehen[start] = 1
        stapel, punkte = [start], []
        x0 = x1 = start % breite
        y0 = y1 = start // breite
        while stapel:
            i = stapel.pop()
            punkte.append(i)
            y, x = divmod(i, breite)
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
            for ny in (y - 1, y, y + 1):
                if not 0 <= ny < hoehe:
                    continue
                for nx in (x - 1, x, x + 1):
                    if 0 <= nx < breite:
                        j = ny * breite + nx
                        if bereich[j] and not gesehen[j]:
                            gesehen[j] = 1
                            stapel.append(j)
        stuecke.append({"n": len(punkte), "kasten": (x0, y0, x1 + 1, y1 + 1), "punkte": punkte})
    stuecke.sort(key=lambda s: (-s["n"], s["kasten"][1], s["kasten"][0]))
    for nr, s in enumerate(stuecke, start=1):
        s["nr"] = nr
        s["anteil_bild"] = round(s["n"] / n, 4) if n else 0.0
        s["ort"] = _ort(s["kasten"], breite, hoehe)
    return stuecke


def _aus_karte(koerper_karte: Sequence, bereich: Sequence[bool], breite: int,
               hoehe: int) -> list[dict]:
    """Baukörper aus einer fertigen Zerlegung (ein Kennwert je Bildpunkt, ``None``/0 = keiner)."""
    n = breite * hoehe
    if len(koerper_karte) != n:
        raise FormtreueError(f"Körperkarte hat {len(koerper_karte)} Punkte, das Bild {n}.")
    je = {}
    for i, (k, m) in enumerate(zip(koerper_karte, bereich)):
        if m and k:
            je.setdefault(k, []).append(i)
    stuecke = []
    for kennung, punkte in je.items():
        xs = [i % breite for i in punkte]
        ys = [i // breite for i in punkte]
        stuecke.append({"n": len(punkte), "punkte": punkte, "kennung": kennung,
                        "kasten": (min(xs), min(ys), max(xs) + 1, max(ys) + 1)})
    stuecke.sort(key=lambda s: (-s["n"], s["kasten"][1], s["kasten"][0]))
    for nr, s in enumerate(stuecke, start=1):
        s["nr"] = nr
        s["anteil_bild"] = round(s["n"] / n, 4) if n else 0.0
        s["ort"] = _ort(s["kasten"], breite, hoehe)
    return stuecke


def name_des_baukoerpers(k: dict) -> str:
    """«Baukörper 1 (der grösste, Bildmitte)»: Nummer nach Grösse und Ort im Bild."""
    zusatz = "der grösste, " if k.get("nr") == 1 else ""
    return f"Baukörper {k.get('nr')} ({zusatz}{k.get('ort')})"


def verloren(erhalten: float | None, schwelle: float) -> bool:
    """Hat ein Stück Bild seine Zeichnung verloren? Die EINE Regel, im Ganzen wie im Fenster.

    ``erhalten`` ist der Teil der Kantenpunkte des Grundbilds, der im KI-Bild noch da ist: am
    besten Versatz gezählt und um die Zufallstreffer bereinigt (:func:`inneres`). Verloren
    heisst: weniger als die Schwelle der Deckung. Weil die Kanten-Deckung nie über dem
    erhaltenen Teil liegt, ist das nie strenger als der Massstab der Deckung am Einzelhaus.
    Was die KI dazumalt, zählt hier nicht: Es senkt die Deckung, nicht den erhaltenen Teil.
    """
    return erhalten is not None and erhalten < schwelle


#: Die Versätze der Suche, die kleinen zuerst.
_VERSAETZE = sorted(((dx, dy) for dy in range(-SUCHE_PX, SUCHE_PX + 1)
                     for dx in range(-SUCHE_PX, SUCHE_PX + 1)),
                    key=lambda v: (abs(v[0]) + abs(v[1]), v))


def _netto(treffer: float, zufall: float) -> float | None:
    """Der erhaltene Teil ohne Zufallstreffer: 0 = nicht besser als Zufall, 1 = alles da."""
    if zufall >= ZUFALL_MAX:
        return None
    return max(0.0, (treffer - zufall) / (1.0 - zufall))


def inneres(punkte: Sequence[int], kanten_ki: Sequence[bool], kanten_grund: Sequence[bool],
            breite: int, hoehe: int, kasten, *, schwelle: float) -> dict | None:
    """Das Innere EINES Baukörpers: wie viel seiner Zeichnung im KI-Bild erhalten ist.

    **Ohne den Saum** (:data:`SAUM_PX`): Der Umriss eines Baus gegen den Grund deckt sich fast
    immer; eine glatte Platte anstelle des Hauptbaus kam allein darüber auf 0,20 bis 0,43.

    **Am besten Versatz** (:data:`SUCHE_PX`): Ein KI-Bild liegt selten bildpunktgenau. Gesucht
    wird EIN Versatz je Baukörper, an dem die meisten Kantenpunkte des Grundbilds im KI-Bild
    Kante sind. Gezählt wird dort genau und mit einem Bildpunkt Toleranz.

    **Ohne Zufallstreffer**: Dichte Kanten (Laub, Flecken) treffen die alten Kanten auch dann,
    wenn vom Bau nichts mehr da ist. Der Zufall ist messbar: der Teil ALLER Punkte des
    Inneren, an dem die Karte des KI-Bilds eine Kante hat. Er wird abgezogen:
    ``erhalten = (treffer - zufall) / (1 - zufall)``.

    **Örtlich**: Dasselbe je Prüffenster (Grösse nach :data:`FENSTER_KANTEN`, halb überlappend);
    ``anteil`` ist der Teil der Fenster, in denen die Zeichnung verloren ist.

    Returns:
        ``None`` ohne Inneres. Sonst ``{innen, kanten_grundbild, kanten_ki, versatz, treffer,
        zufall, erhalten, kanten_iou, anteil, verfleckt, halbe_seite_px, fenster,
        fenster_darunter}``. ``erhalten`` ist ``None``, wenn das Grundbild im Inneren keine
        Kante hat oder die Karte des KI-Bilds dort zu dicht ist (:data:`ZUFALL_MAX`);
        ``anteil`` ist ``None``, wenn das Fenster keine :data:`FENSTER_MIN_FLAECHEN` Mal in
        das Innere passt oder weniger als :data:`FENSTER_MIN_ANZAHL` Fenster zählen.
    """
    x0, y0, x1, y1 = kasten
    b, h = x1 - x0, y1 - y0
    if b <= 2 * SAUM_PX or h <= 2 * SAUM_PX:
        return None
    drin = bytearray(b * h)
    for i in punkte:
        y, x = divmod(i, breite)
        drin[(y - y0) * b + (x - x0)] = 1
    # Summentafel über «gehört zum Baukörper»: das Innere sind die Punkte, deren Umgebung
    # von SAUM_PX ganz im Baukörper liegt.
    tafel = [0] * ((b + 1) * (h + 1))
    for yy in range(h):
        lauf, oben, zeile = 0, yy * (b + 1), (yy + 1) * (b + 1)
        for xx in range(b):
            lauf += drin[yy * b + xx]
            tafel[zeile + xx + 1] = tafel[oben + xx + 1] + lauf
    voll = (2 * SAUM_PX + 1) ** 2
    rand = SUCHE_PX + FEIN_PX + 2 + int(max(abs(k) for k in SKALEN) * max(b, h) / 2.0 + 1)
    pb = breite + 2 * rand                       # die Karte des KI-Bilds mit Rand: kein Abfragen der Grenzen
    ki = bytearray(pb * (hoehe + 2 * rand))
    nah = bytearray(pb * (hoehe + 2 * rand))     # Kante des KI-Bilds hier oder einen Punkt daneben
    weit = bytearray(pb * (hoehe + 2 * rand))    # ... oder bis zwei Punkte daneben
    innen_punkte, grund, n_ki = [], [], 0        # alle Punkte des Inneren; davon Kanten des Grundbilds
    grund_nah = bytearray(b * h)                 # Kante des Grundbilds hier oder einen Punkt daneben
    for yy in range(SAUM_PX, h - SAUM_PX):
        for xx in range(SAUM_PX, b - SAUM_PX):
            if not drin[yy * b + xx]:
                continue
            ax, ay, bx, by = xx - SAUM_PX, yy - SAUM_PX, xx + SAUM_PX + 1, yy + SAUM_PX + 1
            if (tafel[by * (b + 1) + bx] - tafel[ay * (b + 1) + bx]
                    - tafel[by * (b + 1) + ax] + tafel[ay * (b + 1) + ax]) != voll:
                continue
            gepolstert = (y0 + yy + rand) * pb + x0 + xx + rand
            bild = (y0 + yy) * breite + x0 + xx
            ist_kante = bool(kanten_grund[bild])
            innen_punkte.append((gepolstert, xx, yy, ist_kante))
            if ist_kante:
                grund.append((gepolstert, xx, yy))
                for oy in (-1, 0, 1):
                    for ox in (-1, 0, 1):
                        grund_nah[(yy + oy) * b + xx + ox] = 1
            # Nur Kanten des KI-Bilds IM Inneren zählen: Sonst findet die Suche nach dem
            # Versatz den stehen gebliebenen Umriss und hält ihn für Zeichnung (gemessen an
            # der glatten Platte: 41 bis 56 % «Treffer» bei Versatz 3).
            if kanten_ki[bild]:
                n_ki += 1
                ki[gepolstert] = 1
                for o in (-pb - 1, -pb, -pb + 1, -1, 0, 1, pb - 1, pb, pb + 1):
                    nah[gepolstert + o] = 1
                for oy in (-2 * pb, -pb, 0, pb, 2 * pb):
                    for ox in (-2, -1, 0, 1, 2):
                        weit[gepolstert + oy + ox] = 1
    n_innen = len(innen_punkte)
    if not n_innen:
        return None
    fein = sum(grund_nah[yy * b + xx] for _, xx, yy, _ in innen_punkte) / n_innen
    aus = {"innen": n_innen, "kanten_grundbild": len(grund), "kanten_ki": n_ki,
           "zeichnung_dichte": round(fein, 4),
           "versatz": [0, 0], "treffer": None, "zufall": None, "erhalten": None,
           "kanten_iou": None, "anteil": None, "verfleckt": False}
    if not grund:
        return aus
    # ---- der beste Versatz des Baukörpers samt Skalierung (an einer Auswahl der Punkte)
    auswahl = grund[::max(1, len(grund) // 4000)]
    mx, my = b / 2.0, h / 2.0

    def dehnung(skala: float, xx: int, yy: int) -> int:
        """Der Versatz eines Punkts, wenn das KI-Bild um ``skala`` gedehnt ist (um die Mitte)."""
        return int(round(skala * (yy - my))) * pb + int(round(skala * (xx - mx)))
    best = (-1, 0, 0, 0.0)
    for skala in SKALEN:
        punkte_s = [i + dehnung(skala, xx, yy) for i, xx, yy in auswahl]
        for dx, dy in _VERSAETZE:
            if True:
                o = dy * pb + dx
                treffer = sum(ki[i + o] for i in punkte_s)
                if treffer > best[0]:              # bei Gleichstand gilt der frühere, kleinere
                    best = (treffer, dx, dy, skala)
    _, vx, vy, skala = best
    aus["versatz"], aus["skala"] = [vx, vy], round(1.0 + skala, 2)

    def versatz_bei(xx: int, yy: int) -> int:
        return vy * pb + vx + dehnung(skala, xx, yy)
    genau = sum(ki[i + versatz_bei(xx, yy)] for i, xx, yy in grund)
    aus["kanten_iou"] = round(genau / max(1, len(grund) + n_ki - genau), 4)
    # ---- Fenster: halb überlappend; je Punkt bis zu vier Fenster. Je Fenster acht Zähler:
    # Punkte, Kante-KI genau/nah/weit, Kanten des Grundbilds, davon getroffen genau/nah/weit.
    r = max(3, int(round((FENSTER_KANTEN * n_innen / len(grund)) ** 0.5 / 2.0)))
    aus["halbe_seite_px"] = r
    oertlich = n_innen >= FENSTER_MIN_FLAECHEN * (2 * r + 1) ** 2
    zaehler: dict = {}
    ganz = [0] * 8
    for gepolstert, xx, yy, ist_kante in innen_punkte:
        versatz = versatz_bei(xx, yy)
        ziel = gepolstert + versatz
        k0, k1, k2 = ki[ziel], nah[ziel], weit[ziel]
        if not (k2 or ist_kante) and not oertlich:
            ganz[0] += 1
            continue
        werte = (1, k0, k1, k2, ist_kante, ist_kante and k0, ist_kante and k1,
                 ist_kante and k2)
        for j in range(8):
            ganz[j] += werte[j]
        if oertlich:
            fx, fy = xx // r, yy // r
            for fen in ((fx - 1, fy - 1), (fx, fy - 1), (fx - 1, fy), (fx, fy)):
                z = zaehler.get(fen)
                if z is None:
                    z = zaehler[fen] = [0] * 8
                for j in range(8):
                    z[j] += werte[j]

    def erhalten_aus(z) -> tuple[float | None, float, float]:
        """``(erhalten, treffer, zufall)`` eines Fensters oder des Ganzen.

        Dreimal gerechnet: genau, mit einem und mit zwei Punkten Toleranz (zwei wie
        ``umriss.TOLERANZ_PX``), je um den Zufall bereinigt (der Zufall ist der Teil ALLER
        Punkte, an dem die Karte des KI-Bilds mit dieser Toleranz trifft); es gilt der beste
        Wert. Die Toleranz fängt Fenster, die um einen Punkt wandern, und den Rest einer
        Skalierung; wo das KI-Bild dafür zu dicht ist, bleibt die genauere Zählung.
        """
        n, d0, d1, d2, g, h0, h1, h2 = z
        bestes = None
        for treffer, zufall in ((h0 / g, d0 / n), (h1 / g, d1 / n), (h2 / g, d2 / n)):
            netto = _netto(treffer, zufall)
            if netto is not None and (bestes is None or netto > bestes[0]):
                bestes = (netto, treffer, zufall)
        return bestes if bestes is not None else (None, h1 / g, d1 / n)

    netto, treffer, zufall = erhalten_aus(ganz)
    aus["treffer"], aus["zufall"] = round(treffer, 4), round(zufall, 4)
    aus["erhalten"] = None if netto is None else round(netto, 4)
    if oertlich:
        fenster_n = darunter = 0
        for z in zaehler.values():
            if z[4] < FENSTER_MIN_KANTEN:
                continue
            f_netto = erhalten_aus(z)[0]
            if f_netto is None:
                continue
            fenster_n += 1
            if verloren(f_netto, schwelle):
                darunter += 1
        aus["fenster"], aus["fenster_darunter"] = fenster_n, darunter
        if fenster_n >= FENSTER_MIN_ANZAHL:
            aus["anteil"] = round(darunter / fenster_n, 4)
            # An den Zählern entschieden, nicht an der gerundeten Zahl (28 von 84 sind ein Drittel).
            aus["verfleckt"] = darunter >= VERFLECKT_AB_ANTEIL * fenster_n - 1e-9
    return aus


def formtreue_aus_karten(kanten_ki: Sequence[bool], kanten_grund: Sequence[bool],
                         bereich: Sequence[bool], breite: int, hoehe: int, *,
                         schwelle: float | None = None, koerper_karte=None) -> dict:
    """Das Urteil je Baukörper aus zwei fertigen Kantenkarten.

    Args:
        kanten_ki, kanten_grund: Kantenkarten gleicher Grösse (``farbabgleich.kantenkarten``).
        bereich: der Hausbereich (``varianten.hausbereich``).
        schwelle: Vorgabe ``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``.
        koerper_karte: eine eigene Zerlegung (Kennwert je Bildpunkt) statt der
            zusammenhängenden Stücke, für Baukörper, die sich im Bild berühren.

    Returns:
        ``{urteil, warnung, schwelle, herkunft, kanten_iou_haus, anlage, kantenquote,
        baukoerper, aufgeloest, verfleckt, nicht_entscheidbar, nicht_gemessen, schwaechster,
        saetze, hinweise}``. ``baukoerper`` trägt je Stück ``{nr, name, ort, kasten, n,
        anteil_bild, kanten_iou, innen, urteil, grund}``: «aufgeloest» (:func:`verloren` im
        Ganzen), «verfleckt» (in :data:`VERFLECKT_AB_ANTEIL` der Fenster), «dazugemalt»
        (nicht entscheidbar, ohne Warnung), «gehalten» oder «ungemessen» (mit ``grund``).
        ``urteil`` ist «form_weicht_ab», sobald in einer Anlage (``anlage``) ein Baukörper
        aufgelöst oder verfleckt ist ODER die Zahl über das ganze Haus unter der Schwelle
        liegt. ``saetze`` nennen die Baukörper, die nicht halten; ``hinweise`` sagen, wo
        nicht geurteilt werden konnte (nie still).
    """
    from . import varianten  # noqa: PLC0415
    if schwelle is None:
        schwelle = varianten.DECKUNG_KANTEN_IOU_SCHWELLE
    if not 0.0 <= float(schwelle) <= 1.0:
        raise FormtreueError(f"Schwelle {schwelle!r} liegt nicht in 0..1.")
    n = breite * hoehe
    if not (len(kanten_ki) == len(kanten_grund) == len(bereich) == n):
        raise FormtreueError(
            f"Kantenkarten {len(kanten_ki)}/{len(kanten_grund)} und Bereich {len(bereich)} "
            f"passen nicht zu {breite}x{hoehe}={n}.")
    stuecke = (_aus_karte(koerper_karte, bereich, breite, hoehe) if koerper_karte is not None
               else baukoerper(bereich, breite, hoehe))
    quote = {"ki": round(sum(1 for k in kanten_ki if k) / n, 4) if n else 0.0,
             "grundbild": round(sum(1 for k in kanten_grund if k) / n, 4) if n else 0.0}
    quote["erreicht"] = max(quote["ki"], quote["grundbild"]) >= KANTENQUOTE_AB
    beide_haus = eines_haus = 0
    liste = []
    for s in stuecke:
        beide = eines = 0
        for i in s["punkte"]:
            a, b = kanten_ki[i], kanten_grund[i]
            if a or b:
                eines += 1
                if a and b:
                    beide += 1
        beide_haus += beide
        eines_haus += eines
        eintrag = {"nr": s["nr"], "ort": s["ort"], "kasten": list(s["kasten"]), "n": s["n"],
                   "anteil_bild": s["anteil_bild"],
                   "kanten_iou": None if eines == 0 else round(beide / eines, 4)}
        if "kennung" in s:
            eintrag["kennung"] = s["kennung"]
        eintrag["name"] = name_des_baukoerpers(eintrag)
        innen = inneres(s["punkte"], kanten_ki, kanten_grund, breite, hoehe, s["kasten"],
                        schwelle=schwelle)
        if innen is not None:
            eintrag["innen"] = innen
        if innen is None or innen["kanten_grundbild"] < KOERPER_MIN_KANTEN:
            # Im Grundbild innen glatt (oder fast): keine Zeichnung, die verloren gehen könnte.
            # Was die KI dort malt (Ziegel oder Flecken), entscheiden Kanten allein nicht.
            eintrag["urteil"] = UNGEMESSEN
            eintrag["grund"] = (f"im Inneren unter {KOERPER_MIN_KANTEN} Kantenpunkte im "
                                f"Grundbild: keine Zeichnung, die verloren gehen könnte")
        elif innen["erhalten"] is None:
            eintrag["urteil"] = UNGEMESSEN
            eintrag["grund"] = (f"das KI-Bild ist dort so dicht an Kanten, dass sie die Kanten "
                                f"des Grundbilds auch zufällig treffen ({innen['zufall']:.0%} "
                                f"am verschobenen Bild, Grenze {ZUFALL_MAX:.0%})")
        elif innen["zeichnung_dichte"] >= ZUFALL_MAX and innen["kanten_ki"] > 0 and (
                (innen["verfleckt"] and not verloren(innen["erhalten"], schwelle))
                or (FEIN_STRENG and quote["grundbild"] >= KANTENQUOTE_AB
                    and verloren(innen["erhalten"], schwelle))):
            # Die Zeichnung des Grundbilds ist so fein, dass schon ein Punkt Toleranz fast
            # überall trifft: Dann zählt nur die genaue Lage, und Unschärfe oder eine
            # Skalierung verschieben Kanten um einen Punkt. Ein knappes Urteil («verfleckt»,
            # im Ganzen aber nicht verloren) ist dort nicht entscheidbar.
            eintrag["urteil"] = UNGEMESSEN
            eintrag["grund"] = (f"die Zeichnung des Grundbilds ist dort so fein "
                                f"({innen['zeichnung_dichte']:.0%} der Punkte liegen an einer "
                                f"Kante), dass Unschärfe oder Skalierung von Verlust nicht zu "
                                f"trennen sind")
        elif verloren(innen["erhalten"], schwelle) or innen["verfleckt"]:
            if (quote["grundbild"] >= KANTENQUOTE_AB
                    and 2 * innen["kanten_ki"] < innen["kanten_grundbild"]) \
                    or max(quote["grundbild"], quote["ki"]) >= KANTENQUOTE_GLEICHSTAND:
                # Die Quote des GRUNDBILDS ist voll: Seine Kantenkarte ist dann eine Auswahl
                # der stärksten 15 %, und das KI-Bild kann anders auswählen, obwohl der Bau
                # gemalt ist (Gegenlesen: Hausanteil 88 %, 24,6 % Kanten, Fehlalarm).
                eintrag["urteil"] = UNGEMESSEN
                eintrag["grund"] = (f"Kantenquote im Grundbild erreicht ({quote['grundbild']:.1%} "
                                    f"der Bildpunkte sind Kante, höchstens 15 % zählen): Die "
                                    f"Kanten dieses Baus können verdrängt sein, obwohl er "
                                    f"gemalt ist")
            else:
                eintrag["urteil"] = (AUFGELOEST if verloren(innen["erhalten"], schwelle)
                                     else VERFLECKT)
        elif (innen["kanten_iou"] or 0.0) < schwelle:
            # Die Zeichnung des Grundbilds ist da, die KI hat viel dazugemalt. Material oder
            # neue Fenster? Dieselben Daten, zwei Wahrheiten: nicht entscheidbar.
            eintrag["urteil"] = DAZUGEMALT
        else:
            eintrag["urteil"] = GEHALTEN
        liste.append(eintrag)
    # Gerundet wie die Deckung (erst sechs, dann vier Stellen), damit beide Zahlen gleich sind.
    haus = None if eines_haus == 0 else round(round(beide_haus / eines_haus, 6), 4)
    gemessen = [e for e in liste if e["urteil"] != UNGEMESSEN]
    hausflaeche = sum(e["n"] for e in liste)
    rest = hausflaeche - max((e["n"] for e in liste), default=0)
    anlage = hausflaeche > 0 and rest >= ANLAGE_AB_REST * hausflaeche
    haelt_nicht = [e for e in gemessen if e["urteil"] in (AUFGELOEST, VERFLECKT)]
    weicht_ab = haelt_nicht if anlage else []
    if weicht_ab or (haus is not None and haus < schwelle):
        urteil = FORM_WEICHT_AB
    elif haus is None:
        urteil = UNGEMESSEN
    else:
        urteil = DECKUNGSGLEICH
    hinweise = []
    if not anlage and len(liste) >= 1:
        zusatz = ""
        if haelt_nicht:
            zusatz = (" Für sich gemessen hielte "
                      + ", ".join(f"{e['name']} («{e['urteil']}»)" for e in haelt_nicht)
                      + " die Form nicht.")
        hinweise.append(
            f"{SATZ_NICHT_GEMESSEN}: keine Anlage. Neben dem grössten Baukörper decken die "
            f"übrigen {rest / hausflaeche if hausflaeche else 0.0:.0%} der Hausfläche (unter "
            f"{ANLAGE_AB_REST:.0%}); es gilt die Deckung über das ganze Haus.{zusatz}")
    for e in liste:
        nennbar = e["n"] >= KOERPER_MIN_ANTEIL * n or e["n"] >= ANLAGE_AB_REST * hausflaeche
        if anlage and e["urteil"] == UNGEMESSEN and nennbar:
            hinweise.append(f"{SATZ_NICHT_GEMESSEN}: {e['name']}, {e['grund']}.")
        elif anlage and e["urteil"] == DAZUGEMALT:
            hinweise.append(
                f"{SATZ_NICHT_GEMESSEN}: {e['name']}, die Zeichnung des Grundbilds steht "
                f"({e['innen']['erhalten']:.0%} erhalten), aber die KI hat viel dazugemalt "
                f"(Kanten-Deckung im Inneren {e['innen']['kanten_iou']}): Material oder neue "
                f"Fenster, aus Kanten allein nicht entscheidbar.")
    if quote["erreicht"] and anlage:
        hinweise.append(
            f"KANTENQUOTE ERREICHT: {max(quote['ki'], quote['grundbild']):.1%} der Bildpunkte "
            f"sind Kante, höchstens 15 % zählen. Schwächere Kanten können fehlen; die Urteile "
            f"je Baukörper sind an diesem Bild weniger sicher.")
    schwaechster = min((e for e in gemessen if e["innen"]["erhalten"] is not None),
                       key=lambda e: e["innen"]["erhalten"], default=None)
    return {"urteil": urteil, "warnung": urteil == FORM_WEICHT_AB, "schwelle": schwelle,
            "herkunft": HERKUNFT, "kanten_iou_haus": haus, "anlage": anlage,
            "kantenquote": quote, "baukoerper": liste,
            "aufgeloest": [e["nr"] for e in weicht_ab if e["urteil"] == AUFGELOEST],
            "verfleckt": [e["nr"] for e in weicht_ab if e["urteil"] == VERFLECKT],
            "nicht_entscheidbar": [e["nr"] for e in liste if e["urteil"] == DAZUGEMALT],
            "nicht_gemessen": [e["nr"] for e in liste if e["urteil"] == UNGEMESSEN],
            "schwaechster": None if schwaechster is None else schwaechster["nr"],
            "saetze": [satz_des_baukoerpers(e, schwelle) for e in weicht_ab],
            "hinweise": hinweise}


def satz_des_baukoerpers(eintrag: dict, schwelle: float) -> str:
    """Der Satz zu einem Baukörper, der seine Form nicht hält: welcher, wo, mit welcher Zahl."""
    k = eintrag.get("kasten") or [0, 0, 0, 0]
    wo = (f"{SATZ_BAUKOERPER}: {eintrag.get('name')}, Bildpunkte x {k[0]} bis {k[2]}, "
          f"y {k[1]} bis {k[3]}, {float(eintrag.get('anteil_bild') or 0.0):.0%} der "
          f"Bildfläche.")
    innen = eintrag.get("innen") or {}
    zahlen = (f"{float(innen.get('erhalten') or 0.0):.0%} der Kanten des Grundbilds in seinem "
              f"Inneren sind im KI-Bild erhalten (bester Versatz {innen.get('versatz')}, "
              f"Zufallstreffer abgezogen; Schwelle {schwelle:.0%})")
    if eintrag.get("urteil") == VERFLECKT:
        return (f"{wo} Verfleckt: {float(innen.get('anteil') or 0.0):.0%} seines Inneren haben "
                f"die Zeichnung des Grundbilds verloren (ab {VERFLECKT_AB_ANTEIL:.0%} verfleckt; "
                f"gesetzt am synthetischen Satz, nicht geeicht). Im Ganzen: {zahlen}.")
    return f"{wo} Aufgelöst: {zahlen} (je Baukörper gesetzt, nicht geeicht)."


def formtreue(ki: Sequence[Sequence[int]], grund: Sequence[Sequence[int]],
              bereich: Sequence[bool], breite: int, hoehe: int, *,
              schwelle: float | None = None, koerper_karte=None) -> dict:
    """Wie :func:`formtreue_aus_karten`, aus den Farben beider Bilder (``(r, g, b)`` je Punkt)."""
    from . import farbabgleich  # noqa: PLC0415
    if len(ki) != len(grund):
        raise FormtreueError(f"KI-Bild {len(ki)} Punkte, Grundbild {len(grund)}: ungleiche Masse.")
    ka, kb = farbabgleich.kantenkarten(ki, grund, breite, hoehe)
    return formtreue_aus_karten(ka, kb, bereich, breite, hoehe, schwelle=schwelle,
                                koerper_karte=koerper_karte)


def formtreue_aus_bildern(ki_png, grundbild_png, maske, *, material_id_png=None, tabelle=None,
                          schwelle: float | None = None) -> dict | None:
    """Das Urteil je Baukörper aus zwei Bilddateien und der Bauwerksmaske.

    Derselbe Hausbereich wie ``varianten.deckung_aus_bildern`` (Maske ohne Umfeld und Gelände).
    ``None``, wo die Deckung selbst nicht im Haus messen kann: ein Bild fehlt, die Masse sind
    ungleich, oder es gibt keine brauchbare Maske. Dann gibt es keine Baukörper zu beurteilen,
    und die Deckung über das ganze Bild bleibt das einzige Urteil.
    """
    from pathlib import Path  # noqa: PLC0415
    from . import bildlesen, farbabgleich, varianten  # noqa: PLC0415
    if not ki_png or not grundbild_png or not Path(ki_png).is_file() \
            or not Path(grundbild_png).is_file():
        return None
    a, ba, ha = bildlesen.lies_png_farben(ki_png)
    b, bb, hb = bildlesen.lies_png_farben(grundbild_png)
    if (ba, ha) != (bb, hb):
        return None
    kennung = None
    if material_id_png and tabelle and Path(material_id_png).is_file():
        try:
            kennung, bi, hi = bildlesen.lies_png_farben(material_id_png)
            if (bi, hi) != (ba, ha):
                kennung = None
        except (bildlesen.BildError, OSError, ValueError):
            kennung = None
    bereich, _grund = varianten.hausbereich(maske, ba * ha, kennung=kennung, tabelle=tabelle)
    if bereich is None:
        return None
    ka, kb = farbabgleich.kantenkarten(a, b, ba, ha)
    return formtreue_aus_karten(ka, kb, bereich, ba, ha, schwelle=schwelle)


def deckung_mit_baukoerpern(deckung: dict | None, befund: dict | None) -> dict | None:
    """Das Deckungsurteil einer Kamera, nachgeführt um die Prüfung je Baukörper.

    Für die Stelle, die ``varianten.deckung_aus_bildern`` ruft: Heisst die Deckung über das
    ganze Haus «deckungsgleich», hält aber in einer Anlage ein Baukörper seine Form nicht, wird
    das Urteil «form_weicht_ab» (mit Warnung), und der Satz nennt den Baukörper. Die Zahl
    ``kanten_iou`` bleibt die über das ganze Haus. Jedes andere Urteil bleibt, wie es ist;
    die Prüfung macht nie milder. ``befund`` hängt als ``baukoerper_befund`` daran.
    """
    from . import varianten  # noqa: PLC0415
    if not isinstance(deckung, dict) or not isinstance(befund, dict):
        return deckung
    aus = dict(deckung, baukoerper_befund=befund)
    if deckung.get("urteil") == varianten.DECKUNGSGLEICH and befund.get("warnung") \
            and befund.get("saetze"):
        aus["urteil"] = varianten.FORM_WEICHT_AB
        aus["warnung"] = True
        aus["satz"] = (f"{varianten.DECKUNG_SATZ[varianten.FORM_WEICHT_AB]}: "
                       + " ".join(befund.get("saetze") or ()))
    return aus


def deckung_und_formtreue_aus_bildern(ki_png, grundbild_png, gleiche_grundlage: bool, *,
                                      maske=None, material_id_png=None, tabelle=None,
                                      schwelle: float | None = None) -> dict:
    """Das Deckungsurteil einer Kamera samt Prüfung je Baukörper, die Kantenkarten EINMAL gerechnet.

    Liefert genau, was ``varianten.deckung_aus_bildern`` liefert (dieselben Felder, dieselben
    Zahlen: eine Probe hält beides gleich), und führt es mit :func:`deckung_mit_baukoerpern`
    nach, wo im Haus gemessen wird. Ohne brauchbare Maske, ohne Grundbild oder bei ungleichen
    Massen bleibt es beim Urteil der Deckung allein.
    """
    from pathlib import Path  # noqa: PLC0415
    from . import bildlesen, farbabgleich, varianten  # noqa: PLC0415
    if schwelle is None:
        schwelle = varianten.DECKUNG_KANTEN_IOU_SCHWELLE
    deckung = varianten.deckung
    if not grundbild_png or not Path(grundbild_png).is_file():
        return dict(deckung(gleiche_grundlage, None, schwelle=schwelle), grund="kein Grundbild")
    a, ba, ha = bildlesen.lies_png_farben(ki_png)
    b, bb, hb = bildlesen.lies_png_farben(grundbild_png)
    if (ba, ha) != (bb, hb):
        return dict(deckung(gleiche_grundlage, None, schwelle=schwelle),
                    grund=f"KI-Bild {ba}x{ha}, Grundbild {bb}x{hb}: ungleiche Masse")
    kennung = None
    if material_id_png and tabelle and Path(material_id_png).is_file():
        try:
            kennung, bi, hi = bildlesen.lies_png_farben(material_id_png)
            if (bi, hi) != (ba, ha):
                kennung = None
        except (bildlesen.BildError, OSError, ValueError):
            kennung = None
    bereich, grund = varianten.hausbereich(maske, ba * ha, kennung=kennung, tabelle=tabelle)
    ka, kb = farbabgleich.kantenkarten(a, b, ba, ha)
    ganz = farbabgleich.kanten_iou_aus_karten(ka, kb)
    if bereich is None:
        return dict(deckung(gleiche_grundlage, ganz, schwelle=schwelle),
                    bereich=varianten.DECKUNG_BEREICH_GANZ, bereich_grund=grund,
                    kanten_iou_ganz=None if ganz is None else round(ganz, 4))
    haus = farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=bereich)
    urteil = dict(deckung(gleiche_grundlage, haus, schwelle=schwelle),
                  bereich=varianten.DECKUNG_BEREICH_HAUS, n_haus=sum(bereich),
                  kanten_iou_ganz=None if ganz is None else round(ganz, 4))
    if not gleiche_grundlage:
        return urteil
    return deckung_mit_baukoerpern(
        urteil, formtreue_aus_karten(ka, kb, bereich, ba, ha, schwelle=schwelle))

