"""KAMERAS — wo eine Kamera stehen muss, damit das Gebäude im Bild ist.

Warum dieses Modul existiert
----------------------------
Der Vorläufer KosmoVis hat diese Rechnung schon einmal gelöst, und zwar gut. Die
Bestandsaufnahme (``docs/BLENDER_ADDON_BESTAND_2026-08-18.md``, Teil A.1/A.2) hat sie
in 83 Modulen gefunden: ``archviz_pipeline_v6_camera_math.py`` und ihren Vorläufer
``archviz_camera.py``. Beide liegen jenseits einer ``import bpy``-Zeile, die zwei ihrer
vier Funktionen gar nicht brauchen. Dieses Modul ist der Nachbau der rechnenden Hälfte
diesseits der Grenze — mit den Verbesserungen, die beim Vergleich der beiden Fassungen
sichtbar wurden.

Was hier NICHT drin ist: der Verdeckungstest per Strahlenschuss. Der braucht die Szene
und gehört in den Runner. Was hier drin ist, ist seine **Schrittlogik** — die
Sichtprüfung wird als Funktion hereingereicht (``_sicht_frei``), damit der Ablauf ohne
Blender prüfbar bleibt. Das ist die Trennung, die der Bestand nicht macht.

Der Kameravertrag — eine Entscheidung, keine Fundsache
-------------------------------------------------------
Der Bestand trägt **drei unvereinbare Kameraverträge und drei Augenhöhen**:
``look_at`` gegen ``rotation_euler`` gegen ``azimut``/``elevation``; 1.70 m absolut
gegen 1.70 m über dem Gebäudefuss gegen 1.65 m. Das ist keine Rundung, sondern eine
andere Annahme über den Menschen im Bild. Hier gilt:

* **``blick_auf`` ist die führende Form.** Ein Blickziel ist erklärbar und unabhängig
  von Rotationskonventionen. Eine Blender-Rotation lässt sich daraus jederzeit ableiten;
  zurück geht es **nicht** eindeutig, weil ein Blickvektor keine Zielentfernung kennt.
  Wer die verlustbehaftete Form führt, kann die andere nie zurückgewinnen.
* **Die Augenhöhe misst 1.70 m — über dem GELÄNDE, nicht über der Nulllinie.**
  1.70 m, weil das ausgereifteste Verfahren des Bestands und die Mehrheit der
  Fundstellen es so halten.

  Der Bezugspunkt hat mich zuerst einen Irrtum gekostet, und der gehört hierher.
  Zunächst stand hier **absolut**, mit der Begründung: Der Betrachter steht auf dem
  Gelände und nicht auf der Unterkante der Hüllbox — bei einem Gebäude mit Untergeschoss
  sind das zwei verschiedene Orte. Das Argument stimmt und die Folgerung war falsch.
  Absolut heisst nämlich: über **z = 0**, und das ist nur dort das Gelände, wo das Modell
  zufällig auf Meereshöhe sitzt. Ein Bauwerk mit Fuss auf 400 m über Meer bekam eine
  Kamera auf 1.70 m — **400 Meter unter dem Erdgeschoss**. Aufgefallen an einem Test über
  die Höhenlage, nicht an einem Bild.

  Beide Bezüge sind also falsch, wenn man sie zum Naturgesetz macht. Richtig ist der
  **Geländestand**, und den kennt die Hüllbox nicht. Darum: ``gelaende_z`` ist ein
  Parameter. Wer ihn kennt, gibt ihn an. Ohne Angabe gilt die Unterkante der Hüllbox —
  die einzige Bodenreferenz, die in den Daten steckt, und im Zweifel um eine
  Geschosshöhe daneben statt um vierhundert Meter.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es setzt keine Kamera. Es rechnet Positionen und gibt sie mit ihrer Begründung zurück.
Das Setzen ist Sache des Runners jenseits der Prozessgrenze.

Abhängigkeiten: keine. Reine stdlib, kein numpy, kein ``bpy`` (Regel 2), aus Python
heraus ohne jede Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math

from .torwaechter import _lies_bbox

# --------------------------------------------------------------------------------------
# Die Zahlen, und warum sie so stehen
# --------------------------------------------------------------------------------------

#: Sensorbreite in Millimetern. 36 mm ist Kleinbild — die Bezugsgrösse, auf die sich
#: jede Brennweitenangabe in der Architekturfotografie stillschweigend bezieht.
SENSOR_BREITE_MM = 36.0

#: Vorgabe-Brennweite in Millimetern, Kleinbild.
#:
#: **35 mm ist eine SETZUNG des Owners (23.08.2026), keine Ableitung.** Er hat sie als
#: eigene Vorliebe benannt, und genau so steht sie hier — die Unterscheidung zwischen
#: „belegt" und „gesetzt" ist in diesem Projekt keine Formalie (siehe
#: :mod:`aiimaging.komposition`).
#:
#: **Die Recherche sagt etwas anderes, und das gehört danebengeschrieben:** Der
#: HABS-Objektivsatz ergibt umgerechnet 18/25/42/59 mm Kleinbild, und die heutige
#: Ratgeberliteratur trifft sich unabhängig davon bei 24–25 mm
#: (`docs/recherche/KOMPOSITION_AUSSEN.md` §4.2). Zwei unabhängige Quellen gegen eine
#: Vorliebe — die Vorliebe gewinnt, weil es das Bild des Owners ist, und der Widerspruch
#: bleibt sichtbar statt weggeräumt.
#:
#: Vorher stand hier 28 mm, hergeleitet aus dem KosmoVis-Bestand (V6 nutzt 28, der
#: Vorläufer 35). **Nachgemessen, was der Wechsel kostet:** Die Kamera steht rund 19 %
#: weiter weg (bei 15 m Bauhöhe 106 statt 90 m), der Füllgrad bleibt beim angeforderten
#: Wert, und der sichtbare Flächenanteil steigt sogar leicht (0.0623 → 0.0672), weil das
#: längere Objektiv weniger staucht. Kein Eckentest schlägt fehl, keine neue Warnung.
#:
#: **Einstellbar bleibt sie überall**: ``kamerasatz(brennweite_mm=…)``,
#: ``verarbeiter(brennweite_mm=…)``, ``--brennweite`` am Runner, und je Kamera über das
#: Feld ``brennweite_mm`` einer fremden ``CameraSpec``.
BRENNWEITE_MM = 35.0

#: Augenhöhe in Metern, gemessen **über dem Geländestand** — siehe Modulkopf.
#: Ohne bekannten Geländestand über der Unterkante der Hüllbox.
AUGENHOEHE_M = 1.70

#: Anteil der Bildbreite, den das Gebäude füllen soll. Ein Wert unter 1 schiebt die Kamera
#: weiter weg und lässt Luft — das ist die „2/3-Komposition" als Zahl.
#:
#: **0.70 seit dem 25.08.2026 (Owner-Entscheid). Vorher 0.55, aus dem Bestand übernommen
#: und dort erprobt — aber gemessen zu wenig.**
#:
#: Der Anlass ist eine Messung der HomeStation (`auf-13`, 24.08.2026) und ein Befund
#: daraus, der beim Bauen von :func:`rahmungsverhaeltnis` anfiel: Das Geometrie-Tor
#: überschreitet die Schwelle erst zwischen **0,5991 und 0,6488** Bildbreite; bei 0,70
#: besteht **jeder von drei Startwerten** mit Abstand 0,301, bei 0,65 steht einer bei
#: 0,114. Die alte Vorgabe von 0,55 lag also **unter dem Knie** — auch dann, wenn gar kein
#: Gelände in der Szene war.
#:
#: **Das war die zweite Hälfte einer Erklärung, die eine Woche lang fehlte.** Dass die
#: Schwelle 0,65 als unerreichbar galt, lag zum einen an der Rahmung der ganzen Szene
#: statt des Bauwerks — und zum anderen daran, dass die Vorgabe selbst zu weit stand.
#:
#: **Was der Wechsel kostet, ist nachgerechnet und nicht geraten:** Der Abstand sinkt um
#: den Faktor 0,55/0,70 ≈ 0,79. Über drei Bauformen (Flachbau 8 m, Wohnhaus 15 m, Turm
#: 45 m) und alle zwölf Richtungen bleibt der Eckentest vollständig, und **kein einziger
#: Shift** überschreitet :data:`MAX_SHIFT_MM`. Der Preis ist gestalterisch: weniger
#: Umgebung, mehr Bauwerk — und das war die Frage, die der Owner entschieden hat.
DECKUNGSGRAD = 0.70

#: Sicherheitsrand beim Eckentest: 8 % des Bildes bleiben frei. Ohne ihn sitzt eine
#: Gebäudeecke rechnerisch genau auf der Bildkante — und liegt nach der ersten
#: Objektivverzeichnung draussen.
BILDRAND = 0.92

#: Das Blickziel liegt nicht auf Augenhöhe, sondern um diesen Anteil der Gebäudehöhe
#: darüber. Die Kamera kippt dadurch leicht nach oben, das Gebäude sitzt tiefer im Bild.
#: Der übliche Griff der Architekturfotografie.
ZIEL_ANTEIL_HOEHE = 0.20

#: Obergrenze für das Blickziel, als Anteil der Gebäudehöhe über dem Fuss.
#:
#: **Das Blickziel darf das Bauwerk nicht verlassen.** Ohne diese Schranke rechnet
#: ``AUGENHOEHE_M + dz · ZIEL_ANTEIL_HOEHE`` bei niedrigen Bauten ein Ziel ÜBER dem Dach:
#: Ein 2 m hoher Körper bekäme ein Ziel auf 2,1 m, die Kamera schaute über ihn hinweg, und
#: der Rahmen wäre zur Hälfte mit Boden und Himmel gefüllt. Am echten Blender-Lauf
#: aufgefallen (18.08.2026): 2,4 % der Bildpunkte trugen Tiefe.
#:
#: Für Gebäudemasse ändert die Schranke nichts — bei 20 m Höhe liegt das ungeschränkte
#: Ziel bei 5,7 m und die Schranke bei 10 m, es gewinnt weiterhin das erste. Sie greift
#: genau dort, wo die absolute Augenhöhe das Verfahren sonst aus dem Tritt bringt: bei
#: Bauten, die kaum höher sind als der Betrachter.
#:
#: Die Vorlage aus dem Bestand hat diese Schranke nicht. Sie ist dort nie aufgefallen,
#: weil nur echte Gebäude gerendert wurden.
ZIEL_HOECHSTANTEIL = 0.5

#: Mindestabstand zur Fassade in Metern, zusätzlich zur halben Grundrissseite. Verhindert,
#: dass die analytische Rechnung eine Kamera in die Wand stellt.
WANDABSTAND_M = 10.0

#: Seitlicher Versatz bei frontalen Ansichten, als Anteil der Gebäudebreite. Eine exakt
#: mittige Frontale ist symmetrisch und damit bildlich tot.
FRONTAL_VERSATZ = 0.10

#: Vorgabe für ``bias_grad`` — siehe ``richtungen``.
BIAS_GRAD = 35.0

# --------------------------------------------------------------------------------------
# Waagrechte Kamera und Shift — die einzige verbindliche Regel des Fachs
# --------------------------------------------------------------------------------------

#: Die Kamera kippt, um zu rahmen. Bisheriger und **weiterhin vorgegebener** Modus.
#:
#: Er verletzt die einzige institutionell verbindliche Regel der Architekturfotografie
#: (HABS/NPS: senkrechte Kanten bleiben senkrecht). Er bleibt trotzdem die Vorgabe, weil
#: ein Wechsel **jede bisher gemessene Aufnahme** verändern würde und am Gerät gemessen
#: ist, dass er dem Tiefenschätzer nichts nimmt (``auf-20260822-29``: über Eck −0,9835
#: gekippt gegen −0,9650 waagrecht, alle drei innerhalb von 0,019).
#:
#: **Seit dem 23.08.2026 ist er nicht mehr die Vorgabe** — siehe :data:`MODUS_SHIFT`.
#: Er bleibt vollständig erhalten und ist mit ``modus=MODUS_GEKIPPT`` zu haben: Jede vor
#: diesem Tag gemessene Aufnahme ist damit weiterhin bitgleich reproduzierbar, und
#: ``auf-33`` hat genau das nachgewiesen.
#:
#: **Wieviel er kippt — nachgemessen, zweimal, und beide Male anders als behauptet.**
#:
#: Vier Dokumente dieses Projekts sagten „`kameras.py` kippt 9,46°". Diese Zahl ist
#: ``atan(0.20 / 1.2)`` und gilt bei einem Abstand von **1,2 × Gebäudehöhe** — einem
#: Abstand, den :func:`kamerasatz` nie einnimmt (``DECKUNGSGRAD`` stellt die
#: Kamera auf 2,5–5,5 × Gebäudehöhe).
#:
#: Meine Richtigstellung vom 23.08. lautete **1,92°–4,70°** und war ebenfalls zu eng.
#: Gemessen hatte ich über vier Gebäudehöhen und **zwei** Formate — quer und quadratisch.
#: Die HomeStation fuhr am selben Tag ein Hochformat (``auf-33``) und mass **5,985°**.
#: Über flache Bauten, hohe Türme und drei Formate hinweg liegt die Spanne bei
#: **−0,51° bis +5,98°**; negativ, weil ``ZIEL_HOECHSTANTEIL`` das Blickziel bei
#: niedrigen Bauten unter die Augenhöhe holt und die Kamera dann leicht nach unten sieht.
#:
#: Die Lehre ist nicht die Zahl, sondern der Weg dorthin: **Eine Spanne, die aus einer
#: Stichprobe stammt, ist eine Aussage über die Stichprobe.** Ich hatte die negativen
#: Werte am 3-m-Bau sogar gesehen und sie nicht in die genannte Spanne aufgenommen.
MODUS_GEKIPPT = "gekippt"

#: Die Kamera bleibt waagrecht, das Objektiv wird verschoben. Der normgerechte Weg.
#:
#: **Seit dem 23.08.2026 die Vorgabe** (Owner-Entscheid, unter der Bedingung, dass
#: ``auf-33`` das Verhalten am Gerät bestätigt — was es getan hat).
#:
#: **Was er kostet und was er bringt, ist gemessen und nicht behauptet:** Er bringt
#: senkrechte Senkrechte — und er bringt der Bildqualität nach heutigem Stand *nichts*
#: (``auf-20260822-29``). Wer ihn wählt, wählt die Norm, nicht eine bessere Zahl.
#:
#: **Am Gerät nachgewiesen** (``auf-33``, 23.08.2026), in fünf Fällen:
#:
#: * **Die Senkrechten werden senkrecht.** Gekippt weichen die senkrechten
#:   Gebäudekanten um **0,47°–0,98°** von der Bildsenkrechten ab, geshiftet um
#:   **0,004°–0,016°** — und das ist der Rauschboden der Messung.
#: * **Der Umbau war additiv, bis auf das letzte Bit.** Der Stand vor dem Umbau, der
#:   danach und HEAD mit ``--brennweite=28`` liefern bildpunktgleiche Tiefen-, Beauty-
#:   und Material-ID-Ausgaben. Was sich änderte, war die Brennweite, nicht der Umbau.
#: * **Die Rahmung bleibt.** Der Flächenanteil ändert sich um 0,02 %, 2,45 % und 5,05 %
#:   relativ — und in allen drei Fällen rahmt der Shift *grosszügiger*, nicht enger.
#: * **Blender bildet mit genau der Kamera ab, die wir meinen:** Eine unabhängige
#:   Lochkamera-Rechnung trifft die gekippten Kantenwinkel auf 0,004°.
MODUS_SHIFT = "shift"

#: Beide, in der Reihenfolge ihrer Vorgabe.
MODI = (MODUS_GEKIPPT, MODUS_SHIFT)

#: Grösster Shift eines wirklichen Kleinbild-Shift-Objektivs, in Millimetern.
#:
#: **Belegt** (`docs/recherche/KOMPOSITION_AUSSEN.md`, §2): 11 mm ist der übliche
#: Höchstwert von PC/TS-E-Objektiven, neuere Modelle erreichen 12 mm. Die Grenze ist
#: physikalisch — jenseits davon reicht der **Bildkreis** des Objektivs nicht mehr.
#:
#: Unsere Kamera ist gerechnet und kennt diese Grenze nicht; sie könnte beliebig
#: schieben. Genau darum steht die Zahl hier: Ein Bild jenseits von 12 mm ist mit einer
#: wirklichen Kamera nicht aufnehmbar, und die Behauptung „so fotografiert man
#: Architektur" hört dort auf zu gelten. Gemeldet wird das, nicht verboten — die Grenze
#: ist eine Aussage über Objektive, keine über Geometrie.
#:
#: **Für unsere Kameras ist sie bequem eingehalten:** über dieselben vier Gebäudehöhen
#: und zwölf Richtungen gemessen, verlangt der Shift-Modus **0,94–2,30 mm**, also weniger
#: als ein Fünftel des Verfügbaren. Das ist die andere Seite des weiten Abstands aus
#: :data:`MODUS_GEKIPPT`: Wer weit weg steht, muss wenig schieben. Der normgerechte Modus
#: ist damit nicht eine Annäherung an das Machbare, sondern deutlich innerhalb davon.
MAX_SHIFT_MM = 12.0

#: Ab welchem Anteil der ungeschobenen Rahmengrenze eine Rahmenhälfte als entartet gilt.
#:
#: Siehe die Begründung in :func:`ecken_im_bild`: Der Fall „Achse genau auf der
#: Rahmenkante" ist bei 12 mm Shift im Querformat exakt erreicht, und ein Gleitkomma-ULP
#: entscheidet sonst zwischen einer Meldung und einer Zahl mit sechzehn Stellen.
DEGENERIERT_ANTEIL = 1e-9


def shift_aus_ziel(auge, blick_auf, *, brennweite_mm: float = BRENNWEITE_MM) -> dict:
    """Wieviel Shift ersetzt genau diese Kippung?

    **Der Kern in einem Satz:** ``shift_mm = brennweite_mm · tan(Neigungswinkel)``. Der
    Shift in Tangenseinheiten ist nichts anderes als der Winkel, um den sonst gekippt
    würde — ``s = Δh / d``, Höhenunterschied durch waagrechten Abstand.

    Daraus folgt die Eigenschaft, die alles Weitere trägt: Ein Shift verschiebt den
    **Rahmen**, er dreht ihn nicht. Der Rahmen ist danach **nicht mehr symmetrisch zur
    Achse** — oben bleibt mehr Platz, unten weniger. Das ist der Grund, warum ein
    stärkerer Shift den Gebäudefuss aus dem Bild drängt und die Kamera weiter
    zurückzwingt (Recherche §4.3: der zweite Term, den man übersieht).

    Args:
        auge: Standort der Kamera.
        blick_auf: Das Ziel, das der **gekippte** Modus anvisieren würde.
        brennweite_mm: Kleinbild-Brennweite.

    Returns:
        ``{shift_mm, shift_tangens, neigung_grad, waagrechtes_ziel, abstand_m,
        ueber_grenze, grenze_mm, warnungen}``.

        ``waagrechtes_ziel`` ist das Ziel, das die Kamera im Shift-Modus tatsächlich
        anschaut: dieselbe Richtung in der Grundrissebene, aber auf Augenhöhe. Damit ist
        die Achse waagrecht, und senkrechte Kanten bleiben senkrecht.

        ``shift_mm`` ist ``0.0``, wenn das Ziel schon auf Augenhöhe liegt — dann ist
        nichts zu ersetzen, und der Shift-Modus liefert dasselbe Bild wie der gekippte.
    """
    ax, ay, az = float(auge[0]), float(auge[1]), float(auge[2])
    zx, zy, zz = float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2])
    abstand = math.hypot(zx - ax, zy - ay)
    waagrecht = (zx, zy, az)

    if abstand <= 1e-9:
        # Ein Ziel senkrecht über oder unter der Kamera. Kein Shift der Welt bildet das
        # mit waagrechter Achse ab — gemeldet, nicht durch eine Zahl überspielt.
        return {"shift_mm": 0.0, "shift_tangens": 0.0, "neigung_grad": 0.0,
                "waagrechtes_ziel": waagrecht, "abstand_m": 0.0,
                "ueber_grenze": False, "grenze_mm": float(MAX_SHIFT_MM),
                "warnungen": (
                    "Das Blickziel liegt senkrecht über oder unter der Kamera "
                    "(waagrechter Abstand 0). Mit waagrechter Achse ist es nicht "
                    "abzubilden; der Shift-Modus kann hier nichts leisten.",)}

    tangens = (zz - az) / abstand
    shift_mm = float(brennweite_mm) * tangens
    ueber = abs(shift_mm) > MAX_SHIFT_MM

    warnungen = []
    if ueber:
        warnungen.append(
            f"Der nötige Shift beträgt {shift_mm:.1f} mm und übersteigt damit die "
            f"{MAX_SHIFT_MM:.0f} mm, die ein wirkliches Kleinbild-Shift-Objektiv leistet "
            f"(Bildkreis). Gerechnet wird er trotzdem — unsere Kamera hat keinen "
            f"Bildkreis. Aber dieses Bild ist mit einer wirklichen Kamera nicht "
            f"aufnehmbar, und es ist damit kein Beleg dafür, wie Architektur fotografiert "
            f"wird. Wer es echt haben will: weiter weg oder längere Brennweite."
        )

    return {
        "shift_mm": shift_mm,
        "shift_tangens": tangens,
        "neigung_grad": math.degrees(math.atan(tangens)),
        "waagrechtes_ziel": waagrecht,
        "abstand_m": abstand,
        "ueber_grenze": ueber,
        "grenze_mm": float(MAX_SHIFT_MM),
        "warnungen": tuple(warnungen),
    }


def blender_shift_y(shift_mm: float,
                    sensor_breite_mm: float = SENSOR_BREITE_MM) -> float:
    """Millimeter auf dem Sensor → Blenders ``shift_y``.

    Blender gibt den Shift als **Anteil der Sensorkante an, die ``sensor_fit``
    bestimmt** — nicht in Millimetern und, anders als hier zuerst stand, auch nicht
    pauschal als Anteil der grösseren *Bild*kante. Bei uns ist die Bezugskante immer
    ``SENSOR_BREITE_MM``, denn :func:`bildwinkel` setzt die Sensorbreite fest auf 36 mm
    und leitet die Höhe aus dem Seitenverhältnis ab.

    **Am Gerät geprüft** (``auf-33``, 23.08.2026), und die Prüfung war nötig: Ein Shift
    von 0,34 verschob das Bild um **174,088 Bildpunkte** gegen 174,080 vorhergesagte —
    exakt linear. Im Hochformat ergaben sich **36,595 Bildpunkte** gegen 36,616
    vorhergesagte; die Alternative „Anteil der grösseren Bildkante" hätte 54,924
    verlangt und ist damit **widerlegt**.

    ``shift_mm / 36`` ist also richtig — **aber nur, weil der Runner ``sensor_fit``
    ausdrücklich stellt.** Mit Blenders Vorgabe ``AUTO`` wäre die Sensorbreite im
    Hochformat 24 statt 36 mm und der waagrechte Bildwinkel 37,8° statt 54,4°. Die
    Vorsichtsmassnahme war also nicht überflüssig, sondern tragend.
    """
    return float(shift_mm) / float(sensor_breite_mm)

#: Ab welchem Anteil des angeforderten Deckungsgrads eine Kamera als „zu weit weg"
#: gemeldet wird.
#:
#: Der Grund ist am echten Lauf aufgefallen (18.08.2026): Bei einem 2-m-Körper setzt
#: nicht der Bildwinkel den Abstand, sondern die Untergrenze aus Wandabstand — die Kamera
#: steht 11 m von einem 2-m-Objekt, und das Bauwerk füllt gut 2 % der Bildfläche. Das ist
#: kein Fehler: ``WANDABSTAND_M`` und ``AUGENHOEHE_M`` sind Gebäudemasse, und für ein
#: Gebäude stimmt die Rechnung. Aber der Torwächter lässt Bauwerke ab 1 m durch, und über
#: diesen unteren Teil der Spanne liefert das Verfahren eine schlechte Komposition.
#:
#: **Gemeldet statt stillschweigend geliefert.** Ein Bild, auf dem das Bauwerk ein Fleck
#: ist, sieht wie ein Fehler des Bildmodells aus — die Ursache liegt aber in der Kamera,
#: und niemand würde dort suchen. 0.6 ist eine Setzung: deutlich unter dem Angeforderten,
#: aber nicht schon bei jeder Abweichung.
FUELLGRAD_WARNSCHWELLE = 0.6

#: Höchstzahl der Rückschub-Durchläufe. Danach wird die letzte Position geliefert und
#: als unvollkommen gekennzeichnet. Verweigern wäre schlechter: eine Kamera, die knapp
#: schneidet, ist brauchbarer als keine.
MAX_DURCHLAEUFE = 20

#: Punkte näher als das gelten als hinter der Kamera. Nicht 0, weil die perspektivische
#: Division dort gegen unendlich läuft.
MIN_TIEFE_M = 0.5

#: Anteil der Reststrecke je Schritt beim Heranziehen vor einer Verdeckung.
ZIEH_SCHRITT = 0.12

#: Untergrenze beim Heranziehen. Näher als 6 m an das Blickziel ergibt kein Gebäudebild
#: mehr, sondern einen Fassadenausschnitt.
MIN_ZIEH_ABSTAND_M = 6.0

#: Sicherheitsabstand um die Hüllbox beim Heranziehen. Die Kamera darf nie hinein.
HUELLBOX_PUFFER_M = 3.0

#: Höchstzahl der Zieh-Schritte.
MAX_ZIEH_SCHRITTE = 8


# --------------------------------------------------------------------------------------
# Vektorrechnung, klein gehalten
# --------------------------------------------------------------------------------------

def _minus(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _plus(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mal(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _punkt(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _kreuz(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _laenge(a):
    return math.sqrt(_punkt(a, a))


def _normiert(a):
    """Einheitsvektor, oder ``None`` bei Nulllänge.

    ``None`` statt einer Ausnahme, weil der einzige Weg hierher ein entarteter Fall ist
    (Kamera exakt im Blickziel), den die Aufrufer als Befund melden sollen — nicht als
    Absturz.
    """
    laenge = _laenge(a)
    if laenge <= 0.0 or not math.isfinite(laenge):
        return None
    return (a[0] / laenge, a[1] / laenge, a[2] / laenge)


# --------------------------------------------------------------------------------------
# Bildwinkel
# --------------------------------------------------------------------------------------

def bildwinkel(brennweite_mm: float = BRENNWEITE_MM, *,
               seitenverhaeltnis: float = 16 / 9,
               sensor_breite_mm: float = SENSOR_BREITE_MM) -> tuple[float, float]:
    """Brennweite → ``(horizontal, vertikal)`` als Öffnungswinkel im Bogenmass.

    Der vertikale Winkel wird aus dem **Seitenverhältnis** abgeleitet, nicht aus einer
    festen Sensorhöhe. Das ist der Punkt, an dem die Bildproportion überhaupt in die
    Rechnung eingeht: Ein 16:9-Bild braucht bei gleichem Gebäude einen anderen Abstand
    als ein 4:3-Bild. Die Hauptfundstelle des Bestands rechnet mit fest verdrahteten
    27 mm Sensorhöhe und übersieht das; ihr Vorläufer macht es richtig. Hier gewinnt
    der Vorläufer.

    Raises:
        ValueError: Brennweite, Seitenverhältnis oder Sensorbreite nicht positiv-endlich.
            Ein Bildwinkel aus einer Brennweite von 0 wäre 180° — eine Zahl, die
            entsteht, aber nichts bedeutet.
    """
    for name, wert in (("brennweite_mm", brennweite_mm),
                       ("seitenverhaeltnis", seitenverhaeltnis),
                       ("sensor_breite_mm", sensor_breite_mm)):
        if not isinstance(wert, (int, float)) or isinstance(wert, bool):
            raise ValueError(f"{name} muss eine Zahl sein, war: {wert!r}")
        if not math.isfinite(float(wert)) or float(wert) <= 0.0:
            raise ValueError(f"{name} muss positiv und endlich sein, war: {wert!r}")

    sensor_hoehe_mm = sensor_breite_mm / seitenverhaeltnis
    hfov = 2.0 * math.atan(sensor_breite_mm / (2.0 * brennweite_mm))
    vfov = 2.0 * math.atan(sensor_hoehe_mm / (2.0 * brennweite_mm))
    return hfov, vfov


# --------------------------------------------------------------------------------------
# Richtungen
# --------------------------------------------------------------------------------------

#: Die zwölf Richtungen: Kürzel → (Grundazimut in Grad, Vielfaches von ``bias_grad``).
#:
#: Der Azimut zählt im Uhrzeigersinn ab Nord und beschreibt, **wo die Kamera steht** —
#: ``n`` heisst: nördlich des Gebäudes, mit Blick nach Süden.
#:
#: Vier frontal, senkrecht auf eine Fassade. Acht diagonal: Primärrichtung, dann um
#: ``bias_grad`` in einen Quadranten gedreht. ``nNE`` liest sich als „von Norden, nach
#: Nordost gedreht" — die Nordfassade führt, die Ostfassade begleitet.
#:
#: **Diese Vorzeichen sind die Stelle, an der sich der Bestand nachweislich vertan hat**
#: (die N/S-Diagonalen waren invertiert und tragen dort einen Korrekturkommentar). Darum
#: stehen sie hier als Tabelle statt als Rechnung, und darum prüft der Test jede der acht
#: Diagonalen bei ``bias_grad=45`` gegen ihre Himmelsrichtung.
RICHTUNGEN = {
    "n":   (0.0, 0),
    "e":   (90.0, 0),
    "s":   (180.0, 0),
    "w":   (270.0, 0),
    "nNE": (0.0, +1),
    "nNW": (0.0, -1),
    "eEN": (90.0, -1),
    "eES": (90.0, +1),
    "sSE": (180.0, -1),
    "sSW": (180.0, +1),
    "wWS": (270.0, -1),
    "wWN": (270.0, +1),
}

#: Die zwölf Kürzel in der Reihenfolge, in der sie ausgegeben werden: erst die vier
#: Frontalen, dann die acht Diagonalen im Uhrzeigersinn ab Nord.
RICHTUNGSFOLGE = ("n", "e", "s", "w",
                  "nNE", "eEN", "eES", "sSE", "sSW", "wWS", "wWN", "nNW")


def richtungen(bias_grad: float = BIAS_GRAD) -> dict:
    """Die zwölf Kürzel → Azimut in Grad.

    ``bias_grad`` regelt das Verhältnis der beiden sichtbaren Fassaden bei den
    Diagonalen — das ist architektonisches Bildwissen, keine Programmierung:

    * **30°** — die primäre Fassade dominiert, etwa 2/3 zu 1/3.
    * **35°** — ausgewogen, etwa 60/40. Vorgabe.
    * **45°** — echter Eckblick, 50/50. Bei genau 45° fallen je zwei Diagonalen auf
      dieselbe Himmelsrichtung; aus zwölf Richtungen werden acht verschiedene Blicke.
      Das ist kein Fehler, sondern die Aussage des Reglers.

    Raises:
        ValueError: ``bias_grad`` liegt nicht in ``(0, 90)``. Bei 0 fällt die Diagonale
            mit der Frontalen zusammen, bei 90 mit der nächsten Frontalen — in beiden
            Fällen entstünden Doppelbilder statt Eckblicken.
    """
    if isinstance(bias_grad, bool) or not isinstance(bias_grad, (int, float)):
        raise ValueError(f"bias_grad muss eine Zahl sein, war: {bias_grad!r}")
    bias = float(bias_grad)
    if not math.isfinite(bias) or not (0.0 < bias < 90.0):
        raise ValueError(
            f"bias_grad muss zwischen 0 und 90 Grad liegen (ausschliesslich), war: {bias}. "
            "Bei 0 fiele die Diagonale auf die Frontale, bei 90 auf die nächste Frontale."
        )
    return {kuerzel: (grund + faktor * bias) % 360.0
            for kuerzel, (grund, faktor) in RICHTUNGEN.items()}


def _achsen_aus_azimut(azimut_grad: float) -> tuple[tuple, tuple]:
    """Azimut → ``(standort_richtung, blick_richtung)`` in der XY-Ebene.

    Nord ist ``+Y``, Ost ``+X``, gezählt im Uhrzeigersinn — die Konvention des Kompasses,
    nicht die des Einheitskreises. Wer hier ``cos``/``sin`` vertauscht, dreht die ganze
    Anlage um 90°, und zwar unauffällig.
    """
    a = math.radians(azimut_grad)
    standort = (math.sin(a), math.cos(a), 0.0)
    return standort, (-standort[0], -standort[1], 0.0)


def sichtbare_breite(masse, azimut_grad: float) -> float:
    """Wie breit das Gebäude aus dieser Richtung erscheint, in Metern.

    Die Hüllbox ist achsparallel; aus schräger Sicht wird ihre Silhouette breiter als
    jede einzelne Seite. Die Breite quer zur Blickrichtung ist ``|dx·sin a| + |dy·cos a|``
    — für die Frontale genau ``dx`` bzw. ``dy``, für die 45°-Ecke eines quadratischen
    Grundrisses genau die Diagonale.

    **Das ist eine Verbesserung gegenüber dem Bestand, keine Übernahme.** Dort steht
    ``max(breite, tiefe, grundriss_diagonale)`` — und weil die Diagonale eines Rechtecks
    *immer* mindestens so gross ist wie jede seiner Seiten, gewinnt sie ausnahmslos. Das
    ``max`` ist toter Code, und die Folge ist eine Kamera, die auch bei der Frontalen auf
    Diagonalabstand steht. Bei einem 60 × 12 m langen Riegel sind das 61 m statt 60 m —
    harmlos. Bei einem 30 × 30 m Kubus 42 m statt 30 m: das Gebäude füllt nur noch gut
    zwei Drittel des vorgesehenen Anteils. Richtungsabhängig gerechnet verschwindet der
    Fehler ganz.
    """
    dx, dy, _ = masse
    a = math.radians(azimut_grad)
    return abs(dx * math.cos(a)) + abs(dy * math.sin(a))


def sichtbare_tiefe(masse, azimut_grad: float) -> float:
    """Wie tief das Gebäude in Blickrichtung ausgedehnt ist, in Metern.

    Die Gegenrechnung zu ``sichtbare_breite``: ``|dx·cos a| + |dy·sin a|``. Gebraucht,
    weil der Abstand zur Gebäude**mitte** gerechnet wird, die vordere Fassade aber um die
    halbe Tiefe näher steht.
    """
    dx, dy, _ = masse
    a = math.radians(azimut_grad)
    return abs(dx * math.sin(a)) + abs(dy * math.cos(a))


# --------------------------------------------------------------------------------------
# Der analytische Abstand
# --------------------------------------------------------------------------------------

def abstand_aus_bildwinkel(masse, azimut_grad: float, *,
                           hoehe_ueber_grund: float,
                           brennweite_mm: float = BRENNWEITE_MM,
                           seitenverhaeltnis: float = 16 / 9,
                           deckungsgrad: float = DECKUNGSGRAD) -> dict:
    """Wie weit die Kamera stehen muss, damit das Gebäude den vorgesehenen Anteil füllt.

    Zwei Kandidaten, der grössere gewinnt: einer, damit die Breite passt, einer für die
    Höhe. Der vertikale Bedarf wird **von der Zielhöhe aus asymmetrisch** gemessen — nach
    oben bis zur Traufe, nach unten bis zum Fuss, der grössere zählt. Eine halbe
    Gebäudehöhe anzusetzen wäre falsch, weil das Blickziel bei einem hohen Bau eben
    **nicht** in der Mitte der Fassade sitzt; bei einem zwanziggeschossigen Haus liegt es
    im ersten Fünftel.

    Args:
        masse: Kantenlängen ``(dx, dy, dz)`` in Metern.
        azimut_grad: Wo die Kamera steht, im Uhrzeigersinn ab Nord.
        hoehe_ueber_grund: Höhe des Blickziels über der Gebäudeunterkante, in Metern.

    Returns:
        dict mit ``abstand_m`` und den Zwischenwerten, die dazu geführt haben
        (``breite_m``, ``tiefe_m``, ``abstand_breite_m``, ``abstand_hoehe_m``,
        ``untergrenze_m``, ``massgebend``). Wer einen Abstand für falsch hält, soll
        nachsehen können, welcher der drei Kandidaten ihn gesetzt hat.

    Raises:
        ValueError: ``deckungsgrad`` liegt nicht in ``(0, 1]``, oder eines der Masse ist
            negativ bzw. nicht endlich.
    """
    if isinstance(deckungsgrad, bool) or not isinstance(deckungsgrad, (int, float)):
        raise ValueError(f"deckungsgrad muss eine Zahl sein, war: {deckungsgrad!r}")
    deckung = float(deckungsgrad)
    if not math.isfinite(deckung) or not (0.0 < deckung <= 1.0):
        raise ValueError(
            f"deckungsgrad muss in (0, 1] liegen, war: {deckung}. Über 1 hiesse, das "
            "Gebäude solle grösser als das Bild sein — dann ist jeder Abstand zu klein."
        )
    masse = tuple(float(m) for m in masse)
    if len(masse) != 3 or any(not math.isfinite(m) or m < 0.0 for m in masse):
        raise ValueError(f"masse muss drei nichtnegative endliche Zahlen sein, war: {masse!r}")

    hfov, vfov = bildwinkel(brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
    breite = sichtbare_breite(masse, azimut_grad)
    tiefe = sichtbare_tiefe(masse, azimut_grad)

    # Asymmetrisch von der Zielhöhe aus, siehe Docstring.
    nach_oben = max(0.0, masse[2] - hoehe_ueber_grund)
    nach_unten = max(0.0, hoehe_ueber_grund)
    halbe_hoehe = max(nach_oben, nach_unten)

    d_breite = (breite / 2.0) / math.tan(hfov / 2.0) / deckung
    d_hoehe = halbe_hoehe / math.tan(vfov / 2.0) / deckung

    # Die halbe Tiefe kommt dazu, weil bis hier zur Gebäudemitte gerechnet wurde.
    untergrenze = tiefe / 2.0 + WANDABSTAND_M
    kandidaten = {"breite": d_breite + tiefe / 2.0,
                  "hoehe": d_hoehe + tiefe / 2.0,
                  "untergrenze": untergrenze}
    massgebend = max(kandidaten, key=kandidaten.__getitem__)

    return {
        "abstand_m": kandidaten[massgebend],
        "massgebend": massgebend,
        "breite_m": breite,
        "tiefe_m": tiefe,
        "halbe_hoehe_m": halbe_hoehe,
        "abstand_breite_m": kandidaten["breite"],
        "abstand_hoehe_m": kandidaten["hoehe"],
        "untergrenze_m": untergrenze,
        "hfov_grad": math.degrees(hfov),
        "vfov_grad": math.degrees(vfov),
    }


# --------------------------------------------------------------------------------------
# Der Eckentest — passt das Gebäude wirklich ins Bild?
# --------------------------------------------------------------------------------------

def _kamerabasis(auge, blick_auf):
    """``(vorwaerts, rechts, oben)`` aus Standort und Blickziel, oder ``None``.

    ``None`` in zwei Fällen: Kamera steht im Blickziel, oder sie schaut exakt senkrecht.
    Senkrecht ist entartet, weil Welt-Z dann keine Referenz für „oben" mehr hergibt — die
    Bildrotation wäre frei wählbar. Das kommt bei Augenhöhen-Perspektiven nicht vor, aber
    eine Draufsicht ist ein legitimer Wunsch, und dann soll die Antwort ein Befund sein
    und kein stiller Unsinn.
    """
    vorwaerts = _normiert(_minus(blick_auf, auge))
    if vorwaerts is None:
        return None
    rechts = _normiert(_kreuz(vorwaerts, (0.0, 0.0, 1.0)))
    if rechts is None:
        return None
    oben = _kreuz(rechts, vorwaerts)
    return vorwaerts, rechts, oben


def _huellen_flaeche(punkte) -> float:
    """Fläche der konvexen Hülle einer Punktmenge in der Ebene.

    Andrews Monotone Chain plus Schnürsenkelformel — beides Lehrbuch, beides in dreissig
    Zeilen. Für acht Punkte ist jede Bibliothek dafür zu schwer, und eine Abhängigkeit ist
    in diesem Projekt eine Lizenzentscheidung (Regel 1).
    """
    p = sorted(set(punkte))
    if len(p) < 3:
        return 0.0

    def halb(pp):
        stapel = []
        for q in pp:
            while len(stapel) >= 2:
                (ax, ay), (bx, by) = stapel[-2], stapel[-1]
                if (bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax) > 0:
                    break
                stapel.pop()
            stapel.append(q)
        return stapel[:-1]

    huelle = halb(p) + halb(list(reversed(p)))
    flaeche = 0.0
    for i in range(len(huelle)):
        x1, y1 = huelle[i]
        x2, y2 = huelle[(i + 1) % len(huelle)]
        flaeche += x1 * y2 - x2 * y1
    return abs(flaeche) / 2.0


def flaechenanteil(auge, blick_auf, bbox, *,
                   brennweite_mm: float = BRENNWEITE_MM,
                   seitenverhaeltnis: float = 16 / 9,
                   shift_mm: float = 0.0) -> float:
    """Welchen Anteil der BILDFLÄCHE die Hüllbox einnimmt.

    Warum diese Zahl neben ``fuellgrad`` stehen muss
    ------------------------------------------------
    ``fuellgrad`` misst die führende Länge — Breite oder Höhe, je nachdem welche den
    Abstand gesetzt hat. Das ist richtig für die Frage „wurde der Deckungsgrad
    eingehalten", und es ist **blind für das, was ein Mensch sieht.**

    Am 19.08.2026 an zwölf echten Blender-Läufen gemessen (40 × 26 × 15 m, quadratischer
    Rahmen): Der gemeldete Füllgrad lag bei **allen zwölf** zwischen 0.548 und 0.550 —
    praktisch konstant. Die tatsächlich eingenommene Bildfläche schwankte von **3.3 % bis
    9.6 %**, also um den Faktor drei. Die Zahl war richtig und sagte nichts.

    Der Grund ist keine Fehlfunktion, sondern Geometrie: Ein breiter, niedriger Bau kann
    einen quadratischen Rahmen gar nicht füllen. Erfüllt er die Breite, ist die Höhe
    zwangsläufig leer. Das ist eine Frage des **Formats** oder des **Vordergrunds**, nicht
    des Abstands — und darum gehört die Zahl gemeldet und nicht wegoptimiert.

    Gerechnet als konvexe Hülle der acht projizierten Hüllbox-Ecken. Das ist für einen
    Quader exakt und für ein Gebäude eine **Obergrenze**: Die Hüllbox ist voller als der
    Bau. Die gemessenen 3.3–9.6 % liegen entsprechend darunter.

    Returns:
        Anteil in ``[0, 1]``. ``0.0``, wenn die Kamerabasis entartet ist oder Ecken hinter
        der Kamera liegen — dort ist die Projektion keine Fläche mehr.
    """
    gelesen = _lies_bbox(bbox)
    basis = _kamerabasis(auge, blick_auf)
    if gelesen is None or basis is None:
        return 0.0
    vorwaerts, rechts, oben = basis
    hfov, vfov = bildwinkel(brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
    grenze_h = math.tan(hfov / 2.0)
    grenze_v = math.tan(vfov / 2.0)
    # Der Shift verschiebt den Rahmen gegen die Achse — in Tangenseinheiten ist er
    # ``shift_mm / brennweite``. Bei 0 fällt der Term weg und die Rechnung ist die alte.
    versatz = float(shift_mm) / float(brennweite_mm)

    unten, obenecke = gelesen
    flach = []
    for x in (unten[0], obenecke[0]):
        for y in (unten[1], obenecke[1]):
            for z in (unten[2], obenecke[2]):
                v = _minus((x, y, z), auge)
                tiefe = _punkt(v, vorwaerts)
                if tiefe < MIN_TIEFE_M:
                    return 0.0
                # Auf den Bildrahmen normiert: -0.5 .. +0.5 ist der sichtbare Bereich.
                flach.append((_punkt(v, rechts) / tiefe / grenze_h / 2.0,
                              (_punkt(v, oben) / tiefe - versatz) / grenze_v / 2.0))
    return min(1.0, _huellen_flaeche(flach))


def ecken_im_bild(auge, blick_auf, bbox, *,
                  brennweite_mm: float = BRENNWEITE_MM,
                  seitenverhaeltnis: float = 16 / 9,
                  bildrand: float = BILDRAND,
                  shift_mm: float = 0.0) -> dict:
    """Liegen alle acht Hüllbox-Ecken im Bild?

    Geprüft werden **alle acht Ecken einzeln**, nicht die Box als Ganzes. Für jede Ecke
    wird die Tiefe entlang der Blickachse gebildet, die seitlichen Anteile werden durch
    diese Tiefe geteilt — das ist die perspektivische Division — und gegen die
    Tangenswerte des Bildwinkels verglichen.

    Der Eckentest ist der Grund, warum die analytische Rechnung allein nicht genügt: Sie
    arbeitet mit einer Ersatzausdehnung und einem Ziel in der Mitte; der Eckentest prüft
    die Wirklichkeit einschliesslich der Kippung.

    ``shift_mm`` verschiebt den Rahmen gegen die Blickachse (Shift-Objektiv). Der Rahmen
    ist dann **nicht mehr symmetrisch**: nach oben ``grenze_v + s``, nach unten
    ``grenze_v - s``. Die Umstellung nach dem Rückschub bleibt geschlossen lösbar, weil
    ``s`` nicht von der Tiefe abhängt — nur wird jede Ecke jetzt gegen *ihre* Grenze
    gerechnet statt gegen eine gemeinsame. Bei ``shift_mm=0`` ist es Zeile für Zeile die
    frühere Rechnung.

    Mitgeliefert wird ``noetiger_rueckschub_m``: **wie weit** die Kamera entlang ihrer
    Blickachse zurück muss, damit alle acht Ecken hineinpassen. Diese Zahl ist nicht
    geschätzt, sondern umgestellt. Ein Rückschub um Δ entlang der Blickachse erhöht die
    Tiefe jeder Ecke um genau Δ und lässt ihre seitlichen Anteile unberührt; aus
    ``seitlich / (tiefe + Δ) ≤ grenze`` folgt unmittelbar ``Δ ≥ seitlich / grenze −
    tiefe``. Das Maximum über die acht Ecken ist die Antwort — in einem Schritt, ohne
    Tasten.

    Returns:
        dict mit ``passt`` (bool), ``max_ueberstehen`` (1.0 = genau auf der Kante,
        1.2 = 20 % zu gross fürs Bild), ``noetiger_rueckschub_m``,
        ``ecken_hinter_kamera`` und ``begruendung``. Bei entarteter Basis ``passt=False``
        mit der Begründung — nie eine Ausnahme.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": None, "ecken_hinter_kamera": 0,
                "begruendung": f"bbox unbrauchbar: {bbox!r}"}

    basis = _kamerabasis(auge, blick_auf)
    if basis is None:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": None, "ecken_hinter_kamera": 0,
                "begruendung": "Kamerabasis entartet — Kamera im Blickziel oder exakt senkrecht."}
    vorwaerts, rechts, oben = basis

    hfov, vfov = bildwinkel(brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
    grenze_h = math.tan(hfov / 2.0) * bildrand
    grenze_v = math.tan(vfov / 2.0) * bildrand

    # **Hier steckt die ganze Wirkung des Shifts.** Er verschiebt den Rahmen gegen die
    # Achse, und damit ist der Rahmen nicht mehr symmetrisch: Nach oben reicht er
    # ``grenze_v + versatz``, nach unten nur noch ``grenze_v - versatz``. Genau das ist
    # der Grund, warum ein stärkerer Shift den Gebäudefuss aus dem Bild drängt und die
    # Kamera weiter zurückzwingt (Recherche §4.3 — der Term, den man übersieht).
    versatz = float(shift_mm) / float(brennweite_mm)
    grenze_oben = grenze_v + versatz
    grenze_unten = grenze_v - versatz
    # **Relativ verglichen, nicht gegen die harte Null.** Der Grenzfall ist erreichbar
    # und keineswegs exotisch: Bei 24 mm Sensorhöhe (Kleinbild quer) verlässt die Achse
    # den Rahmen bei genau 12 mm Shift — dem Höchstwert wirklicher Objektive (Recherche
    # §4.4). Dort ist ``grenze_v`` rechnerisch exakt gleich ``versatz``, im Gleitkomma
    # aber um ein ULP daneben. Auf der falschen Seite dieses ULP liefert die Umstellung
    # keinen Fehler, sondern einen Rückschub von 1,5·10^16 Metern — eine Zahl, die
    # entsteht und nichts bedeutet. Der Vergleich ist darum relativ.
    if min(grenze_oben, grenze_unten) <= grenze_v * DEGENERIERT_ANTEIL:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": None, "ecken_hinter_kamera": 0,
                "begruendung": (
                    f"Der Shift von {shift_mm:.1f} mm ist bei {brennweite_mm:.0f} mm "
                    f"Brennweite grösser als der halbe Bildwinkel: Die Blickachse liegt "
                    f"dann ausserhalb des Rahmens. Rechnerisch möglich, fotografisch "
                    f"sinnlos — und keine Rückschubweite bringt das in Ordnung.")}

    unten, obenecke = gelesen
    ecken = [(x, y, z)
             for x in (unten[0], obenecke[0])
             for y in (unten[1], obenecke[1])
             for z in (unten[2], obenecke[2])]

    hinter = 0
    max_ueberstehen = 0.0
    noetig = 0.0
    for ecke in ecken:
        v = _minus(ecke, auge)
        tiefe = _punkt(v, vorwaerts)
        hoch = _punkt(v, oben)
        # Die Tiefe, die diese Ecke MINDESTENS braucht, um in den Rahmen zu passen.
        # Waagrecht symmetrisch, senkrecht getrennt nach oben und unten — bei
        # ``shift_mm=0`` sind beide Grenzen gleich und der Ausdruck fällt auf das
        # frühere ``max(|rechts|/grenze_h, |oben|/grenze_v)`` zurück.
        seitlich = max(abs(_punkt(v, rechts)) / grenze_h,
                       hoch / grenze_oben if hoch > 0.0 else 0.0,
                       -hoch / grenze_unten if hoch < 0.0 else 0.0)

        # Die Tiefe, ab der diese Ecke im Bild läge — und was daran heute fehlt.
        # MIN_TIEFE_M steht mit im Maximum, damit eine Ecke direkt auf der Blickachse
        # (seitlich = 0) nicht als „passt schon" durchgeht, während sie hinter der
        # Kamera liegt.
        noetig = max(noetig, max(seitlich, MIN_TIEFE_M) - tiefe)

        if tiefe < MIN_TIEFE_M:
            hinter += 1
            continue
        max_ueberstehen = max(max_ueberstehen, seitlich / tiefe)

    if hinter:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": noetig, "ecken_hinter_kamera": hinter,
                "begruendung": f"{hinter} von 8 Hüllbox-Ecken liegen hinter der Kamera "
                               f"(Tiefe unter {MIN_TIEFE_M} m). Die Kamera steckt im "
                               f"Gebäude; {noetig:.1f} m Rückschub bringen sie heraus."}

    passt = max_ueberstehen <= 1.0
    return {
        "passt": passt,
        "max_ueberstehen": max_ueberstehen,
        "noetiger_rueckschub_m": max(0.0, noetig),
        "ecken_hinter_kamera": 0,
        "begruendung": ("Alle acht Ecken im Bild."
                        if passt else
                        f"Grösstes Überstehen {max_ueberstehen:.3f} — das Gebäude ist um "
                        f"{(max_ueberstehen - 1.0) * 100:.1f} % zu gross für den Rahmen. "
                        f"{noetig:.1f} m Rückschub schaffen Platz."),
    }


