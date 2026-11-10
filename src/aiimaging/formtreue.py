"""Formtreue je Baukörper: hält JEDER Bau einer Anlage seine Form (A0300)?

**Anlass (Wettbewerbsmodell, 24.10.2026, Zelle B2C3):** Die KI löste das Hauptgebäude mit Hof in
grüne Flecken auf und die Halle in eine glatte Platte, und das Ergebnis hiess «deckungsgleich»:
Kanten-Deckung am Haus 0,256 gegen die Schwelle 0,25. Die Deckung (``varianten.deckung``) zählt
die Kanten über die GANZE Hausfläche in einen Topf. In einer Anlage halten die Nebenbauten ihre
Kanten und heben die Zahl über die Schwelle; der aufgelöste Bau geht darin unter.

**Die Regel.** Die Hausfläche (Bauwerksmaske ohne Umfeld und Gelände, wie die Deckung sie
nimmt) wird in ihre zusammenhängenden Stücke zerlegt, das sind die **Baukörper**. Je
Baukörper wird sein **Inneres** gefragt (ohne einen Saum von 2 Bildpunkten: Der Umriss gegen
den Grund deckt sich fast immer und hob am synthetischen Satz eine glatte Platte allein auf
bis zu 0,40), und zwar mit EINER Regel (:func:`verloren`):

    Die Zeichnung ist verloren, wenn die Kanten-Deckung unter der bestehenden Schwelle liegt
    (``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``) UND weniger als die Hälfte der Kanten des
    Grundbilds im KI-Bild noch da ist.

* Gilt das für das ganze Innere, heisst der Baukörper **«aufgelöst»**.
* Gilt es in mindestens einem Drittel der Stände eines Prüffensters, das über das Innere
  wandert, heisst er **«verfleckt»**, auch wenn sein Mittel besteht.
* Liegt nur die Kanten-Deckung unter der Schwelle, die Zeichnung des Grundbilds steht aber
  noch, heisst er **«dazugemalt»**: gemeldet, ohne Warnung. Ob die KI Material gemalt hat
  oder neue Fenster, entscheiden Kanten allein nicht (dieselben Daten, zwei Wahrheiten).

Hält ein Baukörper nicht, weicht die Form ab, und das Urteil sagt, WELCHER: Nummer (1 = der
grösste), Ort im Bild, Kasten in Bildpunkten.

**Nie milder als heute, am Einzelhaus gleich.** Je Baukörper wird nur in einer **Anlage**
geurteilt: mindestens zwei Baukörper von je :data:`KOERPER_MIN_ANTEIL` der Bildfläche. Für ein
einzelnes Haus bleibt die Deckung über das ganze Haus das Urteil; sie ist dort am Gerät
gesetzt. Was die Deckung «Form weicht ab» nennt, bleibt es in jedem Fall.

**Was kein Urteil bekommt («nicht gemessen»), und warum.** Ein Baukörper unter
:data:`KOERPER_MIN_ANTEIL` der Bildfläche, und einer, dessen Inneres im Grundbild weniger als
:data:`KOERPER_MIN_KANTEN` Kantenpunkte trägt: Er hat innen keine Zeichnung, die verloren gehen
könnte, oder so wenig, dass das Urteil an drei, vier Merkmalen hinge. Dort handelt die Prüfung
wie heute. Das ist eine Grenze, keine Lösung: Wird ein im Grundbild glatter Bau zu Flecken,
sieht sie es nicht.

**Weitere Grenzen, die hier stehen, damit sie niemand entdecken muss.**

* Baukörper, die sich im Bild berühren oder überdecken (Schrägsicht), sind EIN
  zusammenhängendes Stück und werden zusammen beurteilt. Wer sie trennen kann (ein Kennpass
  je Bau), übergibt die Zerlegung selbst (``koerper_karte``).
* «Verfleckt» kippt nicht an einer scharfen Kante. Gemessen am synthetischen Satz: Sind bis
  30 % eines Baus verfleckt, schlägt die Prüfung nie an, ab 60 % immer, dazwischen teils.
* Die Schwelle der Deckung ist am Gerät für das ganze Haus gesetzt (neun Bilder, ein Haus).
  Je Baukörper ist alles **gesetzt, nicht geeicht**: die Hälfte, das Drittel, die Grösse des
  Fensters. Die Eichung am echten Bild ist ein Messauftrag für das Gerät.
* Die Kantenfindung lässt höchstens die stärksten 15 % der Bildpunkte als Kante gelten
  (``umriss.KANTEN_QUANTIL``). Füllt die KI diese Quote mit starken Kanten an anderer Stelle,
  fallen schwächere Kanten eines gehaltenen Baus heraus (gemessen am synthetischen Satz).

Reine stdlib, ohne Oberfläche aufrufbar (Regel 4): :func:`formtreue` aus Bilddaten,
:func:`formtreue_aus_bildern` aus zwei Dateien, :func:`deckung_mit_baukoerpern` für die Stelle,
die das Deckungsurteil bildet.
"""
from __future__ import annotations

