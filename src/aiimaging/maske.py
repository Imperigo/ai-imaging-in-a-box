"""BAUWERKSMASKE — welche Bildpunkte das Bauwerk tragen, und welche nur den Boden.

Warum es dieses Modul gibt (HomeStation-Messung, 21.08.2026)
------------------------------------------------------------
Die Geometrie-QA dieses Projekts war **stumpf**, und der Grund war weder die Metrik noch
die Schwelle, sondern der Bildausschnitt: Sie rechnete über das **ganze** Bild. In einer
Szene mit 59,8 % Bodenanteil verglich sie damit im Wesentlichen zwei Bodenrampen
miteinander — die Soll-Karte einer Bodenszene ist eine glatte Rampe von unten nach oben,
und ein monokularer Tiefenschätzer legt in jede strukturlose Fläche genau so eine Rampe.
Zwei Rampen korrelieren, gleichgültig was dazwischen steht.

Was das gekostet hat, steht in ``docs/MASKE_2026-08-21.md`` und ist gemessen, nicht
vermutet:

* **Weisses Rauschen** — ein Bild ohne jede Geometrie — erreichte auf jener Szene den
  Score **0.72**. Der Anker, gegen den ein echtes Bild sich abheben muss, lag damit fast
  auf der Höhe des Urteils.
* Die Reihe über wachsenden Versatz war **nicht monoton**: 4 m Versatz stand besser da
  als 2 m. Was in der Mitte ein Minimum hat, misst keinen Abstand.

Rechnet man dieselbe Rangkorrelation **nur über die Punkte, an denen das Bauwerk steht**,
kippt das Bild:

* Die Reihe wird **streng monoton** — jeder Meter Versatz kostet, keiner bringt.
* Der Abstand zum Rauschen ist eindeutig (4 m bei ρ = −0.739, Rauschen bei −0.521).
* Und, ungefragt: Die Kurven **zweier ganz verschiedener Szenen** (29 % und 59,8 %
  Bodenanteil) fallen mit höchstens **0.005** Abstand zusammen — ohne jede Normierung.

Daraus folgt der Satz, der dieses Modul begründet: **Die Szenenabhängigkeit war nie eine
Eigenschaft der Metrik. Sie war der Boden.**

Woher die Maske kommt — und warum sie nichts kostet
----------------------------------------------------
Naheliegend wäre eine zweite Blender-Aufnahme nur des Bauwerks. Sie wurde gemessen, und
sie ist **überflüssig**: Der Multipass schreibt ohnehin einen **Material-ID-Pass**
(``material_id.png``), in dem jedes Material eine eigene flache Farbe trägt, samt einer
Tabelle im Blender-Report. Bauwerk = alles ausser Hintergrund und Gelände. Die beiden
Wege liefern nicht bloss gleich viele, sondern **dieselben** Punkte::

    aus zweiter Aufnahme : 44604
    aus Material-ID-Pass : 44604
    gemeinsam            : 44604
    nur in der Aufnahme  : 0
    nur im Material-ID   : 0
    Übereinstimmung      : 100.000 %

Die Maske fällt also im selben Durchgang an, in dem die Soll-Karte entsteht.

Die Bedingung, und sie ist keine Kleinigkeit
---------------------------------------------
Das funktioniert, **weil das Gelände ein eigenes Objekt mit eigenem Materialeintrag ist**
(im Messstand hiess es ``Boden_Platte``). Zwei Dinge folgen daraus, und beide stehen im
Ergebnis dieses Moduls statt in einer Fussnote:

1. **Es braucht eine Regel, woran das Gelände zu erkennen ist.** Solange die Zuordnung
   an einem von Hand gewählten Namen hängt, ist der Weg für einen Messstand gut und für
   den Betrieb nicht fertig. Die Regel steht darum hier als benannte, ersetzbare Grösse
   (:data:`GELAENDE_MUSTER`, Parameter ``gelaende_muster``) und wandert mit ins Ergebnis
   — wer später eine Zahl wiederfindet, sieht ihr an, unter welcher Regel sie entstand.
2. **Greift die Regel nicht, ist das ein Befund.** Dann steckt womöglich der ganze Boden
   als „Bauwerk" in der Maske, und genau die Stumpfheit, gegen die dieses Modul gebaut
   ist, käme durch die Hintertür zurück. Dieser Fall liefert darum ``maske=None`` — die
   Dreiteilung dieses Projekts, *bestanden / durchgefallen / nicht gemessen*: **``None``
   heisst hier nicht gemessen und niemals in Ordnung.** Wer eine geländefreie Szene
   rendert, sagt das mit ``gelaende_erwartet=False`` — als Erklärung des Aufrufers, nicht
   als stille Annahme des Moduls.

Was hier ausdrücklich **nicht** entschieden wird
-------------------------------------------------
Ob Gelände und Bauwerk sich einen **Material**-Eintrag teilen, ist aus dem Bild nicht
erkennbar — dann trügen sie dieselbe Kennfarbe, und keine Regel der Welt könnte sie noch
trennen. Diese Bedingung gehört ins Modell und wird beim Export sichergestellt, nicht
hier. Das Feld ``quelle`` im Ergebnis sagt wenigstens, **worüber** die Regel gelaufen ist:
über echte Materialnamen (``material``) oder über Objektnamen (``objekt``, der Rückfall
des Runners für materiallose Meshes).

Ebenfalls nicht hier: die Anwendung der Maske auf die Geometrie-QA. Dieses Modul liefert
die Punktmenge, es urteilt nicht — dieselbe Trennung wie zwischen ``bildlesen`` und
``geometrie_qa``. Die Gegenseite ist ``geometrie_qa.rho_ueber_maske``; sie nimmt genau
eine indexgleiche Folge von Wahrheitswerten entgegen und weist ``None`` ausdrücklich
zurück, statt es als „alle Punkte" zu deuten. Die beiden Module kennen einander nicht —
was sie verbindet, ist die Liste, und dass beide dasselbe unter ``None`` verstehen.

Reine Standardbibliothek. Kein ``bpy``, kein Oberflächen-Import (Regeln 2 und 4).
"""
from __future__ import annotations

import json
import re
from collections.abc import Sequence
from fnmatch import fnmatchcase
from pathlib import Path

from aiimaging.bildlesen import lies_png_farben

#: Die Farbe, die im Material-ID-Pass **nichts** bedeutet: kein Objekt, kein Material.
#:
#: Das ist keine Vereinbarung, sondern eine Ableitung aus dem Runner. Für den
#: Material-ID-Durchgang setzt er die Welt auf ``(0, 0, 0)`` mit Stärke 0 — ein Strahl,
#: der nichts trifft, bringt exakt Schwarz zurück. Die Kennfarben können Schwarz
#: dagegen gar nicht treffen: Sie entstehen aus ``hsv_to_rgb(h, 0.85, 1.00)``, haben also
#: immer einen Kanal auf 255 und keinen unter 38. Deshalb ist der Vergleich hier exakt
#: und braucht keine Schwelle.
HINTERGRUND_FARBE: tuple[int, int, int] = (0, 0, 0)