def schiebe_bis_im_bild(auge, blick_auf, bbox, *,
                        shift_mm: float = 0.0,
                        brennweite_mm: float = BRENNWEITE_MM,
                        seitenverhaeltnis: float = 16 / 9,
                        bildrand: float = BILDRAND,
                        max_durchlaeufe: int = MAX_DURCHLAEUFE) -> dict:
    """Schiebt die Kamera zurück, bis alle acht Ecken im Bild liegen.

    Der Rückschub folgt **nur der horizontalen Blickrichtung**; die Augenhöhe bleibt
    konstant. Das ist der Grund, warum das Verfahren Augenhöhen-Perspektiven liefert und
    keine Drohnenbilder — eine Kamera, die auch nach oben ausweichen darf, landet über
    kurz oder lang im Vogelflug, weil das immer die bequemere Lösung ist.

    Der Schritt ist der **gerechnete** Rückschub aus ``ecken_im_bild``, nicht ein
    getasteter. Weil er die Blickachse betrifft, die Kamera aber waagrecht ausweichen
    soll, wird er durch den Kosinus der Neigung geteilt: Ein um 20° geneigter Blick
    gewinnt bei einem Meter waagrechtem Rückschub nur 94 cm Tiefe.

    Es bleibt eine Schleife, obwohl die Rechnung exakt ist — denn der waagrechte Schub
    ändert die Blickrichtung leicht, und mit ihr die Zerlegung in „seitlich" und „tief".
    In der Praxis sind es ein bis zwei Durchläufe statt der zwanzig, die der Bestand
    veranschlagt.

    **Der Bestand tastet stattdessen**: ``(überstehen − 1) · abstand · 0.6 + 3``. Das ist
    an beiden Enden schlecht. Der Faktor 0.6 dämpft auf 60 % des Nötigen, also braucht es
    mehr Durchläufe. Und bei einer Kamera dicht an der Fassade wird das Überstehen
    zweistellig — derselbe Ausdruck erzeugt dann einen Sprung über Kilometer, und die
    Kamera steht am Ende so weit weg, dass das Gebäude ein Fleck ist. Der Eckentest sagt
    dazu „passt", denn zu klein ist er nie aufgefallen.

    Nach ``max_durchlaeufe`` wird die letzte Position geliefert und ``vollstaendig=False``
    gesetzt. **Verweigern wäre schlechter als eine gekennzeichnet unvollkommene Antwort** —
    aber stillschweigend als gelöst gelten darf sie nicht.
    """
    aktuell = (float(auge[0]), float(auge[1]), float(auge[2]))
    ziel = (float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2]))
    augenhoehe = aktuell[2]

    for durchlauf in range(max_durchlaeufe):
        pruefung = ecken_im_bild(aktuell, ziel, bbox, shift_mm=shift_mm,
                                 brennweite_mm=brennweite_mm,
                                 seitenverhaeltnis=seitenverhaeltnis, bildrand=bildrand)
        if pruefung["passt"]:
            return {"auge": aktuell, "vollstaendig": True, "durchlaeufe": durchlauf,
                    "max_ueberstehen": pruefung["max_ueberstehen"],
                    "begruendung": pruefung["begruendung"]}

        richtung = _normiert((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))
        if richtung is None:
            return {"auge": aktuell, "vollstaendig": False, "durchlaeufe": durchlauf,
                    "max_ueberstehen": pruefung["max_ueberstehen"],
                    "begruendung": "Kamera steht senkrecht über dem Blickziel — ein "
                                   "horizontaler Rückschub hat keine Richtung."}

        # Der Rückschub gilt entlang der Blickachse; ausgewichen wird waagrecht.
        # Bei geneigtem Blick bringt ein waagrechter Meter weniger als einen Meter Tiefe.
        voll = _normiert(_minus(ziel, aktuell))
        neigung = abs(voll[2]) if voll else 0.0
        waagrecht = math.sqrt(max(1.0 - neigung * neigung, 1e-6))
        schub = max(pruefung["noetiger_rueckschub_m"] / waagrecht, 0.5)
        aktuell = (aktuell[0] - richtung[0] * schub,
                   aktuell[1] - richtung[1] * schub,
                   augenhoehe)

    letzte = ecken_im_bild(aktuell, ziel, bbox, shift_mm=shift_mm,
                           brennweite_mm=brennweite_mm,
                           seitenverhaeltnis=seitenverhaeltnis, bildrand=bildrand)
    return {
        "auge": aktuell,
        "vollstaendig": letzte["passt"],
        "durchlaeufe": max_durchlaeufe,
        "max_ueberstehen": letzte["max_ueberstehen"],
        "begruendung": (f"Nach {max_durchlaeufe} Durchläufen: {letzte['begruendung']} "
                        "Die Position wird geliefert, ist aber nicht bestätigt."),
    }