from collections.abc import Sequence

#: So viel der Bildfläche muss ein Baukörper decken, damit er ein eigenes Urteil bekommt.
#: Gesetzt: 1 %, dieselbe Zahl wie ``varianten.DECKUNG_HAUS_MIN_ANTEIL`` für das ganze Haus.
KOERPER_MIN_ANTEIL = 0.01
#: So viele Kantenpunkte muss das Grundbild im Inneren eines Baukörpers haben, damit er ein
#: Urteil bekommt. Gesetzt: 150, so viel, wie ein Prüffenster im Mittel trägt
#: (:data:`FENSTER_KANTEN`). Gemessen am 10.11.2026 mit 24: Ein Nebenbau mit fünf Öffnungen
#: verlor bei 24 % zufälligem Verlust vier davon und hiess «aufgelöst». Das Urteil stimmte für
#: diesen Bau, aber es hing an vier Merkmalen; an so wenig Zeichnung ist es Zufall.
KOERPER_MIN_KANTEN = 150
#: Der Saum am Rand eines Baukörpers, der für die örtliche Prüfung nicht zählt: 2 Bildpunkte,
#: dieselbe Zahl wie ``umriss.TOLERANZ_PX``. Der Umriss gegen den Grund deckt sich fast immer
#: (mit «Umriss halten» sicher) und sagt nichts darüber, ob das Innere noch der Bau ist.
SAUM_PX = 2
#: Die Grösse des Fensters der örtlichen Prüfung: so gross, dass es im Mittel so viele
#: Kantenpunkte des Grundbilds aus dem Inneren des Baukörpers trägt. Gesetzt: 150. Das Fenster
#: richtet sich damit nach der Zeichnung des Baus, nicht nach der Bildgrösse: dichte Zeichnung,
#: kleines Fenster.
FENSTER_KANTEN = 150
#: So viele Kantenpunkte des Grundbilds muss ein Fenster tragen, damit es zählt. Gesetzt: 30,
#: ein Fünftel dessen, was es im Mittel trägt. Ein Fenster am Rand, das nur ein paar Punkte
#: einer Kante streift, sagt nichts.
FENSTER_MIN_KANTEN = 30
#: So viele zählende Fenster braucht ein Baukörper für ein örtliches Urteil.
FENSTER_MIN_ANZAHL = 12
#: So oft muss das Fenster in das Innere des Baukörpers passen (nach Fläche). Gesetzt: 2.
#: Darunter sehen alle Fenster dieselben Kanten, und «100 % des Inneren» hiesse nur «ein
#: Merkmal fehlt». Mit 4 blieben am synthetischen Satz 5 von 100 verfleckten Hauptbauten ohne
#: örtliches Urteil (Zwischenstand 10.11.2026).
FENSTER_MIN_FLAECHEN = 2
#: Ab diesem Anteil der Fensterstände, an denen die Zeichnung verloren ist (:func:`verloren`),
#: heisst ein Baukörper «verfleckt». **Gesetzt: ein Drittel, am synthetischen Satz geprüft,
#: nicht am Gerät geeicht.** Gemessen am 10.11.2026 (``tests/anlagen_erzeuger.py``): Der Anteil
#: folgt dem wirklich verfleckten Teil eines Baus (Abweichung in 95 % der Fälle unter 0,13).
#: 467 gehaltene Baukörper aus 200 intakten Anlagen lagen bei höchstens 0,16. An der Reihe
#: über den verfleckten Teil (504 Bilder): unter 35 % nie beanstandet, 35 bis 45 % 16 von 53,
#: 45 bis 60 % 66 von 71, ab 60 % 237 von 237. Die Schwelle ist ein Mass («ein Drittel des
#: Baus»), keine Kante, die zwei Lager trennt.
VERFLECKT_AB_ANTEIL = 1.0 / 3.0