#: **Die Geländeregel.** Namensmuster, die einen Material- oder Objektnamen als *Gelände*
#: ausweisen — verglichen wird nach Kleinschreibung mit ``fnmatch``, ``*`` und ``?`` sind
#: also Platzhalter.
#:
#: Jeder Eintrag hier ist eine **Setzung**, und jede hat eine andere Herkunft. Das gehört
#: dazugesagt, weil die Regel der schwächste Punkt des ganzen Verfahrens ist:
#:
#: * ``"boden_platte"`` — **gemessen**, im einzigen Fall, an dem der Weg belegt ist
#:   (``docs/MASKE_2026-08-21.md``: 112 197 Bodenpunkte gegen 44 604 Bauwerkspunkte,
#:   100.000 % Übereinstimmung mit der zweiten Aufnahme). Ein Name aus einem Messstand,
#:   mehr nicht.
#: * ``"ifcsite*"`` — die IFC-Klasse für das Grundstück. Der Stern steht dort, weil der
#:   Exportweg dieses Projekts Klassennamen mit angehängter GUID liefert; in der
#:   gemessenen Tabelle stehen ``IfcSlab_2eYuY4S8…`` und ``IfcWall_0QOeb014…``. Der
#:   Anhang ist also belegt, die Zeile ``IfcSite_…`` selbst noch **nicht gesehen**.
#: * ``"gelaende"``, ``"gelände"``, ``"terrain"`` — Hausgebrauch, ungemessen.
#:
#: **Warum kein Stern an ``gelaende``.** ``"gelaende*"`` fienge ``Geländer`` mit, also
#: ein Handlauf am Bauwerk. Ein Muster, das ein Bauteil zum Boden erklärt, richtet mehr
#: Schaden an als ein Muster, das einen Boden nicht erkennt — das zweite meldet sich
#: (``gelaende_erkannt=False``), das erste nicht.
#:
#: Die Liste ist ein **Vorschlag mit Namen**, kein Messnormal. Wer ein Modell mit anderer
#: Namensgebung hat, ersetzt sie über ``gelaende_muster`` — dafür ist sie ein Parameter.
GELAENDE_MUSTER: tuple[str, ...] = (
    "ifcsite*", "boden_platte", "gelaende", "gelände", "terrain",
)

#: Geländewörter, die auch als **Namensteil** zählen — auf Wortgrenzen, nicht als Teilstring.
#:
#: **Der Anlass ist eine Messung, und sie ist unangenehm** (HomeStation,
#: `auf-vis-20260824-12`, 24.08.2026): :data:`GELAENDE_MUSTER` vergleicht mit ``fnmatch``
#: gegen den **ganzen** Namen, und nur ``ifcsite*`` trägt einen Platzhalter. Ein Objekt
#: namens ``Gelaende_Hang`` fällt damit durch die Regel — die Maske kommt als ``None``
#: zurück, und `_bester_seed` rendert dann **einen** Startwert statt drei.
#:
#: **Auf zwei von drei Auftragsgeometrien griff die Drei-Seed-Vorgabe deshalb gar nicht.**
#: Das ist eine Owner-Vorgabe vom 22.08., die seither still abgeschaltet war, und das
#: Ergebnis hiess fälschlich «ein Startwert genügt».
#:
#: **Warum Wortgrenzen und nicht ``*gelaende*``.** Der Docstring von :func:`ist_gelaende`
#: nennt den Grund gegen Teilstrings: ``"boden" in "Bodenplatte des 2. OG"`` wäre wahr,
#: und ein Geschossboden ist kein Gelände. Ein blosses Präfix wäre ebenso falsch:
#: ``gelände*`` trifft **``Geländer_Balkon``** — ein Geländer ist kein Gelände. Genau
#: dieselbe Falle wie beim Bauteilwächter, wo «Betonung» bei «Beton» anschlug.
#:
#: Darum wird der Name in **Wörter zerlegt** (an ``_``, ``-``, Leerzeichen, Punkt) und
#: jedes Wort einzeln verglichen. ``Gelaende_Hang`` trägt das Wort, ``Geländer_Balkon``
#: nicht.
#: .. warning::
#:    **Die Kehrseite, gemessen am 26.08.2026.** Bis zu jenem Tag überlebte der IFC-Name
#:    den glb-Export nicht — die Wortregel bekam nur ``IfcSlab_<GlobalId>`` zu sehen und
#:    konnte auf einen *Namen* gar nicht anschlagen. Seit der Knotenname ihn mitträgt,
#:    greift sie auf viel mehr, und das ist ihr Zweck. Aber:
#:
#:    ``IfcWall_Site-A`` gilt damit als **Gelände**, weil ``site`` eines dieser Wörter
#:    ist. Eine so benannte Wand fällt aus der Bauwerksmaske.
#:
#:    *Die sichere Richtung ist trotzdem diese:* Gelände **in** der Maske ist der
#:    schlimmere Fehler — auf einer Bodenszene erreichte weisses Rauschen dort den Score
#:    0,72. Ein zu kleines Bauwerk misst weniger; ein zu grosses misst das Falsche.
#:
#:    Damit ein Fehlausschluss auffällt, nennt ``abholer.befund_kurz`` seit demselben Tag
#:    **namentlich**, was als Gelände eingestuft wurde. Wer dort eine Wand liest, hat den
#:    Fall vor sich.
GELAENDE_WOERTER: tuple[str, ...] = ("gelaende", "gelände", "terrain", "site",
                                    "toposolid")

# **``toposolid`` ist am 01.09.2026 dazugekommen, und als EINZIGES.** Die HomeStation hat
# an einem echten Bestand gemessen: Das Gelände heisst dort ``IfcCovering_Toposolid_1``,
# daneben ``Sub-Division`` und ``Umgebung - Gras``. **Keines der vier bisherigen Wörter
# passt**, und die Bauwerksbox schrumpfte darum um 2,1 % statt um 34,5 %.
#
# Aufgenommen wurde nur ``toposolid``: Es ist der Fachbegriff für den Geländekörper in
# Archicad und Revit, und ein *Bauteil* dieses Namens gibt es nicht. ``umgebung`` und
# ``gras`` sind **ausdrücklich nicht** aufgenommen — sie sind allgemein genug, um ein
# echtes Bauteil still zu Gelände zu machen, und der Gewinn wäre gering.
#
# *Und das Wort löst das Problem nicht, es verkleinert es nur:* Das nächste Büro schreibt
# wieder etwas anderes. Was für jeden Bestand gilt, ist die laute Meldung, wenn die Regel
# fast nichts trennt — nicht ein weiteres Wort. Die eigentliche Lösung ist ein Feld je
# Szene und liegt als ``auf-20260901-67`` beim Vertrags-Worker.

#: **Umfeld: weder Bauwerk noch Gelände.** IFC-Klassen für Dinge, die in der Szene stehen
#: und nicht dazugehören — Bäume, Nachbargebäude, Strassenmöbel.
#:
#: *Warum sie nicht in die Geländeliste gehören:* Ein Baum ist kein Boden. Die
#: Bauwerksmaske fragt nicht «ist das Gelände?», sondern «ist das unser Bauwerk?», und für
#: diese Frage sind Gelände und Umfeld zwei verschiedene Nein.
#:
#: Gemessen am selben Bestand (01.09.2026): Bäume als ``IfcGeographicElement``, ein
#: Nachbargebäude als ``IfcCivilElement``. Beide wurden bis dahin als **Bauwerk** gezählt.
#:
#: Verglichen wird gegen den **Klassenanfang** und nicht gegen ein Wort im Namen: Die
#: Klasse steht in diesen Exporten vorn (``IfcCivilElement_Nachbar_1``), und ein Wort
#: mitten im Namen wäre eine viel weichere Regel als eine genormte Klasse.
UMFELD_KLASSEN: tuple[str, ...] = ("ifcgeographicelement", "ifccivilelement")

#: Woran ein Name in Wörter zerfällt.
_WORTTRENNER = re.compile(r"[\s_\-.,;:/\\()\[\]]+")

