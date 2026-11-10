"""Formtreue je Baukörper: hält JEDER Bau einer Anlage seine Form (A0300)?

**Anlass (Wettbewerbsmodell, 24.10.2026, Zelle B2C3):** Die KI löste das Hauptgebäude mit Hof in
grüne Flecken auf und die Halle in eine glatte Platte, und das Ergebnis hiess «deckungsgleich»:
Kanten-Deckung am Haus 0,256 gegen die Schwelle 0,25. Die Deckung (``varianten.deckung``) zählt
die Kanten über die GANZE Hausfläche in einen Topf. In einer Anlage halten die Nebenbauten ihre
Kanten und heben die Zahl über die Schwelle; der aufgelöste Bau geht darin unter.

**Die Regel.** Die Hausfläche (Bauwerksmaske ohne Umfeld und Gelände, wie die Deckung sie
nimmt) wird in ihre zusammenhängenden Stücke zerlegt, das sind die **Baukörper**. Jeder
Baukörper wird mit derselben Messung (Kanten des KI-Bilds gegen die Kanten des Grundbilds) und
derselben Schwelle (``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``) dreimal gefragt:

1. **Ganz:** die Zahl über den ganzen Baukörper. Darunter: «aufgelöst».
2. **Im Inneren, ohne den Umriss** (:func:`inneres`): Der Umriss gegen den Grund deckt sich
   fast immer und hob am synthetischen Satz eine glatte Platte allein auf bis zu 0,40.
   Darunter: «aufgelöst».
3. **Örtlich:** Ein Fenster wandert über das Innere. Liegt ab einem Drittel der Stände die
   Zahl unter der Schwelle, heisst der Baukörper «verfleckt», auch wenn sein Mittel besteht.

Hält ein Baukörper nicht, weicht die Form ab, und das Urteil sagt, WELCHER: Nummer (1 = der
grösste), Ort im Bild, Kasten in Bildpunkten.

**Am Einzelhaus ändert sich nichts.** Je Baukörper wird nur in einer **Anlage** geurteilt:
mindestens zwei Baukörper von je :data:`KOERPER_MIN_ANTEIL` der Bildfläche. Für ein einzelnes
Haus bleibt die Deckung über das ganze Haus das Urteil; sie ist dort am Gerät gesetzt. Die
Prüfung kann ein Bild nur strenger beurteilen, nie milder: Was die Deckung «Form weicht ab»
nennt, bleibt es.

**Was nicht beurteilt wird.** Ein Baukörper unter :data:`KOERPER_MIN_ANTEIL` der Bildfläche
oder mit weniger als :data:`KOERPER_MIN_KANTEN` Kantenpunkten im Grundbild heisst «nicht
gemessen» und löst nie eine Warnung aus: An so wenigen Punkten ist das Verhältnis Zufall. Das
Innere urteilt nur mit, wo das Grundbild dort selbst eine Zeichnung hat; ein Bau, der im
Grundbild innen glatt ist, hat innen keine Form zu verlieren.

**Grenzen, die hier stehen, damit sie niemand entdecken muss.**

* Baukörper, die sich im Bild berühren oder überdecken (Schrägsicht), sind EIN
  zusammenhängendes Stück und werden zusammen beurteilt. Wer sie trennen kann (ein Kennpass
  je Bau), übergibt die Zerlegung selbst (``koerper_karte``).
* Die Schwelle ist am Gerät für das ganze Haus gesetzt (neun Bilder, ein Haus). Je Baukörper,
  im Inneren und örtlich ist sie **gesetzt, nicht geeicht**; das Drittel für «verfleckt» stammt
  aus dem synthetischen Satz (``tests/anlagen_erzeuger.py``). Die Eichung am echten Bild ist
  ein Messauftrag für das Gerät.
* Malt die KI auf ein Dach Zeichnung dazu, die das Grundbild nicht hat (Ziegel, Lattung), senkt
  das die Zahl im Inneren wie bisher die Zahl über das Haus. Ob das am echten Bild Fehlalarme
  gibt, ist nicht gemessen.
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
#: So viele Kantenpunkte muss das Grundbild im Baukörper haben. Gesetzt: 24. Darunter
#: verschiebt eine einzelne Fuge das Verhältnis um mehr als den Abstand zur Schwelle.
KOERPER_MIN_KANTEN = 24

#: Der Saum am Rand eines Baukörpers, der für die örtliche Prüfung nicht zählt: 2 Bildpunkte,
#: dieselbe Zahl wie ``umriss.TOLERANZ_PX``. Der Umriss gegen den Grund deckt sich fast immer
#: (mit «Umriss halten» sicher) und sagt nichts darüber, ob das Innere noch der Bau ist.
SAUM_PX = 2
#: Die Grösse des Fensters der örtlichen Prüfung: so gross, dass es im Mittel so viele
#: Kantenpunkte des Grundbilds aus dem Inneren des Baukörpers trägt. Gesetzt: 150. Das Fenster
#: richtet sich damit nach der Zeichnung des Baus, nicht nach der Bildgrösse: dichte Zeichnung,
#: kleines Fenster.
FENSTER_KANTEN = 150
#: So viele Kantenpunkte (KI-Bild oder Grundbild) muss ein Fenster tragen, damit es zählt.
FENSTER_MIN_KANTEN = 8
#: So viele zählende Fenster braucht ein Baukörper für ein örtliches Urteil.
FENSTER_MIN_ANZAHL = 12
#: So oft muss das Fenster in das Innere des Baukörpers passen (nach Fläche). Gesetzt: 2.
#: Darunter sehen alle Fenster dieselben Kanten, und «100 % des Inneren» hiesse nur «ein
#: Merkmal fehlt». Gemessen am synthetischen Satz (10.11.2026, je 100 Startwerte): mit 4
#: bestanden 5 von 100 verfleckten Hauptbauten ohne örtliches Urteil, mit 2 keiner, und der
#: grösste Anteil eines gehaltenen Baukörpers stieg von 0,05 auf 0,14.
FENSTER_MIN_FLAECHEN = 2
#: Ab diesem Anteil seines Inneren, in dem die örtliche Kanten-Deckung unter der Schwelle
#: liegt, heisst ein Baukörper «verfleckt». **Gesetzt aus dem synthetischen Satz (10.11.2026,
#: je 100 Startwerte, ``tests/anlagen_erzeuger.py``), nicht am Gerät geeicht:** 246 gehaltene
#: Baukörper lagen bei höchstens 0,14, 98 verfleckte Hauptbauten bei mindestens 0,50. Ein
#: Drittel liegt in dieser Lücke (Faktor 2,4 nach unten, 1,5 nach oben).
VERFLECKT_AB_ANTEIL = 1.0 / 3.0

GEHALTEN = "gehalten"
AUFGELOEST = "aufgeloest"
VERFLECKT = "verfleckt"
UNGEMESSEN = "ungemessen"

#: Das Urteil über alle Baukörper. Die Wörter sind die der Deckung, damit beide Urteile
#: nebeneinander lesbar sind (``varianten.DECKUNGSGLEICH`` usw.).
DECKUNGSGLEICH = "deckungsgleich"
FORM_WEICHT_AB = "form_weicht_ab"

HERKUNFT = ("Schwelle der Deckung (gesetzt aus auf-20261022-337 und -339), je Baukörper "
            "angewandt: gesetzt, am echten Bild nicht geeicht (A0300)")

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


def inneres(punkte: Sequence[int], kanten_ki: Sequence[bool],
                      kanten_grund: Sequence[bool], breite: int, kasten, *,
                      schwelle: float) -> dict | None:
    """Das Innere EINES Baukörpers: seine Kanten-Deckung ohne den Saum, ganz und örtlich.

    **Ohne den Saum** (:data:`SAUM_PX`): Der Umriss eines Baus gegen den Grund deckt sich fast
    immer (mit «Umriss halten» sicher). Gemessen am 10.11.2026: Eine glatte Platte anstelle des
    Hauptbaus kam allein über ihren Umriss auf 0,21 bis 0,40 (100 Startwerte); im Inneren hat sie 0.

    **Örtlich**: Die Zahl über das ganze Innere mittelt. Hält ein Teil seine Zeichnung genau
    und ist der Rest ein grüner Fleck, liegt sie über der Schwelle. Darum wandert ein Fenster
    (Grösse nach :data:`FENSTER_KANTEN`) über das Innere und rechnet in jedem Stand dieselbe
    Kanten-Deckung; ``anteil`` ist der Teil der Stände unter der Schwelle.

    Returns:
        ``None`` ohne Inneres (der Baukörper ist schmaler als zwei Säume). Sonst ``{innen,
        kanten_grundbild, kanten_iou, anteil, halbe_seite_px, fenster, fenster_darunter}``;
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
    beide, eines = bytearray(b * h), bytearray(b * h)
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
    if not n_innen:
        return None
    summe_beide, summe_eines = sum(beide), sum(eines)
    aus = {"innen": n_innen, "kanten_grundbild": grund_kanten,
           "kanten_iou": None if not summe_eines else round(summe_beide / summe_eines, 4),
           "anteil": None}
    if not grund_kanten:
        return aus
    r = max(3, int(round((FENSTER_KANTEN * n_innen / grund_kanten) ** 0.5 / 2.0)))
    aus["halbe_seite_px"] = r
    if n_innen < FENSTER_MIN_FLAECHEN * (2 * r + 1) ** 2:
        return aus
    schritt = max(1, r // 2)
    t_beide, t_eines = summen(beide), summen(eines)
    fenster = darunter = 0
    for yy in range(0, h, schritt):
        for xx in range(0, b, schritt):
            if not innen[yy * b + xx]:
                continue
            ax, ay, bx, by = max(0, xx - r), max(0, yy - r), min(b, xx + r + 1), min(h, yy + r + 1)
            e = rechteck(t_eines, ax, ay, bx, by)
            if e < FENSTER_MIN_KANTEN:
                continue
            fenster += 1
            if rechteck(t_beide, ax, ay, bx, by) / e < schwelle:
                darunter += 1
    aus["fenster"], aus["fenster_darunter"] = fenster, darunter
    if fenster >= FENSTER_MIN_ANZAHL:
        aus["anteil"] = round(darunter / fenster, 4)
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
        ``{urteil, warnung, schwelle, herkunft, kanten_iou_haus, baukoerper, aufgeloest,
        schwaechster, saetze}``. ``baukoerper`` trägt je Stück ``{nr, name, ort, kasten, n,
        anteil_bild, kanten_iou, innen, urteil}`` (ohne die Punktliste); das Urteil eines
        Baukörpers ist «aufgeloest» (seine Zahl oder die seines Inneren unter der Schwelle),
        «verfleckt» (:func:`inneres`, ``anteil`` ab :data:`VERFLECKT_AB_ANTEIL`), «gehalten» oder
        «ungemessen». ``urteil`` ist «form_weicht_ab», sobald in einer Anlage (``anlage``:
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
        elif grund_kanten < KOERPER_MIN_KANTEN:
            eintrag["urteil"] = UNGEMESSEN
            eintrag["grund"] = (f"nur {grund_kanten} Kantenpunkte im Grundbild, unter "
                                f"{KOERPER_MIN_KANTEN}")
        else:
            innen = inneres(s["punkte"], kanten_ki, kanten_grund, breite, s["kasten"],
                            schwelle=schwelle)
            # Das Innere urteilt mit, wo das Grundbild dort selbst eine Zeichnung hat. Ein Bau,
            # der im Grundbild innen glatt ist, hat innen keine Form zu verlieren.
            innen_zaehlt = innen is not None and innen["kanten_grundbild"] >= KOERPER_MIN_KANTEN
            if innen is not None:
                eintrag["innen"] = innen
            if (iou or 0.0) < schwelle or (innen_zaehlt and (innen["kanten_iou"] or 0.0) < schwelle):
                eintrag["urteil"] = AUFGELOEST
            elif innen_zaehlt and innen["anteil"] is not None \
                    and innen["anteil"] >= VERFLECKT_AB_ANTEIL:
                eintrag["urteil"] = VERFLECKT
            else:
                eintrag["urteil"] = GEHALTEN
        liste.append(eintrag)
    haus = None if eines_haus == 0 else round(beide_haus / eines_haus, 4)
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
    schwaechster = min(gemessen, key=lambda e: e["kanten_iou"] or 0.0) if gemessen else None
    return {"urteil": urteil, "warnung": urteil == FORM_WEICHT_AB, "schwelle": schwelle,
            "herkunft": HERKUNFT, "kanten_iou_haus": haus, "anlage": anlage,
            "baukoerper": liste,
            "aufgeloest": [e["nr"] for e in weicht_ab if e["urteil"] == AUFGELOEST],
            "verfleckt": [e["nr"] for e in weicht_ab if e["urteil"] == VERFLECKT],
            "schwaechster": None if schwaechster is None else schwaechster["nr"],
            "saetze": [satz_des_baukoerpers(e, schwelle) for e in weicht_ab]}


def satz_des_baukoerpers(eintrag: dict, schwelle: float) -> str:
    """Der Satz zu einem Baukörper, der seine Form nicht hält: welcher, wo, mit welcher Zahl."""
    k = eintrag.get("kasten") or [0, 0, 0, 0]
    wo = (f"{SATZ_BAUKOERPER}: {eintrag.get('name')}, Bildpunkte x {k[0]} bis {k[2]}, "
          f"y {k[1]} bis {k[3]}, {float(eintrag.get('anteil_bild') or 0.0):.0%} der "
          f"Bildfläche.")
    if eintrag.get("urteil") == VERFLECKT:
        ort = eintrag.get("innen") or {}
        return (f"{wo} Verfleckt: In {float(ort.get('anteil') or 0.0):.0%} seines Inneren "
                f"liegen die Kanten des KI-Bilds gegen das Grundbild unter {schwelle} (ab "
                f"{VERFLECKT_AB_ANTEIL:.0%} verfleckt; gesetzt am synthetischen Satz, nicht "
                f"geeicht), über den ganzen Baukörper {eintrag.get('kanten_iou')}.")
    innen = (eintrag.get("innen") or {}).get("kanten_iou")
    return (f"{wo} Aufgelöst: Kanten des KI-Bilds gegen das Grundbild dort "
            f"{eintrag.get('kanten_iou')}, im Inneren ohne den Umriss {innen}; die Schwelle "
            f"ist {schwelle} (je Baukörper gesetzt, nicht geeicht).")


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
