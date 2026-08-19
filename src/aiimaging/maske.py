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

def ist_gelaende(name: str, muster: Sequence[str] = GELAENDE_MUSTER) -> bool:
    """Gilt ``name`` nach der Geländeregel als Gelände?

    Die eine Stelle, an der die Regel *angewendet* wird — herausgezogen, damit sie
    einzeln prüfbar ist und damit ein Aufrufer sie befragen kann, ohne ein Bild zu haben.

    Verglichen wird der **ganze** Name nach Kleinschreibung gegen jedes Muster
    (``fnmatch``: ``*`` und ``?`` sind Platzhalter, sonst gilt Gleichheit). Kein
    Teilstring-Vergleich: ``"boden" in "Bodenplatte des 2. OG"`` wäre wahr, und ein
    Geschossboden ist kein Gelände. Wer Teilstrings will, schreibt sie als ``"*boden*"``
    hin — dann steht die Entscheidung wenigstens da.

    Args:
        name: Material- oder Objektname aus der Material-ID-Tabelle.
        muster: Die Regel. Leer heisst: keine Regel, nichts ist Gelände — das ist
            zulässig und wird von :func:`bauwerksmaske` als Befund behandelt, nicht als
            Erfolg.

    Returns:
        ``True``, wenn mindestens ein Muster passt.
    """
    n = str(name).strip().lower()
    return any(fnmatchcase(n, str(m).strip().lower()) for m in muster)


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
    warnungen: list[str] = []

    for stelle, eintrag in enumerate(tabelle):
        farbe = _farbe_aus_eintrag(eintrag, stelle)
        name = str(eintrag.get("name", ""))
        gelaende = ist_gelaende(name, gelaende_muster)
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
        (gelaende_namen if gelaende else bauwerk_namen).append(name)

    gelaende_erkannt = bool(gelaende_namen)

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
        if gelaende_erwartet:
            warnungen.append(
                "Die Geländeregel passte auf keinen einzigen Tabelleneintrag "
                f"(Muster: {list(gelaende_muster)}; Namen: {sorted(bauwerk_namen)}). "
                "Damit ist nicht entscheidbar, ob diese Szene kein Gelände hat oder ob "
                "die Regel es verfehlt hat — im zweiten Fall steckte der ganze Boden als "
                "Bauwerk in der Maske, und genau das macht die Geometrie-QA stumpf "
                "(gemessen: Rauschen erreichte auf einer Bodenszene den Score 0.72). "
                "Die Maske bleibt None: nicht gemessen, nicht in Ordnung. Wer weiss, "
                "dass diese Szene ohne Gelände gerendert wurde, sagt es mit "
                "gelaende_erwartet=False."
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

    maske: list[bool] | None = roh_maske
    if not gelaende_erkannt and gelaende_erwartet:
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
        "gelaende_namen": sorted(set(gelaende_namen)),
        "bauwerk_namen": sorted(set(bauwerk_namen)),
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


__all__ = [
    "GELAENDE_MUSTER", "HINTERGRUND_FARBE", "METHODE", "MaskeError",
    "bauwerksmaske", "bauwerksmaske_aus_lauf", "ist_gelaende", "tabelle_aus_report",
]