# ======================================================================================
# Die dritte Antwort, angewandt auf die Geländeregel selbst
# ======================================================================================
#
# **Der Anlass ist eine Rückfrage der HomeStation** (`auf-47`, 26.08.2026). Ihr Modell
# trägt elf benannte Baustoffe — `Beton_Decke`, `Holz_Stuetze`, `Metall_Fassade`, … —,
# keiner davon heisst nach Gelände. Die Regel meldete `gelaende_erkannt: False`, die Maske
# fiel aus, und der Besteller musste `--kein-gelaende` von Hand setzen.
#
# Ihr Einwand, wörtlich: *«Er verlangt, dass der Besteller VORHER weiss, dass kein Gelände
# in der Szene ist. Bei einer fremden glb weiss er das nicht.»* Und ihr Vorschlag: *«Die
# Geräteregel könnte ihren Nullbefund selbst belegen, indem sie meldet, WELCHE Baustoffe
# sie geprüft hat.»*
#
# **Der Punkt ist richtig und trifft eine Verwechslung, die dieses Projekt sonst überall
# auseinanderhält:** `gelaende_erkannt: False` bedeutete bis heute zweierlei —
#
#   * elf lesbare Namen geprüft, keiner nach Gelände → das ist ein **Nullbefund**;
#   * gar nichts Lesbares vorgefunden → das ist **nicht feststellbar**.
#
# Beides ergab `None`, und `None` liest sich wie ein Fehler statt wie eine Enthaltung.

#: Die Regel hat mindestens einen Eintrag als Gelände eingeordnet.
BEFUND_GELAENDE_GEFUNDEN = "gelaende_gefunden"

#: Lesbare Namen geprüft, keiner nach Gelände. **Ein Befund, keine Ratlosigkeit** — aber
#: kein Beweis: Er gilt nur so weit, wie die Regel vollständig ist, und *das* ist an einem
#: einzelnen Lauf nicht messbar. Ein Baustoff namens ``Erdreich`` stünde in keiner
#: Wortliste dieses Projekts und wäre trotzdem Gelände.
BEFUND_KEIN_GELAENDE_BELEGT = "kein_gelaende_belegt"

#: Es gab nichts zu lesen — leere Namen, oder eine Tabelle mit einem einzigen Eintrag
#: (der Klumpenfall: dann ist innerhalb der Geometrie ohnehin nichts trennbar).
BEFUND_NICHT_ENTSCHEIDBAR = "nicht_entscheidbar"

#: Ab wie vielen benannten Einträgen ein Nullbefund überhaupt einer ist.
#:
#: **Zwei**, und die Zahl ist nicht gegriffen: Bei genau einem Eintrag steht der
#: Klumpenfall vor uns — eine 56-MB-Kontext-IFC kam als ein einziges namenloses Bauteil
#: mit 502 002 Dreiecken an (`BEFUND_2026-08-24_IFC-LESER.md`). Dort trennt die Maske noch
#: den Himmel ab und sonst nichts; «kein Gelände gefunden» wäre dann eine Aussage über
#: eine Tabelle, die gar nichts unterscheidet.
MINDESTENS_BENANNT = 2


#: Vorsilbe der IFC-Klassennamen. Kleingeschrieben verglichen; der Exportweg dieses
#: Projekts hängt eine GUID an (``IfcWall_Wand-Nord_1FMjVFy0…``).
IFC_KLASSENPRAEFIX = "ifc"


def ist_ifc_klassenkatalog(namen) -> bool:
    """Besteht diese Namensliste **durchweg** aus IFC-Klassennamen?

    **Warum das eine eigene Frage ist** (Owner-Entscheid 26.08.2026): Ein Nullbefund der
    Geländeregel belegt nur, dass die *Regel* nicht angeschlagen hat — nicht, dass es kein
    Gelände gibt. Beides fällt nur zusammen, wenn die Regel über einen **vollständigen
    Katalog** gelaufen ist.

    Genau das ist bei IFC-Klassennamen der Fall: ``IfcSite`` ist die genormte Klasse für
    das Grundstück und steht in :data:`GELAENDE_MUSTER`. Trägt jeder Eintrag eine
    IFC-Klasse und ist keiner davon ``IfcSite``, dann ist «kein Gelände» ein **Beweis über
    den Katalog** und keine Vermutung über Hausnamen.

    Bei **Materialnamen** gilt das nicht. Echte Projektgeometrie meldet dort «Beton» und
    «kalksandstein» (gemessen, ``docs/MASKE_2026-08-21.md``) — ein Boden hiesse dann
    «Erdreich» oder «Kies» und stünde in keiner Liste. Ein Nullbefund über solchen Namen
    sagt nichts.

    **Alle, nicht die meisten.** Ein einziger Eintrag ohne IFC-Klasse unter hundert mit
    ist genau der, um den es geht: Er könnte der Boden sein. Die Frage ist ein Beweis oder
    sie ist nichts.

    Args:
        namen: Die benannten Einträge der Materialtabelle.

    Returns:
        ``True`` nur, wenn mindestens :data:`MINDESTENS_BENANNT` Namen vorliegen und
        **jeder** mit ``Ifc`` beginnt.
    """
    sauber = [str(n).strip() for n in namen if str(n).strip()]
    if len(sauber) < MINDESTENS_BENANNT:
        return False
    return all(n.lower().startswith(IFC_KLASSENPRAEFIX) for n in sauber)


def gelaende_befund(gelaende_namen, bauwerk_namen) -> dict:
    """Welche der drei Lagen liegt vor — und woran man das sieht.

    Herausgezogen aus :func:`bauwerksmaske`, damit ein Aufrufer sie **ohne Bild** befragen
    kann: Wer eine glb vor sich hat und wissen will, ob ein Lauf ohne ``--kein-gelaende``
    überhaupt Sinn ergibt, braucht dafür keinen Render.

    Args:
        gelaende_namen: Was die Regel als Gelände eingeordnet hat.
        bauwerk_namen: Alles Übrige aus der Tabelle.

    Returns:
        ``{befund, geprueft, benannt, namenlos, begruendung}``. ``geprueft`` ist die
        Namensliste, auf die sich der Befund stützt — **sie wandert mit**, weil ein
        Nullbefund ohne die Liste eine Behauptung ist und mit ihr eine Auskunft.
    """
    gelaende = sorted(set(str(n) for n in gelaende_namen))
    bauwerk = [str(n) for n in bauwerk_namen]
    benannt = sorted({n for n in bauwerk if n.strip()})
    namenlos = sum(1 for n in bauwerk if not n.strip())

    katalog = ist_ifc_klassenkatalog(benannt)

    if gelaende:
        return {"befund": BEFUND_GELAENDE_GEFUNDEN, "geprueft": sorted(set(bauwerk)),
                "benannt": benannt, "namenlos": namenlos, "ifc_katalog": katalog,
                "begruendung": f"Die Regel ordnete {gelaende} als Gelände ein."}

    if len(benannt) >= MINDESTENS_BENANNT and namenlos == 0:
        return {"befund": BEFUND_KEIN_GELAENDE_BELEGT, "geprueft": benannt,
                "benannt": benannt, "namenlos": 0, "ifc_katalog": katalog,
                "begruendung": (
                    f"{len(benannt)} benannte Einträge geprüft, keiner nach Gelände: "
                    f"{benannt}. "
                    + ("Jeder davon trägt eine IFC-Klasse, und IfcSite ist die genormte "
                       "Klasse für das Grundstück — der Nullbefund ist damit ein BEWEIS "
                       "über den Katalog und keine Vermutung über Hausnamen."
                       if katalog else
                       "Die Namen sind keine IFC-Klassen; über sie ist der Nullbefund "
                       "eine Aussage über die REGEL und nicht über die Szene — ein Boden "
                       "namens 'Erdreich' stünde in keiner Liste."))}

    fehlt = ("kein einziger benannter Eintrag" if not benannt
             else f"{namenlos} namenlose Einträge" if namenlos
             else f"nur {len(benannt)} benannter Eintrag (nötig: {MINDESTENS_BENANNT})")
    return {"befund": BEFUND_NICHT_ENTSCHEIDBAR, "geprueft": benannt,
            "benannt": benannt, "namenlos": namenlos, "ifc_katalog": katalog,
            "begruendung": (
                f"Über diese Tabelle lässt sich nichts sagen: {fehlt}. Eine Geländeregel "
                f"über namenlose Flächen ist keine Regel.")}