# --------------------------------------------------------------------------------------
# Heranziehen vor einer Verdeckung — Schrittlogik ohne Blender
# --------------------------------------------------------------------------------------

def ziehe_bis_frei(auge, blick_auf, bbox, _sicht_frei, *,
                   schritt: float = ZIEH_SCHRITT,
                   min_abstand: float = MIN_ZIEH_ABSTAND_M,
                   puffer: float = HUELLBOX_PUFFER_M,
                   max_schritte: int = MAX_ZIEH_SCHRITTE) -> dict:
    """Zieht die Kamera heran, solange etwas die Sicht verstellt.

    Steht ein Nachbargebäude im Weg, hilft kein Rückschub — die Antwort ist, **näher**
    heranzugehen, bis der Blick am Hindernis vorbei geht. Das ist die Gegenrichtung zu
    ``schiebe_bis_im_bild``, und die beiden ziehen damit gegeneinander: Der Eckentest
    schiebt weg, der Verdeckungstest holt heran. Im Bestand laufen sie nacheinander, nicht
    in einer gemeinsamen Schleife; ob das schwingt, ist dort nie geprüft worden. Hier ist
    die Reihenfolge dieselbe, aber der Ausgang wird protokolliert — wer eine Kamera findet,
    die zwischen zwei Läufen springt, sieht es an ``schritte`` und ``abbruch``.

    Ob die Sicht frei ist, weiss nur die Szene. Darum wird ``_sicht_frei(auge, blick_auf)``
    **hereingereicht**: im Runner ein Strahlenschuss gegen den Depsgraph, im Test eine
    Funktion mit drei Zeilen. Die Schrittlogik selbst — 12 % der Reststrecke, Untergrenze,
    Stopp am erweiterten Hüllbox-Rand, konstante Augenhöhe — ist reine Rechnung und
    gehört diesseits der Grenze. **Der Bestand macht diesen Schnitt nicht**; dort steht
    ``bpy`` im Modulkopf und die halbe Datei ist dadurch unprüfbar.

    Returns:
        dict mit ``auge``, ``frei`` (bool), ``schritte`` und ``abbruch`` — eines von
        ``sicht_frei``, ``untergrenze``, ``huellbox``, ``schritte_erschoepft``,
        ``entartet``.
    """
    aktuell = (float(auge[0]), float(auge[1]), float(auge[2]))
    ziel = (float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2]))
    augenhoehe = aktuell[2]
    gelesen = _lies_bbox(bbox)

    def _in_huellbox(p):
        if gelesen is None:
            return False
        unten, oben = gelesen
        return all(min(unten[i], oben[i]) - puffer <= p[i] <= max(unten[i], oben[i]) + puffer
                   for i in range(2))

    for n in range(max_schritte):
        if _sicht_frei(aktuell, ziel):
            return {"auge": aktuell, "frei": True, "schritte": n, "abbruch": "sicht_frei"}

        richtung = _normiert((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))
        if richtung is None:
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "entartet"}
        abstand = _laenge((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))

        naechster = (aktuell[0] + richtung[0] * abstand * schritt,
                     aktuell[1] + richtung[1] * abstand * schritt,
                     augenhoehe)
        rest = _laenge((ziel[0] - naechster[0], ziel[1] - naechster[1], 0.0))
        if rest < min_abstand:
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "untergrenze"}
        if _in_huellbox(naechster):
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "huellbox"}
        aktuell = naechster

    frei = bool(_sicht_frei(aktuell, ziel))
    return {"auge": aktuell, "frei": frei, "schritte": max_schritte,
            "abbruch": "sicht_frei" if frei else "schritte_erschoepft"}


