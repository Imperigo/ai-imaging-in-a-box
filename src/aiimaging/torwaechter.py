"""TORWÄCHTER — Vorprüfung der Geometrie, BEVOR eine GPU-Stunde verbrannt wird.

Warum dieses Modul existiert
----------------------------
Ein Render ist teuer und langsam; eine Bounding Box ist sechs Zahlen. Zwei Fehlerklassen
haben den Vorläufer KosmoVis mehrfach getroffen, und beide sind an genau diesen sechs
Zahlen erkennbar — lange vor dem ersten Sample:

1. **Massstab.** IFC-Exporte kommen fehlskaliert. Millimeter als Meter gelesen bläht
   einen 30-m-Bau auf 30 km (Faktor 1000), Meter als Millimeter schrumpfen ihn auf 3 cm
   (Faktor 1/1000). Beides bricht Kameraableitung, Tiefenkarte und die spätere
   Geometrie-QA. Im Vorläufer degenerierte ein solcher Fehler alle Bodenplatten auf
   0.004 m — jeder daraus erzeugte Render war eine Halluzination mit korrekt aussehender
   Herkunft.

2. **Georeferenzierung.** Ein schweizerisch verortetes Modell (LV95) sitzt bei einem
   Ostwert um 2.6e6 m. glTF 2.0 speichert Positionen als **float32**: 24 Bit Mantisse,
   also eine relative Auflösung von 2^-23. Bei einem Betrag von 2.6e6 m sind das rund
   0.31 m Quantisierung — sichtbares Zittern, aufreissende Flächen, wandernde Kanten.

Die eine Unterscheidung, um die es hier geht
--------------------------------------------
* **Massstab ist ein Quell-Datenfehler → ABLEHNEN.** Er gehört im Export behoben. Hier
  kaschiert, wanderte er unbemerkt durch die ganze Kette und käme als „unerklärliches“
  Bildproblem zurück.
* **Georeferenz ist heilbar → NICHT ablehnen, sondern Neuzentrierung empfehlen.** Die
  XY-Bbox-Mitte auf den Ursprung schieben genügt; **Z bleibt unberührt**, denn die
  Bodenkote trägt die Geschosshöhen. Ein mitverschobenes Z macht aus einem echten
  Datenfehler ein plausibel aussehendes Modell mit falschen Höhen — die schlimmere Sorte
  Fehler, weil niemand sie sucht.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es rechnet nichts um. Der Verdachtsfaktor wird gemeldet, die Neuzentrierung wird
empfohlen — angewendet wird beides anderswo und sichtbar. Stillschweigend reparieren ist
die Linie, gegen die dieses Projekt durchgehend antritt (siehe ``contracts.py``).

Abhängigkeiten: keine. Reine stdlib, kein numpy, kein ``bpy``, kein ``ifcopenshell``.
Rein rechnend — keine Dateien, kein Subprozess. Damit ist der Torwächter überall
prüfbar, auch dort, wo weder Blender noch eine GPU existiert (Regel 4).
"""
from __future__ import annotations

import math

#: Geometrie darf gerendert werden.
ENTSCHEIDUNG_ANNEHMEN = "annehmen"

#: Quell-Datenfehler im Massstab. Gehört an der Quelle behoben, nicht hier.
ENTSCHEIDUNG_ABLEHNEN_MASSSTAB = "ablehnen_massstab"

#: Die Konversion selbst ist gescheitert oder ihr Report ist unbrauchbar.
ENTSCHEIDUNG_ABLEHNEN_KONVERSION = "ablehnen_konversion"