#: Kurzform des Rechenwegs, wandert in jedes Ergebnis. Dieselbe Bauart wie
#: ``geometrie_qa.METHODE``: Wer später eine Zahl in der Arbeit wiederfindet, soll ihr
#: ansehen, wie sie entstanden ist.
METHODE = ("Bauwerk = Material-ID-Pass ohne Hintergrundfarbe und ohne Geländeeinträge, "
           "Zuordnung Byte-genau über material_id_tabelle, v1")


class MaskeError(ValueError):
    """Aus dieser Eingabe lässt sich keine Maske machen — und ein Ersatzwert wäre schlimmer.

    Erbt von ``ValueError``, dieselbe Wahl wie ``geometrie_qa.QaError`` und
    ``bildlesen.BildError``: Bestehendes ``except ValueError`` greift weiter, und die
    Trennung der drei Klassen sagt trotzdem, *welche* Naht gerissen ist.

    Bewusst ein Fehler und keine leere Maske: Eine leere Maske sähe aus wie „hier steht
    kein Bauwerk" und wäre in Wahrheit „hier wurde nicht gemessen". Genau diese beiden
    Dinge hält dieses Projekt auseinander.
    """


# ======================================================================================
# Die Regel
# ======================================================================================

def ist_umfeld(name: str, klassen: Sequence[str] = UMFELD_KLASSEN) -> bool:
    """Gehört ``name`` zum **Umfeld** — also weder zum Bauwerk noch zum Gelände?

    Bäume, Nachbargebäude, Strassenmöbel. Sie stehen in der Szene und gehören nicht dazu.

    **Der Unterschied zu :func:`ist_gelaende` ist keine Wortklauberei.** Die Maske fragt
    *«ist das unser Bauwerk?»*, und darauf gibt es zwei verschiedene Nein: Der Boden
    trägt es, das Umfeld steht daneben. Ein Nachbargebäude als Gelände zu führen wäre
    zudem eine falsche Aussage über die Szene — und die Szene ist genau das, was hier
    beschrieben wird.

    Geprüft wird der **Klassenanfang**, kleingeschrieben und ohne führende Leerzeichen.
    Ein ``IfcCivilElement_Nachbar_1`` gilt, ein ``Wand_IfcCivilElement_Attrappe`` nicht.
    """
    sauber = str(name or "").strip().lower()
    return any(sauber.startswith(k) for k in klassen)


def ist_gelaende(name: str, muster: Sequence[str] = GELAENDE_MUSTER) -> bool:
    """Gilt ``name`` nach der Geländeregel als Gelände?

    Die eine Stelle, an der die Regel *angewendet* wird — herausgezogen, damit sie
    einzeln prüfbar ist und damit ein Aufrufer sie befragen kann, ohne ein Bild zu haben.

    Verglichen wird der **ganze** Name nach Kleinschreibung gegen jedes Muster
    (``fnmatch``: ``*`` und ``?`` sind Platzhalter, sonst gilt Gleichheit). Kein
    Teilstring-Vergleich: ``"boden" in "Bodenplatte des 2. OG"`` wäre wahr, und ein
    Geschossboden ist kein Gelände. Wer Teilstrings will, schreibt sie als ``"*boden*"``
    hin — dann steht die Entscheidung wenigstens da.

    **Und seit dem 25.08.2026 zusätzlich auf Wortgrenzen** (:data:`GELAENDE_WOERTER`): Der
    Name wird an ``_``, ``-``, Leerzeichen und Satzzeichen zerlegt, und jedes Wort einzeln
    verglichen. ``Gelaende_Hang`` gilt damit als Gelände, ``Geländer_Balkon`` nicht.

    Der Anlass steht bei :data:`GELAENDE_WOERTER` und ist gemessen: Ohne diese Ergänzung
    fiel auf **zwei von drei** Auftragsgeometrien die Maske aus, und mit ihr still die
    Drei-Startwert-Vorgabe des Owners.

    **Die Wortliste ist nicht dasselbe wie die Musterliste** und darf es nicht werden: Ein
    Muster beschreibt den ganzen Namen, ein Wort einen Teil davon. Wer ``boden`` hier
    einträgt, macht jeden Geschossboden zu Gelände — das ist der Grund, warum genau vier
    Wörter darin stehen und keines davon mehrdeutig ist.

    Args:
        name: Material- oder Objektname aus der Material-ID-Tabelle.
        muster: Die Regel. Leer heisst: keine Regel, nichts ist Gelände — das ist
            zulässig und wird von :func:`bauwerksmaske` als Befund behandelt, nicht als
            Erfolg.

    Returns:
        ``True``, wenn mindestens ein Muster passt.
    """
    n = str(name).strip().lower()
    if any(fnmatchcase(n, str(m).strip().lower()) for m in muster):
        return True
    # Wortgrenzen, nicht Teilstrings — siehe GELAENDE_WOERTER. Nur wirksam, wenn der
    # Aufrufer die Vorgabemuster benutzt: Wer eine EIGENE Regel uebergibt, bekommt genau
    # sie und keine stille Zugabe.
    if tuple(muster) != GELAENDE_MUSTER:
        return False
    return bool(set(_WORTTRENNER.split(n)) & set(GELAENDE_WOERTER))


# ======================================================================================
# Die Tabelle
# ======================================================================================

def _farbe_aus_eintrag(eintrag, stelle: int) -> tuple[int, int, int]:
    """Ein ``farbe_srgb_8bit`` aus der Tabelle prüfen und als Tripel zurückgeben."""
    if not isinstance(eintrag, dict):
        raise MaskeError(
            f"material_id_tabelle[{stelle}] ist {type(eintrag).__name__}, erwartet wird "
            f"ein Eintrag mit 'name' und 'farbe_srgb_8bit'."
        )
    farbe = eintrag.get("farbe_srgb_8bit")
    if not isinstance(farbe, (list, tuple)) or len(farbe) != 3:
        raise MaskeError(
            f"material_id_tabelle[{stelle}] ('{eintrag.get('name')}') hat kein "
            f"'farbe_srgb_8bit' mit drei Werten, sondern {farbe!r}. Die Farbe aus dem "
            f"Index zurückzurechnen wäre möglich — der Runner verteilt die Farbtöne über "
            f"den Goldenen Winkel — aber es wäre Raten: Die Palette ist eine Entscheidung "
            f"des Runners und darf sich ändern, ohne dass dieses Modul davon erfährt. "
            f"Die Tabelle ist der Schlüssel, nicht die Formel."
        )
    try:
        werte = tuple(int(k) for k in farbe)
    except (TypeError, ValueError) as fehler:
        raise MaskeError(
            f"material_id_tabelle[{stelle}] ('{eintrag.get('name')}') trägt die Farbe "
            f"{farbe!r} — keine ganzen Zahlen."
        ) from fehler
    if not all(0 <= k <= 255 for k in werte):
        raise MaskeError(
            f"material_id_tabelle[{stelle}] ('{eintrag.get('name')}') trägt die Farbe "
            f"{werte!r}. Erwartet werden Werte in 0..255."
        )
    return werte  # type: ignore[return-value]