# --------------------------------------------------------------------------------------
# Der Kamerasatz
# --------------------------------------------------------------------------------------

#: Unterhalb dieser Kantenlänge in Metern gilt eine Achse der Hüllbox als **leer**.
#:
#: Zehn Zentimeter. Ein Bauwerk, das in einer Richtung weniger misst, ist keines — und
#: die Zahl ist bewusst absolut und nicht relativ: Ein Anteil an der grössten Kante liesse
#: eine 200 m lange, 10 cm hohe Platte als „normal" durchgehen.
LEERE_KANTE_M = 0.10


def huellbox_taugt(bbox) -> dict:
    """Steht in dieser Hüllbox überhaupt ein Bauwerk? — **vor** allem anderen.

    **Der Anlass ist ein Demolauf, der nicht bei uns lag** (HomeStation, 24.08.2026): Der
    Modell-Knoten meldete den ganzen Lauf «Szene: 0 Bauteile (GLB)», weil das aktive
    Projekt den Stationswechsel nicht überlebte. Was danach kommt, ist unsere Sache: Aus
    einer leeren Szene entsteht eine Hüllbox ohne Ausdehnung, und :func:`kamerasatz`
    rechnet darauf weiter.

    **Der leere Fall warnt bereits** — «das Bauwerk füllt 0.0 % des Bildes». Der
    gefährlichere ist der andere: Eine Hüllbox **ohne Höhe** — Gelände ohne Bauwerk, oder
    ein Bauwerk, dessen Umwandlung stillschweigend nichts lieferte — ergibt einen
    Kamerasatz, der **völlig gesund aussieht**: Füllgrad 0,549, keine einzige Warnung. Die
    Kamera steht dann sauber gerahmt vor einer Platte.

    Returns:
        ``{taugt, masse_m, leere_achsen, grund}``. ``taugt`` ist ``False``, wenn eine
        Achse unter :data:`LEERE_KANTE_M` liegt.

    Raises:
        ValueError: Die Hüllbox hat nicht die Form zweier Punkte mit je drei Zahlen.
    """
    try:
        unten, oben = bbox
        masse = tuple(float(oben[i]) - float(unten[i]) for i in range(3))
    except (TypeError, ValueError, IndexError) as fehler:
        raise ValueError(
            f"bbox braucht zwei Punkte mit je drei Zahlen, war {bbox!r}.") from fehler

    leer = [name for name, wert in zip("XYZ", masse) if wert < LEERE_KANTE_M]
    if not leer:
        return {"taugt": True, "masse_m": masse, "leere_achsen": (), "grund": ""}

    if len(leer) == 3:
        grund = ("Die Hüllbox hat in KEINER Richtung Ausdehnung — die Szene ist leer. "
                 "Ein Kamerasatz darauf beschreibt einen Standpunkt um einen Punkt; jede "
                 "Zahl, die danach entsteht, ist Unsinn mit Dezimalpunkt.")
    elif leer == ["Z"]:
        grund = (f"Die Hüllbox hat keine HÖHE ({masse[2]:.3f} m) — das ist Gelände ohne "
                 f"Bauwerk, oder das Bauwerk ist bei der Umwandlung stillschweigend "
                 f"ausgefallen. Der gefährlichere der beiden Fälle: Der Kamerasatz sieht "
                 f"danach völlig gesund aus, Füllgrad und alles, und die Kamera steht "
                 f"sauber gerahmt vor einer Platte.")
    else:
        grund = (f"Die Hüllbox hat in {', '.join(leer)} keine Ausdehnung "
                 f"({', '.join(f'{w:.3f} m' for w in masse)}). Ein Bauwerk, das in einer "
                 f"Richtung nichts misst, ist keines.")
    return {"taugt": False, "masse_m": masse, "leere_achsen": tuple(leer),
            "grund": grund}