# Plausible Gebäudemasse in Metern, gemessen an der GRÖSSTEN Kante der Bounding Box.
#
# Untergrenze 1 m: Kleiner ist kein Bauwerk, sondern ein Bauteil oder ein Massstabsfehler.
# Ein Gartenhaus misst 2–3 m; wer eine einzelne Tür rendert, liegt mit 2.1 m darüber.
# Erst unter 1 m wird die Aussage „das ist ein Gebäude“ unhaltbar.
#
# Obergrenze 1000 m: Das höchste Bauwerk der Welt misst 828 m, ein grosser Campus deckt
# einige hundert Meter ab. 1000 m lässt jedes realistische Einzelprojekt durch und fängt
# den Faktor-1000-Fehler trotzdem sicher: Ein Bau, der plausibel wäre (≥ 1 m), landet
# millimeter-als-meter-gelesen bei ≥ 1000 m und damit ausserhalb.
#
# Die beiden Grenzen sind bewusst weit. Ein Torwächter, der zu eng schneidet, wird
# umgangen — und dann fängt er gar nichts mehr.
MIN_GEBAEUDE_M = 1.0
MAX_GEBAEUDE_M = 1000.0

#: Bis zum Wievielfachen der Gebäudegrenze ein Modell als **Kontextmodell** gilt statt
#: als Einheitenfehler.
#:
#: An 40 echten Dateien (`auf-20260818-08`) fielen zwei Modelle mit 1002 m und 1127 m
#: hier durch — Gelände samt Umgebung, Einheit völlig in Ordnung. Abgelehnt werden sie
#: weiterhin; die Kette rechnet mit einem Bauwerk. Aber die Meldung nennt jetzt die
#: richtige Ursache, statt einen Einheitenfehler auszuschliessen und sonst zu schweigen.
#:
#: Die Grenze ist grosszügig: Ein echter Faktor-1000-Fehler landet bei mindestens
#: 1000 m **mal** der wahren Gebäudegrösse, also weit jenseits davon. Eine Verwechslung
#: der beiden Fälle ist damit praktisch ausgeschlossen.
KONTEXTMODELL_FAKTOR = 100.0

#: Ab welcher Grösse ein angenommenes Bauwerk **glaubwürdig** ist — für die Prüfung einer
#: Einheiten-Hypothese, nicht für die Annahme der Geometrie.
#:
#: `MIN_GEBAEUDE_M` steht bei 1 m und ist bewusst weit: Ein einzelnes Bauteil darf
#: durchgehen. Für die Frage „ist das ein Millimeterfehler?" taugt diese Schranke aber
#: nicht — ein Kontextmodell von 1002 m ergäbe unter dieser Hypothese 1,002 m, was formal
#: in der Spanne liegt und praktisch kein Bauwerk ist. Drei Meter sind eine Geschosshöhe;
#: darunter erklärt die Hypothese nichts mehr, sie verschiebt nur die Zahl.
MIN_GLAUBWUERDIG_M = 3.0

# Ab welchem Koordinatenbetrag float32 zu grob wird.
#
# 1e5 m ergibt eine Quantisierung von 1e5 · 2^-23 ≈ 0.012 m — gut ein Zentimeter, die
# Schwelle, ab der die Zitterbewegung in einem Render bemerkbar wird. Darunter bleibt
# der Fehler unter der Fugenbreite. Ein lokal modelliertes Gebäude (Koordinaten in
# Metern um den Ursprung) liegt um Grössenordnungen darunter, LV95 mit ~2.6e6 m
# deutlich darüber.
GEOREF_SCHWELLE_M = 1.0e5

#: Relative Auflösung von float32: 24 Bit Mantisse, davon 23 gespeichert → 2^-23.
#: glTF 2.0 schreibt float32 für Positionen vor; das ist keine Wahl des Erzeugers.
_FLOAT32_AUFLOESUNG = 2.0 ** -23


# --------------------------------------------------------------------------------------
# Bbox lesen — defensiv, weil der Report aus einem fremden Prozess kommt
# --------------------------------------------------------------------------------------