def tabelle_aus_report(report) -> list[dict]:
    """``material_id_tabelle`` aus einem Blender-Report holen — Pfad oder schon geladen.

    **Warum die Tabelle nicht optional ist.** Die Farben des Material-ID-Passes sind über
    den Goldenen Winkel verteilt (``h = index * 0.618…``), man könnte aus einer Farbe
    also den Index zurückrechnen. Aus dem Index folgt aber **kein Name** — und ohne Namen
    greift keine Geländeregel. Die Rückrechnung führte damit genau zu dem Ergebnis, gegen
    das dieses Modul gebaut ist: einer Maske, die den Boden enthält, ohne es zu sagen.

    Args:
        report: ``dict`` (der geladene Report) oder ein Pfad auf ``blender-report.json``.

    Returns:
        Die Tabelle als Liste von Einträgen, unverändert wie im Report.

    Raises:
        MaskeError: Datei fehlt oder ist kein JSON-Objekt, ``material_id_tabelle`` fehlt,
            ist leer oder ist keine Liste. Eine leere Tabelle heisst in aller Regel: Der
            Lauf lief mit ``--ohne-material-id``. Dann gibt es keine Maske, und das ist
            eine Aussage über den Lauf, nicht über das Bauwerk.
    """
    if isinstance(report, dict):
        daten = report
        herkunft = "übergebener Report"
    else:
        pfad = Path(report)
        try:
            roh = pfad.read_text(encoding="utf-8")
        except OSError as fehler:
            raise MaskeError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler
        try:
            daten = json.loads(roh)
        except json.JSONDecodeError as fehler:
            raise MaskeError(f"{pfad} ist kein gültiges JSON: {fehler}") from fehler
        if not isinstance(daten, dict):
            raise MaskeError(
                f"{pfad} enthält {type(daten).__name__} statt eines Report-Objekts."
            )
        herkunft = str(pfad)

    tabelle = daten.get("material_id_tabelle")
    if tabelle is None:
        raise MaskeError(
            f"{herkunft}: kein Feld 'material_id_tabelle'. Ohne die Zuordnung "
            f"Farbe → Name ist der Material-ID-Pass ein Bild aus bunten Flächen und "
            f"sonst nichts."
        )
    if not isinstance(tabelle, list):
        raise MaskeError(
            f"{herkunft}: 'material_id_tabelle' ist {type(tabelle).__name__} statt einer "
            f"Liste."
        )
    if not tabelle:
        raise MaskeError(
            f"{herkunft}: 'material_id_tabelle' ist leer. Der Lauf hat keinen "
            f"Material-ID-Pass geschrieben (``--ohne-material-id``) — es gibt hier nichts "
            f"zu maskieren, und eine Maske aus dem Nichts wäre erfunden."
        )
    return tabelle


# ======================================================================================
# Die Maske
# ======================================================================================