#: Bildbreite, ab der das Geometrie-Tor **gemessen** bestehen kann.
#:
#: Abgelesen am Knie der Rampe (HomeStation, 24.08.2026): Der Score steigt ab rund 0,50,
#: überschreitet die Schwelle zwischen **0,5991 und 0,6488** und liegt linear bei 0,61.
#: Die Bestellempfehlung ist **0,70**, nicht 0,65 — dort besteht jeder von drei Startwerten
#: mit Abstand 0,301, bei 0,65 steht einer bei 0,114.
#:
#: Hier steht die **untere** Kante des Knies: Alles darunter ist gemessen zu wenig.
#: Zwischen ihr und 0,70 liegt der Bereich, in dem es auf den Startwert ankommt.
BILDBREITE_KNIE = 0.5991

#: Bildbreite, **unter der nicht mehr gerendert wird**.
#:
#: **Der Anlass ist ein Owner-Einwand** (`auf-vis-20260825-15`, Posten 1, 25.08.2026),
#: nachdem die Kette zum ersten Mal ganz durchgelaufen war:
#:
#:   *«Das sollte natuerlich gar nicht so weit kommen — die Modelle muessen pruefen, ob
#:   die Geometrie richtig ist und richtig darstellt, BEVOR AI Imaging startet.»*
#:
#: Bis dahin prüfte die Kette **danach**. Ein Auftrag, bei dem das Bauwerk 17,5 % der
#: Bildbreite füllt, lief bis in die Diffusion — und das Bildmodell erfand eine
#: Fassadendetail-Aufnahme, weil ihm die Vorlage fehlte.
#:
#: Gemessen (HomeStation, `auf-20260824-36`/`-37`), gefüllte Bildbreite → Deckungsmass::
#:
#:     17,5 %  0.0002      50 %  0.001      70 %  0.932
#:     30 %    0.0         65 %  0.637
#:
#: **Der Verlauf ist nicht monoton**: 30 % ist gemessen *schlechter* als 17,5 %. Zwischen
#: den Stützstellen wird darum nicht interpoliert, und die Schwelle steht dort, wo
#: gemessen etwas besteht.
#:
#: .. danger::
#:    **Diese Zahl und** :data:`BILDBREITE_KNIE` **widersprechen einander im Band
#:    0,50–0,65, und der Widerspruch wird hier nicht aufgelöst.** Die Kniemessung vom
#:    24.08. sah die Schwelle zwischen 0,5991 und 0,6488 fallen; die Kettenmessung vom
#:    25.08. sieht bei 50 % noch 0.001. Zwei Messungen, zwei Bedingungen — und die
#:    Regel dieses Projekts lautet, dass eine Zahl an die Bedingung gehört, unter der sie
#:    entstanden ist. Genommen wird die **vorsichtigere**: In einem Band, in dem eine von
#:    zwei Messungen 0.001 sagt, ist ein Renderlauf GPU-Zeit gegen ein Ergebnis, das
#:    niemand verteidigen kann. Wer das Band öffnen will, misst es — und senkt nicht
#:    diese Zahl.
BILDBREITE_ABBRUCH = 0.65