#: Unter diesem Anteil erhaltener Kantenpunkte des Grundbilds gilt die Zeichnung als verloren
#: (zusammen mit der Schwelle der Deckung, siehe :func:`verloren`). Gesetzt: die Hälfte.
ERHALTEN_MIN = 0.5

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

HERKUNFT = ("Schwelle der Deckung (gesetzt aus auf-20261022-337 und -339), je Baukörper im "
            "Inneren angewandt; die Hälfte (erhalten) und das Drittel (verfleckt) gesetzt am "
            "synthetischen Satz, am echten Bild nicht geeicht (A0300)")

#: Der Anfang des Satzes je Baukörper, der seine Form nicht hält.
SATZ_BAUKOERPER = "BAUKÖRPER HÄLT DIE FORM NICHT"


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


def verloren(gemeinsam: int, grund: int, eines: int, schwelle: float) -> bool:
    """Hat ein Stück Bild seine Zeichnung verloren? Die EINE Regel, im Ganzen wie im Fenster.

    Zwei Bedingungen, beide nötig:

    * die Kanten-Deckung (gemeinsame Kantenpunkte durch alle, die eines der Bilder hat) liegt
      unter der Schwelle, das ist der bestehende Massstab der Deckung;
    * weniger als :data:`ERHALTEN_MIN` der Kantenpunkte des Grundbilds sind im KI-Bild noch da.

    Die zweite trennt Verlust von Zugabe: Malt die KI Ziegel oder Lattung auf ein Dach, sinkt
    die Deckung, aber die Zeichnung des Grundbilds steht noch. Ob das Material ist oder ein
    neues Fenster, entscheiden Kanten allein nicht; das heisst hier «dazugemalt» und warnt nicht.
    """
    if grund <= 0 or eines <= 0:
        return False
    return gemeinsam / eines < schwelle and gemeinsam / grund < ERHALTEN_MIN