def bauwerksmaske(farben: Sequence[Sequence[int]], tabelle: Sequence[dict], *,
                  gelaende_muster: Sequence[str] = GELAENDE_MUSTER,
                  gelaende_erwartet: bool = True) -> dict:
    """Farben eines Material-ID-Passes + Tabelle → Bauwerksmaske. Ohne Dateizugriff.

    Args:
        farben: Die Bildpunkte als ``(r, g, b)``-Tripel in 0..255, zeilenweise von oben
            nach unten — also genau das, was
            :func:`aiimaging.bildlesen.lies_png_farben` liefert, und damit indexgleich
            zu einer Tiefenkarte desselben Laufs.
        tabelle: ``material_id_tabelle`` aus dem Blender-Report. Jeder Eintrag braucht
            ``name`` und ``farbe_srgb_8bit``.
        gelaende_muster: **Die Geländeregel**, siehe :data:`GELAENDE_MUSTER` und
            :func:`ist_gelaende`. Ersetzbar, weil sie ersetzt werden **muss**, sobald ein
            Modell anders benannt ist.
        gelaende_erwartet: Ob in dieser Szene überhaupt Gelände vorkommt. Die Vorgabe
            ``True`` heisst: „Hier steht ein Boden, und die Regel soll ihn finden."
            Findet sie ihn dann nicht, bleibt ``maske`` ``None``.

            Das ist der Kern der Sache und keine Vorsicht: Aus dem Bild allein ist
            **nicht entscheidbar**, ob die Regel danebengriff oder ob es schlicht keinen
            Boden gibt. Beides sieht gleich aus. Wer es weiss, sagt es — mit ``False``.
            Wer es nicht weiss, bekommt ``None`` und damit eine Frage statt einer
            Antwort.

    Returns:
        ``{maske, n_bildpunkte, n_bauwerk, n_gelaende, n_hintergrund, n_unbekannt,
        anteil_bauwerk, gelaende_erkannt, gelaende_namen, bauwerk_namen, quelle, muster,
        methode, warnungen}``

        * ``maske`` — Liste von ``bool``, ``True`` wo das Bauwerk steht; ``None``, wenn
          die Geländeregel auf keinen Eintrag passte und Gelände erwartet war.
          **``None`` ist keine leere Maske, sondern keine Maske.**
        * ``n_bauwerk``/``n_gelaende``/``n_hintergrund``/``n_unbekannt`` — Bildpunkte je
          Sorte. Sie werden **immer** gezählt, auch wenn ``maske`` ``None`` ist: Die
          Zahlen sind der Befund, aus dem der Aufrufer sieht, *warum* nichts vorliegt.
          ``n_bauwerk`` heisst dabei immer dasselbe — „weder Hintergrund noch **erkanntes**
          Gelände". Wenn die Regel nicht griff, ist darin der Boden mitgezählt; genau
          deshalb steht dort dann keine Maske.
        * ``n_unbekannt`` — Punkte in einer Farbe, die in der Tabelle nicht vorkommt. Sie
          zählen **nicht** zum Bauwerk. Eine unbekannte Farbe einer Seite zuzuschlagen
          hiesse zu raten; der Runner schaltet Dithering und Rekonstruktionsfilter
          ausdrücklich ab, damit es sie gar nicht erst gibt (mit Dithering wurden aus 5
          Farben gemessene 19).
        * ``anteil_bauwerk`` — ``n_bauwerk / n_bildpunkte``. Zum Vergleich: Im Messstand
          waren es 17,02 %.
        * ``gelaende_erkannt`` — ob die Regel auf mindestens einen Tabelleneintrag passte.
        * ``gelaende_namen``/``bauwerk_namen`` — was die Regel wohin sortiert hat. Ohne
          diese beiden Listen wäre die Regel eine Blackbox, und eine Regel, deren Wirkung
          man nicht sieht, prüft niemand nach.
        * ``quelle`` — sortierte ``quelle``-Werte der Tabelle: ``material`` (echte
          Materialnamen) oder ``objekt`` (Rückfall des Runners für materiallose Meshes).
          Wer eine Objekt-Maske für eine Material-Maske hält, sucht später den Fehler an
          der falschen Stelle.
        * ``muster``/``methode`` — die verwendete Regel und der Rechenweg, damit ein
          Ergebnis ohne seinen Aufruf lesbar bleibt.
        * ``warnungen`` — Klartextsätze. Leer heisst: nichts aufgefallen.

    Raises:
        MaskeError: leere Bildpunktliste, leere oder fehlerhafte Tabelle, ein Eintrag
            ohne brauchbare Farbe, ein Eintrag in der Hintergrundfarbe, oder zwei
            Einträge derselben Farbe, von denen einer Gelände und einer Bauwerk ist.
            Der letzte Fall ist der einzige Kollisionsfall, der wirklich unlösbar ist —
            zwei gleichfarbige Wände stören niemanden, eine gleichfarbige Wand und ein
            gleichfarbiger Boden lassen sich nicht mehr trennen.
    """
    if not farben:
        raise MaskeError("Keine Bildpunkte — es gibt nichts zu maskieren.")
    if not tabelle:
        raise MaskeError(
            "Leere material_id_tabelle. Ohne Zuordnung Farbe → Name ist jede Fläche im "
            "Bild namenlos, und eine Geländeregel über namenlose Flächen ist keine Regel."
        )

    # ── Tabelle in eine Farbzuordnung übersetzen ──────────────────────────────────────
    nach_farbe: dict[tuple[int, int, int], dict] = {}
    gelaende_namen: list[str] = []
    bauwerk_namen: list[str] = []
    umfeld_namen: list[str] = []
    warnungen: list[str] = []

    for stelle, eintrag in enumerate(tabelle):
        farbe = _farbe_aus_eintrag(eintrag, stelle)
        name = str(eintrag.get("name", ""))
        # DAS UMFELD ZAEHLT WIE GELAENDE: nicht Bauwerk. Es steht trotzdem in einer
        # eigenen Liste, weil es etwas anderes IST — ein Baum ist kein Boden, und die
        # Namen im Befund sollen sagen, was ausgeschlossen wurde und warum.
        umfeld = ist_umfeld(name)
        gelaende = umfeld or ist_gelaende(name, gelaende_muster)
        if farbe == HINTERGRUND_FARBE:
            raise MaskeError(
                f"material_id_tabelle[{stelle}] ('{name}') trägt die Hintergrundfarbe "
                f"{HINTERGRUND_FARBE}. Dann wäre nicht mehr unterscheidbar, ob ein "
                f"schwarzer Bildpunkt dieses Material zeigt oder gar nichts. Die Palette "
                f"des Runners kann Schwarz nicht erzeugen (Helligkeit 1.0, Sättigung "
                f"0.85) — diese Tabelle stammt also nicht aus ihr."
            )
        vorher = nach_farbe.get(farbe)
        if vorher is not None:
            if vorher["gelaende"] != gelaende:
                raise MaskeError(
                    f"Farbkollision: '{vorher['name']}' und '{name}' tragen beide "
                    f"{farbe}, werden von der Geländeregel aber verschieden eingeordnet "
                    f"({'Gelände' if vorher['gelaende'] else 'Bauwerk'} gegen "
                    f"{'Gelände' if gelaende else 'Bauwerk'}). Diese Bildpunkte sind "
                    f"nicht zuzuordnen, und eine Seite zu wählen hiesse zu raten."
                )
            warnungen.append(
                f"Zwei Einträge tragen dieselbe Kennfarbe {farbe}: '{vorher['name']}' "
                f"und '{name}'. Für die Maske ist das folgenlos — beide gelten als "
                f"{'Gelände' if gelaende else 'Bauwerk'} —, für jede spätere Auswertung "
                f"je Material aber nicht."
            )
        else:
            nach_farbe[farbe] = {"name": name, "gelaende": gelaende}
        if umfeld:
            umfeld_namen.append(name)
        elif gelaende:
            gelaende_namen.append(name)
        else:
            bauwerk_namen.append(name)

    gelaende_erkannt = bool(gelaende_namen)
    lage = gelaende_befund(gelaende_namen, bauwerk_namen)

    if umfeld_namen:
        # NICHT STILL AUSSCHLIESSEN. Der einzige ernsthafte Einwand gegen das
        # Ausschliessen ist ein Bauteil unseres Baus, das faelschlich als
        # `IfcCivilElement` exportiert waere. Es steht dann hier beim Namen — und ein
        # benannter Ausschluss ist widerlegbar, ein stiller nicht.
        warnungen.append(
            f"UMFELD AUSGESCHLOSSEN: {len(set(umfeld_namen))} Eintrag/Einträge zählen "
            f"weder als Bauwerk noch als Gelände — {sorted(set(umfeld_namen))[:5]}. "
            f"Geprüft wurde gegen den Klassenanfang {list(UMFELD_KLASSEN)}. Steht "
            f"darunter etwas, das zu unserem Bauwerk gehört, ist es hier zu Unrecht "
            f"draussen; dann stimmt der Export und nicht die Regel.")
        if any(str(n).strip().lower().startswith("ifccivilelement") for n in umfeld_namen):
            # DER VORBEHALT ZUM UMRISSMASS, und er ist gemessen (auf-20260823-37):
            # Steht hinter dem Bauwerk ein Nachbargebaeude statt Himmel, trennt der
            # Kantenanteil ein PERFEKTES Bild nicht mehr von weissem Rauschen
            # (+0.0016 gegen -0.0024). Ein Vorbehalt, den der Leser erbt statt ihn zu
            # sehen, ist keiner.
            warnungen.append(
                "NACHBARGEBAEUDE IN DER SZENE: Der Kantenanteil an der Maskengrenze ist "
                "hier nur eingeschränkt aussagekräftig. Gemessen (auf-20260823-37): "
                "Steht hinter dem Bauwerk ein Nachbargebäude statt Himmel, trennt das "
                "Umrissmass ein perfektes Bild nicht mehr von weissem Rauschen "
                "(+0.0016 gegen −0.0024). Das Paarurteil ruht dann allein auf ρ.")

    # ── Bildpunkte einsortieren ───────────────────────────────────────────────────────
    n_gelaende = n_hintergrund = n_unbekannt = 0
    roh_maske: list[bool] = []
    unbekannte_farben: set[tuple[int, int, int]] = set()

    for stelle, punkt in enumerate(farben):
        if len(punkt) != 3:
            raise MaskeError(
                f"Bildpunkt {stelle} hat {len(punkt)} statt 3 Werte. Erwartet wird "
                f"(r, g, b) — so, wie bildlesen.lies_png_farben es liefert."
            )
        farbe = (int(punkt[0]), int(punkt[1]), int(punkt[2]))
        if farbe == HINTERGRUND_FARBE:
            n_hintergrund += 1
            roh_maske.append(False)
            continue
        eintrag = nach_farbe.get(farbe)
        if eintrag is None:
            n_unbekannt += 1
            unbekannte_farben.add(farbe)
            roh_maske.append(False)
            continue
        if eintrag["gelaende"]:
            n_gelaende += 1
            roh_maske.append(False)
            continue
        roh_maske.append(True)

    n_bildpunkte = len(roh_maske)
    n_bauwerk = sum(roh_maske)

    # ── Befunde ───────────────────────────────────────────────────────────────────────
    if not gelaende_erkannt:
        if gelaende_erwartet and lage["befund"] == BEFUND_KEIN_GELAENDE_BELEGT:
            # DER NULLBEFUND MIT SEINEM BELEG.
            #
            # Er sagt dem Aufrufer die ANTWORT statt der Frage — das ist der Unterschied
            # zum Satz darunter. Die Maske fällt trotzdem aus, und der Grund dafür steht
            # dabei: Ein Nullbefund belegt, dass die REGEL nicht angeschlagen hat, nicht,
            # dass es kein Gelände gibt. Diese beiden Dinge fallen nur zusammen, wenn die
            # Regel vollständig ist, und Vollständigkeit ist an einem Lauf nicht messbar.
            warnungen.append(
                f"KEIN GELAENDE BELEGT: {lage['begruendung']} "
                f"Geprüft wurde gegen {list(gelaende_muster)} und die Wortliste "
                f"{list(GELAENDE_WOERTER)}. "
                + ("Die Maske GILT: Jeder geprüfte Eintrag trägt eine IFC-Klasse, und "
                   "IfcSite ist die genormte Klasse für das Grundstück — über einem "
                   "vollständigen Katalog ist ein Nullbefund ein Beweis. Das Urteil ruht "
                   "damit auf einer Regel, die hier nichts zu finden hatte, und nicht auf "
                   "einer Regel, die versagt haben könnte. "
                   if lage["ifc_katalog"] else
                   "Die Maske fällt trotzdem aus — nicht weil der Befund schwach wäre, "
                   "sondern weil er etwas anderes belegt, als er zu belegen scheint: dass "
                   "die REGEL nicht angeschlagen hat. Die Namen sind keine IFC-Klassen; "
                   "ein Baustoff namens 'Erdreich' oder 'Humus' stünde in keiner der "
                   "beiden Listen und wäre trotzdem Gelände. ") +
                "**Und mit der Maske fällt der ganze Maskenweg aus** — rho_maske, Kante "
                "und Paarurteil bleiben None, und das sind die Masse, die die ABWESENHEIT "
                "eines Bauwerks fangen; der Score über das ganze Bild fängt sie nicht "
                "(ein leeres Grundstück erreichte dort 0.9530 und bestand das Tor, "
                "auf-20260821-26). Seit dem Owner-Entscheid vom 26.08.2026 gibt es dann "
                "gar kein Urteil mehr: `bestanden` steht auf None. "
                "WER DIE NAMEN OBEN LIEST UND KEINEN BODEN DARUNTER FINDET, sagt es mit "
                "gelaende_erwartet=False — an der Kommandozeile: "
                "tools/abholen.py --kein-gelaende. Dann gilt die Maske unter dieser "
                "Erklärung, und das steht auch so im Ergebnis."
            )
        elif gelaende_erwartet:
            warnungen.append(
                "Die Geländeregel passte auf keinen einzigen Tabelleneintrag "
                f"(Muster: {list(gelaende_muster)}; Namen: {sorted(bauwerk_namen)}). "
                f"{lage['begruendung']} "
                "Damit ist nicht entscheidbar, ob diese Szene kein Gelände hat oder ob "
                "die Regel es verfehlt hat — im zweiten Fall steckte der ganze Boden als "
                "Bauwerk in der Maske, und genau das macht die Geometrie-QA stumpf "
                "(gemessen: Rauschen erreichte auf einer Bodenszene den Score 0.72). "
                "Die Maske bleibt None: nicht gemessen, nicht in Ordnung. **Und mit "
                "ihr fällt der ganze Maskenweg aus** — rho_maske, Kante und Paarurteil "
                "bleiben None, und das sind die Masse, die die ABWESENHEIT eines "
                "Bauwerks fangen; der Score über das ganze Bild fängt sie nicht (ein "
                "leeres Grundstück erreichte dort 0.9530 und bestand das Tor, "
                "auf-20260821-26). Wer weiss, dass diese Szene "
                "ohne Gelände gerendert wurde, sagt es mit gelaende_erwartet=False — an "
                "der Kommandozeile: tools/abholen.py --kein-gelaende. "
                "HINWEIS ZUR VORGESCHICHTE: Bis zum 26.08.2026 schlug dieser Satz auch "
                "bei Szenen MIT Gelände an, weil der IFC-Name den glb-Export nicht "
                "überlebte und die Regel nichts zu lesen bekam. Seit der Knotenname ihn "
                "mitträgt, ist ein Treffer hier wieder eine Auskunft."
            )
        else:
            warnungen.append(
                "Die Geländeregel passte auf keinen Tabelleneintrag. Der Aufrufer hat "
                "erklärt, dass diese Szene kein Gelände enthält (gelaende_erwartet="
                "False) — die Maske gilt unter dieser Erklärung und nicht aus eigener "
                "Prüfung."
            )
    elif not gelaende_erwartet:
        warnungen.append(
            f"Der Aufrufer hat erklärt, diese Szene enthalte kein Gelände — die Regel "
            f"hat aber {sorted(set(gelaende_namen))} als Gelände eingeordnet und diese "
            f"Punkte aus der Maske genommen. Eine der beiden Angaben stimmt nicht."
        )

    # ── Der Klumpen ───────────────────────────────────────────────────────────────────
    #
    # Gemessen an neun echten IFC (HomeStation, BEFUND_2026-08-24_IFC-LESER.md):
    # `Bestand_Kontext.ifc`, 56 MB, kommt als EIN namenloses Bauteil mit 502 002
    # Dreiecken an — bei beiden Lesern gleich. Keine Klassen, keine Geschosse, keine
    # Materialien.
    #
    # Was das FUER DIE MASKE heisst, ist genauer als «unbrauchbar»: Vom Himmel lässt sich
    # so ein Klumpen sehr wohl trennen — das tut diese Maske weiterhin richtig. Was NICHT
    # geht, ist der Entwurf gegen seine Nachbarschaft. Wer im Kontext rendert, misst dann
    # den ganzen Klumpen und hält das Ergebnis für eine Aussage über sein Bauwerk.
    #
    # Darum eine Warnung und KEIN None: Die Maske ist nicht falsch, sie beantwortet nur
    # eine engere Frage, als der Aufrufer vermutlich meint.
    if len(tabelle) == 1:
        warnungen.append(
            f"Die Materialtabelle hat genau EINEN Eintrag ({sorted(bauwerk_namen) or '—'}). "
            f"Diese Maske trennt die Geometrie noch vom Himmel, aber NICHTS INNERHALB der "
            f"Geometrie — weder Bauwerk von Gelände noch Entwurf von Nachbarschaft. "
            f"Gemessen kommt das an echten Dateien vor: eine 56-MB-Kontext-IFC lieferte "
            f"ein einziges namenloses Bauteil mit 502 002 Dreiecken "
            f"(BEFUND_2026-08-24_IFC-LESER.md). Wird im Kontext gerendert, misst die "
            f"Geometrie-QA den ganzen Klumpen und nicht den Entwurf.")

    if n_bauwerk == 0:
        warnungen.append(
            "Kein einziger Bildpunkt trägt Bauwerk. Entweder steht das Bauwerk ausserhalb "
            "des Bildausschnitts, oder die Geländeregel hat alles eingesammelt "
            f"(als Gelände eingeordnet: {sorted(set(gelaende_namen))}). Eine leere Maske "
            "ist eine gültige Antwort auf die Frage — aber selten die gemeinte."
        )
    if n_unbekannt:
        beispiele = sorted(unbekannte_farben)[:5]
        warnungen.append(
            f"{n_unbekannt} Bildpunkte tragen eine Farbe, die in der Tabelle nicht "
            f"vorkommt (z. B. {beispiele}). Sie zählen nicht zum Bauwerk. Der Runner "
            f"schaltet Dithering und Rekonstruktionsfilter ab, damit an Kanten keine "
            f"Mischfarben entstehen — treten trotzdem welche auf, stammt dieses Bild "
            f"nicht aus dem eingestellten Multipass."
        )

    # DER BELEGTE NULLBEFUND TRAEGT DIE MASKE — aber nur ueber einem IFC-Klassenkatalog.
    #
    # Owner-Entscheid vom 26.08.2026, und er hat einen gemessenen Anlass: Seit der
    # Maskenweg ein zweites Tor ist, kostet eine verworfene Maske das GANZE Urteil. Auf
    # zwei von drei Testszenen verwarf die Regel sie, obwohl dort gar kein Boden steht
    # (141 bzw. 5 benannte Eintraege geprueft, kein IfcSite darunter).
    #
    # Warum die Einschraenkung auf den Katalog: `IfcSite` ist die genormte Klasse fuer das
    # Grundstueck. Traegt jeder Eintrag eine IFC-Klasse und ist keiner davon IfcSite, ist
    # "kein Gelaende" ein Beweis. Ueber MATERIALNAMEN gilt das nicht — echte
    # Projektgeometrie meldet dort "Beton" und "kalksandstein" (docs/MASKE_2026-08-21.md),
    # und ein Boden hiesse "Erdreich" oder "Kies".
    #
    # Der Preis der falschen Entscheidung ist in beide Richtungen gemessen: Steckt der
    # Boden faelschlich in der Maske, sank die Trennschaerfe bei 4,2 % Bodenanteil um
    # 0.042 (0.915 -> 0.873); bei 59,8 % erreichte ein wertloses Bild |rho| 0.92
    # (21.08.2026). Was dazwischen geschieht, ist UNGEMESSEN — und diese Luecke ist der
    # Grund, warum die Ausnahme so eng ist wie sie ist.
    nullbefund_traegt = (lage["befund"] == BEFUND_KEIN_GELAENDE_BELEGT
                         and lage["ifc_katalog"])

    maske: list[bool] | None = roh_maske
    if not gelaende_erkannt and gelaende_erwartet and not nullbefund_traegt:
        maske = None

    return {
        "maske": maske,
        "n_bildpunkte": n_bildpunkte,
        "n_bauwerk": n_bauwerk,
        "n_gelaende": n_gelaende,
        "n_hintergrund": n_hintergrund,
        "n_unbekannt": n_unbekannt,
        "anteil_bauwerk": n_bauwerk / n_bildpunkte,
        "gelaende_erkannt": gelaende_erkannt,
        # WELCHE DER DREI LAGEN — und woran man das sieht. Bis zum 26.08.2026 bedeutete
        # `gelaende_erkannt: False` zweierlei: geprüft und nichts gefunden, oder gar
        # nichts zu prüfen gehabt. Auf Rückfrage der HomeStation (auf-47) getrennt.
        "gelaende_befund": lage["befund"],
        # Der Beleg, auf dem die Ausnahme ruht — er wandert mit, weil ein "die Maske
        # gilt" ohne ihn eine Behauptung ist und mit ihm eine Auskunft.
        "ifc_katalog": lage["ifc_katalog"],
        "gelaende_geprueft": lage["geprueft"],
        "gelaende_begruendung": lage["begruendung"],
        "gelaende_namen": sorted(set(gelaende_namen)),
        "bauwerk_namen": sorted(set(bauwerk_namen)),
        # WAS ALS UMFELD AUSGESCHLOSSEN WURDE, mit Namen. Ein faelschlich
        # ausgeschlossenes Bauteil verschwindet damit nicht still — es steht hier.
        "umfeld_namen": sorted(set(umfeld_namen)),
        "quelle": sorted({str(e["quelle"]) for e in tabelle
                          if e.get("quelle") is not None}),
        "muster": list(gelaende_muster),
        "methode": METHODE,
        "warnungen": warnungen,
    }