def rahmungsverhaeltnis(szene_bbox, bauwerk_bbox, *,
                        deckungsgrad: float = DECKUNGSGRAD) -> dict:
    """Wieviel Bild füllt das **Bauwerk**, wenn die Kamera die **Szene** rahmt?

    **Die Frage, die vor dem Renderlauf beantwortet gehört** — und bis zum 25.08.2026 gar
    nicht beantwortbar war, weil der Runner nur *eine* Hüllbox führte.

    :func:`kamerasatz` stellt die Kamera so, dass die übergebene Box ``deckungsgrad`` der
    Bildbreite einnimmt. Ist das die Box der **ganzen Szene**, füllt das Bauwerk darin nur
    seinen Anteil davon. Gemessen (`auf-13`): Ein Quader auf einer Platte mit zehnfacher
    Grundfläche kommt so auf 1,9 % des Bildes, und das Tor kann rechnerisch nicht bestehen.

    **Das ist eine Rechnung und keine Messung**, und der Unterschied gehört dazu: Der
    Breitenanteil folgt aus den beiden Boxen, der Flächenanteil im Bild hängt zusätzlich
    an der Form des Bauwerks und am Blickwinkel. Die Zahl hier sagt darum, ob die
    **Rahmung** trägt — nicht, welchen Wert die QA erreichen wird.

    Returns:
        ``{breitenanteil, wirksame_bildbreite, traegt, knie, abbruch, abbruch_grund,
        grund}``. ``traegt`` ist ``None``, wenn eine der Boxen fehlt — **nicht** ``False``.

        ``traegt`` und ``abbruch`` beantworten **zwei verschiedene Fragen** und stehen
        darum nebeneinander:

        * ``traegt`` — steht die Rahmung der Messung im Weg? Massstab ist
          :data:`BILDBREITE_KNIE` (0,5991), die untere Kante des gemessenen Knies.
        * ``abbruch`` — soll dieser Lauf **gar nicht erst gerendert** werden? Massstab
          ist :data:`BILDBREITE_ABBRUCH` (0,65), die Stützstelle, an der gemessen etwas
          besteht. ``None`` heisst *nicht feststellbar* und führt **nie** zum Abbruch:
          Wer keine Bauwerksbox hat — und das sind alle Aufnahmen vor dem 25.08.2026 —,
          rendert wie bisher.

        Im Band dazwischen ist ``traegt`` wahr und ``abbruch`` ebenfalls. Das ist kein
        Widerspruch im Code, sondern einer zwischen zwei Messungen; er steht bei
        :data:`BILDBREITE_ABBRUCH`.

    Raises:
        ValueError: Eine Box hat nicht die Form zweier Punkte mit je drei Zahlen.
    """
    antwort = {"breitenanteil": None, "wirksame_bildbreite": None, "traegt": None,
               "knie": BILDBREITE_KNIE, "abbruch": None, "abbruch_grund": "",
               "grund": ""}
    if bauwerk_bbox is None or szene_bbox is None:
        antwort["grund"] = (
            "Eine der beiden Hüllboxen fehlt. Ohne die Box der gebauten Substanz ist der "
            "Bruch zwischen Rahmung und Messung NICHT FESTSTELLBAR — das ist etwas "
            "anderes als 'die Rahmung ist in Ordnung'.")
        return antwort

    szene = huellbox_taugt(szene_bbox)["masse_m"]
    bau = huellbox_taugt(bauwerk_bbox)["masse_m"]
    # Die WAAGRECHTE Ausdehnung entscheidet über die Bildbreite. Die grössere der beiden
    # Grundrisskanten, wie in `kamerasatz`: Eine Kamera über Eck sieht die Diagonale, eine
    # frontale die längere Seite — die kleinere anzusetzen unterschätzte den Bedarf.
    szene_breit = max(szene[0], szene[1])
    bau_breit = max(bau[0], bau[1])
    if szene_breit <= 0.0:
        antwort["grund"] = ("Die Szenenbox hat keine waagrechte Ausdehnung — siehe "
                            "huellbox_taugt. NICHT FESTSTELLBAR.")
        return antwort

    anteil = bau_breit / szene_breit
    wirksam = float(deckungsgrad) * anteil
    antwort["breitenanteil"] = anteil
    antwort["wirksame_bildbreite"] = wirksam
    antwort["traegt"] = wirksam >= BILDBREITE_KNIE
    # Die zweite, schaerfere Frage — und die einzige, die einen Renderlauf verhindert.
    antwort["abbruch"] = wirksam < BILDBREITE_ABBRUCH
    if antwort["abbruch"]:
        antwort["abbruch_grund"] = (
            f"NICHT RENDERN: Das Bauwerk fuellt {wirksam:.1%} der Bildbreite, gemessen "
            f"noetig sind {BILDBREITE_ABBRUCH:.0%} (auf-vis-20260825-15, Posten 1: bei "
            f"17,5 % entstand 0.0002, bei 30 % sogar 0.0, bei 65 % dagegen 0.637). "
            f"Ein Lauf hier kostet GPU-Zeit fuer ein Bild, das die Vorlage nicht traegt "
            f"— das Bildmodell erfindet dann, was es nicht sieht. Abhilfe ist eine "
            f"naehere Kamera oder die Bauwerksbox als Rahmen.")
        if antwort["traegt"]:
            antwort["abbruch_grund"] += (
                f" Achtung: Der Wert liegt UEBER dem Knie {BILDBREITE_KNIE:.4f} und "
                f"trotzdem unter der Abbruchschwelle — die beiden Messungen sind sich in "
                f"diesem Band uneinig, siehe BILDBREITE_ABBRUCH.")

    if antwort["traegt"]:
        antwort["grund"] = (
            f"Das Bauwerk misst {anteil:.1%} der Szenenbreite; bei Deckungsgrad "
            f"{deckungsgrad:.2f} füllt es {wirksam:.1%} der Bildbreite und liegt damit "
            f"über dem gemessenen Knie von {BILDBREITE_KNIE:.2f}. Über das Bild sagt das "
            f"nichts — nur, dass die Rahmung der Messung nicht im Weg steht.")
    else:
        antwort["grund"] = (
            f"RAHMUNG ZU WEIT: Das Bauwerk misst nur {anteil:.1%} der Szenenbreite. Bei "
            f"Deckungsgrad {deckungsgrad:.2f} füllt es {wirksam:.1%} der Bildbreite, "
            f"gemessen nötig sind mindestens {BILDBREITE_KNIE:.2f} (Empfehlung 0.70). "
            f"Die Kamera rahmt die SZENE, gemessen wird das BAUWERK — auf einer grossen "
            f"Geländeplatte kann das Tor so rechnerisch nicht bestehen (auf-13). Abhilfe "
            f"ist eine nähere Kamera oder die Bauwerksbox als Rahmen, keine gesenkte "
            f"Schwelle.")
    return antwort