def _zahl(wert):
    """Ein einzelner Bbox-Wert als endlicher ``float`` — oder ``None``, wenn unbrauchbar.

    ``bool`` wird abgewiesen, obwohl es in Python ein ``int`` ist: ``True`` als Koordinate
    ist immer ein Irrtum, nie eine Absicht. Zahlen in Textform (``"8.0"``) werden
    ebenfalls abgewiesen — sie stillschweigend zu deuten wäre genau die Art Reparatur,
    die dieses Projekt nicht macht.
    """
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        return None
    zahl = float(wert)
    if not math.isfinite(zahl):
        # NaN und inf entstehen real: leere Szene, Überlauf im Exporter, ein Element ohne
        # Geometrie. Sie dürfen keinen Vergleich erreichen — NaN-Vergleiche sind immer
        # falsch und liessen jede Prüfung still durchfallen.
        return None
    return zahl


def _lies_bbox(bbox):
    """bbox → ``(untere_ecke, obere_ecke)`` mit je drei endlichen Zahlen, sonst ``None``.

    Der Report stammt aus einem fremden Prozess jenseits der Prozessgrenze. Alles ist
    möglich: ``None``, eine flache Liste, zwei statt drei Werte, ein Traceback-Rest.
    Nichts davon darf einen ``TypeError`` auslösen — der Torwächter soll ablehnen, nicht
    abstürzen.
    """
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 2:
        return None
    ecken = []
    for ecke in bbox:
        if not isinstance(ecke, (list, tuple)) or len(ecke) != 3:
            return None
        werte = [_zahl(w) for w in ecke]
        if any(w is None for w in werte):
            return None
        ecken.append(werte)
    return ecken[0], ecken[1]