def bauwerksmaske_aus_lauf(material_id_png, report, *,
                           gelaende_muster: Sequence[str] = GELAENDE_MUSTER,
                           gelaende_erwartet: bool = True) -> dict:
    """Wie :func:`bauwerksmaske`, aber von den beiden Dateien eines Blender-Laufs aus.

    Die dünne Schicht darüber — sie liest, sie deutet nicht. Dieselbe Trennung wie
    zwischen ``bildlesen`` und ``geometrie_qa``: Wer eine Maske aus Zahlen im Speicher
    braucht (Tests, andere Quellen, ein späterer Segmentierer), ruft
    :func:`bauwerksmaske` und braucht kein Dateisystem.

    Args:
        material_id_png: Pfad auf ``material_id.png`` aus dem Multipass.
        report: ``blender-report.json`` desselben Laufs — als Pfad oder als schon
            geladenes ``dict``. **Desselben Laufs**: Eine Tabelle aus einem anderen Lauf
            passte womöglich Farbe für Farbe und benennte trotzdem andere Bauteile, denn
            die Indizes hängen an der Objektliste der Szene. Das kann dieses Modul nicht
            prüfen, und darum steht es hier.

    Returns:
        Dasselbe Ergebnis wie :func:`bauwerksmaske`, ergänzt um ``breite``, ``hoehe`` und
        ``material_id_png`` — ohne die Masse liesse sich die Maske nicht wieder zu einem
        Bild zusammensetzen, und ohne den Pfad nicht mehr zurückverfolgen.

    Raises:
        MaskeError: Report unbrauchbar oder ohne Tabelle (siehe
            :func:`tabelle_aus_report`).
        aiimaging.bildlesen.BildError: Das PNG ist keines, ist beschädigt oder hat eine
            andere Bittiefe als 8.
    """
    tabelle = tabelle_aus_report(report)
    farben, breite, hoehe = lies_png_farben(material_id_png)
    ergebnis = bauwerksmaske(
        farben, tabelle,
        gelaende_muster=gelaende_muster, gelaende_erwartet=gelaende_erwartet,
    )
    ergebnis["breite"] = breite
    ergebnis["hoehe"] = hoehe
    ergebnis["material_id_png"] = str(material_id_png)
    return ergebnis