def berichtsfelder_aus_stellung(auge, blick_auf, bbox, *,
                                brennweite_mm: float = BRENNWEITE_MM,
                                gelaende_z: float | None = None) -> dict:
    """Die Felder, die die Kompositionsprüfung braucht — aus einer **gestellten** Kamera.

    **Der Anlass ist ein Wächter, der auf dem Produktivweg nie greift** (HomeStation,
    24.08.2026): *«`komposition.beurteilt` ist bei ausdrücklichen Kameras immer false.»*

    Und das ist der schlechteste denkbare Ort dafür. Kommt der Kamerastandort als Zahlen
    herein — und **so schickt ihn die Oberfläche** —, rechnet :func:`kamerasatz` gar
    nicht, und der Bericht trägt ``abstand_m``, ``gelaende_z``, ``gelaende_bezug`` und
    ``gebaeudehoehe_m`` nicht. :func:`aiimaging.komposition.beurteile_bericht` antwortet
    dann völlig richtig «nicht beurteilbar» — und zwar bei **jedem** Auftrag, der über die
    Oberfläche kommt. Die vierte tote Kante dieser Woche, und die folgenreichste: Das
    Regelwerk läuft genau dort nicht, wo Bilder für Menschen entstehen.

    **Die Zahlen fehlen nicht, sie wurden nur nie ausgerechnet.** Standort, Blickziel und
    Hüllbox liegen alle vor.

    **Warum das hier steht und nicht im Runner.** Es ist reine Arithmetik. Im Runner wäre
    es eine Fähigkeit, die ohne Blender niemand hätte — Regel 4. Der Runner ruft es auf,
    wenn er dieses Modul erreicht, und schreibt sonst gar nichts, statt zu raten.

    Args:
        auge: Standort der Kamera, ``(x, y, z)`` im Weltsystem.
        blick_auf: Punkt, auf den sie zielt.
        bbox: ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` der Szene.
        gelaende_z: Geländestand, oder ``None`` für die Unterkante der Hüllbox — dieselbe
            Regel wie in :func:`kamerasatz`.

    Returns:
        ``{abstand_m, gelaende_z, gelaende_bezug, gebaeudehoehe_m, brennweite_mm}``.

    .. note::
       ``abstand_m`` ist hier die **waagrechte Entfernung vom Auge zum Blickziel**. Auf dem
       gerechneten Weg ist es die Komponente **längs der Blickachse**; die beiden
       unterscheiden sich um den seitlichen Versatz (:data:`FRONTAL_VERSATZ`) und fallen
       ohne ihn zusammen. Für ein Urteil über die Aufnahme ist die Aufnahmeentfernung die
       gemeinte Grösse — der Unterschied steht hier, damit ihn niemand für einen Fehler
       hält.

    Raises:
        ValueError: Punkte oder Hüllbox haben nicht drei Zahlen. ``ValueError`` und keine
            eigene Klasse — dieses Modul wirft durchgehend ``ValueError``, und eine
            zweite Fehlerart für dieselbe Sorte Fehler zwänge jeden Aufrufer, beide zu
            fangen.
    """
    def _punkt(p, name):
        try:
            x, y, z = (float(w) for w in p)
        except (TypeError, ValueError) as fehler:
            raise ValueError(f"{name} braucht drei Zahlen, war {p!r}.") from fehler
        return x, y, z

    ax, ay, _az = _punkt(auge, "auge")
    zx, zy, _zz = _punkt(blick_auf, "blick_auf")
    try:
        unten, oben = bbox
    except (TypeError, ValueError) as fehler:
        raise ValueError(f"bbox braucht zwei Punkte, war {bbox!r}.") from fehler
    _ux, _uy, uz = _punkt(unten, "bbox[min]")
    _ox, _oy, oz = _punkt(oben, "bbox[max]")

    grund = float(uz) if gelaende_z is None else float(gelaende_z)
    bezug = "huellbox_unterkante" if gelaende_z is None else "gesetzt"
    return {
        "abstand_m": round(math.hypot(ax - zx, ay - zy), 4),
        "gelaende_z": round(grund, 4),
        "gelaende_bezug": bezug,
        "gebaeudehoehe_m": round(float(oz) - grund, 4),
        "brennweite_mm": float(brennweite_mm),
    }