def masse_aus_bbox(bbox) -> tuple[float, float, float]:
    """bbox als ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` → Kantenlängen ``(dx, dy, dz)``.

    Die Längen werden als Betrag gebildet. Vertauschte Ecken (obere vor unterer) sind
    dadurch kein Fehler, sondern nur eine andere Schreibweise derselben Box — die
    Ausdehnung ist in beiden Fällen dieselbe.

    Raises:
        ValueError: bbox fehlt, hat die falsche Form oder enthält NaN/inf. Diese
            Funktion ist der einzige Ort im Modul, der wirft; die Prüffunktionen
            darunter fangen den Fall ab und antworten mit einer sauberen Ablehnung.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        raise ValueError(
            "bbox unbrauchbar. Erwartet [[xmin,ymin,zmin],[xmax,ymax,zmax]] mit sechs "
            f"endlichen Zahlen, war: {bbox!r}"
        )
    unten, oben = gelesen
    return (abs(oben[0] - unten[0]), abs(oben[1] - unten[1]), abs(oben[2] - unten[2]))


# --------------------------------------------------------------------------------------
# Massstab — Quell-Datenfehler, führt zur Ablehnung
# --------------------------------------------------------------------------------------

def pruefe_massstab(bbox) -> dict:
    """Liegt die grösste Kante in plausiblen Gebäudemassen?

    Returns:
        ``{plausibel, groesste_kante_m, verdacht_faktor, warnungen}``.

        ``verdacht_faktor`` ist ``1000``, wenn die Geometrie um Faktor 1000 zu gross ist
        (Millimeter als Meter gelesen), und ``0.001``, wenn sie um denselben Faktor zu
        klein ist (Meter als Millimeter). In beiden Fällen gilt dieselbe Lesart: die
        wahren Masse sind ``gemessen / verdacht_faktor``. Lässt sich der Fehlgriff nicht
        auf einen Einheitenwechsel zurückführen, bleibt der Faktor ``None`` — der
        Massstab ist dann trotzdem unplausibel.

        Der Faktor wird **gemeldet, nicht angewendet**. Eine Umrechnung hier hiesse, den
        Quellfehler zu kaschieren; er kehrt dann in der Geometrie-QA als Rätsel wieder.

        ``groesste_kante_m`` ist ``None``, wenn die bbox nicht lesbar war. Bewusst
        ``None`` statt ``0.0``: eine Null behauptete eine Messung, die nicht stattfand.

    Bemerkt wird nur die grösste Kante. Eine flache Bodenplatte hat eine Ausdehnung von
    0 in Z und ist trotzdem gültige Geometrie — die Unterschreitung einzelner Achsen wird
    darum als Warnung gemeldet, nicht als Ablehnungsgrund.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        return {
            "plausibel": False,
            "groesste_kante_m": None,
            "verdacht_faktor": None,
            "warnungen": [
                "bbox unbrauchbar — Massstab nicht prüfbar. Erwartet "
                "[[xmin,ymin,zmin],[xmax,ymax,zmax]] mit sechs endlichen Zahlen."
            ],
        }

    dx, dy, dz = masse_aus_bbox(bbox)
    groesste = max(dx, dy, dz)
    plausibel = MIN_GEBAEUDE_M <= groesste <= MAX_GEBAEUDE_M
    warnungen: list[str] = []
    faktor = None

    if not plausibel:
        # Beide Kandidaten in derselben Leserichtung prüfen: gemessen / faktor = wahr.
        #
        # Die untere Schranke ist hier **nicht** `MIN_GEBAEUDE_M`, und das ist der Kern
        # der Korrektur vom 18.08.2026: Ein Kontextmodell von 1002 m ergibt unter der
        # Millimeter-Hypothese 1,002 m — formal in der Spanne, praktisch kein Bauwerk.
        # Genau daran sind an 40 echten Dateien zwei Geländemodelle als „Einheitenfehler"
        # gemeldet worden (`auf-20260818-08`).
        #
        # Eine Hypothese ist nur so gut wie das, was sie erklärt. „Millimeter" erklärt
        # etwas erst dann, wenn dabei ein **glaubwürdiges** Bauwerk herauskommt — nicht,
        # wenn das Ergebnis gerade so über der Nulllinie liegt.
        for kandidat in (1000.0, 0.001):
            angenommen = groesste / kandidat
            if MIN_GLAUBWUERDIG_M <= angenommen <= MAX_GEBAEUDE_M:
                faktor = kandidat
                break

        if faktor == 1000.0:
            warnungen.append(
                f"Grösste Kante {groesste:.4g} m. Verdacht: Millimeter als Meter gelesen "
                f"(Faktor 1000) — ein 30-m-Bau erscheint als 30-km-Bau. Wahre Masse "
                f"vermutlich {groesste / 1000.0:.4g} m. Korrektur gehört in den Export, "
                f"nicht hierher."
            )
        elif faktor == 0.001:
            warnungen.append(
                f"Grösste Kante {groesste:.4g} m. Verdacht: Meter als Millimeter gelesen "
                f"(Faktor 1/1000) — ein 30-m-Bau schrumpft auf 3 cm. Wahre Masse "
                f"vermutlich {groesste * 1000.0:.4g} m. Korrektur gehört in den Export, "
                f"nicht hierher."
            )
        elif groesste == 0.0:
            warnungen.append(
                "Bounding Box ohne Ausdehnung — beide Ecken fallen zusammen. Leere oder "
                "vollständig degenerierte Geometrie; es gibt nichts zu rendern."
            )
        elif MAX_GEBAEUDE_M < groesste <= MAX_GEBAEUDE_M * KONTEXTMODELL_FAKTOR:
            # BEFUND AN 40 ECHTEN DATEIEN (`auf-20260818-08`, 18.08.2026): Zwei Modelle
            # mit 1002 m und 1127 m grösster Kante wurden hier abgelehnt — mit der
            # Meldung, der Abstand entspreche keinem Einheitenwechsel. Das stimmte und
            # half niemandem: **Es waren Kontextmodelle**, also Gelände samt Umgebung,
            # und ihre Einheit war völlig in Ordnung.
            #
            # Der Torwächter lehnt sie weiterhin ab, und das ist richtig — die Kette
            # rechnet mit einem Bauwerk, und eine Kamera auf einen Quadratkilometer
            # gerichtet liefert eine Tiefenkarte, in der das Haus ein paar Pixel misst.
            # Aber er sagt jetzt, **was** er sieht, statt nur, was es nicht ist.
            #
            # Der Unterschied ist derselbe wie bei `herkunft.pruefe_einheit_gegen_masse`:
            # Ein Verdacht kostet jedes Mal einen Menschen, der nachsieht; eine Diagnose
            # sagt ihm, was zu tun ist.
            warnungen.append(
                f"Grösste Kante {groesste:.4g} m — über der Gebäudegrenze "
                f"({MAX_GEBAEUDE_M:g} m), aber **kein Einheitenfehler**: Ein Faktor 1000 "
                f"läge bei {groesste / 1000.0:.4g} m oder {groesste * 1000.0:.4g} m, und "
                f"beides ist keine Gebäudegrösse. Das sieht nach einem **Kontext- oder "
                f"Geländemodell** aus. Zwei von 40 echten Dateien waren genau das "
                f"(1002 m und 1127 m). Zu rendern ist so ein Modell nicht sinnvoll: Eine "
                f"Kamera auf einen Quadratkilometer liefert eine Tiefenkarte, in der das "
                f"Bauwerk ein paar Bildpunkte misst. Wer es trotzdem braucht, schneidet "
                f"den Ausschnitt vorher zu — in der Herkunftssoftware, nicht hier."
            )
        else:
            warnungen.append(
                f"Grösste Kante {groesste:.4g} m liegt ausserhalb der plausiblen "
                f"Gebäudemasse [{MIN_GEBAEUDE_M:g}, {MAX_GEBAEUDE_M:g}] m, und der "
                f"Abstand entspricht keinem Einheitenwechsel um Faktor 1000."
            )
    else:
        # Plausibel, aber eine Achse ohne Ausdehnung: erwähnenswert (Blender-Kamera und
        # Tiefenkarte brauchen ein Volumen), aber kein Grund abzulehnen — eine
        # Geländeplatte oder ein einzelnes Geschoss sieht genau so aus.
        for name, laenge in (("X", dx), ("Y", dy), ("Z", dz)):
            if laenge == 0.0:
                warnungen.append(
                    f"Ausdehnung 0 in {name} — flache Geometrie. Kein Ablehnungsgrund, "
                    f"aber Kameraableitung und Tiefenkarte werden entartet aussehen."
                )

    return {
        "plausibel": plausibel,
        "groesste_kante_m": groesste,
        "verdacht_faktor": faktor,
        "warnungen": warnungen,
    }