def maske_aus_bericht(bericht: dict, *, gelaende_erwartet: bool = True) -> dict:
    """Die Bauwerksmaske aus dem Material-ID-Pass — oder eine benannte Lücke.

    **Warum ein Fehlschlag hier den Lauf nicht aufhält.** Die Maske ist die *zusätzliche*
    Messung, nicht die einzige; der Score über das ganze Bild entsteht ohnehin. Ein
    Auftrag, der an einer fehlenden Materialtabelle scheiterte, wäre ein Auftrag ohne
    Bild — und das ist teurer als eine ungemessene Zusatzfrage.

    **Warum er trotzdem nicht verschwindet.** Ohne diesen Befund sähe ein Lauf ohne Maske
    hinterher aus wie einer mit Maske und ohne Auffälligkeit. Genau diese Verwechslung
    ist der Grund, warum das ganze Modul die Dreiteilung durchhält.

    **Und warum ``gelaende_erwartet`` hier durchgereicht wird.** Ein reines Gebäude-IFC
    bringt **gar kein Gelände** mit — der eine ``IfcSite`` darin trägt keine Geometrie und
    taucht in der Ausgabe nicht auf (HomeStation, `BEFUND_2026-08-24_IFC-LESER.md`, an
    neun echten Dateien gemessen). Die Maske meldet dann «kein Gelände erkannt», und das
    ist ein **Fehlalarm und kein Befund**: Es fehlt nichts, es war nie welches da.

    Bis zum 24.08.2026 kam der Schalter hier nicht an — er stand in :mod:`aiimaging.maske`
    und war von aussen nicht erreichbar. Dieselbe Naht-Sache wie bei Brennweite und
    Geländestand: einstellbar im Modul, nicht im Betrieb.

    Returns:
        ``{maske, gemessen, grund, ...}``. ``maske`` ist ``None``, wenn sie sich nicht
        bauen liess — dann bleibt der Maskenweg in der QA ungemessen.
    """
    png = bericht.get("material_id_png")
    if not png:
        return {"maske": None, "gemessen": False, "grund": (
            "Kein Material-ID-Pass im Bericht. Ohne ihn gibt es keine Bauwerksmaske — und "
            "damit keine Antwort auf die Frage, ob im Bild überhaupt ein Bauwerk steht. "
            "Der Lauf geht weiter; die Frage bleibt UNGEMESSEN.")}
    try:
        gebaut = bauwerksmaske_aus_lauf(
            png, bericht, gelaende_erwartet=gelaende_erwartet)
    except Exception as fehler:        # noqa: BLE001 — siehe Docstring
        return {"maske": None, "gemessen": False, "grund": (
            f"Bauwerksmaske nicht baubar: {type(fehler).__name__}: {fehler}")}
    if gebaut.get("maske") is None:
        return dict(gebaut, gemessen=False, grund=" ".join(gebaut.get("warnungen") or [])
                    or "Die Geländeregel hat nicht gegriffen.")
    return dict(gebaut, gemessen=True, grund="")


__all__ = [
    "GELAENDE_MUSTER", "HINTERGRUND_FARBE", "METHODE", "MaskeError",
    "maske_aus_bericht",
    "bauwerksmaske", "bauwerksmaske_aus_lauf", "ist_gelaende", "tabelle_aus_report",
]