def inneres(punkte: Sequence[int], kanten_ki: Sequence[bool], kanten_grund: Sequence[bool],
            breite: int, kasten, *, schwelle: float) -> dict | None:
    """Das Innere EINES Baukörpers: seine Kanten-Deckung ohne den Saum, ganz und örtlich.

    **Ohne den Saum** (:data:`SAUM_PX`): Der Umriss eines Baus gegen den Grund deckt sich fast
    immer (mit «Umriss halten» sicher). Gemessen am 10.11.2026: Eine glatte Platte anstelle des
    Hauptbaus kam allein über ihren Umriss auf 0,21 bis 0,40 (100 Startwerte); im Inneren hat sie 0.

    **Örtlich**: Die Zahl über das ganze Innere mittelt. Hält ein Teil seine Zeichnung genau
    und ist der Rest ein grüner Fleck, liegt sie über der Schwelle. Darum wandert ein Fenster
    (Grösse nach :data:`FENSTER_KANTEN`) über das Innere und fragt in jedem Stand dieselbe
    Regel (:func:`verloren`); ``anteil`` ist der Teil der Stände, an denen die Zeichnung
    verloren ist, ``verfleckt`` sagt, ob das :data:`VERFLECKT_AB_ANTEIL` erreicht.

    Returns:
        ``None`` ohne Inneres (der Baukörper ist schmaler als zwei Säume). Sonst ``{innen,
        kanten_grundbild, kanten_iou, erhalten, anteil, verfleckt, halbe_seite_px, fenster,
        fenster_darunter}``; ``erhalten`` ist der Teil der Kantenpunkte des Grundbilds, der im
        KI-Bild noch Kante ist;
        ``kanten_iou`` ist ``None`` ohne jede Kante im Inneren, ``anteil`` ist ``None``, wenn
        das Grundbild im Inneren keine Kante hat, das Fenster keine
        :data:`FENSTER_MIN_FLAECHEN` Mal in das Innere passt oder weniger als
        :data:`FENSTER_MIN_ANZAHL` Fenster zählen.
    """
    x0, y0, x1, y1 = kasten
    b, h = x1 - x0, y1 - y0
    if b <= 2 * SAUM_PX or h <= 2 * SAUM_PX:
        return None
    drin = bytearray(b * h)
    for i in punkte:
        y, x = divmod(i, breite)
        drin[(y - y0) * b + (x - x0)] = 1

    def summen(werte) -> list[int]:
        """Summentafel: die Summe jedes Rechtecks in vier Zugriffen."""
        tafel = [0] * ((b + 1) * (h + 1))
        for yy in range(h):
            lauf, oben, zeile = 0, yy * (b + 1), (yy + 1) * (b + 1)
            for xx in range(b):
                lauf += werte[yy * b + xx]
                tafel[zeile + xx + 1] = tafel[oben + xx + 1] + lauf
        return tafel

    def rechteck(tafel, ax, ay, bx, by) -> int:
        return (tafel[by * (b + 1) + bx] - tafel[ay * (b + 1) + bx]
                - tafel[by * (b + 1) + ax] + tafel[ay * (b + 1) + ax])

    t_drin = summen(drin)
    voll = (2 * SAUM_PX + 1) ** 2
    innen = bytearray(b * h)
    for yy in range(SAUM_PX, h - SAUM_PX):
        for xx in range(SAUM_PX, b - SAUM_PX):
            if drin[yy * b + xx] and rechteck(t_drin, xx - SAUM_PX, yy - SAUM_PX,
                                             xx + SAUM_PX + 1, yy + SAUM_PX + 1) == voll:
                innen[yy * b + xx] = 1
    n_innen = sum(innen)
    beide, eines, nur_grund = bytearray(b * h), bytearray(b * h), bytearray(b * h)
    grund_kanten = 0
    for yy in range(h):
        bild = (y0 + yy) * breite + x0
        for xx in range(b):
            if innen[yy * b + xx]:
                ka, kb = kanten_ki[bild + xx], kanten_grund[bild + xx]
                if ka or kb:
                    eines[yy * b + xx] = 1
                    if ka and kb:
                        beide[yy * b + xx] = 1
                if kb:
                    grund_kanten += 1
                    nur_grund[yy * b + xx] = 1
    if not n_innen:
        return None
    summe_beide, summe_eines = sum(beide), sum(eines)
    aus = {"innen": n_innen, "kanten_grundbild": grund_kanten,
           "kanten_iou": None if not summe_eines else round(summe_beide / summe_eines, 4),
           "erhalten": None if not grund_kanten else round(summe_beide / grund_kanten, 4),
           "anteil": None}
    if not grund_kanten:
        return aus
    r = max(3, int(round((FENSTER_KANTEN * n_innen / grund_kanten) ** 0.5 / 2.0)))
    aus["halbe_seite_px"] = r
    if n_innen < FENSTER_MIN_FLAECHEN * (2 * r + 1) ** 2:
        return aus
    schritt = max(1, r // 2)
    t_beide, t_grund, t_eines = summen(beide), summen(nur_grund), summen(eines)
    fenster = darunter = 0
    for yy in range(0, h, schritt):
        for xx in range(0, b, schritt):
            if not innen[yy * b + xx]:
                continue
            ax, ay, bx, by = max(0, xx - r), max(0, yy - r), min(b, xx + r + 1), min(h, yy + r + 1)
            g = rechteck(t_grund, ax, ay, bx, by)
            if g < FENSTER_MIN_KANTEN:
                continue
            fenster += 1
            gemeinsam = rechteck(t_beide, ax, ay, bx, by)
            if verloren(gemeinsam, g, rechteck(t_eines, ax, ay, bx, by), schwelle):
                darunter += 1
    aus["fenster"], aus["fenster_darunter"] = fenster, darunter
    if fenster >= FENSTER_MIN_ANZAHL:
        aus["anteil"] = round(darunter / fenster, 4)
        # An den Zählern entschieden, nicht an der gerundeten Zahl: 28 von 84 Ständen sind ein
        # Drittel und zählen (gefunden an der Reihe in den Proben: 0,3333 < 1/3).
        aus["verfleckt"] = darunter >= VERFLECKT_AB_ANTEIL * fenster - 1e-9
    return aus


def formtreue_aus_karten(kanten_ki: Sequence[bool], kanten_grund: Sequence[bool],
                         bereich: Sequence[bool], breite: int, hoehe: int, *,
                         schwelle: float | None = None, koerper_karte=None) -> dict:
    """Das Urteil je Baukörper aus zwei fertigen Kantenkarten.

    Args:
        kanten_ki, kanten_grund: Kantenkarten gleicher Grösse (``farbabgleich.kantenkarten``).
            Die Kanten werden am GANZEN Bild gefunden und hier nur je Baukörper gezählt,
            damit der Rand eines Baukörpers keine Kante erfindet.
        bereich: der Hausbereich (``varianten.hausbereich``).
        schwelle: Vorgabe ``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``.
        koerper_karte: eine eigene Zerlegung (Kennwert je Bildpunkt) statt der
            zusammenhängenden Stücke, für Baukörper, die sich im Bild berühren.

    Returns:
        ``{urteil, warnung, schwelle, herkunft, kanten_iou_haus, anlage, baukoerper,
        aufgeloest, verfleckt, nicht_entscheidbar, schwaechster, saetze}``. ``baukoerper`` trägt je Stück ``{nr, name, ort, kasten, n,
        anteil_bild, kanten_iou, innen, urteil}`` (ohne die Punktliste); das Urteil eines
        Baukörpers ist «aufgeloest» (sein Inneres hat die Zeichnung verloren, :func:`verloren`),
        «verfleckt» (:func:`inneres`, ab :data:`VERFLECKT_AB_ANTEIL` der Fensterstände),
        «dazugemalt» (nicht entscheidbar, ohne Warnung), «gehalten» oder «ungemessen». ``urteil`` ist «form_weicht_ab», sobald in einer Anlage (``anlage``:
        mindestens zwei Baukörper von je 1 % der Bildfläche) einer aufgelöst oder verfleckt ist ODER die Zahl
        über das ganze Haus unter der Schwelle liegt; ohne jede Messung «ungemessen».
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
    beide_haus = eines_haus = 0
    liste = []
    for s in stuecke:
        beide = eines = grund_kanten = 0
        for i in s["punkte"]:
            a, b = kanten_ki[i], kanten_grund[i]
            if a or b:
                eines += 1
                if a and b:
                    beide += 1
            if b:
                grund_kanten += 1
        beide_haus += beide
        eines_haus += eines
        iou = None if eines == 0 else round(beide / eines, 4)
        eintrag = {"nr": s["nr"], "ort": s["ort"], "kasten": list(s["kasten"]), "n": s["n"],
                   "anteil_bild": s["anteil_bild"], "kanten_iou": iou,
                   "kanten_grundbild": grund_kanten}
        if "kennung" in s:
            eintrag["kennung"] = s["kennung"]
        eintrag["name"] = name_des_baukoerpers(eintrag)
        if s["n"] < KOERPER_MIN_ANTEIL * n:
            eintrag["urteil"] = UNGEMESSEN
            eintrag["grund"] = f"unter {KOERPER_MIN_ANTEIL:.0%} der Bildfläche"
        else:
            innen = inneres(s["punkte"], kanten_ki, kanten_grund, breite, s["kasten"],
                            schwelle=schwelle)
            if innen is not None:
                eintrag["innen"] = innen
            if innen is None or innen["kanten_grundbild"] < KOERPER_MIN_KANTEN:
                # Im Grundbild innen glatt: Der Bau hat innen keine Zeichnung zu verlieren.
                # Was die KI dort malt (Ziegel oder Flecken), entscheiden Kanten allein nicht.
                eintrag["urteil"] = UNGEMESSEN
                eintrag["grund"] = (f"im Inneren unter {KOERPER_MIN_KANTEN} Kantenpunkte im "
                                    f"Grundbild: keine Zeichnung, die verloren gehen könnte")
            elif (innen["kanten_iou"] or 0.0) < schwelle and innen["erhalten"] < ERHALTEN_MIN:
                eintrag["urteil"] = AUFGELOEST
            elif innen.get("verfleckt"):
                eintrag["urteil"] = VERFLECKT
            elif (innen["kanten_iou"] or 0.0) < schwelle:
                # Die Zeichnung des Grundbilds ist da, die KI hat viel dazugemalt. Material
                # oder neue Fenster? Dieselben Daten, zwei Wahrheiten: nicht entscheidbar.
                eintrag["urteil"] = DAZUGEMALT
            else:
                eintrag["urteil"] = GEHALTEN
        liste.append(eintrag)
    # Gerundet wie die Deckung (erst sechs, dann vier Stellen), damit beide Zahlen gleich sind.
    haus = None if eines_haus == 0 else round(round(beide_haus / eines_haus, 6), 4)
    gemessen = [e for e in liste if e["urteil"] != UNGEMESSEN]
    # EINE ANLAGE sind mindestens zwei Baukörper von je KOERPER_MIN_ANTEIL der Bildfläche
    # (nach Grösse, nicht nach Messbarkeit: Nebenbauten mit glattem Dach machen aus dem
    # Hauptbau kein Einzelhaus). Nur dort urteilt die Prüfung je Baukörper mit: Am Einzelhaus
    # ist die Deckung über das ganze Haus am Gerät gesetzt, und ihr Urteil bleibt unverändert
    # (Auftrag A0300, Fertig-Satz 3).
    anlage = sum(1 for e in liste if e["n"] >= KOERPER_MIN_ANTEIL * n) >= 2
    weicht_ab = [e for e in gemessen if e["urteil"] in (AUFGELOEST, VERFLECKT)] if anlage else []
    if weicht_ab or (haus is not None and haus < schwelle):
        urteil = FORM_WEICHT_AB
    elif haus is None:
        urteil = UNGEMESSEN
    else:
        urteil = DECKUNGSGLEICH
    schwaechster = min(gemessen, key=lambda e: e["innen"]["erhalten"]) if gemessen else None
    return {"urteil": urteil, "warnung": urteil == FORM_WEICHT_AB, "schwelle": schwelle,
            "herkunft": HERKUNFT, "kanten_iou_haus": haus, "anlage": anlage,
            "baukoerper": liste,
            "aufgeloest": [e["nr"] for e in weicht_ab if e["urteil"] == AUFGELOEST],
            "verfleckt": [e["nr"] for e in weicht_ab if e["urteil"] == VERFLECKT],
            "nicht_entscheidbar": [e["nr"] for e in liste if e["urteil"] == DAZUGEMALT],
            "schwaechster": None if schwaechster is None else schwaechster["nr"],
            "saetze": [satz_des_baukoerpers(e, schwelle) for e in weicht_ab]}


def satz_des_baukoerpers(eintrag: dict, schwelle: float) -> str:
    """Der Satz zu einem Baukörper, der seine Form nicht hält: welcher, wo, mit welcher Zahl."""
    k = eintrag.get("kasten") or [0, 0, 0, 0]
    wo = (f"{SATZ_BAUKOERPER}: {eintrag.get('name')}, Bildpunkte x {k[0]} bis {k[2]}, "
          f"y {k[1]} bis {k[3]}, {float(eintrag.get('anteil_bild') or 0.0):.0%} der "
          f"Bildfläche.")
    innen = eintrag.get("innen") or {}
    zahlen = (f"Kanten-Deckung im Inneren {innen.get('kanten_iou')} (Schwelle {schwelle}), "
              f"{float(innen.get('erhalten') or 0.0):.0%} der Kanten des Grundbilds erhalten")
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
    if deckung.get("urteil") == varianten.DECKUNGSGLEICH and befund.get("warnung"):
        aus["urteil"] = varianten.FORM_WEICHT_AB
        aus["warnung"] = True
        aus["satz"] = (f"{varianten.DECKUNG_SATZ[varianten.FORM_WEICHT_AB]}: "
                       + " ".join(befund.get("saetze") or ()))
    return aus