# --------------------------------------------------------------------------------------
# Georeferenz — heilbar, führt zur Empfehlung statt zur Ablehnung
# --------------------------------------------------------------------------------------

def pruefe_georeferenz(bbox) -> dict:
    """Sitzt die Geometrie so weit vom Ursprung, dass float32 zu grob wird?

    Returns:
        ``{georeferenziert, groesster_betrag_m, quantisierung_m,
        empfiehlt_neuzentrierung, warnungen}``.

        ``quantisierung_m`` ist ``groesster_betrag_m · 2^-23`` — der Abstand zweier
        benachbarter darstellbarer float32-Werte bei diesem Betrag, also die kleinste
        Bewegung, die eine Ecke überhaupt noch machen kann. Bei LV95 (~2.6e6 m) sind das
        rund 0.31 m: Ecken springen um Dezimeter, Flächen reissen auf.

        ``empfiehlt_neuzentrierung`` folgt dem **XY**-Betrag, nicht dem Gesamtbetrag.
        Die Heilung ist ein Verschieben der XY-Bbox-Mitte auf den Ursprung; **Z bleibt
        unberührt**, weil die Bodenkote die Geschosshöhen trägt. Läge die Grobheit
        ausnahmsweise allein an einer riesigen Z-Koordinate, hülfe die XY-Verschiebung
        nichts — dieser Fall wird als Warnung gemeldet, statt eine wirkungslose
        Empfehlung auszusprechen.

    Eine Georeferenz ist **kein Ablehnungsgrund**. Sie ist eine Eigenschaft korrekt
    verorteter Modelle und in einem Schritt heilbar; der Massstabsfehler ist es nicht.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        return {
            "georeferenziert": False,
            "groesster_betrag_m": None,
            "quantisierung_m": None,
            "empfiehlt_neuzentrierung": False,
            "warnungen": [
                "bbox unbrauchbar — Georeferenz nicht prüfbar. 'georeferenziert: False' "
                "ist hier keine Feststellung, sondern das Fehlen einer Messung."
            ],
        }

    unten, oben = gelesen
    betrag_xy = max(abs(unten[0]), abs(unten[1]), abs(oben[0]), abs(oben[1]))
    betrag_z = max(abs(unten[2]), abs(oben[2]))
    groesster = max(betrag_xy, betrag_z)
    quantisierung = groesster * _FLOAT32_AUFLOESUNG

    georeferenziert = groesster >= GEOREF_SCHWELLE_M
    empfiehlt = betrag_xy >= GEOREF_SCHWELLE_M
    warnungen: list[str] = []

    if empfiehlt:
        warnungen.append(
            f"Koordinatenbetrag bis {groesster:.6g} m (XY bis {betrag_xy:.6g} m). glTF "
            f"2.0 speichert Positionen als float32 — die Auflösung beträgt hier rund "
            f"{quantisierung:.3g} m. Empfehlung: XY-Bbox-Mitte auf den Ursprung "
            f"verschieben. Z NICHT verschieben, die Bodenkote trägt die Geschosshöhen."
        )
    elif georeferenziert:
        warnungen.append(
            f"Koordinatenbetrag bis {groesster:.6g} m, aber allein in Z (XY bis "
            f"{betrag_xy:.6g} m). Eine XY-Neuzentrierung hilft hier nicht; die Höhenlage "
            f"gehört an der Quelle geprüft."
        )

    return {
        "georeferenziert": georeferenziert,
        "groesster_betrag_m": groesster,
        "quantisierung_m": quantisierung,
        "empfiehlt_neuzentrierung": empfiehlt,
        "warnungen": warnungen,
    }


# --------------------------------------------------------------------------------------
# Gesamturteil
# --------------------------------------------------------------------------------------

def _urteil(entscheidung: str, begruendung: str, massstab: dict, georeferenz: dict) -> dict:
    """Baut die Antwort. Ein Ort, damit kein Rückgabepfad ein Feld vergisst."""
    return {
        "entscheidung": entscheidung,
        "begruendung": begruendung,
        "massstab": massstab,
        "georeferenz": georeferenz,
        # Auch bei Ablehnung mitgeführt: Wer den Massstab an der Quelle repariert, will
        # nicht erst nach dem zweiten Lauf erfahren, dass zusätzlich neuzentriert gehört.
        "empfiehlt_neuzentrierung": georeferenz["empfiehlt_neuzentrierung"],
    }


def torwaechter(report: dict) -> dict:
    """Gesamturteil über einen ``ifc_to_glb``-Report — vor dem Render, nicht danach.

    Args:
        report: Report aus ``aiimaging.runners.ifc_to_glb_runner`` bzw.
            ``seams.ifc_zu_glb``. Gelesen werden ``status``, ``error`` und ``bbox``.

    Returns:
        ``{entscheidung, begruendung, massstab, georeferenz, empfiehlt_neuzentrierung}``.

    Die Prüfreihenfolge und warum sie so ist:

    1. ``status != "ok"`` → ``ablehnen_konversion``. Ohne gelungene Konversion gibt es
       nichts zu rendern.
    2. bbox unlesbar → ``ablehnen_konversion``. Ein Report, der Erfolg meldet und keine
       brauchbare bbox trägt, ist kein Massstabsfehler der Quelle, sondern ein Defekt des
       Reports selbst.
    3. Massstab unplausibel → ``ablehnen_massstab``. **Diese Prüfung ist von Schritt 1
       unabhängig**, und das ist der Kern des Entwurfs: Eine Konversion kann sauber
       ``ok`` melden und die Geometrie trotzdem um Faktor 1000 danebenliegen. Genau diese
       Kombination ist im Vorläufer aufgetreten — der Runner war zufrieden, das Modell
       30 km gross, und der Fehler fiel erst am fertigen Bild auf. Wer den Massstab nur
       prüft, wenn ohnehin schon etwas anderes kaputt ist, prüft nichts.
    4. Sonst ``annehmen`` — gegebenenfalls mit der Empfehlung zur Neuzentrierung. Die
       Georeferenz ist ausdrücklich **kein** Ablehnungsgrund: Sie ist heilbar, der
       Massstabsfehler gehört an die Quelle.

    Der übergebene Report wird nur gelesen, nie verändert.
    """
    if not isinstance(report, dict):
        return _urteil(
            ENTSCHEIDUNG_ABLEHNEN_KONVERSION,
            f"Report ist kein Objekt, sondern {type(report).__name__}.",
            pruefe_massstab(None),
            pruefe_georeferenz(None),
        )

    bbox = report.get("bbox")
    # Beide Prüfungen laufen immer und auf allem, was da ist — auch bei gescheiterter
    # Konversion. Der Aufrufer soll alles sehen, was aus den vorhandenen Zahlen
    # ableitbar ist, statt nach jeder behobenen Ursache erneut anzustossen.
    massstab = pruefe_massstab(bbox)
    georeferenz = pruefe_georeferenz(bbox)

    status = report.get("status")
    if status != "ok":
        fehler = report.get("error")
        begruendung = f"Konversion meldet status={status!r}"
        begruendung += f": {fehler}" if fehler else "."
        return _urteil(ENTSCHEIDUNG_ABLEHNEN_KONVERSION, begruendung, massstab, georeferenz)

    if _lies_bbox(bbox) is None:
        return _urteil(
            ENTSCHEIDUNG_ABLEHNEN_KONVERSION,
            "Konversion meldet status='ok', trägt aber keine brauchbare bbox "
            f"({bbox!r}). Ohne Ausdehnung ist weder Massstab noch Georeferenz prüfbar — "
            "und ungeprüft wird nicht gerendert.",
            massstab,
            georeferenz,
        )

    if not massstab["plausibel"]:
        faktor = massstab["verdacht_faktor"]
        begruendung = (
            f"Massstab unplausibel: grösste Kante {massstab['groesste_kante_m']:.4g} m, "
            f"plausibel wären [{MIN_GEBAEUDE_M:g}, {MAX_GEBAEUDE_M:g}] m."
        )
        if faktor is not None:
            begruendung += (
                f" Verdacht auf Einheitenfehler um Faktor {faktor:g} (wahre Masse "
                f"vermutlich gemessen/{faktor:g}). Es wird nichts umgerechnet — der "
                f"Fehler gehört an der Quelle behoben, sonst wandert er unbemerkt durch "
                f"die ganze Kette."
            )
        return _urteil(ENTSCHEIDUNG_ABLEHNEN_MASSSTAB, begruendung, massstab, georeferenz)

    begruendung = (
        f"Massstab plausibel (grösste Kante {massstab['groesste_kante_m']:.4g} m)."
    )
    if georeferenz["empfiehlt_neuzentrierung"]:
        begruendung += (
            f" Modell ist georeferenziert (Betrag bis "
            f"{georeferenz['groesster_betrag_m']:.6g} m, float32-Auflösung rund "
            f"{georeferenz['quantisierung_m']:.3g} m): vor dem Render XY-Bbox-Mitte auf "
            f"den Ursprung verschieben, Z unverändert lassen. Kein Ablehnungsgrund — "
            f"heilbar in einem Schritt."
        )
    elif georeferenz["georeferenziert"]:
        begruendung += " " + georeferenz["warnungen"][0]
    else:
        begruendung += " Koordinaten nahe genug am Ursprung für float32."
    return _urteil(ENTSCHEIDUNG_ANNEHMEN, begruendung, massstab, georeferenz)