def kamerasatz(bbox, *,
               brennweite_mm: float = BRENNWEITE_MM,
               seitenverhaeltnis: float = 16 / 9,
               deckungsgrad: float = DECKUNGSGRAD,
               augenhoehe_m: float = AUGENHOEHE_M,
               gelaende_z: float | None = None,
               bias_grad: float = BIAS_GRAD,
               bildrand: float = BILDRAND,
               modus: str = MODUS_SHIFT,
               kuerzel=None) -> dict:
    """Aus einer Hüllbox die zwölf Kameras — mit Begründung je Kamera.

    Der Ablauf je Richtung: analytischer Abstand aus dem Bildwinkel, Standort auf
    Augenhöhe, Blickziel angehoben, dann der Eckentest mit Rückschub. Der Verdeckungstest
    fehlt hier bewusst — er braucht die Szene und wird im Runner über ``ziehe_bis_frei``
    nachgeschaltet.

    Args:
        bbox: ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` in Metern, **im Weltsystem**.
        gelaende_z: Höhe des Geländes im Weltsystem, in Metern. ``None`` nimmt die
            Unterkante der Hüllbox. Angeben, wenn das Bauwerk ein **Untergeschoss** hat —
            sonst steht die Kamera im Keller. Nicht angeben heisst nicht „egal", sondern
            „die Unterkante ist die beste Schätzung, die die Daten hergeben".
        modus: ``MODUS_SHIFT`` (Vorgabe seit 23.08.2026) oder ``MODUS_GEKIPPT``.

            Im Shift-Modus bleibt die Achse **waagrecht** und das Objektiv wird
            verschoben; senkrechte Kanten bleiben damit senkrecht. Der Shift wird am
            **analytischen** Abstand bestimmt und danach nicht mehr nachgeführt — ein
            wirkliches Shift-Objektiv verstellt sich auch nicht von selbst, wenn der
            Fotograf einen Schritt zurücktritt. Schiebt der Eckentest die Kamera zurück,
            sitzt das Bauwerk darum etwas tiefer im Rahmen als im gekippten Modus. Das
            ist kein Fehler der Rechnung, sondern was eine Kamera tut.
        kuerzel: Auswahl aus ``RICHTUNGSFOLGE``, oder ``None`` für alle zwölf.

    Returns:
        dict mit ``kameras`` (Liste in der Reihenfolge von ``RICHTUNGSFOLGE``),
        ``masse_m``, ``mitte``, ``bias_grad``, ``unvollstaendig`` — die Kürzel der
        Kameras, deren Eckentest nicht aufging; eine leere Liste dort ist die einzige
        Auskunft, die „alle zwölf sitzen" bedeutet — und ``warnungen``.

        Je Kamera stehen ``abstand_m`` und ``fuellgrad`` dabei: wie weit sie am Ende
        steht und welchen Anteil der Bildbreite das Bauwerk dort einnimmt. **Der
        Eckentest allein genügt als Auskunft nicht** — er meldet „passt", auch wenn das
        Bauwerk ein Fleck in der Bildmitte ist. Zu klein fällt keiner Prüfung auf, die
        nur nach „passt es hinein" fragt.

        Je Kamera stehen ausserdem ``modus``, ``neigung_grad``, ``shift_mm`` und
        ``shift_y``. ``neigung_grad`` steht **auch im gekippten Modus** dabei, und zwar
        absichtlich: Es sind rund 9,5°, sie verletzen die einzige verbindliche Regel des
        Fachs, und diese Tatsache gehört an jedes einzelne Bild statt in ein Dokument,
        das niemand neben dem Bild liest.

    Raises:
        ValueError: bbox unbrauchbar, ``modus`` unbekannt, oder ``kuerzel`` enthält
            einen unbekannten Namen.
    """
    if modus not in MODI:
        raise ValueError(
            f"Unbekannter Kameramodus {modus!r}. Bekannt: {', '.join(MODI)}."
        )
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        raise ValueError(
            "bbox unbrauchbar. Erwartet [[xmin,ymin,zmin],[xmax,ymax,zmax]] mit sechs "
            f"endlichen Zahlen, war: {bbox!r}"
        )
    unten, oben = gelesen
    masse = tuple(abs(oben[i] - unten[i]) for i in range(3))
    mitte = tuple((oben[i] + unten[i]) / 2.0 for i in range(3))
    fuss = min(unten[2], oben[2])

    if kuerzel is None:
        gewaehlt = list(RICHTUNGSFOLGE)
    else:
        gewaehlt = list(kuerzel)
        unbekannt = [k for k in gewaehlt if k not in RICHTUNGEN]
        if unbekannt:
            raise ValueError(
                f"Unbekannte Richtungskürzel: {unbekannt}. "
                f"Bekannt sind: {', '.join(RICHTUNGSFOLGE)}"
            )

    azimute = richtungen(bias_grad)
    # Der Geländestand ist der Bezug — ohne Angabe die Unterkante der Hüllbox. Siehe
    # Modulkopf: Weder „absolut" noch „über der Hüllbox" ist allgemein richtig, aber die
    # Unterkante liegt im Zweifel eine Geschosshöhe daneben und nicht vierhundert Meter.
    grund = fuss if gelaende_z is None else float(gelaende_z)
    # WOHER der Nullpunkt kommt, nicht nur wie hoch er liegt.
    #
    # „Eine Zahl ohne Bezugspunkt ist keine Zahl" — der Satz steht seit dem Raumleser im
    # Projekt, und hier fehlte er noch. Der Unterschied ist nicht kosmetisch: Die
    # Hüllbox-Unterkante liegt bei einem Untergeschoss im Erdreich, und dann steht die
    # Kamera im Keller. `komposition.BEZUGSPUNKTE` führt genau diese Unterscheidung samt
    # ihrer Verlässlichkeit — ohne dieses Feld könnte die Beurteilung sie nicht treffen.
    gelaende_bezug = ("huellbox_unterkante" if gelaende_z is None
                      else "terrain_an_kamera")
    auge_z = grund + augenhoehe_m
    # Das Blickziel liegt darüber, aber niemals über dem Bauwerk hinaus (ZIEL_HOECHSTANTEIL).
    ziel_z = min(auge_z + masse[2] * ZIEL_ANTEIL_HOEHE,
                 fuss + masse[2] * ZIEL_HOECHSTANTEIL)
    hoehe_ueber_grund = ziel_z - fuss

    kameras = []
    unvollstaendig = []
    alle_warnungen: list[str] = []
    for k in gewaehlt:
        azimut = azimute[k]
        rechnung = abstand_aus_bildwinkel(
            masse, azimut, hoehe_ueber_grund=hoehe_ueber_grund,
            brennweite_mm=brennweite_mm, seitenverhaeltnis=seitenverhaeltnis,
            deckungsgrad=deckungsgrad)

        standort, _ = _achsen_aus_azimut(azimut)
        ziel = (mitte[0], mitte[1], ziel_z)

        # Seitlicher Versatz nur bei den Frontalen: eine exakt mittige Frontale ist
        # symmetrisch und damit bildlich tot. Bei den Diagonalen erledigt das der Bias.
        versatz = masse[0] * FRONTAL_VERSATZ if RICHTUNGEN[k][1] == 0 else 0.0
        quer = (standort[1], -standort[0], 0.0)

        auge = (mitte[0] + standort[0] * rechnung["abstand_m"] + quer[0] * versatz,
                mitte[1] + standort[1] * rechnung["abstand_m"] + quer[1] * versatz,
                auge_z)

        # Der Modus entscheidet nur, WIE gerahmt wird — nicht, WAS. Das Ziel oben ist in
        # beiden Fällen dasselbe; im Shift-Modus wird es auf Augenhöhe zurückgeholt und
        # der Höhenunterschied wandert in den Shift.
        schief = shift_aus_ziel(auge, ziel, brennweite_mm=brennweite_mm)
        if modus == MODUS_SHIFT:
            blick = schief["waagrechtes_ziel"]
            shift_mm = schief["shift_mm"]
            alle_warnungen.extend(f"{k}: {w}" for w in schief["warnungen"])
        else:
            blick, shift_mm = ziel, 0.0

        geschoben = schiebe_bis_im_bild(auge, blick, bbox, shift_mm=shift_mm,
                                        brennweite_mm=brennweite_mm,
                                        seitenverhaeltnis=seitenverhaeltnis,
                                        bildrand=bildrand)
        if not geschoben["vollstaendig"]:
            unvollstaendig.append(k)

        # Wie viel des Bildes das Bauwerk am ENDGÜLTIGEN Standort füllt — nicht am
        # analytisch gerechneten. Der Eckentest kann die Kamera noch zurückgeschoben
        # haben, und dann sagt der analytische Abstand nichts mehr über das Bild aus.
        #
        # BEIDE Richtungen, und gewertet wird die grössere. Der Deckungsgrad wird auf
        # Breite und Höhe getrennt angesetzt, und der grössere Bedarf gewinnt — bei einem
        # hohen Bau in einem 16:9-Rahmen ist das die Höhe. Nur die Breite zu messen ergäbe
        # dann eine Warnung für jedes Hochhaus, obwohl der Rahmen vertikal gut gefüllt
        # ist. (Genau dieser Fehler stand hier zuerst: Ein 30 × 30 × 20 m Kubus meldete
        # 27 % Füllung, während er die Bildhöhe zu 46 % einnahm.)
        endgueltig = _laenge((blick[0] - geschoben["auge"][0],
                              blick[1] - geschoben["auge"][1], 0.0))
        hfov = math.radians(rechnung["hfov_grad"])
        vfov = math.radians(rechnung["vfov_grad"])
        # Gemessen an der NAHEN Fassade, nicht in der Gebäudemitte. Der Abstand wird zur
        # Mitte gerechnet; die zugewandte Fassade steht um die halbe Bautiefe näher und
        # ist das, was ein Betrachter als „so gross ist das Haus im Bild" sieht. In der
        # Mitte gemessen erschiene ein 60 m langer Riegel von der Schmalseite als winzig,
        # obwohl seine Stirnfassade den Rahmen füllt — eine Warnung dafür wäre ein
        # Fehlalarm. Die Probe darauf, dass dies das richtige Mass ist: An der nahen
        # Fassade kommt genau der angeforderte Deckungsgrad heraus.
        nah = max(endgueltig - rechnung["tiefe_m"] / 2.0, 1e-6)
        bildbreite = 2.0 * math.tan(hfov / 2.0) * nah
        bildhoehe = 2.0 * math.tan(vfov / 2.0) * nah
        f_breite = (rechnung["breite_m"] / bildbreite) if bildbreite > 0.0 else 0.0
        f_hoehe = (2.0 * rechnung["halbe_hoehe_m"] / bildhoehe) if bildhoehe > 0.0 else 0.0
        fuellgrad = max(f_breite, f_hoehe)

        flaeche = flaechenanteil(geschoben["auge"], blick, bbox,
                                 brennweite_mm=brennweite_mm,
                                 seitenverhaeltnis=seitenverhaeltnis,
                                 shift_mm=shift_mm)

        warnungen = []
        if fuellgrad < deckungsgrad * FUELLGRAD_WARNSCHWELLE:
            warnungen.append(
                f"Das Bauwerk füllt nur {fuellgrad:.1%} des Bildes statt der "
                f"angeforderten {deckungsgrad:.0%} (Breite {f_breite:.1%}, Höhe "
                f"{f_hoehe:.1%}, Fläche {flaeche:.1%}) — massgebend war "
                f"'{rechnung['massgebend']}'. "
                + (f"Bei kleinen Bauten setzt der Mindestabstand von {WANDABSTAND_M:.0f} m "
                   "den Standort, nicht der Bildwinkel; das Verfahren ist auf "
                   "Gebäudemasse ausgelegt. "
                   if rechnung["massgebend"] == "untergrenze" else
                   "Der Eckentest hat die Kamera zurückgeschoben. ")
                + "Ein Bild, auf dem das Bauwerk ein Fleck ist, sieht wie ein Fehler des "
                  "Bildmodells aus — die Ursache liegt hier."
            )
        alle_warnungen.extend(f"{k}: {w}" for w in warnungen)

        kameras.append({
            "kuerzel": k,
            "azimut_grad": azimut,
            "auge": geschoben["auge"],
            "blick_auf": blick,
            "modus": modus,
            # Wie stark die Achse gegen die Waagrechte geneigt ist. Im Shift-Modus 0.0 —
            # das IST die Aussage des Modus. Im gekippten Modus rund 9,5°, und die Zahl
            # steht hier, damit die Normverletzung an jedem Bild klebt.
            "neigung_grad": (0.0 if modus == MODUS_SHIFT else schief["neigung_grad"]),
            "shift_mm": float(shift_mm),
            "shift_y": blender_shift_y(shift_mm),
            "shift_ueber_grenze": bool(modus == MODUS_SHIFT and schief["ueber_grenze"]),
            "brennweite_mm": float(brennweite_mm),
            "seitenverhaeltnis": float(seitenverhaeltnis),
            "abstand_analytisch_m": rechnung["abstand_m"],
            "massgebend": rechnung["massgebend"],
            "durchlaeufe": geschoben["durchlaeufe"],
            "vollstaendig": geschoben["vollstaendig"],
            "abstand_m": endgueltig,
            "fuellgrad": fuellgrad,
            "fuellgrad_breite": f_breite,
            "fuellgrad_hoehe": f_hoehe,
            # Was ein MENSCH sieht — siehe `flaechenanteil`. Der Füllgrad oben war über
            # zwölf gemessene Kameras praktisch konstant, während diese Zahl um den
            # Faktor drei schwankte.
            "flaechenanteil": flaeche,
            "warnungen": tuple(warnungen),
            "begruendung": geschoben["begruendung"],
        })

    # Steht ueberhaupt ein Bauwerk in dieser Huellbox? Die Antwort gehoert nach VORN in
    # die Warnungen, denn wenn sie nein lautet, sind alle uebrigen Zahlen Auskunft ueber
    # eine leere Szene. Der leere Fall warnt ohnehin ueber den Fuellgrad; der Fall OHNE
    # HOEHE tat es bis zum 24.08.2026 nicht — dort sah der ganze Satz gesund aus.
    tauglich = huellbox_taugt(bbox)
    if not tauglich["taugt"]:
        alle_warnungen.insert(0, tauglich["grund"])

    return {
        "kameras": kameras,
        "huellbox_taugt": tauglich["taugt"],
        "leere_achsen": tauglich["leere_achsen"],
        "masse_m": masse,
        "mitte": mitte,
        "bias_grad": float(bias_grad),
        "augenhoehe_m": float(augenhoehe_m),
        "gelaende_z": grund,
        "gelaende_bezug": gelaende_bezug,
        "unvollstaendig": unvollstaendig,
        "warnungen": tuple(alle_warnungen),
    }
